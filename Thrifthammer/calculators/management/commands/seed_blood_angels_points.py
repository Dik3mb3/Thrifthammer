"""
Management command: seed_blood_angels_points

Sets points_cost, category, and active status on UnitType records for
Blood Angels units, using official 11th Edition data sourced from the
BSData community BattleScribe project (github.com/BSData/wh40k-11e), the
same data New Recruit itself is built on.

Usage:
    python manage.py seed_blood_angels_points

The command is fully idempotent -- safe to re-run. It looks up each unit by
(name, faction) -- the same pair UnitType enforces uniqueness on.

Notes:
- BSData's Blood Angels catalogue ("Imperium - Blood Angels.json") only
  defines 16 BA-exclusive units directly, same hybrid pattern as Black
  Templars. Everything else falls back to the base Space Marines faction's
  now-current data via the calculator's parent-faction fallback
  (calculators/views.py). "Deactivate" below means only UnitType.is_active
  on the calculator's own model -- it never touches Product.is_active, the
  browse pages, or anything else about the SKU. Confirmed with user
  2026-08-07 that deactivating a BA-specific duplicate row does NOT remove
  that unit from the Blood Angels calculator: the page falls back to the
  (now-current) Space Marines row for the same product instead, so
  coverage is preserved, only the redundant duplicate is removed.
- Renames (old DB name -> real BSData name):
    ('Blood Angels Librarian Dreadnought', 'Librarian Dreadnought'),
- 'Dreadnought' (48-137) is deliberately kept as an active BA-specific row
  (not deactivated with the other generic duplicates) so it can coexist
  with the new 'Librarian Dreadnought' row below on the same SKU --
  deactivating it would have let the sub-faction 'Librarian Dreadnought'
  row's product-based dedup silently hide the plain Dreadnought option
  from Blood Angels' page entirely (a sub-faction row claiming a product
  suppresses the parent-faction fallback for that same product).
- 'Librarian Dreadnought' -- BSData's only 11e entry is
  "Librarian Dreadnought [Legends]" (170pts), not standard matched play.
  User explicitly directed linking it to the Venerable Dreadnought product
  (48-137) anyway rather than leaving it inactive (2026-08-07) -- an
  intentional, one-off exception to the standard Legends-exclusion rule,
  not a general policy change.
- 'Judiciar' and 'Suppressor Squad' were inactive under Blood Angels with
  no product (unlike Black Templars, where they were already active).
  Reactivated here with the same values used for Black Templars' identical
  productless placeholder rows, per the user's own stated principle that
  any unit legal for the faction should appear in the calculator.
- 6 units confirmed real in 11e with no product anywhere (Death Company
  Marines, Death Company Captain, Death Company Captain with Jump Pack,
  Death Company Dreadnought, Death Company Intercessors, Death Company
  Marines with Bolt Rifles, Death Company Marines with Jump Packs) are
  tracked in memory/project_11e_calculator_migration.md, not created here
  -- including 'Death Company Marines' itself, even though an inactive
  productless placeholder for it already exists in the DB (left untouched
  per user direction 2026-08-07, not reactivated).
- '_stale_926' (product 48-120, a duplicate of the already-correctly-linked
  'Librarian in Terminator Armour' row on 41-28) is already inactive --
  left as-is, no action needed. Not deleted -- the underlying Product
  record is untouched regardless, per standing policy against deleting
  SKUs without explicit permission.
- The ~70 generic Space-Marine-squad rows this chapter had duplicated with
  no BSData Blood-Angels-specific override are deactivated here so they
  correctly fall back to the now-current base Space Marines rows for the
  same product, same reasoning as Black Templars. Confirmed with user
  2026-08-07 after clarifying exactly what "deactivate" affects.
"""

from django.core.management.base import BaseCommand

from calculators.models import UnitType
from products.models import Faction, Product

# ---------------------------------------------------------------------------
# Renames applied first: (old_name, new_name)
# ---------------------------------------------------------------------------
BLOOD_ANGELS_RENAMES = [
    ('Blood Angels Librarian Dreadnought', 'Librarian Dreadnought'),
]

