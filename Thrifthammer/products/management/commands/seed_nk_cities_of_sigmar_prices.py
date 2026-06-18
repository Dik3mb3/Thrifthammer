"""
Management command: seed_nk_cities_of_sigmar_prices

Seeds Noble Knight CurrentPrice records for Cities of Sigmar products
(COS-001 to COS-027) from the AOS Cities of Sigmar - GW, NK, MM.xlsx (2026-06-17).

24 of 27 products have confirmed NK URLs.
No NK entries for: COS-003 Mallus Forgepriest, COS-004 Jorvan Kreel,
COS-026 Luminark of Hysh.

Dual-kit notes:
  - COS-010 Conqueror Cogfort and COS-011 Cannonade Cogfort share one NK listing.

Affiliate tag ?awid=1576 appended to all NK URLs.
Uses create_defaults for price and in_stock so scraper-set values survive
Railway redeploys.

Usage:
    python manage.py seed_nk_cities_of_sigmar_prices
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

    # -- Regiments of Renown ---------------------------------------------------
    (
        'regiment-of-renown-ven-densts-hounds',
        "Regiments of Renown - Ven Denst's Hounds",
        None,
        f'{_NK}/P/2148470044/Regiments-of-Renown---Ven-Densts-Hounds{_AFF}',
        True,
        False,
    ),

    # -- Large Kits ------------------------------------------------------------
    (
        'gate-gargants',
        'Gate Gargants',
        None,
        f'{_NK}/P/2148470035/Gate-Gargants{_AFF}',
        True,
        False,
    ),
    # ⚠ Dual kit: Conqueror Cogfort and Cannonade Cogfort share one NK listing.
    (
        'conqueror-cogfort',
        'Cannonade Cogfort',
        None,
        f'{_NK}/P/2148470009/Cannonade-Cogfort{_AFF}',
        True,
        False,
    ),
    (
        'cannonade-cogfort',
        'Cannonade Cogfort',
        None,
        f'{_NK}/P/2148470009/Cannonade-Cogfort{_AFF}',
        True,
        False,
    ),
    (
        'tahlia-vedra-lioness-of-the-parch',
        'Tahlia Vedra - Lioness of the Parch',
        None,
        f'{_NK}/P/2148095302/Tahlia-Vedra---Lioness-of-the-Parch{_AFF}',
        True,
        False,
    ),

    # -- Heroes ----------------------------------------------------------------
    (
        'aqshian-pyrocaster',
        'Aqshian Pyrocaster',
        None,
        f'{_NK}/P/2148470079/Aqshian-Pyrocaster{_AFF}',
        True,
        False,
    ),
    (
        'amethyst-knellmage',
        'Amethyst Knellmage',
        None,
        f'{_NK}/P/2148470083/Amethyst-Knellmage{_AFF}',
        True,
        False,
    ),
    (
        'erasmus-zonn-the-enlightened-one',
        'Erasmus Zonn - The Enlightened One',
        None,
        f'{_NK}/P/2148470046/Erasmus-Zonn---The-Enlightened-One{_AFF}',
        True,
        False,
    ),
    (
        'dawners-triumph',
        "Dawner's Triumph",
        None,
        f'{_NK}/P/2148470020/Dawners-Triumph{_AFF}',
        True,
        False,
    ),
    (
        'galen-and-doralia-ven-denst',
        'Galen and Doralia Ven Denst',
        None,
        f'{_NK}/P/2148137671/Galen-and-Doralia-Ven-Denst{_AFF}',
        True,
        False,
    ),
    (
        'pontifex-zenestra-matriarch-of-the-great-wheel',
        'Pontifex Zenestra - Matriarch of the Great Wheel',
        None,
        f'{_NK}/P/2148095388/Pontifex-Zenestra---Matriarch-of-the-Great-Wheel{_AFF}',
        True,
        False,
    ),
    (
        'fusil-major-on-ogor-warhulk',
        'Fusil-Major on Ogor Warhulk',
        None,
        f'{_NK}/P/2148095386/Fusil-Major-on-Ogor-Warhulk{_AFF}',
        True,
        False,
    ),
    (
        'freeguild-marshal-and-relic-envoy',
        'Freeguild Marshal and Relic Envoy Webstore Edition',
        None,
        f'{_NK}/P/2148217555/Freeguild-Marshal-and-Relic-Envoy-Webstore-Edition{_AFF}',
        True,
        False,
    ),
    (
        'alchemite-warforger',
        'Alchemite Warforger Webstore Edition',
        None,
        f'{_NK}/P/2148217550/Alchemite-Warforger-Webstore-Edition{_AFF}',
        True,
        False,
    ),
    (
        'freeguild-cavalier-marshal',
        'Freeguild Cavalier-Marshal',
        None,
        f'{_NK}/P/2148095373/Freeguild-Cavalier-Marshal{_AFF}',
        True,
        False,
    ),

    # -- Units -----------------------------------------------------------------
    (
        'freeguild-grenadiers',
        'Freeguild Grenadiers',
        None,
        f'{_NK}/P/2148470043/Freeguild-Grenadiers{_AFF}',
        True,
        False,
    ),
    (
        'freeguild-gallants',
        'Freeguild Gallants',
        None,
        f'{_NK}/P/2148470042/Freeguild-Gallants{_AFF}',
        True,
        False,
    ),
    (
        'wildercorps-hunters',
        'Wildercorps Hunters',
        None,
        f'{_NK}/P/2148134396/Wildercorps-Hunters{_AFF}',
        True,
        False,
    ),
    (
        'saviours-of-cinderfall',
        'Saviours of Cinderfall',
        None,
        f'{_NK}/P/2148407901/Saviours-of-Cinderfall{_AFF}',
        True,
        False,
    ),
    (
        'ironweld-great-cannon',
        'Ironweld Great Cannon',
        None,
        f'{_NK}/P/2148095376/Ironweld-Great-Cannon{_AFF}',
        True,
        False,
    ),
    (
        'freeguild-steelhelms',
        'Freeguild Steelhelms',
        None,
        f'{_NK}/P/2148095379/Freeguild-Steelhelms{_AFF}',
        True,
        False,
    ),
    (
        'freeguild-command-corps',
        'Freeguild Command Corps',
        None,
        f'{_NK}/P/2148095369/Freeguild-Command-Corps{_AFF}',
        True,
        False,
    ),
    (
        'freeguild-cavaliers',
        'Freeguild Cavaliers',
        None,
        f'{_NK}/P/2148095383/Freeguild-Cavaliers{_AFF}',
        True,
        False,
    ),

    # -- Battletome ------------------------------------------------------------
    (
        'order-battletome-cities-of-sigmar',
        'Order Battletome - Cities of Sigmar',
        None,
        f'{_NK}/P/2148470058/Order-Battletome---Cities-of-Sigmar{_AFF}',
        True,
        False,
    ),
]


class Command(BaseCommand):
    """Seed Noble Knight prices for Cities of Sigmar (24 of 27 products have NK URLs)."""

    help = 'Seeds NK CurrentPrice records for COS-001 to COS-027 (24 products have NK URLs).'

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
            f'seed_nk_cities_of_sigmar_prices complete. '
            f'NK prices: {created_count} created, {updated_count} updated.'
        ))
