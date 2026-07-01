"""
Management command: populate_empire_of_man_products

Creates / updates all Empire of Man product entries for ThriftHammer,
seeds GW CurrentPrice records at MSRP.

Category: The Old World (created if not present)
Faction:  Empire of Man (created if not present)

Safe to run repeatedly (idempotent via update_or_create keyed on slug).

Usage:
    python manage.py populate_empire_of_man_products
"""

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Category, Faction, Product, Retailer

_IMG = 'https://www.warhammer.com/app/resources/catalog/product/920x950/{filename}'

# (slug, gw_sku, name, msrp, image_filename, gw_url, ebay_search_name)
PRODUCTS = [
    (
        'arcane-journal-empire-of-man',
        'EOM-001',
        'Arcane Journal: Empire of Man',
        29.00,
        '60042799006_EoMArcaneJournalSBBook01.jpg',
        'https://www.warhammer.com/en-US/shop/arcane-journal-empire-of-man-sb-2024-eng',
        'Arcane Journal: Empire of Man Old World Warhammer',
    ),
    (
        'empire-steam-tank',
        'EOM-002',
        'Empire Steam Tank',
        82.00,
        '99122702019_EoMSteamTankVehicle01.jpg',
        'https://www.warhammer.com/en-US/shop/empire-of-man-steam-tank-2025',
        'Empire Steam Tank Old World Warhammer',
    ),
    (
        'helblaster-volley-gun-helstorm-rocket-battery',
        'EOM-003',
        'Helblaster Volley Gun & Helstorm Rocket Battery',
        60.00,
        '99122702017_EoMEmpireHellblasterVolleygunAndHellstormRocketBattery01.jpg',
        'https://www.warhammer.com/en-US/shop/empire-of-man-helblaster-volley-gun-and-helstorm-rocket-battery-2025',
        'Helblaster Volley Gun & Helstorm Rocket Battery Old World Warhammer',
    ),
    (
        'empire-greatswords',
        'EOM-004',
        'Empire Greatswords',
        90.00,
        '99122702011_EoMGreatswordsRegiment01.jpg',
        'https://www.warhammer.com/en-US/shop/empire-of-man-greatswords-2025',
        'Empire Greatswords Old World Warhammer',
    ),
    (
        'flagellants',
        'EOM-005',
        'Flagellants',
        82.00,
        '99122702010_EoMEmpireFlagellants01.jpg',
        'https://www.warhammer.com/en-US/shop/empire-of-man-flagellants-2025',
        'Flagellants Old World Warhammer',
    ),
    (
        'state-missile-troops',
        'EOM-006',
        'State Missile Troops',
        90.00,
        '99122702009_EoMEmpireStateMissilesTroops01.jpg',
        'https://www.warhammer.com/en-US/shop/empire-of-man-state-missile-troops-2025',
        'State Missile Troops Old World Warhammer',
    ),
    (
        'empire-state-troops',
        'EOM-007',
        'Empire State Troops',
        90.00,
        '99122702008_EoMEmpireStateTroops01.jpg',
        'https://www.warhammer.com/en-US/shop/empire-of-man-empire-state-troops-2025',
        'Empire State Troops Old World Warhammer',
    ),
    (
        'empire-engineer-with-hochland-long-rifle',
        'EOM-008',
        'Empire Engineer with Hochland Long Rifle',
        32.75,
        '99122702006_EoMEmpireEngineerWithHochlandLongRifle01.jpg',
        'https://www.warhammer.com/en-US/shop/empire-of-man-engineer-with-hochland-long-rifle-2025',
        'Empire Engineer with Hochland Long Rifle Old World Warhammer',
    ),
    (
        'cannons-mortars',
        'EOM-009',
        'Cannons & Mortars',
        60.00,
        '99122702016_EoMCannonsAndMortars01.jpg',
        'https://www.warhammer.com/en-US/shop/empire-of-man-cannons-and-mortars-2024',
        'Cannons & Mortars Old World Warhammer',
    ),
    (
        'demigryph-knights',
        'EOM-010',
        'Demigryph Knights',
        65.00,
        '99122702015_EoMDemigryphKnights01.jpg',
        'https://www.warhammer.com/en-US/shop/empire-of-man-demigryph-knights-2024',
        'Demigryph Knights Old World Warhammer',
    ),
    (
        'empire-pistoliers',
        'EOM-011',
        'Empire Pistoliers',
        65.00,
        '99122702014_EoMPistoliers01.jpg',
        'https://www.warhammer.com/en-US/shop/empire-of-man-empire-pistoliers-2024',
        'Empire Pistoliers Old World Warhammer',
    ),
    (
        'empire-knights',
        'EOM-012',
        'Empire Knights',
        65.00,
        '99122702013_EoMEmpireKnights01.jpg',
        'https://www.warhammer.com/en-US/shop/empire-of-man-empire-knights-2024',
        'Empire Knights Old World Warhammer',
    ),
    (
        'free-company-militia',
        'EOM-013',
        'Free Company Militia',
        90.00,
        '99122702007_EoMFreeCompanyMilitia01.jpg',
        'https://www.warhammer.com/en-US/shop/empire-of-man-free-company-militia-2024',
        'Free Company Militia Old World Warhammer',
    ),
    (
        'general-of-the-empire-on-imperial-griffon',
        'EOM-014',
        'General of the Empire on Imperial Griffon',
        82.00,
        '99122702001_EoMGeneralOnImperialGriffin01.jpg',
        'https://www.warhammer.com/en-US/shop/general-of-the-empire-on-imperial-griffon-2024',
        'General of the Empire on Imperial Griffon Old World Warhammer',
    ),
    (
        'commanders-of-the-empire',
        'EOM-015',
        'Commanders of the Empire',
        32.75,
        '99122702004_EoMCommandersOfTheEmpire01.jpg',
        'https://www.warhammer.com/en-US/shop/empire-of-man-commanders-of-the-empire-2024',
        'Commanders of the Empire Old World Warhammer',
    ),
    (
        'empire-archers',
        'EOM-016',
        'Empire Archers',
        65.00,
        '99122702012_EoMEmpireArchers01.jpg',
        'https://www.warhammer.com/en-US/shop/empire-of-man-archers-2025',
        'Empire Archers Old World Warhammer',
    ),
    (
        'captain-of-the-empire',
        'EOM-017',
        'Captain of the Empire',
        33.50,
        '99122702005_EoMCaptainOfTheEmpire01.jpg',
        'https://www.warhammer.com/en-US/shop/empire-of-man-captain-of-the-empire-2025',
        'Captain of the Empire Old World Warhammer',
    ),
    (
        'war-altar-of-sigmar',
        'EOM-018',
        'War Altar of Sigmar',
        82.00,
        '99122702002_EoMWarAltarOfSigmar01.jpg',
        'https://www.warhammer.com/en-US/shop/empire-of-man-war-altar-of-sigmar-2024',
        'War Altar of Sigmar Old World Warhammer',
    ),
]


class Command(BaseCommand):
    help = 'Creates / updates Empire of Man products and seeds GW prices. Idempotent.'

    def handle(self, *args, **options):
        tow_category, _ = Category.objects.get_or_create(
            slug='the-old-world',
            defaults={'name': 'The Old World'},
        )
        faction, _ = Faction.objects.get_or_create(
            slug='empire-of-man',
            defaults={'name': 'Empire of Man', 'category': tow_category},
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
                    'category': tow_category,
                    'faction': faction,
                    'is_active': True,
                    'batch_tag': 'empire-of-man',
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
            f'\npopulate_empire_of_man_products complete. '
            f'Products: {created_count} created, {updated_count} updated. '
            f'GW prices: {price_created} created, {price_updated} updated.'
        ))
