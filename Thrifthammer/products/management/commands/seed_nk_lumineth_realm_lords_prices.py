"""
Management command: seed_nk_lumineth_realm_lords_prices

Seeds Noble Knight CurrentPrice records for Lumineth Realm-lords products
(LRL-001 to LRL-026) from the AOS Lumineth Realm Lords - GW, NK, MM.xlsx (2026-06-17).

25 of 26 products have confirmed NK URLs.
No NK entries for: LRL-006 Endless Spells: Lumineth Realm-lords.

Dual-kit notes:
  - LRL-001 Alarith Spirit of the Mountain and LRL-004 Avalenor, the Stoneheart
    King share one NK listing (Avalenor, the Stoneheart King).
  - LRL-007 Hurakan Spirit of the Wind and LRL-016 Sevireth share one NK listing
    (Sevireth).
  - LRL-010 Lyrior Uthralle and LRL-023 Vanari Lord Regent (2021) share one NK
    listing (Lyrior Uthralle).

Affiliate tag ?awid=1576 appended to all NK URLs.
Uses create_defaults for price and in_stock so scraper-set values survive
Railway redeploys.

Usage:
    python manage.py seed_nk_lumineth_realm_lords_prices
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

    # -- Heroes ----------------------------------------------------------------
    (
        'alarith-stonemage',
        'Alarith Stonemage',
        None,
        f'{_NK}/P/2147834389/Alarith-Stonemage{_AFF}',
        True,
        False,
    ),
    (
        'archmage-teclis-and-celennar-spirit-of-hysh',
        'Archmage Teclis',
        None,
        f'{_NK}/P/2147833116/Archmage-Teclis{_AFF}',
        True,
        False,
    ),
    (
        'ellania-and-ellathor-eclipsian-warsages',
        'Ellania and Ellathor',
        None,
        f'{_NK}/P/2147874707/Ellania-and-Ellathor{_AFF}',
        True,
        False,
    ),
    (
        'hurakan-windmage',
        'Hurakan Windmage',
        None,
        f'{_NK}/P/2148050318/Hurakan-Windmage{_AFF}',
        True,
        False,
    ),
    # ⚠ Dual kit: Lyrior Uthralle and Vanari Lord Regent (2021) share one NK listing.
    (
        'lyrior-uthralle-warden-of-ymetrica',
        'Lyrior Uthralle',
        None,
        f'{_NK}/P/2147874704/Lyrior-Uthralle{_AFF}',
        True,
        False,
    ),
    (
        'vanari-lord-regent-2021',
        'Lyrior Uthralle',
        None,
        f'{_NK}/P/2147874704/Lyrior-Uthralle{_AFF}',
        True,
        False,
    ),
    (
        'scinari-calligrave',
        'Scinari Calligrave',
        None,
        f'{_NK}/P/2147874711/Scinari-Calligrave{_AFF}',
        True,
        False,
    ),
    (
        'scinari-cathallar',
        'Scinari Cathallar',
        None,
        f'{_NK}/P/2147833118/Scinari-Cathallar{_AFF}',
        True,
        False,
    ),
    (
        'scinari-enlightener',
        'Scinari Enlightener',
        None,
        f'{_NK}/P/2148021552/Scinari-Enlightener{_AFF}',
        True,
        False,
    ),
    (
        'scinari-loreseeker',
        'Scinari Loreseeker',
        None,
        f'{_NK}/P/2148034731/Scinari-Loreseeker{_AFF}',
        True,
        False,
    ),
    (
        'the-light-of-eltharion',
        'Light of Eltharion',
        None,
        f'{_NK}/P/2147833119/Light-of-Eltharion-The{_AFF}',
        True,
        False,
    ),
    (
        'vanari-bannerblade',
        'Vanari Bannerblade',
        None,
        f'{_NK}/P/2147874709/Vanari-Bannerblade{_AFF}',
        True,
        False,
    ),
    (
        'vanari-lord-regent',
        'Vanari Lord Regent',
        None,
        f'{_NK}/P/2148411142/Vanari-Lord-Regent{_AFF}',
        True,
        False,
    ),

    # -- Large Kits / Monsters -------------------------------------------------
    # ⚠ Dual kit: Alarith Spirit of the Mountain and Avalenor share one NK listing.
    (
        'alarith-spirit-of-the-mountain',
        'Avalenor, the Stoneheart King',
        None,
        f'{_NK}/P/2147834387/Avalenor---The-Stoneheart-King{_AFF}',
        True,
        False,
    ),
    (
        'avalenor-the-stoneheart-king',
        'Avalenor, the Stoneheart King',
        None,
        f'{_NK}/P/2147834387/Avalenor---The-Stoneheart-King{_AFF}',
        True,
        False,
    ),

    # -- Units -----------------------------------------------------------------
    # ⚠ Dual kit: Hurakan Spirit of the Wind and Sevireth share one NK listing.
    (
        'hurakan-spirit-of-the-wind',
        'Sevireth',
        None,
        f'{_NK}/P/2147874705/Sevireth{_AFF}',
        True,
        False,
    ),
    (
        'sevireth-lord-of-the-seventh-wind',
        'Sevireth',
        None,
        f'{_NK}/P/2147874705/Sevireth{_AFF}',
        True,
        False,
    ),
    (
        'hurakan-windchargers',
        'Hurakan Windchargers',
        None,
        f'{_NK}/P/2148239216/Hurakan-Windchargers-2022-Edition{_AFF}',
        True,
        False,
    ),
    (
        'vanari-auralan-sentinels',
        'Vanari Auralan Sentinels',
        None,
        f'{_NK}/P/2147833115/Vanari-Auralan-Sentinels{_AFF}',
        True,
        False,
    ),
    (
        'vanari-bladelords',
        'Vanari Bladelords',
        None,
        f'{_NK}/P/2147874703/Vanari-Bladelords{_AFF}',
        True,
        False,
    ),
    (
        'vanari-dawnriders',
        'Vanari Dawnriders',
        None,
        f'{_NK}/P/2147834388/Vanari-Dawnriders{_AFF}',
        True,
        False,
    ),
    (
        'vanari-starshard-ballista',
        'Starshard Ballista',
        None,
        f'{_NK}/P/2147874706/Starshard-Ballista{_AFF}',
        True,
        False,
    ),

    # -- Terrain / Scenery -----------------------------------------------------
    (
        'shrine-luminor',
        'Shrine Luminor',
        None,
        f'{_NK}/P/2147874712/Shrine-Luminor{_AFF}',
        True,
        False,
    ),

    # -- Warcry ----------------------------------------------------------------
    (
        'warcry-ydrilan-riverblades',
        'Ydrilan Riverblades',
        None,
        f'{_NK}/P/2148179072/Ydrilan-Riverblades{_AFF}',
        True,
        False,
    ),

    # -- Battletome ------------------------------------------------------------
    (
        'order-battletome-lumineth-realm-lords',
        'Order Battletome: Lumineth Realm-lords',
        None,
        f'{_NK}/P/2148411072/Order-Battletome---Lumineth-Realm-Lords{_AFF}',
        True,
        False,
    ),
]


class Command(BaseCommand):
    """Seed Noble Knight prices for Lumineth Realm-lords (25 of 26 products have NK URLs)."""

    help = 'Seeds NK CurrentPrice records for LRL-001 to LRL-026 (25 products have NK URLs).'

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
            f'seed_nk_lumineth_realm_lords_prices complete. '
            f'NK prices: {created_count} created, {updated_count} updated.'
        ))
