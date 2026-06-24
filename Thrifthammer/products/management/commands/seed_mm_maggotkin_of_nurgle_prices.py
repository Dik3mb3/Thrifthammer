"""
Management command: seed_mm_maggotkin_of_nurgle_prices

Seeds Miniature Market CurrentPrice records for Maggotkin of Nurgle products
(MON-001 to MON-021) from the AOS Maggotkin of Nurgle - GW, NK, MM.xlsx (2026-06-24).

7 of 21 products have confirmed MM URLs.
No MM entries for: MON-001, MON-002, MON-003, MON-004, MON-005,
MON-006, MON-008, MON-009, MON-010, MON-011, MON-012, MON-013,
MON-014, MON-018.

Uses create_defaults for price and in_stock so scraper-set values survive
Railway redeploys.

Usage:
    python manage.py seed_mm_maggotkin_of_nurgle_prices
"""

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Product, Retailer

_MM = 'https://www.miniaturemarket.com'

# (slug, listing_title, price, url, in_stock, not_available)
MM_PRICES = [
    (
        'the-glottkin',
        'The Glottkin',
        None,
        f'{_MM}/gw-83-25.html',
        True,
        False,
    ),
    (
        'pestigors',
        'Pestigors',
        None,
        f'{_MM}/Warhammer-Age-of-Sigmar-Maggotkin-of-Nurgle-Pestigors/GW-83-116-2026',
        True,
        False,
    ),
    (
        'festus-the-leechlord',
        'Festus the Leechlord',
        None,
        f'{_MM}/Warhammer-Age-of-Sigmar-Maggotkin-of-Nurgle-Festus-the-Leechlord/GW-83-115-2026',
        True,
        False,
    ),
    (
        'rotmire-creed',
        'Rotmire Creed',
        None,
        f'{_MM}/gw-111-93.html',
        True,
        False,
    ),
    (
        'chaos-battletome-maggotkin-of-nurgle',
        'Chaos Battletome: Maggotkin of Nurgle',
        None,
        f'{_MM}/Warhammer-Age-of-Sigmar-Chaos-Battletome-Maggotkin-of-Nurgle/GW-83-58-2026',
        True,
        False,
    ),
    (
        'sloven-knights',
        'Sloven Knights',
        None,
        f'{_MM}/Warhammer-Age-of-Sigmar-Maggotkin-of-Nurgle-Sloven-Knights/GW-83-114-2026',
        True,
        False,
    ),
    (
        'rotswords',
        'Rotswords',
        None,
        f'{_MM}/Warhammer-Age-of-Sigmar-Maggotkin-of-Nurgle-Rotswords/GW-83-113-2026',
        True,
        False,
    ),
]


class Command(BaseCommand):
    """Seed Miniature Market prices for Maggotkin of Nurgle (7 of 21 have MM URLs)."""

    help = 'Seeds MM CurrentPrice records for MON-001 to MON-021 (7 products have MM URLs).'

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
            f'seed_mm_maggotkin_of_nurgle_prices complete. '
            f'MM prices: {created_count} created, {updated_count} updated.'
        ))
