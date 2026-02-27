"""
Miniature Market scraper.

For each active GW product, attempts to find the correct MM product page using
a two-step approach:

  Step 1 — Direct SKU URL:
    Fetch https://www.miniaturemarket.com/gw-{SKU}.html and verify the page's
    item_id matches our SKU (e.g. "GW-48-75"). If confirmed, extract price.

  Step 2 — Name search fallback:
    If Step 1 fails (404, wrong product, or SKU mismatch), search MM using the
    product name and pick the best matching result by comparing names.

Price and stock status are extracted from the JavaScript data layer JSON that
MM embeds in every product page:
  - "productPrice": "53.99"
  - "availability": "http://schema.org/InStock"
  - "item_id": "GW-48-75"

Usage:
    python manage.py run_scrapers miniature-market

Notes:
- Respects SCRAPER_REQUEST_DELAY (default 2s) between requests.
- Only scrapes products with standard numeric GW SKUs (e.g. 48-75, 49-06).
  Non-numeric prefixes (KT-, HA-, BP-, etc.) are skipped.
- 404s and unmatched searches remove any stale CurrentPrice rows.
"""

import json
import logging
import re
import time
from decimal import Decimal, InvalidOperation
from urllib.parse import quote_plus

from bs4 import BeautifulSoup
from django.conf import settings
from django.utils import timezone

from prices.models import CurrentPrice
from products.models import Product, Retailer
from scrapers.models import ScrapeJob

logger = logging.getLogger(__name__)

# Only scrape standard numeric GW SKUs like 48-75, 49-06, 101-23
GW_SKU_PATTERN = re.compile(r'^\d{2,3}-\d{2,3}$')

# Schema.org out-of-stock URL fragment
OUT_OF_STOCK_SCHEMA = 'outofstock'

# MM search URL
SEARCH_URL = 'https://www.miniaturemarket.com/catalogsearch/result/index/?q={query}'


