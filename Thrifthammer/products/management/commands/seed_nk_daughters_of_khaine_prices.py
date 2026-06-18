"""
Management command: seed_nk_daughters_of_khaine_prices

Seeds Noble Knight CurrentPrice records for Daughters of Khaine products
(DOK-001 to DOK-015) from the Daughters of Khaine - GW, NK, MM.xlsx (2026-06-17).

All 15 products have confirmed NK URLs.

Dual-kit / triple-kit notes:
  - DOK-001 Blood Stalkers and DOK-006 Blood Sisters share one NK listing.
  - DOK-002 Khinerai Lifetakers and DOK-007 Khinerai Heartrenders share one NK listing.
  - DOK-003 Bloodwrack Shrine, DOK-004 Slaughter Queen on Cauldron of Blood, and
    DOK-005 Hag Queen on Cauldron of Blood all share one NK listing.

Affiliate tag ?awid=1576 appended to all NK URLs.
Uses create_defaults for price and in_stock so scraper-set values survive
Railway redeploys.

Usage:
    python manage.py seed_nk_daughters_of_khaine_prices
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

    # -- Units -----------------------------------------------------------------
    # ⚠ Dual kit: Blood Stalkers and Blood Sisters share one NK listing.
    (
        'blood-stalkers',
        'Melusai Blood Stalkers',
        None,
        f'{_NK}/P/2147693149/Melusai-Blood-Stalkers{_AFF}',
        True,
        False,
    ),
    # ⚠ Dual kit: Khinerai Lifetakers and Khinerai Heartrenders share one NK listing.
    (
        'khinerai-lifetakers',
        'Khinerai Heartrenders / Lifetakers',
        None,
        f'{_NK}/P/2148379525/Khinerai-Heartrenders-Lifetakers{_AFF}',
        True,
        False,
    ),
    # ⚠ Triple kit: Bloodwrack Shrine, Slaughter Queen, and Hag Queen all share
    #   one NK listing (Cauldron of Blood / Bloodwrack Shrine).
    (
        'bloodwrack-shrine',
        'Cauldron of Blood / Bloodwrack Shrine',
        None,
        f'{_NK}/P/2147889739/Cauldron-of-Blood-Bloodwrack-Shrine{_AFF}',
        True,
        False,
    ),
    (
        'slaughter-queen-on-cauldron-of-blood',
        'Cauldron of Blood / Bloodwrack Shrine',
        None,
        f'{_NK}/P/2147889739/Cauldron-of-Blood-Bloodwrack-Shrine{_AFF}',
        True,
        False,
    ),
    (
        'hag-queen-on-cauldron-of-blood',
        'Cauldron of Blood / Bloodwrack Shrine',
        None,
        f'{_NK}/P/2147889739/Cauldron-of-Blood-Bloodwrack-Shrine{_AFF}',
        True,
        False,
    ),
    (
        'blood-sisters',
        'Melusai Blood Stalkers',
        None,
        f'{_NK}/P/2147693149/Melusai-Blood-Stalkers{_AFF}',
        True,
        False,
    ),
    (
        'khinerai-heartrenders',
        'Khinerai Heartrenders / Lifetakers',
        None,
        f'{_NK}/P/2148379525/Khinerai-Heartrenders-Lifetakers{_AFF}',
        True,
        False,
    ),
    (
        'blood-hags',
        'Blood Hags',
        None,
        f'{_NK}/P/2148434586/Blood-Hags{_AFF}',
        True,
        False,
    ),
    (
        'khainite-shadowstalkers',
        'Khainite Shadowstalkers',
        None,
        f'{_NK}/P/2147852232/Khainite-Shadowstalkers{_AFF}',
        True,
        False,
    ),

    # -- Heroes ----------------------------------------------------------------
    (
        'shrine-of-dark-tribute',
        'Shrine of Dark Tribute',
        None,
        f'{_NK}/P/2148434572/Shrine-of-Dark-Tribute{_AFF}',
        True,
        False,
    ),
    (
        'melusai-ironscale',
        'Melusai Ironscale',
        None,
        f'{_NK}/P/2147891220/Melusai-Ironscale{_AFF}',
        True,
        False,
    ),
    (
        'high-gladiatrix',
        'High Gladiatrix',
        None,
        f'{_NK}/P/2147986344/High-Gladiatrix{_AFF}',
        True,
        False,
    ),
    (
        'krethusa-the-croneseer',
        'Krethusa the Cronseer',
        None,
        f'{_NK}/P/2148145460/Krethusa-the-Cronseer{_AFF}',
        True,
        False,
    ),

    # -- Endless Spells --------------------------------------------------------
    (
        'endless-spells-daughters-of-khaine',
        'Endless Spells - Daughters of Khaine',
        None,
        f'{_NK}/P/2147865680/Endless-Spells---Daughters-of-Khaine{_AFF}',
        True,
        False,
    ),

    # -- Battletome ------------------------------------------------------------
    (
        'order-battletome-daughters-of-khaine',
        'Battletome - Daughters of Khaine',
        None,
        f'{_NK}/P/2148434551/Battletome---Daughters-of-Khaine{_AFF}',
        True,
        False,
    ),
]


class Command(BaseCommand):
    """Seed Noble Knight prices for Daughters of Khaine (all 15 products have NK URLs)."""

    help = 'Seeds NK CurrentPrice records for DOK-001 to DOK-015 (all 15 products have NK URLs).'

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
            f'seed_nk_daughters_of_khaine_prices complete. '
            f'NK prices: {created_count} created, {updated_count} updated.'
        ))
