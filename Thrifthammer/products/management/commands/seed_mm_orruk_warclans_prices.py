"""
Management command: seed_mm_orruk_warclans_prices

Seeds Miniature Market CurrentPrice records for Orruk Warclans products
(OW-001 to OW-029) from the AOS - Orruk Warclans - GW, NK, MM.xlsx (2026-06-18).

23 of 29 products have confirmed MM URLs.
No MM entries for: OW-005 Swampcalla Shaman with Pot-grot, OW-006 Killaboss
with Stab-grot, OW-015 Gore-gruntas, OW-016 Warchanter, OW-017 Megaboss,
OW-018 Monsta Killaz.

Dual-kit notes:
  - OW-007 Killaboss on Corpse-rippa Vulcha and OW-009 Gobsprakk share one MM
    listing (gw-89-73).
  - OW-008 Snatchaboss on Sludgeraker Beast and OW-011 Swampboss Skumdrekk
    share one MM listing (gw-89-69).
  - OW-013 Gordrakk, the Fist of Gork and OW-014 Megaboss on Maw-krusha
    share one MM listing (gw-89-25).
  - OW-019 Brute Ragerz and OW-020 Weirdbrute Wrekkaz share one MM listing
    (gw-89-82).
  - OW-027 Maw-grunta Gouger, OW-028 Maw-grunta with Hakkin' Krew, and
    OW-029 Tuskboss on Maw-grunta share one MM listing (gw-89-81).

Uses create_defaults for price and in_stock so scraper-set values survive
Railway redeploys.

Usage:
    python manage.py seed_mm_orruk_warclans_prices
"""

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Product, Retailer

_MM = 'https://www.miniaturemarket.com'

