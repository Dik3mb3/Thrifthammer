"""
Management command: populate_high_elves_products

Creates / updates all High Elves product entries for ThriftHammer,
seeds GW CurrentPrice records at MSRP.

Category: The Old World (created if not present)
Faction:  High Elves (created if not present)

Safe to run repeatedly (idempotent via update_or_create keyed on slug).

Usage:
    python manage.py populate_high_elves_products
"""

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Category, Faction, Product, Retailer

_IMG = 'https://www.warhammer.com/app/resources/catalog/product/920x950/{filename}'

# (slug, gw_sku, name, msrp, image_filename, gw_url, ebay_search_name)
PRODUCTS = [
    (
        'tiranoc-chariots',
        'HER-001',
        'Tiranoc Chariots',
        90.00,
        '99122710018_HighElfRealmsTiranocChariotVehicle1.jpg',
        'https://www.warhammer.com/en-US/shop/high-elf-realms-tiranoc-chariot-2025',
        'Tiranoc Chariots Old World Warhammer',
    ),
    (
        'arcane-journal-high-elf-realms',
        'HER-002',
        'Arcane Journal: High Elf Realms',
        29.00,
        '60042799011_HERArcaneJournal01.jpg',
        'https://www.warhammer.com/en-US/shop/arcane-journal-high-elf-realms-2025-eng',
        'Arcane Journal: High Elf Realms Old World Warhammer',
    ),
    (
        'elven-spearmen',
        'HER-003',
        'Elven Spearmen',
        90.00,
        '99122710013_HighElfRealmsElvenSpearmenRegiment1.jpg',
        'https://www.warhammer.com/en-US/shop/high-elf-realms-elven-spearmen-2025',
        'Elven Spearmen Old World Warhammer',
    ),
    (
        'silver-helms',
        'HER-004',
        'Silver Helms',
        65.00,
        '99122710016_HighElfRealmsSilverHelmsRegiment1.jpg',
        'https://www.warhammer.com/en-US/shop/high-elf-realms-silver-helms-2025',
        'Silver Helms Old World Warhammer',
    ),
    (
        'high-elf-loremaster',
        'HER-005',
        'High Elf Loremaster',
        32.00,
        '99122710004_HighElfRealmsLoremasterCharacter1.jpg',
        'https://www.warhammer.com/en-US/shop/high-elf-realms-high-elf-loremaster-2025',
        'High Elf Loremaster Old World Warhammer',
    ),
    (
        'flamespyre-phoenix',
        'HER-006',
        'Flamespyre Phoenix',
        82.00,
        '99122710019_HighElfRealmsFlamespyrePhoenix1.jpg',
        'https://www.warhammer.com/en-US/shop/high-elf-realms-flamespyre-phoenix-2025',
        'Flamespyre Phoenix Old World Warhammer',
    ),
    (
        'lothern-skycutter',
        'HER-007',
        'Lothern Skycutter',
        82.00,
        '99122710011_HighElfRealmsLothernSkycutter2.jpg',
        'https://www.warhammer.com/en-US/shop/high-elf-realms-lothern-skycutter-2025',
        'Lothern Skycutter Old World Warhammer',
    ),
    (
        'dragon-princes-of-caledor',
        'HER-008',
        'Dragon Princes of Caledor',
        89.00,
        '99122710017_HERDragonPrinces01.jpg',
        'https://www.warhammer.com/en-US/shop/high-elf-realms-dragon-princes-of-caledor-2025',
        'Dragon Princes of Caledor Old World Warhammer',
    ),
    (
        'phoenix-guard',
        'HER-009',
        'Phoenix Guard',
        89.00,
        '99122710006_HERPhoenixGuard01.jpg',
        'https://www.warhammer.com/en-US/shop/high-elf-realms-phoenix-guard-2025',
        'Phoenix Guard Old World Warhammer',
    ),
    (
        'sisters-of-avelorn',
        'HER-010',
        'Sisters of Avelorn',
        55.00,
        '99122710015_HERSistersOfAvelorn01.jpg',
        'https://www.warhammer.com/en-US/shop/high-elf-realms-sisters-of-avelorn-2025',
        'Sisters of Avelorn Old World Warhammer',
    ),
    (
        'high-elf-mages',
        'HER-011',
        'High Elf Mages',
        45.00,
        '99122710003_HERHighElfMages01.jpg',
        'https://www.warhammer.com/en-US/shop/high-elf-realms-mages-2025',
        'High Elf Mages Old World Warhammer',
    ),
    (
        'high-elf-lords',
        'HER-012',
        'High Elf Lords',
        45.00,
        '99122710002_HERLords01.jpg',
        'https://www.warhammer.com/en-US/shop/high-elf-realms-high-elf-lords-2025',
        'High Elf Lords Old World Warhammer',
    ),
    (
        'ellyrian-reavers',
        'HER-013',
        'Ellyrian Reavers',
        89.00,
        '99122710009_HEREllyrianReavers01.jpg',
        'https://www.warhammer.com/en-US/shop/high-elf-realms-ellyrian-reavers-2025',
        'Ellyrian Reavers Old World Warhammer',
    ),
    (
        'white-lions-of-chrace',
        'HER-014',
        'White Lions of Chrace',
        89.00,
        '99122710007_HERWhiteLionsOfChrace01.jpg',
        'https://www.warhammer.com/en-US/shop/high-elf-realms-white-lions-of-chrace-2025',
        'White Lions of Chrace Old World Warhammer',
    ),
    (
        'eagle-claw-bolt-throwers',
        'HER-015',
        'Eagle-claw Bolt Throwers',
        60.00,
        '99122710010_HEREagleClawBoltThrowers01.jpg',
        'https://www.warhammer.com/en-US/shop/high-elf-realms-eagle-claw-bolt-throwers-2025',
        'Eagle-claw Bolt Throwers Old World Warhammer',
    ),
    (
        'lord-on-dragon',
        'HER-016',
        'Lord on Dragon',
        82.00,
        '99122710001_HERLordOnDragon01.jpg',
        'https://www.warhammer.com/en-US/shop/high-elf-realms-lord-on-dragon-2025',
        'Lord on Dragon Old World Warhammer',
    ),
    (
        'swordmasters-of-hoeth',
        'HER-017',
        'Swordmasters of Hoeth',
        89.00,
        '99122710008_HERSwordmastersOfHoeth01.jpg',
        'https://www.warhammer.com/en-US/shop/high-elf-realms-swordmasters-of-hoeth-2025',
        'Swordmasters of Hoeth Old World Warhammer',
    ),
    (
        'great-eagle-of-the-elven-realms',
        'HER-020',
        'Great Eagle of the Elven Realms',
        35.00,
        '99112710014_WHtOWHighElfRealmsGreatEagle1.jpg',
        'https://www.warhammer.com/en-US/shop/great-eagles-of-the-elven-realms-2025',
        'Great Eagle of the Elven Realms Old World Warhammer',
    ),
    (
        'handmaiden-of-the-everqueen',
        'HER-021',
        'Handmaiden of the Everqueen',
        15.00,
        '99062710020_WHtOWHighElfRealmsHandmaidenEverqueenCharacter1.jpg',
        'https://www.warhammer.com/en-US/shop/high-elf-realms-handmaiden-of-the-everqueen-2025',
        'Handmaiden of the Everqueen Old World Warhammer',
    ),
    (
        'korhil-lionmane',
        'HER-022',
        'Korhil Lionmane',
        18.00,
        '99062710004_WHtOWHighElfRealmsKorhilLionmane1.jpg',
        'https://www.warhammer.com/en-US/shop/high-elf-realms-korhil-lionmane-2025',
        'Korhil Lionmane Old World Warhammer',
    ),
    (
        'high-elf-realms-transfer-sheet',
        'HER-023',
        'High Elf Realms Transfer Sheet',
        36.50,
        '99512710001_HERTransferSheet01.jpg',
        'https://www.warhammer.com/en-US/shop/high-elf-realms-transfer-sheet-2025',
        'High Elf Realms Transfer Sheet Old World Warhammer',
    ),
    (
        'elven-archers',
        'HER-024',
        'Elven Archers',
        90.00,
        '99122710014_HighElfRealmsElvenArchersRegiment1.jpg',
        'https://www.warhammer.com/en-US/shop/high-elf-realms-elven-archers-2025',
        'Elven Archers Old World Warhammer',
    ),
    (
        'lothern-sea-guard',
        'HER-025',
        'Lothern Sea Guard',
        89.00,
        '99122710005_HERLothernSeaGuard01.jpg',
        'https://www.warhammer.com/en-US/shop/high-elf-realms-lothern-sea-guard-2025',
        'Lothern Sea Guard Old World Warhammer',
    ),
]


class Command(BaseCommand):
    help = 'Creates / updates High Elves products and seeds GW prices. Idempotent.'

    def handle(self, *args, **options):
        tow_category, _ = Category.objects.get_or_create(
            slug='the-old-world',
            defaults={'name': 'The Old World'},
        )
        faction, _ = Faction.objects.get_or_create(
            slug='high-elves',
            defaults={'name': 'High Elves', 'category': tow_category},
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
                    'batch_tag': 'high-elves',
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
            f'\npopulate_high_elves_products complete. '
            f'Products: {created_count} created, {updated_count} updated. '
            f'GW prices: {price_created} created, {price_updated} updated.'
        ))
