"""
Management command: seed_genestealer_cults_points

Sets points_cost, category, and active status on UnitType records for
Genestealer Cults units, using official 11th Edition data sourced from
the BSData community BattleScribe project (github.com/BSData/wh40k-11e),
the same data New Recruit itself is built on.

Usage:
    python manage.py seed_genestealer_cults_points
    python manage.py seed_genestealer_cults_points --dry-run

The command is fully idempotent -- safe to re-run. It looks up each unit by
(name, faction) -- the same pair UnitType enforces uniqueness on.

Notes:
- Source: "Genestealer Cults.json" -- 62 own sharedSelectionEntries plus
  156 entryLinks. Only 29 of those entryLinks resolve against GSC's own
  entries; the other 127 point into the external "Imperium - Astra
  Militarum - Library" catalogue (Leman Russ variants, Baneblade,
  Chimera, etc. -- lore-accurate "Brood Brothers" allied includes). None
  of those have a GSC-specific product in our catalog (they're the same
  generic Guard vehicles already covered under Astra Militarum's own
  faction), so -- same precedent as Agents of the Imperium/CSM (only
  cross-link when there's an actual product to link to) -- they are
  intentionally NOT onboarded here. User confirmed 2026-08-07.
- Old 10th Edition file used placeholder SKUs (51-01 through 51-18) that
  never existed as real products -- every row silently skipped, every
  time it ran. Rebuilt entirely from the live product catalog (GC-xxx +
  the real 51-xx line).
- Only 8 UnitType rows existed before this pass (Aberrants, Acolyte
  Hybrids x2 builds, Magus, Neophyte Hybrids, Patriarch, Primus, plus an
  inactive Combat Patrol bundle) despite a rich 18-product GC-xxx line
  already in the catalog -- most of the roster is a fresh create.
- 'Codex: Genestealer Cults' (GC-001) and 'Genestealer Cults Combat
  Patrol' (51-69, already inactive) are book/bundle SKUs -- no unit
  created for either.
- 'Purestrain Genestealers' and 'Achilles Ridgerunners' use BSData's
  literal plural/full names, differing slightly from their product's
  display name ('Genestealers' / 'Achilles Ridgerunner') -- both are
  brand-new rows, so BSData's own naming is used directly (consistent
  with every other faction's brand-new creates this project).
"""

from django.core.management.base import BaseCommand

from calculators.models import UnitType
from products.models import Faction, Product

# ---------------------------------------------------------------------------
# Unit data: (gw_sku, points_cost, category, name)
# ---------------------------------------------------------------------------
GENESTEALER_CULTS_UNITS = [
    ('51-44', 140, 'infantry', 'Aberrants'),
    ('GC-004', 85, 'character', 'Abominant'),
    ('GC-016', 95, 'vehicle', 'Achilles Ridgerunners'),
    ('51-41', 70, 'battleline', 'Acolyte Hybrids with Autopistols'),
    ('51-41', 75, 'battleline', 'Acolyte Hybrids with Hand Flamers'),
    ('GC-012', 50, 'character', 'Acolyte Iconward'),
    ('GC-006', 85, 'mounted', 'Atalan Jackals'),
    ('GC-014', 75, 'character', 'Benefictus'),
    ('GC-005', 50, 'character', 'Biophagus'),
    ('GC-018', 50, 'character', 'Clamavus'),
    ('GC-010', 120, 'vehicle', 'Goliath Rockgrinder'),
    ('GC-011', 75, 'transport', 'Goliath Truck'),
    ('GC-013', 75, 'infantry', 'Hybrid Metamorphs'),
    ('GC-017', 55, 'character', 'Jackal Alphus'),
    ('GC-003', 60, 'character', 'Kelermorph'),
    ('GC-008', 35, 'character', 'Locus'),
    ('51-43', 50, 'character', 'Magus'),
    ('51-40', 70, 'battleline', 'Neophyte Hybrids'),
    ('GC-007', 60, 'character', 'Nexos'),
    ('51-42', 80, 'character', 'Patriarch'),
    ('51-42', 70, 'character', 'Primus'),
    ('GC-015', 75, 'infantry', 'Purestrain Genestealers'),
    ('GC-002', 70, 'character', 'Reductus Saboteur'),
    ('GC-009', 65, 'character', 'Sanctus'),
]


class Command(BaseCommand):
    """
    Seed 11th Edition points, category, and active status for Genestealer
    Cults units.

    Looks up each unit by (name, faction) and updates points_cost, category,
    and is_active in place; creates the row if it doesn't exist yet (linking
    the product by gw_sku when one is given). Idempotent -- safe to re-run.
    """

    help = 'Seed 11th Edition points and categories for Genestealer Cults units.'

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
            'Seeding Genestealer Cults points (11th Edition)' + (' [DRY RUN]' if dry_run else '') + '…\n'
        )

        fac = Faction.objects.filter(name='Genestealer Cults').first()
        if not fac:
            self.stdout.write(self.style.ERROR(
                'Genestealer Cults faction not found. Run populate_products first.'
            ))
            return

        updated_count = 0
        created_count = 0
        skipped_count = 0

        for gw_sku, points, category, label in GENESTEALER_CULTS_UNITS:
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
