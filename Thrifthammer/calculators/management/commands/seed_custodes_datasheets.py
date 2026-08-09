"""
Management command: seed_custodes_datasheets

Refreshes stat lines, weapon profiles, and abilities for all Adeptus
Custodes units using 11th Edition data sourced from BSData/wh40k-11e
("Imperium - Adeptus Custodes.json") -- the same source used by
seed_custodes_points.py.

Usage:
    python manage.py seed_custodes_datasheets
    python manage.py seed_custodes_datasheets --dry-run

Notes:
- Does NOT touch points_cost or category -- those are handled entirely by
  seed_custodes_points.py. This command only refreshes stat_* fields,
  WeaponProfile rows, and UnitAbility rows.
- Per-field safety rule: a unit's stats/weapons/abilities are only
  overwritten when BSData actually has that data for it. If extraction
  found nothing, the existing DB value/rows are left untouched.
- 'Shield-Captain (Legio Custodes)' resolves against the same BSData
  "Shield-Captain" entry as the plain 'Shield-Captain' row -- both are the
  same unit on different product releases, per user direction.
- All 27 active units resolved cleanly -- 0 missing stats/weapons/
  abilities, 0 overlong stat fields, 0 markdown artifacts.
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from calculators.models import UnitAbility, UnitType, WeaponProfile

# (name -> {stats?, weapons?, abilities?}). Missing keys mean "no data
# found for this field -- leave existing DB data untouched."
CUSTODES_DATASHEETS = {
    "Aleya": {
        "stats": {
            "stat_movement": "6\"",
            "stat_toughness": 3,
            "stat_save": "3+",
            "stat_wounds": 4,
            "stat_leadership": "6+",
            "stat_oc": 1,
            "stat_invuln": "5+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Somnus",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "2+",
                "strength": "6",
                "ap": "-3",
                "damage": "3",
                "keywords": "Anti-Psyker 5+, Devastating Wounds"
            }
        ],
        "abilities": [
            {
                "name": "Tactical Perception",
                "description": "While this model is leading a unit, models in that unit have the Fights First ability."
            },
            {
                "name": "Tenacious Spirit",
                "description": "While this model is leading a unit, each time a model in that unit makes an attack, add 1 to the Hit roll if that unit is below its Starting Strength, and add 1 to the Wound roll as well if that unit is Below Half-strength."
            },
            {
                "name": "Leader",
                "description": "This model can be attached to the following units:\n\u25a0 Prosecutors\n\u25a0 Vigilators\n\u25a0 Witchseekers"
            },
            {
                "name": "Daughter of the Abyss",
                "description": "This model has the Feel No Pain 3+ ability against Psychic Attacks and mortal wounds."
            },
            {
                "name": "Ceaseless Vigilance",
                "description": "In your Shooting phase, this unit can select one visible enemy unit within 12\". That enemy unit is nulled:\n- While a unit is nulled, that unit has +3\" detection range."
            }
        ]
    },
    "Allarus Custodians": {
        "stats": {
            "stat_movement": "5\"",
            "stat_toughness": 7,
            "stat_save": "2+",
            "stat_wounds": 4,
            "stat_leadership": "6+",
            "stat_oc": 2,
            "stat_invuln": "4+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Guardian Spear",
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
                "name": "Guardian Spear",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "2",
                "skill": "2+",
                "strength": "4",
                "ap": "-1",
                "damage": "2",
                "keywords": "Assault"
            },
            {
                "name": "Balistus grenade launcher",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "D6",
                "skill": "2+",
                "strength": "4",
                "ap": "-1",
                "damage": "1",
                "keywords": "Blast"
            },
            {
                "name": "Castellan axe",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "2+",
                "strength": "9",
                "ap": "-1",
                "damage": "3",
                "keywords": "-"
            },
            {
                "name": "Castellan axe",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "2",
                "skill": "2+",
                "strength": "4",
                "ap": "-1",
                "damage": "2",
                "keywords": "Assault"
            },
            {
                "name": "Misericordia",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "5",
                "skill": "2+",
                "strength": "5",
                "ap": "-2",
                "damage": "1",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Slayers of Tyrants",
                "description": "Each time a model in this unit makes an attack that targets a Character, Monster or Vehicle unit, you can re-roll the Wound roll."
            },
            {
                "name": "From Golden Light",
                "description": "Once per battle, at the end of your opponent's turn, if this unit is not within Engagement Range of one or more enemy units, you can remove it from the battlefield and place it into Strategic Reserves."
            },
            {
                "name": "Vexilla",
                "description": "Add 1 to the Objective Control characteristic of models in the bearer's unit."
            }
        ]
    },
    "Anathema Psykana Rhino": {
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
                "name": "Storm Bolter",
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
                "name": "Hunter-killer missile",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "1",
                "skill": "2+",
                "strength": "14",
                "ap": "-3",
                "damage": "D6",
                "keywords": "One Shot"
            }
        ],
        "abilities": [
            {
                "name": "Self Repair",
                "description": "At the start of your Command phase, this model regains 1 lost wound."
            },
            {
                "name": "Daughter of the Abyss",
                "description": "This model has the Feel No Pain 3+ ability against Psychic Attacks and mortal wounds."
            },
            {
                "name": "Ceaseless Vigilance",
                "description": "In your Shooting phase, this unit can select one visible enemy unit within 12\". That enemy unit is nulled:\n- While a unit is nulled, that unit has +3\" detection range."
            }
        ]
    },
    "Aquilon Custodians": {
        "stats": {
            "stat_movement": "5\"",
            "stat_toughness": 7,
            "stat_save": "2+",
            "stat_wounds": 4,
            "stat_leadership": "6+",
            "stat_oc": 2,
            "stat_invuln": "4+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Solerite power gauntlet",
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
                "name": "Lastrum storm bolter",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "2",
                "skill": "2+",
                "strength": "5",
                "ap": "-1",
                "damage": "1",
                "keywords": "Rapid Fire 2"
            },
            {
                "name": "Twin adrathic destructor",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "1",
                "skill": "2+",
                "strength": "6",
                "ap": "-2",
                "damage": "3",
                "keywords": "Twin-linked"
            },
            {
                "name": "Infernus firepike",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "D6",
                "skill": "N/A",
                "strength": "6",
                "ap": "-1",
                "damage": "1",
                "keywords": "Ignores Cover, Torrent"
            },
            {
                "name": "Solerite power talon",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "7",
                "skill": "2+",
                "strength": "7",
                "ap": "-2",
                "damage": "1",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Heavy Assault Infantry",
                "description": "Each time a model in this unit makes a ranged attack that targets the closest eligible target, re-roll a Wound roll of 1."
            },
            {
                "name": "From Golden Light",
                "description": "Once per battle, at the end of your opponent's turn, if this unit is not whithin Engagement Range of one or more enemy units, you can remove it from the battlefield. In the Reinforcements step of your next Movement phase, set it up anywhere on the battlefield that is more than 9\" horizontally away from all enemy models."
            }
        ]
    },
    "Ares Gunship": {
        "stats": {
            "stat_movement": "20+\"",
            "stat_toughness": 12,
            "stat_save": "2+",
            "stat_wounds": 22,
            "stat_leadership": "6+",
            "stat_oc": 0,
            "stat_invuln": "5+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Arachnus heavy blaze cannon",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "4",
                "skill": "2+",
                "strength": "12",
                "ap": "-3",
                "damage": "D6+1",
                "keywords": "-"
            },
            {
                "name": "Arachnus magna-blaze cannon",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "3",
                "skill": "2+",
                "strength": "18",
                "ap": "-4",
                "damage": "D6+6",
                "keywords": "-"
            },
            {
                "name": "Armoured hull",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "9",
                "skill": "4+",
                "strength": "9",
                "ap": "0",
                "damage": "1",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Infernus Firebomb",
                "description": "At the end of your Movement phase, select one visible enemy unit (excluding AIRCRAFT/Lone Operative units) within 24\" of this unit:\n- That enemy unit cannot have the benefit of cover until the end of your next Shooting phase.\n- Roll one D6 for each model in that enemy unit: for each 6, that enemy unit suffers 1 mortal wound."
            },
            {
                "name": "Damaged: 1-7 wounds remaining",
                "description": "While this model has 1-7 wounds remaining, each time this model makes an attack, subtract 1 from the Hit roll."
            }
        ]
    },
    "Blade Champion": {
        "stats": {
            "stat_movement": "6\"",
            "stat_toughness": 6,
            "stat_save": "2+",
            "stat_wounds": 6,
            "stat_leadership": "6+",
            "stat_oc": 2,
            "stat_invuln": "4+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "\u27a4 Vaultswords - Behemor",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "6",
                "skill": "2+",
                "strength": "7",
                "ap": "-2",
                "damage": "2",
                "keywords": "Precision"
            },
            {
                "name": "\u27a4 Vaultswords - Hurricanis",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "9",
                "skill": "2+",
                "strength": "5",
                "ap": "-1",
                "damage": "1",
                "keywords": "Sustained Hits 1"
            },
            {
                "name": "\u27a4 Vaultswords - Victus",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "5",
                "skill": "2+",
                "strength": "6",
                "ap": "-3",
                "damage": "3",
                "keywords": "Devastating Wounds"
            }
        ],
        "abilities": [
            {
                "name": "Leader",
                "description": "This model can be attached to the following units:\n\u25a0 Custodian Guard\n\u25a0 Custodian Wardens"
            },
            {
                "name": "Martial Inspiration",
                "description": "Once per battle, in your Charge phase, this model's unit is eligible to declare a charge in a turn in which it Advanced."
            },
            {
                "name": "Swift Onslaught",
                "description": "While this model is leading a unit, you can re-roll Charge rolls made for that unit."
            }
        ]
    },
    "Caladius Grav-tank": {
        "stats": {
            "stat_movement": "10\"",
            "stat_toughness": 11,
            "stat_save": "2+",
            "stat_wounds": 14,
            "stat_leadership": "6+",
            "stat_oc": 4,
            "stat_invuln": "5+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Armoured hull",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "4+",
                "strength": "6",
                "ap": "0",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "Twin lastrum bolt cannon",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "3",
                "skill": "2+",
                "strength": "6",
                "ap": "-1",
                "damage": "1",
                "keywords": "Sustained Hits 1"
            },
            {
                "name": "Twin iliastus accelerator cannon",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "4",
                "skill": "2+",
                "strength": "10",
                "ap": "-1",
                "damage": "3",
                "keywords": "Rapid Fire 4, Twin-linked"
            },
            {
                "name": "Twin arachnus heavy blaze cannon",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "4",
                "skill": "2+",
                "strength": "12",
                "ap": "-3",
                "damage": "D6+2",
                "keywords": "Twin-linked"
            }
        ],
        "abilities": [
            {
                "name": "Advanced Firepower",
                "description": "Each time this model makes an attack with its Twin iliastus accelerator cannon that targets an enemy unit (excluding MONSTERS and VEHICLES), that attack has the [LETHAL HITS] ability. Each time this model makes an attack with its Twin arachnus heavy blaze cannon that targets an enemy MONSTER or VEHICLE unit, that attack has the [LETHAL HITS] ability."
            },
            {
                "name": "Damaged: 1-5 wounds remaining",
                "description": "While this model has 1-5 wounds remaining, each time this model makes an attack, subtract 1 from the Hit roll."
            }
        ]
    },
    "Contemptor-Achillus Dreadnought": {
        "stats": {
            "stat_movement": "6\"",
            "stat_toughness": 9,
            "stat_save": "2+",
            "stat_wounds": 10,
            "stat_leadership": "6+",
            "stat_oc": 3,
            "stat_invuln": "5+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Achillus dreadspear",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "1",
                "skill": "2+",
                "strength": "9",
                "ap": "-2",
                "damage": "3",
                "keywords": "-"
            },
            {
                "name": "Achillus dreadspear",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "5",
                "skill": "2+",
                "strength": "12",
                "ap": "-2",
                "damage": "D6+1",
                "keywords": "Lance"
            },
            {
                "name": "Infernus incinerator",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "D6",
                "skill": "N/A",
                "strength": "6",
                "ap": "-1",
                "damage": "1",
                "keywords": "Ignores Cover, Torrent"
            },
            {
                "name": "Lastrum storm bolter",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "2",
                "skill": "2+",
                "strength": "5",
                "ap": "-1",
                "damage": "1",
                "keywords": "Rapid Fire 2"
            },
            {
                "name": "Twin adrathic destructor",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "1",
                "skill": "2+",
                "strength": "6",
                "ap": "-2",
                "damage": "3",
                "keywords": "Twin-linked"
            }
        ],
        "abilities": [
            {
                "name": "Dread Foe",
                "description": "Each time this model is selected to fight, you can select one enemy unit within Engagement Range of it and roll one D6, adding 2 to the result if this model made a Charge move this turn: on 4-5, that enemy unit suffers D3 mortal wounds; on a 6+, that enemy unit suffers 3 mortal wounds."
            }
        ]
    },
    "Contemptor-Galatus Dreadnought": {
        "stats": {
            "stat_movement": "6\"",
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
                "name": "Galatus warblade",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "D6",
                "skill": "N/A",
                "strength": "6",
                "ap": "-1",
                "damage": "1",
                "keywords": "Ignores Cover, Torrent, Twin-linked"
            },
            {
                "name": "Galatus warblade",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "8",
                "skill": "2+",
                "strength": "8",
                "ap": "-2",
                "damage": "3",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Galatus Shield",
                "description": "Each time a melee attack targets this model subtract 1 from the Wound roll."
            }
        ]
    },
    "Coronus Grav-carrier": {
        "stats": {
            "stat_movement": "12\"",
            "stat_toughness": 12,
            "stat_save": "2+",
            "stat_wounds": 16,
            "stat_leadership": "6+",
            "stat_oc": 5,
            "stat_invuln": "5+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Armoured hull",
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
                "name": "Twin arachnus blaze cannon",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "8",
                "skill": "2+",
                "strength": "5",
                "ap": "-1",
                "damage": "1",
                "keywords": "Devastating Wounds, Twin-linked"
            },
            {
                "name": "Twin lastrum bolt cannon",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "3",
                "skill": "2+",
                "strength": "6",
                "ap": "-1",
                "damage": "1",
                "keywords": "Sustained Hits 1"
            }
        ],
        "abilities": [
            {
                "name": "Fire Support",
                "description": "In your Shooting phase, after this model has shot, select one enemy unit hit by one or more of those attacks. Until the end of the phase, each time a friendly model that disembarked from this Transport this turn makes an attack that targets that enemy unit, you can re-roll the Wound roll."
            },
            {
                "name": "Damaged: 1-5 wounds remaining",
                "description": "While this model has 1-5 wounds remaining, each time this model makes an attack, subtract 1 from the Hit roll."
            }
        ]
    },
    "Custodian Guard": {
        "stats": {
            "stat_movement": "6\"",
            "stat_toughness": 6,
            "stat_save": "2+",
            "stat_wounds": 3,
            "stat_leadership": "6+",
            "stat_oc": 2,
            "stat_invuln": "4+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Guardian Spear",
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
                "name": "Guardian Spear",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "2",
                "skill": "2+",
                "strength": "4",
                "ap": "-1",
                "damage": "2",
                "keywords": "Assault"
            },
            {
                "name": "Sentinel Blade",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "5",
                "skill": "2+",
                "strength": "6",
                "ap": "-2",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "Sentinel Blade",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "2",
                "skill": "2+",
                "strength": "4",
                "ap": "-1",
                "damage": "2",
                "keywords": "Assault, Pistol"
            },
            {
                "name": "Misericordia",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "5",
                "skill": "2+",
                "strength": "5",
                "ap": "-2",
                "damage": "1",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Stand Vigil",
                "description": "Each time a model in this unit makes an attack, re-roll a Wound roll of 1. While this unit is within range of an objective marker you control, you can re-roll the Wound roll instead."
            },
            {
                "name": "Sentinel Storm",
                "description": "Once per battle, in your Shooting phase, after the unit has shot, it can shoot again."
            },
            {
                "name": "Praesidium Shield",
                "description": "Add 1 to the bearer's Wounds characteristic."
            },
            {
                "name": "Vexilla",
                "description": "Add 1 to the Objective Control characteristic of models in the bearer's unit."
            }
        ]
    },
    "Custodian Guard with Adrasite and Pyrithite spears": {
        "stats": {
            "stat_movement": "6\"",
            "stat_toughness": 6,
            "stat_save": "2+",
            "stat_wounds": 3,
            "stat_leadership": "6+",
            "stat_oc": 2,
            "stat_invuln": "4+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Adrasite spear",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "1",
                "skill": "2+",
                "strength": "5",
                "ap": "-2",
                "damage": "3",
                "keywords": "-"
            },
            {
                "name": "Adrasite spear",
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
                "name": "Pyrithite spear",
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
                "name": "Pyrithite spear",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "1",
                "skill": "2+",
                "strength": "9",
                "ap": "-4",
                "damage": "D6",
                "keywords": "Melta 2"
            }
        ],
        "abilities": [
            {
                "name": "Stand Vigil",
                "description": "Each time a model in this unit makes an attack, re-roll a Wound roll of 1. While this unit is within range of an objective marker you control, you can re-roll the Wound roll instead."
            },
            {
                "name": "No Foe Shall Stand",
                "description": "Once per battle, at the start of your Shooting phase, this unit can use this ability. If it does, until the end of the phase, ranged weapons equipped by models in this unit have the [LETHAL HITS] and [IGNORES COVER abilities]."
            }
        ]
    },
    "Custodian Wardens": {
        "stats": {
            "stat_movement": "6\"",
            "stat_toughness": 6,
            "stat_save": "2+",
            "stat_wounds": 3,
            "stat_leadership": "6+",
            "stat_oc": 2,
            "stat_invuln": "4+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Guardian Spear",
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
                "name": "Guardian Spear",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "2",
                "skill": "2+",
                "strength": "4",
                "ap": "-1",
                "damage": "2",
                "keywords": "Assault"
            },
            {
                "name": "Castellan axe",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "2+",
                "strength": "9",
                "ap": "-1",
                "damage": "3",
                "keywords": "-"
            },
            {
                "name": "Castellan axe",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "2",
                "skill": "2+",
                "strength": "4",
                "ap": "-1",
                "damage": "2",
                "keywords": "Assault"
            }
        ],
        "abilities": [
            {
                "name": "Resolute Will",
                "description": "While a CHARACTER is leading this unit, each time an attack targets this unit, if the Strength characteristic of that attack is greater than the Toughness characteristic of this unit, subtract 1 from the Wound roll."
            },
            {
                "name": "Living Fortress",
                "description": "Once per battle, at the start of any phase, this unit can use this ability. If it does, until the end of the phase, models in this unit have the Feel No Pain 4+ ability."
            },
            {
                "name": "Vexilla",
                "description": "Add 1 to the Objective Control characteristic of models in the bearer\u2019s unit."
            }
        ]
    },
    "Orion Assault Dropship": {
        "stats": {
            "stat_movement": "20+\"",
            "stat_toughness": 12,
            "stat_save": "2+",
            "stat_wounds": 22,
            "stat_leadership": "6+",
            "stat_oc": 0,
            "stat_invuln": "5+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Arachnus heavy blaze cannon",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "4",
                "skill": "2+",
                "strength": "12",
                "ap": "-3",
                "damage": "D6+1",
                "keywords": "-"
            },
            {
                "name": "Armoured hull",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "9",
                "skill": "4+",
                "strength": "9",
                "ap": "0",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "Spiculus heavy bolt launcher",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "D6+6",
                "skill": "2+",
                "strength": "7",
                "ap": "-1",
                "damage": "2",
                "keywords": "Blast"
            },
            {
                "name": "Twin lastrum bolt cannon",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "3",
                "skill": "2+",
                "strength": "6",
                "ap": "-1",
                "damage": "1",
                "keywords": "Sustained Hits 1"
            }
        ],
        "abilities": [
            {
                "name": "Damaged: 1-7 wounds remaining",
                "description": "While this model has 1-7 wounds remaining, each time this model makes an attack, subtract 1 from the Hit roll."
            },
            {
                "name": "Assault Dropship",
                "description": "If a unit disembarks from this TRANSPORT before it moves, until the end of the turn, that unit is eligibile to charge in a turn in which it Advanced."
            }
        ]
    },
    "Pallas Grav-attack": {
        "stats": {
            "stat_movement": "12\"",
            "stat_toughness": 8,
            "stat_save": "2+",
            "stat_wounds": 9,
            "stat_leadership": "6+",
            "stat_oc": 2,
            "stat_invuln": "5+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Armoured hull",
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
                "name": "Twin arachnus blaze cannon",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "8",
                "skill": "2+",
                "strength": "5",
                "ap": "-1",
                "damage": "1",
                "keywords": "Devastating Wounds, Twin-linked"
            }
        ],
        "abilities": [
            {
                "name": "Merciless Hunter",
                "description": "In your Shooting phase, each time this model makes an attack that targets an enemy unit that is Below Half-strength, add 1 to the Wound roll."
            }
        ]
    },
    "Prosecutors": {
        "stats": {
            "stat_movement": "6\"",
            "stat_toughness": 3,
            "stat_save": "3+",
            "stat_wounds": 1,
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
                "attacks": "1",
                "skill": "3+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Rapid Fire 1"
            },
            {
                "name": "Close combat weapon",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "2",
                "skill": "3+",
                "strength": "3",
                "ap": "0",
                "damage": "1",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Purity of Execution",
                "description": "Each time a model in this unit makes a ranged attack that targets a Psyker unit, that attack has the [PRECISION] and [DEVASTATING WOUNDS] abilities."
            },
            {
                "name": "Daughter of the Abyss",
                "description": "This model has the Feel No Pain 3+ ability against Psychic Attacks and mortal wounds."
            },
            {
                "name": "Ceaseless Vigilance",
                "description": "In your Shooting phase, this unit can select one visible enemy unit within 12\". That enemy unit is nulled:\n- While a unit is nulled, that unit has +3\" detection range."
            }
        ]
    },
    "Shield-Captain": {
        "stats": {
            "stat_movement": "6\"",
            "stat_toughness": 6,
            "stat_save": "2+",
            "stat_wounds": 6,
            "stat_leadership": "6+",
            "stat_oc": 2,
            "stat_invuln": "4+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Guardian Spear",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "7",
                "skill": "2+",
                "strength": "7",
                "ap": "-2",
                "damage": "2",
                "keywords": "-"
            },
            {
                "name": "Guardian Spear",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "2",
                "skill": "2+",
                "strength": "4",
                "ap": "-1",
                "damage": "2",
                "keywords": "Assault"
            },
            {
                "name": "Castellan axe",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "6",
                "skill": "2+",
                "strength": "9",
                "ap": "-1",
                "damage": "3",
                "keywords": "-"
            },
            {
                "name": "Castellan axe",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "2",
                "skill": "2+",
                "strength": "4",
                "ap": "-1",
                "damage": "2",
                "keywords": "Assault"
            },
            {
                "name": "Sentinel Blade",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "7",
                "skill": "2+",
                "strength": "6",
                "ap": "-2",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "Sentinel Blade",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "2",
                "skill": "2+",
                "strength": "4",
                "ap": "-1",
                "damage": "2",
                "keywords": "Assault, Pistol"
            },
            {
                "name": "Pyrithite Spear",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "7",
                "skill": "2+",
                "strength": "7",
                "ap": "-2",
                "damage": "2",
                "keywords": "-"
            },
            {
                "name": "Pyrithite Spear",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "1",
                "skill": "2+",
                "strength": "9",
                "ap": "-4",
                "damage": "D6",
                "keywords": "Melta 2"
            }
        ],
        "abilities": [
            {
                "name": "Master of the Stances",
                "description": "Once per battle, when this model's unit is selected to fight, it can use this ability. If it does, until that fight is resolved, both Ka'tah Stances are active for that unit, instead of only one."
            },
            {
                "name": "Leader",
                "description": "This model can be attached to the following units:\n\u25a0 Custodian Guard\n\u25a0 Custodian Wardens"
            },
            {
                "name": "Strategic Mastery",
                "description": "Once per battle round, one unit from your army with this ability can use it when its unit is targeted with a Stratagem. If it does, reduce the CP cost of that use of that Stratagem by 1CP."
            },
            {
                "name": "Praesidium Shield",
                "description": "Add 1 to the bearer's Wounds characteristic."
            }
        ]
    },
    "Shield-Captain (Legio Custodes)": {
        "stats": {
            "stat_movement": "6\"",
            "stat_toughness": 6,
            "stat_save": "2+",
            "stat_wounds": 6,
            "stat_leadership": "6+",
            "stat_oc": 2,
            "stat_invuln": "4+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Guardian Spear",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "7",
                "skill": "2+",
                "strength": "7",
                "ap": "-2",
                "damage": "2",
                "keywords": "-"
            },
            {
                "name": "Guardian Spear",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "2",
                "skill": "2+",
                "strength": "4",
                "ap": "-1",
                "damage": "2",
                "keywords": "Assault"
            },
            {
                "name": "Castellan axe",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "6",
                "skill": "2+",
                "strength": "9",
                "ap": "-1",
                "damage": "3",
                "keywords": "-"
            },
            {
                "name": "Castellan axe",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "2",
                "skill": "2+",
                "strength": "4",
                "ap": "-1",
                "damage": "2",
                "keywords": "Assault"
            },
            {
                "name": "Sentinel Blade",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "7",
                "skill": "2+",
                "strength": "6",
                "ap": "-2",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "Sentinel Blade",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "2",
                "skill": "2+",
                "strength": "4",
                "ap": "-1",
                "damage": "2",
                "keywords": "Assault, Pistol"
            },
            {
                "name": "Pyrithite Spear",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "7",
                "skill": "2+",
                "strength": "7",
                "ap": "-2",
                "damage": "2",
                "keywords": "-"
            },
            {
                "name": "Pyrithite Spear",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "1",
                "skill": "2+",
                "strength": "9",
                "ap": "-4",
                "damage": "D6",
                "keywords": "Melta 2"
            }
        ],
        "abilities": [
            {
                "name": "Master of the Stances",
                "description": "Once per battle, when this model's unit is selected to fight, it can use this ability. If it does, until that fight is resolved, both Ka'tah Stances are active for that unit, instead of only one."
            },
            {
                "name": "Leader",
                "description": "This model can be attached to the following units:\n\u25a0 Custodian Guard\n\u25a0 Custodian Wardens"
            },
            {
                "name": "Strategic Mastery",
                "description": "Once per battle round, one unit from your army with this ability can use it when its unit is targeted with a Stratagem. If it does, reduce the CP cost of that use of that Stratagem by 1CP."
            },
            {
                "name": "Praesidium Shield",
                "description": "Add 1 to the bearer's Wounds characteristic."
            }
        ]
    },
    "Telemon Heavy Dreadnought": {
        "stats": {
            "stat_movement": "8\"",
            "stat_toughness": 10,
            "stat_save": "2+",
            "stat_wounds": 12,
            "stat_leadership": "6+",
            "stat_oc": 4,
            "stat_invuln": "4+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Armoured feet",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "5",
                "skill": "2+",
                "strength": "7",
                "ap": "0",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "Spiculus bolt launcher",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "D6+3",
                "skill": "2+",
                "strength": "5",
                "ap": "0",
                "damage": "1",
                "keywords": "Blast"
            },
            {
                "name": "Arachnus storm cannon",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "12",
                "skill": "2+",
                "strength": "6",
                "ap": "-1",
                "damage": "1",
                "keywords": "Devastating Wounds"
            },
            {
                "name": "Iliastus accelerator culverin",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "4",
                "skill": "2+",
                "strength": "9",
                "ap": "-1",
                "damage": "3",
                "keywords": "-"
            },
            {
                "name": "Telemon Caestus",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "5",
                "skill": "2+",
                "strength": "12",
                "ap": "-2",
                "damage": "3",
                "keywords": "-"
            },
            {
                "name": "Twin plasma projector",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "D3",
                "skill": "N/A",
                "strength": "7",
                "ap": "-2",
                "damage": "1",
                "keywords": "Torrent, Twin-linked"
            }
        ],
        "abilities": [
            {
                "name": "Guardian Eternal",
                "description": "Each time an attack is allocated to this model, subtract 1 from the Damage characteristic of that attack."
            },
            {
                "name": "Damaged: 1-4 wounds remaining",
                "description": "While this model has 1-4 wounds remaining, each time this model makes an attack, subtract 1 from the Hit roll."
            },
            {
                "name": "Devoted to Destruction",
                "description": "If this model is equipped with 2 Telemon caestus weapons in addition to its armoured feet weapon, add 2 to the Attacks characteristic of those Telemon caestus weapons."
            }
        ]
    },
    "Trajann Valoris": {
        "stats": {
            "stat_movement": "6\"",
            "stat_toughness": 6,
            "stat_save": "2+",
            "stat_wounds": 7,
            "stat_leadership": "5+",
            "stat_oc": 2,
            "stat_invuln": "4+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Watcher's Axe",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "6",
                "skill": "2+",
                "strength": "10",
                "ap": "-2",
                "damage": "3",
                "keywords": "-"
            },
            {
                "name": "Eagle's Scream",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "2",
                "skill": "2+",
                "strength": "5",
                "ap": "-2",
                "damage": "3",
                "keywords": "Assault"
            }
        ],
        "abilities": [
            {
                "name": "Feel No Pain",
                "description": "5+"
            },
            {
                "name": "Leader",
                "description": "This model can be attached to the following units:\n\u25a0 Custodian Guard\n\u25a0 Custodian Wardens"
            },
            {
                "name": "Captain-General",
                "description": "While this model is leading a unit, each time a model in that unit makes an attack, you can ignore any or all modifiers to that attack's Ballistic Skill or Weapon Skill characteristics and/or all modifiers to the Hit roll."
            },
            {
                "name": "Moment Shackle",
                "description": "Once per battle, at the start of the Fight phase, you can select one of the following to take effect until the end of the phase:\n\u25a0 This model's Watcher's Axe melee weapon has an Attacks characteristic of 12.\n\u25a0 This model has a 2+ invulnerable save."
            }
        ]
    },
    "Valerian": {
        "stats": {
            "stat_movement": "6\"",
            "stat_toughness": 6,
            "stat_save": "2+",
            "stat_wounds": 6,
            "stat_leadership": "6+",
            "stat_oc": 2,
            "stat_invuln": "4+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Gnosis",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "3",
                "skill": "2+",
                "strength": "4",
                "ap": "-1",
                "damage": "2",
                "keywords": "Assault"
            },
            {
                "name": "Gnosis",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "7",
                "skill": "2+",
                "strength": "8",
                "ap": "-3",
                "damage": "2",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Leader",
                "description": "This model can be attached to the following units:\n\u25a0 Custodian Guard\n\u25a0 Custodian Wardens"
            },
            {
                "name": "Golden Laurels",
                "description": "While this model is leading a unit, each time a melee attack targets that unit, worsen that Armour Penetration characteristic of that attack by 1."
            },
            {
                "name": "Hero of Lion's Gate",
                "description": "Once per battle, after making a Hit roll, Wound roll or saving throw for this model, you can change the result of that roll to an unmodified 6."
            }
        ]
    },
    "Venatari Custodians": {
        "stats": {
            "stat_movement": "10\"",
            "stat_toughness": 6,
            "stat_save": "2+",
            "stat_wounds": 3,
            "stat_leadership": "6+",
            "stat_oc": 2,
            "stat_invuln": "4+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Venatari lance",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "2",
                "skill": "2+",
                "strength": "4",
                "ap": "-1",
                "damage": "2",
                "keywords": "Assault"
            },
            {
                "name": "Venatari lance",
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
                "name": "Kinetic destroyer",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "2",
                "skill": "2+",
                "strength": "6",
                "ap": "-1",
                "damage": "1",
                "keywords": "Pistol, Sustained Hits 1"
            },
            {
                "name": "Tarsis buckler",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "5",
                "skill": "2+",
                "strength": "5",
                "ap": "-2",
                "damage": "1",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Strike from the Skies",
                "description": "This unit is eligible to shoot and declare a charge in a turn in which it Fell Back."
            },
            {
                "name": "Swooping Dive",
                "description": "Once per battle, you can target this unit with the Rapid Ingress Stratagem for 0 CP, and can do so even if you have already targeted a different unit with that Stratagem that phase."
            },
            {
                "name": "Tarsis Buckler",
                "description": "The bearer has a Wounds characteristic of 4."
            }
        ]
    },
    "Venerable Contemptor Dreadnought": {
        "stats": {
            "stat_movement": "6\"",
            "stat_toughness": 9,
            "stat_save": "2+",
            "stat_wounds": 10,
            "stat_leadership": "6+",
            "stat_oc": 3,
            "stat_invuln": "5+",
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
                "name": "Contemptor combat weapon",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "5",
                "skill": "2+",
                "strength": "12",
                "ap": "-2",
                "damage": "3",
                "keywords": "-"
            },
            {
                "name": "Multi-melta",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "2",
                "skill": "2+",
                "strength": "9",
                "ap": "-4",
                "damage": "D6",
                "keywords": "Melta 2"
            },
            {
                "name": "Kheres-pattern assault cannon",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "6",
                "skill": "2+",
                "strength": "7",
                "ap": "-1",
                "damage": "1",
                "keywords": "Devastating Wounds"
            }
        ],
        "abilities": [
            {
                "name": "Unyielding Ancient",
                "description": "The first time this model is destroyed, remove it from play without resolving its Deadly Demise ability. Then, at the end of the phase, roll one D6: on a 2+, set this model back up on the battlefield as close as possible to where it was destroyed and not within Engagement Range of any enemy units, with D6 wounds remaining."
            }
        ]
    },
    "Venerable Land Raider": {
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
                "name": "Godhammer lascannon",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "2",
                "skill": "2+",
                "strength": "12",
                "ap": "-3",
                "damage": "D6+1",
                "keywords": "-"
            },
            {
                "name": "Storm bolter",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "2",
                "skill": "2+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Rapid fire 2"
            },
            {
                "name": "Twin heavy bolter",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "3",
                "skill": "2+",
                "strength": "5",
                "ap": "-1",
                "damage": "2",
                "keywords": "Sustained Hits 1, Twin-linked"
            },
            {
                "name": "Hunter-killer missile",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "1",
                "skill": "2+",
                "strength": "14",
                "ap": "-3",
                "damage": "D6",
                "keywords": "One Shot"
            }
        ],
        "abilities": [
            {
                "name": "Assault Ramp",
                "description": "Each time a unit disembarks from this model after it has made a Normal move, that unit is still eligible to declare a charge this turn."
            },
            {
                "name": "Damaged: 1-5 Wounds remaining",
                "description": "While this model has 1-5 wounds remaining, each time this model makes an attack, subtract 1 from the Hit roll."
            }
        ]
    },
    "Vertus Praetors": {
        "stats": {
            "stat_movement": "12\"",
            "stat_toughness": 7,
            "stat_save": "2+",
            "stat_wounds": 5,
            "stat_leadership": "6+",
            "stat_oc": 2,
            "stat_invuln": "4+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Interceptor lance",
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
                "name": "Salvo launcher",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "1",
                "skill": "2+",
                "strength": "10",
                "ap": "-3",
                "damage": "D6+1",
                "keywords": "Twin-linked"
            },
            {
                "name": "Vertus hurricane bolter",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "3",
                "skill": "2+",
                "strength": "4",
                "ap": "-1",
                "damage": "2",
                "keywords": "Rapid Fire 3, Twin-linked"
            }
        ],
        "abilities": [
            {
                "name": "Turbo Boost",
                "description": "Each time this unit Advances, do not make an Advance roll. Instead, until the end of the phase, add 6\" to the Move characteristic of models in this unit."
            },
            {
                "name": "Quicksilver Execution",
                "description": "Once per battle, after this unit ends a normal or Advance move, you can select one enemy unit (excluding MONSTERS and VEHICLES) that it moved over during that move, then roll one D6 for each model in this unit; for each 2+, that enemy unit suffers 2 mortal wounds."
            }
        ]
    },
    "Vigilators": {
        "stats": {
            "stat_movement": "6\"",
            "stat_toughness": 3,
            "stat_save": "3+",
            "stat_wounds": 1,
            "stat_leadership": "6+",
            "stat_oc": 1,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Executioner greatblade",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "2",
                "skill": "3+",
                "strength": "5",
                "ap": "-2",
                "damage": "2",
                "keywords": "Anti-Psyker 5+, Devastating Wounds"
            }
        ],
        "abilities": [
            {
                "name": "Deft Parry",
                "description": "Each time a melee attack targets this unit, subtract 1 from the Hit roll."
            },
            {
                "name": "Daughter of the Abyss",
                "description": "This model has the Feel No Pain 3+ ability against Psychic Attacks and mortal wounds."
            },
            {
                "name": "Ceaseless Vigilance",
                "description": "In your Shooting phase, this unit can select one visible enemy unit within 12\". That enemy unit is nulled:\n- While a unit is nulled, that unit has +3\" detection range."
            }
        ]
    },
    "Witchseekers": {
        "stats": {
            "stat_movement": "6\"",
            "stat_toughness": 3,
            "stat_save": "3+",
            "stat_wounds": 1,
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
                "attacks": "2",
                "skill": "3+",
                "strength": "3",
                "ap": "0",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "Witchseeker flamer",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "D6",
                "skill": "N/A",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Ignores Cover, Torrent"
            }
        ],
        "abilities": [
            {
                "name": "Sanctified Flames",
                "description": "In your Shooting phase, after this unit has shot, select one enemy unit that was hit by one or more of those attacks. That unit must take a Battle-shock test."
            },
            {
                "name": "Daughter of the Abyss",
                "description": "This model has the Feel No Pain 3+ ability against Psychic Attacks and mortal wounds."
            },
            {
                "name": "Ceaseless Vigilance",
                "description": "In your Shooting phase, this unit can select one visible enemy unit within 12\". That enemy unit is nulled:\n- While a unit is nulled, that unit has +3\" detection range."
            }
        ]
    }
}


class Command(BaseCommand):
    """Refresh Custodes stat lines, weapon profiles, and abilities from BSData."""

    help = 'Refresh 11th Edition stats/weapons/abilities for Adeptus Custodes units.'

    def add_arguments(self, parser):
        """Add --dry-run flag."""
        parser.add_argument(
            '--dry-run', action='store_true',
            help='Preview changes without writing to the database.',
        )

    def handle(self, *args, **options):
        """Iterate CUSTODES_DATASHEETS and refresh each unit's datasheet data."""
        dry_run = options['dry_run']
        updated = 0
        skipped = 0

        with transaction.atomic():
            for name, payload in CUSTODES_DATASHEETS.items():
                try:
                    unit = UnitType.objects.get(name=name, faction__name='Custodes')
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
