"""
Management command: seed_space_wolves_points

Sets points_cost, category, and active status on UnitType records for
Space Wolves units, using official 11th Edition data sourced from the
BSData community BattleScribe project (github.com/BSData/wh40k-11e), the
same data New Recruit itself is built on.

Usage:
    python manage.py seed_space_wolves_points
    python manage.py seed_space_wolves_points --dry-run

The command is fully idempotent -- safe to re-run. It looks up each unit by
(name, faction) -- the same pair UnitType enforces uniqueness on.

Notes:
- Same hybrid-catalogue pattern as every prior Space Marine successor
  chapter, but with an unusually large chapter-exclusive roster (22 real
  units, vs. 2-3 for most chapters) -- BSData's Space Wolves file defines
  its own points/rules for units that are conceptually the Space-Wolves-
  flavored version of what other chapters just inherit generically
  (Blood Claws, Grey Hunters, Wolf Guard Terminators, etc.). Everything
  else still falls back to the base Space Marines faction via the
  calculator's parent-faction fallback. Source: "Imperium - Space
  Wolves.json".
- 'Wolf Guard Headtakers' appears twice in the raw BSData file as two
  separate entries with identical name/points/category -- a source data
  duplication, not a meaningful distinction. Treated as one unit.
- **'Venerable Dreadnought' renamed** from 'Space Wolves Venerable
  Dreadnought' (BSData's literal name has no chapter prefix) and
  reactivated -- confirmed it's a real, distinct product (53-30), not
  the same physical kit as the generic 'Dreadnought' (48-137, unlike
  Blood Angels' cross-linked Librarian Dreadnought which does share the
  generic kit).
- **'Wolf Scouts'** (90pts, Infantry) links to `KT-026` ("Kill Team: Wolf
  Scouts"), a real product tagged faction=None -- same pattern as Astra
  Militarum's Kasrkin/Ratlings/Tempestus Aquilons cross-links to
  standalone Kill Team boxes.
- The 67 generic Space-Marine-squad rows this chapter had duplicated with
  no BSData Space-Wolves-specific override are deactivated here so they
  correctly fall back to the current base Space Marines rows for the same
  product. Verified before writing this command: all 67 share the exact
  same product_id as their base Space Marines counterpart -- zero shared-
  SKU conflicts. User confirmed 2026-08-08.
"""

from django.core.management.base import BaseCommand

from calculators.models import UnitType
from products.models import Faction, Product

# ---------------------------------------------------------------------------
# Renames applied first: (old_name, new_name)
# ---------------------------------------------------------------------------
SPACE_WOLVES_RENAMES = [
    ('Space Wolves Venerable Dreadnought', 'Venerable Dreadnought'),
]

# ---------------------------------------------------------------------------
# Generic Space-Marine-squad rows -- deactivated so they fall back to base
# Space Marines.
# ---------------------------------------------------------------------------
SPACE_WOLVES_DEACTIVATE = [
    'Ancient', 'Ancient in Terminator Armor', 'Assault Intercessors with Jump Packs',
    'Ballistus Dreadnought', 'Bladeguard Veteran Squad', 'Brutalis Dreadnought',
    'Captain', 'Captain in Gravis Armour', 'Captain in Phobos Armour',
    'Captain in Terminator Armour', 'Captain with Jump Pack',
    'Centurion Assault Squad', 'Centurion Devastator Squad', 'Chaplain',
    'Chaplain in Terminator Armour', 'Chaplain on Bike',
    'Chaplain with Jump Pack', 'Company Heroes', 'Desolation Squad',
    'Dreadnought', 'Drop Pod', 'Eliminator Squad', 'Firestrike Servo-Turrets',
    'Gladiator Lancer', 'Gladiator Reaper', 'Gladiator Valiant',
    'Hammerfall Bunker', 'Heavy Intercessor Squad', 'Hellblaster Squad',
    'Impulsor', 'Inceptor Squad', 'Incursor Squad', 'Infernus Squad',
    'Infiltrator Squad', 'Intercessor Squad', 'Invader ATV',
    'Invictor Tactical Warsuit', 'Land Raider', 'Land Raider Crusader',
    'Land Raider Redeemer', 'Librarian', 'Librarian in Phobos Armour',
    'Librarian in Terminator Armour', 'Lieutenant', 'Lieutenant in Reiver Armour',
    'Outrider Squad', 'Predator Annihilator', 'Predator Destructor',
    'Razorback', 'Redemptor Dreadnought', 'Reiver Squad', 'Repulsor',
    'Repulsor Executioner', 'Rhino', 'Scout Squad', 'Sternguard Veteran Squad',
    'Storm Speeder Hailstrike', 'Storm Speeder Hammerstrike',
    'Storm Speeder Thunderstrike', 'Stormhawk Interceptor',
    'Stormraven Gunship', 'Stormtalon Gunship', 'Techmarine',
    'Terminator Assault Squad', 'Vanguard Veteran Squad with Jump Packs',
    'Vindicator', 'Whirlwind',
]

