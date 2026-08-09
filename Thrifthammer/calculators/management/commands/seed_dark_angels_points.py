"""
Management command: seed_dark_angels_points

Sets points_cost, category, and active status on UnitType records for
Dark Angels units, using official 11th Edition data sourced from the
BSData community BattleScribe project (github.com/BSData/wh40k-11e), the
same data New Recruit itself is built on.

Usage:
    python manage.py seed_dark_angels_points

The command is fully idempotent -- safe to re-run. It looks up each unit by
(name, faction) -- the same pair UnitType enforces uniqueness on.

Notes:
- Same hybrid-catalogue pattern as Black Templars/Blood Angels: BSData's
  Dark Angels file defines only 16 DA-exclusive units directly; everything
  else falls back to the base Space Marines faction via the calculator's
  parent-faction fallback. Unlike those two chapters, all 16 DA-exclusive
  units already existed as DB rows under their correct literal BSData
  names -- no renames needed, only point/category refreshes.
- 'Deathwing Knights' and 'Deathwing Terminator Squad' (44-10), and
  'Ravenwing Dark Talon' and 'Ravenwing Darkshroud' (44-14), were already
  correctly set up as shared-SKU dual-build pairs -- just needed real
  point/category corrections (Darkshroud in particular was badly stale:
  210pts/infantry -> 70pts/vehicle).
- 'Judiciar' and 'Suppressor Squad' were already active productless
  placeholder rows here (unlike Black Templars, where they needed
  reactivating) -- just refreshed to the same values already established
  for Space Marines/Black Templars/Blood Angels.
- 'Dark Angels Interrogator-Chaplain' (44-22) and 'Ravenwing Bike Squadron'
  (44-23) are real, active products with NO entry anywhere in the current
  11e Dark Angels BSData file -- not even Legends-tagged. Left untouched
  (already correctly inactive, 0pts) rather than fabricated.
- The ~70 generic Space-Marine-squad rows this chapter had duplicated with
  no BSData DA-specific override are deactivated here so they correctly
  fall back to the current base Space Marines rows for the same product,
  same reasoning as every other chapter. Confirmed with user 2026-08-07.
"""

from django.core.management.base import BaseCommand

from calculators.models import UnitType
from products.models import Faction, Product

# ---------------------------------------------------------------------------
# Generic Space-Marine-squad duplicates -- deactivated.
# ---------------------------------------------------------------------------
DARK_ANGELS_DEACTIVATE = [
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
    'Dreadnought',
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
DARK_ANGELS_UNITS = [
    ('44-03', 70, 'epic_hero', 'Asmodai'),
    ('44-04', 140, 'epic_hero', 'Azrael'),
    ('44-05', 75, 'epic_hero', 'Belial'),
    ('44-10', 240, 'infantry', 'Deathwing Knights'),
    ('44-10', 165, 'infantry', 'Deathwing Terminator Squad'),
    ('44-02', 75, 'epic_hero', 'Ezekiel'),
    ('44-13', 80, 'infantry', 'Inner Circle Companions'),
    (None, 55, 'character', 'Judiciar'),
    ('44-16', 130, 'vehicle', 'Land Speeder Vengeance'),
    ('44-07', 70, 'epic_hero', 'Lazarus'),
    ('44-06', 265, 'epic_hero', "Lion El'Jonson"),
    ('44-17', 180, 'vehicle', 'Nephilim Jetfighter'),
    ('44-12', 75, 'mounted', 'Ravenwing Black Knights'),
    ('44-09', 105, 'character', 'Ravenwing Command Squad'),
    ('44-14', 200, 'vehicle', 'Ravenwing Dark Talon'),
    ('44-14', 70, 'vehicle', 'Ravenwing Darkshroud'),
    ('44-08', 95, 'epic_hero', 'Sammael'),
    (None, 85, 'infantry', 'Suppressor Squad'),
]


class Command(BaseCommand):
    """
    Seed 11th Edition points, category, and active status for Dark Angels
    units.

    Looks up each unit by (name, faction) and updates points_cost, category,
    and is_active in place; creates the row if it doesn't exist yet (linking
    the product by gw_sku when one is given). Idempotent -- safe to re-run.
    """

    help = 'Seed 11th Edition points and categories for Dark Angels units.'

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
            'Seeding Dark Angels points (11th Edition)' + (' [DRY RUN]' if dry_run else '') + '\u2026\n'
        )

        fac = Faction.objects.filter(name='Dark Angels').first()
        if not fac:
            self.stdout.write(self.style.ERROR(
                'Dark Angels faction not found. Run populate_products first.'
            ))
            return

        for name in DARK_ANGELS_DEACTIVATE:
            unit = UnitType.objects.filter(name=name, faction=fac).first()
            if unit and unit.is_active:
                self.stdout.write(f'  [deactivate] {name!r}')
                if not dry_run:
                    unit.is_active = False
                    unit.save(update_fields=['is_active'])

        updated_count = 0
        created_count = 0
        skipped_count = 0

        for gw_sku, points, category, label in DARK_ANGELS_UNITS:
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
