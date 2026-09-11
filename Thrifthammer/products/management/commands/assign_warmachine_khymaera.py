"""
Management command: assign_warmachine_khymaera

Eighth step of reorganizing the flat 348-product Warmachine category into
per-faction structure. Creates the "Khymaera" Faction under the existing
Warmachine Category, and reassigns the 25 existing WMH-xxx products that
belong to it as their primary faction, plus one dual-tagged SKU (same
pattern as Crucible Guard, Cryx, Cygnar, Dark Operations, Dusk, Khador, and
Southern Kriels before it).

All 26 rows from the user-supplied "Khymaera - Warmachine - Steamforge.xlsx"
already exist in the original 348-product Warmachine batch -- no new
products are created here, only faction reassignment. Every title matched
an existing product by exact name (no collisions, no unmatched rows), and
every row's spreadsheet price matched the existing Steamforged Games
CurrentPrice exactly -- cross-checked before writing this command.

WMH-078 "Shadows & Scum" is already primary-assigned to Southern Kriels
(same title, same $119.99 price appears on that faction's own sheet too --
a genuine mercenary/allied unit sold for use by both armies, not a
duplicate-title coincidence). User-confirmed 2026-09-09: keep Southern
Kriels as the primary faction (unchanged) and dual-tag Khymaera via
secondary_factions, so it also surfaces on Khymaera's product listing --
same mechanism already used for WMH-261 (Two Player Starter Set,
Cygnar/Khador) in assign_warmachine_khador.py.

Usage:
    python manage.py assign_warmachine_khymaera
"""

from django.core.management.base import BaseCommand

from products.models import Category, Faction, Product

KHYMAERA_PRIMARY_SKUS = [
    'WMH-023', 'WMH-028', 'WMH-226', 'WMH-227', 'WMH-228', 'WMH-229', 'WMH-230', 'WMH-231',
    'WMH-232', 'WMH-238', 'WMH-239', 'WMH-240', 'WMH-241', 'WMH-242', 'WMH-243', 'WMH-244',
    'WMH-245', 'WMH-248', 'WMH-249', 'WMH-257', 'WMH-269', 'WMH-270', 'WMH-284', 'WMH-293',
    'WMH-303',
]

# Dual-tag only: primary faction stays Southern Kriels (unchanged), Khymaera
# added via secondary_factions so it also appears on Khymaera's product listing.
KHYMAERA_SECONDARY_SKUS = [
    'WMH-078',
]


class Command(BaseCommand):
    """Create the Khymaera faction and reassign its products."""

    help = 'Creates Warmachine: Khymaera faction and reassigns its 26 products (25 primary + 1 dual-tagged).'

    def handle(self, *args, **options):
        category = Category.objects.get(slug='warmachine')

        faction, created = Faction.objects.get_or_create(
            name='Khymaera',
            defaults={'slug': 'warmachine-khymaera', 'category': category},
        )
        if created:
            self.stdout.write(self.style.SUCCESS('Created faction: Khymaera'))
        else:
            self.stdout.write(f'Found faction: Khymaera (pk={faction.pk})')

        reassigned = 0
        missing = []
        for gw_sku in KHYMAERA_PRIMARY_SKUS:
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
        for gw_sku in KHYMAERA_SECONDARY_SKUS:
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
            f'assign_warmachine_khymaera complete. {reassigned} product(s) reassigned, '
            f'{dual_tagged} dual-tagged.'
        ))
