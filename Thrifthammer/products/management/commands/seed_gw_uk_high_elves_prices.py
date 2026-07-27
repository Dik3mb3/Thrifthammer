"""
Seed Games Workshop UK prices for High Elves.

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
    ('HER-001', 'Tiranoc Chariots', Decimal('54.50'),
     'https://www.warhammer.com/en-GB/shop/high-elf-realms-tiranoc-chariot-2025'),
    ('HER-002', 'Arcane Journal: High Elf Realms', Decimal('17.00'),
     'https://www.warhammer.com/en-GB/shop/arcane-journal-high-elf-realms-2025-eng'),
    ('HER-003', 'Elven Spearmen', Decimal('54.50'),
     'https://www.warhammer.com/en-GB/shop/high-elf-realms-elven-spearmen-2025'),
    ('HER-004', 'Silver Helms', Decimal('40.00'),
     'https://www.warhammer.com/en-GB/shop/high-elf-realms-silver-helms-2025'),
    ('HER-005', 'High Elf Loremaster', Decimal('18.50'),
     'https://www.warhammer.com/en-GB/shop/high-elf-realms-high-elf-loremaster-2025'),
    ('HER-006', 'Flamespyre Phoenix', Decimal('49.50'),
     'https://www.warhammer.com/en-GB/shop/high-elf-realms-flamespyre-phoenix-2025'),
    ('HER-007', 'Lothern Skycutter', Decimal('49.50'),
     'https://www.warhammer.com/en-GB/shop/high-elf-realms-lothern-skycutter-2025'),
    ('HER-008', 'Dragon Princes of Caledor', Decimal('54.50'),
     'https://www.warhammer.com/en-GB/shop/high-elf-realms-dragon-princes-of-caledor-2025'),
    ('HER-009', 'Phoenix Guard', Decimal('54.50'),
     'https://www.warhammer.com/en-GB/shop/high-elf-realms-phoenix-guard-2025'),
    ('HER-010', 'Sisters of Avelorn', Decimal('33.00'),
     'https://www.warhammer.com/en-GB/shop/high-elf-realms-sisters-of-avelorn-2025'),
    ('HER-011', 'High Elf Mages', Decimal('27.50'),
     'https://www.warhammer.com/en-GB/shop/high-elf-realms-mages-2025'),
    ('HER-012', 'High Elf Lords', Decimal('27.50'),
     'https://www.warhammer.com/en-GB/shop/high-elf-realms-high-elf-lords-2025'),
    ('HER-013', 'Ellyrian Reavers', Decimal('54.50'),
     'https://www.warhammer.com/en-GB/shop/high-elf-realms-ellyrian-reavers-2025'),
    ('HER-014', 'White Lions of Chrace', Decimal('54.50'),
     'https://www.warhammer.com/en-GB/shop/high-elf-realms-white-lions-of-chrace-2025'),
    ('HER-015', 'Eagle-claw Bolt Throwers', Decimal('35.50'),
     'https://www.warhammer.com/en-GB/shop/high-elf-realms-eagle-claw-bolt-throwers-2025'),
    ('HER-016', 'Lord on Dragon', Decimal('49.50'),
     'https://www.warhammer.com/en-GB/shop/high-elf-realms-lord-on-dragon-2025'),
    ('HER-017', 'Swordmasters of Hoeth', Decimal('54.50'),
     'https://www.warhammer.com/en-GB/shop/high-elf-realms-swordmasters-of-hoeth-2025'),
    ('HER-020', 'Great Eagle of the Elven Realms', Decimal('20.50'),
     'https://www.warhammer.com/en-GB/shop/great-eagles-of-the-elven-realms-2025'),
    ('HER-021', 'Handmaiden of the Everqueen', Decimal('9.00'),
     'https://www.warhammer.com/en-GB/shop/high-elf-realms-handmaiden-of-the-everqueen-2025'),
    ('HER-022', 'Korhil Lionmane', Decimal('12.00'),
     'https://www.warhammer.com/en-GB/shop/high-elf-realms-korhil-lionmane-2025'),
    ('HER-023', 'High Elf Realms Transfer Sheet', Decimal('23.50'),
     'https://www.warhammer.com/en-GB/shop/high-elf-realms-transfer-sheet-2025'),
    ('HER-024', 'Elven Archers', Decimal('54.50'),
     'https://www.warhammer.com/en-GB/shop/high-elf-realms-elven-archers-2025'),
    ('HER-025', 'Lothern Sea Guard', Decimal('54.50'),
     'https://www.warhammer.com/en-GB/shop/high-elf-realms-lothern-sea-guard-2025'),
]


class Command(BaseCommand):
    help = 'Seed GW UK prices and URLs for High Elves. Idempotent.'

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
                f'Seeded {seeded} High Elves GW UK prices. Skipped: {skipped}.'
            )
        )
