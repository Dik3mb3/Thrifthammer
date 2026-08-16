"""
Management command: assign_warmachine_cygnar

Third step of reorganizing the flat 348-product Warmachine category into
per-faction structure. Creates the "Cygnar" Faction under the existing
Warmachine Category, and reassigns the 49 existing WMH-xxx products that
belong to it.

All 49 products from the user-supplied "Warmachine - Cygnar.xlsx" already
exist in the original 348-product Warmachine batch -- no new products are
created here, only faction reassignment. This sheet had no eBay/Amazon
search name column, so ebay_search_name is left untouched.

Usage:
    python manage.py assign_warmachine_cygnar
"""

from django.core.management.base import BaseCommand

from products.models import Category, Faction, Product

CYGNAR_SKUS = [
    'WMH-030', 'WMH-034', 'WMH-035', 'WMH-036', 'WMH-038', 'WMH-049',
    'WMH-050', 'WMH-051', 'WMH-052', 'WMH-071', 'WMH-073', 'WMH-074',
    'WMH-079', 'WMH-080', 'WMH-081', 'WMH-083', 'WMH-084', 'WMH-102',
    'WMH-142', 'WMH-143', 'WMH-144', 'WMH-145', 'WMH-146', 'WMH-147',
    'WMH-148', 'WMH-149', 'WMH-150', 'WMH-151', 'WMH-152', 'WMH-153',
    'WMH-154', 'WMH-155', 'WMH-156', 'WMH-234', 'WMH-236', 'WMH-255',
    'WMH-261', 'WMH-267', 'WMH-286', 'WMH-291', 'WMH-304', 'WMH-305',
    'WMH-306', 'WMH-308', 'WMH-309', 'WMH-311', 'WMH-312', 'WMH-313',
    'WMH-324',
]


class Command(BaseCommand):
    """Create the Cygnar faction and reassign its products."""

    help = 'Creates Warmachine: Cygnar faction and reassigns its 49 products.'

    def handle(self, *args, **options):
        category = Category.objects.get(slug='warmachine')

        faction, created = Faction.objects.get_or_create(
            name='Cygnar',
            defaults={'slug': 'warmachine-cygnar', 'category': category},
        )
        if created:
            self.stdout.write(self.style.SUCCESS('Created faction: Cygnar'))
        else:
            self.stdout.write(f'Found faction: Cygnar (pk={faction.pk})')

        reassigned = 0
        missing = []
        for gw_sku in CYGNAR_SKUS:
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
            f'assign_warmachine_cygnar complete. {reassigned} product(s) reassigned.'
        ))