# ---------------------------------------------------------------------------
# Unit data: (gw_sku, points_cost, category, name)
# ---------------------------------------------------------------------------
SPACE_WOLVES_UNITS = [
    ('53-21', 95, 'epic_hero', 'Arjac Rockfist'),
    ('53-22', 160, 'epic_hero', 'Bjorn the Fell-Handed'),
    ('53-23', 135, 'battleline', 'Blood Claws'),
    ('53-25', 45, 'monster', 'Fenrisian Wolves'),
    ('53-06', 165, 'battleline', 'Grey Hunters'),
    ('53-26', 50, 'character', 'Iron Priest'),
    ('53-27', 100, 'epic_hero', 'Logan Grimnar'),
    ('53-28', 150, 'epic_hero', 'Murderfang'),
    ('53-29', 75, 'epic_hero', 'Njal Stormcaller'),
    ('53-02', 90, 'epic_hero', 'Ragnar Blackmane'),
    ('53-10', 100, 'mounted', 'Thunderwolf Cavalry'),
    ('53-31', 70, 'epic_hero', 'Ulrik the Slayer'),
    ('53-30', 125, 'vehicle', 'Venerable Dreadnought'),
    ('53-32', 65, 'character', 'Wolf Guard Battle Leader'),
    ('53-33', 85, 'infantry', 'Wolf Guard Headtakers'),
    ('53-08', 150, 'infantry', 'Wolf Guard Terminators'),
    ('53-34', 70, 'character', 'Wolf Priest'),
    ('KT-026', 90, 'infantry', 'Wolf Scouts'),
    ('53-35', 85, 'infantry', 'Wulfen'),
    ('53-36', 135, 'vehicle', 'Wulfen Dreadnought'),
    ('53-35', 100, 'infantry', 'Wulfen with Storm Shields'),
]


class Command(BaseCommand):
    """
    Seed 11th Edition points, category, and active status for Space Wolves
    units.

    Looks up each unit by (name, faction) and updates points_cost, category,
    and is_active in place; creates the row if it doesn't exist yet (linking
    the product by gw_sku when one is given). Idempotent -- safe to re-run.
    """

    help = 'Seed 11th Edition points and categories for Space Wolves units.'

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
            'Seeding Space Wolves points (11th Edition)' + (' [DRY RUN]' if dry_run else '') + '…\n'
        )

        fac = Faction.objects.filter(name='Space Wolves').first()
        if not fac:
            self.stdout.write(self.style.ERROR(
                'Space Wolves faction not found. Run populate_products first.'
            ))
            return

        for old_name, new_name in SPACE_WOLVES_RENAMES:
            unit = UnitType.objects.filter(name=old_name, faction=fac).first()
            if unit:
                self.stdout.write(f'  [rename] {old_name!r} -> {new_name!r}')
                if not dry_run:
                    unit.name = new_name
                    unit.save(update_fields=['name'])

        for name in SPACE_WOLVES_DEACTIVATE:
            unit = UnitType.objects.filter(name=name, faction=fac).first()
            if unit and unit.is_active:
                self.stdout.write(f'  [deactivate] {name!r}')
                if not dry_run:
                    unit.is_active = False
                    unit.save(update_fields=['is_active'])

        updated_count = 0
        created_count = 0
        skipped_count = 0

        for gw_sku, points, category, label in SPACE_WOLVES_UNITS:
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
