"""
Management command: seed_world_eaters_points

Sets points_cost, category, and active status on UnitType records for
World Eaters units, using official 11th Edition data sourced from the
BSData community BattleScribe project (github.com/BSData/wh40k-11e), the
same data New Recruit itself is built on.

Usage:
    python manage.py seed_world_eaters_points
    python manage.py seed_world_eaters_points --dry-run

The command is fully idempotent -- safe to re-run. It looks up each unit by
(name, faction) -- the same pair UnitType enforces uniqueness on.

Notes:
- Source: "Chaos - World Eaters.json" -- self-contained (77 own
  sharedSelectionEntries, zero catalogueLinks reference to the CSM
  catalogue). Same architecture as Death Guard/Emperor's Children/
  Thousand Sons: a full separate legion codex with its own points AND
  rules for shared-name units, not a thin overlay. 30 real 11e units --
  the last faction in this project. Of the 68 root entryLinks, 31 need
  external resolution, but all 31 turned out to be [Legends]/[Crucible]/
  BattleScribe-meta entries already excluded by the standard filter --
  no external library fetch was actually needed this time.
- Supersedes the old `seed_world_eaters_points` command (10th Edition,
  never added to the Procfile).
- 29 of 30 units already had an active UnitType row and product from an
  earlier pre-11e-migration populate command -- mostly a refresh pass,
  plus one missing unit and a batch of category corrections.
- **`Defiler` is 270pts for World Eaters** -- different from CSM's/
  Emperor's Children's/Thousand Sons' own 300pts value for the identical
  shared SKU (`P-CSM-DEFILER-2026`), confirming (again) that each Chaos
  legion assigns its own point cost to shared-name units rather than
  inheriting a single shared value.
- **New cross-faction link**: `Chaos Terminators` (165pts, Infantry) has
  no dedicated World Eaters product, but the generic `99120102097` "Chaos
  Terminator Squad" (already linked to a CSM UnitType row at 175pts) is a
  BSData-confirmed legal include -- same mechanism as Khorne Berzerkers/
  Plague Marines/Rubric Marines/Noise Marines earlier in this project.
  World Eaters' own file defines this unit's full ruleset directly (no
  datasheet copy-step needed, unlike Drukhari's Harlequins rows).
- **Category corrections followed BSData's primary categoryLink
  faithfully**, several non-trivial: Bloodcrushers infantry->mounted,
  Bloodletters infantry->battleline, Chaos Land Raider transport->vehicle
  (Vehicle is primary, Transport only a secondary keyword -- same as
  Thousand Sons' Land Raider), Chaos Spawn/Flesh Hounds infantry/
  mounted->monster (Beast maps to monster), Goremongers battleline->
  infantry, Helbrute infantry->vehicle, Jakhals battleline->infantry,
  Khorne Lord of Skulls epic_hero->vehicle, Lord Invocatus character->
  epic_hero, Master of Executions infantry->character, Slaughterbound
  battleline->character, and both Daemon Prince rows epic_hero->character
  (matching BSData's own Character tier here, same as Thousand Sons/
  Emperor's Children's Daemon Prince).
- No backlog items -- all 30 real BSData units resolved to a product.
"""

from django.core.management.base import BaseCommand

from calculators.models import UnitType
from products.models import Faction, Product

# ---------------------------------------------------------------------------
# Unit data: (gw_sku, points_cost, category, name)
# ---------------------------------------------------------------------------
WORLD_EATERS_UNITS = [
    ('43-04', 330, 'epic_hero', 'World Eaters Angron'),
    ('P-KHORNE-BLOODCRUSHERS', 95, 'mounted', 'Bloodcrushers of Khorne'),
    ('P-KHORNE-BLOODLETTERS-40K', 90, 'battleline', 'Bloodletters of Khorne'),
    ('P-KHORNE-BLOODTHIRSTER', 320, 'epic_hero', 'Bloodthirster'),
    ('99120102052', 220, 'vehicle', 'Chaos Land Raider'),
    ('43-09', 130, 'vehicle', 'Chaos Predator Annihilator'),
    ('43-09', 130, 'vehicle', 'Chaos Predator Destructor'),
    ('99120102092', 75, 'transport', 'Chaos Rhino'),
    ('99120201050', 95, 'monster', 'Chaos Spawn'),
    ('99120102097', 165, 'infantry', 'Chaos Terminators'),
    ('99120201130', 200, 'character', 'Daemon Prince of Khorne'),
    ('99120201130', 170, 'character', 'Daemon Prince of Khorne with wings'),
    ('P-CSM-DEFILER-2026', 270, 'vehicle', 'Defiler'),
    ('43-62', 125, 'infantry', 'World Eaters Eightbound'),
    ('P-WE-EXL-EIGHT-2023', 130, 'infantry', 'World Eaters Exalted Eightbound'),
    ('P-KHORNE-FLESHHOUNDS', 75, 'monster', 'Flesh Hounds of Khorne'),
    ('99120102089', 140, 'vehicle', 'Forgefiend'),
    ('P-WE-KT-GOREMONGERS-2025', 75, 'infantry', 'Kill Team: Goremongers (World Eaters)'),
    ('prod2430129-99120102043', 120, 'vehicle', 'Helbrute'),
    ('99120102090', 175, 'vehicle', 'Heldrake'),
    ('P-WE-JAKHALS-2023', 65, 'infantry', 'World Eaters Jakhals'),
    ('43-60', 170, 'battleline', 'World Eaters Berzerkers'),
    ('P-WE-LORD-SKULLS', 505, 'vehicle', 'Khorne Lord of Skulls'),
    ('P-WE-KHARN-2023', 115, 'epic_hero', 'World Eaters Kharn the Betrayer'),
    ('P-WE-LORD-INVOC-2023', 100, 'epic_hero', 'World Eaters Lord Invocatus'),
    ('43-64', 95, 'character', 'World Eaters Lord on Juggernaut'),
    ('P-CSM-MASTER-EXEC', 60, 'character', 'Master of Executions'),
    ('99120102089', 140, 'vehicle', 'Maulerfiend'),
    ('P-KHORNE-SKARBRAND', 315, 'epic_hero', 'Skarbrand the Bloodthirster'),
    ('P-WE-SLAUGHTER-2025', 100, 'character', 'World Eaters Slaughterbound'),
]


class Command(BaseCommand):
    """
    Seed 11th Edition points, category, and active status for World Eaters
    units.

    Looks up each unit by (name, faction) and updates points_cost, category,
    and is_active in place; creates the row if it doesn't exist yet (linking
    the product by gw_sku when one is given). Idempotent -- safe to re-run.
    """

    help = 'Seed 11th Edition points and categories for World Eaters units.'

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
            'Seeding World Eaters points (11th Edition)' + (' [DRY RUN]' if dry_run else '') + '…\n'
        )

        fac = Faction.objects.filter(name='World Eaters').first()
        if not fac:
            self.stdout.write(self.style.ERROR(
                'World Eaters faction not found. Run populate_products first.'
            ))
            return

        updated_count = 0
        created_count = 0
        skipped_count = 0

        for gw_sku, points, category, label in WORLD_EATERS_UNITS:
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
