"""
Management command: populate_sm_armageddon_box_products

Adds the 2026 launch box to Space Marines:
  SM-001  Warhammer 40,000: Armageddon Box  $295.00

Seeds GW CurrentPrice at MSRP. Idempotent (update_or_create keyed on slug).

Usage:
    python manage.py populate_sm_armageddon_box_products
"""

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Category, Faction, Product, Retailer

_IMG = 'https://www.warhammer.com/app/resources/catalog/product/920x950/{filename}'

# (slug, gw_sku, name, msrp, image_filename, gw_url, ebay_search_name)
PRODUCTS = [
    (
        'warhammer-40000-armageddon-box',
        'SM-001',
        'Warhammer 40,000: Armageddon Box',
        295.00,
        '60010199080_engArmageddon01.jpg',
        'https://www.warhammer.com/en-US/shop/warhammer-40000-armageddon-2026-eng',
        'Warhammer 40K Armageddon Box',
    ),
]


class Command(BaseCommand):
    """Seed the Warhammer 40,000: Armageddon Box product and GW price."""

    help = 'populate_sm_armageddon_box_products — adds SM-001 Armageddon Box ($295)'

    def handle(self, *args, **options):
        """Run the command."""
        category_40k = Category.objects.filter(name='Warhammer 40,000').first()
        if not category_40k:
            self.stderr.write(self.style.ERROR(
                'Warhammer 40,000 category not found — run populate_products first.'
            ))
            return

        faction = Faction.objects.filter(slug='space-marines').first()
        if not faction:
            self.stderr.write(self.style.ERROR(
                'space-marines faction not found — run populate_products first.'
            ))
            return

        gw_retailer = Retailer.objects.filter(name='Games Workshop').first()
        if not gw_retailer:
            self.stdout.write(self.style.WARNING(
                'Games Workshop retailer not found — GW prices will not be seeded.'
            ))

        products_created = 0
        products_updated = 0
        prices_created = 0
        prices_updated = 0

        for (slug, gw_sku, name, msrp, img_filename, gw_url, ebay_search_name) in PRODUCTS:
            image_url = _IMG.format(filename=img_filename)

            product, created = Product.objects.update_or_create(
                slug=slug,
                defaults={
                    'gw_sku': gw_sku,
                    'name': name,
                    'msrp': msrp,
                    'image_url': image_url,
                    'gw_url': gw_url,
                    'category': category_40k,
                    'faction': faction,
                    'is_active': True,
                    'batch_tag': 'sm-armageddon',
                    'ebay_search_name': ebay_search_name,
                },
            )
            status = 'Created' if created else 'Updated'
            self.stdout.write(self.style.SUCCESS(
                f'  {status}: {name} ({gw_sku}) — ${msrp:.2f}'
            ))
            if created:
                products_created += 1
            else:
                products_updated += 1

            if gw_retailer:
                _, p_created = CurrentPrice.objects.update_or_create(
                    product=product,
                    retailer=gw_retailer,
                    defaults={
                        'price': msrp,
                        'url': gw_url,
                        'in_stock': True,
                        'not_available': False,
                        'listing_title': name,
                    },
                )
                if p_created:
                    prices_created += 1
                else:
                    prices_updated += 1

        self.stdout.write(self.style.SUCCESS(
            f'\npopulate_sm_armageddon_box_products complete.\n'
            f'  Products: {products_created} created, {products_updated} updated.\n'
            f'  GW prices: {prices_created} created, {prices_updated} updated.'
        ))
