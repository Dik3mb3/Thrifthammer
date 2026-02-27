"""
Miniature Market scraper.

Scrapes live price, stock status, and product URL for every active GW product
in the database. Uses the predictable Miniature Market URL pattern:

    https://www.miniaturemarket.com/gw-{SKU}.html

If a SKU returns a 404, the product is marked as not available at this retailer
(the CurrentPrice row is deleted if it exists). If the page loads but shows
"Out of stock", the price is saved with in_stock=False.

Usage:
    python manage.py run_scrapers miniature-market

Notes:
- Respects SCRAPER_REQUEST_DELAY (default 2s) between requests.
- Skips products whose gw_sku is blank or starts with a non-GW prefix
  (e.g. custom SKUs like 'HA-', 'KT-', 'BP-' etc. that MM won't carry).
- Only scrapes products with standard numeric GW SKUs (e.g. 48-75, 49-06).
"""

import logging
import re
import time

from bs4 import BeautifulSoup
from django.conf import settings

from prices.models import CurrentPrice
from products.models import Product, Retailer
from scrapers.models import ScrapeJob
from django.utils import timezone

logger = logging.getLogger(__name__)

# SKU prefixes that are GW numeric format (e.g. 48-75) — only these are scraped.
# Non-numeric prefixes (KT-, HA-, BP-, etc.) are skipped as MM won't list them
# under the gw-{SKU}.html pattern.
GW_SKU_PATTERN = re.compile(r'^\d{2,3}-\d{2,3}$')

# Selectors — update here if MM redesigns their product page.
PRICE_SELECTORS = [
    'span.price',
    '.product-info-price .price',
    '[data-price-type="finalPrice"] .price',
    '.special-price .price',
    '.regular-price .price',
]
OUT_OF_STOCK_PHRASES = ['out of stock', 'unavailable', 'sold out']


