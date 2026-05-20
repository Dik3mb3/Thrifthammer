"""
Management command: populate_gsc_products

Creates / updates all Genestealer Cults product entries for ThriftHammer,
seeds GW CurrentPrice records at MSRP.

Covers 18 products from the GSC - GW, NK, MM, AMAZON.xlsx spreadsheet (2026-05-19).

Category: Warhammer 40,000
Faction:  Genestealer Cults

Dual-kit / shared-listing products (same physical box):
  - Goliath Rockgrinder / Goliath Truck  (GC-010 / GC-011)
    share one Amazon ASIN, one MM URL, one NK listing

Special notes:
  - GC-012 (Acolyte Iconward): no MM listing
  - GC-013 (Hybrid Metamorphs): MM column in source spreadsheet contained a GW URL
    (data entry error); no MM URL seeded

Images are baked in as one-off GW CDN URLs -- never auto-refreshed.

Safe to run repeatedly (idempotent via update_or_create keyed on slug).

Usage:
    python manage.py populate_gsc_products
"""

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Category, Faction, Product, Retailer

_IMG = 'https://www.warhammer.com/app/resources/catalog/product/920x950/{filename}'

# ── Product definitions ───────────────────────────────────────────────────────
# (slug, gw_sku, name, msrp, image_filename, gw_url, ebay_search_name)
#
# msrp is USD price from GW en-US storefront as of 2026-05-19.
# ebay_search_name is blank unless the default name gives poor eBay results.
PRODUCTS = [

    # ── Codex ─────────────────────────────────────────────────────────────────
    (
        'codex-genestealer-cults',
        'GC-001',
        'Codex: Genestealer Cults',
        60.00,
        '60030117005_ENGGSCCodex1.jpg',
        'https://www.warhammer.com/en-US/shop/codex-genestealer-cults-2024-eng',
        'Codex Genestealer Cults',
    ),

    # ── Characters ────────────────────────────────────────────────────────────
    (
        'genestealer-cults-reductus-saboteur',
        'GC-002',
        'Genestealer Cults Reductus Saboteur',
        39.00,
        '99070117011_GCReductusSaboteurLead.jpg',
        'https://www.warhammer.com/en-US/shop/genestealer-cults-reductus-saboteur-2022',
        '',
    ),
    (
        'genestealer-cults-kelermorph',
        'GC-003',
        'Genestealer Cults Kelermorph',
        35.00,
        '99070117010_Kelemorph01.jpg',
        'https://www.warhammer.com/en-US/shop/Genestealer-Cults-Kelermorph-2020',
        '',
    ),
    (
        'genestealer-cults-abominant',
        'GC-004',
        'Genestealer Cults Abominant',
        35.00,
        '99070117009_GSCAbominant01.jpg',
        'https://www.warhammer.com/en-US/shop/Genestealer-Cults-Abominant-2019',
        '',
    ),
    (
        'genestealer-cults-biophagus',
        'GC-005',
        'Genestealer Cults Biophagus',
        35.00,
        '99070117003_GSCBiophagus01.jpg',
        'https://www.warhammer.com/en-US/shop/Genestealer-Cults-Biophagus-2019',
        '',
    ),
    (
        'genestealer-cults-nexos',
        'GC-007',
        'Genestealer Cults Nexos',
        35.00,
        '99070117008_GSCNexos01.jpg',
        'https://www.warhammer.com/en-US/shop/Genestealer-Cults-Nexos-2019',
        '',
    ),
    (
        'genestealer-cults-locus',
        'GC-008',
        'Genestealer Cults Locus',
        35.00,
        '99070117007_GCSLocus01.jpg',
        'https://www.warhammer.com/en-US/shop/Genestealer-Cults-Locus-2019',
        '',
    ),
    (
        'genestealer-cults-sanctus',
        'GC-009',
        'Genestealer Cults Sanctus',
        35.00,
        '99070117006_GSCSanctus01.jpg',
        'https://www.warhammer.com/en-US/shop/Genestealer-Cults-Sanctus-2019',
        '',
    ),
    (
        'genestealer-cults-acolyte-iconward',
        'GC-012',
        'Genestealer Cults Acolyte Iconward',
        35.00,
        '99070117002_AcolyteIconward01.jpg',
        'https://www.warhammer.com/en-US/shop/acolyte-iconward-2016',
        '',
    ),
    (
        'genestealer-cults-benefictus',
        'GC-014',
        'Genestealer Cults Benefictus',
        35.00,
        '99070117020_GSCBenefictus1.jpg',
        'https://www.warhammer.com/en-US/shop/genestealer-cults-benefictus-2024',
        '',
    ),
    (
        'genestealer-cults-jackal-alphus',
        'GC-017',
        'Genestealer Cults Jackal Alphus',
        48.00,
        '99120117013_GSCJackalAlphus01.jpg',
        'https://www.warhammer.com/en-US/shop/Genestealer-Cults-Jackal-Alphus-2019',
        '',
    ),
    (
        'genestealer-cults-clamavus',
        'GC-018',
        'Genestealer Cults Clamavus',
        35.00,
        '99070117004_GSCClamavus01.jpg',
        'https://www.warhammer.com/en-US/shop/Genestealer-Cults-Clamavus-2019',
        '',
    ),

    # ── Infantry ──────────────────────────────────────────────────────────────
    (
        'genestealer-cults-atalan-jackals',
        'GC-006',
        'Genestealer Cults Atalan Jackals',
        65.00,
        '99120117014_GSCAtalanJackals01.jpg',
        'https://www.warhammer.com/en-US/shop/Genestealer-Cults-Atalan-Jackals-2019',
        '',
    ),
    (
        'genestealer-cults-hybrid-metamorphs',
        'GC-013',
        'Genestealer Cults Hybrid Metamorphs',
        48.00,
        '99120117003_GenestealerMetamorphs01.jpg',
        'https://www.warhammer.com/en-US/shop/hybrid-metamorphs-2016',
        '',
    ),
    (
        'genestealer-cults-genestealers',
        'GC-015',
        'Genestealer Cults Genestealers',
        60.00,
        '99120106068_Genestealers2.jpg',
        'https://www.warhammer.com/en-US/shop/tyranids-genestealers-2023',
        'Genestealers',  # eBay sellers list as "Tyranids Genestealers" not "Genestealer Cults Genestealers"
    ),

    # ── Vehicles ──────────────────────────────────────────────────────────────
    # ⚠ Dual kit: Goliath Rockgrinder / Goliath Truck share one Amazon ASIN and MM URL
    (
        'genestealer-cults-goliath-rockgrinder',
        'GC-010',
        'Genestealer Cults Goliath Rockgrinder',
        69.00,
        '99120117002_Rockgrinder01.jpg',
        'https://www.warhammer.com/en-US/shop/goliath-rockgrinder-2016',
        '',
    ),
    (
        'genestealer-cults-goliath-truck',
        'GC-011',
        'Genestealer Cults Goliath Truck',
        69.00,
        '99120117002_Goliath01.jpg',
        'https://www.warhammer.com/en-US/shop/goliath-truck-2016',
        '',
    ),
    (
        'genestealer-cults-achilles-ridgerunner',
        'GC-016',
        'Genestealer Cults Achilles Ridgerunner',
        60.00,
        '99120117015_GSCAchilliesRidgerunner01.jpg',
        'https://www.warhammer.com/en-US/shop/Genestealer-Cults-Achilles-Ridgerunner-2019',
        '',
    ),
]


