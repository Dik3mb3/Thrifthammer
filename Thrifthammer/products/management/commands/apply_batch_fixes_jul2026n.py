from django.core.management.base import BaseCommand
from products.models import Product


class Command(BaseCommand):
    help = (
        'Jul 2026n: eBay negative keyword addition for Death Guard Plague '
        'Marines (43-50) -- blocks a separately-sold Plague Spewer weapon '
        'part listing that surfaced after the "belcher" exclusion in '
        'jul2026m blocked a different weapon-part listing.'
    )

    def handle(self, *args, **options):
        fixes = [
            ('ebay_negative_keywords', '43-50', 'legions imperialis Resin 04-113 Proxies Foil belcher spewer'),
        ]

        for field, sku, value in fixes:
            updated = Product.objects.filter(gw_sku=sku).update(**{field: value})
            self.stdout.write(f'{sku} {field}=[{value}] rows={updated}')

        self.stdout.write(self.style.SUCCESS('apply_batch_fixes_jul2026n done'))
