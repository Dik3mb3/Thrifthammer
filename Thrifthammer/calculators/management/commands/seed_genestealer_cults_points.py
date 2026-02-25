"""
Management command: seed_genestealer_cults_points

Sets the points_cost on UnitType records for all Genestealer Cults units,
using official 10th Edition points values sourced from New Recruit.

Usage:
    python manage.py seed_genestealer_cults_points

The command is fully idempotent — safe to re-run. It looks up each product by
its Games Workshop SKU (gw_sku), then filters for the Genestealer Cults
UnitType specifically and updates only that row's points_cost.

Notes:
- Run AFTER populate_products and populate_units.
- Do NOT add to the Procfile yet.
- Line-by-line verified against the New Recruit Genestealer Cults 10th Edition list.
- SKUs not yet in the DB skip gracefully — add products later and re-run.
- Currently seeded SKUs in DB:
    51-40 (Neophyte Hybrids), 51-41 (Acolyte Hybrids), 51-42 (Patriarch),
    51-43 (Magus), 51-44 (Aberrants)
- 51-41 (Acolyte Hybrids): one kit builds both Acolyte Hybrids with Autopistols
  (65pts) and Acolyte Hybrids with Hand Flamers (70pts). Seeded at 65pts (base).
  Add a separate product for the hand flamer variant later.
"""

from django.core.management.base import BaseCommand

from calculators.models import UnitType
from products.models import Faction, Product

# ---------------------------------------------------------------------------
# Points data: (gw_sku, points_cost, display_name_for_logging)
#
# Sourced from New Recruit — Genestealer Cults 10th Edition list.
# Verified line-by-line against the full New Recruit army list.
# ---------------------------------------------------------------------------
GENESTEALER_CULTS_POINTS = [
    # ── Named / unique characters ─────────────────────────────────────────────
    ('51-01',  85, 'Abominant'),                           # 85pts  ✓
    ('51-02',  70, 'Benefictus'),                          # 70pts  ✓
    ('51-03',  60, 'Kelermorph'),                          # 60pts  ✓
    # ── Generic characters ────────────────────────────────────────────────────
    ('51-04',  50, 'Acolyte Iconward'),                    # 50pts  ✓
    ('51-05',  50, 'Biophagus'),                           # 50pts  ✓
    ('51-06',  50, 'Clamavus'),                            # 50pts  ✓
    ('51-07',  55, 'Jackal Alphus'),                       # 55pts  ✓
    ('51-08',  45, 'Locus'),                               # 45pts  ✓
    ('51-43',  50, 'Magus'),                               # 50pts  ✓
    ('51-09',  60, 'Nexos'),                               # 60pts  ✓
    ('51-42',  75, 'Patriarch'),                           # 75pts  ✓
    ('51-10',  70, 'Primus'),                              # 70pts  ✓
    ('51-11',  65, 'Reductus Saboteur'),                   # 65pts  ✓
    ('51-12',  50, 'Sanctus'),                             # 50pts  ✓
    # ── Battleline ────────────────────────────────────────────────────────────
    ('51-40',  65, 'Neophyte Hybrids'),                    # 65pts  ✓
    # ── Infantry ──────────────────────────────────────────────────────────────
    ('51-44', 135, 'Aberrants'),                           # 135pts ✓
    ('51-41',  65, 'Acolyte Hybrids'),                     # 65pts  ✓ (70pts w/ hand flamers, same kit)
    ('51-13',  70, 'Hybrid Metamorphs'),                   # 70pts  ✓
    ('51-14',  75, 'Purestrain Genestealers'),             # 75pts  ✓
    # ── Fast Attack ───────────────────────────────────────────────────────────
    ('51-15',  85, 'Atalan Jackals'),                      # 85pts  ✓
    # ── Vehicles ──────────────────────────────────────────────────────────────
    ('51-16',  95, 'Achilles Ridgerunners'),               # 95pts  ✓
    ('51-17', 120, 'Goliath Rockgrinder'),                 # 120pts ✓
    ('51-18',  85, 'Goliath Truck'),                       # 85pts  ✓
]


class Command(BaseCommand):
    """
    Seed official 10th Edition points costs for Genestealer Cults units.

    Looks up each product by GW SKU, then filters for the Genestealer Cults
    UnitType specifically and updates only that row's points_cost.
    SKUs not found in the DB are skipped with a warning — add the products
    later and re-run. Idempotent — safe to re-run at any time.
    """

    help = 'Seed 10th Edition points values for Genestealer Cults units.'

    def handle(self, *args, **options):
        """Entry point."""
        self.stdout.write('Seeding Genestealer Cults points…\n')

        gsc_faction = Faction.objects.filter(name='Genestealer Cults').first()
        if not gsc_faction:
            self.stdout.write(self.style.ERROR(
                'Genestealer Cults faction not found. Run populate_products first.'
            ))
            return

        updated_count = 0
        skipped_count = 0

        for gw_sku, points, label in GENESTEALER_CULTS_POINTS:
            product = Product.objects.filter(gw_sku=gw_sku).first()

            if not product:
                self.stdout.write(
                    self.style.WARNING(f'  [skip]    {label} (SKU {gw_sku} not found in DB)')
                )
                skipped_count += 1
                continue

            updated = UnitType.objects.filter(
                product=product,
                faction=gsc_faction,
            ).update(points_cost=points)

            if updated:
                self.stdout.write(f'  [updated] {label} > {points} pts')
                updated_count += 1
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f'  [no unit] {label} (SKU {gw_sku}) — GSC UnitType not found. '
                        f'Run populate_units first.'
                    )
                )
                skipped_count += 1

        self.stdout.write(self.style.SUCCESS(
            f'\nDone! Updated: {updated_count}  |  Skipped: {skipped_count}'
        ))
