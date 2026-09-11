"""
Management command: assign_warmachine_southern_kriels

Seventh step of reorganizing the flat 348-product Warmachine category into
per-faction structure. Creates the "Southern Kriels" Faction under the
existing Warmachine Category, and reassigns the 54 existing WMH-xxx products
that belong to it as their primary faction (same pattern as Crucible Guard,
Cryx, Cygnar, Dark Operations, Dusk, and Khador before it).

All 54 rows from the user-supplied "Southern Kriels - Warmachine -
Steamforged.xlsx" already exist in the original 348-product Warmachine
batch -- no new products are created here, only faction reassignment.
Every title matched an existing product by exact name (no collisions, no
unmatched rows), and every row's spreadsheet price matched the existing
Steamforged Games CurrentPrice exactly -- cross-checked before writing this
command. Southern Kriels merges what were separate MK3-era Trollbloods and
Pirates of the Broken Coast (Longshoreman Kriels/pirate mercenary) themes
into one MK4 faction, hence the mix of Kithguard/Brineblood troll-kin
sub-groups and Pyg/Marauder pirate crew SKUs.

No dual-tagged/shared-starter-set SKUs this batch (unlike Khador's
WMH-261 Two Player Starter Set case).

Usage:
    python manage.py assign_warmachine_southern_kriels
"""

from django.core.management.base import BaseCommand

from products.models import Category, Faction, Product

SOUTHERN_KRIELS_PRIMARY_SKUS = [
    'WMH-002', 'WMH-010', 'WMH-021', 'WMH-029', 'WMH-042', 'WMH-044', 'WMH-045', 'WMH-046',
    'WMH-047', 'WMH-064', 'WMH-065', 'WMH-066', 'WMH-067', 'WMH-068', 'WMH-069', 'WMH-070',
    'WMH-077', 'WMH-078', 'WMH-092', 'WMH-098', 'WMH-120', 'WMH-121', 'WMH-122', 'WMH-123',
    'WMH-138', 'WMH-139', 'WMH-140', 'WMH-141', 'WMH-212', 'WMH-213', 'WMH-214', 'WMH-215',
    'WMH-216', 'WMH-217', 'WMH-218', 'WMH-219', 'WMH-220', 'WMH-221', 'WMH-222', 'WMH-223',
    'WMH-224', 'WMH-225', 'WMH-252', 'WMH-258', 'WMH-277', 'WMH-278', 'WMH-279', 'WMH-280',
    'WMH-281', 'WMH-283', 'WMH-287', 'WMH-322', 'WMH-347', 'WMH-348',
]


class Command(BaseCommand):
    """Create the Southern Kriels faction and reassign its products."""

    help = 'Creates Warmachine: Southern Kriels faction and reassigns its 54 products.'

    def handle(self, *args, **options):
        category = Category.objects.get(slug='warmachine')

        faction, created = Faction.objects.get_or_create(
            name='Southern Kriels',
            defaults={'slug': 'warmachine-southern-kriels', 'category': category},
        )
        if created:
            self.stdout.write(self.style.SUCCESS('Created faction: Southern Kriels'))
        else:
            self.stdout.write(f'Found faction: Southern Kriels (pk={faction.pk})')

        reassigned = 0
        missing = []
        for gw_sku in SOUTHERN_KRIELS_PRIMARY_SKUS:
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
            f'assign_warmachine_southern_kriels complete. {reassigned} product(s) reassigned.'
        ))
