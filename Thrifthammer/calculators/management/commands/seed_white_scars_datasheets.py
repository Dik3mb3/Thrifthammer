"""
Management command: seed_white_scars_datasheets

Refreshes stat lines, weapon profiles, and abilities for White Scars
units using 11th Edition data sourced from BSData/wh40k-11e ("Imperium -
Adeptus Astartes - White Scars.json") -- the same source used by
seed_white_scars_points.py.

Usage:
    python manage.py seed_white_scars_datasheets
    python manage.py seed_white_scars_datasheets --dry-run

Notes:
- Does NOT touch points_cost or category -- those are handled entirely by
  seed_white_scars_points.py. This command only refreshes stat_* fields,
  WeaponProfile rows, and UnitAbility rows.
- Scope is both White-Scars-exclusive rows (Kor\'sarro Khan, Suboden
  Khan) -- both resolved cleanly on the first pass, 0 missing
  stats/weapons/abilities, 0 markdown artifacts.
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from calculators.models import UnitAbility, UnitType, WeaponProfile

# (name -> {stats?, weapons?, abilities?}). Missing keys mean "no data
# found for this field -- leave existing DB data untouched."
WHITE_SCARS_DATASHEETS = {
    "Kor'sarro Khan": {
        "stats": {
            "stat_movement": "6\"",
            "stat_toughness": 4,
            "stat_save": "3+",
            "stat_wounds": 5,
            "stat_leadership": "6+",
            "stat_oc": 1,
            "stat_invuln": "4+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Moonfang",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "6",
                "skill": "2+",
                "strength": "5",
                "ap": "-2",
                "damage": "2",
                "keywords": "Devastating Wounds, Precision"
            }
        ],
        "abilities": [
            {
                "name": "For the Khan!",
                "description": "While this model is leading a unit, ranged weapons equipped by models in that unit have the [ASSAULT] ability and melee weapons equipped by models in that unit have the [LANCE] ability."
            },
            {
                "name": "Trophy Taker",
                "description": "Each time this model destroys an enemy Character model, you gain 1CP"
            },
            {
                "name": "Leader",
                "description": "This model can be attached to the following units:\n\n\u25a0 ASSAULT INTERCESSOR SQUAD\n\u25a0 BLADEGUARD VETERAN SQUAD\n\u25a0 COMPANY HEROES\n\u25a0 INTERCESSOR SQUAD\n\u25a0 STERNGUARD VETERAN SQUAD\n\u25a0 TACTICAL SQUAD"
            },
            {
                "name": "Inspiring Commander",
                "description": "If you include this model in your army, until the end of the battle, non-Character models in Outrider Squad units from your army have an Objective Control characteristic of 3 while they are not Battle-shocked."
            }
        ]
    },
    "Suboden Khan": {
        "stats": {
            "stat_movement": "12\"",
            "stat_toughness": 5,
            "stat_save": "3+",
            "stat_wounds": 8,
            "stat_leadership": "6+",
            "stat_oc": 2,
            "stat_invuln": "4+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Onslaught Gatling Cannon",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "8",
                "skill": "2+",
                "strength": "5",
                "ap": "0",
                "damage": "1",
                "keywords": "Devastating Wounds"
            },
            {
                "name": "Stormtooth",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "6",
                "skill": "2+",
                "strength": "6",
                "ap": "-2",
                "damage": "2",
                "keywords": "Lance, Anti-monster 4+, Anti-vehicle 4+"
            },
            {
                "name": "Power Sword",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "8",
                "skill": "2+",
                "strength": "5",
                "ap": "-2",
                "damage": "1",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Spear of Chogoris",
                "description": "This model\u2019s unit is eligible to shoot and declare a charge in a turn in which it Advanced or Fell Back. If that unit is already eligible to shoot and declare a charge in a turn in which it Advanced, add 1 to Advance and Charge rolls made for that unit instead."
            },
            {
                "name": "Skilled Riders",
                "description": "Each time a model in this model\u2019s unit makes a Normal, Advance, Fall Back or Charge move, it can move horizontally through terrain features."
            },
            {
                "name": "Leader",
                "description": "This model can be attached to the following units:\n\n\nOUTRIDER SQUAD"
            }
        ]
    }
}


class Command(BaseCommand):
    """Refresh White Scars stat lines, weapon profiles, and abilities from BSData."""

    help = 'Refresh 11th Edition stats/weapons/abilities for White Scars units.'

    def add_arguments(self, parser):
        """Add --dry-run flag."""
        parser.add_argument(
            '--dry-run', action='store_true',
            help='Preview changes without writing to the database.',
        )

    def handle(self, *args, **options):
        """Iterate WHITE_SCARS_DATASHEETS and refresh each unit's datasheet data."""
        dry_run = options['dry_run']
        updated = 0
        skipped = 0

        with transaction.atomic():
            for name, payload in WHITE_SCARS_DATASHEETS.items():
                try:
                    unit = UnitType.objects.get(name=name, faction__name='White Scars')
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
