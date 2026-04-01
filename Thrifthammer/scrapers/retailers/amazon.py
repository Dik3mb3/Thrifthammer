"""
Amazon price scraper — URL-based approach.

Uses the Amazon product URLs already stored in CurrentPrice records to fetch
live prices directly from product pages.  No Amazon API account required.

Approach:
  For each active product that has an Amazon URL in CurrentPrice:
    1. Strip URL to a clean bare ASIN (/dp/XXXXXXXXXX) to remove tracking params
    2. GET the Amazon product page
    3. Extract price from multiple CSS selector strategies (newest Amazon
       HTML structure first, older fallbacks after)
    4. Determine in_stock from the #availability element
    5. Update CurrentPrice.price and in_stock if a price is found

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
  - Rotate through 5 browser fingerprints (Chrome Win/Mac, Firefox, Edge,
    Safari) — different User-Agents, Sec-CH-UA headers, and Accept strings
  - Fresh session every 15 products — each batch looks like a new visitor
    rather than one session scraping hundreds of pages in sequence
  - Session warm-up: visits amazon.com home page to acquire session cookies
    (session-id, ubid-main, etc.) that real browsers accumulate
  - Always strips URLs to bare ASIN (/dp/ASIN) before fetching — removes
    affiliate/tracking parameters that fingerprint automated scrapers
  - Randomised product order — avoids the predictable sequential pattern
    of automated scraping
  - Expanded block-page detection — catches all known Amazon bot-detection
    page variants (CAPTCHA, robot check, auth-redirect, etc.)
  - 2-second delay between requests (configurable via DEFAULT_DELAY)
  - Randomised extra jitter (0–1 s) to reduce timing fingerprints

Important — where to run this scraper:
  Amazon blocks requests from GitHub Actions (AWS IP ranges). For best
  results run from Railway (Google Cloud) via a Railway Cron service:
    Schedule: 0 4 * * *
    Command:  python manage.py run_scrapers amazon && python manage.py clear_cache

Usage:
    python manage.py run_scrapers amazon

Notes:
  - Only processes products whose CurrentPrice entries have a stored URL.
    Products with no Amazon URL are skipped (not marked not_available).
  - A failed price extraction (blocked/CAPTCHA) logs a warning and skips
    that product, leaving the existing price unchanged.
  - Amazon may block some requests. This scraper will succeed for the
    majority of products in a given run; blocked products retain their
    previous price until the next scheduled run.
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

# Rotate to a fresh session after this many products.
# Shorter batches look more like distinct organic browsing sessions.
_SESSION_ROTATE_EVERY = 15

# ---------------------------------------------------------------------------
# Browser fingerprint pool — rotated across sessions.
# Each entry is (user_agent_string, extra_headers_dict).
# Extra headers must match the UA (e.g. Sec-CH-UA for Chromium-based only).
# ---------------------------------------------------------------------------
_BROWSER_PROFILES = [
    # Chrome 124 on Windows
    (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/124.0.0.0 Safari/537.36',
        {
            'Sec-CH-UA': '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
            'Sec-CH-UA-Mobile': '?0',
            'Sec-CH-UA-Platform': '"Windows"',
            'Accept': (
                'text/html,application/xhtml+xml,application/xml;'
                'q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8'
            ),
        },
    ),
    # Chrome 122 on macOS
    (
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/122.0.0.0 Safari/537.36',
        {
            'Sec-CH-UA': '"Chromium";v="122", "Google Chrome";v="122", "Not-A.Brand";v="99"',
            'Sec-CH-UA-Mobile': '?0',
            'Sec-CH-UA-Platform': '"macOS"',
            'Accept': (
                'text/html,application/xhtml+xml,application/xml;'
                'q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8'
            ),
        },
    ),
    # Firefox 125 on Windows — different Accept header, no Sec-CH-UA
    (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) '
        'Gecko/20100101 Firefox/125.0',
        {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        },
    ),
    # Microsoft Edge 124 on Windows
    (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.0',
        {
            'Sec-CH-UA': '"Chromium";v="124", "Microsoft Edge";v="124", "Not-A.Brand";v="99"',
            'Sec-CH-UA-Mobile': '?0',
            'Sec-CH-UA-Platform': '"Windows"',
            'Accept': (
                'text/html,application/xhtml+xml,application/xml;'
                'q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,'
                'application/signed-exchange;v=b3;q=0.7'
            ),
        },
    ),
    # Safari 17 on macOS — no Sec-CH-UA, no Sec-Fetch-* headers
    (
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4_1) '
        'AppleWebKit/605.1.15 (KHTML, like Gecko) '
        'Version/17.4.1 Safari/605.1.15',
        {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
        },
    ),
]

# User-Agent for the mobile-browser fallback attempt.
_MOBILE_USER_AGENT = (
    'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) '
    'AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 '
    'Mobile/15E148 Safari/604.1'
)

# All known strings that indicate Amazon served a block/bot-detection page.
# Any match means we should treat the response as blocked and return None.
_BLOCK_SIGNALS = (
    'Type the characters you see',    # CAPTCHA
    'Enter the characters you see',   # CAPTCHA variant
    'Robot Check',                    # Robot check page
    '/ap/signin',                     # Redirect to sign-in
    'validateCaptcha',                # Inline CAPTCHA form
    'Sorry, we just need to make sure',  # Auth challenge
    'To discuss automated access to Amazon data',  # Automated-access block
    'api-services-support@amazon.com',             # Automated-access block
    'auth-redirected',                             # Auth redirect signal
    'gcx-auth-challenge',                          # New auth challenge (2024+)
)

# CSS selectors tried for price extraction, in priority order.
# Each entry is (container_selector, whole_selector, fraction_selector).
# If whole_selector is None, the container is expected to hold the full price.
_PRICE_STRATEGIES = [
    # Strategy 1: a-offscreen accessibility span — full "$39.99" in one element.
    (
        '#corePrice_feature_div .a-price .a-offscreen,'
        '#corePriceDisplay_desktop_feature_div .a-price .a-offscreen,'
        '.priceToPay .a-price .a-offscreen',
        None, None,
    ),
    # Strategy 2: whole + fraction split inside corePrice containers (2022+).
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
    # Strategy 3: classic priceblock elements (pre-2022, still live on some pages).
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

# Additional price selectors used only in the mobile fallback attempt.
_MOBILE_PRICE_STRATEGIES = [
    ('#price_inside_buybox',              None, None),
    ('#actualPriceValue',                 None, None),
    ('.a-box-inner .a-color-price',       None, None),
    ('#buyNewSection .a-color-price',     None, None),
    ('#newBuyBoxPrice',                   None, None),
] + _PRICE_STRATEGIES


def _strip_to_asin_url(url):
    """
    Strip an Amazon URL down to the bare ASIN product page.

    Removes affiliate tags, search parameters, and tracking tokens that
    can fingerprint an automated scraper.  Returns the cleaned URL, or the
    original URL unchanged if no ASIN can be found.

    Args:
        url: Any Amazon product URL.

    Returns:
        Bare ASIN URL (https://www.amazon.com/dp/XXXXXXXXXX) or original url.
    """
    asin_match = re.search(r'/dp/([A-Z0-9]{10})', url)
    if asin_match:
        return f'https://www.amazon.com/dp/{asin_match.group(1)}'
    return url


class AmazonScraper:
    """
    Scraper for Amazon (amazon.com).

    Fetches live prices from stored Amazon product page URLs and updates
    CurrentPrice records.  Works without an Amazon API account.

    Uses session rotation and browser fingerprint diversity to reduce the
    chance of bot detection on consecutive requests.
    """

    retailer_slug = 'amazon'

    def __init__(self):
        """Initialise state and create the first browser session."""
        self._ua_index = 0
        self._products_since_rotation = 0
        self.delay = DEFAULT_DELAY
        self.session = None
        self._make_fresh_session()

    # -------------------------------------------------------------------------
    # Session management
    # -------------------------------------------------------------------------

    def _make_fresh_session(self):
        """
        Create a new requests.Session with the next browser profile from the pool.

        Rotates through _BROWSER_PROFILES in order (wrapping around) so that
        each batch of _SESSION_ROTATE_EVERY products uses a different browser
        fingerprint.  Warms up the session by visiting the Amazon home page
        to acquire session cookies.
        """
        ua, extra_headers = _BROWSER_PROFILES[self._ua_index % len(_BROWSER_PROFILES)]
        self._ua_index += 1
        self._products_since_rotation = 0

        session = requests.Session()

        # Base headers present for all browser types
        base_headers = {
            'User-Agent': ua,
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Cache-Control': 'max-age=0',
            'Pragma': 'no-cache',
            'Connection': 'keep-alive',
            'DNT': '1',
            'Upgrade-Insecure-Requests': '1',
        }

        # Chromium-based browsers send Sec-Fetch-* headers; Safari/Firefox do not
        is_chromium = 'Chrome' in ua or 'Edg/' in ua
        if is_chromium:
            base_headers.update({
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
            })

        # Merge base headers with browser-specific extras (UA-matched Accept, Sec-CH-UA, etc.)
        base_headers.update(extra_headers)
        session.headers.update(base_headers)

        self.session = session
        self._warm_up()

        logger.debug(
            '[amazon] Fresh session — profile %d (%s)',
            self._ua_index,
            ua[:60],
        )

    def _warm_up(self):
        """
        Visit Amazon home page to acquire session cookies before scraping.

        Real browsers accumulate cookies (session-id, ubid-main, etc.) from
        the home page.  Sending these with product page requests makes the
        session look more legitimate to Amazon's bot detection.
        """
        try:
            self.session.get('https://www.amazon.com/', timeout=10)
            logger.debug('[amazon] Session warmed up (home page visited)')
            time.sleep(1.5 + random.uniform(0, 1.0))
        except requests.RequestException as exc:
            logger.debug('[amazon] Warm-up request failed (non-fatal): %s', exc)

    # -------------------------------------------------------------------------
    # Public entry point
    # -------------------------------------------------------------------------

    def run(self):
        """
        Scrape Amazon prices for all products with a stored Amazon URL.

        Processes products in randomised order and rotates to a fresh browser
        session every _SESSION_ROTATE_EVERY products.

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

        # Fetch all entries that have an Amazon URL stored.
        entries = list(
            CurrentPrice.objects
            .filter(retailer=retailer)
            .exclude(url='')
            .exclude(url__isnull=True)
            .select_related('product')
        )

        # Randomise order — sequential scraping is a clear bot signal.
        random.shuffle(entries)

        for entry in entries:
            product = entry.product
            if not product.is_active:
                continue

            raw_url = entry.url
            if AMAZON_DOMAIN not in raw_url and 'amzn' not in raw_url:
                logger.debug('[amazon] Skipping non-Amazon URL for %s: %s', product.name, raw_url)
                continue

            # Always use the bare ASIN URL — strips tracking/affiliate params
            # that can fingerprint automated requests.
            url = _strip_to_asin_url(raw_url)

            job.products_found += 1

            # Rotate to a fresh browser session every N products.
            if self._products_since_rotation >= _SESSION_ROTATE_EVERY:
                logger.debug(
                    '[amazon] Rotating browser session after %d products',
                    self._products_since_rotation,
                )
                self._make_fresh_session()

            self._products_since_rotation += 1

            try:
                result = self._fetch_price(url)

                if result is None:
                    retry_delay = self.delay * 2 + random.uniform(1, 3)
                    logger.debug(
                        '[amazon] Attempt 1 failed for %s — retrying in %.1fs',
                        product.name, retry_delay,
                    )
                    time.sleep(retry_delay)
                    result = self._fetch_price(url)

                if result is None:
                    retry_delay2 = self.delay * 3 + random.uniform(2, 5)
                    logger.debug(
                        '[amazon] Attempt 2 failed for %s — final retry in %.1fs',
                        product.name, retry_delay2,
                    )
                    time.sleep(retry_delay2)
                    result = self._fetch_price(url)

                if result is None:
                    # All 3 standard attempts failed — try mobile fallback.
                    logger.debug(
                        '[amazon] All 3 standard attempts failed for %s — '
                        'mobile fallback in 10s',
                        product.name,
                    )
                    time.sleep(10)
                    result = self._fetch_price_fallback(url)

                if result is None:
                    logger.warning(
                        '[amazon] [no price] %s (%s) — could not extract price '
                        'after 4 attempts (3 standard + 1 mobile fallback): %s',
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
                        '[amazon] [updated]  %s (%s) — $%.2f  %s',
                        product.name, product.gw_sku or '-', price, stock_label,
                    )
                    job.prices_updated += 1

            except Exception as exc:
                msg = f'{product.name} ({product.gw_sku}): {exc}'
                errors.append(msg)
                logger.exception('[amazon] Error scraping %s', product.name)

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
            url: Bare Amazon ASIN URL (https://www.amazon.com/dp/...).

        Returns:
            (Decimal price, bool in_stock) or None if price cannot be extracted.
        """
        try:
            response = self.session.get(
                url,
                timeout=15,
                headers={'Referer': 'https://www.amazon.com/'},
            )
        except requests.RequestException as exc:
            logger.warning('[amazon] Request failed for %s: %s', url[:80], exc)
            return None

        if response.status_code != 200:
            logger.debug('[amazon] HTTP %d for %s', response.status_code, url[:80])
            return None

        # Check if we were silently redirected to a block/auth page.
        if 'amazon.com' in response.url and '/ap/' in response.url:
            logger.warning('[amazon] Redirected to auth page for %s', url[:80])
            return None

        for signal in _BLOCK_SIGNALS:
            if signal in response.text:
                logger.warning('[amazon] Blocked page (%s) for %s', signal, url[:80])
                return None

        soup = BeautifulSoup(response.text, 'html.parser')
        price = self._extract_price(soup)

        if price is None:
            return None

        in_stock = self._extract_in_stock(soup)
        return price, in_stock

    def _fetch_price_fallback(self, url):
        """
        Last-resort price fetch using a fresh mobile-browser session.

        Called after all 3 standard attempts have failed.  Uses a completely
        different HTTP fingerprint to avoid triggering the same bot-detection
        rules that blocked the main session:

          - Brand-new requests.Session (no cookies from the blocked session)
          - iPhone Safari User-Agent instead of desktop browser
          - Google search as Referer (looks like organic search traffic)
          - Mobile-specific price CSS selectors tried first

        Returns (Decimal price, bool in_stock) or None if still blocked/failed.
        """
        session = requests.Session()
        session.headers.update({
            'User-Agent':                _MOBILE_USER_AGENT,
            'Accept':                    'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language':           'en-US,en;q=0.5',
            'Accept-Encoding':           'gzip, deflate, br',
            'Referer':                   'https://www.google.com/search?q=warhammer+40k+miniatures',
            'DNT':                       '1',
            'Connection':                'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })

        try:
            response = session.get(url, timeout=15)
        except requests.RequestException as exc:
            logger.warning('[amazon] [fallback] Request failed for %s: %s', url[:80], exc)
            return None

        if response.status_code != 200:
            logger.debug('[amazon] [fallback] HTTP %d for %s', response.status_code, url[:80])
            return None

        for signal in _BLOCK_SIGNALS:
            if signal in response.text:
                logger.warning(
                    '[amazon] [fallback] Blocked (%s) for %s', signal, url[:80],
                )
                return None

        soup = BeautifulSoup(response.text, 'html.parser')

        price = None
        for container_sel, whole_sel, fraction_sel in _MOBILE_PRICE_STRATEGIES:
            price = self._try_strategy(soup, container_sel, whole_sel, fraction_sel)
            if price is not None:
                break

        if price is None:
            return None

        in_stock = self._extract_in_stock(soup)
        logger.info(
            '[amazon] [fallback] [updated] %s — $%.2f  %s',
            url[:80], price, 'in stock' if in_stock else 'OUT OF STOCK',
        )
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
                raw = container.get_text(strip=True)
            else:
                whole_el = container.select_one(whole_sel)
                if not whole_el:
                    return None
                whole_text = whole_el.get_text(strip=True).replace(',', '')

                fraction_el = container.select_one(fraction_sel) if fraction_sel else None
                fraction_text = fraction_el.get_text(strip=True) if fraction_el else '00'

                whole_text = whole_text.rstrip('.')
                raw = f'{whole_text}.{fraction_text}'

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
            return True

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
