"""
Management command: seed_custodes_points

Sets points_cost, category, and active status on UnitType records for
Adeptus Custodes units, using official 11th Edition data sourced from the
BSData community BattleScribe project (github.com/BSData/wh40k-11e), the
same data New Recruit itself is built on.

Usage:
    python manage.py seed_custodes_points

The command is fully idempotent -- safe to re-run. It looks up each unit by
(name, faction) -- the same pair UnitType enforces uniqueness on.

Notes:
- Custodes has no parent faction and its BSData file is self-contained (45
  entries), same shape as Space Marines/Chaos Space Marines, not a
  chapter-style thin overlay.
- Two multi-build splits:
    * 'Contemptor Dreadnought' (AC-006) -> 3 units share this one SKU:
      Contemptor-Achillus Dreadnought (155pts), Contemptor-Galatus
      Dreadnought (165pts), Venerable Contemptor Dreadnought (170pts).
    * 'Telemon Heavy Dreadnought' -> linked to AC-026 ("...Body") only.
      Three more Telemon-related products (AC-013/024/025) are weapon-
      loadout accessory SKUs, not separate purchasable units -- not
      modeled as their own calculator rows. User confirmed 2026-08-07.
- 'Shield-Captain (Legio Custodes)' is a second, distinctly-named row on
  AC-023 -- a newer release of the same 110pt BSData unit as the existing
  'Shield-Captain' row (01-07). Kept as two separate rows rather than one,
  per user direction 2026-08-07.
- 'Aquilon Custodians' links to AC-017 only; AC-018 ("...with Infernus
  Firepikes") is not modeled as a second build variant, per user
  direction.
- 'Talons of the Emperor' (AC-012) is a genuine dual-character box --
  Valerian (110pts, Epic Hero) and Aleya (55pts, Epic Hero) both share
  this one SKU, same "dual-unit box" pattern as Agents of the Imperium's
  Rogue Trader Entourage/Voidsmen-at-Arms.
- Two cross-faction shared-SKU links to existing Space Marines products
  (same physical kit): 'Venerable Land Raider' -> 48-119 (Land Raider
  Redeemer), 'Anathema Psykana Rhino' -> 48-128 (plain Rhino). User
  confirmed 2026-08-07.
- Units confirmed real in 11e with no matching product anywhere in the
  catalog (Agamatus Custodians, Sagittarum Custodians, Knight-Centura,
  Shield-Captain in Allarus Terminator Armour, Shield-Captain on Dawneagle
  Jetbike) are tracked in memory/project_11e_calculator_migration.md, not
  fabricated here.
"""

from django.core.management.base import BaseCommand

from calculators.models import UnitType
from products.models import Faction, Product

# ---------------------------------------------------------------------------
# Unit data: (gw_sku, points_cost, category, name)
# ---------------------------------------------------------------------------
CUSTODES_UNITS = [
    ('AC-012', 55, 'epic_hero', 'Aleya'),
    ('AC-002', 110, 'infantry', 'Allarus Custodians'),
    ('48-128', 65, 'transport', 'Anathema Psykana Rhino'),
    ('AC-017', 195, 'infantry', 'Aquilon Custodians'),
    ('AC-019', 580, 'vehicle', 'Ares Gunship'),
    ('AC-003', 110, 'character', 'Blade Champion'),
    ('AC-005', 210, 'vehicle', 'Caladius Grav-tank'),
    ('AC-006', 155, 'vehicle', 'Contemptor-Achillus Dreadnought'),
    ('AC-006', 165, 'vehicle', 'Contemptor-Galatus Dreadnought'),
    ('AC-007', 180, 'vehicle', 'Coronus Grav-carrier'),
    ('01-08', 170, 'battleline', 'Custodian Guard'),
    ('01-08', 250, 'infantry', 'Custodian Guard with Adrasite and Pyrithite spears'),
    ('01-10', 200, 'infantry', 'Custodian Wardens'),
    ('AC-021', 690, 'vehicle', 'Orion Assault Dropship'),
    ('AC-022', 100, 'vehicle', 'Pallas Grav-attack'),
    ('AC-010', 45, 'infantry', 'Prosecutors'),
    ('01-07', 110, 'character', 'Shield-Captain'),
    ('AC-023', 110, 'character', 'Shield-Captain (Legio Custodes)'),
    ('AC-026', 225, 'vehicle', 'Telemon Heavy Dreadnought'),
    ('01-02', 135, 'epic_hero', 'Trajann Valoris'),
    ('AC-012', 110, 'epic_hero', 'Valerian'),
    ('AC-014', 150, 'infantry', 'Venatari Custodians'),
    ('AC-006', 170, 'vehicle', 'Venerable Contemptor Dreadnought'),
    ('48-119', 220, 'vehicle', 'Venerable Land Raider'),
    ('01-11', 145, 'mounted', 'Vertus Praetors'),
    ('AC-015', 50, 'infantry', 'Vigilators'),
    ('AC-016', 50, 'infantry', 'Witchseekers'),
]


class Command(BaseCommand):
    """
    Seed 11th Edition points, category, and active status for Adeptus
    Custodes units.

    Looks up each unit by (name, faction) and updates points_cost, category,
    and is_active in place; creates the row if it doesn't exist yet (linking
    the product by gw_sku when one is given). Idempotent -- safe to re-run.
    """

    help = 'Seed 11th Edition points and categories for Adeptus Custodes units.'

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
            'Seeding Custodes points (11th Edition)' + (' [DRY RUN]' if dry_run else '') + '\u2026\n'
        )

        fac = Faction.objects.filter(name='Custodes').first()
        if not fac:
            self.stdout.write(self.style.ERROR(
                'Custodes faction not found. Run populate_products first.'
            ))
            return

        updated_count = 0
        created_count = 0
        skipped_count = 0

        for gw_sku, points, category, label in CUSTODES_UNITS:
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
