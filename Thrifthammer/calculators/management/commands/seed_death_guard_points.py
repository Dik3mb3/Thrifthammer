"""
Management command: seed_death_guard_points

Sets the points_cost on UnitType records for all Death Guard units,
using official 10th Edition points values sourced from New Recruit.

Usage:
    python manage.py seed_death_guard_points

The command is fully idempotent — safe to re-run. It looks up each product by
its Games Workshop SKU (gw_sku), then filters for the Death Guard UnitType
specifically and updates only that row's points_cost.

Notes:
- Run AFTER populate_products and populate_units.
- Do NOT add to the Procfile yet.
- Line-by-line verified against the New Recruit Death Guard 10th Edition list.
- SKUs not yet in the DB skip gracefully — add products later and re-run.
- Currently seeded SKUs in DB:
    43-03 (Mortarion), 43-08 (Typhus), 43-50 (Plague Marines),
    43-53 (Poxwalkers), 43-54 (Blightlord Terminators),
    43-55 (Foetid Bloat-drone), 43-56 (Deathshroud Bodyguard)
- 43-80 (Combat Patrol) is a bundle — no UnitType entry.
- 43-55 (Foetid Bloat-drone): one kit, two weapon configurations.
  Standard (fleshmower) = 100pts, heavy blight launcher = 120pts.
  Seeded at 100pts (base). Add a separate product for the 120pt variant later.
"""

from django.core.management.base import BaseCommand

from calculators.models import UnitType
from products.models import Faction, Product

# ---------------------------------------------------------------------------
# Points data: (gw_sku, points_cost, display_name_for_logging)
#
# Sourced from New Recruit — Death Guard 10th Edition list.
# Verified line-by-line against the full New Recruit army list.
# ---------------------------------------------------------------------------
DEATH_GUARD_POINTS = [
    # ── Named characters ──────────────────────────────────────────────────────
    ('43-03', 380, 'Mortarion'),                           # 380pts ✓
    ('43-08', 100, 'Typhus'),                              # 100pts ✓
    # ── Generic characters ────────────────────────────────────────────────────
    ('43-11',  60, 'Biologus Putrifier'),                  # 60pts  ✓
    ('43-12', 195, 'Daemon Prince of Nurgle'),             # 195pts ✓
    ('43-13', 195, 'Daemon Prince of Nurgle with Wings'),  # 195pts ✓
    ('43-14',  75, 'Foul Blightspawn'),                    # 75pts  ✓
    ('43-15',  45, 'Icon Bearer'),                         # 45pts  ✓
    ('43-16', 120, 'Lord of Contagion'),                   # 120pts ✓
    ('43-17',  75, 'Lord of Poxes'),                       # 75pts  ✓
    ('43-18', 100, 'Lord of Virulence'),                   # 100pts ✓
    ('43-19',  60, 'Malignant Plaguecaster'),              # 60pts  ✓
    ('43-20',  50, 'Noxious Blightbringer'),               # 50pts  ✓
    ('43-21',  50, 'Plague Surgeon'),                      # 50pts  ✓
    ('43-22',  50, 'Tallyman'),                            # 50pts  ✓
    # ── Battleline ────────────────────────────────────────────────────────────
    ('43-50',  95, 'Plague Marines'),                      # 95pts  ✓
    ('43-53',  65, 'Poxwalkers'),                          # 65pts  ✓
    # ── Infantry ──────────────────────────────────────────────────────────────
    ('43-54', 115, 'Blightlord Terminators'),              # 115pts ✓
    ('43-56', 160, 'Deathshroud Terminators'),             # 160pts ✓
    ('43-23',  80, 'Chaos Spawn'),                         # 80pts  ✓
    # ── Vehicles / Daemon Engines ─────────────────────────────────────────────
    ('43-55', 100, 'Foetid Bloat-drone'),                  # 100pts ✓ (120pts w/ heavy blight launcher)
    ('43-24', 165, 'Defiler'),                             # 165pts ✓
    ('43-25', 115, 'Helbrute'),                            # 115pts ✓
    ('43-26', 105, 'Miasmic Malignifier'),                 # 105pts ✓
    ('43-27', 100, 'Myphitic Blight-hauler'),              # 100pts ✓
    ('43-28', 210, 'Plagueburst Crawler'),                 # 210pts ✓
    # ── Transports / Vehicles ─────────────────────────────────────────────────
    ('43-29', 220, 'Chaos Land Raider'),                   # 220pts ✓
    ('43-30', 135, 'Chaos Predator Annihilator'),          # 135pts ✓
    ('43-31', 145, 'Chaos Predator Destructor'),           # 145pts ✓
    ('43-32',  85, 'Chaos Rhino'),                         # 85pts  ✓
]


class Command(BaseCommand):
    """
    Seed official 10th Edition points costs for Death Guard units.

    Looks up each product by GW SKU, then filters for the Death Guard
    UnitType specifically and updates only that row's points_cost.
    SKUs not found in the DB are skipped with a warning — add the products
    later and re-run. Idempotent — safe to re-run at any time.
    """

    help = 'Seed 10th Edition points values for Death Guard units.'

    def handle(self, *args, **options):
        """Entry point."""
        self.stdout.write('Seeding Death Guard points…\n')

        dg_faction = Faction.objects.filter(name='Death Guard').first()
        if not dg_faction:
            self.stdout.write(self.style.ERROR(
                'Death Guard faction not found. Run populate_products first.'
            ))
            return

        updated_count = 0
        skipped_count = 0

        for gw_sku, points, label in DEATH_GUARD_POINTS:
            product = Product.objects.filter(gw_sku=gw_sku).first()

            if not product:
                self.stdout.write(
                    self.style.WARNING(f'  [skip]    {label} (SKU {gw_sku} not found in DB)')
                )
                skipped_count += 1
                continue

            updated = UnitType.objects.filter(
                product=product,
                faction=dg_faction,
            ).update(points_cost=points)

            if updated:
                self.stdout.write(f'  [updated] {label} > {points} pts')
                updated_count += 1
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f'  [no unit] {label} (SKU {gw_sku}) — Death Guard UnitType not found. '
                        f'Run populate_units first.'
                    )
                )
                skipped_count += 1

        self.stdout.write(self.style.SUCCESS(
            f'\nDone! Updated: {updated_count}  |  Skipped: {skipped_count}'
        ))
