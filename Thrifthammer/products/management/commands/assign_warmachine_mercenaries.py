"""
Management command: assign_warmachine_mercenaries

Tenth step of reorganizing the flat 348-product Warmachine category into
per-faction structure. Creates the "Mercenaries" Faction under the existing
Warmachine Category, reassigns the 21 existing WMH-xxx products that belong
to it as their primary faction, and creates 1 brand-new product (Captain
Barl "Demolisher" Dunax, WMH-367) that was missing from the original
348-product batch entirely -- same "sheet includes a product the catalog
never had" situation as Protectorate of Menoth, just a single SKU here
instead of a whole new faction.

All 21 reassigned rows from the user-supplied "Mercenaries - Warmachine -
Steamforged.xlsx" matched an existing product by exact name -- cross-
checked (title, price, and existing faction) before writing this command.
User explicitly flagged the possibility of dual-tag/shared SKUs with other
already-assigned factions before this batch was processed (matching the
Southern Kriels/Khymaera "Shadows & Scum" precedent) -- checked directly
against every already-assigned faction and confirmed **zero** collisions
this time; all 21 were still sitting unassigned (faction=None).

Usage:
    python manage.py assign_warmachine_mercenaries
"""

import decimal

from django.core.management.base import BaseCommand
from django.utils.text import slugify

from prices.models import CurrentPrice
from products.models import Category, Faction, Product, Retailer

MERCENARIES_PRIMARY_SKUS = [
    'WMH-001', 'WMH-015', 'WMH-016', 'WMH-017', 'WMH-031', 'WMH-059', 'WMH-060', 'WMH-061',
    'WMH-062', 'WMH-095', 'WMH-187', 'WMH-188', 'WMH-189', 'WMH-190', 'WMH-191', 'WMH-192',
    'WMH-193', 'WMH-194', 'WMH-195', 'WMH-196', 'WMH-321',
]

# New product, not part of the original 348 -- created here, not reassigned.
NEW_PRODUCT = {
    'slug': slugify('Captain Barl Demolisher Dunax Mercenary'),
    'gw_sku': 'WMH-367',
    'name': 'Warmachine: Captain Barl "Demolisher" Dunax (Mercenary)',
    'msrp': decimal.Decimal('19.99'),
    'image_url': 'https://warmachine.gg/cdn/shop/files/WM-ProductImage-Mercenary-BarlDunax.png?v=1787659148&width=2000',
    'product_url': 'https://warmachine.gg/products/warmachine-captain-barl-demolisher-dunax-mercenary',
}


class Command(BaseCommand):
    """Create the Mercenaries faction, reassign its products, and add the one new SKU."""

    help = 'Creates Warmachine: Mercenaries faction, reassigns 21 products, and creates WMH-367.'

    def handle(self, *args, **options):
        category = Category.objects.get(slug='warmachine')

        faction, created = Faction.objects.get_or_create(
            name='Mercenaries',
            defaults={'slug': 'warmachine-mercenaries', 'category': category},
        )
        if created:
            self.stdout.write(self.style.SUCCESS('Created faction: Mercenaries'))
        else:
            self.stdout.write(f'Found faction: Mercenaries (pk={faction.pk})')

        reassigned = 0
        missing = []
        for gw_sku in MERCENARIES_PRIMARY_SKUS:
            try:
                product = Product.objects.get(gw_sku=gw_sku)
            except Product.DoesNotExist:
                missing.append(gw_sku)
                continue
            product.faction = faction
            product.save(update_fields=['faction'])
            reassigned += 1
            self.stdout.write(f'  reassigned: {product.name} ({gw_sku})')

        if missing:
            self.stdout.write(self.style.WARNING(f'  Not found, skipped: {", ".join(missing)}'))

        steamforged = Retailer.objects.get(slug='steamforged-games')
        new_product, new_created = Product.objects.update_or_create(
            slug=NEW_PRODUCT['slug'],
            defaults={
                'gw_sku': NEW_PRODUCT['gw_sku'],
                'name': NEW_PRODUCT['name'],
                'category': category,
                'faction': faction,
                'msrp': NEW_PRODUCT['msrp'],
                'image_url': NEW_PRODUCT['image_url'],
                'gw_url': NEW_PRODUCT['product_url'],
                'ebay_search_name': NEW_PRODUCT['name'],
                'batch_tag': 'warmachine-mercenaries',
                'is_active': True,
            },
        )
        CurrentPrice.objects.update_or_create(
            product=new_product,
            retailer=steamforged,
            defaults={
                'price': NEW_PRODUCT['msrp'],
                'url': NEW_PRODUCT['product_url'],
                'in_stock': True,
                'not_available': False,
            },
        )
        self.stdout.write(
            f"  {'Created' if new_created else 'Updated'}: {new_product.name} ({new_product.gw_sku})"
        )

        self.stdout.write(self.style.SUCCESS(
            f'assign_warmachine_mercenaries complete. {reassigned} product(s) reassigned, '
            f'1 new product created.'
        ))
