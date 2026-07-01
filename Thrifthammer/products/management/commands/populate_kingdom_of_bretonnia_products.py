"""
Management command: populate_kingdom_of_bretonnia_products

Creates / updates all Kingdom of Bretonnia product entries for ThriftHammer,
seeds GW CurrentPrice records at MSRP.

Category: The Old World (created if not present)
Faction:  Kingdom of Bretonnia (created if not present)

Safe to run repeatedly (idempotent via update_or_create keyed on slug).

Usage:
    python manage.py populate_kingdom_of_bretonnia_products
"""

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Category, Faction, Product, Retailer

_IMG = 'https://www.warhammer.com/app/resources/catalog/product/920x950/{filename}'

# (slug, gw_sku, name, msrp, image_filename, gw_url, ebay_search_name)
PRODUCTS = [
    (
        'peasant-bowmen',
        'KOB-001',
        'Peasant Bowmen',
        90.00,
        '99122703007_KoBPeasantBowmenUpdate01.jpg',
        'https://www.warhammer.com/en-US/shop/kingdom-of-bretonnia-peasant-bowmen-2024',
        'Peasant Bowmen Old World Warhammer',
    ),
    (
        'men-at-arms',
        'KOB-002',
        'Men-at-Arms',
        90.00,
        '99122703005_MenAtArms2.jpg',
        'https://www.warhammer.com/en-US/shop/kingdom-of-bretonnia-men-at-arms-2024',
        'Men-at-Arms Old World Warhammer',
    ),
    (
        'knights-of-the-realm-knights-errant',
        'KOB-003',
        'Knights of the Realm/Knights Errant',
        69.00,
        '99122703004_KnightsRealm2.jpg',
        'https://www.warhammer.com/en-US/shop/kingdom-of-bretonnia-knights-of-the-realm-2024',
        'Knights of the Realm/Knights Errant Old World Warhammer',
    ),
    (
        'lord-on-royal-pegasus',
        'KOB-004',
        'Lord on Royal Pegasus',
        69.00,
        '99122703001_BRETLordPegasus1.jpg',
        'https://www.warhammer.com/en-US/shop/kingdom-of-bretonnia-lord-on-royal-pegasus-2024',
        'Lord on Royal Pegasus Old World Warhammer',
    ),
    (
        'pegasus-knights',
        'KOB-005',
        'Pegasus Knights',
        69.00,
        '99122703006_PegasusKnights2.jpg',
        'https://www.warhammer.com/en-US/shop/kingdom-of-bretonnia-pegasus-knights-2024',
        'Pegasus Knights Old World Warhammer',
    ),
    (
        'battle-standard-bearer-on-royal-pegasus',
        'KOB-006',
        'Battle Standard Bearer on Royal Pegasus',
        69.00,
        '99122703002_BretBattleStandardPegasus1.jpg',
        'https://www.warhammer.com/en-US/shop/kingdom-of-bretonnia-battle-standard-on-royal-pegasus-2024',
        'Battle Standard Bearer on Royal Pegasus Old World Warhammer',
    ),
    (
        'knights-of-the-realm-on-foot',
        'KOB-007',
        'Knights of the Realm on Foot',
        89.00,
        '99122703003_KnightsRealmFoot2.jpg',
        'https://www.warhammer.com/en-US/shop/kingdom-of-bretonnia-knights-of-the-realm-on-foot-2024',
        'Knights of the Realm on Foot Old World Warhammer',
    ),
    (
        'arcane-journal-kingdom-of-bretonnia',
        'KOB-008',
        'Arcane Journal: Kingdom of Bretonnia',
        29.00,
        '60042703001_ArcaneJournalKoB1.jpg',
        'https://www.warhammer.com/en-US/shop/arcane-journal-kingdom-of-bretonnia-eng-2024',
        'Arcane Journal: Kingdom of Bretonnia Old World Warhammer',
    ),
]


class Command(BaseCommand):
    help = 'Creates / updates Kingdom of Bretonnia products and seeds GW prices. Idempotent.'

    def handle(self, *args, **options):
        tow_category, _ = Category.objects.get_or_create(
            slug='the-old-world',
            defaults={'name': 'The Old World'},
        )
        faction, _ = Faction.objects.get_or_create(
            slug='kingdom-of-bretonnia',
            defaults={'name': 'Kingdom of Bretonnia', 'category': tow_category},
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
                    'batch_tag': 'kingdom-of-bretonnia',
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
            f'\npopulate_kingdom_of_bretonnia_products complete. '
            f'Products: {created_count} created, {updated_count} updated. '
            f'GW prices: {price_created} created, {price_updated} updated.'
        ))
