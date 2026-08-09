"""
Management command: seed_space_wolves_datasheets

Refreshes stat lines, weapon profiles, and abilities for the Space
Wolves-exclusive units using 11th Edition data sourced from BSData/
wh40k-11e ("Imperium - Space Wolves.json") -- the same source used by
seed_space_wolves_points.py.

Usage:
    python manage.py seed_space_wolves_datasheets
    python manage.py seed_space_wolves_datasheets --dry-run

Notes:
- Does NOT touch points_cost or category -- those are handled entirely by
  seed_space_wolves_points.py. This command only refreshes stat_* fields,
  WeaponProfile rows, and UnitAbility rows.
- Scope is the 21 Space-Wolves-exclusive rows only -- generic squads
  inherit their datasheets from the base Space Marines faction
  automatically.
- Per-field safety rule: a unit's stats/weapons/abilities are only
  overwritten when BSData actually has that data for it. If extraction
  found nothing, the existing DB value/rows are left untouched.
- Three known gaps, all traced to entryLinks with "import": true pointing
  into an external shared catalogue not included in this single-file
  fetch (same class of gap as Black Templars' Land Raider Crusader and
  Blood Angels' Sanguinary Priest): 'Wulfen' has no resolvable stat
  profile within this file (its build-variant sibling, 'Wulfen with
  Storm Shields', happens to embed its own self-named stat profile
  directly and resolved fine); 'Blood Claws' and 'Wolf Priest' have
  0 resolvable weapon profiles (their wargear entryLinks -- Astartes
  Chainsword, Bolt pistol, Crozius arcanum, Absolvor bolt pistol -- are
  all external imports). Existing DB data for these specific fields is
  left untouched per the safety rule.
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from calculators.models import UnitAbility, UnitType, WeaponProfile

# (name -> {stats?, weapons?, abilities?}). Missing keys mean "no data
# found for this field -- leave existing DB data untouched."
SPACE_WOLVES_DATASHEETS = {
    "Arjac Rockfist": {
        "stats": {
            "stat_movement": "6\"",
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
                "name": "Foehammer",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "5",
                "skill": "2+",
                "strength": "8",
                "ap": "-2",
                "damage": "3",
                "keywords": "Anti-Monster 3+, Anti-Vehicle 3+, Precision"
            },
            {
                "name": "Foehammer",
                "weapon_type": "ranged",
                "range": "6\"",
                "attacks": "1",
                "skill": "2+",
                "strength": "8",
                "ap": "-2",
                "damage": "3",
                "keywords": "Anti-Monster 3+, Anti-Vehicle 3+, Assault"
            }
        ],
        "abilities": [
            {
                "name": "Leader",
                "description": "This model can be attached to the following units:\n\n\u25a0 Wolf Guard Terminators"
            },
            {
                "name": "Anvil of Endurance",
                "description": "While this model is leading a unit, each time a model in that unit is destroyed by a melee attack, if that model has not fought this phase, roll one D6, on a 4+, do not remove the destroyed model from play. The destroyed model can fight after the attacking unit has finished making its attacks, and then is removed from play"
            },
            {
                "name": "Champion of the Kingsguard",
                "description": "Each time this model makes a melee attack that targets a CHARACTER unit, you can re-roll the Hit roll and you can re-roll the Wound roll."
            }
        ]
    },
    "Bjorn the Fell-Handed": {
        "stats": {
            "stat_movement": "9\"",
            "stat_toughness": 9,
            "stat_save": "2+",
            "stat_wounds": 8,
            "stat_leadership": "6+",
            "stat_oc": 3,
            "stat_invuln": "5+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Trueclaw",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "6",
                "skill": "2+",
                "strength": "12",
                "ap": "-2",
                "damage": "3",
                "keywords": "Lethal Hits"
            },
            {
                "name": "Assault cannon",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "6",
                "skill": "2+",
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
                "skill": "2+",
                "strength": "9",
                "ap": "-4",
                "damage": "D6",
                "keywords": "Melta 2"
            },
            {
                "name": "\u27a4 Helfrost cannon - dispersed",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "D6",
                "skill": "N/A",
                "strength": "6",
                "ap": "-1",
                "damage": "2",
                "keywords": "Torrent"
            },
            {
                "name": "\u27a4 Helfrost cannon - focused",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "1",
                "skill": "2+",
                "strength": "10",
                "ap": "-3",
                "damage": "5",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Legendary Tenacity",
                "description": "Each time an attack is allocated to this model, if the Strength characteristic of that attack is greater than this model's Toughness characteristic, subtract 1 from the Wound roll."
            },
            {
                "name": "Ancient Tactician",
                "description": "At the start of your Command phase, if this model is on the battlefield, you gain 1 CP"
            }
        ]
    },
    "Blood Claws": {
        "stats": {
            "stat_movement": "7\"",
            "stat_toughness": 4,
            "stat_save": "3+",
            "stat_wounds": 2,
            "stat_leadership": "6+",
            "stat_oc": 2,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "abilities": [
            {
                "name": "Berserk Charge",
                "description": "This unit is eligible to declare a charge in a turn in which it Advanced"
            }
        ]
    },
    "Fenrisian Wolves": {
        "stats": {
            "stat_movement": "10\"",
            "stat_toughness": 4,
            "stat_save": "6+",
            "stat_wounds": 1,
            "stat_leadership": "8+",
            "stat_oc": 0,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Teeth and claws",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "3",
                "skill": "4+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Predatory Instinct",
                "description": "Once per turn, when an enemy unit ends a Normal, Advance or Fall Back move within 9\" of this unit, it can make a Normal move of up to D6\""
            },
            {
                "name": "Hunting Hounds",
                "description": "While this unit is within 6\" of one or more SPACE WOLVES CHARACTER models (excluding WULFEN models), if this unit is not Battle-shocked, models in it have an Objective Control characteristic of 1"
            }
        ]
    },
    "Grey Hunters": {
        "stats": {
            "stat_movement": "7\"",
            "stat_toughness": 4,
            "stat_save": "3+",
            "stat_wounds": 2,
            "stat_leadership": "6+",
            "stat_oc": 3,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
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
                "name": "Bolt Carbine",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "2",
                "skill": "3+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Rapid Fire 1"
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
                "name": "Cunning Hunters",
                "description": "Each time a model in this unit makes an attack, re-roll a Wound roll of 1. If the target is within range of an objective marker, you can re-roll the Wound roll instead."
            }
        ]
    },
    "Iron Priest": {
        "stats": {
            "stat_movement": "7\"",
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
                "name": "\u27a4 Helfrost pistol - dispersed",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "D6",
                "skill": "N/A",
                "strength": "4",
                "ap": "-1",
                "damage": "1",
                "keywords": "Pistol, Torrent"
            },
            {
                "name": "\u27a4 Helfrost pistol - focused",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "1",
                "skill": "2+",
                "strength": "6",
                "ap": "-3",
                "damage": "3",
                "keywords": "Pistol"
            },
            {
                "name": "Tempest hammer and Servo-arm",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "4+",
                "strength": "8",
                "ap": "-2",
                "damage": "3",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Iron Priest",
                "description": "While this model is within 3\" of one or more friendly ADEPTUS ASTARTES VEHICLE units, this model has the Lone Operative ability"
            },
            {
                "name": "Gift of the Iron Wolf",
                "description": "In your Command phase, you can select one friendly ADEPTUS ASTARTES VEHICLE model within 3\" of this model. That model regains up to D3 lost wounds and, until the start of your next Command phase, select one ranged weapon equipped by that model to have the [RAPID FIRE 1] ability. Each model can only be selected for this ability or Blessing of the Omnissiah ability once per turn."
            },
            {
                "name": "Leader",
                "description": "This model can be attached to the following units:\n\n\u25a0 Wolfguard Headtakers\n\u25a0 Blood Claws\n\u25a0 Grey Hunters"
            },
            {
                "name": "Judgement of the Omnissiah",
                "description": "Each time this model makes an attack that targets an enemy unit within Engagement Range of one or more friendly ADEPTUS ASTARTES VEHICLE units, you can re-roll the wound roll."
            }
        ]
    },
    "Logan Grimnar": {
        "stats": {
            "stat_movement": "6\"",
            "stat_toughness": 5,
            "stat_save": "2+",
            "stat_wounds": 8,
            "stat_leadership": "6+",
            "stat_oc": 1,
            "stat_invuln": "4+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Tyrnak and Fenrir",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "6",
                "skill": "2+",
                "strength": "5",
                "ap": "-1",
                "damage": "1",
                "keywords": "Extra Attacks"
            },
            {
                "name": "\u27a4 Axe Morkai - Sweep",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "10",
                "skill": "2+",
                "strength": "6",
                "ap": "-2",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "\u27a4 Axe Morkai - Strike",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "6",
                "skill": "2+",
                "strength": "8",
                "ap": "-2",
                "damage": "3",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Leader",
                "description": "This model can be attached to the following units:\n\n\u25a0 Wolf Guard Terminators"
            },
            {
                "name": "High King of Fenris",
                "description": "Once per battle round, in your Movement phase, you can select one friendly Space Wolves unit that is in Reserves. If you do, until the end of the phase, for the purposes of setting up that unit on the battlefield, treat the current battle round number as being one higher than it actually is."
            },
            {
                "name": "Guile of the Wolf (Aura)",
                "description": "Each time your opponent targets a unit from their army with a Stratagem, if that unit is within 12\" of this model, increase the cost of that usage of that Stratagem by 1CP P (this is not cumulative with any other rules that increase the CP cost of that Stratagem)"
            },
            {
                "name": "Embarking within Transports",
                "description": "This model can embark within friendly Adeptus Astartes Transport models that can transport Terminator models. When doing, it takes up the space of 4 Infantry models"
            }
        ]
    },
    "Murderfang": {
        "stats": {
            "stat_movement": "9\"",
            "stat_toughness": 9,
            "stat_save": "2+",
            "stat_wounds": 8,
            "stat_leadership": "6+",
            "stat_oc": 0,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Murderclaws",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "8",
                "skill": "3+",
                "strength": "14",
                "ap": "-2",
                "damage": "3",
                "keywords": "Sustained Hits 1, Twin-linked"
            },
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
            }
        ],
        "abilities": [
            {
                "name": "Murder-maker [Aura]",
                "description": "In the Fight phase, each time an attack targets a friendly WULFEN unit within 6\" of this model, if a model in that unit is destroyed as a result of that attack, if that model has not fought this phase, roll one D6: on a 4+, do not remove the destroyed model from play; it can fight after the attacking unit has finished making its attacks, and is then removed from play."
            },
            {
                "name": "Force of Untamed Destruction",
                "description": "This model cannot be your WARLORD."
            },
            {
                "name": "Beastial Fury",
                "description": "You can re-roll Advance and Charge rolls made for this model."
            }
        ]
    },
    "Njal Stormcaller": {
        "stats": {
            "stat_movement": "7\"",
            "stat_toughness": 4,
            "stat_save": "3+",
            "stat_wounds": 4,
            "stat_leadership": "6+",
            "stat_oc": 1,
            "stat_invuln": "4+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Staff of the Stormcaller",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "3+",
                "strength": "7",
                "ap": "-1",
                "damage": "D3",
                "keywords": "Psychic, Sustained Hits 2"
            },
            {
                "name": "\u27a4 Living Lightning - witchfire",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "D6",
                "skill": "3+",
                "strength": "7",
                "ap": "-1",
                "damage": "1",
                "keywords": "Psychic, Sustained Hits 2"
            },
            {
                "name": "\u27a4 Living Lightning - focused witchfire",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "2D6",
                "skill": "3+",
                "strength": "7",
                "ap": "-1",
                "damage": "1",
                "keywords": "Hazardous, Psychic, Sustained Hits 2"
            }
        ],
        "abilities": [
            {
                "name": "Leader",
                "description": "This model can be attached to the following units:\n\n\u25a0 Blood Claws\n\u25a0 Grey Hunters\n\u25a0 Wolf Guard Headtakers"
            },
            {
                "name": "Wind Walker (Psychic)",
                "description": "While this model is leading a unit, ranged weapons equipped by models in that unit have the [ASSAULT] ability and each time that unit advances, do not make an Advance roll. Instead, until the end of the phase, add 6\" to the Move characteristic of models in this unit"
            },
            {
                "name": "Tempest's Wrath (Psychic)",
                "description": "In your Shooting phase, after this model's unit has shot, select one enemy unit, (excluding MONSTERS and VEHICLES) hit by one or more of those attacks made with this model's Living Lightning weapon. Until the start of your next turn, that enemy is stormwracked. While a unit is stormwracked, subtract 6\" from the Range characteristic of ranged weapons equipped by models in that unit (to a minimum of 12\")"
            }
        ]
    },
    "Ragnar Blackmane": {
        "stats": {
            "stat_movement": "7\"",
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
                "name": "Frostfang",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "8",
                "skill": "2+",
                "strength": "6",
                "ap": "-3",
                "damage": "2",
                "keywords": "Sustained Hits 1"
            }
        ],
        "abilities": [
            {
                "name": "Leader",
                "description": "This model can be attached to the following units:\n\n\u25a0 Blood Claws\n\u25a0 Wolf Guard Headtakers"
            },
            {
                "name": "War Howl",
                "description": "While this model is leading a BLOOD CLAWS unit, each time a model in that unit makes a melee attack, you can re-roll the Wound roll. While this model is leading a WOLF GUARD HEADTAKERS UNIT, that unit is eligible to declare a charge in a turn in which it Advanced."
            },
            {
                "name": "Battle-lust",
                "description": "Each time this model ends a Charge move, until the end of the turn, add 2 to the Attacks characteristics of this model\u2019s Frostfang."
            }
        ]
    },
    "Thunderwolf Cavalry": {
        "stats": {
            "stat_movement": "12\"",
            "stat_toughness": 6,
            "stat_save": "3+",
            "stat_wounds": 4,
            "stat_leadership": "6+",
            "stat_oc": 2,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Wolf Guard Weapon",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "3+",
                "strength": "5",
                "ap": "-2",
                "damage": "2"
            },
            {
                "name": "Crushing teeth and claws",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "3",
                "skill": "4+",
                "strength": "5",
                "ap": "-1",
                "damage": "1",
                "keywords": "Extra Attacks"
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
                "name": "Thunderous Charge",
                "description": "Each time a model in this unit makes a melee attack with its Wolf Guard weapon, if it made a Charge move this turn, add 1 to the Damage characteristic of that attack"
            },
            {
                "name": "Storm Shield",
                "description": "The bearer has a 4+ invulnerable save."
            }
        ]
    },
    "Ulrik the Slayer": {
        "stats": {
            "stat_movement": "7\"",
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
                "name": "\u27a4 Plasma pistol - standard",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "1",
                "skill": "2+",
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
                "skill": "2+",
                "strength": "8",
                "ap": "-2",
                "damage": "2",
                "keywords": "Hazardous, Pistol"
            },
            {
                "name": "Artificer crozius",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "5",
                "skill": "2+",
                "strength": "6",
                "ap": "-2",
                "damage": "2",
                "keywords": "Anti-Monster 4+, Anti-Vehicle 4+"
            }
        ],
        "abilities": [
            {
                "name": "Slayer\u2019s Oath",
                "description": "At the start of the battle, select one of the following keywords to be this model's Slayer's Oath: CHARACTER, VEHICLE or MONSTER. The first time this model's unit destroys a unit with this model's Slayer's Oath keyword, if your Detachment has a Saga, until the end of the battle, this model's unit receives the benefits of that Detachment rule as if that Saga had been completed."
            },
            {
                "name": "Leader",
                "description": "This model can be attached to the following units:\n\n\u25a0 Blood Claws\n\u25a0 Grey Hunters\n\u25a0 Wolf Guard Headtakers"
            },
            {
                "name": "Oathbound",
                "description": "While this model is leading a unit, each time a model in that unit makes a melee attack, add 1 to the Hit roll. If that attack targets a unit that has this model's Slayer's Oath keyword (see above), add 1 to the Wound roll as well."
            }
        ]
    },
    "Venerable Dreadnought": {
        "stats": {
            "stat_movement": "8\"",
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
                "name": "\u27a4 Fenrisian great axe - strike",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "6",
                "skill": "3+",
                "strength": "10",
                "ap": "-2",
                "damage": "D6+1",
                "keywords": "-"
            },
            {
                "name": "\u27a4 Fenrisian great axe - sweep",
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
                "name": "\u27a4 Helfrost cannon - dispersed",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "D6",
                "skill": "N/A",
                "strength": "6",
                "ap": "-1",
                "damage": "2",
                "keywords": "Torrent"
            },
            {
                "name": "\u27a4 Helfrost cannon - focused",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "10",
                "ap": "-3",
                "damage": "5",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Fervour of the Ancients (Aura)",
                "description": "While a friendly SPACE WOLVES unit is within 6\" of this model, add 1 to Advance and Charge rolls made for that unit."
            },
            {
                "name": "Blizzard shield",
                "description": "The bearer has a 4+ invulnerable save."
            }
        ]
    },
    "Wolf Guard Battle Leader": {
        "stats": {
            "stat_movement": "7\"",
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
                "name": "Master-crafted Power Weapon",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "7",
                "skill": "2+",
                "strength": "5",
                "ap": "-2",
                "damage": "2",
                "keywords": "-"
            },
            {
                "name": "Master-crafted Bolt Carbine",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "2",
                "skill": "3+",
                "strength": "4",
                "ap": "0",
                "damage": "2",
                "keywords": "-"
            },
            {
                "name": "Master-crafted Heavy Bolt Pistol",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "4",
                "ap": "-1",
                "damage": "2",
                "keywords": "Pistol"
            }
        ],
        "abilities": [
            {
                "name": "Tempered Ferocity",
                "description": "While this model is leading a unit, weapons equipped by models in that unit have the [SUSTAINED HITS 1] ability and, each time a model in that unit makes an attack that targets an enemy unit within 6\", re-roll a Hit roll of 1"
            },
            {
                "name": "Heroic Last Stand",
                "description": "If this model is destroyed by a melee attack, if it has not fought this phase, roll one D6: on a 2+, do not remove it from play. The destroyed model can fight after the attacking unit has finished making its attacks, and then it is removed from play."
            },
            {
                "name": "Leader",
                "description": "This model can be attached to the following units:\n\n\u25a0 Blood Claws\n\u25a0 Grey Hunters\n\u25a0 Wolf Guard Headtakers"
            },
            {
                "name": "Storm Shield",
                "description": "The bearer has a Wounds characteristic of 6"
            }
        ]
    },
    "Wolf Guard Headtakers": {
        "stats": {
            "stat_movement": "7\"",
            "stat_toughness": 4,
            "stat_save": "3+",
            "stat_wounds": 3,
            "stat_leadership": "6+",
            "stat_oc": 1,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Master-crafted Power Weapon",
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
                "name": "Paired Master-crafted Power Weapons",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "6",
                "skill": "3+",
                "strength": "5",
                "ap": "-2",
                "damage": "2",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Storm Shield",
                "description": "The bearer has a 4+ invulnerable save."
            }
        ]
    },
    "Wolf Guard Terminators": {
        "stats": {
            "stat_movement": "6\"",
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
                "name": "Twin lightning claws",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "6",
                "skill": "3+",
                "strength": "5",
                "ap": "-2",
                "damage": "1",
                "keywords": "Twin-linked"
            },
            {
                "name": "Relic Great Axe",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "3",
                "skill": "3+",
                "strength": "7",
                "ap": "-2",
                "damage": "3",
                "keywords": "Devastating Wounds"
            },
            {
                "name": "Master-crafted Power Weapon",
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
                "name": "Storm Bolter",
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
                "name": "Assault Cannon",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "6",
                "skill": "2+",
                "strength": "6",
                "ap": "0",
                "damage": "1",
                "keywords": "Devastating Wounds"
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
                "name": "Rugged Resilience",
                "description": "Each time an attack targets this unit, if the Strength characteristic of that attack is greater than the Toughness characteristic of this unit, subtract 1 from the Wound roll."
            },
            {
                "name": "Storm Shield",
                "description": "The bearer has a Wounds characteristic of 4."
            }
        ]
    },
    "Wolf Priest": {
        "stats": {
            "stat_movement": "7\"",
            "stat_toughness": 4,
            "stat_save": "3+",
            "stat_wounds": 4,
            "stat_leadership": "6+",
            "stat_oc": 1,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "abilities": [
            {
                "name": "Leader",
                "description": "This model can be attached to the following units:\n\n\u25a0 Blood Claws\n\u25a0 Grey Hunters\n\u25a0 Wolf Guard Headtakers"
            },
            {
                "name": "Healing Balms",
                "description": "While this model is leading a unit, in your Command phase, you can return 1 model (excluding CHARACTER models) to that unit."
            }
        ]
    },
    "Wolf Scouts": {
        "stats": {
            "stat_movement": "7\"",
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
                "name": "Teeth and Claws",
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
                "name": "Combat Blade",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "3+",
                "strength": "4",
                "ap": "-1",
                "damage": "1"
            },
            {
                "name": "Runic Stave",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "3",
                "skill": "3+",
                "strength": "6",
                "ap": "-1",
                "damage": "D3",
                "keywords": "Psychic"
            },
            {
                "name": "Thunderclap",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "D3",
                "skill": "3+",
                "strength": "5",
                "ap": "-1",
                "damage": "2",
                "keywords": "Blast, Psychic"
            }
        ],
        "abilities": [
            {
                "name": "Hunting Hounds",
                "description": "While this unit is within 6\" of one or more friendly Space Wolves Character models (excluding Wulfen models), if this unit is not Battle-shocked, Hunting Wolves models in this unit have an Objective Control characteristic of 1."
            },
            {
                "name": "Deadly Stalkers",
                "description": "Each time a model in this unit makes an attack that targets an enemy unit, if there are no other units from your opponent\u2019s army within 6\" of that target, add 1 to the Wound roll."
            },
            {
                "name": "Haywire Mine",
                "description": "Once per battle, at the start of any phase, you can select one enemy unit within 3\" of the bearer and roll one D6: on a 2+, that enemy unit suffers D3 mortal wounds, or 2D3 mortal wounds instead if it is a Vehicle unit."
            }
        ]
    },
    "Wulfen": {
        "weapons": [
            {
                "name": "Wulfen Weapons",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "3",
                "skill": "3+",
                "strength": "5",
                "ap": "-2",
                "damage": "2",
                "keywords": "Sustained Hits 1"
            },
            {
                "name": "Stormfrag auto-launcher",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "D3",
                "skill": "4+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Assault, Blast"
            }
        ],
        "abilities": [
            {
                "name": "Savage Frenzy",
                "description": "Each time an enemy unit, (excluding MONSTERS and VEHICLES) within Engagement Range of this unit Falls Back, all that models in that enemy unit must take a Desperate Escape test. When doing so, if that enemy unit is Battle-shocked, subtract 1 from those tests."
            },
            {
                "name": "Death Totem",
                "description": "Each time the bearer makes a melee attack, re-roll a hit roll of 1."
            }
        ]
    },
    "Wulfen Dreadnought": {
        "stats": {
            "stat_movement": "9\"",
            "stat_toughness": 9,
            "stat_save": "2+",
            "stat_wounds": 8,
            "stat_leadership": "6+",
            "stat_oc": 0,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Great wolf claw",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "6",
                "skill": "3+",
                "strength": "10",
                "ap": "-3",
                "damage": "3",
                "keywords": "-"
            },
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
                "name": "\u27a4 Fenrisian great axe - strike",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "6",
                "skill": "3+",
                "strength": "10",
                "ap": "-2",
                "damage": "D6+1",
                "keywords": "-"
            },
            {
                "name": "\u27a4 Fenrisian great axe - sweep",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "12",
                "skill": "3+",
                "strength": "6",
                "ap": "-2",
                "damage": "1",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Bestial Rage",
                "description": "Each time an enemy unit is selected to shoot, after that unit has shot, if this model lost one or more wounds as a result of those attacks, this model can make a Bestial Rage move. To do so, roll one D6, adding 2 to the result: this model can be moved a number of inches up to the result, but must finish that move as close as possible to the closest enemy unit(excluding AIRCRAFT). When doing so, this model can be moved within Engagement Range of that enemy unit. Each model can only make one Bestial Rage move per phase."
            },
            {
                "name": "Violent Fury",
                "description": "If this model is equipped with two melee weapons, those weapon profiles have the TWIN-LINKED ability."
            },
            {
                "name": "Blizzard shield",
                "description": "The bearer has a 4+ invulnerable save."
            }
        ]
    },
    "Wulfen with Storm Shields": {
        "stats": {
            "stat_movement": "9\"",
            "stat_toughness": 6,
            "stat_save": "4+",
            "stat_wounds": 2,
            "stat_leadership": "7+",
            "stat_oc": 0,
            "stat_invuln": "4+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Thunder Hammer",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "2",
                "skill": "3+",
                "strength": "5",
                "ap": "-2",
                "damage": "3",
                "keywords": "Anti-Monster 3+, Anti-Vehicle 3+"
            },
            {
                "name": "Stormfrag auto-launcher",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "D3",
                "skill": "4+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Assault, Blast"
            }
        ],
        "abilities": [
            {
                "name": "Hammer Blow",
                "description": "In the Fight phase, after this unit has fought, select one enemy MONSTER or VEHICLE unit hit by one or more of those attacks. Until the end of the next turn, that enemy unit is suppressed. While a unit is suppressed, each time a model in that unit makes an attack, subtract 1 from the Hit roll."
            },
            {
                "name": "Death Totem",
                "description": "Each time the bearer makes a melee attack, re-roll a hit roll of 1."
            },
            {
                "name": "Storm Shield",
                "description": "The bearer has a 4+ invulnerable save."
            }
        ]
    }
}


class Command(BaseCommand):
    """Refresh Space Wolves stat lines, weapon profiles, and abilities from BSData."""

    help = 'Refresh 11th Edition stats/weapons/abilities for Space-Wolves-exclusive units.'

    def add_arguments(self, parser):
        """Add --dry-run flag."""
        parser.add_argument(
            '--dry-run', action='store_true',
            help='Preview changes without writing to the database.',
        )

    def handle(self, *args, **options):
        """Iterate SPACE_WOLVES_DATASHEETS and refresh each unit's datasheet data."""
        dry_run = options['dry_run']
        updated = 0
        skipped = 0

        with transaction.atomic():
            for name, payload in SPACE_WOLVES_DATASHEETS.items():
                try:
                    unit = UnitType.objects.get(name=name, faction__name='Space Wolves')
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
