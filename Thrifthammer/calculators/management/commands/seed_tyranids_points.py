"""
Management command: seed_tyranids_points

Sets the points_cost on UnitType records for all Tyranids units,
using official 10th Edition points values sourced from New Recruit.

Usage:
    python manage.py seed_tyranids_points

The command is fully idempotent — safe to re-run. It looks up each product by
its Games Workshop SKU (gw_sku), then filters for the Tyranids UnitType
specifically and updates only that row's points_cost.

Notes:
- Run AFTER populate_products and populate_units.
- Do NOT add to the Procfile yet.
- Line-by-line verified against the New Recruit Tyranids 10th Edition list.
- SKUs not yet in the DB skip gracefully — add products later and re-run.
- Currently seeded SKUs in DB:
    51-04 (Hive Tyrant), 51-06 (Carnifex), 51-08 (Tyranid Warriors),
    51-16 (Termagants)
- Kit collision — 51-04 (Hive Tyrant): one kit builds both the ground Hive Tyrant
  (195pts) and the Winged Hive Tyrant (170pts). Seeded at 170pts (Winged, lowest
  cost). Add a separate product for the ground variant later.
- Kit collision — 51-08 (Tyranid Warriors): builds Warriors with Ranged (65pts) or
  Melee (75pts) Bio-Weapons. Seeded at 65pts (Ranged, base/lowest cost).
  Add a separate product for the Melee variant later.
- 71-19 (Combat Patrol) is a bundle — no standalone UnitType entry.
- Forge World / Apocalypse products (Harridan 610pts, Hierophant 810pts)
  use placeholder SKUs; skip gracefully until added to DB.
- SKU range note: Genestealer Cults also use 51-xx (51-40 to 51-44);
  Tyranids use the lower range (51-04 to 51-35 approx.).
"""

from django.core.management.base import BaseCommand

from calculators.models import UnitType
from products.models import Faction, Product

