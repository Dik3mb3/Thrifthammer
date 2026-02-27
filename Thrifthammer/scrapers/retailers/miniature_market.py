"""
Miniature Market scraper.

For each active GW product, tries to find the correct MM product page using
a three-step approach:

  Step 1 — Direct SKU URL (gw-{SKU}.html):
    Fastest path. Verifies item_id in the JS data layer matches our SKU.

  Step 2 — Variant URL patterns:
    MM sometimes appends a year or variant suffix, e.g. gw-48-07-2023.html.
    Tries a few known suffix patterns before giving up.

  Step 3 — Name match on direct page:
    If both URL attempts land on a page, checks item_name similarity to
    confirm it's the right product even if item_id differs (retailers
    sometimes use different SKU codes).

Price, stock status, and the confirmed URL are extracted from MM's JS
data layer which contains:
  - "productPrice": "53.99"
  - "availability": "http://schema.org/InStock"
  - "item_id": "GW-48-75"
  - "item_name": "Warhammer 40K: Space Marine Primaris Intercessors"

Usage:
    python manage.py run_scrapers miniature-market

Notes:
- Scrapes ALL active products regardless of SKU format.
- Numeric GW SKUs (48-75) use the gw-{SKU}.html URL pattern.
- Non-numeric SKUs (KT-, HA-, etc.) go straight to not_available since
  MM does not stock them under a predictable URL.
- Every product always gets a row — either a real price or not_available=True.
"""

import logging
import re
import time
from decimal import Decimal, InvalidOperation

from bs4 import BeautifulSoup
from django.conf import settings
from django.utils import timezone

from prices.models import CurrentPrice
from products.models import Product, Retailer
from scrapers.models import ScrapeJob

logger = logging.getLogger(__name__)

# Standard numeric GW SKU pattern: 48-75, 49-06, 101-23
GW_SKU_PATTERN = re.compile(r'^\d{2,3}-\d{2,3}$')

# Schema.org out-of-stock indicator
OUT_OF_STOCK_SCHEMA = 'outofstock'

# URL suffix variants MM sometimes uses
URL_VARIANTS = [
    'https://www.miniaturemarket.com/gw-{sku}.html',
    'https://www.miniaturemarket.com/gw-{sku}-2024.html',
    'https://www.miniaturemarket.com/gw-{sku}-2023.html',
    'https://www.miniaturemarket.com/gw-{sku}-2022.html',
]


