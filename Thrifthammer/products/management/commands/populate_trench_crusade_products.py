"""
Management command: populate_trench_crusade_products

Creates the Trench Crusade product line as a new top-level Category
(standalone wargame, not a Games Workshop product -- no GW retailer row).
MSRP/images/URLs come from trenchcrusade.com directly.

product.gw_url is populated with the trenchcrusade.com product URL (not a
real GW link) -- this enables the "View" button on the product detail page.
product_detail.html shows "View on Trench Crusade" instead of "View on GW"
for this category specifically.

Usage:
    python manage.py populate_trench_crusade_products
"""

import decimal

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Category, Product, Retailer

# (slug, gw_sku, name, msrp, image_url, product_url, ebay_search_name)
PRODUCTS = [
    ('trench-crusade-carcass-front', 'TC-001', 'Trench Crusade Carcass Front', decimal.Decimal('129.99'), 'https://www.trenchcrusade.com/app/uploads/2026/03/Carcass-Front-box.jpg', 'https://www.trenchcrusade.com/product/pre-order-carcass-front/', 'Trench Crusade Carcass Front'),
    ('prussian-stosstruppen-warband', 'TC-002', 'Prussian Stosstruppen Warband', decimal.Decimal('49.99'), 'https://www.trenchcrusade.com/app/uploads/2025/10/Prussian-Stosstruppen-Warband-scaled.png', 'https://www.trenchcrusade.com/product/prussian-stosstruppen-warband/', 'Prussian Stosstruppen Warband'),
    ('prussian-stosstruppen', 'TC-003', 'Prussian Stosstruppen', decimal.Decimal('34.99'), 'https://www.trenchcrusade.com/app/uploads/2026/02/Prussian-Stosstruppen-scaled.png', 'https://www.trenchcrusade.com/product/prussian-stosstruppen/', 'Prussian Stosstruppen'),
    ('new-antioch-sniper-priests', 'TC-004', 'New Antioch Sniper Priests', decimal.Decimal('24.99'), 'https://www.trenchcrusade.com/app/uploads/2026/02/New-Antioch-Sniper-Priests-scaled.png', 'https://www.trenchcrusade.com/product/new-antioch-sniper-priests/', 'New Antioch Sniper Priests'),
]


class Command(BaseCommand):
    """Populate the Trench Crusade product line (idempotent)."""

    help = 'Populates Trench Crusade products (TC-001 to TC-004).'

    def handle(self, *args, **options):
        category, _ = Category.objects.get_or_create(
            slug='trench-crusade',
            defaults={'name': 'Trench Crusade'},
        )

        trench_crusade, _ = Retailer.objects.get_or_create(
            slug='trench-crusade',
            defaults={
                'name': 'Trench Crusade',
                'website': 'https://www.trenchcrusade.com',
                'country': 'US',
                'is_active': True,
                'is_uk': False,
            },
        )

        products_created = 0
        products_updated = 0
        tc_prices_created = 0
        tc_prices_updated = 0

        for slug, gw_sku, name, msrp, image_url, product_url, ebay_search_name in PRODUCTS:
            product, created = Product.objects.update_or_create(
                slug=slug,
                defaults={
                    'gw_sku': gw_sku,
                    'name': name,
                    'category': category,
                    'msrp': msrp,
                    'image_url': image_url,
                    'gw_url': product_url,
                    'ebay_search_name': ebay_search_name,
                    'batch_tag': 'trench-crusade',
                    'is_active': True,
                },
            )
            if created:
                products_created += 1
            else:
                products_updated += 1

            _, tc_price_created = CurrentPrice.objects.update_or_create(
                product=product,
                retailer=trench_crusade,
                defaults={
                    'price': msrp,
                    'url': product_url,
                    'in_stock': True,
                    'not_available': False,
                },
            )
            if tc_price_created:
                tc_prices_created += 1
            else:
                tc_prices_updated += 1

        self.stdout.write(self.style.SUCCESS(
            f'Products: {products_created} created, {products_updated} updated.'
        ))
        self.stdout.write(self.style.SUCCESS(
            f'Trench Crusade prices: {tc_prices_created} created, {tc_prices_updated} updated.'
        ))
