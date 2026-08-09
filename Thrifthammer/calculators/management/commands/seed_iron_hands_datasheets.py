"""
Management command: seed_iron_hands_datasheets

Refreshes stat lines, weapon profiles, and abilities for the Iron
Hands-exclusive units using 11th Edition data sourced from BSData/
wh40k-11e ("Imperium - Iron Hands.json") -- the same source used by
seed_iron_hands_points.py.

Usage:
    python manage.py seed_iron_hands_datasheets
    python manage.py seed_iron_hands_datasheets --dry-run

Notes:
- Does NOT touch points_cost or category -- those are handled entirely by
  seed_iron_hands_points.py. This command only refreshes stat_* fields,
  WeaponProfile rows, and UnitAbility rows.
- Scope is the 2 IH-exclusive rows only (Caanok Var, Iron Father Feirros)
  -- generic squads inherit their datasheets from the base Space Marines
  faction automatically.
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
IRON_HANDS_DATASHEETS = {
    "Caanok Var": {
        "stats": {
            "stat_movement": "5\"",
            "stat_toughness": 5,
            "stat_save": "2+",
            "stat_wounds": 6,
            "stat_leadership": "6+",
            "stat_oc": 1,
            "stat_invuln": "4+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Axiom - Strike",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "5",
                "skill": "2+",
                "strength": "8",
                "ap": "-2",
                "damage": "2"
            },
            {
                "name": "Axiom - Sweep",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "10",
                "skill": "2+",
                "strength": "5",
                "ap": "-2",
                "damage": "1"
            }
        ],
        "abilities": [
            {
                "name": "Cold and Calculating",
                "description": "Each time a model in this model\u2019s unit makes an attack that targets a Monster or Vehicle unit, that\nattack has the [LETHAL HITS] ability. Each time a model in this model\u2019s unit makes an attack that targets any other unit, that attack has the [SUSTAINED HITS 1] ability."
            },
            {
                "name": "Cerebrex Logic Engine",
                "description": "\u25a0 At the start of the Declare Battle Formations step, you can select one Adeptus Astartes Infantry unit from your army. Until the end of the battle, that unit gains the Scouts 6\" ability.\n\n\n\u25a0 After both players have deployed their armies, you can select one Adeptus Astartes unit from your army and redeploy it. When doing so, you can set that unit up in Strategic Reserves if you wish, regardless of how many units are already in Strategic Reserves."
            },
            {
                "name": "Leader",
                "description": "This model can be attached to the following units:\n\n\n\u25a0 TERMINATOR ASSAULT SQUAD\n\u25a0 TERMINATOR SQUAD"
            }
        ]
    },
    "Iron Father Feirros": {
        "stats": {
            "stat_movement": "5\"",
            "stat_toughness": 6,
            "stat_save": "2+",
            "stat_wounds": 6,
            "stat_leadership": "6+",
            "stat_oc": 1,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Gorgon's Wrath",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "3",
                "skill": "2+",
                "strength": "5",
                "ap": "-1",
                "damage": "2",
                "keywords": "Sustained Hits 2"
            },
            {
                "name": "Harrowhand",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "6",
                "skill": "3+",
                "strength": "7",
                "ap": "-2",
                "damage": "2",
                "keywords": "-"
            },
            {
                "name": "Medusan Manipuli",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "2",
                "skill": "3+",
                "strength": "8",
                "ap": "-2",
                "damage": "3",
                "keywords": "Extra Attacks"
            }
        ],
        "abilities": [
            {
                "name": "Rites of Tempering",
                "description": "While this model is leading a unit, models in that unit have the Feel No Pain 5+ ability"
            },
            {
                "name": "Iron Father",
                "description": "While this model is within 3\" of one or more friendly Adeptus Astartes Vehicle units, it has the Lone Operative ability."
            },
            {
                "name": "Master of the Forge",
                "description": "In your Command phase, select one friendly Adeptus Astartes Vehicle model within 3\" of this model. That model regains up to 3 lost wounds and, until the start of your next Command phase, each time that Vehicle model makes an attack, add 1 to the Hit roll. You cannot select a unit for this ability that has already been selected for the Blessing of the Omnissiah ability this phase, and vice versa."
            },
            {
                "name": "Leader",
                "description": "This model can be attached to the following units:\n\n\u25a0 AGGRESSOR SQUAD\n\u25a0 ERADICATOR SQUAD\n\u25a0 HEAVY INTERCESSOR SQUAD"
            },
            {
                "name": "Inspiring Commander",
                "description": "If you include this model in your army, until the end of the battle, non-Character models in Heavy\nIntercessor Squad units from your army have an Objective Control characteristic of 3 while they are\nnot Battle-shocked."
            }
        ]
    }
}


class Command(BaseCommand):
    """Refresh Iron Hands stat lines, weapon profiles, and abilities from BSData."""

    help = 'Refresh 11th Edition stats/weapons/abilities for Iron-Hands-exclusive units.'

    def add_arguments(self, parser):
        """Add --dry-run flag."""
        parser.add_argument(
            '--dry-run', action='store_true',
            help='Preview changes without writing to the database.',
        )

    def handle(self, *args, **options):
        """Iterate IRON_HANDS_DATASHEETS and refresh each unit's datasheet data."""
        dry_run = options['dry_run']
        updated = 0
        skipped = 0

        with transaction.atomic():
            for name, payload in IRON_HANDS_DATASHEETS.items():
                try:
                    unit = UnitType.objects.get(name=name, faction__name='Iron Hands')
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
