"""
Batch fix: eBay negative keyword additions for Swooping Hawks and Warp Spiders.

Idempotent — safe to re-run.
"""

from django.core.management.base import BaseCommand

from products.models import Product


class Command(BaseCommand):
    help = 'Add eBay negative keywords for Swooping Hawks and Warp Spiders.'

    def handle(self, *args, **options):
        updates = [
            ('P-203614', {'ebay_negative_keywords': 'legions imperialis Resin 04-113 D&D 5e Winged Autarch'}),
            ('P-203611', {'ebay_negative_keywords': 'legions imperialis Resin 04-113 D&D 5e Lhykhis'}),
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
