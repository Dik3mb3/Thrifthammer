"""
Management command: seed_necrons_datasheets

Refreshes stat lines, weapon profiles, and abilities for Necrons units
using 11th Edition data sourced from BSData/wh40k-11e ("Necrons.json") --
the same source used by seed_necrons_points.py. Supersedes the older
hand-authored seed_necrons_stats.py -- left in place, not deleted.

Usage:
    python manage.py seed_necrons_datasheets
    python manage.py seed_necrons_datasheets --dry-run

Notes:
- Does NOT touch points_cost or category -- those are handled entirely by
  seed_necrons_points.py. This command only refreshes stat_* fields,
  WeaponProfile rows, and UnitAbility rows.
- Scoped to the 44 units seed_necrons_points.py assigns real values to.
  'Convergence of Dominion' (kept at its stale 60pts, no BSData points
  value) is intentionally out of scope here too.
- Per-field safety rule: a unit's stats/weapons/abilities are only
  overwritten when BSData actually has that data for it. If extraction
  found nothing, the existing DB value/rows are left untouched.
- All 44 active units resolved cleanly -- 0 missing stats/weapons/
  abilities, 0 overlong stat fields.
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from calculators.models import UnitAbility, UnitType, WeaponProfile

# (name -> {stats?, weapons?, abilities?}). Missing keys mean "no data
# found for this field -- leave existing DB data untouched."
NECRONS_DATASHEETS = {
    "Annihilation Barge": {
        "stats": {
            "stat_movement": "10\"",
            "stat_toughness": 8,
            "stat_save": "3+",
            "stat_wounds": 9,
            "stat_leadership": "7+",
            "stat_oc": 3,
            "stat_invuln": "4+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Twin tesla destructor",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "6",
                "skill": "3+",
                "strength": "8",
                "ap": "0",
                "damage": "2",
                "keywords": "Sustained Hits 2, Twin-linked"
            },
            {
                "name": "Armoured bulk",
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
                "name": "Gauss cannon",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "3",
                "skill": "3+",
                "strength": "5",
                "ap": "-2",
                "damage": "2",
                "keywords": "Lethal Hits"
            },
            {
                "name": "Tesla cannon",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "4",
                "skill": "3+",
                "strength": "6",
                "ap": "0",
                "damage": "1",
                "keywords": "Sustained Hits 2"
            }
        ],
        "abilities": [
            {
                "name": "Malevolent Arcing",
                "description": "In your Shooting phase, each time you select a target for this model’s twin tesla destructor, roll one D6 for the target unit and one D6 for every other enemy unit within 3\" of the target unit. On a 5+, the unit being rolled for is struck by arcing energies; after resolving all of this model’s attacks against the target unit, each unit struck by arcing energies suffers D3 mortal wounds."
            }
        ]
    },
    "C'tan Shard of the Deceiver": {
        "stats": {
            "stat_movement": "8\"",
            "stat_toughness": 11,
            "stat_save": "3+",
            "stat_wounds": 16,
            "stat_leadership": "6+",
            "stat_oc": 4,
            "stat_invuln": "4+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Cosmic insanity",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "6",
                "skill": "2+",
                "strength": "6",
                "ap": "-2",
                "damage": "2",
                "keywords": "Anti-CHARACTER 4+, Devastating Wounds, Precision"
            },
            {
                "name": "Golden fists",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "8",
                "skill": "2+",
                "strength": "10",
                "ap": "-3",
                "damage": "3",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Grand Illusion",
                "description": "If your army includes this model, after both players have deployed their armies, select up to three NECRONS units from your army and redeploy them. When doing so, any of those units can be placed in Strategic Reserves, regardless of how many units are already in Strategic Reserves."
            },
            {
                "name": "Necrodermis",
                "description": "Each time an attack is allocated to this model, subtract 1 from the Damage characteristic of that attack."
            },
            {
                "name": "Enslaved Star God",
                "description": "This model cannot be your WARLORD."
            },
            {
                "name": "Distortion Fields (Aura)",
                "description": "While an enemy unit is within 6\" of this unit, it is unravelling. While an enemy unit is unravelling, each time an attack targets that unit, improve the Armour Penetration characteristic of that attack by 1.\nAt the start of each phase, for each Necrons Monster unit from your army, that unit can suffer 3 mortal wounds. If it does, until the end of the phase, the range of that unit’s Distortion Fields Aura ability is increased to 9\"."
            },
            {
                "name": "Lord of Deceit (Aura)",
                "description": "Each time your opponent targets a unit from their army with a Stratagem, if that unit is within 12\" of this model, increase the cost of that use of that Stratagem by 1CP."
            }
        ]
    },
    "C'tan Shard of the Nightbringer": {
        "stats": {
            "stat_movement": "10\"",
            "stat_toughness": 11,
            "stat_save": "3+",
            "stat_wounds": 16,
            "stat_leadership": "6+",
            "stat_oc": 4,
            "stat_invuln": "4+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Gaze of death",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "D3",
                "skill": "2+",
                "strength": "12",
                "ap": "-3",
                "damage": "D6+3",
                "keywords": "-"
            },
            {
                "name": "➤ Scythe of the Nightbringer - strike",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "6",
                "skill": "2+",
                "strength": "14",
                "ap": "-4",
                "damage": "D6+2",
                "keywords": "Devastating Wounds"
            },
            {
                "name": "➤ Scythe of the Nightbringer - sweep",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "14",
                "skill": "2+",
                "strength": "8",
                "ap": "-2",
                "damage": "2",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Drain Life",
                "description": "At the end of the Fight phase, roll one D6 for each enemy unit within 6\" of this model: on a 4+, that enemy unit suffers D3 mortal wounds."
            },
            {
                "name": "Necrodermis",
                "description": "Each time an attack is allocated to this model, subtract 1 from the Damage characteristic of that attack."
            },
            {
                "name": "Enslaved Star God",
                "description": "This model cannot be your WARLORD."
            },
            {
                "name": "Distortion Fields (Aura)",
                "description": "While an enemy unit is within 6\" of this unit, it is unravelling. While an enemy unit is unravelling, each time an attack targets that unit, improve the Armour Penetration characteristic of that attack by 1.\nAt the start of each phase, for each Necrons Monster unit from your army, that unit can suffer 3 mortal wounds. If it does, until the end of the phase, the range of that unit’s Distortion Fields Aura ability is increased to 9\"."
            },
            {
                "name": "Quantum Goad",
                "description": "This model is eligible to declare a charge in a turn in which it Advanced."
            }
        ]
    },
    "C'tan Shard of the Void Dragon": {
        "stats": {
            "stat_movement": "10\"",
            "stat_toughness": 11,
            "stat_save": "3+",
            "stat_wounds": 16,
            "stat_leadership": "6+",
            "stat_oc": 4,
            "stat_invuln": "4+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Spear of the Void Dragon",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "D3",
                "skill": "2+",
                "strength": "8",
                "ap": "-3",
                "damage": "D6+2",
                "keywords": "Anti-VEHICLE 2+"
            },
            {
                "name": "➤ Spear of the Void Dragon - strike",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "5",
                "skill": "2+",
                "strength": "12",
                "ap": "-4",
                "damage": "D6+2",
                "keywords": "Anti-VEHICLE 2+"
            },
            {
                "name": "➤ Spear of the Void Dragon - sweep",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "10",
                "skill": "2+",
                "strength": "8",
                "ap": "-1",
                "damage": "2",
                "keywords": "-"
            },
            {
                "name": "Voltaic storm",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "D6+3",
                "skill": "2+",
                "strength": "7",
                "ap": "-1",
                "damage": "2",
                "keywords": "Blast, Sustained Hits 2"
            },
            {
                "name": "Canoptek tail blades",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "6",
                "skill": "2+",
                "strength": "6",
                "ap": "-1",
                "damage": "1",
                "keywords": "Extra Attacks"
            }
        ],
        "abilities": [
            {
                "name": "Matter Absorption",
                "description": "At the start of your Shooting phase, select one enemy VEHICLE unit within 12\" of this model and roll one D6: on a 2+, that enemy unit suffers D3 mortal wounds and this model regains up to that many lost wounds."
            },
            {
                "name": "Necrodermis",
                "description": "Each time an attack is allocated to this model, subtract 1 from the Damage characteristic of that attack."
            },
            {
                "name": "Enslaved Star God",
                "description": "This model cannot be your WARLORD."
            },
            {
                "name": "Distortion Fields (Aura)",
                "description": "While an enemy unit is within 6\" of this unit, it is unravelling. While an enemy unit is unravelling, each time an attack targets that unit, improve the Armour Penetration characteristic of that attack by 1.\nAt the start of each phase, for each Necrons Monster unit from your army, that unit can suffer 3 mortal wounds. If it does, until the end of the phase, the range of that unit’s Distortion Fields Aura ability is increased to 9\"."
            },
            {
                "name": "Animus Damper",
                "description": "Once per turn, at the start of your opponent’s Shooting phase, select one enemy Vehicle unit visible to the bearer. That unit must take a Leadership test. Until the end of the phase, each time a model in that unit makes an attack, subtract 1 from the Hit roll and, if that Leadership test was failed, subtract 1 from the Wound roll as well."
            }
        ]
    },
    "Canoptek Doomstalker": {
        "stats": {
            "stat_movement": "8\"",
            "stat_toughness": 8,
            "stat_save": "3+",
            "stat_wounds": 12,
            "stat_leadership": "8+",
            "stat_oc": 4,
            "stat_invuln": "4+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Doomsday blaster",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "D6+1",
                "skill": "4+",
                "strength": "14",
                "ap": "-3",
                "damage": "3",
                "keywords": "Blast, Heavy"
            },
            {
                "name": "Doomstalker limbs",
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
                "name": "Twin gauss flayer",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "1",
                "skill": "4+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Lethal Hits, Rapid Fire 1, Twin-linked"
            }
        ],
        "abilities": [
            {
                "name": "Damaged: 1-4 wounds remaining",
                "description": "While this model has 1-4 wounds remaining, each time this model makes an attack, subtract 1 from the Hit roll."
            },
            {
                "name": "Sentinel Construct",
                "description": "Each time you target this unit with the Fire Overwatch Stratagem, while resolving that Stratagem, hits are scored on unmodified Hit rolls of 5+."
            }
        ]
    },
    "Canoptek Reanimator": {
        "stats": {
            "stat_movement": "8\"",
            "stat_toughness": 6,
            "stat_save": "3+",
            "stat_wounds": 6,
            "stat_leadership": "8+",
            "stat_oc": 3,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Atomiser beam",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "3",
                "skill": "4+",
                "strength": "6",
                "ap": "-2",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "Reanimator's claws",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "4+",
                "strength": "5",
                "ap": "0",
                "damage": "1",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Nanoscarab Reanimation Beam (Aura)",
                "description": "While a friendly NECRONS unit is within 3\" of this model, each time that unit’s Reanimation Protocols activate, that unit heals an additional D3 wounds."
            }
        ]
    },
    "Canoptek Spyders": {
        "stats": {
            "stat_movement": "5\"",
            "stat_toughness": 7,
            "stat_save": "3+",
            "stat_wounds": 6,
            "stat_leadership": "8+",
            "stat_oc": 2,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Automaton claws",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "5",
                "skill": "4+",
                "strength": "8",
                "ap": "-2",
                "damage": "2",
                "keywords": "-"
            },
            {
                "name": "Particle beamer",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "D6",
                "skill": "3+",
                "strength": "6",
                "ap": "0",
                "damage": "1",
                "keywords": "Blast, Devastating Wounds"
            }
        ],
        "abilities": [
            {
                "name": "Canoptek Swarm",
                "description": "In your Command phase, select one friendly CANOPTEK SCARAB SWARM unit within 6\" of this unit. One destroyed model is returned to that CANOPTEK SCARAB SWARM unit for each SPYDER model in this unit."
            },
            {
                "name": "Fabricator Claw Array (Aura)",
                "description": "While a friendly NECRONS VEHICLE unit is within 6\" of the bearer, models in that unit have the Feel No Pain 6+ ability."
            },
            {
                "name": "Gloom Prism (Aura)",
                "description": "While a friendly Necrons unit is within 6\" of the bearer, models in that unit have the Feel No Pain 5+ ability against mortal wounds and Psychic Attacks."
            }
        ]
    },
    "Canoptek Wraiths": {
        "stats": {
            "stat_movement": "10\"",
            "stat_toughness": 6,
            "stat_save": "3+",
            "stat_wounds": 4,
            "stat_leadership": "8+",
            "stat_oc": 2,
            "stat_invuln": "4+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Vicious claws",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "4+",
                "strength": "6",
                "ap": "-1",
                "damage": "2",
                "keywords": "-"
            },
            {
                "name": "Transdimensional beamer",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "1",
                "skill": "4+",
                "strength": "4",
                "ap": "-2",
                "damage": "3",
                "keywords": "-"
            },
            {
                "name": "Particle caster",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "3",
                "skill": "4+",
                "strength": "5",
                "ap": "0",
                "damage": "1",
                "keywords": "Devastating Wounds, Pistol"
            },
            {
                "name": "Whip coils",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "8",
                "skill": "4+",
                "strength": "5",
                "ap": "0",
                "damage": "1",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Wraith Form",
                "description": "Each time this unit ends a Normal move, you can select one enemy unit it moved over during that move and roll one D6 for each model in this unit: for each 4+, that enemy unit suffers 1 mortal wound."
            }
        ]
    },
    "Catacomb Command Barge": {
        "stats": {
            "stat_movement": "10\"",
            "stat_toughness": 8,
            "stat_save": "3+",
            "stat_wounds": 9,
            "stat_leadership": "6+",
            "stat_oc": 3,
            "stat_invuln": "4+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Gauss cannon",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "3",
                "skill": "3+",
                "strength": "5",
                "ap": "-2",
                "damage": "2",
                "keywords": "Lethal Hits"
            },
            {
                "name": "Tesla cannon",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "4",
                "skill": "3+",
                "strength": "6",
                "ap": "0",
                "damage": "1",
                "keywords": "Sustained Hits 2"
            },
            {
                "name": "Staff of light",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "3",
                "skill": "2+",
                "strength": "5",
                "ap": "-2",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "Staff of light",
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
                "name": "Overlord's blade",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "2+",
                "strength": "8",
                "ap": "-3",
                "damage": "2",
                "keywords": "Devastating Wounds"
            }
        ],
        "abilities": [
            {
                "name": "Carrier Wave (Aura)",
                "description": "While a friendly NECRONS unit is within 6\" of this model, add 1 to the Objective Control characteristic of models in that unit."
            },
            {
                "name": "Advanced Quantum Shielding",
                "description": "Each time an attack targets this model, if the Strength characteristic of that attack is greater than this model’s Toughness characteristic, subtract 1 from the Wound roll."
            },
            {
                "name": "Resurrection orb",
                "description": "(Once per battle, per unit) At the end of any phase, you can use this ability. If you do, select up to one friendly NECRONS INFANTRY/NECRONS MOUNTED unit within 6\" of this unit. That unit resurrects:\n- When a unit resurrects, that unit’s Reanimation Protocols activate, but that unit heals D6 wounds (instead of D3 wounds). You cannot resurrect more than one unit per turn."
            }
        ]
    },
    "Chronomancer": {
        "stats": {
            "stat_movement": "5\"",
            "stat_toughness": 4,
            "stat_save": "4+",
            "stat_wounds": 4,
            "stat_leadership": "6+",
            "stat_oc": 1,
            "stat_invuln": "4+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Chronomancer's stave",
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
                "name": "Chronomancer's stave",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "D6",
                "skill": "4+",
                "strength": "5",
                "ap": "-1",
                "damage": "1",
                "keywords": "Blast"
            }
        ],
        "abilities": [
            {
                "name": "Support",
                "description": "This model can be attached to the following units:\n■ IMMORTALS\n■ NECRON WARRIORS"
            },
            {
                "name": "Timesplinter Mantle",
                "description": "- This unit has Stealth.\n- Melee attacks that target this unit have -1 to hit rolls."
            },
            {
                "name": "Chronometron",
                "description": "In your Shooting phase, after this model’s unit has shot, if it is not within Engagement Range of any enemy units, that unit can make a Normal move of up to 5\". If it does, until the end of the turn, that unit is not eligible to declare a charge."
            }
        ]
    },
    "Cryptothralls": {
        "stats": {
            "stat_movement": "5\"",
            "stat_toughness": 4,
            "stat_save": "3+",
            "stat_wounds": 3,
            "stat_leadership": "8+",
            "stat_oc": 1,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Scouring eye",
                "weapon_type": "ranged",
                "range": "6\"",
                "attacks": "2",
                "skill": "4+",
                "strength": "5",
                "ap": "-1",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "Scythed limbs",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "4+",
                "strength": "5",
                "ap": "-1",
                "damage": "1",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Bound Creation",
                "description": "While this unit is in the same unit as a CRYPTEK model, that CRYPTEK model has the Feel No Pain 4+ ability."
            },
            {
                "name": "Systematic Vigour",
                "description": "Each time a CRYPTOTHRALL model in this unit is destroyed by a melee attack, if that model has not fought this phase, roll one D6: on a 2+, do not remove it from play. The destroyed model can fight after the attacking model’s unit has finished making its attacks, and it is then removed from play."
            },
            {
                "name": "Cryptek Retinue",
                "description": "At the start of the Declare Battle Formations step, this unit can join one other unit from your army that is being led by a CRYPTEK model (a unit cannot have more than one CRYPTOTHRALLS unit joined to it). If it does, until the end of the battle, every model in this unit counts as being part of that Bodyguard unit, and that Bodyguard unit’s Starting Strength is increased accordingly."
            }
        ]
    },
    "Deathmarks": {
        "stats": {
            "stat_movement": "5\"",
            "stat_toughness": 5,
            "stat_save": "3+",
            "stat_wounds": 1,
            "stat_leadership": "7+",
            "stat_oc": 1,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Synaptic disintegrator",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "5",
                "ap": "-2",
                "damage": "2",
                "keywords": "Heavy, Precision"
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
            }
        ],
        "abilities": [
            {
                "name": "Hyperspace Hunters",
                "description": "Once per turn, in the Reinforcements step of your opponent’s Movement phase, when an enemy unit is set up on the battlefield from Reserves within 18\" of and visible to this unit, this unit can shoot as if it were your Shooting phase, but must only target that enemy unit when doing so, and can only do so if that enemy unit is an eligible target."
            }
        ]
    },
    "Doom Scythe": {
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
                "name": "Heavy death ray",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "3",
                "skill": "3+",
                "strength": "16",
                "ap": "-4",
                "damage": "D6+1",
                "keywords": "Sustained Hits D3"
            },
            {
                "name": "Twin tesla destructor",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "6",
                "skill": "3+",
                "strength": "8",
                "ap": "0",
                "damage": "2",
                "keywords": "Sustained Hits 2, Twin-linked"
            },
            {
                "name": "Armoured bulk",
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
                "name": "Atavistic Instigation",
                "description": "Each time this model targets an enemy unit with its heavy death ray, your opponent must declare if that unit will stand firm or duck for cover:\n■ If it stands firm, when resolving attacks against that unit this phase, a successful unmodified Hit roll of 5+ scores a Critical Hit.\n■ If it ducks for cover, until the start of your next Shooting phase, each time a model in that unit makes an attack, subtract 1 from the Hit roll."
            },
            {
                "name": "Damaged: 1-4 wounds remaining",
                "description": "While this model has 1-4 wounds remaining, each time this model makes an attack, subtract 1 from the Hit roll."
            }
        ]
    },
    "Doomsday Ark": {
        "stats": {
            "stat_movement": "10\"",
            "stat_toughness": 9,
            "stat_save": "3+",
            "stat_wounds": 14,
            "stat_leadership": "7+",
            "stat_oc": 5,
            "stat_invuln": "4+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Doomsday cannon",
                "weapon_type": "ranged",
                "range": "72\"",
                "attacks": "D6+1",
                "skill": "3+",
                "strength": "18",
                "ap": "-4",
                "damage": "4",
                "keywords": "Blast, Heavy"
            },
            {
                "name": "Gauss flayer array",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "5",
                "skill": "3+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Lethal Hits, Rapid Fire 5"
            },
            {
                "name": "Armoured bulk",
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
                "name": "Damaged: 1-5 wounds remaining",
                "description": "While this model has 1-5 wounds remaining, each time this model makes an attack, subtract 1 from the Hit roll."
            },
            {
                "name": "Overwhelming Obliteration",
                "description": "In your Movement phase, if this model Remains Stationary, until the end of the turn, its doomsday cannon has the [DEVASTATING WOUNDS] ability."
            }
        ]
    },
    "Flayed Ones": {
        "stats": {
            "stat_movement": "5\"",
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
                "name": "Flayer claws",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "3+",
                "strength": "4",
                "ap": "-1",
                "damage": "1",
                "keywords": "Sustained Hits 1, Twin-linked"
            }
        ],
        "abilities": [
            {
                "name": "Flesh Hunger",
                "description": "Each time a model in this unit makes a melee attack, if the target of that attack is Below Half-strength, a successful Hit roll scores a Critical Hit."
            }
        ]
    },
    "Ghost Ark": {
        "stats": {
            "stat_movement": "10\"",
            "stat_toughness": 9,
            "stat_save": "3+",
            "stat_wounds": 14,
            "stat_leadership": "7+",
            "stat_oc": 3,
            "stat_invuln": "4+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Gauss flayer array",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "5",
                "skill": "3+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Lethal Hits, Rapid Fire 5"
            },
            {
                "name": "Armoured bulk",
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
                "name": "Repair Barge",
                "description": "Once per turn, just after an enemy unit finishes making its attacks, if one or more friendly NECRON WARRIORS units within 3\" of this model lost one or more wounds as a result of those attacks, this model can use this ability. If it does, select one of those NECRON WARRIORS units; that unit’s Reanimation Protocols activate. The same NECRON WARRIORS unit cannot be selected for this ability more than once per turn."
            }
        ]
    },
    "Hexmark Destroyer": {
        "stats": {
            "stat_movement": "8\"",
            "stat_toughness": 5,
            "stat_save": "3+",
            "stat_wounds": 5,
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
                "attacks": "4",
                "skill": "3+",
                "strength": "5",
                "ap": "0",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "Enmitic disintegrator pistols",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "6",
                "skill": "2+",
                "strength": "6",
                "ap": "-2",
                "damage": "1",
                "keywords": "Ignores Cover, Pistol"
            }
        ],
        "abilities": [
            {
                "name": "Inescapable Death",
                "description": "Once per turn, one unit from your army with this ability can be targeted with the Fire Overwatch Stratagem for 0CP, even if you have already used that Stratagem on a different unit this phase. In addition, each time you target this unit with the Fire Overwatch Stratagem, while resolving that Stratagem, hits are scored on unmodified Hit rolls of 2+."
            },
            {
                "name": "Multi-threat Eliminator",
                "description": "Once per turn, in your opponent's Shooting phase, when an enemy unit makes a ranged attack that targets a friendly NECRONS unit within 3\" of a model with this ability, after that enemy has shot, one model with this ability that is within 3\" of that target can shoot as if it were your Shooting phase, but must target that enemy unit when doing so, and can only do so if that enemy unit is an eligible target."
            }
        ]
    },
    "Illuminor Szeras": {
        "stats": {
            "stat_movement": "8\"",
            "stat_toughness": 8,
            "stat_save": "2+",
            "stat_wounds": 9,
            "stat_leadership": "6+",
            "stat_oc": 3,
            "stat_invuln": "4+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Eldritch lance",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "3",
                "skill": "3+",
                "strength": "9",
                "ap": "-3",
                "damage": "3",
                "keywords": "-"
            },
            {
                "name": "Eldritch lance",
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
                "name": "Impaling legs",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "3+",
                "strength": "6",
                "ap": "-1",
                "damage": "1",
                "keywords": "Extra Attacks"
            }
        ],
        "abilities": [
            {
                "name": "Illuminor",
                "description": "While this model is within 3\" of one or more other friendly NECRONS units, this model has the Lone Operative ability."
            },
            {
                "name": "Mechanical Augmentation (Aura)",
                "description": "While a friendly NECRONS BATTLELINE unit is within 3\" of this model, each time a model in that unit makes an attack, improve the Armour Penetration characteristic of that attack by 1, and each time an attack targets that unit, worsen the Armour Penetration characteristic of that attack by 1."
            },
            {
                "name": "Atomic Energy Manipulator",
                "description": "At the end of the Fight phase, if this model destroyed one or more models this phase, until the end of the battle, add 3\" to the range of its Mechanical Augmentation ability (to a maximum of 12\")."
            }
        ]
    },
    "Immortals": {
        "stats": {
            "stat_movement": "5\"",
            "stat_toughness": 5,
            "stat_save": "3+",
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
                "name": "Gauss blaster",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "2",
                "skill": "3+",
                "strength": "5",
                "ap": "-1",
                "damage": "1",
                "keywords": "Lethal Hits"
            },
            {
                "name": "Tesla carbine",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "2",
                "skill": "3+",
                "strength": "5",
                "ap": "0",
                "damage": "1",
                "keywords": "Assault, Sustained Hits 2"
            }
        ],
        "abilities": [
            {
                "name": "Implacable Eradication",
                "description": "Each time a model in this unit makes an attack, re-roll a Wound roll of 1. If the target of that attack is an enemy unit within range of an objective marker, you can re-roll the Wound roll instead."
            },
            {
                "name": "Tools of Dominion",
                "description": "This unit’s ranged attacks have [RAPID FIRE 1]."
            }
        ]
    },
    "Imotekh the Stormlord": {
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
                "name": "Gauntlet of Fire",
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
                "name": "Staff of the Destroyer",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "3",
                "skill": "2+",
                "strength": "6",
                "ap": "-3",
                "damage": "2",
                "keywords": "-"
            },
            {
                "name": "Staff of the Destroyer",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "2+",
                "strength": "6",
                "ap": "-3",
                "damage": "2",
                "keywords": "Devastating Wounds"
            }
        ],
        "abilities": [
            {
                "name": "Leader",
                "description": "This model can be attached to the following units:\n■ IMMORTALS\n■ LYCHGUARD\n■ NECRON WARRIORS"
            },
            {
                "name": "Grand Strategist",
                "description": "At the start of your Command phase, if this model is on the battlefield, you gain 1CP."
            },
            {
                "name": "Lord of the Storm",
                "description": "Once per battle, at the end of your Command phase, this model can use this ability. If it does, roll one D6 for each enemy unit within 12\" of this model: on a 2-5, that enemy unit suffers D3 mortal wounds; on a 6, that enemy unit suffers D3+3 mortal wounds."
            }
        ]
    },
    "Lokhust Destroyers": {
        "stats": {
            "stat_movement": "8\"",
            "stat_toughness": 6,
            "stat_save": "3+",
            "stat_wounds": 3,
            "stat_leadership": "7+",
            "stat_oc": 2,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Gauss cannon",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "3",
                "skill": "3+",
                "strength": "5",
                "ap": "-2",
                "damage": "2",
                "keywords": "Lethal Hits"
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
            }
        ],
        "abilities": [
            {
                "name": "Hard-wired for Destruction",
                "description": "Each time a model in this unit makes a ranged attack that targets the closest eligible enemy unit, re-roll a Hit roll of 1. If the target of that attack is within range of an objective marker your opponent controls, you can re-roll the Hit roll instead."
            }
        ]
    },
    "Lokhust Heavy Destroyers": {
        "stats": {
            "stat_movement": "8\"",
            "stat_toughness": 6,
            "stat_save": "3+",
            "stat_wounds": 4,
            "stat_leadership": "7+",
            "stat_oc": 2,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Enmitic exterminator",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "6",
                "skill": "3+",
                "strength": "6",
                "ap": "-1",
                "damage": "1",
                "keywords": "Heavy, Rapid Fire 6, Sustained Hits 1"
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
                "name": "Gauss destructor",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "14",
                "ap": "-4",
                "damage": "6",
                "keywords": "Heavy, Lethal Hits"
            }
        ],
        "abilities": [
            {
                "name": "Optimised for Slaughter",
                "description": "Each time a model in this unit makes an attack with an enmitic exterminator that targets a unit (excluding MONSTERS and VEHICLES), re-roll a Wound roll of 1. Each time a model in this unit makes an attack with a gauss destructor against a MONSTER or VEHICLE unit, re-roll a Wound roll of 1."
            }
        ]
    },
    "Lychguard": {
        "stats": {
            "stat_movement": "5\"",
            "stat_toughness": 5,
            "stat_save": "3+",
            "stat_wounds": 2,
            "stat_leadership": "7+",
            "stat_oc": 1,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Warscythe",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "2",
                "skill": "3+",
                "strength": "8",
                "ap": "-3",
                "damage": "2",
                "keywords": "Devastating Wounds"
            },
            {
                "name": "Hyperphase sword",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "3",
                "skill": "3+",
                "strength": "6",
                "ap": "-2",
                "damage": "1",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Guardian Protocols",
                "description": "While a NOBLE model is leading this unit, each time an attack targets this unit, if the Strength characteristic of that attack is greater than the Toughness characteristic of this unit, subtract 1 from the Wound roll."
            },
            {
                "name": "Dispersion Shield",
                "description": "The bearer has a 4+ invulnerable save."
            }
        ]
    },
    "Monolith": {
        "stats": {
            "stat_movement": "8\"",
            "stat_toughness": 13,
            "stat_save": "2+",
            "stat_wounds": 22,
            "stat_leadership": "7+",
            "stat_oc": 8,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Particle whip",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "3D6",
                "skill": "3+",
                "strength": "8",
                "ap": "-1",
                "damage": "2",
                "keywords": "Blast, Devastating Wounds"
            },
            {
                "name": "Portal of exile",
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
                "name": "Death ray",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "12",
                "ap": "-4",
                "damage": "D6+1",
                "keywords": "Sustained Hits D3"
            },
            {
                "name": "Gauss flux arc",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "3",
                "skill": "3+",
                "strength": "6",
                "ap": "-1",
                "damage": "1",
                "keywords": "Lethal Hits, Rapid Fire 3"
            }
        ],
        "abilities": [
            {
                "name": "Damaged: 1-7 wounds remaining",
                "description": "While this model has 1-7 wounds remaining, subtract 4 from its Objective Control characteristic and each time this model makes an attack, subtract 1 from the Hit roll."
            },
            {
                "name": "Eternity Gate",
                "description": "In your movement phase (excluding the first battle round), you can select one friendly NECRONS INFANTRY unit that is either in strategic reserves or on the battlefield (if you select a unit on the battlefield, remove that unit from the battlefield and place it into strategic reserves). That unit can make an ingress move, and must be set up wholly within 6\" of this unit and not engaged with any enemy units. That unit cannot make a charge move this turn."
            }
        ]
    },
    "Necron Warriors": {
        "stats": {
            "stat_movement": "5\"",
            "stat_toughness": 4,
            "stat_save": "4+",
            "stat_wounds": 1,
            "stat_leadership": "7+",
            "stat_oc": 2,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Gauss flayer",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "1",
                "skill": "4+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Lethal Hits, Rapid Fire 1"
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
            },
            {
                "name": "Gauss reaper",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "2",
                "skill": "4+",
                "strength": "4",
                "ap": "-1",
                "damage": "1",
                "keywords": "Lethal Hits"
            }
        ],
        "abilities": [
            {
                "name": "Their Number is Legion",
                "description": "Each time this unit’s Reanimation Protocols activate, you can re-roll the dice to see how many wounds are regenerated."
            },
            {
                "name": "Enlivened Sentinels",
                "description": "This unit has Scouts 5\"."
            }
        ]
    },
    "Nekrosor Ammentar": {
        "stats": {
            "stat_movement": "10\"",
            "stat_toughness": 8,
            "stat_save": "3+",
            "stat_wounds": 9,
            "stat_leadership": "6+",
            "stat_oc": 3,
            "stat_invuln": "4+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Blade tail and whip coils",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "6",
                "skill": "2+",
                "strength": "6",
                "ap": "-1",
                "damage": "1",
                "keywords": "Extra Attacks"
            },
            {
                "name": "Enmitic disintegrators",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "4",
                "skill": "2+",
                "strength": "6",
                "ap": "-2",
                "damage": "1",
                "keywords": "Ignores Cover, Pistol, Sustained Hits 2"
            },
            {
                "name": "Unmaker gauntlet",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "6",
                "skill": "2+",
                "strength": "10",
                "ap": "-3",
                "damage": "3",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Protective Disciples",
                "description": "While this model is within 3\" of one or more other friendly Destroyer Cult units, this model has the Lone Operative ability."
            },
            {
                "name": "Infectious Murder-madness (Aura)",
                "description": "While a friendly Necrons unit (excluding Monster and Titanic units) is within 6\" of this model, each time a model in that unit makes an attack, if that model has the Destroyer Cult keyword or that enemy unit is the closest eligible target, that attack has the [SUSTAINED HITS 1] ability."
            },
            {
                "name": "Prophet of Destruction",
                "description": "Each time this model destroys an enemy unit, select one other friendly Destroyer Cult unit within 9\" of it. Until the end of the phase, each time a model in that unit makes an attack, re-roll a Wound roll of 1."
            },
            {
                "name": "Nullstone Field Generator (Aura)",
                "description": "While a friendly Necrons unit is within 6\" of the bearer, models in that unit have the Feel No Pain 5+ ability against mortal wounds and Psychic Attacks."
            }
        ]
    },
    "Night Scythe": {
        "stats": {
            "stat_movement": "14\"",
            "stat_toughness": 9,
            "stat_save": "3+",
            "stat_wounds": 12,
            "stat_leadership": "7+",
            "stat_oc": 0,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Twin tesla destructor",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "6",
                "skill": "3+",
                "strength": "8",
                "ap": "0",
                "damage": "2",
                "keywords": "Sustained Hits 2, Twin-linked"
            },
            {
                "name": "Armoured bulk",
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
                "name": "Invasion Beams",
                "description": "At the end of the Fight phase, if there are no models currently embarked within this TRANSPORT, you can select one friendly NECRONS INFANTRY unit wholly within 6\" of this TRANSPORT. Unless that unit is within Engagement Range of one or more enemy units, it can embark within this TRANSPORT. That unit can embark within this TRANSPORT in a turn it disembarked from this TRANSPORT."
            },
            {
                "name": "Damaged: 1-4 wounds remaining",
                "description": "While this model has 1-4 wounds remaining, each time this model makes an attack, subtract 1 from the Hit roll."
            },
            {
                "name": "Quantum Invader",
                "description": "This model can be set up in the Reinforcements step of your first, second or third Movement phase, regardless of any mission rules."
            }
        ]
    },
    "Obelisk": {
        "stats": {
            "stat_movement": "8\"",
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
                "name": "Armoured bulk",
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
                "name": "Tesla sphere",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "6",
                "skill": "3+",
                "strength": "7",
                "ap": "0",
                "damage": "1",
                "keywords": "Anti-FLY 4+, Sustained Hits 2"
            }
        ],
        "abilities": [
            {
                "name": "Damaged: 1-8 wounds remaining",
                "description": "While this model has 1-8 wounds remaining, subtract 4 from its Objective Control characteristic and each time this model makes an attack, subtract 1 from the Hit roll."
            },
            {
                "name": "Gravitic Pulse",
                "description": "At the start of your opponent’s Movement phase, you can select one enemy unit within 18\" of and visible to this model. Until the end of the turn, halve the Move characteristic of models in that unit and halve Advance and Charge rolls made for that unit. In addition, if that unit can FLY, until the start of your next Movement phase, roll one D6 each time that unit ends any type of move: on a 4+, that unit suffers D3 mortal wounds."
            },
            {
                "name": "Mortality Shroud (Aura)",
                "description": "In your opponent’s Battle-shock step, if an enemy unit within 8\" of this unit is below starting strength, that enemy unit makes a battle-shock roll."
            }
        ]
    },
    "Ophydian Destroyers": {
        "stats": {
            "stat_movement": "10\"",
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
                "name": "Ophydian hyperphase weapons",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "5",
                "skill": "3+",
                "strength": "4",
                "ap": "-2",
                "damage": "2",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Tunnelling Horrors",
                "description": "At the end of your opponent’s turn, if this unit is unengaged, you can use this ability. If you do:\n- Place this unit in strategic reserves.\n- This unit must make an ingress move in your next Movement phase (including in your first turn).’"
            },
            {
                "name": "Plasmacyte",
                "description": "Once per battle for each Plasmacyte this unit has, when this unit is selected to fight, you can use this ability. If you do, until the end of the phase, melee weapons equipped by models in this unit have the [DEVASTATING WOUNDS] ability."
            }
        ]
    },
    "Orikan the Diviner": {
        "stats": {
            "stat_movement": "5\"",
            "stat_toughness": 4,
            "stat_save": "4+",
            "stat_wounds": 4,
            "stat_leadership": "6+",
            "stat_oc": 1,
            "stat_invuln": "4+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Staff of Tomorrow",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "2",
                "skill": "3+",
                "strength": "4",
                "ap": "-3",
                "damage": "D3",
                "keywords": "Devastating Wounds"
            }
        ],
        "abilities": [
            {
                "name": "Master Chronomancer",
                "description": "While this model is leading a unit, models in that unit have a 4+ invulnerable save."
            },
            {
                "name": "The Stars Are Right",
                "description": "Once per battle, at the start of the Fight phase, this model can use this ability. If it does, until the end of the phase, triple the Attacks and Strength characteristics of this model’s Staff of Tomorrow and every successful Wound roll made for this model’s attacks scores a Critical Wound."
            },
            {
                "name": "Support",
                "description": "This model can be attached to the following units:\n■ IMMORTALS\n■ NECRON WARRIORS"
            }
        ]
    },
    "Overlord": {
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
                "name": "Overlord's blade",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "2+",
                "strength": "8",
                "ap": "-3",
                "damage": "2",
                "keywords": "Devastating Wounds"
            },
            {
                "name": "Tachyon arrow",
                "weapon_type": "ranged",
                "range": "72\"",
                "attacks": "1",
                "skill": "2+",
                "strength": "16",
                "ap": "-5",
                "damage": "D6+2",
                "keywords": "One Shot"
            },
            {
                "name": "Voidscythe",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "3",
                "skill": "3+",
                "strength": "12",
                "ap": "-3",
                "damage": "3",
                "keywords": "Devastating Wounds"
            },
            {
                "name": "Staff of light",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "3",
                "skill": "2+",
                "strength": "5",
                "ap": "-2",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "Staff of light",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "2+",
                "strength": "5",
                "ap": "-2",
                "damage": "1",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Implacable Resilience",
                "description": "Each time an attack is allocated to this model, subtract 1 from that attack’s Damage characteristic."
            },
            {
                "name": "My Will Be Done",
                "description": "Once per battle round, one unit from your army with this ability can use it when its unit is targeted with a Stratagem. If it does, reduce the CP cost of that use of that Stratagem by 1CP."
            },
            {
                "name": "Resurrection orb",
                "description": "‘(Once per battle, per unit) At the end of any phase, you can use this ability. If you do, this unit resurrects:\n- When a unit resurrects, that unit’s Reanimation Protocols activate, but that unit heals D6 wounds (instead of D3 wounds). You cannot resurrect more than one unit per turn."
            }
        ]
    },
    "Overlord with Translocation Shroud": {
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
                "name": "Overlord's blade",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "2+",
                "strength": "8",
                "ap": "-3",
                "damage": "2",
                "keywords": "Devastating Wounds"
            }
        ],
        "abilities": [
            {
                "name": "Translocation Shroud",
                "description": "Each time this model's unit Advances, do not make an Advance roll for it. Instead, until the end of the phase, add 6\" to the Move characteristic of models in that unit. In addition, each time a model in that unit makes a Normal, Advance or Fall Back move, until that move is finished, it can move horizontally through models and terrain features (it cannot finish a move on top of another model or its base)."
            },
            {
                "name": "My Will Be Done",
                "description": "Once per battle round, one unit from your army with this ability can use it when its unit is targeted with a Stratagem. If it does, reduce the CP cost of that use of that Stratagem by 1CP."
            },
            {
                "name": "Resurrection orb",
                "description": "‘(Once per battle, per unit) At the end of any phase, you can use this ability. If you do, this unit resurrects:\n- When a unit resurrects, that unit’s Reanimation Protocols activate, but that unit heals D6 wounds (instead of D3 wounds). You cannot resurrect more than one unit per turn."
            }
        ]
    },
    "Plasmancer": {
        "stats": {
            "stat_movement": "5\"",
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
                "name": "Plasmic lance",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "3",
                "skill": "4+",
                "strength": "7",
                "ap": "-3",
                "damage": "2",
                "keywords": "-"
            },
            {
                "name": "Plasmic lance",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "2",
                "skill": "4+",
                "strength": "7",
                "ap": "-3",
                "damage": "2",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Support",
                "description": "This model can be attached to the following units:\n■ IMMORTALS\n■ NECRON WARRIORS"
            },
            {
                "name": "Harbinger of Destruction",
                "description": "While this model is leading a unit, each time a model in that unit makes a ranged attack, a successful unmodifed Hit roll of 5+ scores a Critical Hit."
            },
            {
                "name": "Living Lightning",
                "description": "In your Shooting phase, select one enemy unit within 18\" of and visible to this model (excluding units with the Lone Operative ability that are not part of an Attached unit and are not within 12\" of this model) and roll four D6: for each 4+, that enemy unit suffers 1 mortal wound."
            }
        ]
    },
    "Psychomancer": {
        "stats": {
            "stat_movement": "5\"",
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
                "name": "Abyssal lance",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "1",
                "skill": "4+",
                "strength": "6",
                "ap": "-3",
                "damage": "3",
                "keywords": "-"
            },
            {
                "name": "Abyssal lance",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "1",
                "skill": "4+",
                "strength": "6",
                "ap": "-3",
                "damage": "3",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Support",
                "description": "This model can be attached to the following units:\n■ IMMORTALS\n■ NECRON WARRIORS"
            },
            {
                "name": "Nightmare Shroud (Aura)",
                "description": "In the Battle-shock step of your opponent's Command phase, if an enemy unit that is below its Starting Strength is within 6\" of this model, that enemy unit must take a Battle-shock test, subtracting 1 from the roll when it does so."
            },
            {
                "name": "Harbinger of Despair",
                "description": "Once per turn, at the start of your Command, Movement, Shooting, Charge or Fight phase, you can select one enemy unit within 18\" of this model. That unit must take a Battle-shock test, subtracting 1 from the roll when it does so."
            }
        ]
    },
    "Royal Warden": {
        "stats": {
            "stat_movement": "5\"",
            "stat_toughness": 5,
            "stat_save": "3+",
            "stat_wounds": 4,
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
                "attacks": "4",
                "skill": "3+",
                "strength": "5",
                "ap": "0",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "Relic gauss blaster",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "2",
                "skill": "3+",
                "strength": "5",
                "ap": "-1",
                "damage": "2",
                "keywords": "Lethal Hits, Rapid Fire 2"
            }
        ],
        "abilities": [
            {
                "name": "Leader",
                "description": "This model can be attached to the following units:\n■ IMMORTALS\n■ NECRON WARRIORS"
            },
            {
                "name": "Adaptive Strategy",
                "description": "This model's unit is eligible to shoot and declare a charge in a turn in which it Fell Back."
            },
            {
                "name": "Engrammatic Logic",
                "description": "Once per battle, at the start of any phase, you can select one friendly NECRONS unit that is Battle-shocked and within 12\" of this model. That unit is no longer Battle-shocked."
            }
        ]
    },
    "Skorpekh Destroyers": {
        "stats": {
            "stat_movement": "8\"",
            "stat_toughness": 6,
            "stat_save": "3+",
            "stat_wounds": 3,
            "stat_leadership": "7+",
            "stat_oc": 2,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Skorpekh hyperphase weapons",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "3+",
                "strength": "7",
                "ap": "-2",
                "damage": "2",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Whirling Onslaught",
                "description": "Each time a model in this unit makes a melee attack, re-roll a Hit roll of 1. If this unit made a Charge move this turn, you can re-roll the Hit roll instead."
            },
            {
                "name": "Plasmacyte",
                "description": "Once per battle for each Plasmacyte this unit has, when this unit is selected to fight, you can use this ability. If you do, until the end of the phase, melee weapons equipped by models in this unit have the [DEVASTATING WOUNDS] ability."
            }
        ]
    },
    "Skorpekh Lord": {
        "stats": {
            "stat_movement": "8\"",
            "stat_toughness": 7,
            "stat_save": "3+",
            "stat_wounds": 7,
            "stat_leadership": "6+",
            "stat_oc": 2,
            "stat_invuln": "4+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Enmitic annihilator",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "2",
                "skill": "2+",
                "strength": "6",
                "ap": "-1",
                "damage": "1",
                "keywords": "Rapid Fire 2"
            },
            {
                "name": "Flensing claw",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "8",
                "skill": "2+",
                "strength": "6",
                "ap": "-1",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "Hyperphase harvester",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "2+",
                "strength": "10",
                "ap": "-3",
                "damage": "3",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Leader",
                "description": "This model can be attached to the following units:\n■ SKORPEKH DESTROYERS"
            },
            {
                "name": "United In Destruction",
                "description": "While this model is leading a unit, melee weapons equipped by models in that unit have the [LETHAL HITS] ability."
            },
            {
                "name": "Crimson Harvest",
                "description": "Each time this model ends a Charge move, select one enemy unit within Engagement Range of this model and roll one D6: on a 2-5, that unit suffers D3 mortal wounds; on a 6, that unit suffers D3+3 mortal wounds."
            }
        ]
    },
    "Szarekh, The Silent King": {
        "stats": {
            "stat_movement": "8\"",
            "stat_toughness": 10,
            "stat_save": "2+",
            "stat_wounds": 16,
            "stat_leadership": "6+",
            "stat_oc": 6,
            "stat_invuln": "4+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Sceptre of Eternal Glory",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "2",
                "skill": "2+",
                "strength": "10",
                "ap": "-3",
                "damage": "3",
                "keywords": "Devastating Wounds"
            },
            {
                "name": "Staff of Stars",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "12",
                "skill": "2+",
                "strength": "6",
                "ap": "-1",
                "damage": "1",
                "keywords": "Indirect Fire"
            },
            {
                "name": "Weapons of the Final Triarch",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "12",
                "skill": "2+",
                "strength": "8",
                "ap": "-3",
                "damage": "2",
                "keywords": "Lethal Hits"
            },
            {
                "name": "Annihilator beam",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "1",
                "skill": "2+",
                "strength": "14",
                "ap": "-4",
                "damage": "6",
                "keywords": "-"
            },
            {
                "name": "Armoured bulk",
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
                "name": "Damaged: 1-6 wounds remaining",
                "description": "While this unit’s Szarekh model has 1-6 wounds remaining, halve the Attacks characteristic of that model’s weapons, and each time this unit makes an attack, subtract 1 from the Hit roll."
            },
            {
                "name": "Voice of the Triarch",
                "description": "At the start of the battle round, select one Triarch ability. Until the start of the next battle round, this unit has that ability."
            },
            {
                "name": "The Silent King (Aura)",
                "description": "While a friendly NECRONS unit is within 6\" of this unit's Szarekh model, improve that unit's Leadership characteristic by 1."
            },
            {
                "name": "Triarchal Menhirs",
                "description": "If this unit’s Szarekh model is destroyed, all of this unit’s remaining Triarchal Menhir models are also destroyed."
            }
        ]
    },
    "Tesseract Vault": {
        "stats": {
            "stat_movement": "8\"",
            "stat_toughness": 12,
            "stat_save": "2+",
            "stat_wounds": 24,
            "stat_leadership": "7+",
            "stat_oc": 8,
            "stat_invuln": "4+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Armoured bulk",
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
                "name": "Tesla sphere",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "6",
                "skill": "3+",
                "strength": "7",
                "ap": "0",
                "damage": "1",
                "keywords": "Sustained Hits 2"
            }
        ],
        "abilities": [
            {
                "name": "Damaged: 1-8 wounds remaining",
                "description": "While this model has 1-8 wounds remaining, subtract 4 from its Objective Control characteristic and you can only select one of the C'tan Powers weapons in your Shooting phase, instead of two."
            },
            {
                "name": "Powers of the C’tan",
                "description": "In your Shooting phase, when this model is selected to shoot, first select up to 2 different C’tan Powers weapons. Until the end of the phase, this model is equipped with those weapons in addition to its other weapons (this model cannot make attacks with any other C’tan Powers weapon you did not select in this way this phase)."
            }
        ]
    },
    "Tomb Blades": {
        "stats": {
            "stat_movement": "12\"",
            "stat_toughness": 5,
            "stat_save": "4+",
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
                "attacks": "1",
                "skill": "4+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "Twin gauss blaster",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "2",
                "skill": "3+",
                "strength": "5",
                "ap": "-1",
                "damage": "1",
                "keywords": "Lethal Hits, Twin-linked"
            },
            {
                "name": "Particle beamer",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "D6",
                "skill": "3+",
                "strength": "5",
                "ap": "0",
                "damage": "1",
                "keywords": "Blast, Devastating Wounds"
            },
            {
                "name": "Twin tesla carbine",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "2",
                "skill": "3+",
                "strength": "5",
                "ap": "0",
                "damage": "1",
                "keywords": "Assault, Sustained Hits 2, Twin-linked"
            }
        ],
        "abilities": [
            {
                "name": "Evasion Engrams",
                "description": "In your Shooting phase, after this unit has shot, it can make a Normal Move of up to 6\". If it does, until the end of the turn, this unit is not eligible to declare a charge."
            },
            {
                "name": "Shieldvanes",
                "description": "The bearer has a Save characteristic of 3+ and a Move characteristic of 8\"."
            },
            {
                "name": "Shadowloom",
                "description": "The bearer has the Stealth ability."
            },
            {
                "name": "Nebuloscope",
                "description": "Ranged weapons equipped by the bearer have the [IGNORES COVER] ability."
            },
            {
                "name": "Recursive Reanimation",
                "description": "When this unit activates its Reanimation Protocols, +1 to the roll."
            }
        ]
    },
    "Transcendent C'tan": {
        "stats": {
            "stat_movement": "8\"",
            "stat_toughness": 11,
            "stat_save": "3+",
            "stat_wounds": 16,
            "stat_leadership": "6+",
            "stat_oc": 4,
            "stat_invuln": "4+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Crackling tendrils",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "8",
                "skill": "2+",
                "strength": "10",
                "ap": "-3",
                "damage": "D6",
                "keywords": "Sustained Hits 1"
            },
            {
                "name": "Seismic assault",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "6",
                "skill": "2+",
                "strength": "8",
                "ap": "-2",
                "damage": "2",
                "keywords": "Assault, Sustained Hits 1"
            }
        ],
        "abilities": [
            {
                "name": "Transdimensional Displacement",
                "description": "In your Movement phase, when this unit is selected to make an advance move, you can use this ability. If you do:\n- That advance move has no maximum distance.\n- This unit can move through all types of model (including enemy models and MONSTER/VEHICLE models).\n- After moving, this unit must be more than 8\" horizontally from all enemy units."
            },
            {
                "name": "C'tan Shard",
                "description": "This model cannot be given Enhancements."
            },
            {
                "name": "Necrodermis",
                "description": "Each time an attack is allocated to this model, subtract 1 from the Damage characteristic of that attack."
            },
            {
                "name": "Enslaved Star God",
                "description": "This model cannot be your WARLORD."
            },
            {
                "name": "Distortion Fields (Aura)",
                "description": "While an enemy unit is within 6\" of this unit, it is unravelling. While an enemy unit is unravelling, each time an attack targets that unit, improve the Armour Penetration characteristic of that attack by 1.\nAt the start of each phase, for each Necrons Monster unit from your army, that unit can suffer 3 mortal wounds. If it does, until the end of the phase, the range of that unit’s Distortion Fields Aura ability is increased to 9\"."
            },
            {
                "name": "Reletavistic Tether",
                "description": "In your turn, when this unit makes an ingress/advance move using its Transdimensional Displacement ability, this unit can end that move more than 6\" horizontally from all enemy units (instead of more than 8\"). When this unit ends that move within 8\" of an enemy unit, this unit is not eligible to declare a charge until the end of the turn."
            }
        ]
    },
    "Trazyn the Infinite": {
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
                "name": "Empathic Obliterator",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "2+",
                "strength": "7",
                "ap": "0",
                "damage": "D3",
                "keywords": "Sustained Hits D3"
            }
        ],
        "abilities": [
            {
                "name": "Leader",
                "description": "This model can be attached to the following units:\n■ IMMORTALS\n■ LYCHGUARD\n■ NECRON WARRIORS"
            },
            {
                "name": "Ancient Collector",
                "description": "While this model is leading a unit, at the end of your Command phase, if that unit is within range of an objective marker you control, that objective marker remains under your control, even if you have no models within range of it, until your opponent controls it at start or end of any turn."
            },
            {
                "name": "Surrogate Hosts",
                "description": "At the start of your Command phase, if this model is on the battlefield, you can select one other friendly NECRONS INFANTRY CHARACTER model on the battlefield (excluding SKORPEKH LORD or EPIC HERO models). The selected model is destroyed (ignoring any rules that are triggered when a model is destroyed) and this model is put\nin its place, with all of its wounds remaining (if the selected model was leading a unit, this model now attaches to that unit as its Leader)."
            }
        ]
    },
    "Triarch Praetorians": {
        "stats": {
            "stat_movement": "10\"",
            "stat_toughness": 5,
            "stat_save": "3+",
            "stat_wounds": 2,
            "stat_leadership": "7+",
            "stat_oc": 1,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Rod of covenant",
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
                "name": "Rod of covenant",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "5",
                "ap": "-2",
                "damage": "2",
                "keywords": "-"
            },
            {
                "name": "Particle caster",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "3",
                "skill": "3+",
                "strength": "5",
                "ap": "0",
                "damage": "1",
                "keywords": "Devastating Wounds, Pistol"
            },
            {
                "name": "Voidblade",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "3+",
                "strength": "5",
                "ap": "-2",
                "damage": "1",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Relentless Combatants",
                "description": "You can re-roll Charge rolls made for this unit, and this unit is eligible to declare a charge in a turn in which it Fell Back."
            }
        ]
    },
    "Triarch Stalker": {
        "stats": {
            "stat_movement": "8\"",
            "stat_toughness": 8,
            "stat_save": "3+",
            "stat_wounds": 12,
            "stat_leadership": "7+",
            "stat_oc": 4,
            "stat_invuln": "4+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Stalker's forelimbs",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "3+",
                "strength": "7",
                "ap": "-1",
                "damage": "3",
                "keywords": "-"
            },
            {
                "name": "➤ Heat ray - dispersed",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "2D6",
                "skill": "N/A",
                "strength": "5",
                "ap": "-1",
                "damage": "1",
                "keywords": "Ignores Cover, Torrent"
            },
            {
                "name": "➤ Heat ray - focused",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "2",
                "skill": "3+",
                "strength": "9",
                "ap": "-4",
                "damage": "D6",
                "keywords": "Melta 4"
            },
            {
                "name": "Particle shredder",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "D6+6",
                "skill": "2+",
                "strength": "7",
                "ap": "0",
                "damage": "1",
                "keywords": "Blast, Devastating Wounds"
            },
            {
                "name": "Heavy gauss cannon array",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "6",
                "skill": "3+",
                "strength": "8",
                "ap": "-2",
                "damage": "2",
                "keywords": "Lethal Hits"
            }
        ],
        "abilities": [
            {
                "name": "Targeting Relay",
                "description": "In your Shooting phase, after this model has shot, select one enemy unit hit by one or more of those attacks. Until the end of the phase, that unit cannot have the Benefit of Cover."
            }
        ]
    }
}


class Command(BaseCommand):
    """Refresh Necrons stat lines, weapon profiles, and abilities from BSData."""

    help = 'Refresh 11th Edition stats/weapons/abilities for Necrons units.'

    def add_arguments(self, parser):
        """Add --dry-run flag."""
        parser.add_argument(
            '--dry-run', action='store_true',
            help='Preview changes without writing to the database.',
        )

    def handle(self, *args, **options):
        """Iterate NECRONS_DATASHEETS and refresh each unit's datasheet data."""
        dry_run = options['dry_run']
        updated = 0
        skipped = 0

        with transaction.atomic():
            for name, payload in NECRONS_DATASHEETS.items():
                try:
                    unit = UnitType.objects.get(name=name, faction__name='Necrons')
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
