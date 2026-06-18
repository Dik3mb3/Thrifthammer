"""
Management command: seed_nk_fyreslayers_prices

Seeds Noble Knight CurrentPrice records for Fyreslayers products
(FYR-001 to FYR-016) from the AOS Fyreslayers - GW, NK, MM.xlsx (2026-06-17).

13 of 16 products have confirmed NK URLs.
No NK entries for: FYR-004 Gotrek Gurnisson, FYR-011 Auric Runemaster
(Excel NK URL pointed to Magmadroth -- data error, omitted).

Dual-kit / triple-kit notes:
  - FYR-003 Auric Runesmiter, FYR-015 Auric Runeson, and FYR-016 Auric Runefather
    all share one NK listing (Auric Runefather on Magmadroth).
  - FYR-008 Hearthguard Berzerkers and FYR-009 Auric Hearthguard share one NK listing.

Affiliate tag ?awid=1576 appended to all NK URLs.
Uses create_defaults for price and in_stock so scraper-set values survive
Railway redeploys.

Usage:
    python manage.py seed_nk_fyreslayers_prices
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

    # -- Spearhead -------------------------------------------------------------
    (
        'spearhead-fyreslayers',
        'Vanguard - Fyreslayers',
        None,
        f'{_NK}/P/2147977401/Vanguard---Fyreslayers{_AFF}',
        True,
        False,
    ),

    # -- Heroes ----------------------------------------------------------------
    (
        'auric-flamekeeper',
        'Auric Flamekeeper',
        None,
        f'{_NK}/P/2147986343/Auric-Flamekeeper{_AFF}',
        True,
        False,
    ),
    (
        'doomseeker',
        'Doomseeker',
        None,
        f'{_NK}/P/2147647990/Doomseeker{_AFF}',
        True,
        False,
    ),
    (
        'grimwrath-berzerker',
        'Grimwrath Berserker',
        None,
        f'{_NK}/P/2147614159/Grimwrath-Berserker{_AFF}',
        True,
        False,
    ),
    (
        'grimhold-exile',
        'Grimhold Exile Webstore Edition',
        None,
        f'{_NK}/P/2148217644/Grimhold-Exile-Webstore-Edition{_AFF}',
        True,
        False,
    ),

    # -- Units -----------------------------------------------------------------
    # ⚠ Dual kit: Hearthguard Berzerkers and Auric Hearthguard share one NK listing.
    (
        'hearthguard-berzerkers',
        'Hearthguard',
        None,
        f'{_NK}/P/2147612296/Hearthguard{_AFF}',
        True,
        False,
    ),
    (
        'auric-hearthguard',
        'Hearthguard',
        None,
        f'{_NK}/P/2147612296/Hearthguard{_AFF}',
        True,
        False,
    ),
    (
        'vulkite-berzerkers',
        'Vulkite Berzerkers',
        None,
        f'{_NK}/P/2147612297/Vulkite-Berzerkers{_AFF}',
        True,
        False,
    ),
    (
        'vulkyn-flameseekers',
        'Vulkyn Flameseekers',
        None,
        f'{_NK}/P/2148087843/Vulkyn-Flameseekers{_AFF}',
        True,
        False,
    ),

    # -- Large Kits / Monsters -------------------------------------------------
    # ⚠ Triple kit: Auric Runesmiter, Auric Runeson, and Auric Runefather all
    #   share one NK listing (Auric Runefather on Magmadroth).
    (
        'auric-runesmiter-on-magmadroth',
        'Auric Runefather on Magmadroth',
        None,
        f'{_NK}/P/2147977400/Auric-Runefather-on-Magmadroth{_AFF}',
        True,
        False,
    ),
    (
        'auric-runeson-on-magmadroth',
        'Auric Runefather on Magmadroth',
        None,
        f'{_NK}/P/2147977400/Auric-Runefather-on-Magmadroth{_AFF}',
        True,
        False,
    ),
    (
        'auric-runefather-on-magmadroth',
        'Auric Runefather on Magmadroth',
        None,
        f'{_NK}/P/2147977400/Auric-Runefather-on-Magmadroth{_AFF}',
        True,
        False,
    ),

    # -- Terrain / Endless Spells ----------------------------------------------
    (
        'magmic-invocations',
        'Magmic Invocations',
        None,
        f'{_NK}/P/2147747956/Magmic-Invocations{_AFF}',
        True,
        False,
    ),
    (
        'magmic-battleforge',
        'Magmic Battleforge',
        None,
        f'{_NK}/P/2147747957/Magmic-Battleforge{_AFF}',
        True,
        False,
    ),
]


class Command(BaseCommand):
    """Seed Noble Knight prices for Fyreslayers (13 of 16 products have NK URLs)."""

    help = 'Seeds NK CurrentPrice records for FYR-001 to FYR-016 (13 products have NK URLs).'

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
            f'seed_nk_fyreslayers_prices complete. '
            f'NK prices: {created_count} created, {updated_count} updated.'
        ))
