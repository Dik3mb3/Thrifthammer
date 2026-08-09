"""
Management command: seed_chaos_space_marines_points

Sets points_cost, category, and active status on UnitType records for
Chaos Space Marines units, using official 11th Edition data sourced from
the BSData community BattleScribe project (github.com/BSData/wh40k-11e),
the same data New Recruit itself is built on.

Usage:
    python manage.py seed_chaos_space_marines_points

The command is fully idempotent -- safe to re-run. It looks up each unit by
(name, faction) -- the same pair UnitType enforces uniqueness on.

Notes:
- Chaos Space Marines is architecturally the base faction here, same role
  as Space Marines on the loyalist side -- Death Guard, Emperor's Children,
  Thousand Sons, and World Eaters all have parent_faction = Chaos Space
  Marines, and its own BSData file ("Chaos - Chaos Space Marines.json") is
  self-contained (142 entries), not a thin chapter-style overlay.
- Renames (old DB name -> real BSData name):
    ('Chaos Defiler', 'Defiler'),
    ('Chaos Helbrute', 'Helbrute'),
    ('Chaos Sorcerer Lord in Terminator Armour', 'Sorcerer in Terminator Armour'),
    ('Chaos Space Marines Legionaries', 'Legionaries'),
    ('Chaos Space Marines Sorcerer', 'Sorcerer'),
- Two multi-build splits, same pattern as the Space Marines Predator
  split done earlier this project:
    * 'Chaos Predator' (43-09) -> Chaos Predator Annihilator (145pts) /
      Chaos Predator Destructor (150pts)
    * 'Daemon Prince' (99120201130) -> Heretic Astartes Daemon Prince
      (165pts, no wings) / Heretic Astartes Daemon Prince with wings
      (180pts) -- the kit has an optional-wings build.
- ~32 new units link to the dedicated CSM-series product line
  (CSM-001 through CSM-034), including two dual-unit boxes sharing one
  SKU each: Huron Blackheart + Masters of the Maelstrom (CSM-015),
  Venomcrawler + Obliterators (CSM-027). 'Cultist Mob' and
  'Fellgor Beastmen' matched existing CSM-series products under different
  retail names (Chaos Cultists / Fellgor Ravagers) -- user-confirmed
  2026-08-07.
- 4 units CSM's list includes are legion-specific products already
  faction-tagged to Death Guard / Emperor's Children / Thousand Sons /
  World Eaters: Khorne Berzerkers, Rubric Marines, Plague Marines, Noise
  Marines. Linked as new cross-faction shared-SKU rows under Chaos Space
  Marines (same product, same "one product many faction-scoped rows"
  pattern used since Aeldari/Agents of the Imperium) -- user confirmed
  CSM lists can take these 2026-08-07.
- 'Chaos Space Marines Combat Patrol' deactivated -- a bundle box, not a
  unit. User confirmed 2026-08-07.
- 'Warp Talons' (125pts, Infantry) confirmed real in 11e with no matching
  product anywhere in the catalog -- tracked in
  memory/project_11e_calculator_migration.md, not fabricated here.
"""

from django.core.management.base import BaseCommand

from calculators.models import UnitType
from products.models import Faction, Product

# ---------------------------------------------------------------------------
# Renames applied first: (old_name, new_name)
# ---------------------------------------------------------------------------
CSM_RENAMES = [
    ('Chaos Defiler', 'Defiler'),
    ('Chaos Helbrute', 'Helbrute'),
    ('Chaos Sorcerer Lord in Terminator Armour', 'Sorcerer in Terminator Armour'),
    ('Chaos Space Marines Legionaries', 'Legionaries'),
    ('Chaos Space Marines Sorcerer', 'Sorcerer'),
]

# ---------------------------------------------------------------------------
# Bundle rows -- deactivated, never given points.
# ---------------------------------------------------------------------------
CSM_DEACTIVATE = [
    'Chaos Space Marines Combat Patrol',
    # Superseded by the Predator/Daemon Prince splits above -- the original
    # unified rows were left active by mistake on the first run, caught
    # while building the datasheets command (2026-08-07).
    'Chaos Predator',
    'Daemon Prince',
]

