"""
Seed Games Workshop UK prices for Space Wolves.

Run once on Railway startup via Procfile.  Safe to re-run — idempotent.
"""
from decimal import Decimal

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Product, Retailer

_GW_UK_SLUG = 'games-workshop-uk'

# (gw_sku, label, gbp_price, gw_uk_url, in_stock)
_PRICES = [
    ('53-02',  'Space Wolves Ragnar Blackmane',      Decimal('29.50'),  'https://www.warhammer.com/en-GB/shop/Ragnar-Blackmane-2020',                         True),
    ('53-06',  'Space Wolves Grey Hunters',           Decimal('40.00'),  'https://www.warhammer.com/en-GB/shop/space-wolves-grey-hunters-2025',                True),
    ('53-08',  'Space Wolves Wolf Guard Terminators', Decimal('42.50'),  'https://www.warhammer.com/en-GB/shop/space-wolves-wolf-guard-terminators-2025',      True),
    ('53-10',  'Space Wolves Thunderwolf Cavalry',    Decimal('40.00'),  'https://www.warhammer.com/en-GB/shop/Thunderwolf-Cavalry-2020',                      True),
    ('53-20',  'Space Wolves Combat Patrol',          Decimal('105.00'), 'https://www.warhammer.com/en-GB/shop/combat-patrol-space-wolves-2025',               True),
    ('53-21',  'Arjac Rockfist',                      Decimal('29.00'),  'https://www.warhammer.com/en-GB/shop/space-wolves-arjac-rockfist-2025',              True),
    ('53-22',  'Bjorn the Fell-handed',               Decimal('40.00'),  'https://www.warhammer.com/en-GB/shop/Bjorn-the-Fellhanded-2020',                     True),
    ('53-23',  'Blood Claws',                         Decimal('40.00'),  'https://www.warhammer.com/en-GB/shop/space-wolves-blood-claws-2025',                 True),
    ('53-24',  'Codex Supplement: Space Wolves',      Decimal('21.50'),  'https://www.warhammer.com/en-GB/shop/codex-supplement-space-wolves-2025-eng',        True),
    ('53-25',  'Fenrisian Wolves',                    Decimal('27.00'),  'https://www.warhammer.com/en-GB/shop/Fenrisian-Wolves-2020',                         True),
    ('53-26',  'Iron Priest',                         Decimal('25.00'),  'https://www.warhammer.com/en-GB/shop/Space-Wolves-Iron-Priest-2020',                 True),
    ('53-27',  'Logan Grimnar',                       Decimal('44.50'),  'https://www.warhammer.com/en-GB/shop/space-wolves-logan-grimnar-2025',               True),
    ('53-28',  'Murderfang',                          Decimal('40.00'),  'https://www.warhammer.com/en-GB/shop/Murderfang-2020',                               True),
    ('53-29',  'Njal Stormcaller',                    Decimal('29.00'),  'https://www.warhammer.com/en-GB/shop/space-wolves-njal-stormcaller-2025',            True),
    ('53-30',  'Space Wolves Venerable Dreadnought',  Decimal('40.00'),  'https://www.warhammer.com/en-GB/shop/Space-Wolves-Venerable-Dreadnought-2020',       True),
    ('53-31',  'Ulrik the Slayer',                    Decimal('25.00'),  'https://www.warhammer.com/en-GB/shop/Space-Wolves-Ulrik-the-Slayer-2020',            True),
    ('53-32',  'Wolf Guard Battle Leader',            Decimal('27.00'),  'https://www.warhammer.com/en-GB/shop/space-wolves-wolf-guard-battle-leader-2025',    True),
    ('53-33',  'Wolf Guard Headtakers',               Decimal('42.50'),  'https://www.warhammer.com/en-GB/shop/space-wolves-wolf-guard-headtakers-2025',       True),
    ('53-34',  'Wolf Priest',                         Decimal('26.00'),  'https://www.warhammer.com/en-GB/shop/space-wolves-wolf-priest-2025',                 True),
    ('53-35',  'Wulfen',                              Decimal('40.00'),  'https://www.warhammer.com/en-GB/shop/Space-Wolves-Wulfen-2020',                      True),
    ('53-36',  'Wulfen Dreadnought',                  Decimal('40.00'),  'https://www.warhammer.com/en-GB/shop/wulfen-dreadnought-2025',                       True),
    ('KT-026', 'Kill Team: Wolf Scouts',              Decimal('42.50'),  'https://www.warhammer.com/en-GB/shop/kill-team-wolf-scouts-2026',                    True),
]


class Command(BaseCommand):
    help = 'Seed GW UK prices for Space Wolves. Idempotent.'

    def handle(self, *args, **options):
        retailer, created = Retailer.objects.get_or_create(
            slug=_GW_UK_SLUG,
            defaults={
                'name': 'Games Workshop UK',
                'website': 'https://www.warhammer.com/en-GB/',
                'country': 'UK',
                'is_active': True,
                'is_uk': True,
            },
        )
        if created:
            self.stdout.write(f'Created retailer: {retailer.name}')

        seeded = 0
        skipped = 0

        for sku, label, gbp_price, url, in_stock in _PRICES:
            products = list(Product.objects.filter(gw_sku=sku))
            if not products:
                self.stdout.write(f'  SKIP {sku} ({label}) — not found in DB')
                skipped += 1
                continue
            for product in products:
                product.msrp_gbp = gbp_price
                product.save(update_fields=['msrp_gbp'])
                CurrentPrice.objects.update_or_create(
                    product=product,
                    retailer=retailer,
                    defaults={
                        'price': gbp_price,
                        'url': url,
                        'in_stock': in_stock,
                        'not_available': False,
                    },
                )
                seeded += 1

        self.stdout.write(f'Seeded {seeded} Space Wolves GW UK prices. Skipped: {skipped}.')
