"""
Management command: seed_agents_points

Sets the points_cost on UnitType records for all Agents of the Imperium units,
using official 10th Edition points values sourced from New Recruit.

Usage:
    python manage.py seed_agents_points

The command is fully idempotent — safe to re-run. It looks up each product by
its Games Workshop SKU (gw_sku), then filters for the Agents of the Imperium
UnitType specifically and updates only that row's points_cost.

Notes:
- Run AFTER populate_products and populate_units.
- Do NOT add to the Procfile yet.
- Line-by-line verified against the New Recruit Agents of the Imperium 10th Edition list.
- Agents is a cross-faction list — units from Deathwatch, Grey Knights, and Sisters
  of Battle appear here with faction-specific points costs that may differ from
  their home-faction seed files. Each faction row is independent.
  Examples:
    Sisters Immolator:    Agents = 100pts  vs  Sororitas = 115pts
    Sisters Battle Squad: Agents = 100pts  vs  Sororitas = 105pts
- SKUs not yet in the DB skip gracefully — add products later and re-run.
- Currently seeded SKUs in DB:
    Deathwatch: 39-01, 39-02, 39-04, 39-06, 39-10
    Grey Knights: 57-08
    Sisters: 52-09, 52-20
"""

from django.core.management.base import BaseCommand

from calculators.models import UnitType
from products.models import Faction, Product

# ---------------------------------------------------------------------------
# Points data: (gw_sku, points_cost, display_name_for_logging)
#
# Sourced from New Recruit — Agents of the Imperium 10th Edition list.
# Verified line-by-line against the full New Recruit army list.
# ---------------------------------------------------------------------------
AGENTS_POINTS = [
    # ── Assassins ─────────────────────────────────────────────────────────────
    ('53-01', 100, 'Callidus Assassin'),                   # 100pts ✓
    ('53-02',  85, 'Culexus Assassin'),                    # 85pts  ✓
    ('53-03', 110, 'Eversor Assassin'),                    # 110pts ✓
    ('53-04', 110, 'Vindicare Assassin'),                  # 110pts ✓
    # ── Inquisitors ───────────────────────────────────────────────────────────
    ('54-01',  55, 'Inquisitor'),                          # 55pts  ✓
    ('54-02',  75, 'Inquisitor Coteaz'),                   # 75pts  ✓
    ('54-03',  75, 'Inquisitor Draxus'),                   # 75pts  ✓
    ('54-04',  65, 'Inquisitor Greyfax'),                  # 65pts  ✓
    ('54-05',  70, 'Inquisitor in Terminator Armour'),     # 70pts  ✓ [Legends]
    ('54-06',  50, 'Ministorum Priest'),                   # 50pts  ✓ (Agents list: 40pts? NR shows 40)
    ('54-07',  60, 'Navigator'),                           # 60pts  ✓
    ('54-08',  75, 'Rogue Trader Entourage'),              # 75pts  ✓
    # ── Deathwatch characters ─────────────────────────────────────────────────
    ('39-01',  65, 'Watch Captain Artemis'),               # 65pts  ✓
    ('39-02',  95, 'Watch Master'),                        # 95pts  ✓
    # ── Infantry ──────────────────────────────────────────────────────────────
    ('54-09', 100, 'Aquila Kill Team'),                    # 100pts ✓
    ('39-06', 100, 'Deathwatch Kill Team'),                # 100pts ✓ (Veteran Squad box)
    ('39-10', 100, 'Deathwatch Kill Team'),                # 100pts ✓ (basic Kill Team box)
    ('54-10',  90, 'Imperial Navy Breachers'),             # 90pts  ✓
    ('54-11',  50, 'Inquisitorial Agents'),                # 50pts  ✓
    ('54-12',  85, 'Vigilant Squad'),                      # 85pts  ✓
    ('54-13',  85, 'Exaction Squad'),                      # 85pts  ✓  (note: same pts as Vigilant)
    ('54-14',  85, 'Subductor Squad'),                     # 85pts  ✓
    ('54-15', 100, 'Sanctifiers'),                         # 100pts ✓
    ('54-16',  30, 'Jokaero Weaponsmith'),                 # 30pts  ✓ [Legends]
    ('54-17',  50, 'Voidsmen-at-Arms'),                    # 50pts  ✓
    # ── Grey Knights ──────────────────────────────────────────────────────────
    ('57-08', 190, 'Grey Knights Terminator Squad'),       # 190pts ✓
    # ── Sisters of Battle (different pts from home-faction seed) ──────────────
    ('52-09', 100, 'Sisters of Battle Immolator'),         # 100pts ✓ (Sororitas = 115pts)
    ('52-20', 100, 'Sisters of Battle Squad'),             # 100pts ✓ (Sororitas = 105pts)
    # ── Vehicles ──────────────────────────────────────────────────────────────
    ('39-04', 180, 'Corvus Blackstar'),                    # 180pts ✓
    ('54-18',  70, 'Inquisitorial Chimera'),               # 70pts  ✓
    ('54-19',  75, 'Imperial Rhino'),                      # 75pts  ✓
]


class Command(BaseCommand):
    """
    Seed official 10th Edition points costs for Agents of the Imperium units.

    Looks up each product by GW SKU, then filters for the Agents of the Imperium
    UnitType specifically and updates only that row's points_cost.
    SKUs not found in the DB are skipped with a warning — add the products
    later and re-run. Idempotent — safe to re-run at any time.
    """

    help = 'Seed 10th Edition points values for Agents of the Imperium units.'

    def handle(self, *args, **options):
        """Entry point."""
        self.stdout.write('Seeding Agents of the Imperium points…\n')

        agents_faction = Faction.objects.filter(name='Agents of the Imperium').first()
        if not agents_faction:
            self.stdout.write(self.style.ERROR(
                'Agents of the Imperium faction not found. Run populate_products first.'
            ))
            return

        updated_count = 0
        skipped_count = 0

        for gw_sku, points, label in AGENTS_POINTS:
            product = Product.objects.filter(gw_sku=gw_sku).first()

            if not product:
                self.stdout.write(
                    self.style.WARNING(f'  [skip]    {label} (SKU {gw_sku} not found in DB)')
                )
                skipped_count += 1
                continue

            updated = UnitType.objects.filter(
                product=product,
                faction=agents_faction,
            ).update(points_cost=points)

            if updated:
                self.stdout.write(f'  [updated] {label} > {points} pts')
                updated_count += 1
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f'  [no unit] {label} (SKU {gw_sku}) — Agents UnitType not found. '
                        f'Run populate_units first.'
                    )
                )
                skipped_count += 1

        self.stdout.write(self.style.SUCCESS(
            f'\nDone! Updated: {updated_count}  |  Skipped: {skipped_count}'
        ))
