"""
Seed Archon Studio US MSRP prices for StarCraft.

Creates the `archon-studio` Retailer (US, is_uk=False) if it does not exist
-- distinct from the existing UK-only `archon-studio-uk` retailer
(is_uk=True), same is_uk split convention as steamforged-games /
steamforged-games-uk and mantic-games / mantic-games-uk.

All 25 StarCraft products (SC-001..SC-025) were created UK-first by
populate_starcraft_products.py with no US price at all. This command adds
the US side: product.msrp (create-only guard, same rule as every other
MSRP-source retailer -- never resets a value a live updater may have since
changed). Archon Studio's own store (starcraft-tmg.com) is the same single
official publisher source already approved as this category's MSRP
retailer for the UK side, just switched to United States (USD) -- same
site, same URLs, region-dependent price only.

Source: user-supplied "Starcraft - Archon U.S Prices.xlsx" (same 25 rows,
same Title_URL column, as the earlier UK sheet). Spot-verified live:
switched starcraft-tmg.com's own region selector to United States and
confirmed Hydralisk = $49.00, matching the sheet exactly (same page that
showed GBP 35.00 under the UK region during the earlier UK seed).

All 25 rows are marked "Add to cart" on the sheet (including the 9
"pre-orders" section items) -- in_stock=True for all, same as the UK side.

Run once on Railway startup via Procfile. Safe to re-run -- idempotent.
"""
from decimal import Decimal

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Product, Retailer

_ARCHON_US_SLUG = 'archon-studio'

# (gw_sku, usd_price, url, in_stock)
_PRICES = [
    ('SC-001', Decimal('49.00'), 'https://starcraft-tmg.com/shop/products/starcraft-r-hydralisk', True),
    ('SC-002', Decimal('49.00'), 'https://starcraft-tmg.com/shop/products/starcraft-zergling', True),
    ('SC-003', Decimal('49.00'), 'https://starcraft-tmg.com/shop/products/starcraft-roach', True),
    ('SC-004', Decimal('35.00'), 'https://starcraft-tmg.com/shop/products/starcraft-queen', True),
    ('SC-005', Decimal('49.00'), 'https://starcraft-tmg.com/shop/products/starcraft-kerrigan-omega-worm', True),
    ('SC-006', Decimal('49.00'), 'https://starcraft-tmg.com/shop/products/starcraft-marine', True),
    ('SC-007', Decimal('49.00'), 'https://starcraft-tmg.com/shop/products/starcraft-marauder', True),
    ('SC-008', Decimal('29.00'), 'https://starcraft-tmg.com/shop/products/starcraft-medic', True),
    ('SC-009', Decimal('49.00'), 'https://starcraft-tmg.com/shop/products/starcraft-goliath', True),
    ('SC-010', Decimal('39.00'), 'https://starcraft-tmg.com/shop/products/starcraft-jim-raynor-point-defense-drone', True),
    ('SC-011', Decimal('39.00'), 'https://starcraft-tmg.com/shop/products/starcraft-zealot', True),
    ('SC-012', Decimal('39.00'), 'https://starcraft-tmg.com/shop/products/starcraft-adepts', True),
    ('SC-013', Decimal('35.00'), 'https://starcraft-tmg.com/shop/products/starcraft-sentry', True),
    ('SC-014', Decimal('49.00'), 'https://starcraft-tmg.com/shop/products/starcraft-stalker', True),
    ('SC-015', Decimal('49.00'), 'https://starcraft-tmg.com/shop/products/starcraft-artanis-pylon', True),
    ('SC-016', Decimal('49.00'), 'https://starcraft-tmg.com/shop/products/starcraft-lost-temple', True),
    ('SC-017', Decimal('129.00'), 'https://starcraft-tmg.com/shop/pre-orders/starcraft-protoss-starter-set', True),
    ('SC-018', Decimal('119.00'), 'https://starcraft-tmg.com/shop/pre-orders/starcraft-zerg-starter-set', True),
    ('SC-019', Decimal('119.00'), 'https://starcraft-tmg.com/shop/pre-orders/starcraft-terran-starter-set', True),
    ('SC-020', Decimal('59.00'), 'https://starcraft-tmg.com/shop/pre-orders/starcraft-ravager-zerg-expansion-set', True),
    ('SC-021', Decimal('69.00'), 'https://starcraft-tmg.com/shop/pre-orders/starcraft-immortal-protoss-expansion-set', True),
    ('SC-022', Decimal('79.00'), 'https://starcraft-tmg.com/shop/pre-orders/starcraft-siege-tank-terran-expansion-set', True),
    ('SC-023', Decimal('39.00'), 'https://starcraft-tmg.com/shop/pre-orders/starcraft-zeratul-protoss-hero-expansion-set', True),
    ('SC-024', Decimal('39.00'), 'https://starcraft-tmg.com/shop/pre-orders/starcraft-lost-temple-ramp-terrain-expansion-set', True),
    ('SC-025', Decimal('9.99'), 'https://starcraft-tmg.com/shop/pre-orders/starcraft-rulebook', True),
]


class Command(BaseCommand):
    help = 'Seed Archon Studio US MSRP prices and URLs for StarCraft. Idempotent.'

    def handle(self, *args, **options):
        retailer, created = Retailer.objects.get_or_create(
            slug=_ARCHON_US_SLUG,
            defaults={
                'name': 'Archon Studio',
                'website': 'https://starcraft-tmg.com',
                'country': 'US',
                'is_active': True,
                'is_uk': False,
            },
        )
        if created:
            self.stdout.write(f'Created retailer: {retailer.name}')

        seeded = 0
        skipped = 0
        for gw_sku, usd_price, url, in_stock in _PRICES:
            try:
                product = Product.objects.get(gw_sku=gw_sku)
            except Product.DoesNotExist:
                self.stderr.write(f'SKIP — SKU {gw_sku} not in DB')
                skipped += 1
                continue

            if product.msrp is None:
                product.msrp = usd_price
                product.save(update_fields=['msrp'])

            cp_defaults = {'url': url, 'in_stock': in_stock, 'not_available': False, 'currency': 'USD'}
            CurrentPrice.objects.update_or_create(
                product=product,
                retailer=retailer,
                defaults=cp_defaults,
                create_defaults={**cp_defaults, 'price': usd_price},
            )
            seeded += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Seeded {seeded} StarCraft Archon Studio US prices. Skipped: {skipped}.'
            )
        )
