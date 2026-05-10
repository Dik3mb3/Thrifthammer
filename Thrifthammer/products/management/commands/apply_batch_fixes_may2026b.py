"""
Batch fix: eBay search name and negative keyword overrides for Tyranids and AM.

Sets ebay_search_name on products whose default name query returns 0 results
due to eBay search quirks (singular vs plural, overly specific names, etc.)
Sets ebay_negative_keywords on products that need per-SKU filtering.

Idempotent — safe to re-run.
"""

from django.core.management.base import BaseCommand

from products.models import Product


class Command(BaseCommand):
    help = 'Set eBay search name and negative keyword overrides for Tyranids and AM products.'

    def handle(self, *args, **options):
        updates = [
            # Tyranids — singular "Tyranid" + -bits kills results; plural works
            ('TY-001', {'ebay_search_name': 'Tyranids Barbgaunts'}),
            ('TY-014', {'ebay_search_name': 'Tyranids Horrors of the Hive', 'ebay_negative_keywords': 'neurotyrant'}),
            # Dual kits — search under the canonical kit name
            ('TY-023', {'ebay_search_name': 'Tyranid Carnifex'}),
            ('TY-027', {'ebay_search_name': 'Tyranid Carnifex'}),
            ('TY-028', {'ebay_search_name': 'Tyranid Tyrannocyte'}),
            ('TY-042', {'ebay_search_name': "Tyranids: Von Ryan's Leapers"}),
            ('TY-044', {'ebay_search_name': 'Tyranid Venomthropes'}),
            # Astra Militarum
            ('AM-012', {'ebay_search_name': 'Catachan Heavy Weapon Squad'}),
            ('AM-013', {'ebay_search_name': 'Catachan Heavy Weapon Squad'}),
            ('AM-035', {'ebay_search_name': 'Warhammer 40K Ministorum Priest', 'ebay_negative_keywords': 'Taddeus'}),
            ('AM-036', {'ebay_search_name': 'Astra Militarum Bullgryns'}),
            ('AM-040', {'ebay_search_name': 'Astra Militarum Baneblade'}),
            ('AM-042', {'ebay_search_name': 'Astra Militarum Baneblade'}),
            ('AM-043', {'ebay_search_name': 'Astra Militarum Baneblade'}),
        ]

        updated = 0
        for gw_sku, fields in updates:
            rows = Product.objects.filter(gw_sku=gw_sku).update(**fields)
            if rows:
                updated += 1
                self.stdout.write(f'  [ok] {gw_sku}')
            else:
                self.stdout.write(self.style.WARNING(f'  [skip] {gw_sku} not found'))

        self.stdout.write(self.style.SUCCESS(f'\nDone! Updated {updated} products.'))
