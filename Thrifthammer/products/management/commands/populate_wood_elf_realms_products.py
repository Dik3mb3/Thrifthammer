"""
Management command: populate_wood_elf_realms_products

Creates / updates all Wood Elf Realms product entries for ThriftHammer,
seeds GW CurrentPrice records at MSRP.

Category: The Old World (created if not present)
Faction:  Wood Elf Realms (created if not present)

Safe to run repeatedly (idempotent via update_or_create keyed on slug).

Usage:
    python manage.py populate_wood_elf_realms_products
"""

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Category, Faction, Product, Retailer

_IMG = 'https://www.warhammer.com/app/resources/catalog/product/920x950/{filename}'

# (slug, gw_sku, name, msrp, image_filename, gw_url, ebay_search_name)
PRODUCTS = [
    (
        'wood-elf-realms-battalion',
        'WER-001',
        'Wood Elf Realms Battalion',
        195.00,
        '99122704001_WERBattalion01.jpg',
        'https://www.warhammer.com/en-US/shop/battalion-wood-elf-realms-2025',
        'Wood Elf Realms Battalion Old World Warhammer',
    ),
    (
        'arcane-journal-wood-elf-realms',
        'WER-002',
        'Arcane Journal: Wood Elf Realms',
        29.00,
        '60042799013_WERArcaneJournal01.jpg',
        'https://www.warhammer.com/en-US/shop/arcane-journal-wood-elf-realms-sb-eng-2025',
        'Arcane Journal: Wood Elf Realms Old World Warhammer',
    ),
    (
        'wood-elf-noble-on-forest-dragon',
        'WER-003',
        'Wood Elf Noble on Forest Dragon',
        85.00,
        '99112704006_WERNobleOnForestDragonREPACKED01.jpg',
        'https://www.warhammer.com/en-US/shop/wood-elf-realms-noble-on-forest-dragon-2025',
        'Wood Elf Noble on Forest Dragon Old World Warhammer',
    ),
    (
        'araloth-lord-of-talsyn',
        'WER-004',
        'Araloth, Lord of Talsyn',
        32.00,
        '99122704006_Araloth1.jpg',
        'https://www.warhammer.com/en-US/shop/wood-elf-realms-araloth-lord-of-talsyn-2025',
        'Araloth, Lord of Talsyn Old World Warhammer',
    ),
    (
        'wild-riders',
        'WER-005',
        'Wild Riders',
        90.00,
        '99122704005_WoodElfRealmsWildridersREPACKED1.jpg',
        'https://www.warhammer.com/en-US/shop/wood-elf-realms-wildriders-2025',
        'Wild Riders Old World Warhammer',
    ),
    (
        'glade-riders',
        'WER-006',
        'Glade Riders',
        64.00,
        '99122704002_WoodElfRealmsGladeRidersREPACKED1.jpg',
        'https://www.warhammer.com/en-US/shop/wood-elf-realms-glade-riders-2025',
        'Glade Riders Old World Warhammer',
    ),
    (
        'eternal-guard',
        'WER-007',
        'Eternal Guard',
        90.00,
        '99122704004_WoodElfRealmsEternalGuardREPACKED1.jpg',
        'https://www.warhammer.com/en-US/shop/wood-elf-realms-eternal-guard-2025',
        'Eternal Guard Old World Warhammer',
    ),
    (
        'glade-guard',
        'WER-008',
        'Glade Guard',
        90.00,
        '99122704003_WoodElfRealmsGladeGuardRepackaged1.jpg',
        'https://www.warhammer.com/en-US/shop/wood-elf-realms-glade-guard-2025',
        'Glade Guard Old World Warhammer',
    ),
]


class Command(BaseCommand):
    help = 'Creates / updates Wood Elf Realms products and seeds GW prices. Idempotent.'

    def handle(self, *args, **options):
        tow_category, _ = Category.objects.get_or_create(
            slug='the-old-world',
            defaults={'name': 'The Old World'},
        )
        faction, _ = Faction.objects.get_or_create(
            slug='wood-elf-realms',
            defaults={'name': 'Wood Elf Realms', 'category': tow_category},
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
                    'batch_tag': 'wood-elf-realms',
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
            f'\npopulate_wood_elf_realms_products complete. '
            f'Products: {created_count} created, {updated_count} updated. '
            f'GW prices: {price_created} created, {price_updated} updated.'
        ))
