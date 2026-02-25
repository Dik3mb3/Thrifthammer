"""
Management command: seed_emperors_children_points

Sets the points_cost on UnitType records for all Emperor's Children units,
using official 10th Edition points values sourced from New Recruit.

Usage:
    python manage.py seed_emperors_children_points

The command is fully idempotent — safe to re-run. It looks up each product by
its Games Workshop SKU (gw_sku), then filters for the Emperor's Children
UnitType specifically and updates only that row's points_cost.

Notes:
- Run AFTER populate_products and populate_units.
- Do NOT add to the Procfile yet.
- Line-by-line verified against the New Recruit Emperor's Children 10th Edition list.
- As of initial creation, NO Emperor's Children products exist in the DB.
  All entries will [skip] until populate_products.py is updated with EC SKUs.
- Emperor's Children is a new standalone faction (2024/2025 release). SKUs use
  the 43-7x range (placeholder — confirm from GW packaging when adding products).
- Some units (Noise Marines, Chaos Terminators, Chaos Land Raider, Chaos Rhino,
  Chaos Spawn, Heldrake) are shared kits with Chaos Space Marines; they will
  need cross-faction UnitType rows under Emperor's Children in populate_units.
"""

from django.core.management.base import BaseCommand

from calculators.models import UnitType
from products.models import Faction, Product

# ---------------------------------------------------------------------------
# Points data: (gw_sku, points_cost, display_name_for_logging)
#
# Sourced from New Recruit — Emperor's Children 10th Edition list.
# Verified line-by-line against the full New Recruit army list.
# ---------------------------------------------------------------------------
EMPERORS_CHILDREN_POINTS = [
    # ── Named characters ──────────────────────────────────────────────────────
    ('43-70', 340, 'Fulgrim'),                             # 340pts ✓
    ('43-71', 150, 'Lucius the Eternal'),                  # 150pts ✓
    # ── Generic characters ────────────────────────────────────────────────────
    ('43-72', 180, 'Daemon Prince of Slaanesh'),           # 180pts ✓
    ('43-73', 215, 'Daemon Prince of Slaanesh with Wings'), # 215pts ✓
    ('43-74',  80, 'Lord Exultant'),                       # 80pts  ✓
    ('43-75',  70, 'Lord Kakophonist'),                    # 70pts  ✓
    ('43-76',  60, 'Sorcerer'),                            # 60pts  ✓
    # ── Battleline ────────────────────────────────────────────────────────────
    ('43-77',  85, 'Infractors'),                          # 85pts  ✓
    ('43-78',  85, 'Tormentors'),                          # 85pts  ✓
    # ── Infantry ──────────────────────────────────────────────────────────────
    ('43-79', 155, 'Chaos Terminators'),                   # 155pts ✓
    ('43-81', 110, 'Flawless Blades'),                     # 110pts ✓
    ('43-82', 145, 'Noise Marines'),                       # 145pts ✓
    ('43-83',  70, 'Chaos Spawn'),                         # 70pts  ✓
    # ── Vehicles / Daemon Engines ─────────────────────────────────────────────
    ('43-84', 195, 'Heldrake'),                            # 195pts ✓
    # ── Transports ────────────────────────────────────────────────────────────
    ('43-85', 220, 'Chaos Land Raider'),                   # 220pts ✓
    ('43-86',  80, 'Chaos Rhino'),                         # 80pts  ✓
]


class Command(BaseCommand):
    """
    Seed official 10th Edition points costs for Emperor's Children units.

    Looks up each product by GW SKU, then filters for the Emperor's Children
    UnitType specifically and updates only that row's points_cost.
    SKUs not found in the DB are skipped with a warning — add the products
    later and re-run. Idempotent — safe to re-run at any time.
    """

    help = "Seed 10th Edition points values for Emperor's Children units."

    def handle(self, *args, **options):
        """Entry point."""
        self.stdout.write("Seeding Emperor's Children points…\n")

        ec_faction = Faction.objects.filter(name="Emperor's Children").first()
        if not ec_faction:
            self.stdout.write(self.style.ERROR(
                "Emperor's Children faction not found. Run populate_products first."
            ))
            return

        updated_count = 0
        skipped_count = 0

        for gw_sku, points, label in EMPERORS_CHILDREN_POINTS:
            product = Product.objects.filter(gw_sku=gw_sku).first()

            if not product:
                self.stdout.write(
                    self.style.WARNING(f'  [skip]    {label} (SKU {gw_sku} not found in DB)')
                )
                skipped_count += 1
                continue

            updated = UnitType.objects.filter(
                product=product,
                faction=ec_faction,
            ).update(points_cost=points)

            if updated:
                self.stdout.write(f'  [updated] {label} > {points} pts')
                updated_count += 1
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f'  [no unit] {label} (SKU {gw_sku}) — EC UnitType not found. '
                        f'Run populate_units first.'
                    )
                )
                skipped_count += 1

        self.stdout.write(self.style.SUCCESS(
            f'\nDone! Updated: {updated_count}  |  Skipped: {skipped_count}'
        ))
