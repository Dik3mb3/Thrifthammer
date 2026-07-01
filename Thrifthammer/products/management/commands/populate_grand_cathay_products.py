"""
Management command: populate_grand_cathay_products

Creates / updates all Grand Cathay product entries for ThriftHammer,
seeds GW CurrentPrice records at MSRP.

Category: The Old World (created if not present)
Faction:  Grand Cathay (created if not present)

Safe to run repeatedly (idempotent via update_or_create keyed on slug).

Usage:
    python manage.py populate_grand_cathay_products
"""

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Category, Faction, Product, Retailer

_IMG = 'https://www.warhammer.com/app/resources/catalog/product/920x950/{filename}'

# (slug, gw_sku, name, msrp, image_filename, gw_url, ebay_search_name)
PRODUCTS = [
    (
        'iron-hail-gunners-crane-gunner-teams',
        'GCA-001',
        'Iron Hail Gunners & Crane Gunner Teams',
        90.00,
        '99122720011_IRONHAILCRANEGUNNERS1a.jpg',
        'https://www.warhammer.com/en-US/shop/grand-cathay-iron-hail-and-crane-gunners-2026',
        'Iron Hail Gunners & Crane Gunner Teams Old World Warhammer',
    ),
    (
        'peasant-levy',
        'GCA-002',
        'Peasant Levy',
        90.00,
        '99122720012_PEASANTLEVY1.jpg',
        'https://www.warhammer.com/en-US/shop/grand-cathay-peasant-levy-2026',
        'Peasant Levy Old World Warhammer',
    ),
    (
        'astromancers-of-the-celestial-court',
        'GCA-003',
        'Astromancers of the Celestial Court',
        53.00,
        '99122720010_ASTROMANCERSCELESTCOURT1a.jpg',
        'https://www.warhammer.com/en-US/shop/grand-cathay-astromancers-of-the-celestial-court-2026',
        'Astromancers of the Celestial Court Old World Warhammer',
    ),
    (
        'grand-cannon-fire-rain-rocket-battery',
        'GCA-004',
        'Grand Cannon & Fire Rain Rocket Battery',
        90.00,
        '99122720005_TOWGrandCannonAndFireRainRocketBattery01.jpg',
        'https://www.warhammer.com/en-US/shop/grand-cannon-and-fire-rain-rocket-battery-2025',
        'Grand Cannon & Fire Rain Rocket Battery Old World Warhammer',
    ),
    (
        'jade-lancers',
        'GCA-005',
        'Jade Lancers',
        90.00,
        '99122720004_WHtOWBattalionEmpireofGrandCathayBoxedArmy03.jpg',
        'https://www.warhammer.com/en-US/shop/grand-cathay-jade-lancers-2025',
        'Jade Lancers Old World Warhammer',
    ),
    (
        'miao-ying-the-storm-dragon',
        'GCA-006',
        'Miao Ying, the Storm Dragon',
        155.00,
        '99122720008_TOWMiaoYingTheStormDragon01.jpg',
        'https://www.warhammer.com/en-US/shop/grand-cathay-miao-ying-the-storm-dragon-2025',
        'Miao Ying, the Storm Dragon Old World Warhammer',
    ),
    (
        'sky-lantern',
        'GCA-007',
        'Sky Lantern',
        165.00,
        '99122720007_WHtOWGrandCathayKongmingSkyLantern01.jpg',
        'https://www.warhammer.com/en-US/shop/grand-cathay-sky-lantern-2025',
        'Sky Lantern Old World Warhammer',
    ),
    (
        'cathayan-sentinel',
        'GCA-008',
        'Cathayan Sentinel',
        130.00,
        '99122720006_WHtOWGrandCathayCathayanSentinelExtra01.jpg',
        'https://www.warhammer.com/en-US/shop/grand-cathay-cathayan-sentinel-2025',
        'Cathayan Sentinel Old World Warhammer',
    ),
    (
        'gate-masters-of-the-celestial-cities',
        'GCA-009',
        'Gate Masters of the Celestial Cities',
        53.00,
        '99122720003_WHtOWGrandCathayGateMastersoftheCelestialCities01.jpg',
        'https://www.warhammer.com/en-US/shop/grand-cathay-gate-masters-of-the-celestial-cities-2025',
        'Gate Masters of the Celestial Cities Old World Warhammer',
    ),
    (
        'shugengan-lord-on-great-spirit-longma',
        'GCA-010',
        'Shugengan Lord on Great Spirit Longma',
        65.00,
        '99122720001_WHtOWGrandCathayShugenganLordonGreatSpiritLongmar01.jpg',
        'https://www.warhammer.com/en-US/shop/shugengan-lord-on-great-spirit-longma-2025',
        'Shugengan Lord on Great Spirit Longma Old World Warhammer',
    ),
    (
        'arcane-journal-dawn-of-the-storm-dragon',
        'GCA-011',
        'Arcane Journal: Dawn of the Storm Dragon',
        29.00,
        '60042720002_WarhammerOldWorldArcaneJournalDawnoftheStormDragonSB1.jpg',
        'https://www.warhammer.com/en-US/shop/arcane-journal-dawn-of-the-storm-dragon-2025',
        'Arcane Journal: Dawn of the Storm Dragon Old World Warhammer',
    ),
    (
        'arcane-journal-armies-of-grand-cathay',
        'GCA-012',
        'Arcane Journal: Armies of Grand Cathay',
        29.00,
        '60042720001_WHtOWArcaneJournalArmiesofGrandCathayRulebook01.jpg',
        'https://www.warhammer.com/en-US/shop/arcane-journal-armies-of-grand-cathay-2025-eng',
        'Arcane Journal: Armies of Grand Cathay Old World Warhammer',
    ),
    (
        'the-northern-provinces-of-grand-cathay-transfer-sheet',
        'GCA-013',
        'The Northern Provinces of Grand Cathay Transfer Sheet',
        36.50,
        '99512720001_WarhammerOldWorldNorthernProvincesofGrandCathayTransfer.jpg',
        'https://www.warhammer.com/en-US/shop/northern-provinces-of-grand-cathay-tranfers-2025',
        'The Northern Provinces of Grand Cathay Transfer Sheet Old World Warhammer',
    ),
    (
        'jade-warriors',
        'GCA-014',
        'Jade Warriors',
        90.00,
        '99122720002_TOWCathayJadeWarriorsExtra01.jpg',
        'https://www.warhammer.com/en-US/shop/grand-cathay-jade-warriors-2025',
        'Jade Warriors Old World Warhammer',
    ),
    (
        'arcane-journal-the-breaching-of-the-great-bastion',
        'GCA-015',
        'Arcane Journal: The Breaching of the Great Bastion',
        29.00,
        '60042720003_WHtOWArcaneJournalBreachingoftheGreatBastionENG1.jpg',
        'https://www.warhammer.com/en-US/shop/arcane-journal-breaching-of-the-great-bastion-2026-eng',
        'Arcane Journal: The Breaching of the Great Bastion Old World Warhammer',
    ),
]


class Command(BaseCommand):
    help = 'Creates / updates Grand Cathay products and seeds GW prices. Idempotent.'

    def handle(self, *args, **options):
        tow_category, _ = Category.objects.get_or_create(
            slug='the-old-world',
            defaults={'name': 'The Old World'},
        )
        faction, _ = Faction.objects.get_or_create(
            slug='grand-cathay',
            defaults={'name': 'Grand Cathay', 'category': tow_category},
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
                    'batch_tag': 'grand-cathay',
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
            f'\npopulate_grand_cathay_products complete. '
            f'Products: {created_count} created, {updated_count} updated. '
            f'GW prices: {price_created} created, {price_updated} updated.'
        ))
