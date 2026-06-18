"""
Management command: seed_nk_kharadron_overlords_prices

Seeds Noble Knight CurrentPrice records for Kharadron Overlords products
(KO-001 to KO-020) from the AOS Kharadron Overlords - GW, NK, MM.xlsx (2026-06-17).

19 of 20 products have confirmed NK URLs.
No NK entries for: KO-007 Brokk Grungsson, Lord-Magnate of Barak-Nar.

Dual-kit notes:
  - KO-005 Skywardens and KO-009 Endrinriggers share the same physical
    Skyriggers kit but have separate NK listings.

Affiliate tag ?awid=1576 appended to all NK URLs.
Uses create_defaults for price and in_stock so scraper-set values survive
Railway redeploys.

Usage:
    python manage.py seed_nk_kharadron_overlords_prices
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

    # -- Spearhead -------------------------------------------------------------
    (
        'spearhead-kharadron-overlords-grundstok-trailblazers',
        'Grundstok Trailblazers',
        None,
        f'{_NK}/P/2148330187/Grundstok-Trailblazers{_AFF}',
        True,
        False,
    ),

    # -- Heroes ----------------------------------------------------------------
    (
        'codewright',
        'Codewright',
        None,
        f'{_NK}/P/2148039156/Codewright{_AFF}',
        True,
        False,
    ),
    (
        'endrinmaster-with-dirigible-suit',
        'Endrinmaster in Dirigible Suit',
        None,
        f'{_NK}/P/2147841745/Endrinmaster-in-Dirigible-Suit{_AFF}',
        True,
        False,
    ),
    (
        'aether-khemist',
        'Aether-Khemist',
        None,
        f'{_NK}/P/2147664254/Aether-Khemist{_AFF}',
        True,
        False,
    ),
    (
        'aetheric-navigator',
        'Aetheric Navigator',
        None,
        f'{_NK}/P/2147663629/Aetheric-Navigator{_AFF}',
        True,
        False,
    ),
    (
        'arkanaut-admiral',
        'Arkanaut Admiral',
        None,
        f'{_NK}/P/2147662396/Arkanaut-Admiral{_AFF}',
        True,
        False,
    ),
    (
        'drekki-flynt',
        'Drekki Flynt',
        None,
        f'{_NK}/P/2147997396/Drekki-Flynt{_AFF}',
        True,
        False,
    ),
    (
        'endrinmaster-with-endrinharness',
        'Endrinmaster',
        None,
        f'{_NK}/P/2147664251/Endrinmaster{_AFF}',
        True,
        False,
    ),
    (
        'null-khemist',
        'Null-Khemist',
        None,
        f'{_NK}/P/2148330246/Null-Khemist{_AFF}',
        True,
        False,
    ),

    # -- Units -----------------------------------------------------------------
    # ⚠ Dual kit: Skywardens and Endrinriggers share the same Skyriggers kit but
    #   have separate NK listings.
    (
        'skywardens',
        'Skywardens',
        None,
        f'{_NK}/P/2148067845/Skywardens{_AFF}',
        True,
        False,
    ),
    (
        'endrinriggers',
        'Skyriggers',
        None,
        f'{_NK}/P/2147664221/Skyriggers-2017-Edition{_AFF}',
        True,
        False,
    ),
    (
        'grundstok-thunderers',
        'Grundstok Thunderers',
        None,
        f'{_NK}/P/2148324337/Grundstok-Thunderers-2023-Edition{_AFF}',
        True,
        False,
    ),
    (
        'arkanaut-company',
        'Arkanaut Company',
        None,
        f'{_NK}/P/2148286448/Arkanaut-Company{_AFF}',
        True,
        False,
    ),
    (
        'vongrim-harpoon-crew',
        'Vongrim Harpoon Crew',
        None,
        f'{_NK}/P/2148330196/Vongrim-Harpoon-Crew{_AFF}',
        True,
        False,
    ),

    # -- Large Kits / Vessels --------------------------------------------------
    (
        'arkanaut-ironclad',
        'Arkanaut Ironclad',
        None,
        f'{_NK}/P/2147663613/Arkanaut-Ironclad-2017-Edition{_AFF}',
        True,
        False,
    ),
    (
        'grundstok-gunhauler',
        'Grundstok Gunhauler',
        None,
        f'{_NK}/P/2147662402/Grundstok-Gunhauler-2017-Edition{_AFF}',
        True,
        False,
    ),
    (
        'arkanaut-frigate',
        'Arkanaut Frigate',
        None,
        f'{_NK}/P/2147662398/Arkanaut-Frigate{_AFF}',
        True,
        False,
    ),

    # -- Terrain / Scenery -----------------------------------------------------
    (
        'zontari-endrin-dock',
        'Zontari Endrin Dock',
        None,
        f'{_NK}/P/2148330181/Zontari-Endrin-Dock{_AFF}',
        True,
        False,
    ),

    # -- Battletome ------------------------------------------------------------
    (
        'order-battletome-kharadron-overlords',
        'Order Battletome: Kharadron Overlords',
        None,
        f'{_NK}/P/2148330263/Order-Battletome---Kharadron-Overlords{_AFF}',
        True,
        False,
    ),
]


class Command(BaseCommand):
    """Seed Noble Knight prices for Kharadron Overlords (19 of 20 products have NK URLs)."""

    help = 'Seeds NK CurrentPrice records for KO-001 to KO-020 (19 products have NK URLs).'

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
            f'seed_nk_kharadron_overlords_prices complete. '
            f'NK prices: {created_count} created, {updated_count} updated.'
        ))
