"""
Seed Games Workshop UK prices for Hedonites of Slaanesh.

Creates the `games-workshop-uk` Retailer if it does not exist, sets
msrp_gbp on each matched Product, and creates/updates a CurrentPrice
record pointing at the GW UK product page.

Run once on Railway startup via Procfile.  Safe to re-run — idempotent.
"""
from decimal import Decimal

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Product, Retailer

_GW_UK_SLUG = 'games-workshop-uk'

# (gw_sku, label, gbp_price, gw_uk_url)
_PRICES = [
    ('HOS-001', 'Lord of Hubris', Decimal('25.00'),
     'https://www.warhammer.com/en-GB/shop/hedonites-of-slaanesh-lord-of-hubris-2023'),
    ('HOS-002', 'Synessa, the Voice of Slaanesh', Decimal('80.00'),
     'https://www.warhammer.com/en-GB/shop/Synessa-the-Voice-of-Slaanesh-2021'),
    ('HOS-003', 'Dexcessa, the Talon of Slaanesh', Decimal('80.00'),
     'https://www.warhammer.com/en-GB/shop/Dexcessa-The-Talon-Of-Slaanesh-2021'),
    ('HOS-004', 'Symbaresh Twinsouls', Decimal('40.00'),
     'https://www.warhammer.com/en-GB/shop/Hedonites-Of-Slaanesh-Symbaresh-Twinsouls-2020'),
    ('HOS-005', 'Blissbarb Seekers', Decimal('44.50'),
     'https://www.warhammer.com/en-GB/shop/Hedonites-Of-Slaanesh-Blissbarb-Seekers-2020'),
    ('HOS-006', 'Slaangor Fiendbloods', Decimal('38.00'),
     'https://www.warhammer.com/en-GB/shop/Hedonites-Of-Slaanesh-Slaangor-Fiendbloods-2020'),
    ('HOS-007', 'Glutos Orscollion, Lord of Gluttony', Decimal('88.00'),
     'https://www.warhammer.com/en-GB/shop/Hedonites-Of-Slaanesh-Glutos-Orscollion-Lord-Of-Gluttony-2020'),
    ('HOS-008', 'Blissbarb Archers', Decimal('38.00'),
     'https://www.warhammer.com/en-GB/shop/Hedonites-Of-Slaanesh-Blissbarb-Archers-2020'),
    ('HOS-009', 'Sigvald, Prince of Slaanesh', Decimal('40.00'),
     'https://www.warhammer.com/en-GB/shop/Hedonites-Of-Slaanesh-Sigvald-Prince-Of-Slaanesh-2020'),
    ('HOS-010', 'Slickblade Seekers', Decimal('44.50'),
     'https://www.warhammer.com/en-GB/shop/Hedonites-Of-Slaanesh-Slickblade-Seekers-2020'),
    ('HOS-011', 'Myrmidesh Painbringers', Decimal('40.00'),
     'https://www.warhammer.com/en-GB/shop/Hedonites-Of-Slaanesh-Myrmidesh-Painbringers-2020'),
    ('HOS-012', 'Lord of Pain', Decimal('21.50'),
     'https://www.warhammer.com/en-GB/shop/Hedonites-Of-Slaanesh-Lord-Of-Pain-2020'),
    ('HOS-013', 'Shardspeaker of Slaanesh', Decimal('21.50'),
     'https://www.warhammer.com/en-GB/shop/Hedonites-Of-Slaanesh-Shardspeaker-Of-Slaanesh-2020'),
    ('HOS-014', 'Fane of Slaanesh', Decimal('32.50'),
     'https://www.warhammer.com/en-GB/shop/Fane-of-Slaanesh-2019'),
    ('HOS-015', 'Endless Spells: Hedonites of Slaanesh', Decimal('29.50'),
     'https://www.warhammer.com/en-GB/shop/Endless-Spells-Hedonites-of-Slaanesh-2019'),
]


class Command(BaseCommand):
    help = 'Seed GW UK prices and URLs for Hedonites of Slaanesh. Idempotent.'

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
        for gw_sku, label, gbp_price, url in _PRICES:
            try:
                product = Product.objects.get(gw_sku=gw_sku)
            except Product.DoesNotExist:
                self.stderr.write(f'SKIP — SKU {gw_sku} ({label}) not in DB')
                skipped += 1
                continue

            if product.msrp_gbp != gbp_price:
                product.msrp_gbp = gbp_price
                product.save(update_fields=['msrp_gbp'])

            CurrentPrice.objects.update_or_create(
                product=product,
                retailer=retailer,
                defaults={
                    'price': gbp_price,
                    'url': url,
                    'in_stock': True,
                    'not_available': False,
                },
            )
            seeded += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Seeded {seeded} Hedonites of Slaanesh GW UK prices. Skipped: {skipped}.'
            )
        )
