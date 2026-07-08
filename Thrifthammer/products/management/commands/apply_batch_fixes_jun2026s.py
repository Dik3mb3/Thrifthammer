from django.core.management.base import BaseCommand

from products.models import Product


class Command(BaseCommand):
    help = 'Jun 2026s: add "hag queen" eBay negative keyword to DOK-003 and DOK-004'

    def handle(self, *args, **options):
        fixes = [
            ('DOK-004', 'Bloodwrack Melusai Foil "hag queen"'),
            ('DOK-003', 'Bloodwrack Melusai Foil "hag queen"'),
        ]
        for sku, value in fixes:
            updated = Product.objects.filter(gw_sku=sku).update(ebay_negative_keywords=value)
            self.stdout.write(f'{sku} ebay_negative_keywords=[{value}] rows={updated}')

        self.stdout.write(self.style.SUCCESS('apply_batch_fixes_jun2026s done'))
