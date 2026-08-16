"""
Management command: assign_warmachine_dusk

Fifth step of reorganizing the flat 348-product Warmachine category into
per-faction structure. Creates the "Dusk" Faction under the existing
Warmachine Category, and reassigns the 46 existing WMH-xxx products that
belong to it.

All 46 products from the user-supplied "Warmachine - Dusk.xlsx" already
exist in the original 348-product Warmachine batch, none of them
previously assigned to any other faction -- no new products are created
here, only faction reassignment.

Usage:
    python manage.py assign_warmachine_dusk
"""

from django.core.management.base import BaseCommand

from products.models import Category, Faction, Product

DUSK_SKUS = [
    'WMH-003', 'WMH-005', 'WMH-007', 'WMH-009', 'WMH-012', 'WMH-013',
    'WMH-019', 'WMH-020', 'WMH-022', 'WMH-024', 'WMH-026', 'WMH-040',
    'WMH-041', 'WMH-048', 'WMH-063', 'WMH-076', 'WMH-093', 'WMH-094',
    'WMH-096', 'WMH-097', 'WMH-100', 'WMH-197', 'WMH-198', 'WMH-199',
    'WMH-200', 'WMH-201', 'WMH-202', 'WMH-203', 'WMH-204', 'WMH-205',
    'WMH-206', 'WMH-207', 'WMH-208', 'WMH-209', 'WMH-210', 'WMH-211',
    'WMH-251', 'WMH-263', 'WMH-264', 'WMH-265', 'WMH-266', 'WMH-268',
    'WMH-285', 'WMH-288', 'WMH-319', 'WMH-334',
]


class Command(BaseCommand):
    """Create the Dusk faction and reassign its products."""

    help = 'Creates Warmachine: Dusk faction and reassigns its 46 products.'

    def handle(self, *args, **options):
        category = Category.objects.get(slug='warmachine')

        faction, created = Faction.objects.get_or_create(
            name='Dusk',
            defaults={'slug': 'warmachine-dusk', 'category': category},
        )
        if created:
            self.stdout.write(self.style.SUCCESS('Created faction: Dusk'))
        else:
            self.stdout.write(f'Found faction: Dusk (pk={faction.pk})')

        reassigned = 0
        missing = []
        for gw_sku in DUSK_SKUS:
            try:
                product = Product.objects.get(gw_sku=gw_sku)
            except Product.DoesNotExist:
                missing.append(gw_sku)
                continue
            product.faction = faction
            product.save(update_fields=['faction'])
            reassigned += 1
            self.stdout.write(f'  reassigned: {product.name} ({gw_sku})')

        if missing:
            self.stdout.write(self.style.WARNING(f'  Not found, skipped: {", ".join(missing)}'))

        self.stdout.write(self.style.SUCCESS(
            f'assign_warmachine_dusk complete. {reassigned} product(s) reassigned.'
        ))
