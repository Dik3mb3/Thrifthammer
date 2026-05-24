"""
Management command: update_amazon_creators_prices

Fetches live Amazon prices via the official Creators API (OAuth2) and
updates CurrentPrice records.  This is the replacement for the HTML
scraper (scrapers/retailers/amazon.py) which required TLS impersonation
and was fragile against Amazon's anti-bot measures.

The old HTML scraper is NOT removed — it remains as a backup and can
still be run with: python manage.py run_scrapers amazon

Safety rules (same as update_ebay_prices):
  - CurrentPrice entries with manual_url_override=True are NEVER touched.
  - Uses .save() not QuerySet.update() so cache-invalidation signals fire.
  - Dry run (--dry-run) prints what would change without writing to DB.
  - Backup (--backup) dumps all current Amazon URLs to JSON before any writes.

Usage:
  # Verify OAuth2 credentials work (no DB reads or writes):
  python manage.py update_amazon_creators_prices --test-auth

  # Safe first run — back up URLs then do a dry run across all SKUs:
  python manage.py update_amazon_creators_prices --backup --dry-run

  # Back up + update all products:
  python manage.py update_amazon_creators_prices --backup

  # Targeted run for one batch tag:
  python manage.py update_amazon_creators_prices --batch-tag skaven

  # Single SKU by gw_sku:
  python manage.py update_amazon_creators_prices --sku AS-001
"""

import json
from datetime import datetime

import requests
from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Retailer
from scrapers.retailers.amazon_creators import AmazonCreatorsClient, extract_asin


