"""
Management command: seed_nk_trench_crusade_prices

Seeds Noble Knight CurrentPrice records for Trench Crusade products.

3 of 4 products have a confirmed Noble Knight URL. Trench Crusade Carcass
Front has no NK listing yet and is intentionally left out, per the
"blank row = no entry" rule.

Affiliate tag ?awid=1576 appended to all NK URLs.

Usage:
    python manage.py seed_nk_trench_crusade_prices
"""

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Product, Retailer

_NK = 'https://www.nobleknight.com'
_AFF = '?awid=1576'

# (slug, listing_title, price, url, in_stock, not_available)
NK_PRICES = [
    ('prussian-stosstruppen-warband', 'Prussian Stosstruppen Warband', None, f'{_NK}/P/2148379081/Prussian-Stosstruppen-Warband{_AFF}', False, False),
    ('prussian-stosstruppen', 'Prussian Stosstruppen', None, f'{_NK}/P/2148432459/Prussian-Stosstruppen{_AFF}', False, False),
    ('new-antioch-sniper-priests', 'Sniper Priests', None, f'{_NK}/P/2148432464/Sniper-Priests{_AFF}', False, False),
]


class Command(BaseCommand):
    """Seed Noble Knight prices for Trench Crusade products (idempotent)."""

    help = 'Seeds Noble Knight CurrentPrice records for Trench Crusade products.'

    def handle(self, *args, **options):
        if not NK_PRICES:
            self.stdout.write(self.style.WARNING('NK_PRICES is empty -- nothing to seed.'))
            return

        retailer = Retailer.objects.get(slug='noble-knight-games')

        created = 0
        updated = 0

        for slug, listing_title, price, url, in_stock, not_available in NK_PRICES:
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
            f'Noble Knight prices: {created} created, {updated} updated.'
        ))
