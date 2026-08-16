"""
Management command: assign_warmachine_khador

Sixth step of reorganizing the flat 348-product Warmachine category into
per-faction structure. Creates the "Khador" Faction under the existing
Warmachine Category, and reassigns the 51 existing WMH-xxx products that
belong to it as their primary faction, plus one dual-tagged SKU.

All 52 rows from the user-supplied "Warmachine - Khador.xlsx" already exist
in the original 348-product Warmachine batch -- no new products are created
here, only faction reassignment (same pattern as Crucible Guard, Cryx,
Cygnar, Dark Operations, and Dusk before it).

WMH-261 "Two Player Starter Set" is already assigned to Cygnar (a two-player
starter box pairing two factions) and also appears on this Khador sheet.
User-confirmed 2026-08-15: keep Cygnar as the primary faction (unchanged)
and dual-tag Khador via secondary_factions, so it also surfaces on Khador's
product listing -- same mechanism already used for Cephalyx (Cryx/Dark
Operations) and Space Marine chapter squads.

Usage:
    python manage.py assign_warmachine_khador
"""

from django.core.management.base import BaseCommand

from products.models import Category, Faction, Product

KHADOR_PRIMARY_SKUS = [
    'WMH-011', 'WMH-014', 'WMH-027', 'WMH-039', 'WMH-043', 'WMH-055', 'WMH-056', 'WMH-057',
    'WMH-058', 'WMH-072', 'WMH-075', 'WMH-085', 'WMH-086', 'WMH-087', 'WMH-088', 'WMH-089',
    'WMH-091', 'WMH-174', 'WMH-175', 'WMH-176', 'WMH-177', 'WMH-178', 'WMH-179', 'WMH-180',
    'WMH-181', 'WMH-182', 'WMH-183', 'WMH-184', 'WMH-185', 'WMH-186', 'WMH-237', 'WMH-246',
    'WMH-247', 'WMH-253', 'WMH-262', 'WMH-282', 'WMH-289', 'WMH-292', 'WMH-307',
    'WMH-315', 'WMH-316', 'WMH-325', 'WMH-326', 'WMH-327', 'WMH-328', 'WMH-329', 'WMH-330',
    'WMH-331', 'WMH-332', 'WMH-333', 'WMH-335',
]

# ⚠ Dual-tag only: primary faction stays Cygnar (unchanged), Khador added
# via secondary_factions so it also appears on Khador's product listing.
KHADOR_SECONDARY_SKUS = [
    'WMH-261',
]


class Command(BaseCommand):
    """Create the Khador faction and reassign its products."""

    help = 'Creates Warmachine: Khador faction and reassigns its 52 products (51 primary + 1 dual-tagged).'

    def handle(self, *args, **options):
        category = Category.objects.get(slug='warmachine')

        faction, created = Faction.objects.get_or_create(
            name='Khador',
            defaults={'slug': 'warmachine-khador', 'category': category},
        )
        if created:
            self.stdout.write(self.style.SUCCESS('Created faction: Khador'))
        else:
            self.stdout.write(f'Found faction: Khador (pk={faction.pk})')

        reassigned = 0
        missing = []
        for gw_sku in KHADOR_PRIMARY_SKUS:
            try:
                product = Product.objects.get(gw_sku=gw_sku)
            except Product.DoesNotExist:
                missing.append(gw_sku)
                continue
            product.faction = faction
            product.save(update_fields=['faction'])
            reassigned += 1
            self.stdout.write(f'  reassigned: {product.name} ({gw_sku})')

        dual_tagged = 0
        for gw_sku in KHADOR_SECONDARY_SKUS:
            try:
                product = Product.objects.get(gw_sku=gw_sku)
            except Product.DoesNotExist:
                missing.append(gw_sku)
                continue
            product.secondary_factions.add(faction)
            dual_tagged += 1
            self.stdout.write(
                f'  dual-tagged (primary stays {product.faction}): {product.name} ({gw_sku})'
            )

        if missing:
            self.stdout.write(self.style.WARNING(f'  Not found, skipped: {", ".join(missing)}'))

        self.stdout.write(self.style.SUCCESS(
            f'assign_warmachine_khador complete. {reassigned} product(s) reassigned, '
            f'{dual_tagged} dual-tagged.'
        ))
