"""
Firestorm Games UK scraper — URL-based approach (mirrors Noble Knight).

For each active product that has a Firestorm Games URL already stored in
CurrentPrice (seeded via the seed_firestorm_games_*_prices.py commands),
fetches that exact product page and refreshes price + stock only. Never
searches, never matches by name/SKU, never creates a CurrentPrice row or a
Product that doesn't already exist -- if a product has no stored Firestorm
URL, it is skipped entirely.

Price extraction:
    Firestorm renders the live price as:
        <h3 class="price orange">Our Price: £47.96</h3>
    This is always the sale price (never the struck-through RRP, which
    appears separately in a "roundel special" badge) -- matches the parsing
    rule already established in the seed commands.

Stock detection:
    - In stock  → an "ADD TO CART" link (class "btnAddToBasket") is present
      and the page contains no explicit out-of-stock text.
    - Out of stock → the add-to-basket link is absent, OR the page contains
      "out of stock" / "sold out" / "notify me" / "coming soon".

Usage:
    python manage.py run_scrapers firestorm-games
    python manage.py run_scrapers firestorm-games --shard 3/7 --limit 500

Notes:
  - Only processes CurrentPrice rows that already have a Firestorm URL.
  - Failure modes mirror Noble Knight to prevent over-blanking:
      * Network error / non-200 / Cloudflare challenge → the existing price is
        PRESERVED (scrape failure != out of stock).
      * Successful 200 response but no price found → the price is blanked and
        in_stock set to False (product genuinely delisted on Firestorm).
  - A 404 is reported as a stale link and is not retried.  A blocked response
    (403 / 429 / challenge page) is not retried either, and several in a row
    stop the run so the site is not hammered while it is refusing us.
  - Blanking is held back until the end of the run and only applied when the
    number of blanks is believable (see scrapers/safeguards.py).
  - Firestorm's Cloudflare turns away GitHub-hosted runners, so this scraper is
    meant to be run by hand from a normal connection, in slices (--shard).
  - The stored URL keeps its ?aff= affiliate tag; that tag is stripped only
    from the outgoing scrape request so bot traffic doesn't pollute
    Firestorm's affiliate analytics (same reasoning as Noble Knight's
    ?awid= stripping).
  - Polite 1.5s delay + 0-1s jitter between requests.
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

FIRESTORM_DOMAIN = 'firestormgames.co.uk'

DEFAULT_DELAY = 1.5
JITTER_MAX = 1.0

# Sentinel returned by _fetch_price when the page could not be retrieved
# (network error, non-200 HTTP status, Cloudflare challenge, etc.). Distinct
# from None ("page loaded but no price found") so callers preserve the
# existing price instead of erroneously blanking it.
_FETCH_ERROR = object()

# Cloudflare challenge pages are typically very short.
_MIN_PAGE_BYTES = 5_000

_OUT_OF_STOCK_SIGNALS = (
    'out of stock',
    'sold out',
    'notify me',
    'coming soon',
)

# Outcomes of one page fetch (see FirestormGamesUKScraper._fetch_page).
_OK = 'ok'                # price and stock read from a product page
_NO_PRICE = 'no_price'    # a real page that shows no price
_NOT_FOUND = 'not_found'  # HTTP 404
_BLOCKED = 'blocked'      # 403 / 429 / 503, a challenge page or a too-short page
_ERROR = 'error'          # network failure or any other server error


def _strip_affiliate_params(url):
    """
    Remove the ?aff= affiliate tracking param from a Firestorm URL before
    fetching. The tag stays in the DB so user-facing links still earn
    commission, but scraper requests shouldn't count against it.
    """
    parsed = urlparse(url)
    params = parse_qs(parsed.query, keep_blank_values=True)
    params.pop('aff', None)
    new_query = urlencode({k: v[0] for k, v in params.items()})
    return urlunparse(parsed._replace(query=new_query))


class FirestormGamesUKScraper:
    """
    Scraper for Firestorm Games (firestormgames.co.uk).

    Fetches live prices from stored Firestorm product page URLs and updates
    CurrentPrice records. Never matches by name/SKU and never creates new
    Products or CurrentPrice rows -- only refreshes rows that already exist.
    """

    retailer_slug = 'firestorm-games'

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
            'Accept-Language': 'en-GB,en;q=0.9',
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
        Refresh Firestorm Games prices for products with a stored URL.

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
            if FIRESTORM_DOMAIN not in entry.url:
                logger.debug('[firestorm] Skipping non-Firestorm URL for %s: %s', entry.product.name, entry.url)
                continue

            job.products_found += 1
            try:
                self._refresh_entry(entry, job, guard, errors)
            except Exception as exc:
                errors.append(f'{entry.product.name} ({entry.product.gw_sku}): {exc}')
                logger.exception('[firestorm] Error scraping %s', entry.product.name)
                note_crash(guard)

            time.sleep(self.delay + random.uniform(0, JITTER_MAX))

        finish_run(job, guard, errors, 'firestorm')
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
        kind, price, in_stock = self._fetch_with_retries(_strip_affiliate_params(entry.url))

        if kind == _OK:
            entry.price = price
            entry.in_stock = in_stock
            entry.not_available = False
            entry.save(update_fields=['price', 'in_stock', 'not_available', 'last_seen'])
            guard.record_ok(was_priced)
            job.prices_updated += 1
            logger.info(
                '[firestorm] [updated] %s — £%.2f  %s',
                product.name, price, 'in stock' if in_stock else 'OUT OF STOCK',
            )
        elif kind == _NO_PRICE:
            guard.record_ok(was_priced)
            logger.warning('[firestorm] [no price] %s — queued for blanking: %s', product.name, entry.url[:80])
            if was_priced:
                guard.defer_blank(entry, 'no price on the page')
            else:
                entry.save(update_fields=['last_seen'])
        elif kind == _NOT_FOUND:
            guard.record_ok()
            errors.append(f'[stale-link] {product.name} ({product.gw_sku}): {entry.url}')
        elif kind == _BLOCKED:
            guard.record_failure(blocked=True)
            logger.warning('[firestorm] [blocked] %s — price left unchanged: %s', product.name, entry.url[:80])
        else:
            guard.record_failure()
            logger.warning('[firestorm] [fetch-failed] %s — price left unchanged: %s', product.name, entry.url[:80])

    def _fetch_with_retries(self, url):
        """
        Fetch a page, retrying network and server errors twice with a back-off.

        A 404, a block and a "no price" answer are not retried.
        """
        kind, price, in_stock = self._fetch_page(url)
        if kind == _ERROR:
            time.sleep(self.delay + random.uniform(0.5, 1.0))
            kind, price, in_stock = self._fetch_page(url)
        if kind == _ERROR:
            time.sleep(self.delay * 1.5 + random.uniform(0.5, 1.5))
            kind, price, in_stock = self._fetch_page(url)
        return kind, price, in_stock

    # -------------------------------------------------------------------------
    # Price extraction
    # -------------------------------------------------------------------------

    def _fetch_price(self, url):
        """
        GET a Firestorm Games product page and extract the price.

        Return values:
            (Decimal price, bool in_stock)  — price extracted successfully
            None                            — page loaded (200) but no price
                                              found; product is confirmed
                                              unavailable or delisted
            _FETCH_ERROR                    — could not load the page at all
                                              (network error, non-200 status,
                                              or Cloudflare challenge);
                                              caller should preserve existing
                                              price rather than blanking it

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
        GET a Firestorm Games product page.

        Returns ``(kind, price, in_stock)`` where ``kind`` is one of the
        module-level outcomes (_OK, _NO_PRICE, _NOT_FOUND, _BLOCKED, _ERROR);
        price and in_stock are only meaningful for _OK.
        """
        try:
            response = self.session.get(url, timeout=15)
        except Exception as exc:
            logger.warning('[firestorm] Request failed for %s: %s', url[:80], exc)
            return _ERROR, None, False
        kind = self._status_outcome(url, response)
        if kind:
            return kind, None, False
        return self._read_product_page(url, response)

    @staticmethod
    def _status_outcome(url, response):
        """
        Classify a response from its status and size alone.

        Returns an outcome, or None when the page looks like a real product page
        that still has to be read.
        """
        status = response.status_code
        if status == 404:
            logger.warning('[firestorm] 404 for %s — URL may be stale', url[:80])
            return _NOT_FOUND
        if status in (403, 429, 503):
            logger.warning('[firestorm] HTTP %d for %s — looks like a block', status, url[:80])
            return _BLOCKED
        if status != 200:
            logger.debug('[firestorm] HTTP %d for %s', status, url[:80])
            return _ERROR
        # Guard against Cloudflare challenge pages that return HTTP 200 but
        # contain no product content. Real product pages are always much
        # larger than the minimum threshold.
        if len(response.content) < _MIN_PAGE_BYTES:
            logger.warning(
                '[firestorm] Suspiciously short response (%d bytes) for %s — likely bot-detection',
                len(response.content), url[:80],
            )
            return _BLOCKED
        return None

    def _read_product_page(self, url, response):
        """Read price and stock from a page already known to be a product page."""
        soup = BeautifulSoup(response.text, 'html.parser')

        title_lower = (soup.title.string or '').lower() if soup.title else ''
        page_text_lower = soup.get_text().lower()
        bot_signals = (
            'just a moment' in title_lower
            or 'attention required' in title_lower
            or 'checking your browser' in page_text_lower
            or 'access denied' in page_text_lower
        )
        if bot_signals:
            logger.warning('[firestorm] Bot-detection challenge detected for %s', url[:80])
            return _BLOCKED, None, False

        price = self._extract_price(soup)
        if price is None:
            return _NO_PRICE, None, False
        return _OK, price, self._extract_in_stock(soup, page_text_lower)

    @staticmethod
    def _extract_price(soup):
        """
        Extract the live sale price from a Firestorm product page.

        Firestorm renders: <h3 class="price orange">Our Price: £47.96</h3>
        This is always the discounted sale price, never the struck-through
        RRP (which lives in a separate "roundel special" badge). Returns
        Decimal or None.
        """
        for el in soup.select('.price'):
            text = el.get_text(' ', strip=True)
            m = re.search(r'Our Price:?\s*£\s*(\d{1,4}\.\d{2})', text, re.IGNORECASE)
            if m:
                try:
                    price = Decimal(m.group(1))
                    if 1 <= price <= 2000:
                        return price
                except InvalidOperation:
                    pass
        return None

    @staticmethod
    def _extract_in_stock(soup, page_text_lower):
        """
        Determine whether the product is currently in stock.

        In stock  → an "ADD TO CART" link (class "btnAddToBasket") exists.
        Out of stock → the link is absent, OR the page contains an explicit
        out-of-stock signal ("out of stock", "sold out", "notify me",
        "coming soon").
        """
        for signal in _OUT_OF_STOCK_SIGNALS:
            if signal in page_text_lower:
                return False

        add_to_cart = soup.select_one('.btnAddToBasket')
        return add_to_cart is not None
