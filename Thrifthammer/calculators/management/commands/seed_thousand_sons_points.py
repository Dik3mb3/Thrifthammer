"""
Management command: seed_thousand_sons_points

Sets the points_cost on UnitType records for all Thousand Sons units,
using official 10th Edition points values sourced from New Recruit.

Usage:
    python manage.py seed_thousand_sons_points

The command is fully idempotent — safe to re-run. It looks up each product by
its Games Workshop SKU (gw_sku), then filters for the Thousand Sons UnitType
specifically and updates only that row's points_cost.

Notes:
- Run AFTER populate_products and populate_units.
- Do NOT add to the Procfile yet.
- Line-by-line verified against the New Recruit Thousand Sons 10th Edition list.
- SKUs not yet in the DB skip gracefully — add products later and re-run.
- Currently seeded SKUs in DB:
    43-02 (Magnus the Red), 43-30 (Ahriman), 43-35 (Rubric Marines),
    43-36 (Scarab Occult Terminators), 43-38 (Exalted Sorcerers)
- 43-90 (Combat Patrol) is a bundle — no UnitType entry.
- 43-38 (Exalted Sorcerers): kit builds the on-foot Exalted Sorcerer (80pts)
  or mounted Exalted Sorcerer on Disc of Tzeentch (100pts). Seeded at 80pts
  (base foot version). Add a separate product for the disc variant later.
"""

from django.core.management.base import BaseCommand

from calculators.models import UnitType
from products.models import Faction, Product

# ---------------------------------------------------------------------------
# Points data: (gw_sku, points_cost, display_name_for_logging)
#
# Sourced from New Recruit — Thousand Sons 10th Edition list.
# Verified line-by-line against the full New Recruit army list.
# ---------------------------------------------------------------------------
THOUSAND_SONS_POINTS = [
    # ── Named characters ──────────────────────────────────────────────────────
    ('43-02', 435, 'Magnus the Red'),                      # 435pts ✓
    ('43-30', 100, 'Ahriman'),                             # 100pts ✓
    # ── Generic characters ────────────────────────────────────────────────────
    ('43-38',  80, 'Exalted Sorcerer'),                    # 80pts  ✓ (100pts on Disc — same kit)
    ('43-31',  95, 'Infernal Master'),                     # 95pts  ✓
    ('43-32', 180, 'Daemon Prince of Tzeentch'),           # 180pts ✓
    ('43-33', 170, 'Daemon Prince of Tzeentch with Wings'), # 170pts ✓
    ('43-34',  80, 'Sorcerer'),                            # 80pts  ✓
    ('43-37',  85, 'Sorcerer in Terminator Armour'),       # 85pts  ✓
    ('43-39',  60, 'Tzaangor Shaman'),                     # 60pts  ✓
    # ── Battleline ────────────────────────────────────────────────────────────
    ('43-35', 100, 'Rubric Marines'),                      # 100pts ✓
    ('43-40',  70, 'Tzaangors'),                           # 70pts  ✓
    # ── Infantry ──────────────────────────────────────────────────────────────
    ('43-36', 180, 'Scarab Occult Terminators'),           # 180pts ✓
    ('43-41',  45, 'Tzaangor Enlightened'),                # 45pts  ✓ (55pts w/ Fatecaster greatbows)
    ('43-42',  65, 'Chaos Spawn'),                         # 65pts  ✓
    ('43-43',  80, 'Sekhetar Robots'),                     # 80pts  ✓
    # ── Vehicles / Daemon Engines ─────────────────────────────────────────────
    ('43-44', 165, 'Defiler'),                             # 165pts ✓
    ('43-45', 130, 'Forgefiend'),                          # 130pts ✓
    ('43-46', 110, 'Helbrute'),                            # 110pts ✓
    ('43-47', 215, 'Heldrake'),                            # 215pts ✓
    ('43-48', 120, 'Maulerfiend'),                         # 120pts ✓
    ('43-49', 170, 'Mutalith Vortex Beast'),               # 170pts ✓
    # ── Transports ────────────────────────────────────────────────────────────
    ('43-51', 220, 'Chaos Land Raider'),                   # 220pts ✓
    ('43-52', 130, 'Chaos Predator Annihilator'),          # 130pts ✓
    ('43-53', 130, 'Chaos Predator Destructor'),           # 130pts ✓
    ('43-54',  90, 'Chaos Rhino'),                         # 90pts  ✓
    ('43-55', 185, 'Chaos Vindicator'),                    # 185pts ✓
]


class Command(BaseCommand):
    """
    Seed official 10th Edition points costs for Thousand Sons units.

    Looks up each product by GW SKU, then filters for the Thousand Sons
    UnitType specifically and updates only that row's points_cost.
    SKUs not found in the DB are skipped with a warning — add the products
    later and re-run. Idempotent — safe to re-run at any time.
    """

    help = 'Seed 10th Edition points values for Thousand Sons units.'

    def handle(self, *args, **options):
        """Entry point."""
        self.stdout.write('Seeding Thousand Sons points…\n')

        ts_faction = Faction.objects.filter(name='Thousand Sons').first()
        if not ts_faction:
            self.stdout.write(self.style.ERROR(
                'Thousand Sons faction not found. Run populate_products first.'
            ))
            return

        updated_count = 0
        skipped_count = 0

        for gw_sku, points, label in THOUSAND_SONS_POINTS:
            product = Product.objects.filter(gw_sku=gw_sku).first()

            if not product:
                self.stdout.write(
                    self.style.WARNING(f'  [skip]    {label} (SKU {gw_sku} not found in DB)')
                )
                skipped_count += 1
                continue

            updated = UnitType.objects.filter(
                product=product,
                faction=ts_faction,
            ).update(points_cost=points)

            if updated:
                self.stdout.write(f'  [updated] {label} > {points} pts')
                updated_count += 1
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f'  [no unit] {label} (SKU {gw_sku}) — Thousand Sons UnitType not found. '
                        f'Run populate_units first.'
                    )
                )
                skipped_count += 1

        self.stdout.write(self.style.SUCCESS(
            f'\nDone! Updated: {updated_count}  |  Skipped: {skipped_count}'
        ))
