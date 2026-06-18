"""
Management command: populate_fyreslayers_products

Creates / updates all Fyreslayers product entries for ThriftHammer,
seeds GW CurrentPrice records at MSRP, and creates the Fyreslayers faction
(does not exist in DB yet).

Covers 16 products (FYR-001 to FYR-016) from the
AOS Fyreslayers - GW, NK, MM.xlsx (2026-06-17).

Category: Age of Sigmar
Faction:  Fyreslayers (new -- will be created)

Dual-kit / triple-kit products (same physical box, multiple build options):
  - FYR-003 Auric Runesmiter on Magmadroth / FYR-015 Auric Runeson on Magmadroth /
    FYR-016 Auric Runefather on Magmadroth (Magmadroth kit -- three builds)
  - FYR-008 Hearthguard Berzerkers / FYR-009 Auric Hearthguard (Hearthguard kit)

Note: FYR-011 Auric Runemaster has no NK or MM URL -- the Excel URLs were data entry
errors pointing to the Magmadroth kit. Auric Runemaster is a separate foot model.

Images are baked in as one-off GW CDN URLs -- never auto-refreshed.

Safe to run repeatedly (idempotent via update_or_create keyed on slug).

Usage:
    python manage.py populate_fyreslayers_products
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
        'spearhead-fyreslayers',
        'FYR-001',
        'Spearhead: Fyreslayers',
        150.00,
        '99120205043_FYRVanguardLead.jpg',
        f'{_GW}spearhead-fyreslayers-2024',
        'Spearhead: Fyreslayers Age of Sigmar',
    ),

    # -- Heroes ----------------------------------------------------------------
    (
        'auric-flamekeeper',
        'FYR-002',
        'Auric Flamekeeper',
        35.00,
        '99070205014_FYRAuricFlamekeeperLead.jpg',
        f'{_GW}fyreslayers-auric-flamekeeper-2022',
        'Auric Flamekeeper Age of Sigmar',
    ),
    (
        'gotrek-gurnisson',
        'FYR-004',
        'Gotrek Gurnisson',
        39.00,
        '99120205036_GotrekGurnisson01.jpg',
        f'{_GW}Gotrek-Gurnisson-2019',
        'Gotrek Gurnisson Age of Sigmar',
    ),
    (
        'doomseeker',
        'FYR-006',
        'Doomseeker',
        35.00,
        '99070205009_FYREDoomseeker01.jpg',
        f'{_GW}Fyreslayer-Doomseeker-2019',
        'Doomseeker Age of Sigmar',
    ),
    (
        'grimwrath-berzerker',
        'FYR-007',
        'Grimwrath Berzerker',
        39.00,
        '99070205007_GrimWrathBerzerker01.jpg',
        f'{_GW}Grimwrath-Berserker',
        'Grimwrath Berzerker Fyreslayers Warhammer',
    ),
    (
        'auric-runemaster',
        'FYR-011',
        'Auric Runemaster',
        39.00,
        '99070205005_FyreslayersAuricRunemaster01.jpg',
        f'{_GW}Auric-Runemaster',
        'Auric Runemaster Fyreslayers Warhammer',
    ),
    (
        'grimhold-exile',
        'FYR-013',
        'Grimhold Exile',
        39.00,
        '99120205056_FjorisFlamebearers1.jpg',
        f'{_GW}grimhold-exile-2023',
        'Grimhold Exile Age of Sigmar',
    ),

    # -- Units -----------------------------------------------------------------
    # ⚠ Dual kit: Hearthguard Berzerkers and Auric Hearthguard share the same
    #   Hearthguard kit (gw-84-24). NK and MM listings cover both builds.
    (
        'hearthguard-berzerkers',
        'FYR-008',
        'Hearthguard Berzerkers',
        60.00,
        '99120205016_FyreslayersHearthGuardBerzerkers01.jpg',
        f'{_GW}Hearthguard-Berzerkers',
        'Hearthguard Berzerkers Age of Sigmar',
    ),
    (
        'auric-hearthguard',
        'FYR-009',
        'Auric Hearthguard',
        60.00,
        '99120205016_FyreslayersAuricHearthguard01.jpg',
        f'{_GW}Auric-Hearthguard',
        'Auric Hearthguard Age of Sigmar',
    ),
    (
        'vulkite-berzerkers',
        'FYR-010',
        'Vulkite Berzerkers',
        65.00,
        '99120205015_FyreslayersVulkiteBerzerkers01.jpg',
        f'{_GW}Vulkite-Berserkers',
        'Vulkite Berzerkers Age of Sigmar',
    ),
    (
        'vulkyn-flameseekers',
        'FYR-012',
        'Vulkyn Flameseekers',
        60.00,
        '99120205057_VulkynFlameseekers3.jpg',
        f'{_GW}fyreslayers-vulkyn-flameseekers-2025',
        'Vulkyn Flameseekers War Cry Warhammer',
    ),

    # -- Large Kits / Monsters -------------------------------------------------
    # ⚠ Triple kit: Auric Runesmiter, Auric Runeson, and Auric Runefather all
    #   build from the same Magmadroth kit (gw-84-23). NK and MM listings cover
    #   all three builds under "Auric Runefather on Magmadroth".
    (
        'auric-runesmiter-on-magmadroth',
        'FYR-003',
        'Auric Runesmiter on Magmadroth',
        122.00,
        '99120205047_FYRAuricRuneSMITERonMagmadrothLead.jpg',
        f'{_GW}fyreslayers-auric-runesmiter-on-magmadroth-2022',
        'Auric Runefather on Magmadroth Age of Sigmar',
    ),
    (
        'auric-runeson-on-magmadroth',
        'FYR-015',
        'Auric Runeson on Magmadroth',
        122.00,
        '99120205047_FYRAuricRuneSONonMagmadrothLead.jpg',
        f'{_GW}fyreslayers-auric-runeson-on-magmadroth-2022',
        'Auric Runefather on Magmadroth Age of Sigmar',
    ),
    (
        'auric-runefather-on-magmadroth',
        'FYR-016',
        'Auric Runefather on Magmadroth',
        122.00,
        '99120205047_FYRAuricRuneFATHERonMagmadrothLead.jpg',
        f'{_GW}fyreslayers-auric-runefather-on-magmadroth-2022',
        'Auric Runefather on Magmadroth Age of Sigmar',
    ),

    # -- Terrain / Endless Spells ----------------------------------------------
    (
        'magmic-invocations',
        'FYR-005',
        'Magmic Invocations',
        42.00,
        '99120205034_FYREMagmicInvocations01.jpg',
        f'{_GW}Fyreslayers-Magmic-Invocations-2019',
        'Magmic Invocations Age of Sigmar',
    ),
    (
        'magmic-battleforge',
        'FYR-014',
        'Magmic Battleforge',
        53.00,
        '99120205035_CITFYREMagmicBattleforge01.jpg',
        f'{_GW}Fyreslayers-Magmic-Battleforge-2019',
        'Magmic Battleforge Age of Sigmar',
    ),
]


class Command(BaseCommand):
    """Populate Fyreslayers products (FYR-001 to FYR-016)."""

    help = (
        'Creates / updates 16 Fyreslayers products and seeds GW prices at MSRP. '
        'Creates Fyreslayers faction if it does not exist. Idempotent.'
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

        fyr_faction, faction_created = Faction.objects.get_or_create(
            slug='fyreslayers',
            defaults={'name': 'Fyreslayers', 'category': category_aos},
        )
        if faction_created:
            self.stdout.write('  Created Fyreslayers faction.')

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
                    'faction': fyr_faction,
                    'category': category_aos,
                    'msrp': msrp,
                    'image_url': image_url,
                    'gw_url': gw_url,
                    'ebay_search_name': ebay_search_name,
                    'batch_tag': 'fyreslayers',
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
                    defaults={'price': msrp, 'url': gw_url, 'in_stock': True, 'not_available': False},
                )
                if price_created:
                    prices_created += 1
                else:
                    prices_updated += 1

        self.stdout.write(self.style.SUCCESS(
            f'populate_fyreslayers_products complete. '
            f'Products: {products_created} created, {products_updated} updated. '
            f'GW prices: {prices_created} created, {prices_updated} updated.'
        ))
