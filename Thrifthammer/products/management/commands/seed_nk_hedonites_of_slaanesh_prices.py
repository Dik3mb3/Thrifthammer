"""
Management command: seed_nk_hedonites_of_slaanesh_prices

Seeds Noble Knight CurrentPrice records for Hedonites of Slaanesh products
(HOS-001 to HOS-016) from the AOS Hedonites of Slaanesh - GW, NK, MM.xlsx (2026-06-24).

All 16 products have confirmed NK URLs.

Dual-kit notes:
  - HOS-002 Synessa and HOS-003 Dexcessa share one NK listing (Dexcessa - The Talon
    of Slaanesh).
  - HOS-004 Symbaresh Twinsouls and HOS-011 Myrmidesh Painbringers share one NK
    listing (Myrmidesh Painbringers).
  - HOS-005 Blissbarb Seekers and HOS-010 Slickblade Seekers share one NK listing
    (Slickblade Seekers).

Affiliate tag ?awid=1576 appended to all NK URLs.
Uses create_defaults for price and in_stock so scraper-set values survive
Railway redeploys.

Usage:
    python manage.py seed_nk_hedonites_of_slaanesh_prices
"""

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Product, Retailer

_NK = 'https://www.nobleknight.com'
_AFF = '?awid=1576'

# (slug, listing_title, price, url, in_stock, not_available)
NK_PRICES = [
    (
        'lord-of-hubris',
        'Lord of Hubris',
        None,
        f'{_NK}/P/2148041464/Lord-of-Hubris{_AFF}',
        True,
        False,
    ),
    # ⚠ Dual kit: Synessa and Dexcessa share one NK listing.
    (
        'synessa-the-voice-of-slaanesh',
        'Dexcessa - The Talon of Slaanesh',
        None,
        f'{_NK}/P/2148092153/Dexcessa---The-Talon-of-Slaanesh{_AFF}',
        True,
        False,
    ),
    (
        'dexcessa-the-talon-of-slaanesh',
        'Dexcessa - The Talon of Slaanesh',
        None,
        f'{_NK}/P/2148092153/Dexcessa---The-Talon-of-Slaanesh{_AFF}',
        True,
        False,
    ),
    # ⚠ Dual kit: Symbaresh Twinsouls and Myrmidesh Painbringers share one NK listing.
    (
        'symbaresh-twinsouls',
        'Myrmidesh Painbringers',
        None,
        f'{_NK}/P/2148176309/Myrmidesh-Painbringers{_AFF}',
        True,
        False,
    ),
    # ⚠ Dual kit: Blissbarb Seekers and Slickblade Seekers share one NK listing.
    (
        'blissbarb-seekers',
        'Slickblade Seekers',
        None,
        f'{_NK}/P/2147865670/Slickblade-Seekers{_AFF}',
        True,
        False,
    ),
    (
        'slaangor-fiendbloods',
        'Slaangor Fiendbloods',
        None,
        f'{_NK}/P/2148383172/Slaangor-Fiendbloods{_AFF}',
        True,
        False,
    ),
    (
        'glutos-orscollion-lord-of-gluttony',
        'Glutos Orscollion - Lord of Gluttony',
        None,
        f'{_NK}/P/2147865669/Glutos-Orscollion---Lord-of-Gluttony{_AFF}',
        True,
        False,
    ),
    (
        'blissbarb-archers',
        'Blissbarb Archers - 2021 Edition',
        None,
        f'{_NK}/P/2147865668/Blissbarb-Archers-2021-Edition{_AFF}',
        True,
        False,
    ),
    (
        'sigvald-prince-of-slaanesh',
        'Sigvald - Prince of Slaanesh',
        None,
        f'{_NK}/P/2148143350/Sigvald---Prince-of-Slaanesh{_AFF}',
        True,
        False,
    ),
    (
        'slickblade-seekers',
        'Slickblade Seekers',
        None,
        f'{_NK}/P/2147865670/Slickblade-Seekers{_AFF}',
        True,
        False,
    ),
    (
        'myrmidesh-painbringers',
        'Myrmidesh Painbringers',
        None,
        f'{_NK}/P/2148176309/Myrmidesh-Painbringers{_AFF}',
        True,
        False,
    ),
    (
        'lord-of-pain',
        'Lord of Pain',
        None,
        f'{_NK}/P/2147865673/Lord-of-Pain{_AFF}',
        True,
        False,
    ),
    (
        'shardspeaker-of-slaanesh',
        'Shardspeaker of Slaanesh',
        None,
        f'{_NK}/P/2147865674/Shardspeaker-of-Slaanesh{_AFF}',
        True,
        False,
    ),
    (
        'fane-of-slaanesh',
        'Fane of Slaanesh',
        None,
        f'{_NK}/P/2147749548/Fane-of-Slaanesh{_AFF}',
        True,
        False,
    ),
    (
        'endless-spells-hedonites-of-slaanesh',
        'Endless Spells - Hedonites of Slaanesh',
        None,
        f'{_NK}/P/2147749545/Endless-Spells---Hedonites-of-Slaanesh{_AFF}',
        True,
        False,
    ),
    (
        'the-masque',
        'Masque, The',
        None,
        f'{_NK}/P/2148176502/Masque-The{_AFF}',
        True,
        False,
    ),
]


class Command(BaseCommand):
    """Seed Noble Knight prices for Hedonites of Slaanesh (all 16 have NK URLs)."""

    help = 'Seeds NK CurrentPrice records for HOS-001 to HOS-016 (all 16 products have NK URLs).'

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
            f'seed_nk_hedonites_of_slaanesh_prices complete. '
            f'NK prices: {created_count} created, {updated_count} updated.'
        ))
