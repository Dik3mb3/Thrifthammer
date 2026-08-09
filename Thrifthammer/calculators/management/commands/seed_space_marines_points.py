"""
Management command: seed_space_marines_points

Sets points_cost, category, and active status on UnitType records for all
base Space Marines units, using official 11th Edition data sourced from the
BSData community BattleScribe project (github.com/BSData/wh40k-11e), the
same data New Recruit itself is built on.

Usage:
    python manage.py seed_space_marines_points

The command is fully idempotent -- safe to re-run. It looks up each unit by
(name, faction) -- the same pair UnitType enforces uniqueness on.

Notes:
- This is the base/parent faction that every Space Marine successor chapter
  (Ultramarines, Blood Angels, Dark Angels, Black Templars, Space Wolves,
  Deathwatch, Iron Hands, Salamanders, Imperial Fists, White Scars, Raven
  Guard) falls back to for any unit it doesn't override with its own
  chapter-specific row -- see calculators/views.py's parent_faction_id
  merge logic. Migrating this faction correctly is a prerequisite for every
  chapter, not just its own page. First created this session (2026-08-07)
  -- no prior seed_space_marines_points.py existed; the 75 pre-existing
  active rows had been created by populate_units/sync_unit_types, not a
  dedicated points command.
- No file existed to rebuild from -- built directly from the live DB (75
  active rows) merged against BSData.
- 'Firestrike Servo-Turrets' has no independent points value anywhere in
  BSData (`costs: null`), same situation as Aeldari's Starfangs -- 75pts
  here is a user-supplied value (confirmed 2026-08-07), not extracted.
- 'Land Speeder' (AGA-008) and 'Eradicator Squad with Heavy Bolters'
  (AGA-007) link to products tagged with an unusual pseudo-faction
  ("Warhammer 40K: Armageddon 11th Edition" -- an organizational tag for
  that boxed set's constituent SKUs, not a real army faction). Confirmed
  with user before linking (2026-08-07).
- 'Judiciar' and 'Suppressor Squad' are deliberately NOT created here even
  though BSData has real 11e data for both. They already exist as
  productless placeholder rows under some chapters (e.g. Black Templars),
  and the parent-faction fallback only dedupes rows that share the same
  `product_id` -- a productless base-faction row wouldn't merge with those
  existing rows, it would just show as a second, duplicate-looking entry
  on those chapters' pages. Confirmed with user to skip (2026-08-07).
- Other units confirmed real in 11e with no matching product anywhere in
  the catalog (Lieutenant in Phobos Armour, Lieutenant with Combi-weapon,
  Bladeguard Ancient, Astraeus, Thunderhawk Gunship) are tracked in
  memory/project_11e_calculator_migration.md, not fabricated here.
- 'Land Raider'/'Land Raider Crusader' (48-22) and 'Predator Annihilator'/
  'Predator Destructor' (48-23) were already correctly set up as
  shared-SKU dual-build pairs before this pass -- confirmed against
  BSData, no changes needed to that structure.
"""

from django.core.management.base import BaseCommand

from calculators.models import UnitType
from products.models import Faction, Product

