"""
Management command: populate_tomb_kings_of_khemri_products

Creates / updates all Tomb Kings of Khemri product entries for ThriftHammer,
seeds GW CurrentPrice records at MSRP.

Category: The Old World (created if not present)
Faction:  Tomb Kings of Khemri (created if not present)

Note: Necropolis Knights and Sepulchral Stalkers share the same GW catalog
number (99122717006) — they are dual-build kits. Khemrian Warsphinx and
Necrosphinx likewise share 99122717007.

Safe to run repeatedly (idempotent via update_or_create keyed on slug).

Usage:
    python manage.py populate_tomb_kings_of_khemri_products
"""

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Category, Faction, Product, Retailer

_IMG = 'https://www.warhammer.com/app/resources/catalog/product/920x950/{filename}'

# (slug, gw_sku, name, msrp, image_filename, gw_url, ebay_search_name)
PRODUCTS = [
    (
        'skeleton-chariots',
        'TKK-001',
        'Skeleton Chariots',
        90.00,
        '99122717004_WHTOWTKSkeletonChariots01.jpg',
        'https://www.warhammer.com/en-US/shop/tomb-kings-of-khemri-skeleton-chariots-2024',
        'Skeleton Chariots Old World Warhammer',
    ),
    (
        'tomb-kings-skeleton-warriors-archers',
        'TKK-002',
        'Tomb Kings Skeleton Warriors/Archers',
        90.00,
        '99122717002_WHTOWTKSkeletonWarriors02.jpg',
        'https://www.warhammer.com/en-US/shop/tomb-kings-of-khemri-skeleton-warriors-2024',
        'Tomb Kings Skeleton Warriors/Archers Old World Warhammer',
    ),
    (
        'liche-priests',
        'TKK-003',
        'Liche Priests',
        53.00,
        '99122717011_WarhammerOldWorldTombKingsofKhemriLichePriests1.jpg',
        'https://www.warhammer.com/en-US/shop/tomb-kings-of-khemri-liche-priests-2025',
        'Liche Priests Old World Warhammer',
    ),
    (
        'royal-heralds',
        'TKK-004',
        'Royal Heralds',
        53.00,
        '99122717010_WarhammerOldWorldTombKingsofKhemriTombHeralds1.jpg',
        'https://www.warhammer.com/en-US/shop/tomb-kings-of-khemri-royal-heralds-2025',
        'Royal Heralds Old World Warhammer',
    ),
    (
        'tomb-kings-skeleton-horsemen-horse-archers',
        'TKK-005',
        'Tomb Kings Skeleton Horsemen/Horse Archers',
        69.00,
        '99122717003_WHTOWTKSkeletonHorsmen02.jpg',
        'https://www.warhammer.com/en-US/shop/tomb-kings-of-khemri-skeleton-horsemen-2024',
        'Tomb Kings Skeleton Horsemen/Horse Archers Old World Warhammer',
    ),
    (
        'tomb-king-liche-priest-on-necrolith-bone-dragon',
        'TKK-006',
        'Tomb King/Liche Priest on Necrolith Bone Dragon',
        106.00,
        '99122717001_WHTOWTKTombKingOnNecrolithBoneDragon01.jpg',
        'https://www.warhammer.com/en-US/shop/tomb-kings-of-khemri-tomb-king-on-necrolith-bone-dragon-2024',
        'Tomb King/Liche Priest on Necrolith Bone Dragon Old World Warhammer',
    ),
    (
        # ⚠ Dual kit: Necropolis Knights / Sepulchral Stalkers share GW catalog 99122717006
        'necropolis-knights',
        'TKK-007',
        'Necropolis Knights',
        69.00,
        '99122717006_WHTOWTKNecropolisKnights02.jpg',
        'https://www.warhammer.com/en-US/shop/tomb-kings-of-khemri-necropolis-knights-2024',
        'Necropolis Knights Old World Warhammer',
    ),
    (
        # ⚠ Dual kit: Khemrian Warsphinx / Necrosphinx share GW catalog 99122717007
        'khemrian-warsphinx',
        'TKK-008',
        'Khemrian Warsphinx',
        82.00,
        '99122717007_WHTOWTKWarsphinx01.jpg',
        'https://www.warhammer.com/en-US/shop/tomb-kings-of-khemri-khemrian-warsphinx-2024',
        'Khemrian Warsphinx Old World Warhammer',
    ),
    (
        # ⚠ Dual kit: see Khemrian Warsphinx above
        'necrosphinx',
        'TKK-009',
        'Necrosphinx',
        82.00,
        '99122717007_WHTOWTKNecrosphinx01.jpg',
        'https://www.warhammer.com/en-US/shop/tomb-kings-of-khemri-necrosphinx-2024',
        'Necrosphinx Old World Warhammer',
    ),
    (
        # ⚠ Dual kit: see Necropolis Knights above
        'sepulchral-stalkers',
        'TKK-010',
        'Sepulchral Stalkers',
        69.00,
        '99122717006_WHTOWTKSepulchralStalkers02.jpg',
        'https://www.warhammer.com/en-US/shop/tomb-kings-of-khemri-sepulchral-stalkers-2024',
        'Sepulchral Stalkers Old World Warhammer',
    ),
    (
        'tomb-guard',
        'TKK-011',
        'Tomb Guard',
        90.00,
        '99122717005_WHTOWTKTombGuard01.jpg',
        'https://www.warhammer.com/en-US/shop/tomb-kings-of-khemri-tomb-guard-2024',
        'Tomb Guard Old World Warhammer',
    ),
    (
        'arcane-journal-the-war-of-settras-fury',
        'TKK-012',
        "Arcane Journal: The War of Settra's Fury",
        29.00,
        '60042717002_WarhammerOldWorldArcaneJournalWarofSettrasFuryBook1.jpg',
        'https://www.warhammer.com/en-US/shop/arcane-journal-the-war-of-settras-fury-pb-eng-2025',
        "Arcane Journal: The War of Settra's Fury Old World Warhammer",
    ),
    (
        'arcane-journal-tomb-kings-of-khemri',
        'TKK-013',
        'Arcane Journal: Tomb Kings of Khemri',
        29.00,
        '60042717001_ArcaneJournalTKoK1.jpg',
        'https://www.warhammer.com/en-US/shop/arcane-journal-tomb-kings-of-khemri-eng-2024',
        'Arcane Journal: Tomb Kings of Khemri Old World Warhammer',
    ),
]


class Command(BaseCommand):
    help = 'Creates / updates Tomb Kings of Khemri products and seeds GW prices. Idempotent.'

    def handle(self, *args, **options):
        tow_category, _ = Category.objects.get_or_create(
            slug='the-old-world',
            defaults={'name': 'The Old World'},
        )
        faction, _ = Faction.objects.get_or_create(
            slug='tomb-kings-of-khemri',
            defaults={'name': 'Tomb Kings of Khemri', 'category': tow_category},
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
                    'batch_tag': 'tomb-kings-of-khemri',
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
            f'\npopulate_tomb_kings_of_khemri_products complete. '
            f'Products: {created_count} created, {updated_count} updated. '
            f'GW prices: {price_created} created, {price_updated} updated.'
        ))
