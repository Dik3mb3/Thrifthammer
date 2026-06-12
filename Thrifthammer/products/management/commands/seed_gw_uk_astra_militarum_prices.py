"""
Seed Games Workshop UK prices for Astra Militarum.

Creates/reuses the `games-workshop-uk` Retailer, sets msrp_gbp on each
matched Product, and creates/updates a CurrentPrice record pointing at the
GW UK product page.

Run once on Railway startup via Procfile.  Safe to re-run — idempotent.
"""
from decimal import Decimal

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Product, Retailer

_GW_UK_SLUG = 'games-workshop-uk'

# (gw_sku, label, gbp_price, gw_uk_url, in_stock)
_PRICES = [
    ('47-25',  'Combat Patrol: Astra Militarum',          Decimal('105.00'), 'https://www.warhammer.com/en-GB/shop/combat-patrol-astra-militarum-2025',                   True),
    ('AM-018', 'Death Korps of Krieg',                    Decimal('32.50'),  'https://www.warhammer.com/en-GB/shop/astra-militarum-death-korps-of-krieg-2025',            True),
    ('AM-029', 'Krieg Heavy Weapons Squad',               Decimal('32.50'),  'https://www.warhammer.com/en-GB/shop/astra-militarum-krieg-heavy-weapons-squad-2025',       True),
    ('AM-027', 'Krieg Combat Engineers',                  Decimal('29.50'),  'https://www.warhammer.com/en-GB/shop/astra-militarum-krieg-combat-engineers-2025',          True),
    ('AM-031', 'Lord Marshal Dreir',                      Decimal('38.00'),  'https://www.warhammer.com/en-GB/shop/astra-militarum-krieg-lord-marshal-dreir-2025',        True),
    ('AM-009', 'Cadian Castellan',                        Decimal('25.00'),  'https://www.warhammer.com/en-GB/shop/astra-militarum-cadian-castellan-2023',               True),
    ('AM-010', 'Cadian Command Squad',                    Decimal('29.50'),  'https://www.warhammer.com/en-GB/shop/astra-militarum-cadian-command-squad-2023',            True),
    ('47-30',  'Cadian Shock Troops',                     Decimal('32.50'),  'https://www.warhammer.com/en-GB/shop/astra-militarum-cadian-shock-troops-2023',             True),
    ('AM-024', 'Cadian Heavy Weapons Squad',              Decimal('32.50'),  'https://www.warhammer.com/en-GB/shop/astra-militarum-cadian-heavy-weapons-squad-2023',      True),
    ('AM-030', 'Lord Castellan Ursula Creed',             Decimal('29.50'),  'https://www.warhammer.com/en-GB/shop/astra-militarum-lord-castellan-ursula-creed-2023',     True),
    ('AM-011', 'Cadian Upgrades',                         Decimal('23.00'),  'https://www.warhammer.com/en-GB/shop/astra-militarum-cadian-upgrades-2023',                True),
    ('AM-033', 'Manticore',                               Decimal('42.50'),  'https://www.warhammer.com/en-GB/shop/Astra-Militarum-Manticore',                           True),
    ('47-17',  'Basilisk',                                Decimal('42.50'),  'https://www.warhammer.com/en-GB/shop/Imperial-Guard-Basilisk',                             True),
    ('47-05',  'Chimera',                                 Decimal('40.00'),  'https://www.warhammer.com/en-GB/shop/Imperial-Guard-Chimera',                              True),
    ('AM-019', 'Death Riders',                            Decimal('40.00'),  'https://www.warhammer.com/en-GB/shop/astra-militarum-death-riders-2025',                   True),
    ('47-14',  'Hellhound',                               Decimal('40.00'),  'https://www.warhammer.com/en-GB/shop/Imperial-Guard-Hellhound',                            True),
    ('47-08',  'Commissar',                               Decimal('25.00'),  'https://www.warhammer.com/en-GB/shop/astra-militarum-commissar-2023',                      True),
    ('AM-004', 'Attilan Rough Riders',                    Decimal('40.00'),  'https://www.warhammer.com/en-GB/shop/astra-militarum-attilan-rough-riders-2023',           True),
    ('47-12',  'Armoured Sentinel',                       Decimal('29.50'),  'https://www.warhammer.com/en-GB/shop/astra-militarum-armoured-sentinel-2023',              True),
    ('AM-005', 'Baneblade',                               Decimal('120.00'), 'https://www.warhammer.com/en-GB/shop/astra-militarum-baneblade-2023',                      True),
    ('AM-006', 'Banehammer',                              Decimal('120.00'), 'https://www.warhammer.com/en-GB/shop/astra-militarum-banehammer-2023',                     True),
    ('AM-007', 'Banesword',                               Decimal('120.00'), 'https://www.warhammer.com/en-GB/shop/astra-militarum-banesword-2023',                      True),
    ('AM-021', 'Doomhammer',                              Decimal('120.00'), 'https://www.warhammer.com/en-GB/shop/astra-militarum-doomhammer-2023',                     True),
    ('AM-025', 'Hellhammer',                              Decimal('120.00'), 'https://www.warhammer.com/en-GB/shop/astra-militarum-hellhammer-2023',                     True),
    ('AM-040', 'Shadowsword',                             Decimal('120.00'), 'https://www.warhammer.com/en-GB/shop/astra-militarum-shadowsword-2023',                    True),
    ('AM-042', 'Stormlord',                               Decimal('120.00'), 'https://www.warhammer.com/en-GB/shop/astra-militarum-stormlord-2023',                      True),
    ('AM-043', 'Stormsword',                              Decimal('120.00'), 'https://www.warhammer.com/en-GB/shop/astra-militarum-stormsword-2023',                     True),
    ('AM-001', 'Aegis Defence Line',                      Decimal('52.00'),  'https://www.warhammer.com/en-GB/shop/astra-militarum-aegis-defence-line-2023',             True),
    ('AM-022', 'Field Ordnance Battery',                  Decimal('35.50'),  'https://www.warhammer.com/en-GB/shop/astra-militarum-field-ordnance-battery-2023',         True),
    ('AM-032', 'Lord Solar Leontus',                      Decimal('40.00'),  'https://www.warhammer.com/en-GB/shop/astra-militarum-lord-solar-leontus-2023',             True),
    ('AM-038', 'Primaris Psyker',                         Decimal('21.50'),  'https://www.warhammer.com/en-GB/shop/astra-militarum-primaris-psyker-2023',                True),
    ('AM-023', "Gaunt's Ghosts",                          Decimal('49.50'),  'https://www.warhammer.com/en-GB/shop/Astra-Militarum-Gaunts-Ghosts-2021',                  True),
    ('AM-034', 'Militarum Tempestus Scions Command Squad', Decimal('29.50'), 'https://www.warhammer.com/en-GB/shop/Militarum-Tempestus-Scions-Command-Squad-2017',       True),
    ('AM-047', 'Tempestus Scions',                        Decimal('29.50'),  'https://www.warhammer.com/en-GB/shop/Militarum-Tempestus-Scions-2017',                     True),
    ('AM-046', 'Tech-Priest Enginseer',                   Decimal('25.00'),  'https://www.warhammer.com/en-GB/shop/Astra-Militarum-Tech-Priest-Enginseer',               True),
    ('AM-036', 'Nork Deddog',                             Decimal('40.00'),  'https://www.warhammer.com/en-GB/shop/Militarum-Auxilla-Nork-Deddog',                       True),
    ('AM-049', 'Wyvern',                                  Decimal('42.50'),  'https://www.warhammer.com/en-GB/shop/Astra-Militarum-Wyvern',                              True),
    ('AM-044', 'Taurox',                                  Decimal('38.00'),  'https://www.warhammer.com/en-GB/shop/Taurox',                                              True),
    ('AM-045', 'Taurox Prime',                            Decimal('38.00'),  'https://www.warhammer.com/en-GB/shop/Taurox-Prime',                                        True),
    ('AM-026', 'Hydra',                                   Decimal('42.50'),  'https://www.warhammer.com/en-GB/shop/Astra-Militarum-Hydra',                               True),
    ('AM-020', 'Deathstrike',                             Decimal('42.50'),  'https://www.warhammer.com/en-GB/shop/Imperial-Guard-Deathstrike',                          True),
    ('AM-014', 'Catachan Jungle Fighters',                Decimal('25.00'),  'https://www.warhammer.com/en-GB/shop/Imperial-Guard-Catachan-Jungle-Fighters',             True),
    ('AM-048', 'Valkyrie',                                Decimal('58.00'),  'https://www.warhammer.com/en-GB/shop/Imperial-Guard-Valkyrie',                             True),
    ('AM-016', 'Commissar Graves',                        Decimal('62.00'),  'https://www.warhammer.com/en-GB/shop/astra-militarum-commissar-graves-2026',               True),
    ('AM-035', 'Ministorum Priest',                       Decimal('23.00'),  'https://www.warhammer.com/en-GB/shop/adepta-sororitas-ministorum-priest-2024',             True),
    ('47-06',  'Leman Russ Battle Tank',                  Decimal('42.50'),  'https://www.warhammer.com/en-GB/shop/astra-militarum-leman-russ-battle-tank-2023',         True),
    ('AM-039', 'Rogal Dorn Battle Tank',                  Decimal('63.25'),  'https://www.warhammer.com/en-GB/shop/astra-militarum-rogal-dorn-battle-tank-2023',         True),
    ('AM-041', 'Sly Marbo',                               Decimal('19.00'),  'https://www.warhammer.com/en-GB/shop/Astra-Militarum-Sly-Marbo-2018',                      True),
    ('AM-037', 'Ogryns',                                  Decimal('40.00'),  'https://www.warhammer.com/en-GB/shop/Militarum-Auxilla-Ogryns',                            True),
    ('AM-008', 'Bullgryns',                               Decimal('40.00'),  'https://www.warhammer.com/en-GB/shop/Militarum-Auxilla-Bullgryns',                         True),
    ('AM-012', 'Catachan Command Squad',                  Decimal('25.00'),  'https://www.warhammer.com/en-GB/shop/Imperial-Guard-Catachan-Command-Squad',               True),
    ('AM-015', 'Codex: Astra Militarum',                  Decimal('38.00'),  'https://www.warhammer.com/en-GB/shop/codex-astra-militarum-2025-eng',                      True),
    # Temporarily out of stock — price and URL recorded, in_stock=False
    ('AM-028', 'Krieg Command Squad',                     Decimal('29.50'),  'https://www.warhammer.com/en-GB/shop/astra-militarum-krieg-command-squad-2025',            False),
    ('AM-013', 'Catachan Heavy Weapons Squad',            Decimal('29.50'),  'https://www.warhammer.com/en-GB/shop/Imperial-Guard-Catachan-Heavy-Weapon-Squad',          False),
    ('AM-017', 'Commissar Yarrick',                       Decimal('29.50'),  'https://www.warhammer.com/en-GB/shop/astra-militarum-commissar-yarrick-2026',              False),
    ('AM-003', 'Artillery Team',                          Decimal('40.00'),  'https://www.warhammer.com/en-GB/shop/astra-militarum-krieg-artillery-team-2025',           False),
]


class Command(BaseCommand):
    help = 'Seed GW UK prices and URLs for Astra Militarum. Idempotent.'

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

        self.stdout.write(f'Seeded {seeded} Astra Militarum GW UK prices. Skipped: {skipped}.')
