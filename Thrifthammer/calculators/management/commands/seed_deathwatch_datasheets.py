"""
Management command: seed_deathwatch_datasheets

Refreshes stat lines, weapon profiles, and abilities for the
Deathwatch-exclusive units using 11th Edition data sourced from
BSData/wh40k-11e ("Imperium - Deathwatch.json") -- the same source used
by seed_deathwatch_points.py.

Usage:
    python manage.py seed_deathwatch_datasheets
    python manage.py seed_deathwatch_datasheets --dry-run

Notes:
- Does NOT touch points_cost or category -- those are handled entirely by
  seed_deathwatch_points.py. This command only refreshes stat_* fields,
  WeaponProfile rows, and UnitAbility rows.
- Scope is the 10 DW-exclusive rows only -- generic squads inherit their
  datasheets from the base Space Marines faction automatically.
  Judiciar/Suppressor Squad are out of scope -- productless placeholders
  with no DW-specific datasheet source.
- Per-field safety rule: a unit's stats/weapons/abilities are only
  overwritten when BSData actually has that data for it. If extraction
  found nothing, the existing DB value/rows are left untouched.
- All 10 active units resolved cleanly -- 0 missing stats/weapons/
  abilities, 0 overlong stat fields, 0 markdown artifacts.
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from calculators.models import UnitAbility, UnitType, WeaponProfile

# (name -> {stats?, weapons?, abilities?}). Missing keys mean "no data
# found for this field -- leave existing DB data untouched."
DEATHWATCH_DATASHEETS = {
    "Corvus Blackstar": {
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
                "name": "Twin assault cannon",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "6",
                "skill": "3+",
                "strength": "6",
                "ap": "0",
                "damage": "1",
                "keywords": "Devastating Wounds, Twin-Linked"
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
                "keywords": "Twin-Linked"
            },
            {
                "name": "Blackstar rocket launcher",
                "weapon_type": "ranged",
                "range": "30\"",
                "attacks": "D6+1",
                "skill": "3+",
                "strength": "5",
                "ap": "0",
                "damage": "1",
                "keywords": "Blast"
            },
            {
                "name": "Stormstrike missile launcher",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "10",
                "ap": "-2",
                "damage": "3",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Blackstar Cluster Launcher",
                "description": "Each time this model ends a Normal move, you can select one enemy unit it moved over during that move and roll six D6: for each 5+, that unit suffers 1 mortal wound."
            },
            {
                "name": "Damaged: 1-5 Wounds Remaining",
                "description": "While this model has 1-5 wounds remaining, each time this model makes an attack, subtract 1 from the Hit roll."
            },
            {
                "name": "Transport",
                "description": "This model has a transport capacity of 12 ADEPTUS ASTARTES INFANTRY or KILL TEAM models. Each JUMP PACK, GRAVIS or TERMINATOR model takes up the space of 2 models and each CENTURION model takes up the space of 3 models."
            },
            {
                "name": "Auspex Array",
                "description": "Ranged weapons equipped by the bearer have the [IGNORES COVER] ability."
            },
            {
                "name": "Infernum Halo-launcher",
                "description": "The bearer has the SMOKE keyword."
            }
        ]
    },
    "Deathwatch Terminator Squad": {
        "stats": {
            "stat_movement": "5\"",
            "stat_toughness": 5,
            "stat_save": "2+",
            "stat_wounds": 3,
            "stat_leadership": "6+",
            "stat_oc": 1,
            "stat_invuln": "",
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
                "name": "Chainfist",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "3",
                "skill": "4+",
                "strength": "8+",
                "ap": "-2",
                "damage": "2",
                "keywords": "Anti-Vehicle 3+"
            }
        ],
        "abilities": [
            {
                "name": "Terminatus Assault",
                "description": "You can re-roll Charge rolls made for this unit. Each time this unit ends a Charge move, each enemy unit within Engagement Range of this unit must take a Battle-shock test. If that enemy unit does not have the IMPERIUM or CHAOS keywords, subtract 1 from that test."
            },
            {
                "name": "Teleport Homer",
                "description": "At the start of the battle, you can set up one Teleport Homer token for this unit anywhere on the battlefield that is not in your opponent\u2019s deployment zone. If you do, once per battle, you can target this unit with the Rapid Ingress Stratagem for 0CP, but when resolving that Stratagem, you must set this unit up within 3\" of that token and not within 9\" of any enemy models. That token is then removed."
            },
            {
                "name": "Invulnerable Save",
                "description": "Models in this unit have a 4+ invulnerable save."
            },
            {
                "name": "Attached Unit",
                "description": "If a CHARACTER unit from your army with the Leader ability can be attached to a TERMINATOR SQUAD, it can be attached to this unit instead."
            },
            {
                "name": "Storm Shield",
                "description": "The bearer has a Wounds characteristic of 4."
            }
        ]
    },
    "Deathwatch Veterans": {
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
                "name": "Boltgun",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "2",
                "skill": "3",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "-"
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
                "name": "Deathwatch thunder hammer",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "3",
                "skill": "4+",
                "strength": "10",
                "ap": "-2",
                "damage": "3",
                "keywords": "Devastating Wounds"
            },
            {
                "name": "Frag cannon",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "D3",
                "skill": "4+",
                "strength": "7",
                "ap": "-1",
                "damage": "2",
                "keywords": "Blast, Heavy, Rapid Fire D3"
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
                "name": "\u27a4 Infernus heavy bolter - heavy bolter",
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
                "name": "\u27a4 Infernus heavy bolter - heavy flamer",
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
                "name": "Stalker-pattern boltgun",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "4",
                "ap": "-1",
                "damage": "2",
                "keywords": "Heavy, Precision"
            },
            {
                "name": "Deathwatch shotgun",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "2",
                "skill": "3+",
                "strength": "4",
                "ap": "0",
                "damage": "2",
                "keywords": "Assault"
            },
            {
                "name": "Blackshield blades",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "3+",
                "strength": "5",
                "ap": "-2",
                "damage": "1",
                "keywords": "Twin-linked"
            },
            {
                "name": "Xenophase blade",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "3+",
                "strength": "5",
                "ap": "-2",
                "damage": "1",
                "keywords": "Devastating Wounds"
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
                "name": "Death to the Alien",
                "description": "Each time a model in this unit makes an attack, re-roll a Hit roll of 1. If the target of that attack does not have the IMPERIUM or CHAOS keywords, you can re-roll the Hit roll instead."
            },
            {
                "name": "Attached Unit",
                "description": "If a CHARACTER unit from your army with the Leader ability can be attached to a STERNGUARD VETERAN SQUAD, it can be attached to this unit instead."
            },
            {
                "name": "Astartes shield",
                "description": "The bearer has a 4+ invulnerable save."
            }
        ]
    },
    "Decimus Kill Team": {
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
                "name": "\u27a4 Plasma pistol - Standard",
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
                "name": "\u27a4 Plasma pistol - Supercharge",
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
                "name": "Power weapon",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "3+",
                "strength": "5",
                "ap": "-2",
                "damage": "2",
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
                "keywords": "Pistol, Lethal Hits"
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
                "name": "Stalker bolt rifle",
                "weapon_type": "ranged",
                "range": "30\"",
                "attacks": "2",
                "skill": "3+",
                "strength": "5",
                "ap": "-2",
                "damage": "2",
                "keywords": "Heavy, Lethal Hits, Precision"
            },
            {
                "name": "\u27a4 Plasma incinerator - Standard",
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
                "name": "\u27a4 Plasma incinerator - Supercharge",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "2",
                "skill": "3+",
                "strength": "8",
                "ap": "-3",
                "damage": "2",
                "keywords": "Assault, Hazardous, Heavy"
            },
            {
                "name": "Heavy thunder hammer",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "3",
                "skill": "4+",
                "strength": "10",
                "ap": "-2",
                "damage": "3",
                "keywords": "Devastating Wounds"
            },
            {
                "name": "Special-issue bolt pistol",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "4",
                "ap": "-1",
                "damage": "1",
                "keywords": "Pistol, Precision, Lethal Hits"
            },
            {
                "name": "Deathwatch marksman bolt carbine",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "2",
                "skill": "3+",
                "strength": "5",
                "ap": "-1",
                "damage": "1",
                "keywords": "Heavy, Lethal Hits"
            },
            {
                "name": "Combat knife",
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
                "name": "Frag cannon",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "D3",
                "skill": "3+",
                "strength": "7",
                "ap": "-2",
                "damage": "2",
                "keywords": "Blast, Heavy, Lethal Hits, Rapid Fire D3"
            },
            {
                "name": "Hellstorm bolt rifle",
                "weapon_type": "ranged",
                "range": "30\"",
                "attacks": "2",
                "skill": "3+",
                "strength": "5",
                "ap": "-2",
                "damage": "2",
                "keywords": "Assault, Heavy, Lethal Hits"
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
                "name": "\u27a4 Infernus heavy bolter - heavy bolter",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "3",
                "skill": "3+",
                "strength": "5",
                "ap": "-2",
                "damage": "3",
                "keywords": "Sustained Hits 1"
            },
            {
                "name": "\u27a4 Infernus heavy bolter - heavy flamer",
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
                "name": "Xenophase blade",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "3+",
                "strength": "5",
                "ap": "-2",
                "damage": "1",
                "keywords": "Devastating Wounds"
            }
        ],
        "abilities": [
            {
                "name": "Death to the Alien",
                "description": "Each time a model in this unit makes an attack, re-roll a Hit roll of 1. If the target of that attack does not have the Imperium or Chaos keywords, you can re-roll the Hit roll instead."
            },
            {
                "name": "Attached Unit",
                "description": "If a Character unit from your army can be attached to a Fortis Kill Team unit, it can be attached to this unit instead."
            },
            {
                "name": "Astartes shield",
                "description": "The bearer has a 4+ invulnerable save."
            }
        ]
    },
    "Fortis Kill Team": {
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
                "name": "Deathwatch bolt rifle",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "2",
                "skill": "3+",
                "strength": "5",
                "ap": "-2",
                "damage": "1",
                "keywords": "Assault, Heavy, Lethal Hits"
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
                "name": "Heavy bolt pistol",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "4",
                "ap": "-1",
                "damage": "1",
                "keywords": "Pistol"
            },
            {
                "name": "\u27a4 Plasma pistol - Standard",
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
                "name": "\u27a4 Plasma pistol - Supercharge",
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
                "name": "\u27a4 Plasma incinerator - Standard",
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
                "name": "\u27a4 Plasma incinerator - Supercharge",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "2",
                "skill": "3+",
                "strength": "8",
                "ap": "-3",
                "damage": "2",
                "keywords": "Assault, Hazardous, Heavy"
            },
            {
                "name": "Superfrag missile launcher",
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
                "name": "Superkrak missile launcher",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "1",
                "skill": "4+",
                "strength": "10",
                "ap": "-2",
                "damage": "D6+1",
                "keywords": "Heavy"
            }
        ],
        "abilities": [
            {
                "name": "Fortis Doctrines",
                "description": "Each time a model in this unit makes an attack that targets a unit that is below its Starting Strength, add 1 to the Hit roll. If that attack targets a unit that is Below Half-strength, add 1 to the Hit roll and add 1 to the Wound roll instead."
            },
            {
                "name": "Attached Unit",
                "description": "If a CHARACTER from your army with the Leader ability can be attached to an INTERCESSOR SQUAD, it can be attached to this unit instead."
            }
        ]
    },
    "Indomitor Kill Team": {
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
                "name": "Auto boltstorm gauntlets",
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
                "name": "Twin power fists",
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
                "name": "Flamestorm gauntlets",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "D6+1",
                "skill": "N/A",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Ignores Cover, Torrent, Twin-linked"
            },
            {
                "name": "Deathwatch heavy bolt rifle",
                "weapon_type": "ranged",
                "range": "30\"",
                "attacks": "2",
                "skill": "3+",
                "strength": "5",
                "ap": "-2",
                "damage": "2",
                "keywords": "Assault, Heavy, Lethal Hits"
            },
            {
                "name": "Deathwatch heavy bolter",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "3",
                "skill": "3+",
                "strength": "5",
                "ap": "-2",
                "damage": "3",
                "keywords": "Assault, Heavy, Lethal Hits, Sustained Hits 1"
            }
        ],
        "abilities": [
            {
                "name": "Indomitor Doctrines",
                "description": "Each time a model in this unit makes a ranged attack that targets the closest eligible target, or makes a melee attack in a turn in which it made a Charge move, improve the Strength characteristic of that attack by 2."
            },
            {
                "name": "Attached Unit",
                "description": "If a CHARACTER unit from your army can be attached to a HEAVY INTERCESSOR SQUAD, it can be attached to this unit instead."
            }
        ]
    },
    "Spectrus Kill Team": {
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
                "name": "Deathwatch marksman bolt carbine",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "2",
                "skill": "3+",
                "strength": "5",
                "ap": "-1",
                "damage": "1",
                "keywords": "Heavy, Lethal Hits"
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
                "name": "Deathwatch occulus bolt carbine",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "2",
                "skill": "3+",
                "strength": "5",
                "ap": "-1",
                "damage": "1",
                "keywords": "Assault, Ignores Cover, Lethal Hits"
            },
            {
                "name": "Paired combat blades",
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
                "name": "Special-issue bolt pistol",
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
                "name": "Combat knife",
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
                "name": "Deathwatch Bolt carbine",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "2",
                "skill": "3+",
                "strength": "5",
                "ap": "-1",
                "damage": "1",
                "keywords": "Lethal Hits, Precision"
            },
            {
                "name": "Instigator bolt carbine",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "4",
                "ap": "-2",
                "damage": "2",
                "keywords": "Heavy"
            },
            {
                "name": "Bolt sniper rifle",
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
                "name": "Attached Unit",
                "description": "If a CHARACTER from your army with the Leader ability can be attached to an INFILTRATOR SQUAD, it can be attached to this unit instead.\nIf this unit has a Leader unit attached to it during the Declare Battle Formations step, that Leader unit gains the Infiltrators and Scouts 6\" abilities."
            },
            {
                "name": "Spectrus Doctrines",
                "description": "At the end of your opponent\u2019s turn, if this unit is more than 6\" away from all enemy units, you can remove this unit from the battlefield and place it into Strategic Reserves."
            },
            {
                "name": "Helix Gauntlet",
                "description": "Models in the bearer\u2019s unit have the Feel No Pain 6+ ability."
            },
            {
                "name": "Infiltrator Comms Array",
                "description": "Each time you target the bearer\u2019s unit with a Stratagem, roll one D6: on a 5+, you gain 1CP."
            },
            {
                "name": "Instigator Bolt Carbine",
                "description": "In your Shooting phase, after the bearer\u2019s unit has shot, the bearer\u2019s unit can make a Normal move. If it does, until the end of the turn, the bearer\u2019s unit is not eligible to declare a charge."
            }
        ]
    },
    "Talonstrike Kill Team": {
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
                "name": "\u27a4 Plasma pistol - Standard",
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
                "name": "\u27a4 Plasma pistol - Supercharge",
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
                "name": "Assault bolters",
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
                "name": "\u27a4 Plasma exterminators - standard",
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
                "name": "\u27a4 Plasma exterminators - supercharge",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "2",
                "skill": "3+",
                "strength": "8",
                "ap": "-3",
                "damage": "3",
                "keywords": "Assault, Hazardous, Pistol, Twin-linked"
            }
        ],
        "abilities": [
            {
                "name": "Talonstrike Doctrines",
                "description": "Each time this unit is set up on the battlefield, until the end of the turn:\n- Improve the Armour Penetration characteristic of weapons equipped by models in this unit by 1.\n- Melee weapons equipped by models in this unit have the [LANCE] ability."
            },
            {
                "name": "Attached Unit",
                "description": "If a CHARACTER unit from your army with the Leader ability can be attached to an ASSAULT INTERCESSORS WITH JUMP PACKS unit, it can be attached to this unit instead."
            }
        ]
    },
    "Watch Captain Artemis": {
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
                "name": "Hellfire Extremis",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "D6",
                "skill": "N/A",
                "strength": "4",
                "ap": "-1",
                "damage": "1",
                "keywords": "Anti-Infantry 4+, Devastating Wounds, Ignores Cover, Torrent"
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
                "name": "Invulnerable Save",
                "description": "This model has a 4+ invulnerable save."
            },
            {
                "name": "Tactical Instinct",
                "description": "While this model is leading a unit, weapons equipped by models in that unit have the [LETHAL HITS] ability."
            },
            {
                "name": "Unstoppable Champion",
                "description": "The first time this model is destroyed, roll one D6 at the end of the phase. On a 2+, set this model back up on the battlefield, as close as possible to where it was destroyed and not within Engagement Range of any enemy units, with 1 wound remaining."
            },
            {
                "name": "Leader",
                "description": "This model can be attached to the following units:\n- DEATHWATCH VETERANS\n- FORTIS KILL TEAM"
            }
        ]
    },
    "Watch Master": {
        "stats": {
            "stat_movement": "6\"",
            "stat_toughness": 4,
            "stat_save": "2+",
            "stat_wounds": 5,
            "stat_leadership": "6+",
            "stat_oc": 1,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Vigil spear",
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
                "name": "Vigil spear",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "6",
                "skill": "2+",
                "strength": "6",
                "ap": "-2",
                "damage": "D3",
                "keywords": "Lance"
            }
        ],
        "abilities": [
            {
                "name": "Invulnerable Save",
                "description": "This model has a 4+ invulnerable save."
            },
            {
                "name": "Strategic Knowledge",
                "description": "While this model is leading a unit, that unit is eligible to shoot and declare a charge in a turn in which it Advanced or Fell Back."
            },
            {
                "name": "Watch Master",
                "description": "Once per battle round, one unit from your army with this ability can use it when its unit is targeted with a Stratagem. If it does, reduce the CP cost of that use of that Stratagem by 1CP."
            },
            {
                "name": "Leader",
                "description": "This model can be attached to the following units:\n- DEATHWATCH VETERANS\n- FORTIS KILL TEAM"
            }
        ]
    }
}


class Command(BaseCommand):
    """Refresh Deathwatch stat lines, weapon profiles, and abilities from BSData."""

    help = 'Refresh 11th Edition stats/weapons/abilities for Deathwatch-exclusive units.'

    def add_arguments(self, parser):
        """Add --dry-run flag."""
        parser.add_argument(
            '--dry-run', action='store_true',
            help='Preview changes without writing to the database.',
        )

    def handle(self, *args, **options):
        """Iterate DEATHWATCH_DATASHEETS and refresh each unit's datasheet data."""
        dry_run = options['dry_run']
        updated = 0
        skipped = 0

        with transaction.atomic():
            for name, payload in DEATHWATCH_DATASHEETS.items():
                try:
                    unit = UnitType.objects.get(name=name, faction__name='Deathwatch')
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
