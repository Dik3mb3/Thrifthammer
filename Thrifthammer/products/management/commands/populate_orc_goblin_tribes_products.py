"""
Management command: populate_orc_goblin_tribes_products

Creates / updates all Orc & Goblin Tribes product entries for ThriftHammer,
seeds GW CurrentPrice records at MSRP.

Category: The Old World (created if not present)
Faction:  Orc & Goblin Tribes (created if not present)

Safe to run repeatedly (idempotent via update_or_create keyed on slug).

Usage:
    python manage.py populate_orc_goblin_tribes_products
"""

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Category, Faction, Product, Retailer

_IMG = 'https://www.warhammer.com/app/resources/catalog/product/920x950/{filename}'

# (slug, gw_sku, name, msrp, image_filename, gw_url, ebay_search_name)
PRODUCTS = [
    (
        'goblin-shaman',
        'OGT-001',
        'Goblin Shaman',
        32.00,
        '99072709001_OGTGoblinShaman01.jpg',
        'https://www.warhammer.com/en-US/shop/orc-and-goblin-tribes-goblin-shaman-2024',
        'Goblin Shaman Old World Warhammer',
    ),
    (
        'goblin-wolf-rider-mob',
        'OGT-002',
        'Goblin Wolf Rider Mob',
        69.00,
        '99122709007_OGTWolfRiderMob01.jpg',
        'https://www.warhammer.com/en-US/shop/orc-and-goblin-tribes-goblin-wolf-rider-mob-2024',
        'Goblin Wolf Rider Mob Old World Warhammer',
    ),
    (
        'goblin-mob',
        'OGT-003',
        'Goblin Mob',
        90.00,
        '99122709006_OGTGoblinMobArrowsSpears01.jpg',
        'https://www.warhammer.com/en-US/shop/orc-and-goblin-tribes-goblin-mob-2024',
        'Goblin Mob Old World Warhammer',
    ),
    (
        'orc-boar-chariots',
        'OGT-004',
        'Orc Boar Chariots',
        90.00,
        '99122709005_OGTOrcBoarChariots01.jpg',
        'https://www.warhammer.com/en-US/shop/orc-and-goblin-tribes-orc-boar-chariots-2024',
        'Orc Boar Chariots Old World Warhammer',
    ),
    (
        'black-orc-mob',
        'OGT-005',
        'Black Orc Mob',
        90.00,
        '99122709010_OGTBlackOrcMob01.jpg',
        'https://www.warhammer.com/en-US/shop/orc-and-goblin-tribes-black-orc-mob-2024',
        'Black Orc Mob Old World Warhammer',
    ),
    (
        'orc-boar-boyz-mob',
        'OGT-006',
        'Orc Boar Boyz Mob',
        69.00,
        '99122709004_OGTOrcBoarBoyzMob01.jpg',
        'https://www.warhammer.com/en-US/shop/orc-and-goblin-tribes-orc-boar-boyz-mob-2024',
        'Orc Boar Boyz Mob Old World Warhammer',
    ),
    (
        'orc-boyz-orc-arrer-boyz-mob',
        'OGT-007',
        'Orc Boyz & Orc Arrer Boyz Mob',
        90.00,
        '99122709003_OGTOrcBoyzAndOrcArrerBoyzMobs01.jpg',
        'https://www.warhammer.com/en-US/shop/orc-and-goblin-tribes-orc-boyz-and-orc-arrer-boyz-mobs-2024',
        'Orc Boyz & Orc Arrer Boyz Mob Old World Warhammer',
    ),
    (
        'orc-boyz-mob',
        'OGT-008',
        'Orc Boyz Mob',
        90.00,
        '99122709002_OGTOrcBoyzMob02.jpg',
        'https://www.warhammer.com/en-US/shop/orc-goblin-tribes-orc-boyz-mob-2024',
        'Orc Boyz Mob Old World Warhammer',
    ),
    (
        'orc-bosses',
        'OGT-009',
        'Orc Bosses',
        47.00,
        '99122709001_OGTOrcBosses02.jpg',
        'https://www.warhammer.com/en-US/shop/orc-goblin-tribes-orc-bosses-2024',
        'Orc Bosses Old World Warhammer',
    ),
    (
        'night-goblin-mob',
        'OGT-010',
        'Night Goblin Mob',
        90.00,
        '99122709009_OGTNightGoblinMob01.jpg',
        'https://www.warhammer.com/en-US/shop/orc-and-goblin-tribes-night-goblin-mob-2024',
        'Night Goblin Mob Old World Warhammer',
    ),
]


class Command(BaseCommand):
    help = 'Creates / updates Orc & Goblin Tribes products and seeds GW prices. Idempotent.'

    def handle(self, *args, **options):
        tow_category, _ = Category.objects.get_or_create(
            slug='the-old-world',
            defaults={'name': 'The Old World'},
        )
        faction, _ = Faction.objects.get_or_create(
            slug='orc-goblin-tribes',
            defaults={'name': 'Orc & Goblin Tribes', 'category': tow_category},
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
                    'batch_tag': 'orc-goblin-tribes',
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
            f'\npopulate_orc_goblin_tribes_products complete. '
            f'Products: {created_count} created, {updated_count} updated. '
            f'GW prices: {price_created} created, {price_updated} updated.'
        ))