# ---------------------------------------------------------------------------
# Unit data: (gw_sku, points_cost, category, name)
# ---------------------------------------------------------------------------
CHAOS_SPACE_MARINES_UNITS = [
    ('CSM-001', 295, 'epic_hero', 'Abaddon the Despoiler'),
    ('CSM-002', 90, 'infantry', 'Accursed Cultists'),
    ('CSM-003', 70, 'mounted', 'Chaos Bikers'),
    ('99120102052', 220, 'vehicle', 'Chaos Land Raider'),
    ('CSM-029', 90, 'character', 'Chaos Lord'),
    ('CSM-005', 85, 'character', 'Chaos Lord in Terminator Armour'),
    ('CSM-006', 80, 'character', 'Chaos Lord with Jump Pack'),
    ('43-09', 145, 'vehicle', 'Chaos Predator Annihilator'),
    ('43-09', 150, 'vehicle', 'Chaos Predator Destructor'),
    ('99120102092', 65, 'transport', 'Chaos Rhino'),
    ('99120201050', 60, 'monster', 'Chaos Spawn'),
    ('99120102097', 175, 'infantry', 'Chaos Terminator Squad'),
    ('P-CSM-VINDICATOR', 185, 'vehicle', 'Chaos Vindicator'),
    ('CSM-007', 135, 'infantry', 'Chosen'),
    ('CSM-008', 45, 'character', 'Cultist Firebrand'),
    ('CSM-004', 50, 'battleline', 'Cultist Mob'),
    ('CSM-009', 90, 'epic_hero', 'Cypher'),
    ('CSM-010', 65, 'character', 'Dark Apostle'),
    ('CSM-011', 90, 'character', 'Dark Commune'),
    ('P-CSM-DEFILER-2026', 300, 'vehicle', 'Defiler'),
    ('CSM-012', 100, 'epic_hero', 'Fabius Bile'),
    ('CSM-032', 60, 'infantry', 'Fellgor Beastmen'),
    ('99120102089', 160, 'vehicle', 'Forgefiend'),
    ('CSM-013', 90, 'epic_hero', 'Haarken Worldclaimer'),
    ('CSM-014', 125, 'infantry', 'Havocs'),
    ('prod2430129-99120102043', 130, 'vehicle', 'Helbrute'),
    ('99120102090', 175, 'vehicle', 'Heldrake'),
    ('99120201130', 165, 'character', 'Heretic Astartes Daemon Prince'),
    ('99120201130', 180, 'character', 'Heretic Astartes Daemon Prince with wings'),
    ('CSM-015', 130, 'epic_hero', 'Huron Blackheart'),
    ('43-60', 170, 'battleline', 'Khorne Berzerkers'),
    ('CSM-016', 120, 'epic_hero', 'Kravek Morne'),
    ('43-06', 90, 'battleline', 'Legionaries'),
    ('CSM-017', 160, 'character', 'Lord Discordant on Helstalker'),
    ('P-CSM-MASTER-EXEC', 70, 'character', 'Master of Executions'),
    ('CSM-018', 60, 'character', 'Master of Possession'),
    ('CSM-015', 145, 'epic_hero', 'Masters of the Maelstrom'),
    ('99120102089', 130, 'vehicle', 'Maulerfiend'),
    ('CSM-019', 165, 'infantry', 'Mutilators'),
    ('CSM-034', 100, 'infantry', 'Nemesis Claw'),
    ('CSM-020', 125, 'fortification', 'Noctilith Crown'),
    ('99120102204', 145, 'infantry', 'Noise Marines'),
    ('CSM-027', 160, 'infantry', 'Obliterators'),
    ('43-50', 90, 'battleline', 'Plague Marines'),
    ('CSM-021', 120, 'infantry', 'Possessed'),
    ('CSM-022', 110, 'infantry', 'Red Corsairs Raiders'),
    ('CSM-023', 60, 'character', 'Red Corsairs Reave-captain'),
    ('43-35', 100, 'battleline', 'Rubric Marines'),
    ('99070102015', 60, 'character', 'Sorcerer'),
    ('P-CSM-SORC-TERM', 80, 'character', 'Sorcerer in Terminator Armour'),
    ('CSM-024', 70, 'character', 'Traitor Enforcer'),
    ('CSM-025', 70, 'infantry', 'Traitor Guardsmen Squad'),
    ('CSM-026', 220, 'epic_hero', 'Vashtorr the Arkifane'),
    ('CSM-027', 120, 'vehicle', 'Venomcrawler'),
    ('CSM-028', 60, 'character', 'Warpsmith'),
]


