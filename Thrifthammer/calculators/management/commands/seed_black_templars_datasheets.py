"""
Management command: seed_black_templars_datasheets

Refreshes stat lines, weapon profiles, and abilities for the 18
Black-Templars-exclusive units using 11th Edition data sourced from
BSData/wh40k-11e ("Imperium - Black Templars.json") -- the same source
used by seed_black_templars_points.py.

Usage:
    python manage.py seed_black_templars_datasheets
    python manage.py seed_black_templars_datasheets --dry-run

Notes:
- Does NOT touch points_cost or category -- those are handled entirely by
  seed_black_templars_points.py. This command only refreshes stat_* fields,
  WeaponProfile rows, and UnitAbility rows.
- Scope is deliberately just the 18 BT-exclusive rows (Castellan, Chaplain
  Grimaldus, Crusade Ancient, Crusader Squad, Emperor's Champion,
  Execrator, Gladiator Lancer/Reaper/Valiant, High Marshal Helbrecht,
  Impulsor, Land Raider Crusader, Marshal, Repulsor, Repulsor Executioner,
  Sternguard Veteran Squad, Sword Brethren Squad, Terminator Squad) -- the
  generic Space-Marine-squad rows were deactivated by the points command
  and inherit their datasheets from the base Space Marines faction
  automatically. Judiciar/Suppressor Squad (productless placeholders) are
  also out of scope here -- no BT-specific datasheet source exists for
  them.
- Per-field safety rule: a unit's stats/weapons/abilities are only
  overwritten when BSData actually has that data for it. If extraction
  found nothing, the existing DB value/rows are left untouched.
- Known gap: 'Land Raider Crusader' has 0 weapon profiles in BSData's
  Black Templars catalogue -- its "Wargear" selection group only contains
  optional upgrades (Armoured Tracks, Hunter-killer missile) whose
  entryLinks don't resolve against any catalogue this file references
  (not Space Marines, and this file has no "Unaligned Forces" link
  either). The core weapon loadout isn't reachable from this data source.
  Same class of gap as the Orks named-character weapons issue -- left
  blank rather than fabricated (there was no pre-existing weapon data to
  preserve either, confirmed before this command was written).
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from calculators.models import UnitAbility, UnitType, WeaponProfile

# (name -> {stats?, weapons?, abilities?}). Missing keys mean "no data
# found for this field -- leave existing DB data untouched."
BLACK_TEMPLARS_DATASHEETS = {
    "Castellan": {
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
                "name": "Astartes Chainsword",
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
                "name": "Master-crafted Power Weapon",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "6",
                "skill": "2+",
                "strength": "5",
                "ap": "-2",
                "damage": "2",
                "keywords": "Lethal Hits"
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
                "name": "Combi-weapon",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Anti-Infantry 4+, Devastating Wounds, Rapid Fire 1"
            }
        ],
        "abilities": [
            {
                "name": "Support",
                "description": "This model can be attached to the following units:\n\n\u25a0 Assault Intercessor Squad\n\u25a0 Infernus Squad\n\u25a0 Intercessor Squad\n\u25a0 Crusader Squad\n\u25a0 Sword Brethren\n\u25a0 Sternguard Veteran Squad\n\nYou can attach this model to one of the above units even if one Captain or Chapter Master model has already been attached to it. If you do, and that Bodyguard unit is destroyed, the Leader units attached to it become separate units, with their original Starting Strengths."
            },
            {
                "name": "Vehement Aggression",
                "description": "While this model is leading a unit, each time that unit is selected to fight, take a Leadership test for that unit: if passed, until the end of the phase, each time a model in that unit makes an attack, you can re-roll the Hit roll; if failed, until the end of the phase, each time a model in that unit makes an attack, re-roll a Hit roll of 1"
            },
            {
                "name": "Prioritised Eradication",
                "description": "Each time a model in this model's unit makes a melee attack that destroys one or more enemy units, roll one D6: on a 4+, you gain 1 CP"
            }
        ]
    },
    "Chaplain Grimaldus": {
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
                "name": "Artificer Crozius",
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
                "name": "\u27a4 Plasma Pistol - Supercharge",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "1",
                "skill": "2+",
                "strength": "8",
                "ap": "-3",
                "damage": "2",
                "keywords": "Hazardous, Pistol"
            },
            {
                "name": "\u27a4 Plasma Pistol - Standard",
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
                "name": "Close Combat Weapon",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "1",
                "skill": "4+",
                "strength": "3",
                "ap": "0",
                "damage": "1",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Litanies of the Devout",
                "description": "While this unit is leading a unit and contains a Chaplain Grimaldus model, each time a model in that unit makes a melee attack, you can re-roll the Hit roll."
            },
            {
                "name": "Temple Relics",
                "description": "In your Command phase, if this unit contains one or more Cenobyte Servitor models, select one Temple Relics ability (see left). Until the start of your next Command phase, this unit\u2019s Chaplain Grimaldus model has that ability.\n\n\nBanner of the Emperor Victorious: Add 1 to Advance and Charge rolls for this unit\n\n\nColumn of the Major Alter: Add 1 to the Toughness characteristic of models in this unit\n\n\nWater from the Stoup of Elucidation: Improve the Armour Penetration characteristic of melee weapons equipped by models in this unit by 1."
            },
            {
                "name": "Leader",
                "description": "This unit can be attached to the following units:\n\n\u25a0 Assault Intercessor Squad\n\u25a0 Infernus Squad\n\u25a0 Intercessor Squad\n\u25a0 Crusader Squad\n\u25a0 Sword Brethren"
            }
        ]
    },
    "Crusade Ancient": {
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
                "name": "Master-crafted Power Weapon",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "5",
                "skill": "2+",
                "strength": "5",
                "ap": "-2",
                "damage": "2",
                "keywords": "Lethal Hits"
            }
        ],
        "abilities": [
            {
                "name": "Vengeful Exhortation",
                "description": "While this model is leading a unit, each time a model in that unit is destroyed by a melee attack, if it has not fought this phase, roll one D6: on a 4+, do not remove it from play, the destroyed model can fight after the attacking unit has finished making its attacks, and is then removed from play."
            },
            {
                "name": "Martial Honour",
                "description": "The first time a model in this model's unit makes a melee attack that destroys one or more enemy units, until the end of the battle, while this model's unit is not Battle-shocked, add 5 to this model's Objective Control characteristic."
            },
            {
                "name": "Support",
                "description": "This model can be attached to the following units:\n\n\n\u25a0 Crusader Squad\n\u25a0 Sword Brethren Squad\n\n\nYou can attach this model to one of the above units even if one Captain, Chapter Master, Execrator or Lieutenant model has already been attached to it. If you do, and that Bodyguard unit is destroyed, the Leader units attached to it become separate units, with their original Starting Strengths."
            }
        ]
    },
    "Crusader Squad": {
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
                "name": "Master-crafted Power Weapon",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "3",
                "skill": "2+",
                "strength": "5",
                "ap": "-2",
                "damage": "2",
                "keywords": "Lethal Hits"
            },
            {
                "name": "Pyre Pistol",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "D6",
                "skill": "N/A",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Ignores Cover, Pistol, Torrent"
            },
            {
                "name": "Neophyte Firearm",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "2",
                "skill": "3+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Assault"
            }
        ],
        "abilities": [
            {
                "name": "Righteous Zeal",
                "description": "In your opponent's Shooting phase, each time an enemy unit has shot, if any models in this unit were destroyed as a result of those attacks, this unit can make a surge move of up to D6+2."
            },
            {
                "name": "Attached Unit",
                "description": "If a CHARACTER from your army with the Leader ability can be attached to an INTERCESSOR SQUAD, it can be attached to this unit instead."
            }
        ]
    },
    "Emperor's Champion": {
        "stats": {
            "stat_movement": "8\"",
            "stat_toughness": 4,
            "stat_save": "2+",
            "stat_wounds": 5,
            "stat_leadership": "6+",
            "stat_oc": 1,
            "stat_invuln": "4+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "\u27a4 Black Sword - Strike",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "6",
                "skill": "2+",
                "strength": "8",
                "ap": "-3",
                "damage": "3",
                "keywords": "Anti-Character 5+, Precision"
            },
            {
                "name": "\u27a4 Black Sword - Sweep",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "10",
                "skill": "2+",
                "strength": "6",
                "ap": "-2",
                "damage": "1",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Armour of Faith",
                "description": "Once per phase, when an attack is allocated to this model and the saving throw is failed, you can change the Damage characteristic of that attack to 0."
            },
            {
                "name": "Sigismund's Heir",
                "description": "\u25aa When this unit declares a charge, If an enemy CHARACTER unit is within 12\" of this unit, you can use this part of this ability. If you do:\n\u25ab This unit can re-roll that charge roll.\n\u25ab This unit must end that charge move engaged with one or more of those enemy CHARACTER units.\n\n\n\u25aa (Once per battle, per army) In the Fight phase, when this unit is selected to fight, if this unit is engaged with a CHARACTER unit, you can use this part of this ability. If you do, this unit's melee attacks have [DEVASTATING WOUNDS]."
            },
            {
                "name": "Leader",
                "description": "This model can be attached to the following units:\n\n\u25a0 Assault Intercessor Squad\n\u25a0 Intercessor Squad\n\u25a0 Crusader Squad\n\u25a0 Sword Brethren\n\u25a0 Sternguard Veteran Squad"
            },
            {
                "name": "Chosen of the Emperor",
                "description": "You cannot include more than one Emperor's Champion model in your army."
            }
        ]
    },
    "Execrator": {
        "stats": {
            "stat_movement": "6\"",
            "stat_toughness": 4,
            "stat_save": "3+",
            "stat_wounds": 4,
            "stat_leadership": "5+",
            "stat_oc": 1,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Master-crafted Power Weapon",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "3",
                "skill": "2+",
                "strength": "5",
                "ap": "-2",
                "damage": "2",
                "keywords": "Extra Attacks, Lethal Hits"
            },
            {
                "name": "Pyre Pistol",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "D6",
                "skill": "N/A",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Ignores Cover, Pistol, Torrent"
            }
        ],
        "abilities": [
            {
                "name": "Leader",
                "description": "This model can be attached to the following units:\n\n\u25a0 Crusader Squad\n\u25a0 Sword Brethren"
            },
            {
                "name": "Remorseless Persecution",
                "description": "While this model is leading a unit, that unit is eligible to declare a charge in a turn in which it Advanced"
            },
            {
                "name": "Condemnatory Annihilation",
                "description": "Each time this model's unit has fought, if one or more enemy units were destroyed as a result of those attacks, each enemy unit within 6\" of this model must take a Battle-shock test"
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
            }
        ],
        "abilities": [
            {
                "name": "Aquilon Optics",
                "description": "Each time this model is selected to shoot, you can re-roll one Hit roll, you can re-roll one Wound roll and you can re-roll one Damage roll when resolving its attacks"
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
            }
        ],
        "abilities": [
            {
                "name": "Rotating Death",
                "description": "This model\u2019s twin heavy onslaught gatling cannon has the [SUSTAINED HITS 2] ability when targeting Infantry units."
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
            }
        ],
        "abilities": [
            {
                "name": "Ferocious Assault",
                "description": "Each time this model makes an attack with its twin las-talon that targets the closest eligible Monster or Vehicle unit, add 1 to the Hit roll"
            }
        ]
    },
    "High Marshal Helbrecht": {
        "stats": {
            "stat_movement": "6\"",
            "stat_toughness": 4,
            "stat_save": "2+",
            "stat_wounds": 6,
            "stat_leadership": "6+",
            "stat_oc": 3,
            "stat_invuln": "4+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "\u27a4 Sword of the High Marshals - Sweep",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "12",
                "skill": "2+",
                "strength": "6",
                "ap": "-3",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "\u27a4 Sword of the High Marshals - Strike",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "6",
                "skill": "2+",
                "strength": "8",
                "ap": "-3",
                "damage": "3",
                "keywords": "-"
            },
            {
                "name": "Ferocity",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "2",
                "skill": "2+",
                "strength": "5",
                "ap": "-1",
                "damage": "2",
                "keywords": "Anti-infantry 4+, Devastating Wounds"
            }
        ],
        "abilities": [
            {
                "name": "Crusade of Wrath",
                "description": "While this model is leading a unit, add 1 to the Attacks and Strength characteristic of melee weapons equipped by models in that unit."
            },
            {
                "name": "High Marshal",
                "description": "At the start of the Fight phase, select one enemy unit within Engagement Range of this model\u2019s unit and roll one D6, adding 1 to the result for every five models in this model's unit: on a 2-3, that enemy unit suffers D3 mortal wounds; on a 4-5, that enemy unit suffers 3 mortal wounds; on a 6, that enemy unit suffers D3+3 mortal wounds."
            },
            {
                "name": "Leader",
                "description": "This model can be attached to the following units:\n\n\u25a0 Assault Intercessor Squad\n\u25a0 Intercessor Squad\n\u25a0 Crusader Squad\n\u25a0 Sword Brethren"
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
                "name": "Ironhail Skytalon Array",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "8",
                "skill": "3+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Anti-Fly 4+, Sustained Hits 1"
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
                "name": "Legacy of Jerulas",
                "description": "In your Shooting phase, after this model has shot, select one enemy unit hit by one or more of those attacks. Until the end of the turn, each time a friendly model that disembarked from this TRANSPORT this turn makes an attack that targets that enemy unit, re-roll a Hit roll of 1 and a re-roll a Wound roll of 1"
            }
        ]
    },
    "Marshal": {
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
                "name": "Master-crafted Power Weapon",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "7",
                "skill": "2+",
                "strength": "5",
                "ap": "-2",
                "damage": "2",
                "keywords": "Lethal Hits"
            },
            {
                "name": "\u27a4 Plasma Pistol - Standard",
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
                "name": "\u27a4 Plasma Pistol - Supercharge",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "1",
                "skill": "2+",
                "strength": "8",
                "ap": "-3",
                "damage": "2",
                "keywords": "Hazardous, Pistol"
            },
            {
                "name": "Combi-weapon",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Anti-Infantry 4+, Devastating Wounds, Rapid Fire 1"
            }
        ],
        "abilities": [
            {
                "name": "Leader",
                "description": "This model can be attached to the following units:\n\n\u25a0 Assault Intercessor Squad\n\u25a0 Infernus Squad\n\u25a0 Intercessor Squad\n\u25a0 Crusader Squad\n\u25a0 Sword Brethren\n\u25a0 Sternguard Veteran Squad"
            },
            {
                "name": "Inspirational Exemplar",
                "description": "While this model is leading a unit, each time a model in that unit makes a melee attack, an unmodified Hit roll of 5+ scores a Critical Hit."
            },
            {
                "name": "Pious Fervour",
                "description": "Each time this model's unit is selected to fight, until the end of the phase, add 1 to the Attacks characteristic of this model's Master-Crafted Power Weapon for each enemy unit within 6\" of this model (to a maximum of +3)"
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
                "name": "Las-talon",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "2",
                "skill": "3+",
                "strength": "10",
                "ap": "-3",
                "damage": "D6",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Transport",
                "description": "This model has a transport capacity of 14 ADEPTUS ASTARTES INFANTRY models. Each JUMP PACK, GRAVIS or TERMINATOR model takes up the space of 2 models and each CENTURION model takes up the space of 3 models."
            },
            {
                "name": "Stabilised Disembarkation",
                "description": "In your opponent's Shooting phase, each time and enemy unit is selected to shoot, after that unit has shot, if any of those attacks targeted this TRANSPORT, it can use this ability. If it does, any units embarked within it can disembark. When doing so, models in those units can be set up wholly within 6\" of this TRANSPORT and not within Engagement Range of one or more enemy units."
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
                "name": "Heavy Laser Destroyer",
                "weapon_type": "ranged",
                "range": "72\"",
                "attacks": "2",
                "skill": "3+",
                "strength": "16",
                "ap": "-4",
                "damage": "D6+4",
                "keywords": "Heavy"
            }
        ],
        "abilities": [
            {
                "name": "Transport",
                "description": "This model has a transport capacity of 7 Adeptus Astartes Infantry models. Each Jump Pack, Wulfen, Gravis or Terminator model takes up the space of 2 models and each Centurion model takes up the space of 3 models."
            },
            {
                "name": "Interception Strike",
                "description": "Each time this model makes a ranged attack that targets a unit that is within 12\" of one or more ADEPTUS ASTARTES units from your army, you can re-roll the Hit roll."
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
                "name": "Power Weapon",
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
                "name": "Power Fist",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "3+",
                "strength": "8",
                "ap": "-2",
                "damage": "2",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Vitruous Onslaught",
                "description": "Each time a model in this unit makes an attack that targets the closest eligible target, you can re-roll a Wound roll of 1."
            }
        ]
    },
    "Sword Brethren Squad": {
        "stats": {
            "stat_movement": "6\"",
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
                "name": "Pyre Pistol",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "D6",
                "skill": "N/A",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Ignores Cover, Pistol, Torrent"
            },
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
                "name": "Master-crafted Power Weapon",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "3",
                "skill": "2+",
                "strength": "5",
                "ap": "-2",
                "damage": "2",
                "keywords": "Lethal Hits"
            },
            {
                "name": "Astartes Chainsword",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "6",
                "skill": "2+",
                "strength": "4",
                "ap": "-1",
                "damage": "1",
                "keywords": "Sustained Hits 1"
            },
            {
                "name": "Twin Lightning Claws",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "5",
                "skill": "2+",
                "strength": "5",
                "ap": "-2",
                "damage": "1",
                "keywords": "Twin-linked"
            }
        ],
        "abilities": [
            {
                "name": "Exploit Their Cowardice",
                "description": "Each time an enemy unit within Engagement Range of this unit is selected to Fall Back, after it ends that Fall Back move, if this unit is not within Engagement Range of one or more enemy units, this unit can make a Normal move."
            },
            {
                "name": "Attached Unit",
                "description": "If a CHARACTER from your army with the Leader ability can be attached to an INTERCESSOR SQUAD, it can be attached to this unit instead."
            },
            {
                "name": "Fervent Exemplars",
                "description": "SWORD BRETHREN SQUAD unit only. This unit has +1 to charge rolls"
            },
            {
                "name": "Inheritors of Sigismund",
                "description": "SWORD BRETHREN SQUAD unit only. This unit has Fights First"
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
                "name": "Power Fist",
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
                "name": "Teleport Homer",
                "description": "At the start of the battle, you can set up one Teleport Homer token for this unit anywhere on the battlefield that is not in your opponent\u2019s deployment zone. If you do, once per battle, you can target this unit with the Rapid Ingress Stratagem for 0CP, but when resolving that Stratagem, you must set this unit up within 3\" horizontally of that token and not within 8\" horizontally of any enemy models. That token is then removed."
            },
            {
                "name": "Judgement of the Weak",
                "description": "Each time an enemy unit (excluding MONSTERS and VEHICLES) within engagement range of this unit Falls Back, all models in that enemy unit must take a Desperate Escape test. When doing so, if that enemy unit is Battle-shocked, subtract 1 from each of those tests."
            }
        ]
    }
}


class Command(BaseCommand):
    """Refresh Black Templars stat lines, weapon profiles, and abilities from BSData."""

    help = 'Refresh 11th Edition stats/weapons/abilities for Black-Templars-exclusive units.'

    def add_arguments(self, parser):
        """Add --dry-run flag."""
        parser.add_argument(
            '--dry-run', action='store_true',
            help='Preview changes without writing to the database.',
        )

    def handle(self, *args, **options):
        """Iterate BLACK_TEMPLARS_DATASHEETS and refresh each unit's datasheet data."""
        dry_run = options['dry_run']
        updated = 0
        skipped = 0

        with transaction.atomic():
            for name, payload in BLACK_TEMPLARS_DATASHEETS.items():
                try:
                    unit = UnitType.objects.get(name=name, faction__name='Black Templars')
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
