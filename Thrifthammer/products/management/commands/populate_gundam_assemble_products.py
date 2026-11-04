"""
Management command: populate_gundam_assemble_products

Creates the Gundam Assemble miniatures game as a top-level Category in the main
catalogue (a tabletop miniatures game by Bandai, not a Games Workshop product).
The same 14 products also exist in the Gundam section (gundam.Product, series
"Gundam Assemble", batch_tag "gundam-assemble"); this command seeds the
main-catalogue copy so the game appears as its own ThriftHammer category too.

Prices, images and the barcode-anchored handles come from Gundam Planet, which
is the only retailer seeded here. Amazon and eBay rows are NOT created by this
command: eBay links are written by the automated updater, Amazon links by
find_amazon_asins once a listing exists.

Only the 14 included SKUs are touched (ST01, DX01 to DX03, EX01 to EX09, SC01).
Paint Pack PA01 and the Mr. Color paint are paint, not models, and are left out.

Usage:
    python manage.py populate_gundam_assemble_products
"""

import decimal

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Category, Product, Retailer

_CDN = 'https://cdn.shopify.com/s/files/1/0671/4769/4277/files/'
_GP_PRODUCTS = 'https://www.gundamplanet.com/products/'

# (gw_sku, handle, name, msrp, image file on the Gundam Planet CDN)
PRODUCTS = [
    ('GA-ST01', 'st01-gundam-assemble-starter-set-01', 'Gundam Assemble Starter Set 01 (ST01)', '34.95', 'st01-gundam-assemble-starter-set-01-00.jpg?v=1793032947'),
    ('GA-DX01', 'dx01-gundam-assemble-deluxe-set-01', 'Gundam Assemble Deluxe Set 01 (DX01)', '96.95', 'dx01-gundam-assemble-deluxe-set-011.jpg?v=1772584815'),
    ('GA-DX02', 'dx02-gundam-assemble-deluxe-set-02', 'Gundam Assemble Deluxe Set 02 (DX02)', '162.95', 'dx02-gundam-assemble-deluxe-set-021.jpg?v=1772584843'),
    ('GA-DX03', 'dx03-gundam-assemble-deluxe-set-03', 'Gundam Assemble Deluxe Set 03 (DX03)', '162.95', 'dx03-gundam-assemble-deluxe-set-03-gp.jpg?v=1784315437'),
    ('GA-EX01', 'ex01-gundam-assemble-expansion-pack-01', 'Gundam Assemble Expansion Pack 01 (EX01)', '39.95', 'ex01-gundam-assemble-expansion-pack-011.jpg?v=1772584821'),
    ('GA-EX02', 'ex02-gundam-assemble-expansion-pack-02', 'Gundam Assemble Expansion Pack 02 (EX02)', '39.95', 'ex02-gundam-assemble-expansion-pack-021.jpg?v=1772584824'),
    ('GA-EX03', 'ex03-gundam-assemble-expansion-pack-03', 'Gundam Assemble Expansion Pack 03 (EX03)', '39.95', 'ex03-gundam-assemble-expansion-pack-031.jpg?v=1772584832'),
    ('GA-EX04', 'ex04-gundam-assemble-expansion-pack-04', 'Gundam Assemble Expansion Pack 04 (EX04)', '39.95', 'ex04-gundam-assemble-expansion-pack-041.jpg?v=1772584835'),
    ('GA-EX05', 'ex05-gundam-assemble-expansion-pack-05', 'Gundam Assemble Expansion Pack 05 (EX05)', '39.95', 'ex05-gundam-assemble-expansion-pack-051.jpg?v=1772584848'),
    ('GA-EX06', 'ex06-gundam-assemble-expansion-pack-06', 'Gundam Assemble Expansion Pack 06 (EX06)', '39.95', 'ex06-gundam-assemble-expansion-set-06-gp.jpg?v=1784315122'),
    ('GA-EX07', 'ex07-gundam-assemble-expansion-pack-07', 'Gundam Assemble Expansion Pack 07 (EX07)', '39.95', 'ex07-gundam-assemble-expansion-set-07-gp.jpg?v=1784315180'),
    ('GA-EX08', 'ex08-gundam-assemble-expansion-pack-08', 'Gundam Assemble Expansion Pack 08 (EX08)', '39.95', 'ex08-gundam-assemble-expansion-set-08-gp.jpg?v=1784315309'),
    ('GA-EX09', 'ex09-gundam-assemble-expansion-pack-09', 'Gundam Assemble Expansion Pack 09 (EX09)', '39.95', 'ex09-gundam-assemble-expansion-set-09-gp.jpg?v=1784315399'),
    ('GA-SC01', 'sc01-gundam-assemble-scenario-pack-01', 'Gundam Assemble Scenario Pack 01 (SC01)', '53.95', 'sc01-gundam-assemble-scenario-pack-01-gp.jpg?v=1784315349'),
]


class Command(BaseCommand):
    """Populate the Gundam Assemble category in the main catalogue (idempotent)."""

    help = 'Populates Gundam Assemble products (GA-ST01 to GA-SC01) with Gundam Planet prices.'

    def handle(self, *args, **options):
        category, _ = Category.objects.get_or_create(
            slug='gundam-assemble',
            defaults={'name': 'Gundam Assemble'},
        )
        gundam_planet, _ = Retailer.objects.get_or_create(
            slug='gundam-planet',
            defaults={
                'name': 'Gundam Planet',
                'website': 'https://www.gundamplanet.com',
                'country': 'US',
                'is_active': True,
                'is_uk': False,
            },
        )

        counts = {'created': 0, 'updated': 0, 'prices_created': 0, 'prices_updated': 0}
        for gw_sku, handle, name, msrp, image_file in PRODUCTS:
            self._upsert(category, gundam_planet, counts, gw_sku, handle, name,
                         decimal.Decimal(msrp), _CDN + image_file)

        self.stdout.write(self.style.SUCCESS(
            f'Products: {counts["created"]} created, {counts["updated"]} updated.'
        ))
        self.stdout.write(self.style.SUCCESS(
            f'Gundam Planet prices: {counts["prices_created"]} created, '
            f'{counts["prices_updated"]} updated.'
        ))

    def _upsert(self, category, gundam_planet, counts, gw_sku, handle, name, msrp, image_url):
        """Create or update one product and its Gundam Planet price row."""
        product, created = Product.objects.update_or_create(
            slug=handle,
            defaults={
                'gw_sku': gw_sku,
                'name': name,
                'category': category,
                'msrp': msrp,
                'image_url': image_url,
                'batch_tag': 'gundam-assemble',
                'is_active': True,
            },
        )
        counts['created' if created else 'updated'] += 1

        _, price_created = CurrentPrice.objects.update_or_create(
            product=product,
            retailer=gundam_planet,
            defaults={
                'price': msrp,
                'url': _GP_PRODUCTS + handle,
                'in_stock': True,
                'not_available': False,
            },
        )
        counts['prices_created' if price_created else 'prices_updated'] += 1
