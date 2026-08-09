"""
Management command: seed_agents_points

Sets points_cost, category, and active status on UnitType records for all
Agents of the Imperium units, using official 11th Edition data sourced from
the BSData community BattleScribe project (github.com/BSData/wh40k-11e),
the same data New Recruit itself is built on.

Usage:
    python manage.py seed_agents_points

The command is fully idempotent -- safe to re-run. It looks up each unit by
(name, faction) -- the same pair UnitType enforces uniqueness on.

Notes:
- This faction had ZERO UnitType rows of any kind before this command --
  the old points file only ever used `.update()` filtered on `product=`,
  which silently did nothing since no rows existed to update. Every row
  below is a fresh `[create]`, not a refresh.
- Agents of the Imperium is a genuinely cross-faction army list by design
  (BSData confirms it in-source: several units carry Agents-specific point
  costs that differ from their home-faction value for the same physical
  kit, e.g. Sisters of Battle Squad is 100pts here vs 105pts under
  Sororitas). Cross-faction units below are new UnitType rows under
  'Agents of the Imperium', sharing gw_sku with the existing product under
  its home faction -- the same "one product, many faction-scoped rows"
  pattern already used for Space Marine chapter squads and (as of
  2026-08-07) the Aeldari/Drukhari Ynnari units. Approved by user
  2026-08-07.
- 'Inquisitor' (the generic, unnamed 55pt Character entry) has no product
  of its own -- per user direction, it reuses the Inquisitor Greyfax
  product (IA-010) as its physical model, giving that one product two
  UnitType rows under the *same* faction: 'Inquisitor Greyfax' (65pts,
  epic_hero) and 'Inquisitor' (55pts, character). Same shared-SKU
  mechanism as the cross-faction case, just within one faction.
- IA-012 ("Rogue Trader Entourage and Voidsmen-at-Arms") is a genuine
  dual-unit box -- one product, two separate UnitType rows (Rogue Trader
  Entourage 75pts Character, Voidsmen-at-Arms 50pts Infantry).
- Product/unit mapping decisions confirmed by user 2026-08-07:
    Imperial Rhino      -> 48-128 "Rhino" (Space Marines)
    Sanctifiers          -> AS-005 "Kill Team: Sanctifiers" (Sisters of
                             Battle), not the untagged KT-005 duplicate
    Ministorum Priest    -> AS-025 "Adepta Sororitas Ministorum Priest"
                             (Sisters of Battle)
    Inquisitorial Chimera -> 47-05 "Astra Militarum Chimera"
- Eisenhorn (product IA-003 already exists in the catalog) is deliberately
  left out entirely -- BSData's only 11e entry for him is
  "Inquisitor Eisenhorn [Legends]", not legal in standard matched play.
  Not a backlog item (the product already exists), just excluded per the
  standard Legends-exclusion rule until/unless he gets a non-Legends
  datasheet.
- Units confirmed real in 11e with NO matching product at all (Aquila Kill
  Team, Subductor Squad, Vigilant Squad) are tracked in
  memory/project_11e_calculator_migration.md, not fabricated here.
"""

from django.core.management.base import BaseCommand

from calculators.models import UnitType
from products.models import Faction, Product

# ---------------------------------------------------------------------------
# Unit data: (gw_sku, points_cost, category, name)
#
# Sourced from BSData/wh40k-11e ("Imperium - Agents of the Imperium.json"),
# 11th Edition. Base points only, no wargear or squad-size modifiers.
# ---------------------------------------------------------------------------
AGENTS_UNITS = [
    # ── Agents-native products (IA-series) ──────────────────────────────────
    ('IA-002', 100, 'epic_hero',  'Inquisitor Kroyle'),
    ('IA-004',  75, 'epic_hero',  'Inquisitor Coteaz'),
    ('IA-005',  60, 'character',  'Navigator'),
    ('IA-006', 100, 'epic_hero',  'Callidus Assassin'),
    ('IA-007', 110, 'epic_hero',  'Vindicare Assassin'),
    ('IA-008',  85, 'epic_hero',  'Culexus Assassin'),
    ('IA-009', 100, 'epic_hero',  'Eversor Assassin'),
    ('IA-010',  65, 'epic_hero',  'Inquisitor Greyfax'),
    ('IA-010',  55, 'character',  'Inquisitor'),  # generic -- reuses Greyfax model, see docstring
    ('IA-011',  75, 'epic_hero',  'Inquisitor Draxus'),
    ('IA-013',  50, 'infantry',   'Inquisitorial Agents'),
    # ── IA-012 dual-unit box ─────────────────────────────────────────────────
    ('IA-012',  75, 'character',  'Rogue Trader Entourage'),
    ('IA-012',  50, 'infantry',   'Voidsmen-at-Arms'),
    # ── Cross-faction shared-SKU units ──────────────────────────────────────
    ('39-01',   65, 'epic_hero',  'Watch Captain Artemis'),     # Deathwatch product
    ('39-02',   95, 'character',  'Watch Master'),              # Deathwatch product
    ('39-10',  100, 'battleline', 'Deathwatch Kill Team'),      # Deathwatch product
    ('39-04',  180, 'vehicle',    'Corvus Blackstar'),          # Deathwatch product
    ('57-08',  175, 'infantry',   'Grey Knights Terminator Squad'),  # Grey Knights product
    ('52-09',   90, 'transport',  'Sisters of Battle Immolator'),    # Sisters of Battle product
    ('52-20',  100, 'infantry',   'Sisters of Battle Squad'),        # Sisters of Battle product
    ('48-128',  65, 'transport',  'Imperial Rhino'),                 # Space Marines product
    ('AS-005', 100, 'infantry',   'Sanctifiers'),                    # Sisters of Battle product
    ('AS-025',  40, 'character',  'Ministorum Priest'),               # Sisters of Battle product
    ('47-05',   60, 'transport',  'Inquisitorial Chimera'),           # Astra Militarum product
]


class Command(BaseCommand):
    """
    Seed 11th Edition points, category, and active status for Agents of the
    Imperium units.

    Looks up each unit by (name, faction) and updates points_cost, category,
    and is_active in place; creates the row if it doesn't exist yet (linking
    the product by gw_sku when one is given). Idempotent -- safe to re-run.
    """

    help = 'Seed 11th Edition points and categories for Agents of the Imperium units.'

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
            'Seeding Agents of the Imperium points (11th Edition)' + (' [DRY RUN]' if dry_run else '') + '…\n'
        )

        fac = Faction.objects.filter(name='Agents of the Imperium').first()
        if not fac:
            self.stdout.write(self.style.ERROR(
                'Agents of the Imperium faction not found. Run populate_products first.'
            ))
            return

        updated_count = 0
        created_count = 0
        skipped_count = 0

        for gw_sku, points, category, label in AGENTS_UNITS:
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
