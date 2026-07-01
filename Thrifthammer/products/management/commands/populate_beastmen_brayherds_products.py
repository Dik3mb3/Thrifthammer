"""
Management command: populate_beastmen_brayherds_products

Creates / updates all Beastmen Brayherds product entries for ThriftHammer,
seeds GW CurrentPrice records at MSRP.

Category: The Old World (created if not present)
Faction:  Beastmen Brayherds (created if not present)

Safe to run repeatedly (idempotent via update_or_create keyed on slug).

Usage:
    python manage.py populate_beastmen_brayherds_products
"""

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Category, Faction, Product, Retailer

_IMG = 'https://www.warhammer.com/app/resources/catalog/product/920x950/{filename}'

# (slug, gw_sku, name, msrp, image_filename, gw_url, ebay_search_name)
PRODUCTS = [
    (
        'tuskgor-chariot',
        'BBH-001',
        'Tuskgor Chariot',
        43.50,
        '99112716002_TOWBBTuskgorChariotVehicle01.jpg',
        'https://www.warhammer.com/en-US/shop/beastmen-brayherds-tuskgor-chariot-2025',
        'Tuskgor Chariot Old World Warhammer',
    ),
    (
        'beastman-chieftain',
        'BBH-002',
        'Beastman Chieftain',
        32.00,
        '99122716008_TOWBBChieftain01.jpg',
        'https://www.warhammer.com/en-US/shop/beastmen-brayherds-beastmen-chieftain-2025',
        'Beastman Chieftain Old World Warhammer',
    ),
    (
        'ungor-herd',
        'BBH-003',
        'Ungor Herd',
        90.00,
        '99122716003_TOWBBUngorHerd01.jpg',
        'https://www.warhammer.com/en-US/shop/beastmen-brayherds-ungor-herd-2025',
        'Ungor Herd Old World Warhammer',
    ),
    (
        'cygor-ghorgon',
        'BBH-004',
        'Cygor/Ghorgon',
        82.00,
        '99122716006_TOWBBCygor01.jpg',
        'https://www.warhammer.com/en-US/shop/beastmen-brayherds-cygor-2025',
        'Cygor/Ghorgon Old World Warhammer',
    ),
    (
        'minotaur-herd',
        'BBH-005',
        'Minotaur Herd',
        60.00,
        '99122716005_TOWBBMinotaurHerd01.jpg',
        'https://www.warhammer.com/en-US/shop/beastmen-brayherds-minotaur-herd-2025',
        'Minotaur Herd Old World Warhammer',
    ),
    (
        'gor-herd',
        'BBH-006',
        'Gor Herd',
        90.00,
        '99122716002_TOWBBGorHerd01.jpg',
        'https://www.warhammer.com/en-US/shop/beastmen-brayherds-gor-herd-2025',
        'Gor Herd Old World Warhammer',
    ),
    (
        'bestigor-herd',
        'BBH-007',
        'Bestigor Herd',
        90.00,
        '99122716004_TOWBBBestigorHerd01.jpg',
        'https://www.warhammer.com/en-US/shop/beastmen-brayherds-bestigor-herd-2025',
        'Bestigor Herd Old World Warhammer',
    ),
    (
        'beastman-shaman',
        'BBH-008',
        'Beastman Shaman',
        32.00,
        '99122716001_TOWBBShaman01.jpg',
        'https://www.warhammer.com/en-US/shop/beastmen-brayherds-beastman-shaman-2025',
        'Beastman Shaman Old World Warhammer',
    ),
]


class Command(BaseCommand):
    help = 'Creates / updates Beastmen Brayherds products and seeds GW prices. Idempotent.'

    def handle(self, *args, **options):
        tow_category, _ = Category.objects.get_or_create(
            slug='the-old-world',
            defaults={'name': 'The Old World'},
        )
        faction, _ = Faction.objects.get_or_create(
            slug='beastmen-brayherds',
            defaults={'name': 'Beastmen Brayherds', 'category': tow_category},
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
                    'batch_tag': 'beastmen-brayherds',
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
            f'\npopulate_beastmen_brayherds_products complete. '
            f'Products: {created_count} created, {updated_count} updated. '
            f'GW prices: {price_created} created, {price_updated} updated.'
        ))
