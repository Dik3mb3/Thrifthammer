"""
Management command: seed_thousand_sons_points

Sets points_cost, category, and active status on UnitType records for
Thousand Sons units, using official 11th Edition data sourced from the
BSData community BattleScribe project (github.com/BSData/wh40k-11e), the
same data New Recruit itself is built on.

Usage:
    python manage.py seed_thousand_sons_points
    python manage.py seed_thousand_sons_points --dry-run

The command is fully idempotent -- safe to re-run. It looks up each unit by
(name, faction) -- the same pair UnitType enforces uniqueness on.

Notes:
- Source: "Chaos - Thousand Sons.json" -- self-contained (70 own
  sharedSelectionEntries, zero catalogueLinks reference to the CSM
  catalogue). Same architecture as Death Guard/Emperor's Children: a full
  separate legion codex with its own points AND rules for shared-name
  units (Predator, Rhino, Land Raider, etc.), not a thin overlay -- per
  the standing rule established during Death Guard. 35 real 11e units.
- Supersedes the old `seed_thousand_sons_points` command (10th Edition,
  never added to the Procfile).
- 32 of 35 units already had an active UnitType row and product from an
  earlier, pre-11e-migration populate command -- mostly a refresh pass.
- **Exalted Sorcerer 2-way multi-build split** (`43-38`): the existing
  row "Thousand Sons Exalted Sorcerers" (80pts) is renamed to "Exalted
  Sorcerer" (90pts) to match its new sibling "Exalted Sorcerer on Disc
  of Tzeentch" (90pts, new row, same SKU).
- **Tzaangor Enlightened 2-way multi-build split** (`P-TZAANGOR-ENL`):
  the existing row was mislabeled at 55pts (actually the "with Fatecaster
  greatbows" build's points) -- corrected to the base build's real 50pts,
  with "Tzaangor Enlightened with Fatecaster greatbows" (55pts) added as
  a new sibling row on the same SKU.
- **Chaos Spawn (Flesh Change)** -- a second BSData entry with the same
  65pts/Beast stats as plain Chaos Spawn but an added Lone Operative
  rule. User declined to add it as a second row (2026-08-09) -- only
  plain "Chaos Spawn" is seeded.
- Several category corrections followed faithfully per BSData's own
  primary categoryLink even where it doesn't match in-game intuition --
  e.g. Chaos Land Raider is tagged primary=Vehicle in BSData (Transport
  is a secondary keyword only), so it maps to our `vehicle` category,
  not `transport`.
- **Sorcerer** (85pts) and **Sorcerer in Terminator Armour** (95pts) --
  a separate, lower-tier HQ kit from Exalted Sorcerer. No product exists
  for either build in the catalog -- backlogged, not linked to anything.
- Cross-faction shared-SKU products (Chaos Land Raider, Chaos Predator
  Annihilator/Destructor, Chaos Rhino, Chaos Vindicator, Defiler,
  Forgefiend/Maulerfiend dual-kit, Helbrute) were already correctly
  linked from earlier CSM-family migrations -- this pass only refreshes
  their Thousand-Sons-specific points/category values, no relinking
  needed.
"""

from django.core.management.base import BaseCommand

from calculators.models import UnitType
from products.models import Faction, Product

# Old DB name -> new BSData-aligned name.
THOUSAND_SONS_RENAMES = [
    ('Thousand Sons Exalted Sorcerers', 'Exalted Sorcerer'),
]

