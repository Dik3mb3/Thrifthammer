"""
Seed Games Workshop UK prices for Leagues of Votann.

Creates/reuses the `games-workshop-uk` Retailer, sets msrp_gbp on each
matched Product, and creates/updates a CurrentPrice record pointing at the
GW UK product page.

Run once on Railway startup via Procfile.  Safe to re-run — idempotent.

Note: gw_sku 99120118011 covers both Uthar the Destined and Kahl.
A 6th tuple element (name_filter) disambiguates them via icontains lookup.
"""
from decimal import Decimal

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Product, Retailer

_GW_UK_SLUG = 'games-workshop-uk'

# (gw_sku, label, gbp_price, gw_uk_url, in_stock)
# Optional 6th element: name_filter (icontains) for shared-SKU products.
_PRICES = [
    ('73-06',                   'Einhyr Champion',              Decimal('27.00'),  'https://www.warhammer.com/en-GB/shop/lov-einhyr-champion-2022',                          True),
    ('73-10',                   'Hearthkyn Warriors',           Decimal('38.00'),  'https://www.warhammer.com/en-GB/shop/lov-hearthkyn-warriors-2022',                       True),
    ('73-12',                   'Hernkyn Pioneers',             Decimal('42.50'),  'https://www.warhammer.com/en-GB/shop/lov-hernkyn-pioneers-2022',                         True),
    ('73-14',                   'Einhyr Hearthguard',           Decimal('40.00'),  'https://www.warhammer.com/en-GB/shop/lov-einhyr-hearthguard-2022',                       True),
    ('73-25',                   'Combat Patrol',                Decimal('105.00'), 'https://www.warhammer.com/en-GB/shop/combat-patrol-leagues-of-votann-2025',               True),
    ('P-189754-99120118018',    'Kill Team: Hernkyn Yaegirs',   Decimal('42.50'),  'https://www.warhammer.com/en-GB/shop/kill-team-hernkyn-yaegirs-2024',                    True),
    ('P-198770-99120118023',    'Kill Team: Hearthkyn Salvagers', Decimal('42.50'), 'https://www.warhammer.com/en-GB/shop/kill-team-hearthkyn-salvagers-2024',               True),
    ('P-222997-99120118026',    'Memnyr Strategist',            Decimal('25.00'),  'https://www.warhammer.com/en-GB/shop/leagues-of-votann-memnyr-strategist-2025',          True),
    ('P-222999-99120118025',    'Arkanyst Evaluator',           Decimal('25.00'),  'https://www.warhammer.com/en-GB/shop/leagues-of-votann-arkanyst-evaluator-2025',         True),
    ('P-223001-99120118020',    'Ironkin Steeljacks',           Decimal('38.00'),  'https://www.warhammer.com/en-GB/shop/leagues-of-votann-ironkin-steeljacks-2025',         True),
    ('P-223003-99120118019',    'Buri Aegnirssen',              Decimal('27.00'),  'https://www.warhammer.com/en-GB/shop/leagues-of-votann-buri-aegnirsson-2025',            True),
    ('P-223004-99120118021',    'Cthonian Earthshakers',        Decimal('35.50'),  'https://www.warhammer.com/en-GB/shop/leagues-of-votann-cthonian-earthshakers-2025',      True),
    ('P-223006-99120118022',    'Kapricus Defender/Carrier',    Decimal('38.50'),  'https://www.warhammer.com/en-GB/shop/leagues-of-votann-kapricus-2025',                   True),
    ('P-223015-60030118002',    'Codex: Leagues of Votann',     Decimal('38.00'),  'https://www.warhammer.com/en-GB/shop/codex-leagues-of-votann-2025-eng',                  True),
    ('P-240930-99120118028',    'Berehk Stornbrow',             Decimal('29.00'),  'https://www.warhammer.com/en-GB/shop/leagues-of-votann-berehk-stornbrow-2026',           True),
    ('prod5000436-99120118002', 'Cthonian Berserks',            Decimal('40.00'),  'https://www.warhammer.com/en-GB/shop/lov-chonian-berserks-2022',                         True),
    ('prod5000437-99120118003', 'Sagitaur',                     Decimal('42.50'),  'https://www.warhammer.com/en-GB/shop/lov-sagitaur-2022',                                 True),
    ('prod5000438-99120118004', 'Grimnyr',                      Decimal('29.50'),  'https://www.warhammer.com/en-GB/shop/lov-grimnyr-2022',                                  True),
    ('prod5000439-99120118005', 'Brokhyr Thunderkyn',           Decimal('38.00'),  'https://www.warhammer.com/en-GB/shop/lov-brokhyr-thunderkin-2022',                       True),
    ('prod5000440-99120118006', 'Hekaton Land Fortress',        Decimal('74.00'),  'https://www.warhammer.com/en-GB/shop/lov-hekaton-land-fortress-2022',                    True),
    ('prod5000444-99120118010', 'Brokhyr Iron-master',          Decimal('35.50'),  'https://www.warhammer.com/en-GB/shop/lov-brokhyr-iron-master-2022',                      True),
    ('prod5000445-99120118011', 'Uthar the Destined',           Decimal('27.00'),  'https://www.warhammer.com/en-GB/shop/lov-uthar-the-destined-2022',                       True, 'Uthar'),
    ('prod5000456-99120118011', 'Kahl',                         Decimal('27.00'),  'https://www.warhammer.com/en-GB/shop/lov-kahl-2022',                                     True, 'Kahl'),
]


class Command(BaseCommand):
    help = 'Seed GW UK prices and URLs for Leagues of Votann. Idempotent.'

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

        for entry in _PRICES:
            sku, label, gbp_price, url, in_stock = entry[:5]
            name_filter = entry[5] if len(entry) > 5 else None

            qs = Product.objects.filter(gw_sku=sku)
            if name_filter:
                qs = qs.filter(name__icontains=name_filter)
            products = list(qs)

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

        self.stdout.write(f'Seeded {seeded} Leagues of Votann GW UK prices. Skipped: {skipped}.')
