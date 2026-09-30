"""
Seed Firestorm Games UK prices for StarCraft.

Idempotent -- CurrentPrice rows are written via update_or_create keyed on
(product, retailer), price is create-only (see create_defaults below) so a
redeploy never resets a price a manual correction or future live updater
has since changed. NEVER writes msrp_gbp -- Firestorm is a discount
competitor here, not the MSRP source; archon-studio-uk holds that role for
StarCraft (see populate_starcraft_products.py).

Price parsing rule: Firestorm shows two numbers per listing (struck-through
RRP, then sale price). ALWAYS use the lower (sale) price, never the RRP.

Source: https://www.firestormgames.co.uk/wargames-miniatures/starcraft-
(27 listings, 1 page). Each match verified by pairing product title text
with its href directly via JS (not list position).

All 25 of 25 catalog SKUs matched -- full coverage, no gaps. 2 listings
excluded, not gaps -- same "Founders Edition" pattern already caught on
every other retailer for this category:
- "Starcraft - Protoss Starter Set Founders Edition" (GBP 89.10) -- the
  richer/different bundle, not our SC-017.
- "Starcraft - Two Player Starter Set Founders Edition" (GBP 152.10) -- a
  bundle of both single-faction starter sets, not a single SKU.

9 of the 25 matched listings are Firestorm "PRE ORDER" items (Dispatch
Expected 05/10/2026) for the same Wave 2 batch seen at every other
retailer -- recorded with in_stock=True, same live-purchasable-preorder
convention used throughout this catalog.

Every URL carries Firestorm's affiliate code (?aff=6a4ab07d1c6f9) per
standing site policy -- never break this on any Firestorm URL, including
retroactively.

Run once on Railway startup via Procfile. Safe to re-run -- idempotent.
"""
from decimal import Decimal

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Product, Retailer

_FIRESTORM_SLUG = 'firestorm-games'

