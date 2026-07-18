from django.core.management.base import BaseCommand
from products.models import Product


class Command(BaseCommand):
    help = (
        'Jul 2026m: eBay negative keyword additions -- Death Guard Plague '
        'Marines (43-50) blocks a separately-sold Plague Belcher weapon '
        'part; Seraphon Skinks (SR-022) blocks a listing whose title is '
        'prefixed with the seller\'s own internal SKU code "8584C".'
    )

    def handle(self, *args, **options):
        fixes = [
            ('ebay_negative_keywords', '43-50', 'legions imperialis Resin 04-113 Proxies Foil belcher'),
            ('ebay_negative_keywords', 'SR-022', '100th 1926 TShirt Plushie Plush legions imperialis Resin 04-113 Proxies Foil 8584C'),
        ]

        for field, sku, value in fixes:
            updated = Product.objects.filter(gw_sku=sku).update(**{field: value})
            self.stdout.write(f'{sku} {field}=[{value}] rows={updated}')

        self.stdout.write(self.style.SUCCESS('apply_batch_fixes_jul2026m done'))
