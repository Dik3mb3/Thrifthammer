"""
Management command: seed_mm_ogor_mawtribes_prices

Seeds Miniature Market CurrentPrice records for Ogor Mawtribes products
(OM-001 to OM-026) from the AOS Ogor Mawtribes - GW, NK, MM.xlsx (2026-06-18).

Only 3 of 26 products have confirmed MM URLs:
  - OM-001 Spearhead: Ogor Mawtribes – Scrapglutt
  - OM-004 Bloodpelt Hunter
  - OM-025 Ironguts

Uses create_defaults for price and in_stock so scraper-set values survive
Railway redeploys.

Usage:
    python manage.py seed_mm_ogor_mawtribes_prices
"""

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Product, Retailer

_MM = 'https://www.miniaturemarket.com'

# (slug, listing_title, price, url, in_stock, not_available)
# price=None  -> scraper will populate on first run
# in_stock    -> initial assumption; scraper corrects as needed
MM_PRICES = [

    (
        'spearhead-ogor-mawtribes-scrapglutt',
        'Ogor Mawtribes Spearhead Scrapglutt',
        None,
        f'{_MM}/warhammer-age-sigmar-spearhead-ogor-mawtribes-scrapglutt-gw-70-952.html',
        True,
        False,
    ),
    (
        'bloodpelt-hunter',
        'Ogor Mawtribes Bloodpelt Hunter',
        None,
        f'{_MM}/gw-95-21.html',
        True,
        False,
    ),
    (
        'ironguts',
        'Ogor Mawtribes Ironguts',
        None,
        f'{_MM}/age-sigmar-ogor-mawtribes-ironguts-gw-95-09.html',
        True,
        False,
    ),
]


class Command(BaseCommand):
    """Seed Miniature Market prices for Ogor Mawtribes (3 of 26 products have MM URLs)."""

    help = 'Seeds MM CurrentPrice records for OM-001 to OM-026 (3 products have MM URLs).'

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
            f'seed_mm_ogor_mawtribes_prices complete. '
            f'MM prices: {created_count} created, {updated_count} updated.'
        ))
