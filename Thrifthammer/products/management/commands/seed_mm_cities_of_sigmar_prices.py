"""
Management command: seed_mm_cities_of_sigmar_prices

Seeds Miniature Market CurrentPrice records for Cities of Sigmar products
(COS-001 to COS-027) from the AOS Cities of Sigmar - GW, NK, MM.xlsx (2026-06-17).

21 of 27 products have confirmed MM URLs.
No MM entries for: COS-003 Mallus Forgepriest, COS-004 Jorvan Kreel,
COS-015 Wildercorps Hunters, COS-020 Freeguild Marshal and Relic Envoy,
COS-025 Alchemite Warforger, COS-026 Luminark of Hysh.

Dual-kit notes:
  - COS-010 Conqueror Cogfort and COS-011 Cannonade Cogfort share one MM listing.

Uses create_defaults for price and in_stock so scraper-set values survive
Railway redeploys.

Usage:
    python manage.py seed_mm_cities_of_sigmar_prices
"""

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Product, Retailer

_MM = 'https://www.miniaturemarket.com'

# (slug, listing_title, price, url, in_stock, not_available)
# price=None  -> scraper will populate on first run
# in_stock    -> initial assumption; scraper corrects as needed
MM_PRICES = [

    # -- Regiments of Renown ---------------------------------------------------
    (
        'regiment-of-renown-ven-densts-hounds',
        "Regiments of Renown - Cities of Sigmar Ven Denst's Hounds",
        None,
        f'{_MM}/Warhammer-Age-of-Sigmar-Regiments-of-Renown-Cities-of-Sigmar-Ven-Denst-s-Hounds-New-Arrival/GW-86-90-2026',
        True,
        False,
    ),

    # -- Large Kits ------------------------------------------------------------
    (
        'gate-gargants',
        'Cities of Sigmar Gate Gargants',
        None,
        f'{_MM}/Warhammer-Age-of-Sigmar-Cities-of-Sigmar-Gate-Gargants-New-Arrival/GW-86-53-2026',
        True,
        False,
    ),
    # ⚠ Dual kit: Conqueror Cogfort and Cannonade Cogfort share one MM listing.
    (
        'conqueror-cogfort',
        'Cities of Sigmar Cannonade Cogfort',
        None,
        f'{_MM}/Warhammer-Age-of-Sigmar-Cities-of-Sigmar-Cannonade-Cogfort-New-Arrival/GW-86-15-2026',
        True,
        False,
    ),
    (
        'cannonade-cogfort',
        'Cities of Sigmar Cannonade Cogfort',
        None,
        f'{_MM}/Warhammer-Age-of-Sigmar-Cities-of-Sigmar-Cannonade-Cogfort-New-Arrival/GW-86-15-2026',
        True,
        False,
    ),
    (
        'tahlia-vedra-lioness-of-the-parch',
        'Cities of Sigmar Tahlia Vedra Lioness of the Parch',
        None,
        f'{_MM}/warhammer-age-sigmar-cities-sigmar-tahlia-vedra-lioness-parch-gw-86-18.html',
        True,
        False,
    ),

    # -- Heroes ----------------------------------------------------------------
    (
        'aqshian-pyrocaster',
        'Cities of Sigmar Aqshian Pyrocaster',
        None,
        f'{_MM}/Warhammer-Age-of-Sigmar-Cities-of-Sigmar-Aqshian-Pyrocaster-New-Arrival/GW-86-14-2026',
        True,
        False,
    ),
    (
        'amethyst-knellmage',
        'Cities of Sigmar Amethyst Knellmage',
        None,
        f'{_MM}/Warhammer-Age-of-Sigmar-Cities-of-Sigmar-Amethyst-Knellmage-New-Arrival/GW-86-13-2026',
        True,
        False,
    ),
    (
        'erasmus-zonn-the-enlightened-one',
        'Cities of Sigmar Erasmus Zonn the Enlightened One',
        None,
        f'{_MM}/Warhammer-Age-of-Sigmar-Cities-of-Sigmar-Erasmus-Zonn-the-Enlightened-One-New-Arrival/GW-86-10-2026',
        True,
        False,
    ),
    (
        'dawners-triumph',
        "Cities of Sigmar Dawner's Triumph",
        None,
        f'{_MM}/Warhammer-Age-of-Sigmar-Cities-of-Sigmar-Dawner-s-Triumph-New-Arrival/GW-86-50-2026',
        True,
        False,
    ),
    (
        'galen-and-doralia-ven-denst',
        'Galen and Doralia Ven Denst',
        None,
        f'{_MM}/gw-86-45.html',
        True,
        False,
    ),
    (
        'pontifex-zenestra-matriarch-of-the-great-wheel',
        'Cities of Sigmar Pontifex Zenestra Matriarch of the Great Wheel',
        None,
        f'{_MM}/warhammer-age-sigmar-cities-sigmar-pontifex-zenestra-matriarch-great-wheel-gw-86-27.html',
        True,
        False,
    ),
    (
        'fusil-major-on-ogor-warhulk',
        'Cities of Sigmar Fusil-Major on Ogor Warhulk',
        None,
        f'{_MM}/warhammer-age-sigmar-cities-sigmar-fusil-major-on-ogor-warhulk-gw-86-20.html',
        True,
        False,
    ),
    (
        'freeguild-cavalier-marshal',
        'Cities of Sigmar Freeguild Cavalier-Marshal',
        None,
        f'{_MM}/warhammer-age-sigmar-cities-sigmar-freeguild-cavalier-marshal-gw-86-05-2023.html',
        True,
        False,
    ),

    # -- Units -----------------------------------------------------------------
    (
        'freeguild-grenadiers',
        'Cities of Sigmar Freeguild Grenadiers',
        None,
        f'{_MM}/Warhammer-Age-of-Sigmar-Cities-of-Sigmar-Freeguild-Grenadiers-New-Arrival/GW-86-54-2026',
        True,
        False,
    ),
    (
        'freeguild-gallants',
        'Cities of Sigmar Freeguild Gallants',
        None,
        f'{_MM}/Warhammer-Age-of-Sigmar-Cities-of-Sigmar-Freeguild-Gallants-New-Arrival/GW-86-08-2026',
        True,
        False,
    ),
    (
        'saviours-of-cinderfall',
        'Callis & Toll Saviours of Cinderfall',
        None,
        f'{_MM}/warhammer-age-sigmar-callis-toll-saviours-cinderfall-gw-86-36.html',
        True,
        False,
    ),
    (
        'ironweld-great-cannon',
        'Cities of Sigmar Ironweld Great Cannon',
        None,
        f'{_MM}/warhammer-age-sigmar-cities-sigmar-ironweld-great-cannon-gw-86-11.html',
        True,
        False,
    ),
    (
        'freeguild-steelhelms',
        'Cities of Sigmar Freeguild Steelhelms',
        None,
        f'{_MM}/warhammer-age-sigmar-cities-sigmar-freeguild-steelhelms-gw-86-06-2023.html',
        True,
        False,
    ),
    (
        'freeguild-command-corps',
        'Cities of Sigmar Freeguild Command Corps',
        None,
        f'{_MM}/warhammer-age-sigmar-cities-sigmar-freeguild-command-corps-gw-86-12-2023.html',
        True,
        False,
    ),
    (
        'freeguild-cavaliers',
        'Cities of Sigmar Freeguild Cavaliers',
        None,
        f'{_MM}/warhammer-age-sigmar-cities-sigmar-freeguild-cavaliers-gw-86-07.html',
        True,
        False,
    ),

    # -- Battletome ------------------------------------------------------------
    (
        'order-battletome-cities-of-sigmar',
        'Battletome Cities of Sigmar',
        None,
        f'{_MM}/Warhammer-Age-of-Sigmar-Battletome-Cities-of-Sigmar-New-Arrival/GW-86-47-2026',
        True,
        False,
    ),
]


class Command(BaseCommand):
    """Seed Miniature Market prices for Cities of Sigmar (21 of 27 products have MM URLs)."""

    help = 'Seeds MM CurrentPrice records for COS-001 to COS-027 (21 products have MM URLs).'

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
            f'seed_mm_cities_of_sigmar_prices complete. '
            f'MM prices: {created_count} created, {updated_count} updated.'
        ))
