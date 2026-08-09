"""
Management command: seed_deathwatch_points

Sets points_cost, category, and active status on UnitType records for
Deathwatch units, using official 11th Edition data sourced from the
BSData community BattleScribe project (github.com/BSData/wh40k-11e), the
same data New Recruit itself is built on.

Usage:
    python manage.py seed_deathwatch_points

The command is fully idempotent -- safe to re-run. It looks up each unit by
(name, faction) -- the same pair UnitType enforces uniqueness on.

Notes:
- Same hybrid-catalogue pattern as Black Templars/Blood Angels/Dark Angels
  -- BSData's Deathwatch file defines only 10 DW-exclusive units directly;
  everything else falls back to the base Space Marines faction via the
  calculator's parent-faction fallback.
- Renames: {'Deathwatch Kill Team': 'Deathwatch Veterans'}
- 6-way multi-build split on SKU 39-10 ("Deathwatch Kill Team", $40 MSRP,
  described as "Five heavily customisable Deathwatch Space Marines"):
  Deathwatch Veterans (100pts), Decimus Kill Team (100pts), Fortis Kill
  Team (195pts), Indomitor Kill Team (275pts), Spectrus Kill Team
  (170pts), Talonstrike Kill Team (265pts). Same mechanism as the Leman
  Russ 8-way split. User confirmed 2026-08-07.
- 'Deathwatch Veteran Squad' was a stale duplicate of the same concept
  (inactive, 100pts, no product) -- deactivated rather than reused.
- 'Deathwatch Terminator Squad' has no dedicated product -- cross-linked
  to the base Space Marines Terminator Squad product (48-06), same
  pattern as every other cross-faction shared-SKU link this project.
  User confirmed 2026-08-07.
- 'Judiciar'/'Suppressor Squad' were inactive productless placeholders
  here too -- refreshed to the same values established for every other
  chapter.
- The ~67 generic Space-Marine-squad rows this chapter had duplicated
  with no BSData DW-specific override are deactivated here so they
  correctly fall back to the current base Space Marines rows for the
  same product, same reasoning as every chapter so far.
"""

from django.core.management.base import BaseCommand

from calculators.models import UnitType
from products.models import Faction, Product

# ---------------------------------------------------------------------------
# Renames applied first: (old_name, new_name)
# ---------------------------------------------------------------------------
DEATHWATCH_RENAMES = [
    ('Deathwatch Kill Team', 'Deathwatch Veterans'),
]

# ---------------------------------------------------------------------------
# Stale duplicate + generic Space-Marine-squad rows -- deactivated.
# ---------------------------------------------------------------------------
DEATHWATCH_DEACTIVATE = [
    'Deathwatch Veteran Squad',
    'Ancient',
    'Ancient in Terminator Armor',
    'Apothecary',
    'Apothecary Biologis',
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
    'Sternguard Veteran Squad',
    'Storm Speeder Hailstrike',
    'Storm Speeder Hammerstrike',
    'Storm Speeder Thunderstrike',
    'Stormhawk Interceptor',
    'Stormraven Gunship',
    'Stormtalon Gunship',
    'Techmarine',
    'Vanguard Veteran Squad with Jump Packs',
    'Vindicator',
    'Whirlwind',
]

# ---------------------------------------------------------------------------
# Unit data: (gw_sku, points_cost, category, name)
# ---------------------------------------------------------------------------
DEATHWATCH_UNITS = [
    ('39-04', 180, 'vehicle', 'Corvus Blackstar'),
    ('48-06', 180, 'infantry', 'Deathwatch Terminator Squad'),
    ('39-10', 100, 'battleline', 'Deathwatch Veterans'),
    ('39-10', 100, 'battleline', 'Decimus Kill Team'),
    ('39-10', 195, 'infantry', 'Fortis Kill Team'),
    ('39-10', 275, 'infantry', 'Indomitor Kill Team'),
    (None, 55, 'character', 'Judiciar'),
    ('39-10', 170, 'infantry', 'Spectrus Kill Team'),
    (None, 85, 'infantry', 'Suppressor Squad'),
    ('39-10', 265, 'infantry', 'Talonstrike Kill Team'),
    ('39-01', 65, 'epic_hero', 'Watch Captain Artemis'),
    ('39-02', 95, 'character', 'Watch Master'),
]


class Command(BaseCommand):
    """
    Seed 11th Edition points, category, and active status for Deathwatch
    units.

    Looks up each unit by (name, faction) and updates points_cost, category,
    and is_active in place; creates the row if it doesn't exist yet (linking
    the product by gw_sku when one is given). Idempotent -- safe to re-run.
    """

    help = 'Seed 11th Edition points and categories for Deathwatch units.'

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
            'Seeding Deathwatch points (11th Edition)' + (' [DRY RUN]' if dry_run else '') + '\u2026\n'
        )

        fac = Faction.objects.filter(name='Deathwatch').first()
        if not fac:
            self.stdout.write(self.style.ERROR(
                'Deathwatch faction not found. Run populate_products first.'
            ))
            return

        for old_name, new_name in DEATHWATCH_RENAMES:
            unit = UnitType.objects.filter(name=old_name, faction=fac).first()
            if unit:
                self.stdout.write(f'  [rename] {old_name!r} -> {new_name!r}')
                if not dry_run:
                    unit.name = new_name
                    unit.save(update_fields=['name'])

        for name in DEATHWATCH_DEACTIVATE:
            unit = UnitType.objects.filter(name=name, faction=fac).first()
            if unit and unit.is_active:
                self.stdout.write(f'  [deactivate] {name!r}')
                if not dry_run:
                    unit.is_active = False
                    unit.save(update_fields=['is_active'])

        updated_count = 0
        created_count = 0
        skipped_count = 0

        for gw_sku, points, category, label in DEATHWATCH_UNITS:
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
