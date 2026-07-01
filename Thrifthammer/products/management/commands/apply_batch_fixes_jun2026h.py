from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Product, Retailer


class Command(BaseCommand):
    help = 'Jun 2026h: TOW eBay search name fixes, allowed title words, WOC-009 no-listing, delete HER-018/019'

    def handle(self, *args, **options):
        # ebay_search_name updates
        search_fixes = [
            ('EOM-012', 'Empire Knights Empire of Man Warhammer Old World'),
            ('WOC-005', 'Chaos Warhounds Warriors of Chaos Warhammer Old World'),
            ('WER-005', 'Wild Riders Wood Elf Realms Warhammer Old World'),
            ('BBH-006', 'Gor Herd Beastmen Brayherds Warhammer Old World'),
            ('HER-001', 'Tiranoc Chariots High Elf Realms Warhammer the Old World'),
            ('GCA-007', 'Warhammer: Old World Sky Model Lantern'),
            ('DMH-008', 'Dwarf Hammerers Dwarfen Mountain Holds Warhammer Old World'),
            ('TKK-007', 'Sepulchral Stalkers Old World Warhammer'),
            ('GCA-003', 'Warhammer The Old World Grand Cathay Astromancers of the Celestial Court'),
            ('KOB-002', 'Kingdom of Bretonnia Men-At-Arms Warhammer The Old World'),
            ('OGT-003', 'Orc & Goblin Tribes Night Goblin Mob Warhammer The Old World'),
            ('OGT-008', 'Warhammer Old World Orc & Goblins Orc Boyz Mob'),
            ('OGT-009', 'Orc & Goblin Tribes Orc Bosses Warhammer The Old World'),
            ('OGT-010', 'Orc & Goblin Tribes Night Goblin Mob Warhammer The Old World'),
        ]
        for sku, name in search_fixes:
            updated = Product.objects.filter(gw_sku=sku).update(ebay_search_name=name)
            self.stdout.write(f'{sku} ebay_search_name=[{name}] rows={updated}')

        # ebay_allowed_title_words='&' for all SKUs whose search name contains &
        amp_skus = [
            'EOM-003', 'EOM-009', 'GCA-001', 'GCA-004', 'OGT-007',
            'OGT-003', 'OGT-008', 'OGT-009', 'OGT-010',
        ]
        for sku in amp_skus:
            updated = Product.objects.filter(gw_sku=sku).update(ebay_allowed_title_words='&')
            self.stdout.write(f'{sku} ebay_allowed_title_words=[&] rows={updated}')

        # WOC-009 — eBay no listing (manual override prevents scraper from touching)
        try:
            ebay = Retailer.objects.get(slug='ebay')
            woc009 = Product.objects.get(gw_sku='WOC-009')
            _, was_created = CurrentPrice.objects.update_or_create(
                product=woc009,
                retailer=ebay,
                defaults={
                    'url': '',
                    'price': None,
                    'not_available': True,
                    'manual_url_override': True,
                },
            )
            self.stdout.write(f'WOC-009 eBay no-listing {"created" if was_created else "updated"}')
        except Retailer.DoesNotExist:
            self.stdout.write('eBay retailer not found — skipping WOC-009')
        except Product.DoesNotExist:
            self.stdout.write('WOC-009 not found — skipping')

        # Delete HER-018, HER-019 (resin kits — plastic only)
        for sku in ['HER-018', 'HER-019']:
            deleted, _ = Product.objects.filter(gw_sku=sku).delete()
            self.stdout.write(f'{sku} deleted rows={deleted}')

        self.stdout.write(self.style.SUCCESS('apply_batch_fixes_jun2026h done'))
