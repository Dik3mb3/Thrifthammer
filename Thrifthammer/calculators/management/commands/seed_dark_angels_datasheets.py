"""
Management command: seed_dark_angels_datasheets

Refreshes stat lines, weapon profiles, and abilities for the
Dark-Angels-exclusive units using 11th Edition data sourced from
BSData/wh40k-11e ("Imperium - Dark Angels.json") -- the same source used
by seed_dark_angels_points.py.

Usage:
    python manage.py seed_dark_angels_datasheets
    python manage.py seed_dark_angels_datasheets --dry-run

Notes:
- Does NOT touch points_cost or category -- those are handled entirely by
  seed_dark_angels_points.py. This command only refreshes stat_* fields,
  WeaponProfile rows, and UnitAbility rows.
- Scope is the 16 DA-exclusive rows only -- generic squads inherit their
  datasheets from the base Space Marines faction automatically.
  Judiciar/Suppressor Squad are out of scope -- productless placeholders
  with no DA-specific datasheet source.
- Per-field safety rule: a unit's stats/weapons/abilities are only
  overwritten when BSData actually has that data for it. If extraction
  found nothing, the existing DB value/rows are left untouched.
- All 16 active units resolved cleanly -- 0 missing stats/weapons/
  abilities, 0 overlong stat fields, 0 markdown artifacts.
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from calculators.models import UnitAbility, UnitType, WeaponProfile

# (name -> {stats?, weapons?, abilities?}). Missing keys mean "no data
# found for this field -- leave existing DB data untouched."
DARK_ANGELS_DATASHEETS = {
    "Asmodai": {
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
                "name": "\u27a4 Crozius Arcanum and Power Weapon - strike",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "5",
                "skill": "2+",
                "strength": "6",
                "ap": "-2",
                "damage": "2",
                "keywords": "-"
            },
            {
                "name": "\u27a4 Crozius Arcanum and Power Weapon - sweep",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "8",
                "skill": "2+",
                "strength": "5",
                "ap": "-2",
                "damage": "1",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Exemplar of Hate",
                "description": "While this model is leading a unit, each time a model in that unit makes a melee attack, you can re-roll the Hit roll."
            },
            {
                "name": "Feared Interrogator",
                "description": "At the start of the Fight phase, each enemy Character unit within 6\" of this model must take a Battle-shock test, subtracting 1 from that test when they do. In addition, each time this model destroys an enemy Character model with a melee attack, you gain 1CP."
            },
            {
                "name": "Leader",
                "description": "This model can be attached to the following units:\n\u25a0 Assault Intercessor Squad\n\u25a0 Bladeguard Veteran Squad\n\u25a0 Hellblaster Squad\n\u25a0 Infernus Squad\n\u25a0 Inner Circle Companions\n\u25a0 Intercessor Squad\n\u25a0 Sternguard Veteran Squad\n\u25a0 Tactical Squad"
            }
        ]
    },
    "Azrael": {
        "stats": {
            "stat_movement": "6\"",
            "stat_toughness": 4,
            "stat_save": "2+",
            "stat_wounds": 6,
            "stat_leadership": "6+",
            "stat_oc": 1,
            "stat_invuln": "4+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Lion's Wrath",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "2",
                "skill": "2+",
                "strength": "8",
                "ap": "-3",
                "damage": "2",
                "keywords": "Anti-Infantry 4+, Devastating Wounds, Rapid Fire 1"
            },
            {
                "name": "The Sword of Secrets",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "6",
                "skill": "2+",
                "strength": "6",
                "ap": "-4",
                "damage": "2",
                "keywords": "Devastating Wounds"
            }
        ],
        "abilities": [
            {
                "name": "Supreme Grand Master",
                "description": "While this model is leading a unit, weapons equipped by models in that unit have the [SUSTAINED HITS 1] ability."
            },
            {
                "name": "Masterful Tactician",
                "description": "At the start of your Command phase, if this model is on the battlefield, you gain 1CP."
            },
            {
                "name": "The Lion Helm",
                "description": "Models in the bearer\u2019s unit have a 4+ invulnerable save. In addition, once per battle, in any phase, the bearer can summon a Watcher in the Dark. When it does, until the end of the phase, models in the bearer\u2019s unit have the Feel No Pain 4+ ability against mortal wounds."
            },
            {
                "name": "Leader",
                "description": "This model can be attached to the following units:\n\u25a0 Assault Intercessor Squad\n\u25a0 Bladeguard Veteran Squad\n\u25a0 Hellblaster Squad\n\u25a0 Infernus Squad\n\u25a0 Inner Circle Companions\n\u25a0 Intercessor Squad\n\u25a0 Sternguard Veteran Squad\n\u25a0 Tactical Squad"
            }
        ]
    },
    "Belial": {
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
                "name": "Master-crafted storm bolter",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "2",
                "skill": "2+",
                "strength": "4",
                "ap": "0",
                "damage": "2",
                "keywords": "Precision, Rapid Fire 2"
            },
            {
                "name": "The Sword of Silence",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "6",
                "skill": "2+",
                "strength": "6",
                "ap": "-2",
                "damage": "2",
                "keywords": "Precision"
            }
        ],
        "abilities": [
            {
                "name": "Grand Master of the Deathwing",
                "description": "While this model is leading a unit, each time a model in that unit makes an attack, if a Critical Hit is scored, that attack has the [PRECISION] ability."
            },
            {
                "name": "Strikes of Retribution",
                "description": "Each time a melee attack is allocated to this model, after the attacking model\u2019s unit has finished making its attacks, roll one D6 (to a maximum of six D6 per attacking unit): for each 4+, the attacking unit suffers 1 mortal wound."
            },
            {
                "name": "Leader",
                "description": "This unit can be attached to the following units:\n\u25a0 Deathwing Knights\n\u25a0 Deathwing Terminator Squad\n\u25a0 Terminator Assault Squad\n\u25a0 Terminator Squad"
            }
        ]
    },
    "Deathwing Knights": {
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
                "name": "Mace of absolution",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "2+",
                "strength": "6",
                "ap": "-2",
                "damage": "2",
                "keywords": "Anti-Monster 4+, Anti-Vehicle 4+"
            },
            {
                "name": "Power Weapon",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "5",
                "skill": "2+",
                "strength": "6",
                "ap": "-2",
                "damage": "2",
                "keywords": "-"
            },
            {
                "name": "Great Weapon of the Unforgiven",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "5",
                "skill": "2+",
                "strength": "6",
                "ap": "-2",
                "damage": "2",
                "keywords": "Devastating Wounds, Sustained Hits 1"
            },
            {
                "name": "Relic Weapon",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "6",
                "skill": "2+",
                "strength": "7",
                "ap": "-2",
                "damage": "2",
                "keywords": "Lethal Hits"
            }
        ],
        "abilities": [
            {
                "name": "Inner Circle",
                "description": "Each time an attack is allocated to a model in this unit, subtract 1 from the Damage characteristic of that attack."
            },
            {
                "name": "Attached Unit",
                "description": "If a Character unit from your army with the Leader ability can be attached to a Terminator Squad, it can be attached to this unit instead."
            },
            {
                "name": "Teleport Homer",
                "description": "At the start of the battle, you can set up one Teleport Homer token for this unit anywhere on the battlefield that is not in your opponent\u2019s deployment zone. If you do, once per battle, you can target this unit with the Rapid Ingress Stratagem for 0CP, but when resolving that Stratagem, you must set this unit up within 3\" horizontally of that token and not within 8\" horizontally of any enemy models. That token is then removed."
            },
            {
                "name": "Watcher in the Dark",
                "description": "Once per battle, in any phase, just after a mortal wound is allocated to an Adeptus Astartes model in this unit, this unit can summon a Watcher in the Dark. When it does, until the end of the phase, models in this unit have the Feel No Pain 4+ ability against mortal wounds."
            }
        ]
    },
    "Deathwing Terminator Squad": {
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
                "name": "Power Weapon",
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
                "name": "Power Fist",
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
                "name": "Chainfist",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "3",
                "skill": "4+",
                "strength": "8",
                "ap": "-2",
                "damage": "2",
                "keywords": "Anti-Vehicle 3+"
            }
        ],
        "abilities": [
            {
                "name": "Deathwing",
                "description": "Each time a model in this unit makes an attack, you can ignore any or all modifiers to that attack\u2019s Ballistic Skill or Weapon Skill characteristics and/or to the Hit roll.\nIn addition, each time a model in this unit makes an attack that targets your Oath of Moment target (see Codex: Space Marines), add 1 to the Hit roll."
            },
            {
                "name": "Attached Unit",
                "description": "If a Character unit from your army with the Leader ability can be attached to a Terminator Squad, it can be attached to this unit instead."
            },
            {
                "name": "Teleport Homer",
                "description": "At the start of the battle, you can set up one Teleport Homer token for this unit anywhere on the battlefield that is not in your opponent\u2019s deployment zone. If you do, once per battle, you can target this unit with the Rapid Ingress Stratagem for 0CP, but when resolving that Stratagem, you must set this unit up within 3\" horizontally of that token and not within 8\" horizontally of any enemy models. That token is then removed."
            },
            {
                "name": "Watcher in the Dark",
                "description": "Once per battle, in any phase, just after a mortal wound is allocated to an Adeptus Astartes model in this unit, this unit can summon a Watcher in the Dark. When it does, until the end of the phase, models in this unit have the Feel No Pain 4+ ability against mortal wounds."
            }
        ]
    },
    "Ezekiel": {
        "stats": {
            "stat_movement": "6\"",
            "stat_toughness": 4,
            "stat_save": "2+",
            "stat_wounds": 4,
            "stat_leadership": "6+",
            "stat_oc": 1,
            "stat_invuln": "4+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "The Deliverer",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "1",
                "skill": "2+",
                "strength": "4",
                "ap": "-1",
                "damage": "2",
                "keywords": "Pistol, Precision"
            },
            {
                "name": "\u27a4 Mind Wipe - witchfire",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "1",
                "skill": "2+",
                "strength": "6",
                "ap": "-2",
                "damage": "D6",
                "keywords": "Devastating Wounds, Precision, Psychic"
            },
            {
                "name": "\u27a4 Mind Wipe - focussed witchfire",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "1",
                "skill": "2+",
                "strength": "6",
                "ap": "-2",
                "damage": "D6",
                "keywords": "Anti-Character 4+, Devastating Wounds, Hazardous, Precision, Psychic"
            },
            {
                "name": "Traitor's Bane",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "2+",
                "strength": "6",
                "ap": "-2",
                "damage": "D3",
                "keywords": "Anti-Chaos 2+, Psychic"
            }
        ],
        "abilities": [
            {
                "name": "Engulfing Fear [Psychic]",
                "description": "In your Shooting phase, you can select one enemy unit within 18\" of this model. That enemy unit must take a Battle-shock test."
            },
            {
                "name": "Book of Salvation",
                "description": "While this model is leading a unit, add 1 to the Attacks characteristic of melee weapons equipped by models in that unit. When this model is destroyed, each friendly Adeptus Astartes unit within 6\" of this model must take a Battle-shock test."
            },
            {
                "name": "Leader",
                "description": "This model can be attached to the following units:\n\u25a0 Assault Intercessor Squad\n\u25a0 Bladeguard Veteran Squad\n\u25a0 Hellblaster Squad\n\u25a0 Infernus Squad\n\u25a0 Inner Circle Companions\n\u25a0 Intercessor Squad\n\u25a0 Sternguard Veterans Squad\n\u25a0 Tactical Squad"
            }
        ]
    },
    "Inner Circle Companions": {
        "stats": {
            "stat_movement": "6\"",
            "stat_toughness": 4,
            "stat_save": "3+",
            "stat_wounds": 3,
            "stat_leadership": "6+",
            "stat_oc": 2,
            "stat_invuln": "",
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
                "name": "\u27a4 Calibanite Greatsword - Strike",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "3+",
                "strength": "6",
                "ap": "-2",
                "damage": "2",
                "keywords": "Lethal Hits"
            },
            {
                "name": "\u27a4 Calibanite Greatsword - Sweep",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "5",
                "skill": "3+",
                "strength": "6",
                "ap": "-2",
                "damage": "1",
                "keywords": "Sustained Hits 2"
            }
        ],
        "abilities": [
            {
                "name": "Attached Unit",
                "description": "If a Character unit from your army with the Leader ability can be attached to a Sternguard Veteran Squad, it can be attached to this unit instead."
            },
            {
                "name": "Braziers of Judgement",
                "description": "\u25aa This unit has Stealth.\n\u25aa Melee attacks that target this unit have -1 to hit rolls."
            },
            {
                "name": "Emnity for the Unworthy",
                "description": "Each time a model in this unit makes an attack that targets a Character unit, add 1 to the Hit roll."
            }
        ]
    },
    "Land Speeder Vengeance": {
        "stats": {
            "stat_movement": "14\"",
            "stat_toughness": 8,
            "stat_save": "3+",
            "stat_wounds": 10,
            "stat_leadership": "6+",
            "stat_oc": 3,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Close Combat Weapon",
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
                "name": "\u27a4 Plasma storm battery - standard",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "D6+1",
                "skill": "3+",
                "strength": "8",
                "ap": "-2",
                "damage": "2",
                "keywords": "Blast, Twin-Linked"
            },
            {
                "name": "\u27a4 Plasma storm battery - supercharge",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "D6+1",
                "skill": "3+",
                "strength": "9",
                "ap": "-3",
                "damage": "3",
                "keywords": "Blast, Hazardous, Twin-Linked"
            },
            {
                "name": "Assault cannon",
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
                "name": "Heavy bolter",
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
                "name": "Invulnerable Save",
                "description": "5+"
            },
            {
                "name": "Storm of Vengeance",
                "description": "Once per turn, in your opponent\u2019s Shooting phase, when another friendly Adeptus Astartes unit within 6\" of this model is destroyed, one model with this ability can use it. If it does, after the attacking unit has finished making its attacks, that model can shoot as if it were your Shooting phase, but when resolving those attacks it can only target that enemy unit (and only if it is an eligible target)."
            }
        ]
    },
    "Lazarus": {
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
                "name": "Enmity\u2019s Edge",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "6",
                "skill": "2+",
                "strength": "6",
                "ap": "-3",
                "damage": "2",
                "keywords": "Anti-Psyker 2+"
            }
        ],
        "abilities": [
            {
                "name": "Intractable Will",
                "description": "While this model is leading a unit, each time a model in that unit is destroyed by a melee attack, if that model has not fought this phase, roll one D6. On a 4+, do not remove it from play; that destroyed model can fight after the attacking unit has finished making its attacks, and is then removed from play."
            },
            {
                "name": "The Spiritshield Helm",
                "description": "This model has the Feel No Pain 3+ ability against Psychic Attacks and mortal wounds."
            },
            {
                "name": "Leader",
                "description": "This model can be attached to the following units:\n\u25a0 Assault Intercessor Squad\n\u25a0 Bladeguard Veteran Squad\n\u25a0 Infernus Squad\n\u25a0 Inner Circle Companions\n\u25a0 Intercessor Squad\n\u25a0 Sternguard Veteran Squad\n\u25a0 Tactical Squad"
            }
        ]
    },
    "Lion El'Jonson": {
        "stats": {
            "stat_movement": "8\"",
            "stat_toughness": 9,
            "stat_save": "2+",
            "stat_wounds": 10,
            "stat_leadership": "5+",
            "stat_oc": 4,
            "stat_invuln": "3+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "\u27a4 Arma Luminis - bolt",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "4",
                "skill": "2+",
                "strength": "4",
                "ap": "-1",
                "damage": "2",
                "keywords": "Pistol"
            },
            {
                "name": "\u27a4 Arma Luminis - plasma",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "2",
                "skill": "2+",
                "strength": "8",
                "ap": "-3",
                "damage": "2",
                "keywords": "Pistol"
            },
            {
                "name": "\u27a4 Fealty - strike",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "8",
                "skill": "2+",
                "strength": "12",
                "ap": "-4",
                "damage": "4",
                "keywords": "Lethal Hits"
            },
            {
                "name": "\u27a4 Fealty - sweep",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "16",
                "skill": "2+",
                "strength": "6",
                "ap": "-3",
                "damage": "2",
                "keywords": "Sustained Hits 1"
            }
        ],
        "abilities": [
            {
                "name": "Primarch of the First Legion",
                "description": "At the start of your Command phase, select two Primarch of the First Legion abilities. Until the start of your next Command phase, this model has those abilities."
            },
            {
                "name": "The Emperor's Shield",
                "description": "Each time an attack is allocated to this model, if the Strength characteristic of that attack is greater than the Toughness characteristic of this model, subtract 1 from the Wound roll."
            },
            {
                "name": "Dark Angels Bodyguard",
                "description": "While this model is within 3\" of one or more friendly Adeptus Astartes Infantry units, this model has the Lone Operative ability."
            }
        ]
    },
    "Nephilim Jetfighter": {
        "stats": {
            "stat_movement": "-",
            "stat_toughness": 8,
            "stat_save": "3+",
            "stat_wounds": 11,
            "stat_leadership": "6+",
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
                "name": "Blacksword missiles",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "2",
                "skill": "3+",
                "strength": "8",
                "ap": "-2",
                "damage": "D6",
                "keywords": "Anti-Fly 2+"
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
                "keywords": "Sustained Hits 1, Twin-Linked"
            },
            {
                "name": "Avenger mega bolter",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "10",
                "skill": "3+",
                "strength": "5",
                "ap": "-1",
                "damage": "2",
                "keywords": "Sustained Hits 1"
            },
            {
                "name": "Nephilim lascannons",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "2",
                "skill": "3+",
                "strength": "12",
                "ap": "-3",
                "damage": "D6+1",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Lightning-fast Manoeuvres",
                "description": "Ranged attacks that target this unit have -1 to wound rolls"
            },
            {
                "name": "Damaged: 1-3 Wounds Remaining",
                "description": "While this model has 1-3 wounds remaining, each time this model makes an attack, subtract 1 from the Hit roll."
            },
            {
                "name": "Invulnerable Save",
                "description": "5+"
            }
        ]
    },
    "Ravenwing Black Knights": {
        "stats": {
            "stat_movement": "12\"",
            "stat_toughness": 5,
            "stat_save": "3+",
            "stat_wounds": 3,
            "stat_leadership": "6+",
            "stat_oc": 2,
            "stat_invuln": "5+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Bolt Pistol",
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
                "name": "Black Knight combat weapon",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "3",
                "skill": "3+",
                "strength": "5",
                "ap": "-2",
                "damage": "1",
                "keywords": "Devastating Wounds"
            },
            {
                "name": "\u27a4 Plasma talon - Standard",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "2",
                "skill": "3+",
                "strength": "7",
                "ap": "-2",
                "damage": "1",
                "keywords": "Rapid Fire 1"
            },
            {
                "name": "\u27a4 Plasma talon - Supercharged",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "2",
                "skill": "3+",
                "strength": "8",
                "ap": "-3",
                "damage": "2",
                "keywords": "Hazardous, Rapid Fire 1"
            }
        ],
        "abilities": [
            {
                "name": "Knights of Caliban",
                "description": "Each time this unit is selected to fight, if it made a Charge move this turn, until the end of the phase, melee weapons equipped by models in this unit have the [ANTI-MONSTER 4+] and [ANTI-VEHICLE 4+] abilities."
            },
            {
                "name": "Attached Unit",
                "description": "If a Character unit from your army with the Leader ability can be attached to an Outrider Squad, it can be attached to this unit instead."
            }
        ]
    },
    "Ravenwing Command Squad": {
        "stats": {
            "stat_movement": "12\"",
            "stat_toughness": 5,
            "stat_save": "3+",
            "stat_wounds": 4,
            "stat_leadership": "6+",
            "stat_oc": 2,
            "stat_invuln": "5+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Bolt Pistol",
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
                "name": "Black Knight combat weapon",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "3",
                "skill": "3+",
                "strength": "5",
                "ap": "-2",
                "damage": "1",
                "keywords": "Devastating Wounds"
            },
            {
                "name": "\u27a4 Plasma talon - Standard",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "2",
                "skill": "3+",
                "strength": "7",
                "ap": "-2",
                "damage": "1",
                "keywords": "Rapid Fire 1"
            },
            {
                "name": "\u27a4 Plasma talon - Supercharged",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "2",
                "skill": "3+",
                "strength": "8",
                "ap": "-3",
                "damage": "2",
                "keywords": "Hazardous, Rapid Fire 1"
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
            }
        ],
        "abilities": [
            {
                "name": "Support",
                "description": "This unit can be attached to the following units:\n\u25a0 Outrider Squad\n\u25a0 Ravenwing Black Knights"
            },
            {
                "name": "Narthecium",
                "description": "While this unit contains a Ravenwing Apothecary, in your Command phase, you can return 1 destroyed model (excluding Character and Invader ATV models) to this unit."
            },
            {
                "name": "Astartes Banner",
                "description": "While this unit contains a Ravenwing Ancient, add 1 to the Objective Control characteristic of models in this unit."
            },
            {
                "name": "Honour or Death",
                "description": "While this unit contains a Ravenwing Champion, add 1 to Advance and Charge rolls made for this unit and you can target this unit with the Heroic Intervention Stratagem for 0CP."
            }
        ]
    },
    "Ravenwing Dark Talon": {
        "stats": {
            "stat_movement": "-",
            "stat_toughness": 8,
            "stat_save": "3+",
            "stat_wounds": 11,
            "stat_leadership": "6+",
            "stat_oc": None,
            "stat_invuln": "5+",
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
                "name": "Hurricane bolter",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "6",
                "skill": "3+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Rapid Fire 6, Twin-Linked"
            },
            {
                "name": "Rift cannon",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "D3+1",
                "skill": "3+",
                "strength": "16",
                "ap": "-4",
                "damage": "3",
                "keywords": "Blast, Devastating Wounds"
            }
        ],
        "abilities": [
            {
                "name": "Stasis Bomb",
                "description": "At the end of your opponent\u2019s Fight phase, select one visible enemy unit (excluding AIRCRAFT/Lone Operative units) within 24\" of this unit. That enemy unit is slowed until the end of your opponent\u2019s next Movement phase:\n\n\n\u25aa While a unit is slowed, in your opponent\u2019s Movement phase, when that unit is selected to move, unless that unit remains stationary, roll one D6:\n\u25ab On a 1-4, that unit suffers D3 mortal wounds and that unit has -2\" M.\n\u25ab On a 5-6, that unit suffers 2D3 mortal wounds and that unit has -3\" M.\u2019"
            },
            {
                "name": "Damaged: 1-3 Wounds Remaining",
                "description": "While this model has 1-3 wounds remaining, each time this model makes an attack, subtract 1 from the Hit roll."
            }
        ]
    },
    "Ravenwing Darkshroud": {
        "stats": {
            "stat_movement": "14\"",
            "stat_toughness": 8,
            "stat_save": "3+",
            "stat_wounds": 10,
            "stat_leadership": "6+",
            "stat_oc": 3,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Close Combat Weapon",
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
                "name": "Assault cannon",
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
                "name": "Heavy bolter",
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
                "name": "Invulnerable Save",
                "description": "5+"
            },
            {
                "name": "Icon of Old Caliban (Aura)",
                "description": "Friendly ADEPTUS ASTARTES units within 6\" of this unit have Stealth"
            }
        ]
    },
    "Sammael": {
        "stats": {
            "stat_movement": "12\"",
            "stat_toughness": 5,
            "stat_save": "3+",
            "stat_wounds": 7,
            "stat_leadership": "6+",
            "stat_oc": 2,
            "stat_invuln": "4+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Bolt Pistol",
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
                "name": "Master-crafted plasma cannon",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "D3",
                "skill": "2+",
                "strength": "8",
                "ap": "-3",
                "damage": "2",
                "keywords": "Blast"
            },
            {
                "name": "Twin storm bolter",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "2",
                "skill": "2+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Rapid Fire 2, Twin-Linked"
            },
            {
                "name": "The Raven Sword",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "6",
                "skill": "2+",
                "strength": "6",
                "ap": "-3",
                "damage": "2",
                "keywords": "Sustained Hits 2"
            }
        ],
        "abilities": [
            {
                "name": "Leader",
                "description": "This model can be attached to the following units:\n\u25a0 Outrider Squad\n\u25a0 Ravenwing Black Knights"
            },
            {
                "name": "Grand Master of the Ravenwing",
                "description": "\u25aa This unit\u2019s ranged attacks have [ASSAULT].\n\u25aa When this unit is selected to make an advance move, that advance move does not prevent this unit from being eligible to declare a charge.\n\u25aa This unit has MOBILE"
            },
            {
                "name": "Cut Off Their Escape",
                "description": "Each time an enemy unit (excluding Monsters and Vehicles) within Engagement Range of this model\u2019s unit is selected to Fall Back, models in that enemy unit must take Desperate Escape tests as if their unit was Battle-shocked. When doing so, if that enemy unit is also Battle-shocked by other means, subtract 1 from each of those Desperate Escape tests."
            }
        ]
    }
}


class Command(BaseCommand):
    """Refresh Dark Angels stat lines, weapon profiles, and abilities from BSData."""

    help = 'Refresh 11th Edition stats/weapons/abilities for Dark-Angels-exclusive units.'

    def add_arguments(self, parser):
        """Add --dry-run flag."""
        parser.add_argument(
            '--dry-run', action='store_true',
            help='Preview changes without writing to the database.',
        )

    def handle(self, *args, **options):
        """Iterate DARK_ANGELS_DATASHEETS and refresh each unit's datasheet data."""
        dry_run = options['dry_run']
        updated = 0
        skipped = 0

        with transaction.atomic():
            for name, payload in DARK_ANGELS_DATASHEETS.items():
                try:
                    unit = UnitType.objects.get(name=name, faction__name='Dark Angels')
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
