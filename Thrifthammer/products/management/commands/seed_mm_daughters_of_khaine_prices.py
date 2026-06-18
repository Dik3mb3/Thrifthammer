"""
Management command: seed_mm_daughters_of_khaine_prices

Seeds Miniature Market CurrentPrice records for Daughters of Khaine products
(DOK-001 to DOK-015) from the Daughters of Khaine - GW, NK, MM.xlsx (2026-06-17).

8 of 15 products have confirmed MM URLs.
No MM entries for: DOK-003 Bloodwrack Shrine, DOK-004 Slaughter Queen on Cauldron
of Blood, DOK-005 Hag Queen on Cauldron of Blood, DOK-009 Melusai Ironscale,
DOK-011 Order Battletome: Daughters of Khaine (wait -- actually it has one),
DOK-012 Khainite Shadowstalkers, DOK-014 Endless Spells: Daughters of Khaine.

Dual-kit notes:
  - DOK-001 Blood Stalkers and DOK-006 Blood Sisters share one MM listing (gw-85-20).
  - DOK-002 Khinerai Lifetakers and DOK-007 Khinerai Heartrenders share one MM listing
    (gw-85-19).

Uses create_defaults for price and in_stock so scraper-set values survive
Railway redeploys.

Usage:
    python manage.py seed_mm_daughters_of_khaine_prices
"""

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Product, Retailer

_MM = 'https://www.miniaturemarket.com'

# (slug, listing_title, price, url, in_stock, not_available)
# price=None  -> scraper will populate on first run
# in_stock    -> initial assumption; scraper corrects as needed
MM_PRICES = [

    # -- Units -----------------------------------------------------------------
    # ⚠ Dual kit: Blood Stalkers and Blood Sisters share one MM listing.
    (
        'blood-stalkers',
        'Melusai Blood Stalkers / Blood Sisters',
        None,
        f'{_MM}/gw-85-20.html',
        True,
        False,
    ),
    # ⚠ Dual kit: Khinerai Lifetakers and Khinerai Heartrenders share one MM listing.
    (
        'khinerai-lifetakers',
        'Khinerai Heartrenders / Lifetakers',
        None,
        f'{_MM}/gw-85-19.html',
        True,
        False,
    ),
    (
        'blood-sisters',
        'Melusai Blood Stalkers / Blood Sisters',
        None,
        f'{_MM}/gw-85-20.html',
        True,
        False,
    ),
    (
        'khinerai-heartrenders',
        'Khinerai Heartrenders / Lifetakers',
        None,
        f'{_MM}/gw-85-19.html',
        True,
        False,
    ),
    (
        'blood-hags',
        'Daughters of Khaine Blood Hags',
        None,
        f'{_MM}/Warhammer-Age-of-Sigmar-Daughters-of-Khaine-Blood-Hags/GW-85-66-2026',
        True,
        False,
    ),

    # -- Heroes ----------------------------------------------------------------
    (
        'shrine-of-dark-tribute',
        'Daughters of Khaine Shrine of Dark Tribute',
        None,
        f'{_MM}/Warhammer-Age-of-Sigmar-Daughters-of-Khaine-Shrine-of-Dark-Tribute/GW-85-65-2026',
        True,
        False,
    ),
    (
        'high-gladiatrix',
        'High Gladiatrix',
        None,
        f'{_MM}/gw-85-33.html',
        True,
        False,
    ),
    (
        'krethusa-the-croneseer',
        'Daughters of Khaine Krethusa the Croneseer',
        None,
        f'{_MM}/warhammer-age-sigmar-daughters-khaine-krethusa-croneseer-gw-85-24.html',
        True,
        False,
    ),

    # -- Battletome ------------------------------------------------------------
    (
        'order-battletome-daughters-of-khaine',
        'Order Battletome: Daughters of Khaine 2026',
        None,
        f'{_MM}/Warhammer-Age-of-Sigmar-Order-Battletome-Daughters-of-Khaine-2026/GW-85-05-2026',
        True,
        False,
    ),
]


class Command(BaseCommand):
    """Seed Miniature Market prices for Daughters of Khaine (9 of 15 products have MM URLs)."""

    help = 'Seeds MM CurrentPrice records for DOK-001 to DOK-015 (9 products have MM URLs).'

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
            f'seed_mm_daughters_of_khaine_prices complete. '
            f'MM prices: {created_count} created, {updated_count} updated.'
        ))
