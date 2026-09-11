"""
Management command: update_amazon_book_prices

Refreshes existing Amazon BookFormatPrice records (Paperback/Hardback/
E-Book/Audio Book) via the official Creators API.

Sibling to update_amazon_creators_prices.py rather than an extension of it:
BookFormatPrice is a deliberately separate model from CurrentPrice (see
BookFormatPrice's docstring in prices/models.py) so the shared, heavily-used
CurrentPrice table used by every other product on the site is untouched by
the Books feature. Keeping the refresh commands separate preserves that
same isolation.

Safety rules (same as update_amazon_creators_prices.py):
  - BookFormatPrice entries with manual_url_override=True are NEVER touched.
  - Uses .save() not QuerySet.update() so cache-invalidation signals fire
    (if/when BookFormatPrice gets its own signal handlers -- for now the
    GitHub Action's separate "clear cache" step covers this either way).
  - Dry run (--dry-run) prints what would change without writing to DB.
  - Backup (--backup) dumps all current Amazon BookFormatPrice records to
    JSON before any writes.

Audio Book has an extra wrinkle, same one find_amazon_book_asins.py
documents: Audible listings commonly carry TWO "New" offers sharing the
same list price -- a $0.00 "free with trial" offer (usually the Buy Box
winner) and the real cash "Buy Now" price. The shared client's
get_items()/get_items_batched() take the first "New" listing (Buy Box
priority order) via AmazonCreatorsClient._extract_price(), which would
silently overwrite a real price with $0.00 for audiobooks. That shared
method is intentionally NOT modified here (it's relied on by the working
miniatures CurrentPrice refresh pipeline) -- instead, Audio Book ASINs are
looked up via a separate raw batched GetItems call with trial-price-skipping
logic, while Paperback/Hardback/E-Book ASINs use the normal shared method.

Usage:
  python manage.py update_amazon_book_prices --dry-run
  python manage.py update_amazon_book_prices
  python manage.py update_amazon_book_prices --faction horus-heresy-series
  python manage.py update_amazon_book_prices --format audiobook
  python manage.py update_amazon_book_prices --backup
"""

import json
import time
from datetime import datetime
from decimal import Decimal

import requests
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import InterfaceError, OperationalError, connection

from prices.models import BookFormatPrice
from products.models import Category, Faction, Retailer
from scrapers.retailers.amazon_creators import (
    AmazonCreatorsClient, _API_BASE, _BATCH_SIZE, _ITEMS_PATH, extract_asin,
)

_TRIAL_PRICE_THRESHOLD = 1.00  # Audible "free with trial" offers price at $0.00
_CALL_DELAY = 1.1  # seconds between API calls — keeps us under 1 TPS

_FORMAT_ALIASES = {
    'paperback': BookFormatPrice.FORMAT_SOFTBACK,
    'hardback': BookFormatPrice.FORMAT_HARDBACK,
    'ebook': BookFormatPrice.FORMAT_EBOOK,
    'audiobook': BookFormatPrice.FORMAT_AUDIOBOOK,
}


def _best_audiobook_price(item):
    """
    Real "Buy Now" price from a raw GetItems result item, skipping the $0.00
    trial offer.

    Returns a Decimal built via str(amount) -- not float(amount) -- to match
    AmazonCreatorsClient._extract_price()'s conversion exactly. Comparing a
    plain float to the Decimal already stored on the model (entry.price)
    produces false "changed" detections from binary floating-point
    representation error (e.g. Decimal('14.10') != 14.10 as a raw float).
    """
    listings = item.get('offersV2', {}).get('listings', [])
    for listing in listings:
        if listing.get('condition', {}).get('value', 'New') != 'New':
            continue
        amount = listing.get('price', {}).get('money', {}).get('amount')
        if amount is not None and amount >= _TRIAL_PRICE_THRESHOLD:
            return Decimal(str(amount))
    return None


