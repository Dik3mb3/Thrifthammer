"""
Management command: seed_sisters_of_battle_points

Sets points_cost, category, and active status on UnitType records for
Sisters of Battle units, using official 11th Edition data sourced from
the BSData community BattleScribe project (github.com/BSData/wh40k-11e),
the same data New Recruit itself is built on.

Usage:
    python manage.py seed_sisters_of_battle_points
    python manage.py seed_sisters_of_battle_points --dry-run

The command is fully idempotent -- safe to re-run. It looks up each unit by
(name, faction) -- the same pair UnitType enforces uniqueness on.

Notes:
- Source: "Imperium - Adepta Sororitas.json" -- self-contained (70 own
  sharedSelectionEntries, 42/44 entryLinks resolve against its own
  entries). 33 real 11e units.
- Superseded the older `seed_sisters_points` command (different command
  name, still present, not deleted) -- that file used a mix of real and
  stale/placeholder SKUs under 10th Edition values and was never rebuilt
  for 11e.
- Only 7 UnitType rows existed before this pass (Battle Sisters Squad,
  Celestian Sacresants, Exorcist, Immolator, Morvenn Vahl, Retributor
  Squad, Seraphim Squad) despite a rich 30-product AS-xxx line already in
  the catalog -- the other 26 units are fresh creates, all cleanly
  resolved to already-existing products. No backlog items this faction.
- 'Codex: Adepta Sororitas' (AS-004) and 'Armageddon Battalion: Adepta
  Sororitas' (AS-001) are book/bundle SKUs -- no unit created for either;
  neither ever had a UnitType row, so there's nothing to deactivate.
- 'Ministorum Priest with Vindictor' (AS-026) and 'Sister Superior Amalia
  Novena' (AS-030) are real, active products with no entry anywhere in
  the current 11e BSData file at all, not even Legends-tagged -- left
  untouched (no UnitType row exists for either), same precedent as Dark
  Angels' Interrogator-Chaplain/Ravenwing Bike Squadron.
- 'Sanctifiers' links to AS-005 ("Kill Team: Sanctifiers", the Sisters-
  of-Battle-tagged product) -- same product already cross-linked from
  Agents of the Imperium's own migration pass.
"""

from django.core.management.base import BaseCommand

from calculators.models import UnitType
from products.models import Faction, Product

# ---------------------------------------------------------------------------
# Unit data: (gw_sku, points_cost, category, name)
# ---------------------------------------------------------------------------
SISTERS_OF_BATTLE_UNITS = [
    ('AS-006', 80, 'epic_hero', 'Aestred Thurga and Agathae Dolan'),
    ('AS-017', 50, 'infantry', 'Arco-Flagellants'),
    ('52-20', 100, 'battleline', 'Battle Sisters Squad'),
    ('AS-014', 60, 'character', 'Canoness'),
    ('AS-024', 75, 'character', 'Canoness with Jump Pack'),
    ('AS-007', 165, 'vehicle', 'Castigator'),
    ('AS-002', 120, 'infantry', 'Celestian Insidiants'),
    ('52-22', 75, 'infantry', 'Celestian Sacresants'),
    ('AS-010', 85, 'epic_hero', 'Daemonifuge'),
    ('AS-015', 40, 'character', 'Dialogus'),
    ('AS-027', 45, 'character', 'Dogmata'),
    ('AS-022', 90, 'infantry', 'Dominion Squad'),
    ('52-08', 180, 'vehicle', 'Exorcist'),
    ('AS-019', 65, 'character', 'Hospitaller'),
    ('AS-016', 55, 'character', 'Imagifier'),
    ('52-09', 100, 'transport', 'Immolator'),
    ('AS-003', 135, 'epic_hero', 'Intranzia Fraye'),
    ('AS-018', 105, 'epic_hero', 'Junith Eruita'),
    ('AS-025', 50, 'character', 'Ministorum Priest'),
    ('AS-028', 70, 'vehicle', 'Mortifiers'),
    ('52-02', 200, 'epic_hero', 'Morvenn Vahl'),
    ('AS-009', 50, 'character', 'Palatine'),
    ('AS-008', 180, 'vehicle', 'Paragon Warsuits'),
    ('AS-029', 70, 'vehicle', 'Penitent Engines'),
    ('AS-013', 70, 'infantry', 'Repentia Squad'),
    ('52-15', 105, 'infantry', 'Retributor Squad'),
    ('AS-021', 150, 'epic_hero', 'Saint Celestine'),
    ('AS-005', 110, 'infantry', 'Sanctifiers'),
    ('52-12', 75, 'infantry', 'Seraphim Squad'),
    ('AS-023', 90, 'infantry', 'Sisters Novitiate Squad'),
    ('AS-012', 65, 'transport', 'Sororitas Rhino'),
    ('AS-020', 245, 'epic_hero', 'Triumph of Saint Katherine'),
    ('AS-011', 75, 'infantry', 'Zephyrim Squad'),
]


class Command(BaseCommand):
    """
    Seed 11th Edition points, category, and active status for Sisters of
    Battle units.

    Looks up each unit by (name, faction) and updates points_cost, category,
    and is_active in place; creates the row if it doesn't exist yet (linking
    the product by gw_sku when one is given). Idempotent -- safe to re-run.
    """

    help = 'Seed 11th Edition points and categories for Sisters of Battle units.'

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
            'Seeding Sisters of Battle points (11th Edition)' + (' [DRY RUN]' if dry_run else '') + '…\n'
        )

        fac = Faction.objects.filter(name='Sisters of Battle').first()
        if not fac:
            self.stdout.write(self.style.ERROR(
                'Sisters of Battle faction not found. Run populate_products first.'
            ))
            return

        updated_count = 0
        created_count = 0
        skipped_count = 0

        for gw_sku, points, category, label in SISTERS_OF_BATTLE_UNITS:
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
