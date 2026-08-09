"""
Management command: seed_space_marines_datasheets

Refreshes stat lines, weapon profiles, and abilities for all base Space
Marines units using 11th Edition data sourced from BSData/wh40k-11e
("Imperium - Space Marines.json") -- the same source used by
seed_space_marines_points.py.

Usage:
    python manage.py seed_space_marines_datasheets
    python manage.py seed_space_marines_datasheets --dry-run

Notes:
- Does NOT touch points_cost or category -- those are handled entirely by
  seed_space_marines_points.py. This command only refreshes stat_* fields,
  WeaponProfile rows, and UnitAbility rows.
- Per-field safety rule: a unit's stats/weapons/abilities are only
  overwritten when BSData actually has that data for it. If extraction
  found nothing, the existing DB value/rows are left untouched rather than
  blanked.
- All 77 active units resolved cleanly using the full accumulated
  extraction methodology (top-level selectionEntries recursion,
  sharedProfiles fallback by name, infoLinks(type="profile") resolution by
  id). Drop Pod genuinely has 0 weapon profiles in BSData -- not a bug,
  it's an unarmed transport delivery pod.
- Every Space Marine successor chapter (Ultramarines, Blood Angels, Dark
  Angels, Black Templars, Space Wolves, Deathwatch, Iron Hands,
  Salamanders, Imperial Fists, White Scars, Raven Guard) falls back to
  these rows for stats/weapons/abilities on any unit it doesn't override
  with its own chapter-specific row -- refreshing this faction benefits
  all of them immediately, not just the base "Space Marines" calculator
  page.
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from calculators.models import UnitAbility, UnitType, WeaponProfile

# (name -> {stats?, weapons?, abilities?}). Missing keys mean "no data
# found for this field -- leave existing DB data untouched."
SPACE_MARINES_DATASHEETS = {
    "Aggressor Squad": {
        "stats": {
            "stat_movement": "5\"",
            "stat_toughness": 6,
            "stat_save": "3+",
            "stat_wounds": 3,
            "stat_leadership": "6+",
            "stat_oc": 1,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Twin power fist",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "3",
                "skill": "3+",
                "strength": "8",
                "ap": "-2",
                "damage": "2",
                "keywords": "Twin-linked"
            },
            {
                "name": "Auto Boltstorm Gauntlets",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "3",
                "skill": "3+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Twin-linked"
            },
            {
                "name": "Fragstorm grenade launcher",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "D6",
                "skill": "3+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Blast"
            },
            {
                "name": "Flamestorm Gauntlets",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "D6+1",
                "skill": "N/A",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Ignores Cover, Torrent, Twin-linked"
            }
        ],
        "abilities": [
            {
                "name": "Close-quarters Firepower",
                "description": "Each time a model in this unit makes a ranged attack that targets the closest eligible target, improve the Armour Penetration characteristic of that attack\nby 1."
            }
        ]
    },
    "Ancient": {
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
                "keywords": "Close-Quarters"
            },
            {
                "name": "Bolt Rifle",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "2",
                "skill": "3+",
                "strength": "4",
                "ap": "-1",
                "damage": "1",
                "keywords": "Assault, Heavy"
            },
            {
                "name": "Close combat weapon",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "5",
                "skill": "2+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "Power weapon",
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
                "name": "Unbreakable Duty",
                "description": "While this model is within range of an objective marker and/or within 6\" of the centre of the battlefield, this model has the Feel No Pain 4+ ability."
            },
            {
                "name": "Support",
                "description": "This model can be attached to the following units:\n\n\u25a0 ASSAULT INTERCESSOR SQUAD\n\u25a0 CRUSADER SQUAD\n\u25a0 DEATHWATCH VETERANS\n\u25a0 DECIMUS KILL TEAM\n\u25a0 DESOLATION SQUAD\n\u25a0 DEVASTATOR SQUAD\n\u25a0 FORTIS KILL TEAM\n\u25a0 HELLBLASTER SQUAD\n\u25a0 INFERNUS SQUAD\n\u25a0 INNER CIRCLE COMPANIONS\n\u25a0 INTERCESSOR SQUAD\n\u25a0 STERNGUARD VETERAN SQUAD\n\u25a0 SWORD BRETHREN SQUAD\n\u25a0 TACTICAL SQUAD\n\nYou can attach this model to one of the above units even if one Captain, Chapter Master or Lieutenant model has already been attached to it. If you do, and that Bodyguard unit is destroyed, the Leader units attached to it become separate units, with their original Starting Strengths."
            },
            {
                "name": "Astartes Banner",
                "description": "While this model is leading a unit, add 1 to the Objective Control characteristic of models in that unit."
            }
        ]
    },
    "Ancient in Terminator Armor": {
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
                "name": "Power weapon",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "5",
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
                "attacks": "4",
                "skill": "2+",
                "strength": "8",
                "ap": "-2",
                "damage": "2",
                "keywords": "-"
            },
            {
                "name": "Thunder Hammer",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "3+",
                "strength": "8",
                "ap": "-2",
                "damage": "2",
                "keywords": "Devastating Wounds"
            },
            {
                "name": "Chainfist",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "3+",
                "strength": "8",
                "ap": "-2",
                "damage": "2",
                "keywords": "Anti Vehicle 3+"
            },
            {
                "name": "Close combat weapon",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "5",
                "skill": "2+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
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
            }
        ],
        "abilities": [
            {
                "name": "Keep the Banner High",
                "description": "While this model is leading a unit, each time a model in that unit makes an attack, add 1 to the Hit roll if that unit is below its Starting Strength, and add 1 to the Wound roll as well if that unit is Below Half-strength"
            },
            {
                "name": "Support",
                "description": "This model can be attached to the following units:\n\n\u25a0 DEATHWATCH TERMINATOR SQUAD\n\u25a0 DEATHWING KNIGHTS\n\u25a0 DEATHWING TERMINATOR SQUAD\n\u25a0 TERMINATOR ASSAULT SQUAD\n\u25a0 TERMINATOR SQUAD\n\nYou can attach this model to one of the above units even if one Captain, Chapter Master or Lieutenant model has already been attached to it. If you do, and that Bodyguard unit is destroyed, the Leader units attached to it become separate units, with their original Starting Strengths."
            },
            {
                "name": "Astartes Banner",
                "description": "While this model is leading a unit, add 1 to the Objective Control characteristic of models in that unit."
            },
            {
                "name": "Terminator Storm Shield",
                "description": "The bearer has a Wounds characteristic of 6."
            }
        ]
    },
    "Apothecary": {
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
                "name": "Reductor Pistol",
                "weapon_type": "ranged",
                "range": "3\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "4",
                "ap": "-4",
                "damage": "2",
                "keywords": "Pistol"
            },
            {
                "name": "Absolvor bolt pistol",
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
                "name": "Close combat weapon",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "3+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Narthecium",
                "description": "While this model is leading a unit, in your Command phase, you can return 1 destroyed model (excluding Character models) to that unit."
            },
            {
                "name": "Gene Seed Recovery",
                "description": "When this model\u2019s Bodyguard unit is destroyed, roll one D6: on a 2+, you gain 1CP."
            },
            {
                "name": "Support",
                "description": "This model can be attached to the following units:\n\n\u25a0 ASSAULT INTERCESSOR SQUAD\n\u25a0 CRUSADER SQUAD\n\u25a0 DEATHWATCH VETERANS\n\u25a0 DECIMUS KILL TEAM\n\u25a0 DESOLATION SQUAD\n\u25a0 DEVASTATOR SQUAD\n\u25a0 FORTIS KILL TEAM\n\u25a0 HELLBLASTER SQUAD\n\u25a0 INFERNUS SQUAD\n\u25a0 INNER CIRCLE COMPANIONS\n\u25a0 INTERCESSOR SQUAD\n\u25a0 STERNGUARD VETERAN SQUAD\n\u25a0 SWORD BRETHREN SQUAD\n\u25a0 TACTICAL SQUAD\n\n\nYou can attach this model to one of the above units even if one Captain, Chapter Master or Lieutenant model has already been attached to it. If you do, and that Bodyguard unit is destroyed, the Leader units attached to it become separate units, with their original Starting Strengths."
            }
        ]
    },
    "Apothecary Biologis": {
        "stats": {
            "stat_movement": "5\"",
            "stat_toughness": 6,
            "stat_save": "3+",
            "stat_wounds": 5,
            "stat_leadership": "6+",
            "stat_oc": 3,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Absolvor bolt pistol",
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
                "name": "Close combat weapon",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "3+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Surgical Precision",
                "description": "While this model is leading a unit, weapons equipped by models in that unit have the [LETHAL HITS] ability."
            },
            {
                "name": "Vivispectrum",
                "description": "If this model\u2019s unit destroys an enemy unit as the result of a melee attack, until the end of the battle, this model has an Objective Control characteristic of 9."
            },
            {
                "name": "Support",
                "description": "This model can be attached to the following units:\n\n\u25a0 AGGRESSOR SQUAD\n\u25a0 ERADICATOR SQUAD\n\u25a0 HEAVY INTERCESSOR SQUAD\n\u25a0 INDOMITOR KILL TEAM\n\nYou can attach this model to one of the above units even if one Captain or Chapter Master model has already been attached to it. If you do, and that Bodyguard unit is destroyed, the Leader units attached to it become separate units, with their original Starting Strengths."
            }
        ]
    },
    "Assault Intercessor Squad": {
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
                "name": "Heavy Bolt Pistol",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "4",
                "ap": "-1",
                "damage": "1",
                "keywords": "Pistol"
            },
            {
                "name": "Astartes Chainsword",
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
                "name": "Power weapon",
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
                "name": "Thunder Hammer",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "3",
                "skill": "4+",
                "strength": "8",
                "ap": "-2",
                "damage": "2",
                "keywords": "Devastating Wounds"
            }
        ],
        "abilities": [
            {
                "name": "Shock Assault",
                "description": "Each time a model in this unit targets an enemy unit with a melee attack, re-roll a Wound roll of 1. If that enemy unit is within range of an objective marker, you can re-roll the Wound roll instead."
            }
        ]
    },
    "Assault Intercessors with Jump Packs": {
        "stats": {
            "stat_movement": "12\"",
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
                "name": "Heavy Bolt Pistol",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "4",
                "ap": "-1",
                "damage": "1",
                "keywords": "Pistol"
            },
            {
                "name": "Astartes Chainsword",
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
                "name": "Power weapon",
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
            }
        ],
        "abilities": [
            {
                "name": "Hammer of Wrath",
                "description": "Each time this unit ends a Charge move, select one enemy unit within Engagement Range of it, then roll one D6 for each model in this unit that is within Engagement Range of that enemy unit: for each 4+, that enemy unit suffers 1 mortal wound."
            }
        ]
    },
    "Ballistus Dreadnought": {
        "stats": {
            "stat_movement": "8\"",
            "stat_toughness": 10,
            "stat_save": "2+",
            "stat_wounds": 12,
            "stat_leadership": "6+",
            "stat_oc": 4,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Armoured Feet",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "5",
                "skill": "3+",
                "strength": "7",
                "ap": "0",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "Ballistus Lascannon",
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
                "name": "\u27a4 Ballistus Missile Launcher - Frag",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "2D6",
                "skill": "3+",
                "strength": "5",
                "ap": "0",
                "damage": "1",
                "keywords": "Blast"
            },
            {
                "name": "\u27a4 Ballistus Missile Launcher - Krak",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "2",
                "skill": "3+",
                "strength": "10",
                "ap": "-2",
                "damage": "D6",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Ballistus Strike",
                "description": "Each time this model makes a ranged attack that targets a unit that is not Below Half-strength, you can re-roll the Hit roll."
            },
            {
                "name": "Damaged: 1-4 Wounds Remaining",
                "description": "While this model has 1-4 wounds remaining, each time this model makes an attack, subtract 1 from the Hit roll."
            }
        ]
    },
    "Bladeguard Veteran Squad": {
        "stats": {
            "stat_movement": "6\"",
            "stat_toughness": 4,
            "stat_save": "3+",
            "stat_wounds": 3,
            "stat_leadership": "6+",
            "stat_oc": 1,
            "stat_invuln": "4+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Heavy Bolt Pistol",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "4",
                "ap": "-1",
                "damage": "1",
                "keywords": "Pistol"
            },
            {
                "name": "Master-crafted power weapon",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "3+",
                "strength": "5",
                "ap": "-2",
                "damage": "2",
                "keywords": "-"
            },
            {
                "name": "Neo-volkite Pistol",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "5",
                "ap": "0",
                "damage": "2",
                "keywords": "Devastating Wounds, Pistol"
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
                "name": "\u27a4 Plasma pistol - standard",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "7",
                "ap": "-2",
                "damage": "1",
                "keywords": "Pistol"
            }
        ],
        "abilities": [
            {
                "name": "Bladeguard",
                "description": "(Once per turn, per unit): In the Fight phase, when this unit is selected to fight or when an enemy unit targets this unit, you can select one of the following:\n\n\n\u25aa This unit\u2019s melee attacks have +1 to hit rolls.\n\u25aa Or: Attacks that target this unit have -1 to hit rolls."
            }
        ]
    },
    "Brutalis Dreadnought": {
        "stats": {
            "stat_movement": "8\"",
            "stat_toughness": 10,
            "stat_save": "2+",
            "stat_wounds": 12,
            "stat_leadership": "6+",
            "stat_oc": 4,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Twin Icarus ironhail heavy stubber",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "3",
                "skill": "3+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Anti-FLY 4+, Rapid Fire 3, Twin-linked"
            },
            {
                "name": "Brutalis Fists",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "6",
                "skill": "3+",
                "strength": "12",
                "ap": "-2",
                "damage": "3",
                "keywords": "Twin-linked"
            },
            {
                "name": "Brutalis Bolt Rifles",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "4",
                "skill": "3+",
                "strength": "4",
                "ap": "-1",
                "damage": "1",
                "keywords": "Twin-linked"
            },
            {
                "name": "\u27a4 Brutalis Talons - Strike",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "6",
                "skill": "3+",
                "strength": "12",
                "ap": "-2",
                "damage": "3",
                "keywords": "Twin-linked"
            },
            {
                "name": "\u27a4 Brutalis Talons - Sweep",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "10",
                "skill": "3+",
                "strength": "7",
                "ap": "-2",
                "damage": "1",
                "keywords": "Twin-linked"
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
                "name": "Twin multi-melta",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "2",
                "skill": "3+",
                "strength": "9",
                "ap": "-4",
                "damage": "D6",
                "keywords": "Melta 2, Twin-linked"
            }
        ],
        "abilities": [
            {
                "name": "Brutalis Charge",
                "description": "Each time this model ends a Charge move, select one enemy unit within Engagement Range of it and roll one D6: on a 2-3, that enemy unit suffers D3 mortal wounds; on a 4-5, that enemy unit suffers 3 mortal wounds; on a 6, that enemy unit suffers D3+3 mortal wounds"
            },
            {
                "name": "Damaged: 1-4 Wounds Remaining",
                "description": "While this model has 1-4 wounds remaining, each time this model makes an attack, subtract 1 from the Hit roll."
            }
        ]
    },
    "Captain": {
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
                "name": "Master-crafted bolter",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "2",
                "skill": "2+",
                "strength": "4",
                "ap": "-1",
                "damage": "2",
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
                "name": "Master-crafted power weapon",
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
                "name": "Heavy Bolt Pistol",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "1",
                "skill": "2+",
                "strength": "4",
                "ap": "-1",
                "damage": "1",
                "keywords": "Pistol"
            },
            {
                "name": "Neo-volkite Pistol",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "1",
                "skill": "2+",
                "strength": "5",
                "ap": "0",
                "damage": "2",
                "keywords": "Devastating Wounds, Pistol"
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
                "name": "\u27a4 Plasma pistol - standard",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "7",
                "ap": "-2",
                "damage": "1",
                "keywords": "Pistol"
            }
        ],
        "abilities": [
            {
                "name": "Leader",
                "description": "This model can be attached to the following units:\n\n\u25a0 ASSAULT INTERCESSOR SQUAD\n\u25a0 BLADEGUARD VETERAN SQUAD\n\u25a0 COMPANY HEROES, CRUSADER SQUAD\n\u25a0 DEATHWATCH VETERANS\n\u25a0 DECIMUS KILL TEAM\n\u25a0 FORTIS KILL TEAM\n\u25a0 HELLBLASTER SQUAD\n\u25a0 INFERNUS SQUAD\n\u25a0 INNER CIRCLE COMPANIONS\n\u25a0 INTERCESSOR SQUAD\n\u25a0 STERNGUARD VETERAN SQUAD\n\u25a0 SWORD BRETHREN SQUAD\n\u25a0 TACTICAL SQUAD\n\u25a0 VICTRIX HONOUR GUARD"
            },
            {
                "name": "Finest Hour",
                "description": "Once per battle, at the start of the Fight phase, this model can use this ability. If it does, until the end of the phase, add 3 to the Attacks characteristic of melee weapons equipped by this model and those weapons have the [DEVASTATING WOUNDS] ability."
            },
            {
                "name": "Rites of Battle",
                "description": "Once per battle round, one unit from your army with this ability can use it when its unit is targeted with a Stratagem. If it does, reduce the CP cost of that use of that Stratagem by 1CP."
            },
            {
                "name": "Relic Shield",
                "description": "Add 1 to the bearer's Wounds characteristic."
            }
        ]
    },
    "Captain in Gravis Armour": {
        "stats": {
            "stat_movement": "5\"",
            "stat_toughness": 6,
            "stat_save": "3+",
            "stat_wounds": 6,
            "stat_leadership": "6+",
            "stat_oc": 1,
            "stat_invuln": "4+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Master-crafted Heavy Bolt Rifle",
                "weapon_type": "ranged",
                "range": "30\"",
                "attacks": "2",
                "skill": "2+",
                "strength": "5",
                "ap": "-1",
                "damage": "3",
                "keywords": "Assault, Heavy"
            },
            {
                "name": "Master-crafted power weapon",
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
                "name": "Boltstorm gauntlet",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "3",
                "skill": "2+",
                "strength": "4",
                "ap": "-1",
                "damage": "1",
                "keywords": "Pistol"
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
                "name": "Relic Chainsword",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "3",
                "skill": "2+",
                "strength": "4",
                "ap": "-1",
                "damage": "2",
                "keywords": "Extra Attacks"
            },
            {
                "name": "Relic Blade",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "2",
                "skill": "2+",
                "strength": "5",
                "ap": "-2",
                "damage": "2",
                "keywords": "Extra Attacks"
            },
            {
                "name": "Relic Fist",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "1",
                "skill": "2+",
                "strength": "8",
                "ap": "-2",
                "damage": "2",
                "keywords": "Extra Attacks"
            }
        ],
        "abilities": [
            {
                "name": "Refuse to Yield",
                "description": "Each time an attack is allocated to this model, halve the Damage characteristic of that attack."
            },
            {
                "name": "Leader",
                "description": "This model can be attached to the following units:\n\n\u25a0 AGGRESSOR SQUAD\n\u25a0 ERADICATOR SQUAD\n\u25a0 HEAVY INTERCESSOR SQUAD\n\u25a0 INDOMITOR KILL TEAM"
            },
            {
                "name": "Rites of Battle",
                "description": "Once per battle round, one unit from your army with this ability can use it when its unit is targeted with a Stratagem. If it does, reduce the CP cost of that use of that Stratagem by 1CP."
            }
        ]
    },
    "Captain in Phobos Armour": {
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
                "name": "Instigator Bolt Carbine",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "1",
                "skill": "2+",
                "strength": "4",
                "ap": "-2",
                "damage": "2",
                "keywords": "Precision"
            },
            {
                "name": "Combat Knife",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "6",
                "skill": "2+",
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
                "skill": "2+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Pistol"
            }
        ],
        "abilities": [
            {
                "name": "Master of Deceit",
                "description": "After both players have deployed their armies, if your army includes one or more models with this ability, you can select up to three friendly ADEPTUS ASTARTES INFANTRY units and redeploy all of those units. When doing so, any of those units can be placed into Strategic Reserves, regardless of how many units are already in Strategic Reserves."
            },
            {
                "name": "Leader",
                "description": "This model can be attached to the following units:\n\n\u25a0 ELIMINATOR SQUAD\n\u25a0 INCURSOR SQUAD\n\u25a0 INFILTRATOR SQUAD\n\u25a0 REIVER SQUAD\n\u25a0 SCOUT SQUAD\n\u25a0 SPECTRUS KILL TEAM"
            },
            {
                "name": "Rites of Battle",
                "description": "Once per battle round, one unit from your army with this ability can use it when its unit is targeted with a Stratagem. If it does, reduce the CP cost of that use of that Stratagem by 1CP."
            }
        ]
    },
    "Captain in Terminator Armour": {
        "stats": {
            "stat_movement": "5\"",
            "stat_toughness": 5,
            "stat_save": "2+",
            "stat_wounds": 6,
            "stat_leadership": "6+",
            "stat_oc": 1,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
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
                "name": "Combi-weapon",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "1",
                "skill": "4+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Anti-Infantry 4+, Devastating Wounds, Rapid Fire 1"
            },
            {
                "name": "Relic Fist",
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
                "name": "Relic Weapon",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "6",
                "skill": "2+",
                "strength": "5",
                "ap": "-2",
                "damage": "2",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Leader",
                "description": "This model can be attached to the following units:\n\n\u25a0 DEATHWATCH TERMINATOR SQUAD\n\u25a0 DEATHWING KNIGHTS\n\u25a0 DEATHWING TERMINATOR SQUAD\n\u25a0 TERMINATOR ASSAULT SQUAD\n\u25a0 TERMINATOR SQUAD"
            },
            {
                "name": "Unstoppable Valour",
                "description": "You can re-roll Charge rolls made for this model\u2019s unit."
            },
            {
                "name": "Rites of Battle",
                "description": "Once per battle round, one unit from your army with this ability can use it when its unit is targeted with a Stratagem. If it does, reduce the CP cost of that use of that Stratagem by 1CP."
            },
            {
                "name": "Invulnerable Save",
                "description": "4+"
            }
        ]
    },
    "Captain with Jump Pack": {
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
                "name": "Heavy Bolt Pistol",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "4",
                "ap": "-1",
                "damage": "1",
                "keywords": "Pistol"
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
                "name": "Astartes Chainsword",
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
                "name": "Relic Weapon",
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
                "name": "Thunder Hammer",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "5",
                "skill": "3+",
                "strength": "8",
                "ap": "-2",
                "damage": "2",
                "keywords": "Devastating Wounds"
            }
        ],
        "abilities": [
            {
                "name": "Angel's Wrath",
                "description": "While this model is leading a unit, each time that unit ends a Charge move, until the end of the turn, add 1 to the Strength characteristic of melee weapons equipped by models in that unit."
            },
            {
                "name": "Leader",
                "description": "This model can be attached to the following units:\n\n\u25a0 ASSAULT INTERCESSORS WITH JUMP PACKS\n\u25a0 SANGUINARY GUARD\n\u25a0 TALONSTRIKE KILL TEAM\n\u25a0 VANGUARD VETERAN SQUAD WITH JUMP PACKS"
            },
            {
                "name": "Rites of Battle",
                "description": "Once per battle round, one unit from your army with this ability can use it when its unit is targeted with a Stratagem. If it does, reduce the CP cost of that use of that Stratagem by 1CP."
            },
            {
                "name": "Relic Shield",
                "description": "Add 1 to the bearer's Wounds characteristic."
            }
        ]
    },
    "Centurion Assault Squad": {
        "stats": {
            "stat_movement": "4\"",
            "stat_toughness": 7,
            "stat_save": "2+",
            "stat_wounds": 4,
            "stat_leadership": "6+",
            "stat_oc": 2,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Centurion Bolters",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "3",
                "skill": "3+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Rapid Fire 3, Twin-linked"
            },
            {
                "name": "Twin flamer",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "D6",
                "skill": "N/A",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Ignores Cover, Torrent, Twin-linked"
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
                "keywords": "Melta 2, Twin-linked"
            },
            {
                "name": "Siege Drills",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "3",
                "skill": "3+",
                "strength": "10",
                "ap": "-2",
                "damage": "3",
                "keywords": "Twin-linked"
            }
        ],
        "abilities": [
            {
                "name": "Annihilator Protocols",
                "description": "Melee weapons equipped by models in this unit have the [SUSTAINED HITS 2] ability when targeting Monster, Vehicle or Fortification units"
            },
            {
                "name": "Centurion Assault Launchers",
                "description": "The bearer has the Grenades keyword."
            }
        ]
    },
    "Centurion Devastator Squad": {
        "stats": {
            "stat_movement": "4\"",
            "stat_toughness": 7,
            "stat_save": "2+",
            "stat_wounds": 4,
            "stat_leadership": "6+",
            "stat_oc": 2,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Centurion Bolters",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "3",
                "skill": "3+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Rapid Fire 3, Twin-linked"
            },
            {
                "name": "Centurion missile launcher",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "D3",
                "skill": "3+",
                "strength": "9",
                "ap": "-2",
                "damage": "D3",
                "keywords": "Blast"
            },
            {
                "name": "Grav-cannon",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "3",
                "skill": "3+",
                "strength": "6",
                "ap": "-1",
                "damage": "3",
                "keywords": "Anti-vehicle 2+"
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
            },
            {
                "name": "Centurion Fists",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "3",
                "skill": "4+",
                "strength": "5",
                "ap": "-1",
                "damage": "2",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Decimator Protocols",
                "description": "Each time a model in this unit makes a ranged attack, re-roll a Hit roll of 1. If the target of that attack is an enemy unit within range of an objective marker, you can re-roll the Hit roll instead."
            }
        ]
    },
    "Chaplain": {
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
                "name": "Absolvor bolt pistol",
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
                "name": "Crozius arcanum",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "5",
                "skill": "2+",
                "strength": "6",
                "ap": "-1",
                "damage": "2",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Leader",
                "description": "This model can be attached to the following units:\n\n\u25a0 ASSAULT INTERCESSOR SQUAD\n\u25a0 BLADEGUARD VETERAN SQUAD\n\u25a0 CRUSADER SQUAD\n\u25a0 DEATH COMPANY MARINES\n\u25a0 DEATH COMPANY MARINES WITH BOLT RIFLES\n\u25a0 DEATHWATCH VETERANS\n\u25a0 DECIMUS KILL TEAM\n\u25a0 FORTIS KILL TEAM\n\u25a0 HELLBLASTER SQUAD\n\u25a0 INFERNUS SQUAD\n\u25a0 INNER CIRCLE COMPANIONS\n\u25a0 INTERCESSOR SQUAD\n\u25a0 STERNGUARD VETERAN SQUAD\n\u25a0 SWORD BRETHREN SQUAD\n\u25a0 TACTICAL SQUAD"
            },
            {
                "name": "Litany of Hate",
                "description": "While this model is leading a unit, each time a model in that unit makes a melee attack, add 1 to the Wound roll."
            },
            {
                "name": "Spiritual Leader",
                "description": "Once per battle, at the start of any phase, you can select one friendly Adeptus Astartes unit that is Battle-shocked and within 12\" of this model. That unit is no longer Battle-shocked."
            }
        ]
    },
    "Chaplain in Terminator Armour": {
        "stats": {
            "stat_movement": "5\"",
            "stat_toughness": 5,
            "stat_save": "2+",
            "stat_wounds": 5,
            "stat_leadership": "5+",
            "stat_oc": 1,
            "stat_invuln": "4+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Crozius arcanum",
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
                "name": "Recitation of Faith",
                "description": "While this model is leading a unit, models in that unit have the Feel No Pain 4+ ability against mortal wounds."
            },
            {
                "name": "Leader",
                "description": "This model can be attached to the following units:\n\n\u25a0 DEATHWATCH TERMINATOR SQUAD\n\u25a0 DEATHWING KNIGHTS\n\u25a0 DEATHWING TERMINATOR SQUAD\n\u25a0 TERMINATOR ASSAULT SQUAD\n\u25a0 TERMINATOR SQUAD"
            },
            {
                "name": "Litany of Hate",
                "description": "While this model is leading a unit, each time a model in that unit makes a melee attack, add 1 to the Wound roll."
            },
            {
                "name": "Relic Shield",
                "description": "Add 1 to the bearer's Wounds characteristic."
            }
        ]
    },
    "Chaplain on Bike": {
        "stats": {
            "stat_movement": "12\"",
            "stat_toughness": 5,
            "stat_save": "3+",
            "stat_wounds": 5,
            "stat_leadership": "5+",
            "stat_oc": 1,
            "stat_invuln": "4+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Absolvor bolt pistol",
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
                "name": "Crozius arcanum",
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
                "name": "Twin bolt rifle",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "2",
                "skill": "3+",
                "strength": "4",
                "ap": "-1",
                "damage": "1",
                "keywords": "Twin-linked"
            }
        ],
        "abilities": [
            {
                "name": "Catechism of Fire",
                "description": "Each time this model\u2019s unit is selected to shoot, you can select one enemy unit within 12\" of and visible to this model. Until the end of the phase, ranged\nweapons equipped by models in this model\u2019s unit have the [DEVASTATING WOUNDS] ability when targeting that enemy unit."
            },
            {
                "name": "Leader",
                "description": "This model can be attached to the following units:\n\n\u25a0 OUTRIDER SQUAD\n\u25a0 RAVENWING BLACK KNIGHTS"
            },
            {
                "name": "Litany of Hate",
                "description": "While this model is leading a unit, each time a model in that unit makes a melee attack, add 1 to the Wound roll."
            }
        ]
    },
    "Chaplain with Jump Pack": {
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
                "name": "Crozius arcanum",
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
                "name": "Inferno Pistol",
                "weapon_type": "ranged",
                "range": "6\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "8",
                "ap": "-4",
                "damage": "D3",
                "keywords": "Melta 2, Pistol"
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
                "keywords": "Anti-Infantry 4+, Devastating Wounds, Rapid Fire 1"
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
                "name": "Grav-pistol",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "4",
                "ap": "-1",
                "damage": "2",
                "keywords": "Anti-vehicle 2+, Pistol"
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
                "name": "Power fist",
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
                "name": "Bolt pistol",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Close-Quarters"
            },
            {
                "name": "Absolvor bolt pistol",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "5",
                "ap": "-1",
                "damage": "2",
                "keywords": "Pistol"
            }
        ],
        "abilities": [
            {
                "name": "Exhortation of Rage",
                "description": "Each time this model\u2019s unit is selected to fight, you can select one enemy unit within Engagement Range of this model\u2019s unit and roll one D6: on a 4-5, that enemy unit suffers D3 mortal wounds; on a 6, that enemy unit suffers 3 mortal wounds."
            },
            {
                "name": "Leader",
                "description": "This model can be attached to the following units:\n\n\u25a0 ASSAULT INTERCESSORS WITH JUMP PACKS\n\u25a0 DEATH COMPANY MARINES WITH JUMP PACKS\n\u25a0 TALONSTRIKE KILL TEAM\n\u25a0 VANGUARD VETERAN SQUAD WITH JUMP PACKS"
            },
            {
                "name": "Litany of Hate",
                "description": "While this model is leading a unit, each time a model in that unit makes a melee attack, add 1 to the Wound roll."
            }
        ]
    },
    "Company Heroes": {
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
                "name": "Bolt Rifle",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "2",
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
                "keywords": "Close-Quarters"
            },
            {
                "name": "Close combat weapon",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "5",
                "skill": "3+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "Master-crafted Power Weapon",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "6",
                "skill": "2+",
                "strength": "5",
                "ap": "-2",
                "damage": "2",
                "keywords": "Precision"
            },
            {
                "name": "Master-crafted Bolt Rifle",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "2",
                "skill": "2+",
                "strength": "4",
                "ap": "-1",
                "damage": "2",
                "keywords": "Devastating Wounds, Rapid Fire 1"
            },
            {
                "name": "Master-crafted Heavy Bolter",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "3",
                "skill": "3+",
                "strength": "5",
                "ap": "-1",
                "damage": "3",
                "keywords": "Heavy, Sustained Hits 2"
            }
        ],
        "abilities": [
            {
                "name": "Ancient Banner",
                "description": "While this unit contains an Ancient, add 1 to the Objective Control characteristic of models in this unit"
            },
            {
                "name": "Command Squad",
                "description": "While a Character model is leading this unit, each time an attack targets this unit, subtract 1 from the Wound roll."
            }
        ]
    },
    "Desolation Squad": {
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
                "name": "Bolt pistol",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Close-Quarters"
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
                "name": "Castellan Launcher",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "D3",
                "skill": "3+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Blast, Indirect Fire"
            },
            {
                "name": "Superfrag Rocket Launcher",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "D6+1",
                "skill": "4+",
                "strength": "5",
                "ap": "0",
                "damage": "1",
                "keywords": "Blast, Heavy"
            },
            {
                "name": "Superkrak Rocket Launcher",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "1",
                "skill": "4+",
                "strength": "10",
                "ap": "-2",
                "damage": "D6+1",
                "keywords": "Heavy"
            },
            {
                "name": "Vengor launcher",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "D6",
                "skill": "2+",
                "strength": "7",
                "ap": "-1",
                "damage": "2",
                "keywords": "Blast, Indirect Fire"
            }
        ],
        "abilities": [
            {
                "name": "Targeter Optics",
                "description": "Each time this unit Remains Stationary, until the start of your next Movement phase, ranged weapons equipped by models in this unit have the [IGNORES COVER] ability."
            }
        ]
    },
    "Devastator Squad": {
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
                "attacks": "2",
                "skill": "3+",
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
                "keywords": "Close-Quarters"
            },
            {
                "name": "Heavy Bolter",
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
                "name": "Grav-cannon",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "3",
                "skill": "4+",
                "strength": "6",
                "ap": "-1",
                "damage": "3",
                "keywords": "Anti-vehicle 2+, Heavy"
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
                "keywords": "Heavy, Melta 2"
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
                "keywords": "Blast, Heavy"
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
                "keywords": "Blast, Heavy, Hazardous"
            },
            {
                "name": "\u27a4 Missile Launcher - Frag",
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
                "name": "\u27a4 Missile Launcher - Krak",
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
                "name": "Astartes Chainsword",
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
                "name": "Grav-pistol",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "4",
                "ap": "-1",
                "damage": "2",
                "keywords": "Anti-vehicle 2+, Pistol"
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
                "name": "Power fist",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "2",
                "skill": "3+",
                "strength": "8",
                "ap": "-2",
                "damage": "2",
                "keywords": "-"
            },
            {
                "name": "Thunder Hammer",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "2",
                "skill": "4+",
                "strength": "8",
                "ap": "-2",
                "damage": "2",
                "keywords": "Devastating Wounds"
            },
            {
                "name": "Power weapon",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "3",
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
                "keywords": "Anti-Infantry 4+, Devastating Wounds, Rapid Fire 1"
            }
        ],
        "abilities": [
            {
                "name": "Signum",
                "description": "Each time this unit Remains Stationary, until the start of your next Movement phase, ranged weapons equipped by models in this unit have the [IGNORES COVER] ability."
            },
            {
                "name": "Armorium Cherub",
                "description": "Once per battle, after making a Hit roll for a model in this unit, you can change that roll to an unmodified 6."
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
    },
    "Drop Pod": {
        "stats": {
            "stat_movement": "-",
            "stat_toughness": 7,
            "stat_save": "3+",
            "stat_wounds": 8,
            "stat_leadership": "6+",
            "stat_oc": 0,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "abilities": [
            {
                "name": "Drop Pod Assault",
                "description": "This model must start the battle in Reserves and can be set up in the Reinforcements step of your first, second or third Movement phase, regardless of any mission rules. Any units embarked within this model must immediately disembark after it has been set up on the battlefield, and they must be set up more than 8\" away from all enemy models."
            },
            {
                "name": "Transport",
                "description": "This model has a transport capacity of 12 Adeptus Astartes Infantry models. It cannot transport Jump Pack, Wulfen, Gravis, Centurion or Terminator models."
            },
            {
                "name": "Combat Disembarkation",
                "description": "Each time a unit disembarks from this model after it has been set up on the battlefield, that unit is still eligible to declare a charge this turn"
            },
            {
                "name": "Deployment Complete",
                "description": "Once this unit is set up on the battlefield and all units within it have disembarked, until the end of the battle, units cannot embark within this TRANSPORT"
            }
        ]
    },
    "Eliminator Squad": {
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
                "name": "Bolt pistol",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Close-Quarters"
            },
            {
                "name": "Instigator Bolt Carbine",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "4",
                "ap": "-2",
                "damage": "2",
                "keywords": "Precision"
            },
            {
                "name": "Las fusil",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "9",
                "ap": "-3",
                "damage": "D6",
                "keywords": "Heavy"
            },
            {
                "name": "Bolt Sniper Rifle",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "5",
                "ap": "-2",
                "damage": "3",
                "keywords": "Heavy, Precision"
            }
        ],
        "abilities": [
            {
                "name": "Reposition Under Covering Fire",
                "description": "In your Shooting phase, after this unit has shot, if it contains an Eliminator Sergeant equipped with an instigator bolt carbine, this unit can make a\nNormal move. If it does so, until the end of the turn, this unit is not eligible to declare a charge."
            },
            {
                "name": "Mark the Target",
                "description": "Each time this unit Remains Stationary, until the start of your next Movement phase, ranged weapons equipped by models in this unit have the [DEVASTATING WOUNDS] ability."
            },
            {
                "name": "Death in the Dark",
                "description": "INFANTRY PHOBOS unit only. This unit\u2019s attacks that target a hidden unit have +1 to hit rolls."
            }
        ]
    },
    "Eradicator Squad": {
        "stats": {
            "stat_movement": "5\"",
            "stat_toughness": 6,
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
                "keywords": "Close-Quarters"
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
                "name": "Melta rifle",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "9",
                "ap": "-4",
                "damage": "D6",
                "keywords": "Heavy, Melta 2"
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
                "keywords": "Heavy, Melta 2"
            }
        ],
        "abilities": [
            {
                "name": "Total Obliteration",
                "description": "Each time a ranged attack made by a model in this unit targets a Monster or Vehicle model, you can re-roll the Hit roll, you can re-roll the Wound roll and you can re-roll the Damage roll."
            }
        ]
    },
    "Eradicator Squad with Heavy Bolters": {
        "stats": {
            "stat_movement": "5\"",
            "stat_toughness": 6,
            "stat_save": "3+",
            "stat_wounds": 3,
            "stat_leadership": "6+",
            "stat_oc": 1,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Heavy Bolter",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "3",
                "skill": "3+",
                "strength": "5",
                "ap": "-1",
                "damage": "2",
                "keywords": "Heavy, Sustained Hits 1"
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
                "keywords": "Close-Quarters"
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
            }
        ],
        "abilities": [
            {
                "name": "Overlapping Detonations",
                "description": "In your Shooting phase, when this unit is selected to shoot you can select one non-MONSTER/VEHICLE enemy unit visible to it. While making attacks, this unit\u2019s heavy bolters that targeted that selected unit have [BLAST 1]."
            }
        ]
    },
    "Firestrike Servo-Turrets": {
        "stats": {
            "stat_movement": "3\"",
            "stat_toughness": 6,
            "stat_save": "2+",
            "stat_wounds": 6,
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
                "name": "Twin Firestrike Las-talon",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "2",
                "skill": "2+",
                "strength": "10",
                "ap": "-3",
                "damage": "D6+1",
                "keywords": "Twin-linked"
            },
            {
                "name": "Twin Firestrike Autocannon",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "3",
                "skill": "2+",
                "strength": "9",
                "ap": "-1",
                "damage": "3",
                "keywords": "Twin-linked"
            }
        ],
        "abilities": [
            {
                "name": "Sentinel Protocols",
                "description": "Each time you select this unit for the Fire Overwatch Stratagem, hits are scored on unmodified Hit rolls of 4+ when resolving that Stratagem."
            }
        ]
    },
    "Gladiator Lancer": {
        "stats": {
            "stat_movement": "10\"",
            "stat_toughness": 10,
            "stat_save": "3+",
            "stat_wounds": 12,
            "stat_leadership": "6+",
            "stat_oc": 3,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Lancer Laser Destroyer",
                "weapon_type": "ranged",
                "range": "72\"",
                "attacks": "2",
                "skill": "3+",
                "strength": "14",
                "ap": "-4",
                "damage": "D6+3",
                "keywords": "Heavy"
            },
            {
                "name": "Armoured Hull",
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
                "name": "Icarus Rocket Pod",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "D3",
                "skill": "3+",
                "strength": "8",
                "ap": "-1",
                "damage": "2",
                "keywords": "Anti-fly 2+"
            },
            {
                "name": "Ironhail Heavy Stubber",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "3",
                "skill": "3+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Rapid Fire 3"
            },
            {
                "name": "Fragstorm grenade launcher",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "D6",
                "skill": "3+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Blast"
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
                "name": "Aqullon Optics",
                "description": "Each time this model is selected to shoot, you can re-roll one Hit roll, you can re-roll one Wound roll and you can re-roll one Damage roll when resolving its attacks"
            },
            {
                "name": "Damaged: 1-4 Wounds Remaining",
                "description": "While this model has 1-4 wounds remaining, each time this model makes an attack, subtract 1 from the Hit roll."
            }
        ]
    },
    "Gladiator Reaper": {
        "stats": {
            "stat_movement": "10\"",
            "stat_toughness": 10,
            "stat_save": "3+",
            "stat_wounds": 12,
            "stat_leadership": "6+",
            "stat_oc": 3,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Tempest Bolter",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "4",
                "skill": "3+",
                "strength": "4",
                "ap": "-1",
                "damage": "1",
                "keywords": "Rapid Fire 4"
            },
            {
                "name": "Twin Heavy Onslaught Gatling Cannon",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "12",
                "skill": "3+",
                "strength": "6",
                "ap": "0",
                "damage": "1",
                "keywords": "Devastating Wounds, Twin-linked"
            },
            {
                "name": "Armoured Hull",
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
                "name": "Icarus Rocket Pod",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "D3",
                "skill": "3+",
                "strength": "8",
                "ap": "-1",
                "damage": "2",
                "keywords": "Anti-fly 2+"
            },
            {
                "name": "Ironhail Heavy Stubber",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "3",
                "skill": "3+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Rapid Fire 3"
            }
        ],
        "abilities": [
            {
                "name": "Rotating Death",
                "description": "This model\u2019s twin heavy onslaught gatling cannon has the [SUSTAINED HITS 2] ability when targeting Infantry units."
            },
            {
                "name": "Damaged: 1-4 Wounds Remaining",
                "description": "While this model has 1-4 wounds remaining, each time this model makes an attack, subtract 1 from the Hit roll."
            }
        ]
    },
    "Gladiator Valiant": {
        "stats": {
            "stat_movement": "10\"",
            "stat_toughness": 10,
            "stat_save": "3+",
            "stat_wounds": 12,
            "stat_leadership": "6+",
            "stat_oc": 3,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Twin Las-talon",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "2",
                "skill": "3+",
                "strength": "10",
                "ap": "-3",
                "damage": "D6+1",
                "keywords": "Twin-linked"
            },
            {
                "name": "Armoured Hull",
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
                "name": "Icarus Rocket Pod",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "D3",
                "skill": "3+",
                "strength": "8",
                "ap": "-1",
                "damage": "2",
                "keywords": "Anti-fly 2+"
            },
            {
                "name": "Ironhail Heavy Stubber",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "3",
                "skill": "3+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Rapid Fire 3"
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
            }
        ],
        "abilities": [
            {
                "name": "Ferocious Assault",
                "description": "Each time this model makes an attack with its twin las-talon that targets the closest eligible Monster or Vehicle unit, add 1 to the Hit roll"
            },
            {
                "name": "Damaged: 1-4 Wounds Remaining",
                "description": "While this model has 1-4 wounds remaining, each time this model makes an attack, subtract 1 from the Hit roll."
            }
        ]
    },
    "Hammerfall Bunker": {
        "stats": {
            "stat_movement": "-",
            "stat_toughness": 12,
            "stat_save": "2+",
            "stat_wounds": 14,
            "stat_leadership": "6+",
            "stat_oc": 0,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "\u27a4 Hammerfall Missile Launcher - Superfrag",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "2d6+2",
                "skill": "4+",
                "strength": "5",
                "ap": "0",
                "damage": "1",
                "keywords": "Blast"
            },
            {
                "name": "\u27a4 Hammerfall Missile Launcher - Superkrak",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "2",
                "skill": "4+",
                "strength": "10",
                "ap": "-2",
                "damage": "D6+1",
                "keywords": "-"
            },
            {
                "name": "Hammerfall Heavy Bolter Array",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "6",
                "skill": "4+",
                "strength": "5",
                "ap": "-1",
                "damage": "2",
                "keywords": "Defensive Array, Sustained Hits 1, Twin-linked"
            },
            {
                "name": "Hammerfall Heavy Flamer Array",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "2D6",
                "skill": "N/A",
                "strength": "5",
                "ap": "-1",
                "damage": "1",
                "keywords": "Defensive Array, Ignores Cover, Torrent, Twin-linked"
            }
        ],
        "abilities": [
            {
                "name": "Fortification",
                "description": "While an enemy unit is only within Engagement Range of one or more Fortifications from your army:\n\u25a0 That unit can still be selected as the target of ranged attacks, but each time such an attack is made, unless it is made with a Pistol, subtract 1 from the Hit roll.\n\u25a0 Models in that unit do not need to take Desperate Escape tests due to Falling Back while Battle-shocked, except for those that will move over enemy models when doing so."
            },
            {
                "name": "Ceramite Cover",
                "description": "Each time a ranged attack is allocated to a model, if that model is not fully visible to every model in the attacking unit because of this Fortification, that model has the Benefit of Cover against that attack."
            },
            {
                "name": "Damaged: 1-4 Wounds Remaining",
                "description": "While this model has 1-4 wounds remaining, each time this model makes an attack, subtract 1 from the Hit roll."
            },
            {
                "name": "Defensive Array",
                "description": "You can target this Fortification with the Fire Overwatch Strategem for 0CP, and can do so even if you have already targeted another unit with that Stratagem this turn. This Fortification can only be targeted with that Stratagem once per turn."
            }
        ]
    },
    "Heavy Intercessor Squad": {
        "stats": {
            "stat_movement": "5\"",
            "stat_toughness": 6,
            "stat_save": "3+",
            "stat_wounds": 3,
            "stat_leadership": "6+",
            "stat_oc": 2,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Heavy Bolt Rifle",
                "weapon_type": "ranged",
                "range": "30\"",
                "attacks": "2",
                "skill": "3+",
                "strength": "5",
                "ap": "-1",
                "damage": "2",
                "keywords": "Assault, Heavy"
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
                "keywords": "Close-Quarters"
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
                "name": "Heavy Bolter",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "3",
                "skill": "3+",
                "strength": "5",
                "ap": "-1",
                "damage": "2",
                "keywords": "Assault, Heavy, Sustained Hits 1"
            }
        ],
        "abilities": [
            {
                "name": "Unyielding in the Face of the Foe",
                "description": "While this unit is within range of an objective marker you control, each time an attack with a Damage characteristic of 1 is allocated to a model in\nthis unit, add 1 to any armour saving throw made against that attack."
            }
        ]
    },
    "Hellblaster Squad": {
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
                "name": "Bolt pistol",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Close-Quarters"
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
                "name": "\u27a4 Plasma Incinerator - Standard",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "2",
                "skill": "3+",
                "strength": "7",
                "ap": "-2",
                "damage": "1",
                "keywords": "Assault, Heavy"
            },
            {
                "name": "\u27a4 Plasma Incinerator - Supercharge",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "2",
                "skill": "3+",
                "strength": "8",
                "ap": "-3",
                "damage": "2",
                "keywords": "Assault, Heavy, Hazardous"
            }
        ],
        "abilities": [
            {
                "name": "For the Chapter!",
                "description": "Each time a model in this unit is destroyed, roll one D6: on a 3+, do not remove it from play. The destroyed model can shoot after the attacking model\u2019s unit has finished making its attacks, and is then removed from play. When resolving these attacks, any Hazardous tests taken for that attack are automatically passed."
            }
        ]
    },
    "Impulsor": {
        "stats": {
            "stat_movement": "12\"",
            "stat_toughness": 9,
            "stat_save": "3+",
            "stat_wounds": 11,
            "stat_leadership": "6+",
            "stat_oc": 2,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Armoured Hull",
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
                "name": "Ironhail Heavy Stubber",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "3",
                "skill": "3+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Rapid Fire 3"
            },
            {
                "name": "Ironhail Skytalon Array",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "8",
                "skill": "3+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Anti-Fly 4+, Sustained Hits 1"
            },
            {
                "name": "\u27a4 Bellicatus Missile Array - Frag",
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
                "name": "\u27a4 Bellicatus Missile Array - Icarus",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "D3",
                "skill": "3+",
                "strength": "8",
                "ap": "-1",
                "damage": "2",
                "keywords": "Anti-Fly 2+"
            },
            {
                "name": "\u27a4 Bellicatus Missile Array - Krak",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "8",
                "ap": "-2",
                "damage": "D6",
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
            },
            {
                "name": "Fragstorm grenade launcher",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "D6",
                "skill": "3+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Blast"
            }
        ],
        "abilities": [
            {
                "name": "Transport",
                "description": "This model has a transport capacity of 7 TACTICUS or PHOBOS INFANTRY models. It cannot transport JUMP PACK models."
            },
            {
                "name": "Assault Vehicle",
                "description": "Units can disembark from this Transport after it has Advanced. Units that do so count as having made a Normal move, and cannot declare a charge that turn."
            },
            {
                "name": "Orbital Comms Array [Aura]",
                "description": "While a friendly Adeptus Astartes unit is within 6\" of the bearer, each time you target that unit with a Stratagem, roll one D6: on a 5+, you gain 1CP"
            },
            {
                "name": "Shield Dome",
                "description": "The bearer has a 5+ invulnerable save."
            }
        ]
    },
    "Inceptor Squad": {
        "stats": {
            "stat_movement": "10\"",
            "stat_toughness": 6,
            "stat_save": "3+",
            "stat_wounds": 3,
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
                "name": "Assault Bolters",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "3",
                "skill": "3+",
                "strength": "5",
                "ap": "-1",
                "damage": "2",
                "keywords": "Assault, Pistol, Sustained Hits 2, Twin-linked"
            },
            {
                "name": "\u27a4 Plasma Exterminators - Standard",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "2",
                "skill": "3+",
                "strength": "7",
                "ap": "-2",
                "damage": "2",
                "keywords": "Assault, Pistol, Twin-linked"
            },
            {
                "name": "\u27a4 Plasma Exterminators - Supercharge",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "2",
                "skill": "3+",
                "strength": "8",
                "ap": "-3",
                "damage": "3",
                "keywords": "Assault, Pistol, Hazardous, Twin-linked"
            }
        ],
        "abilities": [
            {
                "name": "Meteoric Descent",
                "description": "In your Movement phase, when this unit is set up on the battlefield using the Deep Strike ability, it can perform a meteoric descent. If it does, this unit can be set up anywhere on the battlefield that is more than 6\" horizontally away from all enemy units, but until the end of the turn, it is not eligible to declare a charge."
            }
        ]
    },
    "Incursor Squad": {
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
                "name": "Occulus Bolt Carbine",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "2",
                "skill": "3+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Assault, Ignores Cover"
            },
            {
                "name": "Paired Combat Blades",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "3",
                "skill": "3+",
                "strength": "4",
                "ap": "-1",
                "damage": "1",
                "keywords": "Sustained Hits 1"
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
                "keywords": "Close-Quarters"
            }
        ],
        "abilities": [
            {
                "name": "Multi-spectrum Array",
                "description": "In your Shooting phase, after this unit has shot, select one enemy unit that was hit by one or more attacks made by this unit this phase. Until the end of the phase, each time a friendly Adeptus Astartes unit makes an attack that targets that enemy unit, add 1 to the Hit roll."
            },
            {
                "name": "Haywire Mine",
                "description": "Once per battle, at the start of any phase, you can select one enemy unit within 3\" of the bearer and roll one D6: on a 2+, that enemy unit suffers D3 mortal wounds, or 2D3 mortal wounds instead if it is a Vehicle unit."
            },
            {
                "name": "Death in the Dark",
                "description": "INFANTRY PHOBOS unit only. This unit\u2019s attacks that target a hidden unit have +1 to hit rolls."
            }
        ]
    },
    "Infernus Squad": {
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
                "name": "Pyreblaster",
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
                "name": "Bolt pistol",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Close-Quarters"
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
            }
        ],
        "abilities": [
            {
                "name": "Purge the Foe",
                "description": "In your Shooting phase, after this unit has shot, you can select one enemy Infantry unit hit by one or more of those attacks made with a pyreblaster. That enemy unit must take a Battle-shock test, subtracting 1 from that test."
            }
        ]
    },
    "Infiltrator Squad": {
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
                "name": "Marksman Bolt Carbine",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "2",
                "skill": "3+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Heavy"
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
                "keywords": "Close-Quarters"
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
            }
        ],
        "abilities": [
            {
                "name": "Omni-scramblers",
                "description": "Enemy units that are set up on the battlefield from Reserves cannot be set up within 12\" of this unit."
            },
            {
                "name": "Helix Gauntlet",
                "description": "Models in the bearer\u2019s unit have the Feel No Pain 6+ ability."
            },
            {
                "name": "Infiltrator Comms Array",
                "description": "Each time you target the bearer\u2019s unit with a Stratagem, roll one D6: on a 5+, you gain 1CP"
            },
            {
                "name": "Death in the Dark",
                "description": "INFANTRY PHOBOS unit only. This unit\u2019s attacks that target a hidden unit have +1 to hit rolls."
            }
        ]
    },
    "Intercessor Squad": {
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
                "name": "Bolt pistol",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Close-Quarters"
            },
            {
                "name": "Bolt Rifle",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "2",
                "skill": "3+",
                "strength": "4",
                "ap": "-1",
                "damage": "1",
                "keywords": "Assault, Heavy"
            },
            {
                "name": "\u27a4 Astartes grenade launcher - krak",
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
                "name": "\u27a4 Astartes grenade launcher - frag",
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
                "name": "Power weapon",
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
                "name": "Astartes Chainsword",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "5",
                "skill": "3+",
                "strength": "4",
                "ap": "-1",
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
                "name": "Thunder Hammer",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "3",
                "skill": "4+",
                "strength": "8",
                "ap": "-2",
                "damage": "2",
                "keywords": "Devastating Wounds"
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
            }
        ],
        "abilities": [
            {
                "name": "Objective Secured",
                "description": "If you control an objective marker at the end of your Command phase and this unit is within range of that objective marker, that objective marker remains under your control, even if you have no models within range of it, until your opponent controls it at the start or end of any turn."
            },
            {
                "name": "Hail of Bolts",
                "description": "In your Shooting phase, when this unit is selected to shoot, select up to one visible enemy unit. While making those attacks, this unit\u2019s Bolt Rifle attacks that targeted that enemy unit have +2 A"
            }
        ]
    },
    "Invader ATV": {
        "stats": {
            "stat_movement": "12\"",
            "stat_toughness": 5,
            "stat_save": "3+",
            "stat_wounds": 8,
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
                "keywords": "Close-Quarters"
            },
            {
                "name": "Twin bolt rifle",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "2",
                "skill": "3+",
                "strength": "4",
                "ap": "-1",
                "damage": "1",
                "keywords": "Twin-linked"
            },
            {
                "name": "Close combat weapon",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "5",
                "skill": "3+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "Onslaught gatling cannon",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "8",
                "skill": "3+",
                "strength": "5",
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
            }
        ],
        "abilities": [
            {
                "name": "Outrider Escort",
                "description": "Once per turn, in your opponent's Shooting phase, when another friendly Adeptus Astartes Mounted unit within 6\" of this model is selected as the target of an attack, one model from your army with this ability can use it. If it does, after that enemy unit has finished making its attacks, that model can shoot as if it were your Shooting phase , but when resolving those attacks it can only target that enemy unit [and only if it is an eligible target)."
            }
        ]
    },
    "Invictor Tactical Warsuit": {
        "stats": {
            "stat_movement": "8\"",
            "stat_toughness": 8,
            "stat_save": "3+",
            "stat_wounds": 12,
            "stat_leadership": "6+",
            "stat_oc": 4,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Invictor Fist",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "5",
                "skill": "3+",
                "strength": "14",
                "ap": "-2",
                "damage": "3",
                "keywords": "-"
            },
            {
                "name": "Fragstorm grenade launcher",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "D6",
                "skill": "3+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Blast"
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
                "keywords": "Sustained Hits 1"
            },
            {
                "name": "Twin Ironhail Heavy Stubber",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "3",
                "skill": "3+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Rapid Fire 3, Twin-linked"
            },
            {
                "name": "Incendium Cannon",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "D6+3",
                "skill": "N/A",
                "strength": "6",
                "ap": "-1",
                "damage": "1",
                "keywords": "Ignores Cover, Torrent"
            },
            {
                "name": "Twin Ironhail Autocannon",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "3",
                "skill": "3+",
                "strength": "9",
                "ap": "-1",
                "damage": "3",
                "keywords": "Twin-linked"
            }
        ],
        "abilities": [
            {
                "name": "Combat Support",
                "description": "Once per turn, in your opponent\u2019s Shooting phase, when a friendly Adeptus Astartes Phobos Infantry unit within 6\" of this model is selected as the target of an attack, this model can use this ability. If it does, after that enemy model\u2019s unit has finished making its attacks, this model can shoot as if it were your Shooting phase, but when resolving those attacks it can only target that enemy unit (and only if it is an eligible target)."
            },
            {
                "name": "Damaged: 1-4 Wounds Remaining",
                "description": "While this model has 1-4 wounds remaining, each time this model makes an attack, subtract 1 from the Hit roll."
            }
        ]
    },
    "Land Raider": {
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
                "name": "Godhammer Lascannon",
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
                "name": "Armoured Tracks",
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
                "name": "Hunter-killer missile",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "1",
                "skill": "2+",
                "strength": "14",
                "ap": "-3",
                "damage": "D6",
                "keywords": "One Shot"
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
                "name": "Twin heavy bolter",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "3",
                "skill": "3+",
                "strength": "5",
                "ap": "-1",
                "damage": "2",
                "keywords": "Sustained Hits 1, Twin-linked"
            }
        ],
        "abilities": [
            {
                "name": "Assault Ramp",
                "description": "Each time a unit disembarks from this model after it has made a Normal move, that unit is still eligible to declare a charge this turn."
            },
            {
                "name": "Transport",
                "description": "This model has a transport capacity of 12 Adeptus Astartes Infantry models. Each Jump Pack, Wulfen, Gravis or Terminator model takes up the space of 2 models and each Centurion model takes up the space of 3 models."
            },
            {
                "name": "Damaged: 1-5 Wounds Remaining",
                "description": "While this model has 1-5 wounds remaining, each time this model makes an attack, subtract 1 from the Hit roll."
            }
        ]
    },
    "Land Raider Crusader": {
        "stats": {
            "stat_movement": "12\"",
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
                "name": "Armoured Tracks",
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
                "name": "Hunter-killer missile",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "1",
                "skill": "2+",
                "strength": "14",
                "ap": "-3",
                "damage": "D6",
                "keywords": "One Shot"
            },
            {
                "name": "Hurricane Bolter",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "6",
                "skill": "3+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Rapid Fire 6, Twin-linked"
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
                "name": "Twin assault cannon",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "6",
                "skill": "3+",
                "strength": "6",
                "ap": "0",
                "damage": "1",
                "keywords": "Devastating wounds, Twin-linked"
            }
        ],
        "abilities": [
            {
                "name": "Transport",
                "description": "This model has a transport capacity of 16 Adeptus Astartes Infantry models. Each Jump Pack, Wulfen, Gravis or Terminator model takes up the space of 2 models and each Centurion model takes up the space of 3 models."
            },
            {
                "name": "Assault Ramp",
                "description": "Each time a unit disembarks from this model after it has made a Normal move, that unit is still eligible to declare a charge this turn."
            },
            {
                "name": "Damaged: 1-5 Wounds Remaining",
                "description": "While this model has 1-5 wounds remaining, each time this model makes an attack, subtract 1 from the Hit roll."
            }
        ]
    },
    "Land Raider Redeemer": {
        "stats": {
            "stat_movement": "12\"",
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
                "name": "Flamestorm Cannon",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "D6+3",
                "skill": "N/A",
                "strength": "6",
                "ap": "-2",
                "damage": "2",
                "keywords": "Ignores Cover, Torrent"
            },
            {
                "name": "Armoured Tracks",
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
                "name": "Hunter-killer missile",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "1",
                "skill": "2+",
                "strength": "14",
                "ap": "-3",
                "damage": "D6",
                "keywords": "One Shot"
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
                "name": "Twin assault cannon",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "6",
                "skill": "3+",
                "strength": "6",
                "ap": "0",
                "damage": "1",
                "keywords": "Devastating wounds, Twin-linked"
            }
        ],
        "abilities": [
            {
                "name": "Transport",
                "description": "This model has a transport capacity of 14 Adeptus Astartes Infantry models. Each Jump Pack, Wulfen, Gravis or Terminator model takes up the space of 2 models and each Centurion model takes up the space of 3 models."
            },
            {
                "name": "Assault Ramp",
                "description": "Each time a unit disembarks from this model after it has made a Normal move, that unit is still eligible to declare a charge this turn."
            },
            {
                "name": "Damaged: 1-5 Wounds Remaining",
                "description": "While this model has 1-5 wounds remaining, each time this model makes an attack, subtract 1 from the Hit roll."
            }
        ]
    },
    "Land Speeder": {
        "stats": {
            "stat_movement": "14\"",
            "stat_toughness": 8,
            "stat_save": "3+",
            "stat_wounds": 9,
            "stat_leadership": "6+",
            "stat_oc": 3,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Stormfury Missile Launcher",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "12",
                "ap": "-3",
                "damage": "D6+1"
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
                "name": "Close combat weapon",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "3+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
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
                "name": "Onslaught gatling cannon",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "8",
                "skill": "3+",
                "strength": "5",
                "ap": "0",
                "damage": "1",
                "keywords": "Devastating Wounds"
            }
        ],
        "abilities": [
            {
                "name": "Purgation Run",
                "description": "In your Shooting phase, after this unit has shot, it can make a normal move of up to D6\". If it does,\nuntil the end of the turn, this unit is not eligible to declare a charge."
            }
        ]
    },
    "Librarian": {
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
                "keywords": "Close-Quarters"
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
                "name": "\u27a4 Smite - Witchfire",
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
                "name": "\u27a4 Smite - Focused Witchfire",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "D6",
                "skill": "3+",
                "strength": "6",
                "ap": "-2",
                "damage": "D3",
                "keywords": "Devastating Wounds, Hazardous, Psychic"
            }
        ],
        "abilities": [
            {
                "name": "Mental Fortress [Psychic]",
                "description": "While this model is leading a unit, models in that unit have a 4+ invulnerable save."
            },
            {
                "name": "Leader",
                "description": "This model can be attached to the following units:\n\n\u25a0 ASSAULT INTERCESSOR SQUAD\n\u25a0 DEATHWATCH VETERANS\n\u25a0 DECIMUS KILL TEAM\n\u25a0 DESOLATION SQUAD\n\u25a0 DEVASTATOR SQUAD\n\u25a0 FORTIS KILL TEAM\n\u25a0 HELLBLASTER SQUAD\n\u25a0 INFERNUS SQUAD\n\u25a0 INNER CIRCLE COMPANIONS\n\u25a0 INTERCESSOR SQUAD\n\u25a0 STERNGUARD VETERAN SQUAD\n\u25a0 TACTICAL SQUAD"
            },
            {
                "name": "Psychic Hood",
                "description": "While this model is leading a unit, models in that unit have the Feel No Pain 4+ ability against Psychic Attacks."
            }
        ]
    },
    "Librarian in Phobos Armour": {
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
                "keywords": "Close-Quarters"
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
                "name": "\u27a4 Smite - Witchfire",
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
                "name": "\u27a4 Smite - Focused Witchfire",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "D6",
                "skill": "3+",
                "strength": "6",
                "ap": "-2",
                "damage": "D3",
                "keywords": "Devastating Wounds, Hazardous, Psychic"
            }
        ],
        "abilities": [
            {
                "name": "Shrouding [Psychic]",
                "description": "While this model is leading a unit, models in that unit have the Stealth ability and that unit cannot be targeted by ranged attacks unless the attacking\nmodel is within 12\"."
            },
            {
                "name": "Leader",
                "description": "This model can be attached to the following units:\n\n\u25a0 ELIMINATOR SQUAD\n\u25a0 INCURSOR SQUAD\n\u25a0 INFILTRATOR SQUAD\n\u25a0 REIVER SQUAD\n\u25a0 SPECTRUS KILL TEAM"
            },
            {
                "name": "Psychic Hood",
                "description": "While this model is leading a unit, models in that unit have the Feel No Pain 4+ ability against Psychic Attacks."
            }
        ]
    },
    "Librarian in Terminator Armour": {
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
                "name": "\u27a4 Smite - Witchfire",
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
                "name": "\u27a4 Smite - Focused Witchfire",
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
                "name": "Combi-weapon",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "1",
                "skill": "4+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Anti-Infantry 4+, Devastating Wounds, Rapid Fire 1"
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
                "name": "Veil of Time [Psychic]",
                "description": "While this model is leading a unit, weapons equipped by models in that unit have the [SUSTAINED HITS 1] ability."
            },
            {
                "name": "Leader",
                "description": "This model can be attached to the following units:\n\n\u25a0 DEATHWATCH TERMINATOR SQUAD\n\u25a0 DEATHWING KNIGHTS\n\u25a0 DEATHWING TERMINATOR SQUAD\n\u25a0 TERMINATOR ASSAULT SQUAD\n\u25a0 TERMINATOR SQUAD"
            },
            {
                "name": "Psychic Hood",
                "description": "While this model is leading a unit, models in that unit have the Feel No Pain 4+ ability against Psychic Attacks."
            }
        ]
    },
    "Lieutenant": {
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
                "name": "Neo-volkite Pistol",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "1",
                "skill": "2+",
                "strength": "5",
                "ap": "0",
                "damage": "2",
                "keywords": "Devastating Wounds, Pistol"
            },
            {
                "name": "Master-crafted power weapon",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "5",
                "skill": "2+",
                "strength": "5",
                "ap": "-2",
                "damage": "2",
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
                "name": "Heavy Bolt Pistol",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "1",
                "skill": "2+",
                "strength": "4",
                "ap": "-1",
                "damage": "1",
                "keywords": "Pistol"
            },
            {
                "name": "Close combat weapon",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "5",
                "skill": "2+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "Power fist",
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
                "name": "Master-crafted bolter",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "2",
                "skill": "2+",
                "strength": "4",
                "ap": "-1",
                "damage": "2",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Support",
                "description": "This model can be attached to the following units:\n\n\u25a0 ASSAULT INTERCESSOR SQUAD\n\u25a0 BLADEGUARD VETERAN SQUAD\n\u25a0 COMPANY HEROES\n\u25a0 CRUSADER SQUAD\n\u25a0 DEATHWATCH VETERANS\n\u25a0 DECIMUS KILL TEAM\n\u25a0 FORTIS KILL TEAM\n\u25a0 HELLBLASTER SQUAD\n\u25a0 INFERNUS SQUAD\n\u25a0 INNER CIRCLE COMPANIONS\n\u25a0 INTERCESSOR SQUAD\n\u25a0 STERNGUARD VETERAN SQUAD\n\u25a0 SWORD BRETHREN SQUAD\n\u25a0 TACTICAL SQUAD\n\nYou can attach this model to a unit it can lead even if one Captain or Chapter Master model has already been attached to it. If you do, and that Bodyguard unit is destroyed, the Leader units attached to it become separate units, with their original Starting Strengths."
            },
            {
                "name": "Target Priority",
                "description": "This model\u2019s unit is eligible to shoot and declare a charge in a turn in which it Fell Back"
            },
            {
                "name": "Tactical Precision",
                "description": "While this model is leading a unit, weapons equipped by models in that unit have the [LETHAL HITS] ability."
            },
            {
                "name": "Storm Shield",
                "description": "The bearer has a 4+ invulnerable save"
            }
        ]
    },
    "Lieutenant in Reiver Armour": {
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
                "name": "Combat Knife",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "6",
                "skill": "2+",
                "strength": "4",
                "ap": "-1",
                "damage": "1",
                "keywords": "Precision"
            },
            {
                "name": "Master-crafted Special Issue Bolt Pistol",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "1",
                "skill": "2+",
                "strength": "4",
                "ap": "-1",
                "damage": "2",
                "keywords": "Pistol, Precision"
            }
        ],
        "abilities": [
            {
                "name": "Deadly Terror",
                "description": "While this model is leading a unit, increase the range of that unit\u2019s Terror Troops ability by 3\"."
            },
            {
                "name": "Support",
                "description": "This model can be attached to the following unit:\n\n\u25a0 REIVER SQUAD\n\nYou can attach this model a unit it can lead even if one Captain or Chapter Master model has already been attached to it. If you do, and that Bodyguard unit is destroyed, the Leader units attached to it become separate units, with their original Starting Strengths."
            },
            {
                "name": "Tactical Precision",
                "description": "While this model is leading a unit, weapons equipped by models in that unit have the [LETHAL HITS] ability."
            }
        ]
    },
    "Outrider Squad": {
        "stats": {
            "stat_movement": "12\"",
            "stat_toughness": 5,
            "stat_save": "3+",
            "stat_wounds": 8,
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
                "keywords": "Close-Quarters"
            },
            {
                "name": "Twin bolt rifle",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "2",
                "skill": "3+",
                "strength": "4",
                "ap": "-1",
                "damage": "1",
                "keywords": "Twin-linked"
            },
            {
                "name": "Close combat weapon",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "5",
                "skill": "3+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "Onslaught gatling cannon",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "8",
                "skill": "3+",
                "strength": "5",
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
                "name": "Astartes Chainsword",
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
                "name": "Heavy Bolt Pistol",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "4",
                "ap": "-1",
                "damage": "1",
                "keywords": "Pistol"
            }
        ],
        "abilities": [
            {
                "name": "Thunderous Impact",
                "description": "Each time a model in this unit makes a melee attack, if this unit made a Charge move this turn, improve the Strength and Damage characteristics of that attack by 1"
            }
        ]
    },
    "Predator Annihilator": {
        "stats": {
            "stat_movement": "10",
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
                "name": "Predator Twin Lascannon",
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
                "name": "Armoured Tracks",
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
                "name": "Heavy Bolter",
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
                "name": "Annihilator",
                "description": "Each time a ranged attack made by this model is allocated to a Monster or Vehicle model, you can re-roll the Damage roll"
            },
            {
                "name": "Damaged: 1-4 Wounds Remaining",
                "description": "While this model has 1-4 wounds remaining, each time this model makes an attack, subtract 1 from the Hit roll."
            }
        ]
    },
    "Predator Destructor": {
        "stats": {
            "stat_movement": "10",
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
                "name": "Predator Autocannon",
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
                "name": "Armoured Tracks",
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
                "name": "Heavy Bolter",
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
                "name": "Destructor",
                "description": "Each time this model makes a ranged attack that targets an Infantry unit, improve the Armour Penetration characteristic of that attack by 1."
            },
            {
                "name": "Damaged: 1-4 Wounds Remaining",
                "description": "While this model has 1-4 wounds remaining, each time this model makes an attack, subtract 1 from the Hit roll."
            }
        ]
    },
    "Razorback": {
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
                "name": "Armoured Tracks",
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
                "name": "Fire Support",
                "description": "In your Shooting phase, after this model has shot, select one enemy unit it scored one or more hits against this phase. Until the end of the phase, each time a friendly model that disembarked from this Transport this turn makes an attack that targets that enemy unit, you can re-roll the Wound roll."
            },
            {
                "name": "Transport",
                "description": "This model has a transport capacity of 6 Adeptus Astartes Infantry models. It cannot transport JUMP PACK, WULFEN, PHOBOS, GRAVIS, CENTURION, TERMINATOR or TACTICUS models (excluding TACTICUS CHARACTER models that began the battle attached to a non-TACTICUS unit)"
            }
        ]
    },
    "Redemptor Dreadnought": {
        "stats": {
            "stat_movement": "8\"",
            "stat_toughness": 10,
            "stat_save": "2+",
            "stat_wounds": 12,
            "stat_leadership": "6+",
            "stat_oc": 4,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Redemptor Fist",
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
                "name": "Icarus Rocket Pod",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "D3",
                "skill": "3+",
                "strength": "8",
                "ap": "-1",
                "damage": "2",
                "keywords": "Anti-fly 2+"
            },
            {
                "name": "\u27a4 Macro Plasma Incinerator - Standard",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "D6+1",
                "skill": "3+",
                "strength": "8",
                "ap": "-3",
                "damage": "2",
                "keywords": "Blast"
            },
            {
                "name": "\u27a4 Macro Plasma Incinerator - Supercharge",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "D6+1",
                "skill": "3+",
                "strength": "9",
                "ap": "-4",
                "damage": "3",
                "keywords": "Blast, Hazardous"
            },
            {
                "name": "Heavy Onslaught Gatling Cannon",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "12",
                "skill": "3+",
                "strength": "6",
                "ap": "0",
                "damage": "1",
                "keywords": "Devastating Wounds"
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
                "name": "Onslaught gatling cannon",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "8",
                "skill": "3+",
                "strength": "5",
                "ap": "0",
                "damage": "1",
                "keywords": "Devastating Wounds"
            },
            {
                "name": "Twin Fragstorm Grenade Launcher",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "D6",
                "skill": "3+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Blast, Twin-linked"
            },
            {
                "name": "Twin Storm Bolter",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "2",
                "skill": "3+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Rapid Fire 2, Twin-linked"
            }
        ],
        "abilities": [
            {
                "name": "Duty Eternal",
                "description": "Each time an attack is allocated to this model, subtract 1 from the Damage characteristic of that attack"
            },
            {
                "name": "Damaged: 1-4 Wounds Remaining",
                "description": "While this model has 1-4 wounds remaining, each time this model makes an attack, subtract 1 from the Hit roll."
            }
        ]
    },
    "Reiver Squad": {
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
                "name": "Special Issue Bolt Pistol",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "4",
                "ap": "-1",
                "damage": "1",
                "keywords": "Pistol, Precision"
            },
            {
                "name": "Combat Knife",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "3+",
                "strength": "4",
                "ap": "-1",
                "damage": "1",
                "keywords": "Precision"
            },
            {
                "name": "Bolt Carbine",
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
            }
        ],
        "abilities": [
            {
                "name": "Fearsome Assault",
                "description": "At the start of the Fight phase, each enemy unit within Engagement Range of one or more units with this ability must take a Battle-shock test subtracting 1 from that test"
            },
            {
                "name": "Terror Troops",
                "description": "While an enemy unit (excluding Monsters and Vehicles) is within 3\" of one or more units with this ability, subtract 1 from the Objective Control characteristic of models in that enemy unit."
            },
            {
                "name": "Grapnel Launchers",
                "description": "Each time the bearer\u2019s unit makes a Normal, Advance, Fall Back or Charge move, ignore any vertical distance when determining the total distance the\nbearer can be moved during that move"
            },
            {
                "name": "Reiver Grav-chute",
                "description": "The bearer has the Deep Strike ability."
            },
            {
                "name": "Death in the Dark",
                "description": "INFANTRY PHOBOS unit only. This unit\u2019s attacks that target a hidden unit have +1 to hit rolls."
            }
        ]
    },
    "Repulsor": {
        "stats": {
            "stat_movement": "10\"",
            "stat_toughness": 12,
            "stat_save": "3+",
            "stat_wounds": 16,
            "stat_leadership": "6+",
            "stat_oc": 5,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Armoured Hull",
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
                "name": "Hunter-slayer missile",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "1",
                "skill": "2+",
                "strength": "14",
                "ap": "-3",
                "damage": "D6",
                "keywords": "Indirect Fire, One Shot"
            },
            {
                "name": "Repulsor Defensive Array",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "18",
                "skill": "3+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "-"
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
            },
            {
                "name": "Heavy Onslaught Gatling Cannon",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "12",
                "skill": "3+",
                "strength": "6",
                "ap": "0",
                "damage": "1",
                "keywords": "Devastating Wounds"
            },
            {
                "name": "Las-talon",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "2",
                "skill": "3+",
                "strength": "10",
                "ap": "-3",
                "damage": "D6+1",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Transport",
                "description": "This model has a transport capacity of 14 ADEPTUS ASTARTES INFANTRY models. Each JUMP PACK, WULFEN, GRAVIS or TERMINATOR model takes up the space of 2 models and each CENTURION model takes up the space of 3 models."
            },
            {
                "name": "Emergency Combat Embarkation",
                "description": "Once per turn, in your opponent\u2019s Charge phase, after an enemy unit has selected targets for its charge but before it makes a Charge move, you can select one Adeptus Astartes unit from your army that was selected as a target of that charge. Provided that unit is not within Engagement Range of any enemy units and every model in that unit is within 3\" of this Transport, it can embark within this Transport. The charging unit can then select new targets for its charge."
            },
            {
                "name": "Damaged: 1-5 Wounds Remaining",
                "description": "While this model has 1-5 wounds remaining, each time this model makes an attack, subtract 1 from the Hit roll."
            }
        ]
    },
    "Repulsor Executioner": {
        "stats": {
            "stat_movement": "10\"",
            "stat_toughness": 12,
            "stat_save": "3+",
            "stat_wounds": 16,
            "stat_leadership": "6+",
            "stat_oc": 5,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Repulsor Executioner Defensive Array",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "10",
                "skill": "3+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "Armoured Hull",
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
                "name": "Heavy Onslaught Gatling Cannon",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "12",
                "skill": "3+",
                "strength": "6",
                "ap": "0",
                "damage": "1",
                "keywords": "Devastating Wounds"
            },
            {
                "name": "Icarus Rocket Pod",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "D3",
                "skill": "3+",
                "strength": "8",
                "ap": "-1",
                "damage": "2",
                "keywords": "Anti-fly 2+"
            },
            {
                "name": "Ironhail Heavy Stubber",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "3",
                "skill": "3+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Rapid Fire 3"
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
                "name": "Twin Icarus ironhail heavy stubber",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "3",
                "skill": "3+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Anti-FLY 4+, Rapid Fire 3, Twin-linked"
            },
            {
                "name": "Heavy Laser Destroyer",
                "weapon_type": "ranged",
                "range": "72\"",
                "attacks": "2",
                "skill": "3+",
                "strength": "16",
                "ap": "-4",
                "damage": "D6+4",
                "keywords": "Heavy"
            },
            {
                "name": "\u27a4 Macro Plasma Incinerator - Standard",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "D6+1",
                "skill": "3+",
                "strength": "8",
                "ap": "-3",
                "damage": "2",
                "keywords": "Blast"
            },
            {
                "name": "\u27a4 Macro Plasma Incinerator - Supercharge",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "D6+1",
                "skill": "3+",
                "strength": "9",
                "ap": "-4",
                "damage": "3",
                "keywords": "Blast, Hazardous"
            }
        ],
        "abilities": [
            {
                "name": "Transport",
                "description": "This model has a transport capacity of 7 Adeptus Astartes Infantry models. Each Jump Pack, Wulfen, Gravis or Terminator model takes up the space of 2 models and each Centurion model takes up the space of 3 models."
            },
            {
                "name": "Executioner",
                "description": "Each time this model makes an attack that targets a unit that is Below Half-strength, add 1 to the Hit roll."
            },
            {
                "name": "Damaged: 1-5 Wounds Remaining",
                "description": "While this model has 1-5 wounds remaining, each time this model makes an attack, subtract 1 from the Hit roll."
            }
        ]
    },
    "Rhino": {
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
                "name": "Armoured Tracks",
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
                "name": "Self Repair",
                "description": "At the end of your Command phase, this model regains 1 lost wound."
            },
            {
                "name": "Transport",
                "description": "This model has a transport capacity of 12 ADEPTUS ASTARTES INFANTRY models. It cannot transport JUMP PACK, WULFEN, PHOBOS, GRAVIS, CENTURION, TERMINATOR or TACTICUS models (excluding TACTICUS CHARACTER models that began the battle attached to a non-TACTICUS unit)"
            }
        ]
    },
    "Scout Squad": {
        "stats": {
            "stat_movement": "6\"",
            "stat_toughness": 4,
            "stat_save": "4+",
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
                "attacks": "2",
                "skill": "3+",
                "strength": "4",
                "ap": "0",
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
                "keywords": "Close-Quarters"
            },
            {
                "name": "Combat Knife",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "3",
                "skill": "3+",
                "strength": "4",
                "ap": "-1",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "Astartes Shotgun",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "2",
                "skill": "3+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Assault"
            },
            {
                "name": "Astartes Chainsword",
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
                "name": "Heavy Bolter",
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
                "name": "\u27a4 Missile Launcher - Frag",
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
                "name": "\u27a4 Missile Launcher - Krak",
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
                "name": "Scout Sniper Rifle",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "4",
                "ap": "-2",
                "damage": "2",
                "keywords": "Heavy, Precision"
            }
        ],
        "abilities": [
            {
                "name": "Guerrilla Tactics",
                "description": "At the end of your opponent\u2019s turn, if this unit is more than 6\" away from all enemy models, you can remove this unit from the battlefield and place it into\nStrategic Reserves."
            }
        ]
    },
    "Sternguard Veteran Squad": {
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
                "name": "Sternguard Bolt Pistol",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Devastating Wounds, Pistol"
            },
            {
                "name": "Sternguard Bolt Rifle",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "2",
                "skill": "3+",
                "strength": "4",
                "ap": "-1",
                "damage": "1",
                "keywords": "Assault, Devastating Wounds, Heavy, Rapid Fire 1"
            },
            {
                "name": "Close combat weapon",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "3+",
                "strength": "4",
                "ap": "0",
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
                "keywords": "Anti-Infantry 4+, Devastating Wounds, Rapid Fire 1"
            },
            {
                "name": "Power weapon",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "5",
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
                "attacks": "4",
                "skill": "3+",
                "strength": "8",
                "ap": "-2",
                "damage": "2",
                "keywords": "-"
            },
            {
                "name": "Astartes Chainsword",
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
                "name": "Sternguard Heavy Bolter",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "3",
                "skill": "4+",
                "strength": "5",
                "ap": "-1",
                "damage": "2",
                "keywords": "Devastating Wounds, Heavy, Sustained Hits 1"
            },
            {
                "name": "Pyrecannon",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "D6+1",
                "skill": "N/A",
                "strength": "6",
                "ap": "-1",
                "damage": "1",
                "keywords": "Ignores Cover, Torrent"
            }
        ],
        "abilities": [
            {
                "name": "Sternguard Focus",
                "description": "Each time a model in this unit makes an attack that targets your Oath of Moment Target, you can re-roll the wound roll"
            }
        ]
    },
    "Storm Speeder Hailstrike": {
        "stats": {
            "stat_movement": "14\"",
            "stat_toughness": 9,
            "stat_save": "3+",
            "stat_wounds": 11,
            "stat_leadership": "6+",
            "stat_oc": 3,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Fragstorm grenade launcher",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "D6",
                "skill": "3+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Blast"
            },
            {
                "name": "Onslaught gatling cannon",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "8",
                "skill": "3+",
                "strength": "5",
                "ap": "0",
                "damage": "1",
                "keywords": "Devastating Wounds"
            },
            {
                "name": "Twin Ironhail Heavy Stubber",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "3",
                "skill": "3+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Rapid Fire 3, Twin-linked"
            },
            {
                "name": "Close combat weapon",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "3+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Hailstrike",
                "description": "Each time this model has shot, select one enemy unit (excluding MONSTERS or VEHICLES) that was hit by one or more of those attacks. Until the end of the phase, each time a friendly ADEPTUS ASTARTES unit makes a ranged attack that targets that enemy unit, improve the Armour Penetration characteristic of that attack by 1. The same enemy unit can only be affected by this ability once per phase."
            }
        ]
    },
    "Storm Speeder Hammerstrike": {
        "stats": {
            "stat_movement": "14\"",
            "stat_toughness": 9,
            "stat_save": "3+",
            "stat_wounds": 11,
            "stat_leadership": "6+",
            "stat_oc": 3,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Hammerstrike Missile Launcher",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "2",
                "skill": "3+",
                "strength": "9",
                "ap": "-3",
                "damage": "D6",
                "keywords": "-"
            },
            {
                "name": "Krakstorm Grenade Launcher",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "9",
                "ap": "-1",
                "damage": "D3",
                "keywords": "-"
            },
            {
                "name": "Melta Destroyer",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "3",
                "skill": "3+",
                "strength": "9",
                "ap": "-4",
                "damage": "D6",
                "keywords": "Melta 2"
            },
            {
                "name": "Close combat weapon",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "3+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Hammerstrike",
                "description": "Each time this model has shot, select one enemy unit that was hit by one or more of those attacks. Until the end of the phase, that enemy unit cannot have the Benefit of Cover."
            }
        ]
    },
    "Storm Speeder Thunderstrike": {
        "stats": {
            "stat_movement": "14\"",
            "stat_toughness": 9,
            "stat_save": "3+",
            "stat_wounds": 11,
            "stat_leadership": "6+",
            "stat_oc": 3,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Stormfury Missiles",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "1",
                "skill": "2+",
                "strength": "12",
                "ap": "-3",
                "damage": "D6+1",
                "keywords": "-"
            },
            {
                "name": "Thunderstrike Las-talon",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "2",
                "skill": "2+",
                "strength": "9",
                "ap": "-3",
                "damage": "D6+1",
                "keywords": "-"
            },
            {
                "name": "Twin Icarus Rocket Pod",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "D3",
                "skill": "3+",
                "strength": "8",
                "ap": "-1",
                "damage": "2",
                "keywords": "Anti-Fly 2+, Twin-linked"
            },
            {
                "name": "Close combat weapon",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "3+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Thunderstrike",
                "description": "Each time this model has shot, select one enemy MONSTER or VEHICLE unit that was hit by one or more of those attacks. Until the end of the phase, each time a friendly ADEPTUS ASTARTES unit makes a ranged attack that targets that enemy unit, add 1 to the Wound roll."
            }
        ]
    },
    "Stormhawk Interceptor": {
        "stats": {
            "stat_movement": "-",
            "stat_toughness": 9,
            "stat_save": "3+",
            "stat_wounds": 10,
            "stat_leadership": "6+",
            "stat_oc": None,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Armoured Hull",
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
                "name": "Twin assault cannon",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "6",
                "skill": "3+",
                "strength": "6",
                "ap": "0",
                "damage": "1",
                "keywords": "Devastating wounds, Twin-linked"
            },
            {
                "name": "Icarus Stormcannon",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "6",
                "skill": "3+",
                "strength": "7",
                "ap": "-1",
                "damage": "2",
                "keywords": "Anti-Fly 2+"
            },
            {
                "name": "Las-talon",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "2",
                "skill": "3+",
                "strength": "10",
                "ap": "-3",
                "damage": "D6+1",
                "keywords": "-"
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
                "name": "\u27a4 Typhoon missile launcher - frag",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "2D6",
                "skill": "3+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Blast"
            },
            {
                "name": "\u27a4 Typhoon missile launcher - krak",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "2",
                "skill": "3+",
                "strength": "9",
                "ap": "-2",
                "damage": "D6",
                "keywords": "-"
            },
            {
                "name": "Skyhammer Missile Launcher",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "3",
                "skill": "3+",
                "strength": "8",
                "ap": "-1",
                "damage": "D3",
                "keywords": "Anti-Fly 2+"
            }
        ],
        "abilities": [
            {
                "name": "Interceptor",
                "description": "Each time this model makes a ranged attack that targets a unit that can Fly, add 1 to the Hit roll"
            }
        ]
    },
    "Stormraven Gunship": {
        "stats": {
            "stat_movement": "14\"",
            "stat_toughness": 10,
            "stat_save": "3+",
            "stat_wounds": 14,
            "stat_leadership": "6+",
            "stat_oc": 0,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Hurricane Bolter",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "6",
                "skill": "3+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Rapid Fire 6, Twin-linked"
            },
            {
                "name": "Stormstrike Missile Launcher",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "10",
                "ap": "-2",
                "damage": "3",
                "keywords": "-"
            },
            {
                "name": "Armoured Hull",
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
                "name": "\u27a4 Twin Heavy Plasma Cannon - Standard",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "D3",
                "skill": "3+",
                "strength": "7",
                "ap": "-2",
                "damage": "2",
                "keywords": "Blast, Twin-linked"
            },
            {
                "name": "\u27a4 Twin Heavy Plasma Cannon - Supercharge",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "D3",
                "skill": "3+",
                "strength": "8",
                "ap": "-3",
                "damage": "3",
                "keywords": "Blast, Hazardous, Twin-linked"
            },
            {
                "name": "Twin assault cannon",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "6",
                "skill": "3+",
                "strength": "6",
                "ap": "0",
                "damage": "1",
                "keywords": "Devastating wounds, Twin-linked"
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
                "name": "\u27a4 Typhoon missile launcher - frag",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "2D6",
                "skill": "3+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Blast"
            },
            {
                "name": "\u27a4 Typhoon missile launcher - krak",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "2",
                "skill": "3+",
                "strength": "9",
                "ap": "-2",
                "damage": "D6",
                "keywords": "-"
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
                "name": "Twin multi-melta",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "2",
                "skill": "3+",
                "strength": "9",
                "ap": "-4",
                "damage": "D6",
                "keywords": "Melta 2, Twin-linked"
            }
        ],
        "abilities": [
            {
                "name": "Armoured Resilience",
                "description": "Each time an attack is allocated to this model, subtract 1 from the Damage characteristic of that attack."
            },
            {
                "name": "Transport",
                "description": "This model has a transport capacity of 12 Adeptus Astartes Infantry models and 1 Dreadnought model. Each Jump Pack, Wulfen, Gravis or Terminator model takes up the space of 2 models and each Centurion model takes up the space of 3 models."
            },
            {
                "name": "Damaged: 1-5 Wounds Remaining",
                "description": "While this model has 1-5 wounds remaining, each time this model makes an attack, subtract 1 from the Hit roll."
            }
        ]
    },
    "Stormtalon Gunship": {
        "stats": {
            "stat_movement": "-",
            "stat_toughness": 8,
            "stat_save": "3+",
            "stat_wounds": 10,
            "stat_leadership": "6+",
            "stat_oc": None,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Armoured Hull",
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
                "name": "Twin assault cannon",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "6",
                "skill": "3+",
                "strength": "6",
                "ap": "0",
                "damage": "1",
                "keywords": "Devastating wounds, Twin-linked"
            },
            {
                "name": "Skyhammer Missile Launcher",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "3",
                "skill": "3+",
                "strength": "8",
                "ap": "-1",
                "damage": "D3",
                "keywords": "Anti-Fly 2+, Twin-linked"
            },
            {
                "name": "\u27a4 Typhoon missile launcher - frag",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "2D6",
                "skill": "3+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Blast"
            },
            {
                "name": "\u27a4 Typhoon missile launcher - krak",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "2",
                "skill": "3+",
                "strength": "9",
                "ap": "-2",
                "damage": "D6",
                "keywords": "-"
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
                "name": "Strafing Run",
                "description": "Each time this model makes a ranged attack that targets a unit that cannot Fly, add 1 to the Hit roll."
            }
        ]
    },
    "Tactical Squad": {
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
                "name": "Bolt pistol",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Close-Quarters"
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
                "name": "Twin lightning claws",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "3+",
                "strength": "4",
                "ap": "-2",
                "damage": "1",
                "keywords": "Twin-linked"
            },
            {
                "name": "Astartes Chainsword",
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
                "name": "Grav-pistol",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "4",
                "ap": "-1",
                "damage": "2",
                "keywords": "Anti-vehicle 2+, Pistol"
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
                "name": "Power fist",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "2",
                "skill": "3+",
                "strength": "8",
                "ap": "-2",
                "damage": "2",
                "keywords": "-"
            },
            {
                "name": "Thunder Hammer",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "2",
                "skill": "4+",
                "strength": "8",
                "ap": "-2",
                "damage": "2",
                "keywords": "Devastating Wounds"
            },
            {
                "name": "Power weapon",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "3",
                "skill": "3+",
                "strength": "5",
                "ap": "-2",
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
                "keywords": "Anti-Infantry 4+, Devastating Wounds, Rapid Fire 1"
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
                "keywords": "Rapid Fire 1, Hazardous"
            },
            {
                "name": "Grav-gun",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "2",
                "skill": "3+",
                "strength": "5",
                "ap": "-1",
                "damage": "2",
                "keywords": "Anti-vehicle 2+"
            },
            {
                "name": "Heavy Bolter",
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
                "name": "Multi-melta",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "2",
                "skill": "4+",
                "strength": "9",
                "ap": "-4",
                "damage": "D6",
                "keywords": "Heavy, Melta 2"
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
                "name": "\u27a4 Missile Launcher - Frag",
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
                "name": "\u27a4 Missile Launcher - Krak",
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
                "keywords": "Blast, Heavy"
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
                "keywords": "Blast, Heavy, Hazardous"
            },
            {
                "name": "Grav-cannon",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "3",
                "skill": "4+",
                "strength": "6",
                "ap": "-1",
                "damage": "3",
                "keywords": "Anti-vehicle 2+, Heavy"
            }
        ],
        "abilities": [
            {
                "name": "Combat Squads",
                "description": "At the start of the Declare Battle Formations step, before any units have been set up, this unit can be split into two units, each containing five models"
            }
        ]
    },
    "Techmarine": {
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
                "name": "Forge Bolter",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "3",
                "skill": "2+",
                "strength": "5",
                "ap": "-1",
                "damage": "2",
                "keywords": "-"
            },
            {
                "name": "Grav-pistol",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "1",
                "skill": "2+",
                "strength": "4",
                "ap": "-1",
                "damage": "2",
                "keywords": "Anti-vehicle 2+, Pistol"
            },
            {
                "name": "Omnissian power axe",
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
                "name": "Servo-arm",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "1",
                "skill": "3+",
                "strength": "8",
                "ap": "-2",
                "damage": "3",
                "keywords": "Extra Attacks"
            }
        ],
        "abilities": [
            {
                "name": "Techmarine",
                "description": "While this model is within 3\" of one or more friendly Adeptus Astartes Vehicle units, this model has the Lone Operative ability"
            },
            {
                "name": "Blessing of the Omnissiah",
                "description": "In your Command phase, you can select one friendly Adeptus Astartes Vehicle model within 3\" of this model. That model regains up to D3 lost wounds and, until the start of your next Command phase, each time that Vehicle model makes an attack, add 1 to the Hit roll. Each model can only be selected for this ability once per turn."
            },
            {
                "name": "Vengeance of the Omnissiah",
                "description": "If a friendly Adeptus Astartes Vehicle model is destroyed within 12\" of this model, until the end of the battle, this model\u2019s Omnissian power axe has an\nAttacks characteristic of 7."
            },
            {
                "name": "Leader",
                "description": "This model can be attached to the following units:\n\n\u25a0 ASSAULT INTERCESSOR SQUAD\n\u25a0 CRUSADER SQUAD\n\u25a0 DECIMUS KILL TEAM\n\u25a0 DESOLATION SQUAD\n\u25a0 DEVASTATOR SQUAD\n\u25a0 FORTIS KILL TEAM\n\u25a0 INTERCESSOR SQUAD\n\u25a0 SWORD BRETHREN SQUAD\n\u25a0 TACTICAL SQUAD"
            }
        ]
    },
    "Terminator Assault Squad": {
        "stats": {
            "stat_movement": "5\"",
            "stat_toughness": 5,
            "stat_save": "2+",
            "stat_wounds": 4,
            "stat_leadership": "6+",
            "stat_oc": 1,
            "stat_invuln": "4+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Thunder Hammer",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "3",
                "skill": "3+",
                "strength": "8",
                "ap": "-2",
                "damage": "2",
                "keywords": "Devastating Wounds"
            },
            {
                "name": "Twin Lightning Claws",
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
                "name": "Teleport Homer",
                "description": "At the start of the battle, you can set up one Teleport Homer token for this unit anywhere on the battlefield that is not in your opponent\u2019s deployment zone. If you do, once per battle, you can target this unit with the Rapid Ingress Stratagem for 0CP, but when resolving that Stratagem, you must set this unit up within 3\" horizontally of that token and not within 8\" horizontally of any enemy models. That token is then removed."
            },
            {
                "name": "Terminatus Assault",
                "description": "At the start of the Fight phase, each enemy unit within Engagement Range of this unit must take a Battle-Shock test."
            },
            {
                "name": "Storm Shield",
                "description": "The bearer has a Wounds characteristic of 4."
            }
        ]
    },
    "Terminator Squad": {
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
                "name": "Power weapon",
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
                "name": "Chainfist",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "3",
                "skill": "4+",
                "strength": "8",
                "ap": "-2",
                "damage": "2",
                "keywords": "Anti-Vehicle 3+"
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
                "name": "\u27a4 Cyclone missile launcher - frag",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "2D6",
                "skill": "3+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Blast"
            },
            {
                "name": "\u27a4 Cyclone missile launcher - krak",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "2",
                "skill": "3+",
                "strength": "9",
                "ap": "-2",
                "damage": "D6",
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
                "name": "Assault Cannon",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "6",
                "skill": "3+",
                "strength": "6",
                "ap": "0",
                "damage": "1",
                "keywords": "Devastating Wounds"
            }
        ],
        "abilities": [
            {
                "name": "Teleport Homer",
                "description": "At the start of the battle, you can set up one Teleport Homer token for this unit anywhere on the battlefield that is not in your opponent\u2019s deployment zone. If you do, once per battle, you can target this unit with the Rapid Ingress Stratagem for 0CP, but when resolving that Stratagem, you must set this unit up within 3\" horizontally of that token and not within 8\" horizontally of any enemy models. That token is then removed."
            },
            {
                "name": "Fury of the First",
                "description": "Each time a model in this unit makes an attack that targets your Oath of Moment target, add 1 to the Hit roll."
            }
        ]
    },
    "Vanguard Veteran Squad with Jump Packs": {
        "stats": {
            "stat_movement": "12\"",
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
                "name": "Inferno Pistol",
                "weapon_type": "ranged",
                "range": "6\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "8",
                "ap": "-4",
                "damage": "D3",
                "keywords": "Melta 2, Pistol"
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
                "keywords": "Close-Quarters"
            },
            {
                "name": "Grav-pistol",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "4",
                "ap": "-1",
                "damage": "2",
                "keywords": "Anti-vehicle 2+, Pistol"
            },
            {
                "name": "Heavy Bolt Pistol",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "4",
                "ap": "-1",
                "damage": "1",
                "keywords": "Pistol"
            },
            {
                "name": "Vanguard Veteran Weapon",
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
                "name": "Master-crafted Power Weapon",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "3",
                "skill": "3+",
                "strength": "5",
                "ap": "-2",
                "damage": "2"
            }
        ],
        "abilities": [
            {
                "name": "Vanguard Assault",
                "description": "Each time this unit ends a Charge move, until the end of the turn, melee weapons equipped by models in this unit have the [LETHAL HITS] ability."
            },
            {
                "name": "Storm Shield",
                "description": "The bearer has a 4+ invulnerable save"
            }
        ]
    },
    "Vindicator": {
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
                "name": "Demolisher Cannon",
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
                "name": "Armoured Tracks",
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
                "name": "Siege Shield",
                "description": "When making ranged attacks with its demolisher cannon, this model can target enemy units within Engagement Range of it (provided no other friendly units are also within Engagement Range of that enemy unit). In addition, when making ranged attacks, this model does not suffer the penalty to its Hit rolls for being within Engagement Range of one or more enemy units."
            },
            {
                "name": "Damaged: 1-4 Wounds Remaining",
                "description": "While this model has 1-4 wounds remaining, each time this model makes an attack, subtract 1 from the Hit roll."
            }
        ]
    },
    "Whirlwind": {
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
                "name": "Whirlwind Vengeance Launcher",
                "weapon_type": "ranged",
                "range": "72\"",
                "attacks": "D6+3",
                "skill": "3+",
                "strength": "8",
                "ap": "-2",
                "damage": "2",
                "keywords": "Blast, Indirect Fire"
            },
            {
                "name": "Armoured Tracks",
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
                "name": "Pinning Bombardment",
                "description": "In your Shooting phase, after this model has shot, if one or more of those attacks made with its Whirlwind vengeance launcher scored a hit against an enemy Infantry unit, that unit must take a Battle-shock test."
            },
            {
                "name": "Damaged: 1-4 Wounds Remaining",
                "description": "While this model has 1-4 wounds remaining, each time this model makes an attack, subtract 1 from the Hit roll."
            }
        ]
    }
}


class Command(BaseCommand):
    """Refresh base Space Marines stat lines, weapon profiles, and abilities from BSData."""

    help = 'Refresh 11th Edition stats/weapons/abilities for base Space Marines units.'

    def add_arguments(self, parser):
        """Add --dry-run flag."""
        parser.add_argument(
            '--dry-run', action='store_true',
            help='Preview changes without writing to the database.',
        )

    def handle(self, *args, **options):
        """Iterate SPACE_MARINES_DATASHEETS and refresh each unit's datasheet data."""
        dry_run = options['dry_run']
        updated = 0
        skipped = 0

        with transaction.atomic():
            for name, payload in SPACE_MARINES_DATASHEETS.items():
                try:
                    unit = UnitType.objects.get(name=name, faction__name='Space Marines')
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
