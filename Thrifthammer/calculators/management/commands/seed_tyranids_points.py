"""
Management command: seed_tyranids_points

Sets points_cost, category, and active status on UnitType records for
Tyranids units, using official 11th Edition data sourced from the BSData
community BattleScribe project (github.com/BSData/wh40k-11e), the same
data New Recruit itself is built on.

Usage:
    python manage.py seed_tyranids_points
    python manage.py seed_tyranids_points --dry-run

The command is fully idempotent -- safe to re-run. It looks up each unit by
(name, faction) -- the same pair UnitType enforces uniqueness on.

Notes:
- Source: "Tyranids.json" -- a thin roster (66 root-level entryLinks),
  same split-roster+library pattern as Aeldari/Drukhari/Imperial Knights.
  45 of the 66 root entries resolve against the file's own 61
  sharedSelectionEntries; the other 21 (Lictor, Trygon, Mawloc,
  Deathleaper, Raveners, Winged Hive Tyrant, Winged Tyranid Prime,
  Gargoyles, Von Ryan's Leapers, Ripper Swarms, Parasite of Mortrex,
  Tyrannocyte, Neurolictor, Hyperadapted Raveners, The Red Terror, plus
  BattleScribe meta/Crucible entries) resolve against the separate
  "Library - Tyranids.json" catalogue. 50 real 11e units total (35 from
  the main file + 15 real, priced, non-Legends/non-Crucible units from
  the library).
- Supersedes the old `seed_tyranids_points` command (10th Edition, never
  added to the Procfile).
- Only 5 UnitType rows existed before this pass despite a rich
  48-product line already in the catalog (`51-xx` legacy SKUs + `TY-xxx`)
  -- most of the roster was a fresh create, not a refresh.
- **Tyranid Warriors 2-way multi-build split** (`51-08`): "with Ranged
  Bio-Weapons" (60pts) / "with Melee Bio-Weapons" (75pts).
- **Tyranid Prime 2-way multi-build split** (`TY-036`/`TY-037`, same
  $43.50 MSRP): `TY-037` "Tyranid Prime with Lash Whip" -> "Tyranid
  Prime with Lash Whip" (75pts); `TY-036` "Tyranid Prime" (plain name,
  kept as display name) -> "Winged Tyranid Prime" (65pts). User
  confirmed 2026-08-09.
- **Carnifex/Screamer-Killer**: only one priced Carnifex-chassis generic
  unit exists in BSData ("Screamer-killer", 125pts, Monster) -- no plain
  "Carnifex" entry at all. Two products compete for it: `51-06` "Tyranid
  Carnifex" ($45 MSRP) and `TY-027` "Screamer-Killer Brood" ($106 MSRP).
  User chose to link `51-06` (2026-08-09); `TY-027` is left unlinked --
  a real, active product with no current-edition UnitType row, same
  precedent as Dark Angels' Interrogator-Chaplain / Sisters' Ministorum
  Priest with Vindictor.
- **`TY-014` "Tyranid Horrors of the Hive"** ($114 MSRP) does not match
  any single BSData unit name -- treated as a themed multi-model bundle,
  same as Combat Patrol boxes. No UnitType row.
- **Neurotyrant** (130pts, Character) -- confirmed real unit, but no
  product exists anywhere in the catalog (the `TY-012` SKU slot is
  genuinely empty, not just inactive). Backlogged.
- 5 units confirmed real in 11e with no product anywhere: Spore Mines
  (55pts, Beast), Ripper Swarms (30pts, Swarm), Hyperadapted Raveners
  (165pts, Character), The Red Terror (130pts, Epic Hero), Neurotyrant
  (130pts, Character). User confirmed backlog for all 5 (2026-08-09).
- **Deactivated**: the old unified "Tyranid Warriors" row (65pts,
  `51-08`) is superseded by the Ranged/Melee Bio-Weapons split above and
  would otherwise sit active and stale on the same SKU as its two new
  successors. User confirmed deactivation 2026-08-09.
"""

from django.core.management.base import BaseCommand

from calculators.models import UnitType
from products.models import Faction, Product

# Names to deactivate -- superseded by a multi-build split.
TYRANIDS_DEACTIVATE = ['Tyranid Warriors']

