"""
Management command: populate_iwata_products

Creates the Iwata airbrush product line as a flat Faction
(category=Paint & Supplies, no parent_faction) — matches the Harder &
Steenbeck precedent exactly.

MSRP/images/URLs come from Iwata's own site (iwata-airbrush.com), not
Games Workshop. GW does not sell airbrushes, so no 'games-workshop'
CurrentPrice row is created at all for these products — product.msrp
still drives the site's MSRP/discount reference via the existing
fallback in views.py, since that fallback only looks for a
not_available=False GW row before falling back to product.msrp.

No Noble Knight or Miniature Market rows either -- neither retailer
carries this brand, so no seed_nk_/seed_mm_ files exist for it.

Usage:
    python manage.py populate_iwata_products
"""

import decimal

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Category, Faction, Product, Retailer

# (slug, gw_sku, name, msrp, image_url, product_url, ebay_search_name)
PRODUCTS = [
    ('iwata-eclipse-hp-bcs-siphon-feed-dual-action-airbrush', 'IWA-001', 'Iwata Eclipse HP-BCS Siphon Feed Dual Action Airbrush', decimal.Decimal('143'), 'https://www.iwata-airbrush.com/mm5/graphics/00000001/ECL2000_HP-BCS-A1_300x264.jpg', 'https://www.iwata-airbrush.com/iwata-eclipse-hp-bcs-wbtl.html', 'Iwata Eclipse HP-BCS Siphon Feed Dual Action Airbrush'),
    ('iwata-eclipse-hp-bcs-value-set', 'IWA-002', 'Iwata Eclipse HP-BCS Value Set', decimal.Decimal('161'), 'https://www.iwata-airbrush.com/mm5/graphics/00000001/ECL2001-HP-BCS%20Value%20Set-A1_300x300.jpg', 'https://www.iwata-airbrush.com/iwata-eclipse-bcs-wbtlhos.html', 'Iwata Eclipse HP-BCS Value Set'),
    ('iwata-eclipse-hp-bcs-6-pack-with-zippered-airbrush-case', 'IWA-003', 'Iwata Eclipse HP-BCS 6-Pack with Zippered Airbrush Case', decimal.Decimal('798'), 'https://www.iwata-airbrush.com/mm5/graphics/00000001/ECL2006M-A1_300x289.jpg', 'https://www.iwata-airbrush.com/iwata-eclipse-hp-bcs-6-pak.html', 'Iwata Eclipse HP-BCS 6-Pack with Zippered Airbrush Case'),
    ('iwata-eclipse-hp-bs-gravity-feed-dual-action-airbrush', 'IWA-004', 'Iwata Eclipse HP-BS Gravity Feed Dual Action Airbrush', decimal.Decimal('180'), 'https://www.iwata-airbrush.com/mm5/graphics/00000001/ECL2500_HP-BS-A1_300x113.jpg', 'https://www.iwata-airbrush.com/iwata-eclipse-hp-bs.html', 'Iwata Eclipse HP-BS Gravity Feed Dual Action Airbrush'),
    ('iwata-eclipse-hp-cs-gravity-feed-dual-action-airbrush', 'IWA-005', 'Iwata Eclipse HP-CS Gravity Feed Dual Action Airbrush', decimal.Decimal('198'), 'https://www.iwata-airbrush.com/mm5/graphics/00000001/ECL4500_HP-CS-A1_300x133.jpg', 'https://www.iwata-airbrush.com/iwata-eclipse-hp-cs.html', 'Iwata Eclipse HP-CS Gravity Feed Dual Action Airbrush'),
    ('iwata-eclipse-hp-cs-value-set', 'IWA-006', 'Iwata Eclipse HP-CS Value Set', decimal.Decimal('210'), 'https://www.iwata-airbrush.com/mm5/graphics/00000001/3/ECL4501-A1_300x300.webp', 'https://www.iwata-airbrush.com/eclipse-cs-with-hose.html', 'Iwata Eclipse HP-CS Value Set'),
    ('iwata-g-series-g6-bottle-set-side-feed-airbrush-gun', 'IWA-007', 'Iwata G-Series G6 Bottle Set Side Feed Airbrush-Gun', decimal.Decimal('465'), 'https://www.iwata-airbrush.com/mm5/graphics/00000001/ECL9000-A1_300x300.jpg', 'https://www.iwata-airbrush.com/iwata-pistl-grip-g6.html', 'Iwata G-Series G6 Bottle Set Side Feed Airbrush-Gun'),
    ('iwata-g-series-g6-side-feed-airbrush-gun', 'IWA-008', 'Iwata G-Series G6 Side Feed Airbrush-Gun', decimal.Decimal('516.75'), 'https://www.iwata-airbrush.com/mm5/graphics/00000001/ECL9001_G6-A1_185x300.jpg', 'https://www.iwata-airbrush.com/g6-wpc-61-fluid-cup.html', 'Iwata G-Series G6 Side Feed Airbrush-Gun'),
    ('iwata-g-series-g3-gravity-feed-airbrush-gun', 'IWA-009', 'Iwata G-Series G3 Gravity Feed Airbrush-Gun', decimal.Decimal('665.5'), 'https://www.iwata-airbrush.com/mm5/graphics/00000001/ECL9100_G3-A1_153x300.jpg', 'https://www.iwata-airbrush.com/iwata-pistl-grip-g3.html', 'Iwata G-Series G3 Gravity Feed Airbrush-Gun'),
    ('iwata-g-series-g5-gravity-feed-airbrush-gun', 'IWA-010', 'Iwata G-Series G5 Gravity Feed Airbrush-Gun', decimal.Decimal('665.5'), 'https://www.iwata-airbrush.com/mm5/graphics/00000001/ECL9200_G5-A1_149x300.jpg', 'https://www.iwata-airbrush.com/iwata-pistl-grip-g5.html', 'Iwata G-Series G5 Gravity Feed Airbrush-Gun'),
    ('iwata-high-performance-hp-b-plus-gravity-feed-dual-action-airbrush', 'IWA-011', 'Iwata High Performance HP-B Plus Gravity Feed Dual Action Airbrush', decimal.Decimal('202'), 'https://www.iwata-airbrush.com/mm5/graphics/00000001/H2001_HP-BPlus-A1_300x109.jpg', 'https://www.iwata-airbrush.com/hp-b-plus-airbrush.html', 'Iwata High Performance HP-B Plus Gravity Feed Dual Action Airbrush'),
    ('iwata-hi-line-hp-bh-gravity-feed-dual-action-airbrush', 'IWA-012', 'Iwata Hi-Line HP-BH Gravity Feed Dual Action Airbrush', decimal.Decimal('225'), 'https://www.iwata-airbrush.com/mm5/graphics/00000001/H2100_HP-BH-A1_300x113.jpg', 'https://www.iwata-airbrush.com/hp-bh-hi-line-airbrush.html', 'Iwata Hi-Line HP-BH Gravity Feed Dual Action Airbrush'),
    ('iwata-high-performance-hp-sb-plus-side-feed-dual-action-airbrush', 'IWA-013', 'Iwata High Performance HP-SB Plus Side Feed Dual Action Airbrush', decimal.Decimal('275'), 'https://www.iwata-airbrush.com/mm5/graphics/00000001/H3001_HP-SBPlus-A1_300x98.jpg', 'https://www.iwata-airbrush.com/hp-sb-plus-airbrush.html', 'Iwata High Performance HP-SB Plus Side Feed Dual Action Airbrush'),
    ('iwata-high-performance-hp-c-plus-gravity-feed-dual-action-airbrush', 'IWA-014', 'Iwata High Performance HP-C Plus Gravity Feed Dual Action Airbrush', decimal.Decimal('235'), 'https://www.iwata-airbrush.com/mm5/graphics/00000001/H4001_HP-CPlus-A1_300x136.jpg', 'https://www.iwata-airbrush.com/hp-c-plus-airbrush.html', 'Iwata High Performance HP-C Plus Gravity Feed Dual Action Airbrush'),
    ('iwata-hi-line-hp-ch-gravity-feed-dual-action-airbrush', 'IWA-015', 'Iwata Hi-Line HP-CH Gravity Feed Dual Action Airbrush', decimal.Decimal('301'), 'https://www.iwata-airbrush.com/mm5/graphics/00000001/H4100_HP-CH-A1_300x138.jpg', 'https://www.iwata-airbrush.com/hp-ch-hi-line-airbrush.html', 'Iwata Hi-Line HP-CH Gravity Feed Dual Action Airbrush'),
    ('iwata-high-performance-hp-bc1-plus-siphon-feed-dual-action-airbrush', 'IWA-016', 'Iwata High Performance HP-BC1 Plus Siphon Feed Dual Action Airbrush', decimal.Decimal('295'), 'https://www.iwata-airbrush.com/mm5/graphics/00000001/H5001_HP-BC1Plus-A1_300x200.jpg', 'https://www.iwata-airbrush.com/hp-bc-plus-airbrush.html', 'Iwata High Performance HP-BC1 Plus Siphon Feed Dual Action Airbrush'),
    ('iwata-hi-line-hp-th-gravity-feed-dual-action-trigger-airbrush', 'IWA-017', 'Iwata Hi-Line HP-TH Gravity Feed Dual Action Trigger Airbrush', decimal.Decimal('319'), 'https://www.iwata-airbrush.com/mm5/graphics/00000001/H5200_HP-TH-A1_300x168.jpg', 'https://www.iwata-airbrush.com/hp-th-hiline-airbrush.html', 'Iwata Hi-Line HP-TH Gravity Feed Dual Action Trigger Airbrush'),
    ('anest-iwata-rg-3-side-feed-spray-gun', 'IWA-018', 'ANEST IWATA RG-3 Side Feed Spray Gun', decimal.Decimal('467.25'), 'https://www.iwata-airbrush.com/mm5/graphics/00000001/H9100_RG3L-A1_209x300.jpg', 'https://www.iwata-airbrush.com/rg-3l-wpc-61-cup.html', 'ANEST IWATA RG-3 Side Feed Spray Gun'),
    ('iwata-custom-micron-cm-b-gravity-feed-dual-action-airbrush', 'IWA-019', 'Iwata Custom Micron CM-B Gravity Feed Dual Action Airbrush', decimal.Decimal('549'), 'https://www.iwata-airbrush.com/mm5/graphics/00000001/ICM2002_CM-B-A1_300x189.jpg', 'https://www.iwata-airbrush.com/icm-2002-custom-micron-b2.html', 'Iwata Custom Micron CM-B Gravity Feed Dual Action Airbrush'),
    ('iwata-custom-micron-cm-c-gravity-feed-dual-action-airbrush', 'IWA-020', 'Iwata Custom Micron CM-C Gravity Feed Dual Action Airbrush', decimal.Decimal('549'), 'https://www.iwata-airbrush.com/mm5/graphics/00000001/ICM4002_CM-C-A1_300x203.jpg', 'https://www.iwata-airbrush.com/icm-4002-custom-micron-c2.html', 'Iwata Custom Micron CM-C Gravity Feed Dual Action Airbrush'),
    ('iwata-custom-micron-cm-c-plus-gravity-feed-dual-action-airbrush', 'IWA-021', 'Iwata Custom Micron CM-C Plus Gravity Feed Dual Action Airbrush', decimal.Decimal('670'), 'https://www.iwata-airbrush.com/mm5/graphics/00000001/ICM4502_CM-CPlus-A1_300x220.jpg', 'https://www.iwata-airbrush.com/icm-4502-custom-micron-cp2.html', 'Iwata Custom Micron CM-C Plus Gravity Feed Dual Action Airbrush'),
    ('anest-iwata-lph-50-side-feed-spray-gun', 'IWA-022', 'ANEST IWATA LPH-50 Side Feed Spray Gun', decimal.Decimal('429.5'), 'https://www.iwata-airbrush.com/mm5/graphics/00000001/LPH-50_PC61_A1_194x300.jpg', 'https://www.iwata-airbrush.com/lph-50-spray-gun-w-cup.html', 'ANEST IWATA LPH-50 Side Feed Spray Gun'),
    ('anest-iwata-lph-80-gravity-feed-spray-gun', 'IWA-023', 'ANEST IWATA LPH-80 Gravity Feed Spray Gun', decimal.Decimal('418'), 'https://www.iwata-airbrush.com/mm5/graphics/00000001/LPH-80-A1_155x300.jpg', 'https://www.iwata-airbrush.com/lph-80-miniature-spray-gun.html', 'ANEST IWATA LPH-80 Gravity Feed Spray Gun'),
    ('neo-for-iwata-bcn-siphon-feed-dual-action-airbrush', 'IWA-024', 'NEO for Iwata BCN Siphon Feed Dual Action Airbrush', decimal.Decimal('105.25'), 'https://www.iwata-airbrush.com/mm5/graphics/00000001/N2000_BCN-A1_300x231.jpg', 'https://www.iwata-airbrush.com/neo-for-iwata-siphon.html', 'NEO for Iwata BCN Siphon Feed Dual Action Airbrush'),
    ('neo-for-iwata-cn-gravity-feed-dual-action-airbrush', 'IWA-025', 'NEO for Iwata CN Gravity Feed Dual Action Airbrush', decimal.Decimal('100'), 'https://www.iwata-airbrush.com/mm5/graphics/00000001/N4500_CN-A1_300x133.jpg', 'https://www.iwata-airbrush.com/neo-for-iwata-gravity.html', 'NEO for Iwata CN Gravity Feed Dual Action Airbrush'),
    ('neo-for-iwata-trn2-side-feed-dual-action-trigger-airbrush', 'IWA-026', 'NEO for Iwata TRN2 Side Feed Dual Action Trigger Airbrush', decimal.Decimal('211.5'), 'https://www.iwata-airbrush.com/mm5/graphics/00000001/N5000-A1_300x300.jpg', 'https://www.iwata-airbrush.com/trn2-trigger-neo-airbrush-siphon.html', 'NEO for Iwata TRN2 Side Feed Dual Action Trigger Airbrush'),
    ('neo-for-iwata-trn1-gravity-feed-trigger-airbrush', 'IWA-027', 'NEO for Iwata TRN1 Gravity Feed Trigger Airbrush', decimal.Decimal('211.5'), 'https://www.iwata-airbrush.com/mm5/graphics/00000001/N5500_TRN1-A1_300x244.jpg', 'https://www.iwata-airbrush.com/trn1-trigger-neo-airbrush-gravity.html', 'NEO for Iwata TRN1 Gravity Feed Trigger Airbrush'),
    ('iwata-revolution-hp-sar-siphon-feed-single-action-airbrush', 'IWA-028', 'Iwata Revolution HP-SAR Siphon Feed Single Action Airbrush', decimal.Decimal('113'), 'https://www.iwata-airbrush.com/mm5/graphics/00000001/R1000_HP-SAR-A1_300x219.jpg', 'https://www.iwata-airbrush.com/revolution-single-action.html', 'Iwata Revolution HP-SAR Siphon Feed Single Action Airbrush'),
    ('iwata-revolution-hp-m1-gravity-feed-single-action-airbrush', 'IWA-029', 'Iwata Revolution HP-M1 Gravity Feed Single Action Airbrush', decimal.Decimal('191'), 'https://www.iwata-airbrush.com/mm5/graphics/00000001/R1050_HP-M1-A1_300x243.jpg', 'https://www.iwata-airbrush.com/hp-m1.html', 'Iwata Revolution HP-M1 Gravity Feed Single Action Airbrush'),
    ('iwata-revolution-hp-m2-gravity-feed-single-action-airbrush', 'IWA-030', 'Iwata Revolution HP-M2 Gravity Feed Single Action Airbrush', decimal.Decimal('191'), 'https://www.iwata-airbrush.com/mm5/graphics/00000001/R1060_HP-M2-A1_300x261.jpg', 'https://www.iwata-airbrush.com/revolution-mini-hp-m2.html', 'Iwata Revolution HP-M2 Gravity Feed Single Action Airbrush'),
    ('iwata-revolution-hp-bcr-siphon-feed-dual-action-airbrush', 'IWA-031', 'Iwata Revolution HP-BCR Siphon Feed Dual Action Airbrush', decimal.Decimal('107'), 'https://www.iwata-airbrush.com/mm5/graphics/00000001/R2000_HP-BCR-A1_300x225.jpg', 'https://www.iwata-airbrush.com/revolution-2000-bcr.html', 'Iwata Revolution HP-BCR Siphon Feed Dual Action Airbrush'),
    ('iwata-revolution-hp-bcr-siphon-feed-dual-action-airbrush-with-iwata-airbrush-hose', 'IWA-032', 'Iwata Revolution HP-BCR Siphon Feed Dual Action Airbrush with Iwata Airbrush Hose', decimal.Decimal('122'), 'https://www.iwata-airbrush.com/mm5/graphics/00000001/R2001_HP-BCR-A1_300x255.jpg', 'https://www.iwata-airbrush.com/revolution-bcr-set-whose.html', 'Iwata Revolution HP-BCR Siphon Feed Dual Action Airbrush with Iwata Airbrush Hose'),
    ('iwata-revolution-hp-br-gravity-feed-dual-action-airbrush', 'IWA-033', 'Iwata Revolution HP-BR Gravity Feed Dual Action Airbrush', decimal.Decimal('122'), 'https://www.iwata-airbrush.com/mm5/graphics/00000001/R2500_HP-BR-A1_300x116.jpg', 'https://www.iwata-airbrush.com/revolution-br.html', 'Iwata Revolution HP-BR Gravity Feed Dual Action Airbrush'),
    ('iwata-revolution-hp-cr-gravity-feed-dual-action-airbrush', 'IWA-034', 'Iwata Revolution HP-CR Gravity Feed Dual Action Airbrush', decimal.Decimal('110'), 'https://www.iwata-airbrush.com/mm5/graphics/00000001/R4500_HP-CR-A1_300x139.jpg', 'https://www.iwata-airbrush.com/revolution-4500-cr.html', 'Iwata Revolution HP-CR Gravity Feed Dual Action Airbrush'),
    ('iwata-revolution-hp-tr1-side-feed-dual-action-trigger-airbrush', 'IWA-035', 'Iwata Revolution HP-TR1 Side Feed Dual Action Trigger Airbrush', decimal.Decimal('264'), 'https://www.iwata-airbrush.com/mm5/graphics/00000001/R5000_HP-TR1-A1_300x209.jpg', 'https://www.iwata-airbrush.com/revolution-trigger-brush.html', 'Iwata Revolution HP-TR1 Side Feed Dual Action Trigger Airbrush'),
    ('iwata-revolution-hp-tr2-side-feed-dual-action-trigger-airbrush', 'IWA-036', 'Iwata Revolution HP-TR2 Side Feed Dual Action Trigger Airbrush', decimal.Decimal('264'), 'https://www.iwata-airbrush.com/mm5/graphics/00000001/R5500_HP-TR2-A1_300x234.jpg', 'https://www.iwata-airbrush.com/revolution-trigger-brush-ii.html', 'Iwata Revolution HP-TR2 Side Feed Dual Action Trigger Airbrush'),
]


