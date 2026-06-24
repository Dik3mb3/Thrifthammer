"""
Management command: seed_mm_hedonites_of_slaanesh_prices

Seeds Miniature Market CurrentPrice records for Hedonites of Slaanesh products
(HOS-001 to HOS-016) from the AOS Hedonites of Slaanesh - GW, NK, MM.xlsx (2026-06-24).

10 of 16 products have confirmed MM URLs.
No MM entries for: HOS-005 Blissbarb Seekers, HOS-007 Glutos Orscollion,
HOS-010 Slickblade Seekers, HOS-014 Fane of Slaanesh,
HOS-015 Endless Spells, HOS-016 The Masque.

Dual-kit notes:
  - HOS-002 Synessa and HOS-003 Dexcessa share one MM listing (/gw-97-50.html).
  - HOS-004 Symbaresh Twinsouls and HOS-011 Myrmidesh Painbringers share one
    MM listing (/gw-83-90.html).

Uses create_defaults for price and in_stock so scraper-set values survive
Railway redeploys.

Usage:
    python manage.py seed_mm_hedonites_of_slaanesh_prices
"""

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Product, Retailer

_MM = 'https://www.miniaturemarket.com'

# (slug, listing_title, price, url, in_stock, not_available)
MM_PRICES = [
    (
        'lord-of-hubris',
        'Lord of Hubris',
        None,
        f'{_MM}/warhammer-age-of-sigmar-hedonites-of-slaanesh-lord-of-hubris-gw-83-96.html',
        True,
        False,
    ),
    # ⚠ Dual kit: Synessa and Dexcessa share one MM listing.
    (
        'synessa-the-voice-of-slaanesh',
        'Synessa, the Voice of Slaanesh / Dexcessa, the Talon of Slaanesh',
        None,
        f'{_MM}/gw-97-50.html',
        True,
        False,
    ),
    (
        'dexcessa-the-talon-of-slaanesh',
        'Synessa, the Voice of Slaanesh / Dexcessa, the Talon of Slaanesh',
        None,
        f'{_MM}/gw-97-50.html',
        True,
        False,
    ),
    # ⚠ Dual kit: Symbaresh Twinsouls and Myrmidesh Painbringers share one MM listing.
    (
        'symbaresh-twinsouls',
        'Symbaresh Twinsouls / Myrmidesh Painbringers',
        None,
        f'{_MM}/gw-83-90.html',
        True,
        False,
    ),
    (
        'slaangor-fiendbloods',
        'Slaangor Fiendbloods',
        None,
        f'{_MM}/gw-83-89.html',
        True,
        False,
    ),
    (
        'blissbarb-archers',
        'Blissbarb Archers',
        None,
        f'{_MM}/gw-83-83.html',
        True,
        False,
    ),
    (
        'sigvald-prince-of-slaanesh',
        'Sigvald, Prince of Slaanesh',
        None,
        f'{_MM}/gw-83-84.html',
        True,
        False,
    ),
    (
        'myrmidesh-painbringers',
        'Symbaresh Twinsouls / Myrmidesh Painbringers',
        None,
        f'{_MM}/gw-83-90.html',
        True,
        False,
    ),
    (
        'lord-of-pain',
        'Lord of Pain',
        None,
        f'{_MM}/gw-83-87.html',
        True,
        False,
    ),
    (
        'shardspeaker-of-slaanesh',
        'Shardspeaker of Slaanesh',
        None,
        f'{_MM}/gw-83-88.html',
        True,
        False,
    ),
]


class Command(BaseCommand):
    """Seed Miniature Market prices for Hedonites of Slaanesh (10 of 16 have MM URLs)."""

    help = 'Seeds MM CurrentPrice records for HOS-001 to HOS-016 (10 products have MM URLs).'

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
            f'seed_mm_hedonites_of_slaanesh_prices complete. '
            f'MM prices: {created_count} created, {updated_count} updated.'
        ))
