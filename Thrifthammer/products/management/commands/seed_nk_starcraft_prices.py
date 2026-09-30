"""
Seed Noble Knight Games US prices for StarCraft.

Uses the existing `noble-knight-games` Retailer (US, is_uk=False) -- does
not create it, matching the pattern for every other category's NK seed
command.

Source: user-supplied "Starcraft Noble Knight.xlsx" (Title/Title_URL/Price
columns, 16 rows). 14 of the 25 catalog SKUs matched (NK doesn't carry the
remaining 11 -- Hydralisk, Goliath, the base Protoss Starter Set, the Zerg/
Terran Starter Sets, or any of the Wave 2 pre-order items -- a genuine
coverage gap, not a matching failure).

3 titles are abbreviated on NK's own listing pages relative to our product
names (no "& Pylon" / "& Omega Worm" / "& Point Defense Drone" suffix) --
each verified live via its own product page contents (miniature count,
MFG part number matching Miniature Market's ASSCMG-prefixed codes under
NK's ACHSCMG prefix, and MSRP) before treating as a genuine match:
  - "Protoss - Artanis Hero Expansion Set" -> SC-015 (1x Artanis + 1x Pylon,
    MFG ACHSCMG0021)
  - "Zerg - Kerrigan Hero Expansion Set" -> SC-005 (1x Kerrigan + 1x Omega
    Worm, MFG ACHSCMG0011)
  - "Terran - Jim Raynor Hero Expansion Set" -> SC-010 (1x Jim Raynor + 1x
    Point Defense Drone, MFG ACHSCMG0016)

2 rows NOT matched to any SKU -- same "Founders Edition" trap already
caught and fixed on SC-017's eBay/Amazon matches:
  - "StarCraft - Protoss Starter Set (Founders Edition)" ($115.95) -- the
    richer/different bundle, not our SC-017.
  - "StarCraft - 2 Player Starter Set (Founders Edition)" ($205.95) -- a
    bundle of both single-faction starter sets, not a single SKU.

Run once on Railway startup via Procfile. Safe to re-run -- idempotent.
"""
from decimal import Decimal

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Product, Retailer

_NK_SLUG = 'noble-knight-games'

# (gw_sku, usd_price, url, in_stock)
_PRICES = [
    ('SC-014', Decimal('43.95'), 'https://www.nobleknight.com/P/2148451943/Protoss---Stalker-Expansion-Set', True),
    ('SC-002', Decimal('43.95'), 'https://www.nobleknight.com/P/2148451917/Zerg---Zergling-Expansion-Set', True),
    ('SC-006', Decimal('43.95'), 'https://www.nobleknight.com/P/2148451925/Terran---Marine-Expansion-Set', True),
    ('SC-016', Decimal('43.95'), 'https://www.nobleknight.com/P/2148451949/Terrain---Lost-Temple-Expansion-Set', True),
    ('SC-015', Decimal('43.95'), 'https://www.nobleknight.com/P/2148451944/Protoss---Artanis-Hero-Expansion-Set', True),
    ('SC-005', Decimal('43.95'), 'https://www.nobleknight.com/P/2148451923/Zerg---Kerrigan-Hero-Expansion-Set', True),
    ('SC-010', Decimal('34.95'), 'https://www.nobleknight.com/P/2148451937/Terran---Jim-Raynor-Hero-Expansion-Set', True),
    ('SC-004', Decimal('31.95'), 'https://www.nobleknight.com/P/2148451920/Zerg---Queen-Expansion-Set', True),
    ('SC-013', Decimal('31.95'), 'https://www.nobleknight.com/P/2148451942/Protoss---Sentry-Expansion-Set', True),
    ('SC-008', Decimal('25.95'), 'https://www.nobleknight.com/P/2148510325/Terran---Medic-Expansion-Set', True),
    ('SC-003', Decimal('43.95'), 'https://www.nobleknight.com/P/2148451918/Zerg---Roach-Expansion-Set', True),
    ('SC-007', Decimal('43.95'), 'https://www.nobleknight.com/P/2148451931/Terran---Marauder-Expansion-Set', True),
    ('SC-012', Decimal('34.95'), 'https://www.nobleknight.com/P/2148451941/Protoss---Adept-Expansion-Set', True),
    ('SC-011', Decimal('34.95'), 'https://www.nobleknight.com/P/2148451939/Protoss---Zealot-Expansion-Set', True),
]


class Command(BaseCommand):
    help = 'Seed Noble Knight Games US prices and URLs for StarCraft. Idempotent.'

    def handle(self, *args, **options):
        retailer = Retailer.objects.get(slug=_NK_SLUG)

        seeded = 0
        skipped = 0
        for gw_sku, usd_price, url, in_stock in _PRICES:
            try:
                product = Product.objects.get(gw_sku=gw_sku)
            except Product.DoesNotExist:
                self.stderr.write(f'SKIP — SKU {gw_sku} not in DB')
                skipped += 1
                continue

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
                f'Seeded {seeded} StarCraft Noble Knight prices. Skipped: {skipped}.'
            )
        )
