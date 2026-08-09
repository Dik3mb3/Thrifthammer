"""
Management command: seed_iron_hands_points

Sets points_cost, category, and active status on UnitType records for
Iron Hands units, using official 11th Edition data sourced from the
BSData community BattleScribe project (github.com/BSData/wh40k-11e), the
same data New Recruit itself is built on.

Usage:
    python manage.py seed_iron_hands_points
    python manage.py seed_iron_hands_points --dry-run

The command is fully idempotent -- safe to re-run. It looks up each unit by
(name, faction) -- the same pair UnitType enforces uniqueness on.

Notes:
- Same hybrid-catalogue pattern as every prior Space Marine successor
  chapter -- BSData's Iron Hands file defines only 2 chapter-exclusive
  units directly; everything else falls back to the base Space Marines
  faction via the calculator's parent-faction fallback.
  Source: "Imperium - Iron Hands.json".
- The 74 generic Space-Marine-squad rows this chapter had duplicated with
  no BSData Iron-Hands-specific override are deactivated here so they
  correctly fall back to the current base Space Marines rows for the same
  product. Verified before writing this command: all 74 share the exact
  same product_id as their base Space Marines counterpart -- zero shared-
  SKU conflicts. User confirmed 2026-08-07.
"""

from django.core.management.base import BaseCommand

from calculators.models import UnitType
from products.models import Faction, Product

# ---------------------------------------------------------------------------
# Generic Space-Marine-squad rows -- deactivated so they fall back to base
# Space Marines.
# ---------------------------------------------------------------------------
IRON_HANDS_DEACTIVATE = [
    'Aggressor Squad', 'Ancient', 'Ancient in Terminator Armor', 'Apothecary',
    'Apothecary Biologis', 'Assault Intercessor Squad',
    'Assault Intercessors with Jump Packs', 'Ballistus Dreadnought',
    'Bladeguard Veteran Squad', 'Brutalis Dreadnought', 'Captain',
    'Captain in Gravis Armour', 'Captain in Phobos Armour',
    'Captain in Terminator Armour', 'Captain with Jump Pack',
    'Centurion Assault Squad', 'Centurion Devastator Squad', 'Chaplain',
    'Chaplain in Terminator Armour', 'Chaplain on Bike',
    'Chaplain with Jump Pack', 'Company Heroes', 'Desolation Squad',
    'Devastator Squad', 'Dreadnought', 'Drop Pod', 'Eliminator Squad',
    'Eradicator Squad', 'Firestrike Servo-Turrets', 'Gladiator Lancer',
    'Gladiator Reaper', 'Gladiator Valiant', 'Heavy Intercessor Squad',
    'Hellblaster Squad', 'Impulsor', 'Inceptor Squad', 'Incursor Squad',
    'Infernus Squad', 'Infiltrator Squad', 'Intercessor Squad',
    'Invader ATV', 'Invictor Tactical Warsuit', 'Land Raider',
    'Land Raider Crusader', 'Land Raider Redeemer', 'Librarian',
    'Librarian in Phobos Armour', 'Librarian in Terminator Armour',
    'Lieutenant', 'Lieutenant in Reiver Armour', 'Outrider Squad',
    'Predator Annihilator', 'Predator Destructor', 'Razorback',
    'Redemptor Dreadnought', 'Reiver Squad', 'Repulsor',
    'Repulsor Executioner', 'Rhino', 'Scout Squad', 'Sternguard Veteran Squad',
    'Storm Speeder Hailstrike', 'Storm Speeder Hammerstrike',
    'Storm Speeder Thunderstrike', 'Stormhawk Interceptor',
    'Stormraven Gunship', 'Stormtalon Gunship', 'Tactical Squad', 'Techmarine',
    'Terminator Assault Squad', 'Terminator Squad',
    'Vanguard Veteran Squad with Jump Packs', 'Vindicator', 'Whirlwind',
]

# ---------------------------------------------------------------------------
# Unit data: (gw_sku, points_cost, category, name)
# ---------------------------------------------------------------------------
IRON_HANDS_UNITS = [
    ('61-01', 90, 'epic_hero', 'Caanok Var'),
    ('61-02', 85, 'epic_hero', 'Iron Father Feirros'),
]


class Command(BaseCommand):
    """
    Seed 11th Edition points, category, and active status for Iron Hands
    units.

    Looks up each unit by (name, faction) and updates points_cost, category,
    and is_active in place; creates the row if it doesn't exist yet (linking
    the product by gw_sku when one is given). Idempotent -- safe to re-run.
    """

    help = 'Seed 11th Edition points and categories for Iron Hands units.'

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
            'Seeding Iron Hands points (11th Edition)' + (' [DRY RUN]' if dry_run else '') + '…\n'
        )

        fac = Faction.objects.filter(name='Iron Hands').first()
        if not fac:
            self.stdout.write(self.style.ERROR(
                'Iron Hands faction not found. Run populate_products first.'
            ))
            return

        for name in IRON_HANDS_DEACTIVATE:
            unit = UnitType.objects.filter(name=name, faction=fac).first()
            if unit and unit.is_active:
                self.stdout.write(f'  [deactivate] {name!r}')
                if not dry_run:
                    unit.is_active = False
                    unit.save(update_fields=['is_active'])

        updated_count = 0
        created_count = 0
        skipped_count = 0

        for gw_sku, points, category, label in IRON_HANDS_UNITS:
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