class Command(BaseCommand):
    """Populate the Iwata airbrush product line (idempotent)."""

    help = 'Populates Iwata airbrush products (IWA-001 to IWA-036).'

    def handle(self, *args, **options):
        category, _ = Category.objects.get_or_create(
            slug='paint-supplies',
            defaults={'name': 'Paint & Supplies'},
        )

        iwata_retailer, _ = Retailer.objects.get_or_create(
            slug='iwata-airbrush',
            defaults={
                'name': 'Iwata Airbrush',
                'website': 'https://www.iwata-airbrush.com',
                'country': 'US',
                'is_active': True,
                'is_uk': False,
            },
        )

        iwata_faction, _ = Faction.objects.get_or_create(
            slug='iwata',
            defaults={'name': 'Iwata', 'category': category},
        )

        products_created = 0
        products_updated = 0
        iwata_prices_created = 0
        iwata_prices_updated = 0

        for slug, gw_sku, name, msrp, image_url, product_url, ebay_search_name in PRODUCTS:
            product, created = Product.objects.update_or_create(
                slug=slug,
                defaults={
                    'gw_sku': gw_sku,
                    'name': name,
                    'category': category,
                    'faction': iwata_faction,
                    'msrp': msrp,
                    'image_url': image_url,
                    'gw_url': '',
                    'ebay_search_name': ebay_search_name,
                    'batch_tag': 'iwata',
                    'is_active': True,
                },
            )
            if created:
                products_created += 1
            else:
                products_updated += 1

            _, iwata_price_created = CurrentPrice.objects.update_or_create(
                product=product,
                retailer=iwata_retailer,
                defaults={
                    'price': msrp,
                    'url': product_url,
                    'in_stock': True,
                    'not_available': False,
                },
            )
            if iwata_price_created:
                iwata_prices_created += 1
            else:
                iwata_prices_updated += 1

        self.stdout.write(self.style.SUCCESS(
            f'Products: {products_created} created, {products_updated} updated.'
        ))
        self.stdout.write(self.style.SUCCESS(
            f'Iwata prices: {iwata_prices_created} created, {iwata_prices_updated} updated.'
        ))
