"""
Seed Games Workshop UK prices for Kingdom of Bretonnia.

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
    ('KOB-001', 'Peasant Bowmen', Decimal('54.50'),
     'https://www.warhammer.com/en-GB/shop/kingdom-of-bretonnia-peasant-bowmen-2024'),
    ('KOB-002', 'Men-at-Arms', Decimal('54.50'),
     'https://www.warhammer.com/en-GB/shop/kingdom-of-bretonnia-men-at-arms-2024'),
    ('KOB-003', 'Knights of the Realm/Knights Errant', Decimal('42.50'),
     'https://www.warhammer.com/en-GB/shop/kingdom-of-bretonnia-knights-of-the-realm-2024'),
    ('KOB-004', 'Lord on Royal Pegasus', Decimal('42.50'),
     'https://www.warhammer.com/en-GB/shop/kingdom-of-bretonnia-lord-on-royal-pegasus-2024'),
    ('KOB-005', 'Pegasus Knights', Decimal('42.50'),
     'https://www.warhammer.com/en-GB/shop/kingdom-of-bretonnia-pegasus-knights-2024'),
    ('KOB-006', 'Battle Standard Bearer on Royal Pegasus', Decimal('42.50'),
     'https://www.warhammer.com/en-GB/shop/kingdom-of-bretonnia-battle-standard-on-royal-pegasus-2024'),
    ('KOB-007', 'Knights of the Realm on Foot', Decimal('54.50'),
     'https://www.warhammer.com/en-GB/shop/kingdom-of-bretonnia-knights-of-the-realm-on-foot-2024'),
    ('KOB-008', 'Arcane Journal: Kingdom of Bretonnia', Decimal('17.00'),
     'https://www.warhammer.com/en-GB/shop/arcane-journal-kingdom-of-bretonnia-eng-2024'),
]


class Command(BaseCommand):
    help = 'Seed GW UK prices and URLs for Kingdom of Bretonnia. Idempotent.'

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
                f'Seeded {seeded} Kingdom of Bretonnia GW UK prices. Skipped: {skipped}.'
            )
        )
