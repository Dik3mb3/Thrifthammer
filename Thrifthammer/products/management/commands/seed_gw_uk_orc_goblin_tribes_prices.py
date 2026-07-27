"""
Seed Games Workshop UK prices for Orc & Goblin Tribes.

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
    ('OGT-001', 'Goblin Shaman', Decimal('18.50'),
     'https://www.warhammer.com/en-GB/shop/orc-and-goblin-tribes-goblin-shaman-2024'),
    ('OGT-002', 'Goblin Wolf Rider Mob', Decimal('42.50'),
     'https://www.warhammer.com/en-GB/shop/orc-and-goblin-tribes-goblin-wolf-rider-mob-2024'),
    ('OGT-003', 'Goblin Mob', Decimal('54.50'),
     'https://www.warhammer.com/en-GB/shop/orc-and-goblin-tribes-goblin-mob-2024'),
    ('OGT-004', 'Orc Boar Chariots', Decimal('54.50'),
     'https://www.warhammer.com/en-GB/shop/orc-and-goblin-tribes-orc-boar-chariots-2024'),
    ('OGT-005', 'Black Orc Mob', Decimal('54.50'),
     'https://www.warhammer.com/en-GB/shop/orc-and-goblin-tribes-black-orc-mob-2024'),
    ('OGT-006', 'Orc Boar Boyz Mob', Decimal('42.50'),
     'https://www.warhammer.com/en-GB/shop/orc-and-goblin-tribes-orc-boar-boyz-mob-2024'),
    ('OGT-007', 'Orc Boyz & Orc Arrer Boyz Mob', Decimal('54.50'),
     'https://www.warhammer.com/en-GB/shop/orc-and-goblin-tribes-orc-boyz-and-orc-arrer-boyz-mobs-2024'),
    ('OGT-008', 'Orc Boyz Mob', Decimal('54.50'),
     'https://www.warhammer.com/en-GB/shop/orc-goblin-tribes-orc-boyz-mob-2024'),
    ('OGT-009', 'Orc Bosses', Decimal('29.00'),
     'https://www.warhammer.com/en-GB/shop/orc-goblin-tribes-orc-bosses-2024'),
    ('OGT-010', 'Night Goblin Mob', Decimal('54.50'),
     'https://www.warhammer.com/en-GB/shop/orc-and-goblin-tribes-night-goblin-mob-2024'),
]


class Command(BaseCommand):
    help = 'Seed GW UK prices and URLs for Orc & Goblin Tribes. Idempotent.'

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
                f'Seeded {seeded} Orc & Goblin Tribes GW UK prices. Skipped: {skipped}.'
            )
        )
