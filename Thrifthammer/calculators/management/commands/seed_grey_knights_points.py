"""
Management command: seed_grey_knights_points

Sets points_cost and category on UnitType records for all Grey Knights
units, using official 11th Edition data sourced from the BSData community
BattleScribe project (github.com/BSData/wh40k-11e), the same data New
Recruit itself is built on.

Usage:
    python manage.py seed_grey_knights_points

The command is fully idempotent -- safe to re-run. It looks up each unit by
(name, faction) -- the same pair UnitType enforces uniqueness on -- so SKU
collisions (e.g. Grand Master / Grand Master Voldus sharing product 57-02,
Land Raider / Land Raider Redeemer sharing 48-119) never need special-casing.

Notes:
- Migration from 10th to 11th Edition (2026-08-05). Previous version of this
  file held 10th Edition / New Recruit values and stale GW SKUs that no
  longer matched the current Product catalogue (e.g. it listed Castellan
  Crowe at 57-01 and Brother-Captain at 57-04; the real current SKUs are
  57-21 and 48-103) -- rebuilt from scratch against live DB + BSData data
  rather than edited in place, same as seed_orks_points.py.
- Points are the flat/base cost only. Wargear-swap deltas and squad-size
  conditional cost modifiers are intentionally ignored, per user direction --
  one flat number per unit, same as every other faction's points seed.
- Categories were corrected using BSData's classification where it differs
  from ours. Several Grey Knights terminator-armoured squads (Paladin,
  Purgation, Purifier) were previously bucketed into 'vehicle' by the old
  keyword-based auto-classifier -- they are Infantry.
- [Legends] and [Crucible]-tagged BSData entries are excluded entirely --
  not standard matched-play content.
- BSData also prices some weapon options as their own catalogue entries
  (e.g. "Twin lascannon" at 0pts, type "upgrade") rather than folding them
  into a unit's base cost. These are NOT units and must be excluded when
  parsing BSData -- filter on type in ('unit', 'model'), not just a
  truthy/nonzero points value.
- Grey Knights Thunderhawk Gunship (805pts, confirmed real in BSData) has no
  matching product in our catalogue and was NOT added here -- user declined
  to backlog-track it (2026-08-05), unlike the Orks backlog approach.
"""

from django.core.management.base import BaseCommand

from calculators.models import UnitType
from products.models import Faction, Product

# ---------------------------------------------------------------------------
# Unit data: (gw_sku, points_cost, category, name)
#
# Sourced from BSData/wh40k-11e ("Imperium - Grey Knights.json"), 11th
# Edition. Base points only, no wargear or squad-size modifiers. Verified
# against every currently active Grey Knights UnitType row.
# ---------------------------------------------------------------------------
GREY_KNIGHTS_UNITS = [
    ('48-103', 95,  'character',  'Brother-Captain'),
    ('55-22',  70,  'character',  'Brotherhood Champion'),
    ('HA-051', 65,  'character',  'Brotherhood Chaplain'),
    ('48-120', 90,  'character',  'Brotherhood Librarian'),
    ('48-135', 70,  'character',  'Brotherhood Techmarine'),
    ('57-08',  140, 'battleline', 'Brotherhood Terminator Squad'),
    ('57-21',  100, 'epic_hero',  'Castellan Crowe'),
    ('57-02',  95,  'character',  'Grand Master'),
    ('57-02',  125, 'epic_hero',  'Grand Master Voldus'),
    ('57-23',  200, 'character',  'Grand Master in Nemesis Dreadknight'),
    ('57-24',  125, 'infantry',   'Interceptor Squad'),
    ('48-119', 220, 'vehicle',    'Land Raider'),
    ('48-22',  220, 'vehicle',    'Land Raider Crusader'),
    ('48-119', 250, 'vehicle',    'Land Raider Redeemer'),
    ('57-14',  195, 'vehicle',    'Nemesis Dreadknight'),
    ('57-25',  170, 'infantry',   'Paladin Squad'),
    ('57-26',  110, 'infantry',   'Purgation Squad'),
    ('57-27',  130, 'infantry',   'Purifier Squad'),
    ('48-126', 75,  'transport',  'Razorback'),
    ('48-128', 70,  'transport',  'Rhino'),
    ('48-129', 160, 'vehicle',    'Stormhawk Interceptor'),
    ('48-130', 280, 'vehicle',    'Stormraven Gunship'),
    ('48-134', 170, 'vehicle',    'Stormtalon Gunship'),
    ('57-06',  115, 'battleline', 'Strike Squad'),
    ('48-137', 130, 'character',  'Venerable Dreadnought'),
]


class Command(BaseCommand):
    """
    Seed 11th Edition points, category, and active status for Grey Knights
    units.

    Looks up each unit by (name, faction) and updates points_cost, category,
    and is_active in place; creates the row if it doesn't exist yet (linking
    the product by gw_sku when one is given). Idempotent -- safe to re-run.
    """

    help = 'Seed 11th Edition points and categories for Grey Knights units.'

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
            'Seeding Grey Knights points (11th Edition)' + (' [DRY RUN]' if dry_run else '') + '…\n'
        )

        gk_faction = Faction.objects.filter(name='Grey Knights').first()
        if not gk_faction:
            self.stdout.write(self.style.ERROR(
                'Grey Knights faction not found. Run populate_products first.'
            ))
            return

        updated_count = 0
        created_count = 0
        skipped_count = 0

        for gw_sku, points, category, label in GREY_KNIGHTS_UNITS:
            product = Product.objects.filter(gw_sku=gw_sku).first() if gw_sku else None

            if gw_sku and not product:
                self.stdout.write(
                    self.style.WARNING(f'  [skip]    {label} (SKU {gw_sku} not found in DB)')
                )
                skipped_count += 1
                continue

            unit = UnitType.objects.filter(name=label, faction=gk_faction).first()

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
                        faction=gk_faction,
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
