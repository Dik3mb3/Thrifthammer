"""
Management command: export_amazon_urls

Dumps all CurrentPrice rows for the Amazon retailer (that have a URL) to a
JSON file. This is the input for scrape_amazon_browser.py.

Run this first, before running the browser scraper, to get a fresh list of
every Amazon URL currently tracked in the database.

Usage:
    python manage.py export_amazon_urls --file amazon_urls.json
    python manage.py export_amazon_urls --file amazon_urls.json --dry-run
"""

import json
import os

from django.core.management.base import BaseCommand, CommandError

from prices.models import CurrentPrice
from products.models import Retailer


class Command(BaseCommand):
    """Export all tracked Amazon URLs from CurrentPrice to a JSON file."""

    help = 'Export Amazon URLs from CurrentPrice for use by scrape_amazon_browser.py.'

    def add_arguments(self, parser):
        """Add CLI arguments."""
        parser.add_argument(
            '--file',
            required=True,
            help='Path to write the output JSON file.',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            default=False,
            help='Print what would be exported without writing the file.',
        )

    def handle(self, *args, **options):
        """Execute the export."""
        out_path = options['file']
        dry_run  = options['dry_run']

        try:
            amazon = Retailer.objects.get(name='Amazon')
        except Retailer.DoesNotExist:
            raise CommandError("Retailer 'Amazon' not found in the database.")

        records = (
            CurrentPrice.objects
            .filter(retailer=amazon)
            .exclude(url='')
            .exclude(url__isnull=True)
            .select_related('product')
            .order_by('product__name')
        )

        export = []
        for cp in records:
            export.append({
                'gw_sku': cp.product.gw_sku,
                'name'  : cp.product.name,
                'url'   : cp.url,
                'slug'  : cp.product.slug,
            })

        self.stdout.write(f'Found {len(export)} Amazon URLs in the database.')

        if dry_run:
            for item in export:
                self.stdout.write(f"  {item['gw_sku']:8s}  {item['name']}")
            self.stdout.write(self.style.SUCCESS(f'\n[DRY RUN] Would write {len(export)} entries to {out_path}'))
            return

        with open(out_path, 'w') as f:
            json.dump(export, f, indent=2)

        self.stdout.write(self.style.SUCCESS(
            f'Exported {len(export)} Amazon URLs to {out_path}'
        ))
