"""
Management command: assign_warmachine_dark_operations

Fourth step of reorganizing the flat 348-product Warmachine category into
per-faction structure. Creates the "Dark Operations" Faction under the
existing Warmachine Category, and reassigns the 19 existing WMH-xxx
products that belong to it.

All 19 products from the user-supplied "Warmachine - Dark Operations.xlsx"
already exist in the original 348-product Warmachine batch -- no new
products are created here, only faction reassignment.

WMH-006 (Hive Mind Cadre) and WMH-314 (Criterions Unit) are Cephalyx units
shared between Cryx and Dark Operations in the game's lore. User confirmed
2026-08-13 to dual-tag rather than move: they keep faction=Cryx as primary
and get Dark Operations added via secondary_factions, same pattern already
used for Warcry / Chaos Daemons / Forces of the Emperor. The other 17 SKUs
get faction=Dark Operations directly.

Usage:
    python manage.py assign_warmachine_dark_operations
"""

from django.core.management.base import BaseCommand

from products.models import Category, Faction, Product

# SKUs that get Dark Operations as their primary faction
DARK_OPERATIONS_PRIMARY_SKUS = [
    'WMH-008', 'WMH-105', 'WMH-106', 'WMH-107', 'WMH-117', 'WMH-118',
    'WMH-119', 'WMH-317', 'WMH-318', 'WMH-338', 'WMH-339', 'WMH-340',
    'WMH-341', 'WMH-342', 'WMH-343', 'WMH-344', 'WMH-345',
]

# SKUs that keep their existing primary faction and get Dark Operations
# added as a secondary faction (dual-tag)
DARK_OPERATIONS_SECONDARY_SKUS = ['WMH-006', 'WMH-314']


class Command(BaseCommand):
    """Create the Dark Operations faction and assign its products."""

    help = 'Creates Warmachine: Dark Operations faction and assigns its 19 products.'

    def handle(self, *args, **options):
        category = Category.objects.get(slug='warmachine')

        faction, created = Faction.objects.get_or_create(
            name='Dark Operations',
            defaults={'slug': 'warmachine-dark-operations', 'category': category},
        )
        if created:
            self.stdout.write(self.style.SUCCESS('Created faction: Dark Operations'))
        else:
            self.stdout.write(f'Found faction: Dark Operations (pk={faction.pk})')

        reassigned = 0
        missing = []
        for gw_sku in DARK_OPERATIONS_PRIMARY_SKUS:
            try:
                product = Product.objects.get(gw_sku=gw_sku)
            except Product.DoesNotExist:
                missing.append(gw_sku)
                continue
            product.faction = faction
            product.save(update_fields=['faction'])
            reassigned += 1
            self.stdout.write(f'  reassigned: {product.name} ({gw_sku})')

        tagged = 0
        for gw_sku in DARK_OPERATIONS_SECONDARY_SKUS:
            try:
                product = Product.objects.get(gw_sku=gw_sku)
            except Product.DoesNotExist:
                missing.append(gw_sku)
                continue
            product.secondary_factions.add(faction)
            tagged += 1
            self.stdout.write(f'  dual-tagged: {product.name} ({gw_sku}, primary faction stays {product.faction})')

        if missing:
            self.stdout.write(self.style.WARNING(f'  Not found, skipped: {", ".join(missing)}'))

        self.stdout.write(self.style.SUCCESS(
            f'assign_warmachine_dark_operations complete. '
            f'{reassigned} reassigned, {tagged} dual-tagged.'
        ))
