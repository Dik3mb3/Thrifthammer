"""
Management command: update_gw_prices

Re-fetches the current price from each tracked product's own Games
Workshop US product page and updates both the games-workshop CurrentPrice
and Product.msrp when the price has changed.

LOCAL-ONLY, run by hand -- do NOT wire this into a GitHub Actions
workflow or the Procfile. GW's site runs AWS WAF Bot Control, which
blocks plain HTTP requests and Playwright's own bundled headless
Chromium alike (both were tested and both get served a "Human
Verification" challenge page). What actually gets through -- proven by
this project's existing scrape_amazon_browser.py script, which hits the
exact same class of bot protection on Amazon -- is launching your real,
locally-installed Chrome (not Playwright's bundled browser) in a
visible, non-headless window from your own residential connection. Both
the "real browser" and "residential IP" parts matter; a datacenter IP
(GitHub Actions, this sandbox) gets challenged regardless of browser.

This is also not meant to be scheduled at all -- GW retail prices change
only a handful of times a year (not daily like eBay/Amazon listings), so
run it by hand whenever a price rise is noticed.

Requires Playwright, which is NOT in requirements.txt (kept out on
purpose so it isn't installed on every Railway deploy or CI job for a
command nothing else depends on). One-time local setup:

    pip install playwright
    playwright install    # installs the driver; Chrome itself must already be installed

Usage:
    python manage.py update_gw_prices                    # all tracked GW US products
    python manage.py update_gw_prices --dry-run           # preview only
    python manage.py update_gw_prices --sku 48-75         # single product
    python manage.py update_gw_prices --skus "48-75,53-23"
    python manage.py update_gw_prices --batch-tag skaven
    python manage.py update_gw_prices --limit 50
    python manage.py update_gw_prices --delay 3.0
    python manage.py update_gw_prices --headless          # not recommended -- more likely to be challenged
"""

import decimal
import json
import os
import re
import time

# Playwright's sync API runs its real (async) implementation on a background
# thread bridged via greenlet, which can make Django's SynchronousOnlyOperation
# check (django.utils.asyncio.async_unsafe) false-positive on ordinary,
# sequential .save() calls made from this command -- there's no actual
# concurrent/async DB access happening here, just Playwright's own internal
# threading confusing the detection. Must be set before any ORM call runs,
# so it's set here at import time, before Command.handle() does anything.
os.environ.setdefault('DJANGO_ALLOW_ASYNC_UNSAFE', 'true')

from django.core.management.base import BaseCommand, CommandError
from django.db import Error as DjangoDBError
from django.db import connection

from prices.models import CurrentPrice

USER_AGENT = (
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
    '(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36'
)


