"""
Management command: seed_mm_disciples_of_tzeentch_prices

Seeds Miniature Market CurrentPrice records for Disciples of Tzeentch products
(DOT-001 to DOT-012) from the AOS Disciples of Tzeentch - GW, NK, MM.xlsx (2026-06-24).

4 of 12 products have confirmed MM URLs.
No MM entries for: DOT-001, DOT-003, DOT-004, DOT-005, DOT-006,
DOT-007, DOT-008, DOT-011.

Uses create_defaults for price and in_stock so scraper-set values survive
Railway redeploys.

Usage:
    python manage.py seed_mm_disciples_of_tzeentch_prices
"""

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Product, Retailer

_MM = 'https://www.miniaturemarket.com'

# (slug, listing_title, price, url, in_stock, not_available)
MM_PRICES = [
    (
        'curseling-eye-of-tzeentch',
        'Curseling, Eye of Tzeentch',
        None,
        f'{_MM}/gw-83-68-2022.html',
        True,
        False,
    ),
    (
        'fatemaster',
        'Fatemaster',
        None,
        f'{_MM}/Warhammer-Age-of-Sigmar-Disciples-of-Tzeentch-Fatemaster/GW-83-111-2026',
        True,
        False,
    ),
    (
        'argent-shards',
        'Argent Shards',
        None,
        f'{_MM}/Warhammer-Age-of-Sigmar-Disciples-of-Tzeentch-Argent-Shards/GW-83-107-2026',
        True,
        False,
    ),
    (
        'chaos-battletome-disciples-of-tzeentch',
        'Chaos Battletome: Disciples of Tzeentch',
        None,
        f'{_MM}/Warhammer-Age-of-Sigmar-Chaos-Battletome-Disciples-of-Tzeentch/GW-83-45-2026',
        True,
        False,
    ),
]


class Command(BaseCommand):
    """Seed Miniature Market prices for Disciples of Tzeentch (4 of 12 have MM URLs)."""

    help = 'Seeds MM CurrentPrice records for DOT-001 to DOT-012 (4 products have MM URLs).'

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
            f'seed_mm_disciples_of_tzeentch_prices complete. '
            f'MM prices: {created_count} created, {updated_count} updated.'
        ))
