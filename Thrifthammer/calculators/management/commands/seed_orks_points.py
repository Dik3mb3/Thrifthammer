"""
Management command: seed_orks_points

Sets points_cost and category on UnitType records for all Orks units,
using official 11th Edition data sourced from the BSData community
BattleScribe project (github.com/BSData/wh40k-11e), the same data New
Recruit itself is built on.

Usage:
    python manage.py seed_orks_points

The command is fully idempotent -- safe to re-run. It looks up each unit by
(name, faction) -- the same pair UnitType enforces uniqueness on -- so SKU
collisions (e.g. Warboss / Warboss in Mega Armour sharing product 50-02)
never need special-casing the way earlier per-faction seed files did.

Notes:
- Migration from 10th to 11th Edition (2026-08-05). Previous version of this
  file held 10th Edition / New Recruit values and stale GW SKUs that no
  longer matched the current Product catalogue -- rebuilt from scratch
  against live DB + BSData data rather than edited in place.
- Points are the flat/base cost only. Wargear-swap deltas and squad-size
  conditional cost modifiers (e.g. Boyz jumping from 75 to 160pts above 10
  models) are intentionally ignored, per user direction -- one flat number
  per unit, same as every other faction's points seed.
- Categories were corrected using BSData's classification where it differs
  from ours. Many Ork units (Blitza-bommer, Hunta Rig, etc.) were previously
  bucketed into the generic 'infantry' default by the old keyword-based
  auto-classifier, which doesn't recognise Ork-specific names.
- [Legends] and [Crucible]-tagged BSData entries are excluded entirely --
  not standard matched-play content.
- Reactivates two previously-inactive units now confirmed legal in 11th
  Edition: Big'ed Bossbunka (50-25) and Gargantuan Squiggoth (no linked
  product -- never had one).
- Adds three new units backed by existing Armageddon-box products that had
  no UnitType yet: Bannernob (AGA-010), Wartrakk (AGA-016), Big Mek Dakkarig
  (AGA-017).
- Units confirmed real in 11th Edition but with NO matching product in our
  catalogue (Tankbustas, Wurrboy, Breaka Boyz, Wazdakka Gutsmek, Bigboss)
  are intentionally NOT included here -- tracked in memory/
  project_11e_calculator_migration.md as a backlog for manual SKU onboarding.
"""

from django.core.management.base import BaseCommand

from calculators.models import UnitType
from products.models import Faction, Product

