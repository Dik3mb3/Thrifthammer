from django.core.management.base import BaseCommand
from products.models import Product


class Command(BaseCommand):
    help = (
        'Jul 2026r: eBay negative keyword additions -- 48-25 (Space Marine '
        'Whirlwind) gets "Legiones" to stop matching Horus Heresy Legiones '
        'Astartes Whirlwind listings; 48-07 (Space Marine Tactical Squad) '
        'gets "Horus" to stop matching Horus Heresy-era Tactical Squad '
        'listings; 53-21 (Arjac Rockfist) gets "finecast" to stop matching '
        'the current Finecast resin listing while still allowing other '
        'listings from the same seller.'
    )

    def handle(self, *args, **options):
        fixes = [
            ('ebay_negative_keywords', '48-25', '1999 vintage legions imperialis scorpus Resin 04-113 Proxies Foil Legiones'),
            ('ebay_negative_keywords', '48-07', 'power fist legions imperialis Resin 04-113 Proxies Foil Horus'),
            ('ebay_negative_keywords', '53-21', 'NIB Proxies Foil finecast'),
        ]

        for field, sku, value in fixes:
            updated = Product.objects.filter(gw_sku=sku).update(**{field: value})
            self.stdout.write(f'{sku} {field}=[{value}] rows={updated}')

        self.stdout.write(self.style.SUCCESS('apply_batch_fixes_jul2026r done'))
