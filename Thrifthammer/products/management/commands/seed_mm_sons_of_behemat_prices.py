"""
Management command: seed_mm_sons_of_behemat_prices

Seeds Miniature Market CurrentPrice records for Sons of Behemat products
(SON-001 to SON-006) from the AOS Sons of Behemat - GW, NK, MM.xlsx (2026-06-18).

5 of 6 products have confirmed MM URLs.
No MM entry for: SON-006 Mancrusher Gargant.

Dual-kit notes:
  - SON-001 Kraken-eater Mega-Gargant, SON-002 Warstomper Mega-Gargant,
    SON-003 King Brodd, SON-004 Gatebreaker Mega-Gargant, and
    SON-005 Beast-smasher Mega-Gargant all share one MM listing (gw-93-10).

Uses create_defaults for price and in_stock so scraper-set values survive
Railway redeploys.

Usage:
    python manage.py seed_mm_sons_of_behemat_prices
"""

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Product, Retailer

_MM = 'https://www.miniaturemarket.com'

# (slug, listing_title, price, url, in_stock, not_available)
# price=None  -> scraper will populate on first run
# in_stock    -> initial assumption; scraper corrects as needed
MM_PRICES = [

    # ⚠ Dual kit: Kraken-eater, Warstomper, King Brodd, Gatebreaker, and
    #   Beast-smasher Mega-Gargants all share one MM listing.
    (
        'kraken-eater-mega-gargant',
        'Sons of Behemat King Brodd / Mega-Gargant',
        None,
        f'{_MM}/gw-93-10.html',
        True,
        False,
    ),
    (
        'warstomper-mega-gargant',
        'Sons of Behemat King Brodd / Mega-Gargant',
        None,
        f'{_MM}/gw-93-10.html',
        True,
        False,
    ),
    (
        'king-brodd',
        'Sons of Behemat King Brodd / Mega-Gargant',
        None,
        f'{_MM}/gw-93-10.html',
        True,
        False,
    ),
    (
        'gatebreaker-mega-gargant',
        'Sons of Behemat King Brodd / Mega-Gargant',
        None,
        f'{_MM}/gw-93-10.html',
        True,
        False,
    ),
    (
        'beast-smasher-mega-gargant',
        'Sons of Behemat King Brodd / Mega-Gargant',
        None,
        f'{_MM}/gw-93-10.html',
        True,
        False,
    ),
]


class Command(BaseCommand):
    """Seed Miniature Market prices for Sons of Behemat (5 of 6 products have MM URLs)."""

    help = 'Seeds MM CurrentPrice records for SON-001 to SON-006 (5 products have MM URLs).'

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
            f'seed_mm_sons_of_behemat_prices complete. '
            f'MM prices: {created_count} created, {updated_count} updated.'
        ))
