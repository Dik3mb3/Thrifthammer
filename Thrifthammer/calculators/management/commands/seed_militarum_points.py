"""
Management command: seed_militarum_points

Sets points_cost, category, and active status on UnitType records for all
Astra Militarum units, using official 11th Edition data sourced from the
BSData community BattleScribe project (github.com/BSData/wh40k-11e), the
same data New Recruit itself is built on.

Usage:
    python manage.py seed_militarum_points

The command is fully idempotent -- safe to re-run. It looks up each unit by
(name, faction) -- the same pair UnitType enforces uniqueness on.

Notes:
- Source files: "Imperium - Astra Militarum.json" (a thin entryLinks
  roster, no unit data of its own) resolved against "Imperium - Astra
  Militarum - Library.json" (the shared catalogue with the real costs/
  categories/profiles) -- same split-file pattern as Aeldari.
- This faction had only 7 active UnitType rows before this command (out of
  a 57-product catalog) -- the old 10th Edition file listed ~50 aspirational
  SKUs (47-32 through 47-89) that were never actually onboarded as real
  products, so most of it silently skipped every time it ran. This command
  replaces it entirely, matched against the DB's real product list (8
  legacy "47-xx" SKUs plus 49 "AM-xxx" SKUs).
- Several genuine multi-build kits share one SKU across multiple UnitType
  rows (same pattern used throughout the migration):
    * 47-12 "Sentinel": Scout Sentinels (55pts) / Armoured Sentinels (65pts)
    * AM-016 "Commissar Graves": mounted (125pts) / on Foot (65pts)
    * AM-037 "Ogryns": Ogryn Squad (60pts) / Ogryn Bodyguard (40pts)
    * AM-039 "Rogal Dorn Battle Tank": Battle Tank (260pts) / Commander
      (290pts)
    * 47-06 "Leman Russ Battle Tank" -- a genuine 8-way multi-build kit in
      11e: Battle Tank, Commander, Demolisher, Eradicator, Executioner,
      Exterminator, Punisher, Vanquisher, all sharing this one SKU.
- 3 units (Kasrkin, Ratlings, Tempestus Aquilons) link to real products
  that exist only as standalone "Kill Team: X" boxes tagged with no
  faction at all (KT-012/KT-019/KT-011) -- confirmed with user 2026-08-07
  that these are the correct, only retail source for these units.
- Units confirmed real in 11e with NO matching product anywhere in the
  catalog (Avenger Strike Fighter, Cadian Recon Squad, Centaur RSV, Cyclops
  Demolition Vehicle) are tracked in
  memory/project_11e_calculator_migration.md, not fabricated here.
"""

from django.core.management.base import BaseCommand

from calculators.models import UnitType
from products.models import Faction, Product

