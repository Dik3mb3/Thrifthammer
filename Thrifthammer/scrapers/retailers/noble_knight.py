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
    python manage.py run_scrapers noble-knight-games --shard 3/7 --limit 500

Notes:
  - Only processes products that already have an NK URL in CurrentPrice.
    Products without a URL are skipped (not marked not_available).
  - Failure modes are treated differently to prevent over-blanking:
      * Network error / non-200 response / bot detection → the existing price
        is PRESERVED (scrape failure ≠ out of stock).
      * Successful 200 response but no price found → the price is blanked and
        in_stock set to False (product genuinely unavailable on NK).
      * A /P/ product link that now lands on a different kind of page (NK sends
        delisted products to its homepage, which also shows prices) is treated
        as a dead link and never as a price.
  - Blanking is held back until the end of the run and only applied when the
    number of blanks is believable (see scrapers/safeguards.py), so a markup
    change or an outage cannot zero out prices by accident.
  - The run stops after several failed rows in a row (blocked / site down).
  - manual_url_override=True rows: URL is NOT changed; price IS updated.
  - Polite 1.5 s delay + 0–1 s jitter between requests.
"""

import logging
import random
import re
import time
from decimal import Decimal, InvalidOperation
from urllib.parse import urlparse, urlunparse, parse_qs, urlencode

from curl_cffi import requests as curl_requests
from bs4 import BeautifulSoup
from django.utils import timezone

from prices.models import CurrentPrice
from products.models import Retailer
from scrapers.models import ScrapeJob
from scrapers.safeguards import RunGuard, finish_run, note_crash, select_slice

logger = logging.getLogger(__name__)

NK_DOMAIN = 'nobleknight.com'


def _strip_affiliate_params(url):
    """
    Remove affiliate tracking params from a Noble Knight URL before fetching.

    The ?awid= parameter is stored in the DB so user-facing links earn
    commission, but we strip it from scraper requests so bot traffic does
    not pollute Noble Knight's affiliate analytics.
    """
    parsed = urlparse(url)
    params = parse_qs(parsed.query, keep_blank_values=True)
    params.pop('awid', None)
    new_query = urlencode({k: v[0] for k, v in params.items()})
    return urlunparse(parsed._replace(query=new_query))
DEFAULT_DELAY = 0.75
JITTER_MAX = 0.3

# Sentinel returned by _fetch_price when the page could not be retrieved
# (network error, non-200 HTTP status, bot-detection redirect, etc.).
# Distinct from None ("page loaded but no price found") so the run loop can
# preserve the existing price instead of erroneously blanking it.
# Other code (for example fetch_corsair_prices) imports this, so it stays.
_FETCH_ERROR = object()

# Bot-detection pages are typically very short.  If the response body is
# shorter than this threshold (bytes) we treat it as a blocked request rather
# than a real product page.
_MIN_PAGE_BYTES = 5_000

# Outcomes of one page fetch (see NoblekKnightScraper._fetch_page).
_OK = 'ok'                # price and stock read from a product page
_NO_PRICE = 'no_price'    # a real product page that shows no price
_NOT_FOUND = 'not_found'  # HTTP 404
_BLOCKED = 'blocked'      # 403 / 429 / 503, a challenge page or a too-short page
_ERROR = 'error'          # network failure or any other server error
_DEAD_LINK = 'dead_link'  # a /P/ link that now lands off the product pages


class NoblekKnightScraper:
    """
    Scraper for Noble Knight Games (nobleknight.com).

    Fetches live prices from stored NK product page URLs and updates
    CurrentPrice records. Works without any NK API account.
    """

    retailer_slug = 'noble-knight-games'

    def __init__(self):
        """Initialise a curl_cffi session with TLS impersonation for Cloudflare bypass."""
        self.session = curl_requests.Session(impersonate='chrome120')
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
    # Public entry points
    # -------------------------------------------------------------------------

    def select_entries(self, batch_tag=None, shard=None, limit=None):
        """Return the rows a run with these options would visit (read only)."""
        retailer = Retailer.objects.get(slug=self.retailer_slug)
        return select_slice(self._base_entries(retailer, batch_tag), shard, limit)

    def run(self, batch_tag=None, shard=None, limit=None):
        """
        Scrape NK prices for products with a stored NK URL.

        ``shard`` is an ``(index, count)`` pair and ``limit`` a row cap; together
        they select one slice of the catalog (see scrapers/safeguards.py).
        With neither, every row is visited, as before.

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
        guard = RunGuard()
        entries = select_slice(self._base_entries(retailer, batch_tag), shard, limit)

        for entry in entries:
            if guard.tripped:
                break
            if not entry.product.is_active:
                continue
            if NK_DOMAIN not in entry.url:
                logger.debug('[nk] Skipping non-NK URL for %s: %s', entry.product.name, entry.url)
                continue

            job.products_found += 1
            try:
                self._refresh_entry(entry, job, guard, errors)
            except Exception as exc:
                errors.append(f'{entry.product.name} ({entry.product.gw_sku}): {exc}')
                logger.exception('[nk] Error scraping %s', entry.product.name)
                note_crash(guard)

            time.sleep(self.delay + random.uniform(0, JITTER_MAX))

        finish_run(job, guard, errors, 'nk')
        return job

    # -------------------------------------------------------------------------
    # Run helpers
    # -------------------------------------------------------------------------

    @staticmethod
    def _base_entries(retailer, batch_tag):
        """All rows with a stored URL for this retailer, optionally one batch tag."""
        entries = (
            CurrentPrice.objects
            .filter(retailer=retailer)
            .exclude(url='')
            .exclude(url__isnull=True)
            .select_related('product')
        )
        if batch_tag:
            entries = entries.filter(product__batch_tag=batch_tag)
        return entries

    def _refresh_entry(self, entry, job, guard, errors):
        """Fetch one row's page and apply (or hold back) the result."""
        product = entry.product
        was_priced = entry.price is not None
        # Strip affiliate params so bot requests don't hit NK's affiliate
        # tracking endpoint (the tag stays in the DB for user-facing links).
        kind, price, in_stock = self._fetch_with_retries(_strip_affiliate_params(entry.url))

        if kind == _OK:
            entry.price = price
            entry.in_stock = in_stock
            entry.not_available = False
            entry.save(update_fields=['price', 'in_stock', 'not_available', 'last_seen'])
            guard.record_ok(was_priced)
            job.prices_updated += 1
            logger.info(
                '[nk] [updated] %s — $%.2f  %s',
                product.name, price, 'in stock' if in_stock else 'OUT OF STOCK',
            )
        elif kind in (_NO_PRICE, _DEAD_LINK):
            guard.record_ok(was_priced)
            reason = 'no price on the page' if kind == _NO_PRICE else 'link now lands off the product pages'
            if kind == _DEAD_LINK:
                errors.append(f'[dead-link] {product.name} ({product.gw_sku}): {entry.url}')
            logger.warning('[nk] [%s] %s — %s: %s', kind, product.name, reason, entry.url[:80])
            if was_priced:
                guard.defer_blank(entry, reason)
            else:
                entry.save(update_fields=['last_seen'])
        elif kind == _NOT_FOUND:
            guard.record_ok()
            errors.append(f'[stale-link] {product.name} ({product.gw_sku}): {entry.url}')
        elif kind == _BLOCKED:
            guard.record_failure(blocked=True)
            logger.warning('[nk] [blocked] %s — price left unchanged: %s', product.name, entry.url[:80])
        else:
            guard.record_failure()
            logger.warning('[nk] [fetch-failed] %s — price left unchanged: %s', product.name, entry.url[:80])

    def _fetch_with_retries(self, url):
        """
        Fetch a page, retrying network and server errors twice with a back-off.

        A 404, a block and a "no price" answer are not retried.  A dead-link
        answer is confirmed with one more look after a pause before it counts.
        """
        kind, price, in_stock = self._fetch_page(url)
        if kind == _ERROR:
            time.sleep(self.delay + random.uniform(0.5, 1.0))
            kind, price, in_stock = self._fetch_page(url)
        if kind == _ERROR:
            time.sleep(self.delay * 1.5 + random.uniform(0.5, 1.5))
            kind, price, in_stock = self._fetch_page(url)
        if kind == _DEAD_LINK:
            time.sleep(self.delay + random.uniform(4.0, 6.0))
            kind, price, in_stock = self._fetch_page(url)
        return kind, price, in_stock

    # -------------------------------------------------------------------------
    # Price extraction
    # -------------------------------------------------------------------------

    def _fetch_price(self, url):
        """
        GET a Noble Knight product page and extract the price.

        Return values:
            (Decimal price, bool in_stock)  — price extracted successfully
            None                            — page loaded (200) but no price
                                              found; product is confirmed
                                              unavailable or delisted on NK
            _FETCH_ERROR                    — could not load the page at all
                                              (network error, non-200 status,
                                              bot-detection response or a link
                                              that no longer reaches a product
                                              page); caller should preserve
                                              the existing price

        Kept for callers outside the run loop; the run loop uses _fetch_page.
        """
        kind, price, in_stock = self._fetch_page(url)
        if kind == _OK:
            return price, in_stock
        if kind == _NO_PRICE:
            return None
        return _FETCH_ERROR

    def _fetch_page(self, url):
        """
        GET a Noble Knight product page.

        Returns ``(kind, price, in_stock)`` where ``kind`` is one of the
        module-level outcomes (_OK, _NO_PRICE, _NOT_FOUND, _BLOCKED, _ERROR,
        _DEAD_LINK); price and in_stock are only meaningful for _OK.
        """
        try:
            response = self.session.get(url, timeout=15)
        except Exception as exc:
            logger.warning('[nk] Request failed for %s: %s', url[:80], exc)
            return _ERROR, None, False
        kind = self._status_outcome(url, response)
        if kind:
            return kind, None, False
        return self._read_product_page(url, response)

    def _status_outcome(self, url, response):
        """
        Classify a response from its status, size and final address alone.

        Returns an outcome, or None when the page looks like a real product page
        that still has to be read.
        """
        status = response.status_code
        if status == 404:
            logger.warning('[nk] 404 for %s — URL may be stale', url[:80])
            return _NOT_FOUND
        if status in (403, 429, 503):
            logger.warning('[nk] HTTP %d for %s — looks like a block', status, url[:80])
            return _BLOCKED
        if status != 200:
            logger.debug('[nk] HTTP %d for %s', status, url[:80])
            return _ERROR
        # Guard against bot-detection pages (e.g. Cloudflare CAPTCHA) that
        # return HTTP 200 but contain no product content.  Real product pages
        # are always much larger than the minimum threshold.
        if len(response.content) < _MIN_PAGE_BYTES:
            logger.warning(
                '[nk] Suspiciously short response (%d bytes) for %s — likely bot-detection',
                len(response.content), url[:80],
            )
            return _BLOCKED
        if self._landed_off_product_page(url, response):
            return _DEAD_LINK
        return None

    def _read_product_page(self, url, response):
        """Read price and stock from a page already known to be a product page."""
        soup = BeautifulSoup(response.text, 'html.parser')

        # Secondary bot-detection: check page title for Cloudflare challenge signals.
        # Do NOT check full page text for 'captcha' — NK pages legitimately include
        # this word in Cloudflare footer/script text, causing false positives.
        title_lower = (soup.title.string or '').lower() if soup.title else ''
        page_text_lower = soup.get_text().lower()
        bot_signals = (
            'just a moment' in title_lower
            or 'access denied' in title_lower
            or 'attention required' in title_lower
            or 'checking your browser' in page_text_lower
            or 'access denied' in page_text_lower
        )
        if bot_signals:
            logger.warning('[nk] Bot-detection challenge detected for %s', url[:80])
            return _BLOCKED, None, False

        price = self._extract_price(soup)
        if price is None:
            # Page loaded cleanly but no price present — confirmed unavailable.
            return _NO_PRICE, None, False
        return _OK, price, self._extract_in_stock(soup)

    @staticmethod
    def _landed_off_product_page(requested_url, response):
        """
        True when a /P/ product link was answered by a different kind of page.

        Noble Knight sends delisted products to its homepage with a normal 200
        response, and the homepage shows prices of its own.  Only the shape of
        the final address is checked (it no longer starts with /P/); the product
        number is not compared, so products that share one Noble Knight page are
        not affected.
        """
        if not urlparse(requested_url).path.lower().startswith('/p/'):
            return False
        final_url = str(getattr(response, 'url', '') or requested_url)
        return not urlparse(final_url).path.lower().startswith('/p/')

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
            # Sale listings read "Was old price: $138.95 New Price $117.95":
            # the CURRENT price is the amount after "New Price", not the
            # first dollar amount (which is the old price).
            m = re.search(r'New Price\s*\$\s*(\d{1,4}\.\d{2})', text, re.IGNORECASE)
            if m is None:
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
