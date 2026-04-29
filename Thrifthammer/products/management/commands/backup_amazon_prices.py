"""
Management command: backup_amazon_prices

Dumps all current Amazon CurrentPrice records to a JSON file.
Run this before importing new prices so you have a rollback point.

Usage:
    python manage.py backup_amazon_prices --file amazon_prices_backup.json
"""

import json
import os

from django.core.management.base import BaseCommand, CommandError

from prices.models import CurrentPrice
from products.models import Retailer


class Command(BaseCommand):
    """Dump current Amazon prices to a JSON backup file."""

    help = 'Backup all current Amazon prices to a JSON file for rollback purposes.'

    def add_arguments(self, parser):
        """Add CLI arguments."""
        parser.add_argument(
            '--file',
            required=True,
            help='Path to write the backup JSON file.',
        )

    def handle(self, *args, **options):
        """Execute the backup."""
        out_path = options['file']

        try:
            amazon = Retailer.objects.get(name='Amazon')
        except Retailer.DoesNotExist:
            raise CommandError("Retailer 'Amazon' not found in the database.")

        records = (
            CurrentPrice.objects
            .filter(retailer=amazon)
            .select_related('product')
            .order_by('product__gw_sku')
        )

        backup = {}
        for cp in records:
            backup[cp.product.gw_sku] = {
                'name'         : cp.product.name,
                'url'          : cp.url,
                'price'        : str(cp.price) if cp.price is not None else None,
                'in_stock'     : cp.in_stock,
                'not_available': cp.not_available,
                'listing_title': cp.listing_title,
                'status'       : 'ok' if (cp.price and cp.in_stock and not cp.not_available)
                                 else 'unavailable' if cp.not_available
                                 else 'out_of_stock',
            }

        with open(out_path, 'w') as f:
            json.dump(backup, f, indent=2)

        self.stdout.write(self.style.SUCCESS(
            f'Backed up {len(backup)} Amazon price records to {out_path}'
        ))