# (slug, listing_title, price, url, in_stock, not_available)
# price=None  -> scraper will populate on first run
# in_stock    -> initial assumption; scraper corrects as needed
MM_PRICES = [

    # -- Terrain / Scenery -----------------------------------------------------
    (
        'bossrokk-tower',
        'Orruk Warclans Bossrokk Tower',
        None,
        f'{_MM}/warhammer-age-sigmar-orruk-warclans-bossrokk-tower-gw-89-97.html',
        True,
        False,
    ),

    # -- Manifestations --------------------------------------------------------
    (
        'orruk-warclans-manifestations',
        'Orruk Warclans Manifestations',
        None,
        f'{_MM}/warhammer-age-sigmar-orruk-warclans-manifestations-gw-89-96.html',
        True,
        False,
    ),

    # -- Heroes ----------------------------------------------------------------
    (
        'hobgrot-slittaboss',
        'Orruk Warclans Hobgrot Slittaboss',
        None,
        f'{_MM}/warhammer-age-sigmar-orruk-warclans-hobgrot-slittaboss-gw-89-95.html',
        True,
        False,
    ),
    # ⚠ Dual kit: Killaboss on Corpse-rippa Vulcha and Gobsprakk, The Mouth of
    #   Mork share one MM listing.
    (
        'killaboss-on-corpse-rippa-vulcha',
        'Killaboss on Corpse-rippa Vulcha',
        None,
        f'{_MM}/gw-89-73.html',
        True,
        False,
    ),
    (
        'gobsprakk-the-mouth-of-mork',
        'Killaboss on Corpse-rippa Vulcha',
        None,
        f'{_MM}/gw-89-73.html',
        True,
        False,
    ),
    (
        'marshcrawla-sloggoth',
        'Marshcrawla Sloggoth',
        None,
        f'{_MM}/gw-89-66.html',
        True,
        False,
    ),
    # ⚠ Dual kit: Gordrakk, the Fist of Gork and Megaboss on Maw-krusha share
    #   one MM listing.
    (
        'gordrakk-the-fist-of-gork',
        'Gordrakk Fist of Gork / Orruk Maw-Krusha',
        None,
        f'{_MM}/gw-89-25.html',
        True,
        False,
    ),
    (
        'megaboss-on-maw-krusha',
        'Gordrakk Fist of Gork / Orruk Maw-Krusha',
        None,
        f'{_MM}/gw-89-25.html',
        True,
        False,
    ),
    (
        'breaka-boss-on-mirebrute-troggoth',
        'Orruk Warclans Breaka-boss on Mirebrute Troggoth',
        None,
        f'{_MM}/gw-89-68.html',
        True,
        False,
    ),
    (
        'zoggrok-anvilsmasha',
        'Orruk Warclans Zoggrok Anvilsmasha',
        None,
        f'{_MM}/warhammer-age-of-sigmar-orruk-warclans-zoggrok-anvilsmasha-gw-89-62.html',
        True,
        False,
    ),
    (
        'ardboy-big-boss',
        'Ironjawz Ardboy Big Boss',
        None,
        f'{_MM}/warhammer-age-of-sigmar-ironjawz-ardboy-big-boss-gw-89-57.html',
        True,
        False,
    ),
    (
        'weirdnob-shaman',
        'Orruk Weirdnob Shaman',
        None,
        f'{_MM}/gw-89-27.html',
        True,
        False,
    ),
    # ⚠ Dual kit: Snatchaboss on Sludgeraker Beast and Swampboss Skumdrekk
    #   share one MM listing.
    (
        'snatchaboss-on-sludgeraker-beast',
        'Snatchaboss on Sludgeraker Beast',
        None,
        f'{_MM}/gw-89-69.html',
        True,
        False,
    ),
    (
        'swampboss-skumdrekk',
        'Snatchaboss on Sludgeraker Beast',
        None,
        f'{_MM}/gw-89-69.html',
        True,
        False,
    ),

    # -- Units -----------------------------------------------------------------
    (
        'hobgrot-slittaz',
        'Hobgrot Slittaz',
        None,
        f'{_MM}/gw-89-74.html',
        True,
        False,
    ),
    (
        'beast-skewer-killbow',
        'Beast-skewer Killbow',
        None,
        f'{_MM}/gw-89-60.html',
        True,
        False,
    ),
    # ⚠ Dual kit: Brute Ragerz and Weirdbrute Wrekkaz share one MM listing.
    (
        'brute-ragerz',
        'Orruk Warclans Weirdbrute Wrekkaz',
        None,
        f'{_MM}/warhammer-age-of-sigmar-orruk-warclans-weirdbrute-wrekkaz-gw-89-82.html',
        True,
        False,
    ),
    (
        'weirdbrute-wrekkaz',
        'Orruk Warclans Weirdbrute Wrekkaz',
        None,
        f'{_MM}/warhammer-age-of-sigmar-orruk-warclans-weirdbrute-wrekkaz-gw-89-82.html',
        True,
        False,
    ),
    (
        'man-skewer-boltboyz',
        'Man-Skewer Boltboyz',
        None,
        f'{_MM}/gw-89-67.html',
        True,
        False,
    ),
    # ⚠ Dual kit: Maw-grunta Gouger, Maw-grunta with Hakkin' Krew, and
    #   Tuskboss on Maw-grunta share one MM listing.
    (
        'maw-grunta-gouger',
        'Orruk Warclans Tuskboss on Maw-grunta',
        None,
        f'{_MM}/warhammer-age-sigmar-orruk-warclans-tuskboss-on-maw-grunta-gw-89-81.html',
        True,
        False,
    ),
    (
        'maw-grunta-with-hakkin-krew',
        'Orruk Warclans Tuskboss on Maw-grunta',
        None,
        f'{_MM}/warhammer-age-sigmar-orruk-warclans-tuskboss-on-maw-grunta-gw-89-81.html',
        True,
        False,
    ),
    (
        'tuskboss-on-maw-grunta',
        'Orruk Warclans Tuskboss on Maw-grunta',
        None,
        f'{_MM}/warhammer-age-sigmar-orruk-warclans-tuskboss-on-maw-grunta-gw-89-81.html',
        True,
        False,
    ),

    # -- Battletome ------------------------------------------------------------
    (
        'destruction-battletome-orruk-warclans',
        'Destruction Battletome: Orruk Warclans 4th Edition',
        None,
        f'{_MM}/warhammer-age-sigmar-destruction-battletome-orruk-warclans-4th-edition-gw-89-01-2025.html',
        True,
        False,
    ),
]


class Command(BaseCommand):
    """Seed Miniature Market prices for Orruk Warclans (23 of 29 products have MM URLs)."""

    help = 'Seeds MM CurrentPrice records for OW-001 to OW-029 (23 products have MM URLs).'

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
            f'seed_mm_orruk_warclans_prices complete. '
            f'MM prices: {created_count} created, {updated_count} updated.'
        ))
