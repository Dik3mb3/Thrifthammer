"""
Management command: seed_chaos_space_marines_datasheets

Refreshes stat lines, weapon profiles, and abilities for all Chaos Space
Marines units using 11th Edition data sourced from BSData/wh40k-11e
("Chaos - Chaos Space Marines.json") -- the same source used by
seed_chaos_space_marines_points.py.

Usage:
    python manage.py seed_chaos_space_marines_datasheets
    python manage.py seed_chaos_space_marines_datasheets --dry-run

Notes:
- Does NOT touch points_cost or category -- those are handled entirely by
  seed_chaos_space_marines_points.py. This command only refreshes stat_*
  fields, WeaponProfile rows, and UnitAbility rows.
- Per-field safety rule: a unit's stats/weapons/abilities are only
  overwritten when BSData actually has that data for it. If extraction
  found nothing, the existing DB value/rows are left untouched.
- All 55 active units resolved cleanly -- 0 missing stats/weapons/
  abilities, 0 overlong stat fields, 0 markdown artifacts.
- Chaos Space Marines is the base faction for Death Guard, Emperor's
  Children, Thousand Sons, and World Eaters (same role as Space Marines on
  the loyalist side) -- refreshing this benefits those chapters'
  parent-faction fallback too.
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from calculators.models import UnitAbility, UnitType, WeaponProfile

# (name -> {stats?, weapons?, abilities?}). Missing keys mean "no data
# found for this field -- leave existing DB data untouched."
CHAOS_SPACE_MARINES_DATASHEETS = {
    "Abaddon the Despoiler": {
        "stats": {
            "stat_movement": "5\"",
            "stat_toughness": 5,
            "stat_save": "2+",
            "stat_wounds": 9,
            "stat_leadership": "5+",
            "stat_oc": 4,
            "stat_invuln": "4+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Talon of Horus",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "4",
                "skill": "2+",
                "strength": "5",
                "ap": "-1",
                "damage": "2",
                "keywords": "Sustained Hits 1"
            },
            {
                "name": "Talon of Horus",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "14",
                "skill": "2+",
                "strength": "7",
                "ap": "-3",
                "damage": "1",
                "keywords": "Devastating Wounds"
            },
            {
                "name": "Drach'nyen",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "8",
                "skill": "2+",
                "strength": "14",
                "ap": "-4",
                "damage": "3",
                "keywords": "Devastating Wounds"
            }
        ],
        "abilities": [
            {
                "name": "The Warmaster",
                "description": "In your Command phase, select one Warmaster ability. Until the start of your next Command phase, this model has that ability."
            },
            {
                "name": "Dark Destiny",
                "description": "Each time this model makes a Dark Pact and does not fail the resulting leadership roll, if the result of that roll was 7+, you gain 1CP."
            },
            {
                "name": "Leader",
                "description": "This model can be attached to the following units:\n\u25a0 CHAOS TERMINATOR SQUAD\n\u25a0 CHOSEN"
            }
        ]
    },
    "Accursed Cultists": {
        "stats": {
            "stat_movement": "6\"",
            "stat_toughness": 4,
            "stat_save": "6+",
            "stat_wounds": 3,
            "stat_leadership": "7+",
            "stat_oc": 1,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Hideous mutations",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "D6+2",
                "skill": "4+",
                "strength": "5",
                "ap": "-1",
                "damage": "2",
                "keywords": "-"
            },
            {
                "name": "Blasphemous appendages",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "2",
                "skill": "4+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Howling Horde",
                "description": "In your opponent's Shooting phase, when an enemy unit has shot, if a model from this unit was destroyed as a result of those attacks, this unit can make a surge move of up to D6\"."
            }
        ]
    },
    "Chaos Bikers": {
        "stats": {
            "stat_movement": "12\"",
            "stat_toughness": 5,
            "stat_save": "3+",
            "stat_wounds": 3,
            "stat_leadership": "6+",
            "stat_oc": 2,
            "stat_invuln": "",
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
                "name": "Astartes chainsword",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "3+",
                "strength": "4",
                "ap": "-1",
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
                "name": "Flamer",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "D6",
                "skill": "N/A",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Ignores Cover, Torrent"
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
                "keywords": "Melta 2"
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
                "keywords": "Rapid Fire 1"
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
                "keywords": "Hazardous, Rapid Fire 1"
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
                "name": "Rapid Assault",
                "description": "Each time a model in this unit makes a melee attack, if this unit made a Charge move this turn, improve the Strength characteristic of that attack by 1."
            },
            {
                "name": "Chaos icon",
                "description": "Each time the bearer\u2019s unit takes a Leadership test for the Dark Pacts ability, you can re-roll that test."
            }
        ]
    },
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
    "Chaos Lord": {
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
                "name": "Daemon hammer",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "5",
                "skill": "3+",
                "strength": "8",
                "ap": "-2",
                "damage": "2",
                "keywords": "Devastating Wounds"
            },
            {
                "name": "Accursed weapon",
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
                "name": "Astartes chainblade",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "7",
                "skill": "2+",
                "strength": "4",
                "ap": "-1",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "Power fist",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "5",
                "skill": "2+",
                "strength": "8",
                "ap": "-2",
                "damage": "2",
                "keywords": "-"
            },
            {
                "name": "\u27a4 Plasma pistol - standard",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "1",
                "skill": "2+",
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
                "skill": "2+",
                "strength": "8",
                "ap": "-3",
                "damage": "2",
                "keywords": "Hazardous, Pistol"
            }
        ],
        "abilities": [
            {
                "name": "Leader",
                "description": "This model can be attached to the following units:\n\u25a0 CHOSEN\n\u25a0 LEGIONARIES"
            },
            {
                "name": "Chance for Glory",
                "description": "Once per battle, at the start of the Fight phase, this model can use this ability. If it does, until the end of the phase, improve the Strength, Attacks, Armour\nPenetration and Damage characteristics of melee weapons equipped by this model by 1."
            },
            {
                "name": "Lord of Chaos",
                "description": "Once per battle round, one unit from your army with this ability can use it when its unit is targeted with a Stratagem. If it does, reduce the CP cost of that use of that Stratagem by 1CP."
            }
        ]
    },
    "Chaos Lord in Terminator Armour": {
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
                "name": "Combi-bolter",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "2",
                "skill": "2+",
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
                "skill": "3+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Anti-INFANTRY 4+, Devastating Wounds, Rapid Fire 1"
            },
            {
                "name": "Exalted weapon",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "6",
                "skill": "2+",
                "strength": "5",
                "ap": "-2",
                "damage": "2",
                "keywords": "-"
            },
            {
                "name": "Chainfist",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "5",
                "skill": "3+",
                "strength": "8",
                "ap": "-2",
                "damage": "2",
                "keywords": "Anti-VEHICLE 3+"
            },
            {
                "name": "Paired accursed weapons",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "7",
                "skill": "2+",
                "strength": "5",
                "ap": "-2",
                "damage": "1",
                "keywords": "Twin-linked"
            },
            {
                "name": "Power fist",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "5",
                "skill": "2+",
                "strength": "8",
                "ap": "-2",
                "damage": "2",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Leader",
                "description": "This model can be attached to the following units:\n\u25a0 CHAOS TERMINATOR SQUAD"
            },
            {
                "name": "Formidably Resilient",
                "description": "Each time an attack is allocated to this model, halve the Damage characteristic of that attack."
            },
            {
                "name": "Lord of Chaos",
                "description": "Once per battle round, one unit from your army with this ability can use it when its unit is targeted with a Stratagem. If it does, reduce the CP cost of that use of that Stratagem by 1CP."
            }
        ]
    },
    "Chaos Lord with Jump Pack": {
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
                "name": "Accursed weapon",
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
                "name": "Power fist",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "5",
                "skill": "2+",
                "strength": "8",
                "ap": "-2",
                "damage": "2",
                "keywords": "-"
            },
            {
                "name": "Twin lightning claws",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "6",
                "skill": "2+",
                "strength": "5",
                "ap": "-2",
                "damage": "1",
                "keywords": "Twin-linked"
            },
            {
                "name": "\u27a4 Plasma pistol - standard",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "1",
                "skill": "2+",
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
                "skill": "2+",
                "strength": "8",
                "ap": "-3",
                "damage": "2",
                "keywords": "Hazardous, Pistol"
            },
            {
                "name": "Bolt pistol",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "1",
                "skill": "2+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Pistol"
            }
        ],
        "abilities": [
            {
                "name": "Leader",
                "description": "This model can be attached to the following units:\n\u25a0 RAPTORS"
            },
            {
                "name": "Cruel Hunter",
                "description": "While this model is leading a unit, each time that unit Piles In or Consolidates, each model in that unit can move up to 6\" instead of up to 3\"."
            },
            {
                "name": "Lord of Chaos",
                "description": "Once per battle round, one unit from your army with this ability can use it when its unit is targeted with a Stratagem. If it does, reduce the CP cost of that use of that Stratagem by 1CP."
            }
        ]
    },
    "Chaos Predator Annihilator": {
        "stats": {
            "stat_movement": "10\"",
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
                "name": "Predator twin lascannon",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "14",
                "ap": "-3",
                "damage": "D6+1",
                "keywords": "Twin-linked"
            },
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
            },
            {
                "name": "Heavy bolter",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "3",
                "skill": "3+",
                "strength": "5",
                "ap": "-1",
                "damage": "2",
                "keywords": "Sustained Hits 1"
            },
            {
                "name": "Lascannon",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "12",
                "ap": "-3",
                "damage": "D6+1",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Annihilator",
                "description": "Each time a ranged attack made by this model is allocated to a Monster or Vehicle model, you can re-roll the Damage roll."
            }
        ]
    },
    "Chaos Predator Destructor": {
        "stats": {
            "stat_movement": "10\"",
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
                "name": "Predator autocannon",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "4",
                "skill": "3+",
                "strength": "9",
                "ap": "-1",
                "damage": "3",
                "keywords": "Rapid Fire 2"
            },
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
            },
            {
                "name": "Heavy bolter",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "3",
                "skill": "3+",
                "strength": "5",
                "ap": "-1",
                "damage": "2",
                "keywords": "Sustained Hits 1"
            },
            {
                "name": "Lascannon",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "12",
                "ap": "-3",
                "damage": "D6+1",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Destructor",
                "description": "Each time a ranged attack made by this model targets an enemy INFANTRY unit, improve the Armour Penetration characteristic of that attack by 1."
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
                "name": "Self-repair",
                "description": "At the start of your Command phase, this model regains 1 lost wound."
            }
        ]
    },
    "Chaos Spawn": {
        "stats": {
            "stat_movement": "8\"",
            "stat_toughness": 5,
            "stat_save": "4+",
            "stat_wounds": 4,
            "stat_leadership": "7+",
            "stat_oc": 0,
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
                "name": "Mind-breaking Mutations (Aura)",
                "description": "While an enemy unit (excluding VEHICLES) is within 3\" of this unit, subtract 1 from the Objective Control characteristic of models in that enemy unit."
            }
        ]
    },
    "Chaos Terminator Squad": {
        "stats": {
            "stat_movement": "5\"",
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
            }
        ],
        "abilities": [
            {
                "name": "Despoilers",
                "description": "Each time this unit makes a Dark Pact, until the end of the phase, each time a model in this unit makes an attack, you can re-roll the Hit roll."
            }
        ]
    },
    "Chaos Vindicator": {
        "stats": {
            "stat_movement": "9\"",
            "stat_toughness": 11,
            "stat_save": "2+",
            "stat_wounds": 11,
            "stat_leadership": "6+",
            "stat_oc": 3,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Demolisher cannon",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "D6+3",
                "skill": "3+",
                "strength": "14",
                "ap": "-3",
                "damage": "D6",
                "keywords": "Blast"
            },
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
                "name": "Siege Shield",
                "description": "When making ranged attacks with its demolisher cannon, this model can target enemy units within Engagement Range of it (provided no other friendly units are also within Engagement Range of that enemy unit). In addition, when making ranged attacks, this model does not suffer the penalty to its Hit rolls for being within Engagement Range of one or more enemy units."
            }
        ]
    },
    "Chosen": {
        "stats": {
            "stat_movement": "6\"",
            "stat_toughness": 4,
            "stat_save": "3+",
            "stat_wounds": 3,
            "stat_leadership": "6+",
            "stat_oc": 1,
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
                "name": "Boltgun",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "2",
                "skill": "3+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "-"
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
                "name": "Power fist",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "3+",
                "strength": "8",
                "ap": "-2",
                "damage": "2",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Chosen Marauders",
                "description": "This unit is eligible to shoot and declare a charge in a turn in which it Advanced or Fell Back."
            },
            {
                "name": "Chaos icon",
                "description": "Each time the bearer\u2019s unit takes a Leadership test for the Dark Pacts ability, you can re-roll that test."
            }
        ]
    },
    "Cultist Firebrand": {
        "stats": {
            "stat_movement": "6\"",
            "stat_toughness": 4,
            "stat_save": "4+",
            "stat_wounds": 4,
            "stat_leadership": "6+",
            "stat_oc": 1,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Balefire pike",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "D6+3",
                "skill": "N/A",
                "strength": "5",
                "ap": "-1",
                "damage": "1",
                "keywords": "Ignores Cover, Torrent"
            },
            {
                "name": "Close combat weapon",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "4+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Fiery Faith",
                "description": "While this model is leading a unit, you can re-roll Leadership tests taken for that unit."
            },
            {
                "name": "Cursed Flames",
                "description": "In your Shooting phase, after this model has shot, select one enemy INFANTRY unit hit by one or more of those attacks. That unit must make a Battle-shock test."
            },
            {
                "name": "Leader",
                "description": "This model can be attached to the following units:\n\u25a0 ACCURSED CULTISTS\n\u25a0 CULTIST MOB"
            }
        ]
    },
    "Cultist Mob": {
        "stats": {
            "stat_movement": "6\"",
            "stat_toughness": 3,
            "stat_save": "6+",
            "stat_wounds": 1,
            "stat_leadership": "7+",
            "stat_oc": 1,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Brutal assault weapon",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "2",
                "skill": "4+",
                "strength": "3",
                "ap": "0",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "Bolt pistol",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "1",
                "skill": "4+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Pistol"
            },
            {
                "name": "Autopistol",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "1",
                "skill": "4+",
                "strength": "3",
                "ap": "0",
                "damage": "1",
                "keywords": "Pistol"
            }
        ],
        "abilities": [
            {
                "name": "For the Dark Gods",
                "description": "At the end of your Command phase, if this unit is within range of an objective marker you control, that objective marker remains under your control, even if you have no models within range of it, until your opponent controls it at the start or end of any turn."
            }
        ]
    },
    "Cypher": {
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
                "name": "Cypher's bolt pistol",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "6",
                "skill": "2+",
                "strength": "4",
                "ap": "-1",
                "damage": "1",
                "keywords": "Assault, Pistol, Sustained Hits 1"
            },
            {
                "name": "Cypher's bolt pistol",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "6",
                "skill": "2+",
                "strength": "4",
                "ap": "-1",
                "damage": "1",
                "keywords": "Sustained Hits 1"
            },
            {
                "name": "Cypher's plasma pistol",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "3",
                "skill": "2+",
                "strength": "8",
                "ap": "-3",
                "damage": "2",
                "keywords": "Assault, Pistol, Sustained Hits 1"
            },
            {
                "name": "Cypher's plasma pistol",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "3",
                "skill": "2+",
                "strength": "8",
                "ap": "-3",
                "damage": "2",
                "keywords": "Extra Attacks"
            }
        ],
        "abilities": [
            {
                "name": "Agent of Discord (Aura)",
                "description": "Once per turn, when your opponent targets a unit from their army within 12\u201d of this model with a stratagem, you can use this ability. If you do increase the CP cost of that use of that stratagem by 1CP."
            },
            {
                "name": "Guns Blazing",
                "description": "Once per turn, in your opponent's Shooting phase, when an enemy unit makes a ranged attacks that targets a friendly HERETIC ASTARTES unit within 3\" of this model, after that enemy unit has shot, this model can shoot as if it were your Shooting phase, but it must target only that enemy unit when doing so and can only do so if that enemy unit is an eligible target."
            }
        ]
    },
    "Dark Apostle": {
        "stats": {
            "stat_movement": "6\"",
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
                "name": "Accursed crozius",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "5",
                "skill": "2+",
                "strength": "6",
                "ap": "-1",
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
            },
            {
                "name": "Close combat weapon",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "1",
                "skill": "4+",
                "strength": "3",
                "ap": "0",
                "damage": "1",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Leader",
                "description": "This model can be attached to the following units:\n\u25a0 ACCURSED CULTISTS\n\u25a0 CHOSEN\n\u25a0 CULTIST MOB\n\u25a0 LEGIONARIES"
            },
            {
                "name": "Dark Zealotry",
                "description": "While this unit is leading a unit and contains a DARK APOSTLE model, each time a model in that unit makes a melee attack, add 1 to the Wound roll."
            },
            {
                "name": "Demagogue",
                "description": "Once per battle, at the start of any phase, you can select one friendly HERETIC ASTARTES unit that is Battle-shocked and within 12\" of this unit\u2019s DARK APOSTLE model. That unit is no longer Battle-shocked."
            },
            {
                "name": "Malign Sacrifice",
                "description": "At the start of the Fight phase, if this unit contains one or more Dark Disciple models, you can select one of those models and one enemy unit within Engagement Range of this unit, then roll one D6: on a 2-5, that enemy unit suffers 1 mortal wound; on a 6, that enemy unit suffers D3 mortal wounds. That Dark Disciple model is then destroyed."
            }
        ]
    },
    "Dark Commune": {
        "stats": {
            "stat_movement": "6\"",
            "stat_toughness": 3,
            "stat_save": "6+",
            "stat_wounds": 1,
            "stat_leadership": "7+",
            "stat_oc": 1,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Commune blade",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "2",
                "skill": "4+",
                "strength": "4",
                "ap": "-2",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "Autopistol",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "1",
                "skill": "4+",
                "strength": "3",
                "ap": "0",
                "damage": "1",
                "keywords": "Pistol"
            },
            {
                "name": "Close combat weapon",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "1",
                "skill": "4+",
                "strength": "3",
                "ap": "0",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "\u27a4 Warp Curse - witchfire",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "3",
                "skill": "3+",
                "strength": "4",
                "ap": "-1",
                "damage": "2",
                "keywords": "Psychic"
            },
            {
                "name": "\u27a4 Warp Curse - focused witchfire",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "3",
                "skill": "3+",
                "strength": "5",
                "ap": "-1",
                "damage": "2",
                "keywords": "Hazardous, Psychic, Sustained Hits 2"
            },
            {
                "name": "Commune stave",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "2",
                "skill": "4+",
                "strength": "3",
                "ap": "0",
                "damage": "D3",
                "keywords": "Devastating Wounds"
            }
        ],
        "abilities": [
            {
                "name": "Leader",
                "description": "This model can be attached to the following units:\n\u25a0 ACCURSED CULTISTS\n\u25a0 CULTIST MOB"
            },
            {
                "name": "Faithful Flock",
                "description": "While this unit is leading a unit and contains a CULT DEMAGOGUE model, models in that unit have a 5+ invulnerable save."
            },
            {
                "name": "Dark Ritual",
                "description": "Once per battle, in your Command phase, if this unit contains a CULT DEMAGOGUE model, it can use this ability. If it does, until the end of the turn, this unit can declare a charge in a turn in which it Advanced and each time a model in this unit makes an attack, add 1 to the Hit roll and add 1 to the Wound roll."
            },
            {
                "name": "Chaos icon",
                "description": "Each time the bearer\u2019s unit takes a Leadership test for the Dark Pacts ability, you can re-roll that test."
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
                "keywords": "-"
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
                "name": "Daemonforge",
                "description": "Each time this unit makes a Dark Pact, until the end of the phase, each time this model makes an attack, re-roll a Wound roll of 1."
            }
        ]
    },
    "Fabius Bile": {
        "stats": {
            "stat_movement": "6\"",
            "stat_toughness": 4,
            "stat_save": "3+",
            "stat_wounds": 5,
            "stat_leadership": "6+",
            "stat_oc": 1,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Xyclos needler",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "3",
                "skill": "2+",
                "strength": "2",
                "ap": "-1",
                "damage": "2",
                "keywords": "Anti-INFANTRY 2+, Pistol"
            },
            {
                "name": "The Chirurgeon",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "2",
                "skill": "2+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Extra Attacks"
            },
            {
                "name": "Rod of Torment",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "6",
                "skill": "2+",
                "strength": "5",
                "ap": "-1",
                "damage": "3",
                "keywords": "-"
            },
            {
                "name": "Surgeon Acolyte's tools",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "1",
                "skill": "5+",
                "strength": "3",
                "ap": "0",
                "damage": "1",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Enhanced Warriors",
                "description": "If this unit is attached to a unit at the start of the battle, until the end of the battle, add 1 to the Strength characteristic of melee weapons equipped by Bodyguard models in that unit and add 1 to the Toughness characteristic of Bodyguard models in that unit."
            },
            {
                "name": "Leader",
                "description": "This model can be attached to the following units:\n\u25a0 ACCURSED CULTISTS\n\u25a0 CHOSEN\n\u25a0 CULTIST MOB\n\u25a0 LEGIONARIES"
            },
            {
                "name": "Surgeon Acolyte",
                "description": "Once per turn, when an attack is allocated to a model in this unit, if this unit contains Fabius Bile, you can change the Damage characteristic of that attack to 0."
            },
            {
                "name": "Chirurgeon",
                "description": "The first time this unit\u2019s Fabius Bile model is destroyed, at the end of the phase, roll one D6: on a 2+, set it back up on the battlefield, as close as possible to where it was destroyed and not within Engagement Range of any enemy models, with its full wounds remaining."
            }
        ]
    },
    "Fellgor Beastmen": {
        "stats": {
            "stat_movement": "6\"",
            "stat_toughness": 4,
            "stat_save": "5+",
            "stat_wounds": 1,
            "stat_leadership": "7+",
            "stat_oc": 1,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Chainsword",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "3",
                "skill": "4+",
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
                "skill": "4+",
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
                "skill": "4+",
                "strength": "7",
                "ap": "-2",
                "damage": "1",
                "keywords": "Pistol"
            },
            {
                "name": "\u27a4 Plasma pistol- supercharge",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "1",
                "skill": "4+",
                "strength": "8",
                "ap": "-3",
                "damage": "2",
                "keywords": "Hazardous, Pistol"
            },
            {
                "name": "Autopistol",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "1",
                "skill": "4+",
                "strength": "3",
                "ap": "0",
                "damage": "1",
                "keywords": "Pistol"
            },
            {
                "name": "Close combat weapon",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "2",
                "skill": "4+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "Great weapon",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "2",
                "skill": "5+",
                "strength": "8",
                "ap": "-1",
                "damage": "2",
                "keywords": "-"
            },
            {
                "name": "Corrupted stave",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "2",
                "skill": "4+",
                "strength": "4",
                "ap": "-1",
                "damage": "D3",
                "keywords": "Devastating Wounds, Psychic"
            },
            {
                "name": "Corrupted stave",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "D3",
                "skill": "4+",
                "strength": "5",
                "ap": "-1",
                "damage": "1",
                "keywords": "Devastating Wounds, Psychic"
            }
        ],
        "abilities": [
            {
                "name": "Bestial Raiders",
                "description": "If this unit begins the game in Strategic Reserves, it can be set up in the Reinforcements step of your first, second or third Movement phase, regardless of any mission rules. If this unit is in Strategic Reserves, for the purposes of setting it up on the battlefield, treat the current battle round number as being one higher than it actually is."
            }
        ]
    },
    "Forgefiend": {
        "stats": {
            "stat_movement": "8\"",
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
                "name": "Ectoplasma cannon",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "D3",
                "skill": "3+",
                "strength": "10",
                "ap": "-3",
                "damage": "3",
                "keywords": "Blast"
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
            },
            {
                "name": "Armoured limbs",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "2",
                "skill": "3+",
                "strength": "6",
                "ap": "0",
                "damage": "2",
                "keywords": "-"
            },
            {
                "name": "Forgefiend jaws",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "5",
                "skill": "3+",
                "strength": "7",
                "ap": "0",
                "damage": "2",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Daemonic Ordnance",
                "description": "Each time this model is selected to shoot, it can use this ability. If it does, until the end of the phase, its ranged weapons have the [DEVASTATING WOUNDS] and [HAZARDOUS] abilities."
            }
        ]
    },
    "Haarken Worldclaimer": {
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
                "name": "Hellspear",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "1",
                "skill": "2+",
                "strength": "8",
                "ap": "-3",
                "damage": "3",
                "keywords": "Assault, Sustained Hits D3"
            },
            {
                "name": "Hellspear",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "1",
                "skill": "2+",
                "strength": "8",
                "ap": "-3",
                "damage": "3",
                "keywords": "Extra Attacks, Lance, Sustained Hits D3"
            },
            {
                "name": "Herald's Talon",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "6",
                "skill": "2+",
                "strength": "5",
                "ap": "-2",
                "damage": "2",
                "keywords": "Precision"
            }
        ],
        "abilities": [
            {
                "name": "Leader",
                "description": "This model can be attached to the following units:\n\u25a0 RAPTORS"
            },
            {
                "name": "Head Taker",
                "description": "While this model is leading a unit, each time this model\u2019s unit ends a Charge move, select one enemy unit within Engagement Range of this model\u2019s unit and roll one D6 for each model in this model\u2019s unit which is within Engagement Range of that enemy unit: for each 4+, that enemy unit suffers 1 mortal wound."
            },
            {
                "name": "Herald of the Apocalypse (Aura)",
                "description": "While an enemy unit is within 6\" of this model, in the Battle-shock step of your opponent\u2019s Command phase, if that enemy unit is below its Starting Strength, it must take a Battle-shock test. This ability cannot cause a unit to take two Battle-shock tests in the same phase."
            }
        ]
    },
    "Havocs": {
        "stats": {
            "stat_movement": "5\"",
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
                "name": "Astartes chainsword",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "3+",
                "strength": "4",
                "ap": "-1",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "Flamer",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "D6",
                "skill": "N/A",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Ignores Cover, Torrent"
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
                "keywords": "Rapid Fire 1"
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
                "keywords": "Hazardous, Rapid Fire 1"
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
                "name": "Boltgun",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "2",
                "skill": "3+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "-"
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
                "keywords": "Melta 2"
            },
            {
                "name": "Havoc autocannon",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "2",
                "skill": "3+",
                "strength": "9",
                "ap": "-1",
                "damage": "3",
                "keywords": "-"
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
                "name": "Havoc lascannon",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "12",
                "ap": "-3",
                "damage": "D6+1",
                "keywords": "-"
            },
            {
                "name": "\u27a4 Havoc missile launcher - frag",
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
                "name": "\u27a4 Havoc missile launcher - krak",
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
                "name": "Havoc reaper chaincannon",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "8",
                "skill": "3+",
                "strength": "5",
                "ap": "0",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "Havoc heavy bolter",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "3",
                "skill": "3+",
                "strength": "5",
                "ap": "-1",
                "damage": "2",
                "keywords": "Sustained Hits 1"
            }
        ],
        "abilities": [
            {
                "name": "Stabilisation Talons",
                "description": "Each time a model in this unit makes an attack with a ranged weapon, you can ignore any or all modifiers to the Hit roll and any or all modifiers to the Ballistic Skill characteristic of that weapon."
            }
        ]
    },
    "Helbrute": {
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
                "name": "Helbrute fist",
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
                "name": "\u27a4 Missile launcher - frag",
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
                "name": "\u27a4 Missile launcher - krak",
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
                "name": "Helbrute hammer",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "5",
                "skill": "4+",
                "strength": "14",
                "ap": "-3",
                "damage": "D6+1",
                "keywords": "-"
            },
            {
                "name": "Power scourge",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "8",
                "skill": "3+",
                "strength": "7",
                "ap": "-1",
                "damage": "2",
                "keywords": "-"
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
                "name": "Twin autocannon",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "2",
                "skill": "3+",
                "strength": "9",
                "ap": "-1",
                "damage": "3",
                "keywords": "Twin-linked"
            },
            {
                "name": "Helbrute plasma cannon",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "D3",
                "skill": "3+",
                "strength": "8",
                "ap": "-3",
                "damage": "3",
                "keywords": "Blast, Hazardous"
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
                "name": "Twin lascannon",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "12",
                "ap": "-3",
                "damage": "D6+1",
                "keywords": "Twin-linked"
            }
        ],
        "abilities": [
            {
                "name": "Dark Ascension (Aura)",
                "description": "While a friendly HERETIC ASTARTES unit is within 6\" of this model, each time that unit makes a Dark Pact, until the end of the phase, its weapons gain both abilities conferred by that pact (instead of only one)."
            },
            {
                "name": "Devoted to Destruction",
                "description": "If this model is equipped with 2 melee weapons in addition to its close combat weapon, add 2 to the Attacks characteristics of those 2 weapons."
            }
        ]
    },
    "Heldrake": {
        "stats": {
            "stat_movement": "12+",
            "stat_toughness": 9,
            "stat_save": "3+",
            "stat_wounds": 12,
            "stat_leadership": "6+",
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
                "description": "Each time this model makes an attack that targets a unit that can FLY, add 1 to the Hit roll."
            }
        ]
    },
    "Heretic Astartes Daemon Prince": {
        "stats": {
            "stat_movement": "8\"",
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
                "name": "Dark Blessing (Aura)",
                "description": "While a friendly HERETIC ASTARTES INFANTRY unit is within 6\" of this model, each time a ranged attack is allocated to a model in that unit, that model has the Benefit of Cover against that attack."
            },
            {
                "name": "Ascended Daemon",
                "description": "Each time this model shoot or fights, while resolving those attacks, you can re-roll one Hit roll and you can re-roll one Wound roll."
            },
            {
                "name": "Lord of Chaos",
                "description": "While this model is within 3\" of a friendly Heretic Astartes Infantry unit, this model has Lone Operative."
            }
        ]
    },
    "Heretic Astartes Daemon Prince with wings": {
        "stats": {
            "stat_movement": "12\"",
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
                "name": "Flying Horror",
                "description": "Each time this model ends a Normal or Advance move, select one enemy unit it moved over during that move. That unit must take a Battle-shock test."
            },
            {
                "name": "Daemonic Destruction",
                "description": "Each time this model ends a Charge move, select one enemy unit within Engagement Range of it and roll one D6 for each of this model\u2019s remaining wounds: for each 4+, that enemy unit suffers 1 mortal wound (to a maximum of 6 mortal wounds)."
            }
        ]
    },
    "Huron Blackheart": {
        "stats": {
            "stat_movement": "6\"",
            "stat_toughness": 5,
            "stat_save": "3+",
            "stat_wounds": 5,
            "stat_leadership": "6+",
            "stat_oc": 1,
            "stat_invuln": "4+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Tyrant's Claw heavy flamer",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "D6+2",
                "skill": "N/A",
                "strength": "6",
                "ap": "-1",
                "damage": "1",
                "keywords": "Ignores Cover, Pistol, Torrent"
            },
            {
                "name": "Tyrant's Claw and exalted power weapon",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "6",
                "skill": "2+",
                "strength": "8",
                "ap": "-3",
                "damage": "3",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Leader",
                "description": "This model can be attached to the following units:\n- Chosen\n- Chaos Terminator Squad\n- Legionaries\n- Masters of the Maelstrom\n- Red Corsairs Raiders"
            },
            {
                "name": "Lord of Badab (Aura)",
                "description": "While a friendly Heretic Astartes Infantry unit (excluding Battle-shocked units and Damned units) is within 6\" of this model, add 1 to the Objective Control characteristic of models in that unit."
            },
            {
                "name": "Hamadrya\u2019s Knowledge (Psychic)",
                "description": "Once per battle round, when an enemy unit ends a Normal, Advance or Fall Back move within 8\" of this model\u2019s unit, if this model\u2019s unit is not within Engagement Range of one or more enemy units, it can make a Normal move of up to D3+3\"."
            }
        ]
    },
    "Khorne Berzerkers": {
        "stats": {
            "stat_movement": "8\"",
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
                "name": "Chainblade",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "3+",
                "strength": "4",
                "ap": "-1",
                "damage": "1",
                "keywords": "-"
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
                "name": "Khornate eviscerator",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "3",
                "skill": "3+",
                "strength": "8",
                "ap": "-2",
                "damage": "2",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Blood Surge",
                "description": "In your opponent's Shooting phase, each time an enemy unit has shot, if any models from this unit were destroyed as a result of those attacks, this unit can make a Blood Surge move. To do so, roll one D6 and add 2 to the roll: models in this unit move a number of inches up to this result, but this unit must finish that move as close as possible to the closest enemy unit (excluding Aircraft). When doing so, those models can be moved within Engagement Range of that enemy unit. This unit cannot make a Blood Surge move while it is Battle-shocked or within Engagement Range of one or more enemy units, and can only make one Blood Surge move per phase."
            },
            {
                "name": "Icon of Khorne",
                "description": "Each time the bearer's unit destroys an enemy unit, you gain one Bloodshed point. Each time you make a Blessings of Khorne roll, roll one additional D6 for each Bloodshed point you have, after which, all your Bloodshed points are lost."
            }
        ]
    },
    "Kravek Morne": {
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
                "name": "Combi-bolter",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "2",
                "skill": "2+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Rapid Fire 2"
            },
            {
                "name": "Last Argument and power fist",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "7",
                "skill": "2+",
                "strength": "10",
                "ap": "-2",
                "damage": "2",
                "keywords": "Devastating Wounds"
            },
            {
                "name": "Servo-harness",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "3",
                "skill": "2+",
                "strength": "6",
                "ap": "-2",
                "damage": "2",
                "keywords": "Anti-Vehicle 2+, Extra Attacks"
            }
        ],
        "abilities": [
            {
                "name": "Headlong Destruction",
                "description": "Each time a model in this unit makes an attack that targets the closest eligible enemy unit, improve the Armour Penetration characteristic of that attack by 1."
            },
            {
                "name": "Architect of Ruin",
                "description": "At the start of the battle, select one unit in your opponent\u2019s army to be this model\u2019s hated foe. Each time this model makes an attack that targets its hated foe, you can re-roll the Wound roll. Each time this model\u2019s hated foe is destroyed, you can select a new unit from your opponent\u2019s army to be its hated foe."
            },
            {
                "name": "Leader",
                "description": "This model can be attached to the following units: Chaos Terminator Squad, Mutilators, Obliterators."
            }
        ]
    },
    "Legionaries": {
        "stats": {
            "stat_movement": "6\"",
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
                "name": "Astartes chainsword",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "3+",
                "strength": "4",
                "ap": "-1",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "Heavy melee weapon",
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
                "name": "Boltgun",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "2",
                "skill": "3+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "Balefire tome",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "2",
                "skill": "3+",
                "strength": "5",
                "ap": "-1",
                "damage": "1",
                "keywords": "Psychic"
            },
            {
                "name": "Flamer",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "D6",
                "skill": "N/A",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Ignores Cover, Torrent"
            },
            {
                "name": "Havoc autocannon",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "2",
                "skill": "4+",
                "strength": "9",
                "ap": "-1",
                "damage": "3",
                "keywords": "-"
            },
            {
                "name": "Heavy bolter",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "3",
                "skill": "4+",
                "strength": "5",
                "ap": "-1",
                "damage": "2",
                "keywords": "Heavy, Sustained Hits 1"
            },
            {
                "name": "Lascannon",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "1",
                "skill": "4+",
                "strength": "12",
                "ap": "-3",
                "damage": "D6+1",
                "keywords": "Heavy"
            },
            {
                "name": "\u27a4 Missile launcher - frag",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "D6",
                "skill": "4+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Blast, Heavy"
            },
            {
                "name": "\u27a4 Missile launcher - krak",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "1",
                "skill": "4+",
                "strength": "9",
                "ap": "-2",
                "damage": "D6",
                "keywords": "Heavy"
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
                "keywords": "Rapid Fire 1"
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
                "keywords": "Hazardous, Rapid Fire 1"
            },
            {
                "name": "Reaper chaincannon",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "8",
                "skill": "4+",
                "strength": "5",
                "ap": "0",
                "damage": "1",
                "keywords": "Heavy"
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
                "keywords": "Melta 2"
            }
        ],
        "abilities": [
            {
                "name": "Veterans of the Long War",
                "description": "Each time a model in this unit targets an enemy unit with a melee attack, re-roll a Wound roll of 1. If that enemy unit is within range of an objective marker, you can re-roll the Wound roll instead."
            },
            {
                "name": "Chaos icon",
                "description": "Each time the bearer\u2019s unit takes a Leadership test for the Dark Pacts ability, you can re-roll that test."
            }
        ]
    },
    "Lord Discordant on Helstalker": {
        "stats": {
            "stat_movement": "14\"",
            "stat_toughness": 9,
            "stat_save": "2+",
            "stat_wounds": 10,
            "stat_leadership": "6+",
            "stat_oc": 4,
            "stat_invuln": "4+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Bladed limbs",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "3+",
                "strength": "6",
                "ap": "-1",
                "damage": "2",
                "keywords": "Extra Attacks"
            },
            {
                "name": "Impaler chainglaive",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "5",
                "skill": "2+",
                "strength": "8",
                "ap": "-3",
                "damage": "3",
                "keywords": "Lance"
            },
            {
                "name": "Bolt pistol",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "1",
                "skill": "2+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Pistol"
            },
            {
                "name": "Helstalker autocannon",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "3",
                "skill": "2+",
                "strength": "9",
                "ap": "-1",
                "damage": "3",
                "keywords": "-"
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
                "name": "Techno-virus injector",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "1",
                "skill": "3+",
                "strength": "3",
                "ap": "-3",
                "damage": "2",
                "keywords": "Anti-VEHICLE 2+, Extra Attacks"
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
            }
        ],
        "abilities": [
            {
                "name": "Corrupt Machine Spirits",
                "description": "At the start of your Shooting phase, select one visible enemy Vehicle unit within 12\" of this model and roll one D6: on a 2-3, that enemy unit suffers D3 mortal wounds; on a 4-5, that enemy unit suffers 3 mortal wounds; on a 6, that enemy unit suffers D3+3 mortal wounds.\u2019"
            },
            {
                "name": "Spirit Thief",
                "description": "At the start of your Shooting phase, select one visible enemy Vehicle unit. Until the end of the phase, each time a friendly Heretic Astartes model makes an attack that targets that unit, re-roll a Wound roll of 1."
            }
        ]
    },
    "Master of Executions": {
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
        "weapons": [
            {
                "name": "Axe of dismemberment",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "5",
                "skill": "2+",
                "strength": "7",
                "ap": "-2",
                "damage": "2",
                "keywords": "Devastating Wounds, Precision"
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
                "name": "Support",
                "description": "This model can be attached to the following units:\n\u25a0 CHOSEN\n\u25a0 LEGIONARIES\n\nYou can attach this model to one of the above units even if one other CHARACTER model has already been attached to it (a unit cannot have two MASTERS OF EXECUTIONS attached to it). If you do, and that Bodyguard unit is destroyed, the Leader units attached to it become separate units, with their original Starting Strengths."
            },
            {
                "name": "Warp-sighted Butcher",
                "description": "While this model is leading a unit, each time a model in that unit makes a melee attack that targets a unit that is below its Starting Strength, you can re-roll the Hit roll. If that unit is Below Half-strength, you can re-roll the Wound roll as well."
            },
            {
                "name": "Trophy Taker",
                "description": "Each time this model destroys an enemy CHARACTER model, you gain 1CP."
            }
        ]
    },
    "Master of Possession": {
        "stats": {
            "stat_movement": "8\"",
            "stat_toughness": 4,
            "stat_save": "3+",
            "stat_wounds": 4,
            "stat_leadership": "6+",
            "stat_oc": 1,
            "stat_invuln": "5+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "\u27a4 Rite of Possession - witchfire",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "2",
                "skill": "3+",
                "strength": "4",
                "ap": "-3",
                "damage": "2",
                "keywords": "Anti-PSYKER 2+, Pistol, Precision, Psychic"
            },
            {
                "name": "\u27a4 Rite of Possession - focused witchfire",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "2",
                "skill": "3+",
                "strength": "6",
                "ap": "-3",
                "damage": "3",
                "keywords": "Anti-PSYKER 2+, Hazardous, Pistol, Precision, Psychic"
            },
            {
                "name": "Staff of possession",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "3+",
                "strength": "6",
                "ap": "-1",
                "damage": "D3",
                "keywords": "Anti-PSYKER 2+, Psychic"
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
                "description": "This model can be attached to the following units:\n\u25a0 CHOSEN\n\u25a0 LEGIONARIES\n\u25a0 POSSESSED"
            },
            {
                "name": "Daemonkin (Psychic)",
                "description": "While this model is leading a unit, add 1 to Advance and Charge rolls made for that unit."
            },
            {
                "name": "Sacrificial Dagger",
                "description": "Once per phase, when this model is selected to shoot or fight, it can use this ability. If it does, this model\u2019s unit suffers 1 mortal wound and, until the end of the phase, each time this model makes a Psychic Attack, add 1 to the Hit roll and add 1 to the Wound roll."
            }
        ]
    },
    "Masters of the Maelstrom": {
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
        "weapons": [
            {
                "name": "Absolver bolt pistol",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "5",
                "ap": "-1",
                "damage": "2",
                "keywords": "Pistol"
            },
            {
                "name": "Reductor array",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "6",
                "skill": "3+",
                "strength": "4",
                "ap": "-2",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "Mind Wrench",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "1",
                "skill": "2+",
                "strength": "6",
                "ap": "-2",
                "damage": "D6+1",
                "keywords": "Precision, Psychic"
            },
            {
                "name": "Force stave",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "2+",
                "strength": "6",
                "ap": "-2",
                "damage": "2",
                "keywords": "Psychic"
            },
            {
                "name": "Axe of Ending",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "6",
                "skill": "2+",
                "strength": "6",
                "ap": "-2",
                "damage": "2",
                "keywords": "Anti-CHARACTER 2+, Precision"
            },
            {
                "name": "Bolt pistol",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "4",
                "ap": "-1",
                "damage": "1",
                "keywords": "Pistol"
            },
            {
                "name": "Power sabre",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "3+",
                "strength": "4",
                "ap": "-2",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "Laspistol",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "4",
                "ap": "-1",
                "damage": "1",
                "keywords": "Pistol"
            },
            {
                "name": "Londaxi maimer",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "3",
                "skill": "3+",
                "strength": "4",
                "ap": "-1",
                "damage": "1",
                "keywords": "Assault"
            },
            {
                "name": "Bionic gauntlet",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "1",
                "skill": "2+",
                "strength": "6",
                "ap": "-2",
                "damage": "2",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Fleet Command",
                "description": "After both players have deployed their armies, if this unit is on the battlefield (or any Transport it is embarked within is on the battlefield) select up to three Heretic Astartes units from your army and redeploy them. When doing so, you can set those units up in Strategic Reserves, regardless of how many units are already in Strategic Reserves."
            },
            {
                "name": "Plunder",
                "description": "Once per battle, after this unit ends a Normal move, you can select one visible enemy unit within 12\" of it and roll one D6: on a 2+, that enemy unit suffers D3+1 mortal wounds."
            },
            {
                "name": "Masters of the Maelstrom",
                "description": "At the start of the Declare Battle Formations step, this unit can join one of the following units. This unit then counts as part of that unit for the rest of the battle, and that unit\u2019s Starting Strength is increased accordingly.\n- Chosen, Legionaries, Red Corsairs Raiders\n\n\nThis unit cannot join an Attached unit, and only Huron Blackheart can join a unit this unit has joined."
            },
            {
                "name": "Choice Samples",
                "description": "While this unit's Garreon the Corpsemaster model is on the battlefield, in your Command phase, select one of the following: you can return one destroyed model (excluding Character models) to this unit, or, if one or more Heretic Astartes Infantry units from your army are below Starting Strength and within 3\" of this unit, you gain 1CP."
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
                "name": "Siege Crawler",
                "description": "You can ignore any or all modifiers to this model's Move characteristic and to Advance and Charge rolls made for it."
            }
        ]
    },
    "Mutilators": {
        "stats": {
            "stat_movement": "5\"",
            "stat_toughness": 7,
            "stat_save": "2+",
            "stat_wounds": 5,
            "stat_leadership": "6+",
            "stat_oc": 2,
            "stat_invuln": "5+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "\u27a4 Fleshmetal weapons - rending strikes",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "3+",
                "strength": "9",
                "ap": "-3",
                "damage": "3",
                "keywords": "-"
            },
            {
                "name": "\u27a4 Fleshmetal weapons - clawed sweeps",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "6",
                "skill": "3+",
                "strength": "6",
                "ap": "-2",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "\u27a4 Fleshmetal weapons - thunderous blows",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "2",
                "skill": "3+",
                "strength": "12",
                "ap": "-4",
                "damage": "D6+2",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Crushing Charge",
                "description": "You can re-roll charge rolls made for this unit, and each time this unit makes a Charge move, select one enemy unit and roll one D6 for each model in this unit that is within Engagement Range of that unit: for each 4+, that enemy unit suffers D3 mortal wounds."
            }
        ]
    },
    "Nemesis Claw": {
        "stats": {
            "stat_movement": "6\"",
            "stat_toughness": 4,
            "stat_save": "3+",
            "stat_wounds": 2,
            "stat_leadership": "6+",
            "stat_oc": 1,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Nostraman chainblade",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "5",
                "skill": "3+",
                "strength": "4",
                "ap": "-1",
                "damage": "1",
                "keywords": "Sustained Hits 1"
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
                "name": "Boltgun",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "2",
                "skill": "3+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "-"
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
                "name": "Astartes chainsword",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "3+",
                "strength": "4",
                "ap": "-1",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "Heavy bolter",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "3",
                "skill": "4+",
                "strength": "5",
                "ap": "-1",
                "damage": "2",
                "keywords": "Heavy, Sustained Hits 1"
            },
            {
                "name": "\u27a4 Missile launcher - frag",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "D6",
                "skill": "4+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Blast, Heavy"
            },
            {
                "name": "\u27a4 Missile launcher - krak",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "1",
                "skill": "4+",
                "strength": "9",
                "ap": "-2",
                "damage": "D6",
                "keywords": "Heavy"
            },
            {
                "name": "Flamer",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "D6",
                "skill": "N/A",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Ignores Cover, Torrent"
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
                "keywords": "Rapid Fire 1"
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
                "keywords": "Hazardous, Rapid Fire 1"
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
                "keywords": "Melta 2"
            },
            {
                "name": "Nostraman chainglaive",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "3+",
                "strength": "8",
                "ap": "-2",
                "damage": "1",
                "keywords": "Sustained Hits 1"
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
            }
        ],
        "abilities": [
            {
                "name": "Visions of Suffering (Psychic)",
                "description": "Each time a model in this unit makes an attack that targets an enemy unit that is below its Starting Strength, add 1 to the Hit roll. If that enemy unit is Below Half-strength, add 1 to the Wound roll as well."
            },
            {
                "name": "Attached Unit",
                "description": "If a CHARACTER UNIT unit from your army with the Leader ability (excluding EPIC HEROES) can be attached to a LEGIONARIES unit, it can be attached to this unit instead."
            },
            {
                "name": "Voice eater",
                "description": "Enemy units (excluding MONSTERS and VEHICLES) cannot be targeted with Stratagems while they are within Engagement Range of the bearer\u2019s unit."
            }
        ]
    },
    "Noctilith Crown": {
        "stats": {
            "stat_movement": "-",
            "stat_toughness": 11,
            "stat_save": "3+",
            "stat_wounds": 14,
            "stat_leadership": "6+",
            "stat_oc": 0,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Lashing warp energies",
                "weapon_type": "ranged",
                "range": "6\"",
                "attacks": "8",
                "skill": "4+",
                "strength": "8",
                "ap": "-1",
                "damage": "2",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Malevolent Locus (Aura)",
                "description": "While a friendly HERETIC ASTARTES unit is within 9\" of this Fortification, improve that unit's Leadership characteristic by 1."
            },
            {
                "name": "Malign Cover",
                "description": "Each time a ranged attack is allocated to a model, if that model is not fully visible to every model in the attacking unit because of this Fortification, that model has the Benefit of Cover against that attack."
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
    "Obliterators": {
        "stats": {
            "stat_movement": "4\"",
            "stat_toughness": 7,
            "stat_save": "2+",
            "stat_wounds": 5,
            "stat_leadership": "6+",
            "stat_oc": 2,
            "stat_invuln": "5+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Crushing fists",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "3+",
                "strength": "9",
                "ap": "-2",
                "damage": "2",
                "keywords": "-"
            },
            {
                "name": "\u27a4 Fleshmetal guns - focused malice",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "D3",
                "skill": "3+",
                "strength": "12",
                "ap": "-3",
                "damage": "4",
                "keywords": "Melta 2"
            },
            {
                "name": "\u27a4 Fleshmetal guns - ruinous salvo",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "D6",
                "skill": "3+",
                "strength": "8",
                "ap": "-2",
                "damage": "2",
                "keywords": "Blast"
            },
            {
                "name": "\u27a4 Fleshmetal guns - warp hail",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "D6+3",
                "skill": "3+",
                "strength": "5",
                "ap": "-1",
                "damage": "1",
                "keywords": "Sustained Hits 1"
            }
        ],
        "abilities": [
            {
                "name": "Warp Rift Firepower",
                "description": "(Once per battle, per unit): In your Shooting phase, when this unit is selected to shoot, you can use this ability. If you do, this unit's ranged attacks have [INDIRECT FIRE]."
            }
        ]
    },
    "Plague Marines": {
        "stats": {
            "stat_movement": "5\"",
            "stat_toughness": 6,
            "stat_save": "3+",
            "stat_wounds": 2,
            "stat_leadership": "6+",
            "stat_oc": 2,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Power fist",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "3",
                "skill": "3+",
                "strength": "8",
                "ap": "-2",
                "damage": "2",
                "keywords": "Lethal Hits"
            },
            {
                "name": "Plague knives",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "3",
                "skill": "3+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Lethal Hits"
            },
            {
                "name": "Bubotic weapons",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "3+",
                "strength": "5",
                "ap": "-2",
                "damage": "1",
                "keywords": "Lethal Hits"
            },
            {
                "name": "Plague bolt pistol",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Lethal Hits"
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
                "keywords": "Rapid Fire 1"
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
                "keywords": "Hazardous, Rapid Fire 1"
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
                "keywords": "Lethal Hits"
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
                "name": "Heavy plague weapon",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "3",
                "skill": "4+",
                "strength": "8",
                "ap": "-2",
                "damage": "2",
                "keywords": "Lethal Hits"
            },
            {
                "name": "Blight launcher",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "D3",
                "skill": "3+",
                "strength": "6",
                "ap": "-1",
                "damage": "2",
                "keywords": "Blast, Lethal Hits"
            },
            {
                "name": "Plague spewer",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "D6",
                "skill": "N/A",
                "strength": "5",
                "ap": "-1",
                "damage": "1",
                "keywords": "Anti-INFANTRY 2+, Ignores Cover, Torrent"
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
                "keywords": "Melta 2"
            },
            {
                "name": "Plague belcher",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "D6",
                "skill": "N/A",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Anti-INFANTRY 4+, Ignores Cover, Torrent"
            }
        ],
        "abilities": [
            {
                "name": "Infused with the Blessings of Nurgle",
                "description": "In your Shooting phase, each time this unit is selected to shoot, after this unit has shot, select one enemy unit hit by one or more of those attacks. Until the start of your next turn, that unit is Afflicted."
            },
            {
                "name": "Icon of Despair",
                "description": "While an enemy unit is within 6\" of the bearer, worsen the Leadership characteristic of models in that unit by 1."
            }
        ]
    },
    "Possessed": {
        "stats": {
            "stat_movement": "9\"",
            "stat_toughness": 6,
            "stat_save": "3+",
            "stat_wounds": 3,
            "stat_leadership": "6+",
            "stat_oc": 1,
            "stat_invuln": "5+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Hideous mutations",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "3+",
                "strength": "5",
                "ap": "-1",
                "damage": "2",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Unholy Bloodshed",
                "description": "Once per battle, when this unit makes a Dark Pact, until the end of the phase, weapons equipped by models in this unit have the [DEVASTATING WOUNDS] ability."
            },
            {
                "name": "Chaos icon",
                "description": "Each time the bearer\u2019s unit takes a Leadership test for the Dark Pacts ability, you can re-roll that test."
            }
        ]
    },
    "Red Corsairs Raiders": {
        "stats": {
            "stat_movement": "6\"",
            "stat_toughness": 4,
            "stat_save": "3+",
            "stat_wounds": 3,
            "stat_leadership": "6+",
            "stat_oc": 2,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Boltgun",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "2",
                "skill": "3+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "Reaver's blade",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "3+",
                "strength": "5",
                "ap": "-1",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "Hand flamer",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "D6",
                "skill": "N/A",
                "strength": "3",
                "ap": "0",
                "damage": "1",
                "keywords": "Ignores Cover, Pistol, Torrent"
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
                "name": "Meltagun",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "9",
                "ap": "-4",
                "damage": "D6",
                "keywords": "Melta 2"
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
            }
        ],
        "abilities": [
            {
                "name": "Trophy Takers",
                "description": "The first time this unit destroys an enemy unit, until the end of the battle, while this unit is not Battle-shocked, add 1 to the Objective Control characteristic of models in this unit."
            },
            {
                "name": "Attached Unit",
                "description": "If a Character unit from your army with the Leader ability can be attached to a Legionaries unit, it can be attached to this unit instead."
            }
        ]
    },
    "Red Corsairs Reave-captain": {
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
                "name": "Bolt pistol",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "1",
                "skill": "2+",
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
                "skill": "2+",
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
                "skill": "2+",
                "strength": "8",
                "ap": "-3",
                "damage": "2",
                "keywords": "Hazardous, Pistol"
            },
            {
                "name": "Power sword",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "7",
                "skill": "2+",
                "strength": "5",
                "ap": "-2",
                "damage": "1",
                "keywords": "Sustained Hits 1"
            },
            {
                "name": "Power maul",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "5",
                "skill": "2+",
                "strength": "5",
                "ap": "-2",
                "damage": "2",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Brutal Raider",
                "description": "Each time this model's unit ends a Charge move, until the end of the turn, add 1 to the Strength characteristic of melee weapons equipped by this model and improve the Armour Penetration characteristic of those weapons by 1."
            },
            {
                "name": "Raider's Due",
                "description": "Each time this unit declares a Charge that targets one or more units that are within range of one or more objective markers, you can re-roll the Charge roll."
            },
            {
                "name": "Leader",
                "description": "This model can be attached to the following units: Chosen, Legionaries, Red Corsairs Raiders"
            }
        ]
    },
    "Rubric Marines": {
        "stats": {
            "stat_movement": "6\"",
            "stat_toughness": 4,
            "stat_save": "3+",
            "stat_wounds": 2,
            "stat_leadership": "7+",
            "stat_oc": 2,
            "stat_invuln": "5+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Force weapon",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "3",
                "skill": "3+",
                "strength": "6",
                "ap": "-1",
                "damage": "D3",
                "keywords": "Psychic"
            },
            {
                "name": "Malefic Curse",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "3",
                "skill": "3+",
                "strength": "4",
                "ap": "-3",
                "damage": "1",
                "keywords": "Anti-INFANTRY 4+, Devastating Wounds, Psychic"
            },
            {
                "name": "Inferno bolt pistol",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "4",
                "ap": "-1",
                "damage": "1",
                "keywords": "Pistol"
            },
            {
                "name": "Warpflame pistol",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "D6",
                "skill": "N/A",
                "strength": "3",
                "ap": "-1",
                "damage": "1",
                "keywords": "Ignores Cover, Pistol, Torrent"
            },
            {
                "name": "Inferno boltgun",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "2",
                "skill": "3+",
                "strength": "4",
                "ap": "-2",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "Close combat weapon",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "2",
                "skill": "3+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "Warpflamer",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "D6",
                "skill": "N/A",
                "strength": "4",
                "ap": "-1",
                "damage": "1",
                "keywords": "Ignores Cover, Torrent"
            },
            {
                "name": "Soulreaper cannon",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "6",
                "skill": "3+",
                "strength": "6",
                "ap": "-2",
                "damage": "1",
                "keywords": "Devastating Wounds"
            }
        ],
        "abilities": [
            {
                "name": "Bringers of Change",
                "description": "Each time a model in this unit makes a ranged attack, re-roll a Wound roll of 1. If the target of that attack is within range of an objective marker you do not control, you can re-roll the Wound roll instead."
            },
            {
                "name": "Icon of Flame",
                "description": "Ranged weapons equipped by models in this unit (excluding Characters) have the [Ignores Cover] ability."
            }
        ]
    },
    "Sorcerer": {
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
                "name": "\u27a4 Infernal Gaze - witchfire",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "D6",
                "skill": "3+",
                "strength": "5",
                "ap": "-1",
                "damage": "D3",
                "keywords": "Psychic"
            },
            {
                "name": "\u27a4 Infernal Gaze - focused witchfire",
                "weapon_type": "ranged",
                "range": "24\"",
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
                "ap": "-1",
                "damage": "D3",
                "keywords": "Psychic"
            }
        ],
        "abilities": [
            {
                "name": "Leader",
                "description": "This model can be attached to the following units:\n\u25a0 CHOSEN\n\u25a0 LEGIONARIES"
            },
            {
                "name": "Prescience (Psychic)",
                "description": "While this model is leading a unit, each time an attack targets that unit, subtract 1 from the Hit roll."
            },
            {
                "name": "Gift of Chaos (Psychic)",
                "description": "Each time this model is selected to shoot or fight, after resolving its attacks, select one enemy unit hit by one or more of those attacks that had the [PSYCHIC] ability. That unit must take a Leadership test: if that test is failed, that unit suffers D3 mortal wounds."
            }
        ]
    },
    "Sorcerer in Terminator Armour": {
        "stats": {
            "stat_movement": "5\"",
            "stat_toughness": 5,
            "stat_save": "2+",
            "stat_wounds": 5,
            "stat_leadership": "6+",
            "stat_oc": 1,
            "stat_invuln": "4+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "\u27a4 Infernal Gaze - witchfire",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "D6",
                "skill": "3+",
                "strength": "5",
                "ap": "-1",
                "damage": "D3",
                "keywords": "Psychic"
            },
            {
                "name": "\u27a4 Infernal Gaze - focused witchfire",
                "weapon_type": "ranged",
                "range": "24\"",
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
                "ap": "-1",
                "damage": "D3",
                "keywords": "Psychic"
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
                "name": "Leader",
                "description": "This model can be attached to the following units:\n\u25a0 CHAOS TERMINATOR SQUAD"
            },
            {
                "name": "Warptime (Psychic)",
                "description": "While this model is leading a unit, you can re-roll Advance and Charge rolls made for that unit."
            },
            {
                "name": "Death Hex (Psychic)",
                "description": "At the start of your Shooting phase, one PSYKER with this ability can use it. If it does, select one enemy unit within 12\" of and visible to that PSYKER and roll one D6: on a 1, that PSYKER's unit suffers D3 mortal wounds; on a 2+, until the start of your next Movement phase, each time an attack targets that enemy unit, improve the Armour Penetration characteristic of that attack by 1."
            },
            {
                "name": "Chaos Familiar",
                "description": "Once per battle, when an attack is allocated to the bearer, you can change the Damage characteristic to 0."
            }
        ]
    },
    "Traitor Enforcer": {
        "stats": {
            "stat_movement": "6\"",
            "stat_toughness": 3,
            "stat_save": "5+",
            "stat_wounds": 3,
            "stat_leadership": "6+",
            "stat_oc": 1,
            "stat_invuln": "5+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Power fist",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "3",
                "skill": "3+",
                "strength": "6",
                "ap": "-2",
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
            },
            {
                "name": "Ogryn weapons",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "5",
                "skill": "3+",
                "strength": "7",
                "ap": "-1",
                "damage": "2",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Leader",
                "description": "This unit can be attached to the following unit:\n\u25a0 TRAITOR GUARDSMAN SQUAD"
            },
            {
                "name": "Brutal Example",
                "description": "Once per turn, while this unit is leading a unit and contains a TRAITOR ENFORCER model, you can target that unit with the Fire Overwatch Stratagem for 0CP, and can do so even if you have already targeted a different unit from your army with that Stratagem this phase. Each time you use this ability, one Bodyguard model in that unit is destroyed."
            },
            {
                "name": "Mutated Bodyguard",
                "description": "While this unit contains a Traitor Ogryn model, CHARACTER models in this unit have the Feel No Pain 4+ ability."
            }
        ]
    },
    "Traitor Guardsmen Squad": {
        "stats": {
            "stat_movement": "6\"",
            "stat_toughness": 3,
            "stat_save": "5+",
            "stat_wounds": 1,
            "stat_leadership": "7+",
            "stat_oc": 2,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Chainsword",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "3",
                "skill": "4+",
                "strength": "3",
                "ap": "0",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "Power weapon",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "2",
                "skill": "4+",
                "strength": "4",
                "ap": "-2",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "Close combat weapon",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "1",
                "skill": "4+",
                "strength": "3",
                "ap": "0",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "Corrupted pistol",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "1",
                "skill": "4+",
                "strength": "4",
                "ap": "-1",
                "damage": "1",
                "keywords": "Pistol"
            },
            {
                "name": "Boltgun",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "1",
                "skill": "4+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Rapid Fire 1"
            },
            {
                "name": "Lasgun",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "1",
                "skill": "4+",
                "strength": "3",
                "ap": "0",
                "damage": "1",
                "keywords": "Rapid Fire 1"
            },
            {
                "name": "Flamer",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "D6",
                "skill": "N/A",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Ignores Cover, Torrent"
            },
            {
                "name": "\u27a4 Plasma gun - standard",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "1",
                "skill": "4+",
                "strength": "7",
                "ap": "-2",
                "damage": "1",
                "keywords": "Rapid Fire 1"
            },
            {
                "name": "\u27a4 Plasma gun - supercharge",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "1",
                "skill": "4+",
                "strength": "8",
                "ap": "-3",
                "damage": "2",
                "keywords": "Hazardous, Rapid Fire 1"
            },
            {
                "name": "Meltagun",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "1",
                "skill": "4+",
                "strength": "9",
                "ap": "-4",
                "damage": "D6",
                "keywords": "Melta 2"
            },
            {
                "name": "Cultist sniper rifle",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "1",
                "skill": "4+",
                "strength": "4",
                "ap": "-2",
                "damage": "2",
                "keywords": "Heavy, Precision"
            },
            {
                "name": "\u27a4 Cultist grenade launcher - frag",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "D3",
                "skill": "4+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Blast"
            },
            {
                "name": "\u27a4 Cultist grenade launcher - krak",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "1",
                "skill": "4+",
                "strength": "9",
                "ap": "-2",
                "damage": "D3",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Twisted Defence Force",
                "description": "While this unit is within range of an objective, this unit has +1 Sv against ranged attacks."
            }
        ]
    },
    "Vashtorr the Arkifane": {
        "stats": {
            "stat_movement": "12\"",
            "stat_toughness": 10,
            "stat_save": "2+",
            "stat_wounds": 14,
            "stat_leadership": "6+",
            "stat_oc": 3,
            "stat_invuln": "4+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Vashtorr's claw",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "D6",
                "skill": "N/A",
                "strength": "5",
                "ap": "-2",
                "damage": "1",
                "keywords": "Anti-VEHICLE 4+, Torrent"
            },
            {
                "name": "\u27a4 Vashtorr's hammer - strike",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "6",
                "skill": "2+",
                "strength": "14",
                "ap": "-3",
                "damage": "3",
                "keywords": "Anti-VEHICLE 4+, Devastating Wounds"
            },
            {
                "name": "\u27a4 Vashtorr's hammer - sweep",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "12",
                "skill": "2+",
                "strength": "8",
                "ap": "-1",
                "damage": "2",
                "keywords": "Anti-VEHICLE 4+, Devastating Wounds"
            }
        ],
        "abilities": [
            {
                "name": "Unholy Mechanisms (Aura)",
                "description": "While a friendly Daemon Vehicle unit is within 6\" of this model, add 2 to the Strength characteristic of weapons equipped by models in that unit."
            },
            {
                "name": "Reorder Reality",
                "description": "Each time an enemy unit within 18\" of this model targets this model, subtract 1 from the Hit roll and, until the end of the phase, that enemy unit\u2019s ranged weapons have the [HAZARDOUS] ability."
            },
            {
                "name": "Indentured Daemon Engines",
                "description": "While this model is within 3\" of one or more friendly Daemon Vehicle units, this model has the Lone Operative ability."
            }
        ]
    },
    "Venomcrawler": {
        "stats": {
            "stat_movement": "12\"",
            "stat_toughness": 9,
            "stat_save": "3+",
            "stat_wounds": 9,
            "stat_leadership": "6+",
            "stat_oc": 3,
            "stat_invuln": "5+",
            "stat_fnp": ""
        },
        "weapons": [
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
                "name": "Soulflayer tendrils and claws",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "6",
                "skill": "3+",
                "strength": "6",
                "ap": "-1",
                "damage": "2",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Soul Eater",
                "description": "At the end of the Fight phase, if one or more attacks made by this model that phase destroyed one or more enemy units, until the end of the battle, add 1 to the Attacks characteristic of this model\u2019s weapons."
            }
        ]
    },
    "Warpsmith": {
        "stats": {
            "stat_movement": "6\"",
            "stat_toughness": 4,
            "stat_save": "2+",
            "stat_wounds": 4,
            "stat_leadership": "6+",
            "stat_oc": 1,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Flamer tendril",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "D6",
                "skill": "N/A",
                "strength": "3",
                "ap": "0",
                "damage": "1",
                "keywords": "Ignores Cover, Pistol, Torrent"
            },
            {
                "name": "Forge weapon",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "3+",
                "strength": "6",
                "ap": "-2",
                "damage": "2",
                "keywords": "Anti-VEHICLE 4+"
            },
            {
                "name": "Melta tendril",
                "weapon_type": "ranged",
                "range": "6\"",
                "attacks": "1",
                "skill": "2+",
                "strength": "8",
                "ap": "-4",
                "damage": "D3",
                "keywords": "Melta 1, Pistol"
            },
            {
                "name": "\u27a4 Plasma pistol - standard",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "1",
                "skill": "2+",
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
                "skill": "2+",
                "strength": "8",
                "ap": "-3",
                "damage": "2",
                "keywords": "Hazardous, Pistol"
            }
        ],
        "abilities": [
            {
                "name": "Warpsmith",
                "description": "While this model is within 3\" of one or more friendly Heretic Astartes Vehicle units, this model has the Lone Operative ability."
            },
            {
                "name": "Master of Mechanisms",
                "description": "In your Command phase, select one friendly Heretic Astartes Vehicle model within 3\" of this model. That Vehicle model regains up to D3 lost wounds and, until the start of your next Command phase, each time that Vehicle makes an attack, add 1 to the Hit roll. Each model can only be selected for this ability once per Command phase."
            },
            {
                "name": "Enrage Machine Spirits",
                "description": "At the end of your Movement phase, select one enemy Vehicle unit within 12\" of this model. That unit must take a Battle-shock test."
            },
            {
                "name": "Leader",
                "description": "This model can be attached to the following units: Chosen, Havocs, Legionaires"
            }
        ]
    }
}


class Command(BaseCommand):
    """Refresh Chaos Space Marines stat lines, weapon profiles, and abilities from BSData."""

    help = 'Refresh 11th Edition stats/weapons/abilities for Chaos Space Marines units.'

    def add_arguments(self, parser):
        """Add --dry-run flag."""
        parser.add_argument(
            '--dry-run', action='store_true',
            help='Preview changes without writing to the database.',
        )

    def handle(self, *args, **options):
        """Iterate CHAOS_SPACE_MARINES_DATASHEETS and refresh each unit's datasheet data."""
        dry_run = options['dry_run']
        updated = 0
        skipped = 0

        with transaction.atomic():
            for name, payload in CHAOS_SPACE_MARINES_DATASHEETS.items():
                try:
                    unit = UnitType.objects.get(name=name, faction__name='Chaos Space Marines')
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