class Command(BaseCommand):
    """Update Amazon CurrentPrice records via the Creators API."""

    help = 'Update Amazon prices using the official Creators API (OAuth2)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--test-auth',
            action='store_true',
            help='Test OAuth2 token acquisition only — does not read or write DB.',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Fetch prices from API but do not save to DB.',
        )
        parser.add_argument(
            '--backup',
            action='store_true',
            help=(
                'Before making any changes, dump all Amazon CurrentPrice records '
                'to amazon_prices_backup_YYYYMMDD_HHMMSS.json in the project root.'
            ),
        )
        parser.add_argument(
            '--batch-tag',
            type=str,
            default=None,
            metavar='TAG',
            help='Only update products with this batch_tag (e.g. skaven, stormcast).',
        )
        parser.add_argument(
            '--sku',
            type=str,
            default=None,
            metavar='GW_SKU',
            help='Only update one product by gw_sku (e.g. AS-001).',
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=None,
            metavar='N',
            help='Cap the number of ASINs looked up (useful for spot-checking, e.g. --limit 100).',
        )

    def handle(self, *args, **options):
        """Entry point."""
        client = AmazonCreatorsClient()

        if options['test_auth']:
            self._test_auth(client)
            return

        try:
            retailer = Retailer.objects.get(slug='amazon')
        except Retailer.DoesNotExist:
            self.stderr.write(self.style.ERROR(
                'Retailer with slug "amazon" not found in DB. '
                'Run populate_products first.'
            ))
            return

        qs = (
            CurrentPrice.objects
            .filter(retailer=retailer)
            .exclude(url='')
            .select_related('product')
        )

        if options['sku']:
            qs = qs.filter(product__gw_sku=options['sku'])
        elif options['batch_tag']:
            qs = qs.filter(product__batch_tag=options['batch_tag'])

        entries = list(qs)

        if not entries:
            self.stdout.write(self.style.WARNING('No Amazon entries found for the given filters.'))
            return

        self.stdout.write(f'Found {len(entries)} Amazon CurrentPrice entries to process.')

        if options['backup']:
            self._backup(entries)

        asin_to_entry = {}
        skipped_no_asin = []

        for entry in entries:
            if entry.manual_url_override and not entry.url:
                self.stdout.write(f'  [skip] {entry.product.gw_sku} — manual_url_override=True, no URL')
                continue

            asin = extract_asin(entry.url)
            if not asin:
                skipped_no_asin.append(entry.product.gw_sku)
                continue

            asin_to_entry[asin] = entry

        if skipped_no_asin:
            self.stdout.write(self.style.WARNING(
                f'  Skipped {len(skipped_no_asin)} entries with no ASIN in URL: '
                + ', '.join(skipped_no_asin)
            ))

        if options['limit']:
            asin_to_entry = dict(list(asin_to_entry.items())[:options['limit']])
            self.stdout.write(f'Limiting to first {len(asin_to_entry)} ASINs (--limit).')

        if not asin_to_entry:
            self.stdout.write(self.style.WARNING('No ASINs to look up. Exiting.'))
            return

        self.stdout.write(f'Looking up {len(asin_to_entry)} ASINs via Creators API...')

        try:
            api_results = client.get_items_batched(list(asin_to_entry.keys()))
        except requests.HTTPError as exc:
            self.stderr.write(self.style.ERROR(f'API error: {exc}'))
            if exc.response is not None:
                self.stderr.write(f'Response body: {exc.response.text[:500]}')
            return
        except Exception as exc:
            self.stderr.write(self.style.ERROR(f'Unexpected error: {exc}'))
            return

        dry_run = options['dry_run']
        updated = 0
        no_price = 0
        unchanged = 0

        for asin, result in api_results.items():
            entry = asin_to_entry.get(asin)
            if entry is None:
                continue

            product = entry.product
            new_price = result['price']
            new_in_stock = result['in_stock']

            if new_price is None:
                self.stdout.write(
                    f'  [no price] {product.gw_sku} ({product.name}) — ASIN {asin}'
                )
                no_price += 1
                if not dry_run and (entry.price is not None or entry.in_stock):
                    entry.price = None
                    entry.in_stock = False
                    entry.save(update_fields=['price', 'in_stock', 'last_seen'])
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
                f'  {label} {product.gw_sku} ({product.name}) — '
                + ', '.join(change_parts)
                + f'  [ASIN: {asin} | https://www.amazon.com/dp/{asin}]'
            )

            if not dry_run:
                entry.price = new_price
                entry.in_stock = new_in_stock
                entry.not_available = False
                entry.save(update_fields=['price', 'in_stock', 'not_available', 'last_seen'])

            updated += 1

        missing_from_api = [asin for asin in asin_to_entry if asin not in api_results]
        if missing_from_api:
            self.stdout.write(self.style.WARNING(
                f'  {len(missing_from_api)} ASIN(s) not returned by API: '
                + ', '.join(missing_from_api)
            ))

        dry_label = ' (DRY RUN — no changes saved)' if dry_run else ''
        self.stdout.write(self.style.SUCCESS(
            f'\nDone{dry_label}. '
            f'Updated: {updated}  |  Unchanged: {unchanged}  |  '
            f'No price: {no_price}  |  Missing from API: {len(missing_from_api)}'
        ))

    def _test_auth(self, client):
        """Attempt to acquire an OAuth2 token and print the result."""
        self.stdout.write('Testing Amazon Creators API authentication...')
        try:
            token = client.get_token()
            self.stdout.write(self.style.SUCCESS(
                f'  Token acquired successfully: {token[:20]}...'
            ))
        except Exception as exc:
            self.stderr.write(self.style.ERROR(f'  Auth failed: {exc}'))

    def _backup(self, entries):
        """
        Write all current Amazon CurrentPrice records to a JSON backup file.

        Args:
            entries: list of CurrentPrice objects filtered to amazon retailer.
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'amazon_prices_backup_{timestamp}.json'

        backup_data = [
            {
                'gw_sku':              entry.product.gw_sku,
                'product_name':        entry.product.name,
                'url':                 entry.url,
                'price':               str(entry.price) if entry.price is not None else None,
                'in_stock':            entry.in_stock,
                'not_available':       entry.not_available,
                'manual_url_override': entry.manual_url_override,
                'last_seen':           entry.last_seen.isoformat() if entry.last_seen else None,
            }
            for entry in entries
        ]

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(backup_data, f, indent=2)

        self.stdout.write(self.style.SUCCESS(
            f'  Backup written: {filename} ({len(backup_data)} records)'
        ))
