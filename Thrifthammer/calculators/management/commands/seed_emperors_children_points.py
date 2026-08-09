"""
Management command: seed_emperors_children_points

Sets points_cost, category, and active status on UnitType records for
Emperor's Children units, using official 11th Edition data sourced from
the BSData community BattleScribe project (github.com/BSData/wh40k-11e),
the same data New Recruit itself is built on.

Usage:
    python manage.py seed_emperors_children_points
    python manage.py seed_emperors_children_points --dry-run

The command is fully idempotent -- safe to re-run. It looks up each unit by
(name, faction) -- the same pair UnitType enforces uniqueness on.

Notes:
- Source: "Chaos - Emperor's Children.json" -- self-contained (51 own
  sharedSelectionEntries, no catalogueLinks reference to Chaos Space
  Marines at all). Same architecture as Death Guard: a full separate
  legion codex, NOT a thin overlay over a shared "Chaos Space Marines"
  army list -- confirmed per the standing rule established during Death
  Guard before assuming which migration shape applies.
- Old 10th Edition file used placeholder SKUs (43-70 through 43-86) that
  never actually existed as real products -- every row silently skipped,
  every time it ran. Rebuilt entirely from the live product catalog
  (99120102xxx / 99129915xxx GW SKUs).
- Every one of the 23 real BSData units already had an active UnitType
  row and product before this pass (created by an earlier, pre-11e-
  migration populate command) -- this is a pure refresh, no restructuring.
- 'Defiler' and 'Noise Marines' were already correctly set up as
  cross-faction shared-SKU links to Chaos Space Marines' own rows
  (P-CSM-DEFILER-2026, 99120102204) before this pass -- their new values
  match CSM's own already-refreshed rows for the same SKU.
- **Infractors** (85pts, Battleline) -- new unit, no product of its own.
  User directed linking it to the Tormentors SKU (99120102203) as a
  dual-build kit, same mechanism as every other multi-build split this
  project (Hastarii, Sydonian Dragoon, etc.). Confirmed 2026-08-07.
- **'Codex: Emperor's Children' (65-01) removed from the calculator**
  per explicit user instruction 2026-08-07 -- deactivated, not deleted
  (the Product/SKU itself is untouched).
- 'Combat Patrol: Emperor's Children' (99120102207) is a bundle SKU --
  left untouched, already correctly not a real unit (0pts, combo_box).
"""

from django.core.management.base import BaseCommand

from calculators.models import UnitType
from products.models import Faction, Product

# ---------------------------------------------------------------------------
# Rows removed from the calculator -- deactivated, not deleted.
# ---------------------------------------------------------------------------
EMPERORS_CHILDREN_DEACTIVATE = [
    "Codex: Emperor's Children",
]

# ---------------------------------------------------------------------------
# Unit data: (gw_sku, points_cost, category, name)
# ---------------------------------------------------------------------------
EMPERORS_CHILDREN_UNITS = [
    ('99120102052', 220, 'vehicle', 'Chaos Land Raider'),
    ('99120102092', 70, 'transport', 'Chaos Rhino'),
    ('99120201050', 70, 'monster', 'Chaos Spawn'),
    ('99120102097', 145, 'infantry', 'Chaos Terminators'),
    ('99129915036', 90, 'battleline', 'Daemonettes of Slaanesh'),
    ('99120201130', 170, 'character', 'Daemon Prince of Slaanesh'),
    ('99120201130', 205, 'character', 'Daemon Prince of Slaanesh with Wings'),
    ('P-CSM-DEFILER-2026', 300, 'vehicle', 'Defiler'),
    ('99129915052', 90, 'monster', 'Fiends'),
    ('99120102202', 95, 'infantry', 'Flawless Blades'),
    ('99120102200', 340, 'epic_hero', 'Fulgrim – Daemon Primarch of Slaanesh'),
    ('99120102090', 175, 'vehicle', 'Heldrake'),
    ('99120102203', 85, 'battleline', 'Infractors'),
    ('99129915056', 255, 'character', 'Keeper of Secrets'),
    ('99120102206', 80, 'character', 'Lord Exultant'),
    ('99120102205', 70, 'character', 'Lord Kakophonist'),
    ('99120102201', 120, 'epic_hero', 'Lucius the Eternal'),
    ('99120102089', 120, 'vehicle', 'Maulerfiend'),
    ('99120102204', 145, 'infantry', 'Noise Marines'),
    ('99129915005', 80, 'mounted', 'Seekers of Slaanesh'),
    ('99129915056', 315, 'epic_hero', 'Shalaxi Helbane'),
    ('99070102015', 55, 'character', 'Sorcerer'),
    ('99120102203', 80, 'battleline', 'Tormentors'),
]


class Command(BaseCommand):
    """
    Seed 11th Edition points, category, and active status for Emperor's
    Children units.

    Looks up each unit by (name, faction) and updates points_cost, category,
    and is_active in place; creates the row if it doesn't exist yet (linking
    the product by gw_sku when one is given). Idempotent -- safe to re-run.
    """

    help = "Seed 11th Edition points and categories for Emperor's Children units."

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
            "Seeding Emperor's Children points (11th Edition)" + (' [DRY RUN]' if dry_run else '') + '…\n'
        )

        fac = Faction.objects.filter(name="Emperor's Children").first()
        if not fac:
            self.stdout.write(self.style.ERROR(
                "Emperor's Children faction not found. Run populate_products first."
            ))
            return

        for name in EMPERORS_CHILDREN_DEACTIVATE:
            unit = UnitType.objects.filter(name=name, faction=fac).first()
            if unit and unit.is_active:
                self.stdout.write(f'  [deactivate] {name!r}')
                if not dry_run:
                    unit.is_active = False
                    unit.save(update_fields=['is_active'])

        updated_count = 0
        created_count = 0
        skipped_count = 0

        for gw_sku, points, category, label in EMPERORS_CHILDREN_UNITS:
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
