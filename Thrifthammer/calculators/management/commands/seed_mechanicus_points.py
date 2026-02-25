"""
Management command: seed_mechanicus_points

Sets the points_cost on UnitType records for all Adeptus Mechanicus units,
using official 10th Edition points values sourced from New Recruit.

Usage:
    python manage.py seed_mechanicus_points

The command is fully idempotent — safe to re-run. It looks up each product by
its Games Workshop SKU (gw_sku), then filters for the Adeptus Mechanicus UnitType
specifically and updates only that row's points_cost.

Notes:
- Run AFTER populate_products and populate_units.
- Do NOT add to the Procfile yet.
- Line-by-line verified against the New Recruit Adeptus Mechanicus 10th Edition list.
- SKUs not yet in the DB are included so they seed automatically when products are added.
- Currently seeded SKUs in DB: 59-06, 59-10, 59-11, 59-14, 59-16, 59-18, 59-20
- 59-25 (Combat Patrol) is a bundle — no UnitType entry.
- 59-20 (Electropriests): one box builds either Corpuscarii (65pts) or Fulgurite
  Electro-Priests (70pts). Seeded at 65pts (Corpuscarii base cost).
- All other units skip gracefully until products are added.
"""

from django.core.management.base import BaseCommand

from calculators.models import UnitType
from products.models import Faction, Product

# ---------------------------------------------------------------------------
# Points data: (gw_sku, points_cost, display_name_for_logging)
#
# Sourced from New Recruit — Adeptus Mechanicus 10th Edition list.
# Verified line-by-line against the full New Recruit army list.
# ---------------------------------------------------------------------------
MECHANICUS_POINTS = [
    # ── Named characters ─────────────────────────────────────────────────────
    ('59-01', 210, 'Belisarius Cawl'),                     # 210pts ✓
    # ── Generic characters ────────────────────────────────────────────────────
    ('59-02',  35, 'Cybernetica Datasmith'),               # 35pts  ✓
    ('59-03',  35, 'Skitarii Marshal'),                    # 35pts  ✓
    ('59-04',  50, 'Sydonian Skatros'),                    # 50pts  ✓
    ('59-06',  65, 'Tech-Priest Dominus'),                 # 65pts  ✓
    ('59-07',  55, 'Tech-Priest Enginseer'),               # 55pts  ✓
    ('59-08',  60, 'Tech-Priest Manipulus'),               # 60pts  ✓
    ('59-05',  45, 'Technoarcheologist'),                  # 45pts  ✓
    # ── Battleline ────────────────────────────────────────────────────────────
    ('59-10',  85, 'Skitarii Rangers'),                    # 85pts  ✓
    ('59-11',  95, 'Skitarii Vanguard'),                   # 95pts  ✓
    # ── Infantry ──────────────────────────────────────────────────────────────
    ('59-20',  65, 'Corpuscarii Electro-Priests'),         # 65pts  ✓ (59-20 also builds Fulgurite @ 70pts)
    ('59-21',  60, 'Servitor Battleclade'),                # 60pts  ✓
    ('59-22',  75, 'Sicarian Infiltrators'),               # 75pts  ✓
    ('59-23',  80, 'Sicarian Ruststalkers'),               # 80pts  ✓
    ('59-18', 105, 'Kataphron Destroyers'),                # 105pts ✓
    ('59-24', 160, 'Kataphron Breachers'),                 # 160pts ✓
    ('59-26', 180, 'Kastelan Robots'),                     # 180pts ✓
    # ── Fast Attack ───────────────────────────────────────────────────────────
    ('59-27',  75, 'Pteraxii Skystalkers'),                # 75pts  ✓
    ('59-28',  80, 'Pteraxii Sterylizors'),                # 80pts  ✓
    ('59-29',  60, 'Serberys Raiders'),                    # 60pts  ✓
    ('59-30',  55, 'Serberys Sulphurhounds'),              # 55pts  ✓
    ('59-14',  85, 'Ironstrider Ballistarii'),             # 85pts  ✓
    ('59-31',  55, 'Sydonian Dragoons with Radium Jezzails'), # 55pts ✓
    ('59-32',  65, 'Sydonian Dragoons with Taser Lances'), # 65pts  ✓
    # ── Vehicles ──────────────────────────────────────────────────────────────
    ('59-16', 155, 'Onager Dunecrawler'),                  # 155pts ✓
    ('59-33', 165, 'Skorpius Disintegrator'),              # 165pts ✓
    ('59-34',  85, 'Skorpius Dunerider'),                  # 85pts  ✓
    # ── Aircraft ──────────────────────────────────────────────────────────────
    ('59-35', 160, 'Archaeopter Fusilave'),                # 160pts ✓
    ('59-36', 185, 'Archaeopter Stratoraptor'),            # 185pts ✓
    ('59-37', 150, 'Archaeopter Transvector'),             # 150pts ✓
]


class Command(BaseCommand):
    """
    Seed official 10th Edition points costs for Adeptus Mechanicus units.

    Looks up each product by GW SKU, then filters for the Adeptus Mechanicus
    UnitType specifically and updates only that row's points_cost.
    SKUs not found in the DB are skipped with a warning — add the products
    later and re-run. Idempotent — safe to re-run at any time.
    """

    help = 'Seed 10th Edition points values for Adeptus Mechanicus units.'

    def handle(self, *args, **options):
        """Entry point."""
        self.stdout.write('Seeding Adeptus Mechanicus points…\n')

        mechanicus_faction = Faction.objects.filter(name='Adeptus Mechanicus').first()
        if not mechanicus_faction:
            self.stdout.write(self.style.ERROR(
                'Adeptus Mechanicus faction not found. Run populate_products first.'
            ))
            return

        updated_count = 0
        skipped_count = 0

        for gw_sku, points, label in MECHANICUS_POINTS:
            product = Product.objects.filter(gw_sku=gw_sku).first()

            if not product:
                self.stdout.write(
                    self.style.WARNING(f'  [skip]    {label} (SKU {gw_sku} not found in DB)')
                )
                skipped_count += 1
                continue

            updated = UnitType.objects.filter(
                product=product,
                faction=mechanicus_faction,
            ).update(points_cost=points)

            if updated:
                self.stdout.write(f'  [updated] {label} > {points} pts')
                updated_count += 1
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f'  [no unit] {label} (SKU {gw_sku}) — Mechanicus UnitType not found. '
                        f'Run populate_units first.'
                    )
                )
                skipped_count += 1

        self.stdout.write(self.style.SUCCESS(
            f'\nDone! Updated: {updated_count}  |  Skipped: {skipped_count}'
        ))