# ---------------------------------------------------------------------------
# Unit data: (gw_sku, points_cost, category, name)
# ---------------------------------------------------------------------------
THOUSAND_SONS_UNITS = [
    ('43-30', 100, 'epic_hero', 'Thousand Sons Ahriman'),
    ('P-TZEENTCH-BLUEHORRORS', 90, 'battleline', 'Blue Horrors and Brimstone Horrors'),
    ('99120102052', 220, 'vehicle', 'Chaos Land Raider'),
    ('43-09', 140, 'vehicle', 'Chaos Predator Annihilator'),
    ('43-09', 140, 'vehicle', 'Chaos Predator Destructor'),
    ('99120102092', 80, 'transport', 'Chaos Rhino'),
    ('99120201050', 65, 'monster', 'Chaos Spawn'),
    ('P-CSM-VINDICATOR', 185, 'vehicle', 'Chaos Vindicator'),
    ('99120201130', 170, 'character', 'Daemon Prince of Tzeentch'),
    ('99120201130', 170, 'character', 'Daemon Prince of Tzeentch with wings'),
    ('P-CSM-DEFILER-2026', 300, 'vehicle', 'Defiler'),
    ('43-38', 90, 'character', 'Exalted Sorcerer'),
    ('43-38', 90, 'character', 'Exalted Sorcerer on Disc of Tzeentch'),
    ('P-TZEENTCH-FLAMERS', 65, 'infantry', 'Flamers of Tzeentch'),
    ('99120102089', 135, 'vehicle', 'Forgefiend'),
    ('prod2430129-99120102043', 110, 'vehicle', 'Helbrute'),
    ('99120102090', 175, 'vehicle', 'Heldrake'),
    ('43-79', 95, 'character', 'Thousand Sons Infernal Master'),
    ('P-TZEENTCH-KAIROS', 305, 'epic_hero', 'Kairos Fateweaver'),
    ('P-TZEENTCH-LOC', 320, 'character', 'Lord of Change'),
    ('43-02', 455, 'epic_hero', 'Thousand Sons Magnus the Red'),
    ('99120102089', 120, 'vehicle', 'Maulerfiend'),
    ('P-MUTALITH-VB', 170, 'monster', 'Mutalith Vortex Beast'),
    ('P-PINK-HORRORS-40K', 115, 'battleline', 'Pink Horrors of Tzeentch'),
    ('43-35', 100, 'battleline', 'Thousand Sons Rubric Marines'),
    ('43-36', 180, 'infantry', 'Thousand Sons Scarab Occult Terminators'),
    ('P-TZEENTCH-SCREAMERS', 80, 'monster', 'Screamers of Tzeentch'),
    ('P-TS-SEKHETAR-2025', 85, 'vehicle', 'Thousand Sons Sekhetar Robots'),
    ('P-TZAANGOR-ENL', 50, 'mounted', 'Tzaangor Enlightened'),
    ('P-TZAANGOR-ENL', 55, 'mounted', 'Tzaangor Enlightened with Fatecaster greatbows'),
    ('P-TZAANGOR-SHAMAN', 65, 'character', 'Tzaangor Shaman'),
    ('P-TZAANGORS-40K', 75, 'infantry', 'Thousand Sons Tzaangors'),
]


class Command(BaseCommand):
    """
    Seed 11th Edition points, category, and active status for Thousand Sons
    units.

    Renames pre-existing rows first (THOUSAND_SONS_RENAMES), then looks up
    each unit by (name, faction) and updates points_cost, category, and
    is_active in place; creates the row if it doesn't exist yet (linking
    the product by gw_sku). Idempotent -- safe to re-run.
    """

    help = 'Seed 11th Edition points and categories for Thousand Sons units.'

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
            'Seeding Thousand Sons points (11th Edition)' + (' [DRY RUN]' if dry_run else '') + '…\n'
        )

        fac = Faction.objects.filter(name='Thousand Sons').first()
        if not fac:
            self.stdout.write(self.style.ERROR(
                'Thousand Sons faction not found. Run populate_products first.'
            ))
            return

        for old_name, new_name in THOUSAND_SONS_RENAMES:
            unit = UnitType.objects.filter(name=old_name, faction=fac).first()
            if unit:
                self.stdout.write(f'  [rename] {old_name!r} -> {new_name!r}')
                if not dry_run:
                    unit.name = new_name
                    unit.save(update_fields=['name'])

        updated_count = 0
        created_count = 0
        skipped_count = 0

        for gw_sku, points, category, label in THOUSAND_SONS_UNITS:
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
