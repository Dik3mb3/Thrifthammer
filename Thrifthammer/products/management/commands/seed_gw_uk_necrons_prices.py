"""
Seed Games Workshop UK prices for Necrons.

Creates/reuses the `games-workshop-uk` Retailer, sets msrp_gbp on each
matched Product, and creates/updates a CurrentPrice record pointing at the
GW UK product page.

Run once on Railway startup via Procfile.  Safe to re-run — idempotent.

Notes:
- prod3590140 covers both Obelisk & Transcendent C'tan and Tesseract Vault —
  disambiguated with name_filter.
- prod4390158 covers both Annihilation Barge and Catacomb Command Barge —
  disambiguated with name_filter.
- Night Scythe uses GW's /Necron-Doom-Scythe-2020 URL (shared kit page).
- KT-029 and KT-022 have faction=None but exist as products.
"""
from decimal import Decimal

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Product, Retailer

_GW_UK_SLUG = 'games-workshop-uk'

# (gw_sku, label, gbp_price, gw_uk_url, in_stock)
# Optional 6th element: name_filter (icontains) for shared-SKU products.
_PRICES = [
    ('prod4900147', 'Necrons Royal Court',                Decimal('80.00'),  'https://www.warhammer.com/en-GB/shop/Necrons-Royal-Court-2021',                            True),
    ('71-20',       'Necron Combat Patrol',                Decimal('105.00'), 'https://www.warhammer.com/en-GB/shop/combat-patrol-necrons-2023',                          True),
    ('P-241016',    "C'tan Shard of the Nightbringer",    Decimal('82.50'),  'https://www.warhammer.com/en-GB/shop/necrons-ctan-shard-of-the-nightbringer-2026',         True),
    ('P-241017',    'Nekrosor Ammentar',                   Decimal('38.50'),  'https://www.warhammer.com/en-GB/shop/necrons-nekrosor-ammentar-2026',                      True),
    ('49-21',       'Necron Psychomancer',                 Decimal('25.00'),  'https://www.warhammer.com/en-GB/shop/Necrons-Psychomancer-2020',                           True),
    ('prod4390153', 'Convergence of Dominion',             Decimal('42.50'),  'https://www.warhammer.com/en-GB/shop/Convergence-of-Dominion-2020',                        True),
    ('49-20',       "Necron C'tan Shard of the Void Dragon", Decimal('80.00'), 'https://www.warhammer.com/en-GB/shop/CTan-Shard-of-the-Void-Dragon-2020',                 True),
    ('prod4390154', 'Ophydian Destroyers',                 Decimal('40.00'),  'https://www.warhammer.com/en-GB/shop/Ophydian-Destroyers-2020',                            True),
    ('49-08',       'Necron Monolith',                     Decimal('115.00'), 'https://www.warhammer.com/en-GB/shop/Monolith-2020',                                       True),
    ('prod4390155', 'Lokhust Destroyer Squadron',          Decimal('38.00'),  'https://www.warhammer.com/en-GB/shop/Necron-Destroyer-Squadron-2020',                      True),
    ('49-06',       'Necron Warriors',                     Decimal('32.50'),  'https://www.warhammer.com/en-GB/shop/Necron-Warriors-2020',                                True),
    ('prod4390150', 'Skorpekh Destroyers',                 Decimal('40.00'),  'https://www.warhammer.com/en-GB/shop/Skorpekh-Destroyers-2020',                            True),
    ('prod4390148', 'Hexmark Destroyer',                   Decimal('25.00'),  'https://www.warhammer.com/en-GB/shop/Hexmark-Destroyer-2020',                              True),
    ('prod4390146', 'Canoptek Doomstalker',                Decimal('32.50'),  'https://www.warhammer.com/en-GB/shop/Canoptek-Doomstalker-2020',                           True),
    ('prod4390145', 'Lokhust Heavy Destroyer',             Decimal('25.00'),  'https://www.warhammer.com/en-GB/shop/Lokhust-Heavy-Destroyer-2020',                        True),
    ('prod4390156', 'Canoptek Wraiths',                    Decimal('40.00'),  'https://www.warhammer.com/en-GB/shop/Necron-Canoptek-Wraiths-2020',                        True),
    ('prod3940162', 'Tomb Blades',                         Decimal('38.00'),  'https://www.warhammer.com/en-GB/shop/Necron-Tomb-Blades-2020',                             True),
    ('49-10',       'Necron Immortals',                    Decimal('29.50'),  'https://www.warhammer.com/en-GB/shop/Necron-Immortals-2020',                               True),
    ('prod4390159', 'Night Scythe',                        Decimal('47.00'),  'https://www.warhammer.com/en-GB/shop/Necron-Doom-Scythe-2020',                             True),
    ('prod4390142', 'Deathmarks',                          Decimal('29.50'),  'https://www.warhammer.com/en-GB/shop/Necron-Deathmarks-2020',                              True),
    ('prod4390158', 'Necron Catacomb Command Barge',       Decimal('38.00'),  'https://www.warhammer.com/en-GB/shop/Necron-Catacomb-Command-Barge-2020',                  True, 'Command'),
    ('prod4390158', 'Annihilation Barge',                  Decimal('38.00'),  'https://www.warhammer.com/en-GB/shop/Necron-Annihilation-Barge-2020',                     True, 'Annihilation'),
    ('prod4390157', 'Ghost Ark',                           Decimal('42.50'),  'https://www.warhammer.com/en-GB/shop/Ghost%20Ark-2020',                                    True),
    ('49-12',       'Necron Doomsday Ark',                 Decimal('42.50'),  'https://www.warhammer.com/en-GB/shop/Doomsday-Ark-2020',                                   True),
    ('49-14',       'Necron Canoptek Spyder',              Decimal('29.50'),  'https://www.warhammer.com/en-GB/shop/Canoptek-Spyder-2020',                                True),
    ('prod4390160', 'Illuminor Szeras',                    Decimal('38.00'),  'https://www.warhammer.com/en-GB/shop/Necrons-Illuminor-Szeras-2020',                       True),
    ('prod3590140', "Obelisk & Transcendent C'tan",        Decimal('120.00'), 'https://www.warhammer.com/en-GB/shop/Necron-Obelisk',                                      True, 'Obelisk'),
    ('prod3590140', 'Tesseract Vault',                     Decimal('120.00'), 'https://www.warhammer.com/en-GB/shop/NecronsTesseract-Vault',                              True, 'Tesseract'),
    ('KT-029',      'Kill Team: Canoptek Circle',          Decimal('47.00'),  'https://www.warhammer.com/en-GB/shop/kill-team-canoptek-circle-2025',                      True),
    ('49-22',       'Necron Royal Warden',                 Decimal('25.00'),  'https://www.warhammer.com/en-GB/shop/necrons-royal-warden-2023',                           True),
    ('prod4900150', 'Overlord with Tachyon Arrow',         Decimal('26.00'),  'https://www.warhammer.com/en-GB/shop/necrons-overlord-2023',                               True),
    ('prod4900151', 'Orikan the Diviner',                  Decimal('29.50'),  'https://www.warhammer.com/en-GB/shop/necrons-orikan-the-diviner-2023',                     True),
    ('prod4900149', 'Imotekh the Stormlord',               Decimal('29.50'),  'https://www.warhammer.com/en-GB/shop/necrons-imotekh-the-stormlord-2023',                  True),
    ('prod2901178', "C'tan Shard of The Deceiver",         Decimal('32.50'),  'https://www.warhammer.com/en-GB/shop/Necron-C-tan-Shard-of-The-Deceiver',                  True),
    ('prod2791068', 'Trazyn the Infinite',                 Decimal('19.00'),  'https://www.warhammer.com/en-GB/shop/Necron-Trazyn-the-Infinite',                          True),
    ('49-23',       'Codex: Necrons',                      Decimal('38.00'),  'https://www.warhammer.com/en-GB/shop/codex-necrons-hb-eng-2023',                           True),
    ('49-17',       'Necron Flayed Ones',                  Decimal('35.50'),  'https://www.warhammer.com/en-GB/shop/Necrons-Flayed-Ones-2021',                            True),
    ('prod4900148', 'Chronomancer',                        Decimal('27.00'),  'https://www.warhammer.com/en-GB/shop/Necrons-Chronomancer-2021',                           True),
    ('prod4390152', 'Szarekh, The Silent King',            Decimal('105.50'), 'https://www.warhammer.com/en-GB/shop/Szarekh-The-Silent-King-2020',                        True),
    ('prod4390143', 'Triarch Stalker',                     Decimal('40.00'),  'https://www.warhammer.com/en-GB/shop/Triarch-Stalker-2020',                                True),
    ('prod4390144', 'Triarch Praetorians',                 Decimal('38.00'),  'https://www.warhammer.com/en-GB/shop/Necron-Triarch-Praetorians-2020',                     True),
    ('49-11',       'Necron Lychguard',                    Decimal('38.00'),  'https://www.warhammer.com/en-GB/shop/Necron-Lychguard-2020',                               True),
    ('prod4390141', 'Cryptek',                             Decimal('25.00'),  'https://www.warhammer.com/en-GB/shop/Necron-Cryptek-2020',                                 True),
    ('KT-022',      'Kill Team: Hierotek Circle',          Decimal('47.00'),  'https://www.warhammer.com/en-GB/shop/kill-team-hierotek-circle-2024',                      True),
]


class Command(BaseCommand):
    help = 'Seed GW UK prices and URLs for Necrons. Idempotent.'

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

        self.stdout.write(f'Seeded {seeded} Necrons GW UK prices. Skipped: {skipped}.')
