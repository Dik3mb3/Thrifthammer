"""
Management command: seed_nk_idoneth_deepkin_prices

Seeds Noble Knight CurrentPrice records for Idoneth Deepkin products
(IDK-001 to IDK-021) from the AOS Idoneth Deepkin - GW, NK, MM.xlsx (2026-06-17).

16 of 21 products have confirmed NK URLs.
No NK entries for: IDK-001 Spearhead, IDK-016 Manifestations,
IDK-017 Mathaela, IDK-018 Ikon of the Sea/Storm, IDK-019 Battletome.

Dual-kit notes:
  - IDK-003 Akhelian Ishlaen Guard and IDK-005 Akhelian Morrsarr Guard share
    one NK listing (Akhelian Morrsarr Guard).
  - IDK-008 Akhelian King and IDK-010 Volturnos share one NK listing
    (Volturnos, High King of the Deep).
  - IDK-011 Eidolon of Mathlann - Aspect of the Sea and IDK-015 Aspect of
    the Storm share one NK listing (Eidolon of Mathlann).

Affiliate tag ?awid=1576 appended to all NK URLs.
Uses create_defaults for price and in_stock so scraper-set values survive
Railway redeploys.

Usage:
    python manage.py seed_nk_idoneth_deepkin_prices
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
        'akhelian-thrallmaster',
        'Akhelian Thrallmaster',
        None,
        f'{_NK}/P/2147986345/Akhelian-Thrallmaster{_AFF}',
        True,
        False,
    ),
    (
        'isharann-tidecaster',
        'Isharann Tidecaster',
        None,
        f'{_NK}/P/2148084037/Isharann-Tidecaster{_AFF}',
        True,
        False,
    ),
    # ⚠ Dual kit: Akhelian King and Volturnos share one NK listing.
    (
        'akhelian-king',
        'Volturnos, High King of the Deep',
        None,
        f'{_NK}/P/2148067827/Volturnos---High-King-of-the-Deep{_AFF}',
        True,
        False,
    ),
    (
        'volturnos-high-king-of-the-deep',
        'Volturnos, High King of the Deep',
        None,
        f'{_NK}/P/2148067827/Volturnos---High-King-of-the-Deep{_AFF}',
        True,
        False,
    ),
    (
        'lotann-warden-of-the-soul-ledgers',
        'Lotann, Warden of the Soul Ledgers',
        None,
        f'{_NK}/P/2147701532/Lotann---Warden-of-the-Soul-Ledgers{_AFF}',
        True,
        False,
    ),
    (
        'isharann-soulrender',
        'Isharann Soulrender',
        None,
        f'{_NK}/P/2147702834/Isharann-Soulrender{_AFF}',
        True,
        False,
    ),
    (
        'isharann-soulscryer',
        'Isharann Soulscryer',
        None,
        f'{_NK}/P/2147995063/Isharann-Soulscryer{_AFF}',
        True,
        False,
    ),

    # -- Units -----------------------------------------------------------------
    # ⚠ Dual kit: Akhelian Ishlaen Guard and Morrsarr Guard share one NK listing.
    (
        'akhelian-ishlaen-guard',
        'Akhelian Morrsarr Guard',
        None,
        f'{_NK}/P/2148336039/Akhelian-Morrsarr-Guard{_AFF}',
        True,
        False,
    ),
    (
        'akhelian-morrsarr-guard',
        'Akhelian Morrsarr Guard',
        None,
        f'{_NK}/P/2148336039/Akhelian-Morrsarr-Guard{_AFF}',
        True,
        False,
    ),
    (
        'akhelian-allopex',
        'Akhelian Allopex',
        None,
        f'{_NK}/P/2148040466/Akhelian-Allopex{_AFF}',
        True,
        False,
    ),
    (
        'namarti-reavers',
        'Namarti Reavers',
        None,
        f'{_NK}/P/2148383169/Namarti-Reavers{_AFF}',
        True,
        False,
    ),
    (
        'namarti-thralls',
        'Namarti Thralls',
        None,
        f'{_NK}/P/2147701530/Namarti-Thralls{_AFF}',
        True,
        False,
    ),

    # -- Large Kits / Monsters -------------------------------------------------
    (
        'akhelian-leviadon',
        'Akhelian Leviadon',
        None,
        f'{_NK}/P/2147703350/Akhelian-Leviadon{_AFF}',
        True,
        False,
    ),
    # ⚠ Dual kit: Eidolon Aspect of the Sea and Aspect of the Storm share one
    #   NK listing (Eidolon of Mathlann).
    (
        'eidolon-of-mathlann-aspect-of-the-sea',
        'Eidolon of Mathlann',
        None,
        f'{_NK}/P/2147701531/Eidolon-of-Mathlann-2018{_AFF}',
        True,
        False,
    ),
    (
        'eidolon-of-mathlann-aspect-of-the-storm',
        'Eidolon of Mathlann',
        None,
        f'{_NK}/P/2147701531/Eidolon-of-Mathlann-2018{_AFF}',
        True,
        False,
    ),

    # -- Terrain / Scenery -----------------------------------------------------
    (
        'gloomtide-shipwreck',
        'Gloomtide Shipwreck',
        None,
        f'{_NK}/P/2147701533/Gloomtide-Shipwreck{_AFF}',
        True,
        False,
    ),
]


class Command(BaseCommand):
    """Seed Noble Knight prices for Idoneth Deepkin (16 of 21 products have NK URLs)."""

    help = 'Seeds NK CurrentPrice records for IDK-001 to IDK-021 (16 products have NK URLs).'

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
            f'seed_nk_idoneth_deepkin_prices complete. '
            f'NK prices: {created_count} created, {updated_count} updated.'
        ))
