"""
Management command: seed_price_history

One-time backfill that seeds the PriceHistory table from the current
CurrentPrice snapshot.

Before the price-history signal was added, no historical records existed.
Running this command once populates each product/retailer pair with a
single baseline entry dated "now" (the actual timestamp of the backfill).

This gives charts a starting point — future price changes recorded by the
signal will then show movement relative to this baseline.

Safe to re-run: if a PriceHistory entry for a given (product, retailer)
already exists, no duplicate is created.

Usage:
    python manage.py seed_price_history
    python manage.py seed_price_history --dry-run
"""

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice, PriceHistory


class Command(BaseCommand):
    """Backfill PriceHistory from the current CurrentPrice snapshot."""

    help = 'Seed PriceHistory with one baseline entry per active CurrentPrice row.'

    def add_arguments(self, parser):
        """Add --dry-run flag."""
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Print planned inserts without writing to the database.',
        )

    def handle(self, *args, **options):
        """Create one PriceHistory entry per CurrentPrice that has a price."""
        dry = options['dry_run']
        if dry:
            self.stdout.write(self.style.WARNING('DRY RUN — no changes will be saved.\n'))

        # Gather all CurrentPrice rows that have a real price (skip not_available)
        current_prices = (
            CurrentPrice.objects
            .filter(price__isnull=False)
            .select_related('product', 'retailer')
            .order_by('retailer__name', 'product__name')
        )

        # Build a set of (product_id, retailer_id) pairs that already have history
        existing = set(
            PriceHistory.objects
            .values_list('product_id', 'retailer_id')
            .distinct()
        )

        created = 0
        skipped = 0

        for cp in current_prices:
            key = (cp.product_id, cp.retailer_id)
            if key in existing:
                skipped += 1
                if dry:
                    self.stdout.write(
                        f'  [skip] {cp.product.gw_sku} / {cp.retailer.name} — history exists'
                    )
                continue

            if dry:
                self.stdout.write(
                    f'  [dry] {cp.product.gw_sku} / {cp.retailer.name} '
                    f'— baseline ${cp.price}, in_stock={cp.in_stock}'
                )
            else:
                PriceHistory.objects.create(
                    product=cp.product,
                    retailer=cp.retailer,
                    price=cp.price,
                    in_stock=cp.in_stock,
                )
                created += 1

        if dry:
            to_create = current_prices.count() - len(existing)
            self.stdout.write(
                self.style.WARNING(
                    f'\nDRY RUN complete: {to_create} entries would be created, '
                    f'{skipped} skipped (history already exists).'
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f'\nDone: {created} baseline PriceHistory entries created, '
                    f'{skipped} skipped (history already exists).'
                )
            )
