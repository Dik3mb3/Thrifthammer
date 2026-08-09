"""
Management command: seed_admech_points

Sets points_cost and category on UnitType records for all Adeptus
Mechanicus units, using official 11th Edition data sourced from the BSData
community BattleScribe project (github.com/BSData/wh40k-11e), the same data
New Recruit itself is built on.

Usage:
    python manage.py seed_admech_points

The command is fully idempotent -- safe to re-run. It looks up each unit by
(name, faction) -- the same pair UnitType enforces uniqueness on.

Notes:
- This faction had a batch of real products added to the catalogue that
  never had calculator points seeded at all (every MC-xxx SKU showed
  points_cost=0 before this run) -- this fills in genuinely missing data
  for most of the roster, not just refreshes stale numbers.
- Points are the flat/base cost only, wargear/squad-size modifiers ignored,
  same as every other faction's points seed.
- "Codex: Adeptus Mechanicus" (MC-025) is a book, not a unit -- deactivated
  from the calculator rather than assigned points (same issue found on
  "Codex: Orks").
- "Kill Team: Battleclade" (MC-004) is renamed to "Servitor Battleclade" --
  its GW URL confirms it's the Kill Team box, and BSData's matching unit by
  that name is the 40k-legal identity of what it builds.
- "Hastarii" (MC-007) and "Sydonian Dragoon" (MC-019) are both genuine
  multi-build kits (GW sells one box, two build options with different
  points) -- split into two UnitType rows each, both linked to the same
  product, per user direction (2026-08-05). Matches the existing pattern
  used elsewhere for shared-SKU variants (e.g. Warboss / Warboss in Mega
  Armour, Grand Master / Grand Master Voldus).
"""

from django.core.management.base import BaseCommand

from calculators.models import UnitType
from products.models import Faction, Product

# ---------------------------------------------------------------------------
# Renames applied before the main pass, so the tuple list below can target
# units by their corrected name. (old_name, new_name)
# ---------------------------------------------------------------------------
ADMECH_RENAMES = [
    ('Kill Team: Battleclade', 'Servitor Battleclade'),
    ('Adeptus Mechanicus Hastarii', 'Hastarii Exterminators'),
    ('Adeptus Mechanicus Sydonian Dragoon', 'Sydonian Dragoons with radium jezzails'),
]

# Units deactivated rather than assigned points -- not real deployable units.
ADMECH_DEACTIVATE = [
    'Codex: Adeptus Mechanicus',
]

