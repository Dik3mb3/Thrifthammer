"""
Management command: seed_leagues_of_votann_points

Sets points_cost, category, and active status on UnitType records for
Leagues of Votann units, using official 11th Edition data sourced from
the BSData community BattleScribe project (github.com/BSData/wh40k-11e),
the same data New Recruit itself is built on.

Usage:
    python manage.py seed_leagues_of_votann_points
    python manage.py seed_leagues_of_votann_points --dry-run

The command is fully idempotent -- safe to re-run. It looks up each unit by
(name, faction) -- the same pair UnitType enforces uniqueness on.

Notes:
- Source: "Leagues of Votann.json" -- self-contained (46 own
  sharedSelectionEntries). Old 10th Edition file used placeholder SKUs
  (73-01 through 73-21) that never existed as real products -- every row
  silently skipped, every time it ran. Rebuilt entirely from the live
  product catalog.
- **Real data bug fixed**: the pre-existing 'Berehk Stornbrow' row was
  wrongly linked to the Arkanyst Evaluator product (both shared SKU
  P-222999-99120118025). Its own real product (P-240930-99120118028) had
  zero calculator rows pointing to it. Fixed by relinking. User confirmed
  2026-08-07.
- **'Ironkin Steeljacks' 2-way multi-build split** (P-223001-99120118020):
  BSData now defines "with Heavy Volkanite Disintegrators" and "with
  Melee Weapons" separately (both 80pts) instead of one generic unit.
  User confirmed 2026-08-07. The original unified-name row is deactivated
  (same standing check as CSM's Predator/Daemon Prince split -- caught by
  inspecting the DB directly after the first real run, since it would
  otherwise linger as a stale 3rd row on the same SKU).
- **'Hernkyn Yaegirs' renamed and reactivated** from
  'Kill Team: Hernkyn Yaegirs (Leagues of Votann)' -- same product
  (P-189754-99120118018), exact points/category match (90pts/infantry).
  User confirmed 2026-08-07.
- **Kapricus split**: the old combined 'Kapricus Defender/Carrier' row
  is renamed to 'Kapricus Carrier' (70pts, transport -- BSData's only
  priced Kapricus entry). 'Kapricus Defenders' (65pts, Vehicle) is a
  separate new row sharing the same SKU (P-223006-99120118022, the same
  physical dual-build kit) -- BSData has no costs value for it (same
  situation as Aeldari's Starfangs/Space Marines' Firestrike
  Servo-Turrets), so 65pts is user-supplied from an in-game army-builder
  screenshot, not extracted from BSData. Confirmed 2026-08-07.
- 'Codex: Leagues of Votann' and 'Leagues of Votann Combat Patrol' are
  book/bundle SKUs, already correctly inactive -- left untouched.
  'Kill Team: Hearthkyn Salvagers (Leagues of Votann)' has no entry
  anywhere in the current 11e BSData file at all -- left untouched
  (already correctly inactive).
"""

from django.core.management.base import BaseCommand

from calculators.models import UnitType
from products.models import Faction, Product

# ---------------------------------------------------------------------------
# Renames applied first: (old_name, new_name)
# ---------------------------------------------------------------------------
LEAGUES_OF_VOTANN_RENAMES = [
    ('Kill Team: Hernkyn Yaegirs (Leagues of Votann)', 'Hernkyn Yaegirs'),
    ('Kapricus Defender/Carrier', 'Kapricus Carrier'),
]

# ---------------------------------------------------------------------------
# Original unified-name row from the Ironkin Steeljacks split -- deactivated
# so it doesn't linger alongside the two new split rows on the same SKU.
# Same class of gap as CSM's Predator/Daemon Prince split (caught the same
# way: the old name would otherwise show up as a 3rd, stale entry).
# ---------------------------------------------------------------------------
LEAGUES_OF_VOTANN_DEACTIVATE = [
    'Ironkin Steeljacks',
]

