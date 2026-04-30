"""
Management command: import_amazon_browser_prices

Reads a JSON file produced by scrape_amazon_browser.py and writes the
scraped prices into CurrentPrice (Amazon retailer).

Only updates entries where status == 'ok' and price is a valid number.
Skips unavailable / blocked / no-price results without touching the DB.

Usage:
    python manage.py import_amazon_browser_prices --file amazon_prices_batch1.json
    python manage.py import_amazon_browser_prices --file amazon_prices_batch1.json --dry-run
"""

import decimal
import json
import os

from django.core.management.base import BaseCommand, CommandError

from prices.models import CurrentPrice
from products.models import Product, Retailer


class Command(BaseCommand):
    """Import browser-scraped Amazon prices from a JSON file."""

    help = 'Import Amazon prices scraped by scrape_amazon_browser.py into CurrentPrice.'

    def add_arguments(self, parser):
        """Add CLI arguments."""
        parser.add_argument(
            '--file',
            required=True,
            help='Path to the JSON file produced by scrape_amazon_browser.py',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            default=False,
            help='Print what would be updated without writing to the database.',
        )

    def handle(self, *args, **options):
        """Execute the import."""
        json_path = options['file']
        dry_run   = options['dry_run']

        if not os.path.exists(json_path):
            raise CommandError(f'File not found: {json_path}')

        with open(json_path) as f:
            data = json.load(f)

        try:
            amazon = Retailer.objects.get(name='Amazon')
        except Retailer.DoesNotExist:
            raise CommandError("Retailer 'Amazon' not found in the database.")

        sku_map = {
            p.gw_sku: p
            for p in Product.objects.filter(is_active=True).only('id', 'gw_sku', 'name')
        }

        updated    = 0
        skipped    = 0
        not_found  = 0
        marked_na  = 0

        for sku, entry in data.items():
            status    = entry.get('status', '')
            price_str = entry.get('price')
            url       = entry.get('url', '')
            name      = entry.get('name', sku)

            # ── Definitive unavailability from Amazon ─────────────────────
            # 'unavailable' = Amazon returned "Currently unavailable" page.
            # 'no_price'    = page loaded but no purchasable price found.
            # Both mean the listing is not purchasable right now.
            # Mark not_available=True so the site shows "—" instead of a
            # stale price.  Scraper failures (blocked/timeout/error) are
            # skipped without touching the DB — they may be transient.
            if status in ('unavailable', 'no_price'):
                product = sku_map.get(sku)
                if product:
                    existing = CurrentPrice.objects.filter(
                        product=product, retailer=amazon,
                    ).first()
                    if existing and not existing.not_available:
                        if not dry_run:
                            existing.not_available = True
                            existing.save(update_fields=['not_available'])
                        self.stdout.write(self.style.WARNING(
                            f'  [N/A]  {sku:8s} {name} — '
                            f'status={status}, marked not_available'
                        ))
                        marked_na += 1
                    else:
                        self.stdout.write(
                            f'  [skip] {sku:8s} {name} — '
                            f'status={status}, already not_available or no record'
                        )
                else:
                    self.stdout.write(
                        f'  [skip] {sku:8s} {name} — '
                        f'status={status}, product not in DB'
                    )
                skipped += 1
                continue

            # ── Transient scraper failures — skip without DB changes ──────
            if status != 'ok' or not price_str:
                self.stdout.write(
                    f'  [skip] {sku:8s} {name} — status={status}'
                )
                skipped += 1
                continue

            product = sku_map.get(sku)
            if not product:
                self.stdout.write(
                    self.style.WARNING(f'  [miss] {sku:8s} {name} — not in active products')
                )
                not_found += 1
                continue

            try:
                price = decimal.Decimal(str(price_str))
            except decimal.InvalidOperation:
                self.stdout.write(
                    self.style.WARNING(f'  [bad]  {sku:8s} {name} — invalid price "{price_str}"')
                )
                skipped += 1
                continue

            self.stdout.write(
                f"  [{'dry' if dry_run else 'set'}] {sku:8s}  ${price:>8.2f}  {product.name}"
            )

            if not dry_run:
                CurrentPrice.objects.update_or_create(
                    product=product,
                    retailer=amazon,
                    defaults={
                        'price'        : price,
                        'url'          : url,
                        'in_stock'     : True,
                        'not_available': False,
                        'listing_title': '',
                    },
                )

            updated += 1

        label = '[DRY RUN] ' if dry_run else ''
        self.stdout.write(self.style.SUCCESS(
            f'\n{label}Done!  '
            f'Updated: {updated}  '
            f'Marked N/A: {marked_na}  '
            f'Skipped: {skipped}  '
            f'Not found: {not_found}'
        ))
