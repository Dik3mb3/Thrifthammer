"""
Management command: seed_mm_fyreslayers_prices

Seeds Miniature Market CurrentPrice records for Fyreslayers products
(FYR-001 to FYR-016) from the AOS Fyreslayers - GW, NK, MM.xlsx (2026-06-17).

5 of 16 products have confirmed MM URLs.
No MM entries for: FYR-001 Spearhead: Fyreslayers, FYR-004 Gotrek Gurnisson,
FYR-005 Magmic Invocations, FYR-006 Doomseeker, FYR-007 Grimwrath Berzerker,
FYR-010 Vulkite Berzerkers, FYR-011 Auric Runemaster (Excel MM URL was a data
error pointing to the Magmadroth kit), FYR-012 Vulkyn Flameseekers,
FYR-013 Grimhold Exile, FYR-014 Magmic Battleforge.

Dual-kit / triple-kit notes:
  - FYR-002 Auric Flamekeeper shares MM listing with FYR-010 Auric Runemaster
    at gw-84-44 -- wait, Auric Flamekeeper is gw-84-44, Auric Runemaster is
    separate. Auric Flamekeeper MM URL is gw-84-44.html (correct).
  - FYR-003 Auric Runesmiter, FYR-015 Auric Runeson, and FYR-016 Auric Runefather
    all share one MM listing (gw-84-23-2022).
  - FYR-008 Hearthguard Berzerkers and FYR-009 Auric Hearthguard share one MM listing
    (gw-84-24).

Uses create_defaults for price and in_stock so scraper-set values survive
Railway redeploys.

Usage:
    python manage.py seed_mm_fyreslayers_prices
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
        'auric-flamekeeper',
        'Auric Flamekeeper',
        None,
        f'{_MM}/gw-84-44.html',
        True,
        False,
    ),

    # -- Units -----------------------------------------------------------------
    # ⚠ Dual kit: Hearthguard Berzerkers and Auric Hearthguard share one MM listing.
    (
        'hearthguard-berzerkers',
        'Hearthguard Berzerkers / Auric Hearthguard',
        None,
        f'{_MM}/gw-84-24.html',
        True,
        False,
    ),
    (
        'auric-hearthguard',
        'Hearthguard Berzerkers / Auric Hearthguard',
        None,
        f'{_MM}/gw-84-24.html',
        True,
        False,
    ),

    # -- Large Kits / Monsters -------------------------------------------------
    # ⚠ Triple kit: Auric Runesmiter, Auric Runeson, and Auric Runefather all
    #   share one MM listing (gw-84-23-2022).
    (
        'auric-runesmiter-on-magmadroth',
        'Auric Runefather / Runesmiter / Runeson on Magmadroth',
        None,
        f'{_MM}/gw-84-23-2022.html',
        True,
        False,
    ),
    (
        'auric-runeson-on-magmadroth',
        'Auric Runefather / Runesmiter / Runeson on Magmadroth',
        None,
        f'{_MM}/gw-84-23-2022.html',
        True,
        False,
    ),
    (
        'auric-runefather-on-magmadroth',
        'Auric Runefather / Runesmiter / Runeson on Magmadroth',
        None,
        f'{_MM}/gw-84-23-2022.html',
        True,
        False,
    ),
]


class Command(BaseCommand):
    """Seed Miniature Market prices for Fyreslayers (6 of 16 products have MM URLs)."""

    help = 'Seeds MM CurrentPrice records for FYR-001 to FYR-016 (6 products have MM URLs).'

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
            f'seed_mm_fyreslayers_prices complete. '
            f'MM prices: {created_count} created, {updated_count} updated.'
        ))