# ---------------------------------------------------------------------------
# Unit data: (gw_sku, points_cost, category, name)
#
# Sourced from BSData/wh40k-11e ("Imperium - Astra Militarum.json" roster,
# resolved against "Imperium - Astra Militarum - Library.json"), 11th
# Edition. Base points only, no wargear or squad-size modifiers.
# ---------------------------------------------------------------------------
MILITARUM_UNITS = [
    ('AM-001', 145, 'fortification', 'Aegis Defence Line'),
    ('47-12', 65, 'vehicle', 'Armoured Sentinels'),
    ('AM-003', 95, 'infantry', 'Artillery Team'),
    ('AM-004', 60, 'mounted', 'Attilan Rough Riders'),
    ('AM-005', 415, 'vehicle', 'Baneblade'),
    ('AM-006', 385, 'vehicle', 'Banehammer'),
    ('AM-007', 415, 'vehicle', 'Banesword'),
    ('47-17', 115, 'vehicle', 'Basilisk'),
    ('AM-008', 90, 'infantry', 'Bullgryn Squad'),
    ('AM-009', 55, 'character', 'Cadian Castellan'),
    ('AM-010', 60, 'character', 'Cadian Command Squad'),
    ('AM-024', 65, 'infantry', 'Cadian Heavy Weapons Squad'),
    ('47-30', 75, 'battleline', 'Cadian Shock Troops'),
    ('AM-012', 60, 'character', 'Catachan Command Squad'),
    ('AM-013', 65, 'infantry', 'Catachan Heavy Weapons Squad'),
    ('AM-014', 75, 'battleline', 'Catachan Jungle Fighters'),
    ('47-05', 75, 'transport', 'Chimera'),
    ('47-08', 30, 'character', 'Commissar'),
    ('AM-016', 125, 'epic_hero', 'Commissar Graves'),
    ('AM-016', 65, 'epic_hero', 'Commissar Graves on Foot'),
    ('AM-017', 120, 'epic_hero', 'Commissar Yarrick'),
    ('AM-018', 75, 'battleline', 'Death Korps of Krieg'),
    ('AM-019', 60, 'mounted', 'Death Riders'),
    ('AM-020', 125, 'vehicle', 'Deathstrike'),
    ('AM-021', 380, 'vehicle', 'Doomhammer'),
    ('AM-022', 90, 'infantry', 'Field Ordnance Battery'),
    ('AM-023', 95, 'epic_hero', 'Gaunt’s Ghosts'),
    ('AM-025', 385, 'vehicle', 'Hellhammer'),
    ('47-14', 125, 'vehicle', 'Hellhound'),
    ('AM-026', 90, 'vehicle', 'Hydra'),
    ('KT-012', 105, 'infantry', 'Kasrkin'),
    ('AM-027', 65, 'infantry', 'Krieg Combat Engineers'),
    ('AM-028', 60, 'character', 'Krieg Command Squad'),
    ('AM-029', 60, 'infantry', 'Krieg Heavy Weapons Squad'),
    ('47-06', 185, 'vehicle', 'Leman Russ Battle Tank'),
    ('47-06', 215, 'character', 'Leman Russ Commander'),
    ('47-06', 180, 'vehicle', 'Leman Russ Demolisher'),
    ('47-06', 170, 'vehicle', 'Leman Russ Eradicator'),
    ('47-06', 170, 'vehicle', 'Leman Russ Executioner'),
    ('47-06', 180, 'vehicle', 'Leman Russ Exterminator'),
    ('47-06', 150, 'vehicle', 'Leman Russ Punisher'),
    ('47-06', 150, 'vehicle', 'Leman Russ Vanquisher'),
    ('AM-031', 75, 'epic_hero', 'Lord Marshal Dreir'),
    ('AM-032', 130, 'epic_hero', 'Lord Solar Leontus'),
    ('AM-033', 150, 'vehicle', 'Manticore'),
    ('AM-034', 85, 'character', 'Militarum Tempestus Command Squad'),
    ('AM-035', 35, 'character', 'Ministorum Priest'),
    ('AM-036', 60, 'epic_hero', 'Nork Deddog'),
    ('AM-037', 40, 'character', 'Ogryn Bodyguard'),
    ('AM-037', 60, 'infantry', 'Ogryn Squad'),
    ('AM-038', 60, 'character', 'Primaris Psyker'),
    ('KT-019', 60, 'infantry', 'Ratlings'),
    ('AM-039', 260, 'vehicle', 'Rogal Dorn Battle Tank'),
    ('AM-039', 290, 'character', 'Rogal Dorn Commander'),
    ('47-12', 55, 'vehicle', 'Scout Sentinels'),
    ('AM-040', 375, 'vehicle', 'Shadowsword'),
    ('AM-041', 55, 'epic_hero', 'Sly Marbo'),
    ('AM-042', 395, 'vehicle', 'Stormlord'),
    ('AM-043', 430, 'vehicle', 'Stormsword'),
    ('AM-044', 65, 'transport', 'Taurox'),
    ('AM-045', 75, 'transport', 'Taurox Prime'),
    ('AM-046', 45, 'character', 'Tech-Priest Enginseer'),
    ('KT-011', 95, 'infantry', 'Tempestus Aquilons'),
    ('AM-047', 75, 'infantry', 'Tempestus Scions'),
    ('AM-030', 85, 'epic_hero', 'Ursula Creed'),
    ('AM-048', 170, 'vehicle', 'Valkyrie'),
    ('AM-049', 95, 'vehicle', 'Wyvern'),
]


class Command(BaseCommand):
    """
    Seed 11th Edition points, category, and active status for Astra
    Militarum units.

    Looks up each unit by (name, faction) and updates points_cost, category,
    and is_active in place; creates the row if it doesn't exist yet (linking
    the product by gw_sku when one is given). Idempotent -- safe to re-run.
    """

    help = 'Seed 11th Edition points and categories for Astra Militarum units.'

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
            'Seeding Astra Militarum points (11th Edition)' + (' [DRY RUN]' if dry_run else '') + '\u2026\n'
        )

        fac = Faction.objects.filter(name='Astra Militarum').first()
        if not fac:
            self.stdout.write(self.style.ERROR(
                'Astra Militarum faction not found. Run populate_products first.'
            ))
            return

        updated_count = 0
        created_count = 0
        skipped_count = 0

        for gw_sku, points, category, label in MILITARUM_UNITS:
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
