"""
Seed Games Workshop UK prices for Wood Elf Realms.

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
    ('WER-001', 'Wood Elf Realms Battalion', Decimal('115.00'),
     'https://www.warhammer.com/en-GB/shop/battalion-wood-elf-realms-2025'),
    ('WER-002', 'Arcane Journal: Wood Elf Realms', Decimal('17.00'),
     'https://www.warhammer.com/en-GB/shop/arcane-journal-wood-elf-realms-sb-eng-2025'),
    ('WER-003', 'Wood Elf Noble on Forest Dragon', Decimal('52.00'),
     'https://www.warhammer.com/en-GB/shop/wood-elf-realms-noble-on-forest-dragon-2025'),
    ('WER-004', 'Araloth, Lord of Talsyn', Decimal('18.50'),
     'https://www.warhammer.com/en-GB/shop/wood-elf-realms-araloth-lord-of-talsyn-2025'),
    ('WER-005', 'Wild Riders', Decimal('54.50'),
     'https://www.warhammer.com/en-GB/shop/wood-elf-realms-wildriders-2025'),
    ('WER-006', 'Glade Riders', Decimal('38.50'),
     'https://www.warhammer.com/en-GB/shop/wood-elf-realms-glade-riders-2025'),
    ('WER-007', 'Eternal Guard', Decimal('54.50'),
     'https://www.warhammer.com/en-GB/shop/wood-elf-realms-eternal-guard-2025'),
    ('WER-008', 'Glade Guard', Decimal('54.50'),
     'https://www.warhammer.com/en-GB/shop/wood-elf-realms-glade-guard-2025'),
]


class Command(BaseCommand):
    help = 'Seed GW UK prices and URLs for Wood Elf Realms. Idempotent.'

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
                f'Seeded {seeded} Wood Elf Realms GW UK prices. Skipped: {skipped}.'
            )
        )
