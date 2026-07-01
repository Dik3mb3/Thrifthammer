from django.core.management.base import BaseCommand

from products.models import Product


class Command(BaseCommand):
    help = 'Jun 2026n: Add Imperialis eBay negative keyword to all Horus Heresy SKUs'

    def handle(self, *args, **options):
        factions = ['astartes-legions', 'cult-mechanicum', 'forces-of-the-emperor']
        updated = 0
        for product in Product.objects.filter(faction__slug__in=factions):
            current = (product.ebay_negative_keywords or '').strip()
            if 'Imperialis' not in current:
                new_kw = (current + ' Imperialis').strip() if current else 'Imperialis'
                Product.objects.filter(pk=product.pk).update(ebay_negative_keywords=new_kw)
                self.stdout.write(f'{product.gw_sku} [{product.name[:45]}] → [{new_kw}]')
                updated += 1
        self.stdout.write(self.style.SUCCESS(
            f'apply_batch_fixes_jun2026n done — {updated} products updated'
        ))
