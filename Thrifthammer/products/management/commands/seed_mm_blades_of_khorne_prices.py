"""
Management command: seed_mm_blades_of_khorne_prices

Seeds Miniature Market CurrentPrice records for Blades of Khorne products
(BOK-001 to BOK-012) from the AOS Blades of Khorne - GW, NK, MM.xlsx (2026-06-24).

4 of 12 products have confirmed MM URLs.
No MM entries for: BOK-002, BOK-003, BOK-004, BOK-005, BOK-007,
BOK-008, BOK-010, BOK-012.

Uses create_defaults for price and in_stock so scraper-set values survive
Railway redeploys.

Usage:
    python manage.py seed_mm_blades_of_khorne_prices
"""

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Product, Retailer

_MM = 'https://www.miniaturemarket.com'

# (slug, listing_title, price, url, in_stock, not_available)
MM_PRICES = [
    (
        'realmgore-ritualist',
        'Realmgore Ritualist',
        None,
        f'{_MM}/warhammer-age-of-sigmar-blades-of-khorne-realmgore-ritualist-gw-83-22-2023.html',
        True,
        False,
    ),
    (
        'blood-warriors',
        'Blood Warriors',
        None,
        f'{_MM}/gw-83-24.html',
        True,
        False,
    ),
    (
        'claws-of-karanak',
        'Claws of Karanak',
        None,
        f'{_MM}/warcry-claws-of-karanak-gw-112-03.html',
        True,
        False,
    ),
    (
        'chaos-battletome-blades-of-khorne',
        'Chaos Battletome: Blades of Khorne',
        None,
        f'{_MM}/warhammer-age-sigmar-chaos-battletome-blades-khorne-gw-83-01.html',
        True,
        False,
    ),
]


class Command(BaseCommand):
    """Seed Miniature Market prices for Blades of Khorne (4 of 12 products have MM URLs)."""

    help = 'Seeds MM CurrentPrice records for BOK-001 to BOK-012 (4 products have MM URLs).'

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
            f'seed_mm_blades_of_khorne_prices complete. '
            f'MM prices: {created_count} created, {updated_count} updated.'
        ))
