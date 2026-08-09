"""
Management command: seed_black_templars_points

Sets points_cost, category, and active status on UnitType records for
Black Templars units, using official 11th Edition data sourced from the
BSData community BattleScribe project (github.com/BSData/wh40k-11e), the
same data New Recruit itself is built on.

Usage:
    python manage.py seed_black_templars_points

The command is fully idempotent -- safe to re-run. It looks up each unit by
(name, faction) -- the same pair UnitType enforces uniqueness on.

Notes:
- BSData's Black Templars catalogue ("Imperium - Black Templars.json") only
  defines 18 BT-exclusive/BT-override units directly (a 19th, "Emperor's
  Champion (Anointed)", has no matching product and goes to the backlog
  instead). Everything else a Black Templars army can take is a plain
  Space Marines unit with no BT-specific override -- the calculator's own
  parent-faction fallback (calculators/views.py) already surfaces those
  automatically once the base "Space Marines" faction has current data
  (migrated 2026-08-07, prerequisite for this command).
- This is a MUCH smaller scope than the old 10th Edition file, which
  duplicated a BT-specific row for every unit whether or not BT actually
  had its own points/rules for it. This command intentionally does not
  replicate that -- see the deactivation list below.
- Renames (old DB name -> real BSData name) applied first, so points/
  category updates below can target units by their correct name:
    ('Black Templars Castellan', 'Castellan'),
    ('Black Templars Chaplain Grimaldus', 'Chaplain Grimaldus'),
    ('Black Templars Crusade Ancient', 'Crusade Ancient'),
    ('Black Templars Primaris Crusader Squad', 'Crusader Squad'),
    ("Black Templars Emperor's Champion", "Emperor's Champion"),
    ('Black Templars Execrator', 'Execrator'),
    ('Black Templars Helbrecht', 'High Marshal Helbrecht'),
    ('Black Templars Marshal', 'Marshal'),
    ('Black Templars Sword Brethren', 'Sword Brethren Squad'),
- 3 new units created, sharing gw_sku with the base Space Marines product
  for the same physical kit (Gladiator Lancer/Reaper/Valiant) -- BT gets
  explicit access per its own BSData entries, at identical points/category
  to the base Space Marines version.
- 'Terminator Squad' already existed as an inactive BT row linked to
  48-06 -- reactivated and refreshed, not recreated.
- 2 bundle/book rows (Combat Patrol, Codex Supplement) deactivated --
  never real units.
- The generic Space-Marine-squad rows this chapter had duplicated with no
  BSData BT-specific override (Ancient, Apothecary, Captain, Chaplain,
  Intercessor Squad, Tactical Squad, Devastator Squad, every Dreadnought
  variant, etc. -- 29 rows) are deactivated here so they correctly fall
  back to the now-current base Space Marines rows for the same product,
  rather than sitting frozen on stale 10th Edition points forever.
  EXCEPTION: 'Judiciar' and 'Suppressor Squad' are deliberately left
  active even though they fit this pattern -- both are productless
  placeholder rows and, as of this pass, the ONLY place either unit
  appears anywhere on the site (base Space Marines doesn't have them
  either). Deactivating them would be a net loss of calculator coverage,
  not a cleanup. Confirmed with user 2026-08-07.
"""

from django.core.management.base import BaseCommand

from calculators.models import UnitType
from products.models import Faction, Product

# ---------------------------------------------------------------------------
# Renames applied first: (old_name, new_name)
# ---------------------------------------------------------------------------
BT_RENAMES = [
    ('Black Templars Castellan', 'Castellan'),
    ('Black Templars Chaplain Grimaldus', 'Chaplain Grimaldus'),
    ('Black Templars Crusade Ancient', 'Crusade Ancient'),
    ('Black Templars Primaris Crusader Squad', 'Crusader Squad'),
    ("Black Templars Emperor's Champion", "Emperor's Champion"),
    ('Black Templars Execrator', 'Execrator'),
    ('Black Templars Helbrecht', 'High Marshal Helbrecht'),
    ('Black Templars Marshal', 'Marshal'),
    ('Black Templars Sword Brethren', 'Sword Brethren Squad'),
]

