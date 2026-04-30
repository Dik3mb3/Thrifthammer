"""
Management command: import_faction_stats

Generic stats importer for the army calculator.  Reads a parsed JSON file
(produced by the New Recruit card parser) and a mapping CSV, then fully
synchronises the army-calculator UnitType records for the target faction.

The mapping CSV is the **single source of truth** for the calculator:

* include=Yes  → unit is created (if missing), renamed to card_name, linked
                 to the product via gw_sku, activated, and stats are seeded
                 from the JSON.  Units with no JSON entry are still activated
                 (with whatever stats they already have).
* include≠Yes  → unit is deactivated if it exists.
* not in CSV   → also deactivated (nuclear clean-up at the end of the run).

Safe to re-run — fully idempotent.  Points costs are set from the JSON
``points`` value, so no separate points-seed command is needed.

JSON format expected
--------------------
The top-level structure must be::

    {
        "faction": "...",
        "units": [
            {
                "card_name": "Arjac Rockfist",
                "points": 105,
                "primary_stats": {"M": "6\"", "T": "5", "SV": "2+",
                                  "W": "6", "LD": "6+", "OC": "1"},
                "invuln_save": "4+",          # null if none
                "fnp_save": null,             # null if none
                "ranged_weapons": [...],
                "melee_weapons":  [...],
                "abilities":      [{"name": "...", "description": "..."}]
            },
            ...
        ]
    }

When the same card_name appears more than once in the JSON (e.g. two
loadout variants of the same kit), the **first** occurrence is used.

Mapping CSV format
------------------
Required columns: ``card_name``, ``db_name``, ``include``

    card_name  – exact name as it appears in the JSON (also becomes the
                 displayed unit name in the army calculator)
    db_name    – current UnitType.name in the DB used for the initial
                 lookup; once the unit is renamed to card_name on the
                 first run, subsequent runs find it by card_name.
    gw_sku     – GW SKU (with or without "SKU: " prefix) used to link
                 the UnitType to a Product for price display.
    include    – "Yes" (case-insensitive) to include; anything else hides
                 the unit from the calculator.

Optional columns (ignored but harmless): ``faction``, etc.

UnitType lookup strategy (include=Yes rows)
-------------------------------------------
For each include=Yes row the command tries lookups in this order:

1. In-memory cache (catches duplicate db_name rows — e.g. "Land Raider"
   and "Land Raider Crusader" both mapping to the same UnitType).
2. UnitType.objects.get(name=db_name,   faction=target_faction)
3. UnitType.objects.get(name=card_name, faction=target_faction)
4. Create a new UnitType(name=card_name, …) if nothing is found.

After the first run the unit is named card_name, so lookup 3 is the
steady-state path on all subsequent runs.

Dynamic workflow
----------------
Add a new unit to the mapping CSV (include=Yes, gw_sku filled in) and
re-run the seed.  The command will:

  • Find or create the UnitType.
  • Set its name to card_name.
  • Link it to the correct Product via gw_sku.
  • Seed stats from the JSON (if the card exists).
  • Deactivate everything else in the faction that is not in the CSV.

Adding a new faction
--------------------
1. Parse faction cards → JSON  (parser_output/<faction>_parsed.json).
2. Build mapping CSV          (parser_output/<faction>_mapping.csv).
3. Run::

       python manage.py sync_cross_faction_units --faction "Faction Name"
       python manage.py import_faction_stats \\
           --faction "Faction Name" \\
           --json  ../parser_output/<faction>_parsed.json \\
           --mapping ../parser_output/<faction>_mapping.csv

Usage
-----
    python manage.py import_faction_stats \\
        --faction "Space Marines" \\
        --json  ../parser_output/spacemarines_parsed.json \\
        --mapping ../parser_output/spacemarines_mapping.csv

    # Preview without writing:
    python manage.py import_faction_stats \\
        --faction "Space Marines" \\
        --json  ../parser_output/spacemarines_parsed.json \\
        --mapping ../parser_output/spacemarines_mapping.csv \\
        --dry-run
"""

import csv
import json
import re
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from calculators.models import UnitAbility, UnitType, WeaponProfile
from products.models import Faction, Product


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _extract_save(value):
    """Return the save rating (e.g. '4+') from an invuln/fnp string.

    Handles both the short form ('4+') and the long descriptive form
    ('This model has a 4+ invulnerable save').  Returns '' if nothing
    is found or value is None/empty.
    """
    if not value:
        return ''
    match = re.search(r'\d\+', str(value))
    return match.group(0) if match else ''


