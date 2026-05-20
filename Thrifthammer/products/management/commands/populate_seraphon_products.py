"""
Management command: populate_seraphon_products

Creates / updates all Seraphon product entries for ThriftHammer,
seeds GW CurrentPrice records at MSRP.

Covers 28 products from the AOS Seraphon - GW, NK, MM, AMAZON.xlsx (2026-05-19).

Category: Age of Sigmar
Faction:  Seraphon  (created here via get_or_create — not in populate_products.py)

Triple-kit / shared-listing products (same physical box):
  - Engine of the Gods / Stegadon / Stegadon Chief  (SR-003 / SR-025 / SR-026)
    share one Amazon ASIN and one NK URL; no MM listing

Dual-kit products:
  - Kroxigor / Kroxigor Warspawned        (SR-005 / SR-006)  share Amazon ASIN + MM URL + NK URL
  - Raptadon Chargers / Raptadon Hunters  (SR-008 / SR-009)  share Amazon ASIN + MM URL + NK URL
  - Ripperdactyl Riders / Terradon Riders (SR-011 / SR-027)  share Amazon ASIN; no NK for SR-011

Quad NK URL (same webstore-edition listing):
  - SR-014 Saurus Oldblood
  - SR-015 Saurus Oldblood on Carnosaur
  - SR-017 Saurus Scar-Veteran on Carnosaur
  - SR-019 Skink Oracle on Troglodon

Special notes:
  - SR-002 (Bastiladon): spreadsheet MM column contained the Aggradon Lancers URL
    (data entry error); no MM URL seeded
  - SR-011 (Ripperdactyl Riders): no NK listing in spreadsheet
  - SR-013 (Saurus Guard): no Amazon or MM listing
  - SR-015 / SR-017 / SR-019: no Amazon listing

No UnitType entries — Seraphon is an AoS faction not wired to the army calculator.

Images are baked in as one-off GW CDN URLs -- never auto-refreshed.

Safe to run repeatedly (idempotent via update_or_create keyed on slug).

Usage:
    python manage.py populate_seraphon_products
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

    # ── Infantry ──────────────────────────────────────────────────────────────
    (
        'seraphon-aggradon-lancers',
        'SR-001',
        'Seraphon Aggradon Lancers',
        65.00,
        '99120208034_AggradonLancers2.jpg',
        'https://www.warhammer.com/en-US/shop/seraphon-aggradon-lancers-2023',
        '',
    ),
    (
        'seraphon-bastiladon',
        'SR-002',
        'Seraphon Bastiladon',
        65.00,
        '99120208015_SeraphonBastiladon01.jpg',
        'https://www.warhammer.com/en-US/shop/Seraphon-Bastiladon',
        '',
    ),

    # ── Monsters / War Engines ────────────────────────────────────────────────
    # ⚠ Triple kit: Engine of the Gods / Stegadon / Stegadon Chief share one Amazon ASIN + NK URL
    (
        'seraphon-engine-of-the-gods',
        'SR-003',
        'Seraphon Engine of the Gods',
        73.50,
        '99120208020_SeraphonStegadonEngineofGods01.jpg',
        'https://www.warhammer.com/en-US/shop/Seraphon-Engine-of-the-Gods',
        '',
    ),

    # ── Warband ───────────────────────────────────────────────────────────────
    (
        'seraphon-hunters-of-huanchi',
        'SR-004',
        'Seraphon Hunters of Huanchi',
        60.00,
        '60010299038_WCSunderedFateHuntersOfHuanchiLead.jpg',
        'https://www.warhammer.com/en-US/shop/seraphon-hunters-of-huanchi-2025',
        '',
    ),

    # ── Infantry ──────────────────────────────────────────────────────────────
    # ⚠ Dual kit: Kroxigor / Kroxigor Warspawned share one Amazon ASIN + MM URL + NK URL
    (
        'seraphon-kroxigor',
        'SR-005',
        'Seraphon Kroxigor',
        65.00,
        '99120208032_SERKroxigor01.jpg',
        'https://www.warhammer.com/en-US/shop/seraphon-kroxigor-2023',
        '',
    ),
    (
        'seraphon-kroxigor-warspawned',
        'SR-006',
        'Seraphon Kroxigor Warspawned',
        65.00,
        '99120208032_SERKroxigor01alt.jpg',
        'https://www.warhammer.com/en-US/shop/seraphon-kroxigor-warspawned-2023',
        '',
    ),

    # ── Characters ────────────────────────────────────────────────────────────
    (
        'seraphon-lord-kroak',
        'SR-007',
        'Seraphon Lord Kroak',
        145.00,
        '99120208027_LordKroakLead.jpg',
        'https://www.warhammer.com/en-US/shop/Lord-Kroak-2021',
        '',
    ),

    # ── Cavalry ───────────────────────────────────────────────────────────────
    # ⚠ Dual kit: Raptadon Chargers / Raptadon Hunters share one Amazon ASIN + MM URL + NK URL
    (
        'seraphon-raptadon-chargers',
        'SR-008',
        'Seraphon Raptadon Chargers',
        69.00,
        '99120208038_RaptadonChargers2.jpg',
        'https://www.warhammer.com/en-US/shop/seraphon-raptadon-chargers-2023',
        '',
    ),
    (
        'seraphon-raptadon-hunters',
        'SR-009',
        'Seraphon Raptadon Hunters',
        69.00,
        '60010208001_EngSERArmySet03.jpg',
        'https://www.warhammer.com/en-US/shop/seraphon-raptadon-hunters-2023',
        '',
    ),

    # ── Terrain ───────────────────────────────────────────────────────────────
    (
        'seraphon-realmshaper-engine',
        'SR-010',
        'Seraphon Realmshaper Engine',
        69.00,
        '99120208026_SerRealmshaperEngine01.jpg',
        'https://www.warhammer.com/en-US/shop/Seraphon-Realmshaper-Engine-2020',
        '',
    ),

    # ── Flying Cavalry ────────────────────────────────────────────────────────
    # ⚠ Dual kit ASIN with SR-027 Terradon Riders; no NK listing for this product
    (
        'seraphon-ripperdactyl-riders',
        'SR-011',
        'Seraphon Ripperdactyl Riders',
        65.00,
        '99120208021_RipperdactylRiders01.jpg',
        'https://www.warhammer.com/en-US/shop/Seraphon-Ripperdactyl-Riders',
        '',
    ),

    # ── Characters ────────────────────────────────────────────────────────────
    (
        'seraphon-saurus-astrolith-bearer',
        'SR-012',
        'Seraphon Saurus Astrolith Bearer',
        47.00,
        '99120208035_SaurusAstrolithBearer1.jpg',
        'https://www.warhammer.com/en-US/shop/seraphon-saurus-astrolith-bearer-2023',
        '',
    ),

    # ── Infantry ──────────────────────────────────────────────────────────────
    (
        'seraphon-saurus-guard',
        'SR-013',
        'Seraphon Saurus Guard',
        65.00,
        '99120208016_SeraphonSaurusGuard01.jpg',
        'https://www.warhammer.com/en-US/shop/Seraphon-Saurus-Guard',
        '',
    ),

    # ── Characters ────────────────────────────────────────────────────────────
    # ⚠ Quad NK URL: SR-014 / SR-015 / SR-017 / SR-019 share one NK webstore-edition listing
    (
        'seraphon-saurus-oldblood',
        'SR-014',
        'Seraphon Saurus Oldblood',
        20.00,
        '99070208001_SaurusOldbloodNEW01.jpg',
        'https://www.warhammer.com/en-US/shop/Lizardmen-Saurus-Oldblood',
        '',
    ),
    (
        'seraphon-saurus-oldblood-on-carnosaur',
        'SR-015',
        'Seraphon Saurus Oldblood on Carnosaur',
        96.00,
        '99120208017_OldBloodOnCarnosaur02.jpg',
        'https://www.warhammer.com/en-US/shop/Seraphon-Saurus-Oldblood-on-Carnosaur',
        '',
    ),

    # ── Characters ────────────────────────────────────────────────────────────
    (
        'seraphon-saurus-scar-veteran-on-aggradon',
        'SR-016',
        'Seraphon Saurus Scar-Veteran on Aggradon',
        60.00,
        '99120208031_SERSaurusScarVeteranOnAggradon01.jpg',
        'https://www.warhammer.com/en-US/shop/seraphon-saurus-scar-veteran-on-aggradon-2023',
        '',
    ),
    (
        'seraphon-saurus-scar-veteran-on-carnosaur',
        'SR-017',
        'Seraphon Saurus Scar-Veteran on Carnosaur',
        96.00,
        '99120208017_OldBloodOnCarnosaur01.jpg',
        'https://www.warhammer.com/en-US/shop/Seraphon-Saurus-Scar-Veteran-on-Carnosaur',
        '',
    ),

    # ── Infantry ──────────────────────────────────────────────────────────────
    (
        'seraphon-saurus-warriors',
        'SR-018',
        'Seraphon Saurus Warriors',
        65.00,
        '60010208001_EngSERArmySet02.jpg',
        'https://www.warhammer.com/en-US/shop/seraphon-saurus-warriors-2023',
        '',
    ),

    # ── Characters ────────────────────────────────────────────────────────────
    # ⚠ Quad NK URL: SR-019 shares NK listing with SR-014 / SR-015 / SR-017
    (
        'seraphon-skink-oracle-on-troglodon',
        'SR-019',
        'Seraphon Skink Oracle on Troglodon',
        96.00,
        '99120208017_Troglodon01.jpg',
        'https://www.warhammer.com/en-US/shop/Seraphon-Troglodons',
        '',
    ),
    (
        'seraphon-skink-starpriest',
        'SR-020',
        'Seraphon Skink Starpriest',
        35.00,
        '99070208003_SkinkStarpriest01.jpg',
        'https://www.warhammer.com/en-US/shop/Skink-Starpriest',
        '',
    ),
    (
        'seraphon-skink-starseer',
        'SR-021',
        'Seraphon Skink Starseer',
        60.00,
        '99120208030_SERSkinkStarseer01.jpg',
        'https://www.warhammer.com/en-US/shop/seraphon-skink-starseer-2023',
        '',
    ),

    # ── Infantry ──────────────────────────────────────────────────────────────
    (
        'seraphon-skinks',
        'SR-022',
        'Seraphon Skinks',
        48.00,
        '99120208014_SeraphonSkinks01.jpg',
        'https://www.warhammer.com/en-US/shop/Seraphon-Skinks',
        '',
    ),

    # ── Characters ────────────────────────────────────────────────────────────
    (
        'seraphon-slann-starmaster',
        'SR-023',
        'Seraphon Slann Starmaster',
        94.00,
        '99120208037_Starmaster1.jpg',
        'https://www.warhammer.com/en-US/shop/seraphon-slann-starmaster-2023',
        '',
    ),

    # ── Monsters ──────────────────────────────────────────────────────────────
    (
        'seraphon-spawn-of-chotec',
        'SR-024',
        'Seraphon Spawn of Chotec',
        60.00,
        '99120208033_SERSpawnOfChotec01.jpg',
        'https://www.warhammer.com/en-US/shop/seraphon-spawn-of-chotec-2023',
        '',
    ),

    # ── Monsters / War Engines ────────────────────────────────────────────────
    # ⚠ Triple kit: Stegadon / Stegadon Chief share Amazon ASIN + NK URL with SR-003
    (
        'seraphon-stegadon',
        'SR-025',
        'Seraphon Stegadon',
        73.50,
        '99120208020_SeraphonStegadon01.jpg',
        'https://www.warhammer.com/en-US/shop/Seraphon-Stegadon',
        '',
    ),
    (
        'seraphon-stegadon-chief',
        'SR-026',
        'Seraphon Stegadon Chief',
        73.50,
        '99120208020_StegadonChiefDuplicatePage1.jpg',
        'https://www.warhammer.com/en-US/shop/stegadon-chief-2023',
        '',
    ),

    # ── Flying Cavalry ────────────────────────────────────────────────────────
    # ⚠ Dual kit ASIN with SR-011 Ripperdactyl Riders
    (
        'seraphon-terradon-riders',
        'SR-027',
        'Seraphon Terradon Riders',
        65.00,
        '99120208021_TerradonRiders01.jpg',
        'https://www.warhammer.com/en-US/shop/Seraphon-Terradon-Riders',
        '',
    ),

    # ── Spearhead ─────────────────────────────────────────────────────────────
    (
        'spearhead-seraphon-sunblooded-prowlers',
        'SR-028',
        'Spearhead: Seraphon – Sunblooded Prowlers',
        150.00,
        '99120208046_SeraphonSunbloodedProwlersSpearhead1.jpg',
        'https://www.warhammer.com/en-US/shop/spearhead-seraphon-sunblooded-prowlers-2025',
        '',
    ),
]


class Command(BaseCommand):
    """Populate Seraphon products (SR-001 to SR-028)."""

    help = (
        'Creates / updates 28 Seraphon products and seeds GW prices at MSRP. '
        'Creates the Seraphon faction if it does not exist. '
        'Idempotent.'
    )

    def handle(self, *args, **options):
        """Run the command."""
        try:
            category_aos = Category.objects.get(slug='age-of-sigmar')
        except Category.DoesNotExist:
            self.stderr.write(self.style.ERROR(
                'Age of Sigmar category not found — run populate_products first.'
            ))
            return

        seraphon_faction, faction_created = Faction.objects.get_or_create(
            slug='seraphon',
            defaults={
                'name': 'Seraphon',
                'category': category_aos,
            },
        )
        if faction_created:
            self.stdout.write(self.style.SUCCESS('  Created faction: Seraphon'))
        else:
            self.stdout.write(f'  Faction exists: Seraphon')

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
                    'category': category_aos,
                    'faction': seraphon_faction,
                    'is_active': True,
                    'batch_tag': 'seraphon',
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
            f'\npopulate_seraphon_products complete. '
            f'Products: {product_created} created, {product_updated} updated. '
            f'GW prices: {price_created} created, {price_updated} updated.'
        ))
