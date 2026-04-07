"""
Management command: ensure_retailer_rows

For every product tagged phase-2, phase-3, or belonging to the Emperor's
Children faction, guarantees that all five retailers (Games Workshop,
Miniature Market, Noble Knight Games, eBay, Amazon) have a CurrentPrice
row. Missing rows are created with not_available=True and no URL so they
show up as "not available" in the product detail price chart.

Existing rows are never modified — only absent rows are inserted.

Usage:
    python manage.py ensure_retailer_rows
    python manage.py ensure_retailer_rows --dry-run
"""

from django.db.models import Q
from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Product, Retailer

REQUIRED_RETAILER_NAMES = [
    'Games Workshop',
    'Miniature Market',
    'Noble Knight Games',
    'eBay',
    'Amazon',
]

TARGET_BATCH_TAGS = {'phase-2', 'phase-3'}
TARGET_FACTION = "Emperor's Children"


class Command(BaseCommand):
    """Ensure all 5 retailers have a CurrentPrice row for phase-2/3 and EC products."""

    help = (
        'Adds missing not_available CurrentPrice rows for the 5 standard retailers '
        'on all phase-2, phase-3, and Emperor\'s Children products. Idempotent.'
    )

    def add_arguments(self, parser):
        """Add optional --dry-run flag."""
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Report what would be created without writing to the database.',
        )

    def handle(self, *args, **options):
        """Run the command."""
        dry_run = options['dry_run']

        # ── Load all 5 retailers ──────────────────────────────────────────────
        retailers = {}
        missing_retailers = []
        for name in REQUIRED_RETAILER_NAMES:
            retailer = Retailer.objects.filter(name=name).first()
            if retailer:
                retailers[name] = retailer
            else:
                missing_retailers.append(name)

        if missing_retailers:
            self.stderr.write(self.style.WARNING(
                f'Retailers not found in DB (skipped): {", ".join(missing_retailers)}'
            ))

        if not retailers:
            self.stderr.write(self.style.ERROR('No retailers found — aborting.'))
            return

        # ── Collect target products ───────────────────────────────────────────
        products = (
            Product.objects
            .filter(is_active=True)
            .filter(
                Q(batch_tag__in=TARGET_BATCH_TAGS) | Q(faction__name=TARGET_FACTION)
            )
            .select_related('faction')
            .distinct()
        )

        total_products = products.count()
        self.stdout.write(
            f'Found {total_products} target products '
            f'(phase-2/3 or {TARGET_FACTION}).'
        )

        # ── For each product, add any missing retailer rows ───────────────────
        created_count = 0

        for product in products:
            existing_retailer_ids = set(
                product.current_prices.values_list('retailer_id', flat=True)
            )

            for name, retailer in retailers.items():
                if retailer.pk in existing_retailer_ids:
                    continue

                if dry_run:
                    self.stdout.write(
                        f'  [dry-run] Would add: {product.name} — {name}'
                    )
                    created_count += 1
                    continue

                CurrentPrice.objects.update_or_create(
                    product=product,
                    retailer=retailer,
                    defaults={
                        'price': None,
                        'url': '',
                        'listing_title': '',
                        'in_stock': False,
                        'not_available': True,
                    },
                )
                self.stdout.write(f'  Added: {product.name} — {name}')
                created_count += 1

        label = 'Would create' if dry_run else 'Created'
        self.stdout.write(self.style.SUCCESS(
            f'\nensure_retailer_rows complete. '
            f'{label} {created_count} missing retailer row(s) '
            f'across {total_products} products.'
        ))


