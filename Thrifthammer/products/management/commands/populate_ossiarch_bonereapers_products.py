"""
Management command: populate_ossiarch_bonereapers_products

Creates / updates all Ossiarch Bonereapers product entries for ThriftHammer,
seeds GW CurrentPrice records at MSRP, and uses the existing Ossiarch Bonereapers
faction (slug=ossiarch-bonereapers, already in DB).

Covers 20 products (OBR-001 to OBR-020) from the
AOS Bonereapers - GW, NK, MM.xlsx (2026-06-10).

Category: Age of Sigmar
Faction:  Ossiarch Bonereapers (existing -- get_or_create is safe/idempotent)

Dual-tag product (NOT created here -- handled by add_obr_secondary_faction):
  - Nagash, Supreme Lord of the Undead (SG-016) -- already in DB under
    Soulblight Gravelords; secondary_factions.add() surfaces it on OBR page.

Images are baked in as one-off GW CDN URLs -- never auto-refreshed.

Safe to run repeatedly (idempotent via update_or_create keyed on slug).

Usage:
    python manage.py populate_ossiarch_bonereapers_products
"""

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Category, Faction, Product, Retailer

_IMG = 'https://www.warhammer.com/app/resources/catalog/product/920x950/{filename}'
_GW = 'https://www.warhammer.com/en-US/shop/'