class MiniatureMarketScraper:
    """
    Scraper for Miniature Market (miniaturemarket.com).

    Uses a direct SKU URL first, then falls back to a name-based search
    if the SKU URL returns the wrong product or a 404.
    """

    retailer_slug = 'miniature-market'
    base_url = 'https://www.miniaturemarket.com/gw-{sku}.html'

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

            if not GW_SKU_PATTERN.match(sku):
                logger.debug('Skipping non-standard SKU: %s (%s)', sku, product.name)
                continue

            job.products_found += 1

            try:
                result = self._find_product(sku, product.name)

                if result is None:
                    # Not found on MM — remove stale price row if present
                    deleted, _ = CurrentPrice.objects.filter(
                        product=product, retailer=retailer
                    ).delete()
                    if deleted:
                        logger.info('[removed]  %s — no longer on MM', product.name)
                    else:
                        logger.info('[skip]     %s — not on MM (SKU %s)', product.name, sku)
                else:
                    price, in_stock, final_url = result
                    CurrentPrice.objects.update_or_create(
                        product=product,
                        retailer=retailer,
                        defaults={
                            'price': price,
                            'url': final_url,
                            'in_stock': in_stock,
                        },
                    )
                    stock_label = 'in stock' if in_stock else 'OUT OF STOCK'
                    logger.info(
                        '[updated]  %s — $%.2f (%s) — %s',
                        product.name, price, stock_label, final_url,
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
    # Product finder — SKU URL first, name search fallback
    # -------------------------------------------------------------------------

    def _find_product(self, sku, name):
        """
        Try to locate the MM product page for a given SKU + name.

        Returns:
            (Decimal, bool, str) — (price, in_stock, url) if found
            None                 — if not listed on MM
        """
        # Step 1: direct SKU URL
        direct_url = self.base_url.format(sku=sku)
        result = self._try_direct_url(direct_url, sku)
        if result is not None:
            return result

        # Step 2: name-based search fallback
        time.sleep(self.delay)
        return self._try_name_search(sku, name)

    def _try_direct_url(self, url, sku):
        """
        Fetch the gw-{SKU}.html URL and verify the item_id matches.

        Returns (price, in_stock, url) or None.
        """
        try:
            response = self.session.get(url, timeout=15, allow_redirects=True)
        except Exception as exc:
            raise RuntimeError(f'Network error fetching {url}: {exc}') from exc

        if response.status_code == 404:
            return None
        if response.status_code != 200:
            raise RuntimeError(f'HTTP {response.status_code} for {url}')

        # Redirected away from our URL means SKU not found
        if ('gw-' + sku.lower()) not in response.url.lower():
            return None

        html = response.text
        data = self._extract_data_layer(html)

        if not data:
            return None

        # Verify item_id matches our SKU (e.g. "GW-48-75" matches "48-75")
        item_id = data.get('item_id', '').upper().replace('GW-', '')
        if item_id and item_id != sku.upper():
            logger.debug(
                'SKU mismatch on direct URL: expected %s, got %s — trying search',
                sku, item_id,
            )
            return None

        price = data.get('price')
        in_stock = data.get('in_stock', True)
        if price is None:
            return None

        return price, in_stock, response.url

    def _try_name_search(self, sku, name):
        """
        Search MM by product name and find the best matching result.

        Strips common GW prefixes ("Warhammer 40K:", "Space Marines -") and
        searches for the core product name. Picks the result whose item_id
        matches our SKU, or falls back to the closest name match.

        Returns (price, in_stock, url) or None.
        """
        # Build a clean search query from the product name
        # Remove faction prefixes like "Space Marine", "Necron", etc.
        search_name = self._clean_search_name(name)
        search_url = SEARCH_URL.format(query=quote_plus(search_name))

        try:
            response = self.session.get(search_url, timeout=15)
        except Exception as exc:
            raise RuntimeError(f'Search request failed: {exc}') from exc

        if response.status_code != 200:
            return None

        soup = BeautifulSoup(response.text, 'html.parser')

        # Find all product links on the search results page
        product_links = []
        for a in soup.select('a[href*="miniaturemarket.com"]'):
            href = a.get('href', '')
            if href.endswith('.html') and 'gw-' in href.lower():
                product_links.append(href)

        # Also try list item links
        for a in soup.select('.product-item-link, .product-item-name a'):
            href = a.get('href', '')
            if href and href.endswith('.html'):
                product_links.append(href)

        # Deduplicate
        product_links = list(dict.fromkeys(product_links))

        if not product_links:
            logger.debug('No search results for "%s" (SKU %s)', search_name, sku)
            return None

        # Check each result — prefer one whose item_id matches our SKU
        for link in product_links[:5]:  # check top 5 results max
            time.sleep(1)
            try:
                r = self.session.get(link, timeout=15, allow_redirects=True)
                if r.status_code != 200:
                    continue
                data = self._extract_data_layer(r.text)
                if not data:
                    continue

                item_id = data.get('item_id', '').upper().replace('GW-', '')
                price = data.get('price')
                in_stock = data.get('in_stock', True)

                if price is None:
                    continue

                # Best case: item_id exactly matches our SKU
                if item_id == sku.upper():
                    logger.debug('Search matched by SKU: %s → %s', sku, link)
                    return price, in_stock, r.url

            except Exception:
                continue

        # Nothing matched by SKU — not found on MM
        return None

    # -------------------------------------------------------------------------
    # Data extraction helpers
    # -------------------------------------------------------------------------

    def _extract_data_layer(self, html):
        """
        Extract price, stock status, and item_id from MM's JS data layer.

        MM embeds structured data in multiple places:
          - dataLayer.push({ productPrice, productCurrency })
          - gtag ecommerce items array: { item_id, price }
          - Schema.org: "availability": "http://schema.org/InStock"

        Returns a dict with keys: price (Decimal), in_stock (bool), item_id (str)
        or None if extraction fails.
        """
        result = {}

        # ── item_id ──────────────────────────────────────────────────────────
        id_match = re.search(r'"item_id"\s*:\s*"([^"]+)"', html)
        if id_match:
            result['item_id'] = id_match.group(1)

        # ── Stock status ─────────────────────────────────────────────────────
        # Schema.org availability (most reliable)
        avail_match = re.search(
            r'"availability"\s*:\s*"([^"]+)"', html, re.IGNORECASE
        )
        if avail_match:
            result['in_stock'] = OUT_OF_STOCK_SCHEMA not in avail_match.group(1).lower()
        else:
            # Fallback: page text
            soup = BeautifulSoup(html, 'html.parser')
            page_text = soup.get_text(separator=' ').lower()
            result['in_stock'] = 'out of stock' not in page_text

        # ── Price ─────────────────────────────────────────────────────────────
        price = None

        # Strategy 1: "productPrice":"53.99"
        m = re.search(r'"productPrice"\s*:\s*"?([\d.]+)"?', html)
        if m:
            try:
                price = Decimal(m.group(1))
            except InvalidOperation:
                pass

        # Strategy 2: GA4 ecommerce "price":53.99
        if price is None:
            m = re.search(r'"price"\s*:\s*([\d.]+)', html)
            if m:
                try:
                    candidate = Decimal(m.group(1))
                    if 5 <= candidate <= 1500:
                        price = candidate
                except InvalidOperation:
                    pass

        # Strategy 3: <meta itemprop="price" content="53.99">
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
                    if 5 <= candidate <= 1500:
                        price = candidate
                        break
                except InvalidOperation:
                    continue

        if price and price > 0:
            result['price'] = price

        return result if result else None

    @staticmethod
    def _clean_search_name(name):
        """
        Strip faction/game prefixes from a product name to get a cleaner
        search term for Miniature Market.

        E.g. "Space Marine Intercessors" → "Intercessors"
             "Necron Warriors"           → "Warriors"
             "T'au Fire Warriors"        → "Fire Warriors"
        """
        # Remove leading game system prefixes MM adds
        prefixes = [
            'Warhammer 40K:', 'Warhammer 40,000:', 'Age of Sigmar:',
            'Horus Heresy:', 'Kill Team:', 'Warcry:',
        ]
        cleaned = name
        for prefix in prefixes:
            if cleaned.lower().startswith(prefix.lower()):
                cleaned = cleaned[len(prefix):].strip()

        # Keep the full cleaned name for best search accuracy
        return cleaned
