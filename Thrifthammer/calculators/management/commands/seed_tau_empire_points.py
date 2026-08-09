"""
Management command: seed_tau_empire_points

Sets points_cost, category, and active status on UnitType records for
T'au Empire units, using official 11th Edition data sourced from the
BSData community BattleScribe project (github.com/BSData/wh40k-11e), the
same data New Recruit itself is built on.

Usage:
    python manage.py seed_tau_empire_points
    python manage.py seed_tau_empire_points --dry-run

The command is fully idempotent -- safe to re-run. It looks up each unit by
(name, faction) -- the same pair UnitType enforces uniqueness on.

Notes:
- Source: "T'au Empire.json" -- self-contained (144 own
  sharedSelectionEntries, 67/69 entryLinks resolve against its own
  entries). 43 real 11e units.
- Superseded the older `seed_tau_points` command (different command
  name, still present, not deleted).
- Only 11 UnitType rows existed before this pass despite a rich
  37-product TE-xxx line already in the catalog -- the other 32 units
  are fresh creates.
- **Tiger Shark 2-way multi-build split** (`TE-030`, "Tiger Shark
  AX-1-0"): "Tiger Shark" (375pts) and "AX-1-0 Tiger Shark" (315pts) are
  two distinct BSData units built from the same physical dual-build kit.
  User confirmed 2026-08-08.
- **Commander 2-way multi-build split** (`TE-009`, generic "T'au Empire
  Commander"): "Commander in Coldstar Battlesuit" (95pts) and "Commander
  in Enforcer Battlesuit" (80pts) share the same kit. User confirmed
  2026-08-08.
- **Ta'unar Supremacy Armour** (790pts, Vehicle) -- confirmed real unit,
  but the only 5 candidate products in the catalog (`TE-011`, `TE-012`,
  `TE-031`, `TE-032`, `TE-033`) are all weapon-swap accessory sprues
  ($64-124 MSRP each), not the actual ~$700+ body kit -- no real body
  product exists in the catalog at all. Added to the backlog instead of
  linking to a mismatched accessory SKU. User confirmed 2026-08-08.
- **Tidewall Gunrig** (90pts, Fortification) has no product anywhere --
  added to the backlog.
- Data-integrity note (not acted on): Fire Warriors has 3 near-duplicate
  products (`56-06`, `TE-007`, `TE-008`) all pointing to essentially the
  same real kit with nearly identical pricing -- Breacher Team/Strike
  Team keep using the pre-existing `56-06` link; flagged to user, no
  action taken.
"""

from django.core.management.base import BaseCommand

from calculators.models import UnitType
from products.models import Faction, Product

# ---------------------------------------------------------------------------
# Unit data: (gw_sku, points_cost, category, name)
# ---------------------------------------------------------------------------
TAU_EMPIRE_UNITS = [
    ('56-06', 90, 'battleline', 'Breacher Team'),
    ('56-13', 75, 'vehicle', 'Broadside Battlesuits'),
    ('56-15', 100, 'vehicle', 'Crisis Fireknife Battlesuits'),
    ('56-15', 90, 'vehicle', 'Crisis Starscythe Battlesuits'),
    ('56-15', 125, 'vehicle', 'Crisis Sunforge Battlesuits'),
    ('56-22', 50, 'character', 'Ethereal'),
    ('56-10', 150, 'vehicle', 'Hammerhead Gunship'),
    ('56-19', 85, 'infantry', 'Pathfinder Team'),
    ('56-16', 190, 'vehicle', 'Riptide Battlesuit'),
    ('56-14', 100, 'infantry', 'Stealth Battlesuits'),
    ('56-06', 70, 'battleline', 'Strike Team'),
    ('TE-001', 85, 'fortification', 'Tidewall Shieldline'),
    ('TE-002', 45, 'monster', 'Kroot Hounds'),
    ('TE-003', 220, 'epic_hero', 'The Twin Lance'),
    ('TE-004', 70, 'epic_hero', 'Commander Farsight'),
    ('TE-005', 60, 'epic_hero', 'Darkstrider'),
    ('TE-006', 100, 'epic_hero', 'Commander Shadowsun'),
    ('TE-009', 95, 'character', 'Commander in Coldstar Battlesuit'),
    ('TE-009', 80, 'character', 'Commander in Enforcer Battlesuit'),
    ('TE-010', 50, 'character', 'Cadre Fireblade'),
    ('TE-013', 85, 'fortification', 'Tidewall Droneport'),
    ('TE-015', 150, 'vehicle', 'Ghostkeel Battlesuit'),
    ('TE-016', 375, 'vehicle', 'Stormsurge'),
    ('TE-017', 160, 'vehicle', 'Razorshark Strike Fighter'),
    ('TE-018', 140, 'vehicle', 'Sky Ray Gunship'),
    ('TE-019', 150, 'vehicle', 'Sun Shark Bomber'),
    ('TE-020', 75, 'transport', 'Devilfish'),
    ('TE-021', 75, 'infantry', 'Kroot Farstalkers'),
    ('TE-022', 70, 'infantry', 'Vespid Stingwings'),
    ('TE-023', 80, 'character', 'Kroot Lone-spear'),
    ('TE-024', 50, 'character', 'Kroot Trail Shaper'),
    ('TE-025', 45, 'character', 'Kroot Flesh Shaper'),
    ('TE-026', 60, 'character', 'Kroot War Shaper'),
    ('TE-027', 45, 'mounted', 'Krootox Riders'),
    ('TE-028', 85, 'mounted', 'Krootox Rampagers'),
    ('TE-030', 375, 'vehicle', 'Tiger Shark'),
    ('TE-030', 315, 'vehicle', 'AX-1-0 Tiger Shark'),
    ('TE-034', 2100, 'vehicle', 'Manta'),
    ('TE-035', 55, 'character', 'Firesight Team'),
    ('TE-036', 65, 'vehicle', 'Piranhas'),
    ('TE-037', 65, 'infantry', 'Kroot Carnivores'),
]


class Command(BaseCommand):
    """
    Seed 11th Edition points, category, and active status for T'au Empire
    units.

    Looks up each unit by (name, faction) and updates points_cost, category,
    and is_active in place; creates the row if it doesn't exist yet (linking
    the product by gw_sku when one is given). Idempotent -- safe to re-run.
    """

    help = "Seed 11th Edition points and categories for T'au Empire units."

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
            "Seeding T'au Empire points (11th Edition)" + (' [DRY RUN]' if dry_run else '') + '…\n'
        )

        fac = Faction.objects.filter(name="T'au Empire").first()
        if not fac:
            self.stdout.write(self.style.ERROR(
                "T'au Empire faction not found. Run populate_products first."
            ))
            return

        updated_count = 0
        created_count = 0
        skipped_count = 0

        for gw_sku, points, category, label in TAU_EMPIRE_UNITS:
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