class Command(BaseCommand):
    """Re-check GW US product page prices; update CurrentPrice + Product.msrp on change."""

    help = 'Re-check GW US product page prices and update CurrentPrice + Product.msrp when changed. Run locally only -- see docstring.'

    def add_arguments(self, parser):
        """Register command-line options."""
        parser.add_argument(
            '--dry-run', action='store_true', default=False,
            help='Show results without saving to the database.',
        )
        parser.add_argument(
            '--delay', type=float, default=3.0, metavar='SECONDS',
            help='Delay between requests in seconds (default: 3.0).',
        )
        parser.add_argument(
            '--sku', type=str, default=None, metavar='GW_SKU',
            help='Only check one product by gw_sku (e.g. 48-75).',
        )
        parser.add_argument(
            '--skus', type=str, default=None, metavar='SKUS',
            help='Comma-separated GW SKUs to check (e.g. "48-75,53-23").',
        )
        parser.add_argument(
            '--batch-tag', type=str, default=None, metavar='TAG',
            help='Only check products with this batch_tag.',
        )
        parser.add_argument(
            '--category', type=str, default=None, metavar='NAME',
            help='Filter to products in a category / game system (case-insensitive, '
                 'partial match -- e.g. "40" matches "Warhammer 40,000", '
                 '"sigmar" matches "Age of Sigmar").',
        )
        parser.add_argument(
            '--limit', type=int, default=None, metavar='N',
            help='Cap the number of products checked (useful for spot-checking).',
        )
        parser.add_argument(
            '--skip', type=int, default=0, metavar='N',
            help='Skip the first N products in the filtered/ordered list -- '
                 'use to resume a run that was interrupted partway through '
                 '(e.g. "[739/824]" in the output means 738 already completed, '
                 'so --skip 738 resumes at #739).',
        )
        parser.add_argument(
            '--headless', action='store_true', default=False,
            help='Run without a visible browser window. Not recommended -- '
                 'GW\'s bot protection is more likely to challenge a headless run.',
        )

    def handle(self, *args, **options):
        """Main entry point -- fetch each tracked GW page and reconcile the price."""
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            raise CommandError(
                'Playwright is not installed. This command is local-only:\n'
                '  pip install playwright\n'
                '  playwright install chromium'
            )

        self.dry_run = options['dry_run']
        self.delay = options['delay']

        qs = (
            CurrentPrice.objects
            .filter(retailer__slug='games-workshop', manual_url_override=False)
            .exclude(url='')
            .select_related('product')
            .order_by('product__gw_sku')
        )

        sku_filter = (options['sku'] or '').strip()
        skus_filter = [s.strip() for s in (options['skus'] or '').split(',') if s.strip()]
        batch_tag = (options['batch_tag'] or '').strip()
        category = (options['category'] or '').strip()

        if sku_filter:
            qs = qs.filter(product__gw_sku=sku_filter)
        elif skus_filter:
            qs = qs.filter(product__gw_sku__in=skus_filter)
        if batch_tag:
            qs = qs.filter(product__batch_tag=batch_tag)
        if category:
            qs = qs.filter(product__category__name__icontains=category)

        skip = options['skip'] or 0
        total = qs.count()
        records = list(qs[skip:skip + options['limit']]) if options['limit'] else list(qs[skip:])

        self.stdout.write('\nGW US Price Check (Playwright, local run)')
        self.stdout.write('=' * 50)
        self.stdout.write(f'  Dry run     : {self.dry_run}')
        self.stdout.write(f'  Delay       : {self.delay}s between requests')
        if skip:
            self.stdout.write(f'  Skip        : {skip} (resuming)')
        if category:
            self.stdout.write(f'  Category    : {category}')
        self.stdout.write(f'  Products    : {len(records)} of {total}')
        self.stdout.write('=' * 50 + '\n')

        changed = unchanged = not_found = challenged = no_price = errored = 0

        with sync_playwright() as pw:
            # channel='chrome' launches the real, locally-installed Chrome
            # rather than Playwright's own bundled Chromium -- this is the
            # part that actually gets past GW's bot protection (see docstring).
            browser = pw.chromium.launch(channel='chrome', headless=options['headless'])
            context = browser.new_context(
                viewport={'width': 1280, 'height': 900},
                user_agent=USER_AGENT,
            )
            page = context.new_page()

            for idx, cp in enumerate(records, 1):
                i = skip + idx
                product = cp.product
                if idx > 1:
                    time.sleep(self.delay)

                status, html = self._fetch(page, cp.url)

                if status == 'not_found':
                    self.stdout.write(
                        f'  [{i}/{total}] {product.gw_sku} {product.name} '
                        f'-- GW no longer has this page (404). Skipping -- '
                        f'product and its last known price are untouched.'
                    )
                    not_found += 1
                    continue

                if status == 'challenged':
                    self.stdout.write(self.style.WARNING(
                        f'  [{i}/{total}] {product.gw_sku} {product.name} '
                        f'-- blocked by GW\'s bot challenge, skipping this run.'
                    ))
                    challenged += 1
                    continue

                if status == 'error' or html is None:
                    self.stdout.write(self.style.ERROR(
                        f'  [{i}/{total}] {product.gw_sku} {product.name} '
                        f'-- request failed, skipping this run.'
                    ))
                    errored += 1
                    continue

                new_price = self._extract_price(html)
                if new_price is None:
                    self.stdout.write(self.style.WARNING(
                        f'  [{i}/{total}] {product.gw_sku} {product.name} '
                        f'-- page loaded but no price could be parsed from it.'
                    ))
                    no_price += 1
                    continue

                if cp.price == new_price:
                    unchanged += 1
                    continue

                self.stdout.write(
                    f'  [{i}/{total}] {product.gw_sku} {product.name}: '
                    f'${cp.price} -> ${new_price}'
                )
                changed += 1
                if not self.dry_run:
                    try:
                        self._save_price(cp, product, new_price)
                    except DjangoDBError as exc:
                        # A run this long can outlast an idle Postgres
                        # connection -- Railway drops it silently rather
                        # than erroring until the next query is attempted.
                        # Reconnect and retry this one save instead of
                        # losing the rest of the run.
                        self.stdout.write(self.style.WARNING(
                            f'    DB connection dropped ({exc}); reconnecting and retrying...'
                        ))
                        connection.close()
                        try:
                            self._save_price(cp, product, new_price)
                        except DjangoDBError as exc2:
                            self.stdout.write(self.style.ERROR(
                                f'    Still failed to save {product.gw_sku} after '
                                f'reconnecting: {exc2}. Re-run this SKU with --sku.'
                            ))
                            changed -= 1
                            errored += 1

            browser.close()

        self.stdout.write(
            f'\nDone -- changed: {changed} | unchanged: {unchanged} | '
            f'not found (404 on GW): {not_found} | still challenged: {challenged} | '
            f'no price parsed: {no_price} | errors: {errored}'
        )
        if challenged:
            self.stdout.write(self.style.WARNING(
                f'{challenged} product(s) hit GW\'s bot challenge and were skipped -- '
                f're-run later or re-run just those SKUs with --skus.'
            ))
        if self.dry_run and changed:
            self.stdout.write(self.style.WARNING('Dry run -- no changes were saved.'))

    # ------------------------------------------------------------------
    # Save + fetch/parsing helpers
    # ------------------------------------------------------------------

    def _save_price(self, cp, product, new_price):
        """Persist a changed price to both CurrentPrice and Product.msrp."""
        cp.price = new_price
        cp.save(update_fields=['price'])
        # GW's own listed price IS the MSRP -- keep the static fallback
        # field in sync so it never drifts stale again.
        product.msrp = new_price
        product.save(update_fields=['msrp'])

    def _fetch(self, page, url, retries=1):
        """
        Load a URL in the shared Playwright page.

        Returns (status, html) where status is one of:
          'ok'         -- real page loaded, html has the content
          'not_found'  -- GW returned a genuine 404 (product delisted on
                           their end) -- distinct from a bot challenge so
                           the caller can report it plainly and move on;
                           nothing about the product itself is touched.
          'challenged' -- GW's bot protection served a "Human
                           Verification" page instead of the product
          'error'      -- request/navigation failed outright
        """
        for attempt in range(1 + retries):
            try:
                resp = page.goto(url, timeout=30000, wait_until='domcontentloaded')
                page.wait_for_timeout(2500)  # let the WAF challenge / price widget settle
                content = page.content()

                if resp and resp.status == 404:
                    return 'not_found', content

                if 'window.gokuProps' in content or (resp and resp.status == 202):
                    self.stdout.write(self.style.WARNING(
                        f'    Still challenged by GW\'s bot protection for {url} '
                        f'(attempt {attempt + 1}/{1 + retries}).'
                    ))
                    if attempt < retries:
                        time.sleep(self.delay * 2)
                        continue
                    return 'challenged', None

                return 'ok', content
            except Exception as exc:
                self.stdout.write(self.style.WARNING(
                    f'    Failed to load {url}: {exc} (attempt {attempt + 1}/{1 + retries}).'
                ))
                if attempt < retries:
                    time.sleep(self.delay * 2)
        return 'error', None

    def _extract_price(self, html):
        """
        Parse the current price out of a GW product page.

        Tries JSON-LD structured data first (most reliable), then falls
        back to common price CSS selectors -- same approach already
        proven in import_gw_catalog.py's one-time scraper.
        """
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, 'html.parser')

        for script in soup.find_all('script', type='application/ld+json'):
            try:
                data = json.loads(script.string or '{}')
            except Exception:
                continue
            offers = data.get('offers') if isinstance(data, dict) else None
            if offers:
                if isinstance(offers, list):
                    offers = offers[0]
                raw = str(offers.get('price', '') or offers.get('lowPrice', ''))
                if raw:
                    price = self._to_decimal(raw)
                    if price is not None:
                        return price

        for selector in (
            '[class*="product-price"]',
            '[class*="productPrice"]',
            '[class*="price--main"]',
            '[itemprop="price"]',
            '[class*="price"]',
        ):
            el = soup.select_one(selector)
            if el:
                content = el.get('content', '') or el.get_text(strip=True)
                match = re.search(r'[\d,]+\.?\d*', content.replace(',', ''))
                if match:
                    price = self._to_decimal(match.group())
                    if price is not None:
                        return price

        return None

    @staticmethod
    def _to_decimal(raw):
        """Best-effort string-to-Decimal conversion; returns None on failure."""
        try:
            return decimal.Decimal(raw.replace(',', '')).quantize(decimal.Decimal('0.01'))
        except decimal.InvalidOperation:
            return None
