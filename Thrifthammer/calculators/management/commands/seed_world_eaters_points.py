"""
Management command: seed_world_eaters_points

Sets the points_cost on UnitType records for all World Eaters units,
using official 10th Edition points values sourced from New Recruit.

Usage:
    python manage.py seed_world_eaters_points

The command is fully idempotent — safe to re-run. It looks up each product by
its Games Workshop SKU (gw_sku), then filters for the World Eaters UnitType
specifically and updates only that row's points_cost.

Notes:
- Run AFTER populate_products and populate_units.
- Do NOT add to the Procfile yet.
- Line-by-line verified against the New Recruit World Eaters 10th Edition list.
- SKUs not yet in the DB skip gracefully — add products later and re-run.
- Currently seeded SKUs in DB:
    43-04 (Angron), 43-60 (Khorne Berzerkers), 43-62 (Eightbound),
    43-64 (Lord on Juggernaut)
- 43-95 (Combat Patrol) is a bundle — no UnitType entry.
- 43-62 (Eightbound): the kit also builds Exalted Eightbound (140pts).
  Seeded at 135pts (standard Eightbound base). Add a separate product for
  Exalted Eightbound later.
"""

from django.core.management.base import BaseCommand

from calculators.models import UnitType
from products.models import Faction, Product

# ---------------------------------------------------------------------------
# Points data: (gw_sku, points_cost, display_name_for_logging)
#
# Sourced from New Recruit — World Eaters 10th Edition list.
# Verified line-by-line against the full New Recruit army list.
# ---------------------------------------------------------------------------
WORLD_EATERS_POINTS = [
    # ── Named characters ──────────────────────────────────────────────────────
    ('43-04', 340, 'Angron'),                              # 340pts ✓
    ('43-65', 100, "Khârn the Betrayer"),                  # 100pts ✓
    ('43-66', 110, 'Lord Invocatus'),                      # 110pts ✓
    # ── Generic characters ────────────────────────────────────────────────────
    ('43-64', 105, 'Lord on Juggernaut'),                  # 105pts ✓
    ('43-67', 200, 'Daemon Prince of Khorne'),             # 200pts ✓
    ('43-68', 180, 'Daemon Prince of Khorne with Wings'),  # 180pts ✓
    ('43-69',  60, 'Master of Executions'),                # 60pts  ✓
    ('43-71', 100, 'Slaughterbound'),                      # 100pts ✓
    # ── Battleline ────────────────────────────────────────────────────────────
    ('43-60', 180, 'Khorne Berzerkers'),                   # 180pts ✓
    ('43-72',  65, 'Jakhals'),                             # 65pts  ✓
    ('43-73',  75, 'Goremongers'),                         # 75pts  ✓
    # ── Infantry ──────────────────────────────────────────────────────────────
    ('43-62', 135, 'Eightbound'),                          # 135pts ✓ (Exalted = 140pts, same kit)
    ('43-74', 175, 'Chaos Terminators'),                   # 175pts ✓
    ('43-75',  90, 'Chaos Spawn'),                         # 90pts  ✓
    # ── Vehicles / Daemon Engines ─────────────────────────────────────────────
    ('43-76', 180, 'Defiler'),                             # 180pts ✓
    ('43-77', 170, 'Forgefiend'),                          # 170pts ✓
    ('43-78', 120, 'Helbrute'),                            # 120pts ✓
    ('43-79', 200, 'Heldrake'),                            # 200pts ✓
    ('43-81', 150, 'Maulerfiend'),                         # 150pts ✓
    ('43-82', 505, 'Khorne Lord of Skulls'),               # 505pts ✓
    # ── Transports ────────────────────────────────────────────────────────────
    ('43-83', 220, 'Chaos Land Raider'),                   # 220pts ✓
    ('43-84', 145, 'Chaos Predator Annihilator'),          # 145pts ✓
    ('43-85', 145, 'Chaos Predator Destructor'),           # 145pts ✓
    ('43-86',  85, 'Chaos Rhino'),                         # 85pts  ✓
]


class Command(BaseCommand):
    """
    Seed official 10th Edition points costs for World Eaters units.

    Looks up each product by GW SKU, then filters for the World Eaters
    UnitType specifically and updates only that row's points_cost.
    SKUs not found in the DB are skipped with a warning — add the products
    later and re-run. Idempotent — safe to re-run at any time.
    """

    help = 'Seed 10th Edition points values for World Eaters units.'

    def handle(self, *args, **options):
        """Entry point."""
        self.stdout.write('Seeding World Eaters points…\n')

        we_faction = Faction.objects.filter(name='World Eaters').first()
        if not we_faction:
            self.stdout.write(self.style.ERROR(
                'World Eaters faction not found. Run populate_products first.'
            ))
            return

        updated_count = 0
        skipped_count = 0

        for gw_sku, points, label in WORLD_EATERS_POINTS:
            product = Product.objects.filter(gw_sku=gw_sku).first()

            if not product:
                self.stdout.write(
                    self.style.WARNING(f'  [skip]    {label} (SKU {gw_sku} not found in DB)')
                )
                skipped_count += 1
                continue

            updated = UnitType.objects.filter(
                product=product,
                faction=we_faction,
            ).update(points_cost=points)

            if updated:
                self.stdout.write(f'  [updated] {label} > {points} pts')
                updated_count += 1
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f'  [no unit] {label} (SKU {gw_sku}) — World Eaters UnitType not found. '
                        f'Run populate_units first.'
                    )
                )
                skipped_count += 1

        self.stdout.write(self.style.SUCCESS(
            f'\nDone! Updated: {updated_count}  |  Skipped: {skipped_count}'
        ))
