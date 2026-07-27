"""
Seed Games Workshop UK prices for Grand Cathay.

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
    ('GCA-001', 'Iron Hail Gunners & Crane Gunner Teams', Decimal('54.50'),
     'https://www.warhammer.com/en-GB/shop/grand-cathay-iron-hail-and-crane-gunners-2026'),
    ('GCA-002', 'Peasant Levy', Decimal('54.50'),
     'https://www.warhammer.com/en-GB/shop/grand-cathay-peasant-levy-2026'),
    ('GCA-003', 'Astromancers of the Celestial Court', Decimal('32.50'),
     'https://www.warhammer.com/en-GB/shop/grand-cathay-astromancers-of-the-celestial-court-2026'),
    ('GCA-004', 'Grand Cannon & Fire Rain Rocket Battery', Decimal('54.50'),
     'https://www.warhammer.com/en-GB/shop/grand-cannon-and-fire-rain-rocket-battery-2025'),
    ('GCA-005', 'Jade Lancers', Decimal('54.50'),
     'https://www.warhammer.com/en-GB/shop/grand-cathay-jade-lancers-2025'),
    ('GCA-006', 'Miao Ying, the Storm Dragon', Decimal('93.00'),
     'https://www.warhammer.com/en-GB/shop/grand-cathay-miao-ying-the-storm-dragon-2025'),
    ('GCA-007', 'Sky Lantern', Decimal('98.00'),
     'https://www.warhammer.com/en-GB/shop/grand-cathay-sky-lantern-2025'),
    ('GCA-008', 'Cathayan Sentinel', Decimal('80.00'),
     'https://www.warhammer.com/en-GB/shop/grand-cathay-cathayan-sentinel-2025'),
    ('GCA-009', 'Gate Masters of the Celestial Cities', Decimal('32.50'),
     'https://www.warhammer.com/en-GB/shop/grand-cathay-gate-masters-of-the-celestial-cities-2025'),
    ('GCA-010', 'Shugengan Lord on Great Spirit Longma', Decimal('40.00'),
     'https://www.warhammer.com/en-GB/shop/shugengan-lord-on-great-spirit-longma-2025'),
    ('GCA-011', 'Arcane Journal: Dawn of the Storm Dragon', Decimal('17.00'),
     'https://www.warhammer.com/en-GB/shop/arcane-journal-dawn-of-the-storm-dragon-2025'),
    ('GCA-012', 'Arcane Journal: Armies of Grand Cathay', Decimal('17.00'),
     'https://www.warhammer.com/en-GB/shop/arcane-journal-armies-of-grand-cathay-2025-eng'),
    ('GCA-013', 'The Northern Provinces of Grand Cathay Transfer Sheet', Decimal('23.50'),
     'https://www.warhammer.com/en-GB/shop/northern-provinces-of-grand-cathay-tranfers-2025'),
    ('GCA-014', 'Jade Warriors', Decimal('54.50'),
     'https://www.warhammer.com/en-GB/shop/grand-cathay-jade-warriors-2025'),
    ('GCA-015', 'Arcane Journal: The Breaching of the Great Bastion', Decimal('17.00'),
     'https://www.warhammer.com/en-GB/shop/arcane-journal-breaching-of-the-great-bastion-2026-eng'),
]


class Command(BaseCommand):
    help = 'Seed GW UK prices and URLs for Grand Cathay. Idempotent.'

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
                f'Seeded {seeded} Grand Cathay GW UK prices. Skipped: {skipped}.'
            )
        )
