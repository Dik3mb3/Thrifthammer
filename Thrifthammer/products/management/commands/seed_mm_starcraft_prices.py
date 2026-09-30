"""
Seed Miniature Market US prices for StarCraft.

Uses the existing `miniature-market` Retailer (US, is_uk=False) -- does not
create it, matching the pattern for every other category's MM seed command.

Source: user-supplied "StarCraft Miniature Market.xlsx" (Title/Title_URL/
Price columns, 27 rows). All 25 catalog SKUs matched cleanly, each verified
against Product.name before writing.

2 sheet rows NOT matched to any SKU (real products, but not in our catalog):
- "StarCraft: Two-Player Starter Set" (ASSCMG0002, $204.99) -- a bundle of
  BOTH single-faction starter sets together, not a single SKU.
- "StarCraft: Protoss Starter Set" / Founders Edition (ASSCMG0003, $109.99)
  -- a different, richer bundle (17 miniatures incl. Artanis/Pylon/Force
  Fields, 20 dice, a ruler) than our SC-017 (14 miniatures, no dice, per
  Archon's own direct listing). Confirmed via this same duplicate-title
  discovery that SC-017's eBay and Amazon matches had ALSO wrongly picked
  this Founders Edition bundle -- both were corrected separately.

9 of the 25 matched rows are MM "Preorder" listings (Estimated Release
Date: October 2026) for SC-017 through SC-025's Wave 2 items -- same
in_stock=True-for-a-live-purchasable-preorder convention used elsewhere in
this catalog (e.g. Warmachine's Menoth/Cryx/Dusk waves). SC-017 (Protoss
Starter Set) is the correctly-verified base listing (ASSCMG0004), not the
Founders Edition duplicate above.

Run once on Railway startup via Procfile. Safe to re-run -- idempotent.
"""
from decimal import Decimal

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Product, Retailer

_MM_SLUG = 'miniature-market'

# (gw_sku, usd_price, url, in_stock)
_PRICES = [
    ('SC-001', Decimal('41.99'), 'https://www.miniaturemarket.com/StarCraft-Zerg-Expansion-Set-Hydralisk-New-Arrival/ASSCMG0007', True),
    ('SC-002', Decimal('41.99'), 'https://www.miniaturemarket.com/StarCraft-Zerg-Expansion-Set-Zergling-New-Arrival/ASSCMG0008', True),
    ('SC-003', Decimal('41.99'), 'https://www.miniaturemarket.com/StarCraft-Zerg-Expansion-Set-Roach/ASSCMG0009', True),
    ('SC-004', Decimal('29.99'), 'https://www.miniaturemarket.com/StarCraft-Zerg-Expansion-Set-Queen/ASSCMG0010', True),
    ('SC-005', Decimal('41.99'), 'https://www.miniaturemarket.com/StarCraft-Zerg-Hero-Expansion-Set-Kerrigan-Omega-Worm/ASSCMG0011', True),
    ('SC-006', Decimal('41.99'), 'https://www.miniaturemarket.com/StarCraft-Terran-Expansion-Set-Marine/ASSCMG0012', True),
    ('SC-007', Decimal('41.99'), 'https://www.miniaturemarket.com/StarCraft-Terran-Expansion-Set-Marauder/ASSCMG0013', True),
    ('SC-008', Decimal('24.99'), 'https://www.miniaturemarket.com/StarCraft-Terran-Expansion-Set-Medic/ASSCMG0014', True),
    ('SC-009', Decimal('41.99'), 'https://www.miniaturemarket.com/StarCraft-Terran-Expansion-Set-Goliath-New-Arrival/ASSCMG0015', True),
    ('SC-010', Decimal('33.99'), 'https://www.miniaturemarket.com/StarCraft-Terran-Hero-Expansion-Set-Jim-Raynor-Point-Defense-Drone/ASSCMG0016', True),
    ('SC-011', Decimal('33.99'), 'https://www.miniaturemarket.com/StarCraft-Protoss-Expansion-Set-Zealot/ASSCMG0017', True),
    ('SC-012', Decimal('33.99'), 'https://www.miniaturemarket.com/StarCraft-Protoss-Expansion-Set-Adept/ASSCMG0018', True),
    ('SC-013', Decimal('29.99'), 'https://www.miniaturemarket.com/StarCraft-Protoss-Expansion-Set-Sentry/ASSCMG0019', True),
    ('SC-014', Decimal('41.99'), 'https://www.miniaturemarket.com/StarCraft-Protoss-Expansion-Set-Stalker/ASSCMG0020', True),
    ('SC-015', Decimal('41.99'), 'https://www.miniaturemarket.com/StarCraft-Protoss-Hero-Expansion-Set-Artanis-Pylon/ASSCMG0021', True),
    ('SC-016', Decimal('41.99'), 'https://www.miniaturemarket.com/StarCraft-Terrain-Expansion-Set-Lost-Temple/ASSCMG0022', True),
    ('SC-017', Decimal('109.99'), 'https://www.miniaturemarket.com/StarCraft-Protoss-Starter-Set-Preorder/ASSCMG0004', True),
    ('SC-018', Decimal('100.99'), 'https://www.miniaturemarket.com/StarCraft-Zerg-Starter-Set-Preorder/ASSCMG0005', True),
    ('SC-019', Decimal('100.99'), 'https://www.miniaturemarket.com/StarCraft-Terran-Starter-Set-Preorder/ASSCMG0006', True),
    ('SC-020', Decimal('49.99'), 'https://www.miniaturemarket.com/StarCraft-Zerg-Expansion-Set-Ravager-Preorder/ASSCMG0032', True),
    ('SC-021', Decimal('57.99'), 'https://www.miniaturemarket.com/StarCraft-Protoss-Expansion-Set-Immortal-Preorder/ASSCMG0033', True),
    ('SC-022', Decimal('66.99'), 'https://www.miniaturemarket.com/StarCraft-Terran-Expansion-Set-Siege-Tank-Preorder/ASSCMG0034', True),
    ('SC-023', Decimal('32.99'), 'https://www.miniaturemarket.com/StarCraft-Protoss-Hero-Expansion-Set-Zeratul-Preorder/ASSCMG0035', True),
    ('SC-024', Decimal('32.99'), 'https://www.miniaturemarket.com/StarCraft-Terrain-Expansion-Set-Lost-Temple-Ramp-Preorder/ASSCMG0036', True),
    ('SC-025', Decimal('8.49'), 'https://www.miniaturemarket.com/Starcraft-Core-Rules-Book-Preorder/ASSCMG0031', True),
]


class Command(BaseCommand):
    help = 'Seed Miniature Market US prices and URLs for StarCraft. Idempotent.'

    def handle(self, *args, **options):
        retailer = Retailer.objects.get(slug=_MM_SLUG)

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
                f'Seeded {seeded} StarCraft Miniature Market prices. Skipped: {skipped}.'
            )
        )
