"""
Management command: populate_gaahleri_products

Creates the Gaahleri airbrush product line as a flat Faction
(category=Paint & Supplies, no parent_faction) — matches the Harder &
Steenbeck precedent exactly.

MSRP/images/URLs come from Gaahleri's own site (gaahleri.com), not
Games Workshop. GW does not sell airbrushes, so no 'games-workshop'
CurrentPrice row is created at all for these products — product.msrp
still drives the site's MSRP/discount reference via the existing
fallback in views.py, since that fallback only looks for a
not_available=False GW row before falling back to product.msrp.

No Noble Knight or Miniature Market rows either -- neither retailer
carries this brand, so no seed_nk_/seed_mm_ files exist for it.

GAH-003, GAH-006, and GAH-010 have "&" in their name/search name — set
ebay_allowed_title_words so the eBay bundle-listing filter (which
rejects any title containing " & " by default) doesn't reject
legitimate results for just these three.

Two source Excel image cells (for "Aventus Tailor Made Edition 0.2mm"
and its "& 0.4mm" variant) contained a pasted-in base64 image blob
instead of a hosted URL; the user supplied a real replacement URL for
both (GAH-006, GAH-007) — see conversation history.

Usage:
    python manage.py populate_gaahleri_products
"""

import decimal

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Category, Faction, Product, Retailer

_AMP_SKUS = {'GAH-003', 'GAH-006', 'GAH-010'}

# (slug, gw_sku, name, msrp, image_url, product_url, ebay_search_name)
PRODUCTS = [
    ('aventus-black-aurora', 'GAH-001', 'Aventus Black Aurora', decimal.Decimal('175.49'), 'https://www.gaahleri.com/cdn/shop/files/01gaahleriAVENTUS_012e4f3e-5500-4c41-b766-0a05632f3cb2.jpg?v=1763417686&width=1946', 'https://www.gaahleri.com/products/aventus-black-aurora', 'Aventus Black Aurora'),
    ('aventus-titan-mist', 'GAH-002', 'Aventus Titan Mist', decimal.Decimal('175.49'), 'https://www.gaahleri.com/cdn/shop/files/01gaahleriAVENTUS_49412ea2-d146-428f-9023-1e642c0ede90.jpg?v=1763446515&width=1946', 'https://www.gaahleri.com/products/aventus-titan-mist', 'Aventus Titan Mist'),
    ('aventus-midnight-tide-rex-ver', 'GAH-003', 'Aventus Midnight Tide & Rex Ver.', decimal.Decimal('179.99'), 'https://www.gaahleri.com/cdn/shop/files/01gaahleriAVENTUS_6bfa063f-b36e-42a2-904d-81987c717eda.jpg?v=1784000469&width=1946', 'https://www.gaahleri.com/products/aventus-midnight-tide-barbatos-rex-ver', 'Aventus Midnight Tide & Rex Ver.'),
    ('aventus-verdant-ember', 'GAH-004', 'Aventus Verdant Ember', decimal.Decimal('175.49'), 'https://www.gaahleri.com/cdn/shop/files/01gaahleriAVENTUS_2ff2c79f-0847-404e-8ef3-83d58d4e91b9.jpg?v=1763446472&width=1946', 'https://www.gaahleri.com/products/aventus-verdant-ember', 'Aventus Verdant Ember'),
    ('aventus-crimson-crow', 'GAH-005', 'Aventus Crimson Crow', decimal.Decimal('175.49'), 'https://www.gaahleri.com/cdn/shop/files/01gaahleriAVENTUS_343efc10-3a6c-45f4-a606-5118b41f4363.jpg?v=1763446453&width=1946', 'https://www.gaahleri.com/products/aventus-crimson-crown', 'Aventus Crimson Crow'),
    ('aventus-tailor-made-edition-02mm-04mm', 'GAH-006', 'Aventus Tailor Made Edition 0.2mm & 0.4mm', decimal.Decimal('274.99'), 'https://www.gaahleri.com/cdn/shop/files/02_aventus_tailor_made.jpg?v=1762480679&width=1000', 'https://www.gaahleri.com/products/pen-customization', 'Aventus Tailor Made Edition 0.2mm & 0.4mm'),
    ('aventus-tailor-made-edition-02mm', 'GAH-007', 'Aventus Tailor Made Edition 0.2mm', decimal.Decimal('239.99'), 'https://www.gaahleri.com/cdn/shop/files/02_aventus_tailor_made.jpg?v=1762480679&width=1000', 'https://www.gaahleri.com/products/pen-customization', 'Aventus Tailor Made Edition 0.2mm'),
    ('premium-series-ghpm-mobius-02mm-airbrush', 'GAH-008', 'Premium Series GHPM-Mobius 0.2mm Airbrush', decimal.Decimal('76.99'), 'https://www.gaahleri.com/cdn/shop/files/GHPM-Mobius_02_75631de4-0def-4dbf-ad1b-c20e718aa3d8.jpg?v=1717228807&width=990', 'https://www.gaahleri.com/products/premium-series-ghpm-mobius-0-2mm', 'Premium Series GHPM-Mobius 0.2mm Airbrush'),
    ('premium-series-ghpm-mobius-03mm-airbrush', 'GAH-009', 'Premium Series GHPM-Mobius 0.3mm Airbrush', decimal.Decimal('71.99'), 'https://www.gaahleri.com/cdn/shop/files/GHPM-Mobius_03_1c43189e-8223-4cac-a68f-b09a69435766.jpg?v=1717228913&width=990', 'https://www.gaahleri.com/products/premium-series-ghpm-mobius-0-3mm', 'Premium Series GHPM-Mobius 0.3mm Airbrush'),
    ('premium-series-ghpm-mobius-sp-03-05mm-airbrush', 'GAH-010', 'Premium Series GHPM-Mobius SP 0.3 & 0.5mm Airbrush', decimal.Decimal('79.99'), 'https://www.gaahleri.com/cdn/shop/files/01GaahleriPremiumSeriesGHPM-MobiusSPEng.jpg?v=1732747713&width=1946', 'https://www.gaahleri.com/products/premium-series-ghpm-mobius-sp-0-3-0-5mm', 'Premium Series GHPM-Mobius SP 0.3 & 0.5mm Airbrush'),
    ('premium-series-ghpm-mobius-tg-05mm-airbrush', 'GAH-011', 'Premium Series GHPM-Mobius TG 0.5mm Airbrush', decimal.Decimal('109.99'), 'https://www.gaahleri.com/cdn/shop/files/01GaahleriPremiumSeriesGHPM-MobiusTGEng_09f70bd2-3cd3-4f41-b33e-06384450bd9b.jpg?v=1740123635&width=1946', 'https://www.gaahleri.com/products/premium-series-ghpm-mobius-tg', 'Premium Series GHPM-Mobius TG 0.5mm Airbrush'),
    ('premium-series-ghpm-mobius-tg-05mm-kenji-ver-airbrush', 'GAH-012', 'Premium Series GHPM-Mobius TG 0.5mm Kenji Ver. Airbrush', decimal.Decimal('119.99'), 'https://www.gaahleri.com/cdn/shop/files/01GaahleriPremiumSeriesGHPM-MobiusTGKenjiVerEng.jpg?v=1746415694&width=1946', 'https://www.gaahleri.com/products/premium-series-ghpm-mobius-tg-0-5mm-kenji-ver', 'Premium Series GHPM-Mobius TG 0.5mm Kenji Ver. Airbrush'),
    ('ace-series-ghac-swallowtail-sd-airbrush', 'GAH-013', 'Ace Series GHAC-Swallowtail SD Airbrush', decimal.Decimal('119.99'), 'https://www.gaahleri.com/cdn/shop/files/01GaahleriAceSeriesGHAC-SwallowtailSDVerEng.jpg?v=1735625989&width=1946', 'https://www.gaahleri.com/products/ghac-swallowtail-sd-airbrush', 'Ace Series GHAC-Swallowtail SD Airbrush'),
    ('ace-series-ghac-swallowtail-sd-plaban-ver-airbrush', 'GAH-014', 'Ace Series GHAC-Swallowtail SD Plaban Ver. Airbrush', decimal.Decimal('119.99'), 'https://www.gaahleri.com/cdn/shop/files/01GaahleriAceSeriesGHAC-SwallowtailSDPlabanVerEng.jpg?v=1736125088&width=1946', 'https://www.gaahleri.com/products/ace-series-swallowtail-sd-plaban', 'Ace Series GHAC-Swallowtail SD Plaban Ver. Airbrush'),
    ('ace-series-ghac-swallowtail-barbatos-rex-ver-airbrush', 'GAH-015', 'Ace Series GHAC-Swallowtail Barbatos Rex Ver. Airbrush', decimal.Decimal('133.99'), 'https://www.gaahleri.com/cdn/shop/files/11-27-59.jpg?v=1717228573&width=990', 'https://www.gaahleri.com/products/gaahleri-airbrush-ghac-swallowtail-barbatos', 'Ace Series GHAC-Swallowtail Barbatos Rex Ver. Airbrush'),
]


