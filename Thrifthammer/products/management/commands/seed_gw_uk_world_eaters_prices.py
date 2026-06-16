"""
Seed Games Workshop UK prices for World Eaters.

Run once on Railway startup via Procfile.  Safe to re-run — idempotent.
"""
from decimal import Decimal

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Product, Retailer

_GW_UK_SLUG = 'games-workshop-uk'

# (gw_sku, label, gbp_price, gw_uk_url, in_stock)
_PRICES = [
    ('43-04',                   'World Eaters Angron',                  Decimal('105.50'),  'https://www.warhammer.com/en-GB/shop/world-eaters-angron-daemon-primarch-of-khorne-2023', True),
    ('43-60',                   'World Eaters Berzerkers',              Decimal('42.50'),   'https://www.warhammer.com/en-GB/shop/world-eaters-khorne-berserkers-2023',                True),
    ('43-62',                   'World Eaters Eightbound',              Decimal('40.00'),   'https://www.warhammer.com/en-GB/shop/world-eaters-eightbound-2023',                       True),
    ('43-64',                   'World Eaters Lord on Juggernaut',      Decimal('42.50'),   'https://www.warhammer.com/en-GB/shop/world-eaters-lord-on-juggernaut-2023',               True),
    ('43-95',                   'World Eaters Combat Patrol',           Decimal('105.00'),  'https://www.warhammer.com/en-GB/shop/combat-patrol-world-eaters-2025',                    True),
    ('P-KHORNE-BLOODCRUSHERS',  'Bloodcrushers of Khorne',              Decimal('65.00'),   'https://www.warhammer.com/en-GB/shop/Daemons-Of-Khorne-Bloodcrushers',                   True),
    ('P-KHORNE-BLOODLETTERS-40K', 'Bloodletters of Khorne',            Decimal('27.00'),   'https://www.warhammer.com/en-GB/shop/Daemons-Of-Khorne-Bloodletters-40k-2017',           True),
    ('P-KHORNE-BLOODTHIRSTER',  'Bloodthirster',                        Decimal('105.00'),  'https://www.warhammer.com/en-GB/shop/Daemons-Of-Khorne-Bloodthirster',                   True),
    ('P-KHORNE-FLESHHOUNDS',    'Flesh Hounds of Khorne',               Decimal('38.00'),   'https://www.warhammer.com/en-GB/shop/Flesh-Hounds-2019',                                  True),
    ('P-KHORNE-SKARBRAND',      'Skarbrand the Bloodthirster',          Decimal('105.00'),  'https://www.warhammer.com/en-GB/shop/Skarbrand-Bloodthirster',                           True),
    ('P-WE-CODEX-2025',         'Codex: World Eaters',                  Decimal('38.00'),   'https://www.warhammer.com/en-GB/shop/codex-world-eaters-2025-eng',                       True),
    ('P-WE-EXL-EIGHT-2023',     'World Eaters Exalted Eightbound',      Decimal('40.00'),   'https://www.warhammer.com/en-GB/shop/world-eaters-exalted-eightbound-2023',               True),
    ('P-WE-JAKHALS-2023',       'World Eaters Jakhals',                 Decimal('35.50'),   'https://www.warhammer.com/en-GB/shop/world-eaters-jakhals-2023',                         True),
    ('P-WE-KHARN-2023',         'World Eaters Kharn the Betrayer',      Decimal('27.00'),   'https://www.warhammer.com/en-GB/shop/world-eaters-kharn-the-betrayer-2023',              True),
    ('P-WE-KT-GOREMONGERS-2025', 'Kill Team: Goremongers',              Decimal('42.50'),   'https://www.warhammer.com/en-GB/shop/kill-team-goremongers-2025',                        True),
    ('P-WE-LORD-INVOC-2023',    'World Eaters Lord Invocatus',          Decimal('42.50'),   'https://www.warhammer.com/en-GB/shop/world-eaters-lord-invocatus-2023',                  True),
    ('P-WE-LORD-SKULLS',        'Khorne Lord of Skulls',                Decimal('120.00'),  'https://www.warhammer.com/en-GB/shop/Chaos-Space-Marines-Khorne-Lord-of-Skulls',         True),
    ('P-WE-SLAUGHTER-2025',     'World Eaters Slaughterbound',          Decimal('27.00'),   'https://www.warhammer.com/en-GB/shop/world-eaters-slaughter-bound-2025',                 True),
]


class Command(BaseCommand):
    help = 'Seed GW UK prices for World Eaters. Idempotent.'

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

        self.stdout.write(f'Seeded {seeded} World Eaters GW UK prices. Skipped: {skipped}.')
