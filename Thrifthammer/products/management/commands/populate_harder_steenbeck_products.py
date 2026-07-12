"""
Management command: populate_harder_steenbeck_products

Creates the Harder & Steenbeck airbrush product line as a flat Faction
(category=Paint & Supplies, no parent_faction) — all brands in this
category are siblings for now; no umbrella "Airbrushes" grouping.

Unlike Warhammer faction populate commands, MSRP/images/URLs come from
Harder & Steenbeck's own site (harderairbrush.com), not Games Workshop.
GW does not sell airbrushes, so no 'games-workshop' CurrentPrice row is
created at all for these products — product.msrp still drives the site's
MSRP/discount reference via the existing fallback in views.py, since that
fallback only looks for a not_available=False GW row before falling back
to product.msrp.

Deliberately scoped to 9 core complete-airbrush-unit SKUs (HS-001 to
HS-009), not the full Harder & Steenbeck catalog. The other ~86 SKUs
(spare parts, Chameleon/Black Edition special colorways) were seeded,
reviewed against eBay/Amazon, and then removed on 2026-07-10 pending a
separate, smaller follow-up batch — see project notes.

Usage:
    python manage.py populate_harder_steenbeck_products
"""

import decimal

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Category, Faction, Product, Retailer

# (slug, gw_sku, name, msrp, image_url, product_url, ebay_search_name)
PRODUCTS = [
    ('harder-steenbeck-ultra-2024', 'HS-001', 'Harder & Steenbeck Ultra 2024', decimal.Decimal('120.00'), 'https://harderairbrush.com/cdn/shop/files/IMG_9672-EditV2worked1200x800.png?v=1695998799&width=1200', 'https://harderairbrush.com/products/ultra-2024', 'Harder & Steenbeck Ultra 2024'),  # was HS-001
    ('harder-steenbeck-evolution-2024-crplus', 'HS-002', 'Harder & Steenbeck EVOLUTION 2024 CRplus', decimal.Decimal('180.00'), 'https://harderairbrush.com/cdn/shop/files/ALR17756-Editcopy2in1withneedleLOWRES.png?v=1700238351&width=1200', 'https://harderairbrush.com/products/evolution-2024-2in1', 'Harder & Steenbeck EVOLUTION 2024 CRplus'),  # was HS-003
    ('harder-steenbeck-squidmar-evolution-2024-crplus-2in1', 'HS-003', 'Harder & Steenbeck Squidmar EVOLUTION  2024 CRplus 2in1', decimal.Decimal('240.00'), 'https://harderairbrush.com/cdn/shop/files/3.jpg?v=1700238812&width=5472', 'https://harderairbrush.com/products/evolution-squidmar-2024-2in1', 'Harder & Steenbeck Squidmar EVOLUTION  2024 CRplus 2in1'),  # was HS-004
    ('harder-steenbeck-infinity-2024-crplus', 'HS-004', 'Harder & Steenbeck INFINITY 2024 CRplus', decimal.Decimal('245.00'), 'https://harderairbrush.com/cdn/shop/files/INFINITY-7670-Final.jpg?v=1727077592&width=1617', 'https://harderairbrush.com/products/infinity-2024', 'Harder & Steenbeck INFINITY 2024 CRplus'),  # was HS-005
    ('harder-steenbeck-squidmar-evolution-2024-crplus-solo', 'HS-005', 'Harder & Steenbeck Squidmar EVOLUTION  2024 CRplus Solo', decimal.Decimal('180.00'), 'https://harderairbrush.com/cdn/shop/files/4.jpg?v=1700238831&width=5472', 'https://harderairbrush.com/products/squidmar-evolution-2024-crplus-copy', 'Harder & Steenbeck Squidmar EVOLUTION  2024 CRplus Solo'),  # was HS-010
    ('harder-steenbeck-giraldez-infinity-crplus-mkii', 'HS-006', 'Harder & Steenbeck Giraldez INFINITY CRplus MkII', decimal.Decimal('255.00'), 'https://harderairbrush.com/cdn/shop/files/AG_with_min_01_with_text_1220x798_47d846a6-8424-48a0-8886-05d4bf6cb56a.webp?v=1765563500&width=1220', 'https://harderairbrush.com/products/giraldez-infinity-mark-2', 'Harder & Steenbeck Giraldez INFINITY CRplus MkII'),  # was HS-011
    ('harder-steenbeck-evolution-2024-crplus-045mm', 'HS-007', 'Harder & Steenbeck EVOLUTION 2024 CRplus 0.45mm', decimal.Decimal('180.00'), 'https://harderairbrush.com/cdn/shop/files/ALR17756-Editcopy2in1withneedleLOWRES.png?v=1700238351&width=1200', 'https://harderairbrush.com/products/evolution-2024-crplus-0-45mm', 'Harder & Steenbeck EVOLUTION 2024 CRplus 0.45mm'),  # was HS-018
    ('harder-steenbeck-squidmar-infinity-cr-plus-mkii', 'HS-008', 'Harder & Steenbeck Squidmar Infinity CR plus MKII', decimal.Decimal('258.00'), 'https://harderairbrush.com/cdn/shop/files/Infinity_2026_02.png?v=1783409834&width=5472', 'https://harderairbrush.com/products/squidmar-infinity-cr-plus-mk%E2%85%B1', 'Harder & Steenbeck Squidmar Infinity CR plus MKII'),  # was HS-026
    ('harder-steenbeck-squidmar-miniature-masters-ultra', 'HS-009', 'Harder & Steenbeck Squidmar Miniature Masters ULTRA', decimal.Decimal('137.00'), 'https://harderairbrush.com/cdn/shop/files/3e5f3f3d-7007-8059-4111-d45307561e84.png?v=1782809327&width=2500', 'https://harderairbrush.com/products/squidmar-miniature-masters-ultra', 'Harder & Steenbeck Squidmar Miniature Masters ULTRA'),  # was HS-038
]


