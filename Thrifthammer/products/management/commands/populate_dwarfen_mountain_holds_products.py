"""
Management command: populate_dwarfen_mountain_holds_products

Creates / updates all Dwarfen Mountain Holds product entries for ThriftHammer,
seeds GW CurrentPrice records at MSRP.

Category: The Old World (created if not present)
Faction:  Dwarfen Mountain Holds (created if not present)

Safe to run repeatedly (idempotent via update_or_create keyed on slug).

Usage:
    python manage.py populate_dwarfen_mountain_holds_products
"""

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Category, Faction, Product, Retailer

_IMG = 'https://www.warhammer.com/app/resources/catalog/product/920x950/{filename}'

# (slug, gw_sku, name, msrp, image_filename, gw_url, ebay_search_name)
PRODUCTS = [
    (
        'dwarfen-mountain-holds-battalion',
        'DMH-001',
        'Dwarfen Mountain Holds Battalion',
        195.00,
        '99122705010_ENGWHtOWDMHBattleforce1New.jpg',
        'https://www.warhammer.com/en-US/shop/battalion-dwarfen-mountain-holds-2024',
        'Dwarfen Mountain Holds Battalion Old World Warhammer',
    ),
    (
        'dwarf-king-with-oathstone',
        'DMH-002',
        'Dwarf King With Oathstone',
        32.75,
        '99122705012_DMHDwarfKingOnOathstone01.jpg',
        'https://www.warhammer.com/en-US/shop/dwarfen-mountain-holds-dwarf-king-with-oathstone-2024',
        'Dwarf King With Oathstone Old World Warhammer',
    ),
    (
        'dwarf-slayer-of-legend',
        'DMH-003',
        'Dwarf Slayer of Legend',
        32.75,
        '99122705011_DMHSlayerOfLegend01.jpg',
        'https://www.warhammer.com/en-US/shop/dwarfen-mountain-holds-slayer-of-legend-2024',
        'Dwarf Slayer of Legend Old World Warhammer',
    ),
    (
        'dwarf-cannon-organ-gun',
        'DMH-004',
        'Dwarf Cannon & Organ Gun',
        60.00,
        '99122705008_DMHDwarfCannonsAndOrganGuns01.jpg',
        'https://www.warhammer.com/en-US/shop/dwarfen-mountain-holds-dwarf-cannon-and-organ-gun-2024',
        'Dwarf Cannon & Organ Gun Old World Warhammer',
    ),
    (
        'dwarf-gyrocopters',
        'DMH-005',
        'Dwarf Gyrocopters',
        82.00,
        '99122705007_DMHGyrocoptersAndGyrobombers01.jpg',
        'https://www.warhammer.com/en-US/shop/dwarfen-mountain-holds-gyrocopters-and-gyrobombers-2024',
        'Dwarf Gyrocopters Old World Warhammer',
    ),
    (
        'dwarf-miners',
        'DMH-006',
        'Dwarf Miners',
        65.00,
        '99122705006_DMHDwarfMiners01.jpg',
        'https://www.warhammer.com/en-US/shop/dwarfen-mountain-holds-dwarf-miners-2024',
        'Dwarf Miners Old World Warhammer',
    ),
    (
        'dwarf-lords-with-shieldbearers',
        'DMH-007',
        'Dwarf Lords with Shieldbearers',
        53.00,
        '99122705009_WHtOWDMHLordShieldbearers1.jpg',
        'https://www.warhammer.com/en-US/shop/dwarfen-mountain-holds-dwarf-lords-with-shieldbearers-2024',
        'Dwarf Lords with Shieldbearers Old World Warhammer',
    ),
    (
        'dwarf-hammerers',
        'DMH-008',
        'Dwarf Hammerers',
        90.00,
        '99122705005_WHtOWDMHHammers2.jpg',
        'https://www.warhammer.com/en-US/shop/dwarfen-mountain-holds-dwarf-hammerers-2024',
        'Dwarf Hammerers Old World Warhammer',
    ),
    (
        'dwarf-ironbreakers',
        'DMH-009',
        'Dwarf Ironbreakers',
        90.00,
        '99122705004_WHtOWDMHIronbreakers1.jpg',
        'https://www.warhammer.com/en-US/shop/dwarf-mountain-holds-dwarf-ironbreakers-2024',
        'Dwarf Ironbreakers Old World Warhammer',
    ),
    (
        'dwarf-quarrelers',
        'DMH-010',
        'Dwarf Quarrelers',
        90.00,
        '99122705003_WHtOWDMHQuarrelersThunderers1.jpg',
        'https://www.warhammer.com/en-US/shop/dwarfen-mountain-holds-dwarf-quarrellers-2024',
        'Dwarf Quarrelers Old World Warhammer',
    ),
    (
        'dwarf-warriors',
        'DMH-011',
        'Dwarf Warriors',
        90.00,
        '99122705002_WHtOWDMHWarriors2.jpg',
        'https://www.warhammer.com/en-US/shop/dwarfen-mountain-holds-dwarf-warriors-2024',
        'Dwarf Warriors Old World Warhammer',
    ),
    (
        'dwarf-runesmith',
        'DMH-012',
        'Dwarf Runesmith',
        32.00,
        '99122705001_WHtOWDMHRunesmith1.jpg',
        'https://www.warhammer.com/en-US/shop/dwarfen-mountain-holds-dwarf-runesmith-2024',
        'Dwarf Runesmith Old World Warhammer',
    ),
]


class Command(BaseCommand):
    help = 'Creates / updates Dwarfen Mountain Holds products and seeds GW prices. Idempotent.'

    def handle(self, *args, **options):
        tow_category, _ = Category.objects.get_or_create(
            slug='the-old-world',
            defaults={'name': 'The Old World'},
        )
        faction, _ = Faction.objects.get_or_create(
            slug='dwarfen-mountain-holds',
            defaults={'name': 'Dwarfen Mountain Holds', 'category': tow_category},
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
                    'batch_tag': 'dwarfen-mountain-holds',
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
            f'\npopulate_dwarfen_mountain_holds_products complete. '
            f'Products: {created_count} created, {updated_count} updated. '
            f'GW prices: {price_created} created, {price_updated} updated.'
        ))
