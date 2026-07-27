"""
Seed Games Workshop UK prices for Beastmen Brayherds.

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
    ('BBH-001', 'Tuskgor Chariot', Decimal('27.00'),
     'https://www.warhammer.com/en-GB/shop/beastmen-brayherds-tuskgor-chariot-2025'),
    ('BBH-002', 'Beastman Chieftain', Decimal('18.50'),
     'https://www.warhammer.com/en-GB/shop/beastmen-brayherds-beastmen-chieftain-2025'),
    ('BBH-003', 'Ungor Herd', Decimal('54.50'),
     'https://www.warhammer.com/en-GB/shop/beastmen-brayherds-ungor-herd-2025'),
    ('BBH-004', 'Cygor/Ghorgon', Decimal('49.50'),
     'https://www.warhammer.com/en-GB/shop/beastmen-brayherds-cygor-2025'),
    ('BBH-005', 'Minotaur Herd', Decimal('35.50'),
     'https://www.warhammer.com/en-GB/shop/beastmen-brayherds-minotaur-herd-2025'),
    ('BBH-006', 'Gor Herd', Decimal('54.50'),
     'https://www.warhammer.com/en-GB/shop/beastmen-brayherds-gor-herd-2025'),
    ('BBH-007', 'Bestigor Herd', Decimal('54.50'),
     'https://www.warhammer.com/en-GB/shop/beastmen-brayherds-bestigor-herd-2025'),
    ('BBH-008', 'Beastman Shaman', Decimal('18.50'),
     'https://www.warhammer.com/en-GB/shop/beastmen-brayherds-beastman-shaman-2025'),
]


class Command(BaseCommand):
    help = 'Seed GW UK prices and URLs for Beastmen Brayherds. Idempotent.'

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
                f'Seeded {seeded} Beastmen Brayherds GW UK prices. Skipped: {skipped}.'
            )
        )
