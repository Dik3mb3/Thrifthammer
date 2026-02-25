"""
Management command: seed_grey_knights_points

Sets the points_cost on UnitType records for all Grey Knights units,
using official 10th Edition points values sourced from New Recruit.

Usage:
    python manage.py seed_grey_knights_points

The command is fully idempotent — safe to re-run. It looks up each product by
its Games Workshop SKU (gw_sku), then filters for the Grey Knights UnitType
specifically and updates only that row's points_cost.

Notes:
- Run AFTER populate_products and populate_units.
- Do NOT add to the Procfile yet.
- Line-by-line verified against the New Recruit Grey Knights 10th Edition list.
- SKUs not yet in the DB skip gracefully — add products later and re-run.
- Currently seeded SKUs in DB: 57-02, 57-06, 57-08, 57-14
- 57-20 (Combat Patrol) is a bundle — no UnitType entry.
- 57-14 (Dreadknight): seeded as Nemesis Dreadknight (210pts). The Grand Master
  in Nemesis Dreadknight (225pts) is a character variant — separate SKU 57-03
  when added.
"""

from django.core.management.base import BaseCommand

from calculators.models import UnitType
from products.models import Faction, Product

# ---------------------------------------------------------------------------
# Points data: (gw_sku, points_cost, display_name_for_logging)
#
# Sourced from New Recruit — Grey Knights 10th Edition list.
# Verified line-by-line against the full New Recruit army list.
# ---------------------------------------------------------------------------
GREY_KNIGHTS_POINTS = [
    # ── Named characters ──────────────────────────────────────────────────────
    ('57-01',  90, 'Castellan Crowe'),                     # 90pts  ✓
    ('57-02', 110, 'Grand Master Voldus'),                 # 110pts ✓
    # ── Generic characters ────────────────────────────────────────────────────
    ('57-04',  90, 'Brother-Captain'),                     # 90pts  ✓
    ('57-05',  70, 'Brotherhood Champion'),                # 70pts  ✓
    ('57-09',  65, 'Brotherhood Chaplain'),                # 65pts  ✓
    ('57-10',  80, 'Brotherhood Librarian'),               # 80pts  ✓
    ('57-11',  70, 'Brotherhood Techmarine'),              # 70pts  ✓
    ('57-12',  95, 'Grand Master'),                        # 95pts  ✓
    ('57-03', 225, 'Grand Master in Nemesis Dreadknight'), # 225pts ✓
    ('57-13', 140, 'Venerable Dreadnought'),               # 140pts ✓
    # ── Battleline ────────────────────────────────────────────────────────────
    ('57-06', 120, 'Strike Squad'),                        # 120pts ✓
    # ── Infantry ──────────────────────────────────────────────────────────────
    ('57-08', 160, 'Brotherhood Terminator Squad'),        # 160pts ✓
    ('57-15', 125, 'Interceptor Squad'),                   # 125pts ✓
    ('57-16', 180, 'Paladin Squad'),                       # 180pts ✓
    ('57-17', 115, 'Purgation Squad'),                     # 115pts ✓
    ('57-18', 125, 'Purifier Squad'),                      # 125pts ✓
    # ── Vehicles ──────────────────────────────────────────────────────────────
    ('57-14', 210, 'Nemesis Dreadknight'),                 # 210pts ✓
    ('57-19',  85, 'Razorback'),                           # 85pts  ✓
    ('57-21',  80, 'Rhino'),                               # 80pts  ✓
    ('57-22', 220, 'Land Raider'),                         # 220pts ✓
    ('57-23', 220, 'Land Raider Crusader'),                # 220pts ✓
    ('57-24', 270, 'Land Raider Redeemer'),                # 270pts ✓
    # ── Aircraft ──────────────────────────────────────────────────────────────
    ('57-25', 160, 'Stormhawk Interceptor'),               # 160pts ✓
    ('57-26', 280, 'Stormraven Gunship'),                  # 280pts ✓
    ('57-27', 170, 'Stormtalon Gunship'),                  # 170pts ✓
    ('57-28', 805, 'Grey Knights Thunderhawk Gunship'),    # 805pts ✓
]


class Command(BaseCommand):
    """
    Seed official 10th Edition points costs for Grey Knights units.

    Looks up each product by GW SKU, then filters for the Grey Knights
    UnitType specifically and updates only that row's points_cost.
    SKUs not found in the DB are skipped with a warning — add the products
    later and re-run. Idempotent — safe to re-run at any time.
    """

    help = 'Seed 10th Edition points values for Grey Knights units.'

    def handle(self, *args, **options):
        """Entry point."""
        self.stdout.write('Seeding Grey Knights points…\n')

        gk_faction = Faction.objects.filter(name='Grey Knights').first()
        if not gk_faction:
            self.stdout.write(self.style.ERROR(
                'Grey Knights faction not found. Run populate_products first.'
            ))
            return

        updated_count = 0
        skipped_count = 0

        for gw_sku, points, label in GREY_KNIGHTS_POINTS:
            product = Product.objects.filter(gw_sku=gw_sku).first()

            if not product:
                self.stdout.write(
                    self.style.WARNING(f'  [skip]    {label} (SKU {gw_sku} not found in DB)')
                )
                skipped_count += 1
                continue

            updated = UnitType.objects.filter(
                product=product,
                faction=gk_faction,
            ).update(points_cost=points)

            if updated:
                self.stdout.write(f'  [updated] {label} > {points} pts')
                updated_count += 1
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f'  [no unit] {label} (SKU {gw_sku}) — Grey Knights UnitType not found. '
                        f'Run populate_units first.'
                    )
                )
                skipped_count += 1

        self.stdout.write(self.style.SUCCESS(
            f'\nDone! Updated: {updated_count}  |  Skipped: {skipped_count}'
        ))
