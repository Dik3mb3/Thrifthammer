"""
Management command: seed_genestealer_cults_datasheets

Refreshes stat lines, weapon profiles, and abilities for Genestealer
Cults units using 11th Edition data sourced from BSData/wh40k-11e
("Genestealer Cults.json") -- the same source used by
seed_genestealer_cults_points.py. Supersedes the older hand-authored
seed_genestealer_cults_stats.py (5 units, 10th Edition) -- left in place,
not deleted, since removing it wasn't part of this task's scope.

Usage:
    python manage.py seed_genestealer_cults_datasheets
    python manage.py seed_genestealer_cults_datasheets --dry-run

Notes:
- Does NOT touch points_cost or category -- those are handled entirely by
  seed_genestealer_cults_points.py. This command only refreshes stat_*
  fields, WeaponProfile rows, and UnitAbility rows.
- Scoped to GSC's own 24 units only -- the ~127 Astra Militarum "Brood
  Brothers" allied entries in the same BSData file are intentionally out
  of scope (no GSC-specific product exists for any of them). Same
  precedent as Agents of the Imperium/CSM cross-links.
- Per-field safety rule: a unit's stats/weapons/abilities are only
  overwritten when BSData actually has that data for it. If extraction
  found nothing, the existing DB value/rows are left untouched.
- All 24 active units resolved cleanly -- 0 missing stats/weapons/
  abilities, 0 overlong stat fields.
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from calculators.models import UnitAbility, UnitType, WeaponProfile

# (name -> {stats?, weapons?, abilities?}). Missing keys mean "no data
# found for this field -- leave existing DB data untouched."
GENESTEALER_CULTS_DATASHEETS = {
    "Aberrants": {
        "stats": {
            "stat_movement": "6\"",
            "stat_toughness": 6,
            "stat_save": "5+",
            "stat_wounds": 3,
            "stat_leadership": "7+",
            "stat_oc": 1,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Aberrant weapons",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "3",
                "skill": "3+",
                "strength": "7",
                "ap": "-2",
                "damage": "2",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Feel No Pain 5+",
                "description": "This unit has a 5+ Feel No Pain"
            },
            {
                "name": "Hulking Bodyguards",
                "description": "While a CHARACTER is leading this unit, each time an attack targets this unit, if the Strength characteristic of that attack is greater than the Toughness characteristic of this unit, subtract 1 from the Wound roll."
            }
        ]
    },
    "Abominant": {
        "stats": {
            "stat_movement": "6\"",
            "stat_toughness": 6,
            "stat_save": "5+",
            "stat_wounds": 5,
            "stat_leadership": "7+",
            "stat_oc": 1,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Power sledgehammer",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "3+",
                "strength": "12",
                "ap": "-2",
                "damage": "D6+1",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Feel No Pain 5+",
                "description": "This model has a 5+ Feel No Pain"
            },
            {
                "name": "The Chosen One",
                "description": "While this model is leading a unit, each time a model in that unit is destroyed by a melee attack, if that model has not fought this phase, roll one D6. On a 4+ do not remove the destroyed model from play, it can fight after the attacking model's unit has finished making it's attacks and is then removed from play."
            },
            {
                "name": "Regenerating Gene-mass",
                "description": "The first time this model is destroyed, roll one D6 at the end of the phase. On a 2+, set this model back up on the battlefield as close as possible to where it was destroyed and not within Engagement Range of any enemy units, with its full wounds remaining."
            }
        ]
    },
    "Achilles Ridgerunners": {
        "stats": {
            "stat_movement": "12\"",
            "stat_toughness": 7,
            "stat_save": "3+",
            "stat_wounds": 8,
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
                "skill": "4+",
                "strength": "5",
                "ap": "0",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "Twin heavy stubber",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "3",
                "skill": "4+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Twin-linked, Rapid Fire 3"
            },
            {
                "name": "Achilles missile launcher",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "3",
                "skill": "4+",
                "strength": "9",
                "ap": "-2",
                "damage": "3",
                "keywords": "-"
            },
            {
                "name": "Heavy mortar",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "D6+3",
                "skill": "4+",
                "strength": "6",
                "ap": "0",
                "damage": "1",
                "keywords": "Blast, Indirect Fire"
            },
            {
                "name": "Heavy mining laser",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "D3",
                "skill": "4+",
                "strength": "12",
                "ap": "-3",
                "damage": "D6+1",
                "keywords": "Blast"
            }
        ],
        "abilities": [
            {
                "name": "Crossfire",
                "description": "in your Shooting phase, after this unit has shot, select one enemy unit hit by one or more of those attacks. Until the end of the turn, each time a friendly Genestealer Cults unit makes an attack that targets that enemy unit, improve the Armour Penetration characteristic of that attack by 1. The same enemy unit can only be affected by this ability once per turn."
            },
            {
                "name": "Flare Launcher",
                "description": "The bearer\u2019s unit has the SMOKE keyword and you can target it with the Smokescreen Stratagem for 0CP."
            },
            {
                "name": "Spotter",
                "description": "The bearer\u2019s ranged weapons have a Ballistic Skill characteristic of 3+."
            },
            {
                "name": "Survey Augur",
                "description": "Each time the bearer\u2019s unit has shot, select one enemy unit that was hit by one or more attacks made by the bearer this phase. Until the end of the phase, each time a friendly GENESTEALER CULTS model makes an attack against that unit, that attack has the [IGNORES COVER] ability."
            }
        ]
    },
    "Acolyte Hybrids with Autopistols": {
        "stats": {
            "stat_movement": "6\"",
            "stat_toughness": 4,
            "stat_save": "5+",
            "stat_wounds": 1,
            "stat_leadership": "7+",
            "stat_oc": 2,
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
                "name": "Cult claws and knife",
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
                "name": "Heavy mining tool",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "2",
                "skill": "3+",
                "strength": "5",
                "ap": "-2",
                "damage": "3",
                "keywords": "Anti-Vehicle 4+"
            },
            {
                "name": "Leader's Bio-weapons",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "5",
                "skill": "3+",
                "strength": "5",
                "ap": "-2",
                "damage": "1",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Claimed for the Cult",
                "description": "At the start of your Command phase, roll one D6 for each objective marker that you control that has one or more units from your army with this ability within range of it. If one or more of the results is a 4+, you gain 1CP."
            },
            {
                "name": "Cult Icon",
                "description": "In your Command phase, you can return up to D3 destroyed models to the bearer\u2019s unit. If the bearer\u2019s unit is within range of an objective marker you control, you can return up to 3 destroyed models to that unit instead. This ability cannot be used to return destroyed CHARACTER models in Attached units and any [ONE SHOT] weapons equipped with by returned models that were shot before they were destroyed are still considered to have been shot."
            }
        ]
    },
    "Acolyte Hybrids with Hand Flamers": {
        "stats": {
            "stat_movement": "6\"",
            "stat_toughness": 4,
            "stat_save": "5+",
            "stat_wounds": 1,
            "stat_leadership": "7+",
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
                "name": "Cult claws and knife",
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
                "name": "Demolition charge",
                "weapon_type": "ranged",
                "range": "8\"",
                "attacks": "D6",
                "skill": "5+",
                "strength": "9",
                "ap": "-2",
                "damage": "2",
                "keywords": "Assault, Blast, Hazardous, One Shot"
            },
            {
                "name": "Leader's bio-weapons",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "5",
                "skill": "3+",
                "strength": "5",
                "ap": "-2",
                "damage": "1",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Industrialised Destruction",
                "description": "Each time a model in this unit makes an attack, re-roll a Wound Roll of 1. If the target of that attack is an enemy unit within range of an objective marker, you can re-roll the wound roll."
            },
            {
                "name": "Cult Icon",
                "description": "In your Command phase, you can return up to D3 destroyed models to the bearer\u2019s unit. If the bearer\u2019s unit is within range of an objective marker you control, you can return up to 3 destroyed models to that unit instead. This ability cannot be used to return destroyed CHARACTER models in Attached units and any [ONE SHOT] weapons equipped with by returned models that were shot before they were destroyed are still considered to have been shot."
            }
        ]
    },
    "Acolyte Iconward": {
        "stats": {
            "stat_movement": "6\"",
            "stat_toughness": 4,
            "stat_save": "5+",
            "stat_wounds": 3,
            "stat_leadership": "6+",
            "stat_oc": 1,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Cult claws",
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
                "name": "Autopistol",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "3",
                "ap": "0",
                "damage": "1",
                "keywords": "Pistol"
            }
        ],
        "abilities": [
            {
                "name": "Nexus of Devotion",
                "description": "While this model is leading a unit, models in that unit have the Feel No Pain 5+ ability. If that unit has the HYBRID METAMORPHS keyword, models in that unit have the Feel No Pain 4+ ability instead."
            },
            {
                "name": "Summon the Cult",
                "description": "Once per battle, when you have to remove a Cult Ambush marker because your opponent has moved too close to it, if one or more models from your army with this ability are on the battlefield, you can use this ability. If you do, instead of removing that marker, you can place it anywhere on the battlefield that is within 12\" of a model from your army with this ability and more than 8\" horizontally away from all enemy units (if this is not possible, this ability is not considered to have been used and that marker is removed as normal)."
            },
            {
                "name": "Leader",
                "description": "This model can be attached to the following units:\n- Acolyte Hybrids\n- Hybrid Metamorphs\n- Neophyte Hybrids"
            }
        ]
    },
    "Atalan Jackals": {
        "stats": {
            "stat_movement": "12\"",
            "stat_toughness": 4,
            "stat_save": "5+",
            "stat_wounds": 2,
            "stat_leadership": "7+",
            "stat_oc": 1,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "\u27a4 Grenade launcher - frag",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "D3",
                "skill": "4+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Blast"
            },
            {
                "name": "\u27a4 Grenade launcher - krak",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "1",
                "skill": "4+",
                "strength": "9",
                "ap": "-2",
                "damage": "D3",
                "keywords": "-"
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
                "name": "Atalan small arms",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "2",
                "skill": "4+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Pistol"
            },
            {
                "name": "Atalan power weapon",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "2",
                "skill": "4+",
                "strength": "4",
                "ap": "-2",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "Mining laser",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "1",
                "skill": "4+",
                "strength": "12",
                "ap": "-3",
                "damage": "D6+1",
                "keywords": "-"
            },
            {
                "name": "Atalan incinerator",
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
                "name": "Heavy stubber",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "3",
                "skill": "4+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Assault, Rapid Fire 3"
            }
        ],
        "abilities": [
            {
                "name": "Outrider Gangs",
                "description": "Each time you use the Cult Ambush ability to set this unit back up on the battlefield, in addition to the normal rules, all of its models must be set up wholly within 9\" of a battlefield edge and at least one of its models must be touching one of your Cult Ambush markers (that marker is then removed from the battlefield). If this cannot be done, this unit cannot be set back up."
            },
            {
                "name": "Demolition Run",
                "description": "Once per battle round, in your Movement phase, when this unit ends a Normal, Advance, or Fall Back move, you can select one enemy unit within 6\" of and visible to this unit and roll one D6 for each ATALAN JACKALS model in this unit: for each 4+, that enemy unit suffers 1 mortal wound (to a maximum of 6 mortal wounds.)"
            }
        ]
    },
    "Benefictus": {
        "stats": {
            "stat_movement": "6\"",
            "stat_toughness": 3,
            "stat_save": "5+",
            "stat_wounds": 3,
            "stat_leadership": "7+",
            "stat_oc": 1,
            "stat_invuln": "5+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "\u27a4 Psionic cascade - witchfire",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "12",
                "ap": "-3",
                "damage": "D6+1",
                "keywords": "Ignores Cover, Psychic"
            },
            {
                "name": "\u27a4 Psionic cascade - focused witchfire",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "2",
                "skill": "3+",
                "strength": "12",
                "ap": "-3",
                "damage": "D6+1",
                "keywords": "Hazardous, Ignores Cover, Psychic"
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
            }
        ],
        "abilities": [
            {
                "name": "Bio-horror Disruption (Psychic)",
                "description": "While this model is leading a unit, ranged weapons equipped by models in that unit have the [LETHAL HITS] ability."
            },
            {
                "name": "Psionic Shield (Psychic)",
                "description": "Once per battle, at the start of any phase, this model can use this ability. If it does, until the end of the phase, this model has a 4+ invulnerable save."
            },
            {
                "name": "Leader",
                "description": "This model can be attached to the following units:\n- Acolyte Hybrids\n- Hybrid Metamorphs\n- Neophyte Hybrids"
            }
        ]
    },
    "Biophagus": {
        "stats": {
            "stat_movement": "6\"",
            "stat_toughness": 3,
            "stat_save": "5+",
            "stat_wounds": 3,
            "stat_leadership": "7+",
            "stat_oc": 1,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Injector goad",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "1",
                "skill": "3+",
                "strength": "2",
                "ap": "0",
                "damage": "D3",
                "keywords": "Anti-infantry 2+"
            },
            {
                "name": "Autopistol",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "3",
                "ap": "0",
                "damage": "1",
                "keywords": "Pistol"
            },
            {
                "name": "Chemical vials",
                "weapon_type": "ranged",
                "range": "6\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "1",
                "ap": "-1",
                "damage": "2",
                "keywords": "Anti-Infantry 2+"
            }
        ],
        "abilities": [
            {
                "name": "Twisted Science",
                "description": "While this model is leading a unit, melee weapons equipped by models in that unit have the [LETHAL HITS] ability."
            },
            {
                "name": "Biological Warfare",
                "description": "Once per battle, when this model\u2019s unit is selected to fight, this model can use this ability. If it does, until the end of the phase, improve the Attacks and Damage characteristics of its injector goad by 3."
            },
            {
                "name": "Leader",
                "description": "This model can be attached to the following units:\n- ABERRANTS\n\n- ACOLYTE HYBRIDS WITH AUTOPISTOLS\n- ACOLYTE HYBRIDS WITH HANDFLAMERS\n- HYBRID METAMORPHS\n- NEOPHYTE HYBRIDS\n\nYou can attach this model to an ACOLYTE HYBRIDS or NEOPHYTE HYBRID unit, even if a PRIMUS, MAGUS, or ACOLYTE ICONWARD model has already been attached to it. If you do, and that Bodyguard unit is destroyed, the Leader units attached to it become separate units, with their original Starting Strengths."
            },
            {
                "name": "Alchemicus Familiar",
                "description": "Once per battle, when the bearer\u2019s unit is selected to fight, the bearer can use its alchemicus familiar. If it does, until the end of the phase, each time a model in the bearer's unit makes an attack that targets an INFANTRY unit, add 1 to the Wound roll"
            }
        ]
    },
    "Clamavus": {
        "stats": {
            "stat_movement": "6\"",
            "stat_toughness": 3,
            "stat_save": "5+",
            "stat_wounds": 3,
            "stat_leadership": "6+",
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
                "skill": "3+",
                "strength": "3",
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
                "strength": "3",
                "ap": "0",
                "damage": "1",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Voice of New Truths",
                "description": "In your Command phase, one model from your army with this ability can use it, if it does, select one enemy unit with 18\" of it, that enemy unit must take a Battle-shock test."
            },
            {
                "name": "Scrambler Array",
                "description": "Enemy units that are set up on the battlefield as Reinforcements cannot be set up within 12\" of this model."
            },
            {
                "name": "Leader",
                "description": "This model can be attached to the following units:\n- ACOLYTE HYBRIDS\n- HYBRID METAMORPHS\n- NEOPHYTE HYBRIDS\nYou can attach this model to an ACOLYTE HYBRIDS or NEOPHYTE HYBRID unit, even if a PRIMUS, MAGUS, or ACOLYTE ICONWARD model has already been attached to it. If you do, and that Bodyguard unit is destroyed, the Leader units attached to it become separate units, with their original Starting Strengths."
            }
        ]
    },
    "Goliath Rockgrinder": {
        "stats": {
            "stat_movement": "12\"",
            "stat_toughness": 10,
            "stat_save": "3+",
            "stat_wounds": 10,
            "stat_leadership": "7+",
            "stat_oc": 3,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Drilldozer blade",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "8",
                "skill": "3+",
                "strength": "10",
                "ap": "-2",
                "damage": "2",
                "keywords": "-"
            },
            {
                "name": "Heavy stubber",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "3",
                "skill": "4+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Rapid Fire 3"
            },
            {
                "name": "Demolition charge cache",
                "weapon_type": "ranged",
                "range": "8\"",
                "attacks": "D6",
                "skill": "5+",
                "strength": "9",
                "ap": "-2",
                "damage": "2",
                "keywords": "Assault, Blast, Hazardous"
            },
            {
                "name": "Clearance incinerator",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "2D6",
                "skill": "N/A",
                "strength": "6",
                "ap": "-1",
                "damage": "1",
                "keywords": "Ignores Cover, Torrent"
            },
            {
                "name": "Heavy seismic cannon",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "4",
                "skill": "4+",
                "strength": "8",
                "ap": "-2",
                "damage": "D3",
                "keywords": "Rapid Fire 2"
            },
            {
                "name": "Heavy mining laser",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "D3",
                "skill": "4+",
                "strength": "12",
                "ap": "-3",
                "damage": "D6+1",
                "keywords": "Blast"
            }
        ],
        "abilities": [
            {
                "name": "Grinding Line-breaker",
                "description": "Each time an enemy unit (excluding MONSTER and VEHICLES) that is within Engagement Range of this model Falls Back, all models in that enemy unit must take a Desperate Escape test. When doing so, if that enemy unit is Battle-shocked, subtract 1 from each of those tests."
            },
            {
                "name": "Damaged: 1-3 Wounds Remaining",
                "description": "While this model has 1-3 wounds remaining, each time this model makes an attack, subtract 1 from the Hit roll."
            }
        ]
    },
    "Goliath Truck": {
        "stats": {
            "stat_movement": "12\"",
            "stat_toughness": 9,
            "stat_save": "3+",
            "stat_wounds": 10,
            "stat_leadership": "7+",
            "stat_oc": 2,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Twin autocannon",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "2",
                "skill": "4+",
                "strength": "9",
                "ap": "-1",
                "damage": "3",
                "keywords": "Twin-linked"
            },
            {
                "name": "Goliath wheels",
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
                "name": "Demolition charge cache",
                "weapon_type": "ranged",
                "range": "8\"",
                "attacks": "D6",
                "skill": "5+",
                "strength": "9",
                "ap": "-2",
                "damage": "2",
                "keywords": "Assault, Blast, Hazardous"
            },
            {
                "name": "Heavy stubber",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "3",
                "skill": "4+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Rapid Fire 3"
            }
        ],
        "abilities": [
            {
                "name": "Fire Support",
                "description": "In your Shooting phase, after this model has shot, select one enemy unit it scored one or more hits against this phase. Until the end of the phase, each time a friendly model that disembarked from this TRANSPORT this turn makes an attack that targets that enemy unit, you can re-roll the Wound roll."
            }
        ]
    },
    "Hybrid Metamorphs": {
        "stats": {
            "stat_movement": "6\"",
            "stat_toughness": 4,
            "stat_save": "5+",
            "stat_wounds": 1,
            "stat_leadership": "7+",
            "stat_oc": 1,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "\u27a4 Metamorph mutations - strike",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "3",
                "skill": "3+",
                "strength": "5",
                "ap": "-1",
                "damage": "2",
                "keywords": "-"
            },
            {
                "name": "\u27a4 Metamorph mutations - sweep",
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
                "name": "Leader's Bio-weapons",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "5",
                "skill": "3+",
                "strength": "5",
                "ap": "-1",
                "damage": "2",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Brood Surge",
                "description": "In your opponent\u2019s Shooting phase, when an enemy unit has shot, if a model in this unit was destroyed as a result of those attacks, this unit can make a surge move of up to D6\"."
            },
            {
                "name": "Cult Icon",
                "description": "In your Command phase, you can return up to D3 destroyed models to the bearer\u2019s unit. If the bearer\u2019s unit is within range of an objective marker you control, you can return up to 3 destroyed models to that unit instead. This ability cannot be used to return destroyed CHARACTER models in Attached units and any [ONE SHOT] weapons equipped with by returned models that were shot before they were destroyed are still considered to have been shot."
            }
        ]
    },
    "Jackal Alphus": {
        "stats": {
            "stat_movement": "12\"",
            "stat_toughness": 4,
            "stat_save": "5+",
            "stat_wounds": 4,
            "stat_leadership": "7+",
            "stat_oc": 1,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Cult sniper rifle",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "5",
                "ap": "-2",
                "damage": "3",
                "keywords": "Heavy, Precision"
            },
            {
                "name": "Autopistol",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "3",
                "ap": "0",
                "damage": "1",
                "keywords": "Pistol"
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
            }
        ],
        "abilities": [
            {
                "name": "Priority Target",
                "description": "In your Shooting phase, after this model's unit has shot, select one enemy unit hit by one or more of those attacks made with a cult sniper rifle. Until the end of the phase, each time a friendly Genestealer Cults model makes an attack that targets that enemy unit, re-roll a Hit roll of 1."
            },
            {
                "name": "Master Outrider",
                "description": "In your Shooting phase, after this model\u2019s unit has shot, if it is not within Engagement Range of any enemy units, that unit can make a Normal move of up to 6\" as if it were your Movement phase. If it does, until the end of the turn, that unit is not eligible to declare a charge."
            }
        ]
    },
    "Kelermorph": {
        "stats": {
            "stat_movement": "6\"",
            "stat_toughness": 3,
            "stat_save": "5+",
            "stat_wounds": 3,
            "stat_leadership": "7+",
            "stat_oc": 1,
            "stat_invuln": "5+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Liberator autostubs",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "6",
                "skill": "2+",
                "strength": "6",
                "ap": "-2",
                "damage": "1",
                "keywords": "Devastating Wounds, Pistol"
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
            }
        ],
        "abilities": [
            {
                "name": "Hypersensory Abilities",
                "description": "Once per turn, in your opponent\u2019s Movement phase, when an enemy unit ends a Normal, Advance or Fall Back move within 8\" of this model, if this model is not within Engagement Range of one or more enemy units, it can shoot at that unit as if it were your Shooting phase and then make a Normal move of up to D6\" (it cannot embark within a Transport as part of this move)."
            },
            {
                "name": "Heroic Fusillade",
                "description": "Once per turn, after one model from your army with this ability has shot, you can select one INFANTRY unit hit by one or more of those attacks. That unit must take a Battle-shock test."
            }
        ]
    },
    "Locus": {
        "stats": {
            "stat_movement": "6\"",
            "stat_toughness": 4,
            "stat_save": "5+",
            "stat_wounds": 3,
            "stat_leadership": "7+",
            "stat_oc": 1,
            "stat_invuln": "4+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Locus blades",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "5",
                "skill": "2+",
                "strength": "5",
                "ap": "-2",
                "damage": "2",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Sudden Assault",
                "description": "While this model is leading a unit, models in that unit have the Fights First ability"
            },
            {
                "name": "Bodyguard",
                "description": "While this model is leading a unit, other Character models attached to that unit have the Feel No Pain 4+ ability"
            },
            {
                "name": "Leader",
                "description": "This model can be attached to the following units:\n- Acolyte Hybrids\n- Hybrid Metamorphs\n- Neophyte Hybrids\nYou can attach this model to an Acolyte Hybrids or Neophyte Hybrids unit, even if a Primus, Magus, or Acolyte Iconward model has already been attached to it. If you do, and that Bodyguard unit is destroyed, the Leader units attached to it become separate units, with their original Starting Strengths."
            }
        ]
    },
    "Magus": {
        "stats": {
            "stat_movement": "6\"",
            "stat_toughness": 3,
            "stat_save": "5+",
            "stat_wounds": 4,
            "stat_leadership": "6+",
            "stat_oc": 1,
            "stat_invuln": "5+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Force stave",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "3",
                "skill": "3+",
                "strength": "5",
                "ap": "-1",
                "damage": "D3",
                "keywords": "Psychic"
            },
            {
                "name": "Autopistol",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "3",
                "ap": "0",
                "damage": "1",
                "keywords": "Pistol"
            }
        ],
        "abilities": [
            {
                "name": "Psychic Familiar",
                "description": "Once per battle, at the start of any of your opponent\u2019s Shooting phases, this model can use its psychic familiar. If it does, until the end of the phase, add 6\" to the range of its Mind Control ability."
            },
            {
                "name": "Mind Control (Psychic)",
                "description": "At the start of your opponent\u2019s Shooting phase, one PSYKER model from your army with this ability can use it. If used, select one enemy unit within 18\" of and visible to that PSYKER model and roll one D6: on a 1, that PSYKER model suffers D3 mortal wounds; on a 2-5, until the end of the phase, each time a model in that enemy unit makes an attack, subtract 1 from the Hit roll; on a 6, each time a model in that enemy unit makes an attack, subtract 1 from the Hit roll and subtract 1 from the Wound Roll."
            },
            {
                "name": "Spiritual Leader",
                "description": "Once per battle, at the start of any phase, you can select one friendly GENESTELERS CULTS unit that is Battle-shocked and within 12\" of this model. That unit is no longer Battle-shocked."
            },
            {
                "name": "Leader",
                "description": "This model can be attached to the following units:\n- Acolyte Hybrids\n- Hybrid Metamorphs\n- Neophyte Hybrids"
            }
        ]
    },
    "Neophyte Hybrids": {
        "stats": {
            "stat_movement": "6\"",
            "stat_toughness": 3,
            "stat_save": "5+",
            "stat_wounds": 1,
            "stat_leadership": "7+",
            "stat_oc": 2,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Hybrid firearm",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "1",
                "skill": "4+",
                "strength": "3",
                "ap": "0",
                "damage": "1",
                "keywords": "Rapid Fire 1"
            },
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
                "name": "Close combat weapon",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "1",
                "skill": "4+",
                "strength": "3",
                "ap": "0",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "Mining laser",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "1",
                "skill": "5+",
                "strength": "10",
                "ap": "-3",
                "damage": "D6+1",
                "keywords": "Heavy"
            },
            {
                "name": "Seismic cannon",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "2",
                "skill": "5+",
                "strength": "6",
                "ap": "-1",
                "damage": "D3",
                "keywords": "Heavy, Rapid Fire 2"
            },
            {
                "name": "Heavy stubber",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "3",
                "skill": "4+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Rapid Fire 3"
            },
            {
                "name": "Webber",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "D6",
                "skill": "N/A",
                "strength": "2",
                "ap": "0",
                "damage": "1",
                "keywords": "Devastating Wounds, Torrent"
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
                "name": "\u27a4 Grenade launcher - frag",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "D3",
                "skill": "4+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Blast"
            },
            {
                "name": "\u27a4 Grenade launcher - krak",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "1",
                "skill": "4+",
                "strength": "9",
                "ap": "-2",
                "damage": "D3",
                "keywords": "-"
            },
            {
                "name": "Power weapon",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "1",
                "skill": "4+",
                "strength": "4",
                "ap": "-2",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "Anointed pistol",
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
                "name": "Chainsword",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "2",
                "skill": "4+",
                "strength": "3",
                "ap": "0",
                "damage": "1",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "A Plan Generations in the Making",
                "description": "At the end of your Command phase, if this unit is within range of an objective marker you control, that objective marker remains under your control, even if you have no models within range of it, until your opponent controls it at the start or end of any turn."
            },
            {
                "name": "Cult Icon",
                "description": "In your Command phase, you can return up to 3 destroyed models to the bearer\u2019s unit. If the bearer\u2019s unit is within range of an objective marker you control, you can return up to D3+3 destroyed models to that unit instead. This ability cannot be used to return destroyed CHARACTER models in Attached units and any [ONE SHOT] weapons equipped with by returned models that were shot before they were destroyed are still considered to have been shot."
            }
        ]
    },
    "Nexos": {
        "stats": {
            "stat_movement": "6\"",
            "stat_toughness": 3,
            "stat_save": "5+",
            "stat_wounds": 3,
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
                "skill": "3+",
                "strength": "3",
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
                "strength": "3",
                "ap": "0",
                "damage": "1",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Battlefield Analysis",
                "description": "Once per battle round, one model from your army with this ability can use it when its unit is targeted with a Stratagem. If it does, reduce the CP cost of that use of that Stratagem by 1CP."
            },
            {
                "name": "Cult Infiltration",
                "description": "At the start of each player\u2019s Command phase, if this model is on the battlefield, you can select one of your Cult Ambush markers that is on the battlefield and has not been moved this turn and move it up to 6\""
            },
            {
                "name": "Leader",
                "description": "This model can be attached to the following units:\n- ACOLYTE HYBRIDS\n- HYBRID METAMORPHS\n- NEOPHYTE HYBRIDS\nYou can attach this model to an ACOLYTE HYBRIDS or NEOPHYTE HYBRID unit, even if a PRIMUS, MAGUS, or ACOLYTE ICONWARD model has already been attached to it. If you do, and that Bodyguard unit is destroyed, the Leader units attached to it become separate units, with their original Starting Strengths."
            }
        ]
    },
    "Patriarch": {
        "stats": {
            "stat_movement": "8\"",
            "stat_toughness": 5,
            "stat_save": "4+",
            "stat_wounds": 6,
            "stat_leadership": "6+",
            "stat_oc": 1,
            "stat_invuln": "4+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Patriarch's claws",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "5",
                "skill": "2+",
                "strength": "6",
                "ap": "-2",
                "damage": "2",
                "keywords": "Devastating Wounds, Twin-linked"
            }
        ],
        "abilities": [
            {
                "name": "Might From Beyond",
                "description": "While this model is leading a unit, melee weapons equipped by models in that unit have the [DEVASTATING WOUNDS] ability."
            },
            {
                "name": "Cosmic Horror (Psychic)",
                "description": "At the start of the Fight phase, each enemy unit within 6\" of this model must take a Battle-shock test."
            },
            {
                "name": "Psychic Familiar",
                "description": "Once per battle, at the start of the Fight phase, this model can use its psychic familiar. If it does, until the end of the phase, add 6\" to the range of its Cosmic Horror ability."
            },
            {
                "name": "Supreme Commander",
                "description": "- You cannot include more than one Patriarch model in your army.\n- If this model is in your army, it must be your Warlord."
            }
        ]
    },
    "Primus": {
        "stats": {
            "stat_movement": "6\"",
            "stat_toughness": 3,
            "stat_save": "5+",
            "stat_wounds": 4,
            "stat_leadership": "6+",
            "stat_oc": 1,
            "stat_invuln": "5+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Toxin injector claw",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "2",
                "skill": "2+",
                "strength": "2",
                "ap": "0",
                "damage": "D3",
                "keywords": "Anti-infantry 2+, Extra Attacks"
            },
            {
                "name": "Scoped needle pistol",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "1",
                "skill": "2+",
                "strength": "1",
                "ap": "0",
                "damage": "D3",
                "keywords": "Anti-infantry 2+, Ignores Cover, Pistol"
            },
            {
                "name": "Cult bonesword",
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
                "name": "Cult Demagogue",
                "description": "While this model is leading a unit, each time a model in that unit makes an attack, you can add 1 to the Hit roll."
            },
            {
                "name": "Decoys and Misdirection",
                "description": "If your army includes one or more models with this ability, after both players have deployed their armies, select up to three GENESTEALER CULTS units from your army and redeploy them. When doing so, you can set those units up in Strategic Reserves if you wish, regardless of how many units are already in Strategic Reserves."
            },
            {
                "name": "Leader",
                "description": "This model can be attached to the following units:\n- Acolyte Hybrids\n- Hybrid Metamorphs\n- Neophyte Hybrids"
            }
        ]
    },
    "Purestrain Genestealers": {
        "stats": {
            "stat_movement": "8\"",
            "stat_toughness": 4,
            "stat_save": "5+",
            "stat_wounds": 2,
            "stat_leadership": "7+",
            "stat_oc": 1,
            "stat_invuln": "5+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Cult claws and talons",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "2+",
                "strength": "4",
                "ap": "-2",
                "damage": "1",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Swift and Deadly",
                "description": "This unit is eligible to declare a charge in a turn in which it Advanced."
            }
        ]
    },
    "Reductus Saboteur": {
        "stats": {
            "stat_movement": "6\"",
            "stat_toughness": 3,
            "stat_save": "5+",
            "stat_wounds": 3,
            "stat_leadership": "7+",
            "stat_oc": 1,
            "stat_invuln": "5+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Demolition charges",
                "weapon_type": "ranged",
                "range": "8\"",
                "attacks": "D6",
                "skill": "3+",
                "strength": "9",
                "ap": "-2",
                "damage": "2",
                "keywords": "Assault, Blast, One Shot"
            },
            {
                "name": "Autopistol",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "3",
                "ap": "0",
                "damage": "1",
                "keywords": "Pistol"
            },
            {
                "name": "Remote explosives",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "D6+3",
                "skill": "3+",
                "strength": "5",
                "ap": "0",
                "damage": "1",
                "keywords": "Blast, Indirect Fire"
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
            }
        ],
        "abilities": [
            {
                "name": "Primed and Ready",
                "description": "In your Shooting phase, you can select one model from your army with this ability as the target of the Grenade Stratagem for 0CP, provided that model has not already been the target of that Stratagem this phase."
            },
            {
                "name": "Planted Explosives",
                "description": "Once per battle, when an enemy unit ends a Normal, Advance or Fall Back move within 8\" of this model, this model can use its Reductus mine. If it does, roll one D6: on a 2+, that enemy unit suffers D3+3 mortal wounds. Only one model from your army with this ability can use it in the same battle round."
            }
        ]
    },
    "Sanctus": {
        "stats": {
            "stat_movement": "6\"",
            "stat_toughness": 3,
            "stat_save": "5+",
            "stat_wounds": 3,
            "stat_leadership": "7+",
            "stat_oc": 1,
            "stat_invuln": "5+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Sanctus bio-dagger",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "6",
                "skill": "2+",
                "strength": "3",
                "ap": "-2",
                "damage": "2",
                "keywords": "Anti-infantry 3+, Precision"
            },
            {
                "name": "Cult sniper rifle",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "7",
                "ap": "-2",
                "damage": "3",
                "keywords": "Anti-Psyker 2+, Heavy, Precision"
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
            }
        ],
        "abilities": [
            {
                "name": "Creeping Shadow",
                "description": "If this model is equipped with a Cult Sniper Rifle, In your opponent's Movement phase, if an enemy unit ends a move within 8\u201d of this unit, if this unit is not within Engagement Range of one or more enemy units, this unit can make a Normal move of up to 6\u201d."
            },
            {
                "name": "Psychic Spoor",
                "description": "At the start of the first battle round, select one enemy unit to be this model\u2019s prey. Each time this model makes an attack that targets its prey, you can re-roll the Hit roll and you can re-roll the Wound roll."
            },
            {
                "name": "Cloaked Assassin",
                "description": "If this model is equipped with a Sanctus Bio-dagger, enemy units cannot use the Fire Overwatch Stratagem to shoot at this model. Enemy units cannot target this unit with snap shooting attacks."
            }
        ]
    }
}


class Command(BaseCommand):
    """Refresh Genestealer Cults stat lines, weapon profiles, and abilities from BSData."""

    help = 'Refresh 11th Edition stats/weapons/abilities for Genestealer Cults units.'

    def add_arguments(self, parser):
        """Add --dry-run flag."""
        parser.add_argument(
            '--dry-run', action='store_true',
            help='Preview changes without writing to the database.',
        )

    def handle(self, *args, **options):
        """Iterate GENESTEALER_CULTS_DATASHEETS and refresh each unit's datasheet data."""
        dry_run = options['dry_run']
        updated = 0
        skipped = 0

        with transaction.atomic():
            for name, payload in GENESTEALER_CULTS_DATASHEETS.items():
                try:
                    unit = UnitType.objects.get(name=name, faction__name='Genestealer Cults')
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
