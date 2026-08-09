"""
Management command: seed_tau_empire_datasheets

Refreshes stat lines, weapon profiles, and abilities for T'au Empire
units using 11th Edition data sourced from BSData/wh40k-11e ("T'au
Empire.json") -- the same source used by seed_tau_empire_points.py.

Usage:
    python manage.py seed_tau_empire_datasheets
    python manage.py seed_tau_empire_datasheets --dry-run

Notes:
- Does NOT touch points_cost or category -- those are handled entirely by
  seed_tau_empire_points.py. This command only refreshes stat_* fields,
  WeaponProfile rows, and UnitAbility rows.
- Scope is all 41 active T'au Empire units seeded by
  seed_tau_empire_points.py.
- Per-field safety rule: a unit's stats/weapons/abilities are only
  overwritten when BSData actually has that data for it. If extraction
  found nothing, the existing DB value/rows are left untouched.
- Tidewall Shieldline (fortification wall) legitimately has 0 weapon
  profiles in BSData -- not a gap, just how the datasheet is written.
- Tiger Shark / AX-1-0 Tiger Shark and Commander in Coldstar/Enforcer
  Battlesuit (the two multi-build splits) both resolved cleanly against
  BSData's own literal names -- no name-mapping overrides were needed.
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from calculators.models import UnitAbility, UnitType, WeaponProfile

# (name -> {stats?, weapons?, abilities?}). Missing keys mean "no data
# found for this field -- leave existing DB data untouched."
TAU_EMPIRE_DATASHEETS = {
    "AX-1-0 Tiger Shark": {
        "stats": {
            "stat_movement": "-",
            "stat_toughness": 11,
            "stat_save": "3+",
            "stat_wounds": 18,
            "stat_leadership": "7+",
            "stat_oc": None,
            "stat_invuln": "5+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Twin heavy rail cannon",
                "weapon_type": "ranged",
                "range": "120\"",
                "attacks": "1",
                "skill": "4+",
                "strength": "26",
                "ap": "-5",
                "damage": "12",
                "keywords": "Devastating Wounds, Twin-linked"
            },
            {
                "name": "Missile pod",
                "weapon_type": "ranged",
                "range": "30\"",
                "attacks": "2",
                "skill": "4+",
                "strength": "7",
                "ap": "-1",
                "damage": "2",
                "keywords": "-"
            },
            {
                "name": "Armoured hull",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "3",
                "skill": "5+",
                "strength": "6",
                "ap": "0",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "Burst cannon",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "4",
                "skill": "4+",
                "strength": "5",
                "ap": "0",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "\u27a4 Cyclic ion blaster - standard",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "3",
                "skill": "4+",
                "strength": "7",
                "ap": "-1",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "\u27a4 Cyclic ion blaster - overcharge",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "3",
                "skill": "4+",
                "strength": "8",
                "ap": "-2",
                "damage": "2",
                "keywords": "Hazardous"
            },
            {
                "name": "Seeker missile",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "1",
                "skill": "4+",
                "strength": "14",
                "ap": "-3",
                "damage": "D6+1",
                "keywords": "One Shot"
            }
        ],
        "abilities": [
            {
                "name": "Titan Hunter",
                "description": "This model\u2019s twin heavy rail cannon and seeker missiles have the [ANTI-TITANIC 3+] ability while targeting a unit within half range."
            },
            {
                "name": "Damaged: 1-6 Wounds Remaining",
                "description": "While this model has 1-6 wounds remaining, each time this model makes an attack, subtract 1 from the Hit roll."
            }
        ]
    },
    "Breacher Team": {
        "stats": {
            "stat_movement": "6\"",
            "stat_toughness": 3,
            "stat_save": "4+",
            "stat_wounds": 1,
            "stat_leadership": "7+",
            "stat_oc": 2,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Pulse pistol",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "1",
                "skill": "4+",
                "strength": "5",
                "ap": "0",
                "damage": "1",
                "keywords": "Pistol"
            },
            {
                "name": "Close combat weapon",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "1",
                "skill": "5+",
                "strength": "3",
                "ap": "0",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "Pulse blaster",
                "weapon_type": "ranged",
                "range": "10\"",
                "attacks": "2",
                "skill": "3+",
                "strength": "6",
                "ap": "-1",
                "damage": "1",
                "keywords": "Assault"
            },
            {
                "name": "Support turret",
                "weapon_type": "ranged",
                "range": "30\"",
                "attacks": "2",
                "skill": "5+",
                "strength": "5",
                "ap": "0",
                "damage": "1",
                "keywords": "Indirect Fire, Twin-linked"
            }
        ],
        "abilities": [
            {
                "name": "Breach and Clear",
                "description": "Each time a model in this unit makes a ranged attack that targets an enemy unit within range of an objective marker, you can re-roll the Wound roll."
            },
            {
                "name": "DS8 Support Turret",
                "description": "In your Movement phase, if this unit Remains Stationary, until the start of your next turn, its Shas\u2019ui model is equipped with the support turret weapon.\n\nDesigner\u2019s Note: Place a Support Turret token next to this unit to remind you."
            }
        ]
    },
    "Broadside Battlesuits": {
        "stats": {
            "stat_movement": "5\"",
            "stat_toughness": 6,
            "stat_save": "2+",
            "stat_wounds": 8,
            "stat_leadership": "7+",
            "stat_oc": 2,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Crushing bulk",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "3",
                "skill": "5+",
                "strength": "6",
                "ap": "0",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "Heavy rail rifle",
                "weapon_type": "ranged",
                "range": "60\"",
                "attacks": "2",
                "skill": "4+",
                "strength": "12",
                "ap": "-4",
                "damage": "D6+1",
                "keywords": "Heavy, Devastating Wounds"
            },
            {
                "name": "High-yield missile pods",
                "weapon_type": "ranged",
                "range": "30\"",
                "attacks": "6",
                "skill": "4+",
                "strength": "7",
                "ap": "-1",
                "damage": "2",
                "keywords": "Twin-linked"
            },
            {
                "name": "Seeker missile",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "1",
                "skill": "4+",
                "strength": "14",
                "ap": "-3",
                "damage": "D6+1",
                "keywords": "One Shot"
            },
            {
                "name": "Twin plasma rifle",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "1",
                "skill": "4+",
                "strength": "8",
                "ap": "-3",
                "damage": "3",
                "keywords": "Twin-linked"
            },
            {
                "name": "Twin smart missile system",
                "weapon_type": "ranged",
                "range": "30\"",
                "attacks": "4",
                "skill": "4+",
                "strength": "5",
                "ap": "0",
                "damage": "1",
                "keywords": "Indirect Fire, Twin-linked"
            }
        ],
        "abilities": [
            {
                "name": "Advanced Armour",
                "description": "Models in this unit have the Feel No Pain 4+ ability against mortal wounds."
            },
            {
                "name": "Weapon Support System",
                "description": "Each time the bearer makes a ranged attack, you can ignore any or all modifiers to the Hit roll."
            }
        ]
    },
    "Cadre Fireblade": {
        "stats": {
            "stat_movement": "6\"",
            "stat_toughness": 3,
            "stat_save": "4+",
            "stat_wounds": 3,
            "stat_leadership": "7+",
            "stat_oc": 1,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Fireblade pulse rifle",
                "weapon_type": "ranged",
                "range": "30\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "5",
                "ap": "0",
                "damage": "2",
                "keywords": "Rapid Fire 1"
            },
            {
                "name": "Close combat weapon",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "3",
                "skill": "4+",
                "strength": "3",
                "ap": "0",
                "damage": "1",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Volley Fire",
                "description": "While this model is leading a unit, add 1 to the Attacks characteristic of ranged weapons equipped by models in that unit."
            },
            {
                "name": "Crack Shot",
                "description": "Each time this model makes a ranged attack, on a Critical Wound, that attack has an Armour Penetration characteristic of -3."
            },
            {
                "name": "Leader",
                "description": "This model can be attached to the following units:\n- Breacher Team\n- Strike Team"
            }
        ]
    },
    "Commander Farsight": {
        "stats": {
            "stat_movement": "10\"",
            "stat_toughness": 5,
            "stat_save": "2+",
            "stat_wounds": 8,
            "stat_leadership": "6+",
            "stat_oc": 2,
            "stat_invuln": "4+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "High-intensity plasma rifle",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "2",
                "skill": "2+",
                "strength": "8",
                "ap": "-3",
                "damage": "3",
                "keywords": "-"
            },
            {
                "name": "\u27a4 Dawn Blade - strike",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "2+",
                "strength": "10",
                "ap": "-2",
                "damage": "3",
                "keywords": "-"
            },
            {
                "name": "\u27a4 Dawn Blade - sweep",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "8",
                "skill": "2+",
                "strength": "6",
                "ap": "-1",
                "damage": "1",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Way of the Short Blade",
                "description": "While this model is leading a unit, each time a model in that unit makes an attack that targets an enemy unit within 9\", add 1 to the Wound roll."
            },
            {
                "name": "Puretide's Teachings",
                "description": "Once per battle round, one unit from your army with this ability can use it when its unit is targeted with a Stratagem. If it does, reduce the CP cost of that use of that Stratagem by 1CP."
            },
            {
                "name": "Leader",
                "description": "This model can be attached to the following units:\n- CRISIS BATTLESUITS\n- CRISIS FIREKNIFE BATTLESUITS\n- CRISIS STARSCYTHE BATTLESUITS\n- CRISIS SUNFORGE BATTLESUITS"
            }
        ]
    },
    "Commander Shadowsun": {
        "stats": {
            "stat_movement": "10\"",
            "stat_toughness": 4,
            "stat_save": "3+",
            "stat_wounds": 6,
            "stat_leadership": "6+",
            "stat_oc": 1,
            "stat_invuln": "5+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Light missile pod",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "2",
                "skill": "2+",
                "strength": "7",
                "ap": "0",
                "damage": "2",
                "keywords": "-"
            },
            {
                "name": "High-energy fusion blaster",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "1",
                "skill": "2+",
                "strength": "10",
                "ap": "-4",
                "damage": "D6",
                "keywords": "Melta 2"
            },
            {
                "name": "Flechette launcher",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "5",
                "skill": "2+",
                "strength": "3",
                "ap": "0",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "Battlesuit fists",
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
                "name": "Pulse pistol",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "5",
                "ap": "0",
                "damage": "1",
                "keywords": "Pistol"
            }
        ],
        "abilities": [
            {
                "name": "Agile Combatant",
                "description": "This model is eligible to shoot in a turn in which it Fell Back."
            },
            {
                "name": "Hero of the Empire (Aura)",
                "description": "While a friendly T\u2019au Empire unit is within 6\" of this model, each time a model in that unit makes a ranged attack, re-roll a Hit roll of 1."
            },
            {
                "name": "Advanced Guardian Drone",
                "description": "Each time a ranged attack targets the bearer, subtract 1 from the Wound roll."
            },
            {
                "name": "Command-link Drone (Aura)",
                "description": "While a friendly T\u2019au Empire unit is within 6\" of the bearer, each time you select that unit as the target of a Stratagem, roll one D6: on a 5+, you gain 1CP."
            },
            {
                "name": "Supreme Commander",
                "description": "If this model is in your army, it must be your Warlord."
            }
        ]
    },
    "Commander in Coldstar Battlesuit": {
        "stats": {
            "stat_movement": "12\"",
            "stat_toughness": 5,
            "stat_save": "3+",
            "stat_wounds": 6,
            "stat_leadership": "7+",
            "stat_oc": 2,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Battlesuit fists",
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
                "name": "High-output burst cannon",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "8",
                "skill": "3+",
                "strength": "5",
                "ap": "0",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "Missile pod",
                "weapon_type": "ranged",
                "range": "30\"",
                "attacks": "2",
                "skill": "3+",
                "strength": "7",
                "ap": "-1",
                "damage": "2",
                "keywords": "-"
            },
            {
                "name": "Burst cannon",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "4",
                "skill": "3+",
                "strength": "5",
                "ap": "0",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "Airbursting fragmentation projector",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "D6",
                "skill": "3+",
                "strength": "3",
                "ap": "0",
                "damage": "1",
                "keywords": "Blast, Indirect Fire"
            },
            {
                "name": "\u27a4 Cyclic ion blaster - standard",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "3",
                "skill": "3+",
                "strength": "7",
                "ap": "-1",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "\u27a4 Cyclic ion blaster - overcharge",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "3",
                "skill": "3+",
                "strength": "8",
                "ap": "-2",
                "damage": "2",
                "keywords": "Hazardous"
            },
            {
                "name": "T'au flamer",
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
                "name": "Fusion blaster",
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
                "name": "Plasma rifle",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "8",
                "ap": "-3",
                "damage": "3",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Leader",
                "description": "This model can be attached to the following units:\n- CRISIS BATTLESUITS\n- CRISIS FIREKNIFE BATTLESUITS\n- CRISIS STARSCYTHE BATTLESUITS\n- CRISIS SUNFORGE BATTLESUITS"
            },
            {
                "name": "Coldstar Commander",
                "description": "While this model is leading a unit, models in that unit have a Move characteristic of 12\" and ranged weapons equipped by models in that unit have the [ASSAULT] ability."
            },
            {
                "name": "Battlesuit Support System",
                "description": "The bearer\u2019s unit is eligible to shoot in a turn in which it Fell Back, but when doing so only models equipped with this wargear can make ranged attacks."
            },
            {
                "name": "Shield Generator",
                "description": "The bearer has a 4+ invulnerable save."
            },
            {
                "name": "Weapon Support System",
                "description": "Each time the bearer makes a ranged attack, you can ignore any or all modifiers to the Hit roll."
            }
        ]
    },
    "Commander in Enforcer Battlesuit": {
        "stats": {
            "stat_movement": "8\"",
            "stat_toughness": 5,
            "stat_save": "2+",
            "stat_wounds": 6,
            "stat_leadership": "7+",
            "stat_oc": 2,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Battlesuit fists",
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
                "name": "Missile pod",
                "weapon_type": "ranged",
                "range": "30\"",
                "attacks": "2",
                "skill": "3+",
                "strength": "7",
                "ap": "-1",
                "damage": "2",
                "keywords": "-"
            },
            {
                "name": "Burst cannon",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "4",
                "skill": "3+",
                "strength": "5",
                "ap": "0",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "Airbursting fragmentation projector",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "D6",
                "skill": "3+",
                "strength": "3",
                "ap": "0",
                "damage": "1",
                "keywords": "Blast, Indirect Fire"
            },
            {
                "name": "\u27a4 Cyclic ion blaster - standard",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "3",
                "skill": "3+",
                "strength": "7",
                "ap": "-1",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "\u27a4 Cyclic ion blaster - overcharge",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "3",
                "skill": "3+",
                "strength": "8",
                "ap": "-2",
                "damage": "2",
                "keywords": "Hazardous"
            },
            {
                "name": "T'au flamer",
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
                "name": "Fusion blaster",
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
                "name": "Plasma rifle",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "8",
                "ap": "-3",
                "damage": "3",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Enforcer Commander",
                "description": "While this model is leading a unit, each time a ranged attack targets that unit, worsen the Armour Penetration characteristic of that attack by 1."
            },
            {
                "name": "Leader",
                "description": "This model can be attached to the following units:\n- CRISIS BATTLESUITS\n- CRISIS FIREKNIFE BATTLESUITS\n- CRISIS STARSCYTHE BATTLESUITS\n- CRISIS SUNFORGE BATTLESUITS"
            },
            {
                "name": "Battlesuit Support System",
                "description": "The bearer\u2019s unit is eligible to shoot in a turn in which it Fell Back, but when doing so only models equipped with this wargear can make ranged attacks."
            },
            {
                "name": "Shield Generator",
                "description": "The bearer has a 4+ invulnerable save."
            },
            {
                "name": "Weapon Support System",
                "description": "Each time the bearer makes a ranged attack, you can ignore any or all modifiers to the Hit roll."
            }
        ]
    },
    "Crisis Fireknife Battlesuits": {
        "stats": {
            "stat_movement": "10\"",
            "stat_toughness": 5,
            "stat_save": "3+",
            "stat_wounds": 4,
            "stat_leadership": "7+",
            "stat_oc": 2,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Battlesuit fists",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "3",
                "skill": "5+",
                "strength": "5",
                "ap": "0",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "Plasma rifle",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "1",
                "skill": "4+",
                "strength": "8",
                "ap": "-3",
                "damage": "3",
                "keywords": "-"
            },
            {
                "name": "Missile pod",
                "weapon_type": "ranged",
                "range": "30\"",
                "attacks": "2",
                "skill": "4+",
                "strength": "7",
                "ap": "-1",
                "damage": "2",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Fireknife",
                "description": "Each time a model in this unit makes a ranged attack, re-roll a Hit roll of 1. If that attack targets a unit that is at its Starting Strength, you can re-roll the Hit roll instead."
            },
            {
                "name": "Weapon Support System",
                "description": "Each time a model in this unit makes a ranged attack, you can ignore any or all modifiers to the Hit roll."
            }
        ]
    },
    "Crisis Starscythe Battlesuits": {
        "stats": {
            "stat_movement": "10\"",
            "stat_toughness": 5,
            "stat_save": "3+",
            "stat_wounds": 4,
            "stat_leadership": "7+",
            "stat_oc": 2,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Battlesuit fists",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "3",
                "skill": "5+",
                "strength": "5",
                "ap": "0",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "Burst cannon",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "4",
                "skill": "4+",
                "strength": "5",
                "ap": "0",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "T'au flamer",
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
                "name": "Starscythe",
                "description": "Each time a model in this unit makes a ranged attack (excluding attacks that target MONSTERS and VEHICLES), improve the Armour Penetration characteristic of that attack by 1."
            },
            {
                "name": "Battlesuit Support System",
                "description": "The unit is eligible to shoot in a turn in which it Fell Back."
            }
        ]
    },
    "Crisis Sunforge Battlesuits": {
        "stats": {
            "stat_movement": "10\"",
            "stat_toughness": 5,
            "stat_save": "3+",
            "stat_wounds": 4,
            "stat_leadership": "7+",
            "stat_oc": 2,
            "stat_invuln": "4+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Battlesuit fists",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "3",
                "skill": "5+",
                "strength": "5",
                "ap": "0",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "Fusion blaster",
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
                "name": "Sunforge",
                "description": "Each time a model in this unit makes a ranged attack that targets a MONSTER or VEHICLE unit, you can re-roll the Wound roll and you can re-roll the Damage roll."
            }
        ]
    },
    "Darkstrider": {
        "stats": {
            "stat_movement": "7\"",
            "stat_toughness": 3,
            "stat_save": "4+",
            "stat_wounds": 3,
            "stat_leadership": "7+",
            "stat_oc": 1,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Shade",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "2",
                "skill": "2+",
                "strength": "5",
                "ap": "0",
                "damage": "2",
                "keywords": "Assault"
            },
            {
                "name": "Close combat weapon",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "3",
                "skill": "4+",
                "strength": "3",
                "ap": "0",
                "damage": "1",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Structural Analyser",
                "description": "While this model is leading a unit, each time a model in that unit makes a ranged attack, add 1 to the Wound roll."
            },
            {
                "name": "Jammer Array",
                "description": "Enemy units that are set up on the battlefield from Reserves cannot be set up within 12\" of this model."
            },
            {
                "name": "Leader",
                "description": "This model can be attached to the following unit:\n- Pathfinder Team"
            }
        ]
    },
    "Devilfish": {
        "stats": {
            "stat_movement": "12\"",
            "stat_toughness": 9,
            "stat_save": "3+",
            "stat_wounds": 13,
            "stat_leadership": "7+",
            "stat_oc": 2,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Accelerator burst cannon",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "4",
                "skill": "4+",
                "strength": "6",
                "ap": "-1",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "Armoured hull",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "3",
                "skill": "5+",
                "strength": "6",
                "ap": "0",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "Twin pulse carbine",
                "weapon_type": "ranged",
                "range": "20\"",
                "attacks": "2",
                "skill": "4+",
                "strength": "5",
                "ap": "0",
                "damage": "1",
                "keywords": "Twin-linked, Assault"
            },
            {
                "name": "Smart missile system",
                "weapon_type": "ranged",
                "range": "30\"",
                "attacks": "3",
                "skill": "4+",
                "strength": "5",
                "ap": "0",
                "damage": "1",
                "keywords": "Indirect Fire"
            },
            {
                "name": "Seeker missile",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "1",
                "skill": "4+",
                "strength": "14",
                "ap": "-3",
                "damage": "D6+1",
                "keywords": "One Shot"
            }
        ],
        "abilities": [
            {
                "name": "Rapid Deployment",
                "description": "Units can disembark from this TRANSPORT after it has Advanced. Units that do so count as having made a Normal move that phase, and cannot declare a charge in the same turn, but can otherwise act normally in the remainder of the turn."
            }
        ]
    },
    "Ethereal": {
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
                "name": "Honour stave",
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
                "name": "Coordinated Leadership",
                "description": "In your Command phase, roll one D6: on a 4+, you gain 1CP."
            },
            {
                "name": "Leader",
                "description": "This model can be attached to the following units:\n- Breacher Team\n- Strike Team"
            },
            {
                "name": "Failure Is Not an Option",
                "description": "While this model is leading a unit, models in that unit have the Feel No Pain 5+ ability."
            },
            {
                "name": "Hover Drone",
                "description": "The bearer can Fly and has a Move characteristic of 10\"."
            }
        ]
    },
    "Firesight Team": {
        "stats": {
            "stat_movement": "6\"",
            "stat_toughness": 3,
            "stat_save": "4+",
            "stat_wounds": 4,
            "stat_leadership": "7+",
            "stat_oc": 3,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Close combat weapons",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "5+",
                "strength": "3",
                "ap": "0",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "Longshot pulse rifles",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "3",
                "skill": "4+",
                "strength": "5",
                "ap": "-1",
                "damage": "2",
                "keywords": "Heavy, Precision"
            },
            {
                "name": "Pulse pistol",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "5",
                "ap": "0",
                "damage": "1",
                "keywords": "Pistol"
            }
        ],
        "abilities": [
            {
                "name": "Precise Targeting",
                "description": "Each time a model in this unit makes an attack that targets a Spotted unit, you can re-roll the Hit roll."
            }
        ]
    },
    "Ghostkeel Battlesuit": {
        "stats": {
            "stat_movement": "10\"",
            "stat_toughness": 8,
            "stat_save": "2+",
            "stat_wounds": 12,
            "stat_leadership": "7+",
            "stat_oc": 3,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Ghostkeel fists",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "3",
                "skill": "5+",
                "strength": "6",
                "ap": "0",
                "damage": "2",
                "keywords": "-"
            },
            {
                "name": "Twin burst cannon",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "4",
                "skill": "4+",
                "strength": "5",
                "ap": "0",
                "damage": "1",
                "keywords": "Twin-linked"
            },
            {
                "name": "Twin T'au flamer",
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
                "name": "Twin fusion blaster",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "1",
                "skill": "4+",
                "strength": "9",
                "ap": "-4",
                "damage": "D6",
                "keywords": "Melta 2, Twin-linked"
            },
            {
                "name": "Fusion collider",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "2",
                "skill": "4+",
                "strength": "12",
                "ap": "-4",
                "damage": "D6",
                "keywords": "Melta 2"
            },
            {
                "name": "\u27a4 Cyclic ion raker - standard",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "6",
                "skill": "4+",
                "strength": "7",
                "ap": "-1",
                "damage": "2",
                "keywords": "-"
            },
            {
                "name": "\u27a4 Cyclic ion raker - overcharge",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "6",
                "skill": "4+",
                "strength": "8",
                "ap": "-2",
                "damage": "3",
                "keywords": "Hazardous"
            }
        ],
        "abilities": [
            {
                "name": "Stealth Drones",
                "description": "Twice per battle, after an attack has been allocated to this model, you can change the Damage characteristic of that attack to 0.\n\nDesigner\u2019s Note: Place two Stealth Drone tokens next to the unit, removing one each time this ability has been used."
            },
            {
                "name": "Damaged: 1-4 Wounds Remaining",
                "description": "While this model has 1-4 wounds remaining, each time this model makes an attack, subtract 1 from the Hit roll."
            },
            {
                "name": "Localised Stealth Projectors (Aura)",
                "description": "When a friendly KROOT/VESPID STINGWINGS unit within 6\" of this unit has shot, those attacks do not prevent that unit from being hidden."
            },
            {
                "name": "Battlesuit Support System",
                "description": "The bearer is eligible to shoot in a turn in which it Fell Back but it loses the Smoke keyword."
            }
        ]
    },
    "Hammerhead Gunship": {
        "stats": {
            "stat_movement": "10\"",
            "stat_toughness": 10,
            "stat_save": "3+",
            "stat_wounds": 14,
            "stat_leadership": "7+",
            "stat_oc": 3,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Armoured hull",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "3",
                "skill": "5+",
                "strength": "6",
                "ap": "0",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "Railgun",
                "weapon_type": "ranged",
                "range": "72\"",
                "attacks": "1",
                "skill": "4+",
                "strength": "20",
                "ap": "-5",
                "damage": "D6+6",
                "keywords": "Heavy, Devastating Wounds"
            },
            {
                "name": "\u27a4 Ion cannon - standard",
                "weapon_type": "ranged",
                "range": "60\"",
                "attacks": "D6+3",
                "skill": "4+",
                "strength": "7",
                "ap": "-1",
                "damage": "2",
                "keywords": "Blast"
            },
            {
                "name": "\u27a4 Ion cannon - overcharge",
                "weapon_type": "ranged",
                "range": "60\"",
                "attacks": "D6+3",
                "skill": "4+",
                "strength": "8",
                "ap": "-2",
                "damage": "3",
                "keywords": "Blast, Hazardous"
            },
            {
                "name": "Seeker missile",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "1",
                "skill": "4+",
                "strength": "14",
                "ap": "-3",
                "damage": "D6+1",
                "keywords": "One Shot"
            },
            {
                "name": "Accelerator burst cannon",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "4",
                "skill": "4+",
                "strength": "6",
                "ap": "-1",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "Twin pulse carbine",
                "weapon_type": "ranged",
                "range": "20\"",
                "attacks": "2",
                "skill": "4+",
                "strength": "5",
                "ap": "0",
                "damage": "1",
                "keywords": "Twin-linked"
            },
            {
                "name": "Smart missile system",
                "weapon_type": "ranged",
                "range": "30\"",
                "attacks": "3",
                "skill": "4+",
                "strength": "5",
                "ap": "0",
                "damage": "1",
                "keywords": "Indirect Fire"
            }
        ],
        "abilities": [
            {
                "name": "Armour Hunter",
                "description": "Each time this model makes an attack that targets a MONSTER or VEHICLE, add 1 to the Hit roll."
            },
            {
                "name": "Damaged: 1-5 Wounds Remaining",
                "description": "While this model has 1-5 wounds remaining, each time this model makes an attack, subtract 1 from the Hit roll."
            },
            {
                "name": "Targeting Array",
                "description": "Each time this model is selected to shoot, you can re-roll one Hit roll or you can re-roll one Wound roll when resolving those attacks."
            }
        ]
    },
    "Kroot Carnivores": {
        "stats": {
            "stat_movement": "7\"",
            "stat_toughness": 3,
            "stat_save": "6+",
            "stat_wounds": 1,
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
                "skill": "3+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "Kroot rifle",
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
                "name": "Tanglebomb launcher",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "D3",
                "skill": "4+",
                "strength": "5",
                "ap": "0",
                "damage": "1",
                "keywords": "Blast"
            },
            {
                "name": "Kroot pistol",
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
                "name": "Kroot carbine",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "1",
                "skill": "4+",
                "strength": "4",
                "ap": "0",
                "damage": "2",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Fieldcraft",
                "description": "At the end of the your Command phase, if this unit within range of an objective marker you control, that objective marker remains under your control, even if you have no models within range of it, until your opponent controls it at the start or end of any turn."
            },
            {
                "name": "Bodyguard",
                "description": "If this unit has a Starting Strength of 20, you can attach up to two Leader units to it instead of one, provided those Leaders are not duplicates (e.g. you cannot attach two WAR SHAPERS to this unit). If you do, and this unit is destroyed, the Leader units attached to it become separate units with their original Starting Strengths."
            },
            {
                "name": "Harnessed Alien Instincts",
                "description": "In your Shooting phase, this unit can select one visible enemy unit within 12\". That enemy unit is prey-marked:\n- While a unit is prey-marked, that unit has +3\" detection range."
            }
        ]
    },
    "Kroot Farstalkers": {
        "stats": {
            "stat_movement": "7\"",
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
                "name": "Ripping fangs",
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
                "name": "Farstalker firearm",
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
                "name": "Kroot pistol",
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
                "name": "Dvorgite skinner",
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
                "name": "Londaxi tribalest",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "3",
                "skill": "5+",
                "strength": "7",
                "ap": "-1",
                "damage": "1",
                "keywords": "Anti-Vehicle 4+, Devastating Wounds, Heavy"
            },
            {
                "name": "Ritual blade",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "3",
                "skill": "3+",
                "strength": "5",
                "ap": "0",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "T'au tech rifle",
                "weapon_type": "ranged",
                "range": "30\"",
                "attacks": "1",
                "skill": "4+",
                "strength": "5",
                "ap": "0",
                "damage": "1",
                "keywords": "Rapid Fire 1"
            }
        ],
        "abilities": [
            {
                "name": "Harnessed Alien Instincts",
                "description": "In your Shooting phase, this unit can select one visible enemy unit within 12\". That enemy unit is prey-marked:\n- While a unit is prey-marked, that unit has +3\" detection range."
            }
        ]
    },
    "Kroot Flesh Shaper": {
        "stats": {
            "stat_movement": "7\"",
            "stat_toughness": 3,
            "stat_save": "6+",
            "stat_wounds": 3,
            "stat_leadership": "7+",
            "stat_oc": 1,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Twin ritualistic blades",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "2+",
                "strength": "5",
                "ap": "-1",
                "damage": "1",
                "keywords": "Twin-linked"
            },
            {
                "name": "Kroot scattergun",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "2",
                "skill": "4+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Assault"
            }
        ],
        "abilities": [
            {
                "name": "Leader",
                "description": "This model can be attached to the following unit:\n- Kroot Carnivores\n- Kroot Farstalkers"
            },
            {
                "name": "Rites of Feasting",
                "description": "While this model is leading a unit, models in that unit have the Feel Not Pain 6+ ability. If that unit destroys one or more enemy units in the Fight phase, until the end of the battle, models in that unit have the Feel No Pain 5+ ability instead."
            },
            {
                "name": "Ritual Butchery",
                "description": "While this model is leading a unit, melee weapons equipped by models in that unit have the [SUSTAINED HITS 1] ability."
            },
            {
                "name": "Harnessed Alien Instincts",
                "description": "In your Shooting phase, this unit can select one visible enemy unit within 12\". That enemy unit is prey-marked:\n- While a unit is prey-marked, that unit has +3\" detection range."
            }
        ]
    },
    "Kroot Hounds": {
        "stats": {
            "stat_movement": "12\"",
            "stat_toughness": 3,
            "stat_save": "6+",
            "stat_wounds": 1,
            "stat_leadership": "8+",
            "stat_oc": 0,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Ripping fangs",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "3",
                "skill": "3+",
                "strength": "3",
                "ap": "0",
                "damage": "1",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Loping Pounce",
                "description": "At the start of your Command phase, if this unit is within 6\" of one or more friendly KROOT INFANTRY units, then until the end of the turn, this unit is eligible to declare a charge in a turn in which it Advanced."
            },
            {
                "name": "Hunting Hounds",
                "description": "While this unit is within 12\" of one or more friendly KROOT CHARACTER models, the Objective Control characteristic of models in this unit is 1."
            },
            {
                "name": "Harnessed Alien Instincts",
                "description": "In your Shooting phase, this unit can select one visible enemy unit within 12\". That enemy unit is prey-marked:\n- While a unit is prey-marked, that unit has +3\" detection range."
            }
        ]
    },
    "Kroot Lone-spear": {
        "stats": {
            "stat_movement": "12\"",
            "stat_toughness": 5,
            "stat_save": "5+",
            "stat_wounds": 6,
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
                "skill": "3+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "Kalamandra's bite",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "4+",
                "strength": "5",
                "ap": "-1",
                "damage": "1",
                "keywords": "Extra Attacks"
            },
            {
                "name": "Hunting javelin",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "3",
                "skill": "3+",
                "strength": "4",
                "ap": "-1",
                "damage": "1",
                "keywords": "Lance"
            },
            {
                "name": "Blast javelin",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "D6",
                "skill": "4+",
                "strength": "10",
                "ap": "-2",
                "damage": "2",
                "keywords": "Assault, Blast"
            },
            {
                "name": "Kroot long gun",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "6",
                "ap": "-2",
                "damage": "3",
                "keywords": "Heavy, Precision"
            }
        ],
        "abilities": [
            {
                "name": "Fire and Fade",
                "description": "In your Shooting phase, after this model has shot, if it is not within Engagement Range of one or more enemy units, it can make a Normal move of up to 6\". If it does, until the end of the turn, this model is not eligible to declare a charge."
            },
            {
                "name": "Advanced Scouting",
                "description": "Each time this model makes a ranged attack that hits an enemy unit, until the end of the turn, each time another KROOT model from your army makes an attack that targets that enemy unit, you can re-roll the Hit roll."
            },
            {
                "name": "Harnessed Alien Instincts",
                "description": "In your Shooting phase, this unit can select one visible enemy unit within 12\". That enemy unit is prey-marked:\n- While a unit is prey-marked, that unit has +3\" detection range."
            }
        ]
    },
    "Kroot Trail Shaper": {
        "stats": {
            "stat_movement": "7\"",
            "stat_toughness": 3,
            "stat_save": "6+",
            "stat_wounds": 3,
            "stat_leadership": "7+",
            "stat_oc": 1,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Kroot rifle",
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
                "name": "Shaper's blade",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "2+",
                "strength": "5",
                "ap": "0",
                "damage": "1",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Kroot Ambush",
                "description": "After both players have deployed their armies, you can redeploy this model\u2019s unit and one other friendly KROOT unit. When doing so, any of those units can be placed into Strategic Reserves, regardless of how many units are already in Strategic Reserves."
            },
            {
                "name": "Trail Finding",
                "description": "In your opponent\u2019s Movement phase, if an enemy unit ends a move within 8\" of this unit, if this unit is not within Engagement Range of one or more enemy units, this unit can make a Normal move of up to D6\"."
            },
            {
                "name": "Leader",
                "description": "This model can be attached to the following unit:\n- Kroot Carnivores\n- Kroot Farstalkers"
            },
            {
                "name": "Harnessed Alien Instincts",
                "description": "In your Shooting phase, this unit can select one visible enemy unit within 12\". That enemy unit is prey-marked:\n- While a unit is prey-marked, that unit has +3\" detection range."
            }
        ]
    },
    "Kroot War Shaper": {
        "stats": {
            "stat_movement": "7\"",
            "stat_toughness": 3,
            "stat_save": "6+",
            "stat_wounds": 3,
            "stat_leadership": "7+",
            "stat_oc": 1,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Shaper's blade",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "2+",
                "strength": "5",
                "ap": "0",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "Kroot pistol",
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
                "name": "Bladestave and prey-hook",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "2+",
                "strength": "5",
                "ap": "-1",
                "damage": "2",
                "keywords": "Lethal Hits"
            },
            {
                "name": "Dart-bow and tri-blade",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "D3+1",
                "skill": "4+",
                "strength": "4",
                "ap": "0",
                "damage": "2",
                "keywords": "Anti-Infantry 3+, Assault, Heavy"
            }
        ],
        "abilities": [
            {
                "name": "Root of Honour",
                "description": "Once per battle, at the start of any phase, you can select one friendly KROOT unit that is Battle-shocked and within 12\" of this model. That unit is no longer Battle-shocked."
            },
            {
                "name": "Leader",
                "description": "This model can be attached to the following unit:\n- Kroot Carnivores\n- Kroot Farstalkers"
            },
            {
                "name": "War Leader",
                "description": "Once per battle round, one unit from your army with this ability can use it when its unit is targeted with a Stratagem. If it does, reduce the CP cost of that use of that Stratagem by 1CP."
            },
            {
                "name": "Harnessed Alien Instincts",
                "description": "In your Shooting phase, this unit can select one visible enemy unit within 12\". That enemy unit is prey-marked:\n- While a unit is prey-marked, that unit has +3\" detection range."
            }
        ]
    },
    "Krootox Rampagers": {
        "stats": {
            "stat_movement": "7\"",
            "stat_toughness": 6,
            "stat_save": "5+",
            "stat_wounds": 5,
            "stat_leadership": "7+",
            "stat_oc": 2,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Hunting blades",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "3",
                "skill": "3+",
                "strength": "4",
                "ap": "-1",
                "damage": "1",
                "keywords": "Lance"
            },
            {
                "name": "Kroot pistol and hunting javelins",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "2",
                "skill": "4+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Assault, Pistol"
            },
            {
                "name": "Rampager fists",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "3+",
                "strength": "6",
                "ap": "-1",
                "damage": "2",
                "keywords": "Extra Attacks, Sustained Hits 1"
            }
        ],
        "abilities": [
            {
                "name": "Kroot Linebreakers",
                "description": "Each time this unit ends a Charge move, select one enemy unit within Engagement Range of it, then roll one D6 for each model in this unit that is within Engagement Range of that enemy unit: for each 4+, that enemy unit suffers D3 mortal wounds. If one or more enemy models are destroyed as a result of these mortal wounds, that enemy unit must take a Battle-shock test."
            },
            {
                "name": "Harnessed Alien Instincts",
                "description": "In your Shooting phase, this unit can select one visible enemy unit within 12\". That enemy unit is prey-marked:\n- While a unit is prey-marked, that unit has +3\" detection range."
            }
        ]
    },
    "Krootox Riders": {
        "stats": {
            "stat_movement": "7\"",
            "stat_toughness": 6,
            "stat_save": "5+",
            "stat_wounds": 5,
            "stat_leadership": "7+",
            "stat_oc": 2,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Krootox fists",
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
                "name": "Repeater cannon",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "2",
                "skill": "4+",
                "strength": "7",
                "ap": "-1",
                "damage": "2",
                "keywords": "Rapid Fire 2"
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
                "name": "Tanglecannon",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "D6+1",
                "skill": "4+",
                "strength": "6",
                "ap": "0",
                "damage": "1",
                "keywords": "Blast, Heavy"
            }
        ],
        "abilities": [
            {
                "name": "Kroot Packmates",
                "description": "Once per turn, in your opponent's Shooting phase, when a friendly KROOT INFANTRY unit within 6\" of this unit is selected as the target of an attack, one unit from your army with this ability can use it. If it does, after that enemy unit has finished making its attacks, that unit with this ability can shoot as if it were your Shooting phase, but when resolving those attacks it can only target that enemy unit (and only if it is an eligible target)."
            },
            {
                "name": "Harnessed Alien Instincts",
                "description": "In your Shooting phase, this unit can select one visible enemy unit within 12\". That enemy unit is prey-marked:\n- While a unit is prey-marked, that unit has +3\" detection range."
            }
        ]
    },
    "Manta": {
        "stats": {
            "stat_movement": "40\"",
            "stat_toughness": 14,
            "stat_save": "2+",
            "stat_wounds": 60,
            "stat_leadership": "7+",
            "stat_oc": None,
            "stat_invuln": "5+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Armoured hull",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "8",
                "skill": "5+",
                "strength": "6",
                "ap": "0",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "Heavy rail cannon",
                "weapon_type": "ranged",
                "range": "120\"",
                "attacks": "1",
                "skill": "4+",
                "strength": "26",
                "ap": "-5",
                "damage": "12",
                "keywords": "Devastating Wounds"
            },
            {
                "name": "Long-barrelled burst cannon array",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "32",
                "skill": "4+",
                "strength": "6",
                "ap": "-1",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "\u27a4 Ion cannon - standard",
                "weapon_type": "ranged",
                "range": "60\"",
                "attacks": "D6+3",
                "skill": "4+",
                "strength": "7",
                "ap": "-1",
                "damage": "2",
                "keywords": "Blast"
            },
            {
                "name": "\u27a4 Ion cannon - overcharge",
                "weapon_type": "ranged",
                "range": "60\"",
                "attacks": "D6+3",
                "skill": "4+",
                "strength": "8",
                "ap": "-2",
                "damage": "3",
                "keywords": "Blast, Hazardous"
            },
            {
                "name": "Seeker missile",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "1",
                "skill": "4+",
                "strength": "14",
                "ap": "-3",
                "damage": "D6+1",
                "keywords": "One Shot"
            },
            {
                "name": "Missile pod",
                "weapon_type": "ranged",
                "range": "30\"",
                "attacks": "2",
                "skill": "4+",
                "strength": "7",
                "ap": "-1",
                "damage": "2",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Aggressive Deployment",
                "description": "In your Shooting phase, after this model has shot, select one enemy unit hit by one or more of those attacks. Until the end of the phase, each time a friendly model that disembarked from this TRANSPORT this turn makes an attack that targets that enemy unit, you can re-roll the Wound roll."
            },
            {
                "name": "Air Caste Colossus",
                "description": "Each time you target this model with a Stratagem, you must spend three times that Stratagem\u2019s stated CP cost to do so."
            },
            {
                "name": "Damaged: 1-20 Wounds Remaining",
                "description": "While this model has 1-20 wounds remaining, each time this model makes an attack, subtract 1 from the Hit roll."
            }
        ]
    },
    "Pathfinder Team": {
        "stats": {
            "stat_movement": "7\"",
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
                "name": "Pulse carbine",
                "weapon_type": "ranged",
                "range": "20\"",
                "attacks": "2",
                "skill": "4+",
                "strength": "5",
                "ap": "0",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "Pulse pistol",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "1",
                "skill": "4+",
                "strength": "5",
                "ap": "0",
                "damage": "1",
                "keywords": "Pistol"
            },
            {
                "name": "Close combat weapon",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "1",
                "skill": "5+",
                "strength": "3",
                "ap": "0",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "\u27a4 Semi-automatic grenade launcher - EMP",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "1",
                "skill": "4+",
                "strength": "3",
                "ap": "0",
                "damage": "1",
                "keywords": "Anti-Vehicle 4+, Devastating Wounds"
            },
            {
                "name": "\u27a4 Semi-automatic grenade launcher - fusion",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "1",
                "skill": "4+",
                "strength": "6",
                "ap": "-1",
                "damage": "3",
                "keywords": "-"
            },
            {
                "name": "\u27a4 Ion rifle - standard",
                "weapon_type": "ranged",
                "range": "30\"",
                "attacks": "3",
                "skill": "5+",
                "strength": "7",
                "ap": "-1",
                "damage": "1",
                "keywords": "Heavy"
            },
            {
                "name": "\u27a4 Ion rifle - overcharge",
                "weapon_type": "ranged",
                "range": "30\"",
                "attacks": "3",
                "skill": "5+",
                "strength": "8",
                "ap": "-2",
                "damage": "2",
                "keywords": "Hazardous, Heavy"
            },
            {
                "name": "Rail rifle",
                "weapon_type": "ranged",
                "range": "30\"",
                "attacks": "1",
                "skill": "5+",
                "strength": "10",
                "ap": "-4",
                "damage": "3",
                "keywords": "Devastating Wounds, Heavy"
            },
            {
                "name": "Drone burst cannon",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "4",
                "skill": "5+",
                "strength": "5",
                "ap": "0",
                "damage": "1",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Target Uploaded",
                "description": "Each time a model in this unit makes an attack that targets their Spotted unit, improve the Ballistic Skill characteristic of that attack by 1 and that attack has the [IGNORES COVER] ability."
            },
            {
                "name": "Grav-inhibitor Drone",
                "description": "Each time an enemy unit selects the bearer's unit as the target of a charge, subtract 2 from the Charge roll (this is not cumulative with any other negative modifiers to that Charge roll)."
            },
            {
                "name": "Pulse Accelerator Drone",
                "description": "Add 6\" to the Range characteristic of pulse carbines equipped by models in the bearer\u2019s unit."
            },
            {
                "name": "Recon Drone",
                "description": "The bearer is equipped with 1 drone burst cannon and the bearer\u2019s unit has the Infiltrators ability."
            }
        ]
    },
    "Piranhas": {
        "stats": {
            "stat_movement": "14\"",
            "stat_toughness": 7,
            "stat_save": "4+",
            "stat_wounds": 7,
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
                "attacks": "2",
                "skill": "5+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "Twin pulse carbine",
                "weapon_type": "ranged",
                "range": "20\"",
                "attacks": "2",
                "skill": "4+",
                "strength": "5",
                "ap": "0",
                "damage": "1",
                "keywords": "Twin-linked, Assault"
            },
            {
                "name": "Piranha burst cannon",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "4",
                "skill": "4+",
                "strength": "6",
                "ap": "-1",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "Piranha fusion blaster",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "1",
                "skill": "4+",
                "strength": "9",
                "ap": "-4",
                "damage": "D6",
                "keywords": "Melta 4"
            },
            {
                "name": "Seeker missile",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "1",
                "skill": "4+",
                "strength": "14",
                "ap": "-3",
                "damage": "D6+1",
                "keywords": "One Shot"
            }
        ],
        "abilities": [
            {
                "name": "Drone Harassment Tactics",
                "description": "At the end of your Movement phase, select one enemy unit within 12\" of this unit; that enemy unit must take a Battle-shock test."
            }
        ]
    },
    "Razorshark Strike Fighter": {
        "stats": {
            "stat_movement": "-",
            "stat_toughness": 10,
            "stat_save": "3+",
            "stat_wounds": 12,
            "stat_leadership": "7+",
            "stat_oc": None,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "\u27a4 Quad ion turret - standard",
                "weapon_type": "ranged",
                "range": "30\"",
                "attacks": "8",
                "skill": "4+",
                "strength": "7",
                "ap": "-1",
                "damage": "1",
                "keywords": "Twin-linked"
            },
            {
                "name": "\u27a4 Quad ion turret - overcharge",
                "weapon_type": "ranged",
                "range": "30\"",
                "attacks": "8",
                "skill": "4+",
                "strength": "8",
                "ap": "-2",
                "damage": "2",
                "keywords": "Hazardous, Twin-linked"
            },
            {
                "name": "Seeker missile",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "1",
                "skill": "4+",
                "strength": "14",
                "ap": "-3",
                "damage": "D6+1",
                "keywords": "One Shot"
            },
            {
                "name": "Armoured hull",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "3",
                "skill": "5+",
                "strength": "6",
                "ap": "0",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "Missile pod",
                "weapon_type": "ranged",
                "range": "30\"",
                "attacks": "2",
                "skill": "4+",
                "strength": "7",
                "ap": "-1",
                "damage": "2",
                "keywords": "-"
            },
            {
                "name": "Accelerator burst cannon",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "4",
                "skill": "4+",
                "strength": "6",
                "ap": "-1",
                "damage": "1",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Ground Strike Fighter",
                "description": "Each time this model makes a ranged attack that targets an enemy unit that cannot FLY, add 1 to the Hit roll."
            },
            {
                "name": "Damaged: 1-4 Wounds Remaining",
                "description": "While this model has 1-4 wounds remaining, each time this model makes an attack, subtract 1 from the Hit roll."
            }
        ]
    },
    "Riptide Battlesuit": {
        "stats": {
            "stat_movement": "10\"",
            "stat_toughness": 9,
            "stat_save": "2+",
            "stat_wounds": 14,
            "stat_leadership": "7+",
            "stat_oc": 4,
            "stat_invuln": "4+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Riptide fists",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "6",
                "skill": "5+",
                "strength": "6",
                "ap": "0",
                "damage": "2",
                "keywords": "-"
            },
            {
                "name": "Heavy burst cannon",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "12",
                "skill": "4+",
                "strength": "6",
                "ap": "-1",
                "damage": "2",
                "keywords": "-"
            },
            {
                "name": "\u27a4 Ion accelerator - standard",
                "weapon_type": "ranged",
                "range": "72\"",
                "attacks": "6",
                "skill": "4+",
                "strength": "9",
                "ap": "-2",
                "damage": "3",
                "keywords": "-"
            },
            {
                "name": "\u27a4 Ion accelerator - overcharge",
                "weapon_type": "ranged",
                "range": "72\"",
                "attacks": "6",
                "skill": "4+",
                "strength": "10",
                "ap": "-3",
                "damage": "4",
                "keywords": "Hazardous"
            },
            {
                "name": "Missile pod",
                "weapon_type": "ranged",
                "range": "30\"",
                "attacks": "2",
                "skill": "5+",
                "strength": "7",
                "ap": "-1",
                "damage": "2",
                "keywords": "-"
            },
            {
                "name": "Twin smart missile system",
                "weapon_type": "ranged",
                "range": "30\"",
                "attacks": "3",
                "skill": "4+",
                "strength": "5",
                "ap": "0",
                "damage": "1",
                "keywords": "Indirect Fire, Twin-linked"
            },
            {
                "name": "Twin fusion blaster",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "1",
                "skill": "4+",
                "strength": "9",
                "ap": "-4",
                "damage": "D6",
                "keywords": "Melta 2, Twin-linked"
            },
            {
                "name": "Twin plasma rifle",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "1",
                "skill": "4+",
                "strength": "8",
                "ap": "-3",
                "damage": "3",
                "keywords": "Twin-linked"
            }
        ],
        "abilities": [
            {
                "name": "Nova Charge",
                "description": "Once per battle, when this unit is selected to shoot in your Shooting phase, select one ranged weapon equipped by this model. Until the end of the phase, that weapon has the [DEVASTATING WOUNDS] ability."
            },
            {
                "name": "Damaged: 1-4 Wounds Remaining",
                "description": "While this model has 1-4 wounds remaining, each time this model makes an attack, subtract 1 from the Hit roll."
            },
            {
                "name": "Battlesuit Support System",
                "description": "The bearer\u2019s unit is eligible to shoot in a turn in which it Fell Back, but when doing so only models equipped with this wargear can make ranged attacks."
            },
            {
                "name": "Weapon Support System",
                "description": "Each time the bearer makes a ranged attack, you can ignore any or all modifiers to the Hit roll."
            }
        ]
    },
    "Sky Ray Gunship": {
        "stats": {
            "stat_movement": "10\"",
            "stat_toughness": 10,
            "stat_save": "3+",
            "stat_wounds": 14,
            "stat_leadership": "7+",
            "stat_oc": 3,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Seeker missile rack",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "3",
                "skill": "4+",
                "strength": "14",
                "ap": "-3",
                "damage": "D6+1",
                "keywords": "Twin-linked"
            },
            {
                "name": "Armoured hull",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "3",
                "skill": "5+",
                "strength": "6",
                "ap": "0",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "Accelerator burst cannon",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "4",
                "skill": "4+",
                "strength": "6",
                "ap": "-1",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "Twin pulse carbine",
                "weapon_type": "ranged",
                "range": "20\"",
                "attacks": "2",
                "skill": "4+",
                "strength": "5",
                "ap": "0",
                "damage": "1",
                "keywords": "Twin-linked, Assault"
            },
            {
                "name": "Smart missile system",
                "weapon_type": "ranged",
                "range": "30\"",
                "attacks": "3",
                "skill": "4+",
                "strength": "5",
                "ap": "0",
                "damage": "1",
                "keywords": "Indirect Fire"
            }
        ],
        "abilities": [
            {
                "name": "Velocity Tracker",
                "description": "Each time this model makes an attack with a ranged weapon that targets a unit that can FLY, you can re-roll the Hit roll."
            },
            {
                "name": "Damaged: 1-5 Wounds Remaining",
                "description": "While this model has 1-5 wounds remaining, each time this model makes an attack, subtract 1 from the Hit roll."
            },
            {
                "name": "Targeting Array",
                "description": "Each time this model is selected to shoot, you can re-roll one Hit roll or you can re-roll one Wound roll when resolving those attacks."
            }
        ]
    },
    "Stealth Battlesuits": {
        "stats": {
            "stat_movement": "8\"",
            "stat_toughness": 4,
            "stat_save": "3+",
            "stat_wounds": 2,
            "stat_leadership": "7+",
            "stat_oc": 1,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Battlesuit fists",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "2",
                "skill": "5+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "Burst cannon",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "4",
                "skill": "4+",
                "strength": "5",
                "ap": "0",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "Fusion blaster",
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
                "name": "Pulse pistol",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "1",
                "skill": "4+",
                "strength": "5",
                "ap": "0",
                "damage": "1",
                "keywords": "Pistol"
            }
        ],
        "abilities": [
            {
                "name": "Forward Observers",
                "description": "Each time this unit is an Observer unit, until the end of the phase, each time a ranged attack is made by a model in a Guided unit that targets their Spotted unit, re-roll a Hit roll of 1 and re-roll a Wound roll of 1."
            },
            {
                "name": "Localised Stealth Projectors (Aura)",
                "description": "When a friendly KROOT/VESPID STINGWINGS unit within 6\" of this unit has shot, those attacks do not prevent that unit from being hidden."
            },
            {
                "name": "Homing Beacon",
                "description": "Once per battle, you can use the Rapid Ingress Stratagem for 0CP. The target must be set up within 3\" of the bearer\u2019s unit and more than 8\" away from all enemy units.\nDesigner\u2019s Note: Place a Homing Beacon token next to this unit, removing it once this ability is used."
            }
        ]
    },
    "Stormsurge": {
        "stats": {
            "stat_movement": "8\"",
            "stat_toughness": 11,
            "stat_save": "2+",
            "stat_wounds": 20,
            "stat_leadership": "7+",
            "stat_oc": 6,
            "stat_invuln": "4+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Cluster rocket system",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "4D6",
                "skill": "4+",
                "strength": "5",
                "ap": "0",
                "damage": "1",
                "keywords": "Blast, Heavy"
            },
            {
                "name": "Destroyer missiles",
                "weapon_type": "ranged",
                "range": "72\"",
                "attacks": "1",
                "skill": "4+",
                "strength": "16",
                "ap": "-4",
                "damage": "D6+2",
                "keywords": "Heavy"
            },
            {
                "name": "Thunderous footfalls",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "3",
                "skill": "5+",
                "strength": "8",
                "ap": "-1",
                "damage": "2",
                "keywords": "-"
            },
            {
                "name": "Twin smart missile system",
                "weapon_type": "ranged",
                "range": "30\"",
                "attacks": "3",
                "skill": "4+",
                "strength": "5",
                "ap": "0",
                "damage": "1",
                "keywords": "Heavy, Indirect Fire, Twin-Linked"
            },
            {
                "name": "Pulse Driver Cannon",
                "weapon_type": "ranged",
                "range": "72\"",
                "attacks": "D6+3",
                "skill": "4+",
                "strength": "12",
                "ap": "-3",
                "damage": "3",
                "keywords": "Blast, Heavy"
            },
            {
                "name": "\u27a4 Pulse blast cannon - focused",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "2",
                "skill": "4+",
                "strength": "24",
                "ap": "-6",
                "damage": "12",
                "keywords": "Heavy"
            },
            {
                "name": "\u27a4 Pulse blast cannon - dispersed",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "6",
                "skill": "4+",
                "strength": "10",
                "ap": "-2",
                "damage": "4",
                "keywords": "Heavy"
            },
            {
                "name": "Twin airbursting fragmentation projector",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "D6",
                "skill": "4+",
                "strength": "3",
                "ap": "0",
                "damage": "1",
                "keywords": "Blast, Heavy, Indirect Fire, Twin-linked"
            },
            {
                "name": "Twin burst cannon",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "4",
                "skill": "4+",
                "strength": "5",
                "ap": "0",
                "damage": "1",
                "keywords": "Heavy, Twin-linked"
            },
            {
                "name": "Twin T'au flamer",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "D6",
                "skill": "N/A",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Ignores Cover, Torrent, Twin-linked"
            }
        ],
        "abilities": [
            {
                "name": "Damaged: 1-5 Wounds Remaining",
                "description": "While this model has 1-5 wounds remaining, subtract 3 from this models Objective Control characteristic, and each time this model makes an attack, subtract 1 from the Hit roll."
            },
            {
                "name": "Heavy Walker",
                "description": "Each time this model makes a Normal, Advance or Fall Back move, it can move over models (excluding TITANIC models) and terrain features that are 4\" or less in height as if they were not there."
            },
            {
                "name": "Support System",
                "description": "Each time this model makes a ranged attack, you can ignore any or all modifiers to the Hit roll."
            },
            {
                "name": "Titan-killer",
                "description": "Each time this model makes a ranged attack that targets a TITANIC or TOWERING unit, you can re-roll the Hit roll."
            }
        ]
    },
    "Strike Team": {
        "stats": {
            "stat_movement": "6\"",
            "stat_toughness": 3,
            "stat_save": "4+",
            "stat_wounds": 1,
            "stat_leadership": "7+",
            "stat_oc": 2,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Pulse carbine",
                "weapon_type": "ranged",
                "range": "20\"",
                "attacks": "2",
                "skill": "4+",
                "strength": "5",
                "ap": "0",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "Pulse pistol",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "1",
                "skill": "4+",
                "strength": "5",
                "ap": "0",
                "damage": "1",
                "keywords": "Pistol"
            },
            {
                "name": "Close combat weapon",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "1",
                "skill": "5+",
                "strength": "3",
                "ap": "0",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "Pulse rifle",
                "weapon_type": "ranged",
                "range": "30\"",
                "attacks": "1",
                "skill": "4+",
                "strength": "5",
                "ap": "0",
                "damage": "1",
                "keywords": "Rapid Fire 1"
            },
            {
                "name": "Support turret",
                "weapon_type": "ranged",
                "range": "30\"",
                "attacks": "2",
                "skill": "5+",
                "strength": "5",
                "ap": "0",
                "damage": "1",
                "keywords": "Indirect Fire, Twin-linked"
            }
        ],
        "abilities": [
            {
                "name": "Suppression Volley",
                "description": "In your Shooting phase, after this unit has shot, select one enemy INFANTRY unit hit by one or more of those attacks. Until the start of your next turn, while unit is on the battlefield, that enemy unit is suppressed. While a unit is suppressed, each time a model in that unit makes an attack, subtract 1 from the Hit roll."
            },
            {
                "name": "DS8 Support Turret",
                "description": "In your Movement phase, if this unit Remains Stationary, until the start of your next turn, its Shas\u2019ui model is equipped with the support turret weapon.\n\nDesigner\u2019s Note: Place a Support Turret token next to this unit to remind you."
            }
        ]
    },
    "Sun Shark Bomber": {
        "stats": {
            "stat_movement": "-",
            "stat_toughness": 9,
            "stat_save": "3+",
            "stat_wounds": 12,
            "stat_leadership": "7+",
            "stat_oc": None,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "\u27a4 Twin ion rifle - standard",
                "weapon_type": "ranged",
                "range": "30\"",
                "attacks": "3",
                "skill": "4+",
                "strength": "7",
                "ap": "-1",
                "damage": "1",
                "keywords": "Twin-linked"
            },
            {
                "name": "\u27a4 Twin ion rifle - overcharged",
                "weapon_type": "ranged",
                "range": "30\"",
                "attacks": "3",
                "skill": "4+",
                "strength": "8",
                "ap": "-2",
                "damage": "2",
                "keywords": "Hazardous, Twin-linked"
            },
            {
                "name": "Seeker missile",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "1",
                "skill": "4+",
                "strength": "14",
                "ap": "-3",
                "damage": "D6+1",
                "keywords": "One Shot"
            },
            {
                "name": "Armoured hull",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "3",
                "skill": "5+",
                "strength": "6",
                "ap": "0",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "Twin missile pod",
                "weapon_type": "ranged",
                "range": "30\"",
                "attacks": "2",
                "skill": "4+",
                "strength": "7",
                "ap": "-1",
                "damage": "2",
                "keywords": "Twin-linked"
            },
            {
                "name": "Missile pod",
                "weapon_type": "ranged",
                "range": "30\"",
                "attacks": "2",
                "skill": "4+",
                "strength": "7",
                "ap": "-1",
                "damage": "2",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Pulse Bombs",
                "description": "At the end of your opponent\u2019s Fight phase, select one visible enemy unit (excluding Lone Operative units) within 24\" of this unit, and roll six D6 for that unit: For each 4+, that unit suffers 1 mortal wound."
            },
            {
                "name": "Damaged: 1-4 Wounds Remaining",
                "description": "While this model has 1-4 wounds remaining, each time this model makes an attack, subtract 1 from the Hit roll."
            }
        ]
    },
    "The Twin Lance": {
        "stats": {
            "stat_movement": "10\"",
            "stat_toughness": 6,
            "stat_save": "2+",
            "stat_wounds": 8,
            "stat_leadership": "6+",
            "stat_oc": 2,
            "stat_invuln": "4+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Fusion eliminator",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "2",
                "skill": "2+",
                "strength": "10",
                "ap": "-4",
                "damage": "D6",
                "keywords": "Melta 2"
            },
            {
                "name": "Fusion eliminator",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "1",
                "skill": "4+",
                "strength": "10",
                "ap": "-4",
                "damage": "D6+2",
                "keywords": "Extra Attacks"
            },
            {
                "name": "Shardstorm burst system",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "D6",
                "skill": "2+",
                "strength": "5",
                "ap": "0",
                "damage": "1",
                "keywords": "Pistol"
            },
            {
                "name": "Twin pulse blaster",
                "weapon_type": "ranged",
                "range": "10\"",
                "attacks": "2",
                "skill": "5+",
                "strength": "6",
                "ap": "-1",
                "damage": "1",
                "keywords": "Assault, Twin-linked"
            },
            {
                "name": "XV pulse pistol",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "2",
                "skill": "2+",
                "strength": "6",
                "ap": "-1",
                "damage": "2",
                "keywords": "Rapid Fire 2"
            },
            {
                "name": "XV pulse pistol",
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
                "name": "\u27a4 Ion scattercannon - overcharge",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "4",
                "skill": "2+",
                "strength": "8",
                "ap": "-3",
                "damage": "3",
                "keywords": "Hazardous, Rapid Fire 2"
            },
            {
                "name": "Ion scattercannon",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "3",
                "skill": "4+",
                "strength": "7",
                "ap": "-2",
                "damage": "2",
                "keywords": "Extra Attacks"
            },
            {
                "name": "\u27a4 Ion scattercannon - standard",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "4",
                "skill": "2+",
                "strength": "7",
                "ap": "-2",
                "damage": "2",
                "keywords": "Rapid Fire 2"
            }
        ],
        "abilities": [
            {
                "name": "Neocapacitor Shields",
                "description": "At the start of your opponent\u2019s Charge phase, you can select one visible enemy unit (excluding MONSTER and VEHICLE units) within 12\" of this unit. That unit must take a Battle-shock test and, until the end of the turn, subtract 1 from Charge rolls made for that unit."
            },
            {
                "name": "Exemplars of Mont\u2019ka",
                "description": "Each time a model in this unit makes a ranged attack that targets the closest eligible target, that attack has the [SUSTAINED HITS 1] and [IGNORES COVER] abilities."
            },
            {
                "name": "Retro-thrusters",
                "description": "At the end of the Fight phase, if this unit was eligible to fight this phase, this unit can either make a Normal move of up to 6\" or a Fall Back move."
            },
            {
                "name": "MV15 Gun Drone",
                "description": "The bearer is equipped with 1 twin pulse blaster."
            }
        ]
    },
    "Tidewall Droneport": {
        "stats": {
            "stat_movement": "4\"",
            "stat_toughness": 8,
            "stat_save": "3+",
            "stat_wounds": 10,
            "stat_leadership": "7+",
            "stat_oc": 0,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Drone defenders",
                "weapon_type": "ranged",
                "range": "20\"",
                "attacks": "8",
                "skill": "5+",
                "strength": "5",
                "ap": "0",
                "damage": "1",
                "keywords": "Assault, Twin-linked"
            }
        ],
        "abilities": [
            {
                "name": "Droneport",
                "description": "Each time this FORTIFICATION is selected to shoot, its drone defenders weapon will target and resolve attacks against every enemy unit that is an eligible target to this FORTIFICATION."
            },
            {
                "name": "Tidewall Cover",
                "description": "Each time a ranged attack is allocated to a model, if that model is not fully visible to every model in the attacking unit because of this FORTIFICATION, that model has the Benefit of Cover against that attack."
            }
        ]
    },
    "Tidewall Shieldline": {
        "stats": {
            "stat_movement": "4\"",
            "stat_toughness": 8,
            "stat_save": "3+",
            "stat_wounds": 10,
            "stat_leadership": "7+",
            "stat_oc": 0,
            "stat_invuln": "5+",
            "stat_fnp": ""
        },
        "abilities": [
            {
                "name": "Tidewall Cover",
                "description": "Each time a ranged attack is allocated to a model, if that model is not fully visible to every model in the attacking unit because of this FORTIFICATION, that model has the Benefit of Cover against that attack."
            },
            {
                "name": "Tidewall Defence Platform",
                "description": "If equipped with a Tidewall defence platform, this FORTIFICATION has a Wounds characteristic of 15."
            }
        ]
    },
    "Tiger Shark": {
        "stats": {
            "stat_movement": "-",
            "stat_toughness": 11,
            "stat_save": "3+",
            "stat_wounds": 18,
            "stat_leadership": "7+",
            "stat_oc": None,
            "stat_invuln": "5+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Armoured hull",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "3",
                "skill": "5+",
                "strength": "6",
                "ap": "0",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "Missile pod",
                "weapon_type": "ranged",
                "range": "30\"",
                "attacks": "2",
                "skill": "4+",
                "strength": "7",
                "ap": "-1",
                "damage": "2",
                "keywords": "-"
            },
            {
                "name": "\u27a4 Cyclic ion blaster - standard",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "3",
                "skill": "4+",
                "strength": "7",
                "ap": "-1",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "\u27a4 Cyclic ion blaster - overcharge",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "3",
                "skill": "4+",
                "strength": "8",
                "ap": "-2",
                "damage": "2",
                "keywords": "Hazardous"
            },
            {
                "name": "Burst cannon",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "4",
                "skill": "4+",
                "strength": "5",
                "ap": "0",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "\u27a4 Ion cannon - standard",
                "weapon_type": "ranged",
                "range": "60\"",
                "attacks": "D6+3",
                "skill": "4+",
                "strength": "7",
                "ap": "-1",
                "damage": "2",
                "keywords": "Blast"
            },
            {
                "name": "\u27a4 Ion cannon - overcharge",
                "weapon_type": "ranged",
                "range": "60\"",
                "attacks": "D6+3",
                "skill": "4+",
                "strength": "8",
                "ap": "-2",
                "damage": "3",
                "keywords": "Blast, Hazardous"
            },
            {
                "name": "Swiftstrike burst cannon",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "16",
                "skill": "4+",
                "strength": "6",
                "ap": "-1",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "Swiftstrike railgun",
                "weapon_type": "ranged",
                "range": "72\"",
                "attacks": "1",
                "skill": "4+",
                "strength": "20",
                "ap": "-5",
                "damage": "D6+6",
                "keywords": "Devastating Wounds"
            },
            {
                "name": "Seeker missile",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "1",
                "skill": "4+",
                "strength": "14",
                "ap": "-3",
                "damage": "D6+1",
                "keywords": "One Shot"
            },
            {
                "name": "Skyspear missile rack",
                "weapon_type": "ranged",
                "range": "72\"",
                "attacks": "D6+1",
                "skill": "4+",
                "strength": "6",
                "ap": "-1",
                "damage": "1",
                "keywords": "Anti-Fly 3+, Blast"
            }
        ],
        "abilities": [
            {
                "name": "Strafing Run",
                "description": "In your Shooting phase, after this model has shot, select one enemy unit hit by one or more of those attacks that cannot FLY. That enemy unit must take a Battle-shock test."
            },
            {
                "name": "Damaged: 1-6 Wounds Remaining",
                "description": "While this model has 1-6 wounds remaining, each time this model makes an attack, subtract 1 from the Hit roll."
            },
            {
                "name": "Transport bay",
                "description": "The bearer has the TRANSPORT keyword and has a transport capacity of 12 TACTICAL DRONES models."
            }
        ]
    },
    "Vespid Stingwings": {
        "stats": {
            "stat_movement": "12\"",
            "stat_toughness": 4,
            "stat_save": "4+",
            "stat_wounds": 1,
            "stat_leadership": "7+",
            "stat_oc": 1,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Stingwing claws",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "1",
                "skill": "4+",
                "strength": "4",
                "ap": "-1",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "Neutron blaster",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "2",
                "skill": "4+",
                "strength": "5",
                "ap": "-2",
                "damage": "2",
                "keywords": "Assault"
            },
            {
                "name": "T'au flamer",
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
                "name": "Neutron grenade launcher",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "D6",
                "skill": "4+",
                "strength": "4",
                "ap": "-1",
                "damage": "2",
                "keywords": "Anti-Infantry 3+, Blast"
            },
            {
                "name": "Neutron rail rifle",
                "weapon_type": "ranged",
                "range": "30\"",
                "attacks": "1",
                "skill": "4+",
                "strength": "10",
                "ap": "-4",
                "damage": "3",
                "keywords": "Devastating Wounds"
            }
        ],
        "abilities": [
            {
                "name": "Airborne Agility",
                "description": "At the end of your opponent\u2019s turn, if this unit is not within Engagement Range of one or more enemy units, you can remove it from the battlefield and place it into Strategic Reserves."
            },
            {
                "name": "Oversight Drone",
                "description": "Once per battle, when the bearer\u2019s unit is selected to shoot, until the end of the phase, ranged weapons equipped by models in this unit have the [IGNORES COVER] ability.\n\nDesigner\u2019s Note: Place an Oversight Drone token next to the bearer, removing it once this ability has been used."
            }
        ]
    }
}


class Command(BaseCommand):
    """Refresh T'au Empire stat lines, weapon profiles, and abilities from BSData."""

    help = "Refresh 11th Edition stats/weapons/abilities for T'au Empire units."

    def add_arguments(self, parser):
        """Add --dry-run flag."""
        parser.add_argument(
            '--dry-run', action='store_true',
            help='Preview changes without writing to the database.',
        )

    def handle(self, *args, **options):
        """Iterate TAU_EMPIRE_DATASHEETS and refresh each unit's datasheet data."""
        dry_run = options['dry_run']
        updated = 0
        skipped = 0

        with transaction.atomic():
            for name, payload in TAU_EMPIRE_DATASHEETS.items():
                try:
                    unit = UnitType.objects.get(name=name, faction__name="T'au Empire")
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
