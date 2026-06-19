"""
Management command: seed_nk_orruk_warclans_prices

Seeds Noble Knight CurrentPrice records for Orruk Warclans products
(OW-001 to OW-029) from the AOS - Orruk Warclans - GW, NK, MM.xlsx (2026-06-18).

26 of 29 products have confirmed NK URLs.
No NK entries for: OW-004 Hobgrot Slittaboss, OW-005 Swampcalla Shaman with
Pot-grot, OW-006 Killaboss with Stab-grot.

Dual-kit notes:
  - OW-007 Killaboss on Corpse-rippa Vulcha and OW-009 Gobsprakk, The Mouth of
    Mork share one NK listing (Gobsprakk - The Mouth of Mork).
  - OW-008 Snatchaboss on Sludgeraker Beast and OW-011 Swampboss Skumdrekk
    share one NK listing (Swampboss Skumdrekk).
  - OW-013 Gordrakk, the Fist of Gork and OW-014 Megaboss on Maw-krusha
    share one NK listing (Gordrakk Fist of Gork / Orruk Maw-Krusha).
  - OW-019 Brute Ragerz and OW-020 Weirdbrute Wrekkaz share one NK listing
    (Weirdbrute Wrekkaz).
  - OW-027 Maw-grunta Gouger, OW-028 Maw-grunta with Hakkin' Krew, and
    OW-029 Tuskboss on Maw-grunta share one NK listing (Tuskboss on Maw-Grunta).

Affiliate tag ?awid=1576 appended to all NK URLs.
Uses create_defaults for price and in_stock so scraper-set values survive
Railway redeploys.

Usage:
    python manage.py seed_nk_orruk_warclans_prices
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

    # -- Terrain / Scenery -----------------------------------------------------
    (
        'bossrokk-tower',
        'Bossrokk Tower',
        None,
        f'{_NK}/P/2148304757/Bossrokk-Tower{_AFF}',
        True,
        False,
    ),

    # -- Manifestations --------------------------------------------------------
    (
        'orruk-warclans-manifestations',
        'Manifestations',
        None,
        f'{_NK}/P/2148304759/Manifestations{_AFF}',
        True,
        False,
    ),

    # -- Heroes ----------------------------------------------------------------
    # ⚠ Dual kit: Killaboss on Corpse-rippa Vulcha and Gobsprakk share one NK listing.
    (
        'killaboss-on-corpse-rippa-vulcha',
        'Gobsprakk - The Mouth of Mork',
        None,
        f'{_NK}/P/2147929448/Gobsprakk-The-Mouth-of-Mork{_AFF}',
        True,
        False,
    ),
    (
        'gobsprakk-the-mouth-of-mork',
        'Gobsprakk - The Mouth of Mork',
        None,
        f'{_NK}/P/2147929448/Gobsprakk-The-Mouth-of-Mork{_AFF}',
        True,
        False,
    ),
    (
        'marshcrawla-sloggoth',
        'Marshcrawla Sloggoth',
        None,
        f'{_NK}/P/2147929450/Marshcrawla-Sloggoth{_AFF}',
        True,
        False,
    ),
    # ⚠ Dual kit: Gordrakk, the Fist of Gork and Megaboss on Maw-krusha share one NK listing.
    (
        'gordrakk-the-fist-of-gork',
        'Gordrakk Fist of Gork / Orruk Maw-Krusha',
        None,
        f'{_NK}/P/2147937204/Gordrakk-Fist-of-Gork-Orruk-Maw-Krusha{_AFF}',
        True,
        False,
    ),
    (
        'megaboss-on-maw-krusha',
        'Gordrakk Fist of Gork / Orruk Maw-Krusha',
        None,
        f'{_NK}/P/2147937204/Gordrakk-Fist-of-Gork-Orruk-Maw-Krusha{_AFF}',
        True,
        False,
    ),
    (
        'breaka-boss-on-mirebrute-troggoth',
        'Breaka-Boss on Mirebrute Troggoth',
        None,
        f'{_NK}/P/2147926810/Breaka-Boss-on-Mirebrute-Troggoth{_AFF}',
        True,
        False,
    ),
    (
        'zoggrok-anvilsmasha',
        'Zoggrok Anvilsmasha',
        None,
        f'{_NK}/P/2148081624/Zoggrok-Anvilsmasha{_AFF}',
        True,
        False,
    ),
    (
        'ardboy-big-boss',
        'Ardboy Big Boss',
        None,
        f'{_NK}/P/2148081618/Ardboy-Big-Boss{_AFF}',
        True,
        False,
    ),
    (
        'weirdnob-shaman',
        'Orruk Weirdnob Shaman 2023 Edition',
        None,
        f'{_NK}/P/2148095430/Orruk-Weirdnob-Shaman-2023-Edition{_AFF}',
        True,
        False,
    ),
    (
        'warchanter',
        'Orruk Warchanter',
        None,
        f'{_NK}/P/2147624406/Orruk-Warchanter{_AFF}',
        True,
        False,
    ),
    (
        'megaboss',
        'Orruk Megaboss',
        None,
        f'{_NK}/P/2148003056/Orruk-Megaboss{_AFF}',
        True,
        False,
    ),
    # ⚠ Dual kit: Snatchaboss on Sludgeraker Beast and Swampboss Skumdrekk
    #   share one NK listing.
    (
        'snatchaboss-on-sludgeraker-beast',
        'Swampboss Skumdrekk',
        None,
        f'{_NK}/P/2147929451/Swampboss-Skumdrekk{_AFF}',
        True,
        False,
    ),
    (
        'swampboss-skumdrekk',
        'Swampboss Skumdrekk',
        None,
        f'{_NK}/P/2147929451/Swampboss-Skumdrekk{_AFF}',
        True,
        False,
    ),

    # -- Units -----------------------------------------------------------------
    (
        'hobgrot-slittaz',
        'Hobgrot Slittaz',
        None,
        f'{_NK}/P/2147934898/Hobgrot-Slittaz{_AFF}',
        True,
        False,
    ),
    (
        'beast-skewer-killbow',
        'Beast-Skewer Killbow',
        None,
        f'{_NK}/P/2147926813/Beast-Skewer-Killbow{_AFF}',
        True,
        False,
    ),
    (
        'gore-gruntas',
        'Orruk Gore Gruntas',
        None,
        f'{_NK}/P/2147624410/Orruk-Gore-Gruntas{_AFF}',
        True,
        False,
    ),
    (
        'monsta-killaz',
        'Kruleboyz Monsta Killaz',
        None,
        f'{_NK}/P/2148087839/Kruleboyz-Monsta-Killaz{_AFF}',
        True,
        False,
    ),
    # ⚠ Dual kit: Brute Ragerz and Weirdbrute Wrekkaz share one NK listing.
    (
        'brute-ragerz',
        'Weirdbrute Wrekkaz',
        None,
        f'{_NK}/P/2148081632/Weirdbrute-Wrekkaz{_AFF}',
        True,
        False,
    ),
    (
        'weirdbrute-wrekkaz',
        'Weirdbrute Wrekkaz',
        None,
        f'{_NK}/P/2148081632/Weirdbrute-Wrekkaz{_AFF}',
        True,
        False,
    ),
    (
        'man-skewer-boltboyz',
        'Man-Skewer Boltboyz',
        None,
        f'{_NK}/P/2147934897/Man-Skewer-Boltboyz{_AFF}',
        True,
        False,
    ),
    # ⚠ Dual kit: Maw-grunta Gouger, Maw-grunta with Hakkin' Krew, and
    #   Tuskboss on Maw-grunta share one NK listing.
    (
        'maw-grunta-gouger',
        'Tuskboss on Maw-Grunta',
        None,
        f'{_NK}/P/2148081637/Tuskboss-on-Maw-Grunta{_AFF}',
        True,
        False,
    ),
    (
        'maw-grunta-with-hakkin-krew',
        'Tuskboss on Maw-Grunta',
        None,
        f'{_NK}/P/2148081637/Tuskboss-on-Maw-Grunta{_AFF}',
        True,
        False,
    ),
    (
        'tuskboss-on-maw-grunta',
        'Tuskboss on Maw-Grunta',
        None,
        f'{_NK}/P/2148081637/Tuskboss-on-Maw-Grunta{_AFF}',
        True,
        False,
    ),

    # -- Battletome ------------------------------------------------------------
    (
        'destruction-battletome-orruk-warclans',
        'Destruction Battletome - Orruk Warclans 2024 Edition',
        None,
        f'{_NK}/P/2148304081/Destruction-Battletome---Orruk-Warclans-2024-Edition{_AFF}',
        True,
        False,
    ),
]


class Command(BaseCommand):
    """Seed Noble Knight prices for Orruk Warclans (26 of 29 products have NK URLs)."""

    help = 'Seeds NK CurrentPrice records for OW-001 to OW-029 (26 products have NK URLs).'

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
            f'seed_nk_orruk_warclans_prices complete. '
            f'NK prices: {created_count} created, {updated_count} updated.'
        ))
