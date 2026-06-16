"""
Seed Games Workshop UK prices for Dark Angels.

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
    ('44-02', 'Dark Angels Ezekiel',                     Decimal('20.50'),  'https://www.warhammer.com/en-GB/shop/Dark-Angels-Ezekiel-Grand-Master-of-Librarians',                  True),
    ('44-03', 'Dark Angels Asmodai',                     Decimal('29.00'),  'https://www.warhammer.com/en-GB/shop/dark-angels-asmodai-master-of-repentance-2024',                   True),
    ('44-04', 'Dark Angels Azrael',                      Decimal('29.50'),  'https://www.warhammer.com/en-GB/shop/dark-angels-azrael-2023',                                         True),
    ('44-05', 'Dark Angels Belial',                      Decimal('29.00'),  'https://www.warhammer.com/en-GB/shop/dark-angelsbelial-grand-master-of-the-deathwing-2024',            True),
    ('44-06', "Dark Angels Lion El'Jonson",               Decimal('44.50'),  'https://www.warhammer.com/en-GB/shop/dark-angels-lion-el-johnson-2023',                                True),
    ('44-07', 'Dark Angels Lazarus',                     Decimal('29.00'),  'https://www.warhammer.com/en-GB/shop/Dark-Angels-Master-Lazarus-2020',                                 True),
    ('44-08', 'Dark Angels Sammael',                     Decimal('38.00'),  'https://www.warhammer.com/en-GB/shop/Dark-Angels-Sammael',                                             True),
    ('44-09', 'Dark Angels Ravenwing Command Squad',     Decimal('40.00'),  'https://www.warhammer.com/en-GB/shop/Ravenwing-Command-Squad-2020',                                    True),
    ('44-10', 'Dark Angels Deathwing Knights',           Decimal('44.00'),  'https://www.warhammer.com/en-GB/shop/dark-angels-deathwing-knights-2024',                              True),
    ('44-12', 'Dark Angels Ravenwing Black Knights',     Decimal('40.00'),  'https://www.warhammer.com/en-GB/shop/Ravenwing-Command-Squad-2020',                                    True),
    ('44-13', 'Dark Angels Inner Circle Companions',     Decimal('38.00'),  'https://www.warhammer.com/en-GB/shop/dark-angels-inner-circle-companions-2024',                        True),
    ('44-14', 'Dark Angels Ravenwing Dark Talon',        Decimal('54.50'),  'https://www.warhammer.com/en-GB/shop/Dark-Angels-Ravenwing-Dark-Talon',                                True),
    ('44-15', 'Dark Angels Ravenwing Darkshroud',        Decimal('49.50'),  'https://www.warhammer.com/en-GB/shop/Dark-Angels-Ravenwing-Darkshroud',                                True),
    ('44-16', 'Dark Angels Land Speeder Vengeance',      Decimal('49.50'),  'https://www.warhammer.com/en-GB/shop/Dark-Angels-Land-Speeder-Vengeance',                              True),
    ('44-17', 'Dark Angels Nephilim Jetfighter',         Decimal('54.50'),  'https://www.warhammer.com/en-GB/shop/Dark-Angels-Nephilim-Jetfigher',                                  True),
    ('44-20', 'Dark Angels Combat Patrol',               Decimal('105.00'), 'https://www.warhammer.com/en-GB/shop/combat-patrol-dark-angels-2024',                                  True),
    ('44-21', 'Codex Supplement: Dark Angels',           Decimal('21.50'),  'https://www.warhammer.com/en-GB/shop/codex-supplement-dark-angels-eng-2024',                           True),
    ('44-22', 'Dark Angels Interrogator-Chaplain',       Decimal('23.00'),  'https://www.warhammer.com/en-GB/shop/Dark-Angels-Interrogator-Chaplain-2017',                          True),
    ('44-23', 'Ravenwing Bike Squadron',                 Decimal('35.50'),  'https://www.warhammer.com/en-GB/shop/Dark-Angels-Ravenwing-Bike-Squadron',                             True),
]


class Command(BaseCommand):
    help = 'Seed GW UK prices and URLs for Dark Angels. Idempotent.'

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

        self.stdout.write(f'Seeded {seeded} Dark Angels GW UK prices. Skipped: {skipped}.')
