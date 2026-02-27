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
        Locate the correct MM product page for a given SKU + name.

        Priority order:
          1. Name search — search MM by product name, then within results
             prefer: (a) name AND SKU both match, (b) name match only,
             (c) SKU match only.
          2. Direct SKU URL fallback — try gw-{SKU}.html if search finds
             nothing at all (some products aren't indexed in MM search).

        Returns:
            (Decimal, bool, str) — (price, in_stock, url) if found
            None                 — if not listed on MM
        """
        # Step 1: name-based search (primary)
        result = self._try_name_search(sku, name)
        if result is not None:
            return result

        # Step 2: direct SKU URL fallback
        time.sleep(self.delay)
        return self._try_direct_url(sku)

    def _try_name_search(self, sku, name):
        """
        Search MM by product name and score each result.

        Scoring per result page:
          +2  product name contains our search name (case-insensitive)
          +1  item_id matches our SKU
          Best score wins. Must score >= 1 to be accepted.

        Returns (price, in_stock, url) or None.
        """
        search_name = self._clean_search_name(name)
        search_url = SEARCH_URL.format(query=quote_plus(search_name))

        try:
            response = self.session.get(search_url, timeout=15)
        except Exception as exc:
            raise RuntimeError(f'Search request failed for "{search_name}": {exc}') from exc

        if response.status_code != 200:
            return None

        soup = BeautifulSoup(response.text, 'html.parser')

        # Collect product page links from search results
        product_links = []
        for a in soup.select('.product-item-link, .product-item-name a, a.product-item-photo'):
            href = a.get('href', '')
            if href and href.endswith('.html'):
                product_links.append(href)
        # Also catch any GW-prefixed links
        for a in soup.select('a[href*="/gw-"]'):
            href = a.get('href', '')
            if href.endswith('.html') and href not in product_links:
                product_links.append(href)

        product_links = list(dict.fromkeys(product_links))  # deduplicate, preserve order

        if not product_links:
            logger.debug('No search results for "%s" (SKU %s)', search_name, sku)
            return None

        best_score = 0
        best_result = None
        search_name_lower = search_name.lower()

        for link in product_links[:8]:  # check top 8 results
            time.sleep(1)
            try:
                r = self.session.get(link, timeout=15, allow_redirects=True)
                if r.status_code != 200:
                    continue
                data = self._extract_data_layer(r.text)
                if not data or data.get('price') is None:
                    continue

                score = 0
                item_id = data.get('item_id', '').upper().replace('GW-', '')
                page_name = data.get('item_name', '').lower()

                # +2 for name match (most reliable signal)
                if search_name_lower in page_name or page_name in search_name_lower:
                    score += 2

                # +1 for SKU match (backup signal)
                if item_id == sku.upper():
                    score += 1

                logger.debug(
                    'Candidate: %s | score=%d | item_id=%s | name=%s',
                    link, score, item_id, page_name,
                )

                if score > best_score:
                    best_score = score
                    best_result = (data['price'], data.get('in_stock', True), r.url)

                # Perfect match — stop early
                if score >= 3:
                    break

            except Exception:
                continue

        if best_result and best_score >= 1:
            logger.debug(
                'Search best match (score=%d): %s', best_score, best_result[2]
            )
            return best_result

        return None

    def _try_direct_url(self, sku):
        """
        Fallback: fetch gw-{SKU}.html directly.

        Used when name search returns no results at all (product may not be
        indexed in MM search but still has a direct product page).

        Returns (price, in_stock, url) or None.
        """
        url = self.base_url.format(sku=sku)
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

        data = self._extract_data_layer(response.text)
        if not data or data.get('price') is None:
            return None

        return data['price'], data.get('in_stock', True), response.url

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

        # ── item_name ────────────────────────────────────────────────────────
        name_match = re.search(r'"item_name"\s*:\s*"([^"]+)"', html)
        if name_match:
            result['item_name'] = name_match.group(1)

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
