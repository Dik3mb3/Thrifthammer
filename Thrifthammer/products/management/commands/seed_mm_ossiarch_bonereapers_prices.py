"""
Management command: seed_mm_ossiarch_bonereapers_prices

Seeds Miniature Market CurrentPrice records for Ossiarch Bonereapers products
from the AOS Bonereapers - GW, NK, MM.xlsx (2026-06-10).

11 of 20 products have confirmed MM direct product URLs.
9 products have no MM listing -- no record created for those SKUs:
  - OBR-004  Mortisan Soulmason
  - OBR-006  Katakros, Mortarch of the Necropolis
  - OBR-008  Endless Spells: Ossiarch Bonereapers
  - OBR-009  Morghast Harbingers
  - OBR-010  Morghast Archai
  - OBR-011  Arkhan the Black, Mortarch of Sacrament
  - OBR-012  Mortisan Soulreaper
  - OBR-018  Mortek Crawler
  - OBR-020  Bone-tithe Nexus

Note: OBR-005 (Kavalos Deathriders) Excel had a /search?search= URL which was
discarded per policy; the correct direct URL (gw-94-27.html) was confirmed by
the user and is used here.

Uses create_defaults for price and in_stock so scraper-set values survive
Railway redeploys.

Usage:
    python manage.py seed_mm_ossiarch_bonereapers_prices
"""

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Product, Retailer

_MM = 'https://www.miniaturemarket.com/'

# (slug, listing_title, price, url, in_stock, not_available)
# price=None  -> scraper will populate on first run
# in_stock    -> initial assumption; scraper corrects as needed
MM_PRICES = [

    # -- Battleforces ----------------------------------------------------------
    (
        'battleforce-ossiarch-bonereapers-null-myriad-phalanx',
        'Ossiarch Bonereapers Battleforce: Null Myriad Phalanx',
        None,
        f'{_MM}Warhammer-Age-of-Sigmar-Ossiarch-Bonereapers-Battleforce-Null-Myriad-Phalanx-New-Arrival/GW-94-15-2026',
        True,
        False,
    ),

    # -- Regiments of Renown ---------------------------------------------------
    (
        'regiment-of-renown-heralds-of-the-bone-tithe',
        'Ossiarch Bonereapers: Heralds of the Bone-Tithe',
        None,
        f'{_MM}Warhammer-Age-of-Sigmar-Ossiarch-Bonereapers-Heralds-of-the-Bone-Tithe/GW-94-43-2026',
        True,
        False,
    ),

    # -- Heroes ----------------------------------------------------------------
    (
        'mortisan-ossifector',
        'Mortisan Ossifector',
        None,
        f'{_MM}warhammer-age-of-sigmar-ossiarch-bonereapers-mortisan-ossifector-gw-94-35.html',
        True,
        False,
    ),
    (
        'arch-kavalos-zandtos',
        'Arch-Kavalos Zandtos',
        None,
        f'{_MM}gw-94-30.html',
        True,
        False,
    ),
    (
        'liege-mortek',
        'Liege-Mortek',
        None,
        f'{_MM}Warhammer-Age-of-Sigmar-Ossiarch-Bonereapers-Liege-Mortek/GW-94-46-2026',
        True,
        False,
    ),
    (
        'liege-kavalos-on-war-chariot',
        'Liege-Kavalos on War Chariot',
        None,
        f'{_MM}Warhammer-Age-of-Sigmar-Ossiarch-Bonereapers-Liege-Kavalos-on-War-Chariot/GW-94-36-2026',
        True,
        False,
    ),
    (
        'mortisan-boneshaper',
        'Mortisan Boneshaper',
        None,
        f'{_MM}gw-94-22.html',
        True,
        False,
    ),

    # -- Units -----------------------------------------------------------------
    (
        'kavalos-deathriders',
        'Kavalos Deathriders',
        None,
        f'{_MM}gw-94-27.html',
        True,
        False,
    ),
    (
        'mortek-triaxes',
        'Mortek Triaxes',
        None,
        f'{_MM}Warhammer-Age-of-Sigmar-Ossiarch-Bonereapers-Mortek-Triaxes/GW-94-45-2026',
        True,
        False,
    ),

    # -- Warcry ----------------------------------------------------------------
    (
        'warcry-teratic-cohort',
        'Warcry: Teratic Cohort',
        None,
        f'{_MM}warcry-teratic-cohort-gw-112-22.html',
        True,
        False,
    ),

    # -- Battletome ------------------------------------------------------------
    (
        'death-battletome-ossiarch-bonereapers',
        'Death Battletome: Ossiarch Bonereapers',
        None,
        f'{_MM}Warhammer-Age-of-Sigmar-Death-Battletome-Ossiarch-Bonereapers/GW-94-01-2026',
        True,
        False,
    ),
]


class Command(BaseCommand):
    """Seed Miniature Market prices for Ossiarch Bonereapers (11 products)."""

    help = 'Seeds MM CurrentPrice records for OBR products with confirmed MM URLs (11 of 20).'

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
            f'seed_mm_ossiarch_bonereapers_prices complete. '
            f'MM prices: {created_count} created, {updated_count} updated.'
        ))
