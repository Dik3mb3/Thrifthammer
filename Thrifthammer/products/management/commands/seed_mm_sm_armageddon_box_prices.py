"""
Management command: seed_mm_sm_armageddon_box_prices

Seeds Miniature Market CurrentPrice record for the Armageddon Box (SM-001).
Confirmed MM URL sourced 2026-06-24.

Uses create_defaults for price and in_stock so scraper-set values survive
Railway redeploys.

Usage:
    python manage.py seed_mm_sm_armageddon_box_prices
"""

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Product, Retailer

# (slug, listing_title, price, url, in_stock, not_available)
MM_PRICES = [
    (
        'warhammer-40000-armageddon-box',
        'Warhammer 40,000: Armageddon Box',
        None,
        'https://www.miniaturemarket.com/Warhammer-40K-Armageddon-New-Arrival/GW-40-01-2026',
        True,
        False,
    ),
]


class Command(BaseCommand):
    """Seed Miniature Market price for SM-001 Armageddon Box."""

    help = 'Seeds MM CurrentPrice record for SM-001 Warhammer 40,000: Armageddon Box.'

    def handle(self, *args, **options):
        """Run the command."""
        mm = Retailer.objects.filter(name='Miniature Market').first()
        if not mm:
            self.stderr.write(self.style.ERROR('Miniature Market retailer not found.'))
            return

        created_count = 0
        updated_count = 0

        for (slug, listing_title, price, url, in_stock, not_available) in MM_PRICES:
            try:
                product = Product.objects.get(slug=slug)
            except Product.DoesNotExist:
                self.stderr.write(self.style.WARNING(
                    f'  Product not found: {slug} -- skipping'
                ))
                continue

            _, created = CurrentPrice.objects.update_or_create(
                product=product,
                retailer=mm,
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
            f'seed_mm_sm_armageddon_box_prices complete. '
            f'MM prices: {created_count} created, {updated_count} updated.'
        ))
