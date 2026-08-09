"""
Management command: seed_salamanders_datasheets

Refreshes stat lines, weapon profiles, and abilities for the Salamanders-
exclusive units using 11th Edition data sourced from BSData/wh40k-11e
("Imperium - Salamanders.json") -- the same source used by
seed_salamanders_points.py.

Usage:
    python manage.py seed_salamanders_datasheets
    python manage.py seed_salamanders_datasheets --dry-run

Notes:
- Does NOT touch points_cost or category -- those are handled entirely by
  seed_salamanders_points.py. This command only refreshes stat_* fields,
  WeaponProfile rows, and UnitAbility rows.
- Scope is the 2 Salamanders-exclusive rows only (Adrax Agatone, Vulkan
  He'stan) -- generic squads inherit their datasheets from the base Space
  Marines faction automatically.
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
SALAMANDERS_DATASHEETS = {
    "Adrax Agatone": {
        "stats": {
            "stat_movement": "6\"",
            "stat_toughness": 4,
            "stat_save": "2+",
            "stat_wounds": 5,
            "stat_leadership": "6+",
            "stat_oc": 1,
            "stat_invuln": "4+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Drakkis",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "D6+3",
                "skill": "N/A",
                "strength": "4",
                "ap": "-1",
                "damage": "1",
                "keywords": "Ignores Cover, Pistol, Torrent"
            },
            {
                "name": "Malleus Noctum",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "5",
                "skill": "2+",
                "strength": "10",
                "ap": "-2",
                "damage": "3",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Unto the Anvil",
                "description": "While this model is leading a unit, each time a model in that unit makes a melee attack, you can re-roll the Wound roll."
            },
            {
                "name": "Lord of the Pyroclasts",
                "description": "While an enemy unit is within Engagement Range of this model, halve the Objective Control characteristic of models in that enemy unit"
            },
            {
                "name": "Leader",
                "description": "This model can be attached to the following units:\n\n\u25a0 ASSAULT INTERCESSOR SQUAD\n\u25a0 BLADEGUARD VETERAN SQUAD\n\u25a0 COMPANY HEROES\n\u25a0 INFERNUS SQUAD\n\u25a0 INTERCESSOR SQUAD\n\u25a0 STERNGUARD VETERAN SQUAD\n\u25a0 TACTICAL SQUAD"
            }
        ]
    },
    "Vulkan He'stan": {
        "stats": {
            "stat_movement": "6\"",
            "stat_toughness": 4,
            "stat_save": "2+",
            "stat_wounds": 5,
            "stat_leadership": "6+",
            "stat_oc": 1,
            "stat_invuln": "4+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Gauntlet of the Forge",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "D6+3",
                "skill": "N/A",
                "strength": "6",
                "ap": "-1",
                "damage": "1",
                "keywords": "Ignores Cover, Pistol, Torrent"
            },
            {
                "name": "Spear of Vulkan",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "6",
                "skill": "2+",
                "strength": "6",
                "ap": "-2",
                "damage": "2",
                "keywords": "Devastating Wounds"
            }
        ],
        "abilities": [
            {
                "name": "Forgefather",
                "description": "In your Shooting phase, select one enemy unit within 24\" of and visible to this model. Until the end of the phase, each time a friendly Adeptus Astartes model makes a ranged attack with a Torrent or Melta weapon that targets that enemy unit, you can re-roll the Wound roll"
            },
            {
                "name": "Seeker of the Unfound",
                "description": "The first time this model is set up on the battlefield, select one objective marker on the battlefield. While this model is within range of that objective marker, it has an Objective Control characteristic of 10, a Leadership characteristic of 5+ and the Feel No Pain 4+ ability."
            },
            {
                "name": "Leader",
                "description": "This model can be attached to the following units:\n\n\u25a0 ASSAULT INTERCESSOR SQUAD\n\u25a0 COMPANY HEROES\n\u25a0 INFERNUS SQUAD\n\u25a0 TACTICAL SQUAD"
            },
            {
                "name": "Inspiring Commander",
                "description": "If you include this model in your army, until the end of the battle, non-Character models in Infernus Squad units from your army have an Objective Control characteristic of 2 while they are not Battle-shocked."
            }
        ]
    }
}


class Command(BaseCommand):
    """Refresh Salamanders stat lines, weapon profiles, and abilities from BSData."""

    help = "Refresh 11th Edition stats/weapons/abilities for Salamanders-exclusive units."

    def add_arguments(self, parser):
        """Add --dry-run flag."""
        parser.add_argument(
            '--dry-run', action='store_true',
            help='Preview changes without writing to the database.',
        )

    def handle(self, *args, **options):
        """Iterate SALAMANDERS_DATASHEETS and refresh each unit's datasheet data."""
        dry_run = options['dry_run']
        updated = 0
        skipped = 0

        with transaction.atomic():
            for name, payload in SALAMANDERS_DATASHEETS.items():
                try:
                    unit = UnitType.objects.get(name=name, faction__name='Salamanders')
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
