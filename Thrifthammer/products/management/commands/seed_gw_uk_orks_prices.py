"""
Seed Games Workshop UK prices for Orks.

Creates/reuses the `games-workshop-uk` Retailer, sets msrp_gbp on each
matched Product, and creates/updates a CurrentPrice record pointing at the
GW UK product page.

Run once on Railway startup via Procfile.  Safe to re-run — idempotent.

Note: KT-007 (Kill Team: Wrecka Krew) has faction=None but exists as a product.
"""
from decimal import Decimal

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Product, Retailer

_GW_UK_SLUG = 'games-workshop-uk'

# (gw_sku, label, gbp_price, gw_uk_url, in_stock)
_PRICES = [
    ('50-16',  'Ork Deff Dread',                Decimal('40.00'),  'https://www.warhammer.com/en-GB/shop/Ork-Deff-Dread',                          True),
    ('50-32',  'Boss Snikrot',                   Decimal('27.00'),  'https://www.warhammer.com/en-GB/shop/orks-boss-snikrot-2023',                   True),
    ('50-37',  'Deffkoptas',                     Decimal('42.50'),  'https://www.warhammer.com/en-GB/shop/deffkoptas-2022',                          True),
    ('50-02',  'Ork Warboss in Mega Armour',     Decimal('27.00'),  'https://www.warhammer.com/en-GB/shop/ork-warboss-in-mega-armour-2022',          True),
    ('50-60',  'Painboss',                       Decimal('27.00'),  'https://www.warhammer.com/en-GB/shop/orks-painboss-2021',                       True),
    ('50-40',  'Gunwagon',                       Decimal('80.00'),  'https://www.warhammer.com/en-GB/shop/gunwagon-2021',                            True),
    ('50-30',  'Bonebreaka',                     Decimal('80.00'),  'https://www.warhammer.com/en-GB/shop/bonebreaka-2021',                          True),
    ('50-22',  'Ork Battlewagon',                Decimal('80.00'),  'https://www.warhammer.com/en-GB/shop/orks-battlewagon-2021',                    True),
    ('50-63',  'Squighog Boyz',                  Decimal('42.50'),  'https://www.warhammer.com/en-GB/shop/orks-squighog-boyz-2021',                  True),
    ('50-67',  'Zodgrod Wortsnagga',             Decimal('29.50'),  'https://www.warhammer.com/en-GB/shop/orks-zodgrod-wortsnagga-2021',             True),
    ('50-52',  'Ork Beast Snagga Boyz',          Decimal('38.00'),  'https://www.warhammer.com/en-GB/shop/orks-beast-snagga-boyz-2021',              True),
    ('50-38',  'Ghazghkull Thraka',              Decimal('49.50'),  'https://www.warhammer.com/en-GB/shop/Ghazghkull-Thraka-2020',                   True),
    ('50-44',  'Kustom Boosta-blasta',           Decimal('38.00'),  'https://www.warhammer.com/en-GB/shop/Orks-Kustom-Boosta-Blasta-2019',          True),
    ('50-61',  'Rukkatrukk Squigbuggy',          Decimal('38.00'),  'https://www.warhammer.com/en-GB/shop/Orks-Rukkatrukk-Squigbuggy-2018',         True),
    ('50-36',  'Deffkilla Wartrike',             Decimal('38.00'),  'https://www.warhammer.com/en-GB/shop/Orks-Deffkilla-Wartrike-2018',            True),
    ('50-31',  'Boomdakka Snazzwagon',           Decimal('38.00'),  'https://www.warhammer.com/en-GB/shop/Orks-Boomdakka-Snazzwagon-2018',          True),
    ('50-58',  'Ork Warbiker Mob',               Decimal('35.50'),  'https://www.warhammer.com/en-GB/shop/Ork-Warbiker-Mob-2018',                    True),
    ('50-54',  'Ork Gretchin',                   Decimal('16.00'),  'https://www.warhammer.com/en-GB/shop/Ork-Gretchin-2018',                        True),
    ('50-33',  'Burna-Bommer',                   Decimal('57.00'),  'https://www.warhammer.com/en-GB/shop/Ork-Burna-Bommer-NEW',                     True),
    ('50-29',  'Blitza-Bommer',                  Decimal('57.00'),  'https://www.warhammer.com/en-GB/shop/Ork-Blitza-Bommer-NEW',                    True),
    ('50-35',  'Dakkajet',                       Decimal('57.00'),  'https://www.warhammer.com/en-GB/shop/Ork-Dakkajet-NEW',                         True),
    ('50-65',  'Wazbom Blastajet',               Decimal('57.00'),  'https://www.warhammer.com/en-GB/shop/Ork-Wazbom-Blastajet',                     True),
    ('50-27',  'Big Mek in Mega Armour',         Decimal('44.50'),  'https://www.warhammer.com/en-GB/shop/Big-Mek-in-Mega-Armour',                   True),
    ('50-12',  'Ork Meganobz',                   Decimal('44.50'),  'https://www.warhammer.com/en-GB/shop/Meganobz',                                 True),
    ('50-49',  'Mek Gunz: Traktor Kannon',       Decimal('38.00'),  'https://www.warhammer.com/en-GB/shop/Mek-Gunz-Traktor-Kannon',                  True),
    ('50-47',  'Mek Gunz: Kustom Mega-kannon',   Decimal('38.00'),  'https://www.warhammer.com/en-GB/shop/Mek-Gunz-Kustom-Mega-kannon',             True),
    ('50-48',  'Mek Gunz: Smasha Gun',           Decimal('38.00'),  'https://www.warhammer.com/en-GB/shop/Mek-Gunz-Smasha-Gun',                      True),
    ('50-28',  'Big Mek with Shokk Attack Gun',  Decimal('27.00'),  'https://www.warhammer.com/en-GB/shop/Big-Mek-with-Shokk-Attack-Gun',            True),
    ('50-46',  'Mek Gunz: Bubblechukka',         Decimal('38.00'),  'https://www.warhammer.com/en-GB/shop/Mek-Gunz-Bubblechukka',                    True),
    ('50-50',  'Morkanaut',                      Decimal('91.00'),  'https://www.warhammer.com/en-GB/shop/Morkanaut',                                True),
    ('50-39',  'Gorkanaut',                      Decimal('91.00'),  'https://www.warhammer.com/en-GB/shop/Gorkanaut',                                True),
    ('KT-007', 'Kill Team: Wrecka Krew',         Decimal('42.50'),  'https://www.warhammer.com/en-GB/shop/kill-team-wrecka-krew-2025',               True),
    ('50-26',  'Big Mek',                        Decimal('32.50'),  'https://www.warhammer.com/en-GB/shop/orks-big-mek-2024',                        True),
    ('50-34',  'Codex: Orks',                    Decimal('38.00'),  'https://www.warhammer.com/en-GB/shop/codex-orks-hb-english-2024',               True),
    ('50-15',  'Ork Killa Kans',                 Decimal('40.00'),  'https://www.warhammer.com/en-GB/shop/Ork-Killa-Kans',                           True),
    ('50-41',  'Hunta Rig',                      Decimal('87.50'),  'https://www.warhammer.com/en-GB/shop/hunta-rig-2021',                           True),
    ('50-24',  'Beastboss on Squigosaur',        Decimal('38.00'),  'https://www.warhammer.com/en-GB/shop/beastboss-on-squigosaur-2021',             True),
    ('50-51',  'Mozrog Skragbad',                Decimal('38.00'),  'https://www.warhammer.com/en-GB/shop/orks-mozrog-skragbad-2021',                True),
    ('50-42',  'Kill Rig',                       Decimal('87.50'),  'https://www.warhammer.com/en-GB/shop/orks-kill-rig-2021',                       True),
    ('50-25',  "Big'ed Bossbunka",               Decimal('52.00'),  'https://www.warhammer.com/en-GB/shop/orks-big-ed-bossbunka-2021',               True),
    ('50-23',  'Beastboss',                      Decimal('27.00'),  'https://www.warhammer.com/en-GB/shop/orks-beastboss-2021',                      True),
    ('50-62',  'Shokkjump Dragsta',              Decimal('38.00'),  'https://www.warhammer.com/en-GB/shop/Orks-Shokkjump-Dragsta-2019',             True),
    ('50-45',  'Megatrakk Scrapjet',             Decimal('38.00'),  'https://www.warhammer.com/en-GB/shop/Orks-Megatrakk-Scrapjet-2018',            True),
    ('50-57',  'Ork Stormboyz',                  Decimal('27.00'),  'https://www.warhammer.com/en-GB/shop/Ork-Stormboyz-2018',                       True),
    ('50-09',  'Ork Nobz',                       Decimal('27.00'),  'https://www.warhammer.com/en-GB/shop/Ork-Nobz-2018',                            True),
    ('50-10',  'Ork Boyz',                       Decimal('29.50'),  'https://www.warhammer.com/en-GB/shop/Ork-Boyz-2018',                            True),
    ('50-55',  'Ork Mek',                        Decimal('18.50'),  'https://www.warhammer.com/en-GB/shop/Ork-Mek-2018',                             True),
    ('50-20',  'Ork Flash Gitz',                 Decimal('40.00'),  'https://www.warhammer.com/en-GB/shop/Flash-Gitz',                               True),
    ('50-11',  'Ork Trukk',                      Decimal('36.00'),  'https://www.warhammer.com/en-GB/shop/Ork-Trukk',                                True),
    ('50-43',  'Kommandos',                      Decimal('42.50'),  'https://www.warhammer.com/en-GB/shop/orks-kommandos-2025',                      True),
    ('50-64',  'Stompa',                         Decimal('91.00'),  'https://www.warhammer.com/en-GB/shop/Ork-Stompa',                               True),
]


class Command(BaseCommand):
    help = 'Seed GW UK prices and URLs for Orks. Idempotent.'

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

        self.stdout.write(f'Seeded {seeded} Orks GW UK prices. Skipped: {skipped}.')