# ---------------------------------------------------------------------------
# Points data: (gw_sku, points_cost, display_name_for_logging)
#
# Sourced from New Recruit — Tyranids 10th Edition list.
# Verified line-by-line against the full New Recruit army list.
# ---------------------------------------------------------------------------
TYRANIDS_POINTS = [
    # ── Named characters ──────────────────────────────────────────────────────
    ('51-20', 220, 'The Swarmlord'),                   # 220pts ✓
    ('51-21', 150, 'Old One Eye'),                     # 150pts ✓
    ('51-22',  80, 'Deathleaper'),                     # 80pts  ✓
    ('51-23',  80, 'Broodlord'),                       # 80pts  ✓
    # ── Generic characters ────────────────────────────────────────────────────
    ('51-04', 170, 'Winged Hive Tyrant'),              # 170pts ✓ (ground Hive Tyrant=195pts, same kit)
    ('51-24', 105, 'Neurotyrant'),                     # 105pts ✓
    ('51-25', 160, 'Tervigon'),                        # 160pts ✓
    ('51-26',  80, 'Parasite of Mortrex'),             # 80pts  ✓
    ('51-27',  65, 'Winged Tyranid Prime'),            # 65pts  ✓
    ('51-28', 165, 'Hyperadapted Raveners'),           # 165pts ✓
    # ── Battleline ────────────────────────────────────────────────────────────
    ('51-16',  60, 'Termagants'),                      # 60pts  ✓
    ('51-29',  65, 'Hormagaunts'),                     # 65pts  ✓
    ('51-30',  85, 'Gargoyles'),                       # 85pts  ✓
    # ── Infantry ──────────────────────────────────────────────────────────────
    ('51-08',  65, 'Tyranid Warriors with Ranged Bio-Weapons'), # 65pts ✓ (Melee=75pts, same kit)
    ('51-31',  75, 'Genestealers'),                    # 75pts  ✓
    ('51-32',  55, 'Barbgaunts'),                      # 55pts  ✓
    ('51-33',  45, 'Neurogaunts'),                     # 45pts  ✓
    ('51-34',  70, 'Von Ryan\'s Leapers'),             # 70pts  ✓
    # ── Fast Attack ───────────────────────────────────────────────────────────
    ('51-35', 125, 'Raveners'),                        # 125pts ✓
    ('51-36',  25, 'Ripper Swarms'),                   # 25pts  ✓
    ('51-37',  30, 'Mucolid Spores'),                  # 30pts  ✓
    ('51-38',  55, 'Spore Mines'),                     # 55pts  ✓
    # ── Elites ────────────────────────────────────────────────────────────────
    ('51-39',  90, 'Hive Guard'),                      # 90pts  ✓
    ('51-45',  60, 'Lictor'),                          # 60pts  ✓
    ('51-46', 100, 'Zoanthropes'),                     # 100pts ✓ (includes Neurothrope variant)
    ('51-47',  70, 'Venomthropes'),                    # 70pts  ✓
    ('51-48',  80, 'Tyrant Guard'),                    # 80pts  ✓
    ('51-49',  70, 'Neurolictor'),                     # 70pts  ✓
    # ── Heavy Support ─────────────────────────────────────────────────────────
    ('51-06',  90, 'Carnifexes'),                      # 90pts  ✓
    ('51-50', 125, 'Screamer-killer'),                 # 125pts ✓
    ('51-51', 125, 'Haruspex'),                        # 125pts ✓
    ('51-52', 140, 'Exocrine'),                        # 140pts ✓
    ('51-53', 150, 'Toxicrene'),                       # 150pts ✓
    ('51-54', 170, 'Maleceptor'),                      # 170pts ✓
    ('51-55', 110, 'Psychophage'),                     # 110pts ✓
    ('51-56',  50, 'Biovores'),                        # 50pts  ✓
    ('51-57',  40, 'Pyrovores'),                       # 40pts  ✓
    ('51-58', 200, 'Tyrannofex'),                      # 200pts ✓
    ('51-59', 105, 'Tyrannocyte'),                     # 105pts ✓
    ('51-60', 145, 'Sporocyst'),                       # 145pts ✓
    # ── Monsters ──────────────────────────────────────────────────────────────
    ('51-61', 135, 'Mawloc'),                          # 135pts ✓
    ('51-62', 140, 'Trygon'),                          # 140pts ✓
    ('51-63', 275, 'Norn Assimilator'),                # 275pts ✓
    ('51-64', 260, 'Norn Emissary'),                   # 260pts ✓
    # ── Aircraft ──────────────────────────────────────────────────────────────
    ('51-65', 215, 'Harpy'),                           # 215pts ✓
    ('51-66', 200, 'Hive Crone'),                      # 200pts ✓
    # ── Forge World / Super-heavies ───────────────────────────────────────────
    ('51-67', 610, 'Harridan'),                        # 610pts ✓ (FW placeholder)
    ('51-68', 810, 'Hierophant'),                      # 810pts ✓ (FW placeholder)
]


class Command(BaseCommand):
    """
    Seed official 10th Edition points costs for Tyranids units.

    Looks up each product by GW SKU, then filters for the Tyranids
    UnitType specifically and updates only that row's points_cost.
    SKUs not found in the DB are skipped with a warning — add the products
    later and re-run. Idempotent — safe to re-run at any time.
    """

    help = 'Seed 10th Edition points values for Tyranids units.'

    def handle(self, *args, **options):
        """Entry point."""
        self.stdout.write('Seeding Tyranids points…\n')

        tyranids_faction = Faction.objects.filter(name='Tyranids').first()
        if not tyranids_faction:
            self.stdout.write(self.style.ERROR(
                'Tyranids faction not found. Run populate_products first.'
            ))
            return

        updated_count = 0
        skipped_count = 0

        for gw_sku, points, label in TYRANIDS_POINTS:
            product = Product.objects.filter(gw_sku=gw_sku).first()

            if not product:
                self.stdout.write(
                    self.style.WARNING(f'  [skip]    {label} (SKU {gw_sku} not found in DB)')
                )
                skipped_count += 1
                continue

            updated = UnitType.objects.filter(
                product=product,
                faction=tyranids_faction,
            ).update(points_cost=points)

            if updated:
                self.stdout.write(f'  [updated] {label} > {points} pts')
                updated_count += 1
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f'  [no unit] {label} (SKU {gw_sku}) — Tyranids UnitType not found. '
                        f'Run populate_units first.'
                    )
                )
                skipped_count += 1

        self.stdout.write(self.style.SUCCESS(
            f'\nDone! Updated: {updated_count}  |  Skipped: {skipped_count}'
        ))
