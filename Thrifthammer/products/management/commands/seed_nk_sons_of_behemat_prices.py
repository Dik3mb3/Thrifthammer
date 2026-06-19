"""
Management command: seed_nk_sons_of_behemat_prices

Seeds Noble Knight CurrentPrice records for Sons of Behemat products
(SON-001 to SON-006) from the AOS Sons of Behemat - GW, NK, MM.xlsx (2026-06-18).

All 6 products have confirmed NK URLs.

Dual-kit notes:
  - SON-001 Kraken-eater Mega-Gargant, SON-002 Warstomper Mega-Gargant,
    SON-003 King Brodd, SON-004 Gatebreaker Mega-Gargant, and
    SON-005 Beast-smasher Mega-Gargant all share one NK listing (King Brodd).

Affiliate tag ?awid=1576 appended to all NK URLs.
Uses create_defaults for price and in_stock so scraper-set values survive
Railway redeploys.

Usage:
    python manage.py seed_nk_sons_of_behemat_prices
"""

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Product, Retailer

_NK = 'https://www.nobleknight.com'
_AFF = '?awid=1576'

# (slug, listing_title, price, url, in_stock, not_available)
# price=None  -> scraper will populate on first run
# in_stock    -> initial assumption; scraper corrects as needed
NK_PRICES = [

    # ⚠ Dual kit: Kraken-eater, Warstomper, King Brodd, Gatebreaker, and
    #   Beast-smasher Mega-Gargants all share one NK listing.
    (
        'kraken-eater-mega-gargant',
        'King Brodd',
        None,
        f'{_NK}/P/2148008243/King-Brodd{_AFF}',
        True,
        False,
    ),
    (
        'warstomper-mega-gargant',
        'King Brodd',
        None,
        f'{_NK}/P/2148008243/King-Brodd{_AFF}',
        True,
        False,
    ),
    (
        'king-brodd',
        'King Brodd',
        None,
        f'{_NK}/P/2148008243/King-Brodd{_AFF}',
        True,
        False,
    ),
    (
        'gatebreaker-mega-gargant',
        'King Brodd',
        None,
        f'{_NK}/P/2148008243/King-Brodd{_AFF}',
        True,
        False,
    ),
    (
        'beast-smasher-mega-gargant',
        'King Brodd',
        None,
        f'{_NK}/P/2148008243/King-Brodd{_AFF}',
        True,
        False,
    ),

    # -- Units -----------------------------------------------------------------
    (
        'mancrusher-gargant',
        'Mancrusher Gargants',
        None,
        f'{_NK}/P/2147871315/Mancrusher-Gargants{_AFF}',
        True,
        False,
    ),
]


class Command(BaseCommand):
    """Seed Noble Knight prices for Sons of Behemat (all 6 products have NK URLs)."""

    help = 'Seeds NK CurrentPrice records for SON-001 to SON-006 (6 products have NK URLs).'

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
            f'seed_nk_sons_of_behemat_prices complete. '
            f'NK prices: {created_count} created, {updated_count} updated.'
        ))
