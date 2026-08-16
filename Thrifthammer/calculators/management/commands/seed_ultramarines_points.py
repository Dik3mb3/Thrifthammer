"""
Management command: seed_ultramarines_points

Sets points_cost, category, and active status on UnitType records for
Ultramarines units, using official 11th Edition data sourced from the
BSData community BattleScribe project (github.com/BSData/wh40k-11e), the
same data New Recruit itself is built on.

Usage:
    python manage.py seed_ultramarines_points
    python manage.py seed_ultramarines_points --dry-run

The command is fully idempotent -- safe to re-run. It looks up each unit by
(name, faction) -- the same pair UnitType enforces uniqueness on.

Notes:
- Source: "Imperium - Adeptus Astartes - Ultramarines.json" -- hybrid
  chapter-catalogue pattern, same shape as every other SM successor
  chapter (18 own entries, all 16 root entryLinks resolve locally).
  Supersedes the old `seed_ultramarines_points` command (10th Edition,
  never added to the Procfile).
- **New gotcha**: two entries carry a `"HIDDEN UNTIL LEGENDS"` comment
  even though their name isn't yet suffixed `[Legends]` -- "Captain
  Sicarius" (85pts) and plain "Marneus Calgar" (200pts). Both are being
  phased out of standard play; excluded same as any other Legends unit.
  Their current replacements are "Cato Sicarius" (105pts) and "Marneus
  Calgar in Armour of Antilochus" (155pts).
- **Captain Titus 3-way multi-build split** (`55-31`, "Captain Titus and
  The Wardens of Ultramar" -- the existing combined-name row is
  deactivated and replaced with three sibling rows on the same SKU):
  "Captain Titus" (100pts), "Wardens of Ultramar" (120pts), and
  "Lieutenant Titus" (70pts, an earlier-rank build of the same
  character) -- confirmed with user 2026-08-09 that the box includes all
  three build options.
- **Roboute Guilliman / Marneus Calgar -- productless placeholder rows**,
  same precedent as Judiciar/Suppressor Squad elsewhere: no product
  exists anywhere in the catalog for either character. Two pre-existing
  duplicate rows for Guilliman ("Roboute Guilliman" 0pts, "Space Marine
  Roboute Guilliman" 340pts) are consolidated -- keep "Roboute Guilliman"
  refreshed to 355pts, deactivate the duplicate. The pre-existing stale
  "Marneus Calgar" row (140pts, corresponding to the now Legends-bound
  plain entry) is deactivated the same way in favor of "Marneus Calgar
  in Armour of Antilochus" (155pts) -- same reasoning as the Guilliman
  cleanup the user approved, applied consistently.
- **Uriel Ventris** (105pts, Epic Hero) confirmed real, no product
  anywhere -- backlogged.
- "Ultramarines Upgrades and Transfers" (`55-34`) is a transfer-sheet
  accessory product, not a deployable unit -- left untouched, same
  precedent as Tzaangor Upgrade Pack.
"""

from django.core.management.base import BaseCommand

from calculators.models import UnitType
from products.models import Faction, Product

# Names to deactivate -- superseded by a multi-build split or a
# stale/Legends-bound duplicate.
ULTRAMARINES_DEACTIVATE = [
    'Captain Titus and The Wardens of Ultramar',
    'Marneus Calgar',
    'Space Marine Roboute Guilliman',
]

# ---------------------------------------------------------------------------
# Unit data: (gw_sku, points_cost, category, name)
# gw_sku=None means no product exists -- productless placeholder row.
# ---------------------------------------------------------------------------
ULTRAMARINES_UNITS = [
    ('55-32', 105, 'epic_hero', 'Cato Sicarius'),
    ('55-33', 85, 'character', 'Chief Librarian Tigurius'),
    (None, 155, 'epic_hero', 'Marneus Calgar in Armour of Antilochus'),
    (None, 355, 'epic_hero', 'Roboute Guilliman'),
    ('55-31', 100, 'epic_hero', 'Captain Titus'),
    ('55-31', 120, 'epic_hero', 'Wardens of Ultramar'),
    ('55-31', 70, 'epic_hero', 'Lieutenant Titus'),
    ('55-35', 110, 'infantry', 'Victrix Honour Guard'),
]


class Command(BaseCommand):
    """
    Seed 11th Edition points, category, and active status for Ultramarines
    units.

    Looks up each unit by (name, faction) and updates points_cost, category,
    and is_active in place; creates the row if it doesn't exist yet (linking
    the product by gw_sku when one is given). Idempotent -- safe to re-run.
    """

    help = 'Seed 11th Edition points and categories for Ultramarines units.'

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
            'Seeding Ultramarines points (11th Edition)' + (' [DRY RUN]' if dry_run else '') + '…\n'
        )

        fac = Faction.objects.filter(name='Ultramarines').first()
        if not fac:
            self.stdout.write(self.style.ERROR(
                'Ultramarines faction not found. Run populate_products first.'
            ))
            return

        for name in ULTRAMARINES_DEACTIVATE:
            unit = UnitType.objects.filter(name=name, faction=fac, is_active=True).first()
            if unit:
                self.stdout.write(f'  [deactivate] {name!r}')
                if not dry_run:
                    unit.is_active = False
                    unit.save(update_fields=['is_active'])

        updated_count = 0
        created_count = 0
        skipped_count = 0

        for gw_sku, points, category, label in ULTRAMARINES_UNITS:
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
