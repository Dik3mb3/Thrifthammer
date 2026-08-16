"""
Management command: assign_warmachine_cryx

Second step of reorganizing the flat 348-product Warmachine category into
per-faction structure. Creates the "Cryx" Faction under the existing
Warmachine Category, and reassigns the 23 existing WMH-xxx products that
belong to it.

All 23 products from the user-supplied "Warmachine - Cryx.xlsx" already
exist in the original 348-product Warmachine batch -- no new products are
created here, only faction reassignment. This sheet had no eBay/Amazon
search name column, so ebay_search_name is left untouched.

Usage:
    python manage.py assign_warmachine_cryx
"""

from django.core.management.base import BaseCommand

from products.models import Category, Faction, Product

CRYX_SKUS = [
    'WMH-004', 'WMH-006', 'WMH-025', 'WMH-082', 'WMH-090',
    'WMH-233', 'WMH-235', 'WMH-250', 'WMH-254', 'WMH-256',
    'WMH-259', 'WMH-260', 'WMH-294', 'WMH-295', 'WMH-296',
    'WMH-297', 'WMH-298', 'WMH-299', 'WMH-300', 'WMH-301',
    'WMH-302', 'WMH-310', 'WMH-314',
]


class Command(BaseCommand):
    """Create the Cryx faction and reassign its products."""

    help = 'Creates Warmachine: Cryx faction and reassigns its 23 products.'

    def handle(self, *args, **options):
        category = Category.objects.get(slug='warmachine')

        faction, created = Faction.objects.get_or_create(
            name='Cryx',
            defaults={'slug': 'warmachine-cryx', 'category': category},
        )
        if created:
            self.stdout.write(self.style.SUCCESS('Created faction: Cryx'))
        else:
            self.stdout.write(f'Found faction: Cryx (pk={faction.pk})')

        reassigned = 0
        missing = []
        for gw_sku in CRYX_SKUS:
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
            f'assign_warmachine_cryx complete. {reassigned} product(s) reassigned.'
        ))