# (gw_sku, gbp_price, url, in_stock)
_PRICES = [
    ('SC-001', Decimal('31.50'), 'https://www.firestormgames.co.uk/starcraft-zerg-hydralisk-expansion-set?aff=6a4ab07d1c6f9', True),
    ('SC-002', Decimal('31.50'), 'https://www.firestormgames.co.uk/starcraft-zerg-zergling-expansion-set?aff=6a4ab07d1c6f9', True),
    ('SC-003', Decimal('31.50'), 'https://www.firestormgames.co.uk/starcraft-zerg-roach-expansion-set?aff=6a4ab07d1c6f9', True),
    ('SC-004', Decimal('22.50'), 'https://www.firestormgames.co.uk/starcraft-zerg-queen-expansion-set?aff=6a4ab07d1c6f9', True),
    ('SC-005', Decimal('31.50'), 'https://www.firestormgames.co.uk/starcraft-zerg-kerrigan-primal-kerrigan-hero-expansion-set?aff=6a4ab07d1c6f9', True),
    ('SC-006', Decimal('31.50'), 'https://www.firestormgames.co.uk/starcraft-terran-marine-expansion-set?aff=6a4ab07d1c6f9', True),
    ('SC-007', Decimal('31.50'), 'https://www.firestormgames.co.uk/starcraft-terran-marauder-expansion-set?aff=6a4ab07d1c6f9', True),
    ('SC-008', Decimal('19.80'), 'https://www.firestormgames.co.uk/starcraft-terran-medic-expansion-set?aff=6a4ab07d1c6f9', True),
    ('SC-009', Decimal('31.50'), 'https://www.firestormgames.co.uk/starcraft-terran-goliath-expansion-set?aff=6a4ab07d1c6f9', True),
    ('SC-010', Decimal('26.10'), 'https://www.firestormgames.co.uk/starcraft-terran-jim-raynor-raynors-raiders-hero-expansion-set?aff=6a4ab07d1c6f9', True),
    ('SC-011', Decimal('26.10'), 'https://www.firestormgames.co.uk/starcraft-protoss-zealot-expansion-set?aff=6a4ab07d1c6f9', True),
    ('SC-012', Decimal('26.10'), 'https://www.firestormgames.co.uk/starcraft-protoss-adept-expansion-set?aff=6a4ab07d1c6f9', True),
    ('SC-013', Decimal('22.50'), 'https://www.firestormgames.co.uk/starcraft-protoss-sentry-expansion-set?aff=6a4ab07d1c6f9', True),
    ('SC-014', Decimal('31.50'), 'https://www.firestormgames.co.uk/starcraft-protoss-stalker-expansion-set?aff=6a4ab07d1c6f9', True),
    ('SC-015', Decimal('31.50'), 'https://www.firestormgames.co.uk/starcraft-protoss-artanis-hierarch-hero-expansion-set?aff=6a4ab07d1c6f9', True),
    ('SC-016', Decimal('31.50'), 'https://www.firestormgames.co.uk/starcraft-lost-temple-terrain-expansion-set?aff=6a4ab07d1c6f9', True),
    ('SC-017', Decimal('85.50'), 'https://www.firestormgames.co.uk/starcraft-protoss-starter-set?aff=6a4ab07d1c6f9', True),
    ('SC-018', Decimal('80.10'), 'https://www.firestormgames.co.uk/starcraft-zerg-starter-set?aff=6a4ab07d1c6f9', True),
    ('SC-019', Decimal('80.10'), 'https://www.firestormgames.co.uk/starcraft-terran-starter-set?aff=6a4ab07d1c6f9', True),
    ('SC-020', Decimal('40.50'), 'https://www.firestormgames.co.uk/starcraft-zerg-ravager-expansion-set?aff=6a4ab07d1c6f9', True),
    ('SC-021', Decimal('44.10'), 'https://www.firestormgames.co.uk/starcraft-protoss-immortal-expansion-set?aff=6a4ab07d1c6f9', True),
    ('SC-022', Decimal('53.10'), 'https://www.firestormgames.co.uk/starcraft-terran-siege-tank-expansion-set?aff=6a4ab07d1c6f9', True),
    ('SC-023', Decimal('26.10'), 'https://www.firestormgames.co.uk/starcraft-protoss-zeratul-hero-expansion-set?aff=6a4ab07d1c6f9', True),
    ('SC-024', Decimal('26.10'), 'https://www.firestormgames.co.uk/starcraft-lost-temple-ramp-terrain-expansion-set?aff=6a4ab07d1c6f9', True),
    ('SC-025', Decimal('6.75'), 'https://www.firestormgames.co.uk/starcraft-rulebook-103505?aff=6a4ab07d1c6f9', True),
]


class Command(BaseCommand):
    help = 'Seed Firestorm Games UK prices and URLs for StarCraft. Idempotent.'

    def handle(self, *args, **options):
        retailer, created = Retailer.objects.get_or_create(
            slug=_FIRESTORM_SLUG,
            defaults={
                'name': 'Firestorm Games',
                'website': 'https://www.firestormgames.co.uk/?aff=6a4ab07d1c6f9',
                'country': 'UK',
                'is_active': True,
                'is_uk': True,
            },
        )
        if created:
            self.stdout.write(f'Created retailer: {retailer.name}')

        seeded = 0
        skipped = 0
        for gw_sku, gbp_price, url, in_stock in _PRICES:
            try:
                product = Product.objects.get(gw_sku=gw_sku)
            except Product.DoesNotExist:
                self.stderr.write(f'SKIP — SKU {gw_sku} not in DB')
                skipped += 1
                continue

            cp_defaults = {'url': url, 'in_stock': in_stock, 'not_available': False, 'currency': 'GBP'}
            CurrentPrice.objects.update_or_create(
                product=product,
                retailer=retailer,
                defaults=cp_defaults,
                create_defaults={**cp_defaults, 'price': gbp_price},
            )
            seeded += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Seeded {seeded} StarCraft Firestorm Games prices. Skipped: {skipped}.'
            )
        )
