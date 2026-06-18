"""
Management command: seed_mm_kharadron_overlords_prices

Seeds Miniature Market CurrentPrice records for Kharadron Overlords products
(KO-001 to KO-020) from the AOS Kharadron Overlords - GW, NK, MM.xlsx (2026-06-17).

12 of 20 products have confirmed MM URLs.
No MM entries for: KO-003 Endrinmaster with Dirigible Suit, KO-005 Skywardens,
KO-006 Aether-Khemist, KO-007 Brokk Grungsson, KO-008 Aetheric Navigator,
KO-013 Arkanaut Frigate, KO-014 Arkanaut Admiral, KO-020 Endrinmaster
with Endrinharness.

Dual-kit notes:
  - KO-005 Skywardens and KO-009 Endrinriggers share the same physical
    Skyriggers kit. Only Endrinriggers has an MM listing (gw-84-36).

Uses create_defaults for price and in_stock so scraper-set values survive
Railway redeploys.

Usage:
    python manage.py seed_mm_kharadron_overlords_prices
"""

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Product, Retailer

_MM = 'https://www.miniaturemarket.com'

# (slug, listing_title, price, url, in_stock, not_available)
# price=None  -> scraper will populate on first run
# in_stock    -> initial assumption; scraper corrects as needed
MM_PRICES = [

    # -- Spearhead -------------------------------------------------------------
    (
        'spearhead-kharadron-overlords-grundstok-trailblazers',
        'Spearhead: Kharadron Overlords – Grundstok Trailblazers',
        None,
        f'{_MM}/warhammer-age-sigmar-spearhead-kharadron-overlords-grundstok-trailblazers-gw-70-843.html',
        True,
        False,
    ),

    # -- Heroes ----------------------------------------------------------------
    (
        'codewright',
        'Codewright',
        None,
        f'{_MM}/warhammer-age-of-sigmar-kharadron-overlords-codewright-gw-84-61.html',
        True,
        False,
    ),
    (
        'drekki-flynt',
        'Drekki Flynt',
        None,
        f'{_MM}/gw-84-49.html',
        True,
        False,
    ),
    (
        'null-khemist',
        'Null-Khemist',
        None,
        f'{_MM}/warhammer-age-sigmar-kharadron-overlords-null-khemist-gw-84-53.html',
        True,
        False,
    ),

    # -- Units -----------------------------------------------------------------
    # ⚠ Dual kit: Skywardens and Endrinriggers share the same Skyriggers kit.
    #   Only Endrinriggers has an MM listing.
    (
        'endrinriggers',
        'Skyriggers / Endrinriggers',
        None,
        f'{_MM}/gw-84-36.html',
        True,
        False,
    ),
    (
        'grundstok-thunderers',
        'Grundstok Thunderers',
        None,
        f'{_MM}/gw-84-37.html',
        True,
        False,
    ),
    (
        'arkanaut-company',
        'Arkanaut Company',
        None,
        f'{_MM}/gw-84-35.html',
        True,
        False,
    ),
    (
        'vongrim-harpoon-crew',
        'Vongrim Harpoon Crew',
        None,
        f'{_MM}/warhammer-age-sigmar-kharadron-overlords-vongrim-harpoon-crew-gw-84-52.html',
        True,
        False,
    ),

    # -- Large Kits / Vessels --------------------------------------------------
    (
        'arkanaut-ironclad',
        'Arkanaut Ironclad',
        None,
        f'{_MM}/gw-84-40.html',
        True,
        False,
    ),
    (
        'grundstok-gunhauler',
        'Grundstok Gunhauler',
        None,
        f'{_MM}/gw-84-38.html',
        True,
        False,
    ),

    # -- Terrain / Scenery -----------------------------------------------------
    (
        'zontari-endrin-dock',
        'Zontari Endrin Dock',
        None,
        f'{_MM}/warhammer-age-sigmar-kharadron-overlords-zontari-endrin-dock-gw-84-66.html',
        True,
        False,
    ),

    # -- Battletome ------------------------------------------------------------
    (
        'order-battletome-kharadron-overlords',
        'Order Battletome: Kharadron Overlords',
        None,
        f'{_MM}/warhammer-age-sigmar-order-battletome-kharadron-overlords-gw-84-02.html',
        True,
        False,
    ),
]


class Command(BaseCommand):
    """Seed Miniature Market prices for Kharadron Overlords (12 of 20 products have MM URLs)."""

    help = 'Seeds MM CurrentPrice records for KO-001 to KO-020 (12 products have MM URLs).'

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
            f'seed_mm_kharadron_overlords_prices complete. '
            f'MM prices: {created_count} created, {updated_count} updated.'
        ))
