"""
Management command: seed_blood_angels_datasheets

Refreshes stat lines, weapon profiles, and abilities for the
Blood-Angels-specific units using 11th Edition data sourced from
BSData/wh40k-11e ("Imperium - Blood Angels.json") -- the same source used
by seed_blood_angels_points.py.

Usage:
    python manage.py seed_blood_angels_datasheets
    python manage.py seed_blood_angels_datasheets --dry-run

Notes:
- Does NOT touch points_cost or category -- those are handled entirely by
  seed_blood_angels_points.py. This command only refreshes stat_* fields,
  WeaponProfile rows, and UnitAbility rows.
- Scope: the 9 BA-exclusive rows (Astorath, Baal Predator, Blood Angels
  Captain, Chief Librarian Mephiston, Commander Dante, Lemartes,
  Sanguinary Guard, Sanguinary Priest, The Sanguinor), plus 'Dreadnought'
  (datasheet reused directly from the base Space Marines extraction --
  same physical unit/rules, just kept as its own active BA row per user
  direction so it can coexist with 'Librarian Dreadnought' on the shared
  SKU 48-137) and 'Librarian Dreadnought' (looked up under its literal
  BSData name "Librarian Dreadnought [Legends]" -- the only 11e entry that
  exists for it, included per explicit user direction despite the
  standard Legends-exclusion rule). Judiciar/Suppressor Squad are out of
  scope -- productless placeholders with no BA-specific datasheet source.
- Per-field safety rule: a unit's stats/weapons/abilities are only
  overwritten when BSData actually has that data for it. If extraction
  found nothing, the existing DB value/rows are left untouched.
- Known gap: 'Sanguinary Priest' has 0 weapon profiles in BSData -- same
  root cause as Black Templars' Land Raider Crusader (confirmed by
  inspection, not assumed): its "Wargear" selection group's entryLinks
  (Absolvor bolt pistol, etc.) reference a catalogue this file doesn't
  declare a link for, so the actual weapon entries aren't reachable from
  this data source. Left blank rather than fabricated.
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from calculators.models import UnitAbility, UnitType, WeaponProfile

# (name -> {stats?, weapons?, abilities?}). Missing keys mean "no data
# found for this field -- leave existing DB data untouched."
BLOOD_ANGELS_DATASHEETS = {
    "Astorath": {
        "stats": {
            "stat_movement": "12\"",
            "stat_toughness": 4,
            "stat_save": "2+",
            "stat_wounds": 5,
            "stat_leadership": "5+",
            "stat_oc": 1,
            "stat_invuln": "4+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "The Executioner's Axe",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "6",
                "skill": "2+",
                "strength": "7",
                "ap": "-3",
                "damage": "2",
                "keywords": "Devastating Wounds, Precision"
            }
        ],
        "abilities": [
            {
                "name": "Redeemer of the Lost",
                "description": "While this model is leading a unit, each time a model in that unit is destroyed by a melee attack, if that model has not fought this phase, roll one D6. On a 4+, do not remove it from play; that destroyed model can fight after the attacking model\u2019s unit has finished making its attacks, and is then removed from play."
            },
            {
                "name": "Mass of Doom",
                "description": "Each time this model\u2019s unit makes a Charge move, until the end of the turn, melee weapons equipped by models in that unit have the [DEVASTATING WOUNDS] ability."
            },
            {
                "name": "Leader",
                "description": "This model can be attached to the following unit:\n\n\u25a0 Death Company Marines with Jump Packs"
            }
        ]
    },
    "Baal Predator": {
        "stats": {
            "stat_movement": "12\"",
            "stat_toughness": 10,
            "stat_save": "3+",
            "stat_wounds": 11,
            "stat_leadership": "6+",
            "stat_oc": 3,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Heavy Flamer",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "D6",
                "skill": "N/A",
                "strength": "5",
                "ap": "-1",
                "damage": "1",
                "keywords": "Assault, Ignores Cover, Torrent"
            },
            {
                "name": "Heavy Bolter",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "3",
                "skill": "3+",
                "strength": "5",
                "ap": "-1",
                "damage": "2",
                "keywords": "Assault, Sustained Hits 1"
            },
            {
                "name": "Baal Flamestorm Cannon",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "D6+3",
                "skill": "N/A",
                "strength": "6",
                "ap": "-2",
                "damage": "2",
                "keywords": "Assault, Ignores Cover, Torrent"
            },
            {
                "name": "Twin Assault Cannon",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "6",
                "skill": "3+",
                "strength": "6",
                "ap": "0",
                "damage": "1",
                "keywords": "Assault, Devastating wounds, Twin-linked"
            }
        ],
        "abilities": [
            {
                "name": "Overcharged Engines",
                "description": "You can re-roll Advance rolls made for this model."
            }
        ]
    },
    "Blood Angels Captain": {
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
                "name": "Master-crafted Chainsword",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "7",
                "skill": "2+",
                "strength": "4",
                "ap": "-1",
                "damage": "2",
                "keywords": "-"
            },
            {
                "name": "Heavy Bolt Pistol",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "1",
                "skill": "2+",
                "strength": "4",
                "ap": "-1",
                "damage": "1",
                "keywords": "Pistol"
            }
        ],
        "abilities": [
            {
                "name": "Leader",
                "description": "This model can be attached to the following units:\n\n\u25a0 Assault Intercessor Squad\n\u25a0 Infernus Squad\n\u25a0 Intercessor Squad\n\u25a0 Sternguard Veteran Squad\n\u25a0 Company Heroes\n\u25a0 Tactical Squad"
            }
        ]
    },
    "Chief Librarian Mephiston": {
        "stats": {
            "stat_movement": "7\"",
            "stat_toughness": 5,
            "stat_save": "2+",
            "stat_wounds": 6,
            "stat_leadership": "6+",
            "stat_oc": 1,
            "stat_invuln": "5+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "\u27a4 Fury of the Ancients - Witchfire",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "3",
                "skill": "2+",
                "strength": "4",
                "ap": "-1",
                "damage": "D3",
                "keywords": "Pistol, Psychic, Sustained Hits 1"
            },
            {
                "name": "\u27a4 Fury of the Ancients - Focused Witchfire",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "3",
                "skill": "2+",
                "strength": "5",
                "ap": "-2",
                "damage": "D3",
                "keywords": "Hazardous, Pistol, Psychic, Sustained Hits 3"
            },
            {
                "name": "Vitarus",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "6",
                "skill": "2+",
                "strength": "9",
                "ap": "-3",
                "damage": "D3",
                "keywords": "Lethal Hits, Psychic"
            }
        ],
        "abilities": [
            {
                "name": "The Quickening [Psychic]",
                "description": "This model is eligible to declare a charge in a turn which it Advanced."
            },
            {
                "name": "Transfixing Gaze [Aura, Psychic]",
                "description": "While an enemy unit is within 6\" of this model, each time that unit is selected to Fall Back, it must take a Leadership test. If that test is failed, that unit must Remain Stationary this phase instead."
            }
        ]
    },
    "Commander Dante": {
        "stats": {
            "stat_movement": "12\"",
            "stat_toughness": 4,
            "stat_save": "2+",
            "stat_wounds": 6,
            "stat_leadership": "6+",
            "stat_oc": 1,
            "stat_invuln": "4+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Perdition",
                "weapon_type": "ranged",
                "range": "6\"",
                "attacks": "1",
                "skill": "2+",
                "strength": "9",
                "ap": "-4",
                "damage": "D6",
                "keywords": "Melta 2, Pistol, Sustained Hits D3"
            },
            {
                "name": "The Axe Mortalis",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "8",
                "skill": "2+",
                "strength": "8",
                "ap": "-3",
                "damage": "2",
                "keywords": "Lethal Hits"
            }
        ],
        "abilities": [
            {
                "name": "Death Mask of Sanguinius",
                "description": "At the start of the Fight phase, each enemy unit within 6\" of this model must take a Battle-shock test, subtracting 1 from that test when they do"
            },
            {
                "name": "Lord Regent of the Imperium Nihilus",
                "description": "While this model is leading a unit, add 1 to Advance and Charge rolls made for that unit and each time a model in that unit makes an attack, add 1 to the Hit roll."
            },
            {
                "name": "Leader",
                "description": "This model can be attached to the following units:\n\n\u25a0 Assault Squad with Jump Packs\n\u25a0 Sanguinary Guard\n\u25a0 Vanguard Veteran Squad with Jump Packs\n\u25a0 Assault Intercessors with Jump Packs"
            }
        ]
    },
    "Lemartes": {
        "stats": {
            "stat_movement": "12\"",
            "stat_toughness": 4,
            "stat_save": "3+",
            "stat_wounds": 4,
            "stat_leadership": "5+",
            "stat_oc": 1,
            "stat_invuln": "4+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "The Blood Crozius",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "5",
                "skill": "2+",
                "strength": "6",
                "ap": "-2",
                "damage": "2",
                "keywords": "Lethal Hits"
            },
            {
                "name": "Absolvor Bolt Pistol",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "1",
                "skill": "2+",
                "strength": "5",
                "ap": "-1",
                "damage": "2",
                "keywords": "Pistol"
            }
        ],
        "abilities": [
            {
                "name": "Guardian of the Lost",
                "description": "While this model is leading a unit, each time an attack is allocated to a model in that unit, subtract 1 from the Damage characteristic of that attack."
            },
            {
                "name": "Fury Unbound",
                "description": "While this model is leading a unit, melee weapons equipped by models in that unit have the [LETHAL HITS] ability."
            },
            {
                "name": "Leader",
                "description": "This model can be attached to the following unit:\n\n\u25a0 Death Company Marines with Jump Packs"
            }
        ]
    },
    "Librarian Dreadnought": {
        "stats": {
            "stat_movement": "8\"",
            "stat_toughness": 9,
            "stat_save": "2+",
            "stat_wounds": 8,
            "stat_leadership": "6+",
            "stat_oc": 3,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "\u27a4 Blood Lance - Focused Witchfire",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "12",
                "ap": "-3",
                "damage": "D6+3",
                "keywords": "Hazardous, Psychic, Sustained Hits D3"
            },
            {
                "name": "\u27a4 Blood Lance - Witchfire",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "10",
                "ap": "-3",
                "damage": "D6",
                "keywords": "Psychic, Sustained Hits D3"
            },
            {
                "name": "Furioso Fist",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "5",
                "skill": "3+",
                "strength": "12",
                "ap": "-3",
                "damage": "3",
                "keywords": "-"
            },
            {
                "name": "Furioso Force Halberd",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "1",
                "skill": "2+",
                "strength": "9",
                "ap": "-3",
                "damage": "D6+3",
                "keywords": "Extra Attacks, Psychic"
            }
        ],
        "abilities": [
            {
                "name": "Shield of Sanguinius (Aura, Psychic)",
                "description": "While a friendly Adeptus Astartes unit is within 6\" of this model, models in that unit have the Feel No Pain 5+ ability against mortal wounds and Psychic Attacks."
            },
            {
                "name": "Wings of Sanguinius (Psychic)",
                "description": "Once per turn, at the end of your Movement phase, one Psyker from your army with this ability can use it. If it does, roll one D6: on a 1, that Psyker suffers D3 mortal wounds; on a 2+, select one friendly Adeptus Astartes Infantry unit within 12\" of that Psyker and remove the selected unit from the battlefield, then set it up again anywhere on the battlefield that is more than 9\"\nhorizontally away from all enemy models."
            }
        ]
    },
    "Sanguinary Guard": {
        "stats": {
            "stat_movement": "12\"",
            "stat_toughness": 4,
            "stat_save": "2+",
            "stat_wounds": 3,
            "stat_leadership": "6+",
            "stat_oc": 1,
            "stat_invuln": "4+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Encarmine Blade",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "2+",
                "strength": "6",
                "ap": "-3",
                "damage": "2",
                "keywords": "-"
            },
            {
                "name": "Encarmine Spear",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "2+",
                "strength": "6",
                "ap": "-2",
                "damage": "2",
                "keywords": "Lance"
            },
            {
                "name": "Angelus Boltgun",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "2",
                "skill": "3+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Pistol"
            }
        ],
        "abilities": [
            {
                "name": "Angelic Visage",
                "description": "Each time a melee attack targets this unit, subtract 1 from the Hit roll"
            },
            {
                "name": "Heirs of Azkaellon",
                "description": "While a Character model is leading this unit, each time a melee attack targets this unit, subtract 1 from the Wound roll."
            },
            {
                "name": "Attached Unit",
                "description": "If a Captain model from your army with the Leader ability can be attached to Assault Intercessors with Jump Packs, it can be attached to this unit instead."
            },
            {
                "name": "Sanguinary Banner",
                "description": "Add 1 to the Objective Control characteristic of models in the bearer\u2019s unit."
            }
        ]
    },
    "Sanguinary Priest": {
        "stats": {
            "stat_movement": "6\"",
            "stat_toughness": 4,
            "stat_save": "3+",
            "stat_wounds": 4,
            "stat_leadership": "6+",
            "stat_oc": 1,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "abilities": [
            {
                "name": "Sanguinary Priest",
                "description": "While this model is leading a unit, models in that unit have the Feel No Pain 5+ ability"
            },
            {
                "name": "Blood Chalice",
                "description": "While this model is leading a unit, improve the Armour Penetration characteristic of melee weapons equipped by models in that unit by 1."
            },
            {
                "name": "Support",
                "description": "This model can be attached to the following units:\n- Assault Intercessor Squad\n- Bladeguard Veteran Squad\n- Desolation Squad\n- Devastator Squad\n- Hellblaster Squad\n- Infernus Squad\n- Intercessor Squad\n- Tactical Squad\n- Sternguard Veteran Squad\n\n\nYou can attach this model to one of the above units, even if one Captain, Chapter Master or Lieutenant model has already been attached to it. If you do, and that Bodyguard unit is destroyed, the Leader units attached to it become separate units, with their original Starting Strengths"
            }
        ]
    },
    "The Sanguinor": {
        "stats": {
            "stat_movement": "12\"",
            "stat_toughness": 4,
            "stat_save": "2+",
            "stat_wounds": 7,
            "stat_leadership": "6+",
            "stat_oc": 1,
            "stat_invuln": "4+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Encarmine Broadsword",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "8",
                "skill": "2+",
                "strength": "6",
                "ap": "-3",
                "damage": "2",
                "keywords": "Devastating Wounds"
            }
        ],
        "abilities": [
            {
                "name": "Aura of Fervour (Aura)",
                "description": "While a friendly Adeptus Astartes unit is within 6\" of this model, you can re-roll Battle-shock and Leadership tests taken for that unit"
            },
            {
                "name": "Miraculous Savior",
                "description": "(Once per battle, per army) At the end of your opponent's Charge phase (excluding the first battle round), you can select one enemy unit that made a charge move this phase. This unit can make an ingress move and must be set up engaged with that enemy unit. . That move does not prevent this unit from being eligible to move"
            }
        ]
    },
    "Dreadnought": {
        "stats": {
            "stat_movement": "6\"",
            "stat_toughness": 9,
            "stat_save": "2+",
            "stat_wounds": 8,
            "stat_leadership": "6+",
            "stat_oc": 3,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Dreadnought Combat Weapon",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "5",
                "skill": "3+",
                "strength": "12",
                "ap": "-2",
                "damage": "3",
                "keywords": "-"
            },
            {
                "name": "Heavy Flamer",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "D6",
                "skill": "N/A",
                "strength": "5",
                "ap": "-1",
                "damage": "1",
                "keywords": "Ignores Cover, Torrent"
            },
            {
                "name": "Storm bolter",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "2",
                "skill": "3+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Rapid Fire 2"
            },
            {
                "name": "\u27a4 Missile Launcher - Frag",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "D6",
                "skill": "3+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Blast"
            },
            {
                "name": "\u27a4 Missile Launcher - Krak",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "9",
                "ap": "-2",
                "damage": "D6",
                "keywords": "-"
            },
            {
                "name": "Close combat weapon",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "5",
                "skill": "3+",
                "strength": "6",
                "ap": "0",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "Assault Cannon",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "6",
                "skill": "3+",
                "strength": "6",
                "ap": "0",
                "damage": "1",
                "keywords": "Devastating Wounds"
            },
            {
                "name": "Multi-melta",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "2",
                "skill": "3+",
                "strength": "9",
                "ap": "-4",
                "damage": "D6",
                "keywords": "Melta 2"
            },
            {
                "name": "Twin lascannon",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "12",
                "ap": "-3",
                "damage": "D6+1",
                "keywords": "Twin-linked"
            },
            {
                "name": "\u27a4 Heavy Plasma Cannon - Standard",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "D3",
                "skill": "3+",
                "strength": "7",
                "ap": "-2",
                "damage": "2",
                "keywords": "Blast"
            },
            {
                "name": "\u27a4 Heavy Plasma Cannon",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "D3",
                "skill": "3+",
                "strength": "8",
                "ap": "-3",
                "damage": "3",
                "keywords": "Blast, Hazardous"
            }
        ],
        "abilities": [
            {
                "name": "Wisdom of the Ancients [Aura]",
                "description": "While a friendly Adeptus Astartes Infantry unit is within 6\" of this model, each time a model in that unit makes an attack, re-roll a Hit roll of 1."
            }
        ]
    }
}


class Command(BaseCommand):
    """Refresh Blood Angels stat lines, weapon profiles, and abilities from BSData."""

    help = 'Refresh 11th Edition stats/weapons/abilities for Blood-Angels-specific units.'

    def add_arguments(self, parser):
        """Add --dry-run flag."""
        parser.add_argument(
            '--dry-run', action='store_true',
            help='Preview changes without writing to the database.',
        )

    def handle(self, *args, **options):
        """Iterate BLOOD_ANGELS_DATASHEETS and refresh each unit's datasheet data."""
        dry_run = options['dry_run']
        updated = 0
        skipped = 0

        with transaction.atomic():
            for name, payload in BLOOD_ANGELS_DATASHEETS.items():
                try:
                    unit = UnitType.objects.get(name=name, faction__name='Blood Angels')
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
