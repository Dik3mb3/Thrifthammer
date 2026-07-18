from django.core.management.base import BaseCommand
from products.models import Product


class Command(BaseCommand):
    help = (
        'Jul 2026q: eBay negative keyword additions for Star Wars: Legion '
        'SKUs (SWL-110, SWL-086, SWL-092), and an ebay_search_name fix for '
        'SWL-032 (B2 Super Rocket Battle Droids), whose search name was '
        'missing "Rocket" and was searching identically to SWL-110 (the '
        'non-Rocket B2 Super Battle Droids).'
    )

    def handle(self, *args, **options):
        fixes = [
            ('ebay_negative_keywords', 'SWL-110', 'legions imperialis Resin 04-113 Proxies Foil expansion'),
            ('ebay_negative_keywords', 'SWL-086', 'legions imperialis Resin 04-113 Proxies Foil sealed expansion'),
            ('ebay_negative_keywords', 'SWL-092', 'legions imperialis Resin 04-113 Proxies Foil expansion'),
            ('ebay_search_name', 'SWL-032', 'Star Wars: Legion - B2 Super Rocket Battle Droids'),
        ]

        for field, sku, value in fixes:
            updated = Product.objects.filter(gw_sku=sku).update(**{field: value})
            self.stdout.write(f'{sku} {field}=[{value}] rows={updated}')

        self.stdout.write(self.style.SUCCESS('apply_batch_fixes_jul2026q done'))