class Command(BaseCommand):
    """
    Seed 11th Edition points, category, and active status for Chaos Space
    Marines units.

    Looks up each unit by (name, faction) and updates points_cost, category,
    and is_active in place; creates the row if it doesn't exist yet (linking
    the product by gw_sku when one is given). Idempotent -- safe to re-run.
    """

    help = 'Seed 11th Edition points and categories for Chaos Space Marines units.'

    def add_arguments(self, parser):
        """Add --dry-run option."""
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Preview changes without saving anything.',
        )

    def handle(self, *args, **options):
        """Entry point."""
        dry_run = options['dry_run']
        self.stdout.write(
            'Seeding Chaos Space Marines points (11th Edition)' + (' [DRY RUN]' if dry_run else '') + '\u2026\n'
        )

        fac = Faction.objects.filter(name='Chaos Space Marines').first()
        if not fac:
            self.stdout.write(self.style.ERROR(
                'Chaos Space Marines faction not found. Run populate_products first.'
            ))
            return

        for old_name, new_name in CSM_RENAMES:
            unit = UnitType.objects.filter(name=old_name, faction=fac).first()
            if unit:
                self.stdout.write(f'  [rename] {old_name!r} -> {new_name!r}')
                if not dry_run:
                    unit.name = new_name
                    unit.save(update_fields=['name'])

        for name in CSM_DEACTIVATE:
            unit = UnitType.objects.filter(name=name, faction=fac).first()
            if unit and unit.is_active:
                self.stdout.write(f'  [deactivate] {name!r}')
                if not dry_run:
                    unit.is_active = False
                    unit.save(update_fields=['is_active'])

        updated_count = 0
        created_count = 0
        skipped_count = 0

        for gw_sku, points, category, label in CHAOS_SPACE_MARINES_UNITS:
            product = Product.objects.filter(gw_sku=gw_sku).first() if gw_sku else None

            if gw_sku and not product:
                self.stdout.write(
                    self.style.WARNING(f'  [skip]    {label} (SKU {gw_sku} not found in DB)')
                )
                skipped_count += 1
                continue

            unit = UnitType.objects.filter(name=label, faction=fac).first()

            if unit:
                changes = []
                if unit.points_cost != points:
                    changes.append(f'points {unit.points_cost}->{points}')
                if unit.category != category:
                    changes.append(f'category {unit.category}->{category}')
                if not unit.is_active:
                    changes.append('reactivating')
                change_note = f" ({', '.join(changes)})" if changes else ' (no change)'

                if not dry_run:
                    unit.points_cost = points
                    unit.category = category
                    unit.is_active = True
                    update_fields = ['points_cost', 'category', 'is_active']
                    if product and unit.product_id != product.id:
                        unit.product = product
                        update_fields.append('product')
                    unit.save(update_fields=update_fields)
                self.stdout.write(f'  [update] {label} > {points} pts ({category}){change_note}')
                updated_count += 1
            else:
                if not dry_run:
                    UnitType.objects.create(
                        name=label,
                        faction=fac,
                        product=product,
                        category=category,
                        points_cost=points,
                        typical_quantity=1,
                        is_active=True,
                    )
                self.stdout.write(f'  [create] {label} > {points} pts ({category})')
                created_count += 1

        self.stdout.write(self.style.SUCCESS(
            f'\nDone! Updated: {updated_count}  |  Created: {created_count}  |  Skipped: {skipped_count}'
        ))
