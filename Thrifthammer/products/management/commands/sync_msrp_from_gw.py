"""
Management command: sync_msrp_from_gw

Sets product.msrp = GW's current live price for every product that has an
active, in-stock Games Workshop CurrentPrice record.

Run this once to fix stale MSRP values, then re-run whenever needed (or it
will be called automatically by import_gw_xlsx going forward).

Usage:
    # Preview which products would change:
    python manage.py sync_msrp_from_gw --dry-run

    # Apply updates:
    python manage.py sync_msrp_from_gw
"""

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Product


GW_RETAILER_SLUG = 'games-workshop'


class Command(BaseCommand):
    """
    Sync product.msrp from GW's live CurrentPrice records.

    For every product that has a Games Workshop price on file (in_stock=True,
    not_available=False), this command sets product.msrp to that price so all
    MSRP references across the site (army calculator, collection stats, discount
    columns) reflect the latest GW retail price rather than stale seeded data.
    """

    help = 'Sync product.msrp from GW live prices (safe to re-run).'

    def add_arguments(self, parser):
        """Register --dry-run flag."""
        parser.add_argument(
            '--dry-run',
            action='store_true',
            default=False,
            help='Preview changes without saving to the database.',
        )

    def handle(self, *args, **options):
        """Query GW prices and update product.msrp where stale."""
        dry_run = options['dry_run']

        self.stdout.write('\nSync product.msrp from Games Workshop live prices')
        self.stdout.write('=' * 60)
        if dry_run:
            self.stdout.write(self.style.WARNING('  DRY RUN — no changes will be saved.\n'))

        # Fetch all in-stock GW prices with the associated product
        gw_prices = (
            CurrentPrice.objects
            .filter(
                retailer__slug=GW_RETAILER_SLUG,
                in_stock=True,
                not_available=False,
                price__isnull=False,
            )
            .select_related('product')
        )

        updated = 0
        skipped = 0
        no_product = 0

        for cp in gw_prices:
            product = cp.product
            if product is None:
                no_product += 1
                continue

            if product.msrp == cp.price:
                skipped += 1
                continue

            self.stdout.write(
                f'  {product.name}: '
                f'${product.msrp or "None"} -> ${cp.price}'
            )

            if not dry_run:
                Product.objects.filter(pk=product.pk).update(msrp=cp.price)
            updated += 1

        self.stdout.write('\n' + '=' * 60)
        self.stdout.write(self.style.SUCCESS('Summary'))
        self.stdout.write('=' * 60)
        self.stdout.write(self.style.SUCCESS(f'  Updated  : {updated}'))
        self.stdout.write(f'  Already OK: {skipped}')
        if no_product:
            self.stdout.write(f'  No product: {no_product}')
        if dry_run:
            self.stdout.write(self.style.WARNING('\n  DRY RUN — no changes saved.'))
        self.stdout.write('=' * 60 + '\n')
