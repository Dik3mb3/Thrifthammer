"""
Management command: seed_raven_guard_datasheets

Refreshes stat lines, weapon profiles, and abilities for the Raven
Guard-exclusive units using 11th Edition data sourced from BSData/
wh40k-11e ("Imperium - Raven Guard.json") -- the same source used by
seed_raven_guard_points.py.

Usage:
    python manage.py seed_raven_guard_datasheets
    python manage.py seed_raven_guard_datasheets --dry-run

Notes:
- Does NOT touch points_cost or category -- those are handled entirely by
  seed_raven_guard_points.py. This command only refreshes stat_* fields,
  WeaponProfile rows, and UnitAbility rows.
- Scope is the 2 RG-exclusive rows only (Aethon Shaan, Kayvaan Shrike)
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
RAVEN_GUARD_DATASHEETS = {
    "Aethon Shaan": {
        "stats": {
            "stat_movement": "14\"",
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
                "name": "Claws of Severax",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "7",
                "skill": "2+",
                "strength": "5",
                "ap": "-2",
                "damage": "2",
                "keywords": "Sustained Hits 2, Twin-linked"
            }
        ],
        "abilities": [
            {
                "name": "Chapter Master of the Raven Guard",
                "description": "At the start of the Declare Battle Formations step, if your army includes Aethon Shaan and Kayvaan\nShrike, until the end of the battle, your Kayvaan Shrike unit loses its Lone Operative ability and it\nreplaces its Chapter Master keyword with Captain."
            },
            {
                "name": "Master of Shadows",
                "description": "In your Command phase, you can select one unit from your opponent\u2019s army. Until the start of your next Command phase, each time an Adeptus Astartes unit from your army declares a charge while it is within 12\" of that enemy unit, you can re-roll the Charge roll, but it must declare that enemy unit as a target of that charge (if possible)."
            },
            {
                "name": "Blackwing Mantle",
                "description": "You can target this model\u2019s unit with the Rapid Ingress and Heroic Intervention Stratagems for 0CP,\neven if you have already used that Stratagem on a different unit this phase."
            }
        ]
    },
    "Kayvaan Shrike": {
        "stats": {
            "stat_movement": "12\"",
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
                "name": "Blackout",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "2",
                "skill": "2+",
                "strength": "5",
                "ap": "-1",
                "damage": "2",
                "keywords": "Pistol, Precision"
            },
            {
                "name": "The Raven's Talons",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "7",
                "skill": "2+",
                "strength": "5",
                "ap": "-2",
                "damage": "2",
                "keywords": "Precision, Twin-linked"
            }
        ],
        "abilities": [
            {
                "name": "Trifold Path of Shadow",
                "description": "While this model is leading a unit, models in this unit cannot be targeted by ranged attacks unless the attacking model is within 12\"."
            },
            {
                "name": "Echo of the Ravenspire",
                "description": "At the end of your opponent\u2019s turn, if this model\u2019s unit is not within Engagement Range of any enemy models, you can remove it from the battlefield and place it into Strategic Reserves."
            },
            {
                "name": "Leader",
                "description": "This model can be attached to the following units:\n\n\u25a0 ASSAULT INTERCESSORS WITH JUMP PACKS\n\u25a0 VANGUARD VETERAN SQUAD WITH JUMP PACKS"
            },
            {
                "name": "Inspiring Commander",
                "description": "If you include this model in your army, until the end of the battle, non-Character models in Assault\nIntercessors with Jump Packs units from your army have an Objective Control characteristic of 2 while they are not Battle-shocked."
            }
        ]
    }
}


class Command(BaseCommand):
    """Refresh Raven Guard stat lines, weapon profiles, and abilities from BSData."""

    help = 'Refresh 11th Edition stats/weapons/abilities for Raven-Guard-exclusive units.'

    def add_arguments(self, parser):
        """Add --dry-run flag."""
        parser.add_argument(
            '--dry-run', action='store_true',
            help='Preview changes without writing to the database.',
        )

    def handle(self, *args, **options):
        """Iterate RAVEN_GUARD_DATASHEETS and refresh each unit's datasheet data."""
        dry_run = options['dry_run']
        updated = 0
        skipped = 0

        with transaction.atomic():
            for name, payload in RAVEN_GUARD_DATASHEETS.items():
                try:
                    unit = UnitType.objects.get(name=name, faction__name='Raven Guard')
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
