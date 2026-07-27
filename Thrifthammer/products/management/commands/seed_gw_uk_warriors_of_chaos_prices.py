"""
Seed Games Workshop UK prices for Warriors of Chaos.

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
    ('WOC-001', 'Chaos Marauder Horsemen', Decimal('54.50'),
     'https://www.warhammer.com/en-GB/shop/warriors-of-chaos-chaos-marauder-horsemen-2026'),
    ('WOC-002', 'Arcane Journal: Warriors of Chaos', Decimal('17.00'),
     'https://www.warhammer.com/en-GB/shop/arcane-journal-warriors-of-chaos-sb-eng-2024'),
    ('WOC-003', 'Chaos Marauders', Decimal('54.50'),
     'https://www.warhammer.com/en-GB/shop/warriors-of-chaos-chaos-marauders-2026'),
    ('WOC-004', 'Chaos Chariots', Decimal('54.50'),
     'https://www.warhammer.com/en-GB/shop/warriors-of-chaos-chaos-chariots-2024'),
    ('WOC-005', 'Chaos Warhounds', Decimal('40.00'),
     'https://www.warhammer.com/en-GB/shop/warriors-of-chaos-chaos-warhounds-2024'),
    ('WOC-006', 'Chimera', Decimal('40.00'),
     'https://www.warhammer.com/en-GB/shop/warriors-of-chaos-chimera-2024'),
    ('WOC-007', 'Sorcerer of Chaos', Decimal('19.00'),
     'https://www.warhammer.com/en-GB/shop/warriors-of-chaos-sorcerer-of-chaos-2024'),
    ('WOC-008', 'Arcane Journal: The Razing of Westerland', Decimal('17.00'),
     'https://www.warhammer.com/en-GB/shop/arcane-journal-the-razing-of-westerland-eng-2025'),
    ('WOC-009', 'Dragon Ogres', Decimal('40.00'),
     'https://www.warhammer.com/en-GB/shop/warriors-of-chaos-dragon-ogres-2024'),
    ('WOC-010', 'Chaos Lord on Manticore', Decimal('49.50'),
     'https://www.warhammer.com/en-GB/shop/warriors-of-chaos-lord-on-manticore-2024'),
]


class Command(BaseCommand):
    help = 'Seed GW UK prices and URLs for Warriors of Chaos. Idempotent.'

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
                f'Seeded {seeded} Warriors of Chaos GW UK prices. Skipped: {skipped}.'
            )
        )
