"""
Management command: seed_nk_ogor_mawtribes_prices

Seeds Noble Knight CurrentPrice records for Ogor Mawtribes products
(OM-001 to OM-026) from the AOS Ogor Mawtribes - GW, NK, MM.xlsx (2026-06-18).

23 of 26 products have confirmed NK URLs.
No NK entries for: OM-014 Icefall Yhetees, OM-021 Leadbelchers,
OM-026 Firebelly.

Dual-kit notes:
  - OM-009 Thundertusk Beastriders, OM-010 Stonehorn Beastriders,
    OM-011 Huskard on Thundertusk, OM-012 Huskard on Stonehorn,
    OM-013 Frostlord on Thundertusk, OM-015 Frostlord on Stonehorn
    all share one NK listing (Stonehorn Beastriders 2022 Edition).

Affiliate tag ?awid=1576 appended to all NK URLs.
Uses create_defaults for price and in_stock so scraper-set values survive
Railway redeploys.

Usage:
    python manage.py seed_nk_ogor_mawtribes_prices
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
        'spearhead-ogor-mawtribes-scrapglutt',
        'Spearhead - Scrapglutt',
        None,
        f'{_NK}/P/2148312212/Spearhead---Scrapglutt{_AFF}',
        True,
        False,
    ),

    # -- Heroes ----------------------------------------------------------------
    (
        'tyrant',
        'Tyrant',
        None,
        f'{_NK}/P/2147794799/Tyrant{_AFF}',
        True,
        False,
    ),
    (
        'maneaters',
        'Maneaters Webstore Edition',
        None,
        f'{_NK}/P/2148014952/Maneaters-Webstore-Edition{_AFF}',
        True,
        False,
    ),
    (
        'bloodpelt-hunter',
        'Bloodpelt Hunter',
        None,
        f'{_NK}/P/2148014052/Bloodpelt-Hunter{_AFF}',
        True,
        False,
    ),
    (
        'slaughtermaster',
        'Slaughtermaster',
        None,
        f'{_NK}/P/2147848156/Slaughtermaster{_AFF}',
        True,
        False,
    ),
    (
        'butcher',
        'Butcher',
        None,
        f'{_NK}/P/2147915643/Butcher{_AFF}',
        True,
        False,
    ),
    (
        'icebrow-hunter',
        'Icebrow Hunter Webstore Edition',
        None,
        f'{_NK}/P/2148217579/Icebrow-Hunter-Webstore-Edition{_AFF}',
        True,
        False,
    ),

    # -- Units -----------------------------------------------------------------
    (
        'ogor-gluttons',
        'Ogor Gluttons',
        None,
        f'{_NK}/P/2148061149/Ogor-Gluttons{_AFF}',
        True,
        False,
    ),
    (
        'great-mawpot',
        'Great Mawpot',
        None,
        f'{_NK}/P/2147771423/Great-Mawpot{_AFF}',
        True,
        False,
    ),
    (
        'gnoblar-scraplauncher',
        'Gnoblar Scraplauncher',
        None,
        f'{_NK}/P/2147358106/Gnoblar-Scraplauncher{_AFF}',
        True,
        False,
    ),
    (
        'ironblaster',
        'Ironblaster',
        None,
        f'{_NK}/P/2147734437/Ironblaster{_AFF}',
        True,
        False,
    ),
    # ⚠ Dual kit: Thundertusk Beastriders, Stonehorn Beastriders, Huskard on
    #   Thundertusk, Huskard on Stonehorn, Frostlord on Thundertusk, and
    #   Frostlord on Stonehorn all share one NK listing.
    (
        'thundertusk-beastriders',
        'Stonehorn Beastriders 2022 Edition',
        None,
        f'{_NK}/P/2148476005/Stonehorn-Beastriders-2022-Edition{_AFF}',
        True,
        False,
    ),
    (
        'stonehorn-beastriders',
        'Stonehorn Beastriders 2022 Edition',
        None,
        f'{_NK}/P/2148476005/Stonehorn-Beastriders-2022-Edition{_AFF}',
        True,
        False,
    ),
    (
        'huskard-on-thundertusk',
        'Stonehorn Beastriders 2022 Edition',
        None,
        f'{_NK}/P/2148476005/Stonehorn-Beastriders-2022-Edition{_AFF}',
        True,
        False,
    ),
    (
        'huskard-on-stonehorn',
        'Stonehorn Beastriders 2022 Edition',
        None,
        f'{_NK}/P/2148476005/Stonehorn-Beastriders-2022-Edition{_AFF}',
        True,
        False,
    ),
    (
        'frostlord-on-thundertusk',
        'Stonehorn Beastriders 2022 Edition',
        None,
        f'{_NK}/P/2148476005/Stonehorn-Beastriders-2022-Edition{_AFF}',
        True,
        False,
    ),
    (
        'frostlord-on-stonehorn',
        'Stonehorn Beastriders 2022 Edition',
        None,
        f'{_NK}/P/2148476005/Stonehorn-Beastriders-2022-Edition{_AFF}',
        True,
        False,
    ),
    (
        'gorger-mawpack',
        'Warcry - Gorger Mawpack',
        None,
        f'{_NK}/P/2148447217/Warcry---Gorger-Mawpack{_AFF}',
        True,
        False,
    ),
    (
        'mawpit',
        'Ogor Mawpit',
        None,
        f'{_NK}/P/2148278497/Ogor-Mawpit{_AFF}',
        True,
        False,
    ),
    (
        'mournfang-pack',
        'Mournfang Pack',
        None,
        f'{_NK}/P/2148049626/Mournfang-Pack{_AFF}',
        True,
        False,
    ),
    (
        'gnoblars',
        'Gnoblars Webstore Edition',
        None,
        f'{_NK}/P/2147916880/Gnoblars-Webstore-Edition{_AFF}',
        True,
        False,
    ),
    (
        'frost-sabres',
        'Frost Sabres Webstore Edition',
        None,
        f'{_NK}/P/2148325275/Frost-Sabres-Webstore-Edition{_AFF}',
        True,
        False,
    ),
    (
        'ironguts',
        'Ironguts 2022 Edition',
        None,
        f'{_NK}/P/2148447209/Ironguts-2022-Edition{_AFF}',
        True,
        False,
    ),
]


class Command(BaseCommand):
    """Seed Noble Knight prices for Ogor Mawtribes (23 of 26 products have NK URLs)."""

    help = 'Seeds NK CurrentPrice records for OM-001 to OM-026 (23 products have NK URLs).'

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
            f'seed_nk_ogor_mawtribes_prices complete. '
            f'NK prices: {created_count} created, {updated_count} updated.'
        ))
