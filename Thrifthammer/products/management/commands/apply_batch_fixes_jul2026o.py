from django.core.management.base import BaseCommand
from products.models import Product


class Command(BaseCommand):
    help = (
        'Jul 2026o: eBay negative keyword additions for Death Guard Plague '
        'Marines (43-50) -- blocks the Malignant Plaguecaster single-model '
        'listing and the whole "Kill Team" starter-set/single-figure family '
        'of listings that are a different product from the full squad box.'
    )

    def handle(self, *args, **options):
        fixes = [
            ('ebay_negative_keywords', '43-50', 'legions imperialis Resin 04-113 Proxies Foil belcher spewer Plaguecaster "kill team"'),
        ]

        for field, sku, value in fixes:
            updated = Product.objects.filter(gw_sku=sku).update(**{field: value})
            self.stdout.write(f'{sku} {field}=[{value}] rows={updated}')

        self.stdout.write(self.style.SUCCESS('apply_batch_fixes_jul2026o done'))
