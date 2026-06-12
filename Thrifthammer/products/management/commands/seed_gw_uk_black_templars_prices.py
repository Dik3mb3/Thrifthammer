"""
Seed Games Workshop UK prices for Black Templars.

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
    ('55-30', 'Combat Patrol: Black Templars',      Decimal('105.00'), 'https://www.warhammer.com/en-GB/shop/combat-patrol-black-templars-2025',            True),
    ('55-25', 'Black Templars Castellan',           Decimal('25.00'),  'https://www.warhammer.com/en-GB/shop/black-templars-castellan-2021',                True),
    ('55-22', "Emperor's Champion",                 Decimal('27.00'),  'https://www.warhammer.com/en-GB/shop/black-templars-emperors-champion-2021',        True),
    ('55-24', 'Chaplain Grimaldus & Retinue',       Decimal('35.50'),  'https://www.warhammer.com/en-GB/shop/black-templars-grimaldus-and-retinue-2021',    True),
    ('55-23', 'Black Templars Sword Brethren',      Decimal('40.00'),  'https://www.warhammer.com/en-GB/shop/black-templars-sword-brethren-2021',           True),
    ('55-26', 'Execrator',                          Decimal('26.00'),  'https://www.warhammer.com/en-GB/shop/black-templars-execrator-2025',                True),
    ('55-28', 'Black Templars Marshal',             Decimal('25.00'),  'https://www.warhammer.com/en-GB/shop/black-templars-marshal-2021',                  True),
    ('55-21', 'High Marshal Helbrecht',             Decimal('35.50'),  'https://www.warhammer.com/en-GB/shop/black-templars-high-marshal-helbrecht-2021',   True),
    ('55-20', 'Primaris Crusader Squad',            Decimal('40.00'),  'https://www.warhammer.com/en-GB/shop/black-templars-primaris-crusader-squad-2021',  True),
    ('55-27', 'Crusade Ancient',                    Decimal('27.00'),  'https://www.warhammer.com/en-GB/shop/black-templars-crusade-ancient-2025',          True),
    ('58-01', 'Codex Supplement: Black Templars',   Decimal('21.50'),  'https://www.warhammer.com/en-GB/shop/codex-supplement-black-templars-2025-eng',    True),
]


class Command(BaseCommand):
    help = 'Seed GW UK prices and URLs for Black Templars. Idempotent.'

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

        self.stdout.write(f'Seeded {seeded} Black Templars GW UK prices. Skipped: {skipped}.')
