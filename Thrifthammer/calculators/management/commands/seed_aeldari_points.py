"""
Management command: seed_aeldari_points

Sets points_cost, category, and active status on UnitType records for all
Aeldari units, using official 11th Edition data sourced from the BSData
community BattleScribe project (github.com/BSData/wh40k-11e), the same data
New Recruit itself is built on.

Usage:
    python manage.py seed_aeldari_points

The command is fully idempotent -- safe to re-run. It looks up each unit by
(name, faction) -- the same pair UnitType enforces uniqueness on.

Notes:
- Source files: "Aeldari - Craftworlds.json" (the faction roster -- a thin
  list of entryLinks, not full unit definitions) plus "Aeldari - Aeldari
  Library.json" (the shared catalogue those links resolve into). Unlike
  Orks/Grey Knights/Adeptus Mechanicus, Craftworlds.json has no
  sharedSelectionEntries of its own -- every unit's real data (costs,
  categories, profiles) lives in the Library file and must be resolved via
  the roster's entryLinks targetIds.
- This completely replaces the old 10th Edition / New Recruit hand-authored
  points file, which stored points on (product, faction) rather than
  (name, faction) and had drifted badly out of sync with the live catalog
  (multiple stale duplicate rows at 0pts -- see AELDARI_DEACTIVATE).
- Several duplicate/stale UnitType rows accumulated over time, all sharing a
  SKU with a correctly-seeded sibling row and sitting at 0pts -- these are
  deactivated rather than updated:
    * "Codex: Aeldari" -- a book, wrongly holds SKU 46-30 and a leftover
      points value from a past Asurmen mismatch. Same issue as
      "Codex: Orks" / "Codex: Adeptus Mechanicus".
    * "Harlequin Troupe" -- duplicate of "Troupe" (same SKU prod3530579).
    * "Starfang", "Vyper" (singular) -- duplicates of "Vypers", all sharing
      SKU P-240924.
    * "Support Weapon" -- redundant 4th row on SKU prod770020a, which
      already correctly has D-Cannon Platform / Shadow Weaver Platform /
      Vibro Cannon Platform as the three real build options.
    * "Warlock Skyrunner" (singular) -- duplicate of "Warlock Skyrunners".
    * "Warlocks" -- redundant 3rd row on SKU prod4870187, which already
      correctly has "Warlock" and "Warlock Conclave" as the two real build
      options.
    * "Combat Patrol: Aeldari Corsairs" -- a bundle box, not a deployable
      unit (per user direction 2026-08-07).
- "Starfangs" -- a real, currently-active second build option alongside
  "Vypers" on shared SKU P-240924. The BSData source defines it with
  `costs: null` (no independent points value at all, not even via a
  modifier), so 70pts here is a user-supplied value (confirmed 2026-08-07),
  not extracted from BSData like everything else in this file.
- "Ynnari" units (8 total) are new UnitType rows added under the Aeldari
  faction, sharing gw_sku with existing products that already live under
  the *Drukhari* faction -- same "one physical product, multiple
  faction-scoped UnitType rows" pattern already used for Space Marine
  chapter squads (e.g. Intercessor Squad appears once per chapter, all
  pointing at the same product). Approved by user 2026-08-07 ("they will
  just show up on Aeldari and Drukhari"). Unlike the Space Marine case,
  points differ between the plain-Drukhari and Ynnari-detachment versions
  of the same unit, so these keep the distinct "Ynnari X" name rather than
  colliding with the base Drukhari unit name. Four of the eight
  (Incubi/Reavers/Succubus/Venom) surfaced a pre-existing gap: their
  products already existed but had never had ANY UnitType row, even under
  Drukhari itself -- flagged to the user, not fixed here (out of scope for
  this faction's migration).
"""

from django.core.management.base import BaseCommand

from calculators.models import UnitType
from products.models import Faction, Product

# ---------------------------------------------------------------------------
# Stale/duplicate rows deactivated rather than seeded with points.
# ---------------------------------------------------------------------------
AELDARI_DEACTIVATE = [
    'Codex: Aeldari',
    'Harlequin Troupe',
    'Starfang',
    'Vyper',
    'Support Weapon',
    'Warlock Skyrunner',
    'Warlocks',
    'Combat Patrol: Aeldari Corsairs',
]

