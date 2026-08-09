"""
Management command: seed_death_guard_points

Sets points_cost, category, and active status on UnitType records for
Death Guard units, using official 11th Edition data sourced from the
BSData community BattleScribe project (github.com/BSData/wh40k-11e), the
same data New Recruit itself is built on.

Usage:
    python manage.py seed_death_guard_points

The command is fully idempotent -- safe to re-run. It looks up each unit by
(name, faction) -- the same pair UnitType enforces uniqueness on.

Notes:
- Death Guard is architecturally different from the loyalist Space Marine
  chapters (Black Templars/Blood Angels/Dark Angels). Its BSData file does
  NOT reference the Chaos Space Marines catalogue at all -- it's fully
  self-contained (91 entries) with its own points AND rules for units that
  look "generic" (Chaos Predator, Chaos Rhino, Chaos Spawn, Chaos Land
  Raider, Defiler, Helbrute), several of which genuinely differ from CSM's
  own values for the identical physical kit (e.g. Chaos Rhino: 75pts here
  vs 65pts under plain CSM; Helbrute: 110pts/vehicle here vs 130pts/
  infantry under CSM). User confirmed 2026-08-07: these are NOT
  deactivate-and-fall-back candidates like the loyalist chapters' generic
  squads -- they get their own Death-Guard-specific points AND datasheets
  (stats/weapons/abilities), same principle applying to every other Chaos
  legion (Emperor's Children, Thousand Sons, World Eaters) still to come.
- All 34 real 11e units already existed as active DB rows with real
  products before this pass -- 0 new creates, 0 deactivations. Just
  point/category refreshes, plus linking 2 rows that had a real product
  but weren't connected yet: 'Lord of Virulence' -> 43-77,
  'Miasmic Malignifier' -> 43-78.
- 'Beasts of Nurgle' and 'Myphitic Blight-hauler' have no independent
  points value in BSData (`costs: null`/`0`), same situation as Aeldari's
  Starfangs. 70pts and 100pts respectively are user-supplied values
  (confirmed 2026-08-07), not extracted from BSData.
- 'Death Guard Plague Marine Champion' (43-48) has no entry anywhere in
  the current 11e file at all, not even Legends-tagged -- left untouched
  (already correctly inactive, 0pts), not fabricated.
"""

from django.core.management.base import BaseCommand

from calculators.models import UnitType
from products.models import Faction, Product

# ---------------------------------------------------------------------------
# Unit data: (gw_sku, points_cost, category, name)
# ---------------------------------------------------------------------------
DEATH_GUARD_UNITS = [
    ('prod3700246-99129915062', 70, 'monster', 'Beasts of Nurgle'),
    ('43-24', 60, 'character', 'Biologus Putrifier'),
    ('43-54', 115, 'infantry', 'Blightlord Terminators'),
    ('99120102052', 220, 'vehicle', 'Chaos Land Raider'),
    ('43-09', 135, 'vehicle', 'Chaos Predator Annihilator'),
    ('43-09', 145, 'vehicle', 'Chaos Predator Destructor'),
    ('99120102092', 75, 'transport', 'Chaos Rhino'),
    ('99120201050', 80, 'monster', 'Chaos Spawn'),
    ('99120201130', 195, 'character', 'Daemon Prince of Nurgle'),
    ('99120201130', 170, 'character', 'Daemon Prince of Nurgle with wings'),
    ('43-56', 160, 'infantry', 'Deathshroud Terminators'),
    ('P-CSM-DEFILER-2026', 300, 'vehicle', 'Defiler'),
    ('43-55', 100, 'vehicle', 'Foetid Bloat-drone'),
    ('43-55', 125, 'vehicle', 'Foetid Bloat-drone with heavy blight launcher'),
    ('43-46', 65, 'character', 'Foul Blightspawn'),
    ('prod3700247-99129915063', 265, 'character', 'Great Unclean One'),
    ('prod2430129-99120102043', 110, 'vehicle', 'Helbrute'),
    ('43-47', 45, 'character', 'Icon Bearer'),
    ('prod4650190-99120102150', 120, 'character', 'Lord of Contagion'),
    ('P-223010-99120102198', 65, 'character', 'Lord of Poxes'),
    ('43-77', 100, 'character', 'Lord of Virulence'),
    ('prod4570149-99120102114', 60, 'character', 'Malignant Plaguecaster'),
    ('43-78', 105, 'fortification', 'Miasmic Malignifier'),
    ('43-03', 390, 'epic_hero', 'Mortarion'),
    ('43-56', 100, 'vehicle', 'Myphitic Blight-hauler'),
    ('prod4570149-99120102114', 60, 'character', 'Noxious Blightbringer'),
    ('prod3550127-99129915060', 45, 'infantry', 'Nurglings'),
    ('prod3610130-99129915038', 110, 'mounted', 'Plague Drones'),
    ('43-50', 90, 'battleline', 'Plague Marines'),
    ('43-29', 50, 'character', 'Plague Surgeon'),
    ('P-NURGLE-PLAGUEBEARERS-40K', 115, 'battleline', 'Plaguebearers'),
    ('43-52', 185, 'vehicle', 'Plagueburst Crawler'),
    ('43-53', 65, 'infantry', 'Poxwalkers'),
    ('prod3700271-99129915063', 280, 'epic_hero', 'Rotigus'),
    ('43-45', 60, 'character', 'Tallyman'),
    ('43-08', 100, 'epic_hero', 'Typhus'),
]


class Command(BaseCommand):
    """
    Seed 11th Edition points, category, and active status for Death Guard
    units.

    Looks up each unit by (name, faction) and updates points_cost, category,
    and is_active in place; creates the row if it doesn't exist yet (linking
    the product by gw_sku when one is given). Idempotent -- safe to re-run.
    """

    help = 'Seed 11th Edition points and categories for Death Guard units.'

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
            'Seeding Death Guard points (11th Edition)' + (' [DRY RUN]' if dry_run else '') + '\u2026\n'
        )

        fac = Faction.objects.filter(name='Death Guard').first()
        if not fac:
            self.stdout.write(self.style.ERROR(
                'Death Guard faction not found. Run populate_products first.'
            ))
            return

        updated_count = 0
        created_count = 0
        skipped_count = 0

        for gw_sku, points, category, label in DEATH_GUARD_UNITS:
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
