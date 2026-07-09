from django.core.management.base import BaseCommand
from products.models import Product


class Command(BaseCommand):
    help = 'Jun 2026t: eBay keyword/search name fixes for AGA-019, AGA-022, Rotigus, DOK-005, GG-016, SYL-009, BOK-002, BB-034 image'

    def handle(self, *args, **options):
        fixes = [
            ('ebay_negative_keywords', 'AGA-019', '"2017" "Shadow"'),
            ('ebay_search_name',       'AGA-022', 'Armageddon Box Ork Half'),
            ('ebay_negative_keywords', 'prod3700271-99129915063', 'legions imperialis Resin 04-113 D&D 5e 100th 1926 TShirt Plushie Plush Proxies Foil "Glottkin"'),
            ('ebay_negative_keywords', 'DOK-005', 'Bloodwrack Melusai Foil "hag queen"'),
            ('ebay_negative_keywords', 'GG-016',  'legions imperialis Resin 04-113 Proxies ARACHNOCAULDRON Mushroom Foil SCUTTLETIDE'),
            ('ebay_negative_keywords', 'SYL-009', 'legions imperialis Resin 04-113 Proxies Spiteswarm Skullroot Foil GLADEWYRM'),
            ('ebay_negative_keywords', 'BOK-002', 'legions imperialis Resin 04-113 Proxies Wrath-Axe Foil "Bleeding Icon"'),
            ('image_url',              'BB-034',  'https://www.warhammer.com/app/resources/catalog/product/920x950/99120999007_TreemanLead.jpg?fm=webp&w=892&h=920'),
        ]

        for field, sku, value in fixes:
            updated = Product.objects.filter(gw_sku=sku).update(**{field: value})
            self.stdout.write(f'{sku} {field}=[{value}] rows={updated}')

        self.stdout.write(self.style.SUCCESS('apply_batch_fixes_jun2026t done'))