# ---------------------------------------------------------------------------
# Unit data: (gw_sku, points_cost, category, name)
#
# gw_sku is None for the one unit with no linked retail product
# (Gargantuan Squiggoth). name is matched against UnitType.name -- the
# lookup key -- not used only for logging.
#
# Sourced from BSData/wh40k-11e (Orks.json), 11th Edition. Base points only,
# no wargear or squad-size modifiers. Verified against every currently
# active Orks UnitType row plus 5 confirmed-real additions.
# ---------------------------------------------------------------------------
ORKS_UNITS = [
    ('50-22', 145, 'vehicle',      'Battlewagon'),
    ('50-52',  90, 'battleline',   'Beast Snagga Boyz'),
    ('50-23',  80, 'character',    'Beastboss'),
    ('50-24',  95, 'character',    'Beastboss on Squigosaur'),
    ('50-26',  70, 'character',    'Big Mek'),
    ('50-27',  80, 'character',    'Big Mek in Mega Armour'),
    ('50-28',  70, 'character',    'Big Mek with Shokk Attack Gun'),
    ('50-29', 105, 'vehicle',      'Blitza-bommer'),
    ('50-31',  70, 'vehicle',      'Boomdakka Snazzwagon'),
    ('50-32',  75, 'epic_hero',    'Boss Snikrot'),
    ('50-10',  75, 'battleline',   'Boyz'),
    ('50-53',  60, 'infantry',     'Burna Boyz'),
    ('50-33', 115, 'vehicle',      'Burna-bommer'),
    ('50-35', 125, 'vehicle',      'Dakkajet'),
    ('50-16', 110, 'vehicle',      'Deff Dread'),
    ('50-36',  70, 'character',    'Deffkilla Wartrike'),
    ('50-37',  75, 'vehicle',      'Deffkoptas'),
    ('50-20',  75, 'infantry',     'Flash Gitz'),
    ('50-38', 235, 'epic_hero',    'Ghazghkull Thraka'),
    ('50-39', 255, 'vehicle',      'Gorkanaut'),
    ('50-54',  45, 'infantry',     'Gretchin'),
    ('50-41', 125, 'monster',      'Hunta Rig'),
    ('50-42', 145, 'monster',      'Kill Rig'),
    ('50-15', 120, 'vehicle',      'Killa Kans'),
    ('50-43', 120, 'infantry',     'Kommandos'),
    ('50-44',  70, 'vehicle',      'Kustom Boosta-blasta'),
    ('50-14',  50, 'infantry',     'Lootas'),
    ('50-12',  60, 'infantry',     'Meganobz'),
    ('50-45',  75, 'vehicle',      'Megatrakk Scrapjet'),
    ('50-55',  55, 'character',    'Mek'),
    ('50-46',  45, 'vehicle',      'Mek Gunz'),
    ('50-50', 270, 'vehicle',      'Morkanaut'),
    ('50-51', 125, 'epic_hero',    'Mozrog Skragbad'),
    ('50-09', 105, 'infantry',     'Nobz'),
    ('50-60',  70, 'character',    'Painboss'),
    ('50-56',  90, 'character',    'Painboy'),
    ('50-61',  85, 'vehicle',      'Rukkatrukk Squigbuggy'),
    ('50-62',  70, 'vehicle',      'Shokkjump Dragsta'),
    ('50-63', 140, 'mounted',      'Squighog Boyz'),
    ('50-64', 600, 'vehicle',      'Stompa'),
    ('50-57',  65, 'infantry',     'Stormboyz'),
    ('50-11',  55, 'transport',    'Trukk'),
    ('50-58',  60, 'mounted',      'Warbikers'),
    ('50-02',  85, 'character',    'Warboss'),
    ('50-02',  80, 'character',    'Warboss in Mega Armour'),
    ('50-65', 165, 'vehicle',      'Wazbom Blastajet'),
    ('50-66',  65, 'character',    'Weirdboy'),
    ('50-67',  80, 'epic_hero',    'Zodgrod Wortsnagga'),
    # ── Reactivations (previously inactive, confirmed legal in 11th Ed) ──────
    ('50-25', 135, 'fortification', "Big'ed Bossbunka"),
    (None,    440, 'monster',      'Ork Gargantuan Squiggoth'),
    # ── New (existing Armageddon-box products, no UnitType yet) ─────────────
    ('AGA-010', 50, 'character',   'Bannernob'),
    ('AGA-016', 60, 'mounted',     'Wartrakk'),
    ('AGA-017', 115, 'vehicle',    'Big Mek Dakkarig'),
]


class Command(BaseCommand):
    """
    Seed 11th Edition points, category, and active status for Orks units.

    Looks up each unit by (name, faction) and updates points_cost, category,
    and is_active in place; creates the row if it doesn't exist yet (linking
    the product by gw_sku when one is given). Idempotent -- safe to re-run.
    """

    help = 'Seed 11th Edition points and categories for Orks units.'

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
            'Seeding Orks points (11th Edition)' + (' [DRY RUN]' if dry_run else '') + '…\n'
        )

        orks_faction = Faction.objects.filter(name='Orks').first()
        if not orks_faction:
            self.stdout.write(self.style.ERROR(
                'Orks faction not found. Run populate_products first.'
            ))
            return

        updated_count = 0
        created_count = 0
        skipped_count = 0

        for gw_sku, points, category, label in ORKS_UNITS:
            product = Product.objects.filter(gw_sku=gw_sku).first() if gw_sku else None

            if gw_sku and not product:
                self.stdout.write(
                    self.style.WARNING(f'  [skip]    {label} (SKU {gw_sku} not found in DB)')
                )
                skipped_count += 1
                continue

            unit = UnitType.objects.filter(name=label, faction=orks_faction).first()

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
                        faction=orks_faction,
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
