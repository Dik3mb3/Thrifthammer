from django.core.management.base import BaseCommand
from products.models import Product


class Command(BaseCommand):
    help = 'Jul 2026b: eBay negative keyword fix for P-KHORNE-BLOODCRUSHERS'

    def handle(self, *args, **options):
        fixes = [
            ('ebay_negative_keywords', 'P-KHORNE-BLOODCRUSHERS', 'Sealed legions imperialis Resin 04-113 D&D 5e 100th 1926 TShirt Plushie Plush Proxies Foil 3'),
        ]

        for field, sku, value in fixes:
            updated = Product.objects.filter(gw_sku=sku).update(**{field: value})
            self.stdout.write(f'{sku} {field}=[{value}] rows={updated}')

        self.stdout.write(self.style.SUCCESS('apply_batch_fixes_jul2026b done'))
