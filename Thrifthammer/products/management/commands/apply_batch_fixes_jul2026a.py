from django.core.management.base import BaseCommand
from products.models import Product


class Command(BaseCommand):
    help = 'Jul 2026a: eBay search name fix for AGA-022'

    def handle(self, *args, **options):
        fixes = [
            ('ebay_search_name', 'AGA-022', 'Warhammer 40k Armageddon ORK Army Half of Launch Box'),
        ]

        for field, sku, value in fixes:
            updated = Product.objects.filter(gw_sku=sku).update(**{field: value})
            self.stdout.write(f'{sku} {field}=[{value}] rows={updated}')

        self.stdout.write(self.style.SUCCESS('apply_batch_fixes_jul2026a done'))