# ---------------------------------------------------------------------------
# Bundle/book rows -- deactivated, never given points.
# ---------------------------------------------------------------------------
BT_DEACTIVATE = [
    'Black Templars Combat Patrol',
    'Codex Supplement: Black Templars',
    'Ancient',
    'Apothecary',
    'Ballistus Dreadnought',
    'Bladeguard Veteran Squad',
    'Brutalis Dreadnought',
    'Captain',
    'Chaplain',
    'Company Heroes',
    'Devastator Squad',
    'Eliminator Squad',
    'Firestrike Servo-Turrets',
    'Hammerfall Bunker',
    'Inceptor Squad',
    'Incursor Squad',
    'Infernus Squad',
    'Infiltrator Squad',
    'Intercessor Squad',
    'Invader ATV',
    'Land Raider',
    'Librarian',
    'Lieutenant',
    'Outrider Squad',
    'Predator Destructor',
    'Redemptor Dreadnought',
    'Scout Squad',
    'Tactical Squad',
    'Vanguard Veteran Squad',
    'Vindicator',
    'Whirlwind',
]

# ---------------------------------------------------------------------------
# Unit data: (gw_sku, points_cost, category, name)
#
# Sourced from BSData/wh40k-11e ("Imperium - Black Templars.json"), 11th
# Edition. Base points only, no wargear or squad-size modifiers.
# ---------------------------------------------------------------------------
BLACK_TEMPLARS_UNITS = [
    ('55-25', 70, 'character', 'Castellan'),
    ('55-24', 100, 'infantry', 'Chaplain Grimaldus'),
    ('55-27', 40, 'character', 'Crusade Ancient'),
    ('55-20', 150, 'battleline', 'Crusader Squad'),
    ('55-22', 90, 'character', "Emperor's Champion"),
    ('55-26', 50, 'character', 'Execrator'),
    ('48-113', 160, 'vehicle', 'Gladiator Lancer'),
    ('48-114', 160, 'vehicle', 'Gladiator Reaper'),
    ('48-115', 150, 'vehicle', 'Gladiator Valiant'),
    ('55-21', 110, 'epic_hero', 'High Marshal Helbrecht'),
    ('48-94', 75, 'transport', 'Impulsor'),
    ('48-22', 220, 'vehicle', 'Land Raider Crusader'),
    ('55-28', 80, 'character', 'Marshal'),
    ('48-85', 170, 'vehicle', 'Repulsor'),
    ('48-95', 255, 'vehicle', 'Repulsor Executioner'),
    ('48-43', 85, 'infantry', 'Sternguard Veteran Squad'),
    ('55-23', 105, 'infantry', 'Sword Brethren Squad'),
    ('48-06', 160, 'infantry', 'Terminator Squad'),
    # Productless placeholder rows (see docstring) -- kept active rather than
    # deactivated, but their stale 0pts is corrected using the same BSData
    # values already extracted during the Space Marines pass.
    (None, 55, 'character', 'Judiciar'),
    (None, 85, 'infantry', 'Suppressor Squad'),
]


class Command(BaseCommand):
    """
    Seed 11th Edition points, category, and active status for Black
    Templars units.

    Looks up each unit by (name, faction) and updates points_cost, category,
    and is_active in place; creates the row if it doesn't exist yet (linking
    the product by gw_sku when one is given). Idempotent -- safe to re-run.
    """

    help = 'Seed 11th Edition points and categories for Black Templars units.'

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
            'Seeding Black Templars points (11th Edition)' + (' [DRY RUN]' if dry_run else '') + '\u2026\n'
        )

        fac = Faction.objects.filter(name='Black Templars').first()
        if not fac:
            self.stdout.write(self.style.ERROR(
                'Black Templars faction not found. Run populate_products first.'
            ))
            return

        for old_name, new_name in BT_RENAMES:
            unit = UnitType.objects.filter(name=old_name, faction=fac).first()
            if unit:
                self.stdout.write(f'  [rename] {old_name!r} -> {new_name!r}')
                if not dry_run:
                    unit.name = new_name
                    unit.save(update_fields=['name'])

        for name in BT_DEACTIVATE:
            unit = UnitType.objects.filter(name=name, faction=fac).first()
            if unit and unit.is_active:
                self.stdout.write(f'  [deactivate] {name!r}')
                if not dry_run:
                    unit.is_active = False
                    unit.save(update_fields=['is_active'])

        updated_count = 0
        created_count = 0
        skipped_count = 0

        for gw_sku, points, category, label in BLACK_TEMPLARS_UNITS:
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
