"""
Management command: seed_aeldari_datasheets

Refreshes stat lines, weapon profiles, and abilities for all Aeldari units
using 11th Edition data sourced from BSData/wh40k-11e ("Aeldari -
Craftworlds.json" roster, resolved against "Aeldari - Aeldari
Library.json") -- the same source used by seed_aeldari_points.py.

Usage:
    python manage.py seed_aeldari_datasheets
    python manage.py seed_aeldari_datasheets --dry-run

Notes:
- Does NOT touch points_cost or category -- those are handled entirely by
  seed_aeldari_points.py. This command only refreshes stat_* fields,
  WeaponProfile rows, and UnitAbility rows.
- Per-field safety rule: a unit's stats/weapons/abilities are only
  overwritten when BSData actually has that data for it. If extraction
  found nothing, the existing DB value/rows are left untouched rather than
  blanked.
- Weapon profiles list EVERY weapon option reachable for a unit, each as
  its own row -- same as every other faction.
- Aeldari-specific extraction gotcha (new this faction): many units'
  stat/weapon/ability profiles are not embedded directly on the entry or
  reachable through the usual selectionEntries/selectionEntryGroups tree at
  all -- they're referenced via that entry's own infoLinks with
  type == "profile", pointing by id into the catalogue-level sharedProfiles
  list (confirmed on Corsair Voidreavers, Corsair Skyreavers, Warlock
  Conclave, Warlock Skyrunners, and three of the new Ynnari units). The
  walker now also resolves profile-type infoLinks against sharedProfiles
  before giving up, on top of the AdMech-era fixes (top-level
  selectionEntries recursion, name-matched sharedProfiles fallback for
  stats). All 68/68 active units resolved cleanly with this in place --
  0 missing stats, weapons, or abilities.
- Ynnari units (Ynnari Archon/Incubi/Kabalite Warriors/Raider/Reavers/
  Succubus/Venom/Wyches) resolve directly by their literal BSData roster
  name, same as every other unit -- no alias needed.
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from calculators.models import UnitAbility, UnitType, WeaponProfile

# (name -> {stats?, weapons?, abilities?}). Missing keys mean "no data
# found for this field -- leave existing DB data untouched."
AELDARI_DATASHEETS = {
    "Asurmen": {
        "stats": {
            "stat_movement": "7\"",
            "stat_toughness": 3,
            "stat_save": "2+",
            "stat_wounds": 5,
            "stat_leadership": "6+",
            "stat_oc": 1,
            "stat_invuln": "4+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "The Bloody Twins",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "6",
                "skill": "2+",
                "strength": "5",
                "ap": "-1",
                "damage": "2",
                "keywords": "Assault, Pistol"
            },
            {
                "name": "The Sword of Asur",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "6",
                "skill": "2+",
                "strength": "6",
                "ap": "-3",
                "damage": "3",
                "keywords": "Devastating Wounds"
            }
        ],
        "abilities": [
            {
                "name": "Hand of Asuryan",
                "description": "Once per battle, when this model is selected to shoot, it can use this ability. If it does, until the end of the phase, its Bloody Twins weapon has a Damage characteristic of 3 and the [ANTI-INFANTRY 5+] and [DEVASTATING WOUNDS] abilities."
            },
            {
                "name": "Tactical Acumen",
                "description": "While this model is leading a unit, in your Shooting phase, after that unit has shot, it can make a Normal move of up to 6\". If it does, until the end of the turn, that unit is not eligible to declare a charge."
            },
            {
                "name": "Leader",
                "description": "This model can be attached to the following unit:\n- Dire Avengers"
            }
        ]
    },
    "Autarch": {
        "stats": {
            "stat_movement": "7\"",
            "stat_toughness": 3,
            "stat_save": "3+",
            "stat_wounds": 4,
            "stat_leadership": "6+",
            "stat_oc": 1,
            "stat_invuln": "4+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Scorpion Chainsword",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "7",
                "skill": "2+",
                "strength": "4",
                "ap": "-1",
                "damage": "1",
                "keywords": "Sustained Hits 1"
            },
            {
                "name": "Banshee Blade",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "5",
                "skill": "2+",
                "strength": "4",
                "ap": "-2",
                "damage": "2",
                "keywords": "Anti-Infantry 3+"
            },
            {
                "name": "Star Glaive",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "2+",
                "strength": "6",
                "ap": "-3",
                "damage": "3",
                "keywords": "-"
            },
            {
                "name": "Shuriken Pistol",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "1",
                "skill": "2+",
                "strength": "4",
                "ap": "-1",
                "damage": "1",
                "keywords": "Assault, Pistol"
            },
            {
                "name": "\u27a4 Reaper Launcher - Starshot",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "10",
                "ap": "-2",
                "damage": "3",
                "keywords": "Heavy, Ignores Cover"
            },
            {
                "name": "\u27a4 Reaper Launcher - Starswarm",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "2",
                "skill": "3+",
                "strength": "4",
                "ap": "-2",
                "damage": "1",
                "keywords": "Heavy, Ignores Cover"
            },
            {
                "name": "Death Spinner",
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
                "name": "Dragon Fusion Gun",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "1",
                "skill": "2+",
                "strength": "9",
                "ap": "-4",
                "damage": "D6",
                "keywords": "Assault, Melta 3"
            },
            {
                "name": "Dragon Fusion Pistol",
                "weapon_type": "ranged",
                "range": "6\"",
                "attacks": "1",
                "skill": "2+",
                "strength": "9",
                "ap": "-4",
                "damage": "D6",
                "keywords": "Assault, Melta 3, Pistol"
            }
        ],
        "abilities": [
            {
                "name": "Superlative Strategist",
                "description": "While this model is leading a unit, you can re-roll Advance rolls made for that unit, and you can re-roll any rolls made for that unit while it is performing an Agile Manoeuvre."
            },
            {
                "name": "Path of Command",
                "description": "Once per battle round, one model from your army with this ability can use it when its unit is targeted with a Stratagem. If it does, reduce the CP cost of that usage of that stratagem by 1CP."
            },
            {
                "name": "Leader",
                "description": "This model can be attached to the following units:\n- Dark Reapers\n- Dire Avengers\n- Fire Dragons\n- Guardian Defenders\n- Howling Banshees\n- Storm Guardians\n- Striking Scorpions"
            },
            {
                "name": "Aspect Training",
                "description": "While this model is leading a Howling Banshees unit, it has the Fights First ability.\nWhile this model is leading a Striking Scorpions unit, it has the Infiltrators, Scouts 7\" and Stealth abilities."
            }
        ]
    },
    "Autarch Wayleaper": {
        "stats": {
            "stat_movement": "14\"",
            "stat_toughness": 3,
            "stat_save": "3+",
            "stat_wounds": 4,
            "stat_leadership": "6+",
            "stat_oc": 1,
            "stat_invuln": "4+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Scorpion Chainsword",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "7",
                "skill": "2+",
                "strength": "4",
                "ap": "-1",
                "damage": "1",
                "keywords": "Sustained Hits 1"
            },
            {
                "name": "Banshee Blade",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "5",
                "skill": "2+",
                "strength": "4",
                "ap": "-2",
                "damage": "2",
                "keywords": "Anti-Infantry 3+"
            },
            {
                "name": "Star Glaive",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "2+",
                "strength": "6",
                "ap": "-3",
                "damage": "3",
                "keywords": "-"
            },
            {
                "name": "Shuriken Pistol",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "1",
                "skill": "2+",
                "strength": "4",
                "ap": "-1",
                "damage": "1",
                "keywords": "Assault, Pistol"
            },
            {
                "name": "\u27a4 Reaper Launcher - Starshot",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "10",
                "ap": "-2",
                "damage": "3",
                "keywords": "Heavy, Ignores Cover"
            },
            {
                "name": "\u27a4 Reaper Launcher - Starswarm",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "2",
                "skill": "3+",
                "strength": "4",
                "ap": "-2",
                "damage": "1",
                "keywords": "Heavy, Ignores Cover"
            },
            {
                "name": "Death Spinner",
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
                "name": "Dragon Fusion Gun",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "1",
                "skill": "2+",
                "strength": "9",
                "ap": "-4",
                "damage": "D6",
                "keywords": "Assault, Melta 3"
            },
            {
                "name": "Dragon Fusion Pistol",
                "weapon_type": "ranged",
                "range": "6\"",
                "attacks": "1",
                "skill": "2+",
                "strength": "9",
                "ap": "-4",
                "damage": "D6",
                "keywords": "Assault, Melta 3, Pistol"
            }
        ],
        "abilities": [
            {
                "name": "Path of Command",
                "description": "Once per battle round, one model from your army with this ability can use it when its unit is targeted with a Stratagem. If it does, reduce the CP cost of that usage of that stratagem by 1CP."
            },
            {
                "name": "Indomitable Strength of Will",
                "description": "While this model is leading a unit, each time you spend a Battle Focus token to enable that unit to perform an Agile Manoeuvre, roll one D6: on a 3+ you gain 1 Battle Focus token."
            },
            {
                "name": "Leader",
                "description": "This model can be attached to the following units:\n- Swooping Hawks\n- Warp Spiders"
            }
        ]
    },
    "Avatar of Khaine": {
        "stats": {
            "stat_movement": "10\"",
            "stat_toughness": 11,
            "stat_save": "2+",
            "stat_wounds": 14,
            "stat_leadership": "6+",
            "stat_oc": 5,
            "stat_invuln": "4+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "The Wailing Doom",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "1",
                "skill": "2+",
                "strength": "16",
                "ap": "-4",
                "damage": "D6+2",
                "keywords": "Sustained Hits D3"
            },
            {
                "name": "\u27a4 The Wailing Doom - Strike",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "6",
                "skill": "2+",
                "strength": "16",
                "ap": "-4",
                "damage": "D6+2",
                "keywords": "-"
            },
            {
                "name": "\u27a4 The Wailing Doom - Sweep",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "12",
                "skill": "2+",
                "strength": "8",
                "ap": "-2",
                "damage": "2",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Molten Form",
                "description": "Each time an attack is allocated to this model, halve the Damage characteristic of that attack."
            },
            {
                "name": "The Bloody Handed (Aura)",
                "description": "While a friendly Aeldari unit is within 6\" of this model, add 1 to Advance and Charge rolls made for that unit."
            },
            {
                "name": "Damaged: 1-5 Wounds Remaining",
                "description": "While this model has 1-5 wounds remaining, each time this model makes an attack, subtract 1 from the Hit roll."
            }
        ]
    },
    "Baharroth": {
        "stats": {
            "stat_movement": "14\"",
            "stat_toughness": 3,
            "stat_save": "2+",
            "stat_wounds": 5,
            "stat_leadership": "6+",
            "stat_oc": 1,
            "stat_invuln": "4+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Fury of the Tempest",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "4",
                "skill": "2+",
                "strength": "6",
                "ap": "-1",
                "damage": "2",
                "keywords": "Assault, Lethal Hits"
            },
            {
                "name": "The Shining Blade",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "6",
                "skill": "2+",
                "strength": "5",
                "ap": "-2",
                "damage": "2",
                "keywords": "Sustained Hits 1"
            }
        ],
        "abilities": [
            {
                "name": "Leader",
                "description": "This model can be attached to the following unit:\n\u25a0 Swooping Hawks"
            },
            {
                "name": "Cry of the Wind",
                "description": "Each time this model is set-up on the battlefield, until the end of the turn, each time this model makes a ranged attack, a successful unmodified Hit roll scores a Critical Hit."
            },
            {
                "name": "Cloudstrider",
                "description": "While this model is leading a unit, at the end of your opponent\u2019s turn, if that unit is not within Engagement Range of one or more enemy units, you can remove it from the battlefield and place it into Strategic Reserves. In addition, while this model is leading a unit, when that unit is set up on the battlefield using the Deep Strike ability, in your Movement phase, it can use this ability. If it does, that unit can be set up anywhere on the battlefield that is more than 6\" horizontally away from all enemy models, but until the end of the turn, it is not eligible to declare a charge."
            }
        ]
    },
    "Corsair Skyreavers": {
        "stats": {
            "stat_movement": "12\"",
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
                "name": "Corsair Blade",
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
                "name": "Neuro disruptor",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "4",
                "ap": "-2",
                "damage": "1",
                "keywords": "Anti-Infantry 2+, Assault, Pistol"
            },
            {
                "name": "Shuriken pistol",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "4",
                "ap": "-1",
                "damage": "1",
                "keywords": "Assault, Pistol"
            },
            {
                "name": "Blast Pistol",
                "weapon_type": "ranged",
                "range": "6\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "8",
                "ap": "-3",
                "damage": "D3",
                "keywords": "Assault, Pistol"
            },
            {
                "name": "Shuriken Pistol",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "4",
                "ap": "-1",
                "damage": "1",
                "keywords": "Assault, Pistol"
            },
            {
                "name": "Corsair blaster",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "8",
                "ap": "-4",
                "damage": "D6+1",
                "keywords": "Assault"
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
                "name": "Flamer",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "D6",
                "skill": "N/A",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Assault, Ignores Cover, Torrent"
            },
            {
                "name": "Fusion gun",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "8",
                "ap": "-4",
                "damage": "D6",
                "keywords": "Assault, Melta 2"
            },
            {
                "name": "Shredder",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "D6",
                "skill": "N/A",
                "strength": "6",
                "ap": "0",
                "damage": "1",
                "keywords": "Assault, Torrent"
            }
        ],
        "abilities": [
            {
                "name": "Raid and Run",
                "description": "At the end of the Fight phase, if this unit was eligible to fight this phase, and is not within Engagement Range of one or more enemy units, it can make a Normal move of up to D3+3\". Otherwise, if this unit was eligible to fight this phase, this unit can make a Fall Back move of up to D3+3\"."
            }
        ]
    },
    "Corsair Voidreavers": {
        "stats": {
            "stat_movement": "7\"",
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
                "name": "Close Combat Weapon",
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
                "name": "Shuriken cannon",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "3",
                "skill": "3+",
                "strength": "6",
                "ap": "-1",
                "damage": "2",
                "keywords": "Lethal Hits"
            },
            {
                "name": "Wraithcannon",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "14",
                "ap": "-4",
                "damage": "D6+1",
                "keywords": "-"
            },
            {
                "name": "Shuriken rifle",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "4",
                "ap": "-1",
                "damage": "1",
                "keywords": "Assault, Rapid Fire 1"
            },
            {
                "name": "Shuriken Pistol",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "4",
                "ap": "-1",
                "damage": "1",
                "keywords": "Assault, Pistol"
            },
            {
                "name": "Power sword",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "2",
                "skill": "3+",
                "strength": "4",
                "ap": "-2",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "Blaster",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "8",
                "ap": "-4",
                "damage": "D6+1",
                "keywords": "Assault"
            },
            {
                "name": "Corsair shredder",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "D6",
                "skill": "N/A",
                "strength": "6",
                "ap": "0",
                "damage": "1",
                "keywords": "Assault, Torrent"
            },
            {
                "name": "Neuro disruptor",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "4",
                "ap": "-2",
                "damage": "1",
                "keywords": "Anti-Infantry 2+, Assault, Pistol"
            },
            {
                "name": "Shuriken pistol",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "4",
                "ap": "-1",
                "damage": "1",
                "keywords": "Assault, Pistol"
            }
        ],
        "abilities": [
            {
                "name": "Reavers of the Void",
                "description": "Each time a model in this unit makes an attack, re-roll a Hit roll of 1. If the target of that attack is an enemy unit within range of an objective marker, you can re-roll the Hit roll instead."
            },
            {
                "name": "Mistshield",
                "description": "The bearer has a 4+ invulnerable save."
            }
        ]
    },
    "Corsair Voidscarred": {
        "stats": {
            "stat_movement": "7\"",
            "stat_toughness": 3,
            "stat_save": "4+",
            "stat_wounds": 1,
            "stat_leadership": "6+",
            "stat_oc": 1,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Paired Hekatarii blades",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "2+",
                "strength": "3",
                "ap": "-2",
                "damage": "1",
                "keywords": "Twin-Linked"
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
                "name": "Shuriken Pistol",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "4",
                "ap": "-1",
                "damage": "1",
                "keywords": "Assault, Pistol"
            },
            {
                "name": "Power sword",
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
                "name": "Executioner",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "3",
                "skill": "3+",
                "strength": "6",
                "ap": "-2",
                "damage": "D3",
                "keywords": "Anti-Infantry 2+, Psychic"
            },
            {
                "name": "Witch staff",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "2",
                "skill": "2+",
                "strength": "3",
                "ap": "0",
                "damage": "D3",
                "keywords": "Anti-Infantry 2+, Psychic"
            },
            {
                "name": "Shuriken rifle",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "4",
                "ap": "-1",
                "damage": "1",
                "keywords": "Assault, Rapid Fire 1"
            },
            {
                "name": "Fusion pistol",
                "weapon_type": "ranged",
                "range": "6\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "8",
                "ap": "-4",
                "damage": "D6",
                "keywords": "Assault, Melta 2, Pistol"
            },
            {
                "name": "Shuriken cannon",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "3",
                "skill": "3+",
                "strength": "6",
                "ap": "-1",
                "damage": "2",
                "keywords": "Lethal Hits"
            },
            {
                "name": "Wraithcannon",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "14",
                "ap": "-4",
                "damage": "D6+1",
                "keywords": "-"
            },
            {
                "name": "Long rifle",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "4",
                "ap": "-1",
                "damage": "2",
                "keywords": "Heavy, Precision"
            },
            {
                "name": "Corsair shredder",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "D6",
                "skill": "N/A",
                "strength": "6",
                "ap": "0",
                "damage": "1",
                "keywords": "Assault, Torrent"
            },
            {
                "name": "Corsair blaster",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "8",
                "ap": "-4",
                "damage": "D6+1",
                "keywords": "Assault"
            },
            {
                "name": "Neuro disruptor",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "4",
                "ap": "-2",
                "damage": "1",
                "keywords": "Anti-Infantry 2+, Assault, Pistol"
            },
            {
                "name": "Shuriken pistol",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "4",
                "ap": "-1",
                "damage": "1",
                "keywords": "Assault, Pistol"
            }
        ],
        "abilities": [
            {
                "name": "Piratical Raiders",
                "description": "At the start of the battle, select one unit from your opponent\u2019s army. Each time a model in this unit makes an attack that targets that unit, that attack has the [LETHAL HITS] and [PRECISION] abilities."
            },
            {
                "name": "Channeler stones",
                "description": "Once per turn, the first time a saving throw is failed for the bearer\u2019s unit, change the Damage characteristic of that attack to 0."
            },
            {
                "name": "Faolch\u00fa",
                "description": "Ranged weapons equipped by models in the bearer\u2019s unit have the [IGNORES COVER] ability."
            },
            {
                "name": "Mistshield",
                "description": "The bearer has a 4+ invulnerable save."
            }
        ]
    },
    "Crimson Hunter": {
        "stats": {
            "stat_movement": "-",
            "stat_toughness": 8,
            "stat_save": "3+",
            "stat_wounds": 12,
            "stat_leadership": "6+",
            "stat_oc": None,
            "stat_invuln": "5+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Pulse Laser",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "3",
                "skill": "3+",
                "strength": "9",
                "ap": "-2",
                "damage": "D6",
                "keywords": "-"
            },
            {
                "name": "Wraithbone Hull",
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
                "name": "Starcannon",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "2",
                "skill": "3+",
                "strength": "8",
                "ap": "-3",
                "damage": "2",
                "keywords": "-"
            },
            {
                "name": "Bright Lance",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "12",
                "ap": "-3",
                "damage": "D6+2",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Skyhunter",
                "description": "Each time this model makes a ranged attack that targets a unit that can Fly, add 1 to the Hit roll and add 1 to the Wound roll."
            },
            {
                "name": "Damaged: 1-4 Wounds Remaining",
                "description": "While this model has 1-4 wounds remaining, each time this model makes an attack, subtract 1 from the Hit roll."
            }
        ]
    },
    "D-Cannon Platform": {
        "stats": {
            "stat_movement": "7\"",
            "stat_toughness": 6,
            "stat_save": "4+",
            "stat_wounds": 5,
            "stat_leadership": "7+",
            "stat_oc": 1,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "D-cannon",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "D3",
                "skill": "3+",
                "strength": "16",
                "ap": "-4",
                "damage": "D6+2",
                "keywords": "Blast, Devastating Wounds, Indirect Fire"
            },
            {
                "name": "Close Combat Weapon",
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
                "name": "Shuriken Catapult",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "2",
                "skill": "3+",
                "strength": "4",
                "ap": "-1",
                "damage": "1",
                "keywords": "Assault"
            }
        ],
        "abilities": [
            {
                "name": "Structural Collapse",
                "description": "Each time this model makes an attack with its D-Cannon, re-roll a Damage roll of 1. If that attack targets a Titanic unit, you can re-roll the Damage roll instead."
            },
            {
                "name": "Support Artillery",
                "description": "At the start of the Declare Battle Formations step, this model can join one Guardian Defenders unit from your army (a unit cannot have more than one Support Weapon model joined to it). This model then counts as part of that Guardians unit for the rest of the battle, and that unit's Starting Strength is increased accordingly.\n\n\nThis model, and any unit it is joined to, cannot embark within a Transport."
            },
            {
                "name": "Support Weapon",
                "description": "Each time an attack targets this model's unit, it that unit contains one or more other models, until that attack is resolved, this model has a Toughness characteristic of 3."
            }
        ]
    },
    "Dark Reapers": {
        "stats": {
            "stat_movement": "6\"",
            "stat_toughness": 3,
            "stat_save": "3+",
            "stat_wounds": 1,
            "stat_leadership": "6+",
            "stat_oc": 1,
            "stat_invuln": "5+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "\u27a4 Reaper Launcher - Starshot",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "10",
                "ap": "-2",
                "damage": "3",
                "keywords": "Ignores Cover"
            },
            {
                "name": "\u27a4 Reaper Launcher - Starswarm",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "2",
                "skill": "3+",
                "strength": "5",
                "ap": "-2",
                "damage": "1",
                "keywords": "Ignores Cover"
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
            },
            {
                "name": "Shuriken Cannon",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "3",
                "skill": "3+",
                "strength": "6",
                "ap": "-1",
                "damage": "2",
                "keywords": "Ignores Cover, Lethal Hits"
            },
            {
                "name": "Tempest Launcher",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "2D6",
                "skill": "3+",
                "strength": "4",
                "ap": "-1",
                "damage": "1",
                "keywords": "Blast, Indirect Fire"
            },
            {
                "name": "\u27a4 Missile Launcher - Starshot",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "1",
                "skill": "2+",
                "strength": "10",
                "ap": "-2",
                "damage": "D6",
                "keywords": "Ignores Cover"
            },
            {
                "name": "\u27a4 Missile Launcher - Sunburst",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "D6",
                "skill": "2+",
                "strength": "4",
                "ap": "-1",
                "damage": "1",
                "keywords": "Blast, Ignores Cover"
            }
        ],
        "abilities": [
            {
                "name": "Inescapable Accuracy",
                "description": "Each time a model in this unit makes a ranged attack, you can ignore any or all modifiers to that attack\u2019s Ballistic Skill characteristic and any or all modifiers to the Hit roll."
            },
            {
                "name": "Aspect Shrine Token",
                "description": "Once per battle for each Aspect Shrine token this unit has, you can change the result of one Hit roll or one Wound roll made for a model in this unit (excluding CHARACTER models) to an unmodified 6.\n\nDesigner's Note: Place an Aspect Shrine token next to the unit for each Aspect Shrine token it has, removing one each time this ability is used."
            }
        ]
    },
    "Death Jester": {
        "stats": {
            "stat_movement": "8\"",
            "stat_toughness": 3,
            "stat_save": "6+",
            "stat_wounds": 4,
            "stat_leadership": "6+",
            "stat_oc": 1,
            "stat_invuln": "4+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Jester's Blade",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "2+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "Shrieker Cannon",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "3",
                "skill": "2+",
                "strength": "6",
                "ap": "-2",
                "damage": "2",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Death is Not Enough",
                "description": "In your Shooting phase, after this model has shot, select one enemy unit (excluding Monsters and Vehicles) hit by one or more of those attacks. That enemy unit must take a Battle-shock test. If one or more of those attacks destroyed a model in that enemy unit, subtract 1 from that test."
            },
            {
                "name": "Cruel Amusement",
                "description": "In your Shooting phase, each time this model is selected to shoot, select one of the abilities below. Until the end of the phase, this model\u2019s Shrieker Cannon has that ability:\n\u25a0 [IGNORES COVER]\n\u25a0 [PRECISION]\n\u25a0 [SUSTAINED HITS 3]"
            },
            {
                "name": "Flip Belt",
                "description": "Each time the bearer's unit makes a Normal, Advance, Fall Back or Charge move, ignore any vertical distance when determining the total distance the bearer can be moved during that move."
            },
            {
                "name": "Travelling Players",
                "description": "Unless otherwise stated, you cannot include more than one of this model in your army."
            }
        ]
    },
    "Dire Avengers": {
        "stats": {
            "stat_movement": "7\"",
            "stat_toughness": 3,
            "stat_save": "4+",
            "stat_wounds": 1,
            "stat_leadership": "6+",
            "stat_oc": 1,
            "stat_invuln": "5+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Close Combat Weapon",
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
                "name": "Avenger shuriken catapult",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "4",
                "skill": "3+",
                "strength": "4",
                "ap": "-1",
                "damage": "1",
                "keywords": "Assault"
            },
            {
                "name": "Shuriken Pistol",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "4",
                "ap": "-1",
                "damage": "1",
                "keywords": "Assault, Pistol"
            },
            {
                "name": "Diresword",
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
                "name": "Power Glaive",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "3",
                "skill": "3+",
                "strength": "5",
                "ap": "-3",
                "damage": "1",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Bladestorm",
                "description": "Ranged weapons equipped by models in this unit have the [Sustained Hits 1] ability while targeting an enemy unit within half range."
            },
            {
                "name": "Aspect Shrine Token",
                "description": "Once per battle for each Aspect Shrine token this unit has, you can change the result of one Hit roll or one Wound roll made for a model in this unit (excluding CHARACTER models) to an unmodified 6.\n\nDesigner's Note: Place an Aspect Shrine token next to the unit for each Aspect Shrine token it has, removing one each time this ability is used."
            },
            {
                "name": "Shimmershield",
                "description": "The bearer has a 4+ invulnerable save."
            }
        ]
    },
    "Eldrad Ulthran": {
        "stats": {
            "stat_movement": "7\"",
            "stat_toughness": 4,
            "stat_save": "6+",
            "stat_wounds": 5,
            "stat_leadership": "6+",
            "stat_oc": 1,
            "stat_invuln": "4+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Shuriken Pistol",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "1",
                "skill": "2+",
                "strength": "4",
                "ap": "-1",
                "damage": "1",
                "keywords": "Assault, Pistol"
            },
            {
                "name": "Staff of Ulthamar and witchblade",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "3",
                "skill": "2+",
                "strength": "5",
                "ap": "-1",
                "damage": "2",
                "keywords": "Anti-Infantry 2+, Psychic"
            },
            {
                "name": "Mind War",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "1",
                "skill": "2+",
                "strength": "5",
                "ap": "-2",
                "damage": "D6",
                "keywords": "Anti-character 4+, Precision, Psychic"
            }
        ],
        "abilities": [
            {
                "name": "Diviner of the Futures",
                "description": "At the start of your Command phase, if this model is on the battlefield, you gain 1CP."
            },
            {
                "name": "Doom (Psychic)",
                "description": "At the end of your Movement phase, select one enemy unit within 18\" of and visible to this model. Until the start of your next Command phase, each time a friendly Aeldari model makes an attack that targets that enemy unit, add 1 to the Wound roll"
            },
            {
                "name": "Leader",
                "description": "This model can be attached to the following units:\n- GUARDIAN DEFENDERS\n- STORM GUARDIANS\n- WARLOCK CONCLAVE\n\nIf this model is not already attached to a unit, you can attach this model to a unit, even if one WARLOCKS unit has already been attached to it."
            }
        ]
    },
    "Falcon": {
        "stats": {
            "stat_movement": "14\"",
            "stat_toughness": 9,
            "stat_save": "3+",
            "stat_wounds": 12,
            "stat_leadership": "7+",
            "stat_oc": 3,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Pulse Laser",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "3",
                "skill": "3+",
                "strength": "9",
                "ap": "-2",
                "damage": "D6",
                "keywords": "-"
            },
            {
                "name": "Wraithbone hull",
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
                "name": "Twin Shuriken Catapult",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "2",
                "skill": "3+",
                "strength": "4",
                "ap": "-1",
                "damage": "1",
                "keywords": "Assault, Twin Linked"
            },
            {
                "name": "Shuriken Cannon",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "3",
                "skill": "3+",
                "strength": "6",
                "ap": "-1",
                "damage": "2",
                "keywords": "Lethal Hits"
            }
        ],
        "abilities": [
            {
                "name": "Damaged: 1-4 Wounds Remaining",
                "description": "While this model has 1-4 wounds remaining, each time this model makes an attack, subtract 1 from the Hit roll."
            },
            {
                "name": "Fire Support",
                "description": "In your Shooting phase, after this model has shot, select one enemy unit hit by one or more of those attacks. Until the end of the turn, each time a friendly model that disembarked from this Transport this turn makes an attack that targets that enemy unit, you can re-roll the Wound roll"
            }
        ]
    },
    "Farseer": {
        "stats": {
            "stat_movement": "7\"",
            "stat_toughness": 3,
            "stat_save": "6+",
            "stat_wounds": 4,
            "stat_leadership": "6+",
            "stat_oc": 1,
            "stat_invuln": "4+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Eldritch Storm",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "D6",
                "skill": "3+",
                "strength": "6",
                "ap": "-2",
                "damage": "D3",
                "keywords": "Blast, Psychic"
            },
            {
                "name": "Shuriken Pistol",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "4",
                "ap": "-1",
                "damage": "1",
                "keywords": "Assault, Pistol"
            },
            {
                "name": "Witchblade",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "2",
                "skill": "2+",
                "strength": "3",
                "ap": "0",
                "damage": "2",
                "keywords": "Anti-Infantry 2+, Psychic"
            },
            {
                "name": "Singing Spear",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "1",
                "skill": "2+",
                "strength": "9",
                "ap": "0",
                "damage": "3",
                "keywords": "Assault, Psychic"
            },
            {
                "name": "Singing Spear",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "2",
                "skill": "2+",
                "strength": "3",
                "ap": "0",
                "damage": "3",
                "keywords": "Psychic"
            }
        ],
        "abilities": [
            {
                "name": "Branching Fates (Psychic)",
                "description": "While this model is leading a unit, once per phase you can change the result of one Hit roll, one Wound roll, or one Damage roll made for a model in that unit (excluding Support Weapon models) to an unmodified 6."
            },
            {
                "name": "Guide (Psychic)",
                "description": "At the end of your Movement phase, select one enemy unit within 18\" of and visible to this model. Until the start of your next Command phase, each time a friendly Aeldari model makes an attack that targets that enemy unit, add 1 to the Hit roll. Each unit can only be selected for this ability once per turn."
            },
            {
                "name": "Leader",
                "description": "This model can be attached to the following units: GUARDIAN DEFENDERS, STORM GUARDIANS, WARLOCK CONCLAVE."
            }
        ]
    },
    "Farseer Skyrunner": {
        "stats": {
            "stat_movement": "14\"",
            "stat_toughness": 4,
            "stat_save": "6+",
            "stat_wounds": 5,
            "stat_leadership": "6+",
            "stat_oc": 2,
            "stat_invuln": "4+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Eldritch Storm",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "D6",
                "skill": "3+",
                "strength": "6",
                "ap": "-2",
                "damage": "D3",
                "keywords": "Blast, Psychic"
            },
            {
                "name": "Shuriken Pistol",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "4",
                "ap": "-1",
                "damage": "1",
                "keywords": "Assault, Pistol"
            },
            {
                "name": "Twin Shuriken Catapult",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "2",
                "skill": "3+",
                "strength": "4",
                "ap": "-1",
                "damage": "1",
                "keywords": "Assault, Twin Linked"
            },
            {
                "name": "Witchblade",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "2",
                "skill": "2+",
                "strength": "3",
                "ap": "0",
                "damage": "2",
                "keywords": "Anti-Infantry 2+, Psychic"
            },
            {
                "name": "Singing Spear",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "9",
                "ap": "0",
                "damage": "3",
                "keywords": "Assault, Psychic"
            },
            {
                "name": "Singing Spear",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "2",
                "skill": "2+",
                "strength": "3",
                "ap": "0",
                "damage": "3",
                "keywords": "Psychic"
            }
        ],
        "abilities": [
            {
                "name": "Branching Fates (Psychic)",
                "description": "While this model is leading a unit, once per phase you can change the result of one Hit roll, one Wound roll, or one Damage roll made for a model in that unit to an unmodified 6."
            },
            {
                "name": "Misfortune (Psychic)",
                "description": "At the end of your Movement phase, select one enemy unit within 18\" of and visible to this model. Until the start of your next Command phase, each time a model in that unit makes an attack, subtract 1 from the Wound roll. Each unit can only be selected for this ability once per turn."
            },
            {
                "name": "Leader",
                "description": "This model can be attached to the following units:\n\u25a0 Warlock Skyrunners\n\u25a0 Windriders"
            }
        ]
    },
    "Fire Dragons": {
        "stats": {
            "stat_movement": "7\"",
            "stat_toughness": 3,
            "stat_save": "3+",
            "stat_wounds": 1,
            "stat_leadership": "6+",
            "stat_oc": 1,
            "stat_invuln": "5+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Dragon Fusion Gun",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "9",
                "ap": "-4",
                "damage": "D6",
                "keywords": "Assault, Melta 3"
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
            },
            {
                "name": "Exarch's Dragon Fusion Gun",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "9",
                "ap": "-4",
                "damage": "D6",
                "keywords": "Assault, Melta 6"
            },
            {
                "name": "Dragon's Breath Flamer",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "D6+2",
                "skill": "N/A",
                "strength": "6",
                "ap": "-2",
                "damage": "1",
                "keywords": "Assault, Ignores cover, Torrent"
            },
            {
                "name": "Firepike",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "12",
                "ap": "-4",
                "damage": "D6",
                "keywords": "Assault, Melta 3"
            },
            {
                "name": "Dragon Axe",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "3",
                "skill": "3+",
                "strength": "6",
                "ap": "-4",
                "damage": "D6",
                "keywords": "-"
            },
            {
                "name": "Dragon Fusion Pistol",
                "weapon_type": "ranged",
                "range": "6\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "9",
                "ap": "-4",
                "damage": "D6",
                "keywords": "Assault, Melta 3, Pistol"
            }
        ],
        "abilities": [
            {
                "name": "Assured Destruction",
                "description": "In your Shooting phase, each time a model in this unit makes a ranged attack that targets a Monster or Vehicle unit, you can re-roll the Hit roll, you can re-roll the Wound roll and you can re-roll the Damage roll."
            },
            {
                "name": "Aspect Shrine Token",
                "description": "Once per battle for each Aspect Shrine token this unit has, you can change the result of one Hit roll or one Wound roll made for a model in this unit (excluding CHARACTER models) to an unmodified 6.\n\nDesigner's Note: Place an Aspect Shrine token next to the unit for each Aspect Shrine token it has, removing one each time this ability is used."
            }
        ]
    },
    "Fire Prism": {
        "stats": {
            "stat_movement": "14\"",
            "stat_toughness": 9,
            "stat_save": "3+",
            "stat_wounds": 12,
            "stat_leadership": "7+",
            "stat_oc": 3,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "\u27a4 Prism Cannon - dispersed pulse",
                "weapon_type": "ranged",
                "range": "60\"",
                "attacks": "2D6",
                "skill": "3+",
                "strength": "6",
                "ap": "-2",
                "damage": "2",
                "keywords": "Blast"
            },
            {
                "name": "\u27a4 Prism Cannon - focused lances",
                "weapon_type": "ranged",
                "range": "60\"",
                "attacks": "2",
                "skill": "3+",
                "strength": "18",
                "ap": "-4",
                "damage": "6",
                "keywords": "Linked Fire"
            },
            {
                "name": "Wraithbone Hull",
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
                "name": "Twin Shuriken Catapult",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "2",
                "skill": "3+",
                "strength": "4",
                "ap": "-1",
                "damage": "1",
                "keywords": "Assault, Twin Linked"
            },
            {
                "name": "Shuriken Cannon",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "3",
                "skill": "3+",
                "strength": "6",
                "ap": "-1",
                "damage": "2",
                "keywords": "Lethal Hits"
            }
        ],
        "abilities": [
            {
                "name": "Damaged: 1-4 Wounds Remaining",
                "description": "While this model has 1-4 wounds remaining, each time this model makes an attack, subtract 1 from the Hit roll."
            },
            {
                "name": "Crystal Matrix",
                "description": "Each time this model is selected to shoot, you can re-roll one Hit roll and you can re-roll one Wound roll when resolving those attacks."
            }
        ]
    },
    "Fuegan": {
        "stats": {
            "stat_movement": "7\"",
            "stat_toughness": 3,
            "stat_save": "2+",
            "stat_wounds": 5,
            "stat_leadership": "6+",
            "stat_oc": 1,
            "stat_invuln": "4+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "\u27a4 Searsong - Beam",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "3",
                "skill": "2+",
                "strength": "8",
                "ap": "-3",
                "damage": "2",
                "keywords": "Assault, Melta 1, Sustained hits 2"
            },
            {
                "name": "\u27a4 Searsong - Lance",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "1",
                "skill": "2+",
                "strength": "14",
                "ap": "-4",
                "damage": "D6",
                "keywords": "Assault, Melta 6"
            },
            {
                "name": "The Fire Axe",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "6",
                "skill": "2+",
                "strength": "5",
                "ap": "-4",
                "damage": "3",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Burning Lance",
                "description": "While this model is leading a unit, add 6\" to the Range characteristic of Melta weapons equipped by models in that unit."
            },
            {
                "name": "Unquenchable Resolve",
                "description": "The first time this model is destroyed, at the end of the phase, roll one D6. On a 2+, set this model back up on the battlefield as close as possible to where it was destroyed and not within Engagement Range of one or more enemy units, with its full wounds remaining."
            },
            {
                "name": "Leader",
                "description": "This model can be attached to the following unit:\n\u25a0 Fire Dragons"
            }
        ]
    },
    "Guardian Defenders": {
        "stats": {
            "stat_movement": "7\"",
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
                "name": "Close Combat Weapon",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "1",
                "skill": "3+",
                "strength": "3",
                "ap": "0",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "Shuriken Catapult",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "2",
                "skill": "3+",
                "strength": "4",
                "ap": "-1",
                "damage": "1",
                "keywords": "Assault"
            }
        ],
        "abilities": [
            {
                "name": "Fleet of Foot",
                "description": "This unit can perform the Fade Back Agile Manoeuvre without spending a Battle Focus token to do so. It can do so even if other units have done so in the same phase, and doing so does not prevent other units from performing the same Agile Manoeuvre in the same phase."
            },
            {
                "name": "Crewed Platform",
                "description": "When the last Guardian Defender model in this unit is destroyed, any remaining Heavy Weapon Platform models in this unit are also destroyed."
            }
        ]
    },
    "Hemlock Wraithfighter": {
        "stats": {
            "stat_movement": "-",
            "stat_toughness": 8,
            "stat_save": "3+",
            "stat_wounds": 12,
            "stat_leadership": "6+",
            "stat_oc": None,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Wraithbone Hull",
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
                "name": "Heavy D-Scythe",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "D6",
                "skill": "4+",
                "strength": "12",
                "ap": "-4",
                "damage": "2",
                "keywords": "Blast"
            }
        ],
        "abilities": [
            {
                "name": "Mindshock Pod (Aura, Psychic)",
                "description": "While an enemy unit is within 9\" of this model, subtract 1 from Battle-shock and Leadership tests taken for that unit."
            },
            {
                "name": "Damaged: 1-4 Wounds Remaining",
                "description": "While this model has 1-4 wounds remaining, each time this model makes an attack, subtract 1 from the Hit roll."
            }
        ]
    },
    "Howling Banshees": {
        "stats": {
            "stat_movement": "8\"",
            "stat_toughness": 3,
            "stat_save": "4+",
            "stat_wounds": 1,
            "stat_leadership": "6+",
            "stat_oc": 1,
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Banshee Blade",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "2",
                "skill": "2+",
                "strength": "4",
                "ap": "-2",
                "damage": "2",
                "keywords": "Anti-Infantry 3+"
            },
            {
                "name": "Shuriken Pistol",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "4",
                "ap": "-1",
                "damage": "1",
                "keywords": "Assault, Pistol"
            },
            {
                "name": "Executioner",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "3",
                "skill": "2+",
                "strength": "6",
                "ap": "-3",
                "damage": "3",
                "keywords": "Anti-Infantry 3+"
            },
            {
                "name": "Triskele",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "6",
                "skill": "2+",
                "strength": "3",
                "ap": "-1",
                "damage": "1",
                "keywords": "Anti-Infantry 3+"
            },
            {
                "name": "Triskele",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "3",
                "skill": "3+",
                "strength": "3",
                "ap": "-1",
                "damage": "1",
                "keywords": "Assault, Anti-Infantry 3+"
            },
            {
                "name": "Mirrorswords",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "2+",
                "strength": "4",
                "ap": "-2",
                "damage": "2",
                "keywords": "Anti-Infantry 3+"
            }
        ],
        "abilities": [
            {
                "name": "Acrobatic",
                "description": "This unit is eligible to declare a charge in a turn in which it Advanced or Fell Back"
            },
            {
                "name": "Aspect Shrine Token",
                "description": "Once per battle for each Aspect Shrine token this unit has, you can change the result of one Hit roll or one Wound roll made for a model in this unit (excluding CHARACTER models) to an unmodified 6.\n\nDesigner's Note: Place an Aspect Shrine token next to the unit for each Aspect Shrine token it has, removing one each time this ability is used."
            }
        ]
    },
    "Jain Zar": {
        "stats": {
            "stat_movement": "8\"",
            "stat_toughness": 3,
            "stat_save": "2+",
            "stat_wounds": 5,
            "stat_leadership": "6+",
            "stat_oc": 1,
            "stat_invuln": "4+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Silent Death",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "6",
                "skill": "2+",
                "strength": "6",
                "ap": "-2",
                "damage": "1",
                "keywords": "Assault"
            },
            {
                "name": "Blade of Destruction",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "8",
                "skill": "2+",
                "strength": "6",
                "ap": "-3",
                "damage": "2",
                "keywords": "Anti-Infantry 3+"
            }
        ],
        "abilities": [
            {
                "name": "Leader",
                "description": "This model can be attached to the following unit:\n\u25a0 Howling Banshees"
            },
            {
                "name": "Whirling Death",
                "description": "While this model is leading a unit, each time that unit Advances, do not make an Advance roll. Instead, until the end of the phase, add 6\" to the Move characteristic of models in that unit and each time a model in that unit makes an Advance move, ignore any vertical distance when determining the total distance that model can be moved during that move."
            },
            {
                "name": "Storm of Silence",
                "description": "Each time this model makes an attack that targets a Character unit, you can re-roll the Wound roll."
            }
        ]
    },
    "Kharseth": {
        "stats": {
            "stat_movement": "7\"",
            "stat_toughness": 3,
            "stat_save": "6+",
            "stat_wounds": 4,
            "stat_leadership": "6+",
            "stat_oc": 1,
            "stat_invuln": "4+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Dread of the Deep Void",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "D6+2",
                "skill": "3+",
                "strength": "3",
                "ap": "-2",
                "damage": "1",
                "keywords": "Anti-Infantry 2+, Blast, Hazardous, Ignores Cover, Psychic"
            },
            {
                "name": "Waystave",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "3",
                "skill": "2+",
                "strength": "3",
                "ap": "0",
                "damage": "3",
                "keywords": "Anti-Infantry 2+, Psychic"
            }
        ],
        "abilities": [
            {
                "name": "Leader",
                "description": "This model can be attached to the following units:\n- CORSAIR REAVER BAND\n- CORSAIR VOIDREAVERS\n- CORSAIR VOIDSCARRED"
            },
            {
                "name": "Aethersense (Psychic)",
                "description": "Enemy units that are set up on the battlefield from Reserves cannot be set up within 12\" of this model."
            },
            {
                "name": "Fury of the Void (Psychic)",
                "description": "In your Shooting phase, after this model\u2019s unit has shot, select one enemy unit hit by one or more attacks made with this model\u2019s Dread of the Deep Void. Until the end of the turn, that unit is riven. Each time an Aeldari model from your army makes an attack that targets a riven unit, add 1 to the Strength characteristic of that attack."
            }
        ]
    },
    "Lhykhis": {
        "stats": {
            "stat_movement": "12\"",
            "stat_toughness": 3,
            "stat_save": "2+",
            "stat_wounds": 5,
            "stat_leadership": "6+",
            "stat_oc": 1,
            "stat_invuln": "4+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Brood Twain",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "D6+3",
                "skill": "N/A",
                "strength": "6",
                "ap": "-2",
                "damage": "1",
                "keywords": "Ignores Cover, Torrent, Twin-Linked"
            },
            {
                "name": "Spider's Fangs",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "5",
                "skill": "2+",
                "strength": "4",
                "ap": "-2",
                "damage": "1",
                "keywords": "Extra Attacks, Lethal Hits"
            },
            {
                "name": "Weaverender",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "5",
                "skill": "2+",
                "strength": "6",
                "ap": "-2",
                "damage": "2",
                "keywords": "Lethal Hits"
            }
        ],
        "abilities": [
            {
                "name": "Leader",
                "description": "This model can be attached to the following unit:\n\u25a0 Warp Spiders"
            },
            {
                "name": "Empyric Ambush",
                "description": "While this model is leading a unit, that unit is eligible to declare a charge in a turn in which it used its Flickerjump ability."
            },
            {
                "name": "Whispering Web",
                "description": "In your Shooting phase, after this model has shot, select one enemy unit hit by one or more of those attacks. Until the end of the turn, each time a friendly Aeldari model makes an attack that targets that unit, an unmodified Hit roll of 5+ scores a Critical Hit."
            }
        ]
    },
    "Maugan Ra": {
        "stats": {
            "stat_movement": "7\"",
            "stat_toughness": 3,
            "stat_save": "2+",
            "stat_wounds": 5,
            "stat_leadership": "6+",
            "stat_oc": 1,
            "stat_invuln": "4+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Maugetar",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "6",
                "skill": "2+",
                "strength": "7",
                "ap": "-2",
                "damage": "2",
                "keywords": "Devastating wounds, Ignores cover"
            },
            {
                "name": "Maugetar",
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
                "name": "Leader",
                "description": "This model can be attached to the following unit:\n\u25a0 Dark Reapers"
            },
            {
                "name": "Harvester of Souls",
                "description": "While this model is leading a unit, in your Shooting phase, after selecting targets for that unit's attacks, if every attack targets the same unit, roll one D6 for the target unit and one D6 for every other enemy unit within 3\" of the target unit. On a 5+, the unit being rolled for is struck by explosive debris; after resolving all of that unit's attacks against the target unit, each unit struck by explosive debris suffers D3 mortal wounds."
            },
            {
                "name": "Face of Death",
                "description": "In your Shooting phase, after this model has shot, select one enemy unit hit by one or more of those attacks. That enemy unit must take a Battle-shock test, subtracting 1 from the result."
            }
        ]
    },
    "Night Spinner": {
        "stats": {
            "stat_movement": "14\"",
            "stat_toughness": 9,
            "stat_save": "3+",
            "stat_wounds": 12,
            "stat_leadership": "7+",
            "stat_oc": 3,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Doomweaver",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "D6+3",
                "skill": "3+",
                "strength": "7",
                "ap": "-1",
                "damage": "2",
                "keywords": "Blast, Indirect Fire, Twin Linked"
            },
            {
                "name": "Wraithbone Hull",
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
                "name": "Twin Shuriken Catapult",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "2",
                "skill": "3+",
                "strength": "4",
                "ap": "-1",
                "damage": "1",
                "keywords": "Assault, Twin Linked"
            },
            {
                "name": "Shuriken Cannon",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "3",
                "skill": "3+",
                "strength": "6",
                "ap": "-1",
                "damage": "2",
                "keywords": "Lethal Hits"
            }
        ],
        "abilities": [
            {
                "name": "Damaged: 1-4 Wounds Remaining",
                "description": "While this model has 1-4 wounds remaining, each time this model makes an attack, subtract 1 from the Hit roll."
            },
            {
                "name": "Monofilament Web",
                "description": "In your Shooting phase, after this model has shot, if one or more of those attacks made with its doomweaver scored a hit against an enemy unit, until the start of your next turn, that enemy unit is pinned. While a unit is pinned, subtract 2 from that unit's Move characteristic and subtract 2 from Charge rolls made for it."
            }
        ]
    },
    "Prince Yriel": {
        "stats": {
            "stat_movement": "7\"",
            "stat_toughness": 3,
            "stat_save": "3+",
            "stat_wounds": 5,
            "stat_leadership": "6+",
            "stat_oc": 1,
            "stat_invuln": "4+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "The Eye of Wrath",
                "weapon_type": "ranged",
                "range": "6\"",
                "attacks": "3",
                "skill": "2+",
                "strength": "6",
                "ap": "-2",
                "damage": "2",
                "keywords": "Assault, Pistol"
            },
            {
                "name": "The Spear of Twilight",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "5",
                "skill": "2+",
                "strength": "7",
                "ap": "-3",
                "damage": "3",
                "keywords": "Lance"
            },
            {
                "name": "Shuriken Pistol",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "1",
                "skill": "2+",
                "strength": "4",
                "ap": "-1",
                "damage": "1",
                "keywords": "Assault, Pistol"
            }
        ],
        "abilities": [
            {
                "name": "Leader",
                "description": "This model can be attached to the following units:\n- CORSAIR REAVER BAND\n- CORSAIR VOIDREAVERS\n- CORSAIR VOIDSCARRED"
            },
            {
                "name": "Piratical Hero",
                "description": "While this model is leading a unit, each time a model in that unit makes an attack, that attack has the [Sustained Hits 1] ability and add 1 to the Hit roll."
            },
            {
                "name": "Prince of Corsairs",
                "description": "After both players have deployed their armies, if this model is on the battlefield (or any Transport it is embarked within is on the battlefield), select up to three Aeldari units from your army and redeploy them. When doing so, you can set those units up in Strategic Reserves, regardless of how many units are already in Strategic Reserves."
            }
        ]
    },
    "Rangers": {
        "stats": {
            "stat_movement": "7\"",
            "stat_toughness": 3,
            "stat_save": "5+",
            "stat_wounds": 1,
            "stat_leadership": "7+",
            "stat_oc": 1,
            "stat_invuln": "5+*",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Long rifle",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "4",
                "ap": "-1",
                "damage": "2",
                "keywords": "Heavy, Precision"
            },
            {
                "name": "Close Combat Weapon",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "1",
                "skill": "3+",
                "strength": "3",
                "ap": "0",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "Shuriken Pistol",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "1",
                "skill": "2+",
                "strength": "4",
                "ap": "-1",
                "damage": "1",
                "keywords": "Assault, Pistol"
            }
        ],
        "abilities": [
            {
                "name": "Path of the Outcast",
                "description": "In your opponent's Movement phase, if an enemy unit ends a move within 8\" of this unit, if this unit is not within Engagement Range of one or more enemy units, this unit can make a Normal move of up to D6\"."
            }
        ]
    },
    "Shadow Weaver Platform": {
        "stats": {
            "stat_movement": "7\"",
            "stat_toughness": 6,
            "stat_save": "4+",
            "stat_wounds": 5,
            "stat_leadership": "7+",
            "stat_oc": 1,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Shadow weaver",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "D6+2",
                "skill": "3+",
                "strength": "6",
                "ap": "-1",
                "damage": "1",
                "keywords": "Blast, Indirect Fire"
            },
            {
                "name": "Close Combat Weapon",
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
                "name": "Shuriken Catapult",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "2",
                "skill": "3+",
                "strength": "4",
                "ap": "-1",
                "damage": "1",
                "keywords": "Assault"
            }
        ],
        "abilities": [
            {
                "name": "Monofilament Snare",
                "description": "In your Shooting phase, after this model has shot, select one enemy unit hit by one or more of those attacks made with its Shadow Weaver. Until the start of your next turn, that enemy unit it snared. While a unit is snared, each time that unit makes a Normal, Advance or Fall Back move, roll one D6 for each model in that unit: for each 1, that unit suffers 1 mortal wound."
            },
            {
                "name": "Support Artillery",
                "description": "At the start of the Declare Battle Formations step, this model can join one Guardian Defenders unit from your army (a unit cannot have more than one Support Weapon model joined to it). This model then counts as part of that Guardians unit for the rest of the battle, and that unit's Starting Strength is increased accordingly.\n\n\nThis model, and any unit it is joined to, cannot embark within a Transport."
            },
            {
                "name": "Support Weapon",
                "description": "Each time an attack targets this model's unit, it that unit contains one or more other models, until that attack is resolved, this model has a Toughness characteristic of 3."
            }
        ]
    },
    "Shadowseer": {
        "stats": {
            "stat_movement": "8\"",
            "stat_toughness": 3,
            "stat_save": "6+",
            "stat_wounds": 4,
            "stat_leadership": "6+",
            "stat_oc": 1,
            "stat_invuln": "4+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Miststave",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "2+",
                "strength": "5",
                "ap": "-1",
                "damage": "D3",
                "keywords": "Psychic"
            },
            {
                "name": "Shuriken Pistol",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "1",
                "skill": "2+",
                "strength": "4",
                "ap": "-1",
                "damage": "1",
                "keywords": "Assault, Pistol"
            },
            {
                "name": "Neuro Disruptor",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "1",
                "skill": "2+",
                "strength": "4",
                "ap": "-2",
                "damage": "1",
                "keywords": "Anti-infantry 2+, Assault, Pistol"
            }
        ],
        "abilities": [
            {
                "name": "Leader",
                "description": "This model can be attached to the following unit:\n\u25a0 Troupe"
            },
            {
                "name": "Fog of Dreams (Psychic)",
                "description": "While this model is leading a unit, that unit can only be selected as the target of a ranged attack if the attacking model is within 18\"."
            },
            {
                "name": "Treacherous Illusion (Psychic)",
                "description": "Melee weapons equipped by enemy models have the [Hazardous] ability while targeting this model's unit."
            },
            {
                "name": "Travelling Players",
                "description": "Unless otherwise stated, you cannot include more than one of this model in your army."
            },
            {
                "name": "Flip Belt",
                "description": "Each time the bearer's unit makes a Normal, Advance, Fall Back or Charge move, ignore any vertical distance when determining the total distance the bearer can be moved during that move."
            }
        ]
    },
    "Shining Spears": {
        "stats": {
            "stat_movement": "14\"",
            "stat_toughness": 4,
            "stat_save": "3+",
            "stat_wounds": 2,
            "stat_leadership": "6+",
            "stat_oc": 2,
            "stat_invuln": "5+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Twin Shuriken Catapult",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "2",
                "skill": "3+",
                "strength": "4",
                "ap": "-1",
                "damage": "1",
                "keywords": "Assault, Twin Linked"
            },
            {
                "name": "Laser Lance",
                "weapon_type": "ranged",
                "range": "6\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "6",
                "ap": "-2",
                "damage": "3",
                "keywords": "Assault"
            },
            {
                "name": "Laser Lance",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "3",
                "skill": "3+",
                "strength": "5",
                "ap": "-2",
                "damage": "3",
                "keywords": "Anti-Monster 3+, Anti-Vehicle 3+, Lance"
            },
            {
                "name": "Paragon Sabre",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "6",
                "skill": "3+",
                "strength": "5",
                "ap": "-2",
                "damage": "2",
                "keywords": "-"
            },
            {
                "name": "Star Lance",
                "weapon_type": "ranged",
                "range": "6\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "9",
                "ap": "-3",
                "damage": "3",
                "keywords": "Assault"
            },
            {
                "name": "Star Lance",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "3+",
                "strength": "5",
                "ap": "-3",
                "damage": "3",
                "keywords": "Anti-Monster 3+, Anti-Vehicle 3+, Lance"
            },
            {
                "name": "Shuriken Cannon",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "3",
                "skill": "3+",
                "strength": "6",
                "ap": "-1",
                "damage": "2",
                "keywords": "Lethal Hits"
            }
        ],
        "abilities": [
            {
                "name": "Extreme Mobility",
                "description": "Each time this unit makes a Normal, Advance, Fall Back or Charge move, ignore any vertical distance when determining the total distance models in this unit can be moved during that move."
            },
            {
                "name": "Shimmershield",
                "description": "The bearer has a 4+ invulnerable save."
            }
        ]
    },
    "Shroud Runners": {
        "stats": {
            "stat_movement": "14\"",
            "stat_toughness": 4,
            "stat_save": "5+",
            "stat_wounds": 3,
            "stat_leadership": "7+",
            "stat_oc": 2,
            "stat_invuln": "5+*",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Long rifle",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "1",
                "skill": "2+",
                "strength": "4",
                "ap": "-1",
                "damage": "2",
                "keywords": "Precision"
            },
            {
                "name": "Scatter Laser",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "6",
                "skill": "3+",
                "strength": "5",
                "ap": "0",
                "damage": "1",
                "keywords": "Sustained Hits 1"
            },
            {
                "name": "Close Combat Weapon",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "1",
                "skill": "3+",
                "strength": "3",
                "ap": "0",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "Shuriken Pistol",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "1",
                "skill": "2+",
                "strength": "4",
                "ap": "-1",
                "damage": "1",
                "keywords": "Assault, Pistol"
            }
        ],
        "abilities": [
            {
                "name": "Target Acquisition",
                "description": "In your Shooting phase, after this unit has shot, select one enemy unit hit by one or more of those attacks made with a long rifle. Until the end of the phase, that enemy unit cannot have the Benefit of Cover."
            }
        ]
    },
    "Skyweavers": {
        "stats": {
            "stat_movement": "14\"",
            "stat_toughness": 4,
            "stat_save": "4+",
            "stat_wounds": 3,
            "stat_leadership": "6+",
            "stat_oc": 2,
            "stat_invuln": "4+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Close Combat Weapon",
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
                "name": "Skyweaver Haywire Cannon",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "2",
                "skill": "3+",
                "strength": "3",
                "ap": "-1",
                "damage": "3",
                "keywords": "Anti-Vehicle 4+, Devastating Wounds"
            },
            {
                "name": "Shuriken Cannon",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "3",
                "skill": "3+",
                "strength": "6",
                "ap": "-1",
                "damage": "2",
                "keywords": "Lethal Hits"
            },
            {
                "name": "Star Bolas",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "D3",
                "skill": "3+",
                "strength": "7",
                "ap": "-2",
                "damage": "2",
                "keywords": "-"
            },
            {
                "name": "Zephyrglaive",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "3+",
                "strength": "6",
                "ap": "-2",
                "damage": "2",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Acrobatic Grace",
                "description": "- This unit has Stealth.\n- Melee attacks that target this unit have -1 to hit rolls."
            }
        ]
    },
    "Solitaire": {
        "stats": {
            "stat_movement": "12\"",
            "stat_toughness": 3,
            "stat_save": "6+",
            "stat_wounds": 4,
            "stat_leadership": "6+",
            "stat_oc": 1,
            "stat_invuln": "4+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Solitaire Weapons",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "9",
                "skill": "2+",
                "strength": "6",
                "ap": "-2",
                "damage": "2",
                "keywords": "Precision"
            }
        ],
        "abilities": [
            {
                "name": "Blitz",
                "description": "Once per battle, in your Movement phase, before this model makes a Normal move it can use this ability. If it does, until the end of\nthe turn, add 2D6\" to this model\u2019s Move characteristic and add 3 to the\nAttacks characteristic of this model\u2019s Solitaire weapons."
            },
            {
                "name": "Blur of Movement",
                "description": "This model is eligible to declare a charge in a turn in which it Advanced."
            },
            {
                "name": "Flip Belt",
                "description": "Each time the bearer's unit makes a Normal, Advance, Fall Back or Charge move, ignore any vertical distance when determining the total distance the bearer can be moved during that move."
            }
        ]
    },
    "Spiritseer": {
        "stats": {
            "stat_movement": "7\"",
            "stat_toughness": 3,
            "stat_save": "6+",
            "stat_wounds": 3,
            "stat_leadership": "6+",
            "stat_oc": 1,
            "stat_invuln": "4+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Witch Staff",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "2",
                "skill": "2+",
                "strength": "3",
                "ap": "0",
                "damage": "D3",
                "keywords": "Anti-infantry 2+, Psychic"
            },
            {
                "name": "Shuriken Pistol",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "1",
                "skill": "2+",
                "strength": "4",
                "ap": "-1",
                "damage": "1",
                "keywords": "Assault, Pistol"
            }
        ],
        "abilities": [
            {
                "name": "Spirit Mark (Psychic)",
                "description": "Once per turn, in your Movement phase, when this model starts or ends a move, select one friendly Wraith Construct unit within 6\" of this model (excluding Titanic units) and one enemy unit visible to this model. Until the start of your next Movement phase, weapons equipped by models in that friendly unit have the [Sustained Hits 1] ability while targeting that enemy unit."
            },
            {
                "name": "Tears of Isha (Psychic)",
                "description": "In your Command phase, select one friendly Wraith Construct unit within 6\" of this model. If one or more models in that unit are destroyed, you can return one destroyed model to that unit. Otherwise, one model in that unit regains up to D3 lost wounds. Each unit can only be selected for this ability once per turn."
            },
            {
                "name": "Spiritseer",
                "description": "While this model is within 3\" of one or more friendly Wraith Construct units, this model has the Lone Operative ability."
            }
        ]
    },
    "Starfangs": {
        "stats": {
            "stat_movement": "14\"",
            "stat_toughness": 6,
            "stat_save": "3+",
            "stat_wounds": 6,
            "stat_leadership": "7+",
            "stat_oc": 2,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Wraithbone Hull",
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
                "name": "Disintegrator Cannon",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "3",
                "skill": "3+",
                "strength": "6",
                "ap": "-3",
                "damage": "2",
                "keywords": "Assault"
            },
            {
                "name": "Starfang Grenade Launcher",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "D3",
                "skill": "3+",
                "strength": "6",
                "ap": "-3",
                "damage": "2",
                "keywords": "Assault, Blast"
            }
        ],
        "abilities": [
            {
                "name": "Hallucinogen Grenades",
                "description": "At the start of your opponent\u2019s Shooting phase, this unit can use this ability. If it does, select one Aeldari Infantry unit from your army visible to and within 36\" of this unit: until the end of the phase, that unit has the Stealth ability."
            }
        ]
    },
    "Starweaver": {
        "stats": {
            "stat_movement": "14\"",
            "stat_toughness": 6,
            "stat_save": "4+",
            "stat_wounds": 6,
            "stat_leadership": "6+",
            "stat_oc": 2,
            "stat_invuln": "4+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Close Combat Weapon",
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
                "name": "Shuriken Cannon",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "3",
                "skill": "3+",
                "strength": "6",
                "ap": "-1",
                "damage": "2",
                "keywords": "Lethal Hits"
            }
        ],
        "abilities": [
            {
                "name": "Rapid Embarkation",
                "description": "At the end of the Fight phase, if there are no models currently embarked within this Transport, you can select one friendly Harlequins Infantry unit that has 6 or fewer models that is wholly within 6\" of this Transport. Unless that unit is within Engagement Range of one or more enemy units, it can embark within this Transport. That unit can embark within this TRANSPORT in a turn it disembarked from this TRANSPORT."
            }
        ]
    },
    "Storm Guardians": {
        "stats": {
            "stat_movement": "7\"",
            "stat_toughness": 3,
            "stat_save": "4+",
            "stat_wounds": 2,
            "stat_leadership": "7+",
            "stat_oc": 0,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Close Combat Weapon",
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
                "name": "Shuriken Pistol",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "4",
                "ap": "-1",
                "damage": "1",
                "keywords": "Assault, Pistol"
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
                "keywords": "Assault, Ignores Cover, Torrent"
            },
            {
                "name": "Fusion gun",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "8",
                "ap": "-4",
                "damage": "D6",
                "keywords": "Assault, Melta 2"
            },
            {
                "name": "Power sword",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "2",
                "skill": "3+",
                "strength": "4",
                "ap": "-2",
                "damage": "1",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Stormblades",
                "description": "At the end of your Command phase, if this unit is within range of an objective marker you control, that objective marker remains under your control until your opponent's Level of Control over that objective marker is greater than yours at the end of a phase."
            },
            {
                "name": "Crewed Platform",
                "description": "When the last Storm Guardian model in this unit is destroyed, any remaining Serpent\u2019s Scale Platform models in this unit are also destroyed."
            },
            {
                "name": "Serpent Shield",
                "description": "Models in the bearer\u2019s unit have a 5+ invulnerable save."
            }
        ]
    },
    "Swooping Hawks": {
        "stats": {
            "stat_movement": "14\"",
            "stat_toughness": 3,
            "stat_save": "4+",
            "stat_wounds": 1,
            "stat_leadership": "6+",
            "stat_oc": 1,
            "stat_invuln": "5+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Lasblaster",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "4",
                "skill": "3+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Assault, Lethal Hits"
            },
            {
                "name": "Close Combat Weapon",
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
                "name": "Exarch's Lasblaster",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "4",
                "skill": "3+",
                "strength": "5",
                "ap": "-1",
                "damage": "1",
                "keywords": "Assault, Lethal Hits"
            },
            {
                "name": "Hawk's Talon",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "2",
                "skill": "3+",
                "strength": "6",
                "ap": "-2",
                "damage": "2",
                "keywords": "Lethal Hits"
            },
            {
                "name": "Scatter Laser",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "6",
                "skill": "3+",
                "strength": "5",
                "ap": "0",
                "damage": "1",
                "keywords": "Sustained Hits 1"
            },
            {
                "name": "Power Sword",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "5",
                "skill": "3+",
                "strength": "4",
                "ap": "-2",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "Sunpistol",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "2",
                "skill": "3+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Assault, Lethal Hits, Pistol"
            }
        ],
        "abilities": [
            {
                "name": "Grenade Pack Flyover",
                "description": "Once per turn, in your Movement phase, when this unit is set-up on the battlefield or ends a Normal, Advance or Fall Back move, it can use this ability. If it does, select one enemy unit within 8\" of and visible to this unit and roll one D6 for each Swooping Hawks model in this unit. For each 4+, that enemy unit suffers 1 mortal wound (to a maximum of 6 mortal wounds). Each time this unit uses this ability , until the end of the turn, you cannot target this unit with the Grenades Stratagem."
            },
            {
                "name": "Aspect Shrine Token",
                "description": "Once per battle for each Aspect Shrine token this unit has, you can change the result of one Hit roll or one Wound roll made for a model in this unit (excluding CHARACTER models) to an unmodified 6.\n\nDesigner's Note: Place an Aspect Shrine token next to the unit for each Aspect Shrine token it has, removing one each time this ability is used."
            }
        ]
    },
    "The Visarch": {
        "stats": {
            "stat_movement": "8\"",
            "stat_toughness": 3,
            "stat_save": "2+",
            "stat_wounds": 5,
            "stat_leadership": "6+",
            "stat_oc": 1,
            "stat_invuln": "4+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "\u27a4 Asu-var - quicksilver stance",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "8",
                "skill": "2+",
                "strength": "4",
                "ap": "-1",
                "damage": "1",
                "keywords": "Sustained Hits 2"
            },
            {
                "name": "\u27a4 Asu-var - duellist stance",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "6",
                "skill": "2+",
                "strength": "5",
                "ap": "-2",
                "damage": "2",
                "keywords": "Devastating Wounds, Precision"
            },
            {
                "name": "\u27a4 Asu-var - mythic stance",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "2+",
                "strength": "3",
                "ap": "-4",
                "damage": "3",
                "keywords": "Anti-Epic Hero 2+, Precision"
            }
        ],
        "abilities": [
            {
                "name": "Way of the Blade",
                "description": "While this model is leading a unit, models in that unit have the Fights First ability."
            },
            {
                "name": "Yvraine's Champion",
                "description": "While this model is leading a unit, other Character models attached to that unit have the Feel No Pain 4+ ability."
            },
            {
                "name": "Leader",
                "description": "This model can be attached to the following units:\n- CORSAIR REAVER BAND\n- CORSAIR VOIDREAVERS\n- CORSAIR VOIDSCARRED\n- GUARDIAN DEFENDERS\n- STORM GUARDIANS\n- YNNARI INCUBI\n- YNNARI KABALITE WARRIORS\n- YNNARI WYCHES\n\nYou can attach this unit to one of the above units, even if Yvraine has already been attached to it. If you do, and that Bodyguard unit is destroyed, the Leader units attached to it become separate units, with their original Starting Strengths."
            },
            {
                "name": "Servant of the Whispering God",
                "description": "If your army includes The Visarch, it cannot include any Epic Hero units (excluding Ynnari units). If your army includes any Epic Hero units (excluding Ynnari units), it cannot include The Visarch."
            }
        ]
    },
    "The Yncarne": {
        "stats": {
            "stat_movement": "10\"",
            "stat_toughness": 10,
            "stat_save": "2+",
            "stat_wounds": 12,
            "stat_leadership": "6+",
            "stat_oc": 3,
            "stat_invuln": "4+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "\u27a4 Vilith-zhar - Strike",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "5",
                "skill": "2+",
                "strength": "12",
                "ap": "-4",
                "damage": "D6+1",
                "keywords": "-"
            },
            {
                "name": "\u27a4 Vilith-zhar - Sweep",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "10",
                "skill": "2+",
                "strength": "6",
                "ap": "-4",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "Swirling soul energy",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "D6+3",
                "skill": "N/A",
                "strength": "7",
                "ap": "-1",
                "damage": "D3",
                "keywords": "Ignores Cover, Psychic, Torrent"
            }
        ],
        "abilities": [
            {
                "name": "Inevitable Death",
                "description": "Once in each of your opponent's turns, if this model is on the battlefield when another friendly Aeldari unit is destroyed, just after removing the last model in that unit, you can remove this model from the battlefield and set it up as close as possible to where that destroyed model was destroyed and not within Engagement Range of one or more enemy units. Doing so does not prevent this model from being eligible to move."
            },
            {
                "name": "Ethereal Form",
                "description": "Each time this model destroys an enemy unit it regains up to D3 lost wounds."
            },
            {
                "name": "Avatar of the Whispering God",
                "description": "If your army includes The Yncarne, it cannot include any Epic Hero units (excluding Ynnari units). If your army includes any Epic Hero units (excluding Ynnari units), it cannot include The Yncarne."
            }
        ]
    },
    "Troupe": {
        "stats": {
            "stat_movement": "8\"",
            "stat_toughness": 3,
            "stat_save": "6+",
            "stat_wounds": 1,
            "stat_leadership": "6+",
            "stat_oc": 1,
            "stat_invuln": "4+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Shuriken Pistol",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "4",
                "ap": "-1",
                "damage": "1",
                "keywords": "Assault, Pistol"
            },
            {
                "name": "Harlequin's Blade",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "5",
                "skill": "3+",
                "strength": "3",
                "ap": "-1",
                "damage": "1",
                "keywords": "Devastating Wounds"
            },
            {
                "name": "Harlequin's Special Weapon",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "3+",
                "strength": "4",
                "ap": "-1",
                "damage": "1",
                "keywords": "Devastating Wounds"
            },
            {
                "name": "Fusion Pistol",
                "weapon_type": "ranged",
                "range": "6\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "8",
                "ap": "-4",
                "damage": "D6",
                "keywords": "Assault, Melta 2, Pistol"
            },
            {
                "name": "Neuro Disruptor",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "4",
                "ap": "-2",
                "damage": "1",
                "keywords": "Anti-infantry 2+, Assault, Pistol"
            },
            {
                "name": "Power sword",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "5",
                "skill": "3+",
                "strength": "4",
                "ap": "-2",
                "damage": "1",
                "keywords": "Devastating Wounds"
            }
        ],
        "abilities": [
            {
                "name": "Dance of Death",
                "description": "At the start of the Fight phase, select one of the following abilities for this unit to gain until the end of the phase:\n\u25a0 Hero's Prowess: Each time a model in this unit makes an attack, re-roll a Hit roll of 1.\n\u25a0 Villain's Doom: Each time a model in this unit makes an attack, add 1 to the Wound roll.\n\u25a0 Trickster's Grace: Each time an attack targets this unit, subtract 1 from the Hit roll."
            },
            {
                "name": "Flip Belt",
                "description": "Each time the bearer's unit makes a Normal, Advance, Fall Back or Charge move, ignore any vertical distance when determining the total distance the bearer can be moved during that move."
            }
        ]
    },
    "Vibro Cannon Platform": {
        "stats": {
            "stat_movement": "7\"",
            "stat_toughness": 6,
            "stat_save": "4+",
            "stat_wounds": 5,
            "stat_leadership": "7+",
            "stat_oc": 1,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Vibro Cannon",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "D6",
                "skill": "3+",
                "strength": "9",
                "ap": "-1",
                "damage": "2",
                "keywords": "-"
            },
            {
                "name": "Close Combat Weapon",
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
                "name": "Shuriken Catapult",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "2",
                "skill": "3+",
                "strength": "4",
                "ap": "-1",
                "damage": "1",
                "keywords": "Assault"
            }
        ],
        "abilities": [
            {
                "name": "Sonic Destruction",
                "description": "In your Shooting phase, each time this model makes an attack with its Vibro Cannon that targets an enemy unit, improve the Strength, Armour Penetration and Damage characteristics of that attack by 1 for each other friendly Vibro Cannon Platform model that made one or more attacks with its Vibro Cannon that also targeted that enemy unit this phase."
            },
            {
                "name": "Support Artillery",
                "description": "At the start of the Declare Battle Formations step, this model can join one Guardian Defenders unit from your army (a unit cannot have more than one Support Weapon model joined to it). This model then counts as part of that Guardians unit for the rest of the battle, and that unit's Starting Strength is increased accordingly.\n\n\nThis model, and any unit it is joined to, cannot embark within a Transport."
            },
            {
                "name": "Support Weapon",
                "description": "Each time an attack targets this model's unit, it that unit contains one or more other models, until that attack is resolved, this model has a Toughness characteristic of 3."
            }
        ]
    },
    "Voidweaver": {
        "stats": {
            "stat_movement": "14\"",
            "stat_toughness": 6,
            "stat_save": "4+",
            "stat_wounds": 6,
            "stat_leadership": "6+",
            "stat_oc": 2,
            "stat_invuln": "4+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Close Combat Weapon",
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
                "name": "Shuriken Cannon",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "3",
                "skill": "3+",
                "strength": "6",
                "ap": "-1",
                "damage": "2",
                "keywords": "Lethal Hits"
            },
            {
                "name": "\u27a4 Prismatic Cannon - dispersed pulse",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "2D6",
                "skill": "3+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Blast"
            },
            {
                "name": "\u27a4 Prismatic Cannon - focused lances",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "2",
                "skill": "3+",
                "strength": "12",
                "ap": "-3",
                "damage": "4",
                "keywords": "-"
            },
            {
                "name": "Voidweaver Haywire Cannon",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "3",
                "skill": "3+",
                "strength": "4",
                "ap": "-1",
                "damage": "3",
                "keywords": "Anti-vehicle 4+, Devastating Wounds"
            }
        ],
        "abilities": [
            {
                "name": "Polychromatic Camoflage",
                "description": "This unit can only be selected as the target of a ranged attack if the attacking model is within 18\"."
            }
        ]
    },
    "Vypers": {
        "stats": {
            "stat_movement": "14\"",
            "stat_toughness": 6,
            "stat_save": "3+",
            "stat_wounds": 6,
            "stat_leadership": "7+",
            "stat_oc": 2,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Wraithbone Hull",
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
                "name": "Bright Lance",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "12",
                "ap": "-3",
                "damage": "D6+2",
                "keywords": "-"
            },
            {
                "name": "Scatter Laser",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "6",
                "skill": "3+",
                "strength": "5",
                "ap": "0",
                "damage": "1",
                "keywords": "Sustained Hits 2"
            },
            {
                "name": "Starcannon",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "2",
                "skill": "2+",
                "strength": "8",
                "ap": "-3",
                "damage": "2",
                "keywords": "-"
            },
            {
                "name": "Shuriken Cannon",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "3",
                "skill": "3+",
                "strength": "6",
                "ap": "-1",
                "damage": "2",
                "keywords": "Lethal Hits"
            },
            {
                "name": "\u27a4 Missile Launcher - Starshot",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "10",
                "ap": "-2",
                "damage": "D6",
                "keywords": "-"
            },
            {
                "name": "\u27a4 Missile Launcher - Sunburst",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "D6",
                "skill": "3+",
                "strength": "4",
                "ap": "-1",
                "damage": "1",
                "keywords": "Blast"
            }
        ],
        "abilities": [
            {
                "name": "Harassment Fire",
                "description": "In your Shooting phase, after this unit has shot, select one enemy unit hit by one or more of those attacks. Until the start of your next turn, that enemy unit is suppressed. While a unit is suppressed, each time a model in that unit makes an attack, subtract 1 from the Hit roll."
            }
        ]
    },
    "War Walkers": {
        "stats": {
            "stat_movement": "10\"",
            "stat_toughness": 7,
            "stat_save": "3+",
            "stat_wounds": 6,
            "stat_leadership": "7+",
            "stat_oc": 2,
            "stat_invuln": "5+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "War Walker feet",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "3",
                "skill": "3+",
                "strength": "5",
                "ap": "0",
                "damage": "1",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Crystalline Targeting",
                "description": "In your Shooting phase, after this unit has shot, select one enemy unit hit by one or more of those attacks. Until the end of the phase, each time a friendly Aeldari unit makes an attack that targets that enemy unit, improve the Armour Penetration characteristic of that attack by 1. Each unit can only be selected for that ability once per turn."
            }
        ]
    },
    "Warlock": {
        "stats": {
            "stat_movement": "7\"",
            "stat_toughness": 3,
            "stat_save": "6+",
            "stat_wounds": 2,
            "stat_leadership": "6+",
            "stat_oc": 1,
            "stat_invuln": "4+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Destructor",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "D6",
                "skill": "N/A",
                "strength": "5",
                "ap": "-1",
                "damage": "1",
                "keywords": "Psychic, Torrent"
            },
            {
                "name": "Shuriken Pistol",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "4",
                "ap": "-1",
                "damage": "1",
                "keywords": "Assault, Pistol"
            },
            {
                "name": "Witchblade",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "2",
                "skill": "3+",
                "strength": "3",
                "ap": "0",
                "damage": "2",
                "keywords": "Anti-Infantry 2+, Psychic"
            },
            {
                "name": "Singing Spear",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "9",
                "ap": "0",
                "damage": "3",
                "keywords": "Assault, Psychic"
            },
            {
                "name": "Singing Spear",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "2",
                "skill": "3+",
                "strength": "3",
                "ap": "0",
                "damage": "3",
                "keywords": "Psychic"
            }
        ],
        "abilities": [
            {
                "name": "Leader",
                "description": "This model can be attached to the following units:\n- Guardian Defenders\n- Storm Guardians\n\nYou can attach this model to a unit, even if one Autarch or Farseer model has already been attached to it. If you do, and that Bodyguard unit is destroyed, the Leader units attached to it become separate units, with their original Starting Strengths."
            },
            {
                "name": "Runes of Fortune (Psychic)",
                "description": "Each time an enemy unit declares a charge, if one or more units with this ability are selected as a target of that charge, subtract 2 from the Charge roll."
            },
            {
                "name": "Psychic Communion (Psychic)",
                "description": "Each time this model is selected to shoot, until the end of the phase, add 1 to the Attacks and Strength characteristics of its Destructor weapon for each other friendly Aeldari Psyker model within 6\" of this model (to a maximum of +2)."
            }
        ]
    },
    "Warlock Conclave": {
        "stats": {
            "stat_movement": "7\"",
            "stat_toughness": 3,
            "stat_save": "6+",
            "stat_wounds": 2,
            "stat_leadership": "6+",
            "stat_oc": 1,
            "stat_invuln": "4+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Witchblade",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "2",
                "skill": "3+",
                "strength": "3",
                "ap": "0",
                "damage": "2",
                "keywords": "Anti-Infantry 2+, Psychic"
            },
            {
                "name": "Shuriken Pistol",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "4",
                "ap": "-1",
                "damage": "1",
                "keywords": "Assault, Pistol"
            },
            {
                "name": "Destructor",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "D6",
                "skill": "N/A",
                "strength": "5",
                "ap": "-1",
                "damage": "1",
                "keywords": "Psychic, Torrent"
            },
            {
                "name": "Singing Spear",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "9",
                "ap": "0",
                "damage": "3",
                "keywords": "Assault, Psychic"
            },
            {
                "name": "Singing Spear",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "2",
                "skill": "3+",
                "strength": "3",
                "ap": "0",
                "damage": "3",
                "keywords": "Psychic"
            }
        ],
        "abilities": [
            {
                "name": "Protect (Psychic)",
                "description": "While a Farseer model is leading this unit, each time an attack targets this unit, subtract 1 from the Wound roll."
            },
            {
                "name": "Psychic Communion (Psychic)",
                "description": "Each time this unit is selected to shoot, for each Warlock model in this unit, until the end of the phase, add 1 to the Attacks and Strength characteristics of that model's Destructor weapon for each other friendly Aeldari Psyker model within 6\" of this model (to a maximum of +2)."
            },
            {
                "name": "Leader",
                "description": "At the start of the Declare Battle Formations step, if this unit is not an Attached unit, this unit can join one GUARDIAN DEFENDERS or STORM GUARDIANS unit from your army (a unit cannot have more than one WARLOCK CONCLAVE unit joined to it). If it does, until the end of the battle, every model in this unit counts as being part of that Bodyguard unit, and that Bodyguard unit\u2019s Starting Strength is increased accordingly."
            }
        ]
    },
    "Warlock Skyrunners": {
        "stats": {
            "stat_movement": "14\"",
            "stat_toughness": 4,
            "stat_save": "6+",
            "stat_wounds": 3,
            "stat_leadership": "6+",
            "stat_oc": 2,
            "stat_invuln": "4+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Twin Shuriken Catapult",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "2",
                "skill": "3+",
                "strength": "4",
                "ap": "-1",
                "damage": "1",
                "keywords": "Assault, Twin Linked"
            },
            {
                "name": "Witchblade",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "2",
                "skill": "3+",
                "strength": "3",
                "ap": "0",
                "damage": "2",
                "keywords": "Anti-Infantry 2+, Psychic"
            },
            {
                "name": "Shuriken Pistol",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "4",
                "ap": "-1",
                "damage": "1",
                "keywords": "Assault, Pistol"
            },
            {
                "name": "Destructor",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "D6",
                "skill": "N/A",
                "strength": "5",
                "ap": "-1",
                "damage": "1",
                "keywords": "Psychic, Torrent"
            },
            {
                "name": "Singing Spear",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "9",
                "ap": "0",
                "damage": "3",
                "keywords": "Assault, Psychic"
            },
            {
                "name": "Singing Spear",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "2",
                "skill": "3+",
                "strength": "3",
                "ap": "0",
                "damage": "3",
                "keywords": "Psychic"
            }
        ],
        "abilities": [
            {
                "name": "Psychic Communion (Psychic)",
                "description": "Each time this unit is selected to shoot, for each Warlock model in this unit, until the end of the phase, add 1 to the Attacks and Strength characteristics of that model's Destructor weapon for each other friendly Aeldari Psyker model within 6\" of this model (to a maximum of +2)."
            },
            {
                "name": "Leader",
                "description": "At the start of the Declare Battle Formations step, if this unit is not an Attached unit, this unit can join one WINDRIDERS unit from your army (a unit cannot have more than one WARLOCK SKYRUNNERS unit joined to it). If it does, until the end of the battle, every model in this unit counts as being part of that Bodyguard unit, and that Bodyguard unit\u2019s Starting Strength is increased accordingly."
            },
            {
                "name": "Runes of Battle (Psychic)",
                "description": "Weapons equipped by models in this unit have the [IGNORES COVER] ability."
            }
        ]
    },
    "Warp Spiders": {
        "stats": {
            "stat_movement": "12\"",
            "stat_toughness": 3,
            "stat_save": "3+",
            "stat_wounds": 1,
            "stat_leadership": "6+",
            "stat_oc": 1,
            "stat_invuln": "5+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Death spinner",
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
                "name": "Close Combat Weapon",
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
                "name": "Exarch's Deathspinner",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "D6",
                "skill": "N/A",
                "strength": "6",
                "ap": "-2",
                "damage": "1",
                "keywords": "Ignores Cover, Torrent"
            },
            {
                "name": "Death Weavers",
                "weapon_type": "ranged",
                "range": "6\"",
                "attacks": "D6",
                "skill": "N/A",
                "strength": "4",
                "ap": "-1",
                "damage": "1",
                "keywords": "Ignores Cover, Torrent, Twin-Linked"
            },
            {
                "name": "Spinneret Rifle",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "D6",
                "skill": "N/A",
                "strength": "5",
                "ap": "-1",
                "damage": "1",
                "keywords": "Ignores Cover, Torrent"
            },
            {
                "name": "Powerblades",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "5",
                "skill": "3+",
                "strength": "4",
                "ap": "-2",
                "damage": "1",
                "keywords": "Lethal Hits, Twin-Linked"
            },
            {
                "name": "Powerblade Array",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "10",
                "skill": "3+",
                "strength": "4",
                "ap": "-2",
                "damage": "1",
                "keywords": "Lethal Hits, Twin-Linked"
            }
        ],
        "abilities": [
            {
                "name": "Flickerjump",
                "description": "In your Movement phase, each time this unit is selected to make a Normal move, it can use this ability. If it does, until the end of the turn, this unit is not eligible to declare a charge and models in it have a Move characteristic of 24\". Each time this unit uses this ability, at the end of the phase, roll one D6 for each model in this unit: for each 1, this unit suffers 1 mortal wound."
            },
            {
                "name": "Aspect Shrine Token",
                "description": "Once per battle for each Aspect Shrine token this unit has, you can change the result of one Hit roll or one Wound roll made for a model in this unit (excluding CHARACTER models) to an unmodified 6.\n\nDesigner's Note: Place an Aspect Shrine token next to the unit for each Aspect Shrine token it has, removing one each time this ability is used."
            }
        ]
    },
    "Wave Serpent": {
        "stats": {
            "stat_movement": "14\"",
            "stat_toughness": 9,
            "stat_save": "3+",
            "stat_wounds": 13,
            "stat_leadership": "7+",
            "stat_oc": 2,
            "stat_invuln": "5+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Wraithbone Hull",
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
                "name": "Twin Shuriken Catapult",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "2",
                "skill": "3+",
                "strength": "4",
                "ap": "-1",
                "damage": "1",
                "keywords": "Assault, Twin Linked"
            },
            {
                "name": "Shuriken Cannon",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "3",
                "skill": "3+",
                "strength": "6",
                "ap": "-1",
                "damage": "2",
                "keywords": "Lethal Hits"
            },
            {
                "name": "\u27a4 Twin Aeldari Missile Launcher - Starshot",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "10",
                "ap": "-2",
                "damage": "D6",
                "keywords": "Twin-Linked"
            },
            {
                "name": "\u27a4 Twin Aeldari Missile Launcher - Sunburst",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "D6",
                "skill": "3+",
                "strength": "4",
                "ap": "-1",
                "damage": "1",
                "keywords": "Blast, Twin-Linked"
            },
            {
                "name": "Twin Bright Lance",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "12",
                "ap": "-3",
                "damage": "D6+2",
                "keywords": "Twin-Linked"
            },
            {
                "name": "Twin Scatter Laser",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "6",
                "skill": "3+",
                "strength": "5",
                "ap": "0",
                "damage": "1",
                "keywords": "Sustained Hits 1, Twin-Linked"
            },
            {
                "name": "Twin Shuriken Cannon",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "3",
                "skill": "3+",
                "strength": "6",
                "ap": "-1",
                "damage": "2",
                "keywords": "Lethal Hits, Twin-Linked"
            },
            {
                "name": "Twin Starcannon",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "2",
                "skill": "3+",
                "strength": "8",
                "ap": "-3",
                "damage": "2",
                "keywords": "Twin-Linked"
            }
        ],
        "abilities": [
            {
                "name": "Wave Serpent Shield",
                "description": "Each time a ranged attack targets this model, if the Strength characteristic of that attack is greater than the Toughness characteristic of this model, subtract 1 from the Wound roll."
            },
            {
                "name": "Damaged: 1-4 Wounds Remaining",
                "description": "While this model has 1-4 wounds remaining, each time this model makes an attack, subtract 1 from the Hit roll."
            }
        ]
    },
    "Windriders": {
        "stats": {
            "stat_movement": "14\"",
            "stat_toughness": 4,
            "stat_save": "4+",
            "stat_wounds": 2,
            "stat_leadership": "7+",
            "stat_oc": 2,
            "stat_invuln": "6+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Twin shuriken catapult",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "2",
                "skill": "3+",
                "strength": "4",
                "ap": "-1",
                "damage": "1",
                "keywords": "Assault, Twin-linked"
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
                "name": "Scatter laser",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "6",
                "skill": "3+",
                "strength": "5",
                "ap": "0",
                "damage": "1",
                "keywords": "Sustained Hits 1"
            },
            {
                "name": "Shuriken cannon",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "3",
                "skill": "3+",
                "strength": "6",
                "ap": "-1",
                "damage": "2",
                "keywords": "Lethal Hits"
            }
        ],
        "abilities": [
            {
                "name": "Swift Demise",
                "description": "Each time a model in this unit makes a ranged attack, re-roll a Hit roll of 1. If the target of that attack is the closest eligible target, you can re-roll the Hit roll instead."
            }
        ]
    },
    "Wraithblades": {
        "stats": {
            "stat_movement": "6\"",
            "stat_toughness": 6,
            "stat_save": "2+",
            "stat_wounds": 3,
            "stat_leadership": "8+",
            "stat_oc": 1,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Ghostswords",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "5",
                "skill": "4+",
                "strength": "5",
                "ap": "-2",
                "damage": "2",
                "keywords": "-"
            },
            {
                "name": "Ghostaxe",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "3",
                "skill": "4+",
                "strength": "7",
                "ap": "-2",
                "damage": "2",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Malevolent Souls",
                "description": "Each time a model in this unit is destroyed by a melee attack, if that model has not fought this phase, roll one D6. On a 3+, do not remove it from play; that destroyed model can fight after the attacking model\u2019s unit has finished making its attacks, and is then removed from play."
            },
            {
                "name": "Psychic Guidance",
                "description": "While this unit is within 12\" of one or more friendly Aeldari Psyker models, models in this unit have a Leadership characteristic of 6+ and each time a model in this unit makes an attack, add 1 to the Hit roll."
            },
            {
                "name": "Forceshield",
                "description": "The bearer has a 4+ invulnerable save."
            }
        ]
    },
    "Wraithguard": {
        "stats": {
            "stat_movement": "6\"",
            "stat_toughness": 6,
            "stat_save": "2+",
            "stat_wounds": 3,
            "stat_leadership": "8+",
            "stat_oc": 1,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Close Combat Weapon",
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
                "name": "Wraithcannon",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "1",
                "skill": "4+",
                "strength": "14",
                "ap": "-4",
                "damage": "D6+1",
                "keywords": "-"
            },
            {
                "name": "D-Scythe",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "D6",
                "skill": "N/A",
                "strength": "7",
                "ap": "-3",
                "damage": "1",
                "keywords": "Torrent"
            }
        ],
        "abilities": [
            {
                "name": "War Construct",
                "description": "This unit is eligible to shoot in a turn in which it Fell Back."
            },
            {
                "name": "Psychic Guidance",
                "description": "While this unit is within 12\" of one or more friendly Aeldari Psyker models, models in this unit have a Leadership characteristic of 6+ and each time a model in this unit makes an attack, add 1 to the Hit roll."
            }
        ]
    },
    "Wraithknight": {
        "stats": {
            "stat_movement": "12\"",
            "stat_toughness": 12,
            "stat_save": "2+",
            "stat_wounds": 18,
            "stat_leadership": "6+",
            "stat_oc": 10,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Titanic Feet",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "5",
                "skill": "3+",
                "strength": "8",
                "ap": "-1",
                "damage": "2",
                "keywords": "-"
            },
            {
                "name": "Heavy Wraithcannon",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "D3",
                "skill": "3+",
                "strength": "20",
                "ap": "-4",
                "damage": "2D6",
                "keywords": "Devastating Wounds"
            },
            {
                "name": "Suncannon",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "D6+4",
                "skill": "3+",
                "strength": "10",
                "ap": "-3",
                "damage": "3",
                "keywords": "Blast"
            },
            {
                "name": "Scatter Laser",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "6",
                "skill": "3+",
                "strength": "5",
                "ap": "0",
                "damage": "1",
                "keywords": "Sustained Hits 1"
            },
            {
                "name": "Shuriken Cannon",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "3",
                "skill": "3+",
                "strength": "6",
                "ap": "-1",
                "damage": "2",
                "keywords": "Lethal Hits"
            },
            {
                "name": "Starcannon",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "2",
                "skill": "3+",
                "strength": "8",
                "ap": "-3",
                "damage": "2",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Damaged: 1-6 Wounds Remaining",
                "description": "While this model has 1-6 wounds remaining, subtract 5 from this model\u2019s Objective Control characteristic and each time this model makes an attack, subtract 1 from the Hit roll."
            },
            {
                "name": "Titanic Strides",
                "description": "Each time this model makes a Normal, Advance or Fall Back move, it can move through models (excluding Titanic models) and sections of terrain features that are 4\" or less in height. When doing so:\nIt can move within Engagement Range of enemy models, but cannot end that move within Engagement Range of them.\nIt can also move through sections of terrain features that are more than 4\" in height, but if it does, after it has moved, roll one D6: on a 1, this model is battle-shocked."
            },
            {
                "name": "Point-blank Devastation",
                "description": "Each time this model's Heavy Wraithcannon or Suncannon targets a unit within half range, you can re-roll the dice to determine the number of attacks made."
            },
            {
                "name": "Scattershield",
                "description": "The bearer has a 4+ invulnerable save and each time an attack is allocated to the bearer, subtract 1 from the Damage characteristic of that attack."
            }
        ]
    },
    "Wraithknight with Ghostglaive": {
        "stats": {
            "stat_movement": "12\"",
            "stat_toughness": 12,
            "stat_save": "2+",
            "stat_wounds": 18,
            "stat_leadership": "6+",
            "stat_oc": 10,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "\u27a4 Titanic Ghostglaive - Strike",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "5",
                "skill": "3+",
                "strength": "16",
                "ap": "-3",
                "damage": "6",
                "keywords": "-"
            },
            {
                "name": "\u27a4 Titanic Ghostglaive - Sweep",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "15",
                "skill": "3+",
                "strength": "8",
                "ap": "-2",
                "damage": "2",
                "keywords": "-"
            },
            {
                "name": "Heavy Wraithcannon",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "D3",
                "skill": "3+",
                "strength": "20",
                "ap": "-4",
                "damage": "2D6",
                "keywords": "Devastating Wounds"
            },
            {
                "name": "Scatter Laser",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "6",
                "skill": "3+",
                "strength": "5",
                "ap": "0",
                "damage": "1",
                "keywords": "Sustained Hits 1"
            },
            {
                "name": "Shuriken Cannon",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "3",
                "skill": "3+",
                "strength": "6",
                "ap": "-1",
                "damage": "2",
                "keywords": "Lethal Hits"
            },
            {
                "name": "Starcannon",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "2",
                "skill": "3+",
                "strength": "8",
                "ap": "-3",
                "damage": "2",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Damaged: 1-6 Wounds Remaining",
                "description": "While this model has 1-6 wounds remaining, subtract 5 from this model\u2019s Objective Control characteristic and each time this model makes an attack, subtract 1 from the Hit roll."
            },
            {
                "name": "Titanic Agility",
                "description": "Each time this model makes a Normal, Advance or Fall Back move, it can move through models and terrain features. When doing so, it can move within Engagement Range of enemy models, but cannot end that move within Engagement Range of them."
            },
            {
                "name": "Scattershield",
                "description": "The bearer has a 4+ invulnerable save and each time an attack is allocated to the bearer, subtract 1 from the Damage characteristic of that attack."
            }
        ]
    },
    "Wraithlord": {
        "stats": {
            "stat_movement": "8\"",
            "stat_toughness": 10,
            "stat_save": "2+",
            "stat_wounds": 10,
            "stat_leadership": "8+",
            "stat_oc": 3,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "\u27a4 Ghostglaive - Strike",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "4+",
                "strength": "10",
                "ap": "-3",
                "damage": "D6+1",
                "keywords": "-"
            },
            {
                "name": "\u27a4 Ghostglaive - Sweep",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "8",
                "skill": "4+",
                "strength": "7",
                "ap": "-2",
                "damage": "2",
                "keywords": "-"
            },
            {
                "name": "Wraithbone Fists",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "4+",
                "strength": "7",
                "ap": "-2",
                "damage": "2",
                "keywords": "-"
            },
            {
                "name": "Shuriken Catapult",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "2",
                "skill": "4+",
                "strength": "4",
                "ap": "-1",
                "damage": "1",
                "keywords": "Assault"
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
                "keywords": "Assault, Ignores cover, Torrent"
            },
            {
                "name": "\u27a4 Aeldari Missile Launcher - Starshot",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "1",
                "skill": "4+",
                "strength": "10",
                "ap": "-2",
                "damage": "D6",
                "keywords": "-"
            },
            {
                "name": "\u27a4 Aeldari Missile Launcher - Sunburst",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "D6",
                "skill": "4+",
                "strength": "4",
                "ap": "-1",
                "damage": "1",
                "keywords": "Blast"
            },
            {
                "name": "Bright Lance",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "1",
                "skill": "4+",
                "strength": "12",
                "ap": "-3",
                "damage": "D6+2",
                "keywords": "-"
            },
            {
                "name": "Scatter Laser",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "6",
                "skill": "4+",
                "strength": "5",
                "ap": "0",
                "damage": "1",
                "keywords": "Sustained Hits 1"
            },
            {
                "name": "Shuriken Cannon",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "3",
                "skill": "4+",
                "strength": "6",
                "ap": "-1",
                "damage": "2",
                "keywords": "Lethal Hits"
            },
            {
                "name": "Starcannon",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "2",
                "skill": "4+",
                "strength": "8",
                "ap": "-3",
                "damage": "2",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Fated Hero",
                "description": "At the start of the battle, select one of the following keywords: Infantry, Monster, Mounted, Vehicle. Each time this model makes an attack that targets a unit with the selected keyword, re-roll a Hit roll of 1 and re-roll a Wound roll of 1."
            },
            {
                "name": "Psychic Guidance",
                "description": "While this model is within 12\" of one or more friendly Aeldari Psyker models, improve the Ballistic Skill and Weapon Skill characteristics of weapons equipped by this model by 1 and it has a Leadership characteristic of 6+."
            }
        ]
    },
    "Ynnari Archon": {
        "stats": {
            "stat_movement": "8\"",
            "stat_toughness": 3,
            "stat_save": "4+",
            "stat_wounds": 4,
            "stat_leadership": "6+",
            "stat_oc": 1,
            "stat_invuln": "2+*",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Huskblade",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "5",
                "skill": "2+",
                "strength": "3",
                "ap": "-2",
                "damage": "2",
                "keywords": "Anti-Infantry 3+"
            },
            {
                "name": "Splinter Pistol",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "1",
                "skill": "2+",
                "strength": "2",
                "ap": "0",
                "damage": "1",
                "keywords": "Anti-Infantry 3+, Assault, Pistol"
            },
            {
                "name": "Blast Pistol",
                "weapon_type": "ranged",
                "range": "6\"",
                "attacks": "1",
                "skill": "2+",
                "strength": "8",
                "ap": "-3",
                "damage": "D3",
                "keywords": "Pistol"
            }
        ],
        "abilities": [
            {
                "name": "Leader",
                "description": "This model can be attached to the following units:\n\u25a0 Ynnari Incubi\n\u25a0 Ynnari Kabalite Warriors"
            },
            {
                "name": "Overlord",
                "description": "While this model is leading a unit, each time a model in that unit makes an attack, re-roll a Wound roll of 1. While that unit is below its Starting Strength, each time a model in that unit makes an attack, you can re-roll the Wound roll instead."
            },
            {
                "name": "Reborn Mastermind",
                "description": "Once per battle round, one model from your army with this ability can use it when its unit is targeted with a Stratgem. If it does, reduce the CP cost of that usage of that Stratagem by 1CP."
            },
            {
                "name": "Shadow Field",
                "description": "You cannot re-roll invulnerable saving throws made for the bearer. The first time an invulnerable saving throw made for the bearer is failed, until the end of the battle, the bearer has no invulnerable saving throw."
            }
        ]
    },
    "Ynnari Incubi": {
        "stats": {
            "stat_movement": "7\"",
            "stat_toughness": 3,
            "stat_save": "3+",
            "stat_wounds": 1,
            "stat_leadership": "6+",
            "stat_oc": 1,
            "stat_invuln": "5+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Klaive",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "3",
                "skill": "3+",
                "strength": "4",
                "ap": "-2",
                "damage": "2",
                "keywords": "-"
            },
            {
                "name": "\u27a4 Demiklaives - Dual Blades",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "6",
                "skill": "3+",
                "strength": "4",
                "ap": "-1",
                "damage": "1",
                "keywords": "Twin-Linked"
            },
            {
                "name": "\u27a4 Demiklaives - Single Blade",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "3",
                "skill": "3+",
                "strength": "4",
                "ap": "-2",
                "damage": "2",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Tormentors",
                "description": "At the start of the Fight phase, each enemy unit within Engagement Range of one or more units with this ability must take a Battle-shock test."
            }
        ]
    },
    "Ynnari Kabalite Warriors": {
        "stats": {
            "stat_movement": "8\"",
            "stat_toughness": 3,
            "stat_save": "4+",
            "stat_wounds": 1,
            "stat_leadership": "6+",
            "stat_oc": 2,
            "stat_invuln": "6+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Shredder",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "D6",
                "skill": "N/A",
                "strength": "6",
                "ap": "0",
                "damage": "1",
                "keywords": "Assault, Torrent"
            },
            {
                "name": "Close Combat Weapon",
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
                "name": "Splinter Rifle",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "2",
                "skill": "3+",
                "strength": "2",
                "ap": "0",
                "damage": "1",
                "keywords": "Anti-Infantry 3+, Assault"
            },
            {
                "name": "Blaster",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "8",
                "ap": "-4",
                "damage": "D6+1",
                "keywords": "Assault"
            },
            {
                "name": "Splinter Cannon",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "3",
                "skill": "4+",
                "strength": "3",
                "ap": "-1",
                "damage": "2",
                "keywords": "Anti-Infantry 3+, Heavy, Sustained Hits 1"
            },
            {
                "name": "Dark Lance",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "1",
                "skill": "4+",
                "strength": "12",
                "ap": "-3",
                "damage": "D6+2",
                "keywords": "Heavy"
            },
            {
                "name": "Blast Pistol",
                "weapon_type": "ranged",
                "range": "6\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "8",
                "ap": "-3",
                "damage": "D3",
                "keywords": "Pistol"
            },
            {
                "name": "Splinter Pistol",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "1",
                "skill": "2+",
                "strength": "2",
                "ap": "0",
                "damage": "1",
                "keywords": "Anti-Infantry 3+, Assault, Pistol"
            },
            {
                "name": "Sybarite Weapon",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "3",
                "skill": "3+",
                "strength": "3",
                "ap": "-1",
                "damage": "1",
                "keywords": "Anti-Infantry 3+"
            }
        ],
        "abilities": [
            {
                "name": "Sadistic Raiders",
                "description": "At the end of your Command phase, if you control an objective marker that this unit (or a Transport it is embarked within) is within range of, that objective marker remains under your control until your opponent's Level of Control over that objective marker is greater than yours at the end of any phase."
            },
            {
                "name": "Phantasm Grenade Launcher",
                "description": "The bearer\u2019s unit has the Grenades keyword."
            }
        ]
    },
    "Ynnari Raider": {
        "stats": {
            "stat_movement": "14\"",
            "stat_toughness": 8,
            "stat_save": "4+",
            "stat_wounds": 10,
            "stat_leadership": "6+",
            "stat_oc": 2,
            "stat_invuln": "6+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Bladevanes",
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
                "name": "Disintegrator Cannon",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "3",
                "skill": "3+",
                "strength": "5",
                "ap": "-2",
                "damage": "2",
                "keywords": "-"
            },
            {
                "name": "Dark Lance",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "12",
                "ap": "-3",
                "damage": "D6+2",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Aethersails",
                "description": "Each time this model Advances, do not make an Advance roll for it. Instead, until the end of the phase, add 6\" to the Move characteristic of this model."
            }
        ]
    },
    "Ynnari Reavers": {
        "stats": {
            "stat_movement": "16\"",
            "stat_toughness": 4,
            "stat_save": "4+",
            "stat_wounds": 2,
            "stat_leadership": "6+",
            "stat_oc": 2,
            "stat_invuln": "6+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Splinter Rifle",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "2",
                "skill": "3+",
                "strength": "2",
                "ap": "0",
                "damage": "1",
                "keywords": "Anti-Infantry 3+, Assault"
            },
            {
                "name": "Splinter Pistol",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "2",
                "ap": "0",
                "damage": "1",
                "keywords": "Anti-Infantry 3+, Assault, Pistol"
            },
            {
                "name": "Bladevanes",
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
                "name": "Blaster",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "8",
                "ap": "-4",
                "damage": "D6+1",
                "keywords": "Assault"
            },
            {
                "name": "Heat Lance",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "14",
                "ap": "-4",
                "damage": "D6",
                "keywords": "Assault, Melta 3"
            },
            {
                "name": "Agonizer",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "3+",
                "strength": "3",
                "ap": "-1",
                "damage": "1",
                "keywords": "Anti-Infantry 3+"
            }
        ],
        "abilities": [
            {
                "name": "Eviscerating Fly-by",
                "description": "Each time this unit ends a Normal move, you can select one enemy unit (excluding Monster and Vehicle units) that it moved over during that move. If you do, roll one D6 for each model in this unit: for each 4+, that enemy unit suffers 1 mortal wound."
            }
        ]
    },
    "Ynnari Succubus": {
        "stats": {
            "stat_movement": "8\"",
            "stat_toughness": 3,
            "stat_save": "6+",
            "stat_wounds": 4,
            "stat_leadership": "6+",
            "stat_oc": 1,
            "stat_invuln": "4+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Succubus Weapons",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "6",
                "skill": "2+",
                "strength": "3",
                "ap": "-2",
                "damage": "1",
                "keywords": "Anti-Infantry 3+"
            },
            {
                "name": "Splinter Pistol",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "1",
                "skill": "2+",
                "strength": "2",
                "ap": "0",
                "damage": "1",
                "keywords": "Anti-Infantry 3+, Assault, Pistol"
            },
            {
                "name": "Blast Pistol",
                "weapon_type": "ranged",
                "range": "6\"",
                "attacks": "1",
                "skill": "2+",
                "strength": "8",
                "ap": "-3",
                "damage": "D3",
                "keywords": "Pistol"
            }
        ],
        "abilities": [
            {
                "name": "Empowered by Death",
                "description": "At the start of the Fight phase, if this model's unit is below its Starting Strength, models in that unit have the Fights First ability."
            },
            {
                "name": "Storm of Blades",
                "description": "While this model is leading a unit, melee weapons equipped by models in that unit have the [SUSTAINED HITS 1] ability."
            },
            {
                "name": "Leader",
                "description": "This model can be attached to the following unit:\n\u25a0 Ynnari Wyches"
            }
        ]
    },
    "Ynnari Venom": {
        "stats": {
            "stat_movement": "14\"",
            "stat_toughness": 6,
            "stat_save": "4+",
            "stat_wounds": 6,
            "stat_leadership": "6+",
            "stat_oc": 1,
            "stat_invuln": "6+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Bladevanes",
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
                "name": "Splinter Cannon",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "3",
                "skill": "3+",
                "strength": "3",
                "ap": "-1",
                "damage": "2",
                "keywords": "Anti-Infantry 3+, Sustained hits 1"
            },
            {
                "name": "Twin Splinter Rifle",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "2",
                "skill": "3+",
                "strength": "2",
                "ap": "0",
                "damage": "1",
                "keywords": "Anti-Infantry 3+, Assault, Rapid Fire 1, Twin Linked"
            }
        ],
        "abilities": [
            {
                "name": "Lithe Embarkation",
                "description": "At the end of the Fight phase, if there are no models currently embarked within this Transport, you can select one friendly Ynnari Infantry unit that only includes models from the units listed in this unit's Transport section, that has 6 or fewer models and that is wholly within 6\" of this Transport. Unless that unit is within Engagement Range of one or more enemy units, it can embark within this Transport. That unit can embark within this TRANSPORT in a turn it disembarked from this TRANSPORT."
            }
        ]
    },
    "Ynnari Wyches": {
        "stats": {
            "stat_movement": "8\"",
            "stat_toughness": 3,
            "stat_save": "6+",
            "stat_wounds": 1,
            "stat_leadership": "6+",
            "stat_oc": 2,
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Splinter Pistol",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "2",
                "ap": "0",
                "damage": "1",
                "keywords": "Anti-Infantry 3+, Assault, Pistol"
            },
            {
                "name": "Hekatarii Blade",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "3",
                "skill": "3+",
                "strength": "3",
                "ap": "-1",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "Blast Pistol",
                "weapon_type": "ranged",
                "range": "6\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "8",
                "ap": "-3",
                "damage": "D3",
                "keywords": "Pistol"
            }
        ],
        "abilities": [
            {
                "name": "No Escape",
                "description": "Each time an enemy unit (excluding Monsters and Vehicles) within Engagement Range of one or more units from your army with this ability is selected to Fall Back, all models in that enemy unit must take a Desperate Escape test. When doing so, if that enemy unit is Battle-shocked, subtract 1 from each of those tests."
            }
        ]
    },
    "Yvraine": {
        "stats": {
            "stat_movement": "8\"",
            "stat_toughness": 3,
            "stat_save": "6+",
            "stat_wounds": 4,
            "stat_leadership": "6+",
            "stat_oc": 1,
            "stat_invuln": "4+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Kha-vir",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "5",
                "skill": "2+",
                "strength": "4",
                "ap": "-3",
                "damage": "2",
                "keywords": "Devastating Wounds"
            },
            {
                "name": "Storm of Whispers",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "D6+3",
                "skill": "2+",
                "strength": "2",
                "ap": "-2",
                "damage": "1",
                "keywords": "Anti-Infantry 2+, Devastating Wounds, Psychic"
            }
        ],
        "abilities": [
            {
                "name": "Herald of Ynnead",
                "description": "At the start of the Fight phase, select one enemy unit within Engagement Range of this model. Until the end of the phase, each time a friendly AELDARI model makes an attack that targets that unit, you can re-roll a Wound roll of 1."
            },
            {
                "name": "Word of the Phoenix (Psychic)",
                "description": "While this model is leading a unit, in your Command phase, roll one D6: on a 2+, D3+1 destroyed Bodyguard models (excluding Support Weapon models) are returned to that unit with their full wounds remaining."
            },
            {
                "name": "Leader",
                "description": "This model can be attached to the following units:\n- CORSAIR REAVER BAND\n- CORSAIR VOIDREAVERS\n- CORSAIR VOIDSCARRED\n- GUARDIAN DEFENDERS\n- STORM GUARDIANS\n- YNNARI INCUBI\n- YNNARI KABALITE WARRIORS\n- YNNARI WYCHES"
            },
            {
                "name": "Servant of the Whispering God",
                "description": "If your army includes Yvraine, it cannot include any Epic Hero units (excluding Ynnari units). If your army includes any Epic Hero units (excluding Ynnari units), it cannot include Yvraine."
            }
        ]
    }
}


class Command(BaseCommand):
    """Refresh Aeldari stat lines, weapon profiles, and abilities from BSData."""

    help = 'Refresh 11th Edition stats/weapons/abilities for Aeldari units.'

    def add_arguments(self, parser):
        """Add --dry-run flag."""
        parser.add_argument(
            '--dry-run', action='store_true',
            help='Preview changes without writing to the database.',
        )

    def handle(self, *args, **options):
        """Iterate AELDARI_DATASHEETS and refresh each unit's datasheet data."""
        dry_run = options['dry_run']
        updated = 0
        skipped = 0

        with transaction.atomic():
            for name, payload in AELDARI_DATASHEETS.items():
                try:
                    unit = UnitType.objects.get(name=name, faction__name='Aeldari')
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
