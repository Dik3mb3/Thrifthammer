"""
Seed Games Workshop UK prices for Aeldari.

Creates/reuses the `games-workshop-uk` Retailer, sets msrp_gbp on each
matched Product, and creates/updates a CurrentPrice record pointing at the
GW UK product page.

Run once on Railway startup via Procfile.  Safe to re-run — idempotent.

Note: SKU P-240924 maps to two DB products (Vyper and Starfang — same physical
kit).  Both receive the same GW UK URL and price via filter-based lookup.
"""
from decimal import Decimal

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Product, Retailer

_GW_UK_SLUG = 'games-workshop-uk'

# (gw_sku, label, gbp_price, gw_uk_url, in_stock)
_PRICES = [
    ('46-25',       'Combat Patrol: Aeldari',       Decimal('105.00'), 'https://www.warhammer.com/en-GB/shop/combat-patrol-aeldari-2025',               True),
    ('P-240879',    'Combat Patrol: Aeldari Corsairs', Decimal('105.00'), 'https://www.warhammer.com/en-GB/shop/combat-patrol-aeldari-corsairs-2026',    True),
    ('prod4900142', 'Shining Spears',               Decimal('42.50'),  'https://www.warhammer.com/en-GB/shop/aeldari-shining-spears-2022',               True),
    ('46-30',       'Codex: Aeldari',               Decimal('38.00'),  'https://www.warhammer.com/en-GB/shop/codex-aeldari-2025-eng',                   True),
    ('prod3600196', 'Crimson Hunter',               Decimal('58.00'),  'https://www.warhammer.com/en-GB/shop/Eldar-Crimson-Hunter-2017',                 True),
    ('P-203614',    'Swooping Hawks',               Decimal('40.00'),  'https://www.warhammer.com/en-GB/shop/aeldari-swooping-hawks-2025',               True),
    ('P-203611',    'Warp Spiders',                 Decimal('40.00'),  'https://www.warhammer.com/en-GB/shop/aeldari-warp-spiders-2025',                 True),
    ('prod4870190', 'Maugan Ra',                    Decimal('29.50'),  'https://www.warhammer.com/en-GB/shop/aeldari-maugan-ra-2022',                    True),
    ('prod4870189', 'Dark Reapers',                 Decimal('40.00'),  'https://www.warhammer.com/en-GB/shop/aeldari-dark-reapers-2022',                 True),
    ('prod4390157', 'Howling Banshees',             Decimal('40.00'),  'https://www.warhammer.com/en-GB/shop/Craftworlds-Howling-Banshees-2020',         True),
    ('prod4390156', 'Jain Zar',                     Decimal('29.50'),  'https://www.warhammer.com/en-GB/shop/Craftworlds-Jain-Zar-2020',                 True),
    ('46-06',       'Dire Avengers',                Decimal('29.50'),  'https://www.warhammer.com/en-GB/shop/Eldar-Dire-Avengers-2017',                  True),
    ('P-203621',    'Fuegan',                       Decimal('29.50'),  'https://www.warhammer.com/en-GB/shop/aeldari-phoenix-lord-fuegan-2025',           True),
    ('P-203620',    'Baharroth',                    Decimal('29.50'),  'https://www.warhammer.com/en-GB/shop/aeldari-phoenix-lord-baharroth-2025',        True),
    ('P-203618',    'Lhykhis',                      Decimal('29.50'),  'https://www.warhammer.com/en-GB/shop/aeldari-phoenix-lord-lhykhis-2025',          True),
    ('46-14',       'Fire Dragons',                 Decimal('40.00'),  'https://www.warhammer.com/en-GB/shop/aeldari-fire-dragons-2025',                  True),
    ('prod4900145', 'Shroud Runners',               Decimal('44.50'),  'https://www.warhammer.com/en-GB/shop/aeldari-shroud-runners-2022',               True),
    ('prod4900144', 'Rangers',                      Decimal('40.00'),  'https://www.warhammer.com/en-GB/shop/aeldari-rangers-2022',                      True),
    ('prod3660121', 'Windriders',                   Decimal('38.00'),  'https://www.warhammer.com/en-GB/shop/Eldar-Windriders-2017',                     True),
    ('prod3660120', 'Warlock Skyrunner',             Decimal('27.00'),  'https://www.warhammer.com/en-GB/shop/Eldar-Warlock-Skyrunner-2017',              True),
    ('prod3600197', 'Hemlock Wraithfighter',         Decimal('58.00'),  'https://www.warhammer.com/en-GB/shop/Eldar-Hemlock-Wraithfighter-2017',          True),
    ('prod3580144', 'Wraithknight',                 Decimal('105.00'), 'https://www.warhammer.com/en-GB/shop/Eldar-Wraithknight-2017',                   True),
    ('prod3530578', 'Wraithlord',                   Decimal('40.00'),  'https://www.warhammer.com/en-GB/shop/Eldar-Wraithlord-2017',                     True),
    ('prod2780228', 'Voidweaver',                   Decimal('29.50'),  'https://www.warhammer.com/en-GB/shop/Voidweaver',                                True),
    ('prod2620124', 'Skyweavers',                   Decimal('35.50'),  'https://www.warhammer.com/en-GB/shop/Harlequin-Skyweavers',                      True),
    ('prod2600170', 'Starweaver',                   Decimal('29.50'),  'https://www.warhammer.com/en-GB/shop/Harlequin-Starweaver',                      True),
    # P-240924 seeds both Vyper and Starfang (same physical kit, same box URL)
    ('P-240924',    'Vyper / Starfang',             Decimal('38.50'),  'https://www.warhammer.com/en-GB/shop/aeldari-vyper-2026',                        True),
    ('P-240923',    'Corsair Voidreavers',           Decimal('38.50'),  'https://www.warhammer.com/en-GB/shop/aeldari-corsair-voidreavers-2026',          True),
    ('P-240922',    'Corsair Skyreavers',            Decimal('37.50'),  'https://www.warhammer.com/en-GB/shop/aeldari-corsair-skyreavers-2026',           True),
    ('46-29',       'Wave Serpent / Falcon',         Decimal('42.50'),  'https://www.warhammer.com/en-GB/shop/aeldari-wave-serpent-2025',                 True),
    ('P-203606',    'War Walkers',                  Decimal('52.00'),  'https://www.warhammer.com/en-GB/shop/aeldari-war-walkers-2025',                  True),
    ('prod770020a', 'Support Weapon',               Decimal('18.50'),  'https://www.warhammer.com/en-GB/shop/Eldar-Support-Weapon',                      True),
    ('prod770019a', 'Fire Prism',                   Decimal('42.50'),  'https://www.warhammer.com/en-GB/shop/Eldar-Fire-Prism',                          True),
    ('prod4900146', 'Autarch',                      Decimal('27.00'),  'https://www.warhammer.com/en-GB/shop/aeldari-autarch-2022',                      True),
    ('prod4900143', 'Avatar of Khaine',             Decimal('69.50'),  'https://www.warhammer.com/en-GB/shop/aeldari-avatar-of-khaine-2022',             True),
    ('prod4870191', 'The Yncarne',                  Decimal('35.50'),  'https://www.warhammer.com/en-GB/shop/aeldari-the-yncarne-2022',                  True),
    ('prod4870187', 'Warlocks',                     Decimal('38.00'),  'https://www.warhammer.com/en-GB/shop/aeldari-warlocks-2022',                     True),
    ('prod4870186', 'The Visarch',                  Decimal('21.50'),  'https://www.warhammer.com/en-GB/shop/aeldari-the-visarch-2022',                  True),
    ('prod4870185', 'Yvraine',                      Decimal('27.00'),  'https://www.warhammer.com/en-GB/shop/aeldari-yvraine-2022',                      True),
    ('prod4240206', 'Spiritseer',                   Decimal('20.50'),  'https://www.warhammer.com/en-GB/shop/Craftworlds-Spiritseer-2019',               True),
    ('prod3650295', 'Farseer Skyrunner',            Decimal('27.00'),  'https://www.warhammer.com/en-GB/shop/Eldar-Farseer-Skyrunner-2017',              True),
    ('prod3650164', 'Eldrad Ulthran',               Decimal('25.00'),  'https://www.warhammer.com/en-GB/shop/Eldrad-Ulthran-2017',                       True),
    ('prod3530579', 'Harlequin Troupe',             Decimal('29.50'),  'https://www.warhammer.com/en-GB/shop/Harlequin-Troupe-Troop-2017',               True),
    ('prod2810200', 'Autarch Wayleaper',            Decimal('19.00'),  'https://www.warhammer.com/en-GB/shop/Eldar-Autarch',                             True),
    ('prod2620122', 'Solitaire',                    Decimal('19.00'),  'https://www.warhammer.com/en-GB/shop/Solitaire',                                 True),
    ('prod2620121', 'Shadowseer',                   Decimal('20.50'),  'https://www.warhammer.com/en-GB/shop/Harlequin-Shadowseer',                      True),
    ('prod2620120', 'Death Jester',                 Decimal('20.50'),  'https://www.warhammer.com/en-GB/shop/Harlequin-Death-Jester',                    True),
    ('46-02',       'Farseer',                      Decimal('20.50'),  'https://www.warhammer.com/en-GB/shop/Eldar-Farseer',                             True),
    ('prod2180123', 'Night Spinner',                Decimal('42.50'),  'https://www.warhammer.com/en-GB/shop/Eldar-Night-Spinner',                       True),
    ('P-240921',    'Kharseth',                     Decimal('27.00'),  'https://www.warhammer.com/en-GB/shop/aeldari-kharseth-2026',                     True),
    ('P-240880',    'Prince Yriel',                 Decimal('29.00'),  'https://www.warhammer.com/en-GB/shop/aeldari-prince-yriel-2026',                 True),
    # Temporarily out of stock — price and URL recorded, in_stock=False
    ('P-203616',    'Asurmen',                      Decimal('29.50'),  'https://www.warhammer.com/en-GB/shop/aeldari-asurmen-2025',                      False),
    ('prod4870188', 'Guardian Defenders',           Decimal('38.00'),  'https://www.warhammer.com/en-GB/shop/aeldari-guardians-2022',                    False),
    ('46-09',       'Aeldari Guardians',            Decimal('38.00'),  'https://www.warhammer.com/en-GB/shop/aeldari-guardians-2022',                    False),
    ('prod3590139', 'Wraithblades',                 Decimal('40.00'),  'https://www.warhammer.com/en-GB/shop/Eldar-Wraithblades-2017',                   False),
    ('prod3590128', 'Wraithguard',                  Decimal('40.00'),  'https://www.warhammer.com/en-GB/shop/Eldar-Wraithguard-2017',                    False),
]


class Command(BaseCommand):
    help = 'Seed GW UK prices and URLs for Aeldari. Idempotent.'

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

        self.stdout.write(f'Seeded {seeded} Aeldari GW UK prices. Skipped: {skipped}.')