class Command(BaseCommand):
    """Populate the Gaahleri airbrush product line (idempotent)."""

    help = 'Populates Gaahleri airbrush products (GAH-001 to GAH-015).'

    def handle(self, *args, **options):
        category, _ = Category.objects.get_or_create(
            slug='paint-supplies',
            defaults={'name': 'Paint & Supplies'},
        )

        gaahleri_retailer, _ = Retailer.objects.get_or_create(
            slug='gaahleri',
            defaults={
                'name': 'Gaahleri',
                'website': 'https://www.gaahleri.com',
                'country': 'US',
                'is_active': True,
                'is_uk': False,
            },
        )

        gaahleri_faction, _ = Faction.objects.get_or_create(
            slug='gaahleri',
            defaults={'name': 'Gaahleri', 'category': category},
        )

        products_created = 0
        products_updated = 0
        gaahleri_prices_created = 0
        gaahleri_prices_updated = 0

        for slug, gw_sku, name, msrp, image_url, product_url, ebay_search_name in PRODUCTS:
            product, created = Product.objects.update_or_create(
                slug=slug,
                defaults={
                    'gw_sku': gw_sku,
                    'name': name,
                    'category': category,
                    'faction': gaahleri_faction,
                    'msrp': msrp,
                    'image_url': image_url,
                    'gw_url': '',
                    'ebay_search_name': ebay_search_name,
                    'ebay_allowed_title_words': '&' if gw_sku in _AMP_SKUS else '',
                    'batch_tag': 'gaahleri',
                    'is_active': True,
                },
            )
            if created:
                products_created += 1
            else:
                products_updated += 1

            _, gaahleri_price_created = CurrentPrice.objects.update_or_create(
                product=product,
                retailer=gaahleri_retailer,
                defaults={
                    'price': msrp,
                    'url': product_url,
                    'in_stock': True,
                    'not_available': False,
                },
            )
            if gaahleri_price_created:
                gaahleri_prices_created += 1
            else:
                gaahleri_prices_updated += 1

        self.stdout.write(self.style.SUCCESS(
            f'Products: {products_created} created, {products_updated} updated.'
        ))
        self.stdout.write(self.style.SUCCESS(
            f'Gaahleri prices: {gaahleri_prices_created} created, {gaahleri_prices_updated} updated.'
        ))
