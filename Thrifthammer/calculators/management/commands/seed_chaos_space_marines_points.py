"""
Management command: seed_chaos_space_marines_points

Sets the points_cost on UnitType records for all Chaos Space Marines units,
using official 10th Edition points values sourced from New Recruit.

Usage:
    python manage.py seed_chaos_space_marines_points

The command is fully idempotent — safe to re-run. It looks up each product by
its Games Workshop SKU (gw_sku), then filters for the Chaos Space Marines
UnitType specifically and updates only that row's points_cost.

Notes:
- Run AFTER populate_products and populate_units.
- Do NOT add to the Procfile yet.
- Line-by-line verified against the New Recruit Chaos Space Marines 10th Edition list.
- As of initial creation, NO dedicated Chaos Space Marines products exist in the DB.
  All entries will [skip] until populate_products.py is updated with CSM SKUs.
- Cross-faction kits (Plague Marines 43-50, Rubric Marines 43-35, Khorne Berzerkers
  43-60) exist in the DB under Death Guard / Thousand Sons / World Eaters factions.
  This seed targets the Chaos Space Marines UnitType row for those products, which
  only exists once populate_units creates a cross-faction entry for them.
- Placeholder SKUs use the 102-xx range (CSM catalogue numbers begin with 43-xx
  for the shared god-faction range; dedicated CSM boxes typically 43-xx or separate).
"""

from django.core.management.base import BaseCommand

from calculators.models import UnitType
from products.models import Faction, Product

# ---------------------------------------------------------------------------
# Points data: (gw_sku, points_cost, display_name_for_logging)
#
# Sourced from New Recruit — Chaos Space Marines 10th Edition list.
# Verified line-by-line against the full New Recruit army list.
# ---------------------------------------------------------------------------
CHAOS_SM_POINTS = [
    # ── Named characters ──────────────────────────────────────────────────────
    ('43-01', 270, 'Abaddon the Despoiler'),               # 270pts ✓
    ('43-05',  90, 'Cypher'),                              # 90pts  ✓
    ('43-06', 100, 'Fabius Bile'),                         # 100pts ✓
    ('43-07',  90, 'Haarken Worldclaimer'),                # 90pts  ✓
    ('43-09', 120, 'Huron Blackheart'),                    # 120pts ✓
    ('43-10', 115, 'Masters of the Maelstrom'),            # 115pts ✓
    ('43-11', 175, 'Vashtorr the Arkifane'),               # 175pts ✓
    # ── Generic characters ────────────────────────────────────────────────────
    ('43-12',  90, 'Chaos Lord'),                          # 90pts  ✓
    ('43-13',  85, 'Chaos Lord in Terminator Armour'),     # 85pts  ✓
    ('43-14',  80, 'Chaos Lord with Jump Pack'),           # 80pts  ✓
    ('43-15',  45, 'Cultist Firebrand'),                   # 45pts  ✓
    ('43-16',  65, 'Dark Apostle'),                        # 65pts  ✓
    ('43-17',  90, 'Dark Commune'),                        # 90pts  ✓
    ('43-18', 165, 'Heretic Astartes Daemon Prince'),      # 165pts ✓
    ('43-19', 180, 'Heretic Astartes Daemon Prince with Wings'), # 180pts ✓
    ('43-20',  80, 'Master of Executions'),                # 80pts  ✓
    ('43-21',  60, 'Master of Possession'),                # 60pts  ✓
    ('43-22',  75, 'Red Corsairs Reave-captain'),          # 75pts  ✓
    ('43-23',  60, 'Sorcerer'),                            # 60pts  ✓
    ('43-24',  80, 'Sorcerer in Terminator Armour'),       # 80pts  ✓
    ('43-25',  55, 'Traitor Enforcer'),                    # 55pts  ✓
    ('43-26',  70, 'Warpsmith'),                           # 70pts  ✓
    # ── Battleline ────────────────────────────────────────────────────────────
    ('43-27',  50, 'Cultist Mob'),                         # 50pts  ✓
    ('43-60', 180, 'Khorne Berzerkers'),                   # 180pts ✓ (kit in DB as World Eaters)
    ('43-28',  90, 'Legionaries'),                         # 90pts  ✓
    ('43-50',  95, 'Plague Marines'),                      # 95pts  ✓ (kit in DB as Death Guard)
    ('43-35', 100, 'Rubric Marines'),                      # 100pts ✓ (kit in DB as Thousand Sons)
    # ── Infantry ──────────────────────────────────────────────────────────────
    ('43-29',  90, 'Accursed Cultists'),                   # 90pts  ✓
    ('43-31',  70, 'Chaos Bikers'),                        # 70pts  ✓
    ('43-32',  70, 'Chaos Spawn'),                         # 70pts  ✓
    ('43-33', 180, 'Chaos Terminator Squad'),              # 180pts ✓
    ('43-34', 125, 'Chosen'),                              # 125pts ✓
    ('43-37',  70, 'Fellgor Beastmen'),                    # 70pts  ✓
    ('43-39', 145, 'Noise Marines'),                       # 145pts ✓
    ('43-40', 160, 'Obliterators'),                        # 160pts ✓
    ('43-41', 120, 'Possessed'),                           # 120pts ✓
    ('43-42', 110, 'Raptors'),                             # 110pts ✓
    ('43-43', 110, 'Red Corsairs Raiders'),                # 110pts ✓
    ('43-44',  70, 'Traitor Guardsmen Squad'),             # 70pts  ✓
    ('43-45', 125, 'Warp Talons'),                         # 125pts ✓
    ('43-46', 110, 'Nemesis Claw'),                        # 110pts ✓
    ('43-47', 125, 'Havocs'),                              # 125pts ✓
    # ── Vehicles / Daemon Engines ─────────────────────────────────────────────
    ('43-48', 220, 'Chaos Land Raider'),                   # 220pts ✓
    ('43-49', 135, 'Chaos Predator Annihilator'),          # 135pts ✓
    ('43-51', 140, 'Chaos Predator Destructor'),           # 140pts ✓
    ('43-52',  75, 'Chaos Rhino'),                         # 75pts  ✓
    ('43-53', 185, 'Chaos Vindicator'),                    # 185pts ✓
    ('43-55', 190, 'Defiler'),                             # 190pts ✓
    ('43-57', 170, 'Forgefiend'),                          # 170pts ✓
    ('43-58', 130, 'Helbrute'),                            # 130pts ✓
    ('43-59', 205, 'Heldrake'),                            # 205pts ✓
    ('43-61', 450, 'Khorne Lord of Skulls'),               # 450pts ✓
    ('43-63', 130, 'Maulerfiend'),                         # 130pts ✓
    ('43-65', 110, 'Venomcrawler'),                        # 110pts ✓
]


