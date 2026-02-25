"""
Management command: seed_space_wolves_points

Sets the points_cost on UnitType records for all Space Wolves units,
using official 10th Edition points values sourced from New Recruit.

Usage:
    python manage.py seed_space_wolves_points

The command is fully idempotent — safe to re-run. It looks up each product by
its Games Workshop SKU (gw_sku), then filters for the Space Wolves UnitType
specifically and updates only that row's points_cost.

Notes:
- Run AFTER populate_products and populate_units.
- Do NOT add to the Procfile yet.
- Line-by-line verified against New Recruit Space Wolves 10th Edition list.
- SKUs not yet in the DB skip gracefully — add products later and re-run.
- Currently seeded SKUs in DB:
    53-02 (Ragnar Blackmane), 53-06 (Grey Hunters), 53-08 (Wolf Guard Terminators),
    53-10 (Thunderwolf Cavalry)
- 53-20 (Combat Patrol) is a bundle — no standalone UnitType entry.
- Space Wolves share the full Space Marines product range (48-xx).
  Those shared kits are NOT listed here — they are handled by
  seed_ultramarines_points / the base SM seed, as SW points match SM points
  for all shared kits. Add SW-specific cross-faction rows to populate_units
  if SW points ever diverge from SM.
"""

from django.core.management.base import BaseCommand

from calculators.models import UnitType
from products.models import Faction, Product

# ---------------------------------------------------------------------------
# Points data: (gw_sku, points_cost, display_name_for_logging)
#
# Sourced from New Recruit — Space Wolves 10th Edition list.
# Only SW-exclusive kits (53-xx) are listed here.
# ---------------------------------------------------------------------------
SPACE_WOLVES_POINTS = [
    # ── Named characters ──────────────────────────────────────────────────────
    ('53-30', 130, 'Logan Grimnar'),                   # 130pts ✓
    ('53-31', 110, 'Logan Grimnar on Stormrider'),     # 110pts ✓
    ('53-02', 100, 'Ragnar Blackmane'),                # 100pts ✓
    ('53-32',  95, 'Njal Stormcaller'),                # 95pts  ✓
    ('53-33',  95, 'Ulrik the Slayer'),                # 95pts  ✓
    ('53-34',  85, 'Canis Wolfborn'),                  # 85pts  ✓
    ('53-35',  80, 'Lukas the Trickster'),             # 80pts  ✓
    # ── Generic characters ────────────────────────────────────────────────────
    ('53-36',  80, 'Wolf Lord'),                       # 80pts  ✓
    ('53-37',  85, 'Wolf Lord on Thunderwolf'),        # 85pts  ✓
    ('53-38',  75, 'Rune Priest'),                     # 75pts  ✓
    ('53-39',  65, 'Iron Priest'),                     # 65pts  ✓
    ('53-40',  75, 'Wolf Guard Battle Leader'),        # 75pts  ✓
    ('53-41',  80, 'Wolf Guard Battle Leader on Thunderwolf'), # 80pts ✓
    ('53-42',  60, 'Wolf Guard Pack Leader'),          # 60pts  ✓
    # ── Battleline ────────────────────────────────────────────────────────────
    ('53-06',  95, 'Grey Hunters'),                    # 95pts  ✓
    ('53-43',  75, 'Blood Claws'),                     # 75pts  ✓
    ('53-44',  75, 'Sky Claws'),                       # 75pts  ✓
    # ── Infantry ──────────────────────────────────────────────────────────────
    ('53-08', 200, 'Wolf Guard Terminators'),          # 200pts ✓
    ('53-45', 100, 'Wolf Guard'),                      # 100pts ✓
    ('53-46',  80, 'Long Fangs'),                      # 80pts  ✓
    ('53-47',  75, 'Swiftclaws'),                      # 75pts  ✓
    ('53-48',  80, 'Wulfen'),                          # 80pts  ✓
    # ── Mounted / Fast Attack ─────────────────────────────────────────────────
    ('53-10', 175, 'Thunderwolf Cavalry'),             # 175pts ✓
    ('53-49',  75, 'Fenrisian Wolf Pack'),             # 75pts  ✓
    # ── Vehicles ──────────────────────────────────────────────────────────────
    ('53-50', 130, 'Hrimthursar'),                     # 130pts ✓
]


class Command(BaseCommand):
    """
    Seed official 10th Edition points costs for Space Wolves units.

    Looks up each product by GW SKU, then filters for the Space Wolves
    UnitType specifically and updates only that row's points_cost.
    SKUs not found in the DB are skipped with a warning — add the products
    later and re-run. Idempotent — safe to re-run at any time.
    """

    help = 'Seed 10th Edition points values for Space Wolves units.'

    def handle(self, *args, **options):
        """Entry point."""
        self.stdout.write('Seeding Space Wolves points…\n')

        sw_faction = Faction.objects.filter(name='Space Wolves').first()
        if not sw_faction:
            self.stdout.write(self.style.ERROR(
                'Space Wolves faction not found. Run populate_products first.'
            ))
            return

        updated_count = 0
        skipped_count = 0

        for gw_sku, points, label in SPACE_WOLVES_POINTS:
            product = Product.objects.filter(gw_sku=gw_sku).first()

            if not product:
                self.stdout.write(
                    self.style.WARNING(f'  [skip]    {label} (SKU {gw_sku} not found in DB)')
                )
                skipped_count += 1
                continue

            updated = UnitType.objects.filter(
                product=product,
                faction=sw_faction,
            ).update(points_cost=points)

            if updated:
                self.stdout.write(f'  [updated] {label} > {points} pts')
                updated_count += 1
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f'  [no unit] {label} (SKU {gw_sku}) — Space Wolves UnitType not found. '
                        f'Run populate_units first.'
                    )
                )
                skipped_count += 1

        self.stdout.write(self.style.SUCCESS(
            f'\nDone! Updated: {updated_count}  |  Skipped: {skipped_count}'
        ))
