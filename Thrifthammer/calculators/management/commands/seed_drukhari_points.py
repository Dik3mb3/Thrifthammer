"""
Management command: seed_drukhari_points

Sets points_cost, category, and active status on UnitType records for
Drukhari units, using official 11th Edition data sourced from the
BSData community BattleScribe project (github.com/BSData/wh40k-11e), the
same data New Recruit itself is built on.

Usage:
    python manage.py seed_drukhari_points
    python manage.py seed_drukhari_points --dry-run

The command is fully idempotent -- safe to re-run. It looks up each unit by
(name, faction) -- the same pair UnitType enforces uniqueness on.

Notes:
- Source: "Aeldari - Drukhari.json" -- a thin roster of entryLinks with no
  sharedSelectionEntries of its own, resolved against the shared
  "Aeldari - Aeldari Library.json" catalogue. Same split-file pattern as
  the Aeldari (Craftworlds) migration.
- The old 10th Edition file used `.filter(product=...).update()` keyed on
  ~34 aspirational `45-xx` SKUs that were never actually onboarded as real
  products (only 45-02/06/07/10/12/25 exist) -- it silently no-op'd for
  almost everything, every time it ran. Rebuilt entirely from the live
  DR-xxx product line + the real 45-xx products.
- Drukhari had only 6 UnitType rows before this pass (Archon, Kabalite
  Warriors, Raider, Ravager, Wyches, plus an inactive Combat Patrol
  bundle) despite an 18-product DR-xxx line existing in the catalog --
  this is mostly fresh creates, not a refresh. Resolves the deferred
  "Drukhari missing UnitType rows" backlog item (Incubi, Reavers,
  Succubus, Venom, plus more that also turned out to have no row).
- 'Codex: Drukhari' (DR-006) and 'Drukhari Combat Patrol' (45-25, already
  inactive) are book/bundle SKUs -- no unit created for either.
- **Scourges 2-way multi-build split** (DR-013, "Drukhari Scourges"):
  Scourges with Heavy Weapons (110pts) / Scourges with Shardcarbines
  (75pts), both Infantry, same SKU. User confirmed 2026-08-07.
- **12 cross-faction shared-SKU rows, user confirmed 2026-08-07**: BSData's
  Drukhari roster also legally includes several Harlequins/Corsair units
  (allied army-list inclusions). All 12 already exist as active,
  correctly-pointed UnitType rows under the Aeldari faction (that
  catalogue covers Craftworlds/Corsairs/Harlequins/Ynnari under one
  book) -- these rows link Drukhari to the *same* products, same
  mechanism as the Ynnari cross-links added during the Aeldari
  migration: Corsair Skyreavers, Corsair Voidreavers, Corsair
  Voidscarred, Death Jester, Kharseth, Prince Yriel, Shadowseer,
  Solitaire, Troupe, Skyweavers, Starweaver, Voidweaver.
- 'Troupe Master' (75pts, Character) is also roster-linked here but has
  no product anywhere in the catalog -- already tracked on Aeldari's
  backlog list, not duplicated here.
"""

from django.core.management.base import BaseCommand

from calculators.models import UnitType
from products.models import Faction, Product

# ---------------------------------------------------------------------------
# Unit data: (gw_sku, points_cost, category, name)
# ---------------------------------------------------------------------------
DRUKHARI_UNITS = [
    # -- Core Drukhari --
    ('45-02', 80, 'character', 'Archon'),
    ('45-07', 110, 'battleline', 'Kabalite Warriors'),
    ('45-10', 75, 'transport', 'Raider'),
    ('45-12', 110, 'vehicle', 'Ravager'),
    ('45-06', 90, 'battleline', 'Wyches'),
    ('DR-001', 80, 'epic_hero', 'Lelith Hesperax'),
    ('DR-002', 85, 'epic_hero', 'Drazhar'),
    ('DR-003', 50, 'character', 'Haemonculus'),
    ('DR-004', 50, 'character', 'Succubus'),
    ('DR-005', 60, 'battleline', 'Wracks'),
    ('DR-007', 90, 'infantry', 'Incubi'),
    ('DR-008', 75, 'monster', 'Talos'),
    ('DR-009', 55, 'monster', 'Cronos'),
    ('DR-010', 65, 'transport', 'Venom'),
    ('DR-011', 245, 'vehicle', 'Voidraven Bomber'),
    ('DR-012', 170, 'vehicle', 'Razorwing Jetfighter'),
    ('DR-013', 110, 'infantry', 'Scourges with Heavy Weapons'),
    ('DR-013', 75, 'infantry', 'Scourges with Shardcarbines'),
    ('DR-014', 115, 'infantry', 'Hand of the Archon'),
    ('DR-015', 80, 'infantry', 'Mandrakes'),
    ('DR-016', 100, 'epic_hero', 'Lady Malys'),
    ('DR-017', 75, 'mounted', 'Reavers'),
    ('DR-018', 90, 'mounted', 'Hellions'),
    # -- Cross-faction Harlequins/Corsairs (share products with Aeldari) --
    ('P-240922', 75, 'infantry', 'Corsair Skyreavers'),
    ('P-240923', 65, 'battleline', 'Corsair Voidreavers'),
    ('P-240923', 70, 'infantry', 'Corsair Voidscarred'),
    ('prod2620120', 70, 'character', 'Death Jester'),
    ('P-240921', 85, 'epic_hero', 'Kharseth'),
    ('P-240880', 95, 'epic_hero', 'Prince Yriel'),
    ('prod2620121', 50, 'character', 'Shadowseer'),
    ('prod2620122', 115, 'epic_hero', 'Solitaire'),
    ('prod3530579', 85, 'infantry', 'Troupe'),
    ('prod2620124', 95, 'mounted', 'Skyweavers'),
    ('prod2600170', 70, 'transport', 'Starweaver'),
    ('prod2780228', 115, 'vehicle', 'Voidweaver'),
]


class Command(BaseCommand):
    """
    Seed 11th Edition points, category, and active status for Drukhari
    units.

    Looks up each unit by (name, faction) and updates points_cost, category,
    and is_active in place; creates the row if it doesn't exist yet (linking
    the product by gw_sku when one is given). Idempotent -- safe to re-run.
    """

    help = 'Seed 11th Edition points and categories for Drukhari units.'

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
            'Seeding Drukhari points (11th Edition)' + (' [DRY RUN]' if dry_run else '') + '…\n'
        )

        fac = Faction.objects.filter(name='Drukhari').first()
        if not fac:
            self.stdout.write(self.style.ERROR(
                'Drukhari faction not found. Run populate_products first.'
            ))
            return

        updated_count = 0
        created_count = 0
        skipped_count = 0

        for gw_sku, points, category, label in DRUKHARI_UNITS:
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
