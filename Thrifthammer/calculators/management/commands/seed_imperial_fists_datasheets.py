"""
Management command: seed_imperial_fists_datasheets

Refreshes stat lines, weapon profiles, and abilities for the Imperial
Fists-exclusive units using 11th Edition data sourced from BSData/
wh40k-11e ("Imperium - Imperial Fists.json") -- the same source used by
seed_imperial_fists_points.py.

Usage:
    python manage.py seed_imperial_fists_datasheets
    python manage.py seed_imperial_fists_datasheets --dry-run

Notes:
- Does NOT touch points_cost or category -- those are handled entirely by
  seed_imperial_fists_points.py. This command only refreshes stat_*
  fields, WeaponProfile rows, and UnitAbility rows.
- Scope is the 2 IF-exclusive rows only (Darnath Lysander, Tor Garadon)
  -- generic squads inherit their datasheets from the base Space Marines
  faction automatically. Pedro Kantor is out of scope -- no product
  exists for him anywhere in the catalog (tracked on the project
  backlog).
- Per-field safety rule: a unit's stats/weapons/abilities are only
  overwritten when BSData actually has that data for it. If extraction
  found nothing, the existing DB value/rows are left untouched.
- Both active units resolved cleanly -- 0 missing stats/weapons/
  abilities, 0 overlong stat fields.
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from calculators.models import UnitAbility, UnitType, WeaponProfile

# (name -> {stats?, weapons?, abilities?}). Missing keys mean "no data
# found for this field -- leave existing DB data untouched."
IMPERIAL_FISTS_DATASHEETS = {
    "Darnath Lysander": {
        "stats": {
            "stat_movement": "5\"",
            "stat_toughness": 5,
            "stat_save": "2+",
            "stat_wounds": 7,
            "stat_leadership": "6+",
            "stat_oc": 1,
            "stat_invuln": "4+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Fist of Dorn",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "5",
                "skill": "2+",
                "strength": "10",
                "ap": "-3",
                "damage": "3",
                "keywords": "Devastating Wounds"
            }
        ],
        "abilities": [
            {
                "name": "Icon of Obstinacy",
                "description": "Each time an attack targets this model's unit, if the Strength characteristic of that attack is greater than or equal to the Toughness characteristic of that unit, subtract 1 from the Wound roll."
            },
            {
                "name": "Rampart",
                "description": "Once per battle, at the start of any phase, this model can use this ability. If it does, until the end of the phase, this model has a 2+ invulnerable save."
            },
            {
                "name": "Leader",
                "description": "This model can be attached to the following units:\n\n\u25a0 TERMINATOR ASSAULT SQUAD\n\u25a0 TERMINATOR SQUAD"
            },
            {
                "name": "Inspiring Commander",
                "description": "\u2018If you include this model in your army, until the end of the battle, non-Character models in Terminator Assault Squad and Terminator Squad units from your army have an Objective Control characteristic of 2 while they are not Battle-shocked."
            }
        ]
    },
    "Tor Garadon": {
        "stats": {
            "stat_movement": "5\"",
            "stat_toughness": 6,
            "stat_save": "3+",
            "stat_wounds": 6,
            "stat_leadership": "6+",
            "stat_oc": 1,
            "stat_invuln": "4+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Artificer Grav Gun",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "2",
                "skill": "2+",
                "strength": "5",
                "ap": "-1",
                "damage": "2",
                "keywords": "Anti-vehicle 2+"
            },
            {
                "name": "Hand of Defiance",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "5",
                "skill": "2+",
                "strength": "12",
                "ap": "-2",
                "damage": "2",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Signum Array",
                "description": "While this model is leading a unit, ranged weapons equipped by models in that unit have the [IGNORES COVER] ability."
            },
            {
                "name": "Siege Captain",
                "description": "Each time this model makes an attack that targets a Monster, Vehicle, or Fortification unit, improve the Strength, Armour Penetration and Damage characteristics of that attack by 2."
            },
            {
                "name": "Leader",
                "description": "This model can be attached to the following units:\n\n\u25a0 AGGRESSOR SQUAD\n\u25a0 ERADICATOR SQUAD\n\u25a0 HEAVY INTERCESSOR SQUAD"
            }
        ]
    }
}


class Command(BaseCommand):
    """Refresh Imperial Fists stat lines, weapon profiles, and abilities from BSData."""

    help = 'Refresh 11th Edition stats/weapons/abilities for Imperial-Fists-exclusive units.'

    def add_arguments(self, parser):
        """Add --dry-run flag."""
        parser.add_argument(
            '--dry-run', action='store_true',
            help='Preview changes without writing to the database.',
        )

    def handle(self, *args, **options):
        """Iterate IMPERIAL_FISTS_DATASHEETS and refresh each unit's datasheet data."""
        dry_run = options['dry_run']
        updated = 0
        skipped = 0

        with transaction.atomic():
            for name, payload in IMPERIAL_FISTS_DATASHEETS.items():
                try:
                    unit = UnitType.objects.get(name=name, faction__name='Imperial Fists')
                except UnitType.DoesNotExist:
                    self.stdout.write(self.style.WARNING(f'  SKIP (not found): {name}'))
                    skipped += 1
                    continue

                changes = []

                if 'stats' in payload:
                    for field, val in payload['stats'].items():
                        if getattr(unit, field) != val:
                            changes.append(field)
                        setattr(unit, field, val)

                n_weapons = len(payload.get('weapons', []))
                n_abilities = len(payload.get('abilities', []))

                if dry_run:
                    note = []
                    if 'stats' in payload:
                        note.append(f"stats({'chg' if changes else 'ok'})")
                    if 'weapons' in payload:
                        note.append(f'{n_weapons}w')
                    if 'abilities' in payload:
                        note.append(f'{n_abilities}a')
                    self.stdout.write(f"  DRY-RUN -> {name!r} " + ' '.join(note))
                    updated += 1
                    continue

                if 'stats' in payload:
                    unit.save()

                if 'weapons' in payload:
                    WeaponProfile.objects.filter(unit_type=unit).delete()
                    for order, wp in enumerate(payload['weapons']):
                        WeaponProfile.objects.create(unit_type=unit, order=order, **wp)

                if 'abilities' in payload:
                    UnitAbility.objects.filter(unit_type=unit).delete()
                    for order, ab in enumerate(payload['abilities']):
                        UnitAbility.objects.create(unit_type=unit, order=order, **ab)

                self.stdout.write(
                    f'  OK: {name!r} -- {n_weapons} weapons, {n_abilities} abilities'
                )
                updated += 1

            if dry_run:
                self.stdout.write(self.style.WARNING('Dry run -- no changes written.'))
                transaction.set_rollback(True)

        self.stdout.write(self.style.SUCCESS(
            f'\nDone. {updated} updated, {skipped} skipped.'
        ))
