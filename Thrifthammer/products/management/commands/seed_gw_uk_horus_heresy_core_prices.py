"""
Seed Games Workshop UK prices for Horus Heresy (Core).

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
    ('HA-001', 'MKVI Tactical Squad', Decimal('54.50'),
     'https://www.warhammer.com/en-GB/shop/legiones-astartes-mk6-tactical-squad-2022'),
    ('HA-002', 'Contemptor Dreadnought', Decimal('40.00'),
     'https://www.warhammer.com/en-GB/shop/legiones-astartes-contemptor-dreadnought-2022'),
    ('HA-010', 'Horus Heresy MKIII Tactical Squad', Decimal('50.50'),
     'https://www.warhammer.com/en-GB/shop/horus-heresy-legion-astartes-mk3-tactical-squad-2023'),
    ('HA-012', 'Deimos Pattern Predator Battle Tank', Decimal('47.50'),
     'https://www.warhammer.com/en-GB/shop/legiones-astartes-predator-battle-tank-2022'),
    ('HA-021', 'Horus Heresy Leviathan Dreadnought', Decimal('54.50'),
     'https://www.warhammer.com/en-GB/shop/leviathan-siege-dreadnought-with-claw-and-drill-weapons-2022'),
    ('HA-030', 'Horus Heresy Cataphractii Terminators', Decimal('42.50'),
     'https://www.warhammer.com/en-GB/shop/cataphractii-terminators-combi-bolters-and-power-fists-2026'),
    ('HA-040', 'Horus Heresy Spartan Assault Tank', Decimal('74.00'),
     'https://www.warhammer.com/en-GB/shop/legiones-astartes-spartan-assault-tank-2022'),
    ('HA-041', 'Horus Heresy Sicaran Battle Tank', Decimal('55.00'),
     'https://www.warhammer.com/en-GB/shop/legiones-astartes-sicaran-battle-tank-2022'),
]


class Command(BaseCommand):
    help = 'Seed GW UK prices and URLs for Horus Heresy (Core). Idempotent.'

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
                f'Seeded {seeded} Horus Heresy (Core) GW UK prices. Skipped: {skipped}.'
            )
        )