# ---------------------------------------------------------------------------
# Unit data: (gw_sku, points_cost, category, name)
# ---------------------------------------------------------------------------
LEAGUES_OF_VOTANN_UNITS = [
    ('P-222999-99120118025', 70, 'character', 'Arkanyst Evaluator'),
    ('P-240930-99120118028', 85, 'epic_hero', 'Berehk Stornbrow'),
    ('prod5000444-99120118010', 70, 'character', 'Brokhyr Iron-master'),
    ('prod5000439-99120118005', 80, 'infantry', 'Brokhyr Thunderkyn'),
    ('P-223003-99120118019', 85, 'epic_hero', 'Buri Aegnirssen'),
    ('prod5000436-99120118002', 100, 'infantry', 'Cthonian Berserks'),
    ('P-223004-99120118021', 110, 'infantry', 'Cthonian Earthshakers'),
    ('73-06', 65, 'character', 'Einhyr Champion'),
    ('73-14', 130, 'infantry', 'Einhyr Hearthguard'),
    ('prod5000438-99120118004', 65, 'character', 'Grimnyr'),
    ('73-10', 100, 'battleline', 'Hearthkyn Warriors'),
    ('prod5000440-99120118006', 250, 'vehicle', 'Hekaton Land Fortress'),
    ('73-12', 80, 'mounted', 'Hernkyn Pioneers'),
    ('P-189754-99120118018', 90, 'infantry', 'Hernkyn Yaegirs'),
    ('P-223001-99120118020', 80, 'infantry', 'Ironkin Steeljacks with Heavy Volkanite Disintegrators'),
    ('P-223001-99120118020', 80, 'infantry', 'Ironkin Steeljacks with Melee Weapons'),
    ('prod5000456-99120118011', 65, 'character', 'Kahl'),
    ('P-223006-99120118022', 70, 'transport', 'Kapricus Carrier'),
    ('P-223006-99120118022', 65, 'vehicle', 'Kapricus Defenders'),
    ('P-222997-99120118026', 45, 'character', 'Memnyr Strategist'),
    ('prod5000437-99120118003', 85, 'transport', 'Sagitaur'),
    ('prod5000445-99120118011', 90, 'epic_hero', 'Uthar the Destined'),
]


class Command(BaseCommand):
    """
    Seed 11th Edition points, category, and active status for Leagues of
    Votann units.

    Looks up each unit by (name, faction) and updates points_cost, category,
    and is_active in place; creates the row if it doesn't exist yet (linking
    the product by gw_sku when one is given). Idempotent -- safe to re-run.
    """

    help = 'Seed 11th Edition points and categories for Leagues of Votann units.'

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
            'Seeding Leagues of Votann points (11th Edition)' + (' [DRY RUN]' if dry_run else '') + '…\n'
        )

        fac = Faction.objects.filter(name='Leagues of Votann').first()
        if not fac:
            self.stdout.write(self.style.ERROR(
                'Leagues of Votann faction not found. Run populate_products first.'
            ))
            return

        for old_name, new_name in LEAGUES_OF_VOTANN_RENAMES:
            unit = UnitType.objects.filter(name=old_name, faction=fac).first()
            if unit:
                self.stdout.write(f'  [rename] {old_name!r} -> {new_name!r}')
                if not dry_run:
                    unit.name = new_name
                    unit.save(update_fields=['name'])

        for name in LEAGUES_OF_VOTANN_DEACTIVATE:
            unit = UnitType.objects.filter(name=name, faction=fac).first()
            if unit and unit.is_active:
                self.stdout.write(f'  [deactivate] {name!r}')
                if not dry_run:
                    unit.is_active = False
                    unit.save(update_fields=['is_active'])

        updated_count = 0
        created_count = 0
        skipped_count = 0

        for gw_sku, points, category, label in LEAGUES_OF_VOTANN_UNITS:
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
                if product and unit.product_id != product.id:
                    changes.append(f'product {unit.product_id}->{product.id}')
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
