"""
Seed Games Workshop UK prices for Grey Knights.

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
    ('57-02', 'Grand Master Voldus',                  Decimal('26.00'),  'https://www.warhammer.com/en-GB/shop/Grey-Knights-Grand-Master-Voldus-2017',                        True),
    ('57-06', 'Grey Knights Strike Squad',             Decimal('42.50'),  'https://www.warhammer.com/en-GB/shop/Grey-Knights-Strike-Squad-2017',                               True),
    ('57-08', 'Grey Knights Terminators',              Decimal('38.00'),  'https://www.warhammer.com/en-GB/shop/Grey-Knights-Terminators-2017',                                True),
    ('57-20', 'Grey Knights Combat Patrol',            Decimal('105.00'), 'https://www.warhammer.com/en-GB/shop/combat-patrol-grey-knights-2025',                              True),
    ('57-21', 'Castellan Crowe',                      Decimal('29.50'),  'https://www.warhammer.com/en-GB/shop/grey-knights-castellan-crowe-2022',                            True),
    ('57-22', 'Codex: Grey Knights',                  Decimal('38.00'),  'https://www.warhammer.com/en-GB/shop/codex-grey-knights-2025-eng',                                  True),
    ('57-23', 'Grand Master in Nemesis Dreadknight',  Decimal('49.50'),  'https://www.warhammer.com/en-GB/shop/grey-knights-grandmaster-in-nemesis-dreadknight-2025',         True),
    ('57-24', 'Grey Knights Interceptor Squad',        Decimal('42.50'),  'https://www.warhammer.com/en-GB/shop/Grey-Knights-Interceptor-Squad-2022',                         True),
    ('57-25', 'Grey Knights Paladins',                 Decimal('38.00'),  'https://www.warhammer.com/en-GB/shop/Grey-Knights-Paladins-2017',                                  True),
    ('57-26', 'Grey Knights Purgation Squad',          Decimal('42.50'),  'https://www.warhammer.com/en-GB/shop/Grey-Knights-Purgation-Squad-2022',                           True),
    ('57-27', 'Grey Knights Purifier Squad',           Decimal('42.50'),  'https://www.warhammer.com/en-GB/shop/Grey-Knights-Purifier-Squad-2022',                            True),
]


class Command(BaseCommand):
    help = 'Seed GW UK prices and URLs for Grey Knights. Idempotent.'

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

        self.stdout.write(f'Seeded {seeded} Grey Knights GW UK prices. Skipped: {skipped}.')
