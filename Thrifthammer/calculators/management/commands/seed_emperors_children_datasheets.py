"""
Management command: seed_emperors_children_datasheets

Refreshes stat lines, weapon profiles, and abilities for Emperor's
Children units using 11th Edition data sourced from BSData/wh40k-11e
("Chaos - Emperor's Children.json") -- the same source used by
seed_emperors_children_points.py.

Usage:
    python manage.py seed_emperors_children_datasheets
    python manage.py seed_emperors_children_datasheets --dry-run

Notes:
- Does NOT touch points_cost or category -- those are handled entirely by
  seed_emperors_children_points.py. This command only refreshes stat_*
  fields, WeaponProfile rows, and UnitAbility rows.
- Emperor's Children is self-contained (not a thin overlay), same
  architecture as Death Guard -- every one of these 23 units has its own
  full datasheet in BSData, not inherited from Chaos Space Marines.
- Per-field safety rule: a unit's stats/weapons/abilities are only
  overwritten when BSData actually has that data for it. If extraction
  found nothing, the existing DB value/rows are left untouched.
- All 23 active units resolved cleanly -- 0 missing stats/weapons/
  abilities, 0 overlong stat fields.
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from calculators.models import UnitAbility, UnitType, WeaponProfile

# (name -> {stats?, weapons?, abilities?}). Missing keys mean "no data
# found for this field -- leave existing DB data untouched."
EMPERORS_CHILDREN_DATASHEETS = {
    "Chaos Land Raider": {
        "stats": {
            "stat_movement": "10\"",
            "stat_toughness": 12,
            "stat_save": "2+",
            "stat_wounds": 16,
            "stat_leadership": "6+",
            "stat_oc": 5,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Armoured tracks",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "6",
                "skill": "4+",
                "strength": "8",
                "ap": "0",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "Soulshatter lascannon",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "2",
                "skill": "3+",
                "strength": "12",
                "ap": "-3",
                "damage": "D6+1",
                "keywords": "-"
            },
            {
                "name": "Havoc launcher",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "D6",
                "skill": "3+",
                "strength": "5",
                "ap": "0",
                "damage": "1",
                "keywords": "Blast"
            },
            {
                "name": "Twin heavy bolter",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "3",
                "skill": "3+",
                "strength": "5",
                "ap": "-1",
                "damage": "2",
                "keywords": "Sustained Hits 1, Twin-linked"
            },
            {
                "name": "Combi-bolter",
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
                "name": "Combi-weapon",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "1",
                "skill": "4+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Anti-INFANTRY 4+, Devastating Wounds, Rapid Fire 1"
            }
        ],
        "abilities": [
            {
                "name": "Assault Ramp",
                "description": "Each time a unit disembarks from this model after it has made a Normal move, that unit is still eligible to declare a charge this turn."
            },
            {
                "name": "Damaged: 1-5 wounds remaining",
                "description": "While this model has 1-5 wounds remaining, each time this model makes an attack, subtract 1 from the Hit roll."
            }
        ]
    },
    "Chaos Rhino": {
        "stats": {
            "stat_movement": "12\"",
            "stat_toughness": 9,
            "stat_save": "3+",
            "stat_wounds": 10,
            "stat_leadership": "6+",
            "stat_oc": 2,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Armoured tracks",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "3",
                "skill": "4+",
                "strength": "6",
                "ap": "0",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "Combi-bolter",
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
                "name": "Havoc launcher",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "D6",
                "skill": "3+",
                "strength": "5",
                "ap": "0",
                "damage": "1",
                "keywords": "Blast"
            },
            {
                "name": "Combi-weapon",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "1",
                "skill": "4+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Anti-INFANTRY 4+, Devastating Wounds, Rapid Fire 1"
            }
        ],
        "abilities": [
            {
                "name": "Assault Vehicle",
                "description": "Units can disembark from this Vehicle after it has Advanced. Units that do so count as having made a Normal move that phase, and cannot declare a charge in the same turn, but can otherwise act normally."
            }
        ]
    },
    "Chaos Spawn": {
        "stats": {
            "stat_movement": "10\"",
            "stat_toughness": 5,
            "stat_save": "4+",
            "stat_wounds": 4,
            "stat_leadership": "7+",
            "stat_oc": 1,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Hideous Mutations",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "D6+2",
                "skill": "4+",
                "strength": "5",
                "ap": "-1",
                "damage": "2",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Scuttling Horrors",
                "description": "In your opponent's Movement phase, if an enemy unit ends a move within 8\u201d of this unit, if this unit is not within Engagement Range of one or more enemy units, this unit can make a Normal move of up to 6\u201d."
            }
        ]
    },
    "Chaos Terminators": {
        "stats": {
            "stat_movement": "6\"",
            "stat_toughness": 5,
            "stat_save": "2+",
            "stat_wounds": 3,
            "stat_leadership": "6+",
            "stat_oc": 1,
            "stat_invuln": "4+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Combi-bolter",
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
                "name": "Accursed weapon",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "3+",
                "strength": "5",
                "ap": "-2",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "Combi-weapon",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "1",
                "skill": "4+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Anti-INFANTRY 4+, Devastating Wounds, Rapid Fire 1"
            },
            {
                "name": "Chainfist",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "3",
                "skill": "4+",
                "strength": "8",
                "ap": "-2",
                "damage": "2",
                "keywords": "Anti-VEHICLE 3+"
            },
            {
                "name": "Power fist",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "3",
                "skill": "3+",
                "strength": "8",
                "ap": "-2",
                "damage": "2",
                "keywords": "-"
            },
            {
                "name": "Paired accursed weapons",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "5",
                "skill": "3+",
                "strength": "5",
                "ap": "-2",
                "damage": "1",
                "keywords": "Twin-linked"
            },
            {
                "name": "Heavy flamer",
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
                "name": "Reaper autocannon",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "4",
                "skill": "3+",
                "strength": "7",
                "ap": "-1",
                "damage": "1",
                "keywords": "Devastating Wounds, Sustained Hits 1"
            }
        ],
        "abilities": [
            {
                "name": "Lethal Obsession",
                "description": "In your Shooting phase, after this unit has shot, you can use this ability. If you do, select one enemy unit hit by those ranged attacks. Until the end of the turn, when this unit declares a charge:\n- This unit can re-roll that charge roll.\n- This unit must end that charge move engaged with that enemy unit."
            },
            {
                "name": "Frenzied Ferocity",
                "description": "This unit's attacks have [SUSTAINED HITS 1]."
            }
        ]
    },
    "Daemon Prince of Slaanesh": {
        "stats": {
            "stat_movement": "10\"",
            "stat_toughness": 10,
            "stat_save": "2+",
            "stat_wounds": 10,
            "stat_leadership": "6+",
            "stat_oc": 3,
            "stat_invuln": "4+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "\u27a4 Hellforged weapons - strike",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "6",
                "skill": "2+",
                "strength": "8",
                "ap": "-2",
                "damage": "3",
                "keywords": "-"
            },
            {
                "name": "\u27a4 Hellforged weapons - sweep",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "14",
                "skill": "2+",
                "strength": "6",
                "ap": "0",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "Infernal cannon",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "3",
                "skill": "2+",
                "strength": "5",
                "ap": "-1",
                "damage": "2",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Lord of Excess",
                "description": "While this model is within 3\" of one or more friendly Slaanesh Infantry, this model has the Lone Operative ability."
            },
            {
                "name": "Excessive Vigour (Aura)",
                "description": "While a friendly Slaanesh unit is within 6\" of this model, if that unit made a Charge move this turn, improve the Armour Penetration characteristic of melee weapons equipped by that unit by 1."
            },
            {
                "name": "Ecstatic Death",
                "description": "If this model is destroyed by a melee attack, if it has not fought this phase, roll one D6: on a 2+, do not remove it from play. This model can fight after the attacking unit has finished making its attacks, and is then removed from play."
            }
        ]
    },
    "Daemon Prince of Slaanesh with Wings": {
        "stats": {
            "stat_movement": "14\"",
            "stat_toughness": 9,
            "stat_save": "2+",
            "stat_wounds": 10,
            "stat_leadership": "6+",
            "stat_oc": 3,
            "stat_invuln": "4+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "\u27a4 Hellforged weapons - strike",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "6",
                "skill": "2+",
                "strength": "8",
                "ap": "-2",
                "damage": "3",
                "keywords": "-"
            },
            {
                "name": "\u27a4 Hellforged weapons - sweep",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "14",
                "skill": "2+",
                "strength": "6",
                "ap": "0",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "Infernal cannon",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "3",
                "skill": "2+",
                "strength": "5",
                "ap": "-1",
                "damage": "2",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Daemonic Destruction",
                "description": "Each time this model ends a Charge move, select one enemy unit within Engagement Range of this model and roll one D6 for each of this model's remaining wounds: for each 4+, that enemy unit suffers 1 mortal wound (to a maximum of 6 mortal wounds)."
            },
            {
                "name": "Stimulated by Pain",
                "description": "Each time an attack is allocated to this model, subtract 1 from the Damage characteristic of that attack."
            }
        ]
    },
    "Daemonettes of Slaanesh": {
        "stats": {
            "stat_movement": "9\"",
            "stat_toughness": 3,
            "stat_save": "7+",
            "stat_wounds": 1,
            "stat_leadership": "7+",
            "stat_oc": 1,
            "stat_invuln": "5+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Slashing claws",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "3",
                "skill": "3+",
                "strength": "4",
                "ap": "-1",
                "damage": "1",
                "keywords": "Devastating Wounds"
            }
        ],
        "abilities": [
            {
                "name": "Horrifying Beauty",
                "description": "At the start of the Fight phase, each enemy unit in Engagement Range of one or more units from your army with this ability must take a Battle-shock test, subtracting 1 from that test if that enemy unit is Below Half-strength."
            },
            {
                "name": "Daemonic Icon",
                "description": "Models in the bearer's unit have a Leadership characteristic of 6+."
            },
            {
                "name": "Instrument of Chaos",
                "description": "Add 1 to Charge rolls made for the bearer's unit."
            }
        ]
    },
    "Defiler": {
        "stats": {
            "stat_movement": "12\"",
            "stat_toughness": 11,
            "stat_save": "3+",
            "stat_wounds": 18,
            "stat_leadership": "6+",
            "stat_oc": 5,
            "stat_invuln": "5+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Shearing claws - strike",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "5",
                "skill": "3+",
                "strength": "16",
                "ap": "-3",
                "damage": "D6+1",
                "keywords": "Precision"
            },
            {
                "name": "Shearing claws - sweep",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "10",
                "skill": "3+",
                "strength": "6",
                "ap": "-2",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "\u27a4 Heavy missile launcher - frag",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "2D6",
                "skill": "3+",
                "strength": "5",
                "ap": "-1",
                "damage": "1",
                "keywords": "Blast"
            },
            {
                "name": "\u27a4 Heavy missile launcher - krak",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "2",
                "skill": "3+",
                "strength": "10",
                "ap": "-2",
                "damage": "D6+1",
                "keywords": "-"
            },
            {
                "name": "Electroscourge",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "5",
                "skill": "3+",
                "strength": "12",
                "ap": "-2",
                "damage": "2",
                "keywords": "Extra Attacks, Sustained Hits 2"
            },
            {
                "name": "Hades lascannon",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "2",
                "skill": "3+",
                "strength": "12",
                "ap": "-3",
                "damage": "D6+1",
                "keywords": "-"
            },
            {
                "name": "Heavy reaper autocannon",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "4",
                "skill": "3+",
                "strength": "9",
                "ap": "-1",
                "damage": "3",
                "keywords": "Devastating Wounds, Sustained Hits 1"
            },
            {
                "name": "Hades battle cannon",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "D6+3",
                "skill": "3+",
                "strength": "10",
                "ap": "-1",
                "damage": "3",
                "keywords": "Blast"
            },
            {
                "name": "Ectoplasma destructor",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "D6",
                "skill": "3+",
                "strength": "12",
                "ap": "-3",
                "damage": "3",
                "keywords": "Blast"
            },
            {
                "name": "Heavy baleflamer",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "D6+3",
                "skill": "N/A",
                "strength": "7",
                "ap": "-2",
                "damage": "2",
                "keywords": "Ignores Cover, Torrent"
            },
            {
                "name": "Excruciator cannon",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "6",
                "skill": "3+",
                "strength": "6",
                "ap": "-1",
                "damage": "2",
                "keywords": "-"
            },
            {
                "name": "Magma cutter",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "2",
                "skill": "3+",
                "strength": "9",
                "ap": "-4",
                "damage": "D6",
                "keywords": "Melta 2"
            }
        ],
        "abilities": [
            {
                "name": "Scuttling Walker",
                "description": "Each time this unit makes a Normal, Advance or Fall Back move, it can move through models (excluding Titanic models) and terrain features. When doing so, it can move within Engagement Range of enemy models, but cannot end that move within Engagement Range of them, and any Desperate Escape test is automatically passed."
            },
            {
                "name": "Revel in Desecration",
                "description": "Each time this model makes an attack that targets an enemy unit that is not below Half-strength, add 1 to the Hit roll."
            }
        ]
    },
    "Fiends": {
        "stats": {
            "stat_movement": "12\"",
            "stat_toughness": 5,
            "stat_save": "7+",
            "stat_wounds": 4,
            "stat_leadership": "7+",
            "stat_oc": 2,
            "stat_invuln": "5+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Barbed tail and dissecting claws",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "5",
                "skill": "3+",
                "strength": "5",
                "ap": "-2",
                "damage": "2",
                "keywords": "Devastating Wounds"
            }
        ],
        "abilities": [
            {
                "name": "Soporific Musk",
                "description": "Each time an enemy unit (excluding Monsters and Vehicles) within Engagement Range of one or more units from your army with this ability Falls Back, models in that unit must take Desperate Escape tests. When doing so, if that enemy unit is also Battle-shocked, subtract 1 from each of those Desperate Escape tests."
            }
        ]
    },
    "Flawless Blades": {
        "stats": {
            "stat_movement": "8\"",
            "stat_toughness": 5,
            "stat_save": "3+",
            "stat_wounds": 3,
            "stat_leadership": "6+",
            "stat_oc": 1,
            "stat_invuln": "5+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Blissblade",
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
                "name": "Bolt pistol",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Pistol"
            }
        ],
        "abilities": [
            {
                "name": "Daemonic Patrons",
                "description": "Each time this unit is selected to fight, it can call upon daemonic patrons. If it does, until the end of the phase, each time a model in this unit makes an attack. an unmodified Wound roll of 3+ scores a Critical Wound. At the end of the Fight phase, if this unit called upon daemonic patrons this phase and no enemy models were destroyed by attacks made by models in this unit this phase, one model in this unit is destroyed."
            },
            {
                "name": "Eager Patrons",
                "description": "This unit has +2\" M."
            },
            {
                "name": "Beguiling Grotesquerie",
                "description": "Enemy units cannot target this unit with snap shooting attacks."
            }
        ]
    },
    "Fulgrim \u2013 Daemon Primarch of Slaanesh": {
        "stats": {
            "stat_movement": "16\"",
            "stat_toughness": 11,
            "stat_save": "2+",
            "stat_wounds": 16,
            "stat_leadership": "5+",
            "stat_oc": 6,
            "stat_invuln": "4+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Malefic lash",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "6",
                "skill": "2+",
                "strength": "8",
                "ap": "-2",
                "damage": "2",
                "keywords": "Sustained Hits 1"
            },
            {
                "name": "Serpentine tail",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "6",
                "skill": "2+",
                "strength": "6",
                "ap": "-1",
                "damage": "1",
                "keywords": "Extra Attacks"
            },
            {
                "name": "\u27a4 Daemonic blades - strike",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "6",
                "skill": "2+",
                "strength": "14",
                "ap": "-3",
                "damage": "D6+1",
                "keywords": "Sustained Hits 1"
            },
            {
                "name": "\u27a4 Daemonic blades - sweep",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "12",
                "skill": "2+",
                "strength": "8",
                "ap": "-2",
                "damage": "2",
                "keywords": "Sustained Hits 1"
            }
        ],
        "abilities": [
            {
                "name": "Daemonic Poisons",
                "description": "In your Shooting phase and the Fight phase, after this model has finished making its attacks, select one enemy unit hit by one or more of those attacks. Until the end of the battle, that enemy unit is poisoned. At the start of each player's Command phase, roll one D6 for each poisoned enemy unit on the battlefield: on a 4+, that enemy unit suffers D3 mortal wounds."
            },
            {
                "name": "Daemon Prince of Slaanesh",
                "description": "At the start of your opponent's Command phase, select one of the abilities in the Daemon Prince of Slaanesh section. Until the start of your opponent's next Command phase, this model has that ability."
            },
            {
                "name": "Damaged: 1-6 Wounds Remaining",
                "description": "While this model has 1-6 wounds remaining, each time this model makes an attack, subtract 1 from the Hit roll."
            },
            {
                "name": "Supreme Commander",
                "description": "If this model is in your army, it must be your Warlord."
            },
            {
                "name": "Serpentine",
                "description": "Each time this model makes a Normal, Advance or Fall Back move, it can move over sections of terrain features that are 4\" or less in height."
            }
        ]
    },
    "Heldrake": {
        "stats": {
            "stat_movement": "12\"",
            "stat_toughness": 10,
            "stat_save": "3+",
            "stat_wounds": 14,
            "stat_leadership": "7+",
            "stat_oc": None,
            "stat_invuln": "5+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Heldrake claws",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "5",
                "skill": "3+",
                "strength": "7",
                "ap": "-1",
                "damage": "2",
                "keywords": "Anti-FLY 2+, Devastating Wounds"
            },
            {
                "name": "Baleflamer",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "D6+3",
                "skill": "N/A",
                "strength": "6",
                "ap": "-1",
                "damage": "2",
                "keywords": "Ignores Cover, Torrent"
            },
            {
                "name": "Hades autocannon",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "6",
                "skill": "3+",
                "strength": "8",
                "ap": "-1",
                "damage": "2",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Airborne Predator",
                "description": "Each time this model ends a Normal move, you can select one enemy unit that it moved over during that move and roll two D6, adding 1 to each result if that enemy unit can FLY: for each 4+, that enemy unit suffers D3 mortal wounds."
            }
        ]
    },
    "Infractors": {
        "stats": {
            "stat_movement": "7\"",
            "stat_toughness": 4,
            "stat_save": "3+",
            "stat_wounds": 2,
            "stat_leadership": "6+",
            "stat_oc": 2,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Bolt pistol",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Pistol"
            },
            {
                "name": "\u27a4 Plasma pistol - standard",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "7",
                "ap": "-2",
                "damage": "1",
                "keywords": "Pistol"
            },
            {
                "name": "\u27a4 Plasma pistol - supercharge",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "8",
                "ap": "-3",
                "damage": "2",
                "keywords": "Hazardous, Pistol"
            },
            {
                "name": "Rapture lash",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "6",
                "skill": "3+",
                "strength": "4",
                "ap": "-1",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "Power sword",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "3+",
                "strength": "5",
                "ap": "-2",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "Duelling sabre",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "3+",
                "strength": "4",
                "ap": "-1",
                "damage": "1",
                "keywords": "Precision"
            }
        ],
        "abilities": [
            {
                "name": "Excessive Assault",
                "description": "Each time a model in this unit targets an enemy unit with a melee attack, re-roll a Wound roll of 1. If that enemy unit is within range of an objective marker, you can re-roll the Wound roll instead."
            },
            {
                "name": "Icon of Excess",
                "description": "At the end of your Shooting phase or the Fight phase, if the bearer's unit destroyed one or more enemy units this phase, the bearer's unit takes a Leadership test. If that test is passed, you gain 1CP."
            }
        ]
    },
    "Keeper of Secrets": {
        "stats": {
            "stat_movement": "14\"",
            "stat_toughness": 10,
            "stat_save": "5+",
            "stat_wounds": 18,
            "stat_leadership": "6+",
            "stat_oc": 5,
            "stat_invuln": "4+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "\u27a4 Phantasmagoria - witchfire",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "6",
                "skill": "2+",
                "strength": "6",
                "ap": "-2",
                "damage": "1",
                "keywords": "Devastating Wounds, Psychic"
            },
            {
                "name": "\u27a4 Phantasmagoria - focused witchfire",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "9",
                "skill": "2+",
                "strength": "6",
                "ap": "-2",
                "damage": "1",
                "keywords": "Devastating Wounds, Hazardous, Psychic"
            },
            {
                "name": "Snapping claws",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "2+",
                "strength": "6",
                "ap": "-2",
                "damage": "3",
                "keywords": "Devastating Wounds, Extra Attacks"
            },
            {
                "name": "Witstealer sword",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "6",
                "skill": "2+",
                "strength": "8",
                "ap": "-2",
                "damage": "3",
                "keywords": "-"
            },
            {
                "name": "Living whip",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "6",
                "skill": "2+",
                "strength": "6",
                "ap": "-1",
                "damage": "2",
                "keywords": "Assault"
            },
            {
                "name": "Ritual knife",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "3",
                "skill": "2+",
                "strength": "6",
                "ap": "-2",
                "damage": "2",
                "keywords": "Extra Attacks"
            }
        ],
        "abilities": [
            {
                "name": "Daemon Lord of Slaanesh (Aura)",
                "description": "While a friendly Legions of Excess unit is within 6\" of this model, improve the Armour Penetration of melee weapons in that unit by 1."
            },
            {
                "name": "Mesmerising Form",
                "description": "Each time an attack targets this model, subtract 1 from the Hit roll."
            },
            {
                "name": "Shining aegis",
                "description": "The bearer has a Save characteristic of 3+."
            }
        ]
    },
    "Lord Exultant": {
        "stats": {
            "stat_movement": "7\"",
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
                "name": "Close combat weapon",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "6",
                "skill": "2+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "Bolt pistol",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Pistol"
            },
            {
                "name": "Rapture lash",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "2+",
                "strength": "4",
                "ap": "-1",
                "damage": "1",
                "keywords": "Extra Attacks"
            },
            {
                "name": "\u27a4 Plasma pistol - standard",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "7",
                "ap": "-2",
                "damage": "1",
                "keywords": "Pistol"
            },
            {
                "name": "\u27a4 Plasma pistol - supercharge",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "8",
                "ap": "-3",
                "damage": "2",
                "keywords": "Hazardous, Pistol"
            },
            {
                "name": "Power fist",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "3",
                "skill": "3+",
                "strength": "8",
                "ap": "-2",
                "damage": "2",
                "keywords": "-"
            },
            {
                "name": "Phoenix power spear",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "5",
                "skill": "2+",
                "strength": "7",
                "ap": "-2",
                "damage": "2",
                "keywords": "Lance"
            },
            {
                "name": "Master-crafted power sword",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "5",
                "skill": "2+",
                "strength": "5",
                "ap": "-2",
                "damage": "2",
                "keywords": "Precision"
            },
            {
                "name": "Screamer pistol",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "3",
                "skill": "2+",
                "strength": "5",
                "ap": "-1",
                "damage": "2",
                "keywords": "Ignores Cover, Pistol"
            }
        ],
        "abilities": [
            {
                "name": "Perfectionists",
                "description": "While this model is leading a unit, weapons equipped by models in that unit have the [LETHAL HITS] ability."
            },
            {
                "name": "Euphoric Strikes",
                "description": "Once per battle, at the start of the Fight phase, this model can use this ability. If it does so, until the end of the phase, add 3 to the Attacks characteristic of melee weapons equipped by this model and improve the Armour Penetration characteristic of those weapons by 1."
            },
            {
                "name": "Lord of the Host",
                "description": "If this model is attached to an Emperor's Children Battleline unit during the Declare Battle Formations step, this model has the Infiltrators and Scouts 6\" ability."
            },
            {
                "name": "Leader",
                "description": "This model can be attached to the following units: Infractors; Tormentors"
            }
        ]
    },
    "Lord Kakophonist": {
        "stats": {
            "stat_movement": "6\"",
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
                "name": "Screamer pistol",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "3",
                "skill": "2+",
                "strength": "5",
                "ap": "-1",
                "damage": "2",
                "keywords": "Ignores Cover, Pistol"
            },
            {
                "name": "Power sword",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "6",
                "skill": "2+",
                "strength": "5",
                "ap": "-2",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "Close combat weapon",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "6",
                "skill": "2+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Leader",
                "description": "This model can be attached to the following units: Emperor's Children Terminator Squad; Noise Marines"
            },
            {
                "name": "Obsessive Annunciation",
                "description": "While this model is leading a unit, ranged weapons equipped by that unit have the [SUSTAINED HITS 1] ability."
            },
            {
                "name": "Doom Siren",
                "description": "In your Shooting phase, after this model's unit has shot, select one enemy Infantry unit hit by one or more of those attacks and roll three D6: for each 4+, that enemy unit suffers 1 mortal wound. If an enemy suffers one or more mortal wounds as a result of this ability, it must take a Battle-shock test."
            }
        ]
    },
    "Lucius the Eternal": {
        "stats": {
            "stat_movement": "8\"",
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
                "name": "Blade of the Laer",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "6",
                "skill": "2+",
                "strength": "8",
                "ap": "-3",
                "damage": "3",
                "keywords": "Precision"
            },
            {
                "name": "Lash of Torment",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "10",
                "skill": "2+",
                "strength": "4",
                "ap": "-1",
                "damage": "1",
                "keywords": "Sustained Hits 1"
            }
        ],
        "abilities": [
            {
                "name": "Leader",
                "description": "This model can be attached to the following units:\n- Flawless Blades"
            },
            {
                "name": "Duellist\u2019s Hubris",
                "description": "At the start of the Fight phase, if this model is not leading a unit, until the end of the phase, it has the Fights First ability."
            },
            {
                "name": "A Challenge Worthy of Skill",
                "description": "Each time this model makes an attack that targets a Character, Monster or Walker unit, you can re-roll the Hit roll and re-roll the Wound roll."
            }
        ]
    },
    "Maulerfiend": {
        "stats": {
            "stat_movement": "10\"",
            "stat_toughness": 10,
            "stat_save": "3+",
            "stat_wounds": 12,
            "stat_leadership": "6+",
            "stat_oc": 3,
            "stat_invuln": "5+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Maulerfiend fists",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "6",
                "skill": "3+",
                "strength": "14",
                "ap": "-2",
                "damage": "D6+1",
                "keywords": "-"
            },
            {
                "name": "Magma cutter",
                "weapon_type": "ranged",
                "range": "6\"",
                "attacks": "2",
                "skill": "3+",
                "strength": "9",
                "ap": "-4",
                "damage": "D6",
                "keywords": "Melta 2"
            },
            {
                "name": "Lasher tendrils",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "6",
                "skill": "3+",
                "strength": "7",
                "ap": "-1",
                "damage": "1",
                "keywords": "Extra Attacks"
            }
        ],
        "abilities": [
            {
                "name": "Glutton for Punishment",
                "description": "Each time this model makes an attack, if it is below its Starting Strength, add 1 to the Hit roll. If this model is also Below Half-Strength, add 1 to the Wound roll as well."
            }
        ]
    },
    "Noise Marines": {
        "stats": {
            "stat_movement": "6\"",
            "stat_toughness": 5,
            "stat_save": "3+",
            "stat_wounds": 2,
            "stat_leadership": "6+",
            "stat_oc": 1,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Close combat weapon",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "3",
                "skill": "3+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "Power sword",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "3+",
                "strength": "5",
                "ap": "-2",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "Screamer pistol",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "3",
                "skill": "3+",
                "strength": "5",
                "ap": "-1",
                "damage": "2",
                "keywords": "Ignores Cover, Pistol"
            },
            {
                "name": "Sonic blaster",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "3",
                "skill": "3+",
                "strength": "5",
                "ap": "-1",
                "damage": "2",
                "keywords": "Ignores Cover"
            },
            {
                "name": "\u27a4 Blastmaster - varied frequency",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "6",
                "skill": "3+",
                "strength": "6",
                "ap": "-2",
                "damage": "1",
                "keywords": "Ignores Cover"
            },
            {
                "name": "\u27a4 Blastmaster - single frequency",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "3",
                "skill": "3+",
                "strength": "10",
                "ap": "-2",
                "damage": "3",
                "keywords": "Ignores Cover"
            }
        ],
        "abilities": [
            {
                "name": "Terrifying Crescendo",
                "description": "In your Shooting phase, after this unit has shot, select one enemy unit hit by one or more of those attacks. Until the start of your next Shooting phase, each time a Battle-shock or Leadership test is taken for that enemy unit, subtract 1 from that test."
            }
        ]
    },
    "Seekers of Slaanesh": {
        "stats": {
            "stat_movement": "14\"",
            "stat_toughness": 4,
            "stat_save": "7+",
            "stat_wounds": 2,
            "stat_leadership": "7+",
            "stat_oc": 1,
            "stat_invuln": "5+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Lashing tongues",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "2",
                "skill": "4+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Extra Attacks, Lethal Hits"
            },
            {
                "name": "Slashing claws",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "3",
                "skill": "3+",
                "strength": "4",
                "ap": "-1",
                "damage": "1",
                "keywords": "Devastating Wounds"
            }
        ],
        "abilities": [
            {
                "name": "Unholy Speed",
                "description": "You can re-roll Advance and Charge rolls made for this unit."
            },
            {
                "name": "Daemonic Icon",
                "description": "Models in the bearer's unit have a Leadership characteristic of 6+."
            },
            {
                "name": "Instrument of Chaos",
                "description": "Add 1 to Charge rolls made for the bearer's unit."
            }
        ]
    },
    "Shalaxi Helbane": {
        "stats": {
            "stat_movement": "14\"",
            "stat_toughness": 10,
            "stat_save": "3+",
            "stat_wounds": 20,
            "stat_leadership": "6+",
            "stat_oc": 5,
            "stat_invuln": "4+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Lash of Slaanesh",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "6",
                "skill": "2+",
                "strength": "6",
                "ap": "-1",
                "damage": "2",
                "keywords": "Assault"
            },
            {
                "name": "\u27a4 Pavane of Slaanesh - witchfire",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "D6",
                "skill": "2+",
                "strength": "9",
                "ap": "-1",
                "damage": "D3",
                "keywords": "Devastating Wounds, Psychic"
            },
            {
                "name": "\u27a4 Pavane of Slaanesh - focused witchfire",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "D6",
                "skill": "2+",
                "strength": "9",
                "ap": "-2",
                "damage": "D3",
                "keywords": "Hazardous, Devastating Wounds, Psychic, Sustained Hits 3"
            },
            {
                "name": "Snapping claws",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "2+",
                "strength": "6",
                "ap": "-2",
                "damage": "3",
                "keywords": "Devastating Wounds, Extra Attacks"
            },
            {
                "name": "Soulpiercer",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "6",
                "skill": "2+",
                "strength": "12",
                "ap": "-3",
                "damage": "D6+2",
                "keywords": "Precision"
            }
        ],
        "abilities": [
            {
                "name": "No Prey Can Evade",
                "description": "You can re-roll Advance and Charge rolls made for this model."
            },
            {
                "name": "Monarch of the Hunt",
                "description": "At the start of the first battle round, select one enemy unit to be this model's quarry. Each time this model makes a melee attack that targets its quarry, you can re-roll the Hit roll and you can re-roll the Wound roll. Each time this model's quarry is destroyed, select one new enemy unit to be this model's quarry."
            },
            {
                "name": "Damaged: 1-7 wounds remaining",
                "description": "While this model has 1-7 wounds remaining, each time this model makes an attack, subtract 1 from the Hit roll."
            }
        ]
    },
    "Sorcerer": {
        "stats": {
            "stat_movement": "7\"",
            "stat_toughness": 4,
            "stat_save": "3+",
            "stat_wounds": 4,
            "stat_leadership": "6+",
            "stat_oc": 1,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Agonising Energies - witchfire",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "D6",
                "skill": "3+",
                "strength": "5",
                "ap": "-1",
                "damage": "D3",
                "keywords": "Psychic"
            },
            {
                "name": "Agonising Energies - focused witchfire",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "D6",
                "skill": "3+",
                "strength": "6",
                "ap": "-2",
                "damage": "D3",
                "keywords": "Devastating Wounds, Hazardous, Psychic"
            },
            {
                "name": "Force weapon",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "3+",
                "strength": "6",
                "ap": "-2",
                "damage": "D3",
                "keywords": "Psychic"
            },
            {
                "name": "Bolt pistol",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Pistol"
            }
        ],
        "abilities": [
            {
                "name": "Leader",
                "description": "This model can be attached to the following units: Infractors; Noise Marines; Tormentors"
            },
            {
                "name": "Warped Interference (Psychic)",
                "description": "While this model is leading a unit, each time a ranged attack targets that unit, models in it have the Benefit of Cover against that attack."
            },
            {
                "name": "Wracking Agonies (Psychic)",
                "description": "In your Shooting phase, after this model has shot, select one INFANTRY unit hit by one or more of those attacks made with its Agonising Energies. Until the start of your next turn, that unit is wracked with agonies. While a unit is wracked with agonies, subtract 2\" from its Move characteristic and subtract 2 from charge rolls made for it."
            }
        ]
    },
    "Tormentors": {
        "stats": {
            "stat_movement": "7\"",
            "stat_toughness": 4,
            "stat_save": "3+",
            "stat_wounds": 2,
            "stat_leadership": "6+",
            "stat_oc": 2,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Bolt pistol",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Pistol"
            },
            {
                "name": "\u27a4 Plasma pistol - standard",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "7",
                "ap": "-2",
                "damage": "1",
                "keywords": "Pistol"
            },
            {
                "name": "\u27a4 Plasma pistol - supercharge",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "8",
                "ap": "-3",
                "damage": "2",
                "keywords": "Hazardous, Pistol"
            },
            {
                "name": "Rapture lash",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "6",
                "skill": "3+",
                "strength": "4",
                "ap": "-1",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "Power sword",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "3+",
                "strength": "5",
                "ap": "-2",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "Boltgun",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "2",
                "skill": "3+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Precision"
            },
            {
                "name": "Close combat weapon",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "3",
                "skill": "3+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "\u27a4 Plasma gun - standard",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "7",
                "ap": "-2",
                "damage": "1",
                "keywords": "Precision, Rapid Fire 1"
            },
            {
                "name": "\u27a4 Plasma gun - supercharge",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "8",
                "ap": "-3",
                "damage": "2",
                "keywords": "Hazardous, Precision, Rapid Fire 1"
            },
            {
                "name": "Meltagun",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "9",
                "ap": "-4",
                "damage": "D6",
                "keywords": "Melta 2, Precision"
            }
        ],
        "abilities": [
            {
                "name": "Objective Defiled",
                "description": "At the end of your Command phase, if this unit is within range of an objective marker you control, that objective marker remains under your control until your opponent's Level of Control over that objective marker is greater than yours at the end of a phase."
            },
            {
                "name": "Icon of Excess",
                "description": "At the end of your Shooting phase or the Fight phase, if the bearer's unit destroyed one or more enemy units this phase, the bearer's unit takes a Leadership test. If that test is passed, you gain 1CP."
            }
        ]
    }
}


class Command(BaseCommand):
    """Refresh Emperor's Children stat lines, weapon profiles, and abilities from BSData."""

    help = "Refresh 11th Edition stats/weapons/abilities for Emperor's Children units."

    def add_arguments(self, parser):
        """Add --dry-run flag."""
        parser.add_argument(
            '--dry-run', action='store_true',
            help='Preview changes without writing to the database.',
        )

    def handle(self, *args, **options):
        """Iterate EMPERORS_CHILDREN_DATASHEETS and refresh each unit's datasheet data."""
        dry_run = options['dry_run']
        updated = 0
        skipped = 0

        with transaction.atomic():
            for name, payload in EMPERORS_CHILDREN_DATASHEETS.items():
                try:
                    unit = UnitType.objects.get(name=name, faction__name="Emperor's Children")
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