class MiniatureMarketScraper:
    """
    Scraper for Miniature Market (miniaturemarket.com).

    Tries direct SKU URL variants, verifies correctness by matching
    item_name from the JS data layer against our product name.
    Always writes a result row — either with price or not_available=True.
    """

    retailer_slug = 'miniature-market'

    def __init__(self):
        """Initialise requests session with browser-like headers."""
        import requests
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': (
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                'AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/120.0.0.0 Safari/537.36'
            ),
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept': (
                'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
            ),
        })
        self.delay = getattr(settings, 'SCRAPER_REQUEST_DELAY', 2)

    # -------------------------------------------------------------------------
    # Public entry point
    # -------------------------------------------------------------------------

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
            job.products_found += 1

            try:
                # Non-numeric SKUs (KT-, HA-, BP-, etc.) are not on MM
                if not GW_SKU_PATTERN.match(sku):
                    self._save_not_available(product, retailer)
                    logger.info('[n/a]      %s — non-standard SKU', product.name)
                    job.prices_updated += 1
                    continue

                result = self._find_product(sku, product.name)

                if result is None:
                    self._save_not_available(product, retailer)
                    logger.info('[n/a]      %s — not found on MM', product.name)
                else:
                    price, in_stock, final_url = result
                    CurrentPrice.objects.update_or_create(
                        product=product,
                        retailer=retailer,
                        defaults={
                            'price': price,
                            'url': final_url,
                            'in_stock': in_stock,
                            'not_available': False,
                        },
                    )
                    stock_label = 'in stock' if in_stock else 'OUT OF STOCK'
                    logger.info(
                        '[updated]  %s — $%.2f (%s)',
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

    # -------------------------------------------------------------------------
    # Product finder
    # -------------------------------------------------------------------------

    def _find_product(self, sku, name):
        """
        Try URL variants for gw-{SKU}.html and verify by name match.

        For each URL variant:
          1. Fetch the page
          2. Extract data layer (item_name, item_id, price, availability)
          3. Score the match:
             +2  item_name closely matches our product name
             +1  item_id matches our SKU
          4. Accept if score >= 1

        Returns (Decimal, bool, str) or None.
        """
        clean_name = self._clean_name(name).lower()

        for url_template in URL_VARIANTS:
            url = url_template.format(sku=sku)
            try:
                response = self.session.get(url, timeout=15, allow_redirects=True)
            except Exception:
                continue

            if response.status_code == 404:
                continue
            if response.status_code != 200:
                continue

            # If redirected away from a gw- URL, this variant doesn't exist
            if 'gw-' not in response.url.lower():
                continue

            data = self._extract_data_layer(response.text)
            if not data or data.get('price') is None:
                continue

            # Score this result
            score = 0
            item_id = data.get('item_id', '').upper().replace('GW-', '')
            page_name = self._clean_name(data.get('item_name', '')).lower()

            # Name match — strip common MM prefix "Warhammer 40K: " for comparison
            if clean_name and page_name:
                if clean_name in page_name or page_name in clean_name:
                    score += 2
                else:
                    # Partial word match — check if most words overlap
                    our_words = set(clean_name.split())
                    page_words = set(page_name.split())
                    overlap = our_words & page_words
                    if len(overlap) >= max(1, len(our_words) - 1):
                        score += 1

            # SKU match
            if item_id and item_id == sku.upper():
                score += 1

            logger.debug(
                'URL %s | score=%d | item_id=%s | page_name="%s" | our_name="%s"',
                url, score, item_id, page_name, clean_name,
            )

            if score >= 1:
                return data['price'], data.get('in_stock', True), response.url

            time.sleep(1)

        return None

    # -------------------------------------------------------------------------
    # Data extraction
    # -------------------------------------------------------------------------

    def _extract_data_layer(self, html):
        """
        Extract price, stock, item_id, and item_name from MM's JS data layer.

        Returns dict with keys: price, in_stock, item_id, item_name
        or None if extraction fails entirely.
        """
        result = {}

        # item_id — e.g. "GW-48-75"
        m = re.search(r'"item_id"\s*:\s*"([^"]+)"', html)
        if m:
            result['item_id'] = m.group(1)

        # item_name — e.g. "Warhammer 40K: Space Marine Primaris Intercessors"
        m = re.search(r'"item_name"\s*:\s*"([^"]+)"', html)
        if m:
            result['item_name'] = m.group(1)

        # Stock status — schema.org availability
        m = re.search(r'"availability"\s*:\s*"([^"]+)"', html, re.IGNORECASE)
        if m:
            result['in_stock'] = OUT_OF_STOCK_SCHEMA not in m.group(1).lower()
        else:
            soup = BeautifulSoup(html, 'html.parser')
            result['in_stock'] = 'out of stock' not in soup.get_text().lower()

        # Price — try multiple strategies
        price = None

        # Strategy 1: "productPrice":"53.99"
        m = re.search(r'"productPrice"\s*:\s*"?([\d.]+)"?', html)
        if m:
            try:
                price = Decimal(m.group(1))
            except InvalidOperation:
                pass

        # Strategy 2: GA4 "price":53.99
        if price is None:
            m = re.search(r'"price"\s*:\s*([\d.]+)', html)
            if m:
                try:
                    candidate = Decimal(m.group(1))
                    if 1 <= candidate <= 1500:
                        price = candidate
                except InvalidOperation:
                    pass

        # Strategy 3: meta itemprop price
        if price is None:
            m = re.search(
                r'itemprop=["\']price["\'][^>]*content=["\']([^"\']+)["\']', html
            )
            if not m:
                m = re.search(
                    r'content=["\']([^"\']+)["\'][^>]*itemprop=["\']price["\']', html
                )
            if m:
                try:
                    price = Decimal(m.group(1))
                except InvalidOperation:
                    pass

        # Strategy 4: first $ amount in valid range
        if price is None:
            for m in re.finditer(r'\$\s*(\d{1,4}\.\d{2})', html):
                try:
                    candidate = Decimal(m.group(1))
                    if 1 <= candidate <= 1500:
                        price = candidate
                        break
                except InvalidOperation:
                    continue

        if price and price > 0:
            result['price'] = price

        return result if result else None

    # -------------------------------------------------------------------------
    # Helpers
    # -------------------------------------------------------------------------

    @staticmethod
    def _save_not_available(product, retailer):
        """Upsert a not_available=True CurrentPrice row for this product."""
        CurrentPrice.objects.update_or_create(
            product=product,
            retailer=retailer,
            defaults={
                'price': None,
                'url': '',
                'in_stock': False,
                'not_available': True,
            },
        )

    @staticmethod
    def _clean_name(name):
        """
        Strip common prefixes MM and GW add so names compare cleanly.

        'Warhammer 40K: Space Marine Primaris Intercessors'
          → 'Space Marine Primaris Intercessors'
        'Space Marines - Assault Intercessors'
          → 'Space Marines Assault Intercessors'
        """
        prefixes = [
            'Warhammer 40K:', 'Warhammer 40,000:', 'Age of Sigmar:',
            'Horus Heresy:', 'Kill Team:', 'Warcry:', 'Necromunda:',
        ]
        cleaned = name.strip()
        for prefix in prefixes:
            if cleaned.lower().startswith(prefix.lower()):
                cleaned = cleaned[len(prefix):].strip()
                break
        # Normalise dashes and extra spaces
        cleaned = re.sub(r'\s*-\s*', ' ', cleaned)
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        return cleaned
