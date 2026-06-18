"""
Management command: populate_idoneth_deepkin_products

Creates / updates all Idoneth Deepkin product entries for ThriftHammer,
seeds GW CurrentPrice records at MSRP, and creates the Idoneth Deepkin faction
if it does not already exist.

Covers 21 products (IDK-001 to IDK-021) from the
AOS Idoneth Deepkin - GW, NK, MM.xlsx (2026-06-17).

Category: Age of Sigmar
Faction:  Idoneth Deepkin (get_or_create -- safe whether pre-existing or new)

Dual-kit products (same physical box, multiple build options):
  - IDK-003 Akhelian Ishlaen Guard / IDK-005 Akhelian Morrsarr Guard
    (Akhelian Guard kit -- NK and MM listings cover both builds)
  - IDK-008 Akhelian King / IDK-010 Volturnos, High King of the Deep
    (same kit -- NK listing covers both builds; no MM for either)
  - IDK-011 Eidolon of Mathlann - Aspect of the Sea /
    IDK-015 Eidolon of Mathlann - Aspect of the Storm
    (same kit -- NK and MM listings cover both builds)

No NK entries for: IDK-001, IDK-016, IDK-017, IDK-018, IDK-019.
No MM entries for: IDK-004, IDK-008, IDK-010, IDK-012, IDK-013, IDK-014,
                   IDK-020, IDK-021.

Images are baked in as one-off GW CDN URLs -- never auto-refreshed.

Safe to run repeatedly (idempotent via update_or_create keyed on slug).

Usage:
    python manage.py populate_idoneth_deepkin_products
"""

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Category, Faction, Product, Retailer

_IMG = 'https://www.warhammer.com/app/resources/catalog/product/920x950/{filename}'
_GW = 'https://www.warhammer.com/en-US/shop/'