# ---------------------------------------------------------------------------
# Bundle/book rows + generic Space-Marine-squad duplicates -- deactivated.
# ---------------------------------------------------------------------------
BLOOD_ANGELS_DEACTIVATE = [
    'Blood Angels Combat Patrol',
    'Codex Supplement: Blood Angels',
    'Ancient',
    'Ancient in Terminator Armor',
    'Apothecary',
    'Assault Intercessors with Jump Packs',
    'Ballistus Dreadnought',
    'Bladeguard Veteran Squad',
    'Brutalis Dreadnought',
    'Captain',
    'Captain in Gravis Armour',
    'Captain in Phobos Armour',
    'Captain in Terminator Armour',
    'Captain with Jump Pack',
    'Centurion Assault Squad',
    'Centurion Devastator Squad',
    'Chaplain',
    'Chaplain in Terminator Armour',
    'Chaplain on Bike',
    'Chaplain with Jump Pack',
    'Company Heroes',
    'Desolation Squad',
    'Devastator Squad',
    'Drop Pod',
    'Eliminator Squad',
    'Firestrike Servo-Turrets',
    'Gladiator Lancer',
    'Gladiator Reaper',
    'Gladiator Valiant',
    'Hammerfall Bunker',
    'Heavy Intercessor Squad',
    'Hellblaster Squad',
    'Impulsor',
    'Inceptor Squad',
    'Incursor Squad',
    'Infernus Squad',
    'Infiltrator Squad',
    'Intercessor Squad',
    'Invader ATV',
    'Invictor Tactical Warsuit',
    'Land Raider',
    'Land Raider Crusader',
    'Land Raider Redeemer',
    'Librarian',
    'Librarian in Phobos Armour',
    'Librarian in Terminator Armour',
    'Lieutenant',
    'Lieutenant in Reiver Armour',
    'Outrider Squad',
    'Predator Annihilator',
    'Predator Destructor',
    'Razorback',
    'Redemptor Dreadnought',
    'Reiver Squad',
    'Repulsor',
    'Repulsor Executioner',
    'Rhino',
    'Scout Squad',
    'Sternguard Veteran Squad',
    'Storm Speeder Hailstrike',
    'Storm Speeder Hammerstrike',
    'Storm Speeder Thunderstrike',
    'Stormhawk Interceptor',
    'Stormraven Gunship',
    'Stormtalon Gunship',
    'Tactical Squad',
    'Techmarine',
    'Terminator Assault Squad',
    'Vanguard Veteran Squad with Jump Packs',
    'Vindicator',
    'Whirlwind',
]

# ---------------------------------------------------------------------------
# Unit data: (gw_sku, points_cost, category, name)
# ---------------------------------------------------------------------------
BLOOD_ANGELS_UNITS = [
    ('41-03', 85, 'epic_hero', 'Astorath'),
    ('41-10', 125, 'vehicle', 'Baal Predator'),
    ('41-26', 80, 'character', 'Blood Angels Captain'),
    ('41-02', 110, 'epic_hero', 'Chief Librarian Mephiston'),
    ('41-04', 125, 'epic_hero', 'Commander Dante'),
    ('48-137', 135, 'vehicle', 'Dreadnought'),
    (None, 55, 'character', 'Judiciar'),
    ('41-05', 100, 'epic_hero', 'Lemartes'),
    ('48-137', 170, 'vehicle', 'Librarian Dreadnought'),
    ('41-06', 125, 'infantry', 'Sanguinary Guard'),
    ('41-09', 75, 'character', 'Sanguinary Priest'),
    (None, 85, 'infantry', 'Suppressor Squad'),
    ('41-08', 130, 'epic_hero', 'The Sanguinor'),
]


class Command(BaseCommand):
    """
    Seed 11th Edition points, category, and active status for Blood Angels
    units.

    Looks up each unit by (name, faction) and updates points_cost, category,
    and is_active in place; creates the row if it doesn't exist yet (linking
    the product by gw_sku when one is given). Idempotent -- safe to re-run.
    """

    help = 'Seed 11th Edition points and categories for Blood Angels units.'

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
            'Seeding Blood Angels points (11th Edition)' + (' [DRY RUN]' if dry_run else '') + '\u2026\n'
        )

        fac = Faction.objects.filter(name='Blood Angels').first()
        if not fac:
            self.stdout.write(self.style.ERROR(
                'Blood Angels faction not found. Run populate_products first.'
            ))
            return

        for old_name, new_name in BLOOD_ANGELS_RENAMES:
            unit = UnitType.objects.filter(name=old_name, faction=fac).first()
            if unit:
                self.stdout.write(f'  [rename] {old_name!r} -> {new_name!r}')
                if not dry_run:
                    unit.name = new_name
                    unit.save(update_fields=['name'])

        for name in BLOOD_ANGELS_DEACTIVATE:
            unit = UnitType.objects.filter(name=name, faction=fac).first()
            if unit and unit.is_active:
                self.stdout.write(f'  [deactivate] {name!r}')
                if not dry_run:
                    unit.is_active = False
                    unit.save(update_fields=['is_active'])

        updated_count = 0
        created_count = 0
        skipped_count = 0

        for gw_sku, points, category, label in BLOOD_ANGELS_UNITS:
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