class MiniatureMarketScraper:
    """
    Scraper for Miniature Market (miniaturemarket.com).

    Iterates over all active products with standard GW SKUs, fetches each
    product page, extracts price and stock status, and upserts CurrentPrice.
    """

    retailer_slug = 'miniature-market'
    base_url = 'https://www.miniaturemarket.com/gw-{sku}.html'

    def __init__(self):
        """Initialise requests session with browser-like headers."""
        import requests
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': getattr(
                settings,
                'SCRAPER_USER_AGENT',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                'AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/120.0.0.0 Safari/537.36',
            ),
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        })
        self.delay = getattr(settings, 'SCRAPER_REQUEST_DELAY', 2)

    def run(self):
        """Execute a full scrape job and return the ScrapeJob record."""
        try:
            retailer = Retailer.objects.get(slug=self.retailer_slug)
        except Retailer.DoesNotExist:
            logger.error('Retailer "%s" not found in DB.', self.retailer_slug)
            raise

        job = ScrapeJob.objects.create(
            retailer=retailer,
            status='running',
            started_at=timezone.now(),
        )
        errors = []

        products = Product.objects.filter(is_active=True).exclude(gw_sku='')

        for product in products:
            sku = product.gw_sku.strip()

            # Skip non-standard SKUs (KT-001, HA-001, BP-001, etc.)
            if not GW_SKU_PATTERN.match(sku):
                logger.debug('Skipping non-standard SKU: %s (%s)', sku, product.name)
                continue

            url = self.base_url.format(sku=sku)
            job.products_found += 1

            try:
                result = self._scrape_product(url, sku, product.name)

                if result is None:
                    # 404 — product not listed on MM; remove stale price if exists
                    deleted, _ = CurrentPrice.objects.filter(
                        product=product, retailer=retailer
                    ).delete()
                    if deleted:
                        logger.info('[removed]  %s — no longer listed on MM', product.name)
                    else:
                        logger.info('[skip]     %s — not on MM (SKU %s)', product.name, sku)
                else:
                    price, in_stock = result
                    CurrentPrice.objects.update_or_create(
                        product=product,
                        retailer=retailer,
                        defaults={
                            'price': price,
                            'url': url,
                            'in_stock': in_stock,
                        },
                    )
                    stock_label = 'in stock' if in_stock else 'OUT OF STOCK'
                    logger.info(
                        '[updated]  %s — £%.2f (%s)',
                        product.name, price, stock_label,
                    )
                    job.prices_updated += 1

            except Exception as exc:
                msg = f'{product.name} (SKU {sku}): {exc}'
                errors.append(msg)
                logger.exception('Error scraping %s', product.name)

            time.sleep(self.delay)

        job.status = 'success'
        job.errors = '\n'.join(errors)
        job.finished_at = timezone.now()
        job.save()
        return job

    def _scrape_product(self, url, sku, name):
        """
        Fetch a single product page and extract price + stock status.

        Miniature Market renders prices via JavaScript data layer JSON, so we
        extract price from the raw HTML using regex against known JS patterns
        rather than CSS selectors.

        Returns:
            (Decimal, bool) — (price, in_stock) if found
            None            — if the product is not listed (404 / redirect)
        """
        from decimal import Decimal, InvalidOperation

        try:
            response = self.session.get(url, timeout=15, allow_redirects=True)
        except Exception as exc:
            raise RuntimeError(f'Network error fetching {url}: {exc}') from exc

        # MM returns 404 or redirects to homepage for unknown SKUs
        if response.status_code == 404:
            return None
        if response.status_code != 200:
            raise RuntimeError(f'HTTP {response.status_code} for {url}')

        # If redirected away from the product URL, SKU doesn't exist on MM
        if ('gw-' + sku.lower()) not in response.url.lower():
            return None

        html = response.text

        # ── Stock status ─────────────────────────────────────────────────────
        # Check the JS data layer first: "availability":"in stock" / "out of stock"
        stock_match = re.search(r'"availability"\s*:\s*"([^"]+)"', html, re.IGNORECASE)
        if stock_match:
            in_stock = 'out of stock' not in stock_match.group(1).lower()
        else:
            # Fallback: scan visible page text
            soup = BeautifulSoup(html, 'html.parser')
            page_text = soup.get_text(separator=' ').lower()
            in_stock = not any(phrase in page_text for phrase in OUT_OF_STOCK_PHRASES)

        # ── Price ─────────────────────────────────────────────────────────────
        price = None

        # Strategy 1: JS data layer — "productPrice":"53.99"
        match = re.search(r'"productPrice"\s*:\s*"?([\d.]+)"?', html)
        if match:
            try:
                price = Decimal(match.group(1))
            except InvalidOperation:
                pass

        # Strategy 2: gtag / GA4 ecommerce — "price":53.99
        if price is None:
            match = re.search(r'"price"\s*:\s*([\d.]+)', html)
            if match:
                try:
                    candidate = Decimal(match.group(1))
                    # Sanity check — GW products are between $5 and $1000
                    if 5 <= candidate <= 1000:
                        price = candidate
                except InvalidOperation:
                    pass

        # Strategy 3: meta tag — <meta itemprop="price" content="53.99">
        if price is None:
            match = re.search(r'itemprop=["\']price["\'][^>]*content=["\']([^"\']+)["\']', html)
            if not match:
                match = re.search(r'content=["\']([^"\']+)["\'][^>]*itemprop=["\']price["\']', html)
            if match:
                try:
                    price = Decimal(match.group(1))
                except InvalidOperation:
                    pass

        # Strategy 4: last resort — first $ price in reasonable range on the page
        if price is None:
            for m in re.finditer(r'\$\s*(\d{1,4}\.\d{2})', html):
                try:
                    candidate = Decimal(m.group(1))
                    if 5 <= candidate <= 1000:
                        price = candidate
                        break
                except InvalidOperation:
                    continue

        if price is None or price <= 0:
            raise RuntimeError(f'Could not extract price from {url}')

        return price, in_stock
