"""
Seed Games Workshop UK prices for Chaos Daemons.

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
    ('CD-001', "Be'lakor, the Dark Master",                          Decimal('105.00'), 'https://www.warhammer.com/en-GB/shop/Chaos-Daemons-Belakor-The-Dark-Master-2021',      True),
    ('CD-002', "Syll'Esske: The Vengeful Allegiance",                Decimal('38.00'),  'https://www.warhammer.com/en-GB/shop/The-Vengeful-Allegiance-2019',                    True),
    ('CD-003', 'The Contorted Epitome',                              Decimal('38.00'),  'https://www.warhammer.com/en-GB/shop/The-Contorted-Epitome-2019',                      True),
    ('CD-004', 'Infernal Enrapturess',                               Decimal('29.50'),  'https://www.warhammer.com/en-GB/shop/Infernal-Enrapturess-2019',                       True),
    ('CD-005', 'The Masque',                                         Decimal('25.00'),  'https://www.warhammer.com/en-GB/shop/The-Masque-2019',                                 True),
    ('CD-006', 'Skulltaker',                                         Decimal('26.00'),  'https://www.warhammer.com/en-GB/shop/Skulltaker-2019',                                 True),
    ('CD-007', 'Skull Altar',                                        Decimal('32.50'),  'https://www.warhammer.com/en-GB/shop/Skull-Altar-2019',                                True),
    ('CD-008', 'Feculent Gnarlmaw',                                  Decimal('32.50'),  'https://www.warhammer.com/en-GB/shop/Feculent-Gnarlmaw-2018',                          True),
    ('CD-009', 'Horticulous Slimux',                                 Decimal('40.00'),  'https://www.warhammer.com/en-GB/shop/Horticulous-Slimux-2018',                         True),
    ('CD-010', 'Changecaster',                                       Decimal('35.50'),  'https://www.warhammer.com/en-GB/shop/changecaster-2022',                               True),
    ('CD-011', 'Karanak',                                            Decimal('27.00'),  'https://www.warhammer.com/en-GB/shop/Karanak-the-Hound-of-Vengeance-2019',             True),
    ('CD-013', 'Sloppity Bilepiper',                                 Decimal('25.00'),  'https://www.warhammer.com/en-GB/shop/Sloppity-Bilepiper-Herald-Of-Nurgle-2018',        True),
    ('CD-014', 'Poxbringer',                                         Decimal('20.50'),  'https://www.warhammer.com/en-GB/shop/Poxbringer-Herald-Of-Nurgle-2018',                True),
    ('CD-015', 'The Changeling',                                     Decimal('25.00'),  'https://www.warhammer.com/en-GB/shop/the-changeling-2016',                             True),
    ('CD-016', 'Burning Chariot of Tzeentch',                        Decimal('35.50'),  'https://www.warhammer.com/en-GB/shop/Burning-Chariot-of-Tzeentch',                     True),
    ('CD-017', 'Exalted Flamer of Tzeentch',                         Decimal('35.50'),  'https://www.warhammer.com/en-GB/shop/Exalted-Flamer-of-Tzeentch',                      True),
    ('CD-018', 'Fateskimmer, Herald of Tzeentch on Burning Chariot', Decimal('35.50'),  'https://www.warhammer.com/en-GB/shop/herald-of-tzeentch-on-burning-chariot-2016',      True),
    ('CD-019', 'Skull Cannon',                                       Decimal('29.50'),  'https://www.warhammer.com/en-GB/shop/Daemons-Of-Khorne-Skull-Cannon',                  True),
    ('CD-020', 'Rendmaster, Herald of Khorne on Blood Throne',       Decimal('29.50'),  'https://www.warhammer.com/en-GB/shop/Daemons-Of-Khorne-Bloodthrone',                   True),
    ('CD-021', 'Soul Grinder',                                       Decimal('49.50'),  'https://www.warhammer.com/en-GB/shop/Soul-Grinder',                                    True),
    # Temporarily out of stock — price and URL recorded, in_stock=False
    ('CD-012', 'Bloodmaster, Herald of Khorne',                      Decimal('20.50'),  'https://www.warhammer.com/en-GB/shop/Bloodmaster-Herald-of-Khorne-2019',               False),
]


class Command(BaseCommand):
    help = 'Seed GW UK prices and URLs for Chaos Daemons. Idempotent.'

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

        self.stdout.write(f'Seeded {seeded} Chaos Daemons GW UK prices. Skipped: {skipped}.')
