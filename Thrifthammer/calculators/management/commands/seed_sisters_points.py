"""
Management command: seed_sisters_points

Sets the points_cost on UnitType records for all Adepta Sororitas units,
using official 10th Edition points values sourced from New Recruit.

Usage:
    python manage.py seed_sisters_points

The command is fully idempotent — safe to re-run. It looks up each product by
its Games Workshop SKU (gw_sku), then filters for the Adepta Sororitas UnitType
specifically and updates only that row's points_cost.

Notes:
- Run AFTER populate_products and populate_units.
- Do NOT add to the Procfile yet.
- Line-by-line verified against the New Recruit Adepta Sororitas 10th Edition list.
- SKUs not yet in the DB are included here so they are seeded automatically
  when the corresponding products are added later.
- Currently seeded SKUs in DB: 52-02, 52-08, 52-09, 52-12, 52-15, 52-20, 52-22
- 52-25 (Combat Patrol) is a bundle product — no UnitType entry.
- Named characters, vehicles, and squads not yet in DB will be skipped gracefully.
"""

from django.core.management.base import BaseCommand

from calculators.models import UnitType
from products.models import Faction, Product

# ---------------------------------------------------------------------------
# Points data: (gw_sku, points_cost, display_name_for_logging)
#
# Sourced from New Recruit — Adepta Sororitas 10th Edition list.
# Verified line-by-line against the full New Recruit army list.
# SKUs not yet in the DB are included here so they are seeded automatically
# when the corresponding products are added later.
# ---------------------------------------------------------------------------
SISTERS_POINTS = [
    # ── Named characters ─────────────────────────────────────────────────────
    ('52-17',  70, 'Aestred Thurga and Agathae Dolan'),  # 70pts ✓
    ('52-13',  85, 'Daemonifuge'),                        # 85pts ✓
    ('52-01',  80, 'Junith Eruita'),                      # 80pts ✓
    ('52-02', 185, 'Morvenn Vahl'),                       # 185pts ✓
    ('52-03', 150, 'Saint Celestine'),                    # 150pts ✓
    ('52-04', 235, 'Triumph of Saint Katherine'),         # 235pts ✓
    # ── Generic characters ────────────────────────────────────────────────────
    ('52-05',  60, 'Canoness'),                           # 60pts ✓
    ('52-18',  75, 'Canoness with Jump Pack'),            # 75pts ✓
    ('52-06',  40, 'Dialogus'),                           # 40pts ✓
    ('52-07',  45, 'Dogmata'),                            # 45pts ✓
    ('52-10',  60, 'Hospitaller'),                        # 60pts ✓
    ('52-11',  65, 'Imagifier'),                          # 65pts ✓
    ('52-14',  50, 'Ministorum Priest'),                  # 50pts ✓
    ('52-16',  50, 'Palatine'),                           # 50pts ✓
    # ── Battleline ────────────────────────────────────────────────────────────
    ('52-20', 105, 'Battle Sisters Squad'),               # 105pts ✓
    ('52-23', 100, 'Sisters Novitiate Squad'),            # 100pts ✓
    # ── Infantry ──────────────────────────────────────────────────────────────
    ('52-19',  45, 'Arco-Flagellants'),                   # 45pts ✓
    ('52-26', 120, 'Celestian Insidiants'),               # 120pts ✓
    ('52-22',  70, 'Celestian Sacresants'),               # 70pts ✓
    ('52-21', 120, 'Dominion Squad'),                     # 120pts ✓
    ('52-27',  70, 'Mortifiers'),                         # 70pts ✓
    ('52-28',  75, 'Penitent Engines'),                   # 75pts ✓
    ('52-29',  75, 'Repentia Squad'),                     # 75pts ✓
    ('52-15', 120, 'Retributor Squad'),                   # 120pts ✓
    ('52-30', 110, 'Sanctifiers'),                        # 110pts ✓
    # ── Fast Attack ───────────────────────────────────────────────────────────
    ('52-12',  80, 'Seraphim Squad'),                     # 80pts ✓
    ('52-31',  80, 'Zephyrim Squad'),                     # 80pts ✓
    # ── Heavy Support / Vehicles ──────────────────────────────────────────────
    ('52-32', 210, 'Paragon Warsuits'),                   # 210pts ✓
    ('52-33', 160, 'Castigator'),                         # 160pts ✓
    ('52-08', 210, 'Exorcist'),                           # 210pts ✓
    ('52-09', 115, 'Immolator'),                          # 115pts ✓
    # ── Transports ────────────────────────────────────────────────────────────
    ('52-24',  75, 'Sororitas Rhino'),                    # 75pts ✓
]


class Command(BaseCommand):
    """
    Seed official 10th Edition points costs for Adepta Sororitas units.

    Looks up each product by GW SKU, then filters for the Adepta Sororitas
    UnitType specifically and updates only that row's points_cost.
    SKUs not found in the DB are skipped with a warning — add the products
    later and re-run. Idempotent — safe to re-run at any time.
    """

    help = 'Seed 10th Edition points values for Adepta Sororitas units.'

    def handle(self, *args, **options):
        """Entry point."""
        self.stdout.write('Seeding Adepta Sororitas points…\n')

        sisters_faction = Faction.objects.filter(name='Adepta Sororitas').first()
        if not sisters_faction:
            self.stdout.write(self.style.ERROR(
                'Adepta Sororitas faction not found. Run populate_products first.'
            ))
            return

        updated_count = 0
        skipped_count = 0

        for gw_sku, points, label in SISTERS_POINTS:
            product = Product.objects.filter(gw_sku=gw_sku).first()

            if not product:
                self.stdout.write(
                    self.style.WARNING(f'  [skip]    {label} (SKU {gw_sku} not found in DB)')
                )
                skipped_count += 1
                continue

            updated = UnitType.objects.filter(
                product=product,
                faction=sisters_faction,
            ).update(points_cost=points)

            if updated:
                self.stdout.write(f'  [updated] {label} > {points} pts')
                updated_count += 1
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f'  [no unit] {label} (SKU {gw_sku}) — Sororitas UnitType not found. '
                        f'Run populate_units first.'
                    )
                )
                skipped_count += 1

        self.stdout.write(self.style.SUCCESS(
            f'\nDone! Updated: {updated_count}  |  Skipped: {skipped_count}'
        ))
