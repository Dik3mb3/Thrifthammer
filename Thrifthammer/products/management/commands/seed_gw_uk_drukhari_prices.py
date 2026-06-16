"""
Seed Games Workshop UK prices for Drukhari.

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
    ('45-02',  'Drukhari Archon',                Decimal('25.00'),  'https://www.warhammer.com/en-GB/shop/drukhari-archon-2025',                    True),
    ('45-06',  'Drukhari Wyches',                Decimal('29.50'),  'https://www.warhammer.com/en-GB/shop/Dark-Eldar-Wyches',                        True),
    ('45-07',  'Drukhari Kabalite Warriors',     Decimal('29.50'),  'https://www.warhammer.com/en-GB/shop/Drukhari-Kabalite-Warriors-2017',          True),
    ('45-10',  'Drukhari Raider',                Decimal('40.00'),  'https://www.warhammer.com/en-GB/shop/Drukhari-Raider',                          True),
    ('45-12',  'Drukhari Ravager',               Decimal('42.50'),  'https://www.warhammer.com/en-GB/shop/Dark-Eldar-Ravager',                       True),
    ('45-25',  'Drukhari Combat Patrol',         Decimal('105.00'), 'https://www.warhammer.com/en-GB/shop/combat-patrol-drukhari-2025',               True),
    ('DR-001', 'Drukhari Lelith Hesperax',       Decimal('29.50'),  'https://www.warhammer.com/en-GB/shop/Drukhari-Lelith-Hesperax-2021',            True),
    ('DR-002', 'Drukhari Drazhar',               Decimal('29.50'),  'https://www.warhammer.com/en-GB/shop/Drukhari-Drazhar-2020',                    True),
    ('DR-003', 'Drukhari Haemonculus',           Decimal('18.50'),  'https://www.warhammer.com/en-GB/shop/Haemonculus-2017',                         True),
    ('DR-004', 'Drukhari Succubus',              Decimal('18.50'),  'https://www.warhammer.com/en-GB/shop/Succubus-2014',                             True),
    ('DR-005', 'Drukhari Wracks',                Decimal('38.00'),  'https://www.warhammer.com/en-GB/shop/drukhari-wracks-2025',                     True),
    ('DR-006', 'Codex: Drukhari',               Decimal('38.00'),  'https://www.warhammer.com/en-GB/shop/codex-drukhari-hb-2025-eng',               True),
    ('DR-007', 'Drukhari Incubi',                Decimal('40.00'),  'https://www.warhammer.com/en-GB/shop/Drukhari-Incubi-2020',                     True),
    ('DR-008', 'Drukhari Talos',                 Decimal('40.00'),  'https://www.warhammer.com/en-GB/shop/Dark-Eldar-Talos-Pain-Engine-2018',        True),
    ('DR-009', 'Drukhari Cronos',                Decimal('40.00'),  'https://www.warhammer.com/en-GB/shop/Dark-Eldar-Cronos-Parasite-Engine-2018',   True),
    ('DR-010', 'Drukhari Venom',                 Decimal('27.00'),  'https://www.warhammer.com/en-GB/shop/Dark-Eldar-Venom-2017',                    True),
    ('DR-011', 'Drukhari Voidraven Bomber',      Decimal('58.00'),  'https://www.warhammer.com/en-GB/shop/Voidraven-Bomber',                         True),
    ('DR-012', 'Drukhari Razorwing Jetfighter',  Decimal('38.50'),  'https://www.warhammer.com/en-GB/shop/Dark-Eldar-Razorwing-Jetfighter',          True),
    ('DR-013', 'Drukhari Scourges',              Decimal('25.00'),  'https://www.warhammer.com/en-GB/shop/Dark-Eldar-Scourges',                      True),
    ('DR-014', 'Drukhari Hand of the Archon',    Decimal('36.00'),  'https://www.warhammer.com/en-GB/shop/kill-team-hand-of-the-archon-2024',        True),
    ('DR-015', 'Drukhari Mandrakes',             Decimal('49.50'),  'https://www.warhammer.com/en-GB/shop/kill-team-mandrakes-2024',                 True),
    ('DR-016', 'Drukhari Lady Malys',            Decimal('29.50'),  'https://www.warhammer.com/en-GB/shop/drukhari-lady-malys-2025',                 True),
    ('DR-017', 'Drukhari Reavers',               Decimal('29.50'),  'https://www.warhammer.com/en-GB/shop/Dark-Eldar-Reavers',                       True),
    ('DR-018', 'Drukhari Hellions',              Decimal('21.50'),  'https://www.warhammer.com/en-GB/shop/Dark-Eldar-Hellions',                      True),
]


class Command(BaseCommand):
    help = 'Seed GW UK prices and URLs for Drukhari. Idempotent.'

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

        self.stdout.write(f'Seeded {seeded} Drukhari GW UK prices. Skipped: {skipped}.')
