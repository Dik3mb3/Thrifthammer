"""
Management command: sync_cross_faction_units

Creates or updates UnitType records for units that appear in a sub-faction's
army calculator but share their physical kit with a parent faction.

For each configured unit this command:
  1. Looks up the UnitType in the PARENT faction by name.
  2. Copies its product FK (for pricing / deduplication) and category
     (for calculator grouping) into the TARGET sub-faction.
  3. Creates the UnitType if it does not exist; updates it if it does.

Why the product link matters
-----------------------------
The army calculator view deduplicates parent-faction units by product_id.
When a sub-faction UnitType shares the same product as a parent-faction
UnitType, the parent's entry is automatically suppressed in the sub-faction
view — no duplicates, no extra code needed in the view.

Relationship to populate_units
--------------------------------
populate_units._create_blood_angels_cross_faction_units() handles the first
batch of BA units (those with 48-xx products already in the DB at launch).
This command handles the remainder — units added in phase-2 / phase-3 — and
serves as the canonical place for all future sub-faction additions.

Idempotent — safe to re-run at any time.

Usage:
    python manage.py sync_cross_faction_units
    python manage.py sync_cross_faction_units --faction "Blood Angels"
    python manage.py sync_cross_faction_units --dry-run
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from calculators.models import UnitType
from products.models import Faction

# ---------------------------------------------------------------------------
# Cross-faction unit registry
#
# Top-level key  : sub-faction name  (must match Faction.name in the DB)
# parent_faction : faction to inherit product + category from
# units          : list of unit entries — each entry is a dict:
#
#   parent   (required)  Exact UnitType.name in the parent faction.
#   name     (optional)  Display name in the sub-faction calculator.
#                        Omit when identical to parent.
#   category (optional)  Override category. Omit to inherit from parent.
#                        Use when the parent has a legacy / incorrect value.
#
# To add a new sub-faction, add a new top-level key following the same
# pattern.  populate_units does NOT need to be changed.
# ---------------------------------------------------------------------------

CROSS_FACTION_UNITS = {

    # ── Blood Angels ─────────────────────────────────────────────────────────
    # SM kits that appear in the Blood Angels army list but were NOT created
    # by populate_units._create_blood_angels_cross_faction_units().
    # populate_units already handles the original 35 units (Ancient, Captain,
    # Chaplain, Librarian, Lieutenant, Apothecary, all standard infantry /
    # vehicle SKUs that were in the DB at launch).  Only add units here that
    # populate_units skips.
    "Blood Angels": {
        "parent_faction": "Space Marines",
        "units": [

            # ── Characters ───────────────────────────────────────────────────
            {"parent": "Ancient in Terminator Armour"},
            {"parent": "Captain in Gravis Armour"},
            {"parent": "Captain in Phobos Armour"},
            {"parent": "Captain in Terminator Armour"},
            {"parent": "Captain with Jump Pack"},
            # SM name differs from BA display name:
            {"parent": "Space Marine Chaplain in Terminator Armour",
             "name":   "Chaplain in Terminator Armour"},
            {"parent": "Chaplain on Bike"},
            {"parent": "Space Marine Judiciar",
             "name":   "Judiciar"},
            {"parent": "Librarian in Terminator Armour"},
            {"parent": "Lieutenant in Reiver Armour"},
            {"parent": "Primaris Librarian in Phobos Armour",
             "name":   "Librarian in Phobos Armour"},
            # SM stores Techmarine under legacy 'hq' category:
            {"parent": "Techmarine",
             "category": "character"},

            # ── Battleline ───────────────────────────────────────────────────
            {"parent": "Assault Intercessors with Jump Packs"},

            # ── Infantry ─────────────────────────────────────────────────────
            {"parent": "Centurion Assault Squad"},
            {"parent": "Centurion Devastator Squad"},
            {"parent": "Desolation Squad"},
            {"parent": "Heavy Intercessor Squad"},
            {"parent": "Hellblaster Squad"},
            {"parent": "Reiver Squad"},
            {"parent": "Terminator Assault Squad"},

            # ── Vehicles ─────────────────────────────────────────────────────
            {"parent": "Gladiator Lancer"},
            {"parent": "Gladiator Reaper"},
            {"parent": "Gladiator Valiant"},
            # SM stores Invictor under legacy 'infantry' category:
            {"parent": "Invictor Tactical Warsuit",
             "category": "vehicle"},
            # Predator Annihilator shares the SM Predator kit (same SKU):
            {"parent": "Space Marine Predator",
             "name":    "Predator Annihilator"},
            {"parent": "Storm Speeder Hailstrike"},
            {"parent": "Storm Speeder Hammerstrike"},
            {"parent": "Storm Speeder Thunderstrike"},
            # SM categories Stormhawk + Stormtalon as 'transport'; they are gunships:
            {"parent": "Stormhawk Interceptor",
             "category": "vehicle"},
            {"parent": "Stormtalon Gunship",
             "category": "vehicle"},
            {"parent": "Venerable Dreadnought"},

            # ── Transports ───────────────────────────────────────────────────
            {"parent": "Drop Pods"},
            {"parent": "Space Marine Land Raider",
             "name":   "Land Raider"},
            {"parent": "Land Raider Redeemer"},
            {"parent": "Razorback"},
            # SM stores Rhino under legacy 'dedicated_transport' category:
            {"parent": "Rhino",
             "category": "transport"},
            {"parent": "Stormraven Gunship"},

            # ── Mounted ──────────────────────────────────────────────────────
            # SM UnitType name is 'Space Marine Suppressors'; no product linked yet:
            {"parent": "Space Marine Suppressors",
             "name":   "Suppressor Squad"},
        ],
    },

    # ── Future sub-factions — add when their army calculators are built ───────
    # "Dark Angels": {
    #     "parent_faction": "Space Marines",
    #     "units": [
    #         {"parent": "Ravenwing Bike Squadron"},
    #         ...
    #     ],
    # },
    # "Space Wolves": {
    #     "parent_faction": "Space Marines",
    #     "units": [
    #         {"parent": "Blood Claws"},
    #         ...
    #     ],
    # },
}


class Command(BaseCommand):
    """Sync cross-faction UnitType records from parent faction to sub-faction."""

    help = (
        'Create / update UnitType records for units that a sub-faction shares '
        'with its parent faction (e.g. Blood Angels inheriting SM kits).'
    )

    def add_arguments(self, parser):
        """Register CLI arguments."""
        parser.add_argument(
            '--faction',
            type=str,
            default='',
            metavar='FACTION',
            help='Only sync this faction (e.g. "Blood Angels"). Defaults to all.',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Preview changes without writing to the database.',
        )

    def handle(self, *args, **options):
        """Iterate configured factions and sync their cross-faction units."""
        faction_filter = options['faction'].strip()
        dry_run = options['dry_run']

        if dry_run:
            self.stdout.write(self.style.WARNING('Dry-run mode — no changes will be written.\n'))

        totals = {'created': 0, 'updated': 0, 'skipped': 0}

        for faction_name, config in CROSS_FACTION_UNITS.items():
            if faction_filter and faction_name != faction_filter:
                continue
            self._sync_faction(faction_name, config, dry_run, totals)

        self.stdout.write(
            self.style.SUCCESS(
                f"\nDone — {totals['created']} created, "
                f"{totals['updated']} updated, "
                f"{totals['skipped']} skipped."
            )
        )

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _sync_faction(self, faction_name, config, dry_run, totals):
        """Sync one sub-faction's cross-faction units."""
        self.stdout.write(f'\n{faction_name}  (inheriting from {config["parent_faction"]})')
        self.stdout.write('-' * 70)

        sub_faction = Faction.objects.filter(name=faction_name).first()
        if not sub_faction:
            self.stdout.write(self.style.ERROR(
                f'  ERROR: sub-faction "{faction_name}" not found in DB — skipping.'
            ))
            return

        parent_faction = Faction.objects.filter(name=config['parent_faction']).first()
        if not parent_faction:
            self.stdout.write(self.style.ERROR(
                f'  ERROR: parent faction "{config["parent_faction"]}" not found in DB — skipping.'
            ))
            return

        created = updated = skipped = 0

        with transaction.atomic():
            for entry in config['units']:
                parent_name  = entry['parent']
                display_name = entry.get('name', parent_name)
                cat_override = entry.get('category')

                # Look up parent UnitType
                parent_unit = (
                    UnitType.objects
                    .filter(name=parent_name, faction=parent_faction)
                    .select_related('product')
                    .first()
                )
                if not parent_unit:
                    self.stdout.write(self.style.WARNING(
                        f'  [SKIP]    parent not found: "{parent_name}"'
                    ))
                    skipped += 1
                    continue

                product  = parent_unit.product
                category = cat_override or parent_unit.category

                if product is None:
                    self.stdout.write(self.style.WARNING(
                        f'  [NO SKU]  "{display_name}" — parent has no product, '
                        f'pricing unavailable until one is added'
                    ))

                sku_label = product.gw_sku if product else 'NULL'

                if dry_run:
                    exists = UnitType.objects.filter(
                        name=display_name, faction=sub_faction
                    ).exists()
                    action = 'UPDATE' if exists else 'CREATE'
                    self.stdout.write(
                        f'  [DRY {action:6}]  "{display_name}"'
                        f'  category={category}  sku={sku_label}'
                    )
                    created += not exists
                    updated += exists
                    continue

                _, was_created = UnitType.objects.update_or_create(
                    name=display_name,
                    faction=sub_faction,
                    defaults={
                        'product':   product,
                        'category':  category,
                        'is_active': True,
                    },
                )

                tag = 'CREATED' if was_created else 'UPDATED'
                self.stdout.write(
                    f'  [{tag:7}]  "{display_name}"'
                    f'  category={category}  sku={sku_label}'
                )
                created += was_created
                updated += not was_created

            if dry_run:
                transaction.set_rollback(True)

        self.stdout.write(
            f'  {faction_name}: {created} created, {updated} updated, {skipped} skipped.'
        )
        totals['created'] += created
        totals['updated'] += updated
        totals['skipped'] += skipped