# -- Product definitions -------------------------------------------------------
# (slug, gw_sku, name, msrp, image_filename, gw_url, ebay_search_name)
#
# msrp is USD price from GW en-US storefront as of 2026-06-17.
# ebay_search_name is set directly -- single source of truth for eBay search.
PRODUCTS = [

    # -- Spearhead -------------------------------------------------------------
    (
        'spearhead-idoneth-deepkin-akhelian-tide-guard',
        'IDK-001',
        'Spearhead: Idoneth Deepkin – Akhelian Tide Guard',
        150.00,
        '99120219024_IDAkhelianTideGuardSpearhead01.jpg',
        f'{_GW}spearhead-idoneth-deepkin-akhelian-tide-guard-2025',
        'Spearhead Idoneth Deepkin Akhelian Tide Guard Age of Sigmar',
    ),

    # -- Heroes ----------------------------------------------------------------
    (
        'akhelian-thrallmaster',
        'IDK-002',
        'Akhelian Thrallmaster',
        35.00,
        '99070219007_IDAhkelianThrallmasterLead.jpg',
        f'{_GW}idoneth-deepkin-akhelian-thrallmaster-2022',
        'Akhelian Thrallmaster Age of Sigmar',
    ),
    (
        'isharann-tidecaster',
        'IDK-007',
        'Isharann Tidecaster',
        35.00,
        '99070219006_IsharannTidecaster01.jpg',
        f'{_GW}Idoneth-Deepkin-Isharann-Tidecaster-2018',
        'Isharann Tidecaster Age of Sigmar',
    ),
    # ⚠ Dual kit: Akhelian King and Volturnos share the same physical kit.
    #   NK listing covers both builds under "Volturnos, High King of the Deep".
    (
        'akhelian-king',
        'IDK-008',
        'Akhelian King',
        60.00,
        '99120219004_Volturnos02.jpg',
        f'{_GW}Akhelian-King-2018',
        'Akhelian King Age of Sigmar',
    ),
    (
        'volturnos-high-king-of-the-deep',
        'IDK-010',
        'Volturnos, High King of the Deep',
        60.00,
        '99120219004_Volturnos01.jpg',
        f'{_GW}Volturnos-High-King-Of-The-Deep-2018',
        'Volturnos, High King of the Deep Age of Sigmar',
    ),
    (
        'lotann-warden-of-the-soul-ledgers',
        'IDK-014',
        'Lotann, Warden of the Soul Ledgers',
        39.00,
        '99120219006_IdonethLotann01.jpg',
        f'{_GW}Lotann-Warden-Of-The-Soul-Ledgers-2018',
        'Lotann, Warden of the Soul Ledgers Age of Sigmar',
    ),
    (
        'mathaela-oracle-of-the-abyss',
        'IDK-017',
        'Mathaela, Oracle of the Abyss',
        43.50,
        '99120219033_IDMathaelaOracleOfTheAbyss01.jpg',
        f'{_GW}idoneth-deepkin-mathaela-oracle-of-the-abyss-2025',
        'Mathaela, Oracle of the Abyss Age of Sigmar',
    ),
    (
        'isharann-soulrender',
        'IDK-020',
        'Isharann Soulrender',
        35.00,
        '99070219004_IsharannSoulrender01.jpg',
        f'{_GW}Idoneth-Deepkin-Isharann-Soulrender-2018',
        'Isharann Soulrender Age of Sigmar',
    ),
    (
        'isharann-soulscryer',
        'IDK-021',
        'Isharann Soulscryer',
        35.00,
        '99120219035_IDIsharannSoulscryer01.jpg',
        f'{_GW}idoneth-deepkin-isharann-soulscryer-2025',
        'Isharann Soulscryer Age of Sigmar',
    ),

    # -- Units -----------------------------------------------------------------
    # ⚠ Dual kit: Akhelian Ishlaen Guard and Akhelian Morrsarr Guard share the
    #   same Akhelian Guard kit. NK and MM listings cover both builds.
    (
        'akhelian-ishlaen-guard',
        'IDK-003',
        'Akhelian Ishlaen Guard',
        60.00,
        '99120219008_IdonethIshlaenGuard01.jpg',
        f'{_GW}Idoneth-Deepkin-Akhelian-Ishlaen-Guard-2018',
        'Akhelian Morrsarr Guard Age of Sigmar',
    ),
    (
        'akhelian-morrsarr-guard',
        'IDK-005',
        'Akhelian Morrsarr Guard',
        60.00,
        '99120219008_IdonethMorrsarrGuard01.jpg',
        f'{_GW}Idoneth-Deepkin-Akhelian-Guard-2018',
        'Akhelian Morrsarr Guard Age of Sigmar',
    ),
    (
        'akhelian-allopex',
        'IDK-006',
        'Akhelian Allopex',
        60.00,
        '99120219007_IdonethAllopex01.jpg',
        f'{_GW}Idoneth-Deepkin-Akhelian-Allopex-2018',
        'Akhelian Allopex Age of Sigmar',
    ),
    (
        'namarti-reavers',
        'IDK-009',
        'Namarti Reavers',
        60.00,
        '99120219010_NamartiReavers01.jpg',
        f'{_GW}Namarti-Reavers-2018',
        'Namarti Reavers Age of Sigmar',
    ),
    (
        'namarti-thralls',
        'IDK-013',
        'Namarti Thralls',
        60.00,
        '99120219011_NamartiThralls01.jpg',
        f'{_GW}Namarti-Thralls-2018',
        'Namarti Thralls Age of Sigmar',
    ),

    # -- Large Kits / Monsters -------------------------------------------------
    (
        'akhelian-leviadon',
        'IDK-004',
        'Akhelian Leviadon',
        150.00,
        '99120219009_AkhelianLeviadon01.jpg',
        f'{_GW}Idoneth-Deepkin-Akhelian-Leviadon-2018',
        'Akhelian Leviadon Age of Sigmar',
    ),
    # ⚠ Dual kit: Eidolon of Mathlann - Aspect of the Sea and Aspect of the Storm
    #   share the same kit. NK and MM listings cover both builds.
    (
        'eidolon-of-mathlann-aspect-of-the-sea',
        'IDK-011',
        'Eidolon of Mathlann – Aspect of the Sea',
        150.00,
        '99120219005_EidolonAspectSea01.jpg',
        f'{_GW}Eidolon-Aspect-of-the-sea-2018',
        'Eidolon of Mathlann Age of Sigmar',
    ),
    (
        'eidolon-of-mathlann-aspect-of-the-storm',
        'IDK-015',
        'Eidolon of Mathlann – Aspect of the Storm',
        150.00,
        '99120219005_EidolonAspectStorm01.jpg',
        f'{_GW}Eidolon-Of-Mathlann-2018',
        'Eidolon of Mathlann Age of Sigmar',
    ),

    # -- Terrain / Scenery -----------------------------------------------------
    (
        'gloomtide-shipwreck',
        'IDK-012',
        'Gloomtide Shipwreck',
        65.00,
        '99120299050_GloomtideShipwreck01.jpg',
        f'{_GW}Etheric-Vortex-Gloomtide-Shipwreck-2018',
        'Gloomtide Shipwreck Idoneth Deepkin Warhammer',
    ),
    (
        'ikon-of-the-sea-storm',
        'IDK-018',
        'Ikon of the Sea/Storm',
        40.00,
        '99120219025_IDIkonOfTheSea01.jpg',
        f'{_GW}idoneth-deepkin-ikon-of-the-sea-2025',
        'Ikon of the Sea/Storm Age of Sigmar',
    ),

    # -- Endless Spells / Manifestations ---------------------------------------
    (
        'idoneth-deepkin-manifestations',
        'IDK-016',
        'Idoneth Deepkin Manifestations',
        60.00,
        '99120219034_IDManifestationsSceneryKit01.jpg',
        f'{_GW}idoneth-deepkin-manifestations-2025',
        'Idoneth Deepkin Manifestations Age of Sigmar',
    ),

    # -- Battletome ------------------------------------------------------------
    (
        'order-battletome-idoneth-deepkin',
        'IDK-019',
        'Order Battletome: Idoneth Deepkin',
        60.00,
        '60030219003_EngIDBattletome01.jpg',
        f'{_GW}battletome-idoneth-deepkin-2025-eng',
        'Order Battletome: Idoneth Deepkin Age of Sigmar',
    ),
]


