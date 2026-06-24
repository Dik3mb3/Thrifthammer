"""
Management command: seed_nk_maggotkin_of_nurgle_prices

Seeds Noble Knight CurrentPrice records for Maggotkin of Nurgle products
(MON-001 to MON-021) from the AOS Maggotkin of Nurgle - GW, NK, MM.xlsx (2026-06-24).

18 of 21 products have confirmed NK URLs.
No NK entries for: MON-011 The Court of Gelgus Pust, MON-012 Cankerborn,
MON-014 Pox-Wretches.

Dual-kit notes:
  - MON-002 Lord of Afflictions and MON-003 Pusgoyle Blightlords share one
    NK listing (Pusgoyle Blightlords).
  - MON-005 Morbidex Twiceborn, MON-006 Bloab Rotspawned, and MON-008
    Orghotts Daemonspew share one NK listing (Maggoth Lord triple-kit).

Affiliate tag ?awid=1576 appended to all NK URLs.
Uses create_defaults for price and in_stock so scraper-set values survive
Railway redeploys.

Usage:
    python manage.py seed_nk_maggotkin_of_nurgle_prices
"""

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Product, Retailer

_NK = 'https://www.nobleknight.com'
_AFF = '?awid=1576'

# (slug, listing_title, price, url, in_stock, not_available)
NK_PRICES = [
    (
        'rotbringer-sorcerer',
        'Rotbringer Sorcerer',
        None,
        f'{_NK}/P/2147945645/Rotbringer-Sorcerer{_AFF}',
        True,
        False,
    ),
    # ⚠ Dual kit: Lord of Afflictions and Pusgoyle Blightlords share one NK listing.
    (
        'lord-of-afflictions',
        'Pusgoyle Blightlords',
        None,
        f'{_NK}/P/2147691268/Pusgoyle-Blightlords{_AFF}',
        True,
        False,
    ),
    (
        'pusgoyle-blightlords',
        'Pusgoyle Blightlords',
        None,
        f'{_NK}/P/2147691268/Pusgoyle-Blightlords{_AFF}',
        True,
        False,
    ),
    (
        'lord-of-blights',
        'Lord of Blights',
        None,
        f'{_NK}/P/2147956537/Lord-of-Blights{_AFF}',
        True,
        False,
    ),
    # ⚠ Dual kit (triple): Morbidex Twiceborn, Bloab Rotspawned, and Orghotts Daemonspew
    #   all come from the same Maggoth Lord kit -- share one NK listing.
    (
        'morbidex-twiceborn',
        'Maggoth Lord - Bloab Rotspawned / Orghotts Daemonspew / Morbidex Twiceborn Webstore Edition',
        None,
        f'{_NK}/P/2148095184/Maggoth-Lord-Bloab-Rotspawned-Orghotts-Daemonspew-Morbidex-Twiceborn-Webstore-Edition{_AFF}',
        True,
        False,
    ),
    (
        'bloab-rotspawned',
        'Maggoth Lord - Bloab Rotspawned / Orghotts Daemonspew / Morbidex Twiceborn Webstore Edition',
        None,
        f'{_NK}/P/2148095184/Maggoth-Lord-Bloab-Rotspawned-Orghotts-Daemonspew-Morbidex-Twiceborn-Webstore-Edition{_AFF}',
        True,
        False,
    ),
    (
        'orghotts-daemonspew',
        'Maggoth Lord - Bloab Rotspawned / Orghotts Daemonspew / Morbidex Twiceborn Webstore Edition',
        None,
        f'{_NK}/P/2148095184/Maggoth-Lord-Bloab-Rotspawned-Orghotts-Daemonspew-Morbidex-Twiceborn-Webstore-Edition{_AFF}',
        True,
        False,
    ),
    (
        'the-glottkin',
        'Glottkin, The',
        None,
        f'{_NK}/P/2148009791/Glottkin-The{_AFF}',
        True,
        False,
    ),
    (
        'lord-of-plagues',
        'Lord of Plagues',
        None,
        f'{_NK}/P/2147956531/Lord-of-Plagues{_AFF}',
        True,
        False,
    ),
    (
        'gutrot-spume',
        'Gutrot Spume - 2015 Edition',
        None,
        f'{_NK}/P/2147593196/Gutrot-Spume-2015-Edition{_AFF}',
        True,
        False,
    ),
    (
        'spoilpox-scrivener',
        'Spoilpox Scrivener',
        None,
        f'{_NK}/P/2148003062/Spoilpox-Scrivener{_AFF}',
        True,
        False,
    ),
    (
        'pestigors',
        'Pestigors',
        None,
        f'{_NK}/P/2148395213/Pestigors{_AFF}',
        True,
        False,
    ),
    (
        'festus-the-leechlord',
        'Festus The Leechlord',
        None,
        f'{_NK}/P/2148395201/Festus-The-Leechlord{_AFF}',
        True,
        False,
    ),
    (
        'rotmire-creed',
        'Rotmire Creed',
        None,
        f'{_NK}/P/2148021526/Rotmire-Creed{_AFF}',
        True,
        False,
    ),
    (
        'harbinger-of-decay',
        'Harbringer of Decay Webstore Edition',
        None,
        f'{_NK}/P/2147915636/Harbringer-of-Decay-Webstore-Edition{_AFF}',
        True,
        False,
    ),
    (
        'chaos-battletome-maggotkin-of-nurgle',
        'Chaos Battletome - Maggotkin of Nurgle',
        None,
        f'{_NK}/P/2148395229/Chaos-Battletome---Maggotkin-of-Nurgle{_AFF}',
        True,
        False,
    ),
    (
        'sloven-knights',
        'Sloven Knights',
        None,
        f'{_NK}/P/2148395210/Sloven-Knights{_AFF}',
        True,
        False,
    ),
    (
        'rotswords',
        'Rotswords',
        None,
        f'{_NK}/P/2148395207/Rotswords{_AFF}',
        True,
        False,
    ),
]


class Command(BaseCommand):
    """Seed Noble Knight prices for Maggotkin of Nurgle (18 of 21 have NK URLs)."""

    help = 'Seeds NK CurrentPrice records for MON-001 to MON-021 (18 products have NK URLs).'

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
            f'seed_nk_maggotkin_of_nurgle_prices complete. '
            f'NK prices: {created_count} created, {updated_count} updated.'
        ))