# ---------------------------------------------------------------------------
# Unit data: (gw_sku, points_cost, category, name)
#
# Sourced from BSData/wh40k-11e ("Imperium - Adeptus Mechanicus.json"),
# 11th Edition. Base points only, no wargear or squad-size modifiers.
# ---------------------------------------------------------------------------
ADMECH_UNITS = [
    ('MC-001', 160, 'vehicle',    'Adeptus Mechanicus Archaeopter Fusilave'),
    ('MC-002', 185, 'vehicle',    'Adeptus Mechanicus Archaeopter Stratoraptor'),
    ('MC-003', 145, 'vehicle',    'Adeptus Mechanicus Archaeopter Transvector'),
    ('MC-005', 220, 'epic_hero',  'Adeptus Mechanicus Belisarius Cawl'),
    ('MC-006',  70, 'infantry',   'Adeptus Mechanicus Fulgurite Electro-Priests'),
    ('MC-008', 160, 'vehicle',    'Adeptus Mechanicus Kastelan Robots'),
    ('MC-009', 150, 'infantry',   'Adeptus Mechanicus Kataphron Breachers'),
    ('MC-010',  80, 'infantry',   'Adeptus Mechanicus Pteraxii Skystalkers'),
    ('MC-011',  80, 'infantry',   'Adeptus Mechanicus Pteraxii Sterylizors'),
    ('MC-012',  60, 'mounted',    'Adeptus Mechanicus Serberys Raiders'),
    ('MC-013',  55, 'mounted',    'Adeptus Mechanicus Serberys Sulphurhounds'),
    ('MC-014',  75, 'infantry',   'Adeptus Mechanicus Sicarian Infiltrators'),
    ('MC-015',  75, 'infantry',   'Adeptus Mechanicus Sicarian Ruststalkers'),
    ('MC-016',  35, 'character',  'Adeptus Mechanicus Skitarii Marshal'),
    ('MC-017', 160, 'vehicle',    'Adeptus Mechanicus Skorpius Disintegrator'),
    ('MC-018',  75, 'transport',  'Adeptus Mechanicus Skorpius Dunerider'),
    ('MC-020',  50, 'character',  'Adeptus Mechanicus Sydonian Skatros'),
    ('MC-022',  55, 'character',  'Adeptus Mechanicus Tech-Priest Enginseer'),
    ('MC-023',  60, 'character',  'Adeptus Mechanicus Tech-Priest Manipulus'),
    ('MC-021',  45, 'character',  'Adeptus Mechanicus Technoarcheologist'),
    ('MC-024', 180, 'epic_hero',  'Adeptus Mechanicus Thulia Ghuld'),
    ('59-14',   80, 'vehicle',    'Ironstrider Ballistarii'),
    ('59-18',  100, 'infantry',   'Kataphron Destroyers'),
    ('59-10',   85, 'battleline', 'Skitarii Rangers'),
    ('59-11',   85, 'battleline', 'Skitarii Vanguard'),
    ('59-06',   65, 'character',  'Tech-Priest Dominus'),
    # ── Renamed 1:1 (Kill Team box -> its 40k-legal unit identity) ─────────
    ('MC-004',  65, 'infantry',   'Servitor Battleclade'),
    # ── Electropriests / Dunecrawler: DB name is shorthand, GW URL confirms
    #    which BSData unit they actually are; points already matched, listed
    #    here for completeness/idempotency ──────────────────────────────────
    ('59-20',   65, 'infantry',   'Electropriests'),
    ('59-16',  155, 'vehicle',    'Dunecrawler'),
    # ── Hastarii split (one box, two build options, different points) ──────
    ('MC-007', 105, 'infantry',   'Hastarii Exterminators'),
    ('MC-007', 115, 'infantry',   'Hastarii Fusiliers'),
    # ── Sydonian Dragoon split (one box, two build options) ────────────────
    ('MC-019',  55, 'vehicle',    'Sydonian Dragoons with radium jezzails'),
    ('MC-019',  60, 'vehicle',    'Sydonian Dragoons with taser lances'),
]


class Command(BaseCommand):
    """
    Seed 11th Edition points, category, and active status for Adeptus
    Mechanicus units.

    Looks up each unit by (name, faction) and updates points_cost, category,
    and is_active in place; creates the row if it doesn't exist yet (linking
    the product by gw_sku when one is given). Idempotent -- safe to re-run.
    """

    help = 'Seed 11th Edition points and categories for Adeptus Mechanicus units.'

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
            'Seeding Adeptus Mechanicus points (11th Edition)' + (' [DRY RUN]' if dry_run else '') + '…\n'
        )

        fac = Faction.objects.filter(name='Adeptus Mechanicus').first()
        if not fac:
            self.stdout.write(self.style.ERROR(
                'Adeptus Mechanicus faction not found. Run populate_products first.'
            ))
            return

        for old_name, new_name in ADMECH_RENAMES:
            unit = UnitType.objects.filter(name=old_name, faction=fac).first()
            if unit:
                self.stdout.write(f'  [rename] {old_name!r} -> {new_name!r}')
                if not dry_run:
                    unit.name = new_name
                    unit.save(update_fields=['name'])

        for name in ADMECH_DEACTIVATE:
            unit = UnitType.objects.filter(name=name, faction=fac).first()
            if unit and unit.is_active:
                self.stdout.write(f'  [deactivate] {name!r} (not a real unit)')
                if not dry_run:
                    unit.is_active = False
                    unit.save(update_fields=['is_active'])

        updated_count = 0
        created_count = 0
        skipped_count = 0

        for gw_sku, points, category, label in ADMECH_UNITS:
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
