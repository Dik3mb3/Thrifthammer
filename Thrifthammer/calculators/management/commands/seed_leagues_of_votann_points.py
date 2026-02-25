"""
Management command: seed_leagues_of_votann_points

Sets the points_cost on UnitType records for all Leagues of Votann units,
using official 10th Edition points values sourced from New Recruit.

Usage:
    python manage.py seed_leagues_of_votann_points

The command is fully idempotent — safe to re-run. It looks up each product by
its Games Workshop SKU (gw_sku), then filters for the Leagues of Votann
UnitType specifically and updates only that row's points_cost.

Notes:
- Run AFTER populate_products and populate_units.
- Do NOT add to the Procfile yet.
- Line-by-line verified against the New Recruit Leagues of Votann 10th Edition list.
- SKUs not yet in the DB skip gracefully — add products later and re-run.
- Currently seeded SKUs in DB:
    73-06 (Kahl), 73-10 (Hearthkyn Warriors), 73-12 (Hernkyn Pioneers),
    73-14 (Einhyr Hearthguard)
- 73-25 (Combat Patrol) is a bundle — no UnitType entry.
"""

from django.core.management.base import BaseCommand

from calculators.models import UnitType
from products.models import Faction, Product

# ---------------------------------------------------------------------------
# Points data: (gw_sku, points_cost, display_name_for_logging)
#
# Sourced from New Recruit — Leagues of Votann 10th Edition list.
# Verified line-by-line against the full New Recruit army list.
# ---------------------------------------------------------------------------
LEAGUES_OF_VOTANN_POINTS = [
    # ── Named characters ──────────────────────────────────────────────────────
    ('73-01',  95, 'Buri Aegnirssen'),                     # 95pts  ✓
    ('73-02',  95, 'Ûthar the Destined'),                  # 95pts  ✓
    # ── Generic characters ────────────────────────────────────────────────────
    ('73-03',  65, 'Arcanyst Evaluator'),                  # 65pts  ✓
    ('73-04',  75, 'Brôkhyr Iron-master'),                 # 75pts  ✓
    ('73-05',  70, 'Einhyr Champion'),                     # 70pts  ✓
    ('73-07',  65, 'Grimnyr'),                             # 65pts  ✓
    ('73-06',  65, 'Kâhl'),                                # 65pts  ✓
    ('73-08',  45, 'Memnyr Strategist'),                   # 45pts  ✓
    # ── Battleline ────────────────────────────────────────────────────────────
    ('73-10', 100, 'Hearthkyn Warriors'),                  # 100pts ✓
    # ── Infantry ──────────────────────────────────────────────────────────────
    ('73-09',  80, 'Brôkhyr Thunderkyn'),                  # 80pts  ✓
    ('73-11', 100, 'Cthonian Beserks'),                    # 100pts ✓
    ('73-15', 110, 'Cthonian Earthshakers'),               # 110pts ✓
    ('73-14', 135, 'Einhyr Hearthguard'),                  # 135pts ✓
    ('73-16',  90, 'Hernkyn Yaegirs'),                     # 90pts  ✓
    ('73-17',  85, 'Ironkin Steeljacks'),                  # 85pts  ✓ (both weapon configs same pts)
    # ── Fast Attack ───────────────────────────────────────────────────────────
    ('73-12',  80, 'Hernkyn Pioneers'),                    # 80pts  ✓
    # ── Vehicles ──────────────────────────────────────────────────────────────
    ('73-18',  90, 'Sagitaur'),                            # 90pts  ✓
    ('73-19',  75, 'Kapricus Carrier'),                    # 75pts  ✓
    ('73-20',  70, 'Kapricus Defenders'),                  # 70pts  ✓
    # ── Heavy vehicles ────────────────────────────────────────────────────────
    ('73-21', 240, 'Hekaton Land Fortress'),               # 240pts ✓
]


class Command(BaseCommand):
    """
    Seed official 10th Edition points costs for Leagues of Votann units.

    Looks up each product by GW SKU, then filters for the Leagues of Votann
    UnitType specifically and updates only that row's points_cost.
    SKUs not found in the DB are skipped with a warning — add the products
    later and re-run. Idempotent — safe to re-run at any time.
    """

    help = 'Seed 10th Edition points values for Leagues of Votann units.'

    def handle(self, *args, **options):
        """Entry point."""
        self.stdout.write('Seeding Leagues of Votann points…\n')

        lov_faction = Faction.objects.filter(name='Leagues of Votann').first()
        if not lov_faction:
            self.stdout.write(self.style.ERROR(
                'Leagues of Votann faction not found. Run populate_products first.'
            ))
            return

        updated_count = 0
        skipped_count = 0

        for gw_sku, points, label in LEAGUES_OF_VOTANN_POINTS:
            product = Product.objects.filter(gw_sku=gw_sku).first()

            if not product:
                self.stdout.write(
                    self.style.WARNING(f'  [skip]    {label} (SKU {gw_sku} not found in DB)')
                )
                skipped_count += 1
                continue

            updated = UnitType.objects.filter(
                product=product,
                faction=lov_faction,
            ).update(points_cost=points)

            if updated:
                self.stdout.write(f'  [updated] {label} > {points} pts')
                updated_count += 1
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f'  [no unit] {label} (SKU {gw_sku}) — LoV UnitType not found. '
                        f'Run populate_units first.'
                    )
                )
                skipped_count += 1

        self.stdout.write(self.style.SUCCESS(
            f'\nDone! Updated: {updated_count}  |  Skipped: {skipped_count}'
        ))
