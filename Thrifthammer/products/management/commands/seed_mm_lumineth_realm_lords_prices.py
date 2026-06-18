"""
Management command: seed_mm_lumineth_realm_lords_prices

Seeds Miniature Market CurrentPrice records for Lumineth Realm-lords products
(LRL-001 to LRL-026) from the AOS Lumineth Realm Lords - GW, NK, MM.xlsx (2026-06-17).

9 of 26 products have confirmed MM URLs.
No MM entries for: LRL-001, LRL-002, LRL-003, LRL-004, LRL-005, LRL-006,
LRL-009, LRL-010, LRL-012, LRL-013, LRL-015, LRL-017, LRL-018, LRL-020,
LRL-022, LRL-023, LRL-025.

Dual-kit notes:
  - LRL-007 Hurakan Spirit of the Wind and LRL-016 Sevireth share one MM listing
    (gw-87-22).

Uses create_defaults for price and in_stock so scraper-set values survive
Railway redeploys.

Usage:
    python manage.py seed_mm_lumineth_realm_lords_prices
"""

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Product, Retailer

_MM = 'https://www.miniaturemarket.com'

# (slug, listing_title, price, url, in_stock, not_available)
# price=None  -> scraper will populate on first run
# in_stock    -> initial assumption; scraper corrects as needed
MM_PRICES = [

    # -- Heroes ----------------------------------------------------------------
    (
        'scinari-enlightener',
        'Scinari Enlightener',
        None,
        f'{_MM}/gw-87-16.html',
        True,
        False,
    ),
    (
        'vanari-lord-regent',
        'Vanari Lord Regent',
        None,
        f'{_MM}/Warhammer-Age-of-Sigmar-Lumineth-Realmlords-Vanari-Lord-Regent/GW-87-66-2026',
        True,
        False,
    ),

    # -- Units -----------------------------------------------------------------
    # ⚠ Dual kit: Hurakan Spirit of the Wind and Sevireth share one MM listing.
    (
        'hurakan-spirit-of-the-wind',
        'Sevireth / Hurakan Spirit of the Wind',
        None,
        f'{_MM}/gw-87-22.html',
        True,
        False,
    ),
    (
        'sevireth-lord-of-the-seventh-wind',
        'Sevireth / Hurakan Spirit of the Wind',
        None,
        f'{_MM}/gw-87-22.html',
        True,
        False,
    ),
    (
        'hurakan-windchargers',
        'Hurakan Windchargers',
        None,
        f'{_MM}/gw-87-21.html',
        True,
        False,
    ),
    (
        'vanari-auralan-sentinels',
        'Vanari Auralan Sentinels',
        None,
        f'{_MM}/gw-87-58.html',
        True,
        False,
    ),
    (
        'vanari-bladelords',
        'Vanari Bladelords',
        None,
        f'{_MM}/gw-87-23.html',
        True,
        False,
    ),

    # -- Warcry ----------------------------------------------------------------
    (
        'warcry-ydrilan-riverblades',
        'Warcry: Ydrilan Riverblades',
        None,
        f'{_MM}/warcry-ydrilan-riverblades-gw-112-13.html',
        True,
        False,
    ),

    # -- Battletome ------------------------------------------------------------
    (
        'order-battletome-lumineth-realm-lords',
        'Order Battletome: Lumineth Realm-lords',
        None,
        f'{_MM}/Warhammer-Age-of-Sigmar-Order-Battletome-Lumineth-Realmlords/GW-87-04-2026',
        True,
        False,
    ),
]


class Command(BaseCommand):
    """Seed Miniature Market prices for Lumineth Realm-lords (9 of 26 products have MM URLs)."""

    help = 'Seeds MM CurrentPrice records for LRL-001 to LRL-026 (9 products have MM URLs).'

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
            f'seed_mm_lumineth_realm_lords_prices complete. '
            f'MM prices: {created_count} created, {updated_count} updated.'
        ))
