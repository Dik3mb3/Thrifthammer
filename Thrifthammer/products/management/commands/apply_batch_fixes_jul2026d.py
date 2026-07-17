from django.core.management.base import BaseCommand
from products.models import Product


class Command(BaseCommand):
    help = 'Jul 2026d: eBay negative keyword additions across BattleTech and other SKUs'

    def handle(self, *args, **options):
        fixes = [
            ('ebay_negative_keywords', 'BT-105', 'legions imperialis Resin 04-113 Proxies Foil Rare Victor'),
            ('ebay_negative_keywords', 'BT-080', 'legions imperialis Resin 04-113 Proxies Foil Charger'),
            ('ebay_negative_keywords', 'BT-022', 'legions imperialis Resin 04-113 Proxies Foil Atlas'),
            ('ebay_negative_keywords', 'BT-068', 'legions imperialis Resin 04-113 Proxies Foil Jumping StarSlayer'),
            ('ebay_negative_keywords', 'BT-103', 'legions imperialis Resin 04-113 Proxies Foil Direct'),
            ('ebay_negative_keywords', 'BT-011', 'legions imperialis Resin 04-113 Proxies Foil 3rd Lot Separated'),
            ('ebay_negative_keywords', 'BT-030', 'legions imperialis Resin 04-113 Proxies Foil Rifleman'),
            ('ebay_negative_keywords', 'BT-004', 'legions imperialis Resin 04-113 Proxies Foil Map Pack'),
            ('ebay_negative_keywords', 'BT-056', 'legions imperialis Resin 04-113 Proxies Foil Objectives'),
            ('ebay_negative_keywords', 'BT-083', 'legions imperialis Resin 04-113 Proxies Foil Mash Truck'),
            ('ebay_negative_keywords', 'BT-024', 'legions imperialis Resin 04-113 Proxies Foil Proliferation Counters'),
            ('ebay_negative_keywords', 'BT-025', 'legions imperialis Resin 04-113 Proxies Foil Special CGL Scale'),
            ('ebay_negative_keywords', 'BT-019', 'legions imperialis Resin 04-113 Proxies Foil Alternate Scales'),
            ('ebay_negative_keywords', 'BT-109', 'legions imperialis Resin 04-113 Proxies Foil Direct'),
            ('ebay_negative_keywords', 'IA-013', 'legions imperialis Resin 04-113 Proxies Foil Dice'),
            ('ebay_negative_keywords', 'prod3940162', 'legions imperialis Resin 04-113 D&D 5e 100th 1926 TShirt Plushie Plush Proxies Foil G619'),
            ('ebay_negative_keywords', '47-08', 'legions imperialis Resin 04-113 Proxies Foil Prefectus'),
            ('ebay_negative_keywords', '53-27', 'logo ny rangers york parts replacement dermaplane Resin 04-113 Proxies Foil Rock'),
            ('ebay_negative_keywords', 'NM-006', 'redemptionists Foil Dice'),
            ('ebay_negative_keywords', 'BB-009', 'Dice Proxies Foil Treeman'),
        ]

        for field, sku, value in fixes:
            updated = Product.objects.filter(gw_sku=sku).update(**{field: value})
            self.stdout.write(f'{sku} {field}=[{value}] rows={updated}')

        self.stdout.write(self.style.SUCCESS('apply_batch_fixes_jul2026d done'))
