"""
Management command: update_amazon_prices_keepa

Fetches current Amazon prices via the Keepa API and updates CurrentPrice records.

WHY KEEPA INSTEAD OF DIRECT SCRAPING
─────────────────────────────────────
Amazon blocks all datacenter IP ranges (AWS, Google Cloud, Azure).  Direct
scraping from GitHub Actions, Railway, or any cloud server returns CAPTCHA
or auth-redirect pages 100% of the time.  Residential proxies that bypass
this cost $100-500/month.

Keepa (keepa.com) is a long-established Amazon price tracking service with
legitimate Amazon access.  Their REST API returns current prices for any
ASIN — no scraping, no blocks, works from any IP including GitHub Actions.

FREE TIER — setup steps
────────────────────────
1. Create a free account at https://keepa.com/#!api
2. The free plan gives 1000 tokens/day.
3. Each product lookup costs 1 token (we batch 100 ASINs per request for
   efficiency, still 1 token per product in the batch).
4. 375 products/week = ~54 products/day → well within the free tier.
5. Add your API key as:
     - GitHub secret:   KEEPA_API_KEY
     - Railway env var: KEEPA_API_KEY
6. Run via GitHub Actions (scrape-amazon.yml) or Railway Cron.

PRICE TYPES USED
────────────────
Keepa price type 0 = sold by Amazon.com directly.
Keepa price type 1 = new condition from any marketplace seller.
Logic: prefer Amazon's own price (type 0); fall back to marketplace new
(type 1) if Amazon doesn't stock it directly.  -1 = out of stock or
not available at that seller type.  Keepa prices are in US cents.

Usage:
    python manage.py update_amazon_prices_keepa
    python manage.py update_amazon_prices_keepa --dry-run   # preview, no writes
"""

import logging
import os
import re
import time
from decimal import Decimal, InvalidOperation

import requests
from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Retailer

logger = logging.getLogger(__name__)

KEEPA_API_URL   = 'https://api.keepa.com/product'
KEEPA_DOMAIN    = 1          # amazon.com
KEEPA_BATCH_MAX = 100        # Keepa allows up to 100 ASINs per request
KEEPA_DELAY     = 1.5        # seconds between batch requests (polite crawling)

ASIN_RE = re.compile(r'/dp/([A-Z0-9]{10})')


def _extract_asin(url):
    """Return the 10-char ASIN from an Amazon URL, or None if not found."""
    m = ASIN_RE.search(url or '')
    return m.group(1) if m else None


def _keepa_price_to_decimal(cents):
    """
    Convert a Keepa price integer to Decimal dollars.

    Keepa returns -1 for 'not available' and positive integers for prices
    in US cents (e.g. 13300 → $133.00).

    Returns Decimal price, or None if not available.
    """
    if cents is None or cents < 0:
        return None
    try:
        return Decimal(cents) / 100
    except InvalidOperation:
        return None