class Command(BaseCommand):
    """Populate the Harder & Steenbeck airbrush product line (idempotent)."""

    help = 'Populates Harder & Steenbeck airbrush products (HS-001 to HS-009).'

    def handle(self, *args, **options):
        category, _ = Category.objects.get_or_create(
            slug='paint-supplies',
            defaults={'name': 'Paint & Supplies'},
        )

        hs_retailer, _ = Retailer.objects.get_or_create(
            slug='harder-steenbeck',
            defaults={
                'name': 'Harder & Steenbeck',
                'website': 'https://harderairbrush.com',
                'country': 'US',
                'is_active': True,
                'is_uk': False,
            },
        )

        hs_faction, _ = Faction.objects.get_or_create(
            slug='harder-steenbeck',
            defaults={'name': 'Harder & Steenbeck', 'category': category},
        )

        products_created = 0
        products_updated = 0
        hs_prices_created = 0
        hs_prices_updated = 0

        for slug, gw_sku, name, msrp, image_url, product_url, ebay_search_name in PRODUCTS:
            product, created = Product.objects.update_or_create(
                slug=slug,
                defaults={
                    'gw_sku': gw_sku,
                    'name': name,
                    'category': category,
                    'faction': hs_faction,
                    'msrp': msrp,
                    'image_url': image_url,
                    'gw_url': '',
                    'ebay_search_name': ebay_search_name,
                    # "Harder & Steenbeck" itself contains " & ", which the eBay
                    # bundle-listing filter would otherwise reject on every
                    # legitimate result — see ebay_api_client.py's " & " check.
                    'ebay_allowed_title_words': '& +',
                    'batch_tag': 'harder-steenbeck',
                    'is_active': True,
                },
            )
            if created:
                products_created += 1
            else:
                products_updated += 1

            _, hs_price_created = CurrentPrice.objects.update_or_create(
                product=product,
                retailer=hs_retailer,
                defaults={
                    'price': msrp,
                    'url': product_url,
                    'in_stock': True,
                    'not_available': False,
                },
            )
            if hs_price_created:
                hs_prices_created += 1
            else:
                hs_prices_updated += 1

        self.stdout.write(self.style.SUCCESS(
            f'Products: {products_created} created, {products_updated} updated.'
        ))
        self.stdout.write(self.style.SUCCESS(
            f'Harder & Steenbeck prices: {hs_prices_created} created, {hs_prices_updated} updated.'
        ))
