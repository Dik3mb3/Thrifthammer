"""
Management command: seed_necrons_points

Sets points_cost, category, and active status on UnitType records for
Necrons units, using official 11th Edition data sourced from the BSData
community BattleScribe project (github.com/BSData/wh40k-11e), the same
data New Recruit itself is built on.

Usage:
    python manage.py seed_necrons_points
    python manage.py seed_necrons_points --dry-run

The command is fully idempotent -- safe to re-run. It looks up each unit by
(name, faction) -- the same pair UnitType enforces uniqueness on.

Notes:
- Source: "Necrons.json" -- self-contained (84 own sharedSelectionEntries,
  only linked to "Unaligned Forces"). 52 real 11e units.
- **PRODUCT_OVERRIDES**: 3 SKU strings are shared by TWO distinct Product
  rows in our catalog (a pre-existing data quirk, confirmed as legitimate
  dual-build GW kits during a full-catalog sweep 2026-08-08, not a bug --
  same pattern as Vyper/Starfang, Maulerfiend/Forgefiend, etc.):
    prod4390158 -> "Annihilation Barge" (id 608) / "Necron Catacomb
      Command Barge" (id 607)
    prod3590140 -> "Obelisk & Transcendent C'tan" (id 611, the combo box
      that builds BOTH Obelisk and Transcendent C'tan) / "Tesseract
      Vault" (id 612, a separate box)
  A plain gw_sku lookup (`Product.objects.filter(gw_sku=X).first()`) is
  non-deterministic between the two rows for these SKUs, so this command
  resolves them by exact product PK instead, to avoid silently linking a
  unit to the wrong Product row.
- **'Codex: Necrons' (49-23) removed from the calculator** per explicit
  user instruction 2026-08-08 -- deactivated, not deleted.
- **Renames**: 'Lokhust Destroyer Squadron'->'Lokhust Destroyers',
  'Lokhust Heavy Destroyer'->'Lokhust Heavy Destroyers' (BSData plurals).
  'Overlord with Tachyon Arrow'->'Overlord with Translocation Shroud' --
  BSData no longer has a "Tachyon Arrow" unit variant (now just a weapon
  upgrade option, not a separate unit); "Translocation Shroud" is the
  current real variant, same product SKU (prod4900150).
- **Cryptek specialists**: BSData has 5 named specialists (Chronomancer,
  Geomancer, Plasmancer, Psychomancer, Technomancer). Existing links for
  Chronomancer (its own SKU), Psychomancer (its own SKU), and Plasmancer
  (shares "Necrons Royal Court", prod4900147, with Skorpekh Lord/
  Canoptek Reanimator/Cryptothralls) were left as-is per explicit user
  instruction 2026-08-08 -- Geomancer and Technomancer have no product
  anywhere in the catalog and were NOT linked to Royal Court or the
  unused "Cryptek" product (prod4390141) -- added to the backlog instead.
- 'Convergence of Dominion' has no points value in the current 11e
  BSData file (`costs: null`, same class of gap as Kapricus Defenders) --
  user confirmed keeping the existing stale 60pts rather than guessing.
  Not included in this command's unit list -- its current DB value is
  left untouched entirely.
- 8 units confirmed real in 11e with no product anywhere in the catalog
  (Canoptek Macrocytes, Canoptek Scarab Swarms, Canoptek Tomb Crawlers,
  Geomancer, Lokhust Lord, Seraptek Heavy Construct, Technomancer, Tomb
  Citadel Walls) -- added to the project backlog, not created here.
"""

from django.core.management.base import BaseCommand

from calculators.models import UnitType
from products.models import Faction, Product

# ---------------------------------------------------------------------------
# Renames applied first: (old_name, new_name)
# ---------------------------------------------------------------------------
NECRONS_RENAMES = [
    ('Lokhust Destroyer Squadron', 'Lokhust Destroyers'),
    ('Lokhust Heavy Destroyer', 'Lokhust Heavy Destroyers'),
    ('Overlord with Tachyon Arrow', 'Overlord with Translocation Shroud'),
]

# ---------------------------------------------------------------------------
# Rows removed from the calculator -- deactivated, not deleted.
# ---------------------------------------------------------------------------
NECRONS_DEACTIVATE = [
    'Codex: Necrons',
    # Stale generic unit -- superseded by the 5 named Cryptek specialists
    # (Chronomancer, Geomancer, Plasmancer, Psychomancer, Technomancer) in
    # 11e. Doesn't match any current BSData unit. Caught via direct DB
    # inspection after the first real run (same standing check as CSM's
    # Predator/Daemon Prince split). User confirmed 2026-08-08.
    'Cryptek',
]

# ---------------------------------------------------------------------------
# Explicit product PK overrides for units whose gw_sku is shared by two
# distinct Product rows (see docstring). Checked before the normal
# gw_sku-based lookup.
# ---------------------------------------------------------------------------
PRODUCT_PK_OVERRIDES = {
    'Annihilation Barge': 608,
    'Catacomb Command Barge': 607,
    'Obelisk': 611,
    'Transcendent C\'tan': 611,
    'Tesseract Vault': 612,
}

