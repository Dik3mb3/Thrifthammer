"""
Noble Knight Games scraper — URL-based approach (mirrors Amazon scraper).

For each active product that has a Noble Knight URL stored in CurrentPrice,
fetches the product page directly and extracts the live price.

Price extraction:
    The price lives in a nested <span class="price"> element as plain text:
        <span class="price">Our Price $31.95</span>
    A single regex captures the dollar amount.

Stock detection:
    - In stock  → page contains an "Add to Cart" button (class "atc")
      that is NOT disabled.
    - Out of stock → button is disabled or absent, OR the page contains
      the text "Out of Stock".

Usage:
    python manage.py run_scrapers noble-knight-games

Notes:
  - Only processes products that already have an NK URL in CurrentPrice.
    Products without a URL are skipped (not marked not_available).
  - If price extraction fails after 3 attempts: price is blanked and
    in_stock is set to False (treat as out of stock on NK).
  - manual_url_override=True rows: URL is NOT changed; price IS updated.
  - Polite 1.5 s delay + 0–1 s jitter between requests.
"""

import logging
import random
import re
import time
from decimal import Decimal, InvalidOperation

import requests
from bs4 import BeautifulSoup
from django.utils import timezone

from prices.models import CurrentPrice
from products.models import Retailer
from scrapers.models import ScrapeJob

logger = logging.getLogger(__name__)

NK_DOMAIN = 'nobleknight.com'
DEFAULT_DELAY = 1.5
JITTER_MAX = 1.0


class NoblekKnightScraper:
    """
    Scraper for Noble Knight Games (nobleknight.com).

    Fetches live prices from stored NK product page URLs and updates
    CurrentPrice records. Works without any NK API account.
    """

    retailer_slug = 'noble-knight-games'

    def __init__(self):
        """Initialise a requests session with browser-like headers."""
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': (
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                'AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/124.0.0.0 Safari/537.36'
            ),
            'Accept': (
                'text/html,application/xhtml+xml,application/xml;'
                'q=0.9,image/avif,image/webp,*/*;q=0.8'
            ),
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Upgrade-Insecure-Requests': '1',
        })
        self.delay = DEFAULT_DELAY

    # -------------------------------------------------------------------------
    # Public entry point
    # -------------------------------------------------------------------------

    def run(self):
        """
        Scrape NK prices for all products with a stored NK URL.

        Returns the ScrapeJob record.
        """
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

        entries = (
            CurrentPrice.objects
            .filter(retailer=retailer)
            .exclude(url='')
            .exclude(url__isnull=True)
            .select_related('product')
        )

        for entry in entries:
            product = entry.product
            if not product.is_active:
                continue

            url = entry.url
            if NK_DOMAIN not in url:
                logger.debug('[nk] Skipping non-NK URL for %s: %s', product.name, url)
                continue

            job.products_found += 1

            try:
                result = self._fetch_price(url)

                if result is None:
                    # Retry once with back-off
                    time.sleep(self.delay * 2 + random.uniform(1, 3))
                    result = self._fetch_price(url)

                if result is None:
                    # Final retry
                    time.sleep(self.delay * 3 + random.uniform(2, 5))
                    result = self._fetch_price(url)

                if result is None:
                    logger.warning(
                        '[nk] [no price] %s — blanking price (out of stock or fetch failed): %s',
                        product.name, url[:80],
                    )
                    entry.price = None
                    entry.in_stock = False
                    entry.save(update_fields=['price', 'in_stock'])
                else:
                    price, in_stock = result
                    entry.price = price
                    entry.in_stock = in_stock
                    entry.not_available = False
                    entry.save(update_fields=['price', 'in_stock', 'not_available'])
                    logger.info(
                        '[nk] [updated] %s — $%.2f  %s',
                        product.name, price, 'in stock' if in_stock else 'OUT OF STOCK',
                    )
                    job.prices_updated += 1

            except Exception as exc:
                msg = f'{product.name} ({product.gw_sku}): {exc}'
                errors.append(msg)
                logger.exception('[nk] Error scraping %s', product.name)

            time.sleep(self.delay + random.uniform(0, JITTER_MAX))

        job.status = 'success'
        job.errors = '\n'.join(errors)
        job.finished_at = timezone.now()
        job.save()
        return job

    # -------------------------------------------------------------------------
    # Price extraction
    # -------------------------------------------------------------------------

    def _fetch_price(self, url):
        """
        GET a Noble Knight product page and extract the price.

        Returns (Decimal price, bool in_stock) or None if extraction fails.
        """
        try:
            response = self.session.get(url, timeout=15)
        except requests.RequestException as exc:
            logger.warning('[nk] Request failed for %s: %s', url[:80], exc)
            return None

        if response.status_code == 404:
            logger.warning('[nk] 404 for %s — URL may be stale', url[:80])
            return None

        if response.status_code != 200:
            logger.debug('[nk] HTTP %d for %s', response.status_code, url[:80])
            return None

        soup = BeautifulSoup(response.text, 'html.parser')
        price = self._extract_price(soup)
        if price is None:
            return None

        in_stock = self._extract_in_stock(soup)
        return price, in_stock

    @staticmethod
    def _extract_price(soup):
        """
        Extract price from the NK product page.

        NK renders: <span class="price">Our Price $31.95</span>
        Returns Decimal or None.
        """
        # Find the innermost .price span that contains a dollar amount
        for el in soup.select('span.price'):
            text = el.get_text(strip=True)
            m = re.search(r'\$\s*(\d{1,4}\.\d{2})', text)
            if m:
                try:
                    price = Decimal(m.group(1))
                    if 1 <= price <= 2000:
                        return price
                except InvalidOperation:
                    pass
        return None

    @staticmethod
    def _extract_in_stock(soup):
        """
        Determine whether the product is currently in stock.

        In stock  → an "Add to Cart" button (class "atc") exists and is not disabled.
        Out of stock → button is disabled, absent, or page contains "Out of Stock".
        Returns True if in stock, False otherwise.
        """
        # Check for explicit out-of-stock text
        page_text = soup.get_text().lower()
        if 'out of stock' in page_text:
            return False

        # Check the add-to-cart button
        atc = soup.select_one('button.atc, .atc')
        if atc is None:
            return False  # No cart button = not available

        # Disabled button = out of stock
        if atc.has_attr('disabled'):
            return False

        button_text = atc.get_text(strip=True).lower()
        if 'out of stock' in button_text or 'sold out' in button_text:
            return False

        return True
