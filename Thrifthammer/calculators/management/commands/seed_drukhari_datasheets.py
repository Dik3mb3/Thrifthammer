"""
Management command: seed_drukhari_datasheets

Refreshes stat lines, weapon profiles, and abilities for the core
Drukhari units using 11th Edition data sourced from BSData/wh40k-11e
("Aeldari - Drukhari.json" resolved against "Aeldari - Aeldari
Library.json") -- the same source used by seed_drukhari_points.py.

Usage:
    python manage.py seed_drukhari_datasheets
    python manage.py seed_drukhari_datasheets --dry-run

Notes:
- Does NOT touch points_cost or category -- those are handled entirely by
  seed_drukhari_points.py. This command only refreshes stat_* fields,
  WeaponProfile rows, and UnitAbility rows.
- Scoped to the 23 core-Drukhari rows only (including the Scourges
  Heavy Weapons/Shardcarbines split, which BSData resolves as two
  independently-named unit entries, not a single build-choice unit).
  The 12 cross-faction Harlequins/Corsair rows added to Drukhari share
  their product AND their unit identity with existing Aeldari rows --
  refreshing those is Aeldari's own datasheet command's job, not this
  one's.
- Per-field safety rule: a unit's stats/weapons/abilities are only
  overwritten when BSData actually has that data for it. If extraction
  found nothing, the existing DB value/rows are left untouched.
- All 23 active units resolved cleanly -- 0 missing stats/weapons/
  abilities. One overlong stat field skipped (Wyches' conditional
  invulnerable save "4+* / 6+", 8 chars vs stat_invuln's max_length=4)
  -- same class of gap as Aeldari's Howling Banshees.
- **Also copies datasheets for the 12 cross-faction Harlequins/Corsair
  rows** from their existing Aeldari counterpart (same physical unit,
  same rules) -- these rows were created with correct points/category by
  seed_drukhari_points.py but had zero stat_*/weapon/ability data of
  their own, since BSData extraction for this command is scoped to the
  Drukhari roster's own entries and these 12 are Aeldari-book units.
  Caught by direct DB inspection after the first datasheets run.
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from calculators.models import UnitAbility, UnitType, WeaponProfile

STAT_FIELDS = [
    'stat_movement', 'stat_toughness', 'stat_save', 'stat_wounds',
    'stat_leadership', 'stat_oc', 'stat_invuln', 'stat_fnp',
]

# Cross-faction rows added to Drukhari that share their physical unit
# (and therefore their datasheet) with an existing Aeldari row of the
# same name.
DRUKHARI_CROSS_FACTION_COPY = [
    'Corsair Skyreavers', 'Corsair Voidreavers', 'Corsair Voidscarred',
    'Death Jester', 'Kharseth', 'Prince Yriel', 'Shadowseer', 'Solitaire',
    'Troupe', 'Skyweavers', 'Starweaver', 'Voidweaver',
]

# (name -> {stats?, weapons?, abilities?}). Missing keys mean "no data
# found for this field -- leave existing DB data untouched."
DRUKHARI_DATASHEETS = {
    "Archon": {
        "stats": {
            "stat_movement": "7\"",
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
                "name": "Splinter pistol",
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
                "name": "Blast pistol",
                "weapon_type": "ranged",
                "range": "6\"",
                "attacks": "1",
                "skill": "2+",
                "strength": "8",
                "ap": "-3",
                "damage": "D3",
                "keywords": "Pistol"
            },
            {
                "name": "Huskblade",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "2+",
                "strength": "3",
                "ap": "-2",
                "damage": "3",
                "keywords": "Devastating Wounds"
            },
            {
                "name": "Agoniser",
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
                "name": "Master-crafted power weapon",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "5",
                "skill": "2+",
                "strength": "4",
                "ap": "-2",
                "damage": "2",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Leader",
                "description": "This model can be attached to the following units:\n- COURT OF THE ARCHON\n- HAND OF THE ARCHON\n- INCUBI\n- KABALITE WARRIORS"
            },
            {
                "name": "Overlord",
                "description": "Once per battle, at the start of any phase, you can select one friendly Drukhari unit that is Battle-shocked and within 12\" of this model. That unit is no longer Battle-shocked."
            },
            {
                "name": "Devious Mastermind",
                "description": "Once per battle round, one model from your army with this ability can use it when its unit is targeted with a stratagem. If it does, reduce the CP cost of that use of that Stratagem by 1CP."
            },
            {
                "name": "Hatred Eternal (Pain)",
                "description": "In your Shooting or the Fight phase, when you select this model's unit to shoot or fight, you can spend 1 Pain token to Empower that unit. While that unit is Empowered, each time a model in that unit makes an attack, you can re-roll the Hit roll."
            },
            {
                "name": "Shadowfield",
                "description": "While this model has an InSv, this unit cannot re-roll save rolls. When this model loses a wound (excluding from mortal wounds), this model has no InSv until the end of the battle."
            },
            {
                "name": "Soul Trap",
                "description": "Add 1 to the Attacks and Strength characteristics of the bearer's melee weapons. The first time the bearer makes a melee attack that destroys an enemy model, after all the bearer's attacks have been resolved, until the end of the battle, add an additional 1 to the Attacks and Strength characteristics of the bearer's melee weapons."
            }
        ]
    },
    "Cronos": {
        "stats": {
            "stat_movement": "7\"",
            "stat_toughness": 7,
            "stat_save": "3+",
            "stat_wounds": 7,
            "stat_leadership": "7+",
            "stat_oc": 2,
            "stat_invuln": "6+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Spirit Vortex",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "D6",
                "skill": "3+",
                "strength": "5",
                "ap": "-1",
                "damage": "1",
                "keywords": "Blast, Ignores Cover"
            },
            {
                "name": "Spirit Syphon",
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
                "name": "Spirit-leech Tentacles",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "6",
                "skill": "3+",
                "strength": "5",
                "ap": "-1",
                "damage": "1",
                "keywords": "Anti-Infantry 2+"
            }
        ],
        "abilities": [
            {
                "name": "Pain Engine (Aura)",
                "description": "Each time you spend 1 Pain token to Empower a friendly unit within 9\" of this unit, roll one D6, adding 1 to the result if one or more models in this unit are not equipped with a spirit vortex: on a 5+, you gain 1 Pain token.\n\n\nDesigner's Note: Pain tokens you spend for reasons other than Empowering a unit do not trigger this ability."
            },
            {
                "name": "Pain Parasite (Pain)",
                "description": "In your Shooting phase or the Fight phase, when you select this unit to shoot or fight, you can spend 1 Pain token to Empower this unit. While Empowered, each time this unit shoots or fights, after it has resolved its attacks, if one or more enemy models were destroyed as a result of those attacks, one model in this unit regains up to 3 lost wounds (if all models in this unit have their starting number of wounds and this unit is below its Starting Strength, 1 model is returned to this unit with 3 wounds remaining)."
            }
        ]
    },
    "Drazhar": {
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
                "name": "\u27a4 The Executioner's demiklaives - Dual Blades",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "8",
                "skill": "2+",
                "strength": "5",
                "ap": "-2",
                "damage": "2",
                "keywords": "Devastating Wounds"
            },
            {
                "name": "\u27a4 The Executioner's demiklaives - Single Blade",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "6",
                "skill": "2+",
                "strength": "6",
                "ap": "-2",
                "damage": "3",
                "keywords": "Devastating Wounds"
            }
        ],
        "abilities": [
            {
                "name": "Leader",
                "description": "This model can be attached to the following unit:\n\u25a0 Incubi"
            },
            {
                "name": "Master of Blades (Pain)",
                "description": "In the Fight phase, when you select this model's unit to fight, you can spend 1 Pain token to Empower that unit. While that unit is Empowered, each time a model in that unit makes a melee attack, add 1 to the Wound roll."
            },
            {
                "name": "Onslaught",
                "description": "While this model is leading a unit, each time a model in that unit makes a Pile-In or Consolidation move, it can move up to 6\" instead of up to 3\"."
            },
            {
                "name": "Silent Executioner",
                "description": "Each time this model make an attack that targets a unit that is below its Starting Strength, you can re-roll the Hit roll. If that target is Below Half-Strength, you can re-roll the Wound roll as well."
            }
        ]
    },
    "Haemonculus": {
        "stats": {
            "stat_movement": "7\"",
            "stat_toughness": 4,
            "stat_save": "5+",
            "stat_wounds": 5,
            "stat_leadership": "7+",
            "stat_oc": 1,
            "stat_invuln": "6+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Haemonculus tools and scissorhands",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "5",
                "skill": "2+",
                "strength": "3",
                "ap": "-1",
                "damage": "D3",
                "keywords": "Anti-Infantry 2+, Precision"
            },
            {
                "name": "Stinger Pistol",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "1",
                "skill": "2+",
                "strength": "2",
                "ap": "-1",
                "damage": "D3",
                "keywords": "Anti-infantry 2+, Pistol, Precision"
            }
        ],
        "abilities": [
            {
                "name": "Leader",
                "description": "This model can be attached to the following unit:\n\u25a0 Wracks"
            },
            {
                "name": "Fear Incarnate (Aura)",
                "description": "While an enemy unit is within 6\" of this model, worsen the Leadership characteristic of models in that unit by 1. In addition, in the Battle-shock step of your opponent's Command phase, if such an enemy unit is below its Starting Strength, it must take a Battle-shock test."
            },
            {
                "name": "Pain Adept",
                "description": "In your Command phase, if one or more models from your army with this ability are on the battlefield, roll one D6: on a 4+, you gain 1 Pain token."
            },
            {
                "name": "Fleshcraft (Pain)",
                "description": "In your Command phase, you can spend 1 Pain token to Empower this model's unit. Each time you do, you can return up to D3+1 destroyed Bodyguard models to that unit."
            }
        ]
    },
    "Hand of the Archon": {
        "stats": {
            "stat_movement": "7\"",
            "stat_toughness": 3,
            "stat_save": "4+",
            "stat_wounds": 1,
            "stat_leadership": "7+",
            "stat_oc": 1,
            "stat_invuln": "6+",
            "stat_fnp": ""
        },
        "weapons": [
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
                "skill": "3+",
                "strength": "2",
                "ap": "0",
                "damage": "1",
                "keywords": "Anti-Infantry 3+, Assault, Pistol"
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
                "name": "Power Weapon",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "3+",
                "strength": "3",
                "ap": "-2",
                "damage": "1",
                "keywords": "Anti-Infantry 3+"
            },
            {
                "name": "Stinger pistol",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "2",
                "ap": "0",
                "damage": "1",
                "keywords": "Anti-Infantry 2+, Pistol"
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
                "name": "Shardcarbine",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "3",
                "skill": "3+",
                "strength": "2",
                "ap": "0",
                "damage": "1",
                "keywords": "Anti-Infantry 3+, Assault"
            },
            {
                "name": "Pain sculptors",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "3",
                "skill": "3+",
                "strength": "4",
                "ap": "-1",
                "damage": "1",
                "keywords": "Anti-Infantry 4+, Twin-Linked"
            },
            {
                "name": "Razorflail",
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
                "name": "Assassins' Poisons (Pain)",
                "description": "In your Shooting phase or the Fight phase, when you select this unit to shoot or fight, you can spend 1 Pain token to Empower this unit. While Empowered, weapons equipped by models in this unit (excluding blast pistols, blasters and dark lances) have the [Lethal Hits] and [Precision] abilities."
            },
            {
                "name": "Archon's Will",
                "description": "At the start of the first battle round, select one objective marker on the battlefield. Until the end of the battle, while this unit is within range of that objective marker, unless this unit is Battle-shocked, models in this unit have a 5+ invulnerable save and an Objective Control characteristic of 3."
            },
            {
                "name": "Archon's Retinue",
                "description": "If this unit has a Leader unit attached to it during the Declare Battle Formations step, that Leader unit gains the Scouts 7\" ability."
            },
            {
                "name": "Phantasm Grenade Launcher",
                "description": "The bearer\u2019s unit has the Smoke keyword."
            },
            {
                "name": "Kabalite icon",
                "description": "While the bearer's unit is not Battle-shocked, add 1 to the bearer's Objective Control characteristic."
            },
            {
                "name": "Stimm-needler",
                "description": "Once per turn, the first time a saving throw is failed for a model in the bearer's unit, change the Damage characteristic of that attack to 0."
            }
        ]
    },
    "Hellions": {
        "stats": {
            "stat_movement": "14\"",
            "stat_toughness": 4,
            "stat_save": "4+",
            "stat_wounds": 2,
            "stat_leadership": "7+",
            "stat_oc": 1,
            "stat_invuln": "6+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Hellglaive",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "3",
                "skill": "3+",
                "strength": "4",
                "ap": "-1",
                "damage": "2",
                "keywords": "Lance, Sustained Hits 1"
            },
            {
                "name": "Splinter Pods",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "2",
                "skill": "3+",
                "strength": "2",
                "ap": "0",
                "damage": "1",
                "keywords": "Anti-Infantry 3+, Assault, Twin Linked"
            },
            {
                "name": "Power weapon",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "3+",
                "strength": "3",
                "ap": "-2",
                "damage": "1",
                "keywords": "Anti-Infantry 3+, Lance, Sustained Hits 1"
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
                "keywords": "Anti-infantry 3+, Assault, Pistol"
            },
            {
                "name": "Stunclaw",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "3+",
                "strength": "3",
                "ap": "-1",
                "damage": "1",
                "keywords": "Devastating Wounds, Lance, Precision"
            }
        ],
        "abilities": [
            {
                "name": "Battlefield Butchery (Pain)",
                "description": "In the Fight phase, when you select this unit to fight, you can spend 1 Pain token to Empower this unit. While Empowered, add 1 to the Attacks and Strength characteristics of this unit's melee weapons."
            },
            {
                "name": "Skyboard Evasion",
                "description": "In your opponent's Movement phase, if an enemy unit ends a move within 8\u201d of this unit, if this unit is not within Engagement Range of one or more enemy units, this unit can make a Normal move of up to D6\u201d."
            },
            {
                "name": "Phantasm Grenade Launcher",
                "description": "The bearer\u2019s unit has the Smoke and Grenades keywords."
            }
        ]
    },
    "Incubi": {
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
                "strength": "5",
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
                "ap": "-2",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "\u27a4 Demiklaives - Single Blade",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "3+",
                "strength": "5",
                "ap": "-2",
                "damage": "2",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Tormentors",
                "description": "At the start of the Fight phase, each enemy unit within Engagement Range of one or more units with this ability must take a Battle-shock test. Each time a model in this unit makes a melee attack that targets a Battle-shocked unit, add 1 to the Hit roll."
            },
            {
                "name": "Decapitating Strikes (Pain)",
                "description": "In the Fight phase, when you select this unit to fight, you can spend 1 Pain token to Empower this unit. While Empowered, each time a model in this unit makes a melee attack that targets an Infantry unit, that attack has the [Devastating Wounds] ability."
            },
            {
                "name": "Incubi Shrine Token",
                "description": "Once per battle for each Incubi Shrine token this unit has, you can change the result of one Hit roll or one Wound roll made for a Klaivex or Incubi model in this unit to an unmodified 6."
            }
        ]
    },
    "Kabalite Warriors": {
        "stats": {
            "stat_movement": "7\"",
            "stat_toughness": 3,
            "stat_save": "4+",
            "stat_wounds": 1,
            "stat_leadership": "7+",
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
                "skill": "3+",
                "strength": "2",
                "ap": "0",
                "damage": "1",
                "keywords": "Anti-Infantry 3+, Assault, Pistol"
            },
            {
                "name": "Power Weapon",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "3",
                "skill": "3+",
                "strength": "3",
                "ap": "-2",
                "damage": "1",
                "keywords": "Anti-Infantry 3+"
            }
        ],
        "abilities": [
            {
                "name": "Cruel Enforcers",
                "description": "At the end of your Command phase, if this unit is within range of an objective marker you control, that objective marker remains under you control, until your opponent's Level of Control over that objective marker is greater than yours at the end of a phase."
            },
            {
                "name": "Sadistic Raiders (Pain)",
                "description": "In your Shooting phase or the Fight phase, when you select this unit to shoot or fight, you can spend 1 Pain token to Empower this unit. While Empowered, each time a model in this unit makes an attack, re-roll a Wound roll of 1. If the target is within range of an objective marker, you can re-roll the Wound roll instead."
            },
            {
                "name": "Phantasm Grenade Launcher",
                "description": "The bearer\u2019s unit has the Smoke and Grenades keywords."
            },
            {
                "name": "Kabalite Icon",
                "description": "While the bearer's unit is not Battle-shocked, add 1 to the bearer's Objective Control characteristic."
            }
        ]
    },
    "Lady Malys": {
        "stats": {
            "stat_movement": "7\"",
            "stat_toughness": 3,
            "stat_save": "4+",
            "stat_wounds": 5,
            "stat_leadership": "6+",
            "stat_oc": 2,
            "stat_invuln": "4+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Lady's Blade",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "6",
                "skill": "2+",
                "strength": "5",
                "ap": "-3",
                "damage": "3",
                "keywords": "Devastating Wounds, Hazardous"
            },
            {
                "name": "Razor fan",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "6",
                "skill": "2+",
                "strength": "3",
                "ap": "0",
                "damage": "1",
                "keywords": "Extra Attacks"
            }
        ],
        "abilities": [
            {
                "name": "Leader",
                "description": "This model can be attached to the following units:\n\u25a0 Hand of the Archon\n\u25a0 Incubi\n\u25a0 Kabalite Warriors"
            },
            {
                "name": "Archon of the Poisoned Tongue (Pain)",
                "description": "In your Shooting phase or the Fight phase, when you select this model's unit to shoot or fight, you can spend 1 Pain token to Empower that unit. If you do, select one of the following abilities: [Sustained Hits 1]; [Lethal Hits]. Until the end of the phase, while that unit is Empowered, weapons equipped by models in that unit have that selected ability."
            },
            {
                "name": "Precognisant",
                "description": "If you army includes this model, after both players have deployed their armies, select up to three Drukhari units from your army and redeploy them. When doing so, you can set those units up in Strategic Reserves if you wish, regardless of how many units are already in Strategic Reserves."
            },
            {
                "name": "Mind Like a Steel Trap",
                "description": "Once per turn, when your opponent targets a unit from their army within 12\u201d of this model with a stratagem, you can use this ability. If you do increase the CP cost of that use of that stratagem by 1CP."
            }
        ]
    },
    "Lelith Hesperax": {
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
                "name": "Lelith's blades",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "8",
                "skill": "2+",
                "strength": "3",
                "ap": "-2",
                "damage": "1",
                "keywords": "Anti-Infantry 2+, Precision, Sustained Hits 2"
            }
        ],
        "abilities": [
            {
                "name": "Leader",
                "description": "This model can be attached to the following unit:\n\u25a0 Wyches"
            },
            {
                "name": "Brides of Death (Pain)",
                "description": "In the Fight phase, when you select this model's unit to fight, you can spend 1 Pain token to Empower that unit. While that unit is Empowered, each time a model in that unit makes a melee attack, improve the Strength and Armour Penetration characteristics of that attack by 1."
            },
            {
                "name": "Thrilling Spectacle",
                "description": "Once per battle, at the start of the Fight phase, this model can use this ability. If it does, until the end of the phase, this model has a 3+ invulnerable save and change the Attacks characteristic of melee weapons equipped by this model to 12."
            },
            {
                "name": "Blur of Blades",
                "description": "While this model is leading a unit, models in that unit have the Fights First ability."
            }
        ]
    },
    "Mandrakes": {
        "stats": {
            "stat_movement": "8\"",
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
                "name": "Baleblast",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "2",
                "skill": "3+",
                "strength": "5",
                "ap": "-1",
                "damage": "1",
                "keywords": "Assault, Devastating Wounds, Ignores Cover"
            },
            {
                "name": "Glimmersteel Blade",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "3",
                "skill": "3+",
                "strength": "5",
                "ap": "-1",
                "damage": "1",
                "keywords": "Devastating Wounds"
            }
        ],
        "abilities": [
            {
                "name": "Fade Away (Pain)",
                "description": "At the end of your opponent\u2019s Fight phase, if this unit is not within Engagement Range of one or more enemy units, you can spend 1 Pain token to Empower this unit. Each time you do, remove this unit from the battlefield and place it into Strategic Reserves."
            },
            {
                "name": "Shade Weavers",
                "description": "This unit cannot be targeted by ranged attacks unless the attacking model is within 18\"."
            }
        ]
    },
    "Raider": {
        "stats": {
            "stat_movement": "14\"",
            "stat_toughness": 8,
            "stat_save": "4+",
            "stat_wounds": 10,
            "stat_leadership": "7+",
            "stat_oc": 2,
            "stat_invuln": "6+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Bladevanes and chainsnares",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "D3+3",
                "skill": "4+",
                "strength": "6",
                "ap": "-1",
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
                "description": "While one or more Drukhari units are embarked within this model, you can re-roll Advance and Charge rolls made for this model."
            },
            {
                "name": "Splinter Racks (Pain)",
                "description": "In your Shooting phase, when you select this model to shoot, you can spend 1 Pain token to Empower this model. While Empowered, if one or more units are embarked within this model, each time this model makes an attack with a ranged weapon that has the Anti ability, you can re-roll the Hit roll."
            },
            {
                "name": "Vanguard of the Dark City",
                "description": "At the start of your Command phase, select one of the abilities in the Vanguard of the Dark City section (see left) for this model. Until the start of your next Command phase, this model has that ability."
            },
            {
                "name": "Masters of the Shadowed Sky",
                "description": "At the end of your Command phase, if this model is within range of an objective marker you control, and if one or more Kabalite Warriors units are embarked within it, that objective marker remains under your control until your opponent's Level of Control over that objective marker is greater than yours at the end of a phase."
            },
            {
                "name": "Speed of the Kill",
                "description": "Each time a Wyches unit disembarks from this model (excluding Emergency Disembarkations), models in that Wyches unit must be setup wholly within 6\" of this model."
            },
            {
                "name": "Visions of Butchery",
                "description": "While one or more Wracks units are embarked within this model, for each Wracks model embarked within this model, add 1 to the Attacks characteristic of this model's Bladevanes and chainsnares."
            }
        ]
    },
    "Ravager": {
        "stats": {
            "stat_movement": "14\"",
            "stat_toughness": 9,
            "stat_save": "4+",
            "stat_wounds": 11,
            "stat_leadership": "7+",
            "stat_oc": 3,
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
                "ap": "-1",
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
                "name": "Damaged: 1-4 Wounds Remaining",
                "description": "While this model has 1-4 wounds remaining, each time this model makes an attack, subtract 1 from the Hit roll."
            },
            {
                "name": "Eradicate the Foe",
                "description": "Each time this model makes an attack that targets an enemy unit that is at its Starting Strength, you can re-roll the Hit roll."
            },
            {
                "name": "Agonising Suppression (Pain)",
                "description": "In your Shooting phase, when you select this model to shoot, you can spend 1 Pain token to Empower this model. While Empowered, after this model has shot, select one enemy unit hit by one or more of those attacks. Until the start of your next turn, that enemy unit is suppressed. While a unit is suppressed, each time a model in that unit makes an attack, subtract 1 from the Hit roll."
            }
        ]
    },
    "Razorwing Jetfighter": {
        "stats": {
            "stat_movement": "-",
            "stat_toughness": 8,
            "stat_save": "4+",
            "stat_wounds": 10,
            "stat_leadership": "7+",
            "stat_oc": None,
            "stat_invuln": "6+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Bladed Wings",
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
                "name": "\u27a4 Razorwing Missiles - Monoscythe Missiles",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "D6",
                "skill": "3+",
                "strength": "6",
                "ap": "-1",
                "damage": "2",
                "keywords": "Blast"
            },
            {
                "name": "\u27a4 Razorwing Missiles - Neurotoxin Missiles",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "D6+3",
                "skill": "3+",
                "strength": "2",
                "ap": "0",
                "damage": "1",
                "keywords": "Anti-Infantry 2+, Blast"
            },
            {
                "name": "\u27a4 Razorwing Missiles - Shatterfield Missiles",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "D6",
                "skill": "3+",
                "strength": "7",
                "ap": "-2",
                "damage": "1",
                "keywords": "Blast"
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
                "keywords": "Anti-Infantry 3+, Sustained Hits 1"
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
                "keywords": "Anti-Infantry 3+, Assault, Rapid Fire 2, Twin Linked"
            }
        ],
        "abilities": [
            {
                "name": "Ground-attack Craft",
                "description": "Each time a model in this unit makes a ranged attack that targets an enemy unit (excluding units that can Fly), add 1 to the Hit roll."
            },
            {
                "name": "Nowhere to Run (Pain)",
                "description": "In your Shooting phase, when you select this unit to shoot, you can spend 1 Pain token to Empower this unit. While Empowered, after this unit has shot, select one enemy unit (excluding Monsters and Vehicles) hit by one or more of those attacks; until the start of your next turn, that enemy unit is pinned. While a unit is pinned, subtract 2 from that unit's Move characteristic and subtract 2 from Charge rolls made for that unit."
            }
        ]
    },
    "Reavers": {
        "stats": {
            "stat_movement": "16\"",
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
                "attacks": "4",
                "skill": "3+",
                "strength": "4",
                "ap": "-1",
                "damage": "1",
                "keywords": "Lance"
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
            }
        ],
        "abilities": [
            {
                "name": "Eviscerating Fly-by",
                "description": "Each time this unit ends a Normal or Advance move, you can select one enemy unit (excluding Monster and Vehicle units) that it moved over during that move, then roll one D6 for each model in this unit: for each 4+, that enemy unit suffers 1 mortal wound."
            },
            {
                "name": "Matchless Swiftness (Pain)",
                "description": "In your Movement phase, when you select this unit to Advance, you can spend 1 Pain token to Empower this unit. While Empowered, each time this unit Advances, do not make an Advance roll. Instead, until the end of the phase, add 8\" to the Move characteristic of models in this unit."
            }
        ]
    },
    "Scourges with Heavy Weapons": {
        "stats": {
            "stat_movement": "14\"",
            "stat_toughness": 3,
            "stat_save": "4+",
            "stat_wounds": 1,
            "stat_leadership": "7+",
            "stat_oc": 1,
            "stat_invuln": "5+",
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
                "skill": "4+",
                "strength": "14",
                "ap": "-4",
                "damage": "D6",
                "keywords": "Assault, Heavy, Melta 3"
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
                "name": "Haywire Blaster",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "2",
                "skill": "4+",
                "strength": "3",
                "ap": "-1",
                "damage": "3",
                "keywords": "Anti-Vehicle 4+, Devastating Wounds, Heavy"
            },
            {
                "name": "Shardcarbine",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "3",
                "skill": "3+",
                "strength": "2",
                "ap": "0",
                "damage": "1",
                "keywords": "Anti-Infantry 3+, Assault"
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
                "name": "Power Weapon",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "3",
                "skill": "3+",
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
                "skill": "3+",
                "strength": "2",
                "ap": "0",
                "damage": "1",
                "keywords": "Anti-Infantry 3+, Assault, Pistol"
            }
        ],
        "abilities": [
            {
                "name": "Airborne Evasion",
                "description": "In your Shooting phase, after this unit has shot, if it is not within Engagement Range of any enemy units, it can make a Normal move of up to 6\". If it does, until the end of the turn, this unit is not eligible to declare a charge."
            },
            {
                "name": "Winged Strike (Pain)",
                "description": "In your Shooting phase, when you select this unit to shoot, you can spend 1 Pain token to Empower this unit. While Empowered, each time a model in this unit makes a range attack, you can re-roll the Hit roll."
            }
        ]
    },
    "Scourges with Shardcarbines": {
        "stats": {
            "stat_movement": "14\"",
            "stat_toughness": 3,
            "stat_save": "4+",
            "stat_wounds": 1,
            "stat_leadership": "7+",
            "stat_oc": 1,
            "stat_invuln": "5+",
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
                "name": "Shardcarbine",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "3",
                "skill": "3+",
                "strength": "2",
                "ap": "0",
                "damage": "1",
                "keywords": "Anti-Infantry 3+, Assault"
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
                "name": "Power Weapon",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "3",
                "skill": "3+",
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
                "skill": "3+",
                "strength": "2",
                "ap": "0",
                "damage": "1",
                "keywords": "Anti-Infantry 3+, Assault, Pistol"
            }
        ],
        "abilities": [
            {
                "name": "Murderous Crossfire",
                "description": "After this unit has shot, select one enemy unit hit by one or more of those attacks. Until the end of the phase, each time a friendly Drukhari unit makes a ranged attack that targets that enemy unit, improve the Armour Penetration characteristic of that attack by 1. The same enemy unit can only be affected by this ability once per turn."
            },
            {
                "name": "Swooping Descent (Pain)",
                "description": "In your Movement phase, you can spend 1 Pain token to Empower this unit. While Empowered, each time a model in this unit is set up on the battlefield using the Deep Strike ability, it can be set up anywhere on the battlefield that is more than 6\" horizontally away from all enemy units. When doing so, if this unit is set up within 8\" of one or more enemy units, until the end of the turn, it is not eligible to declare a charge."
            }
        ]
    },
    "Succubus": {
        "stats": {
            "stat_movement": "8\"",
            "stat_toughness": 3,
            "stat_save": "6+",
            "stat_wounds": 4,
            "stat_leadership": "7+",
            "stat_oc": 1,
            "stat_invuln": "4+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Archite glaive and agoniser",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "7",
                "skill": "2+",
                "strength": "3",
                "ap": "-2",
                "damage": "1",
                "keywords": "Anti-Infantry 3+, Precision"
            }
        ],
        "abilities": [
            {
                "name": "Lithe Agility (Pain)",
                "description": "In your Movement phase when you select this model's unit to Advance, or in your Charge phase before you make a Charge roll for this model's unit, you can spend 1 Pain token to Empower that unit. While that unit is Empowered, you can re-roll Advance and Charge rolls made for that unit."
            },
            {
                "name": "Storm of Blades",
                "description": "While this model is leading a unit, melee weapons equipped by models in that unit have the [Sustained Hits 1] ability."
            },
            {
                "name": "Leader",
                "description": "This model can be attached to the following unit:\n\u25a0 Wyches"
            },
            {
                "name": "Bloody Spectacle",
                "description": "Each time this model makes a melee attack that targets a Character unit, you can re-roll the Hit roll and you can re-roll the Wound roll. Each time this model's unit destroys a Character model, you gain 1CP."
            }
        ]
    },
    "Talos": {
        "stats": {
            "stat_movement": "7\"",
            "stat_toughness": 7,
            "stat_save": "3+",
            "stat_wounds": 7,
            "stat_leadership": "7+",
            "stat_oc": 2,
            "stat_invuln": "6+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Macro-Scalpel",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "5",
                "skill": "3+",
                "strength": "7",
                "ap": "-2",
                "damage": "2",
                "keywords": "-"
            },
            {
                "name": "Talos Ichor Injector",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "1",
                "skill": "2+",
                "strength": "8",
                "ap": "-2",
                "damage": "D6",
                "keywords": "Extra Attacks"
            },
            {
                "name": "Twin Liquifier Gun",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "D6",
                "skill": "N/A",
                "strength": "4",
                "ap": "-1",
                "damage": "1",
                "keywords": "Anti-Infantry 3+, Torrent, Twin-Linked"
            },
            {
                "name": "Chain-flails",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "8",
                "skill": "3+",
                "strength": "6",
                "ap": "-1",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "Talos Gauntlet",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "5",
                "skill": "4+",
                "strength": "9",
                "ap": "-2",
                "damage": "3",
                "keywords": "-"
            },
            {
                "name": "Twin Splinter Cannon",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "3",
                "skill": "3+",
                "strength": "3",
                "ap": "-1",
                "damage": "2",
                "keywords": "Anti-Infantry 3+, Sustained hits 1, Twin-Linked"
            },
            {
                "name": "Twin Haywire Blaster",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "2",
                "skill": "3+",
                "strength": "3",
                "ap": "-1",
                "damage": "3",
                "keywords": "Anti-Vehicle 4+, Devastating Wounds, Twin-Linked"
            },
            {
                "name": "Twin heat lance",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "14",
                "ap": "-4",
                "damage": "D6",
                "keywords": "Assault, Melta 3, Twin-Linked"
            },
            {
                "name": "Stinger Pod",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "2D6",
                "skill": "3+",
                "strength": "5",
                "ap": "0",
                "damage": "1",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Torture Device",
                "description": "Each time this unit destroys an enemy unit, you gain 1 additional Pain token."
            },
            {
                "name": "Devoted to Pain",
                "description": "If a model in this unit is equipped with 2 macro-scalpels, those weapons have the [Twin-Linked] ability."
            },
            {
                "name": "Mindless Killing Machines (Pain)",
                "description": "At the start of the Fight phase, you can spend 1 Pain token to Empower this unit. While Empowered, each time a model in this unit is destroyed by a melee attack, if that model has not fought this phase, roll one D6. On a 2+, do not remove it from play; that destroyed model can fight after the attacking unit has finished making its attacks, and it is then removed from play."
            }
        ]
    },
    "Venom": {
        "stats": {
            "stat_movement": "14\"",
            "stat_toughness": 6,
            "stat_save": "4+",
            "stat_wounds": 6,
            "stat_leadership": "7+",
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
                "ap": "-1",
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
                "keywords": "Anti-Infantry 3+, Assault, Rapid Fire 2, Twin Linked"
            }
        ],
        "abilities": [
            {
                "name": "Aerialists",
                "description": "At the end of the Fight phase, if there are no models currently embarked within this TRANSPORT, you can select one friendly DRUKHARI INFANTRY unit that has 6 or fewer models that is wholly within 6\" of this TRANSPORT (you cannot select a unit that can FLY). Unless that unit is within Engagement Range of one or more enemy units, it can embark within this TRANSPORT. That unit can embark within this TRANSPORT in a turn it disembarked from this TRANSPORT."
            },
            {
                "name": "Rapid Deployment (Pain)",
                "description": "In your Movement phase, when you select this model to Advance, you can spend 1 Pain token to Empower this model. While Empowered, units can disembark from this model after it has Advanced. Units that do so count as having made a Normal move that phase, and cannot declare a charge in the same turn, but can otherwise act normally in the remainder of the turn."
            }
        ]
    },
    "Voidraven Bomber": {
        "stats": {
            "stat_movement": "20+\"",
            "stat_toughness": 9,
            "stat_save": "4+",
            "stat_wounds": 12,
            "stat_leadership": "7+",
            "stat_oc": 0,
            "stat_invuln": "6+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Bladed Wings",
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
                "name": "\u27a4 Voidraven Missiles -  Implosion Missiles",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "D3",
                "skill": "3+",
                "strength": "9",
                "ap": "-2",
                "damage": "3",
                "keywords": "Blast"
            },
            {
                "name": "\u27a4 Voidraven Missiles - Shatterfield Missiles",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "D6",
                "skill": "3+",
                "strength": "7",
                "ap": "-2",
                "damage": "1",
                "keywords": "Blast"
            },
            {
                "name": "Void Lance",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "2",
                "skill": "3+",
                "strength": "14",
                "ap": "-4",
                "damage": "D6+2",
                "keywords": "-"
            },
            {
                "name": "Dark Scythe",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "6",
                "skill": "3+",
                "strength": "8",
                "ap": "-4",
                "damage": "2",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Damaged: 1-4 Wounds Remaining",
                "description": "While this model has 1-4 wounds remaining, each time this model makes an attack, subtract 1 from the Hit roll."
            },
            {
                "name": "Void Mine",
                "description": "At the end of your opponent\u2019s Fight phase, select one visible enemy model (excluding Lone Operative units) within 24\" of this unit, and roll one D6 for each enemy unit within D6\" of that model:\n- For each 4+, that enemy unit suffers D6 mortal wounds."
            },
            {
                "name": "Nowhere to Hide (Pain)",
                "description": "In your Shooting phase, when you select this unit to shoot, you can spend 1 Pain token to Empower this unit. While Empowered, after this unit has shot, select one enemy unit hit by one or more of those attacks. Until the end of the phase, that enemy unit cannot have the Benefit of Cover."
            }
        ]
    },
    "Wracks": {
        "stats": {
            "stat_movement": "7\"",
            "stat_toughness": 4,
            "stat_save": "5+",
            "stat_wounds": 2,
            "stat_leadership": "7+",
            "stat_oc": 2,
            "stat_invuln": "6+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Twin Torturer's Tools",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "2",
                "skill": "3+",
                "strength": "4",
                "ap": "-1",
                "damage": "1",
                "keywords": "Anti-Infantry 4+, Twin-Linked"
            },
            {
                "name": "Torturer's tool",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "2",
                "skill": "3+",
                "strength": "4",
                "ap": "-1",
                "damage": "1",
                "keywords": "Anti-Infantry 4+"
            },
            {
                "name": "Hexrifle",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "8",
                "ap": "-2",
                "damage": "3",
                "keywords": "Heavy, Precision"
            },
            {
                "name": "Liquifier Gun",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "D6",
                "skill": "N/A",
                "strength": "4",
                "ap": "-1",
                "damage": "1",
                "keywords": "Anti-Infantry 3+, Torrent"
            },
            {
                "name": "Ossefactor",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "2",
                "ap": "-2",
                "damage": "2",
                "keywords": "Anti-Infantry 4+, Devastating Wounds"
            },
            {
                "name": "Stinger Pistol",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "2",
                "ap": "0",
                "damage": "1",
                "keywords": "Anti-infantry 2+, Pistol"
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
                "keywords": "Anti-Infantry 3+"
            }
        ],
        "abilities": [
            {
                "name": "Torturer\u2019s Craft",
                "description": "In your Shooting phase and the Fight phase, after this unit has shot or fought, select one enemy unit (excluding Vehicles) hit by one or more of those attacks. That units must take a Battle-shock test."
            },
            {
                "name": "Experimental Enhancements (Pain)",
                "description": "In the Fight phase, when you select this unit to fight, you can spend 1 Pain token to Empower this unit. Each time you do, select one of the following to apply to this unit until the end of the phase:\n\n\u25a0 Melee weapons equipped by non-Character models in this unit have an Attacks characteristic of 3.\n\u25a0 Melee weapons equipped by non-Character models in this unit have an Attacks characteristic of 4 and the [Hazardous] ability."
            }
        ]
    },
    "Wyches": {
        "stats": {
            "stat_movement": "8\"",
            "stat_toughness": 3,
            "stat_save": "6+",
            "stat_wounds": 1,
            "stat_leadership": "7+",
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
                "attacks": "4",
                "skill": "3+",
                "strength": "3",
                "ap": "-1",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "Gladiatorial weapons",
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
                "name": "Blast Pistol",
                "weapon_type": "ranged",
                "range": "6\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "8",
                "ap": "-4",
                "damage": "D3",
                "keywords": "Pistol"
            },
            {
                "name": "Power weapon",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "5",
                "skill": "3+",
                "strength": "3",
                "ap": "-2",
                "damage": "1",
                "keywords": "Anti-Infantry 3+"
            }
        ],
        "abilities": [
            {
                "name": "No Escape",
                "description": "Each time an enemy unit (excluding Monsters and Vehicles) within Engagement Range of one or more units from your army with this ability Falls Back, all models in that enemy unit must take Desperate Escape test. When doing so, if that enemy unit is Battle-shocked, subtract 1 from each of those tests."
            },
            {
                "name": "Acrobatic Gladiators (Pain)",
                "description": "At the start of your Charge phase, you can spend 1 Pain token to Empower this unit. While Empowered, this unit is eligible to declare a charge in a turn in which it Advanced or Fell Back."
            }
        ]
    }
}


class Command(BaseCommand):
    """Refresh core Drukhari stat lines, weapon profiles, and abilities from BSData."""

    help = 'Refresh 11th Edition stats/weapons/abilities for core Drukhari units.'

    def add_arguments(self, parser):
        """Add --dry-run flag."""
        parser.add_argument(
            '--dry-run', action='store_true',
            help='Preview changes without writing to the database.',
        )

    def handle(self, *args, **options):
        """Iterate DRUKHARI_DATASHEETS and refresh each unit's datasheet data."""
        dry_run = options['dry_run']
        updated = 0
        skipped = 0

        with transaction.atomic():
            for name, payload in DRUKHARI_DATASHEETS.items():
                try:
                    unit = UnitType.objects.get(name=name, faction__name='Drukhari')
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

            self.stdout.write('\nCopying cross-faction Harlequins/Corsairs datasheets from Aeldari...')
            for name in DRUKHARI_CROSS_FACTION_COPY:
                src = UnitType.objects.filter(name=name, faction__name='Aeldari').first()
                dst = UnitType.objects.filter(name=name, faction__name='Drukhari').first()
                if not src or not dst:
                    self.stdout.write(self.style.WARNING(
                        f'  SKIP (missing source or target): {name}'
                    ))
                    skipped += 1
                    continue

                src_weapons = list(WeaponProfile.objects.filter(unit_type=src).order_by('order'))
                src_abilities = list(UnitAbility.objects.filter(unit_type=src).order_by('order'))

                if dry_run:
                    self.stdout.write(
                        f"  DRY-RUN -> {name!r} copy from Aeldari "
                        f'{len(src_weapons)}w {len(src_abilities)}a'
                    )
                    updated += 1
                    continue

                for field in STAT_FIELDS:
                    setattr(dst, field, getattr(src, field))
                dst.save(update_fields=STAT_FIELDS)

                WeaponProfile.objects.filter(unit_type=dst).delete()
                for wp in src_weapons:
                    WeaponProfile.objects.create(
                        unit_type=dst, order=wp.order, name=wp.name,
                        weapon_type=wp.weapon_type, range=wp.range,
                        attacks=wp.attacks, skill=wp.skill, strength=wp.strength,
                        ap=wp.ap, damage=wp.damage, keywords=wp.keywords,
                    )

                UnitAbility.objects.filter(unit_type=dst).delete()
                for ab in src_abilities:
                    UnitAbility.objects.create(
                        unit_type=dst, order=ab.order, name=ab.name,
                        description=ab.description,
                    )

                self.stdout.write(
                    f'  OK: {name!r} copied from Aeldari -- {len(src_weapons)} weapons, '
                    f'{len(src_abilities)} abilities'
                )
                updated += 1

            if dry_run:
                self.stdout.write(self.style.WARNING('Dry run -- no changes written.'))
                transaction.set_rollback(True)

        self.stdout.write(self.style.SUCCESS(
            f'\nDone. {updated} updated, {skipped} skipped.'
        ))
