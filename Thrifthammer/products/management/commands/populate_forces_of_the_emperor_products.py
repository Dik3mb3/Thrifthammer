"""
Management command: populate_forces_of_the_emperor_products

Creates / updates all Forces of the Emperor product entries for ThriftHammer,
seeds GW CurrentPrice records at MSRP.

Category: Horus Heresy (already exists in DB)
Faction:  Forces of the Emperor (created if not present)

Dual-kit notes:
  Solar Auxilia Tactical Command Section / Solar Auxilia Lasrifle Section share GW catalog 99123005012.

Excludes 7 products that are the same physical kits as existing Custodes
catalog entries (AC-004, AC-005, AC-007, AC-008, AC-023, 01-08, 01-10).
Those are cross-tagged via secondary_factions instead of duplicated.
See add_forces_of_the_emperor_secondary_faction.py.

Safe to run repeatedly (idempotent via update_or_create keyed on slug).

Usage:
    python manage.py populate_forces_of_the_emperor_products
"""

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Category, Faction, Product, Retailer

_IMG = 'https://www.warhammer.com/app/resources/catalog/product/920x950/{filename}'

# (slug, gw_sku, name, msrp, image_filename, gw_url, ebay_search_name)
PRODUCTS = [
    (
        'rapier-fire-support-battery',
        'FOE-001',
        'Rapier Fire Support Battery',
        73.50,
        '99123005019_SOLARAUXILIARAPIERFIRESUPPORTBATTERY2.jpg',
        'https://www.warhammer.com/en-US/shop/solar-auxilia-rapier-fire-support-battery-2026',
        'Rapier Fire Support Battery Horus Heresy',
    ),
    (
        'rapier-direct-fire-battery',
        'FOE-002',
        'Rapier Direct Fire Battery',
        73.50,
        '99123005018_SOLARAUXILIARAPIERDIRECTFIREBATTERY2.jpg',
        'https://www.warhammer.com/en-US/shop/solar-auxilia-rapier-direct-fire-battery-2026',
        'Rapier Direct Fire Battery Horus Heresy',
    ),
    (
        'liber-auxilia-solar-auxilia-army-book',
        'FOE-003',
        'Liber Auxilia: Solar Auxilia Army Book',
        53.00,
        '60033005001_ENGHorusHeresyLiberAuxiliaCodex1.jpg',
        'https://www.warhammer.com/en-US/shop/horus-heresy-liber-auxilia-2025-eng',
        'Liber Auxilia: Solar Auxilia Army Book Horus Heresy',
    ),
    (
        'charonite-ogryn-section',
        'FOE-004',
        'Charonite Ogryn Section',
        73.50,
        '99123005017_SOLARAUXILIACHARONITEOGRYNSECTION1a.jpg',
        'https://www.warhammer.com/en-US/shop/solar-auxilia-charonite-ogryn-section-2026',
        'Charonite Ogryn Section Horus Heresy',
    ),
    (
        'sentinel-guard-sodality',
        'FOE-005',
        'Sentinel Guard Sodality',
        73.50,
        '99123043002_CustodesSentinelGuard1.jpg',
        'https://www.warhammer.com/en-US/shop/legio-custodes-sentinel-guard-sodality-2026',
        'Sentinel Guard Sodality Horus Heresy',
    ),
    (
        'venatari-sodality',
        'FOE-006',
        'Venatari Sodality',
        82.00,
        '99123043003_CustodesVenatariSodality1.jpg',
        'https://www.warhammer.com/en-US/shop/legio-custodes-venatari-sodality-2026',
        'Venatari Sodality Horus Heresy',
    ),
    (
        'custodian-guard-sodality',
        'FOE-007',
        'Custodian Guard Sodality',
        73.50,
        '99123043005_CustodesCustodianGuard1.jpg',
        'https://www.warhammer.com/en-US/shop/legio-custodes-custodian-guard-sodality-2026',
        'Custodian Guard Sodality Horus Heresy',
    ),
    (
        'solar-auxilia-combat-force',
        'FOE-008',
        'Solar Auxilia: Combat Force',
        170.00,
        '99123005021_HorusHeresySolarAuxiliaCombatForceArmy1.jpg',
        'https://www.warhammer.com/en-US/shop/horus-heresy-solar-auxilia-combat-force-2025',
        'Solar Auxilia: Combat Force Horus Heresy',
    ),
    (
        'malcador-infernus',
        'FOE-009',
        'Malcador Infernus',
        110.00,
        '99123005013_HHSolarAuxiliaMalcadorInfernusVehicle1.jpg',
        'https://www.warhammer.com/en-US/shop/solar-auxilia-malcador-infernus-2025',
        'Malcador Infernus Horus Heresy',
    ),
    (
        'valdor-tank-destroyer',
        'FOE-010',
        'Valdor Tank Destroyer',
        92.00,
        '99123005010_HHSolarAuxiliaValdorTankHunterVehicle1.jpg',
        'https://www.warhammer.com/en-US/shop/solar-auxilia-valdor-tank-destroyer-2025',
        'Valdor Tank Destroyer Horus Heresy',
    ),
    (
        'arvus-lighter',
        'FOE-011',
        'Arvus Lighter',
        82.00,
        '99123008007_HHArvusLighterVehicle1.jpg',
        'https://www.warhammer.com/en-US/shop/horus-heresy-arvus-lighter-2025',
        'Arvus Lighter Horus Heresy',
    ),
    (
        'hermes-light-veletaris-sentinel-squadron',
        'FOE-012',
        'Hermes Light/Veletaris Sentinel Squadron',
        69.00,
        '99123005011_THHSolarAuxilliaHermesLightSentinelSquadron01.jpg',
        'https://www.warhammer.com/en-US/shop/solar-auxilia-hermes-sentinel-squadron-2024',
        'Hermes Light/Veletaris Sentinel Squadron Horus Heresy',
    ),
    (
        'solar-auxilia-basilisk-medusa',
        'FOE-013',
        'Solar Auxilia Basilisk/Medusa',
        69.00,
        '99122605007_BasilisksMedusas1.jpg',
        'https://www.warhammer.com/en-US/shop/solar-auxilia-basilisk-medusa-2024',
        'Solar Auxilia Basilisk/Medusa Horus Heresy',
    ),
    (
        'solar-auxilia-leman-russ-assault-tank',
        'FOE-014',
        'Solar Auxilia Leman Russ Assault Tank',
        69.00,
        '99123005006_SALemanRussAssaultTank1.jpg',
        'https://www.warhammer.com/en-US/shop/solar-auxilia-leman-russ-assault-tank-2024',
        'Solar Auxilia Leman Russ Assault Tank Horus Heresy',
    ),
    (
        'malcador-heavy-tank',
        'FOE-015',
        'Malcador Heavy Tank',
        96.00,
        '99123005005_SAMalcador1.jpg',
        'https://www.warhammer.com/en-US/shop/solar-auxilia-malcador-2024',
        'Malcador Heavy Tank Horus Heresy',
    ),
    (
        'veletaris-storm-section',
        'FOE-016',
        'Veletaris Storm Section',
        60.00,
        '99123005008_Veletaris2.jpg',
        'https://www.warhammer.com/en-US/shop/solar-auxilia-velataris-2024',
        'Veletaris Storm Section Horus Heresy',
    ),
    (
        'aethon-heavy-sentinel',
        'FOE-017',
        'Aethon Heavy Sentinel',
        60.00,
        '99123005009_AethonHeavySentinel2a.jpg',
        'https://www.warhammer.com/en-US/shop/solar-auxilia-aethon-heavy-sentinel-2024',
        'Aethon Heavy Sentinel Horus Heresy',
    ),
    (
        # ⚠ Dual kit: shares GW catalog 99123005012 with 'Solar Auxilia Lasrifle Section'
        'solar-auxilia-tactical-command-section',
        'FOE-018',
        'Solar Auxilia Tactical Command Section',
        35.00,
        '99123005012_THHSolarAuxLaunchBox09.jpg',
        'https://www.warhammer.com/en-US/shop/solar-auxilia-tactical-command-section-2024',
        'Solar Auxilia Tactical Command Section Horus Heresy',
    ),
    (
        # ⚠ Dual kit: shares GW catalog 99123005012 with 'Solar Auxilia Tactical Command Section'
        'solar-auxilia-lasrifle-section',
        'FOE-019',
        'Solar Auxilia Lasrifle Section',
        82.00,
        '99123005012_THHSolarAuxLaunchBox02.jpg',
        'https://www.warhammer.com/en-US/shop/solar-auxilia-lasrifle-section-2024',
        'Solar Auxilia Lasrifle Section Horus Heresy',
    ),
    (
        'solar-auxilia-leman-russ-strike-command-tank',
        'FOE-020',
        'Solar Auxilia Leman Russ Strike/Command Tank',
        69.00,
        '99123005004_LemanRussStrikeTank1.jpg',
        'https://www.warhammer.com/en-US/shop/solar-auxilia-leman-russ-strike-tank-2024',
        'Solar Auxilia Leman Russ Strike/Command Tank Horus Heresy',
    ),
    (
        'dracosan-armoured-transport',
        'FOE-021',
        'Dracosan Armoured Transport',
        96.00,
        '99123005001_DracosanArmouredTransport1.jpg',
        'https://www.warhammer.com/en-US/shop/solar-auxilia-dracosan-2024',
        'Dracosan Armoured Transport Horus Heresy',
    ),
]


