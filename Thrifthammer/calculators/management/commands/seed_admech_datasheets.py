"""
Management command: seed_admech_datasheets

Refreshes stat lines, weapon profiles, and abilities for all Adeptus
Mechanicus units using 11th Edition data sourced from BSData/wh40k-11e
("Imperium - Adeptus Mechanicus.json") -- the same source used by
seed_admech_points.py.

Usage:
    python manage.py seed_admech_datasheets
    python manage.py seed_admech_datasheets --dry-run

Notes:
- Does NOT touch points_cost or category -- those are handled entirely by
  seed_admech_points.py. This command only refreshes stat_* fields,
  WeaponProfile rows, and UnitAbility rows.
- Per-field safety rule: a unit's stats/weapons/abilities are only
  overwritten when BSData actually has that data for it. If extraction
  found nothing for a given field, the existing DB value/rows are left
  untouched rather than blanked.
- Weapon profiles list EVERY weapon option reachable for a unit (not a
  guessed "default" loadout), each as its own row -- same as Orks/Grey
  Knights. Ability text has markdown syntax (**bold**, ^^highlight^^,
  *italic*) and stray non-breaking-space/replacement-character artifacts
  stripped at generation time.
- AdMech-specific extraction gotcha (new this faction): several units'
  weapon options live in the unit entry's own top-level "selectionEntries"
  list (embedded model/upgrade sub-entries), not under
  "selectionEntryGroups" like Orks/Grey Knights -- the tree walker was
  extended to also recurse into that list. Also, one unit (Ironstrider
  Ballistarii) has its stat profile defined at the catalogue-level
  "sharedProfiles" list rather than embedded on the entry -- the walker
  falls back to a name-matched lookup there when the normal recursive
  search finds nothing.
- All 33 active units resolved cleanly: 0 missing stats, 0 missing
  weapons, 0 missing abilities.
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from calculators.models import UnitAbility, UnitType, WeaponProfile

# (name -> {stats?, weapons?, abilities?}). Missing keys mean "no data
# found for this field -- leave existing DB data untouched."
ADMECH_DATASHEETS = {
    "Adeptus Mechanicus Archaeopter Fusilave": {
        "stats": {
            "stat_movement": "-",
            "stat_toughness": 9,
            "stat_save": "3+",
            "stat_wounds": 10,
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
                "name": "Cognis heavy stubber array",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "9",
                "skill": "4+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Rapid Fire 9, Sustained Hits 1, Twin-linked"
            }
        ],
        "abilities": [
            {
                "name": "Bomb Rack",
                "description": "At the end of your opponent\u2019s Fight phase, select one visible enemy unit (excluding Lone Operative units) within 24\" of this unit, and roll six D6 for that unit: for each 4+, that unit suffers 1 mortal wound."
            },
            {
                "name": "Chaff Launcher",
                "description": "The bearer has the Smoke keyword."
            },
            {
                "name": "Command Uplink",
                "description": "Each time you select the bearer\u2019s unit as the target of a Stratagem, roll one D6: on a 5+, you gain 1CP."
            }
        ]
    },
    "Adeptus Mechanicus Archaeopter Stratoraptor": {
        "stats": {
            "stat_movement": "-",
            "stat_toughness": 9,
            "stat_save": "3+",
            "stat_wounds": 10,
            "stat_leadership": "7+",
            "stat_oc": None,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Cognis heavy stubber",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "3",
                "skill": "4+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Rapid Fire 3, Sustained Hits 1"
            },
            {
                "name": "Heavy phosphor blaster",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "3",
                "skill": "4+",
                "strength": "6",
                "ap": "-1",
                "damage": "2",
                "keywords": "Ignores Cover"
            },
            {
                "name": "Twin cognis lascannon",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "1",
                "skill": "4+",
                "strength": "12",
                "ap": "-3",
                "damage": "D6+1",
                "keywords": "Sustained hits 1, Twin-linked"
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
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Strafing Run",
                "description": "Each time this model makes a ranged attack that targets an enemy unit (excluding units that can Fly), add 1 to the Hit roll."
            },
            {
                "name": "Chaff Launcher",
                "description": "The bearer has the Smoke keyword."
            },
            {
                "name": "Command Uplink",
                "description": "Each time you select the bearer\u2019s unit as the target of a Stratagem, roll one D6: on a 5+, you gain 1CP."
            }
        ]
    },
    "Adeptus Mechanicus Archaeopter Transvector": {
        "stats": {
            "stat_movement": "14\"",
            "stat_toughness": 9,
            "stat_save": "3+",
            "stat_wounds": 10,
            "stat_leadership": "7+",
            "stat_oc": 0,
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
                "name": "Cognis heavy stubber array",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "9",
                "skill": "4+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Rapid Fire 9, Sustained Hits 1, Twin-linked"
            }
        ],
        "abilities": [
            {
                "name": "Aerial Deployment",
                "description": "In your first Movement phase, this unit can make an ingress move."
            },
            {
                "name": "Chaff Launcher",
                "description": "The bearer has the Smoke keyword."
            },
            {
                "name": "Command Uplink",
                "description": "Each time you select the bearer\u2019s unit as the target of a Stratagem, roll one D6: on a 5+, you gain 1CP."
            }
        ]
    },
    "Adeptus Mechanicus Belisarius Cawl": {
        "stats": {
            "stat_movement": "8\"",
            "stat_toughness": 8,
            "stat_save": "2+",
            "stat_wounds": 10,
            "stat_leadership": "6+",
            "stat_oc": 3,
            "stat_invuln": "4+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Arc Scourge",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "2+",
                "strength": "5",
                "ap": "-1",
                "damage": "1",
                "keywords": "Anti-Vehicle 4+, Devastating Wounds, Extra Attacks"
            },
            {
                "name": "Cawl's Omnissian axe",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "2+",
                "strength": "8",
                "ap": "-2",
                "damage": "2",
                "keywords": "-"
            },
            {
                "name": "Mechadendrite hive",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "2D6",
                "skill": "3+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Extra Attacks"
            },
            {
                "name": "Solar atomiser",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "3",
                "skill": "2+",
                "strength": "14",
                "ap": "-4",
                "damage": "D6",
                "keywords": "Melta 3"
            }
        ],
        "abilities": [
            {
                "name": "Canticles of the Omnissiah",
                "description": "At the start of your Command phase, select one of the abilities in the Canticles of the Omnissiah section. Until the start of your next Command phase, this model has that ability.\n\nInvocation of Machine Vengeance (Aura): At the start of your Command phase, select one unit from your opponent\u2019s army. Until the start of your next Command phase, that enemy unit is your Machine Vengeance target. Each time a model in a friendly Adeptus Mechanicus unit makes an attack that targets your Machine Vengeance target, you can re-roll the Hit roll.\n\nMantra of Discipline: This model has the Battleline keyword and has the following ability:\nBinharic Courage (Aura): While a friendly Adeptus Mechanicus unit is within 6\" of this model, add 1 to the Objective Control characteristic of models in that unit and each time you take a Battle-shock or Leadership test for that unit, add 1 to that test.\u2019\n\nShroudpsalm (Aura): While a friendly Adeptus Mechanicus unit is within 6\" of this model, that unit has the Stealth ability."
            },
            {
                "name": "Mechanicus Bodyguard",
                "description": "While this model is within 3\" of one or more other friendly Adeptus Mechanicus units, this model has the Lone Operative ability."
            },
            {
                "name": "Self-repair Mechanisms",
                "description": "At the start of your Command phase, this model regains up to D3 lost wounds."
            },
            {
                "name": "Supreme Commander",
                "description": "If this model is in your army, it must be your Warlord."
            }
        ]
    },
    "Adeptus Mechanicus Fulgurite Electro-Priests": {
        "stats": {
            "stat_movement": "6\"",
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
                "name": "Electroleech stave",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "2",
                "skill": "3+",
                "strength": "6",
                "ap": "-1",
                "damage": "2",
                "keywords": "Devastating Wounds"
            }
        ],
        "abilities": [
            {
                "name": "Electro-Infusion",
                "description": "While a Character model is leading this unit, each time an attack targets this unit, subtract 1 from the Wound roll."
            }
        ]
    },
    "Adeptus Mechanicus Kastelan Robots": {
        "stats": {
            "stat_movement": "6\"",
            "stat_toughness": 9,
            "stat_save": "2+",
            "stat_wounds": 7,
            "stat_leadership": "7+",
            "stat_oc": 2,
            "stat_invuln": "5+",
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
                "name": "Twin Kastelan phosphor blaster",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "3",
                "skill": "4+",
                "strength": "6",
                "ap": "-1",
                "damage": "1",
                "keywords": "Ignores Cover, Twin-linked"
            },
            {
                "name": "Twin Kastelan fist",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "4+",
                "strength": "12",
                "ap": "-2",
                "damage": "3",
                "keywords": "Twin-linked"
            },
            {
                "name": "Kastelan fist",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "4+",
                "strength": "12",
                "ap": "-2",
                "damage": "3",
                "keywords": "-"
            },
            {
                "name": "Kastelan phosphor blaster",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "3",
                "skill": "4+",
                "strength": "6",
                "ap": "-1",
                "damage": "1",
                "keywords": "Ignores Cover"
            },
            {
                "name": "Incendine combustor",
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
                "name": "Heavy phosphor blaster",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "3",
                "skill": "4+",
                "strength": "6",
                "ap": "-1",
                "damage": "2",
                "keywords": "Ignores Cover"
            }
        ],
        "abilities": [
            {
                "name": "Robotic Bodyguard",
                "description": "While a Cybernetica Datasmith model is leading this unit, that model has the Feel No Pain 4+ ability."
            },
            {
                "name": "Repulsor Grid",
                "description": "When an enemy unit targets this unit with ranged attacks, until that enemy unit has shot, when this unit makes a save roll:\n- On an unmodified 6, that enemy unit suffers 1 mortal wound after that enemy unit has shot."
            }
        ]
    },
    "Adeptus Mechanicus Kataphron Breachers": {
        "stats": {
            "stat_movement": "5\"",
            "stat_toughness": 7,
            "stat_save": "3+",
            "stat_wounds": 3,
            "stat_leadership": "7+",
            "stat_oc": 1,
            "stat_invuln": "6+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Arc claw",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "4+",
                "strength": "5",
                "ap": "-1",
                "damage": "1",
                "keywords": "Anti-Vehicle 4+"
            },
            {
                "name": "Heavy arc rifle",
                "weapon_type": "ranged",
                "range": "30\"",
                "attacks": "2",
                "skill": "4+",
                "strength": "8",
                "ap": "-2",
                "damage": "3",
                "keywords": "Anti-Vehicle 4+, Rapid Fire 2"
            },
            {
                "name": "Hydraulic claw",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "2",
                "skill": "4+",
                "strength": "8",
                "ap": "-2",
                "damage": "3",
                "keywords": "-"
            },
            {
                "name": "Torsion cannon",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "D3",
                "skill": "4+",
                "strength": "6",
                "ap": "-2",
                "damage": "2",
                "keywords": "Anti-Infantry 2+, Blast"
            }
        ],
        "abilities": [
            {
                "name": "Breaching Command",
                "description": "Each time a model in this unit makes an attack, re-roll a Hit roll of 1. While this unit is within 6\u201d of one or more friendly Adeptus Mechanicus Battleline units, you can re-roll the Hit roll instead."
            }
        ]
    },
    "Adeptus Mechanicus Pteraxii Skystalkers": {
        "stats": {
            "stat_movement": "12\"",
            "stat_toughness": 4,
            "stat_save": "4+",
            "stat_wounds": 2,
            "stat_leadership": "7+",
            "stat_oc": 1,
            "stat_invuln": "5+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Flechette blaster",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "5",
                "skill": "4+",
                "strength": "3",
                "ap": "0",
                "damage": "1",
                "keywords": "Pistol"
            },
            {
                "name": "Taser goad",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "3",
                "skill": "4+",
                "strength": "6",
                "ap": "0",
                "damage": "1",
                "keywords": "Sustained Hits 2"
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
                "name": "Flechette carbine",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "6",
                "skill": "4+",
                "strength": "3",
                "ap": "0",
                "damage": "1",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Ride the Thermals",
                "description": "In your Shooting phase, after this unit has shot, if it is not within Engagement Range of one or more enemy units, it can do one of the following:\n- Make a Normal move of up to 6\".\n- Make a Normal move of up to 12\", provided every model in this unit ends that move wholly within 6\" of one or more friendly Adeptus Mechanicus Battleline units.\n\nIn either case, if it does, until the end of the turn, this unit is not eligible to declare a charge."
            }
        ]
    },
    "Adeptus Mechanicus Pteraxii Sterylizors": {
        "stats": {
            "stat_movement": "12\"",
            "stat_toughness": 4,
            "stat_save": "4+",
            "stat_wounds": 2,
            "stat_leadership": "7+",
            "stat_oc": 1,
            "stat_invuln": "5+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Flechette blaster",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "5",
                "skill": "4+",
                "strength": "3",
                "ap": "0",
                "damage": "1",
                "keywords": "Pistol"
            },
            {
                "name": "Taser goad",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "3",
                "skill": "4+",
                "strength": "6",
                "ap": "0",
                "damage": "1",
                "keywords": "Sustained Hits 2"
            },
            {
                "name": "Pteraxii talons",
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
                "name": "Phosphor torch",
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
                "name": "Searing Conflagaration",
                "description": "Each time a model in this unit makes an attack with a phosphor torch that targets an enemy unit within range of an objective marker, re-roll a Wound roll of 1. If this unit is also within 6\" of one or more friendly Adeptus Mechanicus Battleline units, each time such an attack targets such a unit, you can re-roll the Wound roll instead."
            }
        ]
    },
    "Adeptus Mechanicus Serberys Raiders": {
        "stats": {
            "stat_movement": "12\"",
            "stat_toughness": 4,
            "stat_save": "4+",
            "stat_wounds": 2,
            "stat_leadership": "7+",
            "stat_oc": 2,
            "stat_invuln": "5+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Galvanic carbine",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "3",
                "skill": "4+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Devastating Wounds"
            },
            {
                "name": "Cavalry sabre & clawed limbs",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "4+",
                "strength": "4",
                "ap": "-1",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "Mechanicus pistol",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "1",
                "skill": "4+",
                "strength": "6",
                "ap": "-1",
                "damage": "1",
                "keywords": "Devastating Wounds, Pistol"
            }
        ],
        "abilities": [
            {
                "name": "Tactica Obliqua",
                "description": "In your opponent's Movement phase, if an enemy unit ends a move within 8\u201d of this unit, if this unit is not within Engagement Range of one or more enemy units, it can do one of the following:\n- Make a Normal move of up to D6\".\n- Make a Normal move of up to 6\", provided every model in this unit ends that move wholly within 6\" of one or more friendly Adeptus Mechanicus Battleline units."
            },
            {
                "name": "Enhanced data-tether",
                "description": "Each time you select the bearer\u2019s unit as the target of a Stratagem, roll one D6: on a 5+, you gain 1CP."
            },
            {
                "name": "Stealth-screened Cybercanids",
                "description": "This unit has Lone Operative 15\"."
            }
        ]
    },
    "Adeptus Mechanicus Serberys Sulphurhounds": {
        "stats": {
            "stat_movement": "12\"",
            "stat_toughness": 4,
            "stat_save": "4+",
            "stat_wounds": 2,
            "stat_leadership": "7+",
            "stat_oc": 2,
            "stat_invuln": "5+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Cavalry arc maul",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "1",
                "skill": "4+",
                "strength": "5",
                "ap": "-1",
                "damage": "1",
                "keywords": "Anti-Vehicle 4+, Devastating Wounds, Extra Attacks"
            },
            {
                "name": "Clawed limbs",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "4+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "Mechanicus pistol",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "1",
                "skill": "4+",
                "strength": "6",
                "ap": "-1",
                "damage": "1",
                "keywords": "Devastating Wounds, Pistol"
            },
            {
                "name": "Sulphur breath",
                "weapon_type": "ranged",
                "range": "9\"",
                "attacks": "D6",
                "skill": "N/A",
                "strength": "3",
                "ap": "-1",
                "damage": "1",
                "keywords": "Ignores Cover, Pistol, Torrent"
            },
            {
                "name": "Phosphor pistol",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "1",
                "skill": "4+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Ignores Cover, Pistol"
            },
            {
                "name": "Phosphor blast carbine",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "D6",
                "skill": "4+",
                "strength": "6",
                "ap": "0",
                "damage": "1",
                "keywords": "Blast, Ignores cover"
            }
        ],
        "abilities": [
            {
                "name": "Line-breakers",
                "description": "Each time this unit ends a Charge move, select one enemy unit within Engagement Range of it and roll one D6 for each model in this unit that is within Engagement Range of that enemy unit, adding 2 to the result if this unit started its Charge move within 6\" of one or more friendly Adeptus Mechanicus Battleline units. For each 4+, that enemy unit suffers 1 mortal wound."
            }
        ]
    },
    "Adeptus Mechanicus Sicarian Infiltrators": {
        "stats": {
            "stat_movement": "8\"",
            "stat_toughness": 4,
            "stat_save": "4+",
            "stat_wounds": 2,
            "stat_leadership": "7+",
            "stat_oc": 1,
            "stat_invuln": "5+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Power weapon",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "4+",
                "strength": "4",
                "ap": "-2",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "Stubcarbine",
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
                "name": "Flechette blaster",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "5",
                "skill": "4+",
                "strength": "3",
                "ap": "0",
                "damage": "1",
                "keywords": "Pistol"
            },
            {
                "name": "Taser goad",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "3",
                "skill": "4+",
                "strength": "6",
                "ap": "-1",
                "damage": "1",
                "keywords": "Sustained Hits 2"
            }
        ],
        "abilities": [
            {
                "name": "Neurostatic Interference (Aura)",
                "description": "While an enemy unit is within 6\" of this unit, each time a Battle-shock or Leadership test is taken for that unit, subtract 1 from that test. While this unit is within 6\" of one or more friendly Adeptus Mechanicus Battleline units, subtract 2 from that test instead."
            }
        ]
    },
    "Adeptus Mechanicus Sicarian Ruststalkers": {
        "stats": {
            "stat_movement": "8\"",
            "stat_toughness": 4,
            "stat_save": "4+",
            "stat_wounds": 2,
            "stat_leadership": "7+",
            "stat_oc": 1,
            "stat_invuln": "5+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Transonic razor & chordclaw",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "3",
                "skill": "4+",
                "strength": "5",
                "ap": "-2",
                "damage": "2",
                "keywords": "Anti-Infantry 3+, Precision"
            },
            {
                "name": "Transonic blades",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "5",
                "skill": "4+",
                "strength": "5",
                "ap": "-1",
                "damage": "1",
                "keywords": "Devastating Wounds, Precision"
            },
            {
                "name": "Transonic blades & chordclaw",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "5",
                "skill": "4+",
                "strength": "5",
                "ap": "-2",
                "damage": "1",
                "keywords": "Anti-Infantry 3+, Devastating Wounds, Precision"
            }
        ],
        "abilities": [
            {
                "name": "Optimised Gait",
                "description": "Add 1 to Advance and Charge rolls made for this unit. While this unit is within 6\" of one or more friendly Adeptus Mechanicus Battleline units, add 2 to Advance and Charge rolls made for this unit instead."
            }
        ]
    },
    "Adeptus Mechanicus Skitarii Marshal": {
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
                "name": "Control stave",
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
                "name": "Mechanicus pistol",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "1",
                "skill": "4+",
                "strength": "6",
                "ap": "-1",
                "damage": "1",
                "keywords": "Devastating Wounds, Pistol"
            }
        ],
        "abilities": [
            {
                "name": "Support",
                "description": "This model can be attached to the following units:\n- Skitarii Rangers\n- Skitarii Vanguard"
            },
            {
                "name": "Control Edict",
                "description": "While this model is leading a unit, each time a model in that unit makes an attack, you can re-roll the Hit roll."
            },
            {
                "name": "Servo-skull Uplink",
                "description": "Once per battle, at the start of any phase, you can select one friendly Skitarii unit that is Battle-shocked and within 6\" of this model. That unit is no longer Battle-shocked."
            }
        ]
    },
    "Adeptus Mechanicus Skorpius Disintegrator": {
        "stats": {
            "stat_movement": "10\"",
            "stat_toughness": 10,
            "stat_save": "2+",
            "stat_wounds": 12,
            "stat_leadership": "7+",
            "stat_oc": 3,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Cognis heavy stubber",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "3",
                "skill": "4+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Rapid Fire 3, Sustained Hits 1"
            },
            {
                "name": "Disruptor missile launcher",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "3",
                "skill": "4+",
                "strength": "9",
                "ap": "-2",
                "damage": "D6",
                "keywords": "Twin-linked"
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
                "keywords": "-"
            },
            {
                "name": "Belleros energy cannon",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "2D6",
                "skill": "4+",
                "strength": "7",
                "ap": "-2",
                "damage": "1",
                "keywords": "Blast, Indirect Fire"
            },
            {
                "name": "Ferrumite cannon",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "3",
                "skill": "4+",
                "strength": "12",
                "ap": "-3",
                "damage": "D6+1",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Broad spectrum data-tether",
                "description": "Each time you select the bearer as the target of a Stratagem, roll one D6: on a 5+, you gain 1CP."
            },
            {
                "name": "Blistering Salvoes",
                "description": "Each time this model makes an attack with a belleros energy cannon that targets an Infantry unit, add 1 to the Hit roll. Each time this model makes an attack with a ferrumite cannon that targets a Monster or Vehicle unit, add 1 to the Hit roll."
            },
            {
                "name": "Damaged: 1-4 wounds remaining",
                "description": "While this model has 1-4 wounds remaining, each time this model makes an attack, subtract 1 from the Hit roll."
            }
        ]
    },
    "Adeptus Mechanicus Skorpius Dunerider": {
        "stats": {
            "stat_movement": "12\"",
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
                "name": "Cognis heavy stubber array",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "9",
                "skill": "4+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Rapid Fire 9, Sustained Hits 1, Twin-linked"
            }
        ],
        "abilities": [
            {
                "name": "Broad spectrum data-tether",
                "description": "Each time you select the bearer as the target of a Stratagem, roll one D6: on a 5+, you gain 1CP."
            },
            {
                "name": "Fire Support",
                "description": "In your Shooting phase, after this model has shot, select one enemy unit it scored one or more hits against this phase. Until the end of the phase, each time a friendly model that disembarked from this Transport this turn makes an attack that targets that enemy unit, you can re-roll the Wound roll."
            }
        ]
    },
    "Adeptus Mechanicus Sydonian Skatros": {
        "stats": {
            "stat_movement": "8\"",
            "stat_toughness": 4,
            "stat_save": "4+",
            "stat_wounds": 4,
            "stat_leadership": "7+",
            "stat_oc": 1,
            "stat_invuln": "5+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Sydonian Feet",
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
                "name": "Mechanicus pistol",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "1",
                "skill": "4+",
                "strength": "6",
                "ap": "-1",
                "damage": "1",
                "keywords": "Devastating Wounds, Pistol"
            },
            {
                "name": "Radium Jezzail",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "5",
                "ap": "-2",
                "damage": "3",
                "keywords": "Heavy, Precision, Anti-Infantry 3+"
            },
            {
                "name": "Skatros transuranic arquebus",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "7",
                "ap": "-2",
                "damage": "D3",
                "keywords": "Heavy, Precision, Anti-Monster 4+, Anti-Vehicle 4+"
            }
        ],
        "abilities": [
            {
                "name": "Dread Snipers",
                "description": "In your Shooting phase, after this model has shot, select one enemy unit hit by one or more of those attacks. That unit must take a Battle-shock test."
            },
            {
                "name": "Sydonian Sentinel",
                "description": "This model cannot be your Warlord."
            },
            {
                "name": "Achillan Eye",
                "description": "Each time this model makes an attack with a radium jezzail that targets an Infantry unit, you can re-roll the Wound roll. Each time this model makes an attack with a Skatros transuranic arquebus that targets a Monster or Vehicle unit, you can re-roll the Wound roll."
            }
        ]
    },
    "Adeptus Mechanicus Tech-Priest Enginseer": {
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
                "name": "Servo arm",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "1",
                "skill": "4+",
                "strength": "6",
                "ap": "-2",
                "damage": "2",
                "keywords": "Extra Attacks"
            },
            {
                "name": "Omnissian axe",
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
                "skill": "4+",
                "strength": "6",
                "ap": "-1",
                "damage": "1",
                "keywords": "Devastating Wounds, Pistol"
            }
        ],
        "abilities": [
            {
                "name": "Enginseer",
                "description": "While this model is within 3\" of one or more friendly Adeptus Mechanicus Vehicle units, unless it is leading a unit, this model has the Lone Operative ability."
            },
            {
                "name": "Omnissiah's Blessing",
                "description": "In your Command phase, select one friendly Adeptus Mechanicus model within 3\" of this model. That model regains up to D3 lost wounds and, if it is a Vehicle model, until the start of your next Command phase, that model has the Feel No Pain 5+ ability. Each model can only be selected for this ability once per Command phase"
            },
            {
                "name": "Vengeance for the Omnissiah",
                "description": "If a friendly Adeptus Mechanicus Vehicle model is destroyed within 12\" of this model, until the end of the battle, this model\u2019s Omnissian axe has an Attacks characteristic of 6."
            },
            {
                "name": "Leader",
                "description": "This model can be attached to the following units:\n\u25a0 Corpuscarii Electro-Priests\n\u25a0 Fulgurite Electro-Priests\n\u25a0 Kataphron Breachers\n\u25a0 Kataphron Destroyers\n\u25a0 Servitors\n\u25a0 Skitarii Rangers\n\u25a0 Skitarii Vanguard"
            }
        ]
    },
    "Adeptus Mechanicus Tech-Priest Manipulus": {
        "stats": {
            "stat_movement": "6\"",
            "stat_toughness": 4,
            "stat_save": "2+",
            "stat_wounds": 4,
            "stat_leadership": "7+",
            "stat_oc": 1,
            "stat_invuln": "5+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Omnissian staff",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "3+",
                "strength": "6",
                "ap": "-1",
                "damage": "2",
                "keywords": "-"
            },
            {
                "name": "Magnarail lance",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "7",
                "ap": "-2",
                "damage": "3",
                "keywords": "Heavy"
            },
            {
                "name": "Transonic cannon",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "D6",
                "skill": "N/A",
                "strength": "4",
                "ap": "0",
                "damage": "2",
                "keywords": "Devastating Wounds, Torrent"
            }
        ],
        "abilities": [
            {
                "name": "Leader",
                "description": "This model can be attached to the following units:\n\u25a0 Corpuscarii Electro-Priests\n\u25a0 Fulgurite Electro-Priests\n\u25a0 Kataphron Breachers\n\u25a0 Kataphron Destroyers\n\u25a0 Skitarii Rangers\n\u25a0 Skitarii Vanguard"
            },
            {
                "name": "Galvanic Field",
                "description": "While this model is leading a unit, weapons equipped by models in that unit have the [Lethal Hits] ability."
            },
            {
                "name": "Defend the Divine Work",
                "description": "Once per battle, at the start of any phase, this model can use this ability. If it does, until the end of the phase, all models in this model\u2019s unit have a 4+ invulnerable save."
            }
        ]
    },
    "Adeptus Mechanicus Technoarcheologist": {
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
                "name": "Servo-arc claw",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "3",
                "skill": "4+",
                "strength": "8",
                "ap": "-2",
                "damage": "2",
                "keywords": "Anti-Vehicle 4+, Devastating Wounds"
            },
            {
                "name": "Mechanicus pistol",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "1",
                "skill": "4+",
                "strength": "6",
                "ap": "-1",
                "damage": "1",
                "keywords": "Devastating Wounds, Pistol"
            }
        ],
        "abilities": [
            {
                "name": "Seekers of Divine Arcana",
                "description": "While this model is leading a unit, add 1 to the Objective Control characteristic of models in that unit."
            },
            {
                "name": "Cogitative Instincts",
                "description": "Enemy units that are set up on the battlefield as Reinforcements cannot be set up within 12\" horizontally of this model."
            },
            {
                "name": "Support",
                "description": "This model can be attached to the following units:\n\u25a0 Corpuscarii Electro-Priests\n\u25a0 Fulgurite Electro-Priests\n\u25a0 Kataphron Breachers\n\u25a0 Kataphron Destroyers\n\u25a0 Skitarii Rangers\n\u25a0 Skitarii Vanguard"
            }
        ]
    },
    "Adeptus Mechanicus Thulia Ghuld": {
        "stats": {
            "stat_movement": "8\"",
            "stat_toughness": 8,
            "stat_save": "2+",
            "stat_wounds": 10,
            "stat_leadership": "6+",
            "stat_oc": 3,
            "stat_invuln": "4+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "\u27a4 Rod of the War Forge - strike",
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
                "name": "\u27a4 Rod of the War Forge - sweep",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "12",
                "skill": "2+",
                "strength": "6",
                "ap": "-1",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "\u27a4 Jericho-class conversion resonator - shockwave",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "D6+2",
                "skill": "2+",
                "strength": "6",
                "ap": "-2",
                "damage": "1",
                "keywords": "Blast, Sustained Hits 1"
            },
            {
                "name": "\u27a4 Jericho-class conversion resonator - titanic impact",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "2",
                "skill": "2+",
                "strength": "12",
                "ap": "-3",
                "damage": "D6+2",
                "keywords": "Devastating Wounds"
            }
        ],
        "abilities": [
            {
                "name": "Icon of War",
                "description": "Fanatical Devotion: You can select one friendly Skitarii or Thulia Ghuld unit within 6\" of this model; until the start of your next Command phase, that unit is eligible to shoot and declare a charge in a turn in which it Advanced.\n\nAdaptive Tactics: You can select one friendly Skitarii or Thulia Ghuld unit within 6\" of this model; until the start of your next Command phase, that unit is eligible to shoot and declare a charge in a turn in which it Fell Back.\n\nThe Fires of Mars: You can select one friendly Skitarii or Thulia Ghuld unit within 6\" of this model; until the start of your next Command phase, the Conqueror Imperative and Protector Imperative are both active for that unit."
            },
            {
                "name": "Mechanicus Bodyguard",
                "description": "While this model is within 3\" of one or more other friendly Adeptus Mechanicus units, this model has the Lone Operative ability."
            },
            {
                "name": "Secutor of Olympus",
                "description": "At the start of your Shooting phase, select one enemy Vehicle unit within 12\" of this model and roll one D6: on a 2+, that enemy unit suffers D3+1 mortal wounds."
            },
            {
                "name": "Supreme Commander",
                "description": "If this model is in your army, it must be your Warlord."
            },
            {
                "name": "Rod of the War Forge",
                "description": "In your Command phase, select one of the abilities in the Icon of War section. Until the start of your next Command phase, this model has that ability."
            }
        ]
    },
    "Dunecrawler": {
        "stats": {
            "stat_movement": "8\"",
            "stat_toughness": 10,
            "stat_save": "2+",
            "stat_wounds": 11,
            "stat_leadership": "7+",
            "stat_oc": 3,
            "stat_invuln": "4+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Cognis heavy stubber",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "3",
                "skill": "4+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Rapid Fire 3, Sustained Hits 1"
            },
            {
                "name": "Dunecrawler legs",
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
                "name": "\u27a4 Eradication beamer - dissipated",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "3D3",
                "skill": "4+",
                "strength": "10",
                "ap": "-2",
                "damage": "2",
                "keywords": "Blast, Sustained Hits 1"
            },
            {
                "name": "\u27a4 Eradication beamer - focused",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "3D3",
                "skill": "4+",
                "strength": "10",
                "ap": "-3",
                "damage": "3",
                "keywords": "Blast, Sustained Hits 1"
            },
            {
                "name": "Daedalus missile launcher",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "2",
                "skill": "4+",
                "strength": "10",
                "ap": "-2",
                "damage": "D6+1",
                "keywords": "Anti-Fly 2+"
            },
            {
                "name": "Icarus array",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "6",
                "skill": "4+",
                "strength": "8",
                "ap": "-1",
                "damage": "2",
                "keywords": "Anti-Fly 4+, Twin-linked"
            },
            {
                "name": "Neutron laser",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "3",
                "skill": "4+",
                "strength": "16",
                "ap": "-4",
                "damage": "D6+2",
                "keywords": "Heavy"
            },
            {
                "name": "Twin Onager heavy phosphor blaster",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "12",
                "skill": "4+",
                "strength": "6",
                "ap": "-1",
                "damage": "2",
                "keywords": "Ignores Cover, Twin-linked"
            }
        ],
        "abilities": [
            {
                "name": "Emanatus Forcefield (Aura)",
                "description": "While a friendly Adeptus Mechanicus Battleline model is wholly within 6\" of this model, that Battleline model has a 4+ invulnerable save against ranged attacks."
            },
            {
                "name": "Damaged: 1-4 wounds remaining",
                "description": "While this mdel has 1-4 wounds remaining, each time this model makes an attack, subtract 1 from the Hit roll."
            },
            {
                "name": "Scuttling Walker",
                "description": "Each time this model makes a Normal, Advance or Fall Back move, it can move through friendly Monster and Vehicle models and sections of terrain features that are 4\" or less in height."
            },
            {
                "name": "Broad spectrum data-tether",
                "description": "The bearer loses the SMOKE keyword, but each time you target the bearer with a Stratagem, roll one D6: on a 5+, you gain 1CP."
            }
        ]
    },
    "Electropriests": {
        "stats": {
            "stat_movement": "6\"",
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
                "name": "Electrostatic gauntlets",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "3",
                "skill": "3+",
                "strength": "5",
                "ap": "0",
                "damage": "1",
                "keywords": "Pistol, Sustained Hits 2"
            },
            {
                "name": "Electrostatic gauntlets",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "3",
                "skill": "4+",
                "strength": "5",
                "ap": "0",
                "damage": "1",
                "keywords": "Sustained Hits 2"
            }
        ],
        "abilities": [
            {
                "name": "Electro-shock",
                "description": "In your Shooting phase, after this unit has shot, select one enemy unit (excluding Monsters and Vehicles) hit by one or more of those attacks. Until the end of your opponent\u2019s next turn, that enemy unit is shocked. While a unit is shocked, subtract 2\" from its Move characteristic and subtract 2 from Advance and Charge rolls made for it."
            }
        ]
    },
    "Hastarii Exterminators": {
        "stats": {
            "stat_movement": "5\"",
            "stat_toughness": 4,
            "stat_save": "3+",
            "stat_wounds": 2,
            "stat_leadership": "7+",
            "stat_oc": 1,
            "stat_invuln": "5+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Power weapon",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "2",
                "skill": "4+",
                "strength": "5",
                "ap": "-2",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "Hastarii arc blaster",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "1",
                "skill": "4+",
                "strength": "6",
                "ap": "-1",
                "damage": "2",
                "keywords": "Anti-Vehicle 4+, Devastating Wounds"
            },
            {
                "name": "\u27a4 Eradication caster - focused",
                "weapon_type": "ranged",
                "range": "15\"",
                "attacks": "2",
                "skill": "4+",
                "strength": "5",
                "ap": "-2",
                "damage": "2",
                "keywords": "Anti-Infantry 4+"
            },
            {
                "name": "\u27a4 Eradication caster - dissipated",
                "weapon_type": "ranged",
                "range": "30\"",
                "attacks": "2",
                "skill": "4+",
                "strength": "5",
                "ap": "-1",
                "damage": "2",
                "keywords": "Anti-Infantry 4+"
            },
            {
                "name": "Close combat weapon",
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
                "name": "Attached Unit",
                "description": "If a Character unit from your army can be attached to a Skitarii Rangers unit, it can be attached to this unit instead"
            },
            {
                "name": "Broad-spectrum Targeting Augurs",
                "description": "Each time a model in this unit makes an attack with an eradication caster that targets a unit (excluding Monster and Vehicle units), that attack has the [SUSTAINED HITS 1] ability."
            }
        ]
    },
    "Hastarii Fusiliers": {
        "stats": {
            "stat_movement": "5\"",
            "stat_toughness": 4,
            "stat_save": "3+",
            "stat_wounds": 2,
            "stat_leadership": "7+",
            "stat_oc": 1,
            "stat_invuln": "5+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Hastarii phosphor blaster",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "2",
                "skill": "4+",
                "strength": "5",
                "ap": "0",
                "damage": "1",
                "keywords": "Ignores Cover"
            },
            {
                "name": "Neutron fusil",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "1",
                "skill": "4+",
                "strength": "12",
                "ap": "-3",
                "damage": "D6+1",
                "keywords": "-"
            },
            {
                "name": "Power weapon",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "2",
                "skill": "4+",
                "strength": "5",
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
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Attached Unit",
                "description": "If a Character unit from your army can be attached to a Skitarii Rangers unit, it can be attached to this unit instead"
            },
            {
                "name": "Monocular Targeting Helms",
                "description": "Each time a model in this unit makes an attack with a neutron fusil against a Monster or Vehicle unit, that attack has the [IGNORES COVER] ability."
            }
        ]
    },
    "Ironstrider Ballistarii": {
        "stats": {
            "stat_movement": "10\"",
            "stat_toughness": 7,
            "stat_save": "3+",
            "stat_wounds": 7,
            "stat_leadership": "7+",
            "stat_oc": 2,
            "stat_invuln": "5+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Twin cognis autocannon",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "4",
                "skill": "4+",
                "strength": "9",
                "ap": "-1",
                "damage": "3",
                "keywords": "Sustained Hits 1, Twin-linked"
            },
            {
                "name": "Ironstrider feet",
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
                "name": "Twin cognis lascannon",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "2",
                "skill": "4+",
                "strength": "12",
                "ap": "-3",
                "damage": "D6+1",
                "keywords": "Sustained Hits 1, Twin-linked"
            }
        ],
        "abilities": [
            {
                "name": "Elevated Strider",
                "description": "This unit is eligible to shoot in a turn in which it Fell Back or Advanced, and you can re-roll Desperate Escape tests taken for models in this unit."
            },
            {
                "name": "Broad Spectrum Data-tether",
                "description": "Each time you select this unit as the target of a Stratagem, roll one D6: on a 5+, you gain 1CP."
            }
        ]
    },
    "Kataphron Destroyers": {
        "stats": {
            "stat_movement": "5\"",
            "stat_toughness": 6,
            "stat_save": "3+",
            "stat_wounds": 3,
            "stat_leadership": "7+",
            "stat_oc": 1,
            "stat_invuln": "6+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Heavy grav-cannon",
                "weapon_type": "ranged",
                "range": "30\"",
                "attacks": "4",
                "skill": "4+",
                "strength": "6",
                "ap": "-1",
                "damage": "2",
                "keywords": "Anti-Vehicle 2+"
            },
            {
                "name": "Cognis flamer",
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
                "name": "Close combat weapon",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "2",
                "skill": "4+",
                "strength": "5",
                "ap": "0",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "Phosphor blaster",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "1",
                "skill": "4+",
                "strength": "5",
                "ap": "0",
                "damage": "1",
                "keywords": "Ignores Cover, Rapid Fire 1"
            },
            {
                "name": "\u27a4 Kataphron plasma culverin - standard",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "4",
                "skill": "4+",
                "strength": "7",
                "ap": "-2",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "\u27a4 Kataphron plasma culverin - supercharge",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "4",
                "skill": "4+",
                "strength": "8",
                "ap": "-3",
                "damage": "2",
                "keywords": "Hazardous"
            }
        ],
        "abilities": [
            {
                "name": "Sentinel Directive",
                "description": "Each time you target this unit with the Fire Overwatch Stratagem, hits are scored on unmodified Hit rolls of 5+ when resolving that Stratagem."
            }
        ]
    },
    "Servitor Battleclade": {
        "stats": {
            "stat_movement": "6\"",
            "stat_toughness": 4,
            "stat_save": "4+",
            "stat_wounds": 1,
            "stat_leadership": "8+",
            "stat_oc": 1,
            "stat_invuln": "6+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Mechanicus pistol",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "1",
                "skill": "4+",
                "strength": "6",
                "ap": "-1",
                "damage": "1",
                "keywords": "Devastating Wounds, Pistol"
            },
            {
                "name": "Dataspikes",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "4+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "Heavy arc rifle",
                "weapon_type": "ranged",
                "range": "30\"",
                "attacks": "1",
                "skill": "4+",
                "strength": "8",
                "ap": "-2",
                "damage": "3",
                "keywords": "Anti-VEHICLE 4+, Rapid Fire 1"
            },
            {
                "name": "Servo-claw",
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
                "name": "Incendine igniter",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "D6",
                "skill": "N/A",
                "strength": "3",
                "ap": "0",
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
                "name": "Phosphor blaster",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "1",
                "skill": "4+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Ignores Cover, Rapid Fire 1"
            }
        ],
        "abilities": [
            {
                "name": "Network Override",
                "description": "While this unit contains one or more Tech-Priest models, this unit is:\n- Eligible to perform an Action in a turn in which it Advanced.\n- Eligible to shoot in a turn in which it started an Action."
            },
            {
                "name": "Attached Unit",
                "description": "If a Character unit from your army with the Leader ability can be attached to a Kataphron Breachers unit, it can be attached to this unit instead."
            }
        ]
    },
    "Skitarii Rangers": {
        "stats": {
            "stat_movement": "6\"",
            "stat_toughness": 3,
            "stat_save": "4+",
            "stat_wounds": 1,
            "stat_leadership": "7+",
            "stat_oc": 2,
            "stat_invuln": "5+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Alpha combat weapon",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "2",
                "skill": "4+",
                "strength": "5",
                "ap": "-1",
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
                "name": "Galvanic rifle",
                "weapon_type": "ranged",
                "range": "30\"",
                "attacks": "2",
                "skill": "4+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "Mechanicus pistol",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "1",
                "skill": "4+",
                "strength": "6",
                "ap": "-1",
                "damage": "1",
                "keywords": "Devastating Wounds, Pistol"
            },
            {
                "name": "Transuranic arquebus",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "1",
                "skill": "4+",
                "strength": "7",
                "ap": "-2",
                "damage": "D3",
                "keywords": "Heavy, Precision"
            },
            {
                "name": "Arc rifle",
                "weapon_type": "ranged",
                "range": "30\"",
                "attacks": "1",
                "skill": "4+",
                "strength": "8",
                "ap": "-1",
                "damage": "D3",
                "keywords": "Anti-Vehicle 4+, Devastating Wounds, Rapid Fire 1"
            },
            {
                "name": "\u27a4 Plasma caliver -  supercharge",
                "weapon_type": "ranged",
                "range": "30\"",
                "attacks": "2",
                "skill": "4+",
                "strength": "8",
                "ap": "-3",
                "damage": "2",
                "keywords": "Hazardous"
            },
            {
                "name": "\u27a4 Plasma caliver - standard",
                "weapon_type": "ranged",
                "range": "30\"",
                "attacks": "2",
                "skill": "4+",
                "strength": "7",
                "ap": "-2",
                "damage": "1",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Objective Scouted",
                "description": "At the end of your Command phase, if this unit is within range of an objective marker you control, that objective marker remains under your control, even if you have no models within range of it, until your opponent controls it at the start or end of any turn."
            },
            {
                "name": "Enhanced data-tether",
                "description": "Each time you select the bearer\u2019s unit\nas the target of a Stratagem, roll one D6: on a 5+, you gain 1CP."
            },
            {
                "name": "Omnispex",
                "description": "Ranged weapons equipped by models in the bearer\u2019s unit have the IGNORES COVER ability."
            }
        ]
    },
    "Skitarii Vanguard": {
        "stats": {
            "stat_movement": "6\"",
            "stat_toughness": 3,
            "stat_save": "4+",
            "stat_wounds": 1,
            "stat_leadership": "7+",
            "stat_oc": 2,
            "stat_invuln": "5+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Alpha combat weapon",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "2",
                "skill": "4+",
                "strength": "5",
                "ap": "-1",
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
                "name": "Radium carbine",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "3",
                "skill": "4+",
                "strength": "3",
                "ap": "0",
                "damage": "1",
                "keywords": "Anti-Infantry 4+"
            },
            {
                "name": "Mechanicus pistol",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "1",
                "skill": "4+",
                "strength": "6",
                "ap": "-1",
                "damage": "1",
                "keywords": "Devastating Wounds, Pistol"
            },
            {
                "name": "Transuranic arquebus",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "1",
                "skill": "4+",
                "strength": "7",
                "ap": "-2",
                "damage": "D3",
                "keywords": "Heavy, Precision"
            },
            {
                "name": "Arc rifle",
                "weapon_type": "ranged",
                "range": "30\"",
                "attacks": "1",
                "skill": "4+",
                "strength": "8",
                "ap": "-1",
                "damage": "D3",
                "keywords": "Anti-Vehicle 4+, Devastating Wounds, Rapid Fire 1"
            },
            {
                "name": "\u27a4 Plasma caliver -  supercharge",
                "weapon_type": "ranged",
                "range": "30\"",
                "attacks": "2",
                "skill": "4+",
                "strength": "8",
                "ap": "-3",
                "damage": "2",
                "keywords": "Hazardous"
            },
            {
                "name": "\u27a4 Plasma caliver - standard",
                "weapon_type": "ranged",
                "range": "30\"",
                "attacks": "2",
                "skill": "4+",
                "strength": "7",
                "ap": "-2",
                "damage": "1",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Rad-saturation (Aura)",
                "description": "While an enemy unit (excluding Vehicle units) is within 3\" of this unit, subtract 1 from the Objective Control characteristic of models in that unit."
            },
            {
                "name": "Enhanced data-tether",
                "description": "Each time you select the bearer\u2019s unit as the target of a Stratagem, roll one D6: on a 5+, you gain 1CP."
            },
            {
                "name": "Omnispex",
                "description": "Ranged weapons equipped by models in the bearer\u2019s unit have the IGNORES COVER ability."
            }
        ]
    },
    "Sydonian Dragoons with radium jezzails": {
        "stats": {
            "stat_movement": "10\"",
            "stat_toughness": 7,
            "stat_save": "3+",
            "stat_wounds": 7,
            "stat_leadership": "7+",
            "stat_oc": 2,
            "stat_invuln": "5+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Phosphor serpenta",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "1",
                "skill": "4+",
                "strength": "5",
                "ap": "-1",
                "damage": "2",
                "keywords": "Ignores Cover, Pistol"
            },
            {
                "name": "Radium jezzail",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "1",
                "skill": "4+",
                "strength": "5",
                "ap": "-2",
                "damage": "3",
                "keywords": "Anti-Infantry 3+, Heavy, Precision"
            },
            {
                "name": "Ironstrider feet",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "3",
                "skill": "4+",
                "strength": "5",
                "ap": "0",
                "damage": "1",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Focused Hunters",
                "description": "At the start of the battle, select one unit from your opponent\u2019s army. Until the end of the battle, each time a model in this unit makes an attack that targets that unit, you can re-roll the Hit roll."
            },
            {
                "name": "Broad Spectrum Data-tether",
                "description": "Each time you select the bearer as the target of a Stratagem, roll one D6: on a 5+, you gain 1CP."
            }
        ]
    },
    "Sydonian Dragoons with taser lances": {
        "stats": {
            "stat_movement": "10\"",
            "stat_toughness": 7,
            "stat_save": "3+",
            "stat_wounds": 7,
            "stat_leadership": "7+",
            "stat_oc": 2,
            "stat_invuln": "5+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Phosphor serpenta",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "1",
                "skill": "4+",
                "strength": "5",
                "ap": "-1",
                "damage": "2",
                "keywords": "Ignores Cover, Pistol"
            },
            {
                "name": "Taser lance",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "4+",
                "strength": "7",
                "ap": "-2",
                "damage": "2",
                "keywords": "Anti-Walker 2+, Lance, Sustained Hits 2"
            }
        ],
        "abilities": [
            {
                "name": "Dynamic Efficiency",
                "description": "This unit is eligible to declare a charge in a turn in which it Advanced or Fell Back, and you can re-roll Desperate Escape tests taken for models in this unit."
            },
            {
                "name": "Broad Spectrum Data-tether",
                "description": "Each time you select the bearer as the target of a Stratagem, roll one D6: on a 5+, you gain 1CP."
            }
        ]
    },
    "Tech-Priest Dominus": {
        "stats": {
            "stat_movement": "6\"",
            "stat_toughness": 4,
            "stat_save": "2+",
            "stat_wounds": 4,
            "stat_leadership": "7+",
            "stat_oc": 1,
            "stat_invuln": "5+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Omnissian axe",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "3+",
                "strength": "6",
                "ap": "-2",
                "damage": "2",
                "keywords": "-"
            },
            {
                "name": "Macrostubber",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "5",
                "skill": "3+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Pistol"
            },
            {
                "name": "Phosphor serpenta",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "5",
                "ap": "-1",
                "damage": "2",
                "keywords": "Ignores Cover, Pistol"
            },
            {
                "name": "\u27a4 Eradication ray - dissipated",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "D3",
                "skill": "3+",
                "strength": "6",
                "ap": "-1",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "\u27a4 Eradication ray - focused",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "D3",
                "skill": "3+",
                "strength": "6",
                "ap": "-2",
                "damage": "2",
                "keywords": "-"
            },
            {
                "name": "Volkite blaster",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "3",
                "skill": "3+",
                "strength": "5",
                "ap": "0",
                "damage": "2",
                "keywords": "Devastating Wounds"
            }
        ],
        "abilities": [
            {
                "name": "Leader",
                "description": "This model can be attached to the following units:\n\u25a0 Corpuscarii Electro-Priests\n\u25a0 Fulgurite Electro-Priests\n\u25a0 Kataphron Breachers\n\u25a0 Kataphron Destroyers\n\u25a0 Skitarii Rangers\n\u25a0 Skitarii Vanguard"
            },
            {
                "name": "Lord of the Machine Cult",
                "description": "While this model is leading a unit, models in that unit have the Feel No Pain 5+ ability. If that unit has the Electro-Priests keyword, models in that unit have the Feel No Pain 4+ ability instead"
            },
            {
                "name": "Data-spike",
                "description": "At the start of the Fight phase, you can select one enemy Vehicle unit within Engagement Range of this model\u2019s unit and roll one D6: on a 4+, that enemy unit suffers D6 mortal wounds and, until the end of the phase, the Weapon Skill characteristic of melee weapons equipped by that enemy unit is worsened by 1."
            }
        ]
    }
}


class Command(BaseCommand):
    """Refresh Adeptus Mechanicus stat lines, weapon profiles, and abilities from BSData."""

    help = 'Refresh 11th Edition stats/weapons/abilities for Adeptus Mechanicus units.'

    def add_arguments(self, parser):
        """Add --dry-run flag."""
        parser.add_argument(
            '--dry-run', action='store_true',
            help='Preview changes without writing to the database.',
        )

    def handle(self, *args, **options):
        """Iterate ADMECH_DATASHEETS and refresh each unit's datasheet data."""
        dry_run = options['dry_run']
        updated = 0
        skipped = 0

        with transaction.atomic():
            for name, payload in ADMECH_DATASHEETS.items():
                try:
                    unit = UnitType.objects.get(name=name, faction__name='Adeptus Mechanicus')
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
