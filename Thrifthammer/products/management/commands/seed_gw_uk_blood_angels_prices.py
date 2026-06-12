"""
Seed Games Workshop UK prices for Blood Angels.

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
    ('41-25', 'Blood Angels Combat Patrol',               Decimal('105.00'), 'https://www.warhammer.com/en-GB/shop/combat-patrol-blood-angels-2024',              True),
    ('41-04', 'Blood Angels Commander Dante',             Decimal('29.50'),  'https://www.warhammer.com/en-GB/shop/blood-angels-commander-dante-2023',            True),
    ('41-02', 'Blood Angels Mephiston',                   Decimal('29.50'),  'https://www.warhammer.com/en-GB/shop/Mephiston-Lord-of-Death-2020',                 True),
    ('41-10', 'Blood Angels Baal Predator',               Decimal('47.50'),  'https://www.warhammer.com/en-GB/shop/Blood-Angels-Baal-Predator',                   True),
    ('41-28', 'Blood Angels Librarian in Terminator Armour', Decimal('23.00'), 'https://www.warhammer.com/en-GB/shop/Blood-Angels-Terminator-Librarian-2014',    True),
    ('41-09', 'Blood Angels Sanguinary Priest',           Decimal('26.00'),  'https://www.warhammer.com/en-GB/shop/blood-angels-sanguinary-priest-2024',          True),
    ('41-03', 'Blood Angels Astorath the Grim',           Decimal('29.00'),  'https://www.warhammer.com/en-GB/shop/blood-angels-astorath-the-grim-2024',          True),
    ('41-06', 'Blood Angels Sanguinary Guard',            Decimal('38.00'),  'https://www.warhammer.com/en-GB/shop/blood-angels-sanguinary-guard-2024',           True),
    ('41-26', 'Blood Angels Captain',                     Decimal('27.00'),  'https://www.warhammer.com/en-GB/shop/blood-angels-captain-2024',                    True),
    ('41-08', 'Blood Angels The Sanguinor',               Decimal('29.00'),  'https://www.warhammer.com/en-GB/shop/blood-angels-the-sanguinor-2024',              True),
    ('41-05', 'Blood Angels Lemartes',                    Decimal('29.00'),  'https://www.warhammer.com/en-GB/shop/blood-angels-lemartes-2024',                   True),
    ('41-29', 'Codex Supplement: Blood Angels',           Decimal('21.50'),  'https://www.warhammer.com/en-GB/shop/codex-supplement-blood-angels-2024-eng',      True),
    # Temporarily out of stock — price and URL recorded, in_stock=False
    ('41-27', 'Blood Angels Chaplain With Jump Pack',     Decimal('25.00'),  'https://www.warhammer.com/en-GB/shop/Blood-Angels-Chaplain-with-Jump-Pack-2020',   False),
]


class Command(BaseCommand):
    help = 'Seed GW UK prices and URLs for Blood Angels. Idempotent.'

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

        self.stdout.write(f'Seeded {seeded} Blood Angels GW UK prices. Skipped: {skipped}.')