class Command(BaseCommand):
    """Update Amazon BookFormatPrice records via the Creators API."""

    help = 'Update Amazon book prices (all 4 formats) using the official Creators API (OAuth2)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Fetch prices from API but do not save to DB.',
        )
        parser.add_argument(
            '--backup',
            action='store_true',
            help=(
                'Before making any changes, dump all Amazon BookFormatPrice records '
                'to amazon_book_prices_backup_YYYYMMDD_HHMMSS.json in the project root.'
            ),
        )
        parser.add_argument(
            '--faction',
            type=str,
            default=None,
            help='Only update books in this faction (e.g. horus-heresy-series).',
        )
        parser.add_argument(
            '--category',
            type=str,
            default=None,
            help='Only update books in this category (e.g. warhammer).',
        )
        parser.add_argument(
            '--format',
            type=str,
            default=None,
            choices=sorted(_FORMAT_ALIASES),
            help='Only update one format: paperback, hardback, ebook, audiobook.',
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=None,
            metavar='N',
            help='Cap the number of ASINs looked up (useful for spot-checking).',
        )

    def handle(self, *args, **options):
        """Entry point."""
        client = AmazonCreatorsClient()

        try:
            retailer = Retailer.objects.get(slug='amazon')
        except Retailer.DoesNotExist:
            self.stderr.write(self.style.ERROR('Retailer with slug "amazon" not found in DB.'))
            return

        qs = (
            BookFormatPrice.objects
            .filter(retailer=retailer)
            .exclude(url='')
            .select_related('product')
        )

        if options['faction']:
            try:
                faction = Faction.objects.get(slug=options['faction'])
            except Faction.DoesNotExist:
                self.stderr.write(self.style.ERROR(f'Faction "{options["faction"]}" not found.'))
                return
            qs = qs.filter(product__faction=faction)

        if options['category']:
            try:
                category = Category.objects.get(slug=options['category'])
            except Category.DoesNotExist:
                self.stderr.write(self.style.ERROR(f'Category "{options["category"]}" not found.'))
                return
            qs = qs.filter(product__category=category)

        if options['format']:
            qs = qs.filter(format=_FORMAT_ALIASES[options['format']])

        entries = list(qs)

        if not entries:
            self.stdout.write(self.style.WARNING('No Amazon book entries found for the given filters.'))
            return

        self.stdout.write(f'Found {len(entries)} Amazon BookFormatPrice entries to process.')

        if options['backup']:
            self._backup(entries)

        # Split by format: Audio Book needs the trial-price-aware raw lookup,
        # everything else can safely use the shared client's batched GetItems.
        audiobook_entries = [e for e in entries if e.format == BookFormatPrice.FORMAT_AUDIOBOOK]
        other_entries = [e for e in entries if e.format != BookFormatPrice.FORMAT_AUDIOBOOK]

        asin_to_entries = {}
        skipped_no_asin = []
        audiobook_asin_to_entries = {}

        for entry in other_entries:
            if entry.manual_url_override and not entry.url:
                self.stdout.write(f'  [skip] {entry.product.gw_sku} ({entry.get_format_display()}) — manual_url_override=True, no URL')
                continue
            asin = extract_asin(entry.url)
            if not asin:
                skipped_no_asin.append(f'{entry.product.gw_sku}:{entry.format}')
                continue
            asin_to_entries.setdefault(asin, []).append(entry)

        for entry in audiobook_entries:
            if entry.manual_url_override and not entry.url:
                self.stdout.write(f'  [skip] {entry.product.gw_sku} (Audio Book) — manual_url_override=True, no URL')
                continue
            asin = extract_asin(entry.url)
            if not asin:
                skipped_no_asin.append(f'{entry.product.gw_sku}:{entry.format}')
                continue
            audiobook_asin_to_entries.setdefault(asin, []).append(entry)

        if skipped_no_asin:
            self.stdout.write(self.style.WARNING(
                f'  Skipped {len(skipped_no_asin)} entries with no ASIN in URL: '
                + ', '.join(skipped_no_asin)
            ))

        if options['limit']:
            asin_to_entries = dict(list(asin_to_entries.items())[:options['limit']])
            audiobook_asin_to_entries = dict(list(audiobook_asin_to_entries.items())[:options['limit']])
            self.stdout.write(f'Limiting to first {options["limit"]} ASINs per group (--limit).')

        if not asin_to_entries and not audiobook_asin_to_entries:
            self.stdout.write(self.style.WARNING('No ASINs to look up. Exiting.'))
            return

        api_results = {}

        if asin_to_entries:
            self.stdout.write(f'Looking up {len(asin_to_entries)} Paperback/Hardback/E-Book ASINs via Creators API...')
            try:
                api_results.update(client.get_items_batched(list(asin_to_entries.keys())))
            except requests.HTTPError as exc:
                self.stderr.write(self.style.ERROR(f'API error: {exc}'))
                if exc.response is not None:
                    self.stderr.write(f'Response body: {exc.response.text[:500]}')
                return
            except Exception as exc:
                self.stderr.write(self.style.ERROR(f'Unexpected error: {exc}'))
                return

        if audiobook_asin_to_entries:
            self.stdout.write(f'Looking up {len(audiobook_asin_to_entries)} Audio Book ASINs via Creators API (trial-price-aware)...')
            try:
                api_results.update(
                    self._get_audiobook_items_batched(client, list(audiobook_asin_to_entries.keys()))
                )
            except requests.HTTPError as exc:
                self.stderr.write(self.style.ERROR(f'API error (audiobooks): {exc}'))
                if exc.response is not None:
                    self.stderr.write(f'Response body: {exc.response.text[:500]}')
                return
            except Exception as exc:
                self.stderr.write(self.style.ERROR(f'Unexpected error (audiobooks): {exc}'))
                return

        combined_asin_to_entries = {**asin_to_entries, **audiobook_asin_to_entries}

        dry_run = options['dry_run']
        updated = 0
        no_price = 0
        unchanged = 0
        failed = 0

        for asin, result in api_results.items():
            entry_list = combined_asin_to_entries.get(asin)
            if not entry_list:
                continue

            new_price = result['price']
            new_in_stock = result['in_stock']

            for entry in entry_list:
                product = entry.product
                fmt_display = entry.get_format_display()

                if new_price is None:
                    self.stdout.write(
                        f'  [no price] {product.gw_sku} ({product.name}, {fmt_display}) — ASIN {asin}'
                    )
                    no_price += 1
                    if not dry_run and (entry.price is not None or entry.in_stock):
                        entry.price = None
                        entry.in_stock = False
                        if not self._save_entry(entry, ['price', 'in_stock', 'last_seen']):
                            failed += 1
                    continue

                price_changed = (entry.price != new_price)
                stock_changed = (entry.in_stock != new_in_stock)

                if not price_changed and not stock_changed:
                    unchanged += 1
                    continue

                change_parts = []
                if price_changed:
                    old_str = f'${entry.price:.2f}' if entry.price is not None else 'none'
                    change_parts.append(f'${new_price:.2f} (was {old_str})')
                if stock_changed:
                    change_parts.append('in_stock=' + str(new_in_stock))

                label = '[dry-run]' if dry_run else '[updated]'
                self.stdout.write(
                    f'  {label} {product.gw_sku} ({product.name}, {fmt_display}) — '
                    + ', '.join(change_parts)
                    + f'  [ASIN: {asin} | https://www.amazon.com/dp/{asin}]'
                )

                if not dry_run:
                    entry.price = new_price
                    entry.in_stock = new_in_stock
                    entry.not_available = False
                    if not self._save_entry(entry, ['price', 'in_stock', 'not_available', 'last_seen']):
                        failed += 1
                        continue

                updated += 1

        missing_from_api = [asin for asin in combined_asin_to_entries if asin not in api_results]
        if missing_from_api:
            self.stdout.write(self.style.WARNING(
                f'  {len(missing_from_api)} ASIN(s) not returned by API: '
                + ', '.join(missing_from_api)
            ))

        dry_label = ' (DRY RUN — no changes saved)' if dry_run else ''
        summary_style = self.style.ERROR if failed else self.style.SUCCESS
        self.stdout.write(summary_style(
            f'\nDone{dry_label}. '
            f'Updated: {updated}  |  Unchanged: {unchanged}  |  '
            f'No price: {no_price}  |  Missing from API: {len(missing_from_api)}  |  '
            f'Failed: {failed}'
        ))

    def _get_audiobook_items_batched(self, client, asins):
        """
        Raw batched GetItems lookup for Audio Book ASINs, applying
        _best_audiobook_price() instead of the shared client's
        _extract_price() so the $0.00 trial offer is never mistaken for
        the real Buy Now price. Mirrors AmazonCreatorsClient.get_items_batched()'s
        batching/delay behaviour exactly, just with different price parsing.
        """
        token = client.get_token()
        headers = {
            'Authorization': f'Bearer {token}',
            'x-marketplace': 'www.amazon.com',
            'Content-Type': 'application/json; charset=utf-8',
        }
        resources = [
            'offersV2.listings.price',
            'offersV2.listings.condition',
        ]

        results = {}
        batches = [asins[i:i + _BATCH_SIZE] for i in range(0, len(asins), _BATCH_SIZE)]

        for idx, batch in enumerate(batches):
            if idx > 0:
                time.sleep(_CALL_DELAY)

            payload = {
                'itemIds': batch,
                'partnerTag': settings.AMAZON_ASSOCIATE_TAG,
                'partnerType': 'Associates',
                'resources': resources,
            }
            resp = client._session.post(f'{_API_BASE}{_ITEMS_PATH}', json=payload, headers=headers, timeout=20)
            if resp.status_code == 429:
                time.sleep(5)
                resp = client._session.post(f'{_API_BASE}{_ITEMS_PATH}', json=payload, headers=headers, timeout=20)
            resp.raise_for_status()
            data = resp.json()

            for item in data.get('itemsResult', {}).get('items', []):
                asin = item.get('asin')
                if not asin:
                    continue
                price = _best_audiobook_price(item)
                results[asin] = {'price': price, 'in_stock': price is not None}

        return results

    def _save_entry(self, entry, update_fields):
        """
        Save a BookFormatPrice entry, recovering from a dropped DB connection.

        Same rationale as update_amazon_creators_prices.py's _save_entry:
        this batch run holds one DB connection open for its entire duration,
        including idle minutes while fetching prices from the Amazon API
        before any writes happen. On OperationalError or InterfaceError,
        close the stale connection so Django opens a fresh one, wait
        briefly, and retry once.
        """
        try:
            entry.save(update_fields=update_fields)
            return True
        except (OperationalError, InterfaceError) as exc:
            self.stderr.write(self.style.WARNING(
                f'  [db-retry] {entry.product.gw_sku} — connection error, retrying: {exc}'
            ))
            connection.close()
            time.sleep(2)
            try:
                entry.save(update_fields=update_fields)
                return True
            except (OperationalError, InterfaceError) as exc2:
                self.stderr.write(self.style.ERROR(
                    f'  [db-error] {entry.product.gw_sku} — save failed after retry, skipping: {exc2}'
                ))
                return False

    def _backup(self, entries):
        """Write all current Amazon BookFormatPrice records to a JSON backup file."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'amazon_book_prices_backup_{timestamp}.json'

        backup_data = [
            {
                'gw_sku':              entry.product.gw_sku,
                'product_name':        entry.product.name,
                'format':              entry.format,
                'url':                 entry.url,
                'price':               str(entry.price) if entry.price is not None else None,
                'in_stock':            entry.in_stock,
                'not_available':       entry.not_available,
                'manual_url_override': entry.manual_url_override,
                'is_msrp_source':      entry.is_msrp_source,
                'last_seen':           entry.last_seen.isoformat() if entry.last_seen else None,
            }
            for entry in entries
        ]

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(backup_data, f, indent=2)

        self.stdout.write(self.style.SUCCESS(
            f'  Backup written: {filename} ({len(backup_data)} records)'
        ))