class Command(BaseCommand):
    """Populate Idoneth Deepkin products (IDK-001 to IDK-021)."""

    help = (
        'Creates / updates 21 Idoneth Deepkin products and seeds GW prices at MSRP. '
        'Creates Idoneth Deepkin faction if it does not exist. Idempotent.'
    )

    def handle(self, *args, **options):
        """Run the command."""
        try:
            category_aos = Category.objects.get(slug='age-of-sigmar')
        except Category.DoesNotExist:
            self.stderr.write(self.style.ERROR(
                'Age of Sigmar category not found -- run populate_products first.'
            ))
            return

        idk_faction, faction_created = Faction.objects.get_or_create(
            slug='idoneth-deepkin',
            defaults={'name': 'Idoneth Deepkin', 'category': category_aos},
        )
        if faction_created:
            self.stdout.write('  Created Idoneth Deepkin faction.')

        gw = Retailer.objects.filter(name='Games Workshop').first()

        products_created = 0
        products_updated = 0
        prices_created = 0
        prices_updated = 0

        for (slug, gw_sku, name, msrp, image_filename, gw_url, ebay_search_name) in PRODUCTS:
            image_url = _IMG.format(filename=image_filename)

            product, created = Product.objects.update_or_create(
                slug=slug,
                defaults={
                    'name': name,
                    'gw_sku': gw_sku,
                    'faction': idk_faction,
                    'category': category_aos,
                    'msrp': msrp,
                    'image_url': image_url,
                    'gw_url': gw_url,
                    'ebay_search_name': ebay_search_name,
                    'batch_tag': 'idoneth-deepkin',
                    'is_active': True,
                },
            )
            if created:
                products_created += 1
                self.stdout.write(f'  Created: {name} ({gw_sku})')
            else:
                products_updated += 1
                self.stdout.write(f'  Updated: {name} ({gw_sku})')

            if gw:
                _, price_created = CurrentPrice.objects.update_or_create(
                    product=product,
                    retailer=gw,
                    defaults={
                        'price': msrp,
                        'url': gw_url,
                        'in_stock': True,
                        'not_available': False,
                    },
                )
                if price_created:
                    prices_created += 1
                else:
                    prices_updated += 1

        self.stdout.write(self.style.SUCCESS(
            f'populate_idoneth_deepkin_products complete. '
            f'Products: {products_created} created, {products_updated} updated. '
            f'GW prices: {prices_created} created, {prices_updated} updated.'
        ))
