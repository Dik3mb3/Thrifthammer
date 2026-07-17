from django.core.management.base import BaseCommand
from products.models import Product


class Command(BaseCommand):
    help = 'Jul 2026h: eBay search name corrections for Star Wars: Legion no-match SKUs'

    def handle(self, *args, **options):
        fixes = [
            ('ebay_search_name', 'SWL-032', 'Star Wars: Legion - B2 Super Battle Droids'),
            ('ebay_search_name', 'SWL-053', 'Star Wars Legion Red Attack Dice'),
            ('ebay_search_name', 'SWL-057', 'Upgrade Card Pack Star Wars Legion'),
            ('ebay_search_name', 'SWL-094', 'Star Wars: Legion - Separatist Alliance Command Card Pack'),
            ('ebay_search_name', 'SWL-096', 'Star Wars Legion Rebel Alliance Command Card Pack'),
            ('ebay_search_name', 'SWL-100', 'Star Wars: Legion - Battle Card Pack'),
            ('ebay_search_name', 'SWL-102', 'Star Wars Legion Battle Deck Card Pack II'),
        ]

        for field, sku, value in fixes:
            updated = Product.objects.filter(gw_sku=sku).update(**{field: value})
            self.stdout.write(f'{sku} {field}=[{value}] rows={updated}')

        self.stdout.write(self.style.SUCCESS('apply_batch_fixes_jul2026h done'))
