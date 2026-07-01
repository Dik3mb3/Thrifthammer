"""
Management command: populate_warriors_of_chaos_products

Creates / updates all Warriors of Chaos (The Old World) product entries for
ThriftHammer, seeds GW CurrentPrice records at MSRP.

Category: The Old World (created if not present)
Faction:  Warriors of Chaos (created if not present)

Safe to run repeatedly (idempotent via update_or_create keyed on slug).

Usage:
    python manage.py populate_warriors_of_chaos_products
"""

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Category, Faction, Product, Retailer

_IMG = 'https://www.warhammer.com/app/resources/catalog/product/920x950/{filename}'

# (slug, gw_sku, name, msrp, image_filename, gw_url, ebay_search_name)
PRODUCTS = [
    (
        'chaos-marauder-horsemen',
        'WOC-001',
        'Chaos Marauder Horsemen',
        90.00,
        '99122701015_WarhammertheOldWorldWarriorsOfChaosMarauderHorsemen01.jpg',
        'https://www.warhammer.com/en-US/shop/warriors-of-chaos-chaos-marauder-horsemen-2026',
        'Chaos Marauder Horsemen Old World Warhammer',
    ),
    (
        'arcane-journal-warriors-of-chaos',
        'WOC-002',
        'Arcane Journal: Warriors of Chaos',
        29.00,
        '60042799010_WoCArcaneJournal01.jpg',
        'https://www.warhammer.com/en-US/shop/arcane-journal-warriors-of-chaos-sb-eng-2024',
        'Arcane Journal: Warriors of Chaos Old World Warhammer',
    ),
    (
        'chaos-marauders',
        'WOC-003',
        'Chaos Marauders',
        90.00,
        '99122701014_WarhammertheOldWorldWarriorsOfChaosMarauders01.jpg',
        'https://www.warhammer.com/en-US/shop/warriors-of-chaos-chaos-marauders-2026',
        'Chaos Marauders Old World Warhammer',
    ),
    (
        'chaos-chariots',
        'WOC-004',
        'Chaos Chariots',
        89.00,
        '99122701008_WoCChariots1.jpg',
        'https://www.warhammer.com/en-US/shop/warriors-of-chaos-chaos-chariots-2024',
        'Chaos Chariots Old World Warhammer',
    ),
    (
        'chaos-warhounds',
        'WOC-005',
        'Chaos Warhounds',
        65.00,
        '99122701007_WoCWarhounds1.jpg',
        'https://www.warhammer.com/en-US/shop/warriors-of-chaos-chaos-warhounds-2024',
        'Chaos Warhounds Old World Warhammer',
    ),
    (
        'chimera',
        'WOC-006',
        'Chimera',
        65.00,
        '99122701010_Chimera1.jpg',
        'https://www.warhammer.com/en-US/shop/warriors-of-chaos-chimera-2024',
        'Chimera Old World Warhammer',
    ),
    (
        'sorcerer-of-chaos',
        'WOC-007',
        'Sorcerer of Chaos',
        33.50,
        '99122701012_SorcererofChaos1.jpg',
        'https://www.warhammer.com/en-US/shop/warriors-of-chaos-sorcerer-of-chaos-2024',
        'Sorcerer of Chaos Old World Warhammer',
    ),
    (
        'arcane-journal-the-razing-of-westerland',
        'WOC-008',
        'Arcane Journal: The Razing of Westerland',
        29.00,
        '60042701001_WHtOWArcaneJournalRazingofWesterland1.jpg',
        'https://www.warhammer.com/en-US/shop/arcane-journal-the-razing-of-westerland-eng-2025',
        'Arcane Journal: The Razing of Westerland Old World Warhammer',
    ),
    (
        'dragon-ogres',
        'WOC-009',
        'Dragon Ogres',
        65.00,
        '99122701011_DragonOgres1.jpg',
        'https://www.warhammer.com/en-US/shop/warriors-of-chaos-dragon-ogres-2024',
        'Dragon Ogres Old World Warhammer',
    ),
    (
        'chaos-lord-on-manticore',
        'WOC-010',
        'Chaos Lord on Manticore',
        82.00,
        '99122701001_LordonManticore1.jpg',
        'https://www.warhammer.com/en-US/shop/warriors-of-chaos-lord-on-manticore-2024',
        'Chaos Lord on Manticore Old World Warhammer',
    ),
]


class Command(BaseCommand):
    help = 'Creates / updates Warriors of Chaos (TOW) products and seeds GW prices. Idempotent.'

    def handle(self, *args, **options):
        tow_category, _ = Category.objects.get_or_create(
            slug='the-old-world',
            defaults={'name': 'The Old World'},
        )
        faction, _ = Faction.objects.get_or_create(
            slug='warriors-of-chaos',
            defaults={'name': 'Warriors of Chaos', 'category': tow_category},
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
                    'batch_tag': 'warriors-of-chaos',
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
            f'\npopulate_warriors_of_chaos_products complete. '
            f'Products: {created_count} created, {updated_count} updated. '
            f'GW prices: {price_created} created, {price_updated} updated.'
        ))