def _fetch_keepa_batch(asins, api_key):
    """
    Call the Keepa API for a batch of up to 100 ASINs.

    Returns a dict mapping ASIN → (price: Decimal, in_stock: bool).
    ASINs for which no data is returned are omitted from the result.

    Keepa stats.current layout (price type indices):
      0  Amazon.com (sold by Amazon directly)
      1  New, any marketplace seller
      2  Used, any marketplace seller
      ...
    We use type-0 first; fall back to type-1 if type-0 is -1.
    """
    asin_param = ','.join(asins)
    try:
        response = requests.get(
            KEEPA_API_URL,
            params={
                'key':     api_key,
                'domain':  KEEPA_DOMAIN,
                'asin':    asin_param,
                'stats':   1,     # include stats.current
                'offers':  0,     # no marketplace offer details needed
                'history': 0,     # no price history CSV needed
            },
            timeout=30,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        logger.error('[keepa] API request failed: %s', exc)
        return {}

    try:
        data = response.json()
    except ValueError:
        logger.error('[keepa] Non-JSON response from API')
        return {}

    remaining = data.get('tokensLeft', '?')
    logger.info('[keepa] Tokens remaining after batch: %s', remaining)

    results = {}
    for product in data.get('products') or []:
        asin = product.get('asin')
        if not asin:
            continue

        stats   = product.get('stats') or {}
        current = stats.get('current') or []

        # Pull type-0 (Amazon direct) and type-1 (marketplace new)
        type0 = current[0] if len(current) > 0 else -1
        type1 = current[1] if len(current) > 1 else -1

        if type0 and type0 > 0:
            price_cents = type0
        elif type1 and type1 > 0:
            price_cents = type1
        else:
            price_cents = -1

        price    = _keepa_price_to_decimal(price_cents)
        in_stock = price is not None

        results[asin] = (price, in_stock)

    return results


class Command(BaseCommand):
    """Update Amazon CurrentPrice records using the Keepa API."""

    help = (
        'Fetches current Amazon prices via the Keepa API and updates '
        'CurrentPrice records.  Requires KEEPA_API_KEY env var.  Idempotent.'
    )

    def add_arguments(self, parser):
        """Register optional flags."""
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be updated without writing to the database.',
        )

    def handle(self, *args, **options):
        """Entry point — fetch prices and update the DB."""
        dry_run = options['dry_run']

        api_key = os.environ.get('KEEPA_API_KEY', '').strip()
        if not api_key:
            self.stderr.write(self.style.ERROR(
                'KEEPA_API_KEY environment variable is not set.  '
                'Get a free API key at https://keepa.com/#!api'
            ))
            return

        try:
            retailer = Retailer.objects.get(slug='amazon')
        except Retailer.DoesNotExist:
            self.stderr.write(self.style.ERROR('Amazon retailer not found in DB.'))
            return

        # Collect all CurrentPrice rows that have an Amazon URL.
        entries = list(
            CurrentPrice.objects
            .filter(retailer=retailer)
            .exclude(url='')
            .exclude(url__isnull=True)
            .select_related('product')
        )

        # Build ASIN → entry mapping.  Skip non-Amazon URLs and inactive products.
        asin_to_entry = {}
        skipped_no_asin = 0
        for entry in entries:
            if not entry.product.is_active:
                continue
            asin = _extract_asin(entry.url)
            if not asin:
                logger.debug(
                    '[keepa] No ASIN found in URL for %s: %s',
                    entry.product.name, entry.url,
                )
                skipped_no_asin += 1
                continue
            asin_to_entry[asin] = entry

        all_asins = list(asin_to_entry.keys())
        self.stdout.write(
            f'Found {len(all_asins)} products with Amazon ASINs '
            f'({skipped_no_asin} skipped — no ASIN in URL).'
        )

        if not all_asins:
            self.stdout.write('Nothing to do.')
            return

        updated   = 0
        unchanged = 0
        no_price  = 0

        # Process in batches of KEEPA_BATCH_MAX.
        for batch_start in range(0, len(all_asins), KEEPA_BATCH_MAX):
            batch = all_asins[batch_start:batch_start + KEEPA_BATCH_MAX]
            batch_num = batch_start // KEEPA_BATCH_MAX + 1
            total_batches = (len(all_asins) + KEEPA_BATCH_MAX - 1) // KEEPA_BATCH_MAX

            self.stdout.write(
                f'  Batch {batch_num}/{total_batches} — {len(batch)} ASINs …'
            )

            price_map = _fetch_keepa_batch(batch, api_key)

            for asin in batch:
                entry   = asin_to_entry[asin]
                product = entry.product

                if asin not in price_map:
                    logger.warning(
                        '[keepa] No data returned for %s (%s)',
                        product.name, asin,
                    )
                    no_price += 1
                    continue

                new_price, new_in_stock = price_map[asin]

                if new_price is None:
                    # Keepa says not available at any price type.
                    if not entry.not_available:
                        if not dry_run:
                            entry.not_available = True
                            entry.in_stock = False
                            entry.save(update_fields=['not_available', 'in_stock'])
                        self.stdout.write(
                            f'    [{"dry" if dry_run else "updated"}] '
                            f'{product.name} — marked not_available'
                        )
                        updated += 1
                    else:
                        unchanged += 1
                    continue

                price_changed     = entry.price != new_price
                in_stock_changed  = entry.in_stock != new_in_stock
                was_not_available = entry.not_available

                if price_changed or in_stock_changed or was_not_available:
                    old_price = entry.price
                    if not dry_run:
                        entry.price         = new_price
                        entry.in_stock      = new_in_stock
                        entry.not_available = False
                        entry.save(update_fields=['price', 'in_stock', 'not_available'])
                    self.stdout.write(self.style.SUCCESS(
                        f'    [{"dry" if dry_run else "updated"}] '
                        f'{product.name} — '
                        f'${old_price} → ${new_price}  '
                        f'{"in stock" if new_in_stock else "OUT OF STOCK"}'
                    ))
                    updated += 1
                else:
                    logger.debug(
                        '[keepa] No change: %s — $%s', product.name, new_price,
                    )
                    unchanged += 1

            if batch_start + KEEPA_BATCH_MAX < len(all_asins):
                time.sleep(KEEPA_DELAY)

        self.stdout.write(self.style.SUCCESS(
            f'\nDone.  '
            f'{updated} updated, {unchanged} unchanged, {no_price} no data from Keepa.'
        ))
