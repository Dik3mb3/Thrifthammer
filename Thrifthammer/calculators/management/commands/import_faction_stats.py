"""
Management command: import_faction_stats

Generic stats importer for the army calculator.  Reads a parsed JSON file
(produced by the New Recruit card parser) and a mapping CSV, then seeds
stats, weapon profiles, and abilities for each included unit in the target
faction.

Safe to re-run — deletes and recreates weapon profiles / abilities each
time, and overwrites stat fields directly.  Points costs are also set from
the JSON ``points`` value, so no separate points-seed command is needed.

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
                "ranged_weapons": [
                    {"name": "Foehammer", "range": "6\"",
                     "A": "1", "BS": "2+", "S": "8",
                     "AP": "-2", "D": "3",
                     "keywords": "Anti-Monster 3+, Assault"}
                ],
                "melee_weapons": [
                    {"name": "Foehammer",
                     "A": "5", "WS": "2+", "S": "8",
                     "AP": "-2", "D": "3",
                     "keywords": "Precision"}
                ],
                "abilities": [
                    {"name": "Leader", "description": "..."}
                ]
            },
            ...
        ]
    }

When the same card_name appears more than once in the JSON (e.g., two
loadout variants of the same kit), the **first** occurrence is used.  The
later entries are silently ignored.  Add a second mapping-CSV row with the
same card_name and a different db_name to seed both UnitTypes if needed.

Mapping CSV format
------------------
Required columns: ``card_name``, ``db_name``, ``include``

    card_name  – exact name as it appears in the JSON (used for lookup)
    db_name    – UnitType.name in the DB for native units;
                 for SM-shared units (synced via sync_cross_faction_units)
                 you can leave this as the SM parent name — the command will
                 fall back to card_name if db_name is not found in the
                 target faction.
    include    – "Yes" to process, anything else to skip

Optional columns (ignored but harmless): ``gw_sku``, ``faction``, etc.

UnitType lookup strategy
------------------------
For each row the command tries two lookups in order:

1. UnitType.objects.get(name=db_name,   faction=target_faction)
2. UnitType.objects.get(name=card_name, faction=target_faction)

Whichever succeeds first is used.  If both fail the unit is skipped with a
warning.  This means:

* Native units  (e.g. Grey Hunters → "Space Wolves Grey Hunters") resolve
  on the first try because db_name matches the UnitType.name.
* SM-shared units (e.g. card_name "Aggressor Squad", db_name
  "Space Marine Aggressors") miss on the first try and hit on the
  second — because sync_cross_faction_units creates them under the
  card_name display name.

Adding a new faction
--------------------
1. Parse faction cards → JSON file (parser_output/<faction>_parsed.json).
2. Build mapping CSV   → parser_output/<faction>_mapping.csv
3. Run::

       python manage.py sync_cross_faction_units --faction "Faction Name"
       python manage.py import_faction_stats \\
           --faction "Faction Name" \\
           --json  ../parser_output/<faction>_parsed.json \\
           --mapping ../parser_output/<faction>_mapping.csv

Usage
-----
    python manage.py import_faction_stats \\
        --faction "Space Wolves" \\
        --json  ../parser_output/spacewolves_parsed.json \\
        --mapping ../parser_output/spacewolves_mapping.csv

    # Preview without writing:
    python manage.py import_faction_stats \\
        --faction "Space Wolves" \\
        --json  ../parser_output/spacewolves_parsed.json \\
        --mapping ../parser_output/spacewolves_mapping.csv \\
        --dry-run
"""

