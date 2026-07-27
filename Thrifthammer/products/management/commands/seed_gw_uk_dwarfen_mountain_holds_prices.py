"""
Seed Games Workshop UK prices for Dwarfen Mountain Holds.

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
    ('DMH-001', 'Dwarfen Mountain Holds Battalion', Decimal('115.00'),
     'https://www.warhammer.com/en-GB/shop/battalion-dwarfen-mountain-holds-2024'),
    ('DMH-002', 'Dwarf King With Oathstone', Decimal('18.50'),
     'https://www.warhammer.com/en-GB/shop/dwarfen-mountain-holds-dwarf-king-with-oathstone-2024'),
    ('DMH-003', 'Dwarf Slayer of Legend', Decimal('18.50'),
     'https://www.warhammer.com/en-GB/shop/dwarfen-mountain-holds-slayer-of-legend-2024'),
    ('DMH-004', 'Dwarf Cannon & Organ Gun', Decimal('35.50'),
     'https://www.warhammer.com/en-GB/shop/dwarfen-mountain-holds-dwarf-cannon-and-organ-gun-2024'),
    ('DMH-005', 'Dwarf Gyrocopters', Decimal('49.50'),
     'https://www.warhammer.com/en-GB/shop/dwarfen-mountain-holds-gyrocopters-and-gyrobombers-2024'),
    ('DMH-006', 'Dwarf Miners', Decimal('40.00'),
     'https://www.warhammer.com/en-GB/shop/dwarfen-mountain-holds-dwarf-miners-2024'),
    ('DMH-007', 'Dwarf Lords with Shieldbearers', Decimal('32.50'),
     'https://www.warhammer.com/en-GB/shop/dwarfen-mountain-holds-dwarf-lords-with-shieldbearers-2024'),
    ('DMH-008', 'Dwarf Hammerers', Decimal('54.50'),
     'https://www.warhammer.com/en-GB/shop/dwarfen-mountain-holds-dwarf-hammerers-2024'),
    ('DMH-009', 'Dwarf Ironbreakers', Decimal('54.50'),
     'https://www.warhammer.com/en-GB/shop/dwarf-mountain-holds-dwarf-ironbreakers-2024'),
    ('DMH-010', 'Dwarf Quarrelers', Decimal('54.50'),
     'https://www.warhammer.com/en-GB/shop/dwarfen-mountain-holds-dwarf-quarrellers-2024'),
    ('DMH-011', 'Dwarf Warriors', Decimal('54.50'),
     'https://www.warhammer.com/en-GB/shop/dwarfen-mountain-holds-dwarf-warriors-2024'),
    ('DMH-012', 'Dwarf Runesmith', Decimal('18.50'),
     'https://www.warhammer.com/en-GB/shop/dwarfen-mountain-holds-dwarf-runesmith-2024'),
]


class Command(BaseCommand):
    help = 'Seed GW UK prices and URLs for Dwarfen Mountain Holds. Idempotent.'

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
                f'Seeded {seeded} Dwarfen Mountain Holds GW UK prices. Skipped: {skipped}.'
            )
        )