def _safe_str(value):
    """Return str(value) or '' for None/missing values."""
    return '' if value is None else str(value)


# ---------------------------------------------------------------------------
# Command
# ---------------------------------------------------------------------------

class Command(BaseCommand):
    """Seed army-calculator stats from a parsed card JSON + mapping CSV.

    The mapping CSV is the single source of truth for the calculator:
    card_name becomes the display name, gw_sku links to the Product,
    and include=Yes is the only gate.  Everything not explicitly included
    is hidden (nuclear deactivation at the end of each run).

    Reusable for any faction — pass --faction, --json, and --mapping.
    Safe to re-run (idempotent).
    """

    help = (
        'Dynamic faction stats importer: the mapping CSV is the single source '
        'of truth.  Renames units to card_name, links products via gw_sku, '
        'seeds stats from JSON, and hides everything not in the mapping.'
    )

    def add_arguments(self, parser):
        """Define command-line arguments."""
        parser.add_argument(
            '--faction', required=True,
            help='Faction name exactly as stored in the DB (e.g. "Space Marines")',
        )
        parser.add_argument(
            '--json', required=True, dest='json_file',
            help='Path to the parsed JSON file (from the card parser)',
        )
        parser.add_argument(
            '--mapping', required=True, dest='mapping_file',
            help='Path to the mapping CSV file',
        )
        parser.add_argument(
            '--dry-run', action='store_true',
            help='Preview what would change without writing to the database',
        )

    def handle(self, *args, **options):
        """Execute the import."""
        faction_name = options['faction']
        json_path    = Path(options['json_file'])
        mapping_path = Path(options['mapping_file'])
        dry_run      = options['dry_run']

        # ── Validate files ────────────────────────────────────────────────
        if not json_path.exists():
            raise CommandError(f'JSON file not found: {json_path}')
        if not mapping_path.exists():
            raise CommandError(f'Mapping CSV not found: {mapping_path}')

        # ── Load faction ─────────────────────────────────────────────────
        try:
            faction = Faction.objects.get(name=faction_name)
        except Faction.DoesNotExist:
            available = list(Faction.objects.values_list('name', flat=True))
            raise CommandError(
                f'Faction "{faction_name}" not found in the database.\n'
                f'Available factions: {available}'
            )

        # ── Load JSON ────────────────────────────────────────────────────
        # Build a dict keyed by card_name; first occurrence wins when
        # duplicates exist (e.g. two loadout variants of the same kit).
        with json_path.open(encoding='utf-8') as fh:
            data = json.load(fh)

        units_by_card_name = {}
        for unit in data.get('units', []):
            card_name = (unit.get('card_name') or '').strip()
            if card_name and card_name not in units_by_card_name:
                units_by_card_name[card_name] = unit

        self.stdout.write(
            f'Loaded {len(units_by_card_name)} unique units from {json_path.name}.'
        )

        # ── Load mapping CSV — include=Yes rows only ──────────────────────
        required_cols = {'card_name', 'db_name', 'include'}
        rows = []  # include=Yes

        with mapping_path.open(encoding='utf-8-sig') as fh:
            reader = csv.DictReader(fh)
            fieldnames = set(reader.fieldnames or [])
            missing_cols = required_cols - fieldnames
            if missing_cols:
                raise CommandError(
                    f'Mapping CSV is missing required columns: {missing_cols}\n'
                    f'Found columns: {fieldnames}'
                )
            for row in reader:
                if (row.get('include') or '').strip().lower() == 'yes':
                    rows.append(row)

        self.stdout.write(
            f'Found {len(rows)} include=Yes rows in {mapping_path.name}.'
        )

        # ── Seed loop ────────────────────────────────────────────────────
        # name_to_unit  — maps any known name → UnitType for fast lookup.
        # consumed_pks  — PKs already claimed by a row this run.
        #
        # When multiple rows share the same db_name (e.g. "Apothecary" and
        # "Apothecary Biologis" both point to "Space Marine Apothecary"), the
        # FIRST matching row claims that UnitType (consumed_pks).  Subsequent
        # rows with the same db_name skip consumed units and either find their
        # own card_name in the DB or create a fresh UnitType.  This makes each
        # kit-variant a stable, independent UnitType after the first run.
        name_to_unit  = {}
        consumed_pks  = set()
        seeded_pks    = set()

        updated = created_new = no_json = 0

        with transaction.atomic():

            for row in rows:
                card_name  = (row.get('card_name') or '').strip()
                db_name    = (row.get('db_name')   or '').strip()
                gw_sku_raw = (row.get('gw_sku')    or '').strip()

                if not card_name:
                    continue

                # Parse SKU — strip "SKU: " prefix if present
                gw_sku = gw_sku_raw.replace('SKU:', '').strip()

                # ── Resolve product by SKU (for pricing link) ─────────────
                product = None
                if gw_sku:
                    product = Product.objects.filter(gw_sku=gw_sku).first()
                    if not product:
                        self.stdout.write(self.style.WARNING(
                            f'  WARN: SKU {gw_sku!r} not in DB — {card_name!r} '
                            f'will have no price link'
                        ))

                # ── Find existing UnitType ────────────────────────────────
                # Try names in priority order: cache → db_name → card_name.
                # Skip any unit already consumed by a previous row (this lets
                # duplicate-db_name rows each get their own UnitType).
                unit = None
                for lookup_name in dict.fromkeys(
                    n for n in [db_name, card_name] if n
                ):
                    # 1. Check cache
                    cached = name_to_unit.get(lookup_name)
                    if cached is not None and cached.pk not in consumed_pks:
                        unit = cached
                        break

                    # 2. DB lookup
                    try:
                        candidate = UnitType.objects.get(
                            name=lookup_name, faction=faction,
                        )
                        if candidate.pk not in consumed_pks:
                            unit = candidate
                            break
                    except UnitType.DoesNotExist:
                        continue

                # 3. Create if still not found
                if unit is None:
                    if dry_run:
                        self.stdout.write(
                            f'  DRY-RUN WOULD CREATE: {card_name!r} '
                            f'(SKU {gw_sku or "none"})'
                        )
                        created_new += 1
                        continue

                    unit = UnitType(
                        name=card_name,
                        faction=faction,
                        product=product,
                        is_active=False,   # activated below after stats seed
                        points_cost=0,
                        category='infantry',
                    )
                    unit.save()
                    created_new += 1
                    self.stdout.write(f'  CREATED: {card_name!r}')

                # Mark consumed + cache under both names for this run
                consumed_pks.add(unit.pk)
                seeded_pks.add(unit.pk)
                if db_name:
                    name_to_unit[db_name] = unit
                name_to_unit[card_name] = unit

                # ── Dry-run preview ───────────────────────────────────────
                if dry_run:
                    unit_data = units_by_card_name.get(card_name)
                    pts  = unit_data.get('points', '?') if unit_data else 'no JSON'
                    name_change = (
                        f'{unit.name!r} -> {card_name!r}'
                        if unit.name != card_name else repr(card_name)
                    )
                    self.stdout.write(
                        f'  DRY-RUN: {name_change} '
                        f'({pts}pts, SKU {gw_sku or "none"})'
                    )
                    updated += 1
                    continue

                # ── Resolve name conflict before renaming ─────────────────
                # If a *different* UnitType already owns card_name in this
                # faction, temporarily rename it out of the way so our save
                # doesn't violate the unique(name, faction) constraint.
                # The conflicting unit is always stale (not in seeded_pks) and
                # will be fully deactivated by the nuclear step at the end.
                if unit.name != card_name:
                    conflict = (
                        UnitType.objects
                        .filter(name=card_name, faction=faction)
                        .exclude(pk=unit.pk)
                        .first()
                    )
                    if conflict:
                        conflict.name      = f'_stale_{conflict.pk}'
                        conflict.is_active = False
                        conflict.save(update_fields=['name', 'is_active'])
                        self.stdout.write(self.style.WARNING(
                            f'  CONFLICT RESOLVED: stale {card_name!r} '
                            f'(pk={conflict.pk}) renamed out of the way'
                        ))

                # ── Apply rename + product link ───────────────────────────
                unit.name      = card_name
                unit.is_active = True
                # Only update product when a SKU is supplied — prevents
                # clearing a valid existing product link when gw_sku is blank.
                if gw_sku:
                    unit.product = product  # None if SKU not found in DB

                # ── Seed stats from JSON (if card data exists) ────────────
                unit_data = units_by_card_name.get(card_name)

                if unit_data:
                    ps         = unit_data.get('primary_stats') or {}
                    points_raw = unit_data.get('points', 0)
                    try:
                        points = int(str(points_raw).replace('pts', '').strip())
                    except (ValueError, TypeError):
                        points = 0

                    unit.points_cost     = points
                    unit.stat_movement   = _safe_str(ps.get('M'))
                    unit.stat_toughness  = _safe_str(ps.get('T'))
                    unit.stat_save       = _safe_str(ps.get('SV'))
                    unit.stat_wounds     = _safe_str(ps.get('W'))
                    unit.stat_leadership = _safe_str(ps.get('LD'))
                    unit.stat_oc         = _safe_str(ps.get('OC'))
                    unit.stat_invuln     = _extract_save(unit_data.get('invuln_save'))
                    unit.stat_fnp        = _extract_save(unit_data.get('fnp_save'))
                    unit.save()

                    # Replace weapon profiles (delete then recreate)
                    unit.weapon_profiles.all().delete()
                    order = 0

                    for wpn in unit_data.get('ranged_weapons') or []:
                        WeaponProfile.objects.create(
                            unit_type   = unit,
                            order       = order,
                            name        = _safe_str(wpn.get('name')),
                            weapon_type = 'ranged',
                            range       = _safe_str(wpn.get('range')),
                            attacks     = _safe_str(wpn.get('A')),
                            skill       = _safe_str(wpn.get('BS')),
                            strength    = _safe_str(wpn.get('S')),
                            ap          = _safe_str(wpn.get('AP')),
                            damage      = _safe_str(wpn.get('D')),
                            keywords    = _safe_str(wpn.get('keywords')),
                        )
                        order += 1

                    for wpn in unit_data.get('melee_weapons') or []:
                        WeaponProfile.objects.create(
                            unit_type   = unit,
                            order       = order,
                            name        = _safe_str(wpn.get('name')),
                            weapon_type = 'melee',
                            range       = 'Melee',
                            attacks     = _safe_str(wpn.get('A')),
                            skill       = _safe_str(wpn.get('WS')),
                            strength    = _safe_str(wpn.get('S')),
                            ap          = _safe_str(wpn.get('AP')),
                            damage      = _safe_str(wpn.get('D')),
                            keywords    = _safe_str(wpn.get('keywords')),
                        )
                        order += 1

                    # Replace abilities (delete then recreate)
                    unit.abilities.all().delete()
                    for ab_order, ab in enumerate(unit_data.get('abilities') or []):
                        UnitAbility.objects.create(
                            unit_type   = unit,
                            order       = ab_order,
                            name        = _safe_str(ab.get('name')),
                            description = _safe_str(ab.get('description')),
                        )

                    self.stdout.write(
                        f'  OK: {card_name!r} ({points}pts, SKU {gw_sku or "none"})'
                    )
                else:
                    # No JSON stats — still activate and rename, just no stat data
                    unit.save()
                    no_json += 1
                    self.stdout.write(
                        self.style.WARNING(
                            f'  ACTIVE (no JSON stats): {card_name!r} '
                            f'(SKU {gw_sku or "none"})'
                        )
                    )

                updated += 1

            # ── Nuclear deactivation ──────────────────────────────────────
            # Any UnitType in this faction that was NOT processed as
            # include=Yes above is hidden.  This makes the mapping CSV the
            # single source of truth — no manual deactivation batch fixes
            # needed when the mapping changes.
            to_deactivate_qs = (
                UnitType.objects
                .filter(faction=faction, is_active=True)
                .exclude(pk__in=seeded_pks)
            )
            deactivated_names = list(to_deactivate_qs.values_list('name', flat=True))
            deactivated = len(deactivated_names)

            if deactivated_names:
                if dry_run:
                    for name in deactivated_names:
                        self.stdout.write(
                            f'  DRY-RUN WOULD HIDE: {name!r}'
                        )
                else:
                    to_deactivate_qs.update(is_active=False)
                    for name in deactivated_names:
                        self.stdout.write(self.style.WARNING(
                            f'  HIDDEN (not in mapping): {name!r}'
                        ))

            if dry_run:
                transaction.set_rollback(True)

        # ── Summary ───────────────────────────────────────────────────────
        verb = 'would' if dry_run else 'done'
        self.stdout.write(self.style.SUCCESS(
            f'\n{faction_name} import {verb}:\n'
            f'  {updated} seeded/renamed\n'
            f'  {created_new} created (new to DB)\n'
            f'  {no_json} activated without JSON stats\n'
            f'  {deactivated} hidden (not in mapping)'
        ))
