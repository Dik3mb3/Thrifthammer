"""
Management command: populate_cities_of_sigmar_products

Creates / updates all Cities of Sigmar product entries for ThriftHammer,
seeds GW CurrentPrice records at MSRP, and uses the existing Cities of Sigmar
faction (slug=cities-of-sigmar, already in DB).

Covers 27 products (COS-001 to COS-027) from the
AOS Cities of Sigmar - GW, NK, MM.xlsx (2026-06-17).

Category: Age of Sigmar
Faction:  Cities of Sigmar (existing -- get_or_create is safe/idempotent)

Dual-kit products (same physical box, two build options):
  - COS-010 Conqueror Cogfort / COS-011 Cannonade Cogfort

Images are baked in as one-off GW CDN URLs -- never auto-refreshed.

Safe to run repeatedly (idempotent via update_or_create keyed on slug).

Usage:
    python manage.py populate_cities_of_sigmar_products
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

    # -- Regiments of Renown ---------------------------------------------------
    (
        'regiment-of-renown-ven-densts-hounds',
        'COS-001',
        "Regiment of Renown: Ven Denst's Hounds",
        94.00,
        '99120202071_CitiesOfSigmarVenDenstsHounds01.jpg',
        f'{_GW}cities-of-sigmar-ven-densts-hounds-2026',
        "Cities of Sigmar Regiments of Renown Ven Denst's Hounds",
    ),

    # -- Large Kits ------------------------------------------------------------
    (
        'gate-gargants',
        'COS-002',
        'Gate Gargants',
        106.00,
        '99120202064_GATEGARGANTS1.jpg',
        f'{_GW}cities-of-sigmar-gate-gargants-2026',
        'Gate Gargants Age of Sigmar',
    ),
    # ⚠ Dual kit: Conqueror Cogfort / Cannonade Cogfort share the same physical
    #   box (GW-86-15). NK and MM listings cover both builds.
    (
        'conqueror-cogfort',
        'COS-010',
        'Conqueror Cogfort',
        210.00,
        '99120202068_CANNONADECONQUERORCOGFORT2.jpg',
        f'{_GW}cities-of-sigmar-conqueror-cogfort-2026',
        'Cannonade Cogfort Age of Sigmar',
    ),
    (
        'cannonade-cogfort',
        'COS-011',
        'Cannonade Cogfort',
        210.00,
        '99120202068_CANNONADECONQUERORCOGFORT1.jpg',
        f'{_GW}cities-of-sigmar-cannonade-cogfort-2026',
        'Cannonade Cogfort Age of Sigmar',
    ),
    (
        'tahlia-vedra-lioness-of-the-parch',
        'COS-018',
        'Tahlia Vedra, Lioness of the Parch',
        165.00,
        '99120202043_TahliaVedraLionessoftheParch1.jpg',
        f'{_GW}tahlia-vedra-lioness-of-the-parch-2023',
        'Tahlia Vedra, Lioness of the Parch Age of Sigmar',
    ),

    # -- Heroes ----------------------------------------------------------------
    (
        'mallus-forgepriest',
        'COS-003',
        'Mallus Forgepriest',
        40.00,
        '99120202062_CitiesOfSigmarMallusForgepriest01.jpg',
        f'{_GW}cities-of-sigmar-mallus-forgepriest-2026',
        'Cities of Sigmar Mallus Forgepriest',
    ),
    (
        'jorvan-kreel-heir-of-the-kraken',
        'COS-004',
        'Jorvan Kreel, Heir of the Kraken',
        47.00,
        '99120202075_CitiesOfSigmarJorvanKreelHeirOfTheKraken01.jpg',
        f'{_GW}cities-of-sigmar-jorvan-kreel-heir-of-the-kraken-2026',
        'Cities of Sigmar Jorvan Kreel, Heir of the Kraken',
    ),
    (
        'aqshian-pyrocaster',
        'COS-005',
        'Aqshian Pyrocaster',
        40.00,
        '99120202067_AQSHIANPYROCASTER1.jpg',
        f'{_GW}cities-of-sigmar-aqshian-pyrocaster-2026',
        'Aqshian Pyrocaster Age of Sigmar',
    ),
    (
        'amethyst-knellmage',
        'COS-006',
        'Amethyst Knellmage',
        40.00,
        '99120202066_AMETHYSTKNELLMAGE1.jpg',
        f'{_GW}cities-of-sigmar-amethyst-knellmage-2026',
        'Amethyst Knellmage Age of Sigmar',
    ),
    (
        'erasmus-zonn-the-enlightened-one',
        'COS-007',
        'Erasmus Zonn the Enlightened One',
        69.00,
        '99120202065_ERASMUSZONN1.jpg',
        f'{_GW}cities-of-sigmar-erasmus-zonn-the-enlightened-one-2026',
        'Erasmus Zonn the Enlightened One Age of Sigmar',
    ),
    (
        'dawners-triumph',
        'COS-009',
        "Dawner's Triumph",
        65.00,
        '99120202072_CitiesOfSigmarDawnersTriumph01.jpg',
        f'{_GW}cities-of-sigmar-dawners-triumph-2026',
        "Dawner's Triumph Age of Sigmar",
    ),
    (
        'galen-and-doralia-ven-denst',
        'COS-014',
        'Galen and Doralia ven Denst',
        60.00,
        '99120202037_AoSGalenDoraliaVenDenstLead.jpg',
        f'{_GW}Galen-And-Doralia-Ven-Denst-2021',
        'Galen and Doralia ven Denst Age of Sigmar',
    ),
    (
        'pontifex-zenestra-matriarch-of-the-great-wheel',
        'COS-017',
        'Pontifex Zenestra, Matriarch of the Great Wheel',
        73.50,
        '99120202046_PontifexVenestraMatriarchoftheGreatWheel1.jpg',
        f'{_GW}zenestra-matriarch-of-the-great-wheel-2023',
        'Pontifex Zenestra, Matriarch of the Great Wheel Age of Sigmar',
    ),
    (
        'fusil-major-on-ogor-warhulk',
        'COS-019',
        'Fusil-Major on Ogor Warhulk',
        60.00,
        '99120202047_FusilMajoronOgorWarhulk1.jpg',
        f'{_GW}fusil-major-on-ogor-warhulk-2023',
        'Fusil-Major on Ogor Warhulk Age of Sigmar',
    ),
    (
        'freeguild-marshal-and-relic-envoy',
        'COS-020',
        'Freeguild Marshal and Relic Envoy',
        47.00,
        '99120202040_FreeguildMarshalRelicEnvoy2.jpg',
        f'{_GW}freeguild-marshal-and-relic-envoy-2023',
        'Freeguild Marshal and Relic Envoy Age of Sigmar',
    ),
    (
        'alchemite-warforger',
        'COS-025',
        'Alchemite Warforger',
        39.00,
        '99120202039_CoSAlchemiteWarforger1.jpg',
        f'{_GW}alchemite-warforger-2023',
        'Alchemite Warforger Age of Sigmar',
    ),
    (
        'luminark-of-hysh',
        'COS-026',
        'Luminark of Hysh',
        73.50,
        '99120202055_LuminarkofHysh1.jpg',
        f'{_GW}cities-of-sigmar-luminark-of-hysh-2024',
        'Luminark of Hysh Age of Sigmar',
    ),
    (
        'freeguild-cavalier-marshal',
        'COS-027',
        'Freeguild Cavalier-Marshal',
        60.00,
        '99120202044_FreeguildCavalierMarshal1.jpg',
        f'{_GW}freeguild-cavalier-marshal-2023',
        'Freeguild Cavalier-Marshal Age of Sigmar',
    ),

    # -- Units -----------------------------------------------------------------
    (
        'freeguild-grenadiers',
        'COS-012',
        'Freeguild Grenadiers',
        60.00,
        '60010299051_ENGCityofAshSpearheadGame5.jpg',
        f'{_GW}cities-of-sigmar-freeguild-grenadiers-2026',
        'Freeguild Grenadiers Age of Sigmar',
    ),
    (
        'freeguild-gallants',
        'COS-013',
        'Freeguild Gallants',
        60.00,
        '99120202063_CitiesOfSigmarFreeguildGallants01.jpg',
        f'{_GW}cities-of-sigmar-freeguild-gallants-2026',
        'Freeguild Gallants Age of Sigmar',
    ),
    (
        'wildercorps-hunters',
        'COS-015',
        'Wildercorps Hunters',
        60.00,
        '60120299003_WCHandHCoreGame3.jpg',
        f'{_GW}cities-of-sigmar-wildercorps-hunters-2025',
        'Wildercorps Hunters Age of Sigmar',
    ),
    (
        'saviours-of-cinderfall',
        'COS-016',
        'Saviours of Cinderfall',
        82.00,
        '99120299096_CallisTollSavioursofCinderfall2.jpg',
        f'{_GW}callis-toll-saviours-of-cinderfall-2024',
        'Saviours of Cinderfall Age of Sigmar',
    ),
    (
        'ironweld-great-cannon',
        'COS-021',
        'Ironweld Great Cannon',
        60.00,
        '99120202045_FreeguildIronweldCannon1.jpg',
        f'{_GW}ironweld-great-cannon-2023',
        'Ironweld Great Cannon Age of Sigmar',
    ),
    (
        'freeguild-steelhelms',
        'COS-022',
        'Freeguild Steelhelms',
        60.00,
        '99120202041_FreeguildSteelhelms2.jpg',
        f'{_GW}freeguild-steelhelms-2023',
        'Freeguild Steelhelms Age of Sigmar',
    ),
    (
        'freeguild-command-corps',
        'COS-023',
        'Freeguild Command Corps',
        60.00,
        '99120202048_FreeguildCommand2.jpg',
        f'{_GW}freeguild-command-corps-2023',
        'Freeguild Command Corps Age of Sigmar',
    ),
    (
        'freeguild-cavaliers',
        'COS-024',
        'Freeguild Cavaliers',
        69.00,
        '99120202042_AoSCoSigmar7.jpg',
        f'{_GW}freeguild-cavaliers-2023',
        'Freeguild Cavaliers Age of Sigmar',
    ),

    # -- Battletome ------------------------------------------------------------
    (
        'order-battletome-cities-of-sigmar',
        'COS-008',
        'Order Battletome: Cities of Sigmar 4th Edition',
        60.00,
        '60030202006_ENGCoSigmarBattletomeSTDED1.jpg',
        f'{_GW}battletome-cities-of-sigmar-2026-eng',
        'Order Battletome: Cities of Sigmar Age of Sigmar',
    ),
]


class Command(BaseCommand):
    """Populate Cities of Sigmar products (COS-001 to COS-027)."""

    help = (
        'Creates / updates 27 Cities of Sigmar products and seeds GW prices at MSRP. '
        'Uses existing Cities of Sigmar faction. Idempotent.'
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

        cos_faction, faction_created = Faction.objects.get_or_create(
            slug='cities-of-sigmar',
            defaults={'name': 'Cities of Sigmar', 'category': category_aos},
        )
        if faction_created:
            self.stdout.write('  Created Cities of Sigmar faction.')

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
                    'faction': cos_faction,
                    'category': category_aos,
                    'msrp': msrp,
                    'image_url': image_url,
                    'gw_url': gw_url,
                    'ebay_search_name': ebay_search_name,
                    'batch_tag': 'cities-of-sigmar',
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
            f'populate_cities_of_sigmar_products complete. '
            f'Products: {products_created} created, {products_updated} updated. '
            f'GW prices: {prices_created} created, {prices_updated} updated.'
        ))
