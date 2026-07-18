"""
Management command: seed_mm_trench_crusade_prices

Seeds Miniature Market CurrentPrice records for Trench Crusade products.

All 4 products have a confirmed Miniature Market URL.

Usage:
    python manage.py seed_mm_trench_crusade_prices
"""

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Product, Retailer

# (slug, listing_title, price, url, in_stock, not_available)
MM_PRICES = [
    ('trench-crusade-carcass-front', 'Trench Crusade: Carcass Front Narrative Campaign Box (Preorder)', None, 'https://www.miniaturemarket.com/Trench-Crusade-Carcass-Front-Narrative-Campaign-Box-Preorder/ASTCNC0001', False, False),
    ('prussian-stosstruppen-warband', 'Trench Crusade: Prussian Stosstruppen Warband', None, 'https://www.miniaturemarket.com/Trench-Crusade-Prussian-Stosstruppen-Warband/ACHTCPM2012', False, False),
    ('prussian-stosstruppen', 'Trench Crusade: Prussian Stosstruppen', None, 'https://www.miniaturemarket.com/Trench-Crusade-Prussian-Stosstruppen/ASTCPM2015', False, False),
    ('new-antioch-sniper-priests', 'Trench Crusade: Sniper Priests', None, 'https://www.miniaturemarket.com/Trench-Crusade-Sniper-Priests/ASTCPM2019', False, False),
]


class Command(BaseCommand):
    """Seed Miniature Market prices for Trench Crusade products (idempotent)."""

    help = 'Seeds Miniature Market CurrentPrice records for Trench Crusade products.'

    def handle(self, *args, **options):
        if not MM_PRICES:
            self.stdout.write(self.style.WARNING('MM_PRICES is empty -- nothing to seed.'))
            return

        retailer = Retailer.objects.get(slug='miniature-market')

        created = 0
        updated = 0

        for slug, listing_title, price, url, in_stock, not_available in MM_PRICES:
            try:
                product = Product.objects.get(slug=slug)
            except Product.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'Product not found for slug: {slug}'))
                continue

            _, price_created = CurrentPrice.objects.update_or_create(
                product=product,
                retailer=retailer,
                create_defaults={
                    'price': price,
                    'in_stock': in_stock,
                },
                defaults={
                    'url': url,
                    'listing_title': listing_title,
                    'not_available': not_available,
                },
            )
            if price_created:
                created += 1
            else:
                updated += 1

        self.stdout.write(self.style.SUCCESS(
            f'Miniature Market prices: {created} created, {updated} updated.'
        ))