# -- Product definitions -------------------------------------------------------
# (slug, gw_sku, name, msrp, image_filename, gw_url, ebay_search_name)
#
# msrp is USD price from GW en-US storefront as of 2026-06-10.
# ebay_search_name is set directly -- single source of truth for eBay search.
PRODUCTS = [

    # -- Battleforces ----------------------------------------------------------
    (
        'battleforce-ossiarch-bonereapers-null-myriad-phalanx',
        'OBR-001',
        'Battleforce: Ossiarch Bonereapers - Null Myriad Phalanx',
        250.00,
        '99120207261_OssiarchBonereapersNullMyriadPhalanx01.jpg',
        f'{_GW}ossiarch-bonereapers-null-myriad-phalanx-2026',
        'Battleforce: Ossiarch Bonereapers - Null Myriad Phalanx',
    ),

    # -- Regiments of Renown ---------------------------------------------------
    (
        'regiment-of-renown-heralds-of-the-bone-tithe',
        'OBR-002',
        'Regiment of Renown: Heralds of the Bone-tithe',
        94.00,
        '99120207196_OssiarchBonereapersHeraldsOfTheBonetithe01.jpg',
        f'{_GW}ossiarch-bonereapers-heralds-of-the-bone-tithe-2026',
        'Regiment of Renown: Heralds of the Bone-tithe Ossiarch Bonereapers',
    ),

    # -- Heroes ----------------------------------------------------------------
    (
        'mortisan-ossifector',
        'OBR-003',
        'Mortisan Ossifector',
        35.00,
        '99070207016_OBMortisanOssifector01.jpg',
        f'{_GW}ossiarch-bonereapers-mortisan-ossifector-2023',
        'Mortisan Ossifector Ossiarch Bonereapers',
    ),
    (
        'mortisan-soulmason',
        'OBR-004',
        'Mortisan Soulmason',
        43.50,
        '99120207080_OBRMortisanSoulmason01.jpg',
        f'{_GW}Ossiarch-Bonereapers-Mortisan-Soulmason-2019',
        'Mortisan Soulmason Ossiarch Bonereapers',
    ),
    (
        'katakros-mortarch-of-the-necropolis',
        'OBR-006',
        'Katakros, Mortarch of the Necropolis',
        122.00,
        '99120207076_OBRKatakarosMortarch01.jpg',
        f'{_GW}Ossiarch-Bonereapers-Katakros-Mortarch-Of-The-Necropolis-2019',
        'Katakros, Mortarch of the Necropolis Ossiarch Bonereapers',
    ),
    (
        'arch-kavalos-zandtos',
        'OBR-007',
        'Arch-Kavalos Zandtos',
        60.00,
        '99120207074_OBRArchKavalosZandtosDarkLanceofOssia01.jpg',
        f'{_GW}Arch-Kavalos-Zandtos-Dark-Lance-Of-Ossia-2019',
        'Arch-Kavalos Zandtos Ossiarch Bonereapers',
    ),
    # ⚠ Mortarchs kit: Arkhan the Black shares the physical Deathlords Mortarchs
    #   box with Mannfred von Carstein and Neferata; only Arkhan is listed here.
    (
        'arkhan-the-black-mortarch-of-sacrament',
        'OBR-011',
        'Arkhan the Black, Mortarch of Sacrament',
        94.00,
        '99120207031_DeathLordsMortarchsArkhantheBlack01a.jpg',
        f'{_GW}Deathlords-Mortarchs-Arkhan',
        'Arkhan the Black, Mortarch of Sacrament Ossiarch Bonereapers',
    ),
    (
        'mortisan-soulreaper',
        'OBR-012',
        'Mortisan Soulreaper',
        36.50,
        '99120207222_OBVanguard01.jpg',
        f'{_GW}ossiarch-bonereapers-mortisan-soulreaper-2026',
        'Mortisan Soulreaper Ossiarch Bonereapers',
    ),
    (
        'liege-mortek',
        'OBR-013',
        'Liege-Mortek',
        36.50,
        '99120207199_OssiarchBonereapersLiegeMortek01.jpg',
        f'{_GW}ossiarch-bonereapers-liege-mortek-2026',
        'Liege-Mortek Ossiarch Bonereapers',
    ),
    (
        'liege-kavalos-on-war-chariot',
        'OBR-015',
        'Liege-Kavalos on War Chariot',
        77.00,
        '99120207200_OssiarchBonereapersLiegeKavalosWarChariot01.jpg',
        f'{_GW}ossiarch-bonereapers-liege-kavalos-on-war-chariot-2026',
        'Liege-Kavalos on War Chariot Ossiarch Bonereapers',
    ),
    (
        'mortisan-boneshaper',
        'OBR-019',
        'Mortisan Boneshaper',
        35.00,
        '99070207010_OBRMortisanBoneshaper01.jpg',
        f'{_GW}Ossiarch-Bonereapers-Mortisan-Boneshaper-2019',
        'Mortisan Boneshaper Ossiarch Bonereapers',
    ),

    # -- Units -----------------------------------------------------------------
    (
        'kavalos-deathriders',
        'OBR-005',
        'Kavalos Deathriders',
        65.00,
        '99120207077_OBRKavalosDeathriders01.jpg',
        f'{_GW}Ossiarch-Bonereapers-Kavalos-Deathriders-2019',
        'Kavalos Deathriders Ossiarch Bonereapers',
    ),
    (
        'morghast-harbingers',
        'OBR-009',
        'Morghast Harbingers',
        73.50,
        '99120207028_DeathLordsMarghastsHarbingers01.jpg',
        f'{_GW}Morghast-Harbingers-2018',
        'Morghast Harbingers Ossiarch Bonereapers',
    ),
    (
        'morghast-archai',
        'OBR-010',
        'Morghast Archai',
        73.50,
        '99120207028_DeathLordsMarghastsArchai01.jpg',
        f'{_GW}Morghast-Archai-2018',
        'Morghast Archai Ossiarch Bonereapers',
    ),
    (
        'mortek-triaxes',
        'OBR-014',
        'Mortek Triaxes',
        65.00,
        '99120207198_OssiarchBonereapersMortekTriaxes01.jpg',
        f'{_GW}ossiarch-bonereapers-mortek-triaxes-2026',
        'Mortek Triaxes Ossiarch Bonereapers',
    ),
    (
        'mortek-crawler',
        'OBR-018',
        'Mortek Crawler',
        96.00,
        '99120207078_OBRMortekCrawler01.jpg',
        f'{_GW}Ossiarch-Bonereapers-Mortek-Crawler-2019',
        'Mortek Crawler Ossiarch Bonereapers',
    ),

    # -- Warcry ----------------------------------------------------------------
    (
        'warcry-teratic-cohort',
        'OBR-017',
        'Warcry: Teratic Cohort',
        65.00,
        '60120299006_ENGWCBriarBone3.jpg',
        f'{_GW}warcry-teratic-cohort-2024',
        'Warcry: Teratic Cohort',
    ),

    # -- Terrain / Scenery -----------------------------------------------------
    (
        'bone-tithe-nexus',
        'OBR-020',
        'Bone-tithe Nexus',
        69.00,
        '99120207083_CITOBRBoneTitheNexus01.jpg',
        f'{_GW}Ossiarch-Bonereapers-Bone-Tithe-Nexus-2019',
        'Bone-tithe Nexus Ossiarch Bonereapers',
    ),

    # -- Spells / Endless ------------------------------------------------------
    (
        'endless-spells-ossiarch-bonereapers',
        'OBR-008',
        'Endless Spells: Ossiarch Bonereapers',
        53.00,
        '99120207082_CITOBREndlessSpells01.jpg',
        f'{_GW}Endless-Spells-Ossiarch-Bonereapers-2019',
        'Endless Spells: Ossiarch Bonereapers',
    ),

    # -- Battletome ------------------------------------------------------------
    (
        'death-battletome-ossiarch-bonereapers',
        'OBR-016',
        'Death Battletome: Ossiarch Bonereapers',
        60.00,
        '60030207022_engOssiarchBonereapersBattletome01.jpg',
        f'{_GW}battletome-ossiarch-bonereapers-2026-eng',
        'Death Battletome: Ossiarch Bonereapers',
    ),
]


class Command(BaseCommand):
    """Populate Ossiarch Bonereapers products (OBR-001 to OBR-020)."""

    help = (
        'Creates / updates 20 Ossiarch Bonereapers products and seeds GW prices at MSRP. '
        'Uses existing Ossiarch Bonereapers faction. Idempotent.'
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

        obr_faction, faction_created = Faction.objects.get_or_create(
            slug='ossiarch-bonereapers',
            defaults={'name': 'Ossiarch Bonereapers', 'category': category_aos},
        )
        if faction_created:
            self.stdout.write('  Created Ossiarch Bonereapers faction.')

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
                    'faction': obr_faction,
                    'category': category_aos,
                    'msrp': msrp,
                    'image_url': image_url,
                    'gw_url': gw_url,
                    'ebay_search_name': ebay_search_name,
                    'batch_tag': 'ossiarch-bonereapers',
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
                    defaults={'price': msrp, 'in_stock': True},
                )
                if price_created:
                    prices_created += 1
                else:
                    prices_updated += 1

        self.stdout.write(self.style.SUCCESS(
            f'populate_ossiarch_bonereapers_products complete. '
            f'Products: {products_created} created, {products_updated} updated. '
            f'GW prices: {prices_created} created, {prices_updated} updated.'
        ))
