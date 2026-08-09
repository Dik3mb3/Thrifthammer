"""
Management command: seed_imperial_knights_datasheets

Refreshes stat lines, weapon profiles, and abilities for Imperial Knights
units using 11th Edition data sourced from BSData/wh40k-11e
("Imperium - Imperial Knights - Library.json") -- the same source used
by seed_imperial_knights_points.py. Supersedes the older hand-authored
seed_imperial_knights_stats.py (7 units, 10th Edition) -- left in place,
not deleted.

Usage:
    python manage.py seed_imperial_knights_datasheets
    python manage.py seed_imperial_knights_datasheets --dry-run

Notes:
- Does NOT touch points_cost or category -- those are handled entirely by
  seed_imperial_knights_points.py. This command only refreshes stat_*
  fields, WeaponProfile rows, and UnitAbility rows.
- Covers all 20 active units including the 5 cross-faction shared-SKU
  rows (Acastus Knight Asterius/Porphyrion, Cerastus Knight Atrapos,
  Questoris Knight Magaera/Styrix) -- their datasheets are genuinely
  defined in the Imperial Knights Library file itself (the "Chaos"
  naming only affects which Product row their gw_sku happens to be
  tagged under in our own catalog, not the BSData source), so no
  cross-faction copy step is needed, unlike Drukhari's Harlequins rows.
- Per-field safety rule: a unit's stats/weapons/abilities are only
  overwritten when BSData actually has that data for it. If extraction
  found nothing, the existing DB value/rows are left untouched.
- All 20 active units resolved cleanly -- 0 missing stats/weapons/
  abilities, 0 overlong stat fields.
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from calculators.models import UnitAbility, UnitType, WeaponProfile

# (name -> {stats?, weapons?, abilities?}). Missing keys mean "no data
# found for this field -- leave existing DB data untouched."
IMPERIAL_KNIGHTS_DATASHEETS = {
    "Acastus Knight Asterius": {
        "stats": {
            "stat_movement": "8\"",
            "stat_toughness": 13,
            "stat_save": "2+",
            "stat_wounds": 30,
            "stat_leadership": "6+",
            "stat_oc": 10,
            "stat_invuln": "5+*",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Twin conversion beam cannon",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "3",
                "skill": "3+",
                "strength": "16",
                "ap": "-2",
                "damage": "6",
                "keywords": "Conversion, Twin-linked, Sustained Hits D3"
            },
            {
                "name": "Asterius volkite culverin",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "6",
                "skill": "3+",
                "strength": "6",
                "ap": "0",
                "damage": "2",
                "keywords": "Devastating Wounds"
            },
            {
                "name": "Karacnos mortar battery",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "D6+3",
                "skill": "3+",
                "strength": "6",
                "ap": "-1",
                "damage": "1",
                "keywords": "Anti-Infantry 2+, Blast, Ignores Cover, Indirect Fire"
            },
            {
                "name": "Titanic feet",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "6",
                "skill": "4+",
                "strength": "10",
                "ap": "-1",
                "damage": "2",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Sunderer of Fortresses",
                "description": "Each time this model makes an attack that targets a VEHICLE, improve the Strength and Damage characteristics of that attack by 1. If that attack targets a FORTIFICATION, improve the Strength and Damage characteristics of that attack by 2 instead."
            },
            {
                "name": "Damaged: 1-10 Wounds Remaining",
                "description": "While this model has 1-10 wounds remaining, subtract 5 from this model's Objective Control characteristic and each time this model makes an attack, subtract 1 from the Hit roll."
            }
        ]
    },
    "Acastus Knight Porphyrion": {
        "stats": {
            "stat_movement": "8\"",
            "stat_toughness": 13,
            "stat_save": "2+",
            "stat_wounds": 30,
            "stat_leadership": "6+",
            "stat_oc": 10,
            "stat_invuln": "5+*",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Twin magna lascannon",
                "weapon_type": "ranged",
                "range": "72\"",
                "attacks": "D6",
                "skill": "3+",
                "strength": "18",
                "ap": "-4",
                "damage": "D6+6",
                "keywords": "Blast, Twin-linked"
            },
            {
                "name": "Titanic feet",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "6",
                "skill": "4+",
                "strength": "10",
                "ap": "-1",
                "damage": "2",
                "keywords": "-"
            },
            {
                "name": "Acastus autocannon",
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
                "name": "Lascannon",
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
                "name": "Acastus ironstorm missile pod",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "D6+6",
                "skill": "3+",
                "strength": "5",
                "ap": "0",
                "damage": "1",
                "keywords": "Blast, Heavy, Indirect Fire"
            },
            {
                "name": "Helios defence missiles",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "3",
                "skill": "3+",
                "strength": "10",
                "ap": "-2",
                "damage": "D6",
                "keywords": "Anti-Fly 2+, Heavy"
            }
        ],
        "abilities": [
            {
                "name": "Damaged: 1-10 Wounds Remaining",
                "description": "While this model has 1-10 wounds remaining, subtract 5 from this model's Objective Control characteristic and each time this model makes an attack, subtract 1 from the Hit roll."
            }
        ]
    },
    "Armiger Helverin": {
        "stats": {
            "stat_movement": "12\"",
            "stat_toughness": 9,
            "stat_save": "3+",
            "stat_wounds": 14,
            "stat_leadership": "7+",
            "stat_oc": 6,
            "stat_invuln": "5+*",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Armiger autocannon",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "4",
                "skill": "3+",
                "strength": "9",
                "ap": "-1",
                "damage": "3",
                "keywords": "-"
            },
            {
                "name": "Armoured feet",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "3+",
                "strength": "6",
                "ap": "0",
                "damage": "1",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Suppression Protocols",
                "description": "In your Shooting phase, after this model has shot, select one enemy unit (excluding Monsters and Vehicles) hit by one or more of those attacks made with an Armiger autocannon. Until the start of your next turn, that enemy unit is suppressed. While that unit is suppressed, each time a model in that unit makes an attack, subtract 1 from the Hit roll."
            },
            {
                "name": "Damaged: 1-5 Wounds Remaining",
                "description": "While this model has 1-5 wounds remaining, subtract 3 from this model's Objective Control characteristic and each time this model makes an attack, subtract 1 from the Hit roll."
            }
        ]
    },
    "Armiger Warglaive": {
        "stats": {
            "stat_movement": "12\"",
            "stat_toughness": 9,
            "stat_save": "3+",
            "stat_wounds": 14,
            "stat_leadership": "7+",
            "stat_oc": 6,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "\u27a4 Reaper chain-cleaver - strike",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "3+",
                "strength": "10",
                "ap": "-3",
                "damage": "3",
                "keywords": "-"
            },
            {
                "name": "\u27a4 Reaper chain-cleaver - sweep",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "8",
                "skill": "3+",
                "strength": "8",
                "ap": "-2",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "Thermal spear",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "2",
                "skill": "3+",
                "strength": "12",
                "ap": "-4",
                "damage": "D6",
                "keywords": "Melta 4"
            }
        ],
        "abilities": [
            {
                "name": "Impetuous Glory",
                "description": "Each time this model makes a charge move, until the end of the turn, add 1 to the Attacks characteristic of this model's reaper chain-cleaver - strike profile, and add 2 to the Attacks characteristic of this model's reaper chain-cleaver - sweep profile."
            },
            {
                "name": "Damaged: 1-5 Wounds Remaining",
                "description": "While this model has 1-5 wounds remaining, subtract 3 from this model's Objective Control characteristic and each time this model makes an attack, subtract 1 from the Hit roll."
            }
        ]
    },
    "Canis Rex": {
        "stats": {
            "stat_movement": "10\"",
            "stat_toughness": 11,
            "stat_save": "3+",
            "stat_wounds": 26,
            "stat_leadership": "6+",
            "stat_oc": 10,
            "stat_invuln": "5+*",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "\u27a4 Las-impulsor - high intensity",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "D6",
                "skill": "2+",
                "strength": "14",
                "ap": "-3",
                "damage": "4",
                "keywords": "Blast, Sustained Hits 1"
            },
            {
                "name": "\u27a4 Las-impulsor - low intensity",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "2D6",
                "skill": "2+",
                "strength": "7",
                "ap": "-1",
                "damage": "2",
                "keywords": "Blast, Sustained Hits 1"
            },
            {
                "name": "\u27a4 Freedom's Hand - strike",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "5",
                "skill": "2+",
                "strength": "20",
                "ap": "-3",
                "damage": "9",
                "keywords": "Sustained Hits 1"
            },
            {
                "name": "\u27a4 Freedom's Hand - sweep",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "10",
                "skill": "2+",
                "strength": "10",
                "ap": "-2",
                "damage": "3",
                "keywords": "Sustained Hits 1"
            },
            {
                "name": "Questoris multi-laser",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "4",
                "skill": "2+",
                "strength": "6",
                "ap": "0",
                "damage": "1",
                "keywords": "Sustained Hits 1"
            },
            {
                "name": "Close combat weapon",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "2",
                "skill": "2+",
                "strength": "3",
                "ap": "0",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "Hekhtur's pistol",
                "weapon_type": "ranged",
                "range": "12\"",
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
                "name": "Chainbreaker",
                "description": "Once per battle, at the start of any phase, you can select one friendly Imperium unit that is Battle-shocked and within 12\" of this model. That unit is no longer Battle-shocked."
            },
            {
                "name": "Legendary Freeblade",
                "description": "Once per turn, you can target this model with a Stratagem for 0CP, and can do so even if you have already targeted a different unit with that Stratagem in the same phase."
            },
            {
                "name": "Damaged: 1-9 Wounds Remaining",
                "description": "While this model has 1-9 wounds remaining, subtract 5 from this model's Objective Control characteristic and each time this model makes an attack, subtract 1 from the Hit roll."
            },
            {
                "name": "Using Sir Hekhtur",
                "description": "If your Canis Rex model is destroyed, this model is treated as a model disembarking from a destroyed Transport and must perform an Emergency Disembarkation. Sir Hekhtur cannot be selected as the target of any of your Stratagems other than Core Stratagems. Your Canis Rex unit is not considered to be destroyed until Sir Hekhtur is also destroyed."
            }
        ]
    },
    "Cerastus Knight Acheron": {
        "stats": {
            "stat_movement": "12\"",
            "stat_toughness": 11,
            "stat_save": "3+",
            "stat_wounds": 28,
            "stat_leadership": "6+",
            "stat_oc": 10,
            "stat_invuln": "5+*",
            "stat_fnp": ""
        },
        "weapons": [
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
                "name": "Acheron flame cannon",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "2D6",
                "skill": "N/A",
                "strength": "8",
                "ap": "-1",
                "damage": "2",
                "keywords": "Torrent, Ignores Cover"
            },
            {
                "name": "\u27a4 Reaper chainfist - strike",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "3+",
                "strength": "14",
                "ap": "-4",
                "damage": "6",
                "keywords": "-"
            },
            {
                "name": "\u27a4 Reaper chainfist - sweep",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "12",
                "skill": "3+",
                "strength": "9",
                "ap": "-3",
                "damage": "2",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Searing Flames",
                "description": "In your Shooting phase, after this model has shot, select one enemy unit hit by one or more of those attacks made with an Acheron flame cannon. Until the end of the phase, that enemy unit cannot have the Benefit of Cover."
            },
            {
                "name": "Damaged: 1-10 Wounds Remaining",
                "description": "While this model has 1-10 wounds remaining, subtract 5 from this model's Objective Control characteristic and each time this model makes an attack, subtract 1 from the Hit roll."
            }
        ]
    },
    "Cerastus Knight Atrapos": {
        "stats": {
            "stat_movement": "12\"",
            "stat_toughness": 11,
            "stat_save": "3+",
            "stat_wounds": 28,
            "stat_leadership": "6+",
            "stat_oc": 10,
            "stat_invuln": "5+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "\u27a4 Atrapos lascutter - high intensity (melee)",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "6",
                "skill": "3+",
                "strength": "14",
                "ap": "-3",
                "damage": "4",
                "keywords": "Sustained Hits 1"
            },
            {
                "name": "\u27a4 Atrapos lascutter - low intensity (melee)",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "12",
                "skill": "3+",
                "strength": "7",
                "ap": "-1",
                "damage": "2",
                "keywords": "Sustained Hits 1"
            },
            {
                "name": "\u27a4 Atrapos lascutter - high intensity (ranged)",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "D6",
                "skill": "3+",
                "strength": "14",
                "ap": "-3",
                "damage": "4",
                "keywords": "Sustained Hits 1"
            },
            {
                "name": "\u27a4 Atrapos lascutter - low intensity (ranged)",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "2D6",
                "skill": "3+",
                "strength": "7",
                "ap": "-1",
                "damage": "2",
                "keywords": "Sustained Hits 1"
            },
            {
                "name": "\u27a4 Graviton singularity cannon - singularity",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "D3",
                "skill": "3+",
                "strength": "16",
                "ap": "-4",
                "damage": "D6+1",
                "keywords": "Blast, Devastating Wounds, Hazardous"
            },
            {
                "name": "\u27a4 Graviton singularity cannon - contained",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "D3",
                "skill": "3+",
                "strength": "16",
                "ap": "-4",
                "damage": "D6+1",
                "keywords": "Blast"
            }
        ],
        "abilities": [
            {
                "name": "Macro-extinction Protocols",
                "description": "Each time this model makes an attack that targets a MONSTER or VEHICLE unit, add 1 to the Hit roll. If that target is TITANIC or TOWERING, add 1 to the Wound roll as well."
            },
            {
                "name": "Damaged: 1-10 Wounds Remaining",
                "description": "While this model has 1-10 wounds remaining, subtract 5 from this model's Objective Control characteristic and each time this model makes an attack, subtract 1 from the Hit roll."
            }
        ]
    },
    "Cerastus Knight Castigator": {
        "stats": {
            "stat_movement": "12\"",
            "stat_toughness": 11,
            "stat_save": "3+",
            "stat_wounds": 28,
            "stat_leadership": "6+",
            "stat_oc": 10,
            "stat_invuln": "5+*",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Castigator bolt cannon",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "18",
                "skill": "3+",
                "strength": "6",
                "ap": "-2",
                "damage": "2",
                "keywords": "Twin-linked"
            },
            {
                "name": "\u27a4 Tempest warblade - strike",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "3+",
                "strength": "14",
                "ap": "-4",
                "damage": "6",
                "keywords": "-"
            },
            {
                "name": "\u27a4 Tempest warblade - sweep",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "12",
                "skill": "3+",
                "strength": "9",
                "ap": "-3",
                "damage": "2",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Storm of Bolts",
                "description": "In your Shooting phase, after this model has shot, select one unit (excluding MONSTERS and VEHICLES) hit by one or more of those attacks. Until the start of your next turn, while this model is on the battlefield, that enemy unit is suppressed. While a unit is suppressed, each time a model in that unit makes an attack, subtract 1 from the Hit roll."
            },
            {
                "name": "Damaged: 1-10 Wounds Remaining",
                "description": "While this model has 1-10 wounds remaining, subtract 5 from this model's Objective Control characteristic and each time this model makes an attack, subtract 1 from the Hit roll."
            }
        ]
    },
    "Cerastus Knight Lancer": {
        "stats": {
            "stat_movement": "14\"",
            "stat_toughness": 11,
            "stat_save": "3+",
            "stat_wounds": 28,
            "stat_leadership": "6+",
            "stat_oc": 10,
            "stat_invuln": "4+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "\u27a4 Cerastus shock lance - strike",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "5",
                "skill": "2+",
                "strength": "20",
                "ap": "-3",
                "damage": "8",
                "keywords": "Lance"
            },
            {
                "name": "Cerastus shock lance",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "6",
                "skill": "3+",
                "strength": "6",
                "ap": "0",
                "damage": "2",
                "keywords": "Assault, Sustained Hits 2"
            },
            {
                "name": "\u27a4 Cerastus shock lance - sweep",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "10",
                "skill": "2+",
                "strength": "10",
                "ap": "-2",
                "damage": "3",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Shock Charge",
                "description": "You can target this model with the Tank Shock Stratagem for 0CP, and can do so even if you have already targeted a different unit with that Stratagem this phase."
            },
            {
                "name": "Damaged: 1-10 Wounds Remaining",
                "description": "While this model has 1-10 wounds remaining, subtract 5 from this model's Objective Control characteristic and each time this model makes an attack, subtract 1 from the Hit roll."
            }
        ]
    },
    "Knight Castellan": {
        "stats": {
            "stat_movement": "8\"",
            "stat_toughness": 12,
            "stat_save": "3+",
            "stat_wounds": 28,
            "stat_leadership": "6+",
            "stat_oc": 10,
            "stat_invuln": "5+*",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "\u27a4 Plasma decimator - standard",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "D6+3",
                "skill": "3+",
                "strength": "8",
                "ap": "-3",
                "damage": "2",
                "keywords": "Blast"
            },
            {
                "name": "\u27a4 Plasma decimator - supercharge",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "D6+3",
                "skill": "3+",
                "strength": "9",
                "ap": "-4",
                "damage": "3",
                "keywords": "Blast, Hazardous"
            },
            {
                "name": "Volcano lance",
                "weapon_type": "ranged",
                "range": "72\"",
                "attacks": "D3",
                "skill": "3+",
                "strength": "18",
                "ap": "-5",
                "damage": "D6+8",
                "keywords": "Blast"
            },
            {
                "name": "Titanic feet",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "4+",
                "strength": "8",
                "ap": "-1",
                "damage": "2",
                "keywords": "-"
            },
            {
                "name": "Twin meltagun",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "9",
                "ap": "-4",
                "damage": "D6",
                "keywords": "Melta 2, Twin-Linked"
            }
        ],
        "abilities": [
            {
                "name": "Titan Hunter",
                "description": "Each time a ranged attack made by this model is allocated to a Monster or Vehicle model, you can re-roll the Damage roll."
            },
            {
                "name": "Damaged: 1-10 Wounds Remaining",
                "description": "While this model has 1-10 wounds remaining, subtract 5 from this model's Objective Control characteristic and each time this model makes an attack, subtract 1 from the Hit roll."
            },
            {
                "name": "Ion Aegis (Aura)",
                "description": "While a friendly Armiger model is within 6\" of this model, each time a ranged attack targets that model, it has the Benefit of Cover against that attack."
            }
        ]
    },
    "Knight Crusader": {
        "stats": {
            "stat_movement": "10\"",
            "stat_toughness": 11,
            "stat_save": "3+",
            "stat_wounds": 26,
            "stat_leadership": "6+",
            "stat_oc": 10,
            "stat_invuln": "5+*",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Avenger gatling cannon",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "18",
                "skill": "3+",
                "strength": "6",
                "ap": "-2",
                "damage": "2",
                "keywords": "-"
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
                "name": "Titanic feet",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "4+",
                "strength": "8",
                "ap": "-1",
                "damage": "2",
                "keywords": "-"
            },
            {
                "name": "Questoris heavy stubber",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "3",
                "skill": "3+",
                "strength": "4",
                "ap": "-1",
                "damage": "1",
                "keywords": "Rapid Fire 3"
            },
            {
                "name": "Rapid-fire battle cannon",
                "weapon_type": "ranged",
                "range": "72\"",
                "attacks": "D6+3",
                "skill": "3+",
                "strength": "10",
                "ap": "-1",
                "damage": "3",
                "keywords": "Blast, Rapid Fire D6+3"
            },
            {
                "name": "Thermal cannon",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "2D3",
                "skill": "3+",
                "strength": "12",
                "ap": "-4",
                "damage": "D6",
                "keywords": "Blast, Melta 6"
            }
        ],
        "abilities": [
            {
                "name": "Punishing Salvoes",
                "description": "In your Movement phase, if this model Remains Stationary, until the end of the turn, ranged weapons equipped by this model have the [SUSTAINED HITS 1] ability."
            },
            {
                "name": "Damaged: 1-9 Wounds Remaining",
                "description": "While this model has 1-9 wounds remaining, subtract 5 from this model's Objective Control characteristic and each time this model makes an attack, subtract 1 from the Hit roll."
            }
        ]
    },
    "Knight Defender": {
        "stats": {
            "stat_movement": "10\"",
            "stat_toughness": 11,
            "stat_save": "3+",
            "stat_wounds": 26,
            "stat_leadership": "6+",
            "stat_oc": 10,
            "stat_invuln": "4+*",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Twin incendine combustor",
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
                "name": "Conversion beam obliterator",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "3",
                "skill": "3+",
                "strength": "12",
                "ap": "-2",
                "damage": "4",
                "keywords": "Conversion, Sustained Hits D3"
            },
            {
                "name": "\u27a4 Plasma executor - standard",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "D6+3",
                "skill": "3+",
                "strength": "8",
                "ap": "-2",
                "damage": "2",
                "keywords": "Blast"
            },
            {
                "name": "\u27a4 Plasma executor - supercharge",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "D6+3",
                "skill": "3+",
                "strength": "9",
                "ap": "-3",
                "damage": "3",
                "keywords": "Blast, Hazardous"
            },
            {
                "name": "Phosphor blaster",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "5",
                "ap": "0",
                "damage": "1",
                "keywords": "Ignores Cover, Rapid Fire 1"
            },
            {
                "name": "Titanic feet",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "4+",
                "strength": "8",
                "ap": "-1",
                "damage": "2",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Selfless Protector",
                "description": "Each time a ranged attack is allocated to an Imperial Knights model from your army, if that model is not fully visible to every model in the attacking unit because of this Knight Defender model, that model has the Benefit of Cover and a 4+ invulnerable save against that attack."
            },
            {
                "name": "Damaged: 1-9 Wounds Remaining",
                "description": "While this model has 1-9 wounds remaining, subtract 5 from this model's Objective Control characteristic and each time this model makes an attack, subtract 1 from the Hit roll."
            }
        ]
    },
    "Knight Errant": {
        "stats": {
            "stat_movement": "10\"",
            "stat_toughness": 11,
            "stat_save": "3+",
            "stat_wounds": 26,
            "stat_leadership": "6+",
            "stat_oc": 10,
            "stat_invuln": "5+*",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Thermal cannon",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "2D3",
                "skill": "3+",
                "strength": "12",
                "ap": "-4",
                "damage": "D6",
                "keywords": "Blast, Melta 6"
            }
        ],
        "abilities": [
            {
                "name": "Aggressive Assault",
                "description": "Each time this model makes a ranged attack that targets the closest eligible target, add 1 to the Hit roll."
            },
            {
                "name": "Damaged: 1-9 Wounds Remaining",
                "description": "While this model has 1-9 wounds remaining, subtract 5 from this model's Objective Control characteristic and each time this model makes an attack, subtract 1 from the Hit roll."
            }
        ]
    },
    "Knight Gallant": {
        "stats": {
            "stat_movement": "12\"",
            "stat_toughness": 11,
            "stat_save": "3+",
            "stat_wounds": 26,
            "stat_leadership": "6+",
            "stat_oc": 10,
            "stat_invuln": "5+*",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "\u27a4 Reaper chainsword - sweep",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "18",
                "skill": "2+",
                "strength": "9",
                "ap": "-3",
                "damage": "2",
                "keywords": "Lethal Hits"
            },
            {
                "name": "\u27a4 Reaper chainsword - strike",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "6",
                "skill": "2+",
                "strength": "14",
                "ap": "-4",
                "damage": "6",
                "keywords": "Devastating Wounds"
            },
            {
                "name": "\u27a4 Thunderstrike gauntlet - strike",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "6",
                "skill": "2+",
                "strength": "20",
                "ap": "-3",
                "damage": "8",
                "keywords": "Devastating Wounds"
            },
            {
                "name": "\u27a4 Thunderstrike gauntlet - sweep",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "12",
                "skill": "2+",
                "strength": "10",
                "ap": "-2",
                "damage": "3",
                "keywords": "Lethal Hits"
            }
        ],
        "abilities": [
            {
                "name": "Martial Pride",
                "description": "Each time this unit Consolidates, models in it can move an additional 3\" provided your unit can end that move within Engagement Range of one or more enemy units."
            },
            {
                "name": "Damaged: 1-9 Wounds Remaining",
                "description": "While this model has 1-9 wounds remaining, subtract 5 from this model's Objective Control characteristic and each time this model makes an attack, subtract 1 from the Hit roll."
            }
        ]
    },
    "Knight Paladin": {
        "stats": {
            "stat_movement": "10\"",
            "stat_toughness": 11,
            "stat_save": "3+",
            "stat_wounds": 26,
            "stat_leadership": "6+",
            "stat_oc": 10,
            "stat_invuln": "5+*",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Questoris heavy stubber",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "3",
                "skill": "3+",
                "strength": "4",
                "ap": "-1",
                "damage": "1",
                "keywords": "Rapid Fire 3"
            },
            {
                "name": "Rapid-fire battle cannon",
                "weapon_type": "ranged",
                "range": "72\"",
                "attacks": "D6+3",
                "skill": "3+",
                "strength": "10",
                "ap": "-1",
                "damage": "3",
                "keywords": "Blast, Rapid Fire D6+3"
            }
        ],
        "abilities": [
            {
                "name": "Seasoned Noble",
                "description": "Each time this model makes a ranged attack that targets the closest eligible target, improve the Armour Penetration characteristic of that attack by 1."
            },
            {
                "name": "Damaged: 1-9 Wounds Remaining",
                "description": "While this model has 1-9 wounds remaining, subtract 5 from this model's Objective Control characteristic and each time this model makes an attack, subtract 1 from the Hit roll."
            }
        ]
    },
    "Knight Preceptor": {
        "stats": {
            "stat_movement": "10\"",
            "stat_toughness": 11,
            "stat_save": "3+",
            "stat_wounds": 26,
            "stat_leadership": "6+",
            "stat_oc": 10,
            "stat_invuln": "5+*",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "\u27a4 Las-impulsor - high intensity",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "D6",
                "skill": "3+",
                "strength": "14",
                "ap": "-3",
                "damage": "4",
                "keywords": "Blast"
            },
            {
                "name": "\u27a4 Las-impulsor - low intensity",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "2D6",
                "skill": "3+",
                "strength": "7",
                "ap": "-1",
                "damage": "2",
                "keywords": "Blast"
            },
            {
                "name": "Preceptor multi-laser",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "4",
                "skill": "3+",
                "strength": "6",
                "ap": "0",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "Questoris heavy stubber",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "3",
                "skill": "3+",
                "strength": "4",
                "ap": "-1",
                "damage": "1",
                "keywords": "Rapid Fire 3"
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
                "name": "Exemplar of the Code",
                "description": "At the start of the battle, select one unit from your opponent\u2019s army to be this model's quarry. Each time this model makes an attack that targets its quarry, you can re-roll the Wound roll. Each time this model's quarry is destroyed, you can select a new unit from your opponent's army to be its quarry."
            },
            {
                "name": "Damaged: 1-9 Wounds Remaining",
                "description": "While this model has 1-9 wounds remaining, subtract 5 from this model's Objective Control characteristic and each time this model makes an attack, subtract 1 from the Hit roll."
            }
        ]
    },
    "Knight Valiant": {
        "stats": {
            "stat_movement": "8\"",
            "stat_toughness": 12,
            "stat_save": "3+",
            "stat_wounds": 28,
            "stat_leadership": "6+",
            "stat_oc": 10,
            "stat_invuln": "5+*",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Conflagration cannon",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "3D6",
                "skill": "N/A",
                "strength": "8",
                "ap": "-1",
                "damage": "2",
                "keywords": "Ignores Cover, Torrent"
            },
            {
                "name": "Thundercoil harpoon",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "D3",
                "skill": "3+",
                "strength": "24",
                "ap": "-6",
                "damage": "10",
                "keywords": "Blast, Devastating Wounds"
            },
            {
                "name": "Titanic feet",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "4+",
                "strength": "8",
                "ap": "-1",
                "damage": "2",
                "keywords": "-"
            },
            {
                "name": "Twin meltagun",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "9",
                "ap": "-4",
                "damage": "D6",
                "keywords": "Melta 2, Twin-Linked"
            }
        ],
        "abilities": [
            {
                "name": "Thundershock",
                "description": "In your Shooting phase, each time you select a target for this model's thundercoil harpoon, roll one D6 for the target unit and one D6 for each other enemy unit within 6\" of the target unit. On a 4+, the unit being rolled for is struck by arcing energies; after resolving all of this model's attacks against the target unit, each unit struck by arcing energies suffers D3 mortal wounds."
            },
            {
                "name": "Damaged: 1-10 Wounds Remaining",
                "description": "While this model has 1-10 wounds remaining, subtract 5 from this model's Objective Control characteristic and each time this model makes an attack, subtract 1 from the Hit roll."
            },
            {
                "name": "Ion Aegis (Aura)",
                "description": "While a friendly Armiger model is within 6\" of this model, each time a ranged attack targets that model, it has the Benefit of Cover against that attack."
            }
        ]
    },
    "Knight Warden": {
        "stats": {
            "stat_movement": "10\"",
            "stat_toughness": 11,
            "stat_save": "3+",
            "stat_wounds": 26,
            "stat_leadership": "6+",
            "stat_oc": 10,
            "stat_invuln": "5+*",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Avenger gatling cannon",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "18",
                "skill": "3+",
                "strength": "6",
                "ap": "-2",
                "damage": "2",
                "keywords": "-"
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
            }
        ],
        "abilities": [
            {
                "name": "Thin Their Ranks",
                "description": "Each time this model makes a ranged attack that targets an enemy unit (excluding Monsters and Vehicles), that attack has the [DEVASTATING WOUNDS] ability."
            },
            {
                "name": "Damaged: 1-9 Wounds Remaining",
                "description": "While this model has 1-9 wounds remaining, subtract 5 from this model's Objective Control characteristic and each time this model makes an attack, subtract 1 from the Hit roll."
            }
        ]
    },
    "Questoris Knight Magaera": {
        "stats": {
            "stat_movement": "10\"",
            "stat_toughness": 11,
            "stat_save": "3+",
            "stat_wounds": 26,
            "stat_leadership": "6+",
            "stat_oc": 10,
            "stat_invuln": "5+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Phased plasma-fusil",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "2",
                "skill": "3+",
                "strength": "8",
                "ap": "-3",
                "damage": "2",
                "keywords": "Rapid Fire 2"
            },
            {
                "name": "Lightning cannon",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "12",
                "skill": "3+",
                "strength": "9",
                "ap": "0",
                "damage": "2",
                "keywords": "Sustained Hits 2"
            },
            {
                "name": "\u27a4 Hekaton siege claw - strike",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "3+",
                "strength": "20",
                "ap": "-3",
                "damage": "8",
                "keywords": "-"
            },
            {
                "name": "\u27a4 Hekaton siege claw - sweep",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "8",
                "skill": "3+",
                "strength": "10",
                "ap": "-2",
                "damage": "3",
                "keywords": "-"
            },
            {
                "name": "Twin rad cleanser",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "D6",
                "skill": "N/A",
                "strength": "2",
                "ap": "0",
                "damage": "1",
                "keywords": "Torrent, Ignores Cover, Anti-Infantry 2+, Twin-linked"
            },
            {
                "name": "\u27a4 Reaper chainsword - strike",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "3+",
                "strength": "14",
                "ap": "-4",
                "damage": "6",
                "keywords": "-"
            },
            {
                "name": "\u27a4 Reaper chainsword - sweep",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "12",
                "skill": "3+",
                "strength": "9",
                "ap": "-3",
                "damage": "2",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Repair Auto-simulacra",
                "description": "At the end of your Command phase, this model regains up to D3 lost wounds."
            },
            {
                "name": "Damaged: 1-9 Wounds Remaining",
                "description": "While this model has 1-9 wounds remaining, subtract 5 from this model's Objective Control characteristic and each time this model makes an attack, subtract 1 from the Hit roll."
            }
        ]
    },
    "Questoris Knight Styrix": {
        "stats": {
            "stat_movement": "10\"",
            "stat_toughness": 11,
            "stat_save": "3+",
            "stat_wounds": 26,
            "stat_leadership": "6+",
            "stat_oc": 10,
            "stat_invuln": "5+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Graviton crusher",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "3",
                "skill": "3+",
                "strength": "6",
                "ap": "-1",
                "damage": "2",
                "keywords": "Anti-Vehicle 2+, Blast"
            },
            {
                "name": "Volkite chierovile",
                "weapon_type": "ranged",
                "range": "30\"",
                "attacks": "12",
                "skill": "3+",
                "strength": "12",
                "ap": "0",
                "damage": "3",
                "keywords": "Devastating Wounds"
            },
            {
                "name": "\u27a4 Hekaton siege claw - strike",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "3+",
                "strength": "20",
                "ap": "-3",
                "damage": "8",
                "keywords": "-"
            },
            {
                "name": "\u27a4 Hekaton siege claw - sweep",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "8",
                "skill": "3+",
                "strength": "10",
                "ap": "-2",
                "damage": "3",
                "keywords": "-"
            },
            {
                "name": "Twin rad cleanser",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "D6",
                "skill": "N/A",
                "strength": "2",
                "ap": "0",
                "damage": "1",
                "keywords": "Torrent, Ignores Cover, Anti-Infantry 2+, Twin-linked"
            },
            {
                "name": "\u27a4 Reaper chainsword - strike",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "3+",
                "strength": "14",
                "ap": "-4",
                "damage": "6",
                "keywords": "-"
            },
            {
                "name": "\u27a4 Reaper chainsword - sweep",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "12",
                "skill": "3+",
                "strength": "9",
                "ap": "-3",
                "damage": "2",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Grav-pinned",
                "description": "In your Shooting phase, after this model has shot, if an enemy INFANTRY unit was hit by one or more of those attacks made with a graviton crusher, until the end of your opponent\u2019s next turn, that enemy unit is grav-pinned. While a unit is grav-pinned, subtract 2 from that unit\u2019s Move characteristic and subtract 2 from Charge rolls made for that unit."
            },
            {
                "name": "Damaged: 1-9 Wounds Remaining",
                "description": "While this model has 1-9 wounds remaining, subtract 5 from this model's Objective Control characteristic and each time this model makes an attack, subtract 1 from the Hit roll."
            }
        ]
    }
}


class Command(BaseCommand):
    """Refresh Imperial Knights stat lines, weapon profiles, and abilities from BSData."""

    help = 'Refresh 11th Edition stats/weapons/abilities for Imperial Knights units.'

    def add_arguments(self, parser):
        """Add --dry-run flag."""
        parser.add_argument(
            '--dry-run', action='store_true',
            help='Preview changes without writing to the database.',
        )

    def handle(self, *args, **options):
        """Iterate IMPERIAL_KNIGHTS_DATASHEETS and refresh each unit's datasheet data."""
        dry_run = options['dry_run']
        updated = 0
        skipped = 0

        with transaction.atomic():
            for name, payload in IMPERIAL_KNIGHTS_DATASHEETS.items():
                try:
                    unit = UnitType.objects.get(name=name, faction__name='Imperial Knights')
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