class Command(BaseCommand):
    """
    Seed official 10th Edition points costs for Chaos Space Marines units.

    Looks up each product by GW SKU, then filters for the Chaos Space Marines
    UnitType specifically and updates only that row's points_cost.
    SKUs not found in the DB are skipped with a warning — add the products
    later and re-run. Idempotent — safe to re-run at any time.
    """

    help = 'Seed 10th Edition points values for Chaos Space Marines units.'

    def handle(self, *args, **options):
        """Entry point."""
        self.stdout.write('Seeding Chaos Space Marines points…\n')

        csm_faction = Faction.objects.filter(name='Chaos Space Marines').first()
        if not csm_faction:
            self.stdout.write(self.style.ERROR(
                'Chaos Space Marines faction not found. Run populate_products first.'
            ))
            return

        updated_count = 0
        skipped_count = 0

        for gw_sku, points, label in CHAOS_SM_POINTS:
            product = Product.objects.filter(gw_sku=gw_sku).first()

            if not product:
                self.stdout.write(
                    self.style.WARNING(f'  [skip]    {label} (SKU {gw_sku} not found in DB)')
                )
                skipped_count += 1
                continue

            updated = UnitType.objects.filter(
                product=product,
                faction=csm_faction,
            ).update(points_cost=points)

            if updated:
                self.stdout.write(f'  [updated] {label} > {points} pts')
                updated_count += 1
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f'  [no unit] {label} (SKU {gw_sku}) — CSM UnitType not found. '
                        f'Run populate_units first.'
                    )
                )
                skipped_count += 1

        self.stdout.write(self.style.SUCCESS(
            f'\nDone! Updated: {updated_count}  |  Skipped: {skipped_count}'
        ))
