"""
Management command: seed_imperial_knights_points

Sets points_cost, category, and active status on UnitType records for
Imperial Knights units, using official 11th Edition data sourced from
the BSData community BattleScribe project (github.com/BSData/wh40k-11e),
the same data New Recruit itself is built on.

Usage:
    python manage.py seed_imperial_knights_points
    python manage.py seed_imperial_knights_points --dry-run

The command is fully idempotent -- safe to re-run. It looks up each unit by
(name, faction) -- the same pair UnitType enforces uniqueness on.

Notes:
- Source: "Imperium - Imperial Knights.json" roster (0 own entries, 8
  entryLinks) resolved against "Imperium - Imperial Knights - Library.json"
  (44 entries) -- same split-file pattern as Aeldari/Drukhari/Astra
  Militarum. The roster also links a handful of Adeptus Mechanicus
  Skitarii units (Tech-Priest Manipulus/Dominus, Skitarii Marshal/
  Rangers/Vanguard) as legal allied includes -- intentionally out of
  scope here, same precedent as Genestealer Cults' Astra Militarum
  "Brood Brothers" links (no Imperial-Knights-specific product for any
  of them).
- Old 10th Edition file used placeholder SKUs (54-23 through 54-28) for
  5 units that turned out to already be real products in the catalog --
  just tagged under a different faction (see below).
- **5 cross-faction shared-SKU links, user confirmed 2026-08-07**: Acastus
  Knight Asterius/Porphyrion, Cerastus Knight Atrapos, Questoris Knight
  Magaera/Styrix all have real products already in the catalog
  (CK-013/014/016/017/018) -- but tagged to the `Chaos Knights` faction,
  literally named "Chaos Acastus Knight Asterius" etc. GW sells the same
  physical kit buildable as either loyalist or Chaos. Neither faction had
  a calculator row for these before this pass. User approved cross-
  linking Imperial Knights to these Chaos-Knights-tagged products despite
  the product name, same mechanism as every other cross-faction shared-
  SKU link this project.
- **Armiger Moirax** (150pts, Vehicle) and **Knight Destrier** (265pts,
  Character) have no product anywhere in the catalog -- added to the
  project backlog, not created here. User confirmed 2026-08-07.
- Multi-build kits (all pre-existing, confirmed correct before this pass):
  54-15 builds Knight Preceptor/Canis Rex, 54-20 builds Armiger Warglaive/
  Helverin, 54-21 builds Knight Castellan/Valiant, 54-22 builds Knight
  Errant/Gallant/Paladin/Warden/Crusader/Defender (six-way, largest
  fan-out after the Leman Russ 8-way and Deathwatch Kill Team 6-way).
"""

from django.core.management.base import BaseCommand

from calculators.models import UnitType
from products.models import Faction, Product

# ---------------------------------------------------------------------------
# Unit data: (gw_sku, points_cost, category, name)
# ---------------------------------------------------------------------------
IMPERIAL_KNIGHTS_UNITS = [
    ('54-15', 415, 'epic_hero', 'Canis Rex'),
    ('54-15', 365, 'character', 'Knight Preceptor'),
    ('54-20', 140, 'vehicle', 'Armiger Helverin'),
    ('54-20', 140, 'vehicle', 'Armiger Warglaive'),
    ('54-21', 425, 'character', 'Knight Castellan'),
    ('54-21', 400, 'character', 'Knight Valiant'),
    ('54-22', 395, 'character', 'Knight Crusader'),
    ('54-22', 400, 'character', 'Knight Defender'),
    ('54-22', 355, 'character', 'Knight Errant'),
    ('54-22', 355, 'character', 'Knight Gallant'),
    ('54-22', 375, 'character', 'Knight Paladin'),
    ('54-22', 375, 'character', 'Knight Warden'),
    ('31-06', 415, 'character', 'Cerastus Knight Lancer'),
    ('31-66', 380, 'character', 'Cerastus Knight Castigator'),
    ('31-67', 380, 'character', 'Cerastus Knight Acheron'),
    # -- Cross-faction (share products tagged to Chaos Knights) --
    ('CK-016', 785, 'vehicle', 'Acastus Knight Asterius'),
    ('CK-017', 725, 'vehicle', 'Acastus Knight Porphyrion'),
    ('CK-018', 405, 'character', 'Cerastus Knight Atrapos'),
    ('CK-013', 385, 'character', 'Questoris Knight Magaera'),
    ('CK-014', 375, 'character', 'Questoris Knight Styrix'),
]


class Command(BaseCommand):
    """
    Seed 11th Edition points, category, and active status for Imperial
    Knights units.

    Looks up each unit by (name, faction) and updates points_cost, category,
    and is_active in place; creates the row if it doesn't exist yet (linking
    the product by gw_sku when one is given). Idempotent -- safe to re-run.
    """

    help = 'Seed 11th Edition points and categories for Imperial Knights units.'

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
            'Seeding Imperial Knights points (11th Edition)' + (' [DRY RUN]' if dry_run else '') + '…\n'
        )

        fac = Faction.objects.filter(name='Imperial Knights').first()
        if not fac:
            self.stdout.write(self.style.ERROR(
                'Imperial Knights faction not found. Run populate_products first.'
            ))
            return

        updated_count = 0
        created_count = 0
        skipped_count = 0

        for gw_sku, points, category, label in IMPERIAL_KNIGHTS_UNITS:
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