# ---------------------------------------------------------------------------
# Unit data: (gw_sku, points_cost, category, name)
# ---------------------------------------------------------------------------
NECRONS_UNITS = [
    ('prod4390158', 95, 'vehicle', 'Annihilation Barge'),
    ('prod2901178', 330, 'epic_hero', "C'tan Shard of the Deceiver"),
    ('P-241016', 360, 'epic_hero', "C'tan Shard of the Nightbringer"),
    ('49-20', 345, 'epic_hero', "C'tan Shard of the Void Dragon"),
    ('prod4390146', 140, 'vehicle', 'Canoptek Doomstalker'),
    ('prod4900147', 75, 'vehicle', 'Canoptek Reanimator'),
    ('49-14', 65, 'vehicle', 'Canoptek Spyders'),
    ('prod4390999', 95, 'monster', 'Canoptek Wraiths'),
    ('prod4390158', 120, 'character', 'Catacomb Command Barge'),
    ('prod4900148', 70, 'character', 'Chronomancer'),
    ('prod4900147', 60, 'infantry', 'Cryptothralls'),
    ('prod4390142', 60, 'infantry', 'Deathmarks'),
    ('49-13', 200, 'vehicle', 'Doom Scythe'),
    ('49-12', 210, 'vehicle', 'Doomsday Ark'),
    ('49-17', 55, 'infantry', 'Flayed Ones'),
    ('prod4390998', 100, 'transport', 'Ghost Ark'),
    ('prod4390148', 75, 'character', 'Hexmark Destroyer'),
    ('prod4390160', 175, 'epic_hero', 'Illuminor Szeras'),
    ('49-10', 70, 'battleline', 'Immortals'),
    ('prod4900149', 100, 'epic_hero', 'Imotekh the Stormlord'),
    ('prod4390155', 40, 'mounted', 'Lokhust Destroyers'),
    ('prod4390145', 50, 'mounted', 'Lokhust Heavy Destroyers'),
    ('49-11', 80, 'infantry', 'Lychguard'),
    ('49-08', 420, 'vehicle', 'Monolith'),
    ('49-06', 80, 'battleline', 'Necron Warriors'),
    ('P-241017', 185, 'epic_hero', 'Nekrosor Ammentar'),
    ('prod4390159', 125, 'vehicle', 'Night Scythe'),
    ('prod3590140', 280, 'vehicle', 'Obelisk'),
    ('prod4390154', 80, 'infantry', 'Ophydian Destroyers'),
    ('prod4900151', 90, 'epic_hero', 'Orikan the Diviner'),
    ('49-03', 90, 'character', 'Overlord'),
    ('prod4900150', 90, 'character', 'Overlord with Translocation Shroud'),
    ('prod4900147', 55, 'character', 'Plasmancer'),
    ('49-21', 55, 'character', 'Psychomancer'),
    ('49-22', 50, 'character', 'Royal Warden'),
    ('prod4390150', 85, 'infantry', 'Skorpekh Destroyers'),
    ('prod4900147', 90, 'character', 'Skorpekh Lord'),
    ('prod3590140', 465, 'vehicle', 'Tesseract Vault'),
    ('prod4390152', 420, 'epic_hero', 'Szarekh, The Silent King'),
    ('prod3940162', 70, 'mounted', 'Tomb Blades'),
    ('prod3590140', 340, 'character', "Transcendent C'tan"),
    ('prod2791068', 65, 'epic_hero', 'Trazyn the Infinite'),
    ('prod4390144', 80, 'infantry', 'Triarch Praetorians'),
    ('prod4390143', 110, 'vehicle', 'Triarch Stalker'),
]


class Command(BaseCommand):
    """
    Seed 11th Edition points, category, and active status for Necrons
    units.

    Looks up each unit by (name, faction) and updates points_cost, category,
    and is_active in place; creates the row if it doesn't exist yet (linking
    the product by gw_sku, or an explicit PRODUCT_PK_OVERRIDES entry when
    the gw_sku is ambiguous). Idempotent -- safe to re-run.
    """

    help = 'Seed 11th Edition points and categories for Necrons units.'

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
            'Seeding Necrons points (11th Edition)' + (' [DRY RUN]' if dry_run else '') + '…\n'
        )

        fac = Faction.objects.filter(name='Necrons').first()
        if not fac:
            self.stdout.write(self.style.ERROR(
                'Necrons faction not found. Run populate_products first.'
            ))
            return

        for old_name, new_name in NECRONS_RENAMES:
            unit = UnitType.objects.filter(name=old_name, faction=fac).first()
            if unit:
                self.stdout.write(f'  [rename] {old_name!r} -> {new_name!r}')
                if not dry_run:
                    unit.name = new_name
                    unit.save(update_fields=['name'])

        for name in NECRONS_DEACTIVATE:
            unit = UnitType.objects.filter(name=name, faction=fac).first()
            if unit and unit.is_active:
                self.stdout.write(f'  [deactivate] {name!r}')
                if not dry_run:
                    unit.is_active = False
                    unit.save(update_fields=['is_active'])

        updated_count = 0
        created_count = 0
        skipped_count = 0

        for gw_sku, points, category, label in NECRONS_UNITS:
            if label in PRODUCT_PK_OVERRIDES:
                product = Product.objects.filter(id=PRODUCT_PK_OVERRIDES[label]).first()
            else:
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
