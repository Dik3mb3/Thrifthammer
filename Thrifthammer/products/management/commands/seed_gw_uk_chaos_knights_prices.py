"""
Seed Games Workshop UK prices for Chaos Knights.

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
    ('CK-001', 'Codex: Chaos Knights',             Decimal('38.00'),   'https://www.warhammer.com/en-GB/shop/codex-chaos-knights-2025-eng',                               True),
    ('CK-002', 'Chaos Knight Ruinator',             Decimal('120.00'),  'https://www.warhammer.com/en-GB/shop/chaos-knights-chaos-knight-ruinator-2025',                   True),
    ('CK-003', 'Chaos War Dog Huntsmen',            Decimal('60.00'),   'https://www.warhammer.com/en-GB/shop/war-dog-huntsman-2022',                                      True),
    ('CK-004', 'Chaos War Dog Executioners',        Decimal('60.00'),   'https://www.warhammer.com/en-GB/shop/war-dog-executioner-2022',                                   True),
    ('CK-005', 'Chaos War Dog Stalkers',            Decimal('60.00'),   'https://www.warhammer.com/en-GB/shop/chaos-knights-war-dog-stalker-2022',                         True),
    ('CK-006', 'Chaos War Dog Brigands',            Decimal('60.00'),   'https://www.warhammer.com/en-GB/shop/chaos-knights-war-dog-brigand-2022',                         True),
    ('CK-007', 'Chaos War Dog Karnivores',          Decimal('60.00'),   'https://www.warhammer.com/en-GB/shop/chaos-knights-war-dog-karnivore-2022',                       True),
    ('CK-008', 'Chaos Knight Tyrant',               Decimal('118.00'),  'https://www.warhammer.com/en-GB/shop/imperial-knights-knight-dominus-knight-tyrant-2022',         True),
    ('CK-009', 'Chaos Knight Despoiler',            Decimal('115.00'),  'https://www.warhammer.com/en-GB/shop/knight-questoris-despoiler-2025',                           True),
    ('CK-010', 'Chaos Knight Questoris',            Decimal('115.00'),  'https://www.warhammer.com/en-GB/shop/imperial-knights-knight-questoris-2025',                     True),
    ('CK-011', 'Chaos Cerastus Knight Acheron',     Decimal('129.00'),  'https://www.warhammer.com/en-GB/shop/horus-heresy-cerastus-knight-acheron-2023',                  True),
    ('CK-012', 'Chaos Cerastus Knight Castigator',  Decimal('129.00'),  'https://www.warhammer.com/en-GB/shop/horus-heresy-cerastus-knight-castigator-2023',               True),
    ('CK-013', 'Chaos Questoris Knight Magaera',    Decimal('163.50'),  'https://www.warhammer.com/en-GB/shop/Questoris-Knight-Magaera',                                  True),
    ('CK-014', 'Chaos Questoris Knight Styrix',     Decimal('163.50'),  'https://www.warhammer.com/en-GB/shop/Questoris-Knight-Styrix',                                   True),
    ('CK-015', 'Chaos Cerastus Knight Lancer',      Decimal('129.00'),  'https://www.warhammer.com/en-GB/shop/horus-heresy-cerastus-knight-lancer-2023',                  True),
    ('CK-016', 'Chaos Acastus Knight Asterius',     Decimal('431.50'),  'https://www.warhammer.com/en-GB/shop/Mechanicum-Acastus-Knight-Asterius-2019',                   True),
    ('CK-017', 'Chaos Acastus Knight Porphyrion',   Decimal('463.50'),  'https://www.warhammer.com/en-GB/shop/Acastus-Knight-Porphyrion',                                 True),
    ('CK-018', 'Chaos Cerastus Knight Atrapos',     Decimal('243.50'),  'https://www.warhammer.com/en-GB/shop/Mechanicum-Cerastus-Knight-Atrapos',                        True),
]


class Command(BaseCommand):
    help = 'Seed GW UK prices and URLs for Chaos Knights. Idempotent.'

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

        self.stdout.write(f'Seeded {seeded} Chaos Knights GW UK prices. Skipped: {skipped}.')
