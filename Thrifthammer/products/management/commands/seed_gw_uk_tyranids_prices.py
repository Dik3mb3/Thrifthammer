"""
Seed Games Workshop UK prices for Tyranids.

Run once on Railway startup via Procfile.  Safe to re-run — idempotent.
"""
from decimal import Decimal

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Product, Retailer

_GW_UK_SLUG = 'games-workshop-uk'

# (gw_sku, label, gbp_price, gw_uk_url, in_stock)
_PRICES = [
    ('51-04',   'Tyranid Hive Tyrant',                  Decimal('40.00'),   'https://www.warhammer.com/en-GB/shop/tyranids-hive-tyrant-no-wings-2022',  True),
    ('51-06',   'Tyranid Carnifex',                     Decimal('64.50'),   'https://www.warhammer.com/en-GB/shop/Carnifex-Brood',                       True),
    ('51-08',   'Tyranid Warriors',                     Decimal('40.00'),   'https://www.warhammer.com/en-GB/shop/Tyranid-Warriors-2017',                 True),
    ('51-16',   'Tyranid Termagants',                   Decimal('29.50'),   'https://www.warhammer.com/en-GB/shop/tyranids-termagants-2023',              True),
    ('71-19',   'Tyranid Combat Patrol',                Decimal('105.00'),  'https://www.warhammer.com/en-GB/shop/combat-patrol-tyranid-assault-brood-2025', True),
    ('TY-001',  'Tyranid Barbgaunts',                   Decimal('29.50'),   'https://www.warhammer.com/en-GB/shop/tyranids-barbgaunts-2023',              True),
    ('TY-002',  'Tyranid Biovore',                      Decimal('32.50'),   'https://www.warhammer.com/en-GB/shop/tyranids-biovore-2023',                 True),
    ('TY-003',  'Tyranid Broodlord',                    Decimal('29.50'),   'https://www.warhammer.com/en-GB/shop/Tyranid-Broodlord',                     True),
    ('TY-004',  'Codex: Tyranids',                      Decimal('38.00'),   'https://www.warhammer.com/en-GB/shop/codex-tyranids-2023-eng',               True),
    ('TY-005',  'Tyranid Deathleaper',                  Decimal('40.00'),   'https://www.warhammer.com/en-GB/shop/tyranids-deathleaper-2023',             True),
    ('TY-006',  'Tyranid Exocrine',                     Decimal('54.50'),   'https://www.warhammer.com/en-GB/shop/Exocrine',                              True),
    ('TY-007',  'Tyranid Gargoyle Brood',               Decimal('30.00'),   'https://www.warhammer.com/en-GB/shop/Tyranid-Gargoyle-Brood',                True),
    ('TY-008',  'Tyranid Genestealers',                 Decimal('35.50'),   'https://www.warhammer.com/en-GB/shop/tyranids-genestealers-2023',            True),
    ('TY-009',  'Tyranid Haruspex',                     Decimal('54.50'),   'https://www.warhammer.com/en-GB/shop/Haruspex',                              True),
    ('TY-010',  'Tyranid Hive Crone',                   Decimal('58.00'),   'https://www.warhammer.com/en-GB/shop/Hive-Crone',                            True),
    ('TY-011',  'Tyranid Hive Guard',                   Decimal('52.00'),   'https://www.warhammer.com/en-GB/shop/Hive-Guard',                            True),
    ('TY-013',  'Tyranid Hormagaunts',                  Decimal('32.50'),   'https://www.warhammer.com/en-GB/shop/tyranids-hormagaunts-2023',             True),
    ('TY-014',  'Tyranid Horrors of the Hive',          Decimal('69.50'),   'https://www.warhammer.com/en-GB/shop/tyranids-horrors-of-the-hive-2023',     True),
    ('TY-015',  'Tyranid Raveners',                     Decimal('42.50'),   'https://www.warhammer.com/en-GB/shop/kill-team-raveners-2025',               True),
    ('TY-016',  'Tyranid Lictor',                       Decimal('32.50'),   'https://www.warhammer.com/en-GB/shop/tyranids-lictor-2023',                  True),
    ('TY-017',  'Tyranid Maleceptor',                   Decimal('52.50'),   'https://www.warhammer.com/en-GB/shop/Maleceptor',                            True),
    ('TY-018',  'Tyranid Mawloc',                       Decimal('57.00'),   'https://www.warhammer.com/en-GB/shop/Tyranid-Mawloc',                        True),
    ('TY-019',  'Tyranid Neurogaunts',                  Decimal('27.00'),   'https://www.warhammer.com/en-GB/shop/tyranids-neurogaunts-2023',             True),
    ('TY-020',  'Tyranid Neurolictor',                  Decimal('27.00'),   'https://www.warhammer.com/en-GB/shop/tyranids-neurolictor-2023',             True),
    ('TY-021',  'Tyranid Norn Assimilator',             Decimal('74.00'),   'https://www.warhammer.com/en-GB/shop/tyranids-norn-assimilator-2023',        True),
    ('TY-022',  'Tyranid Norn Emissary',                Decimal('74.00'),   'https://www.warhammer.com/en-GB/shop/tyranids-norn-emissary-2023',           True),
    ('TY-023',  'Tyranid Old One Eye\'s Carnifex Brood', Decimal('64.50'),  'https://www.warhammer.com/en-GB/shop/Old-One-Eyes-Carnifex-Brood-2017',      True),
    ('TY-024',  'Tyranid Parasite of Mortrex',          Decimal('27.00'),   'https://www.warhammer.com/en-GB/shop/tyranids-parasite-of-mortrex-2022',     True),
    ('TY-025',  'Tyranid Psychophage',                  Decimal('38.00'),   'https://www.warhammer.com/en-GB/shop/tyranids-psychophage-2023',             True),
    ('TY-026',  'Tyranid Pyrovore',                     Decimal('32.50'),   'https://www.warhammer.com/en-GB/shop/tyranids-pyrovore-2023',                True),
    ('TY-027',  'Tyranid Screamer-Killer Brood',        Decimal('64.50'),   'https://www.warhammer.com/en-GB/shop/Screamer-Killer-Brood-2017',            True),
    ('TY-028',  'Tyranid Sporocyst and Mucolid Spore',  Decimal('49.50'),   'https://www.warhammer.com/en-GB/shop/Sporocyst',                             True),
    ('TY-029',  'Tyranid Tervigon',                     Decimal('42.50'),   'https://www.warhammer.com/en-GB/shop/Tyranid-Tervigon',                      True),
    ('TY-030',  'Tyranid The Swarmlord',                Decimal('40.00'),   'https://www.warhammer.com/en-GB/shop/The-Swarmlord-2019',                    True),
    ('TY-031',  'Tyranid Toxicrene',                    Decimal('52.50'),   'https://www.warhammer.com/en-GB/shop/Toxicrene',                             True),
    ('TY-032',  'Tyranid Trygon',                       Decimal('57.00'),   'https://www.warhammer.com/en-GB/shop/Tyranid-Trygon',                        True),
    ('TY-033',  'Tyranid Harpy',                        Decimal('58.00'),   'https://www.warhammer.com/en-GB/shop/Tyranid-Harpy',                         True),
    ('TY-034',  'Tyranid Harridan',                     Decimal('350.50'),  'https://www.warhammer.com/en-GB/shop/Tyranid-Harridan',                      True),
    ('TY-035',  'Tyranid Hierophant Bio-Titan',         Decimal('350.50'),  'https://www.warhammer.com/en-GB/shop/Tyranid-Hierophant-Bio-Titan',          True),
    ('TY-036',  'Tyranid Prime',                        Decimal('27.00'),   'https://www.warhammer.com/en-GB/shop/tyranids-prime-2023',                   True),
    ('TY-037',  'Tyranid Prime with Lash Whip',         Decimal('27.00'),   'https://www.warhammer.com/en-GB/shop/tyranid-prime-with-lash-whip-2026',     True),
    ('TY-038',  'Tyranid Tyrannocyte',                  Decimal('49.50'),   'https://www.warhammer.com/en-GB/shop/Tyrannocyte',                           True),
    ('TY-039',  'Tyranid Tyrannofex',                   Decimal('42.50'),   'https://www.warhammer.com/en-GB/shop/Tyranid-Tyrannofex',                    True),
    ('TY-040',  'Tyranid Tyrant Guard',                 Decimal('52.00'),   'https://www.warhammer.com/en-GB/shop/Tyrant-Guard',                          True),
    ('TY-041',  'Tyranid Venomthropes',                 Decimal('49.50'),   'https://www.warhammer.com/en-GB/shop/Venomthropes',                          True),
    ('TY-042',  "Tyranid Von Ryan's Leapers",           Decimal('32.50'),   'https://www.warhammer.com/en-GB/shop/tyranids-von-ryans-leapers-2023',       True),
    ('TY-043',  'Tyranid Winged Hive Tyrant',           Decimal('40.00'),   'https://www.warhammer.com/en-GB/shop/Tyranids-Hive-Tyrant-2019',             True),
    ('TY-044',  'Tyranid Zoanthropes',                  Decimal('49.50'),   'https://www.warhammer.com/en-GB/shop/Zoanthropes',                           True),
]


class Command(BaseCommand):
    help = 'Seed GW UK prices for Tyranids. Idempotent.'

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

        self.stdout.write(f'Seeded {seeded} Tyranids GW UK prices. Skipped: {skipped}.')
