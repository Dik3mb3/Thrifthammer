from django.core.management.base import BaseCommand

from products.models import Product


class Command(BaseCommand):
    help = 'Jun 2026k: CM-001 Legions/Imperialis negative keywords; CM-014 Armiger Warglaives search name'

    def handle(self, *args, **options):
        # CM-001: exclude Legions Imperialis listings (Epic-scale game, not HH 28mm)
        updated = Product.objects.filter(gw_sku='CM-001').update(
            ebay_negative_keywords='Legions Imperialis',
        )
        self.stdout.write(f'CM-001 ebay_negative_keywords=[Legions Imperialis] rows={updated}')

        # CM-014: same kit as CM-015 — align search name to the Warglaives listing
        updated = Product.objects.filter(gw_sku='CM-014').update(
            ebay_search_name='Age of Darkness Armiger Warglaives Horus Heresy',
        )
        self.stdout.write(f'CM-014 ebay_search_name=[Age of Darkness Armiger Warglaives Horus Heresy] rows={updated}')

        self.stdout.write(self.style.SUCCESS('apply_batch_fixes_jun2026k done'))
