from django.core.management.base import BaseCommand

from products.models import Product


class Command(BaseCommand):
    help = 'Jun 2026l: FOE-011 Arvus Lighter LI keyword fix; FOE-012 Hermes search name'

    def handle(self, *args, **options):
        # FOE-011: exclude Legions Imperialis Epic-scale listings; refine search name
        updated = Product.objects.filter(gw_sku='FOE-011').update(
            ebay_negative_keywords='Imperialis',
            ebay_search_name='Arvus Lighter Solar Auxilia Warhammer Horus Heresy',
        )
        self.stdout.write(f'FOE-011 ebay_negative_keywords=[Imperialis] ebay_search_name=[Arvus Lighter Solar Auxilia Warhammer Horus Heresy] rows={updated}')

        # FOE-012: refined search name to improve match rate
        updated = Product.objects.filter(gw_sku='FOE-012').update(
            ebay_search_name='Solar Auxilia Hermes Sentinel Squadron Warhammer Horus Heresy',
        )
        self.stdout.write(f'FOE-012 ebay_search_name=[Solar Auxilia Hermes Sentinel Squadron Warhammer Horus Heresy] rows={updated}')

        self.stdout.write(self.style.SUCCESS('apply_batch_fixes_jun2026l done'))
