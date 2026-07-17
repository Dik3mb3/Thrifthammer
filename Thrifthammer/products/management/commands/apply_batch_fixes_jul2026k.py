from django.core.management.base import BaseCommand
from products.models import Product


class Command(BaseCommand):
    help = (
        'Jul 2026k: eBay negative keyword additions across Kharadron '
        'Overlords, Stormcast Eternals, BattleTech, Marvel Crisis '
        'Protocol, and Star Wars: Legion SKUs; fix Space Marine '
        'Terminator Squad (48-06) search name self-cancelling against '
        'its own "assault" negative keyword; match 48-23 (Space Marine '
        'Predator) search name to sibling kit 48-124 (Predator '
        'Destructor).'
    )

    def handle(self, *args, **options):
        fixes = [
            ('ebay_negative_keywords', 'KO-010', 'legions imperialis Resin 04-113 Proxies Foil Gunhauler'),
            ('ebay_negative_keywords', 'SE-019', 'legions imperialis Resin 04-113 100th 1926 TShirt Plushie Plush Proxies Foil Knight Judicator'),
            ('ebay_negative_keywords', 'BT-101', 'legions imperialis Resin 04-113 Proxies Foil Charger'),
            ('ebay_negative_keywords', 'BT-080', 'legions imperialis Resin 04-113 Proxies Foil Charger Merlin'),
            ('ebay_negative_keywords', 'BT-056', 'legions imperialis Resin 04-113 Proxies Foil Objectives Assault Cavalry'),
            ('ebay_negative_keywords', 'BT-099', 'legions imperialis Resin 04-113 Proxies Foil Heavy'),
            ('ebay_negative_keywords', 'MCP-064', 'Cassandra Nova'),
            ('ebay_negative_keywords', 'MCP-020', 'from'),
            ('ebay_negative_keywords', 'MCP-036', 'Missing'),
            ('ebay_negative_keywords', 'MCP-004', 'Support'),
            ('ebay_negative_keywords', 'MCP-003', 'from'),
            ('ebay_negative_keywords', 'MCP-006', 'from'),
            ('ebay_negative_keywords', 'SWL-054', 'Promo'),
            ('ebay_negative_keywords', 'SWL-030', 'expansion'),
            ('ebay_negative_keywords', 'SWL-032', 'expansion'),
            ('ebay_negative_keywords', 'SWL-056', 'expansion'),
            ('ebay_negative_keywords', 'SWL-087', 'expansion'),
            ('ebay_search_name', '48-06', 'Space Marine Terminator Squad'),
            ('ebay_negative_keywords', '48-06', 'assault legions imperialis Resin 04-113 Proxies Foil Chaos'),
            ('ebay_search_name', '48-23', 'Predator Destructor'),
        ]

        for field, sku, value in fixes:
            updated = Product.objects.filter(gw_sku=sku).update(**{field: value})
            self.stdout.write(f'{sku} {field}=[{value}] rows={updated}')

        self.stdout.write(self.style.SUCCESS('apply_batch_fixes_jul2026k done'))