class Command(BaseCommand):
    """Populate Genestealer Cults products (GC-001 to GC-018)."""

    help = (
        'Creates / updates 18 Genestealer Cults products and seeds GW prices at MSRP. '
        'Idempotent.'
    )

    def handle(self, *args, **options):
        """Run the command."""
        try:
            category_40k = Category.objects.get(slug='warhammer-40000')
        except Category.DoesNotExist:
            self.stderr.write(self.style.ERROR(
                'Warhammer 40,000 category not found — run populate_products first.'
            ))
            return

        try:
            gsc_faction = Faction.objects.get(slug='genestealer-cults')
        except Faction.DoesNotExist:
            self.stderr.write(self.style.ERROR(
                'Genestealer Cults faction not found — run populate_products first.'
            ))
            return

        gw_retailer = Retailer.objects.filter(name='Games Workshop').first()
        if not gw_retailer:
            self.stdout.write(self.style.WARNING(
                'Games Workshop retailer not found — GW prices will not be seeded.'
            ))

        product_created = product_updated = price_created = price_updated = 0

        for (slug, gw_sku, name, msrp, img_filename, gw_url, ebay_name) in PRODUCTS:
            image_url = _IMG.format(filename=img_filename)

            product, created = Product.objects.update_or_create(
                slug=slug,
                defaults={
                    'name': name,
                    'gw_sku': gw_sku,
                    'msrp': msrp,
                    'image_url': image_url,
                    'gw_url': gw_url,
                    'ebay_search_name': ebay_name,
                    'category': category_40k,
                    'faction': gsc_faction,
                    'is_active': True,
                    'batch_tag': 'genestealer-cults',
                },
            )
            status = 'Created' if created else 'Updated'
            self.stdout.write(self.style.SUCCESS(f'  {status}: {name} ({gw_sku})'))
            if created:
                product_created += 1
            else:
                product_updated += 1

            # ── Seed GW CurrentPrice at MSRP ──────────────────────────────────
            if gw_retailer and gw_url:
                _, p_created = CurrentPrice.objects.update_or_create(
                    product=product,
                    retailer=gw_retailer,
                    defaults={
                        'price': msrp,
                        'url': gw_url,
                        'in_stock': True,
                        'not_available': False,
                    },
                )
                if p_created:
                    price_created += 1
                else:
                    price_updated += 1

        self.stdout.write(self.style.SUCCESS(
            f'\npopulate_gsc_products complete. '
            f'Products: {product_created} created, {product_updated} updated. '
            f'GW prices: {price_created} created, {price_updated} updated.'
        ))
