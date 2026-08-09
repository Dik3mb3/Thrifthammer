from django.core.management.base import BaseCommand
from products.models import Product


class Command(BaseCommand):
    help = (
        'Aug 2026e: fix ebay_search_name for Space Marine Firestrike '
        'Servo-Turrets (48-28) -- was plural "Servo-Turrets", but every '
        'real eBay listing and GW\'s own official product name use the '
        'singular "Servo-Turret", so the search returned zero eBay '
        'results. Confirmed the fix resolves it: with the singular '
        'search name, the automated matcher finds a valid listing on its '
        'own (2026-08-07).'
    )

    def handle(self, *args, **options):
        updated = Product.objects.filter(gw_sku='48-28').update(
            ebay_search_name='Space Marine Firestrike Servo-Turret Warhammer'
        )
        self.stdout.write(f'48-28 ebay_search_name updated, rows={updated}')
        self.stdout.write(self.style.SUCCESS('apply_batch_fixes_aug2026e done'))