# ---------------------------------------------------------------------------
# Unit data: (gw_sku, points_cost, category, name)
#
# Sourced from BSData/wh40k-11e ("Imperium - Space Marines.json"), 11th
# Edition. Base points only, no wargear or squad-size modifiers.
# ---------------------------------------------------------------------------
SPACE_MARINES_UNITS = [
    ('48-92', 80, 'infantry', 'Aggressor Squad'),
    ('48-34', 40, 'character', 'Ancient'),
    ('48-99', 65, 'character', 'Ancient in Terminator Armor'),
    ('48-33', 40, 'character', 'Apothecary'),
    ('48-33', 70, 'character', 'Apothecary Biologis'),
    ('48-76', 75, 'battleline', 'Assault Intercessor Squad'),
    ('48-100', 85, 'infantry', 'Assault Intercessors with Jump Packs'),
    ('48-46', 150, 'vehicle', 'Ballistus Dreadnought'),
    ('48-38', 80, 'infantry', 'Bladeguard Veteran Squad'),
    ('48-44', 150, 'vehicle', 'Brutalis Dreadnought'),
    ('48-106', 80, 'character', 'Captain'),
    ('48-101', 80, 'character', 'Captain in Gravis Armour'),
    ('48-102', 70, 'character', 'Captain in Phobos Armour'),
    ('48-103', 85, 'character', 'Captain in Terminator Armour'),
    ('48-105', 75, 'character', 'Captain with Jump Pack'),
    ('48-107', 150, 'infantry', 'Centurion Assault Squad'),
    ('48-108', 175, 'infantry', 'Centurion Devastator Squad'),
    ('48-32', 60, 'character', 'Chaplain'),
    ('HA-051', 75, 'character', 'Chaplain in Terminator Armour'),
    ('48-109', 70, 'character', 'Chaplain on Bike'),
    ('41-27', 75, 'character', 'Chaplain with Jump Pack'),
    ('48-37', 105, 'infantry', 'Company Heroes'),
    ('48-111', 180, 'infantry', 'Desolation Squad'),
    ('48-15', 120, 'infantry', 'Devastator Squad'),
    ('48-137', 135, 'vehicle', 'Dreadnought'),
    ('48-112', 60, 'transport', 'Drop Pod'),
    ('48-98', 75, 'infantry', 'Eliminator Squad'),
    ('48-39', 90, 'infantry', 'Eradicator Squad'),
    ('AGA-007', 80, 'infantry', 'Eradicator Squad with Heavy Bolters'),
    ('48-28', 75, 'vehicle', 'Firestrike Servo-Turrets'),
    ('48-113', 160, 'vehicle', 'Gladiator Lancer'),
    ('48-114', 160, 'vehicle', 'Gladiator Reaper'),
    ('48-115', 150, 'vehicle', 'Gladiator Valiant'),
    ('48-27', 175, 'fortification', 'Hammerfall Bunker'),
    ('48-116', 100, 'battleline', 'Heavy Intercessor Squad'),
    ('48-117', 110, 'infantry', 'Hellblaster Squad'),
    ('48-94', 70, 'transport', 'Impulsor'),
    ('48-97', 125, 'infantry', 'Inceptor Squad'),
    ('48-96', 85, 'infantry', 'Incursor Squad'),
    ('48-45', 85, 'infantry', 'Infernus Squad'),
    ('48-41', 110, 'infantry', 'Infiltrator Squad'),
    ('48-75', 80, 'battleline', 'Intercessor Squad'),
    ('48-42', 60, 'mounted', 'Invader ATV'),
    ('48-118', 125, 'vehicle', 'Invictor Tactical Warsuit'),
    ('48-22', 220, 'vehicle', 'Land Raider'),
    ('48-22', 220, 'vehicle', 'Land Raider Crusader'),
    ('48-119', 250, 'vehicle', 'Land Raider Redeemer'),
    ('AGA-008', 105, 'vehicle', 'Land Speeder'),
    ('48-30', 70, 'character', 'Librarian'),
    ('48-125', 70, 'character', 'Librarian in Phobos Armour'),
    ('41-28', 75, 'character', 'Librarian in Terminator Armour'),
    ('48-61', 45, 'character', 'Lieutenant'),
    ('48-121', 45, 'character', 'Lieutenant in Reiver Armour'),
    ('48-40', 70, 'mounted', 'Outrider Squad'),
    ('48-23', 135, 'vehicle', 'Predator Annihilator'),
    ('48-23', 140, 'vehicle', 'Predator Destructor'),
    ('48-126', 85, 'transport', 'Razorback'),
    ('48-93', 195, 'vehicle', 'Redemptor Dreadnought'),
    ('48-127', 75, 'infantry', 'Reiver Squad'),
    ('48-95', 170, 'vehicle', 'Repulsor'),
    ('48-95', 255, 'vehicle', 'Repulsor Executioner'),
    ('48-128', 65, 'transport', 'Rhino'),
    ('48-29', 65, 'infantry', 'Scout Squad'),
    ('48-43', 100, 'infantry', 'Sternguard Veteran Squad'),
    ('48-131', 105, 'vehicle', 'Storm Speeder Hailstrike'),
    ('48-132', 140, 'vehicle', 'Storm Speeder Hammerstrike'),
    ('48-133', 135, 'vehicle', 'Storm Speeder Thunderstrike'),
    ('48-129', 155, 'vehicle', 'Stormhawk Interceptor'),
    ('48-130', 280, 'vehicle', 'Stormraven Gunship'),
    ('48-134', 165, 'vehicle', 'Stormtalon Gunship'),
    ('48-07', 140, 'battleline', 'Tactical Squad'),
    ('48-135', 55, 'character', 'Techmarine'),
    ('48-136', 155, 'infantry', 'Terminator Assault Squad'),
    ('48-06', 160, 'infantry', 'Terminator Squad'),
    ('48-08', 105, 'infantry', 'Vanguard Veteran Squad with Jump Packs'),
    ('48-26', 185, 'vehicle', 'Vindicator'),
    ('48-25', 175, 'vehicle', 'Whirlwind'),
]


class Command(BaseCommand):
    """
    Seed 11th Edition points, category, and active status for base Space
    Marines units.

    Looks up each unit by (name, faction) and updates points_cost, category,
    and is_active in place; creates the row if it doesn't exist yet (linking
    the product by gw_sku when one is given). Idempotent -- safe to re-run.
    """

    help = 'Seed 11th Edition points and categories for base Space Marines units.'

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
            'Seeding Space Marines points (11th Edition)' + (' [DRY RUN]' if dry_run else '') + '\u2026\n'
        )

        fac = Faction.objects.filter(name='Space Marines').first()
        if not fac:
            self.stdout.write(self.style.ERROR(
                'Space Marines faction not found. Run populate_products first.'
            ))
            return

        updated_count = 0
        created_count = 0
        skipped_count = 0

        for gw_sku, points, category, label in SPACE_MARINES_UNITS:
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
