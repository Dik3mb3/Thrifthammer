from django.core.management.base import BaseCommand
from products.models import Product


class Command(BaseCommand):
    help = 'Jun 2026v: update AGA-019 ebay_search_name for Core Rulebook'

    def handle(self, *args, **options):
        updated = Product.objects.filter(gw_sku='AGA-019').update(
            ebay_search_name='Warhammer 40k 11th Armageddon Core Rules'
        )
        self.stdout.write(f'AGA-019 ebay_search_name updated rows={updated}')
        self.stdout.write(self.style.SUCCESS('apply_batch_fixes_jun2026v done'))
