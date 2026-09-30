"""
Seed Noble Knight Games US prices for StarCraft.

Uses the existing `noble-knight-games` Retailer (US, is_uk=False) -- does
not create it, matching the pattern for every other category's NK seed
command.

Source: user-supplied "Starcraft Noble Knight.xlsx" (Title/Title_URL/Price
columns, 16 rows), plus 3 more user-supplied URLs added afterward (Hydralisk,
Goliath, Lost Temple Ramp). 17 of the 25 catalog SKUs matched. Still not
carried at all: the base Protoss Starter Set, the Zerg/Terran Starter Sets,
and every Wave 2 pre-order item except none -- a genuine coverage gap, not
a matching failure.

Every URL below carries Noble Knight's `?awid=1576` affiliate parameter
(see add_nk_affiliate_tags.py) -- added directly here since that cleanup
command is not in the Procfile and would not fix this command's own output
on the next redeploy otherwise.

SC-001 Hydralisk and SC-009 Goliath are both currently OUT OF STOCK on NK
("Last Stocked" date shown, no price displayed at all) -- recorded with
price=None, in_stock=False, not_available=False (real listing, no current
price to capture), same convention as the real-but-unavailable NK rows
found during the Southern Kriels rollout. SC-009's on-page DESCRIPTION text
is actually Marauder's copy-pasted by mistake (NK's own data error) -- the
title, URL, and MFG part # (ACHSCMG0015) all correctly identify it as
Goliath, so treated as a genuine match per the same precedent as WMH-059's
"Mulgreth" title typo elsewhere in this catalog.

SC-024 (Lost Temple Ramp) uses the IDENTICAL NK listing already assigned to
SC-016 (Lost Temple) -- same pattern already confirmed on Amazon, where both
SKUs share ASIN B0HGZK1JSY. User-supplied both URLs independently and they
match, so NK (like Amazon) appears to sell these as one combined listing.

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
    ('SC-014', Decimal('43.95'), 'https://www.nobleknight.com/P/2148451943/Protoss---Stalker-Expansion-Set?awid=1576', True),
    ('SC-002', Decimal('43.95'), 'https://www.nobleknight.com/P/2148451917/Zerg---Zergling-Expansion-Set?awid=1576', True),
    ('SC-006', Decimal('43.95'), 'https://www.nobleknight.com/P/2148451925/Terran---Marine-Expansion-Set?awid=1576', True),
    ('SC-016', Decimal('43.95'), 'https://www.nobleknight.com/P/2148451949/Terrain---Lost-Temple-Expansion-Set?awid=1576', True),
    ('SC-015', Decimal('43.95'), 'https://www.nobleknight.com/P/2148451944/Protoss---Artanis-Hero-Expansion-Set?awid=1576', True),
    ('SC-005', Decimal('43.95'), 'https://www.nobleknight.com/P/2148451923/Zerg---Kerrigan-Hero-Expansion-Set?awid=1576', True),
    ('SC-010', Decimal('34.95'), 'https://www.nobleknight.com/P/2148451937/Terran---Jim-Raynor-Hero-Expansion-Set?awid=1576', True),
    ('SC-004', Decimal('31.95'), 'https://www.nobleknight.com/P/2148451920/Zerg---Queen-Expansion-Set?awid=1576', True),
    ('SC-013', Decimal('31.95'), 'https://www.nobleknight.com/P/2148451942/Protoss---Sentry-Expansion-Set?awid=1576', True),
    ('SC-008', Decimal('25.95'), 'https://www.nobleknight.com/P/2148510325/Terran---Medic-Expansion-Set?awid=1576', True),
    ('SC-003', Decimal('43.95'), 'https://www.nobleknight.com/P/2148451918/Zerg---Roach-Expansion-Set?awid=1576', True),
    ('SC-007', Decimal('43.95'), 'https://www.nobleknight.com/P/2148451931/Terran---Marauder-Expansion-Set?awid=1576', True),
    ('SC-012', Decimal('34.95'), 'https://www.nobleknight.com/P/2148451941/Protoss---Adept-Expansion-Set?awid=1576', True),
    ('SC-011', Decimal('34.95'), 'https://www.nobleknight.com/P/2148451939/Protoss---Zealot-Expansion-Set?awid=1576', True),
    ('SC-001', None, 'https://www.nobleknight.com/P/2148451915/Zerg---Hydralisk-Expansion-Set?awid=1576', False),
    ('SC-009', None, 'https://www.nobleknight.com/P/2148451934/Terran---Goliath-Expansion-Set?awid=1576', False),
    ('SC-024', Decimal('43.95'), 'https://www.nobleknight.com/P/2148451949/Terrain---Lost-Temple-Expansion-Set?awid=1576', True),
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
