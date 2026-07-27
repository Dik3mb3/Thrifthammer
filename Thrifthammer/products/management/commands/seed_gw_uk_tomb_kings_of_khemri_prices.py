"""
Seed Games Workshop UK prices for Tomb Kings of Khemri.

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
    ('TKK-001', 'Skeleton Chariots', Decimal('54.50'),
     'https://www.warhammer.com/en-GB/shop/tomb-kings-of-khemri-skeleton-chariots-2024'),
    ('TKK-002', 'Tomb Kings Skeleton Warriors/Archers', Decimal('54.50'),
     'https://www.warhammer.com/en-GB/shop/tomb-kings-of-khemri-skeleton-warriors-2024'),
    ('TKK-003', 'Liche Priests', Decimal('32.50'),
     'https://www.warhammer.com/en-GB/shop/tomb-kings-of-khemri-liche-priests-2025'),
    ('TKK-004', 'Royal Heralds', Decimal('32.50'),
     'https://www.warhammer.com/en-GB/shop/tomb-kings-of-khemri-royal-heralds-2025'),
    ('TKK-005', 'Tomb Kings Skeleton Horsemen/Horse Archers', Decimal('42.50'),
     'https://www.warhammer.com/en-GB/shop/tomb-kings-of-khemri-skeleton-horsemen-2024'),
    ('TKK-006', 'Tomb King/Liche Priest on Necrolith Bone Dragon', Decimal('64.50'),
     'https://www.warhammer.com/en-GB/shop/tomb-kings-of-khemri-tomb-king-on-necrolith-bone-dragon-2024'),
    ('TKK-007', 'Necropolis Knights', Decimal('42.50'),
     'https://www.warhammer.com/en-GB/shop/tomb-kings-of-khemri-necropolis-knights-2024'),
    ('TKK-008', 'Khemrian Warsphinx', Decimal('49.50'),
     'https://www.warhammer.com/en-GB/shop/tomb-kings-of-khemri-khemrian-warsphinx-2024'),
    ('TKK-009', 'Necrosphinx', Decimal('49.50'),
     'https://www.warhammer.com/en-GB/shop/tomb-kings-of-khemri-necrosphinx-2024'),
    ('TKK-010', 'Sepulchral Stalkers', Decimal('42.50'),
     'https://www.warhammer.com/en-GB/shop/tomb-kings-of-khemri-sepulchral-stalkers-2024'),
    ('TKK-011', 'Tomb Guard', Decimal('54.50'),
     'https://www.warhammer.com/en-GB/shop/tomb-kings-of-khemri-tomb-guard-2024'),
    ('TKK-012', 'Arcane Journal: The War of Settra\'s Fury', Decimal('17.00'),
     'https://www.warhammer.com/en-GB/shop/arcane-journal-the-war-of-settras-fury-pb-eng-2025'),
    ('TKK-013', 'Arcane Journal: Tomb Kings of Khemri', Decimal('17.00'),
     'https://www.warhammer.com/en-GB/shop/arcane-journal-tomb-kings-of-khemri-eng-2024'),
]


class Command(BaseCommand):
    help = 'Seed GW UK prices and URLs for Tomb Kings of Khemri. Idempotent.'

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
                f'Seeded {seeded} Tomb Kings of Khemri GW UK prices. Skipped: {skipped}.'
            )
        )
