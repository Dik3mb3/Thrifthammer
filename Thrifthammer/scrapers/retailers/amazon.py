"""
Amazon price scraper — URL-based approach.

Uses the Amazon product URLs already stored in CurrentPrice records to fetch
live prices directly from product pages.  No Amazon API account required.

Approach:
  For each active product that has an Amazon URL in CurrentPrice:
    1. GET the stored Amazon product page URL
    2. Extract price from multiple CSS selector strategies (newest Amazon
       HTML structure first, older fallbacks after)
    3. Determine in_stock from the #availability element
    4. Update CurrentPrice.price and in_stock if a price is found

Price extraction cascade (tried in order):
  1. span.a-offscreen inside the core price block — Amazon's accessibility
     span that holds the full formatted price (e.g. "$39.99") in one place.
     Most reliable because it predates the split whole/fraction layout.
  2. #corePrice_feature_div / #corePriceDisplay_desktop_feature_div —
     the 2022+ desktop price container.  Price is split into
     a-price-whole + a-price-fraction.
  3. #priceblock_ourprice / #priceblock_dealprice — older price blocks,
     still used on some product pages.
  4. .priceToPay span.a-price — checkout CTA price, used on some listings.

If no price can be extracted (e.g. Amazon serves a bot-check page, or the
product is sold by a third-party marketplace seller only), the product is
skipped and the existing price is left unchanged.

Anti-bot measures:
  - Realistic browser User-Agent string
  - Accept / Accept-Language / Accept-Encoding headers
  - 2-second delay between requests (configurable via SCRAPER_REQUEST_DELAY)
  - Randomised extra jitter (0–1 s) to reduce fingerprinting

Usage:
    python manage.py run_scrapers amazon

Notes:
  - Only processes products whose CurrentPrice.manual_url_override is False.
    Manually-curated URLs are respected and prices are updated normally —
    manual_url_override only prevents the URL itself from being overwritten.
  - Products with no Amazon URL are skipped (not marked not_available).
  - A failed price extraction (blocked/CAPTCHA) logs a warning and skips
    that product, leaving the existing price unchanged.
  - Amazon may block some requests. This scraper will succeed for the
    majority of products in a given run; any that are blocked will retain
    their previous price until the next scheduled run.
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

# Amazon US domain
AMAZON_DOMAIN = 'amazon.com'

# Delay between page requests (seconds).  Polite crawling reduces blocking.
DEFAULT_DELAY = 2.0

# Extra random jitter added to each delay (0–JITTER_MAX seconds).
JITTER_MAX = 1.0

# CSS selectors tried for price extraction, in priority order.
# Each entry is (container_selector, whole_selector, fraction_selector).
# If whole_selector is None, the container is expected to hold the full price.
_PRICE_STRATEGIES = [
    # Strategy 1: a-offscreen accessibility span — full "$39.99" string in one element.
    # Exists inside the primary price block on modern Amazon pages.
    (
        '#corePrice_feature_div .a-price .a-offscreen,'
        '#corePriceDisplay_desktop_feature_div .a-price .a-offscreen,'
        '.priceToPay .a-price .a-offscreen',
        None, None,
    ),
    # Strategy 2: whole + fraction split inside corePrice containers (2022+ layout).
    (
        '#corePrice_feature_div',
        '.a-price-whole',
        '.a-price-fraction',
    ),
    (
        '#corePriceDisplay_desktop_feature_div',
        '.a-price-whole',
        '.a-price-fraction',
    ),
    # Strategy 3: classic priceblock elements (pre-2022 layout, still live on some pages).
    (
        '#priceblock_ourprice',
        None, None,
    ),
    (
        '#priceblock_dealprice',
        None, None,
    ),
    # Strategy 4: priceToPay CTA block.
    (
        '.priceToPay',
        '.a-price-whole',
        '.a-price-fraction',
    ),
]


class AmazonScraper:
    """
    Scraper for Amazon (amazon.com).

    Fetches live prices from stored Amazon product page URLs and updates
    CurrentPrice records.  Works without an Amazon API account.
    """

    retailer_slug = 'amazon'

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
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
        })
        self.delay = DEFAULT_DELAY

    # -------------------------------------------------------------------------
    # Public entry point
    # -------------------------------------------------------------------------

    def run(self):
        """
        Scrape Amazon prices for all products with a stored Amazon URL.

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

        # Only fetch products that already have an Amazon URL stored.
        # Skip manual_url_override — the URL is correct by design; we still
        # update the price (price staleness is independent of URL correctness).
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
            if AMAZON_DOMAIN not in url:
                logger.debug('[amazon] Skipping non-Amazon URL for %s: %s', product.name, url)
                continue

            job.products_found += 1

            try:
                result = self._fetch_price(url)

                if result is None:
                    # First attempt failed — wait a little longer and try again.
                    retry_delay = self.delay * 2 + random.uniform(1, 3)
                    logger.debug(
                        '[amazon] Attempt 1 failed for %s — retrying in %.1fs',
                        product.name, retry_delay,
                    )
                    time.sleep(retry_delay)
                    result = self._fetch_price(url)

                if result is None:
                    # Second attempt failed — one more try with a longer back-off.
                    retry_delay2 = self.delay * 3 + random.uniform(2, 5)
                    logger.debug(
                        '[amazon] Attempt 2 failed for %s — final retry in %.1fs',
                        product.name, retry_delay2,
                    )
                    time.sleep(retry_delay2)
                    result = self._fetch_price(url)

                if result is None:
                    # All 3 attempts failed — leave existing price intact.
                    logger.warning(
                        '[amazon] [no price] %s (%s) — could not extract price after 3 attempts: %s',
                        product.name, product.gw_sku, url[:80],
                    )
                else:
                    price, in_stock = result
                    entry.price = price
                    entry.in_stock = in_stock
                    entry.not_available = False
                    entry.save(update_fields=['price', 'in_stock', 'not_available'])
                    stock_label = 'in stock' if in_stock else 'OUT OF STOCK'
                    logger.info(
                        '[amazon] [updated]  %s (%s) — £%.2f  %s',
                        product.name, product.gw_sku or '-', price, stock_label,
                    )
                    job.prices_updated += 1

            except Exception as exc:
                msg = f'{product.name} ({product.gw_sku}): {exc}'
                errors.append(msg)
                logger.exception('[amazon] Error scraping %s', product.name)

            # Polite delay + random jitter between requests.
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
        GET an Amazon product page and extract the price.

        Args:
            url: Full Amazon product URL (https://www.amazon.com/dp/...).

        Returns:
            (Decimal price, bool in_stock) or None if price cannot be extracted.
        """
        try:
            response = self.session.get(url, timeout=15)
        except requests.RequestException as exc:
            logger.warning('[amazon] Request failed for %s: %s', url[:80], exc)
            return None

        if response.status_code != 200:
            logger.debug('[amazon] HTTP %d for %s', response.status_code, url[:80])
            return None

        # Quick bot-check detection: Amazon CAPTCHA pages contain the string
        # "Type the characters you see" in the response body.
        if 'Type the characters you see' in response.text:
            logger.warning('[amazon] Bot-check page returned for %s', url[:80])
            return None

        soup = BeautifulSoup(response.text, 'html.parser')
        price = self._extract_price(soup)

        if price is None:
            return None

        in_stock = self._extract_in_stock(soup)
        return price, in_stock

    def _extract_price(self, soup):
        """
        Try each price strategy in turn.  Return Decimal price or None.

        Args:
            soup: BeautifulSoup of the Amazon product page.

        Returns:
            Decimal price or None.
        """
        for container_sel, whole_sel, fraction_sel in _PRICE_STRATEGIES:
            price = self._try_strategy(soup, container_sel, whole_sel, fraction_sel)
            if price is not None:
                return price
        return None

    @staticmethod
    def _try_strategy(soup, container_sel, whole_sel, fraction_sel):
        """
        Apply one price-extraction strategy to the parsed page.

        Args:
            soup:          BeautifulSoup object.
            container_sel: CSS selector for the price container element.
                           If whole_sel is None, the container's text IS the price.
            whole_sel:     CSS selector (relative to container) for the integer part.
            fraction_sel:  CSS selector (relative to container) for the decimal part.

        Returns:
            Decimal price or None.
        """
        try:
            container = soup.select_one(container_sel)
            if not container:
                return None

            if whole_sel is None:
                # Container holds the full price string (e.g. "$39.99" or "39.99")
                raw = container.get_text(strip=True)
            else:
                whole_el = container.select_one(whole_sel)
                if not whole_el:
                    return None
                whole_text = whole_el.get_text(strip=True).replace(',', '')

                fraction_el = container.select_one(fraction_sel) if fraction_sel else None
                fraction_text = fraction_el.get_text(strip=True) if fraction_el else '00'

                # Amazon sometimes includes a trailing period in the whole part
                whole_text = whole_text.rstrip('.')
                raw = f'{whole_text}.{fraction_text}'

            # Strip currency symbols, commas, whitespace
            cleaned = re.sub(r'[^\d.]', '', raw)
            if not cleaned:
                return None

            return Decimal(cleaned)

        except (InvalidOperation, ValueError, AttributeError):
            return None

    @staticmethod
    def _extract_in_stock(soup):
        """
        Determine whether the product is currently in stock.

        Args:
            soup: BeautifulSoup of the Amazon product page.

        Returns:
            True if in stock, False if unavailable.  Defaults to True
            (if the availability element is absent, a price was found so
            the product is likely purchaseable).
        """
        availability_div = soup.select_one('#availability')
        if availability_div is None:
            return True  # No availability notice = assume in stock

        avail_text = availability_div.get_text(strip=True).lower()
        unavailable_signals = (
            'currently unavailable',
            'out of stock',
            'unavailable',
        )
        for signal in unavailable_signals:
            if signal in avail_text:
                return False

        return True