# ---------------------------------------------------------------------------
# Unit data: (gw_sku, points_cost, category, name)
# ---------------------------------------------------------------------------
TYRANIDS_UNITS = [
    ('TY-001', 55, 'infantry', 'Tyranid Barbgaunts'),
    ('TY-002', 60, 'infantry', 'Tyranid Biovore'),
    ('TY-003', 80, 'character', 'Tyranid Broodlord'),
    ('TY-005', 80, 'epic_hero', 'Tyranid Deathleaper'),
    ('TY-006', 140, 'monster', 'Tyranid Exocrine'),
    ('TY-007', 80, 'battleline', 'Tyranid Gargoyle Brood'),
    ('TY-008', 75, 'infantry', 'Tyranid Genestealers'),
    ('TY-009', 125, 'monster', 'Tyranid Haruspex'),
    ('TY-010', 170, 'monster', 'Tyranid Hive Crone'),
    ('TY-011', 80, 'infantry', 'Tyranid Hive Guard'),
    ('51-04', 195, 'character', 'Tyranid Hive Tyrant'),
    ('TY-013', 70, 'battleline', 'Tyranid Hormagaunts'),
    ('TY-015', 125, 'infantry', 'Tyranid Raveners'),
    ('TY-016', 60, 'infantry', 'Tyranid Lictor'),
    ('TY-017', 190, 'monster', 'Tyranid Maleceptor'),
    ('TY-018', 135, 'monster', 'Tyranid Mawloc'),
    ('TY-019', 45, 'infantry', 'Tyranid Neurogaunts'),
    ('TY-020', 80, 'infantry', 'Tyranid Neurolictor'),
    ('TY-021', 250, 'monster', 'Tyranid Norn Assimilator'),
    ('TY-022', 250, 'monster', 'Tyranid Norn Emissary'),
    ('TY-023', 140, 'epic_hero', "Tyranid Old One Eye's Carnifex Brood"),
    ('TY-024', 70, 'character', 'Tyranid Parasite of Mortrex'),
    ('TY-025', 110, 'monster', 'Tyranid Psychophage'),
    ('TY-026', 45, 'infantry', 'Tyranid Pyrovore'),
    ('51-06', 125, 'monster', 'Tyranid Carnifex'),
    ('TY-028', 145, 'monster', 'Tyranid Sporocyst and Mucolid Spore'),
    ('TY-029', 160, 'character', 'Tyranid Tervigon'),
    ('TY-030', 210, 'epic_hero', 'Tyranid The Swarmlord'),
    ('TY-031', 120, 'monster', 'Tyranid Toxicrene'),
    ('TY-032', 140, 'monster', 'Tyranid Trygon'),
    ('TY-033', 185, 'monster', 'Tyranid Harpy'),
    ('TY-034', 610, 'monster', 'Tyranid Harridan'),
    ('TY-035', 810, 'monster', 'Tyranid Hierophant Bio-Titan'),
    ('TY-036', 65, 'character', 'Winged Tyranid Prime'),
    ('TY-037', 75, 'character', 'Tyranid Prime with Lash Whip'),
    ('TY-038', 80, 'transport', 'Tyranid Tyrannocyte'),
    ('TY-039', 180, 'monster', 'Tyranid Tyrannofex'),
    ('TY-040', 80, 'infantry', 'Tyranid Tyrant Guard'),
    ('TY-041', 55, 'infantry', 'Tyranid Venomthropes'),
    ('TY-042', 55, 'infantry', "Tyranid Von Ryan's Leapers"),
    ('TY-043', 185, 'character', 'Tyranid Winged Hive Tyrant'),
    ('TY-044', 90, 'infantry', 'Tyranid Zoanthropes'),
    ('51-16', 60, 'battleline', 'Tyranid Termagants'),
    ('51-08', 60, 'infantry', 'Tyranid Warriors with Ranged Bio-Weapons'),
    ('51-08', 75, 'infantry', 'Tyranid Warriors with Melee Bio-Weapons'),
]


class Command(BaseCommand):
    """
    Seed 11th Edition points, category, and active status for Tyranids
    units.

    Looks up each unit by (name, faction) and updates points_cost, category,
    and is_active in place; creates the row if it doesn't exist yet (linking
    the product by gw_sku when one is given). Idempotent -- safe to re-run.
    """

    help = 'Seed 11th Edition points and categories for Tyranids units.'

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
            'Seeding Tyranids points (11th Edition)' + (' [DRY RUN]' if dry_run else '') + '…\n'
        )

        fac = Faction.objects.filter(name='Tyranids').first()
        if not fac:
            self.stdout.write(self.style.ERROR(
                'Tyranids faction not found. Run populate_products first.'
            ))
            return

        for name in TYRANIDS_DEACTIVATE:
            unit = UnitType.objects.filter(name=name, faction=fac, is_active=True).first()
            if unit:
                self.stdout.write(f'  [deactivate] {name!r}')
                if not dry_run:
                    unit.is_active = False
                    unit.save(update_fields=['is_active'])

        updated_count = 0
        created_count = 0
        skipped_count = 0

        for gw_sku, points, category, label in TYRANIDS_UNITS:
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
