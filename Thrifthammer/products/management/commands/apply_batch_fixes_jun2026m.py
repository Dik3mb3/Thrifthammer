from django.core.management.base import BaseCommand

from products.models import Product


class Command(BaseCommand):
    help = 'Jun 2026m: FOE-012 Hermes Sentinel Squadron negative keywords to block single-mini listings'

    def handle(self, *args, **options):
        updated = Product.objects.filter(gw_sku='FOE-012').update(
            ebay_negative_keywords='x1 1x',
        )
        self.stdout.write(f'FOE-012 ebay_negative_keywords=[x1 1x] rows={updated}')
        self.stdout.write(self.style.SUCCESS('apply_batch_fixes_jun2026m done'))
