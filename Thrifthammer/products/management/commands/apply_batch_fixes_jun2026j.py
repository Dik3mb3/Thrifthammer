from django.core.management.base import BaseCommand

from products.models import Product


class Command(BaseCommand):
    help = 'Jun 2026j: Cult Mechanicum eBay search name corrections for CM-001, CM-012, CM-014, CM-017'

    def handle(self, *args, **options):
        search_fixes = [
            ('CM-001', 'Combat Force Mechanicum Horus Heresy Warhammer'),
            ('CM-012', 'Mechanicum Tech-Thralls Covenant Warhammer Horus Heresy'),
            ('CM-014', 'Age of Darkness Armiger Warhammer Horus Heresy'),
            ('CM-017', 'Mechanicum Myrmidon Destructor Host Miniatures Warhammer'),
        ]
        for sku, name in search_fixes:
            updated = Product.objects.filter(gw_sku=sku).update(ebay_search_name=name)
            self.stdout.write(f'{sku} ebay_search_name=[{name}] rows={updated}')

        self.stdout.write(self.style.SUCCESS('apply_batch_fixes_jun2026j done'))
