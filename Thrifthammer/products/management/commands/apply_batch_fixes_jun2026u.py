from django.core.management.base import BaseCommand
from products.models import Product


class Command(BaseCommand):
    help = 'Jun 2026u: add Goblin eBay negative keyword to OGT-009 Orc Bosses'

    def handle(self, *args, **options):
        updated = Product.objects.filter(gw_sku='OGT-009').update(
            ebay_negative_keywords='legions imperialis Resin 04-113 Proxies Foil Goblin'
        )
        self.stdout.write(f'OGT-009 ebay_negative_keywords updated rows={updated}')
        self.stdout.write(self.style.SUCCESS('apply_batch_fixes_jun2026u done'))
