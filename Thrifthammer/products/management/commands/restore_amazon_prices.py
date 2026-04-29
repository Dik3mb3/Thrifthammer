"""
Management command: restore_amazon_prices

Restores Amazon CurrentPrice records from a backup JSON file produced
by backup_amazon_prices.

Only restores SKUs present in the backup file. Any SKUs NOT in the backup
are left untouched (so a partial backup only restores what it contains).

Usage:
    python manage.py restore_amazon_prices --file amazon_prices_backup.json
    python manage.py restore_amazon_prices --file amazon_prices_backup.json --dry-run
"""

import decimal
import json
import os

from django.core.management.base import BaseCommand, CommandError

from prices.models import CurrentPrice
from products.models import Product, Retailer


class Command(BaseCommand):
    """Restore Amazon prices from a backup JSON file."""

    help = 'Restore Amazon prices from a backup produced by backup_amazon_prices.'

    def add_arguments(self, parser):
        """Add CLI arguments."""
        parser.add_argument(
            '--file',
            required=True,
            help='Path to the backup JSON file.',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            default=False,
            help='Show what would be restored without writing to the database.',
        )

    def handle(self, *args, **options):
        """Execute the restore."""
        json_path = options['file']
        dry_run   = options['dry_run']

        if not os.path.exists(json_path):
            raise CommandError(f'Backup file not found: {json_path}')

        with open(json_path) as f:
            backup = json.load(f)

        try:
            amazon = Retailer.objects.get(name='Amazon')
        except Retailer.DoesNotExist:
            raise CommandError("Retailer 'Amazon' not found in the database.")

        sku_map = {
            p.gw_sku: p
            for p in Product.objects.filter(is_active=True).only('id', 'gw_sku', 'name')
        }

        restored  = 0
        not_found = 0

        for sku, entry in backup.items():
            product = sku_map.get(sku)
            if not product:
                self.stdout.write(
                    self.style.WARNING(f'  [miss] {sku:8s} — not in active products, skipping')
                )
                not_found += 1
                continue

            price_str = entry.get('price')
            price     = decimal.Decimal(price_str) if price_str else None

            self.stdout.write(
                f"  [{'dry' if dry_run else 'restore'}] {sku:8s}  "
                f"{'$'+price_str if price_str else 'no price':>10s}  {product.name}"
            )

            if not dry_run:
                CurrentPrice.objects.update_or_create(
                    product=product,
                    retailer=amazon,
                    defaults={
                        'price'        : price,
                        'url'          : entry.get('url', ''),
                        'in_stock'     : entry.get('in_stock', False),
                        'not_available': entry.get('not_available', False),
                        'listing_title': entry.get('listing_title', ''),
                    },
                )

            restored += 1

        label = '[DRY RUN] ' if dry_run else ''
        self.stdout.write(self.style.SUCCESS(
            f'\n{label}Restore complete.  Restored: {restored}  Not found: {not_found}'
        ))
