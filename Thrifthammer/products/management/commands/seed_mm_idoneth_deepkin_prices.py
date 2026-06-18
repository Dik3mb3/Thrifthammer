"""
Management command: seed_mm_idoneth_deepkin_prices

Seeds Miniature Market CurrentPrice records for Idoneth Deepkin products
(IDK-001 to IDK-021) from the AOS Idoneth Deepkin - GW, NK, MM.xlsx (2026-06-17).

13 of 21 products have confirmed MM URLs.
No MM entries for: IDK-004 Akhelian Leviadon, IDK-008 Akhelian King,
IDK-010 Volturnos, IDK-012 Gloomtide Shipwreck, IDK-013 Namarti Thralls,
IDK-014 Lotann, IDK-020 Isharann Soulrender, IDK-021 Isharann Soulscryer.

Dual-kit notes:
  - IDK-003 Akhelian Ishlaen Guard and IDK-005 Akhelian Morrsarr Guard share
    one MM listing (gw-87-34).
  - IDK-011 Eidolon of Mathlann - Aspect of the Sea and IDK-015 Aspect of
    the Storm share one MM listing (gw-87-32).

Uses create_defaults for price and in_stock so scraper-set values survive
Railway redeploys.

Usage:
    python manage.py seed_mm_idoneth_deepkin_prices
"""

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Product, Retailer

_MM = 'https://www.miniaturemarket.com'

# (slug, listing_title, price, url, in_stock, not_available)
# price=None  -> scraper will populate on first run
# in_stock    -> initial assumption; scraper corrects as needed
MM_PRICES = [

    # -- Spearhead -------------------------------------------------------------
    (
        'spearhead-idoneth-deepkin-akhelian-tide-guard',
        'Spearhead: Idoneth Deepkin – Akhelian Tide Guard',
        None,
        f'{_MM}/warhammer-age-sigmar-spearhead-idoneth-deepkin-akhelian-tide-guard-gw-70-873.html',
        True,
        False,
    ),

    # -- Heroes ----------------------------------------------------------------
    (
        'akhelian-thrallmaster',
        'Akhelian Thrallmaster',
        None,
        f'{_MM}/gw-87-37.html',
        True,
        False,
    ),
    (
        'isharann-tidecaster',
        'Isharann Tidecaster',
        None,
        f'{_MM}/gw-87-27.html',
        True,
        False,
    ),
    (
        'mathaela-oracle-of-the-abyss',
        'Mathaela, Oracle of the Abyss',
        None,
        f'{_MM}/warhammer-age-sigmar-idoneth-deepkin-mathaela-oracle-abyss-gw-87-40.html',
        True,
        False,
    ),

    # -- Units -----------------------------------------------------------------
    # ⚠ Dual kit: Akhelian Ishlaen Guard and Morrsarr Guard share one MM listing.
    (
        'akhelian-ishlaen-guard',
        'Akhelian Ishlaen Guard / Morrsarr Guard',
        None,
        f'{_MM}/gw-87-34.html',
        True,
        False,
    ),
    (
        'akhelian-morrsarr-guard',
        'Akhelian Ishlaen Guard / Morrsarr Guard',
        None,
        f'{_MM}/gw-87-34.html',
        True,
        False,
    ),
    (
        'akhelian-allopex',
        'Akhelian Allopex',
        None,
        f'{_MM}/gw-87-35.html',
        True,
        False,
    ),
    (
        'namarti-reavers',
        'Namarti Reavers',
        None,
        f'{_MM}/gw-87-30.html',
        True,
        False,
    ),

    # -- Large Kits / Monsters -------------------------------------------------
    # ⚠ Dual kit: Eidolon Aspect of the Sea and Aspect of the Storm share one
    #   MM listing (gw-87-32).
    (
        'eidolon-of-mathlann-aspect-of-the-sea',
        'Eidolon of Mathlann',
        None,
        f'{_MM}/gw-87-32.html',
        True,
        False,
    ),
    (
        'eidolon-of-mathlann-aspect-of-the-storm',
        'Eidolon of Mathlann',
        None,
        f'{_MM}/gw-87-32.html',
        True,
        False,
    ),

    # -- Endless Spells / Manifestations / Terrain -----------------------------
    (
        'idoneth-deepkin-manifestations',
        'Idoneth Deepkin Manifestations',
        None,
        f'{_MM}/warhammer-age-sigmar-idoneth-deepkin-manifestations-gw-87-41.html',
        True,
        False,
    ),
    (
        'ikon-of-the-sea-storm',
        'Ikon of the Sea/Storm',
        None,
        f'{_MM}/warhammer-age-sigmar-idoneth-deepkin-ikon-sea-gw-87-39.html',
        True,
        False,
    ),

    # -- Battletome ------------------------------------------------------------
    (
        'order-battletome-idoneth-deepkin',
        'Order Battletome: Idoneth Deepkin',
        None,
        f'{_MM}/warhammer-age-sigmar-order-battletome-idoneth-deepkin-gw-87-01.html',
        True,
        False,
    ),
]


class Command(BaseCommand):
    """Seed Miniature Market prices for Idoneth Deepkin (13 of 21 products have MM URLs)."""

    help = 'Seeds MM CurrentPrice records for IDK-001 to IDK-021 (13 products have MM URLs).'

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
            f'seed_mm_idoneth_deepkin_prices complete. '
            f'MM prices: {created_count} created, {updated_count} updated.'
        ))
