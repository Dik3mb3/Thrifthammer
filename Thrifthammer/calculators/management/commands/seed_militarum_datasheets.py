"""
Management command: seed_militarum_datasheets

Refreshes stat lines, weapon profiles, and abilities for all Astra
Militarum units using 11th Edition data sourced from BSData/wh40k-11e
("Imperium - Astra Militarum.json" roster, resolved against "Imperium -
Astra Militarum - Library.json") -- the same source used by
seed_militarum_points.py.

Usage:
    python manage.py seed_militarum_datasheets
    python manage.py seed_militarum_datasheets --dry-run

Notes:
- Does NOT touch points_cost or category -- those are handled entirely by
  seed_militarum_points.py. This command only refreshes stat_* fields,
  WeaponProfile rows, and UnitAbility rows.
- Per-field safety rule: a unit's stats/weapons/abilities are only
  overwritten when BSData actually has that data for it. If extraction
  found nothing, the existing DB value/rows are left untouched rather than
  blanked.
- All 67 active units resolved cleanly using the full accumulated
  extraction methodology (top-level selectionEntries recursion,
  sharedProfiles fallback by name, infoLinks(type="profile") resolution by
  id). Aegis Defence Line (a Fortification) genuinely has 0 weapon
  profiles in BSData -- not a bug, it's a defensive emplacement with
  abilities but no weapons of its own.
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from calculators.models import UnitAbility, UnitType, WeaponProfile

# (name -> {stats?, weapons?, abilities?}). Missing keys mean "no data
# found for this field -- leave existing DB data untouched."
MILITARUM_DATASHEETS = {
    "Aegis Defence Line": {
        "stats": {
            "stat_movement": "-",
            "stat_toughness": 12,
            "stat_save": "2+",
            "stat_wounds": 10,
            "stat_leadership": "7+",
            "stat_oc": 0,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "abilities": [
            {
                "name": "Emplacement Platform",
                "description": "Friendly Astra Militarum Infantry models can be set up or end any type of move on top of the platform section of this Fortification."
            },
            {
                "name": "Reinforced Cover",
                "description": "Each time a ranged attack is allocated to a model, if that model is not fully visible to every model in the attacking unit because of this Fortification, that model has the Benefit of Cover against that attack."
            },
            {
                "name": "Defence Line",
                "description": "While an Astra Militarum Infantry model has the Benefit of Cover as a result of this terrain feature, that model has a 4+ invulnerable save"
            },
            {
                "name": "Deployment",
                "description": "When this model is set up, it will consist of 1 platform section, up to 5 shield sections, up to 2 broken shield sections and up to 2 end sections. All sections must be connected to each other to form a continuous defence line; the 2 broken shield sections can be placed either at the end of the defence line, or in the middle of it such that both are within \u00bd\" of each other (in this case, these 2 sections count as being connected to each other). All of the sections that have been set up are then treated as a single model for all rules purposes."
            }
        ]
    },
    "Armoured Sentinels": {
        "stats": {
            "stat_movement": "8\"",
            "stat_toughness": 8,
            "stat_save": "2+",
            "stat_wounds": 7,
            "stat_leadership": "7+",
            "stat_oc": 2,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Close combat weapon",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "2",
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
                "skill": "4+",
                "strength": "14",
                "ap": "-3",
                "damage": "D6",
                "keywords": "One Shot"
            },
            {
                "name": "Sentinel chainsaw",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "3",
                "skill": "4+",
                "strength": "6",
                "ap": "-1",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "Multi-laser",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "4",
                "skill": "4+",
                "strength": "6",
                "ap": "0",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "Autocannon",
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
                "name": "Lascannon",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "1",
                "skill": "4+",
                "strength": "12",
                "ap": "-3",
                "damage": "D6+1",
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
                "name": "\u27a4 Plasma cannon - standard",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "D3",
                "skill": "4+",
                "strength": "7",
                "ap": "-2",
                "damage": "1",
                "keywords": "Blast"
            },
            {
                "name": "\u27a4 Plasma cannon - supercharge",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "D3",
                "skill": "4+",
                "strength": "8",
                "ap": "-3",
                "damage": "2",
                "keywords": "Blast, Hazardous"
            }
        ],
        "abilities": [
            {
                "name": "Mobile Hunter-killers",
                "description": "Each time a model in this unit makes an attack that targets a Monster or Vehicle unit, you can re-roll the Wound roll."
            }
        ]
    },
    "Artillery Team": {
        "stats": {
            "stat_movement": "3\"",
            "stat_toughness": 7,
            "stat_save": "3+",
            "stat_wounds": 10,
            "stat_leadership": "7+",
            "stat_oc": 3,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Crew close combat weapons",
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
                "name": "Heavy mortar",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "D6+3",
                "skill": "5+",
                "strength": "8",
                "ap": "-1",
                "damage": "2",
                "keywords": "Blast, Heavy, Indirect Fire"
            },
            {
                "name": "Siege cannon",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "D6",
                "skill": "5+",
                "strength": "12",
                "ap": "-2",
                "damage": "3",
                "keywords": "Blast, Heavy, Indirect Fire"
            },
            {
                "name": "Multiple rocket launcher",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "D6+3",
                "skill": "5+",
                "strength": "2",
                "ap": "-1",
                "damage": "1",
                "keywords": "Anti-Infantry 3+, Blast, Heavy, Indirect Fire"
            },
            {
                "name": "Heavy quad launcher",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "2D6",
                "skill": "5+",
                "strength": "5",
                "ap": "0",
                "damage": "1",
                "keywords": "Blast, Heavy, Indirect Fire, Twin-linked"
            }
        ],
        "abilities": [
            {
                "name": "Remorseless Barrage",
                "description": "In your Shooting phase, after this model has shot, if one or more of those attacks made with an Indirect Fire weapon scored a hit against an enemy unit, that unit must take a Battle-shock test (if an Infantry unit is hit by one or more attacks made by a multiple rocket launcher, they must subtract 1 from their Battle-shock test when doing so)."
            }
        ]
    },
    "Attilan Rough Riders": {
        "stats": {
            "stat_movement": "12\"",
            "stat_toughness": 4,
            "stat_save": "4+",
            "stat_wounds": 2,
            "stat_leadership": "7+",
            "stat_oc": 1,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Laspistol",
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
                "name": "\u27a4 Hunting lance - frag tip",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "D6",
                "skill": "3+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Lance"
            },
            {
                "name": "\u27a4 Hunting lance - melta tip",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "1",
                "skill": "3+",
                "strength": "9",
                "ap": "-4",
                "damage": "D6",
                "keywords": "Lance"
            },
            {
                "name": "Steed's hooves",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "2",
                "skill": "4+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Extra Attacks"
            },
            {
                "name": "Goad lance",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "2",
                "skill": "3+",
                "strength": "6",
                "ap": "-2",
                "damage": "2",
                "keywords": "Lance"
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
            }
        ],
        "abilities": [
            {
                "name": "Horsemasters",
                "description": "This unit is eligible to shoot and declare a charge in a turn in which it Fell Back."
            }
        ]
    },
    "Baneblade": {
        "stats": {
            "stat_movement": "12\"",
            "stat_toughness": 13,
            "stat_save": "2+",
            "stat_wounds": 24,
            "stat_leadership": "7+",
            "stat_oc": 8,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Baneblade cannon",
                "weapon_type": "ranged",
                "range": "72\"",
                "attacks": "3D6",
                "skill": "4+",
                "strength": "12",
                "ap": "-2",
                "damage": "3",
                "keywords": "Blast"
            },
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
                "name": "Coaxial autocannon",
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
                "name": "Demolisher cannon",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "D6+3",
                "skill": "4+",
                "strength": "14",
                "ap": "-3",
                "damage": "D6",
                "keywords": "Blast"
            },
            {
                "name": "Heavy stubber",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "3",
                "skill": "4+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Rapid Fire 3"
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
                "keywords": "-"
            },
            {
                "name": "Twin heavy bolter",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "3",
                "skill": "4+",
                "strength": "5",
                "ap": "-1",
                "damage": "2",
                "keywords": "Sustained Hits 1, Twin-linked"
            }
        ],
        "abilities": [
            {
                "name": "Rolling Fortress",
                "description": "Each time a ranged attack is allocated to an Astra Militarum model from your army, if that model is not fully visible to every model in the attacking unit because of this Baneblade model, that model has the Benefit of Cover against that attack."
            },
            {
                "name": "Damaged: 1-8 Wounds Remaining",
                "description": "While this model has 1-8 wounds remaining, subtract 4 from its Objective Control characteristic and each time this model makes an attack, subtract 1 from the Hit roll."
            }
        ]
    },
    "Banehammer": {
        "stats": {
            "stat_movement": "12\"",
            "stat_toughness": 13,
            "stat_save": "2+",
            "stat_wounds": 24,
            "stat_leadership": "7+",
            "stat_oc": 8,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Tremor cannon",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "2D6+3",
                "skill": "4+",
                "strength": "12",
                "ap": "-2",
                "damage": "3",
                "keywords": "Blast"
            },
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
                "name": "Lascannon",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "1",
                "skill": "4+",
                "strength": "12",
                "ap": "-3",
                "damage": "D6+1",
                "keywords": "-"
            },
            {
                "name": "Twin heavy bolter",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "3",
                "skill": "4+",
                "strength": "5",
                "ap": "-1",
                "damage": "2",
                "keywords": "Sustained Hits 1, Twin-linked"
            }
        ],
        "abilities": [
            {
                "name": "Tremor Quake",
                "description": "In your Shooting phase, just after selecting a target for this model\u2019s tremor cannon, the target unit and every other enemy Infantry unit within 3\" of that unit must take a Battle-shock test."
            },
            {
                "name": "Transport",
                "description": "This model has a transport capacity of 26 Astra Militarum Infantry models. Each Ogryn model takes up the space of 3 models. It cannot transport Artillery models."
            },
            {
                "name": "Damaged: 1-8 Wounds Remaining",
                "description": "While this model has 1-8 wounds remaining, subtract 4 from its Objective Control characteristic and each time this model makes an attack, subtract 1 from the Hit roll."
            }
        ]
    },
    "Banesword": {
        "stats": {
            "stat_movement": "12\"",
            "stat_toughness": 13,
            "stat_save": "2+",
            "stat_wounds": 24,
            "stat_leadership": "7+",
            "stat_oc": 8,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Quake cannon",
                "weapon_type": "ranged",
                "range": "72\"",
                "attacks": "D6+6",
                "skill": "4+",
                "strength": "16",
                "ap": "-4",
                "damage": "4",
                "keywords": "Blast, Ignores Cover"
            },
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
                "name": "Lascannon",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "1",
                "skill": "4+",
                "strength": "12",
                "ap": "-3",
                "damage": "D6+1",
                "keywords": "-"
            },
            {
                "name": "Twin heavy bolter",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "3",
                "skill": "4+",
                "strength": "5",
                "ap": "-1",
                "damage": "2",
                "keywords": "Sustained Hits 1, Twin-linked"
            }
        ],
        "abilities": [
            {
                "name": "Armour Obliteration",
                "description": "Each time an attack made with this model\u2019s quake cannon destroys an enemy model that has the Deadly Demise ability, that model\u2019s Deadly Demise ability inflicts mortal wounds on a D6 roll of 3+ instead of on a 6."
            },
            {
                "name": "Damaged: 1-8 Wounds Remaining",
                "description": "While this model has 1-8 wounds remaining, subtract 4 from its Objective Control characteristic and each time this model makes an attack, subtract 1 from the Hit roll."
            }
        ]
    },
    "Basilisk": {
        "stats": {
            "stat_movement": "10\"",
            "stat_toughness": 9,
            "stat_save": "3+",
            "stat_wounds": 11,
            "stat_leadership": "7+",
            "stat_oc": 3,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Earthshaker cannon",
                "weapon_type": "ranged",
                "range": "240\"",
                "attacks": "D6+3",
                "skill": "4+",
                "strength": "8",
                "ap": "-2",
                "damage": "2",
                "keywords": "Blast, Indirect Fire,"
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
            }
        ],
        "abilities": [
            {
                "name": "Earthshaker Rounds",
                "description": "In your Shooting phase, after this model has shot, if one or more of those attacks made with its earthshaker cannon scored a hit against an enemy INFANTRY unit, until the start of your next Shooting phase, that unit is shaken. While a unit is shaken, subtract 2\" from its Move characteristic and subtract 2 from Charge rolls made for it."
            },
            {
                "name": "Damaged: 1-4 Wounds Remaining",
                "description": "While this model has 1-4 wounds remaining, each time this model makes an attack, subtract 1 from the Hit roll."
            }
        ]
    },
    "Bullgryn Squad": {
        "stats": {
            "stat_movement": "6\"",
            "stat_toughness": 6,
            "stat_save": "3+",
            "stat_wounds": 3,
            "stat_leadership": "7+",
            "stat_oc": 1,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Close combat weapon",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "3+",
                "strength": "6",
                "ap": "0",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "Bullgryn maul",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "3+",
                "strength": "7",
                "ap": "-1",
                "damage": "2",
                "keywords": "-"
            },
            {
                "name": "Grenadier gauntlet",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "D6",
                "skill": "4+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Blast"
            }
        ],
        "abilities": [
            {
                "name": "Wall of Muscle",
                "description": "Each time an attack is allocated to a model in this unit, subtract 1 from the Damage characteristic of that attack."
            },
            {
                "name": "Slabshield",
                "description": "The bearer has a Wounds characteristic of 4."
            },
            {
                "name": "Brute Shield",
                "description": "The bearer has a 4+ invulnerable save."
            }
        ]
    },
    "Cadian Castellan": {
        "stats": {
            "stat_movement": "6\"",
            "stat_toughness": 3,
            "stat_save": "5+",
            "stat_wounds": 4,
            "stat_leadership": "7+",
            "stat_oc": 1,
            "stat_invuln": "5+",
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
                "name": "Laspistol",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "3",
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
                "name": "Close combat weapon",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "3",
                "skill": "3+",
                "strength": "3",
                "ap": "0",
                "damage": "1",
                "keywords": "-"
            },
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
                "name": "Power weapon",
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
                "name": "Chainsword",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "5",
                "skill": "3+",
                "strength": "3",
                "ap": "0",
                "damage": "1",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Senior Officer",
                "description": "While this model is leading a unit, ranged weapons equipped by models in that unit have the [SUSTAINED HITS 1] ability"
            },
            {
                "name": "Get Back in the Fight",
                "description": "While this model is leading a unit, that unit is eligible to shoot in a turn in which it Fell Back."
            }
        ]
    },
    "Cadian Command Squad": {
        "stats": {
            "stat_movement": "6\"",
            "stat_toughness": 3,
            "stat_save": "5+",
            "stat_wounds": 3,
            "stat_leadership": "7+",
            "stat_oc": 1,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Power fist",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "3",
                "skill": "4+",
                "strength": "6",
                "ap": "-2",
                "damage": "2",
                "keywords": "-"
            },
            {
                "name": "Power weapon",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "3",
                "skill": "4+",
                "strength": "4",
                "ap": "-2",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "Chainsword",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "4+",
                "strength": "3",
                "ap": "0",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "Laspistol",
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
                "name": "\u27a4 Plasma pistol - supercharge",
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
                "name": "Close combat weapon",
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
                "name": "\u27a4 Grenade launcher - frag",
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
                "name": "\u27a4 Grenade launcher - krak",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "1",
                "skill": "4+",
                "strength": "9",
                "ap": "-2",
                "damage": "D3",
                "keywords": "-"
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
            }
        ],
        "abilities": [
            {
                "name": "Cadia Stands!",
                "description": "While this unit contains an OFFICER model and this unit is within range of an objective, this unit can re-roll battle-shock rolls."
            },
            {
                "name": "Regimental Standard",
                "description": "Add 1 to the Objective Control characteristic of models in the bearer\u2019s unit."
            },
            {
                "name": "Master Vox",
                "description": "Each time the Officer in the bearer\u2019s unit issues an Order, it can issue it to an eligible unit up to 24\" away."
            },
            {
                "name": "Medi-pack",
                "description": "At the start of your Command phase, if the bearer's unit is below its Starting Strength, you can return up to D3 destroyed Platoon (excluding Characters) to this unit."
            }
        ]
    },
    "Cadian Heavy Weapons Squad": {
        "stats": {
            "stat_movement": "6\"",
            "stat_toughness": 3,
            "stat_save": "5+",
            "stat_wounds": 2,
            "stat_leadership": "7+",
            "stat_oc": 2,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Laspistol",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "2",
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
                "strength": "3",
                "ap": "0",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "Heavy bolter",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "3",
                "skill": "5+",
                "strength": "5",
                "ap": "-1",
                "damage": "2",
                "keywords": "Heavy, Sustained Hits 1"
            },
            {
                "name": "Mortar",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "D6",
                "skill": "5+",
                "strength": "5",
                "ap": "0",
                "damage": "1",
                "keywords": "Blast, Heavy, Indirect Fire"
            },
            {
                "name": "\u27a4 Missile launcher - frag",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "D6",
                "skill": "5+",
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
                "skill": "5+",
                "strength": "9",
                "ap": "-2",
                "damage": "D6",
                "keywords": "Heavy"
            },
            {
                "name": "Lascannon",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "1",
                "skill": "5+",
                "strength": "12",
                "ap": "-3",
                "damage": "D6+1",
                "keywords": "Heavy"
            },
            {
                "name": "Autocannon",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "2",
                "skill": "5+",
                "strength": "9",
                "ap": "-1",
                "damage": "3",
                "keywords": "Heavy"
            }
        ],
        "abilities": [
            {
                "name": "Covering Fire",
                "description": "Each time you target this unit with the Fire Overwatch Stratagem, while resolving that Stratagem, hits are scored on unmodified Hit rolls of 5+, or on unmodified Hit rolls of 4+ instead if this unit is within 6\" of one or more friendly Platoon units."
            },
            {
                "name": "Embarking",
                "description": "While embarked within a Transport, each model takes up the space of 2 models, and each weapon equipped by these models is considered to be 2 models' weapons for the purposes of the Firing Deck ability."
            }
        ]
    },
    "Cadian Shock Troops": {
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
                "name": "Laspistol",
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
                "name": "Sergeant's autogun",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "2",
                "skill": "4+",
                "strength": "3",
                "ap": "0",
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
                "name": "Lasgun",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "1",
                "skill": "4+",
                "strength": "3",
                "ap": "0",
                "damage": "1",
                "keywords": "Rapid Fire 1"
            }
        ],
        "abilities": [
            {
                "name": "Shock Troops",
                "description": "At the end of your Command phase, if this unit is within range of an objective marker you control, that objective marker remains under your control, even if you have no models within range of it, until your opponent controls it at the start or end of any turn."
            },
            {
                "name": "Unit Composition",
                "description": "This unit can have up to two Leader units attached to it, provided no more than one of those units is a Command Squad unit. If it does, and this Bodyguard unit is destroyed, the Leader units attached to it become separate units, with their original Starting Strengths."
            },
            {
                "name": "Vox-caster",
                "description": "Each time you target the bearer\u2019s unit with a Stratagem, roll one D6, adding 1 to the result if there are one or more friendly Officer models within 6\": on a 5+, you gain 1CP"
            }
        ]
    },
    "Catachan Command Squad": {
        "stats": {
            "stat_movement": "6\"",
            "stat_toughness": 3,
            "stat_save": "5+",
            "stat_wounds": 1,
            "stat_leadership": "7+",
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
                "skill": "4+",
                "strength": "3",
                "ap": "0",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "Laspistol",
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
                "name": "\u27a4 Grenade launcher - frag",
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
                "name": "\u27a4 Grenade launcher - krak",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "1",
                "skill": "4+",
                "strength": "9",
                "ap": "-2",
                "damage": "D3",
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
                "name": "Sniper rifle",
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
                "name": "\u27a4 Plasma pistol - supercharge",
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
                "name": "Chainsword",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "4+",
                "strength": "3",
                "ap": "0",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "Power fist",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "3",
                "skill": "4+",
                "strength": "6",
                "ap": "-2",
                "damage": "2",
                "keywords": "-"
            },
            {
                "name": "Power weapon",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "3",
                "skill": "4+",
                "strength": "4",
                "ap": "-2",
                "damage": "1",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Master Vox",
                "description": "Each time the Officer in the bearer\u2019s unit issues an Order, it can issue it to an eligible unit up to 24\" away."
            },
            {
                "name": "Regimental Standard",
                "description": "Add 1 to the Objective Control characteristic of models in the bearer\u2019s unit."
            },
            {
                "name": "Medi-pack",
                "description": "At the start of your Command phase, if the bearer's unit is below its Starting Strength, you can return up to D3 destroyed Platoon (excluding Characters) to this unit."
            }
        ]
    },
    "Catachan Heavy Weapons Squad": {
        "stats": {
            "stat_movement": "6\"",
            "stat_toughness": 3,
            "stat_save": "5+",
            "stat_wounds": 2,
            "stat_leadership": "7+",
            "stat_oc": 2,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Close combat weapon",
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
                "name": "Heavy bolter",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "3",
                "skill": "5+",
                "strength": "5",
                "ap": "-1",
                "damage": "2",
                "keywords": "Heavy, Sustained Hits 1"
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
                "name": "Mortar",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "D6",
                "skill": "5+",
                "strength": "5",
                "ap": "0",
                "damage": "1",
                "keywords": "Blast, Heavy, Indirect Fire"
            },
            {
                "name": "\u27a4 Missile launcher - frag",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "D6",
                "skill": "5+",
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
                "skill": "5+",
                "strength": "9",
                "ap": "-2",
                "damage": "D6",
                "keywords": "Heavy"
            },
            {
                "name": "Lascannon",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "1",
                "skill": "5+",
                "strength": "12",
                "ap": "-3",
                "damage": "D6+1",
                "keywords": "Heavy"
            },
            {
                "name": "Autocannon",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "2",
                "skill": "5+",
                "strength": "9",
                "ap": "-1",
                "damage": "3",
                "keywords": "Heavy"
            }
        ],
        "abilities": [
            {
                "name": "Bring it Down!",
                "description": "Each time a model in this unit makes a ranged attack that targets a Monster or Vehicle unit, re-roll a Hit roll of 1 and re-roll a Wound roll of 1."
            },
            {
                "name": "Embarking",
                "description": "While embarked within a Transport, each model takes up the space of 2 models, and each weapon equipped by these models is considered to be 2 models' weapons for the purposes of the Firing Deck ability."
            }
        ]
    },
    "Catachan Jungle Fighters": {
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
                "name": "Laspistol",
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
            }
        ],
        "abilities": [
            {
                "name": "Jungle Fighters",
                "description": "Each time a model in this unit makes a melee attack, if this unit made a Charge move or was charged this turn, add 1 to the Wound roll."
            },
            {
                "name": "Unit Composition",
                "description": "This unit can have up to two Leader units attached to it, provided no more than one of those units is a Command Squad unit. If it does, and this Bodyguard unit is destroyed, the Leader units attached to it become separate units, with their original Starting Strengths."
            },
            {
                "name": "Vox-caster",
                "description": "Each time you target the bearer\u2019s unit with a Stratagem, roll one D6, adding 1 to the result if there are one or more friendly Officer models within 6\": on a 5+, you gain 1CP"
            }
        ]
    },
    "Chimera": {
        "stats": {
            "stat_movement": "10\"",
            "stat_toughness": 9,
            "stat_save": "3+",
            "stat_wounds": 11,
            "stat_leadership": "7+",
            "stat_oc": 2,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Lasgun array",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "6",
                "skill": "4+",
                "strength": "3",
                "ap": "0",
                "damage": "1",
                "keywords": "Rapid Fire 6"
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
                "skill": "4+",
                "strength": "14",
                "ap": "-3",
                "damage": "D6",
                "keywords": "One Shot"
            }
        ],
        "abilities": [
            {
                "name": "Mobile Command Vehicle",
                "description": "In your Command phase, one Officer model embarked within this Transport can issue Orders even though it is not on the battlefield. When doing so, measure distances to and from this Transport*."
            }
        ]
    },
    "Commissar": {
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
                "name": "Power weapon",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "3",
                "skill": "3+",
                "strength": "4",
                "ap": "-2",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "Chainsword",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "3+",
                "strength": "3",
                "ap": "0",
                "damage": "1"
            }
        ],
        "abilities": [
            {
                "name": "Summary Execution",
                "description": "Once per battle round, at the start of any phase, you can select one friendly Astra Militarum Infantry unit that is Battle-shocked and within 12\" of this model. If you do, one model in that unit is destroyed, and that unit is then no longer Battle-shocked."
            },
            {
                "name": "Political Overwatch",
                "description": "While another Officer model is in the same unit as this model, you can re-roll Battle-shock tests taken for that unit."
            },
            {
                "name": "Leader",
                "description": "This model can be attached to the following units:\n- CADIAN SHOCK TROOPS\n- CATACHAN JUNGLE FIGHTERS\n- DEATH KORPS GRENADIER SQUAD\n- DEATH KORPS OF KRIEG\n- KASRKIN\n- KRIEG COMBAT ENGINEERS\n- TEMPESTUS SCIONS"
            }
        ]
    },
    "Commissar Graves": {
        "stats": {
            "stat_movement": "12\"",
            "stat_toughness": 8,
            "stat_save": "3+",
            "stat_wounds": 12,
            "stat_leadership": "6+",
            "stat_oc": 5,
            "stat_invuln": "4+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Prefectus heavy stubber",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "3",
                "skill": "3+",
                "strength": "5",
                "ap": "0",
                "damage": "1",
                "keywords": "Rapid Fire 3"
            },
            {
                "name": "Enforcer crew",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "10",
                "skill": "4+",
                "strength": "3",
                "ap": "0",
                "damage": "1",
                "keywords": "Extra Attacks"
            },
            {
                "name": "Armoured hull",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "3",
                "skill": "4+",
                "strength": "6",
                "ap": "0",
                "damage": "1",
                "keywords": "Extra Attacks"
            },
            {
                "name": "Chiron gatling cannon",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "12",
                "skill": "3+",
                "strength": "5",
                "ap": "0",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "Power sword and Manus Mortis",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "5",
                "skill": "2+",
                "strength": "6",
                "ap": "-2",
                "damage": "2",
                "keywords": "Lance"
            }
        ],
        "abilities": [
            {
                "name": "Brutal Disciplinarian",
                "description": "Once per turn, at the start of any phase, you can select one friendly Astra Militarum Infantry unit (excluding units that only contain one model) that is Battle-shocked and within 24\" of and visible to this model. If you do, one model in that unit is destroyed, and that unit is no longer Battle-shocked."
            },
            {
                "name": "Mechanised Spearhead",
                "description": "In your Movement phase, each time a friendly Astra Militarum Regiment unit disembarks from a Transport that is within 6\" of this model, after that unit has been set up, this model can issue 1 Order to that Regiment unit, regardless of how many Orders this model has already issued this turn."
            },
            {
                "name": "Aquiline Prow",
                "description": "Each time this unit ends a Charge move, you can select one enemy unit within Engagement Range of it, then roll one D6: on a 2-3, that enemy unit suffers D3 mortal wounds; on a 4-5, that enemy unit suffers 3 mortal wounds; on a 6, that enemy unit suffers D3+3 mortal wounds."
            }
        ]
    },
    "Commissar Graves on Foot": {
        "stats": {
            "stat_movement": "6\"",
            "stat_toughness": 3,
            "stat_save": "4+",
            "stat_wounds": 4,
            "stat_leadership": "6+",
            "stat_oc": 1,
            "stat_invuln": "5+",
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
                "name": "Power sword and Manus Mortis",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "5",
                "skill": "2+",
                "strength": "6",
                "ap": "-2",
                "damage": "2",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Brutal Disciplinarian",
                "description": "Once per turn, at the start of any phase, you can select one friendly Astra Militarum Infantry (excluding units that only contain one model) unit that is Battle-shocked and within 12\" of this model. If you do, one model in that unit is destroyed, and that unit is no longer Battle-shocked."
            },
            {
                "name": "Leader",
                "description": "This model can be attached to the following units:\n- CADIAN SHOCK TROOPS\n- CATACHAN JUNGLE FIGHTERS\n- DEATH KORPS GRENADIER SQUAD\n- DEATH KORPS OF KRIEG\n- KASRKIN\n- KRIEG COMBAT ENGINEERS\n- TEMPESTUS SCIONS"
            },
            {
                "name": "Icon of Discipline",
                "description": "This model\u2019s unit is eligible to shoot and declare a Charge in a turn in which it Fell Back."
            },
            {
                "name": "Using Commissar Graves",
                "description": "Your army can only include one Commissar Graves or Commissar Graves on Foot unit."
            }
        ]
    },
    "Commissar Yarrick": {
        "stats": {
            "stat_movement": "6\"",
            "stat_toughness": 4,
            "stat_save": "4+",
            "stat_wounds": 5,
            "stat_leadership": "6+",
            "stat_oc": 1,
            "stat_invuln": "4+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Laspistol",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "1",
                "skill": "2+",
                "strength": "3",
                "ap": "0",
                "damage": "1",
                "keywords": "Pistol"
            },
            {
                "name": "Power sword",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "6",
                "skill": "2+",
                "strength": "4",
                "ap": "-2",
                "damage": "1"
            },
            {
                "name": "Power klaw",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "2+",
                "strength": "8",
                "ap": "-2",
                "damage": "2"
            },
            {
                "name": "Bale Eye",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "2",
                "skill": "2+",
                "strength": "6",
                "ap": "-2",
                "damage": "D3+1",
                "keywords": "Precision"
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
                "keywords": "Rapid Fire 2"
            }
        ],
        "abilities": [
            {
                "name": "Will of Iron",
                "description": "The first time this model is destroyed, remove it from play, then, at the end of the phase, roll one D6: on a 2+, set this model back up on the battlefield as close as possible to where it was destroyed and not within Engagement Range of one or more enemy units, with 3 wounds remaining."
            },
            {
                "name": "Leader",
                "description": "This model can be attached to the following units:\n- CADIAN SHOCK TROOPS\n- CATACHAN JUNGLE FIGHTERS\n- DEATH KORPS GRENADIER SQUAD\n- DEATH KORPS OF KRIEG\n- KASRKIN\n- KRIEG COMBAT ENGINEERS\n- TEMPESTUS SCIONS"
            },
            {
                "name": "Hero of Hades Hive",
                "description": "In your Command phase, you can select one of the abilities in the Hero of Hades Hive section. Until the start of your next Command phase, this model has that ability."
            }
        ]
    },
    "Death Korps of Krieg": {
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
                "name": "\u27a4 Grenade launcher - frag",
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
                "name": "\u27a4 Grenade launcher - krak",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "1",
                "skill": "4+",
                "strength": "9",
                "ap": "-2",
                "damage": "D3",
                "keywords": "-"
            },
            {
                "name": "Long-las",
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
                "keywords": "Rapid Fire 1, Hazardous"
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
                "name": "Laspistol",
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
                "name": "\u27a4 Plasma pistol - supercharge",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "1",
                "skill": "4+",
                "strength": "8",
                "ap": "-3",
                "damage": "2",
                "keywords": "Hazardous, Pistol"
            }
        ],
        "abilities": [
            {
                "name": "Grim Demeanour",
                "description": "Each time a model in this unit makes an attack, add 1 to the Hit roll if this unit is below its Starting Strength, and add 1 to the Wound roll as well if this unit is Below Half-strength."
            },
            {
                "name": "Unit Composition",
                "description": "This unit can have up to two Leader units attached to it, provided no more than one of those units is a Command Squad unit. If it does, and this Bodyguard unit is destroyed, the Leader units attached to it become separate units, with their original Starting Strengths."
            },
            {
                "name": "Death Korps of Krieg Medi-pack",
                "description": "At the start of your Command phase, if the bearer\u2019s unit is below its Starting Strength, you can return up to D3 destroyed Death Korps Troopers to this unit (if this unit contains two models equipped with a Death Korps medi-pack, return up to D3+1 destroyed Death Korps Troopers to this unit instead)."
            },
            {
                "name": "Vox-caster",
                "description": "Each time you target the bearer\u2019s unit with a Stratagem, roll one D6, adding 1 to the result if there are one or more friendly Officer models within 6\": on a 5+, you gain 1CP"
            }
        ]
    },
    "Death Riders": {
        "stats": {
            "stat_movement": "10\"",
            "stat_toughness": 4,
            "stat_save": "4+",
            "stat_wounds": 2,
            "stat_leadership": "7+",
            "stat_oc": 1,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Steed's savage claws",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "2",
                "skill": "4+",
                "strength": "4",
                "ap": "-1",
                "damage": "1",
                "keywords": "Extra Attacks"
            },
            {
                "name": "Power sabre",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "3",
                "skill": "3+",
                "strength": "4",
                "ap": "-2",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "Death Rider lascarbine",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "2",
                "skill": "4+",
                "strength": "3",
                "ap": "0",
                "damage": "1",
                "keywords": "Assault"
            },
            {
                "name": "Frag lance",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "D6",
                "skill": "3+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Lance"
            }
        ],
        "abilities": [
            {
                "name": "Screening Line",
                "description": "In your opponent's Movement phase, if an enemy unit ends a move within 8\" of this unit, if this unit is not within Engagement Range of one or more enemy units, this unit can make a Normal move of up to 6\"."
            }
        ]
    },
    "Deathstrike": {
        "stats": {
            "stat_movement": "10\"",
            "stat_toughness": 10,
            "stat_save": "3+",
            "stat_wounds": 11,
            "stat_leadership": "7+",
            "stat_oc": 3,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Deathstrike Missile",
                "weapon_type": "ranged",
                "range": "N/A",
                "attacks": "2D6",
                "skill": "2+",
                "strength": "16",
                "ap": "-4",
                "damage": "1",
                "keywords": "Blast, One Shot, Plasma Warhead"
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
            }
        ],
        "abilities": [
            {
                "name": "Deathstrike Missile",
                "description": "In your Shooting phase, each time this model is selected to shoot, if it has not shot with its Deathstrike missile this battle, you can do one of the following in addition to resolving this model\u2019s ranged attacks:\n\n- Designate Target: If this model does not have a Deathstrike Target marker on the battlefield, place a Deathstrike Target marker for this model anywhere on the battlefield.\n\n- Adjust Target: If this model has a Deathstrike Target marker on the battlefield, move that marker to anywhere else on the battlefield."
            },
            {
                "name": "Damaged: 1-4 Wounds Remaining",
                "description": "While this model has 1-4 wounds remaining, each time this model makes an attack, subtract 1 from the Hit roll."
            }
        ]
    },
    "Doomhammer": {
        "stats": {
            "stat_movement": "12\"",
            "stat_toughness": 13,
            "stat_save": "2+",
            "stat_wounds": 24,
            "stat_leadership": "7+",
            "stat_oc": 8,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Magma cannon",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "D6+3",
                "skill": "4+",
                "strength": "12",
                "ap": "-4",
                "damage": "D6",
                "keywords": "Blast, Melta 6"
            },
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
                "name": "Lascannon",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "1",
                "skill": "4+",
                "strength": "12",
                "ap": "-3",
                "damage": "D6+1",
                "keywords": "-"
            },
            {
                "name": "Twin heavy bolter",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "3",
                "skill": "4+",
                "strength": "5",
                "ap": "-1",
                "damage": "2",
                "keywords": "Sustained Hits 1, Twin-linked"
            }
        ],
        "abilities": [
            {
                "name": "Close-range Titan Killer",
                "description": "Each time this model\u2019s magma cannon targets a Monster or Vehicle unit, that target is always considered to be within half range of that weapon."
            },
            {
                "name": "Damaged: 1-8 Wounds Remaining",
                "description": "While this model has 1-8 wounds remaining, subtract 4 from its Objective Control characteristic and each time this model makes an attack, subtract 1 from the Hit roll."
            }
        ]
    },
    "Field Ordnance Battery": {
        "stats": {
            "stat_movement": "3\"",
            "stat_toughness": 5,
            "stat_save": "4+",
            "stat_wounds": 6,
            "stat_leadership": "7+",
            "stat_oc": 2,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Malleus rocket launcher",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "D6+6",
                "skill": "5+",
                "strength": "6",
                "ap": "-1",
                "damage": "1",
                "keywords": "Blast, Heavy"
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
                "name": "Laspistol",
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
                "name": "Battery close combat weapons",
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
                "name": "Bombast field gun",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "D6",
                "skill": "5+",
                "strength": "7",
                "ap": "-1",
                "damage": "2",
                "keywords": "Blast, Heavy, Indirect Fire"
            },
            {
                "name": "Heavy lascannon",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "2",
                "skill": "5+",
                "strength": "14",
                "ap": "-3",
                "damage": "D6+1",
                "keywords": "Heavy"
            }
        ],
        "abilities": [
            {
                "name": "Rearm, Reload, Fire",
                "description": "While this unit is being affected by an Order, provided it Remained Stationary this turn, all Heavy weapons equipped by models in this unit have the [SUSTAINED HITS 1] ability"
            }
        ]
    },
    "Gaunt\u2019s Ghosts": {
        "stats": {
            "stat_movement": "6\"",
            "stat_toughness": 3,
            "stat_save": "4+",
            "stat_wounds": 3,
            "stat_leadership": "6+",
            "stat_oc": 1,
            "stat_invuln": "5+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Gaunt's chainsword",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "5",
                "skill": "2+",
                "strength": "3",
                "ap": "-1",
                "damage": "1",
                "keywords": "-"
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
                "name": "Corbec's hot-shot lascarbine",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "3",
                "skill": "3+",
                "strength": "3",
                "ap": "-1",
                "damage": "1",
                "keywords": "Assault"
            },
            {
                "name": "Straight silver knife",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "3",
                "skill": "3+",
                "strength": "3",
                "ap": "0",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "Larkin's long-las",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "1",
                "skill": "2+",
                "strength": "5",
                "ap": "-2",
                "damage": "4",
                "keywords": "Heavy, Precision"
            },
            {
                "name": "Lascarbine",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "3",
                "skill": "3+",
                "strength": "3",
                "ap": "0",
                "damage": "1",
                "keywords": "Assault"
            },
            {
                "name": "Mkoll's straight silver knife",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "5",
                "skill": "2+",
                "strength": "3",
                "ap": "-1",
                "damage": "1",
                "keywords": "Devastating Wounds, Precision"
            },
            {
                "name": "Rawne's lascarbine",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "3",
                "skill": "3+",
                "strength": "3",
                "ap": "0",
                "damage": "1",
                "keywords": "Assault, Sustained Hits 1"
            },
            {
                "name": "Bragg's autocannon",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "4",
                "skill": "5+",
                "strength": "9",
                "ap": "-1",
                "damage": "3",
                "keywords": "Heavy"
            }
        ],
        "abilities": [
            {
                "name": "Covert Stealth Team",
                "description": "At the end of your opponent\u2019s turn, if this unit is unengaged, you can use this ability. If you do:\n- Place this unit in strategic reserves.\n- This unit has Deep Strike until the start of your next Shooting phase.\n- This unit must make an ingress move in your next Movement phase (including in your first turn)."
            },
            {
                "name": "Tanith Camo-cloaks",
                "description": "Models in this unit have the Benefit of Cover."
            }
        ]
    },
    "Hellhammer": {
        "stats": {
            "stat_movement": "12\"",
            "stat_toughness": 13,
            "stat_save": "2+",
            "stat_wounds": 24,
            "stat_leadership": "7+",
            "stat_oc": 8,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Hellhammer cannon",
                "weapon_type": "ranged",
                "range": "30\"",
                "attacks": "4D6",
                "skill": "4+",
                "strength": "7",
                "ap": "-1",
                "damage": "2",
                "keywords": "Blast, Ignores Cover"
            },
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
                "name": "Coaxial autocannon",
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
                "name": "Demolisher cannon",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "D6+3",
                "skill": "4+",
                "strength": "14",
                "ap": "-3",
                "damage": "D6",
                "keywords": "Blast"
            },
            {
                "name": "Heavy stubber",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "3",
                "skill": "4+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Rapid Fire 3"
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
                "keywords": "-"
            },
            {
                "name": "Twin heavy bolter",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "3",
                "skill": "4+",
                "strength": "5",
                "ap": "-1",
                "damage": "2",
                "keywords": "Sustained Hits 1, Twin-linked"
            }
        ],
        "abilities": [
            {
                "name": "Close-quarters Warfare",
                "description": "This model does not suffer the penalty to its Hit rolls for making ranged attacks while enemy units are within Engagement Range of it."
            },
            {
                "name": "Damaged: 1-8 Wounds Remaining",
                "description": "While this model has 1-8 wounds remaining, subtract 4 from its Objective Control characteristic and each time this model makes an attack, subtract 1 from the Hit roll."
            }
        ]
    },
    "Hellhound": {
        "stats": {
            "stat_movement": "10\"",
            "stat_toughness": 10,
            "stat_save": "2+",
            "stat_wounds": 11,
            "stat_leadership": "7+",
            "stat_oc": 3,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Hunter-killer missile",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "1",
                "skill": "4+",
                "strength": "14",
                "ap": "-3",
                "damage": "D6",
                "keywords": "One Shot"
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
                "name": "Multi-melta",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "2",
                "skill": "4+",
                "strength": "9",
                "ap": "-4",
                "damage": "D6",
                "keywords": "Melta 2"
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
                "keywords": "Sustained Hits 1"
            },
            {
                "name": "Chem cannon",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "D6+1",
                "skill": "N/A",
                "strength": "2",
                "ap": "-2",
                "damage": "2",
                "keywords": "Anti-Infantry 2+, Torrent"
            },
            {
                "name": "Inferno cannon",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "2D6",
                "skill": "N/A",
                "strength": "6",
                "ap": "-2",
                "damage": "1",
                "keywords": "Ignores Cover, Torrent"
            },
            {
                "name": "Melta cannon",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "D3",
                "skill": "4+",
                "strength": "9",
                "ap": "-4",
                "damage": "D6",
                "keywords": "Blast, Melta 4"
            }
        ],
        "abilities": [
            {
                "name": "Flush Them Out",
                "description": "In your Shooting phase, after this model has shot, select one enemy unit that was hit by one or more of those attacks. Until the start of your next Shooting phase, that unit is scattered. While a unit is scattered, it cannot have the Benefit of Cover."
            },
            {
                "name": "Damaged: 1-4 Wounds Remaining",
                "description": "While this model has 1-4 wounds remaining, each time this model makes an attack, subtract 1 from the Hit roll."
            }
        ]
    },
    "Hydra": {
        "stats": {
            "stat_movement": "10\"",
            "stat_toughness": 9,
            "stat_save": "3+",
            "stat_wounds": 11,
            "stat_leadership": "7+",
            "stat_oc": 3,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Hydra autocannon",
                "weapon_type": "ranged",
                "range": "72\"",
                "attacks": "4",
                "skill": "4+",
                "strength": "9",
                "ap": "-1",
                "damage": "3",
                "keywords": "Anti-Fly 2+, Twin-linked"
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
            }
        ],
        "abilities": [
            {
                "name": "Flak Battery",
                "description": "Each time this model makes an attack that targets a unit that can Fly, you can re-roll the Hit roll."
            },
            {
                "name": "Damaged: 1-4 Wounds Remaining",
                "description": "While this model has 1-4 wounds remaining, each time this model makes an attack, subtract 1 from the Hit roll."
            }
        ]
    },
    "Kasrkin": {
        "stats": {
            "stat_movement": "6\"",
            "stat_toughness": 3,
            "stat_save": "4+",
            "stat_wounds": 1,
            "stat_leadership": "7+",
            "stat_oc": 1,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Hot-shot lasgun",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "3",
                "ap": "-1",
                "damage": "1",
                "keywords": "Rapid Fire 1"
            },
            {
                "name": "Close combat weapon",
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
                "name": "Hot-shot marksman rifle",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "4",
                "ap": "-2",
                "damage": "3",
                "keywords": "Heavy, Precision"
            },
            {
                "name": "Hot-shot laspistol",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "3",
                "ap": "-1",
                "damage": "1",
                "keywords": "Pistol"
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
                "keywords": "Rapid Fire 1, Hazardous"
            },
            {
                "name": "Hot-shot volley gun",
                "weapon_type": "ranged",
                "range": "30\"",
                "attacks": "2",
                "skill": "3+",
                "strength": "4",
                "ap": "-1",
                "damage": "1",
                "keywords": "Rapid Fire 2"
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
                "name": "\u27a4 Grenade launcher - frag",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "D3",
                "skill": "3+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Blast"
            },
            {
                "name": "\u27a4 Grenade launcher - krak",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "9",
                "ap": "-2",
                "damage": "D3",
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
                "name": "Chainsword",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
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
                "attacks": "3",
                "skill": "4+",
                "strength": "4",
                "ap": "-2",
                "damage": "1",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Warrior Elite",
                "description": "Once per battle round, at the start of any phase, you can select one Order to affect this unit until the start of your next Command phase, in addition to any other Orders issued to this unit by an Officer model this turn."
            },
            {
                "name": "Melta mine",
                "description": "Once per battle, at the start of any phase, you can select one enemy unit within 3\" of the bearer and roll one D6: on a 2+, that enemy unit suffers D3 mortal wounds, or 2D3 mortal wounds instead if it is a Vehicle unit."
            },
            {
                "name": "Vox-caster",
                "description": "Each time you target the bearer\u2019s unit with a Stratagem, roll one D6, adding 1 to the result if there are one or more friendly Officer models within 6\": on a 5+, you gain 1CP"
            }
        ]
    },
    "Krieg Combat Engineers": {
        "stats": {
            "stat_movement": "6\"",
            "stat_toughness": 3,
            "stat_save": "4+",
            "stat_wounds": 1,
            "stat_leadership": "7+",
            "stat_oc": 1,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
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
                "name": "Trench club",
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
                "name": "Close combat weapon",
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
                "name": "Combat shotgun",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "2",
                "skill": "4+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Assault"
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
                "name": "\u27a4 Plasma pistol - supercharge",
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
                "name": "Chainsword",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
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
                "attacks": "3",
                "skill": "4+",
                "strength": "4",
                "ap": "-2",
                "damage": "1",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Grenadiers",
                "description": "Once per turn, you can target this unit with the Grenade Stratagem for 0CP."
            },
            {
                "name": "Signal Flares",
                "description": "In your Shooting phase, this unit can select one visible enemy unit within 12\". That enemy unit is designated:\n\u25aa While a unit is designated, that unit has +3\" detection range."
            },
            {
                "name": "Remote mine",
                "description": "Once per battle, at the start of your Shooting phase, you can select one enemy unit within 9\" of and visible to the bearer and roll one D6: on a 3+, that enemy unit suffers D3 mortal wounds, or 2D3 mortal wounds instead if it is a VEHICLE or FORTIFICATIONS unit.\n\nDesigner's Note: Place a Remote Mine token next to the unit, removing it once this ability has been used."
            }
        ]
    },
    "Krieg Command Squad": {
        "stats": {
            "stat_movement": "6\"",
            "stat_toughness": 3,
            "stat_save": "5+",
            "stat_wounds": 3,
            "stat_leadership": "6+",
            "stat_oc": 1,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
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
                "name": "\u27a4 Plasma pistol - supercharge",
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
                "name": "Laspistol",
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
                "name": "Power fist",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "3",
                "skill": "4+",
                "strength": "6",
                "ap": "-2",
                "damage": "2",
                "keywords": "-"
            },
            {
                "name": "Power weapon",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "3",
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
                "attacks": "2",
                "skill": "4+",
                "strength": "3",
                "ap": "0",
                "damage": "1",
                "keywords": "-"
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
                "name": "\u27a4 Grenade launcher - frag",
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
                "name": "\u27a4 Grenade launcher - krak",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "1",
                "skill": "4+",
                "strength": "9",
                "ap": "-2",
                "damage": "D3",
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
                "name": "Trench club",
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
                "name": "Lasgun",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "1",
                "skill": "4+",
                "strength": "3",
                "ap": "0",
                "damage": "1",
                "keywords": "Rapid Fire 1"
            }
        ],
        "abilities": [
            {
                "name": "Grim Determination",
                "description": "While this unit contains an Officer, you can target this unit with Stratagems even while it is Battle-shocked and Orders issued to this unit do not cease to affect this unit if it becomes Battle-shocked."
            },
            {
                "name": "Leader",
                "description": "This model can be attached to the following units:\n- DEATH KORPS GRENADIER SQUAD\n- DEATH KORPS OF KRIEG\n- KRIEG COMBAT ENGINEERS"
            },
            {
                "name": "Alchemyk Counteragents",
                "description": "The bearer's unit has the Feel No Pain 6+ ability against mortal wounds."
            },
            {
                "name": "Servo-scribes",
                "description": "Once per battle, when issuing an Order, the Lord Commissar can issue one additional Order.\n\n\nDesigner's Note: Place a Servo-scribes token next to the unit, removing it when this ability has been used."
            },
            {
                "name": "Master Vox",
                "description": "Each time the Officer in the bearer\u2019s unit issues an Order, it can issue it to an eligible unit up to 24\" away."
            },
            {
                "name": "Regimental Standard",
                "description": "Add 1 to the Objective Control characteristic of models in the bearer\u2019s unit."
            }
        ]
    },
    "Krieg Heavy Weapons Squad": {
        "stats": {
            "stat_movement": "4\"",
            "stat_toughness": 3,
            "stat_save": "4+",
            "stat_wounds": 2,
            "stat_leadership": "7+",
            "stat_oc": 1,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Krieg heavy flamer",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "D6",
                "skill": "N/A",
                "strength": "5",
                "ap": "-1",
                "damage": "2",
                "keywords": "Ignores Cover, Torrent"
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
                "name": "Laspistol",
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
                "name": "Twin Krieg heavy stubber",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "3",
                "skill": "5+",
                "strength": "6",
                "ap": "-1",
                "damage": "1",
                "keywords": "Heavy, Rapid Fire 3, Twin-linked"
            },
            {
                "name": "Lascannon",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "1",
                "skill": "5+",
                "strength": "12",
                "ap": "-3",
                "damage": "D6+1",
                "keywords": "Heavy"
            }
        ],
        "abilities": [
            {
                "name": "Final Duty",
                "description": "While the Fire Coordinator model is on the battlefield, each time a Heavy Weapons Gunner model is destroyed, roll one D6: on a 3+, do not remove it from play. The destroyed model can shoot after the attacking model\u2019s unit has finished making its attacks, and is then removed from play."
            },
            {
                "name": "Embarking",
                "description": "While embarked within a Transport, each Heavy Weapons Gunner model takes up the space of 2 models, and each weapon equipped by these models is considered to be 2 models' weapons for the purposes of the Firing Deck ability."
            }
        ]
    },
    "Leman Russ Battle Tank": {
        "stats": {
            "stat_movement": "10\"",
            "stat_toughness": 11,
            "stat_save": "2+",
            "stat_wounds": 13,
            "stat_leadership": "7+",
            "stat_oc": 3,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Leman Russ battle cannon",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "D6+3",
                "skill": "4+",
                "strength": "10",
                "ap": "-1",
                "damage": "3",
                "keywords": "Blast"
            },
            {
                "name": "Armoured tracks",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "6",
                "skill": "4+",
                "strength": "7",
                "ap": "0",
                "damage": "1",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Armoured Spearhead",
                "description": "Each time this model makes an attack that targets an enemy unit, re-roll a Hit roll of 1 and, if that unit is within range of an objective marker you do not control, you can re-roll the Hit roll instead."
            },
            {
                "name": "Damaged: 1-4 Wounds Remaining",
                "description": "While this model has 1-4 wounds remaining, each time this model makes an attack, subtract 1 from the Hit roll."
            }
        ]
    },
    "Leman Russ Commander": {
        "stats": {
            "stat_movement": "10\"",
            "stat_toughness": 11,
            "stat_save": "2+",
            "stat_wounds": 13,
            "stat_leadership": "7+",
            "stat_oc": 3,
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
                "strength": "7",
                "ap": "0",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "Hunter-killer missile",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "1",
                "skill": "4+",
                "strength": "14",
                "ap": "-3",
                "damage": "D6",
                "keywords": "One Shot"
            },
            {
                "name": "Leman Russ battle cannon",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "D6+3",
                "skill": "4+",
                "strength": "10",
                "ap": "-1",
                "damage": "3",
                "keywords": "Blast"
            },
            {
                "name": "Demolisher battle cannon",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "D6+1",
                "skill": "4+",
                "strength": "14",
                "ap": "-3",
                "damage": "D6",
                "keywords": "Blast"
            },
            {
                "name": "Vanquisher battle cannon",
                "weapon_type": "ranged",
                "range": "72\"",
                "attacks": "1",
                "skill": "4+",
                "strength": "18",
                "ap": "-4",
                "damage": "D6+6",
                "keywords": "Heavy"
            },
            {
                "name": "Eradicator nova cannon",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "D3+6",
                "skill": "4+",
                "strength": "7",
                "ap": "-1",
                "damage": "2",
                "keywords": "Blast, Ignores Cover"
            },
            {
                "name": "\u27a4 Executioner plasma cannon - standard",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "D6+3",
                "skill": "4+",
                "strength": "7",
                "ap": "-2",
                "damage": "2",
                "keywords": "Blast"
            },
            {
                "name": "\u27a4 Executioner plasma cannon - supercharge",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "D6+3",
                "skill": "4+",
                "strength": "8",
                "ap": "-3",
                "damage": "3",
                "keywords": "Blast, Hazardous"
            },
            {
                "name": "Punisher gatling cannon",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "20",
                "skill": "4+",
                "strength": "6",
                "ap": "0",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "Exterminator autocannon",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "4",
                "skill": "4+",
                "strength": "9",
                "ap": "-1",
                "damage": "3",
                "keywords": "Rapid Fire 4, Twin-linked"
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
                "keywords": "Sustained Hits 1"
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
                "name": "Multi-melta",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "2",
                "skill": "4+",
                "strength": "9",
                "ap": "-4",
                "damage": "D6",
                "keywords": "Melta 2"
            },
            {
                "name": "\u27a4 Plasma cannon - standard",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "D3",
                "skill": "4+",
                "strength": "7",
                "ap": "-2",
                "damage": "1",
                "keywords": "Blast"
            },
            {
                "name": "\u27a4 Plasma cannon - supercharge",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "D3",
                "skill": "4+",
                "strength": "8",
                "ap": "-3",
                "damage": "2",
                "keywords": "Blast, Hazardous"
            },
            {
                "name": "Storm bolter",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "2",
                "skill": "4+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Rapid Fire 2"
            },
            {
                "name": "Heavy stubber",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "3",
                "skill": "4+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Rapid Fire 3"
            }
        ],
        "abilities": [
            {
                "name": "Death Befitting An Officer",
                "description": "In your opponent\u2019s Shooting phase, when this unit is destroyed, before this unit\u2019s deadly demise roll, roll one D6:\n- On a 2+, do not remove this unit from the battlefield. After the attacking unit has shot, this unit can shoot using normal shooting, but while doing so this unit can only target that enemy unit. When this unit has shot, or at the end of the phase (whichever comes first), resolve this unit\u2019s deadly demise roll, then this unit is removed from the battlefield."
            },
            {
                "name": "Vox-net",
                "description": "Each time this model issues an Order, it can issue it to an eligible unit up to 12\" away"
            },
            {
                "name": "Damaged: 1-4 Wounds Remaining",
                "description": "While this model has 1-4 wounds remaining, each time this model makes an attack, subtract 1 from the Hit roll."
            }
        ]
    },
    "Leman Russ Demolisher": {
        "stats": {
            "stat_movement": "10\"",
            "stat_toughness": 11,
            "stat_save": "2+",
            "stat_wounds": 13,
            "stat_leadership": "7+",
            "stat_oc": 3,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Demolisher battle cannon",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "D6+1",
                "skill": "4+",
                "strength": "14",
                "ap": "-3",
                "damage": "D6",
                "keywords": "Blast"
            },
            {
                "name": "Armoured tracks",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "6",
                "skill": "4+",
                "strength": "7",
                "ap": "0",
                "damage": "1",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Line-breaker",
                "description": "When making ranged attacks with its demolisher battle cannon, this model can target enemy units within Engagement Range of it (provided no other friendly units are also within Engagement Range of that enemy unit). In addition, when making ranged attacks, this model does not suffer the penalty to its Hit rolls for being within Engagement Range of one or more enemy units."
            },
            {
                "name": "Damaged: 1-4 Wounds Remaining",
                "description": "While this model has 1-4 wounds remaining, each time this model makes an attack, subtract 1 from the Hit roll."
            }
        ]
    },
    "Leman Russ Eradicator": {
        "stats": {
            "stat_movement": "10\"",
            "stat_toughness": 11,
            "stat_save": "2+",
            "stat_wounds": 13,
            "stat_leadership": "7+",
            "stat_oc": 3,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Eradicator nova cannon",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "D3+6",
                "skill": "4+",
                "strength": "7",
                "ap": "-1",
                "damage": "2",
                "keywords": "Blast, Ignores Cover"
            },
            {
                "name": "Armoured tracks",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "6",
                "skill": "4+",
                "strength": "7",
                "ap": "0",
                "damage": "1",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Urban Warfare",
                "description": "Each time a ranged attack targets this model, if this model has the Benefit of Cover against that attack, subtract 1 from the Damage characteristic of that attack."
            },
            {
                "name": "Damaged: 1-4 Wounds Remaining",
                "description": "While this model has 1-4 wounds remaining, each time this model makes an attack, subtract 1 from the Hit roll."
            }
        ]
    },
    "Leman Russ Executioner": {
        "stats": {
            "stat_movement": "10\"",
            "stat_toughness": 11,
            "stat_save": "2+",
            "stat_wounds": 13,
            "stat_leadership": "7+",
            "stat_oc": 3,
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
                "strength": "7",
                "ap": "0",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "\u27a4 Executioner plasma cannon - standard",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "D6+3",
                "skill": "4+",
                "strength": "7",
                "ap": "-2",
                "damage": "2",
                "keywords": "Blast"
            },
            {
                "name": "\u27a4 Executioner plasma cannon - supercharge",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "D6+3",
                "skill": "4+",
                "strength": "8",
                "ap": "-3",
                "damage": "3",
                "keywords": "Blast, Hazardous"
            }
        ],
        "abilities": [
            {
                "name": "Gung-ho Executioners",
                "description": "Each time this model makes an attack with its executioner plasma cannon that targets a unit that is Below Half-strength, add 1 to the Hit roll."
            },
            {
                "name": "Damaged: 1-4 Wounds Remaining",
                "description": "While this model has 1-4 wounds remaining, each time this model makes an attack, subtract 1 from the Hit roll."
            }
        ]
    },
    "Leman Russ Exterminator": {
        "stats": {
            "stat_movement": "10\"",
            "stat_toughness": 11,
            "stat_save": "2+",
            "stat_wounds": 13,
            "stat_leadership": "7+",
            "stat_oc": 3,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Exterminator autocannon",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "4",
                "skill": "4+",
                "strength": "9",
                "ap": "-1",
                "damage": "3",
                "keywords": "Rapid Fire 4, Twin-linked"
            },
            {
                "name": "Armoured tracks",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "6",
                "skill": "4+",
                "strength": "7",
                "ap": "0",
                "damage": "1",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Withering Hail",
                "description": "In your Shooting phase, after this model has shot, select one enemy unit hit by one or more of those attacks made with its exterminator autocannon. Until the end of the phase, each time a friendly Astra Militarum unit makes an attack that targets that enemy unit, improve the Armour Penetration characteristic of that attack by 1. The same enemy unit can only be affected by this ability once per phase."
            },
            {
                "name": "Damaged: 1-4 Wounds Remaining",
                "description": "While this model has 1-4 wounds remaining, each time this model makes an attack, subtract 1 from the Hit roll."
            }
        ]
    },
    "Leman Russ Punisher": {
        "stats": {
            "stat_movement": "10\"",
            "stat_toughness": 11,
            "stat_save": "2+",
            "stat_wounds": 13,
            "stat_leadership": "7+",
            "stat_oc": 3,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Punisher gatling cannon",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "20",
                "skill": "4+",
                "strength": "6",
                "ap": "0",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "Armoured tracks",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "6",
                "skill": "4+",
                "strength": "7",
                "ap": "0",
                "damage": "1",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Damaged: 1-4 Wounds Remaining",
                "description": "While this model has 1-4 wounds remaining, each time this model makes an attack, subtract 1 from the Hit roll."
            }
        ]
    },
    "Leman Russ Vanquisher": {
        "stats": {
            "stat_movement": "10\"",
            "stat_toughness": 11,
            "stat_save": "2+",
            "stat_wounds": 13,
            "stat_leadership": "7+",
            "stat_oc": 3,
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
                "strength": "7",
                "ap": "0",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "Vanquisher battle cannon",
                "weapon_type": "ranged",
                "range": "72\"",
                "attacks": "1",
                "skill": "4+",
                "strength": "18",
                "ap": "-4",
                "damage": "D6+6",
                "keywords": "Heavy"
            }
        ],
        "abilities": [
            {
                "name": "Tank-killer",
                "description": "Each time this model makes a ranged attack with its vanquisher battle cannon that targets a Monster or Vehicle unit, you can re-roll the Wound roll."
            },
            {
                "name": "Damaged: 1-4 Wounds Remaining",
                "description": "While this model has 1-4 wounds remaining, each time this model makes an attack, subtract 1 from the Hit roll."
            }
        ]
    },
    "Lord Marshal Dreir": {
        "stats": {
            "stat_movement": "10\"",
            "stat_toughness": 4,
            "stat_save": "4+",
            "stat_wounds": 6,
            "stat_leadership": "7+",
            "stat_oc": 2,
            "stat_invuln": "4+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Sabre of Sacrifice",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "6",
                "skill": "2+",
                "strength": "6",
                "ap": "-2",
                "damage": "1",
                "keywords": "Anti-Infantry 4+"
            },
            {
                "name": "Savage claws",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "2",
                "skill": "4+",
                "strength": "4",
                "ap": "-1",
                "damage": "1",
                "keywords": "Extra Attacks"
            },
            {
                "name": "Laspistol",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "3",
                "ap": "0",
                "damage": "1",
                "keywords": "Pistol"
            }
        ],
        "abilities": [
            {
                "name": "Tough to Kill",
                "description": "The first time this model is destroyed, roll one D6 at the end of the phase. On a 2+, set this model back up on the battlefield as close as possible to where it was destroyed and not within Engagement Range of any enemy units, with D3 wounds remaining."
            },
            {
                "name": "Leader",
                "description": "This model can be attached to the following unit:\n- Death Riders"
            },
            {
                "name": "Leading the Charge",
                "description": "Each time this model's unit makes a Charge move, until the end of the turn, melee weapons equipped by models in that unit have the [DEVASTATING WOUNDS] ability."
            }
        ]
    },
    "Lord Solar Leontus": {
        "stats": {
            "stat_movement": "12\"",
            "stat_toughness": 4,
            "stat_save": "3+",
            "stat_wounds": 8,
            "stat_leadership": "6+",
            "stat_oc": 2,
            "stat_invuln": "4+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Sol's Righteous Gaze",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "2",
                "skill": "2+",
                "strength": "8",
                "ap": "-2",
                "damage": "2",
                "keywords": "Pistol"
            },
            {
                "name": "Conquest",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "6",
                "skill": "2+",
                "strength": "6",
                "ap": "-2",
                "damage": "2",
                "keywords": "-"
            },
            {
                "name": "Konstantin's hooves",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "2",
                "skill": "4+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Extra Attacks"
            }
        ],
        "abilities": [
            {
                "name": "The Lord Solar",
                "description": "At the start of your Command phase, If this model is on the battlefield, you gain 1CP."
            },
            {
                "name": "The Collegiate Astrolex",
                "description": "After both players have deployed their armies, select up to three Astra Militarum units from your army and redeploy them. When doing so, you can set those units up in Strategic Reserves if you wish, regardless of how many units are already in Strategic Reserves."
            },
            {
                "name": "Supreme Commander",
                "description": "If this model is in your army, it must be your Warlord."
            },
            {
                "name": "Leader",
                "description": "This model can be attached to the following units:\n- ATTILAN ROUGH RIDERS\n- CADIAN SHOCK TROOPS\n- CATACHAN JUNGLE FIGHTERS\n- DEATH KORPS GRENADIER SQUAD\n- DEATH KORPS OF KRIEG\n- DEATH RIDERS\n- KASRKIN\n- KRIEG COMBAT ENGINEERS"
            }
        ]
    },
    "Manticore": {
        "stats": {
            "stat_movement": "10\"",
            "stat_toughness": 10,
            "stat_save": "3+",
            "stat_wounds": 11,
            "stat_leadership": "7+",
            "stat_oc": 3,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Storm eagle rockets",
                "weapon_type": "ranged",
                "range": "120\"",
                "attacks": "D6",
                "skill": "4+",
                "strength": "7",
                "ap": "-2",
                "damage": "3",
                "keywords": "Anti-Infantry 2+, Blast, Indirect Fire"
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
            }
        ],
        "abilities": [
            {
                "name": "Furious Barrage",
                "description": "In your Shooting phase, after this model has shot, select one enemy unit (excluding Monsters and Vehicles) that was hit by one or more of those attacks made with this model's storm eagle rockets. Until the start of your next Shooting phase, that enemy unit is staggered. While a unit is staggered, subtract 1 from the Objective Control characteristic of models in that unit (to a minimum of 1)."
            },
            {
                "name": "Damaged: 1-4 Wounds Remaining",
                "description": "While this model has 1-4 wounds remaining, each time this model makes an attack, subtract 1 from the Hit roll."
            }
        ]
    },
    "Militarum Tempestus Command Squad": {
        "stats": {
            "stat_movement": "6\"",
            "stat_toughness": 3,
            "stat_save": "4+",
            "stat_wounds": 1,
            "stat_leadership": "7+",
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
                "skill": "4+",
                "strength": "3",
                "ap": "0",
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
                "name": "\u27a4 Grenade launcher - frag",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "D3",
                "skill": "3+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Blast"
            },
            {
                "name": "\u27a4 Grenade launcher - krak",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "9",
                "ap": "-2",
                "damage": "D3",
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
                "name": "Hot-shot volley gun",
                "weapon_type": "ranged",
                "range": "30\"",
                "attacks": "2",
                "skill": "3+",
                "strength": "4",
                "ap": "-1",
                "damage": "1",
                "keywords": "Rapid Fire 2"
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
                "keywords": "Rapid Fire 1, Hazardous"
            },
            {
                "name": "Hot-shot lasgun",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "3",
                "ap": "-1",
                "damage": "1",
                "keywords": "Rapid Fire 1"
            },
            {
                "name": "Hot-shot laspistol",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "3",
                "ap": "-1",
                "damage": "1",
                "keywords": "Pistol"
            },
            {
                "name": "Tempestus dagger",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "3+",
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
            }
        ],
        "abilities": [
            {
                "name": "Leader",
                "description": "This unit can be attached to the following unit:\n- Tempestus Scions"
            },
            {
                "name": "Tempestor Prime",
                "description": "While this unit contains a Tempestor Prime, ranged weapons equipped by models in this unit have the [SUSTAINED HITS 1] ability."
            },
            {
                "name": "Regimental Standard",
                "description": "Add 1 to the Objective Control characteristic of models in the bearer\u2019s unit."
            },
            {
                "name": "Master Vox",
                "description": "Each time the Officer in the bearer\u2019s unit issues an Order, it can issue it to an eligible unit up to 24\" away."
            },
            {
                "name": "Medi-pack",
                "description": "At the start of your Command phase, if the bearer's unit is below its Starting Strength, you can return up to D3 destroyed Tempestus Scions models to this unit."
            },
            {
                "name": "Command Rod",
                "description": "While the bearer is leading a unit, that unit can be affected by up to two different Orders at the same time."
            }
        ]
    },
    "Ministorum Priest": {
        "stats": {
            "stat_movement": "6\"",
            "stat_toughness": 3,
            "stat_save": "6+",
            "stat_wounds": 3,
            "stat_leadership": "7+",
            "stat_oc": 1,
            "stat_invuln": "4+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Zealot's vindicator",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "3",
                "skill": "4+",
                "strength": "5",
                "ap": "-1",
                "damage": "2",
                "keywords": "-"
            },
            {
                "name": "Zealot's vindicator",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "D6",
                "skill": "N/A",
                "strength": "5",
                "ap": "0",
                "damage": "1",
                "keywords": "Ignores Cover, Torrent"
            },
            {
                "name": "Holy pistol",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "3",
                "skill": "4+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Pistol"
            },
            {
                "name": "Power weapon",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "3",
                "skill": "3+",
                "strength": "4",
                "ap": "-2",
                "damage": "1",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Holy Piety",
                "description": "Each time this model makes a melee attack, unless this model's unit is Battle-shocked, you can re-roll the Hit roll."
            },
            {
                "name": "War Hymns",
                "description": "While this model is leading a unit, melee weapons equipped by models in that unit have the [SUSTAINED HITS 1] ability."
            },
            {
                "name": "Leader",
                "description": "This model can be attached to the following units:\n- CADIAN SHOCK TROOPS\n- CATACHAN JUNGLE FIGHTERS\n- DEATH KORPS GRENADIER SQUAD\n- DEATH KORPS OF KRIEG\n- KASRKIN\n- KRIEG COMBAT ENGINEERS\n- TEMPESTUS SCIONS"
            }
        ]
    },
    "Nork Deddog": {
        "stats": {
            "stat_movement": "6\"",
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
                "name": "Huge knife",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "6",
                "skill": "2+",
                "strength": "8",
                "ap": "-1",
                "damage": "2",
                "keywords": "Devastating Wounds"
            },
            {
                "name": "Ripper gun",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "3",
                "skill": "3+",
                "strength": "5",
                "ap": "-1",
                "damage": "2",
                "keywords": "Rapid Fire 3"
            }
        ],
        "abilities": [
            {
                "name": "Thunderous Head-butt",
                "description": "Each time this model\u2019s unit is selected to fight, you can select one enemy unit within Engagement Range of this model and roll one D6: on a 2-5, that enemy unit suffers D3 mortal wounds; on a 6, that enemy unit suffers D3+3 mortal wounds."
            },
            {
                "name": "Loyal Protector",
                "description": "At the start of the Declare Battle Formations step, this model must join one Command Squad unit from your army (a Command Squad cannot have more than one Loyal Protector model joined to it). This model then counts as part of that Command Squad for the rest of the battle, and its Starting Strength is increased accordingly. If it is not possible to join this model to a Command Squad, it does not take part in the battle and counts as having been destroyed.\n\nWhile this model is joined to a unit, it can embark within any Transport that unit can embark within, and takes up the space of 3 models.\n\nThis model cannot be selected as your Warlord."
            },
            {
                "name": "Ogryn Bodyguard",
                "description": "While one or more Officer models are in the same unit as this model, those Officer models have the Feel No Pain 4+ ability"
            }
        ]
    },
    "Ogryn Bodyguard": {
        "stats": {
            "stat_movement": "6\"",
            "stat_toughness": 6,
            "stat_save": "5+",
            "stat_wounds": 6,
            "stat_leadership": "7+",
            "stat_oc": 1,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Close combat weapon",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "3+",
                "strength": "6",
                "ap": "0",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "Huge knife",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "6",
                "skill": "3+",
                "strength": "8",
                "ap": "-1",
                "damage": "2",
                "keywords": "-"
            },
            {
                "name": "Bullgryn maul",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "5",
                "skill": "3+",
                "strength": "7",
                "ap": "-1",
                "damage": "2",
                "keywords": "-"
            },
            {
                "name": "Ripper gun",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "3",
                "skill": "4+",
                "strength": "5",
                "ap": "-1",
                "damage": "2",
                "keywords": "Rapid Fire 3"
            },
            {
                "name": "Ripper gun",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "3+",
                "strength": "6",
                "ap": "-1",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "Grenadier gauntlet",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "D6",
                "skill": "4+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Blast"
            }
        ],
        "abilities": [
            {
                "name": "Loyal Protector",
                "description": "At the start of the Declare Battle Formations step, this model must join one Command Squad unit from your army (a Command Squad cannot have more than one Loyal Protector model joined to it). This model then counts as part of that Command Squad for the rest of the battle, and its Starting Strength is increased accordingly. If it is not possible to join this model to a Command Squad, it does not take part in the battle and counts as having been destroyed.\n\nWhile this model is joined to a unit, it can embark within any Transport that unit can embark within, and takes up the space of 3 models.\n\nThis model cannot be selected as your WARLORD and cannot be given Enhancements"
            },
            {
                "name": "Ogryn Bodyguard",
                "description": "While one or more Officer models are in the same unit as this model, those Officer models have the Feel No Pain 4+ ability"
            },
            {
                "name": "Slabshield",
                "description": "The bearer has a Wounds characteristic of 7."
            },
            {
                "name": "Brute Shield",
                "description": "The bearer has a 4+ invulnerable save."
            }
        ]
    },
    "Ogryn Squad": {
        "stats": {
            "stat_movement": "6\"",
            "stat_toughness": 6,
            "stat_save": "5+",
            "stat_wounds": 3,
            "stat_leadership": "7+",
            "stat_oc": 1,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Ripper gun",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "3",
                "skill": "4+",
                "strength": "5",
                "ap": "-1",
                "damage": "2",
                "keywords": "Rapid Fire 3"
            },
            {
                "name": "Ripper gun",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "3+",
                "strength": "6",
                "ap": "-1",
                "damage": "1",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Point-blank Barrage",
                "description": "Each time a model in this unit makes a ranged attack that targets the closest eligible target, improve the Armour Penetration characteristic of that attack by 1."
            }
        ]
    },
    "Primaris Psyker": {
        "stats": {
            "stat_movement": "6\"",
            "stat_toughness": 3,
            "stat_save": "5+",
            "stat_wounds": 3,
            "stat_leadership": "7+",
            "stat_oc": 1,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "\u27a4 Psychic maelstrom - witchfire",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "D6",
                "skill": "3+",
                "strength": "5",
                "ap": "-2",
                "damage": "1",
                "keywords": "Blast, Devastating Wounds, Psychic"
            },
            {
                "name": "\u27a4 Psychic maelstrom - focused witchfire",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "D6+1",
                "skill": "3+",
                "strength": "6",
                "ap": "-2",
                "damage": "2",
                "keywords": "Blast, Devastating Wounds, Hazardous, Psychic"
            },
            {
                "name": "Force weapon",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "3",
                "skill": "4+",
                "strength": "6",
                "ap": "-1",
                "damage": "D3",
                "keywords": "Psychic"
            },
            {
                "name": "Laspistol",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "3",
                "ap": "0",
                "damage": "1",
                "keywords": "Pistol"
            }
        ],
        "abilities": [
            {
                "name": "Psychic Barrier (Psychic)",
                "description": "At the start of your opponent\u2019s Shooting phase, you can roll one D6: on a 1, this Psyker\u2019s unit suffers D3 mortal wounds; on a 2+, until the end of the phase, models in this Psyker\u2019s unit have a 4+ invulnerable save."
            },
            {
                "name": "Leader",
                "description": "This model can be attached to the following units:\n- CADIAN SHOCK TROOPS\n- CATACHAN JUNGLE FIGHTERS\n- DEATH KORPS GRENADIER SQUAD\n- DEATH KORPS OF KRIEG\n- KASRKIN\n- KRIEG COMBAT ENGINEERS\n- TEMPESTUS SCIONS"
            },
            {
                "name": "Malign Wardings (Psychic)",
                "description": "While this model is leading a unit, models in that unit have the Feel No Pain 4+ ability against Psychic Attacks"
            }
        ]
    },
    "Ratlings": {
        "stats": {
            "stat_movement": "6\"",
            "stat_toughness": 2,
            "stat_save": "6+",
            "stat_wounds": 1,
            "stat_leadership": "8+",
            "stat_oc": 1,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Close combat weapon",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "1",
                "skill": "5+",
                "strength": "2",
                "ap": "0",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "Sniper rifle",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "4",
                "ap": "-2",
                "damage": "2",
                "keywords": "Heavy, Precision"
            },
            {
                "name": "Tankstopper rifle",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "9",
                "ap": "-3",
                "damage": "D6",
                "keywords": "Heavy"
            }
        ],
        "abilities": [
            {
                "name": "Shoot Sharp and Scarper",
                "description": "In your Shooting phase, after this unit has shot, if it is not within Engagement Range of any enemy units, it can make a Normal move as if it were your Movement phase. If it does, until the end of the turn, this unit is not eligible to declare a charge."
            },
            {
                "name": "Ratling Battlemutt",
                "description": "Once per battle, when this unit is selected to shoot, it can use this ability. If it does, until the end of the phase, ranged weapons equipped by models in this unit have the [LETHAL HITS] ability.\n\nDesigner\u2019s Note: Place a Ratling Battlemutt token next to the unit, removing it once this ability has been used."
            },
            {
                "name": "Demolition Gear",
                "description": "The bearer\u2019s unit has the Grenades keyword."
            }
        ]
    },
    "Rogal Dorn Battle Tank": {
        "stats": {
            "stat_movement": "10\"",
            "stat_toughness": 12,
            "stat_save": "2+",
            "stat_wounds": 18,
            "stat_leadership": "7+",
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
                "strength": "7",
                "ap": "0",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "Heavy stubber",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "3",
                "skill": "4+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Rapid Fire 3"
            },
            {
                "name": "Coaxial autocannon",
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
                "name": "Oppressor cannon",
                "weapon_type": "ranged",
                "range": "72\"",
                "attacks": "D6+3",
                "skill": "4+",
                "strength": "12",
                "ap": "-2",
                "damage": "3",
                "keywords": "Blast"
            },
            {
                "name": "Twin battle cannon",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "D6+3",
                "skill": "4+",
                "strength": "10",
                "ap": "-1",
                "damage": "3",
                "keywords": "Blast, Twin-linked"
            },
            {
                "name": "Castigator gatling cannon",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "12",
                "skill": "4+",
                "strength": "5",
                "ap": "0",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "Pulveriser cannon",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "D6",
                "skill": "4+",
                "strength": "9",
                "ap": "-3",
                "damage": "3",
                "keywords": "Blast"
            },
            {
                "name": "Multi-melta",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "2",
                "skill": "4+",
                "strength": "9",
                "ap": "-4",
                "damage": "D6",
                "keywords": "Melta 2"
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
                "keywords": "Sustained Hits 1"
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
            }
        ],
        "abilities": [
            {
                "name": "Ablative Plating",
                "description": "Once per battle, when an attack is allocated to this model, you change the Damage characteristic of that attack to 0."
            },
            {
                "name": "Damaged: 1-6 Wounds Remaining",
                "description": "While this model has 1-6 wounds remaining, each time this model makes an attack, subtract 1 from the Hit roll."
            }
        ]
    },
    "Rogal Dorn Commander": {
        "stats": {
            "stat_movement": "10\"",
            "stat_toughness": 12,
            "stat_save": "2+",
            "stat_wounds": 18,
            "stat_leadership": "7+",
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
                "strength": "7",
                "ap": "0",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "Heavy stubber",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "3",
                "skill": "4+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Rapid Fire 3"
            },
            {
                "name": "Castigator gatling cannon",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "12",
                "skill": "4+",
                "strength": "5",
                "ap": "0",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "Pulveriser cannon",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "D6",
                "skill": "4+",
                "strength": "9",
                "ap": "-3",
                "damage": "3",
                "keywords": "Blast"
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
                "name": "Multi-melta",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "2",
                "skill": "4+",
                "strength": "9",
                "ap": "-4",
                "damage": "D6",
                "keywords": "Melta 2"
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
                "keywords": "Sustained Hits 1"
            },
            {
                "name": "Coaxial autocannon",
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
                "name": "Oppressor cannon",
                "weapon_type": "ranged",
                "range": "72\"",
                "attacks": "D6+3",
                "skill": "4+",
                "strength": "12",
                "ap": "-2",
                "damage": "3",
                "keywords": "Blast"
            },
            {
                "name": "Twin battle cannon",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "D6+3",
                "skill": "4+",
                "strength": "10",
                "ap": "-1",
                "damage": "3",
                "keywords": "Blast, Twin-linked"
            }
        ],
        "abilities": [
            {
                "name": "Called Shots",
                "description": "Each time this model is selected to shoot, you can re-roll one Hit roll, you can re-roll one Wound roll and you can re-roll one Damage roll when resolving its attacks."
            },
            {
                "name": "Vox-net",
                "description": "Each time this model issues an Order, it can issue it to an eligible unit up to 12\" away"
            },
            {
                "name": "Damaged: 1-6 Wounds Remaining",
                "description": "While this model has 1-6 wounds remaining, each time this model makes an attack, subtract 1 from the Hit roll."
            }
        ]
    },
    "Scout Sentinels": {
        "stats": {
            "stat_movement": "10\"",
            "stat_toughness": 7,
            "stat_save": "3+",
            "stat_wounds": 7,
            "stat_leadership": "7+",
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
                "skill": "4+",
                "strength": "14",
                "ap": "-3",
                "damage": "D6",
                "keywords": "One Shot"
            },
            {
                "name": "Sentinel chainsaw",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "3",
                "skill": "4+",
                "strength": "6",
                "ap": "-1",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "Autocannon",
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
                "name": "Lascannon",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "1",
                "skill": "4+",
                "strength": "12",
                "ap": "-3",
                "damage": "D6+1",
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
                "name": "\u27a4 Plasma cannon - standard",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "D3",
                "skill": "4+",
                "strength": "7",
                "ap": "-2",
                "damage": "1",
                "keywords": "Blast"
            },
            {
                "name": "\u27a4 Plasma cannon - supercharge",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "D3",
                "skill": "4+",
                "strength": "8",
                "ap": "-3",
                "damage": "2",
                "keywords": "Blast, Hazardous"
            },
            {
                "name": "Multi-laser",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "4",
                "skill": "4+",
                "strength": "6",
                "ap": "0",
                "damage": "1",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Daring Recon",
                "description": "At the start of your Shooting phase, select one enemy unit within 18\" of and visible to this unit. Until the end of the phase, each time a friendly Astra Militarum model makes an attack that targets that unit, re-roll a Hit roll of 1."
            },
            {
                "name": "Signal Flares",
                "description": "In your Shooting phase, this unit can select one visible enemy unit within 12\". That enemy unit is designated:\n\u25aa While a unit is designated, that unit has +3\" detection range."
            }
        ]
    },
    "Shadowsword": {
        "stats": {
            "stat_movement": "12\"",
            "stat_toughness": 13,
            "stat_save": "2+",
            "stat_wounds": 24,
            "stat_leadership": "7+",
            "stat_oc": 8,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Volcano cannon",
                "weapon_type": "ranged",
                "range": "96\"",
                "attacks": "D3+1",
                "skill": "4+",
                "strength": "24",
                "ap": "-5",
                "damage": "12",
                "keywords": "Blast, Heavy"
            },
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
                "name": "Lascannon",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "1",
                "skill": "4+",
                "strength": "12",
                "ap": "-3",
                "damage": "D6+1",
                "keywords": "-"
            },
            {
                "name": "Twin heavy bolter",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "3",
                "skill": "4+",
                "strength": "5",
                "ap": "-1",
                "damage": "2",
                "keywords": "Sustained Hits 1, Twin-linked"
            }
        ],
        "abilities": [
            {
                "name": "Titan-killer",
                "description": "Each time this model makes a ranged attack with its volcano cannon that targets a Monster or Vehicle unit, that attack has the [DEVASTATING WOUNDS] ability."
            },
            {
                "name": "Damaged: 1-8 Wounds Remaining",
                "description": "While this model has 1-8 wounds remaining, subtract 4 from its Objective Control characteristic and each time this model makes an attack, subtract 1 from the Hit roll."
            }
        ]
    },
    "Sly Marbo": {
        "stats": {
            "stat_movement": "6\"",
            "stat_toughness": 3,
            "stat_save": "5+",
            "stat_wounds": 4,
            "stat_leadership": "7+",
            "stat_oc": 1,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Ripper pistol",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "3",
                "skill": "2+",
                "strength": "5",
                "ap": "-1",
                "damage": "2",
                "keywords": "Anti-Infantry 2+, Pistol, Precision"
            },
            {
                "name": "Envenomed blade",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "5",
                "skill": "2+",
                "strength": "5",
                "ap": "-1",
                "damage": "2",
                "keywords": "Anti-Infantry 2+, Precision"
            }
        ],
        "abilities": [
            {
                "name": "Like Fighting a Shadow",
                "description": "In your Shooting phase, after this model has shot, if it is not within Engagement Range of one or more enemy units, it can make a Normal move. If it does, until the end of the turn, this model is not eligible to declare a charge."
            },
            {
                "name": "One-man Army",
                "description": "Once per turn, in your opponent's Shooting phase, when an enemy unit makes a ranged attack that targets a friendly Regiment unit within 3\" of this model, after that enemy unit has shot, this model can shoot as if it were your Shooting phase, but it must target only that enemy unit when doing so, and can only do so if that enemy unit is an eligible target."
            }
        ]
    },
    "Stormlord": {
        "stats": {
            "stat_movement": "12\"",
            "stat_toughness": 13,
            "stat_save": "2+",
            "stat_wounds": 24,
            "stat_leadership": "7+",
            "stat_oc": 8,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Vulcan mega-bolter",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "20",
                "skill": "4+",
                "strength": "6",
                "ap": "-1",
                "damage": "2",
                "keywords": "Sustained Hits 1"
            },
            {
                "name": "Twin heavy bolter",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "3",
                "skill": "4+",
                "strength": "5",
                "ap": "-1",
                "damage": "2",
                "keywords": "Sustained Hits 1, Twin-linked"
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
                "keywords": "-"
            },
            {
                "name": "Heavy stubber",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "3",
                "skill": "4+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Rapid Fire 3"
            },
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
            }
        ],
        "abilities": [
            {
                "name": "Mount Up!",
                "description": "At the end of your opponent\u2019s Movement phase, if there are no models currently embarked within this Transport, you can select one friendly Astra Militarum Infantry unit (excluding Artillery units) that is wholly within 6\" of this Transport. Unless that unit is within Engagement Range of one or more enemy units, it can embark within this Transport."
            },
            {
                "name": "Damaged: 1-8 Wounds Remaining",
                "description": "While this model has 1-8 wounds remaining, subtract 4 from its Objective Control characteristic and each time this model makes an attack, subtract 1 from the Hit roll."
            }
        ]
    },
    "Stormsword": {
        "stats": {
            "stat_movement": "12\"",
            "stat_toughness": 13,
            "stat_save": "2+",
            "stat_wounds": 24,
            "stat_leadership": "7+",
            "stat_oc": 8,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Stormsword siege cannon",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "D6+6",
                "skill": "4+",
                "strength": "16",
                "ap": "-4",
                "damage": "D6+2",
                "keywords": "Blast, Ignores Cover"
            },
            {
                "name": "Twin heavy bolter",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "3",
                "skill": "4+",
                "strength": "5",
                "ap": "-1",
                "damage": "2",
                "keywords": "Sustained Hits 1, Twin-linked"
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
                "keywords": "-"
            },
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
            }
        ],
        "abilities": [
            {
                "name": "Concussive Wave",
                "description": "In your Shooting phase, just after selecting a target for this model\u2019s Stormsword siege cannon, roll one D6 for the target unit and every other unit within 3\" of that unit: on a 5+, the unit being rolled for is struck by a concussive wave. After this model has finished making its attacks against that target unit this phase, each unit struck by a concussive wave suffers D3 mortal wounds."
            },
            {
                "name": "Damaged: 1-8 Wounds Remaining",
                "description": "While this model has 1-8 wounds remaining, subtract 4 from its Objective Control characteristic and each time this model makes an attack, subtract 1 from the Hit roll."
            }
        ]
    },
    "Taurox": {
        "stats": {
            "stat_movement": "12\"",
            "stat_toughness": 8,
            "stat_save": "3+",
            "stat_wounds": 10,
            "stat_leadership": "7+",
            "stat_oc": 2,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Twin autocannon",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "2",
                "skill": "4+",
                "strength": "9",
                "ap": "-1",
                "damage": "3",
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
                "name": "Storm bolter",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "2",
                "skill": "4+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Rapid Fire 2"
            }
        ],
        "abilities": [
            {
                "name": "Rapid Deployment",
                "description": "Units can disembark from this Transport after it has Advanced. Units that do so count as having made a Normal move that phase, and cannot declare a charge in the same turn, but can otherwise act normally."
            }
        ]
    },
    "Taurox Prime": {
        "stats": {
            "stat_movement": "12\"",
            "stat_toughness": 8,
            "stat_save": "3+",
            "stat_wounds": 10,
            "stat_leadership": "7+",
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
                "name": "Storm bolter",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "2",
                "skill": "3+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Rapid Fire 2"
            }
        ],
        "abilities": [
            {
                "name": "Transport Support",
                "description": "In your Shooting phase, after this model has shot, select one enemy unit that was hit by one or more of those attacks. Until the end of the phase, each time a friendly model that disembarked from this Transport this turn makes an attack that targets that enemy unit, you can re-roll the Hit roll."
            }
        ]
    },
    "Tech-Priest Enginseer": {
        "stats": {
            "stat_movement": "6\"",
            "stat_toughness": 4,
            "stat_save": "3+",
            "stat_wounds": 3,
            "stat_leadership": "7+",
            "stat_oc": 1,
            "stat_invuln": "5+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Enginseer Axe",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "3",
                "skill": "4+",
                "strength": "6",
                "ap": "-2",
                "damage": "2",
                "keywords": "-"
            },
            {
                "name": "Mechanicus pistol",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "6",
                "ap": "0",
                "damage": "1",
                "keywords": "Devastating Wounds, Pistol"
            },
            {
                "name": "Servo-arm",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "1",
                "skill": "4+",
                "strength": "6",
                "ap": "-2",
                "damage": "2",
                "keywords": "Extra Attacks"
            }
        ],
        "abilities": [
            {
                "name": "Vengeance for the Omnissiah",
                "description": "If a friendly Astra Militarum Vehicle model is destroyed within 12\" of this model, until the end of the battle, this model\u2019s Enginseer axe has an Attacks characteristic of 6"
            },
            {
                "name": "Omnissiah\u2019s Blessing",
                "description": "In your Command phase, select one friendly Astra Militarum Vehicle model within 3\" of this model. That Vehicle model regains up to D3 lost wounds and, until the start of your next Command phase, that Vehicle model has a 4+ invulnerable save. Each model can only be selected for this ability once per turn."
            },
            {
                "name": "Enginseer",
                "description": "While this model is within 3\" of one or more friendly Astra Militarum Vehicle units, this model has the Lone Operative ability"
            },
            {
                "name": "Leader",
                "description": "This model can be attached to the following units:\n- Cadian Shock Troops\n- Catachan Jungle Fighters\n- Death Korps of Krieg\n- Kasrkin\n- Krieg Combat Engineers"
            }
        ]
    },
    "Tempestus Aquilons": {
        "stats": {
            "stat_movement": "6\"",
            "stat_toughness": 3,
            "stat_save": "4+",
            "stat_wounds": 1,
            "stat_leadership": "7+",
            "stat_oc": 1,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Hot-shot lascarbine",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "2",
                "skill": "3+",
                "strength": "3",
                "ap": "-1",
                "damage": "1",
                "keywords": "Assault"
            },
            {
                "name": "Close combat weapon",
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
                "name": "Hot-shot laspistol",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "3",
                "ap": "-1",
                "damage": "1",
                "keywords": "Pistol"
            },
            {
                "name": "Hot-shot long las",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "4",
                "ap": "-2",
                "damage": "3",
                "keywords": "Heavy, Precision"
            },
            {
                "name": "\u27a4 Plasma carbine - standard",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "2",
                "skill": "3+",
                "strength": "7",
                "ap": "-2",
                "damage": "1",
                "keywords": "Assault"
            },
            {
                "name": "\u27a4 Plasma carbine - supercharge",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "2",
                "skill": "3+",
                "strength": "8",
                "ap": "-3",
                "damage": "2",
                "keywords": "Assault, Hazardous"
            },
            {
                "name": "Melta carbine",
                "weapon_type": "ranged",
                "range": "10\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "9",
                "ap": "-4",
                "damage": "D6",
                "keywords": "Assault, Melta 2"
            },
            {
                "name": "Chainsword",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
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
                "attacks": "3",
                "skill": "4+",
                "strength": "4",
                "ap": "-2",
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
                "name": "Sentry flamer",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "D6+3",
                "skill": "N/A",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Ignores Cover, Torrent"
            },
            {
                "name": "Sentry hot-shot volley gun",
                "weapon_type": "ranged",
                "range": "30\"",
                "attacks": "4",
                "skill": "4+",
                "strength": "4",
                "ap": "-1",
                "damage": "1",
                "keywords": "Rapid Fire 4"
            },
            {
                "name": "\u27a4 Sentry grenade launcher - frag",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "D3+3",
                "skill": "4+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Blast"
            },
            {
                "name": "\u27a4 Sentry grenade launcher - krak",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "2",
                "skill": "4+",
                "strength": "9",
                "ap": "-2",
                "damage": "D3",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Precision Drop",
                "description": "In your Movement phase, when this unit is set up on the battlefield using the Deep Strike ability, it can perform a precision drop. If it does, this unit can be set up anywhere on the battlefield that is more than 6\" horizontally away from all enemy units, but until the end of the turn, it is not eligible to declare a charge."
            },
            {
                "name": "Servo-sentry",
                "description": "When this unit is set up on the battlefield using the Deep Strike ability, the Tempestor Aquilon can shoot with its sentry weapon (its sentry flamer, sentry grenade launcher or sentry hot-shot volley gun)."
            },
            {
                "name": "Signal Flares",
                "description": "In your Shooting phase, this unit can select one visible enemy unit within 12\". That enemy unit is designated:\n\u25aa While a unit is designated, that unit has +3\" detection range."
            }
        ]
    },
    "Tempestus Scions": {
        "stats": {
            "stat_movement": "6\"",
            "stat_toughness": 3,
            "stat_save": "4+",
            "stat_wounds": 1,
            "stat_leadership": "7+",
            "stat_oc": 1,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Hot-shot laspistol",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "3",
                "ap": "-1",
                "damage": "1",
                "keywords": "Pistol"
            },
            {
                "name": "Close combat weapon",
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
                "name": "Hot-shot lasgun",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "3",
                "ap": "-1",
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
                "name": "\u27a4 Grenade launcher - frag",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "D3",
                "skill": "3+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Blast"
            },
            {
                "name": "\u27a4 Grenade launcher - krak",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "9",
                "ap": "-2",
                "damage": "D3",
                "keywords": "-"
            },
            {
                "name": "Hot-shot volley gun",
                "weapon_type": "ranged",
                "range": "30\"",
                "attacks": "2",
                "skill": "3+",
                "strength": "4",
                "ap": "-1",
                "damage": "1",
                "keywords": "Rapid Fire 2"
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
                "keywords": "Rapid Fire 1, Hazardous"
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
                "name": "Chainsword",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "4+",
                "strength": "3",
                "ap": "0",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "Power fist",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "3",
                "skill": "4+",
                "strength": "6",
                "ap": "-2",
                "damage": "2",
                "keywords": "-"
            },
            {
                "name": "Power weapon",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "3",
                "skill": "4+",
                "strength": "4",
                "ap": "-2",
                "damage": "1",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Storm Troopers",
                "description": "Each time a model in this unit makes an attack, re-roll a Wound roll of 1. If the target of that attack is an enemy unit within range of an objective marker, you can re-roll the Wound roll instead."
            },
            {
                "name": "Unit Composition",
                "description": "This unit can have up to two Leader units attached to it, provided no more than one of those units is a Command Squad unit. If it does, and this Bodyguard unit is destroyed, the Leader units attached to it become separate units, with their original Starting Strengths."
            },
            {
                "name": "Vox-caster",
                "description": "Each time you target the bearer\u2019s unit with a Stratagem, roll one D6, adding 1 to the result if there are one or more friendly Officer models within 6\": on a 5+, you gain 1CP"
            }
        ]
    },
    "Ursula Creed": {
        "stats": {
            "stat_movement": "6\"",
            "stat_toughness": 3,
            "stat_save": "4+",
            "stat_wounds": 4,
            "stat_leadership": "7+",
            "stat_oc": 1,
            "stat_invuln": "5+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Duty and Vengeance",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "4",
                "skill": "3+",
                "strength": "5",
                "ap": "-2",
                "damage": "1",
                "keywords": "Pistol"
            },
            {
                "name": "Power weapon",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "3+",
                "strength": "4",
                "ap": "-2",
                "damage": "1",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Lord Castellan",
                "description": "While this model is leading a unit, that unit can be affected by up to two different Orders at the same time."
            },
            {
                "name": "Tactical Genius",
                "description": "Once per battle round, one unit from your army with this ability can use it when a friendly Regiment unit within 12\" of that model is targeted with a Stratagem. If it does, reduce the CP cost of that usage of that Stratagem by 1 CP."
            },
            {
                "name": "Leader",
                "description": "This model can be attached to the following units:\n- Cadian Shock Troops\n- Kasrkin"
            }
        ]
    },
    "Valkyrie": {
        "stats": {
            "stat_movement": "14\"",
            "stat_toughness": 10,
            "stat_save": "2+",
            "stat_wounds": 14,
            "stat_leadership": "7+",
            "stat_oc": None,
            "stat_invuln": "",
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
                "name": "Heavy bolter",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "3",
                "skill": "4+",
                "strength": "5",
                "ap": "-1",
                "damage": "2",
                "keywords": "Sustained Hits 1"
            }
        ],
        "abilities": [
            {
                "name": "Airborne Insertion",
                "description": "At the end of your opponent\u2019s Movement phase, one or more units embarked within this Transport can disembark from it."
            },
            {
                "name": "Damaged: 1-5 Wounds Remaining",
                "description": "While this model has 1-5 wounds remaining, each time this model makes an attack, subtract 1 from the Hit roll."
            }
        ]
    },
    "Wyvern": {
        "stats": {
            "stat_movement": "10\"",
            "stat_toughness": 9,
            "stat_save": "3+",
            "stat_wounds": 11,
            "stat_leadership": "7+",
            "stat_oc": 3,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Wyvern quad stormshard mortar",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "2D6",
                "skill": "4+",
                "strength": "5",
                "ap": "0",
                "damage": "1",
                "keywords": "Blast, Indirect Fire, Twin-linked"
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
            }
        ],
        "abilities": [
            {
                "name": "Suppression Bombardment",
                "description": "In your Shooting phase, after this model has shot, select one enemy unit (excluding Monsters and Vehicles) that was hit by one or more attacks made with this model\u2019s Wyvern quad stormshard mortar. Unit the start of your next Shooting phase, that enemy unit is suppressed. While a unit is suppressed, each time a model in that unit makes an attack, subtract 1 from the Hit roll."
            }
        ]
    }
}


class Command(BaseCommand):
    """Refresh Astra Militarum stat lines, weapon profiles, and abilities from BSData."""

    help = 'Refresh 11th Edition stats/weapons/abilities for Astra Militarum units.'

    def add_arguments(self, parser):
        """Add --dry-run flag."""
        parser.add_argument(
            '--dry-run', action='store_true',
            help='Preview changes without writing to the database.',
        )

    def handle(self, *args, **options):
        """Iterate MILITARUM_DATASHEETS and refresh each unit's datasheet data."""
        dry_run = options['dry_run']
        updated = 0
        skipped = 0

        with transaction.atomic():
            for name, payload in MILITARUM_DATASHEETS.items():
                try:
                    unit = UnitType.objects.get(name=name, faction__name='Astra Militarum')
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
