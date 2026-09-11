"""
Management command: assign_warmachine_orgoth_sea_raiders

Ninth step of reorganizing the flat 348-product Warmachine category into
per-faction structure. Creates the "Orgoth Sea Raiders" Faction under the
existing Warmachine Category, and reassigns the 28 existing WMH-xxx
products that belong to it as their primary faction (same pattern as
Crucible Guard, Cryx, Cygnar, Dark Operations, Dusk, Khador, Southern
Kriels, and Khymaera before it).

All 28 rows from the user-supplied "Orgoth - Warmachine - Steamforged.xlsx"
already exist in the original 348-product Warmachine batch -- no new
products are created here, only faction reassignment. Every title matched
an existing product by exact name (no collisions, no unmatched rows, no
cross-faction naming collisions like Southern Kriels/Khymaera's Shadows &
Scum), and every row's spreadsheet price matched the existing Steamforged
Games CurrentPrice exactly -- cross-checked before writing this command.

WMH-101 "The Graveborn Command Cadre (HIPS)" is included per the sheet --
"The Graveborn" is apparently a sub-theme within Orgoth Sea Raiders (same
pattern as Southern Kriels' Kithguard/Brineblood sub-groups), not a
separate faction.

Usage:
    python manage.py assign_warmachine_orgoth_sea_raiders
"""

from django.core.management.base import BaseCommand

from products.models import Category, Faction, Product

ORGOTH_PRIMARY_SKUS = [
    'WMH-037', 'WMH-053', 'WMH-054', 'WMH-101', 'WMH-157', 'WMH-158', 'WMH-159', 'WMH-160',
    'WMH-161', 'WMH-162', 'WMH-163', 'WMH-164', 'WMH-165', 'WMH-166', 'WMH-167', 'WMH-168',
    'WMH-169', 'WMH-170', 'WMH-171', 'WMH-172', 'WMH-173', 'WMH-271', 'WMH-272', 'WMH-273',
    'WMH-274', 'WMH-275', 'WMH-276', 'WMH-290',
]


class Command(BaseCommand):
    """Create the Orgoth Sea Raiders faction and reassign its products."""

    help = 'Creates Warmachine: Orgoth Sea Raiders faction and reassigns its 28 products.'

    def handle(self, *args, **options):
        category = Category.objects.get(slug='warmachine')

        faction, created = Faction.objects.get_or_create(
            name='Orgoth Sea Raiders',
            defaults={'slug': 'warmachine-orgoth-sea-raiders', 'category': category},
        )
        if created:
            self.stdout.write(self.style.SUCCESS('Created faction: Orgoth Sea Raiders'))
        else:
            self.stdout.write(f'Found faction: Orgoth Sea Raiders (pk={faction.pk})')

        reassigned = 0
        missing = []
        for gw_sku in ORGOTH_PRIMARY_SKUS:
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
            f'assign_warmachine_orgoth_sea_raiders complete. {reassigned} product(s) reassigned.'
        ))
