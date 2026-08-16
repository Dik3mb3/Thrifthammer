"""
Management command: seed_world_eaters_datasheets

Refreshes stat lines, weapon profiles, and abilities for World Eaters
units using 11th Edition data sourced from BSData/wh40k-11e ("Chaos -
World Eaters.json") -- the same source used by
seed_world_eaters_points.py.

Usage:
    python manage.py seed_world_eaters_datasheets
    python manage.py seed_world_eaters_datasheets --dry-run

Notes:
- Does NOT touch points_cost or category -- those are handled entirely by
  seed_world_eaters_points.py. This command only refreshes stat_* fields,
  WeaponProfile rows, and UnitAbility rows.
- Scope is all 30 real-unit active World Eaters rows (excludes the
  Combat Patrol bundle, which correctly has no BSData match).
- Per-field safety rule: a unit\'s stats/weapons/abilities are only
  overwritten when BSData actually has that data for it. If extraction
  found nothing, the existing DB value/rows are left untouched.
- All 30 real units resolved cleanly on the first pass -- 0 missing
  stats, weapons, or abilities, 0 overlong stat fields. Last faction in
  the whole 11e Army Calculator migration project.
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from calculators.models import UnitAbility, UnitType, WeaponProfile

# (name -> {stats?, weapons?, abilities?}). Missing keys mean "no data
# found for this field -- leave existing DB data untouched."
WORLD_EATERS_DATASHEETS = {
    "Bloodcrushers of Khorne": {
        "stats": {
            "stat_movement": "10\"",
            "stat_toughness": 7,
            "stat_save": "3+",
            "stat_wounds": 4,
            "stat_leadership": "7+",
            "stat_oc": 2,
            "stat_invuln": "5+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Hellblade",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "2",
                "skill": "3+",
                "strength": "5",
                "ap": "-2",
                "damage": "2",
                "keywords": "-"
            },
            {
                "name": "Bladed horn",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "4+",
                "strength": "6",
                "ap": "-1",
                "damage": "1",
                "keywords": "Extra Attacks, Lance"
            }
        ],
        "abilities": [
            {
                "name": "Brass Stampede",
                "description": "Each time this unit ends a Charge move, select one enemy unit within Engagement Range of this unit and roll one D6 for each model in this unit: for each 4+, that enemy unit suffers D3 mortal wounds."
            },
            {
                "name": "Instrument of Chaos",
                "description": "Add 1 to Charge rolls made for the bearer’s unit."
            },
            {
                "name": "Daemonic Icon",
                "description": "Models in the bearer’s unit have a Leadership characteristic of 6+."
            }
        ]
    },
    "Bloodletters of Khorne": {
        "stats": {
            "stat_movement": "8\"",
            "stat_toughness": 4,
            "stat_save": "7+",
            "stat_wounds": 1,
            "stat_leadership": "7+",
            "stat_oc": 1,
            "stat_invuln": "5+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Hellblade",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "2",
                "skill": "3+",
                "strength": "5",
                "ap": "-2",
                "damage": "2",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Bane of Cowards",
                "description": "Each time an enemy unit (excluding Monsters and Vehicles) within Engagement Range of one or more units from your army with this ability Falls Back, models in that enemy unit must take Desperate Escape tests. When doing so, if that enemy unit is also Battle-shocked, subtract 1 from each of those Desperate Escape tests."
            },
            {
                "name": "Instrument of Chaos",
                "description": "Add 1 to Charge rolls made for the bearer’s unit."
            },
            {
                "name": "Daemonic Icon",
                "description": "Models in the bearer’s unit have a Leadership characteristic of 6+."
            }
        ]
    },
    "Bloodthirster": {
        "stats": {
            "stat_movement": "12\"",
            "stat_toughness": 11,
            "stat_save": "3+",
            "stat_wounds": 18,
            "stat_leadership": "6+",
            "stat_oc": 5,
            "stat_invuln": "4+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Hellfire breath",
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
                "name": "➤ Great axe of Khorne - strike",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "7",
                "skill": "2+",
                "strength": "16",
                "ap": "-4",
                "damage": "D6+2",
                "keywords": "-"
            },
            {
                "name": "➤ Great axe of Khorne - sweep",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "14",
                "skill": "2+",
                "strength": "10",
                "ap": "-2",
                "damage": "2",
                "keywords": "-"
            },
            {
                "name": "➤ Axe of Khorne - strike",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "8",
                "skill": "2+",
                "strength": "14",
                "ap": "-4",
                "damage": "D3+1",
                "keywords": "-"
            },
            {
                "name": "➤ Axe of Khorne - sweep",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "16",
                "skill": "2+",
                "strength": "8",
                "ap": "-2",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "Bloodflail",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "1",
                "skill": "2+",
                "strength": "16",
                "ap": "-3",
                "damage": "D6+1",
                "keywords": "Devastating Wounds"
            },
            {
                "name": "Lash of Khorne",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "9",
                "skill": "2+",
                "strength": "8",
                "ap": "-1",
                "damage": "2",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Daemon Lord of Khorne (Aura)",
                "description": "While a friendly Blood Legions unit is within 6\" of this model, each time a model in that unit makes a melee attack, add 1 to the Hit roll."
            },
            {
                "name": "Relentless Carnage",
                "description": "At the end of the Fight phase, you can select one enemy unit within Engagement Range of this model and roll eight D6: for each 4+, that enemy unit suffers 1 mortal wound."
            },
            {
                "name": "Damaged: 1-6 wounds remaining",
                "description": "While this model has 1-6 wounds remaining, each time this model makes an attack, subtract 1 from the Hit roll."
            }
        ]
    },
    "Chaos Land Raider": {
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
                "attacks": "9",
                "skill": "3+",
                "strength": "8",
                "ap": "0",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "Soulshatter lascannon",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "2",
                "skill": "4+",
                "strength": "12",
                "ap": "-3",
                "damage": "D6+1",
                "keywords": "Rapid Fire 2"
            },
            {
                "name": "Havoc launcher",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "D6",
                "skill": "4+",
                "strength": "5",
                "ap": "0",
                "damage": "1",
                "keywords": "Blast"
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
                "keywords": "Rapid Fire 2, Sustained Hits 1, Twin-linked"
            },
            {
                "name": "Combi-bolter",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "2",
                "skill": "4+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Rapid Fire 4"
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
                "name": "Assault Ramp",
                "description": "Each time a unit disembarks from this model after it has made a Normal move, that unit is still eligible to declare a charge this turn."
            },
            {
                "name": "Damaged: 1-5 wounds remaining",
                "description": "While this model has 1-5 wounds remaining, each time this model makes an attack, subtract 1 from the Hit roll."
            }
        ]
    },
    "Chaos Predator Annihilator": {
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
                "name": "Predator twin lascannon",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "1",
                "skill": "4+",
                "strength": "14",
                "ap": "-3",
                "damage": "D6+1",
                "keywords": "Rapid Fire 2, Twin-linked"
            },
            {
                "name": "Armoured tracks",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "6",
                "skill": "3+",
                "strength": "6",
                "ap": "0",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "Havoc launcher",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "D6",
                "skill": "4+",
                "strength": "5",
                "ap": "0",
                "damage": "1",
                "keywords": "Blast"
            },
            {
                "name": "Combi-bolter",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "2",
                "skill": "4+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Rapid Fire 4"
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
                "name": "Heavy bolter",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "3",
                "skill": "4+",
                "strength": "5",
                "ap": "-1",
                "damage": "2",
                "keywords": "Rapid Fire 2, Sustained Hits 1"
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
            }
        ],
        "abilities": [
            {
                "name": "Blood-hungry Annihilator",
                "description": "Each time this model makes a ranged attack that targets the closest eligible Monster or Vehicle target within 18\", you can re-roll the Wound roll and you can re-roll the Damage roll."
            }
        ]
    },
    "Chaos Predator Destructor": {
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
                "name": "Predator autocannon",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "4",
                "skill": "4+",
                "strength": "9",
                "ap": "-1",
                "damage": "3",
                "keywords": "Rapid Fire 6"
            },
            {
                "name": "Armoured tracks",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "6",
                "skill": "3+",
                "strength": "6",
                "ap": "0",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "Havoc launcher",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "D6",
                "skill": "4+",
                "strength": "5",
                "ap": "0",
                "damage": "1",
                "keywords": "Blast"
            },
            {
                "name": "Combi-bolter",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "2",
                "skill": "4+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Rapid Fire 4"
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
                "name": "Heavy bolter",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "3",
                "skill": "4+",
                "strength": "5",
                "ap": "-1",
                "damage": "2",
                "keywords": "Rapid Fire 2, Sustained Hits 1"
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
            }
        ],
        "abilities": [
            {
                "name": "Punishing Suppression",
                "description": "In your Shooting phase, after this model has shot, select one enemy unit hit by one or more of those attacks (excluding Monsters and Vehicles*). Until the start of your next turn, that enemy unit is suppressed. While a unit is suppressed, each time a model in that unit makes an attack, subtract 1 from the Hit roll."
            }
        ]
    },
    "Chaos Rhino": {
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
                "name": "Armoured tracks",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "6",
                "skill": "3+",
                "strength": "6",
                "ap": "0",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "Combi-bolter",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "2",
                "skill": "4+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Rapid Fire 4"
            },
            {
                "name": "Havoc launcher",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "D6",
                "skill": "4+",
                "strength": "5",
                "ap": "0",
                "damage": "1",
                "keywords": "Blast"
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
                "name": "Meet Any Challenge",
                "description": "In your opponent's Movement phase, each time an enemy unit is set up or ends a Normal, Advance or Fall Back move within 8\" of this model, any units embarked within it can disembark."
            }
        ]
    },
    "Chaos Spawn": {
        "stats": {
            "stat_movement": "10\"",
            "stat_toughness": 5,
            "stat_save": "4+",
            "stat_wounds": 4,
            "stat_leadership": "7+",
            "stat_oc": 1,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Hideous Mutations",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "D6+4",
                "skill": "4+",
                "strength": "5",
                "ap": "-1",
                "damage": "2",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "To Slake Its Rage",
                "description": "This unit is eligible to declare a charge in a turn in which it Advanced."
            }
        ]
    },
    "Chaos Terminators": {
        "stats": {
            "stat_movement": "7\"",
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
                "name": "Accursed weapon",
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
                "ap": "-3",
                "damage": "2",
                "keywords": "Anti-VEHICLE 3+"
            },
            {
                "name": "Combi-bolter",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "2",
                "skill": "4+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Rapid Fire 4"
            },
            {
                "name": "Paired accursed weapons",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "5",
                "skill": "3+",
                "strength": "5",
                "ap": "-2",
                "damage": "1",
                "keywords": "Twin-linked"
            },
            {
                "name": "Reaper autocannon",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "4",
                "skill": "4+",
                "strength": "7",
                "ap": "-1",
                "damage": "1",
                "keywords": "Devastating Wounds, Rapid Fire 2, Sustained Hits 1"
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
                "name": "Bloody Fury",
                "description": "- This unit’s ranged attacks that target the closest eligible target can re-roll hit rolls.\n- When this unit declares a charge, you can use this part of this ability.\nIf you do:\n-- This unit can re-roll that charge roll.\n-- This unit must end that charge move engaged with the closest charge target."
            },
            {
                "name": "Sanctified in Slaughter",
                "description": "This unit has +1OC."
            },
            {
                "name": "Gore-stained Veterans",
                "description": "This unit’s melee attacks have +1 WS."
            }
        ]
    },
    "Daemon Prince of Khorne": {
        "stats": {
            "stat_movement": "10\"",
            "stat_toughness": 10,
            "stat_save": "2+",
            "stat_wounds": 10,
            "stat_leadership": "6+",
            "stat_oc": 3,
            "stat_invuln": "4+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "➤ Hellforged weapons - strike",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "8",
                "skill": "2+",
                "strength": "8",
                "ap": "-2",
                "damage": "3",
                "keywords": "-"
            },
            {
                "name": "➤ Hellforged weapons - sweep",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "16",
                "skill": "2+",
                "strength": "6",
                "ap": "-1",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "Infernal cannon",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "3",
                "skill": "3+",
                "strength": "5",
                "ap": "-1",
                "damage": "2",
                "keywords": "Rapid Fire 1"
            }
        ],
        "abilities": [
            {
                "name": "Lord of Murder",
                "description": "While this model is within 3\" of one or more friendly World Eaters Infantry units, this model has the Lone Operative ability."
            },
            {
                "name": "Devastating Assault",
                "description": "Each time this model makes a Charge move, until the end of the turn, its hellforged weapons have the [DEVASTATING WOUNDS] ability."
            },
            {
                "name": "Direct the Slaughter",
                "description": "Once per battle round, one model from your army with this ability can use it when a friendly World Eaters unit within 12\" of this model is targeted with a Stratagem. If it does, reduce the CP cost of that Stratagem by 1CP."
            }
        ]
    },
    "Daemon Prince of Khorne with wings": {
        "stats": {
            "stat_movement": "14\"",
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
                "name": "➤ Hellforged weapons - strike",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "8",
                "skill": "2+",
                "strength": "8",
                "ap": "-2",
                "damage": "3",
                "keywords": "-"
            },
            {
                "name": "➤ Hellforged weapons - sweep",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "16",
                "skill": "2+",
                "strength": "6",
                "ap": "-1",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "Infernal cannon",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "3",
                "skill": "3+",
                "strength": "5",
                "ap": "-1",
                "damage": "2",
                "keywords": "Rapid Fire 1"
            }
        ],
        "abilities": [
            {
                "name": "Bloodied Terror",
                "description": "At the start of the Fight phase, each enemy unit within Engagement Range of this model must take a Battle-shock test, subtracting 1 if that enemy unit is Below Half-strength."
            },
            {
                "name": "Swooping Predator",
                "description": "Each time this model ends a Normal or Advance move, you can select one enemy unit that it moved over during that move and roll 6 D6: for each 4+, that enemy unit suffers 1 mortal wound."
            }
        ]
    },
    "Defiler": {
        "stats": {
            "stat_movement": "14\"",
            "stat_toughness": 11,
            "stat_save": "3+",
            "stat_wounds": 18,
            "stat_leadership": "6+",
            "stat_oc": 5,
            "stat_invuln": "5+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Shearing claws - strike",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "6",
                "skill": "3+",
                "strength": "16",
                "ap": "-3",
                "damage": "D6+1",
                "keywords": "-"
            },
            {
                "name": "Shearing claws - sweep",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "12",
                "skill": "3+",
                "strength": "6",
                "ap": "-2",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "➤ Heavy missile launcher - frag",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "2D6",
                "skill": "4+",
                "strength": "5",
                "ap": "-1",
                "damage": "1",
                "keywords": "Blast, Rapid Fire 3"
            },
            {
                "name": "➤ Heavy missile launcher - krak",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "2",
                "skill": "4+",
                "strength": "10",
                "ap": "-2",
                "damage": "D6+1",
                "keywords": "Rapid Fire 1"
            },
            {
                "name": "Electroscourge",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "7",
                "skill": "3+",
                "strength": "12",
                "ap": "-2",
                "damage": "2",
                "keywords": "Extra Attacks, Sustained Hits 2"
            },
            {
                "name": "Hades lascannon",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "2",
                "skill": "4+",
                "strength": "12",
                "ap": "-3",
                "damage": "D6+1",
                "keywords": "Rapid Fire 1"
            },
            {
                "name": "Heavy reaper autocannon",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "4",
                "skill": "4+",
                "strength": "9",
                "ap": "-1",
                "damage": "3",
                "keywords": "Devastating Wounds, Rapid Fire 2, Sustained Hits 1"
            },
            {
                "name": "Hades battle cannon",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "D6+3",
                "skill": "4+",
                "strength": "10",
                "ap": "-1",
                "damage": "3",
                "keywords": "Blast, Rapid Fire 3"
            },
            {
                "name": "Ectoplasma destructor",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "D6",
                "skill": "4+",
                "strength": "12",
                "ap": "-3",
                "damage": "3",
                "keywords": "Blast, Rapid Fire 2"
            },
            {
                "name": "Heavy baleflamer",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "D6+3",
                "skill": "N/A",
                "strength": "7",
                "ap": "-2",
                "damage": "2",
                "keywords": "Ignores Cover, Torrent"
            },
            {
                "name": "Excruciator cannon",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "6",
                "skill": "4+",
                "strength": "6",
                "ap": "-1",
                "damage": "2",
                "keywords": "Rapid Fire 3"
            },
            {
                "name": "Magma cutter",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "2",
                "skill": "4+",
                "strength": "9",
                "ap": "-4",
                "damage": "D6",
                "keywords": "Melta 2, Rapid Fire 1"
            }
        ],
        "abilities": [
            {
                "name": "Scuttling Walker",
                "description": "Each time this unit makes a Normal, Advance or Fall Back move, it can move through models (excluding Titanic models) and terrain features. When doing so, it can move within Engagement Range of enemy models, but cannot end that move within Engagement Range of them, and any Desperate Escape test is automatically passed."
            },
            {
                "name": "Unleash Wrath",
                "description": "At the end of your opponent's Movement phase, you can select one enemy unit that was set up on the battlefield within 12\" of this model; this model can then either:\n- Shoot at that unit, but only if it is an eligible target.\n- Declare a charge against that unit (note that even if this charge is successful, this model does not receive any Charge bonus this turn)."
            },
            {
                "name": "Terror of Khorne",
                "description": "At the start of the Fight phase, you can select one enemy unit engaged with this unit. That enemy unit makes a battle-shock roll, with -1 to that battle-shock roll. You cannot select the same enemy unit for this effect more than once per phase."
            }
        ]
    },
    "Flesh Hounds of Khorne": {
        "stats": {
            "stat_movement": "12\"",
            "stat_toughness": 4,
            "stat_save": "7+",
            "stat_wounds": 2,
            "stat_leadership": "7+",
            "stat_oc": 1,
            "stat_invuln": "5+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Gore-drenched fangs",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "3",
                "skill": "3+",
                "strength": "5",
                "ap": "-1",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "Burning roar",
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
                "name": "Hunters from the Warp",
                "description": "At the end of your opponent’s turn, if this unit is not within Engagement Range of one or more enemy units, you can remove it from the battlefield and place it into Strategic Reserves."
            },
            {
                "name": "Collar of Khorne",
                "description": "The bearer has the Feel No Pain 3+ ability against Psychic Attacks."
            }
        ]
    },
    "Forgefiend": {
        "stats": {
            "stat_movement": "10\"",
            "stat_toughness": 10,
            "stat_save": "3+",
            "stat_wounds": 12,
            "stat_leadership": "6+",
            "stat_oc": 3,
            "stat_invuln": "5+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Ectoplasma cannon",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "D3",
                "skill": "4+",
                "strength": "10",
                "ap": "-3",
                "damage": "3",
                "keywords": "Blast, Rapid Fire 1"
            },
            {
                "name": "Hades autocannon",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "6",
                "skill": "4+",
                "strength": "8",
                "ap": "-1",
                "damage": "2",
                "keywords": "Rapid Fire 4"
            },
            {
                "name": "Forgefiend claws",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "6",
                "skill": "3+",
                "strength": "6",
                "ap": "0",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "Forgefiend jaws",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "8",
                "skill": "3+",
                "strength": "7",
                "ap": "-1",
                "damage": "2",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Furious Onslaught",
                "description": "Each time this model makes a ranged attack that targets the closest eligible target within 18\", you can re-roll the Hit roll."
            },
            {
                "name": "Terror of Khorne",
                "description": "At the start of the Fight phase, you can select one enemy unit engaged with this unit. That enemy unit makes a battle-shock roll, with -1 to that battle-shock roll. You cannot select the same enemy unit for this effect more than once per phase."
            }
        ]
    },
    "Helbrute": {
        "stats": {
            "stat_movement": "9\"",
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
                "name": "Close combat weapon",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "6",
                "skill": "3+",
                "strength": "6",
                "ap": "0",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "Helbrute fist",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "6",
                "skill": "3+",
                "strength": "12",
                "ap": "-2",
                "damage": "3",
                "keywords": "-"
            },
            {
                "name": "Combi-bolter",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "2",
                "skill": "4+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Rapid Fire 4"
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
                "name": "➤ Missile launcher - frag",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "D6",
                "skill": "4+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Blast, Rapid Fire 3"
            },
            {
                "name": "➤ Missile launcher - krak",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "1",
                "skill": "4+",
                "strength": "9",
                "ap": "-2",
                "damage": "D6",
                "keywords": "Rapid Fire 1"
            },
            {
                "name": "Helbrute hammer",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "6",
                "skill": "4+",
                "strength": "14",
                "ap": "-3",
                "damage": "D6+1",
                "keywords": "-"
            },
            {
                "name": "Power scourge",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "10",
                "skill": "3+",
                "strength": "7",
                "ap": "-1",
                "damage": "2",
                "keywords": "-"
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
                "keywords": "Melta 2, Rapid Fire 1"
            },
            {
                "name": "Twin autocannon",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "2",
                "skill": "4+",
                "strength": "9",
                "ap": "-1",
                "damage": "3",
                "keywords": "Rapid Fire 2, Twin-linked"
            },
            {
                "name": "Plasma cannon",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "D3",
                "skill": "4+",
                "strength": "8",
                "ap": "-3",
                "damage": "3",
                "keywords": "Blast, Hazardous, Rapid Fire D3"
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
                "keywords": "Rapid Fire 2, Sustained Hits 1, Twin-linked"
            },
            {
                "name": "Twin lascannon",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "1",
                "skill": "4+",
                "strength": "12",
                "ap": "-3",
                "damage": "D6+1",
                "keywords": "Rapid Fire 1, Twin-linked"
            }
        ],
        "abilities": [
            {
                "name": "Frenzy",
                "description": "(Once per turn, per unit) In the Fight phase, when an enemy unit targets this unit, after that unit has resolved its attacks, you can use this ability. If you do, this unit is eligible to fight (even if it has already fought this phase) and must be selected to fight next."
            },
            {
                "name": "Devoted to Destruction",
                "description": "If this model is equipped with 2 melee weapons in addition to its close combat weapon, add 2 to the Attacks characteristic of those two weapons."
            }
        ]
    },
    "Heldrake": {
        "stats": {
            "stat_movement": "12\"",
            "stat_toughness": 9,
            "stat_save": "3+",
            "stat_wounds": 12,
            "stat_leadership": "6+",
            "stat_oc": None,
            "stat_invuln": "5+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Heldrake claws",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "6",
                "skill": "3+",
                "strength": "7",
                "ap": "-1",
                "damage": "2",
                "keywords": "Anti-FLY 2+, Devastating Wounds"
            },
            {
                "name": "Baleflamer",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "D6+3",
                "skill": "N/A",
                "strength": "6",
                "ap": "-1",
                "damage": "2",
                "keywords": "Ignores Cover, Torrent"
            },
            {
                "name": "Hades autocannon",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "6",
                "skill": "4+",
                "strength": "8",
                "ap": "-1",
                "damage": "2",
                "keywords": "Rapid Fire 4"
            }
        ],
        "abilities": [
            {
                "name": "Airborne Predator",
                "description": "Each time this model makes an attack that targets a unit that can Fly, add 1 to the Hit roll."
            },
            {
                "name": "Terror of Khorne",
                "description": "At the start of the Fight phase, you can select one enemy unit engaged with this unit. That enemy unit makes a battle-shock roll, with -1 to that battle-shock roll. You cannot select the same enemy unit for this effect more than once per phase."
            }
        ]
    },
    "Khorne Lord of Skulls": {
        "stats": {
            "stat_movement": "12\"",
            "stat_toughness": 13,
            "stat_save": "3+",
            "stat_wounds": 24,
            "stat_leadership": "6+",
            "stat_oc": 8,
            "stat_invuln": "5+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "➤ Great cleaver of Khorne - strike",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "6",
                "skill": "3+",
                "strength": "16",
                "ap": "-4",
                "damage": "8",
                "keywords": "-"
            },
            {
                "name": "➤ Great cleaver of Khorne - sweep",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "18",
                "skill": "3+",
                "strength": "8",
                "ap": "-2",
                "damage": "2",
                "keywords": "-"
            },
            {
                "name": "Hades gatling cannon",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "12",
                "skill": "4+",
                "strength": "8",
                "ap": "-2",
                "damage": "2",
                "keywords": "Rapid Fire 6, Sustained Hits 1"
            },
            {
                "name": "Skullhurler",
                "weapon_type": "ranged",
                "range": "60\"",
                "attacks": "2D6",
                "skill": "4+",
                "strength": "14",
                "ap": "-3",
                "damage": "3",
                "keywords": "Rapid Fire 3"
            },
            {
                "name": "Gorestorm cannon",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "D6+3",
                "skill": "4+",
                "strength": "10",
                "ap": "-2",
                "damage": "3",
                "keywords": "Blast, Rapid Fire 3"
            },
            {
                "name": "Daemongore cannon",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "D6",
                "skill": "4+",
                "strength": "14",
                "ap": "-4",
                "damage": "D6+2",
                "keywords": "Blast, Rapid Fire 3"
            },
            {
                "name": "Ichor cannon",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "2D6",
                "skill": "4+",
                "strength": "7",
                "ap": "-2",
                "damage": "2",
                "keywords": "Blast, Rapid Fire 4"
            }
        ],
        "abilities": [
            {
                "name": "Idol of Blessed Blood",
                "description": "At the start of the battle round, if this unit is on the battlefield, when you make a Blessings of Khorne roll, roll one additional D6."
            },
            {
                "name": "Damaged: 1-8 wounds remaining",
                "description": "While this model has 1-8 wounds remaining, subtract 4 from this model’s Objective Control characteristic and each time this model makes an attack, subtract 1 from the Hit roll."
            },
            {
                "name": "Terror of Khorne",
                "description": "At the start of the Fight phase, you can select one enemy unit engaged with this unit. That enemy unit makes a battle-shock roll, with -1 to that battle-shock roll. You cannot select the same enemy unit for this effect more than once per phase."
            }
        ]
    },
    "Kill Team: Goremongers (World Eaters)": {
        "stats": {
            "stat_movement": "9\"",
            "stat_toughness": 4,
            "stat_save": "6+",
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
                "name": "Chainblade",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "3",
                "skill": "4+",
                "strength": "3",
                "ap": "0",
                "damage": "1",
                "keywords": "Lance"
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
                "name": "Blood harpoon",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "1",
                "skill": "4+",
                "strength": "5",
                "ap": "-1",
                "damage": "2",
                "keywords": "Assault, Sustained Hits D3"
            }
        ],
        "abilities": [
            {
                "name": "Loping Speed",
                "description": "In your opponent's Movement phase, if an enemy unit ends a move within 8\" of this unit, if this unit is not within Engagement Range of one or more enemy units, this unit can make a Normal move of up to D6\"."
            }
        ]
    },
    "Master of Executions": {
        "stats": {
            "stat_movement": "8\"",
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
                "name": "Axe of dismemberment",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "5",
                "skill": "2+",
                "strength": "7",
                "ap": "-2",
                "damage": "2",
                "keywords": "Devastating Wounds, Precision"
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
            }
        ],
        "abilities": [
            {
                "name": "Leader",
                "description": "This model can be attached to the following unit: Khorne Berzerkers"
            },
            {
                "name": "A Worthy Skull",
                "description": "Each time this model makes a melee attack that targets a Character unit, you can re-roll the Hit roll and you can re-roll the Wound roll. Each time this model's unit destroys a Character model, you gain 1CP."
            },
            {
                "name": "Forwards, For Blood!",
                "description": "While this model is leading a unit, you can re-roll Advance rolls made for that unit and each time that unit makes a Blood Surge move, you can re-roll the D6 used to determine how far models in that unit move."
            }
        ]
    },
    "Maulerfiend": {
        "stats": {
            "stat_movement": "12\"",
            "stat_toughness": 10,
            "stat_save": "3+",
            "stat_wounds": 12,
            "stat_leadership": "6+",
            "stat_oc": 3,
            "stat_invuln": "5+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Maulerfiend fists",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "8",
                "skill": "3+",
                "strength": "14",
                "ap": "-2",
                "damage": "D6+1",
                "keywords": "-"
            },
            {
                "name": "Magma cutter",
                "weapon_type": "ranged",
                "range": "6\"",
                "attacks": "2",
                "skill": "4+",
                "strength": "9",
                "ap": "-4",
                "damage": "D6",
                "keywords": "Melta 2, Rapid Fire 1"
            },
            {
                "name": "Lasher tendrils",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "6",
                "skill": "3+",
                "strength": "7",
                "ap": "-1",
                "damage": "1",
                "keywords": "Extra Attacks"
            }
        ],
        "abilities": [
            {
                "name": "The Scent of Blood",
                "description": "In the Charge phase, when this unit declares a charge:\n- If an enemy unit below starting strength is within 9\" of this unit, this unit has +1 to charge rolls.\n- Or: If an enemy unit below half strength is within 9\" of this unit, this unit has +2 to charge rolls."
            },
            {
                "name": "Savage Exaltation",
                "description": "Each time this model makes a melee attack that targets an enemy unit that is below its Starting Strength, add 1 to the Hit roll and, if that attack targets an enemy unit that is Below Half-Strength, add 1 to the Wound roll as well."
            },
            {
                "name": "Terror of Khorne",
                "description": "At the start of the Fight phase, you can select one enemy unit engaged with this unit. That enemy unit makes a battle-shock roll, with -1 to that battle-shock roll. You cannot select the same enemy unit for this effect more than once per phase."
            }
        ]
    },
    "Skarbrand the Bloodthirster": {
        "stats": {
            "stat_movement": "10\"",
            "stat_toughness": 11,
            "stat_save": "3+",
            "stat_wounds": 20,
            "stat_leadership": "6+",
            "stat_oc": 5,
            "stat_invuln": "4+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Bellow of endless fury",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "2D6",
                "skill": "N/A",
                "strength": "8",
                "ap": "-1",
                "damage": "1",
                "keywords": "Ignores Cover, Torrent"
            },
            {
                "name": "➤ Slaughter and Carnage - strike",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "8",
                "skill": "2+",
                "strength": "16",
                "ap": "-4",
                "damage": "6",
                "keywords": "-"
            },
            {
                "name": "➤ Slaughter and Carnage - sweep",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "16",
                "skill": "2+",
                "strength": "8",
                "ap": "-2",
                "damage": "2",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Rage Embodied (Aura)",
                "description": "While a friendly Blood Legions unit is within 6\" of this model, add 1 to the Attacks characteristic of melee weapons equipped by models in that unit."
            },
            {
                "name": "Murderlust",
                "description": "This unit is eligible to declare a charge in a turn in which it Advanced."
            },
            {
                "name": "Damaged: 1-7 wounds remaining",
                "description": "While this model has 1-7 wounds remaining, add 2 to the Attacks characteristic of this model’s Slaughter and Carnage."
            }
        ]
    },
    "World Eaters Angron": {
        "stats": {
            "stat_movement": "14\"",
            "stat_toughness": 11,
            "stat_save": "2+",
            "stat_wounds": 16,
            "stat_leadership": "5+",
            "stat_oc": 6,
            "stat_invuln": "4+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "➤ Samni’arius and Spinegrinder - strike",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "8",
                "skill": "2+",
                "strength": "14",
                "ap": "-3",
                "damage": "D6+2",
                "keywords": "Devastating Wounds"
            },
            {
                "name": "➤ Samni’arius and Spinegrinder - sweep",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "16",
                "skill": "2+",
                "strength": "7",
                "ap": "-2",
                "damage": "2",
                "keywords": "Devastating Wounds"
            }
        ],
        "abilities": [
            {
                "name": "Reborn in Blood",
                "description": "At the start of the battle round, when you make a Blessings of Khorne roll, if this model is destroyed, you can use a triple 6 from that roll to use this ability instead of activating any Blessings of Khorne at the start of that battle round. If you do, this model is no longer destroyed and in the Reinforcements step of your next Movement phase, it is set up anywhere on the battlefield using its Deep Strike ability, with 8 wounds remaining."
            },
            {
                "name": "Wrathful Presence",
                "description": "At the start of the battle round, select one Wrathful Presence ability. Until the start of the next battle round, this model has that ability."
            },
            {
                "name": "Damaged: 1-6 wounds remaining",
                "description": "While this model has 1-6 wounds remaining, each time this model makes an attack, subtract 1 from the Hit roll."
            }
        ]
    },
    "World Eaters Berzerkers": {
        "stats": {
            "stat_movement": "8\"",
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
                "name": "Chainblade",
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
                "name": "➤ Plasma pistol - standard",
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
                "name": "➤ Plasma pistol - supercharge",
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
                "name": "Khornate eviscerator",
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
                "name": "Blood Surge",
                "description": "In your opponent’s Shooting phase, when an enemy unit has shot, if a model in this unit was destroyed as a result of those attacks, this unit can make a surge move of up to D6+2\"."
            },
            {
                "name": "Icon of Khorne",
                "description": "If the bearer's unit contains 1 or more Icons of Khorne, each time the bearer's unit destroys an enemy unit, you gain one Bloodshed point. Each time you make a Blessings of Khorne roll, roll one additional D6 for each Bloodshed point you have, after which, all your Bloodshed points are lost."
            }
        ]
    },
    "World Eaters Eightbound": {
        "stats": {
            "stat_movement": "10\"",
            "stat_toughness": 6,
            "stat_save": "3+",
            "stat_wounds": 3,
            "stat_leadership": "6+",
            "stat_oc": 1,
            "stat_invuln": "5+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Chainblades",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "5",
                "skill": "3+",
                "strength": "8",
                "ap": "-2",
                "damage": "2",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Beacons of Rage (Aura)",
                "description": "While a friendly World Eaters unit is within 6\" of this unit, each time a model in that unit makes a melee attack that targets a unit (excluding Monsters and Vehicles), add 1 to the Hit roll. If that attack targets a unit that is Below Half-strength, add 1 to the Wound roll as well."
            },
            {
                "name": "Brazen Fury",
                "description": "In your opponent’s Shooting phase, when an enemy unit has shot, if a model in this unit was destroyed as a result of those attacks, this unit can make a surge move of up to D6\". That surge move is a Brazen Fury move."
            }
        ]
    },
    "World Eaters Exalted Eightbound": {
        "stats": {
            "stat_movement": "10\"",
            "stat_toughness": 6,
            "stat_save": "3+",
            "stat_wounds": 3,
            "stat_leadership": "6+",
            "stat_oc": 1,
            "stat_invuln": "5+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Chainblades",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "3+",
                "strength": "8",
                "ap": "-3",
                "damage": "2",
                "keywords": "Anti-MONSTER 3+, Anti-VEHICLE 3+"
            }
        ],
        "abilities": [
            {
                "name": "Rend and Tear",
                "description": "Each time a model in this unit makes a melee attack that targets a Monster or Vehicle unit, until the end of the phase, improve the Damage characteristic of that attack by 1."
            },
            {
                "name": "Brazen Fury",
                "description": "In your opponent’s Shooting phase, when an enemy unit has shot, if a model in this unit was destroyed as a result of those attacks, this unit can make a surge move of up to D6\". That surge move is a Brazen Fury move."
            }
        ]
    },
    "World Eaters Jakhals": {
        "stats": {
            "stat_movement": "7\"",
            "stat_toughness": 4,
            "stat_save": "6+",
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
                "name": "Chainblades",
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
                "name": "Mauler chainblade",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "3",
                "skill": "5+",
                "strength": "4",
                "ap": "-1",
                "damage": "2",
                "keywords": "-"
            },
            {
                "name": "Skullsmasher and mangler",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "2",
                "skill": "4+",
                "strength": "4",
                "ap": "-1",
                "damage": "2",
                "keywords": "-"
            },
            {
                "name": "Paired manglers",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "4+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Objective Ravaged",
                "description": "At the end of your Command phase, if this unit is within range of an objective marker you control, that objective marker remains under your control until your opponent's Level of Control over that objective marker is greater than yours at the end of a phase."
            },
            {
                "name": "Icon of Khorne",
                "description": "If the bearer's unit contains 1 or more Icons of Khorne, each time the bearer's unit destroys an enemy unit, you gain one Bloodshed point. Each time you make a Blessings of Khorne roll, roll one additional D6 for each Bloodshed point you have, after which, all your Bloodshed points are lost."
            }
        ]
    },
    "World Eaters Kharn the Betrayer": {
        "stats": {
            "stat_movement": "8\"",
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
                "name": "Gorechild",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "8",
                "skill": "2+",
                "strength": "7",
                "ap": "-2",
                "damage": "3",
                "keywords": "-"
            },
            {
                "name": "➤ Plasma pistol - standard",
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
                "name": "➤ Plasma pistol - supercharge",
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
                "name": "Legendary Killer",
                "description": "While this model is leading a unit, each time a model in that unit makes a melee attack, re-roll a Hit roll of 1 and re-roll a Wound roll of 1."
            },
            {
                "name": "The Betrayer",
                "description": "At the end of your Charge phase, if this model is leading a unit and that unit is not within Engagement Range of one or more enemy units, you must take a Leadership test for this model. If that test is failed, one Bodyguard model of your choice in that unit is destroyed."
            },
            {
                "name": "Berserker Frenzy",
                "description": "The first time this model is destroyed, at the end of the phase, roll one D6: on a 2+, set this model back up on the battlefield as close as possible to where it was destroyed and not within Engagement Range of any enemy units, with 3 wounds remaining."
            },
            {
                "name": "Leader",
                "description": "This model can be attached to the following unit: Khorne Berzerkers"
            }
        ]
    },
    "World Eaters Lord Invocatus": {
        "stats": {
            "stat_movement": "10\"",
            "stat_toughness": 6,
            "stat_save": "3+",
            "stat_wounds": 8,
            "stat_leadership": "6+",
            "stat_oc": 2,
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
                "name": "Coward's Bane",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "7",
                "skill": "2+",
                "strength": "6",
                "ap": "-2",
                "damage": "2",
                "keywords": "Devastating Wounds"
            },
            {
                "name": "Bladed horn",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "3+",
                "strength": "6",
                "ap": "-1",
                "damage": "2",
                "keywords": "Extra Attacks, Lance"
            }
        ],
        "abilities": [
            {
                "name": "Leader",
                "description": "This model can be attached to the following units: Eightbound, Exalted Eightbound, Khorne Berzerkers"
            },
            {
                "name": "Fire Riders",
                "description": "While this model is leading a unit, models in that unit have the Deep Strike ability and each time a model in that unit makes a Normal, Advance, Fall Back or Charge move, it can move horizontally through models and terrain features. When making a Normal, Advance or Fall Back move, models in that unit can move within Engagement Range of enemy models, but cannot end that move within Engagement Range of them and any Desperate Escape test is automatically passed."
            },
            {
                "name": "Bloody Stampede",
                "description": "Each time this model's unit ends a Charge move, select one enemy unit within Engagement Range of this model, then roll one D6: on a 2-3, that enemy unit suffers 1 mortal wound; on a 4-5, that enemy unit suffers D3 mortal wounds; on a 6, that enemy unit suffers D3+3 mortal wounds."
            }
        ]
    },
    "World Eaters Lord on Juggernaut": {
        "stats": {
            "stat_movement": "10\"",
            "stat_toughness": 6,
            "stat_save": "3+",
            "stat_wounds": 7,
            "stat_leadership": "6+",
            "stat_oc": 2,
            "stat_invuln": "4+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Bladed horn",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "3+",
                "strength": "6",
                "ap": "-1",
                "damage": "2",
                "keywords": "Extra Attacks, Lance"
            },
            {
                "name": "Exalted chainblade",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "7",
                "skill": "2+",
                "strength": "6",
                "ap": "-1",
                "damage": "2",
                "keywords": "-"
            },
            {
                "name": "➤ Plasma pistol - standard",
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
                "name": "➤ Plasma pistol - supercharge",
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
                "name": "Aggressive Advance",
                "description": "While this model is leading a unit, models in that unit have a Move characteristic of 10\" and each time a model in that unit makes a Normal, Advance, Fall Back or Charge move, it can move horizontally though terrain features."
            },
            {
                "name": "Crush All Who Stand Before Us",
                "description": "Each time this model's unit is selected to fight, you can use this ability. When determining which models in this unit are eligible to fight, any models in it that are within 3\" of one or more enemy models are eligible to fight. When resolving those attacks, such models can target one of those enemy units that is within 3\" of them and within Engagement Range of their unit."
            },
            {
                "name": "Leader",
                "description": "This model can be attached to the following units: Eightbound, Exalted Eightbound, Khorne Berzerkers"
            }
        ]
    },
    "World Eaters Slaughterbound": {
        "stats": {
            "stat_movement": "10\"",
            "stat_toughness": 6,
            "stat_save": "3+",
            "stat_wounds": 6,
            "stat_leadership": "6+",
            "stat_oc": 1,
            "stat_invuln": "5+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Lacerator and daemonic claw",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "6",
                "skill": "2+",
                "strength": "10",
                "ap": "-2",
                "damage": "2",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Rage Eternal",
                "description": "While this model is leading a unit, in your Command phase, you can return one destroyed Bodyguard model to that unit."
            },
            {
                "name": "Possessed Lord",
                "description": "Once per battle, at the start of the Fight phase, this model can use this ability. If it does, until the end of the phase, add 3 to the Attacks characteristic of melee weapons equipped by this model and those weapons have the [Devastating Wounds] ability."
            },
            {
                "name": "Leader",
                "description": "This model can be attached to the following units: Eightbound, Exalted Eightbound"
            },
            {
                "name": "Lord of the Eightbound",
                "description": "If this model is attached to a World Eaters Possessed unit during the Declare Battle Formations step, this model has the Deep Strike and Scouts 6\" abilities."
            }
        ]
    }
}


class Command(BaseCommand):
    """Refresh World Eaters stat lines, weapon profiles, and abilities from BSData."""

    help = 'Refresh 11th Edition stats/weapons/abilities for World Eaters units.'

    def add_arguments(self, parser):
        """Add --dry-run flag."""
        parser.add_argument(
            '--dry-run', action='store_true',
            help='Preview changes without writing to the database.',
        )

    def handle(self, *args, **options):
        """Iterate WORLD_EATERS_DATASHEETS and refresh each unit's datasheet data."""
        dry_run = options['dry_run']
        updated = 0
        skipped = 0

        with transaction.atomic():
            for name, payload in WORLD_EATERS_DATASHEETS.items():
                try:
                    unit = UnitType.objects.get(name=name, faction__name='World Eaters')
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
