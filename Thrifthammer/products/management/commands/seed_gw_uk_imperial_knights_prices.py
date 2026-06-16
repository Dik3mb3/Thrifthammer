"""
Seed Games Workshop UK prices for Imperial Knights.

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
    ('31-06', 'Cerastus Knight Lancer',              Decimal('129.00'), 'https://www.warhammer.com/en-GB/shop/horus-heresy-cerastus-knight-lancer-2023',                     True),
    ('31-66', 'Cerastus Knight Castigator',           Decimal('129.00'), 'https://www.warhammer.com/en-GB/shop/horus-heresy-cerastus-knight-castigator-2023',                 True),
    ('31-67', 'Cerastus Knight Acheron',              Decimal('129.00'), 'https://www.warhammer.com/en-GB/shop/horus-heresy-cerastus-knight-acheron-2023',                    True),
    ('54-15', 'Imperial Knight Preceptor/Canis Rex',  Decimal('115.00'), 'https://www.warhammer.com/en-GB/shop/imperial-knights-knight-preceptor-canis-rex-2025',             True),
    ('54-20', 'Imperial Knight Armigers Warglaive',   Decimal('60.00'),  'https://www.warhammer.com/en-GB/shop/imperial-knights-knight-armigers-armiger-warglaive-2022',      True),
    ('54-21', 'Imperial Knight Dominus Valiant',      Decimal('118.00'), 'https://www.warhammer.com/en-GB/shop/imperial-knights-knight-dominus-knight-valiant-2022',          True),
    ('54-22', 'Imperial Knight Questoris',            Decimal('115.00'), 'https://www.warhammer.com/en-GB/shop/imperial-knights-knight-questoris-2025',                       True),
]


class Command(BaseCommand):
    help = 'Seed GW UK prices and URLs for Imperial Knights. Idempotent.'

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

        self.stdout.write(f'Seeded {seeded} Imperial Knights GW UK prices. Skipped: {skipped}.')
