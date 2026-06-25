"""
Management command: seed_nk_sm_armageddon_box_prices

Seeds Noble Knight CurrentPrice record for the Armageddon Box (SM-001).
Confirmed NK URL sourced 2026-06-24.

Affiliate tag ?awid=1576 appended.
Uses create_defaults for price and in_stock so scraper-set values survive
Railway redeploys.

Usage:
    python manage.py seed_nk_sm_armageddon_box_prices
"""

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Product, Retailer

_NK = 'https://www.nobleknight.com'
_AFF = '?awid=1576'

# (slug, listing_title, price, url, in_stock, not_available)
NK_PRICES = [
    (
        'warhammer-40000-armageddon-box',
        'Warhammer 40,000: Armageddon Core Set',
        None,
        f'{_NK}/P/2148474111/Warhammer-40000---Armageddon-Core-Set{_AFF}',
        True,
        False,
    ),
]


class Command(BaseCommand):
    """Seed Noble Knight price for SM-001 Armageddon Box."""

    help = 'Seeds NK CurrentPrice record for SM-001 Warhammer 40,000: Armageddon Box.'

    def handle(self, *args, **options):
        """Run the command."""
        nk = Retailer.objects.filter(name='Noble Knight Games').first()
        if not nk:
            self.stderr.write(self.style.ERROR('Noble Knight Games retailer not found.'))
            return

        created_count = 0
        updated_count = 0

        for (slug, listing_title, price, url, in_stock, not_available) in NK_PRICES:
            try:
                product = Product.objects.get(slug=slug)
            except Product.DoesNotExist:
                self.stderr.write(self.style.WARNING(
                    f'  Product not found: {slug} -- skipping'
                ))
                continue

            _, created = CurrentPrice.objects.update_or_create(
                product=product,
                retailer=nk,
                defaults={
                    'url': url,
                    'listing_title': listing_title,
                    'not_available': not_available,
                },
                create_defaults={
                    'price': price,
                    'in_stock': in_stock,
                },
            )
            if created:
                created_count += 1
            else:
                updated_count += 1

        self.stdout.write(self.style.SUCCESS(
            f'seed_nk_sm_armageddon_box_prices complete. '
            f'NK prices: {created_count} created, {updated_count} updated.'
        ))
