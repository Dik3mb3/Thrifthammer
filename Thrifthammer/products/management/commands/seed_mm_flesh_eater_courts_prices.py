"""
Management command: seed_mm_flesh_eater_courts_prices

Seeds Miniature Market CurrentPrice records for Flesh-Eater Courts products
from the AOS Flesh Eater Courts - GW, NK, MM.xlsx (2026-06-10).

Only 9 of 21 products have confirmed MM URLs:
  FEC-004  Crypt Infernal Courtier    (shares MM listing with FEC-005)
  FEC-005  Crypt Haunter Courtier     (shares MM listing with FEC-004)
  FEC-006  High Falconer Felgryn
  FEC-009  Abhorrant Cardinal
  FEC-010  Grand Justice Gormayne
  FEC-011  Royal Decapitator
  FEC-016  Morbheg Knights
  FEC-017  Cryptguard
  FEC-018  Royal Beastflayers

The remaining 12 products have no MM listing — no records created for them.

Uses create_defaults for price and in_stock so scraper-set values survive
Railway redeploys.

Usage:
    python manage.py seed_mm_flesh_eater_courts_prices
"""

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Product, Retailer

_MM = 'https://www.miniaturemarket.com'

# (slug, listing_title, price, url, in_stock, not_available)
# price=None  → scraper will populate on first run
MM_PRICES = [

    # ⚠ Dual listing: FEC-004 / FEC-005 (Crypt Infernal Courtier / Crypt Haunter Courtier)
    #   share the same MM page — Crypt Flayers box (gw-91-13)
    (
        'crypt-infernal-courtier',
        'Crypt Flayers',
        None,
        f'{_MM}/gw-91-13.html',
        True,
        False,
    ),
    # ⚠ Dual listing: FEC-005 / FEC-004 share the same MM page
    (
        'crypt-haunter-courtier',
        'Crypt Flayers',
        None,
        f'{_MM}/gw-91-13.html',
        True,
        False,
    ),
    (
        'high-falconer-felgryn',
        'High Falconer Felgryn',
        None,
        f'{_MM}/warhammer-age-sigmar-flesh-eater-courts-high-falconer-felgryn-gw-91-87.html',
        True,
        False,
    ),
    (
        'abhorrant-cardinal',
        'Abhorrant Cardinal',
        None,
        f'{_MM}/warhammer-age-sigmar-flesh-eater-courts-abhorrant-cardinal-gw-91-72.html',
        True,
        False,
    ),
    (
        'grand-justice-gormayne',
        'Grand Justice Gormayne',
        None,
        f'{_MM}/warhammer-age-sigmar-flesh-eater-courts-grand-justice-gormayne-gw-91-70.html',
        True,
        False,
    ),
    (
        'royal-decapitator',
        'Royal Decapitator',
        None,
        f'{_MM}/warhammer-age-sigmar-flesh-eater-courts-royal-decapitator-gw-91-69.html',
        True,
        False,
    ),
    (
        'morbheg-knights',
        'Morbheg Knights',
        None,
        f'{_MM}/warhammer-age-sigmar-flesh-eater-courts-morbheg-knights-gw-91-77.html',
        True,
        False,
    ),
    (
        'cryptguard',
        'Cryptguard',
        None,
        f'{_MM}/warhammer-age-sigmar-flesh-eater-courts-cryptguard-gw-91-76.html',
        True,
        False,
    ),
    (
        'royal-beastflayers',
        'Royal Beastflayers Warband',
        None,
        f'{_MM}/warcry-royal-beastflayers-warband-gw-111-98.html',
        True,
        False,
    ),
]


class Command(BaseCommand):
    """Seed Miniature Market prices for Flesh-Eater Courts (9 products)."""

    help = 'Seeds MM CurrentPrice records for 9 FEC products with confirmed MM URLs.'

    def handle(self, *args, **options):
        """Run the command."""
        try:
            mm = Retailer.objects.get(name='Miniature Market')
        except Retailer.DoesNotExist:
            self.stderr.write(self.style.ERROR('Miniature Market retailer not found.'))
            return

        created_count = 0
        updated_count = 0

        for (slug, listing_title, price, url, in_stock, not_available) in MM_PRICES:
            try:
                product = Product.objects.get(slug=slug)
            except Product.DoesNotExist:
                self.stderr.write(self.style.WARNING(
                    f'  Product not found: {slug} — skipping'
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
            f'seed_mm_flesh_eater_courts_prices complete. '
            f'MM prices: {created_count} created, {updated_count} updated.'
        ))