class Command(BaseCommand):
    help = 'Creates / updates Forces of the Emperor products and seeds GW prices. Idempotent.'

    def handle(self, *args, **options):
        hh_category, _ = Category.objects.get_or_create(
            slug='horus-heresy',
            defaults={'name': 'Horus Heresy'},
        )
        faction, _ = Faction.objects.get_or_create(
            slug='forces-of-the-emperor',
            defaults={'name': 'Forces of the Emperor', 'category': hh_category},
        )
        gw_retailer = Retailer.objects.filter(name='Games Workshop').first()

        created_count = updated_count = price_created = price_updated = 0

        for (slug, gw_sku, name, msrp, img_filename, gw_url, ebay_name) in PRODUCTS:
            product, created = Product.objects.update_or_create(
                slug=slug,
                defaults={
                    'name': name,
                    'gw_sku': gw_sku,
                    'msrp': msrp,
                    'image_url': _IMG.format(filename=img_filename),
                    'gw_url': gw_url,
                    'ebay_search_name': ebay_name,
                    'category': hh_category,
                    'faction': faction,
                    'is_active': True,
                    'batch_tag': 'forces-of-the-emperor',
                },
            )
            if created:
                created_count += 1
            else:
                updated_count += 1
            self.stdout.write(f'  {"Created" if created else "Updated"}: {name} ({gw_sku})')

            if gw_retailer and msrp is not None:
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
            f'\npopulate_forces_of_the_emperor_products complete. '
            f'Products: {created_count} created, {updated_count} updated. '
            f'GW prices: {price_created} created, {price_updated} updated.'
        ))