import csv
import json
import re
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from calculators.models import UnitAbility, UnitType, WeaponProfile
from products.models import Faction


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

    Reusable for any faction — pass --faction, --json, and --mapping.
    Safe to re-run (idempotent).
    """

    help = (
        'Generic stats importer: seeds UnitType stats, weapon profiles, and '
        'abilities from a parsed card JSON file and a mapping CSV.'
    )

    def add_arguments(self, parser):
        """Define command-line arguments."""
        parser.add_argument(
            '--faction', required=True,
            help='Faction name exactly as stored in the DB (e.g. "Space Wolves")',
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

        # ── Load mapping CSV ─────────────────────────────────────────────
        required_cols = {'card_name', 'db_name', 'include'}
        rows = []           # include == "Yes" — seed stats + ensure active
        excluded_rows = []  # include != "Yes" — deactivate in army calculator

        # utf-8-sig strips the UTF-8 BOM that Excel sometimes adds
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
                else:
                    excluded_rows.append(row)

        self.stdout.write(
            f'Found {len(rows)} included, {len(excluded_rows)} excluded '
            f'in {mapping_path.name}.'
        )

        # ── Seed loop ────────────────────────────────────────────────────
        updated = skipped = deactivated = 0

        with transaction.atomic():
            for row in rows:
                card_name = (row.get('card_name') or '').strip()
                db_name   = (row.get('db_name')   or '').strip()

                # Find unit data in JSON
                unit_data = units_by_card_name.get(card_name)
                if unit_data is None:
                    self.stdout.write(
                        f'  SKIP (not in JSON): "{card_name}"'
                    )
                    skipped += 1
                    continue

                # Find the UnitType in the database.
                # Try db_name first (native units), then card_name (SM-shared
                # units where sync creates them under the display name).
                unit = None
                tried = []
                for lookup_name in dict.fromkeys([db_name, card_name]):
                    if not lookup_name:
                        continue
                    tried.append(lookup_name)
                    try:
                        unit = UnitType.objects.get(
                            name=lookup_name, faction=faction,
                        )
                        break
                    except UnitType.DoesNotExist:
                        continue

                if unit is None:
                    self.stdout.write(
                        f'  SKIP (UnitType not in "{faction_name}"): '
                        f'tried {tried}'
                    )
                    skipped += 1
                    continue

                # Extract stats from JSON
                ps         = unit_data.get('primary_stats') or {}
                points_raw = unit_data.get('points', 0)
                try:
                    points = int(str(points_raw).replace('pts', '').strip())
                except (ValueError, TypeError):
                    points = 0

                if dry_run:
                    self.stdout.write(
                        f'  DRY-RUN: {unit.name} '
                        f'({points}pts, T{ps.get("T", "?")})'
                    )
                    updated += 1
                    continue

                # Write stats; also ensure the unit is visible in the calculator
                # (re-activates a unit if it was previously hidden by this command)
                unit.is_active      = True
                unit.points_cost    = points
                unit.stat_movement  = _safe_str(ps.get('M'))
                unit.stat_toughness = _safe_str(ps.get('T'))
                unit.stat_save      = _safe_str(ps.get('SV'))
                unit.stat_wounds    = _safe_str(ps.get('W'))
                unit.stat_leadership = _safe_str(ps.get('LD'))
                unit.stat_oc        = _safe_str(ps.get('OC'))
                unit.stat_invuln    = _extract_save(unit_data.get('invuln_save'))
                unit.stat_fnp       = _extract_save(unit_data.get('fnp_save'))
                unit.save()

                # Replace weapon profiles (delete then recreate)
                unit.weapon_profiles.all().delete()
                order = 0

                for wpn in unit_data.get('ranged_weapons') or []:
                    rng_val = _safe_str(wpn.get('range'))
                    WeaponProfile.objects.create(
                        unit_type   = unit,
                        order       = order,
                        name        = _safe_str(wpn.get('name')),
                        weapon_type = 'ranged',
                        range       = rng_val,
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

                self.stdout.write(f'  OK: {unit.name} ({points}pts)')
                updated += 1

            # ── Deactivate excluded units ─────────────────────────────────
            # Units in the mapping with include != "Yes" are hidden from the
            # army calculator by setting is_active=False.  Units NOT in the
            # mapping at all are left untouched — this only affects rows that
            # are explicitly listed in the CSV with a non-"Yes" include value.
            for row in excluded_rows:
                card_name = (row.get('card_name') or '').strip()
                db_name   = (row.get('db_name')   or '').strip()

                # Same two-step lookup as the include loop
                unit = None
                for lookup_name in dict.fromkeys([db_name, card_name]):
                    if not lookup_name:
                        continue
                    try:
                        unit = UnitType.objects.get(
                            name=lookup_name, faction=faction,
                        )
                        break
                    except UnitType.DoesNotExist:
                        continue

                if unit is None:
                    continue  # Not in DB yet — nothing to deactivate

                if dry_run:
                    status = 'already hidden' if not unit.is_active else 'would hide'
                    self.stdout.write(
                        f'  DRY-RUN DEACTIVATE ({status}): {unit.name!r}'
                    )
                    deactivated += 1
                    continue

                if not unit.is_active:
                    continue  # Already hidden — no-op

                unit.is_active = False
                unit.save(update_fields=['is_active'])
                self.stdout.write(self.style.WARNING(
                    f'  HIDDEN: {unit.name!r} (include != Yes — removed from calculator)'
                ))
                deactivated += 1

            if dry_run:
                transaction.set_rollback(True)

        verb = 'would update' if dry_run else 'updated'
        hide_verb = 'would hide' if dry_run else 'hidden'
        self.stdout.write(
            self.style.SUCCESS(
                f'\n{faction_name} import complete: '
                f'{updated} {verb}, {skipped} skipped, '
                f'{deactivated} {hide_verb} from calculator.'
            )
        )