# ---------------------------------------------------------------------------
# Unit data: (gw_sku, points_cost, category, name)
#
# Sourced from BSData/wh40k-11e ("Aeldari - Craftworlds.json" roster,
# resolved against "Aeldari - Aeldari Library.json"), 11th Edition. Base
# points only, no wargear or squad-size modifiers.
# ---------------------------------------------------------------------------
AELDARI_UNITS = [
    ('P-203616', 135, 'epic_hero', 'Asurmen'),
    ('prod4900146', 75, 'character', 'Autarch'),
    ('prod2810200', 70, 'character', 'Autarch Wayleaper'),
    ('prod4900143', 250, 'epic_hero', 'Avatar of Khaine'),
    ('P-203620', 125, 'epic_hero', 'Baharroth'),
    ('P-240922', 75, 'infantry', 'Corsair Skyreavers'),
    ('P-240923', 65, 'battleline', 'Corsair Voidreavers'),
    ('P-240923', 70, 'infantry', 'Corsair Voidscarred'),
    ('prod3600196', 160, 'vehicle', 'Crimson Hunter'),
    ('prod770020a', 110, 'infantry', 'D-Cannon Platform'),
    ('prod4870189', 100, 'infantry', 'Dark Reapers'),
    ('prod2620120', 70, 'character', 'Death Jester'),
    ('46-06', 75, 'infantry', 'Dire Avengers'),
    ('prod3650164', 130, 'epic_hero', 'Eldrad Ulthran'),
    ('46-29', 130, 'vehicle', 'Falcon'),
    ('46-02', 65, 'character', 'Farseer'),
    ('prod3650295', 60, 'character', 'Farseer Skyrunner'),
    ('46-14', 120, 'infantry', 'Fire Dragons'),
    ('prod770019a', 150, 'vehicle', 'Fire Prism'),
    ('P-203621', 130, 'epic_hero', 'Fuegan'),
    ('prod4870188', 90, 'battleline', 'Guardian Defenders'),
    ('prod3600197', 155, 'vehicle', 'Hemlock Wraithfighter'),
    ('prod4390157', 85, 'infantry', 'Howling Banshees'),
    ('prod4390156', 105, 'epic_hero', 'Jain Zar'),
    ('P-240921', 85, 'epic_hero', 'Kharseth'),
    ('P-203618', 135, 'epic_hero', 'Lhykhis'),
    ('prod4870190', 100, 'epic_hero', 'Maugan Ra'),
    ('prod2180123', 170, 'vehicle', 'Night Spinner'),
    ('P-240880', 95, 'epic_hero', 'Prince Yriel'),
    ('prod4900144', 60, 'infantry', 'Rangers'),
    ('prod770020a', 60, 'infantry', 'Shadow Weaver Platform'),
    ('prod2620121', 50, 'character', 'Shadowseer'),
    ('prod4900142', 100, 'mounted', 'Shining Spears'),
    ('prod4900145', 90, 'mounted', 'Shroud Runners'),
    ('prod2620124', 95, 'mounted', 'Skyweavers'),
    ('prod2620122', 115, 'epic_hero', 'Solitaire'),
    ('prod4240206', 55, 'character', 'Spiritseer'),
    ('prod2600170', 70, 'transport', 'Starweaver'),
    ('46-09', 110, 'battleline', 'Storm Guardians'),
    ('P-203614', 95, 'infantry', 'Swooping Hawks'),
    ('prod4870186', 90, 'epic_hero', 'The Visarch'),
    ('prod4870191', 245, 'epic_hero', 'The Yncarne'),
    ('prod3530579', 85, 'infantry', 'Troupe'),
    ('prod770020a', 60, 'infantry', 'Vibro Cannon Platform'),
    ('prod2780228', 115, 'vehicle', 'Voidweaver'),
    ('P-240924', 75, 'vehicle', 'Vypers'),
    ('P-240924', 70, 'vehicle', 'Starfangs'),  # user-supplied, see docstring
    ('P-203606', 85, 'vehicle', 'War Walkers'),
    ('prod4870187', 45, 'character', 'Warlock'),
    ('prod4870187', 55, 'infantry', 'Warlock Conclave'),
    ('prod3660120', 55, 'mounted', 'Warlock Skyrunners'),
    ('P-203611', 105, 'infantry', 'Warp Spiders'),
    ('46-29', 115, 'transport', 'Wave Serpent'),
    ('prod3660121', 80, 'mounted', 'Windriders'),
    ('prod3590139', 140, 'infantry', 'Wraithblades'),
    ('prod3590128', 145, 'infantry', 'Wraithguard'),
    ('prod3580144', 385, 'monster', 'Wraithknight'),
    (None, 380, 'monster', 'Wraithknight with Ghostglaive'),
    ('prod3530578', 125, 'monster', 'Wraithlord'),
    ('prod4870185', 100, 'epic_hero', 'Yvraine'),
    # ── Ynnari -- new rows, share SKUs with existing Drukhari products ─────
    ('45-02', 85, 'character', 'Ynnari Archon'),
    ('DR-007', 80, 'infantry', 'Ynnari Incubi'),
    ('45-07', 110, 'battleline', 'Ynnari Kabalite Warriors'),
    ('45-10', 70, 'transport', 'Ynnari Raider'),
    ('DR-017', 65, 'mounted', 'Ynnari Reavers'),
    ('DR-004', 45, 'character', 'Ynnari Succubus'),
    ('DR-010', 65, 'transport', 'Ynnari Venom'),
    ('45-06', 90, 'battleline', 'Ynnari Wyches'),
]


class Command(BaseCommand):
    """
    Seed 11th Edition points, category, and active status for Aeldari units.

    Looks up each unit by (name, faction) and updates points_cost, category,
    and is_active in place; creates the row if it doesn't exist yet (linking
    the product by gw_sku when one is given). Idempotent -- safe to re-run.
    """

    help = 'Seed 11th Edition points and categories for Aeldari units.'

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
            'Seeding Aeldari points (11th Edition)' + (' [DRY RUN]' if dry_run else '') + '…\n'
        )

        fac = Faction.objects.filter(name='Aeldari').first()
        if not fac:
            self.stdout.write(self.style.ERROR(
                'Aeldari faction not found. Run populate_products first.'
            ))
            return

        for name in AELDARI_DEACTIVATE:
            unit = UnitType.objects.filter(name=name, faction=fac).first()
            if unit and unit.is_active:
                self.stdout.write(f'  [deactivate] {name!r} (stale duplicate / not a real unit)')
                if not dry_run:
                    unit.is_active = False
                    unit.save(update_fields=['is_active'])

        updated_count = 0
        created_count = 0
        skipped_count = 0

        for gw_sku, points, category, label in AELDARI_UNITS:
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
