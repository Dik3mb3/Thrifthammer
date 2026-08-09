"""
Management command: seed_tyranids_datasheets

Refreshes stat lines, weapon profiles, and abilities for Tyranids units
using 11th Edition data sourced from BSData/wh40k-11e ("Tyranids.json"
main roster + "Library - Tyranids.json" for units the roster only thinly
links to) -- the same sources used by seed_tyranids_points.py.

Usage:
    python manage.py seed_tyranids_datasheets
    python manage.py seed_tyranids_datasheets --dry-run

Notes:
- Does NOT touch points_cost or category -- those are handled entirely by
  seed_tyranids_points.py. This command only refreshes stat_* fields,
  WeaponProfile rows, and UnitAbility rows.
- Scope is all 45 real-unit active Tyranids rows (excludes the Combat
  Patrol bundle, which correctly has no BSData match and is simply
  skipped).
- Per-field safety rule: a unit\'s stats/weapons/abilities are only
  overwritten when BSData actually has that data for it. If extraction
  found nothing, the existing DB value/rows are left untouched.
- All 45 real units resolved cleanly on the first pass -- 0 missing
  stats, weapons, or abilities, 0 overlong stat fields.
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from calculators.models import UnitAbility, UnitType, WeaponProfile

# (name -> {stats?, weapons?, abilities?}). Missing keys mean "no data
# found for this field -- leave existing DB data untouched."
TYRANIDS_DATASHEETS = {
    "Tyranid Barbgaunts": {
        "stats": {
            "stat_movement": "6\"",
            "stat_toughness": 4,
            "stat_save": "4+",
            "stat_wounds": 2,
            "stat_leadership": "8+",
            "stat_oc": 1,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Barblauncher",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "D6",
                "skill": "4+",
                "strength": "5",
                "ap": "0",
                "damage": "1",
                "keywords": "Blast, Heavy"
            },
            {
                "name": "Chitinous claws and teeth",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "1",
                "skill": "4+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Disruption Bombardment",
                "description": "In your Shooting phase, after this unit has shot, select one enemy INFANTRY unit hit by one or more of those attacks. Until the end of your opponent\u2019s next turn, that enemy unit is disrupted. While a unit is disrupted, subtract 2 from its Move characteristic, and subtract 2 from Advance and Charge rolls made for it."
            }
        ]
    },
    "Tyranid Biovore": {
        "stats": {
            "stat_movement": "5\"",
            "stat_toughness": 6,
            "stat_save": "3+",
            "stat_wounds": 5,
            "stat_leadership": "8+",
            "stat_oc": 1,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Spore mine launcher",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "D3",
                "skill": "4+",
                "strength": "6",
                "ap": "-1",
                "damage": "2",
                "keywords": "Blast, Devastating Wounds, Heavy, Indirect Fire"
            },
            {
                "name": "Chitin-barbed limbs",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "2",
                "skill": "4+",
                "strength": "5",
                "ap": "0",
                "damage": "1",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Seed Spore Mines",
                "description": "Once per turn, in your Shooting Phase, when selected to shoot, one unit with this ability can use it instead of making any attacks with its ranged weapons. If it does, you can add one new SPORE MINES unit to your army and set it up anywhere on the battlefield that is wholly within 48\" of this unit and more than 8\" horizontally away from all enemy units. That SPORE MINES unit contains 1 model for each model in this unit."
            }
        ]
    },
    "Tyranid Broodlord": {
        "stats": {
            "stat_movement": "8\"",
            "stat_toughness": 5,
            "stat_save": "4+",
            "stat_wounds": 6,
            "stat_leadership": "7+",
            "stat_oc": 1,
            "stat_invuln": "4+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Broodlord Claws and Talons",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "5",
                "skill": "2+",
                "strength": "6",
                "ap": "-2",
                "damage": "2",
                "keywords": "Devastating Wounds, Twin-linked"
            }
        ],
        "abilities": [
            {
                "name": "Vicious Insight",
                "description": "While this model is leading a unit, weapons equipped by models in that unit have the [DEVASTATING WOUNDS] ability."
            },
            {
                "name": "Hypnotic Gaze (Psychic)",
                "description": "At the start of the Fight phase, select one enemy unit within Engagement Range of this model. Until the end of the phase, each time a model in that unit makes an attack, subtract 1 from the Hit roll."
            },
            {
                "name": "Leader",
                "description": "This model can be attached to the following unit:\n- Genestealers"
            }
        ]
    },
    "Tyranid Carnifex": {
        "stats": {
            "stat_movement": "8\"",
            "stat_toughness": 9,
            "stat_save": "2+",
            "stat_wounds": 10,
            "stat_leadership": "8+",
            "stat_oc": 3,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Bio-plasmic scream",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "D6+3",
                "skill": "4+",
                "strength": "8",
                "ap": "-2",
                "damage": "1",
                "keywords": "Assault, Blast"
            },
            {
                "name": "Screamer-killer talons",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "10",
                "skill": "3+",
                "strength": "10",
                "ap": "-2",
                "damage": "3",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Death Scream",
                "description": "In your Shooting phase, after this model has shot, select one unit hit by one or more of those attacks. That unit must take a Battle-shock test, subtracting 1 from that test."
            }
        ]
    },
    "Tyranid Deathleaper": {
        "stats": {
            "stat_movement": "8\"",
            "stat_toughness": 6,
            "stat_save": "3+",
            "stat_wounds": 7,
            "stat_leadership": "7+",
            "stat_oc": 1,
            "stat_invuln": "4+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Lictor claws and talons",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "6",
                "skill": "2+",
                "strength": "7",
                "ap": "-2",
                "damage": "2",
                "keywords": "Precision"
            }
        ],
        "abilities": [
            {
                "name": "Fear of the Unseen (Aura)",
                "description": "While an enemy unit is within 6\" of this model, worsen the Leadership characteristic of models in that unit by 1. In addition, in the Battle-shock step of your opponent\u2019s Command phase, if such an enemy unit is below its Starting Strength, it must take a Battle-shock test."
            },
            {
                "name": "Hunter Organism",
                "description": "This model cannot be your Warlord"
            },
            {
                "name": "Feeder Tendrils",
                "description": "Each time this model destroys an enemy Character model, you gain 1CP."
            }
        ]
    },
    "Tyranid Exocrine": {
        "stats": {
            "stat_movement": "8\"",
            "stat_toughness": 10,
            "stat_save": "3+",
            "stat_wounds": 14,
            "stat_leadership": "8+",
            "stat_oc": 4,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Bio-plasmic cannon",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "D6+3",
                "skill": "3+",
                "strength": "9",
                "ap": "-3",
                "damage": "3",
                "keywords": "Blast, Heavy"
            },
            {
                "name": "Powerful limbs",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "3",
                "skill": "3+",
                "strength": "7",
                "ap": "0",
                "damage": "2",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Symbiotic Targeting",
                "description": "In your Shooting phase, after this model has shot, select one enemy unit hit by one or more of those attacks. Until the end of the phase, each time a friendly TYRANIDS model makes an attack that targets that unit, re-roll a Hit roll of 1."
            },
            {
                "name": "Damaged: 1-5 Wounds Remaining",
                "description": "While this model has 1-5 wounds remaining, each time this model makes an attack, subtract 1 from the Hit roll."
            }
        ]
    },
    "Tyranid Gargoyle Brood": {
        "stats": {
            "stat_movement": "12\"",
            "stat_toughness": 3,
            "stat_save": "6+",
            "stat_wounds": 1,
            "stat_leadership": "8+",
            "stat_oc": 2,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Blinding venom",
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
                "name": "Fleshborer",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "1",
                "skill": "4+",
                "strength": "5",
                "ap": "0",
                "damage": "1",
                "keywords": "Assault"
            }
        ],
        "abilities": [
            {
                "name": "Winged Swarm",
                "description": "In your Shooting phase, after this unit has shot, if it is not within Engagement Range of any enemy units, it can make a Normal move of up to 6\". If it does, until the end of the turn, this unit is not eligible to declare a charge."
            }
        ]
    },
    "Tyranid Genestealers": {
        "stats": {
            "stat_movement": "8\"",
            "stat_toughness": 4,
            "stat_save": "5+",
            "stat_wounds": 2,
            "stat_leadership": "7+",
            "stat_oc": 1,
            "stat_invuln": "5+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Genestealers claws and talons",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "2+",
                "strength": "4",
                "ap": "-2",
                "damage": "1",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Vanguard Predator",
                "description": "Each time a model in this unit makes an attack, re-roll a Hit roll of 1. If the target is within range of one or more objective markers, re-roll a Wound roll 1 as well."
            }
        ]
    },
    "Tyranid Harpy": {
        "stats": {
            "stat_movement": "-",
            "stat_toughness": 9,
            "stat_save": "3+",
            "stat_wounds": 12,
            "stat_leadership": "8+",
            "stat_oc": None,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Stinger salvoes",
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
                "name": "Scything wings",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "4+",
                "strength": "7",
                "ap": "-1",
                "damage": "2",
                "keywords": "-"
            },
            {
                "name": "Twin stranglethorn cannon",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "D6+1",
                "skill": "2+",
                "strength": "7",
                "ap": "-1",
                "damage": "2",
                "keywords": "Blast, Twin-linked"
            },
            {
                "name": "Twin heavy venom cannon",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "D3",
                "skill": "3+",
                "strength": "9",
                "ap": "-2",
                "damage": "3",
                "keywords": "Blast, Twin-linked"
            }
        ],
        "abilities": [
            {
                "name": "Spore Mine Cysts",
                "description": "At the end of your opponent\u2019s Fight phase, you can do one of the following:\n- Select one visible enemy unit (excluding Lone Operative units) within 24\" of this unit and roll six D6 for that unit: for each 3+, that unit suffers 1 mortal wound.\n- Add a new SPORE MINES unit containing D3 models to your army and set it up anywhere on the battlefield that is within 6\" of this model and more than 8\" horizontally away from all enemy units. You cannot select this option for more than one model per turn."
            },
            {
                "name": "Damaged: 1-4 Wounds Remaining",
                "description": "While this model has 1-4 wounds remaining, each time this model makes an attack, subtract 1 from the Hit roll."
            }
        ]
    },
    "Tyranid Harridan": {
        "stats": {
            "stat_movement": "14\"",
            "stat_toughness": 10,
            "stat_save": "3+",
            "stat_wounds": 30,
            "stat_leadership": "8+",
            "stat_oc": 0,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Dire bio-cannon",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "D6+6",
                "skill": "3+",
                "strength": "10",
                "ap": "-3",
                "damage": "3",
                "keywords": "Blast"
            },
            {
                "name": "Gargantuan scything talons",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "6",
                "skill": "3+",
                "strength": "14",
                "ap": "-2",
                "damage": "D6",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Damaged: 1-10 wounds remaining",
                "description": "While this model has 1-10 wounds remaining, each time this model makes an attack, subtract 1 from the Hit roll."
            },
            {
                "name": "Frenzied Metabolism",
                "description": "Each time this model is selected to shoot, you can use this ability. If you do, until the end of the phase, each time this model makes an attack, add 1 to the Wound roll. After resolving those attacks, roll one D6: on a 2+, this model suffers D3 mortal wounds."
            }
        ]
    },
    "Tyranid Haruspex": {
        "stats": {
            "stat_movement": "8\"",
            "stat_toughness": 11,
            "stat_save": "3+",
            "stat_wounds": 14,
            "stat_leadership": "8+",
            "stat_oc": 4,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Grasping tongue",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "6",
                "ap": "-2",
                "damage": "D6+1",
                "keywords": "Precision"
            },
            {
                "name": "Shovelling claws",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "3+",
                "strength": "14",
                "ap": "-2",
                "damage": "D6+1",
                "keywords": "Extra Attacks"
            },
            {
                "name": "Ravenous maw",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "14",
                "skill": "3+",
                "strength": "7",
                "ap": "-1",
                "damage": "2",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Grisly Spectacle",
                "description": "Each time this model is selected to fight, after resolving its attacks, if one or more enemy units were destroyed by those attacks, each enemy unit within 6\" of this model must take a Battle-shock test."
            },
            {
                "name": "Damaged: 1-5 Wounds Remaining",
                "description": "While this model has 1-5 wounds remaining, each time this model makes an attack, subtract 1 from the Hit roll."
            }
        ]
    },
    "Tyranid Hierophant Bio-Titan": {
        "stats": {
            "stat_movement": "12\"",
            "stat_toughness": 14,
            "stat_save": "2+",
            "stat_wounds": 30,
            "stat_leadership": "8+",
            "stat_oc": 12,
            "stat_invuln": "5+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Bio-plasma torrent",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "3D6",
                "skill": "N/A",
                "strength": "7",
                "ap": "-2",
                "damage": "1",
                "keywords": "Assault, Torrent"
            },
            {
                "name": "Dire bio-cannon",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "D6+6",
                "skill": "3+",
                "strength": "10",
                "ap": "-3",
                "damage": "3",
                "keywords": "Blast"
            },
            {
                "name": "Lashwhip pods",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "10",
                "skill": "3+",
                "strength": "5",
                "ap": "-1",
                "damage": "1",
                "keywords": "Extra Attacks"
            },
            {
                "name": "Titanic scything talons",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "8",
                "skill": "3+",
                "strength": "20",
                "ap": "-2",
                "damage": "D6+1",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Damaged: 1-10 wounds remaining",
                "description": "While this model has 1-10 wounds remaining, subtract 6 from this model\u2019s Objective Control characteristic and each time this model makes an attack, subtract 1 from the Hit roll."
            },
            {
                "name": "Apex-beast",
                "description": "Each time this model makes an attack that targets a unit that is Battle-shocked, add 1 to the Hit roll."
            },
            {
                "name": "Stalking Forward",
                "description": "Each time this model makes a Normal, Advance or Fall Back move, it can move over models (excluding TITANIC models) and terrain features that are 4\" or less in height as if they were not there."
            }
        ]
    },
    "Tyranid Hive Crone": {
        "stats": {
            "stat_movement": "-",
            "stat_toughness": 9,
            "stat_save": "3+",
            "stat_wounds": 12,
            "stat_leadership": "8+",
            "stat_oc": None,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Drool cannon",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "2D6",
                "skill": "N/A",
                "strength": "6",
                "ap": "-1",
                "damage": "1",
                "keywords": "Torrent"
            },
            {
                "name": "Tentaclids",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "4",
                "skill": "3+",
                "strength": "7",
                "ap": "0",
                "damage": "2",
                "keywords": "Anti-vehicle 4+, Devastating Wounds"
            },
            {
                "name": "Thorax spur",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "1",
                "skill": "3+",
                "strength": "10",
                "ap": "-3",
                "damage": "D6",
                "keywords": "Anti-fly 2+, Extra Attacks"
            },
            {
                "name": "Scything wings",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "4+",
                "strength": "7",
                "ap": "-1",
                "damage": "2",
                "keywords": "-"
            },
            {
                "name": "Stinger salvoes",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "8",
                "skill": "3+",
                "strength": "5",
                "ap": "0",
                "damage": "1",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Airborne Predator",
                "description": "Each time this model makes a ranged attack that targets a unit that can FLY, add 1 to the Hit roll."
            },
            {
                "name": "Damaged: 1-4 Wounds Remaining",
                "description": "While this model has 1-4 wounds remaining, each time this model makes an attack, subtract 1 from the Hit roll."
            }
        ]
    },
    "Tyranid Hive Guard": {
        "stats": {
            "stat_movement": "6\"",
            "stat_toughness": 7,
            "stat_save": "3+",
            "stat_wounds": 4,
            "stat_leadership": "8+",
            "stat_oc": 1,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Shockcannon",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "2",
                "skill": "3+",
                "strength": "7",
                "ap": "-1",
                "damage": "3",
                "keywords": "Anti-Vehicle 2+"
            },
            {
                "name": "Chitinous claws and teeth",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "3",
                "skill": "4+",
                "strength": "5",
                "ap": "0",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "Impaler cannon",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "4",
                "skill": "4+",
                "strength": "5",
                "ap": "-1",
                "damage": "1",
                "keywords": "Heavy, Indirect Fire"
            }
        ],
        "abilities": [
            {
                "name": "Defensive Stance",
                "description": "Each time you target this unit with the Fire Overwatch Stratagem, while resolving that Stratagem, hits are scored on unmodified Hit rolls of 5+, or unmodified Hit rolls of 4+ instead if this unit is within range of an objective marker that you control."
            }
        ]
    },
    "Tyranid Hive Tyrant": {
        "stats": {
            "stat_movement": "8\"",
            "stat_toughness": 10,
            "stat_save": "2+",
            "stat_wounds": 10,
            "stat_leadership": "7+",
            "stat_oc": 3,
            "stat_invuln": "4+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Monstrous bonesword and lash whip",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "6",
                "skill": "2+",
                "strength": "9",
                "ap": "-2",
                "damage": "3",
                "keywords": "Twin-linked"
            },
            {
                "name": "Heavy venom cannon",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "D3",
                "skill": "2+",
                "strength": "9",
                "ap": "-2",
                "damage": "3",
                "keywords": "Blast"
            },
            {
                "name": "Stranglethorn cannon",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "D6+1",
                "skill": "2+",
                "strength": "7",
                "ap": "-1",
                "damage": "2",
                "keywords": "Blast"
            },
            {
                "name": "Monstrous scything talons",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "2+",
                "strength": "7",
                "ap": "-2",
                "damage": "2",
                "keywords": "Extra Attacks"
            }
        ],
        "abilities": [
            {
                "name": "Onslaught (Aura, Psychic)",
                "description": "While a friendly TYRANIDS unit is within 6\" of this model, ranged weapons equipped by models in that unit have the [ASSAULT] and [LETHAL HITS] abilities."
            },
            {
                "name": "Leader",
                "description": "This model can be attached to the following unit:\n- Tyrant Guard"
            },
            {
                "name": "Will of the Hive Mind",
                "description": "Once per battle round, one model from your army with this ability can use it when a friendly TYRANIDS unit within 12\" of that model is targeted with a Stratagem. If it does, reduce the CP cost of that use of that Stratagem by 1CP."
            }
        ]
    },
    "Tyranid Hormagaunts": {
        "stats": {
            "stat_movement": "10\"",
            "stat_toughness": 3,
            "stat_save": "5+",
            "stat_wounds": 1,
            "stat_leadership": "8+",
            "stat_oc": 2,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Hormagaunt talons",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "3",
                "skill": "4+",
                "strength": "3",
                "ap": "-1",
                "damage": "1",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Bounding Leap",
                "description": "This unit is eligible to declare a charge in a turn in which it Advanced."
            }
        ]
    },
    "Tyranid Lictor": {
        "stats": {
            "stat_movement": "8\"",
            "stat_toughness": 6,
            "stat_save": "4+",
            "stat_wounds": 6,
            "stat_leadership": "7+",
            "stat_oc": 1,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Lictor claws and talons",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "6",
                "skill": "2+",
                "strength": "7",
                "ap": "-2",
                "damage": "2",
                "keywords": "Precision"
            }
        ],
        "abilities": [
            {
                "name": "Pheromone Trail",
                "description": "Once per battle round, you can target one model with this ability with the Rapid Ingress Stratagem for 0CP."
            },
            {
                "name": "Feeder Tendrils",
                "description": "Each time this model destroys an enemy Character model, you gain 1CP."
            }
        ]
    },
    "Tyranid Maleceptor": {
        "stats": {
            "stat_movement": "8\"",
            "stat_toughness": 11,
            "stat_save": "3+",
            "stat_wounds": 14,
            "stat_leadership": "7+",
            "stat_oc": 4,
            "stat_invuln": "4+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "\u27a4 Massive scything talons - strike",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "3",
                "skill": "3+",
                "strength": "9",
                "ap": "-2",
                "damage": "D6+1",
                "keywords": "-"
            },
            {
                "name": "\u27a4 Massive scything talons - sweep",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "6",
                "skill": "3+",
                "strength": "7",
                "ap": "-1",
                "damage": "2",
                "keywords": "-"
            },
            {
                "name": "Psychic overload",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "D6+3",
                "skill": "3+",
                "strength": "10",
                "ap": "-2",
                "damage": "3",
                "keywords": "Blast, Psychic"
            }
        ],
        "abilities": [
            {
                "name": "Encephalic Diffusion (Aura, Psychic)",
                "description": "While an enemy unit is within 6\" of this model, each time a model in that unit makes an attack, subtract 1 from the Hit roll, and, if that enemy unit is Below Half-strength, subtract 1 from the Wound roll as well."
            },
            {
                "name": "Damaged: 1-5 Wounds Remaining",
                "description": "While this model has 1-5 wounds remaining, each time this model makes an attack, subtract 1 from the Hit roll."
            }
        ]
    },
    "Tyranid Mawloc": {
        "stats": {
            "stat_movement": "10\"",
            "stat_toughness": 10,
            "stat_save": "3+",
            "stat_wounds": 14,
            "stat_leadership": "8+",
            "stat_oc": 4,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Distendible jaw",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "1",
                "skill": "3+",
                "strength": "5",
                "ap": "0",
                "damage": "3",
                "keywords": "Anti-infantry 4+, Devastating Wounds, Extra Attacks"
            },
            {
                "name": "Mawloc scything talons",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "16",
                "skill": "3+",
                "strength": "8",
                "ap": "-2",
                "damage": "1",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Terror from the Deep",
                "description": "Each time this unit is set up on the battlefield using the Deep Strike ability, roll one D6 for each enemy unit within 12\" of this model: on a 2-4, that unit suffers D3 mortal wounds; on a 5+, that unit suffers 3 mortal wounds and must take a Battle-shock test."
            },
            {
                "name": "Damaged: 1-5 Wounds Remaining",
                "description": "While this model has 1-5 wounds remaining, each time this model makes an attack, subtract 1 from the Hit roll."
            }
        ]
    },
    "Tyranid Neurogaunts": {
        "stats": {
            "stat_movement": "6\"",
            "stat_toughness": 3,
            "stat_save": "6+",
            "stat_wounds": 1,
            "stat_leadership": "8+",
            "stat_oc": 1,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Chitinous claws and teeth",
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
                "name": "Neurocytes",
                "description": "While this unit is within Synapse Range of your friendly Tyranids unit (excluding Neurogaunt units), it has the Synapse keyword."
            }
        ]
    },
    "Tyranid Neurolictor": {
        "stats": {
            "stat_movement": "8\"",
            "stat_toughness": 5,
            "stat_save": "4+",
            "stat_wounds": 7,
            "stat_leadership": "7+",
            "stat_oc": 1,
            "stat_invuln": "4+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Piercing claws and talons",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "6",
                "skill": "2+",
                "strength": "6",
                "ap": "-2",
                "damage": "1",
                "keywords": "Precision"
            }
        ],
        "abilities": [
            {
                "name": "Feeder Tendrils",
                "description": "Each time this model destroys an enemy CHARACTER model, you gain 1CP"
            },
            {
                "name": "Neural Disruption",
                "description": "In your Command phase, select one enemy unit within 12\" of this model. That unit must take a Battle-shock test"
            },
            {
                "name": "Psychological Saboteur (Aura)",
                "description": "While an enemy unit is with 12\" of this model, if that unit is Battle-shocked:\n\n- Each time a model in that unit makes an attack, subtract 1 from the Hit roll\n- Each time a friendly TYRANIDS model makes an attack that targets that unit, add 1 to the Wound roll."
            }
        ]
    },
    "Tyranid Norn Assimilator": {
        "stats": {
            "stat_movement": "10\"",
            "stat_toughness": 11,
            "stat_save": "2+",
            "stat_wounds": 16,
            "stat_leadership": "7+",
            "stat_oc": 5,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Monstrous scything talons",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "6",
                "skill": "2+",
                "strength": "9",
                "ap": "-2",
                "damage": "3",
                "keywords": "-"
            },
            {
                "name": "Toxinjecter Harpoon",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "2+",
                "strength": "12",
                "ap": "-3",
                "damage": "D6+1",
                "keywords": "Extra Attacks"
            },
            {
                "name": "Toxinjecter Harpoon",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "2",
                "skill": "2+",
                "strength": "12",
                "ap": "-3",
                "damage": "D6+1",
                "keywords": "Harpooned"
            }
        ],
        "abilities": [
            {
                "name": "Harpoon Barbs",
                "description": "Once per turn, when an enemy unit within Engagement Range of this unit is chosen to Fall Back, roll one D6; on a 2+, that unit suffers D6 mortal wounds."
            },
            {
                "name": "Damaged: 1-5 Wounds Remaining",
                "description": "While this model has 1-5 wounds remaining, each time this model makes an attack, subtract 1 from the Hit roll."
            },
            {
                "name": "Singular Purpose",
                "description": "At the start of the first battle round, select one of the following:\n- Select one enemy unit. Until the end of the battle, each time this model makes an attack that targets that unit you can re-roll the Hit roll and you can re-roll the Wound roll\n- Select one objective marker. Until the end of the battle, while this model is within range of that objective marker, it has the Feel No Pain 5+ ability and an Objective Control characteristic of 15."
            },
            {
                "name": "Protean Purpose",
                "description": "(Once per battle, per unit) In your Command phase, you can use this ability. If you do, this unit can make a selection for its Singular Purpose ability (this replaces the previous selection)."
            }
        ]
    },
    "Tyranid Norn Emissary": {
        "stats": {
            "stat_movement": "10\"",
            "stat_toughness": 11,
            "stat_save": "2+",
            "stat_wounds": 16,
            "stat_leadership": "7+",
            "stat_oc": 5,
            "stat_invuln": "4+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Monstrous rending claws",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "2+",
                "strength": "7",
                "ap": "-2",
                "damage": "2",
                "keywords": "Extra Attacks"
            },
            {
                "name": "Monstrous scything talons",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "6",
                "skill": "2+",
                "strength": "9",
                "ap": "-2",
                "damage": "3",
                "keywords": "-"
            },
            {
                "name": "\u27a4 Psychic tendril - neuroparasite",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "2",
                "skill": "2+",
                "strength": "8",
                "ap": "-2",
                "damage": "D3",
                "keywords": "Precision, Psychic"
            },
            {
                "name": "\u27a4 Psychic tendril - neurolance",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "2",
                "skill": "2+",
                "strength": "12",
                "ap": "-3",
                "damage": "D6",
                "keywords": "Melta 2, Psychic"
            },
            {
                "name": "\u27a4 Psychic tendril - neuroblast",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "2D6",
                "skill": "2+",
                "strength": "6",
                "ap": "-2",
                "damage": "1",
                "keywords": "Blast, Psychic"
            }
        ],
        "abilities": [
            {
                "name": "Singular Purpose",
                "description": "At the start of the first battle round, select one of the following:\n- Select one enemy unit. Until the end of the battle, each time this model makes an attack that targets that unit you can re-roll the Hit roll and you can re-roll the Wound roll\n- Select one objective marker. Until the end of the battle, while this model is within range of that objective marker, it has the Feel No Pain 5+ ability and an Objective Control characteristic of 15."
            },
            {
                "name": "Damaged: 1-5 Wounds Remaining",
                "description": "While this model has 1-5 wounds remaining, each time this model makes an attack, subtract 1 from the Hit roll."
            },
            {
                "name": "Protean Purpose",
                "description": "(Once per battle, per unit) In your Command phase, you can use this ability. If you do, this unit can make a selection for its Singular Purpose ability (this replaces the previous selection)."
            }
        ]
    },
    "Tyranid Old One Eye's Carnifex Brood": {
        "stats": {
            "stat_movement": "8\"",
            "stat_toughness": 9,
            "stat_save": "2+",
            "stat_wounds": 9,
            "stat_leadership": "8+",
            "stat_oc": 3,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "\u27a4 Old One Eye\u2019s claws and talons - Strike",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "6",
                "skill": "3+",
                "strength": "14",
                "ap": "-3",
                "damage": "D6+1",
                "keywords": "-"
            },
            {
                "name": "\u27a4 Old One Eye\u2019s claws and talons - Sweep",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "12",
                "skill": "3+",
                "strength": "6",
                "ap": "-1",
                "damage": "1",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Alpha Leader",
                "description": "While this model is leading a unit, each time a model in that unit makes an attack, you can re-roll the Hit roll."
            },
            {
                "name": "Unstoppable Monster",
                "description": "At the start of each player\u2019s Command phase, this model regains up to D3 lost wounds."
            },
            {
                "name": "Leader",
                "description": "This model can be attached to the following unit:\n- Carnifexes"
            }
        ]
    },
    "Tyranid Parasite of Mortrex": {
        "stats": {
            "stat_movement": "12\"",
            "stat_toughness": 5,
            "stat_save": "4+",
            "stat_wounds": 5,
            "stat_leadership": "8+",
            "stat_oc": 1,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Barbed ovipositor",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "1",
                "skill": "2+",
                "strength": "3",
                "ap": "-2",
                "damage": "3",
                "keywords": "Anti-infantry 3+, Extra Attacks"
            },
            {
                "name": "Clawed limbs",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "6",
                "skill": "2+",
                "strength": "5",
                "ap": "-1",
                "damage": "1",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Parasitic Infection",
                "description": "Each time an Infantry model is destroyed by an attack made with this model\u2019s barbed ovipositor, after this model has finished making its attacks, you can add one new Ripper Swarms unit to your army consisting of D3 models and set it up within 3\" of this model. If you do, that Ripper Swarms unit can be set up within Engagement Range of the destroyed model\u2019s unit (but not within Engagement Range of any other enemy units)."
            },
            {
                "name": "It Itches!",
                "description": "At the start of the Fight phase, select one enemy unit within Engagement Range of this model. That enemy unit must take a Battle-shock test."
            }
        ]
    },
    "Tyranid Prime with Lash Whip": {
        "stats": {
            "stat_movement": "10\"",
            "stat_toughness": 5,
            "stat_save": "3+",
            "stat_wounds": 6,
            "stat_leadership": "7+",
            "stat_oc": 1,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Rending claw",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "2+",
                "strength": "8",
                "ap": "-2",
                "damage": "3",
                "keywords": "-"
            },
            {
                "name": "Lash whip",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "8",
                "skill": "2+",
                "strength": "4",
                "ap": "-2",
                "damage": "1",
                "keywords": "Extra Attacks"
            },
            {
                "name": "Scything talons",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "6",
                "skill": "2+",
                "strength": "6",
                "ap": "-2",
                "damage": "2",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Alpha Warrior",
                "description": "Weapons equipped by models in this model\u2019s unit have the [SUSTAINED HITS 1] ability."
            },
            {
                "name": "Aggressive Leader-beast",
                "description": "In your opponent\u2019s Shooting phase, when an enemy unit has shot, if a model in this unit was destroyed by those attacks, this unit can make a surge move of up to D6\"."
            },
            {
                "name": "Leader",
                "description": "This model can be attached to the following unit:\n- Hormagaunts\n- Termagants\n- Tyranid Warriors with Melee Bio-weapons\n- Tyranid Warriors with Ranged Bio-weapons"
            }
        ]
    },
    "Tyranid Psychophage": {
        "stats": {
            "stat_movement": "12\"",
            "stat_toughness": 9,
            "stat_save": "3+",
            "stat_wounds": 10,
            "stat_leadership": "8+",
            "stat_oc": 3,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Talons and betentacled maw",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "6",
                "skill": "3+",
                "strength": "6",
                "ap": "-2",
                "damage": "2",
                "keywords": "Anti-Psyker 4+, Devastating Wounds"
            },
            {
                "name": "Psychoclastic torrent",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "D6",
                "skill": "N/A",
                "strength": "6",
                "ap": "-1",
                "damage": "1",
                "keywords": "Ignores Cover, Torrent"
            }
        ],
        "abilities": [
            {
                "name": "Bio-stimulus",
                "description": "In your Shooting phase, after this model has shot, select one enemy unit hit by one or more of those attacks. Until the end of the turn, each time a friendly TYRANIDS unit makes a melee attack that targets that enemy unit, improve the Armour Penetration characteristic of that attack by 1. The same enemy unit can only be affected by this ability once per turn."
            },
            {
                "name": "Feeding Frenzy",
                "description": "Each time this model makes a melee attack that targets a unit that is below its Starting Strength, add 1 to the Hit roll. If that target is also Below Half strength, add 1 to the Wound roll as well."
            }
        ]
    },
    "Tyranid Pyrovore": {
        "stats": {
            "stat_movement": "5\"",
            "stat_toughness": 6,
            "stat_save": "3+",
            "stat_wounds": 5,
            "stat_leadership": "8+",
            "stat_oc": 1,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Flamespurt",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "D6+1",
                "skill": "N/A",
                "strength": "6",
                "ap": "-1",
                "damage": "1",
                "keywords": "Ignores Cover, Torrent, Twin-linked"
            },
            {
                "name": "Chitin-barbed limbs",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "2",
                "skill": "4+",
                "strength": "5",
                "ap": "0",
                "damage": "1",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Burning Spray",
                "description": "In your Shooting phase, after this unit has shot, select one enemy unit hit by one or more of those attacks. Until the end of the phase, that enemy unit cannot have the Benefit of Cover."
            }
        ]
    },
    "Tyranid Raveners": {
        "stats": {
            "stat_movement": "10\"",
            "stat_toughness": 5,
            "stat_save": "4+",
            "stat_wounds": 3,
            "stat_leadership": "8+",
            "stat_oc": 1,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Ravener claws and talons",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "3",
                "skill": "3+",
                "strength": "5",
                "ap": "-2",
                "damage": "2",
                "keywords": "Twin-linked"
            }
        ],
        "abilities": [
            {
                "name": "Death From Below",
                "description": "At the end of your opponent\u2019s turn, if this unit is not within Engagement Range of one or more enemy units, you can remove it from the battlefield and place it into Strategic Reserves."
            }
        ]
    },
    "Tyranid Sporocyst and Mucolid Spore": {
        "stats": {
            "stat_movement": "-",
            "stat_toughness": 10,
            "stat_save": "3+",
            "stat_wounds": 10,
            "stat_leadership": "8+",
            "stat_oc": 0,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Flensing whips",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "6",
                "skill": "4+",
                "strength": "7",
                "ap": "-1",
                "damage": "2",
                "keywords": "-"
            },
            {
                "name": "Sporocyst bio-weapon",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "10",
                "skill": "4+",
                "strength": "5",
                "ap": "-1",
                "damage": "2",
                "keywords": "Hive Defences"
            }
        ],
        "abilities": [
            {
                "name": "Seed Mucolids",
                "description": "Once per turn, in your shooting phase, when selected to shoot, one unit with this ability can use it instead of making any attacks with it's ranged weapons. If it does, you can add one new MUCOLID SPORES containing 1 model to your army and set it up anywhere on the battlefield that is wholly within 18\" of this model and more than 8\" horizontally away from all enemy units."
            },
            {
                "name": "Hive Defences",
                "description": "You can target this model with the Fire Overwatch stratagem for 0CP, and can do so even if you have already targeted a different unit with that stratagem this turn. This model can only be targeted with that Stratagem once per turn"
            }
        ]
    },
    "Tyranid Termagants": {
        "stats": {
            "stat_movement": "6\"",
            "stat_toughness": 3,
            "stat_save": "5+",
            "stat_wounds": 1,
            "stat_leadership": "8+",
            "stat_oc": 2,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Chitinous claws and teeth",
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
                "name": "Fleshborer",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "1",
                "skill": "4+",
                "strength": "5",
                "ap": "0",
                "damage": "1",
                "keywords": "Assault"
            },
            {
                "name": "Termagant spinefist",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "2",
                "skill": "4+",
                "strength": "3",
                "ap": "0",
                "damage": "1",
                "keywords": "Assault, Pistol, Twin-linked"
            },
            {
                "name": "Termagant devourer",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "2",
                "skill": "4+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "Shardlauncher",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "D3",
                "skill": "4+",
                "strength": "5",
                "ap": "0",
                "damage": "1",
                "keywords": "Blast, Heavy"
            },
            {
                "name": "Spike rifle",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "1",
                "skill": "4+",
                "strength": "4",
                "ap": "-1",
                "damage": "1",
                "keywords": "Heavy"
            },
            {
                "name": "Strangleweb",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "D6",
                "skill": "N/A",
                "strength": "2",
                "ap": "0",
                "damage": "1",
                "keywords": "Assault, Devastating Wounds, Torrent"
            }
        ],
        "abilities": [
            {
                "name": "Skulking Horrors",
                "description": "In your opponent's Movement phase, if an enemy unit ends a move within 8\" of this unit, if this unit is not within Engagement Range of one or more enemy units, this unit can make a Normal move of up to D6\"."
            }
        ]
    },
    "Tyranid Tervigon": {
        "stats": {
            "stat_movement": "8\"",
            "stat_toughness": 11,
            "stat_save": "2+",
            "stat_wounds": 16,
            "stat_leadership": "7+",
            "stat_oc": 5,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Stinger salvoes",
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
                "name": "\u27a4 Massive scything talons - strike",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "3+",
                "strength": "9",
                "ap": "-2",
                "damage": "D6",
                "keywords": "-"
            },
            {
                "name": "\u27a4 Massive scything talons - sweep",
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
                "name": "Massive crushing claws",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "4+",
                "strength": "12",
                "ap": "-3",
                "damage": "D6+1",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Spawn Termagants",
                "description": "In your Command phase, you can select one friendly TERMAGANTS unit within 6\" of this model and return up to D3+3 destroyed TERMAGANT models to that unit. A TERMAGANTS unit cannot be selected for this ability more than once per phase."
            },
            {
                "name": "Brood Progenitor (Aura, Psychic)",
                "description": "While a friendly TERMAGANTS unit is within 6\" of this model, ranged weapons equipped by models in that unit have the [LETHAL HITS] ability."
            },
            {
                "name": "Damaged: 1-5 Wounds Remaining",
                "description": "While this model has 1-5 wounds remaining, each time this model makes an attack, subtract 1 from the Hit roll."
            }
        ]
    },
    "Tyranid The Swarmlord": {
        "stats": {
            "stat_movement": "8\"",
            "stat_toughness": 10,
            "stat_save": "2+",
            "stat_wounds": 10,
            "stat_leadership": "7+",
            "stat_oc": 3,
            "stat_invuln": "4+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Bone Sabres",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "8",
                "skill": "2+",
                "strength": "9",
                "ap": "-2",
                "damage": "3",
                "keywords": "Twin-linked"
            },
            {
                "name": "Synaptic Pulse",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "D6+3",
                "skill": "N/A",
                "strength": "5",
                "ap": "-1",
                "damage": "2",
                "keywords": "Psychic, Torrent"
            }
        ],
        "abilities": [
            {
                "name": "Hive Commander",
                "description": "At the start of your Command phase, if this model is on the battlefield, you gain 1CP"
            },
            {
                "name": "Malign Presence (Aura)",
                "description": "Once per turn, when your opponent targets a unit from their army within 12\" of this model with a stratagem, you can use this ability. If you do increase the CP cost of that use of that stratagem by 1CP."
            },
            {
                "name": "Domination of the Hive Mind (Aura)",
                "description": "While a friendly TYRANIDS unit is within 9\" of this model, that unit is within your army\u2019s Synapse Range."
            },
            {
                "name": "Leader",
                "description": "This model can be attached to the following unit:\n- Tyrant Guard"
            }
        ]
    },
    "Tyranid Toxicrene": {
        "stats": {
            "stat_movement": "8\"",
            "stat_toughness": 11,
            "stat_save": "3+",
            "stat_wounds": 14,
            "stat_leadership": "8+",
            "stat_oc": 4,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Massive toxic lashes",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "12",
                "skill": "3+",
                "strength": "6",
                "ap": "-1",
                "damage": "2",
                "keywords": "Anti-infantry 2+"
            },
            {
                "name": "Massive toxic lashes",
                "weapon_type": "ranged",
                "range": "9\"",
                "attacks": "2D6",
                "skill": "3+",
                "strength": "6",
                "ap": "-1",
                "damage": "2",
                "keywords": "Anti-infantry 2+"
            }
        ],
        "abilities": [
            {
                "name": "Grasping Tendrils",
                "description": "Each time an enemy unit (excluding Titanic units) within Engagement Range of one or more units from your army with this ability is selected to Fall Back, you can roll one D6: on a 3+, that enemy unit must Remain Stationary instead."
            },
            {
                "name": "Hypertoxic Miasma (Aura)",
                "description": "At the end of your Movement phase, roll one D6 for each enemy unit within 6\" of this model: on a 2-3, that unit suffers 1 mortal wound; on a 4-5, that unit suffers D3 mortal wounds; on a 6, that unit suffers D6 mortal wounds."
            },
            {
                "name": "Damaged: 1-5 Wounds Remaining",
                "description": "While this model has 1-5 wounds remaining, each time this model makes an attack, subtract 1 from the Hit roll."
            }
        ]
    },
    "Tyranid Trygon": {
        "stats": {
            "stat_movement": "10\"",
            "stat_toughness": 10,
            "stat_save": "3+",
            "stat_wounds": 14,
            "stat_leadership": "8+",
            "stat_oc": 4,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Trygon scything talons",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "12",
                "skill": "3+",
                "strength": "9",
                "ap": "-2",
                "damage": "3",
                "keywords": "-"
            },
            {
                "name": "Bio-electric pulse",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "6",
                "skill": "3+",
                "strength": "5",
                "ap": "0",
                "damage": "1",
                "keywords": "Sustained Hits 2"
            }
        ],
        "abilities": [
            {
                "name": "Subterranean Tunnels",
                "description": "In your Movement phase, when this model is set up on the battlefield using the Deep Strike ability, it can use a subterranean tunnel. If it does, this model can be set up anywhere on the battlefield that is more than 6\" horizontally away from all enemy units, but until the end of the turn, it is not eligible to declare a charge."
            },
            {
                "name": "Damaged: 1-5 Wounds Remaining",
                "description": "While this model has 1-5 wounds remaining, each time this model makes an attack, subtract 1 from the Hit roll."
            }
        ]
    },
    "Tyranid Tyrannocyte": {
        "stats": {
            "stat_movement": "8\"",
            "stat_toughness": 9,
            "stat_save": "3+",
            "stat_wounds": 10,
            "stat_leadership": "8+",
            "stat_oc": 2,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Flensing Whips",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "6",
                "skill": "4+",
                "strength": "7",
                "ap": "-1",
                "damage": "2",
                "keywords": "-"
            },
            {
                "name": "Tyrannocyte Bio-weapons",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "5",
                "skill": "4+",
                "strength": "5",
                "ap": "-1",
                "damage": "2",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Aerial Seeding",
                "description": "This model must start the battle in Reserves, but neither it nor any units embarked within it are counted towards any limits placed on the maximum number of Reserves units you can start the battle with. This model can be set up in the Reinforcements step of your first, second or third Movement phase, regardless of any mission rules. Any units embarked within this model must immediately disembark after it has been set up on the battlefield, and they must be set up more than 8\" away from all enemy models. After this model has been set up on the battlefield, no units can embark within it."
            }
        ]
    },
    "Tyranid Tyrannofex": {
        "stats": {
            "stat_movement": "9\"",
            "stat_toughness": 12,
            "stat_save": "2+",
            "stat_wounds": 16,
            "stat_leadership": "8+",
            "stat_oc": 5,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Powerful limbs",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "3+",
                "strength": "8",
                "ap": "0",
                "damage": "2",
                "keywords": "-"
            },
            {
                "name": "Stinger salvoes",
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
                "name": "Rupture cannon",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "2",
                "skill": "3+",
                "strength": "18",
                "ap": "-4",
                "damage": "D6+6",
                "keywords": "Heavy"
            },
            {
                "name": "Fleshborer hive",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "20",
                "skill": "3+",
                "strength": "5",
                "ap": "0",
                "damage": "1",
                "keywords": "Heavy, Sustained Hits 1, Twin-linked"
            },
            {
                "name": "Acid spray",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "D6+6",
                "skill": "N/A",
                "strength": "6",
                "ap": "-2",
                "damage": "2",
                "keywords": "Torrent"
            }
        ],
        "abilities": [
            {
                "name": "Resilient Organism",
                "description": "Once per battle, when an attack is allocated to this model, you can change the Damage characteristic of that attack to 0."
            },
            {
                "name": "Damaged: 1-5 Wounds Remaining",
                "description": "While this model has 1-5 wounds remaining, each time this model makes an attack, subtract 1 from the Hit roll."
            }
        ]
    },
    "Tyranid Tyrant Guard": {
        "stats": {
            "stat_movement": "6\"",
            "stat_toughness": 8,
            "stat_save": "3+",
            "stat_wounds": 4,
            "stat_leadership": "8+",
            "stat_oc": 1,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Scything talons and rending claws",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "5",
                "skill": "3+",
                "strength": "5",
                "ap": "-1",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "Bone cleaver, lash whip and rending claws",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "3",
                "skill": "3+",
                "strength": "5",
                "ap": "-1",
                "damage": "2",
                "keywords": "-"
            },
            {
                "name": "Crushing claws and rending claws",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "2",
                "skill": "4+",
                "strength": "8",
                "ap": "-2",
                "damage": "2",
                "keywords": "Twin-linked"
            }
        ],
        "abilities": [
            {
                "name": "Guardian Organism",
                "description": "While a CHARACTER model is leading this unit, that Character has the Feel No Pain 5+ ability"
            }
        ]
    },
    "Tyranid Venomthropes": {
        "stats": {
            "stat_movement": "6\"",
            "stat_toughness": 5,
            "stat_save": "4+",
            "stat_wounds": 3,
            "stat_leadership": "8+",
            "stat_oc": 1,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Toxic lashes",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "5",
                "skill": "3+",
                "strength": "3",
                "ap": "0",
                "damage": "1",
                "keywords": "Anti-Infantry 2+"
            }
        ],
        "abilities": [
            {
                "name": "Foul Spores (Aura)",
                "description": "Friendly TYRANIDS units within 6' of this unit have Stealth."
            }
        ]
    },
    "Tyranid Von Ryan's Leapers": {
        "stats": {
            "stat_movement": "10\"",
            "stat_toughness": 5,
            "stat_save": "4+",
            "stat_wounds": 3,
            "stat_leadership": "8+",
            "stat_oc": 1,
            "stat_invuln": "6+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Leaper's talons",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "6",
                "skill": "3+",
                "strength": "5",
                "ap": "-1",
                "damage": "1",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Pouncing Leap",
                "description": "You can target this unit with the Heroic Intervention stratagem, regardless of any other uses of that stratagem this phase. If you do:\n\u25aa That use is -1 CP.\n\u25aa That use does not prevent any uses of that stratagem on other units this phase."
            }
        ]
    },
    "Tyranid Warriors with Melee Bio-Weapons": {
        "stats": {
            "stat_movement": "6\"",
            "stat_toughness": 5,
            "stat_save": "4+",
            "stat_wounds": 3,
            "stat_leadership": "7+",
            "stat_oc": 2,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Tyranid Warrior claws and talons",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "6",
                "skill": "3+",
                "strength": "5",
                "ap": "-2",
                "damage": "1",
                "keywords": "Twin-linked"
            }
        ],
        "abilities": [
            {
                "name": "Adaptive Instincts (Once per turn, per unit)",
                "description": "In the Fight phase, when this unit is selected to fight or when an enemy unit targets this unit, you can select one of the following:\n\u25aa This unit\u2019s melee attacks have +1 S.\n\u25aa <ins>Or</ins>: This unit has +1 T."
            }
        ]
    },
    "Tyranid Warriors with Ranged Bio-Weapons": {
        "stats": {
            "stat_movement": "6\"",
            "stat_toughness": 5,
            "stat_save": "4+",
            "stat_wounds": 3,
            "stat_leadership": "7+",
            "stat_oc": 2,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Tyranid Warrior claws and talons",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "5",
                "skill": "3+",
                "strength": "5",
                "ap": "-1",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "Deathspitter",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "3",
                "skill": "4+",
                "strength": "5",
                "ap": "-1",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "Spinefists",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "2",
                "skill": "4+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Assault, Pistol, Twin-linked"
            },
            {
                "name": "Venom cannon",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "D3",
                "skill": "4+",
                "strength": "9",
                "ap": "-2",
                "damage": "2",
                "keywords": "Blast"
            },
            {
                "name": "Barbed strangler",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "D6+1",
                "skill": "4+",
                "strength": "6",
                "ap": "-1",
                "damage": "1",
                "keywords": "Blast"
            },
            {
                "name": "Devourer",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "5",
                "skill": "4+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Adaptable Predators",
                "description": "This unit is eligible to shoot and declare a charge in a turn in which it Fell Back."
            }
        ]
    },
    "Tyranid Winged Hive Tyrant": {
        "stats": {
            "stat_movement": "12\"",
            "stat_toughness": 9,
            "stat_save": "2+",
            "stat_wounds": 10,
            "stat_leadership": "7+",
            "stat_oc": 3,
            "stat_invuln": "4+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Tyrant talons",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "5",
                "skill": "2+",
                "strength": "7",
                "ap": "-2",
                "damage": "2",
                "keywords": "-"
            },
            {
                "name": "Monstrous scything talons",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "2+",
                "strength": "7",
                "ap": "-2",
                "damage": "2",
                "keywords": "Extra Attacks"
            },
            {
                "name": "Stranglethorn cannon",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "D6+1",
                "skill": "2+",
                "strength": "7",
                "ap": "-1",
                "damage": "2",
                "keywords": "Blast"
            },
            {
                "name": "Heavy venom cannon",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "D3",
                "skill": "2+",
                "strength": "9",
                "ap": "-2",
                "damage": "3",
                "keywords": "Blast"
            },
            {
                "name": "Monstrous bonesword and lash whip",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "6",
                "skill": "2+",
                "strength": "9",
                "ap": "-2",
                "damage": "3",
                "keywords": "Twin-linked"
            }
        ],
        "abilities": [
            {
                "name": "Paroxysm (Psychic)",
                "description": "At the start of the Fight phase, you can select one enemy unit within 12\" of and visible to this model and roll one D6: on a 1, this Psyker suffers D3 mortal wounds; on a 2+, until the end of the phase, subtract 1 from the Attacks characteristic of weapons equipped by models in that unit."
            },
            {
                "name": "Will of the Hive Mind",
                "description": "Once per battle round, one model from your army with this ability can use it when a friendly TYRANIDS unit within 12\" of that model is targeted with a Stratagem. If it does, reduce the CP cost of that use of that Stratagem by 1CP."
            }
        ]
    },
    "Tyranid Zoanthropes": {
        "stats": {
            "stat_movement": "5\"",
            "stat_toughness": 5,
            "stat_save": "5+",
            "stat_wounds": 3,
            "stat_leadership": "7+",
            "stat_oc": 1,
            "stat_invuln": "4+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Chitinous claws and teeth",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "2",
                "skill": "5+",
                "strength": "3",
                "ap": "0",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "\u27a4 Warp blast - witchfire",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "D3",
                "skill": "3+",
                "strength": "7",
                "ap": "-2",
                "damage": "D3",
                "keywords": "Blast, Psychic"
            },
            {
                "name": "\u27a4 Warp blast - focused witchfire",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "12",
                "ap": "-3",
                "damage": "D6+1",
                "keywords": "Lethal Hits, Psychic"
            }
        ],
        "abilities": [
            {
                "name": "Spirit Leech (Aura, Psychic)",
                "description": "While an enemy unit is within 6\" of this unit, if it contains a Neurothrope, each time that enemy unit fails a Battle-shock test, it suffers D3 mortal wounds and one model in this unit regains up to D3 lost wounds."
            },
            {
                "name": "Warp Field (Aura, Psychic)",
                "description": "While a friendly TYRANIDS unit is within 6\" of this unit, models in that unit have a 6+ invulnerable save."
            }
        ]
    },
    "Winged Tyranid Prime": {
        "stats": {
            "stat_movement": "12\"",
            "stat_toughness": 5,
            "stat_save": "4+",
            "stat_wounds": 6,
            "stat_leadership": "7+",
            "stat_oc": 1,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Prime talons",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "6",
                "skill": "2+",
                "strength": "6",
                "ap": "-1",
                "damage": "2",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Alpha Warrior",
                "description": "While this model is leading a unit, weapons equipped by models in that unit have the [SUSTAINED HITS 1] ability."
            },
            {
                "name": "Death Blow",
                "description": "If this model is destroyed by a melee attack, if it has not fought this phase, roll one D6: on a 4+, do not remove it from play. The destroyed model can fight after the attacking model\u2019s unit has finished making its attacks, and is then removed from play."
            },
            {
                "name": "Leader",
                "description": "This model can be attached to the following units:\n- Gargoyles\n- Tyranid Warriors With Melee Bio-Weapons\n- Tyranid Warriors With Ranged Bio-Weapons"
            }
        ]
    }
}


class Command(BaseCommand):
    """Refresh Tyranids stat lines, weapon profiles, and abilities from BSData."""

    help = 'Refresh 11th Edition stats/weapons/abilities for Tyranids units.'

    def add_arguments(self, parser):
        """Add --dry-run flag."""
        parser.add_argument(
            '--dry-run', action='store_true',
            help='Preview changes without writing to the database.',
        )

    def handle(self, *args, **options):
        """Iterate TYRANIDS_DATASHEETS and refresh each unit's datasheet data."""
        dry_run = options['dry_run']
        updated = 0
        skipped = 0

        with transaction.atomic():
            for name, payload in TYRANIDS_DATASHEETS.items():
                try:
                    unit = UnitType.objects.get(name=name, faction__name='Tyranids')
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
