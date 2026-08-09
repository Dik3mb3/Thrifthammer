"""
Management command: seed_grey_knights_datasheets

Refreshes stat lines, weapon profiles, and abilities for all Grey Knights
units using 11th Edition data sourced from BSData/wh40k-11e
("Imperium - Grey Knights.json") -- the same source used by
seed_grey_knights_points.py.

Usage:
    python manage.py seed_grey_knights_datasheets
    python manage.py seed_grey_knights_datasheets --dry-run

Notes:
- Does NOT touch points_cost or category -- those are handled entirely by
  seed_grey_knights_points.py. This command only refreshes stat_* fields,
  WeaponProfile rows, and UnitAbility rows.
- Per-field safety rule: a unit's stats/weapons/abilities are only
  overwritten when BSData actually has that data for it. If extraction
  found nothing for a given field, the existing DB value/rows are left
  untouched rather than blanked.
- Weapon profiles list EVERY weapon option reachable for a unit (not a
  guessed "default" loadout), each as its own row -- same as Orks. Ability
  text has markdown syntax (**bold**, ^^highlight^^, *italic*) stripped at
  generation time, since BSData's source text embeds it and our templates
  render it as literal characters.
- Known gaps, left untouched (existing data kept as-is):
  * Stats: Brotherhood Terminator Squad, Paladin Squad -- stat profile not
    resolvable via the recursive search for these two units.
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from calculators.models import UnitAbility, UnitType, WeaponProfile

# (name -> {stats?, weapons?, abilities?}). Missing keys mean "no data
# found for this field -- leave existing DB data untouched."
GREY_KNIGHTS_DATASHEETS = {
    "Brother-Captain": {
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
                "name": "Nemesis force weapon",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "2+",
                "strength": "6",
                "ap": "-2",
                "damage": "2",
                "keywords": "Psychic"
            },
            {
                "name": "Storm bolter",
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
                "name": "Incinerator",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "D6",
                "skill": "N/A",
                "strength": "6",
                "ap": "-1",
                "damage": "1",
                "keywords": "Ignores Cover, Torrent"
            },
            {
                "name": "Psycannon",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "3",
                "skill": "2+",
                "strength": "8",
                "ap": "-1",
                "damage": "2",
                "keywords": "Psychic"
            },
            {
                "name": "Psilencer",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "6",
                "skill": "2+",
                "strength": "5",
                "ap": "0",
                "damage": "1",
                "keywords": "Precision, Psychic, Sustained Hits 1"
            }
        ],
        "abilities": [
            {
                "name": "Leader",
                "description": "This model can be attached to the following units:\n\u25a0 Brotherhood Terminator Squad\n\u25a0 Paladin Squad"
            },
            {
                "name": "Hammerhand (Psychic)",
                "description": "While this model is leading a unit, melee weapons equipped by models in that unit have the [Lethal Hits] ability."
            },
            {
                "name": "Eye of Judgement (Psychic)",
                "description": "Each time this model makes an attack, you can re-roll the Wound roll."
            }
        ]
    },
    "Brotherhood Champion": {
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
                "name": "Nemesis force weapon",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "5",
                "skill": "2+",
                "strength": "6",
                "ap": "-2",
                "damage": "2",
                "keywords": "Precision, Psychic"
            },
            {
                "name": "Storm bolter",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "2",
                "skill": "2+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Rapid Fire 2"
            }
        ],
        "abilities": [
            {
                "name": "Leader",
                "description": "This model can be attached to the following units:\n\u25a0 Purgation Squad\n\u25a0 Strike Squad"
            },
            {
                "name": "Clarion of Haste (Psychic)",
                "description": "While this model is leading a unit, that unit is eligible to declare a charge in a turn in which it Advanced."
            },
            {
                "name": "Inspiring Exemplar",
                "description": "Each time this model destroys a Character model in the Fight phase, you gain 1CP and, until the end of the battle, add 1 to the Attacks characteristic of its Nemesis force weapon."
            }
        ]
    },
    "Brotherhood Chaplain": {
        "stats": {
            "stat_movement": "5\"",
            "stat_toughness": 5,
            "stat_save": "2+",
            "stat_wounds": 5,
            "stat_leadership": "5+",
            "stat_oc": 1,
            "stat_invuln": "4+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Crozius arcanum",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "5",
                "skill": "2+",
                "strength": "6",
                "ap": "-1",
                "damage": "2",
                "keywords": "-"
            },
            {
                "name": "Storm bolter",
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
                "name": "Zealous Path",
                "description": "While this model is leading a unit, you can re-roll Charge rolls made for that unit."
            },
            {
                "name": "Leader",
                "description": "This model can be attached to the following units:\n\u25a0 Brotherhood Terminator Squad\n\u25a0 Paladin Squad"
            }
        ]
    },
    "Brotherhood Librarian": {
        "stats": {
            "stat_movement": "5\"",
            "stat_toughness": 5,
            "stat_save": "2+",
            "stat_wounds": 5,
            "stat_leadership": "6+",
            "stat_oc": 1,
            "stat_invuln": "4+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Nemesis force weapon",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "2+",
                "strength": "6",
                "ap": "-1",
                "damage": "2",
                "keywords": "Psychic"
            },
            {
                "name": "Vortex of Doom",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "D6+3",
                "skill": "3+",
                "strength": "8",
                "ap": "-2",
                "damage": "2",
                "keywords": "Blast, Psychic"
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
                "keywords": "Anti-infantry 4+, Devastating Wounds, Rapid Fire 1"
            },
            {
                "name": "Storm bolter",
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
                "name": "Haloed in Soulfire (Psychic)",
                "description": "While this model is leading a unit, that unit can only be selected as the target of a ranged attack if the attacking model is within 18\"."
            },
            {
                "name": "Leader",
                "description": "This model can be attached to the following units:\n- Brotherhood Terminator Squad\n- Paladin Squad"
            },
            {
                "name": "Sanctic Hood",
                "description": "While this model is leading a unit, models in that unit have the Feel No Pain 4+ ability against Psychic Attacks."
            }
        ]
    },
    "Brotherhood Techmarine": {
        "stats": {
            "stat_movement": "6\"",
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
                "name": "Servo-arm",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "1",
                "skill": "3+",
                "strength": "8",
                "ap": "-2",
                "damage": "3",
                "keywords": "Extra Attacks"
            },
            {
                "name": "Omnissian power axe",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "3+",
                "strength": "6",
                "ap": "-2",
                "damage": "2",
                "keywords": "-"
            },
            {
                "name": "Grav-pistol",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "1",
                "skill": "2+",
                "strength": "4",
                "ap": "-1",
                "damage": "2",
                "keywords": "Anti-Vehicle 2+, Pistol"
            },
            {
                "name": "Forge bolter",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "3",
                "skill": "2+",
                "strength": "5",
                "ap": "-1",
                "damage": "2",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Leader",
                "description": "This model can be attached to the following units:\n\u25a0 Strike Squad\n\u25a0 Purgation Squad\n\u25a0 Purifier Squad"
            },
            {
                "name": "Guardians of the Machine",
                "description": "Each time an enemy unit ends a charge move engaged with one or more friendly GREY KNIGHTS VEHICLE units and within 6\" of this unit, you can target this unit with the Heroic Intervention stratagem, regardless of any other uses of that stratagem this phase. If you do:\n- That use is -1 CP.\n- That use does not prevent any uses of that stratagem on other units this phase."
            },
            {
                "name": "Blessing of the Omnissiah",
                "description": "In your Command phase, you can select one friendly Grey Knights Vehicle model within 3\" of this model. That model regains up to D3 lost wounds and, until the start of your next Command phase, each time that Vehicle model makes an attack, add 1 to the Hit roll. Each model can only be selected for this ability once per turn."
            },
            {
                "name": "Techmarine",
                "description": "While this model is within 3\" of one or more friendly Grey Knights Vehicle units, this model has the Lone Operative ability."
            }
        ]
    },
    "Brotherhood Terminator Squad": {
        "weapons": [
            {
                "name": "Nemesis force weapon",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "3+",
                "strength": "6",
                "ap": "-2",
                "damage": "2",
                "keywords": "Psychic"
            },
            {
                "name": "Storm bolter",
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
                "name": "Incinerator",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "D6",
                "skill": "N/A",
                "strength": "6",
                "ap": "-1",
                "damage": "1",
                "keywords": "Ignores Cover, Torrent"
            },
            {
                "name": "Psycannon",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "3",
                "skill": "3+",
                "strength": "8",
                "ap": "-1",
                "damage": "2",
                "keywords": "Psychic"
            },
            {
                "name": "Psilencer",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "6",
                "skill": "3+",
                "strength": "5",
                "ap": "0",
                "damage": "1",
                "keywords": "Precision, Psychic, Sustained Hits 1"
            }
        ],
        "abilities": [
            {
                "name": "Force Edge (Psychic)",
                "description": "Each time a model in this unit makes a melee attack that targets a unit (excluding Vehicles or Monsters), improve the Armour Penetration characteristic of that attack by 1."
            }
        ]
    },
    "Castellan Crowe": {
        "stats": {
            "stat_movement": "6\"",
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
                "name": "Storm bolter",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "2",
                "skill": "2+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Rapid Fire 2"
            }
        ],
        "abilities": [
            {
                "name": "Champion of the Order of Purifiers (Psychic)",
                "description": "While this model is leading a unit, add 1 to the Attacks characteristic of Purifying Flame weapons equipped by that unit."
            },
            {
                "name": "Foesight (Psychic)",
                "description": "Each time this model makes an attack that targets a Character unit, you can re-roll the Hit roll."
            },
            {
                "name": "Leader",
                "description": "This model can be attached to the following unit:\n\u25a0 Purifier Squad"
            }
        ]
    },
    "Grand Master": {
        "stats": {
            "stat_movement": "5\"",
            "stat_toughness": 5,
            "stat_save": "2+",
            "stat_wounds": 7,
            "stat_leadership": "6+",
            "stat_oc": 1,
            "stat_invuln": "4+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Nemesis force weapon",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "5",
                "skill": "2+",
                "strength": "6",
                "ap": "-2",
                "damage": "2",
                "keywords": "Psychic"
            },
            {
                "name": "Storm bolter",
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
                "name": "Incinerator",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "D6",
                "skill": "N/A",
                "strength": "6",
                "ap": "-1",
                "damage": "1",
                "keywords": "Ignores Cover, Torrent"
            },
            {
                "name": "Psycannon",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "3",
                "skill": "2+",
                "strength": "8",
                "ap": "-1",
                "damage": "2",
                "keywords": "Psychic"
            },
            {
                "name": "Psilencer",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "6",
                "skill": "2+",
                "strength": "5",
                "ap": "0",
                "damage": "1",
                "keywords": "Precision, Psychic, Sustained Hits 1"
            }
        ],
        "abilities": [
            {
                "name": "Might of Titan (Psychic)",
                "description": "Once per battle, at the start of the Fight phase, this model can use this ability. If it does, until the end of the phase, add 3 to the Attacks and Strength characteristics of melee weapons equipped by this model."
            },
            {
                "name": "Leader",
                "description": "This model can be attached to the following units:\n- Brotherhood Terminator Squad\n- Paladin Squad"
            }
        ]
    },
    "Grand Master Voldus": {
        "stats": {
            "stat_movement": "5\"",
            "stat_toughness": 5,
            "stat_save": "2+",
            "stat_wounds": 7,
            "stat_leadership": "6+",
            "stat_oc": 1,
            "stat_invuln": "4+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Storm bolter",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "2",
                "skill": "2+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Rapid Fire 2"
            }
        ],
        "abilities": [
            {
                "name": "Sanctuary (Psychic)",
                "description": "- This unit has Stealth.\n- Melee attacks that target this unit have -1 to hit rolls."
            },
            {
                "name": "Hammer Aflame (Psychic)",
                "description": "Each time this model\u2019s unit is selected to fight, you can select one enemy unit within Engagement Range of this model\u2019s unit and roll one D6: on a 2-3, that enemy unit suffers 1 mortal wound; on a 4-5, that enemy unit suffers D3 mortal wounds; on a 6+, that enemy unit suffers D3+3 mortal wounds."
            },
            {
                "name": "Leader",
                "description": "This model can be attached to the following units:\n\u25a0 Brotherhood Terminator Squad\n\u25a0 Paladin Squad"
            }
        ]
    },
    "Grand Master in Nemesis Dreadknight": {
        "stats": {
            "stat_movement": "8\"",
            "stat_toughness": 8,
            "stat_save": "2+",
            "stat_wounds": 13,
            "stat_leadership": "6+",
            "stat_oc": 4,
            "stat_invuln": "4+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Fragstorm grenade launcher",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "D6",
                "skill": "3+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Blast"
            },
            {
                "name": "Nemesis mace",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "5",
                "skill": "2+",
                "strength": "6",
                "ap": "-3",
                "damage": "3",
                "keywords": "Anti-Character 2+, Precision, Psychic"
            },
            {
                "name": "Nemesis flail",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "10",
                "skill": "2+",
                "strength": "5",
                "ap": "-1",
                "damage": "2",
                "keywords": "Psychic"
            },
            {
                "name": "Dreadfists",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "6",
                "skill": "2+",
                "strength": "6",
                "ap": "-1",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "Nemesis daemon greathammer",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "5",
                "skill": "3+",
                "strength": "14",
                "ap": "-3",
                "damage": "D6+1",
                "keywords": "Psychic"
            },
            {
                "name": "\u27a4 Nemesis greatsword - strike",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "5",
                "skill": "2+",
                "strength": "10",
                "ap": "-2",
                "damage": "D6",
                "keywords": "Psychic"
            },
            {
                "name": "\u27a4 Nemesis greatsword - sweep",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "10",
                "skill": "2+",
                "strength": "5",
                "ap": "-1",
                "damage": "1",
                "keywords": "Psychic"
            },
            {
                "name": "Sublimator",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "2",
                "skill": "3+",
                "strength": "9",
                "ap": "-4",
                "damage": "D6",
                "keywords": "Melta 4, Psychic, Twin-linked"
            },
            {
                "name": "Gatling psilencer",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "12",
                "skill": "3+",
                "strength": "6",
                "ap": "0",
                "damage": "1",
                "keywords": "Psychic, Sustained Hits 1"
            },
            {
                "name": "Heavy incinerator",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "2D6",
                "skill": "N/A",
                "strength": "6",
                "ap": "-1",
                "damage": "1",
                "keywords": "Ignores Cover, Torrent"
            },
            {
                "name": "Heavy psycannon",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "6",
                "skill": "3+",
                "strength": "10",
                "ap": "-2",
                "damage": "3",
                "keywords": "Ignores Cover, Psychic"
            }
        ],
        "abilities": [
            {
                "name": "Surge of Wrath (Psychic)",
                "description": "Each time this model makes a melee attack that targets a Monster or Vehicle unit, you can re-roll the Hit roll, you can re-roll the Wound roll and you can re-roll the Damage roll."
            }
        ]
    },
    "Interceptor Squad": {
        "stats": {
            "stat_movement": "12\"",
            "stat_toughness": 4,
            "stat_save": "2+",
            "stat_wounds": 2,
            "stat_leadership": "6+",
            "stat_oc": 1,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Nemesis force weapon",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "3",
                "skill": "3+",
                "strength": "6",
                "ap": "-2",
                "damage": "2",
                "keywords": "Psychic"
            },
            {
                "name": "Storm bolter",
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
                "name": "Incinerator",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "D6",
                "skill": "N/A",
                "strength": "6",
                "ap": "-1",
                "damage": "1",
                "keywords": "Ignores Cover, Torrent"
            },
            {
                "name": "Psilencer",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "6",
                "skill": "3+",
                "strength": "5",
                "ap": "0",
                "damage": "1",
                "keywords": "Precision, Psychic, Sustained Hits 1"
            },
            {
                "name": "Psycannon",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "3",
                "skill": "3+",
                "strength": "8",
                "ap": "-1",
                "damage": "2",
                "keywords": "Psychic"
            }
        ],
        "abilities": [
            {
                "name": "Personal Teleporters",
                "description": "In your Shooting phase, after this unit has shot, if it is not within Engagement Range of one or more enemy units, it can make a Normal move of up to 6\" as if it were your Movement phase. If it does, until the end of the turn, this unit is not eligible to declare a charge."
            }
        ]
    },
    "Land Raider": {
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
                "name": "Godhammer lascannon",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "2",
                "skill": "3+",
                "strength": "12",
                "ap": "-3",
                "damage": "D6+1",
                "keywords": "-"
            },
            {
                "name": "Storm bolter",
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
                "name": "Hunter-killer missile",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "1",
                "skill": "2+",
                "strength": "14",
                "ap": "-3",
                "damage": "D6",
                "keywords": "One Shot"
            },
            {
                "name": "Multi-melta",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "2",
                "skill": "3+",
                "strength": "9",
                "ap": "-4",
                "damage": "D6",
                "keywords": "Melta 2"
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
                "name": "Armoured tracks",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "6",
                "skill": "4+",
                "strength": "8",
                "ap": "0",
                "damage": "1",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Assault Ramp",
                "description": "Each time a unit disembarks from this model after it has made a Normal move, that unit is still eligible to declare a charge this turn."
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
        "weapons": [
            {
                "name": "Storm bolter",
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
                "name": "Hunter-killer missile",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "1",
                "skill": "2+",
                "strength": "14",
                "ap": "-3",
                "damage": "D6",
                "keywords": "One Shot"
            },
            {
                "name": "Multi-melta",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "2",
                "skill": "3+",
                "strength": "9",
                "ap": "-4",
                "damage": "D6",
                "keywords": "Melta 2"
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
                "name": "Armoured tracks",
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
                "name": "Hurricane bolter",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "6",
                "skill": "3+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Rapid Fire 6, Twin-Linked"
            }
        ],
        "abilities": [
            {
                "name": "Assault Ramp",
                "description": "Each time a unit disembarks from this model after it has made a Normal move, that unit is still eligible to declare a charge this turn."
            }
        ]
    },
    "Land Raider Redeemer": {
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
        "weapons": [
            {
                "name": "Flamestorm cannon",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "D6+3",
                "skill": "N/A",
                "strength": "6",
                "ap": "-2",
                "damage": "2",
                "keywords": "Ignores Cover, Torrent"
            },
            {
                "name": "Storm bolter",
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
                "name": "Hunter-killer missile",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "1",
                "skill": "2+",
                "strength": "14",
                "ap": "-3",
                "damage": "D6",
                "keywords": "One Shot"
            },
            {
                "name": "Multi-melta",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "2",
                "skill": "3+",
                "strength": "9",
                "ap": "-4",
                "damage": "D6",
                "keywords": "Melta 2"
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
                "name": "Armoured tracks",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "6",
                "skill": "4+",
                "strength": "8",
                "ap": "0",
                "damage": "1",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Assault Ramp",
                "description": "Each time a unit disembarks from this model after it has made a Normal move, that unit is still eligible to declare a charge this turn."
            }
        ]
    },
    "Nemesis Dreadknight": {
        "stats": {
            "stat_movement": "8\"",
            "stat_toughness": 8,
            "stat_save": "2+",
            "stat_wounds": 13,
            "stat_leadership": "6+",
            "stat_oc": 4,
            "stat_invuln": "4+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "\u27a4 Nemesis greatsword - strike",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "5",
                "skill": "2+",
                "strength": "10",
                "ap": "-2",
                "damage": "D6",
                "keywords": "Psychic"
            },
            {
                "name": "\u27a4 Nemesis greatsword - sweep",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "10",
                "skill": "2+",
                "strength": "5",
                "ap": "-1",
                "damage": "1",
                "keywords": "Psychic"
            },
            {
                "name": "Nemesis daemon greathammer",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "5",
                "skill": "3+",
                "strength": "14",
                "ap": "-3",
                "damage": "D6+1",
                "keywords": "Psychic"
            },
            {
                "name": "Dreadfists",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "6",
                "skill": "2+",
                "strength": "6",
                "ap": "-1",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "Gatling psilencer",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "12",
                "skill": "3+",
                "strength": "6",
                "ap": "0",
                "damage": "1",
                "keywords": "Psychic, Sustained Hits 1"
            },
            {
                "name": "Heavy psycannon",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "6",
                "skill": "3+",
                "strength": "10",
                "ap": "-2",
                "damage": "3",
                "keywords": "Ignores Cover, Psychic"
            },
            {
                "name": "Heavy incinerator",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "2D6",
                "skill": "N/A",
                "strength": "6",
                "ap": "-1",
                "damage": "1",
                "keywords": "Ignores Cover, Torrent"
            }
        ],
        "abilities": [
            {
                "name": "Indomitable Spirit (Psychic)",
                "description": "This model is eligible to shoot and declare a charge in a turn in which it Advanced or Fell Back."
            }
        ]
    },
    "Paladin Squad": {
        "weapons": [
            {
                "name": "Nemesis force weapon",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "2+",
                "strength": "6",
                "ap": "-2",
                "damage": "2",
                "keywords": "Psychic"
            },
            {
                "name": "Storm bolter",
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
                "name": "Incinerator",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "D6",
                "skill": "N/A",
                "strength": "6",
                "ap": "-1",
                "damage": "1",
                "keywords": "Ignores Cover, Torrent"
            },
            {
                "name": "Psycannon",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "3",
                "skill": "2+",
                "strength": "8",
                "ap": "-1",
                "damage": "2",
                "keywords": "Psychic"
            },
            {
                "name": "Psilencer",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "6",
                "skill": "2+",
                "strength": "5",
                "ap": "0",
                "damage": "1",
                "keywords": "Precision, Psychic, Sustained Hits 1"
            }
        ],
        "abilities": [
            {
                "name": "Attuned Onslaught (Psychic)",
                "description": "Each time this unit makes a Charge move, until the end of the turn, add 1 to the Damage characteristic of melee weapons equipped by Paladin Squad models in this unit."
            }
        ]
    },
    "Purgation Squad": {
        "stats": {
            "stat_movement": "6\"",
            "stat_toughness": 4,
            "stat_save": "2+",
            "stat_wounds": 2,
            "stat_leadership": "6+",
            "stat_oc": 1,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Nemesis force weapon",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "3",
                "skill": "3+",
                "strength": "6",
                "ap": "-2",
                "damage": "2",
                "keywords": "Psychic"
            },
            {
                "name": "Storm bolter",
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
                "name": "Incinerator",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "D6",
                "skill": "N/A",
                "strength": "6",
                "ap": "-1",
                "damage": "1",
                "keywords": "Ignores Cover, Torrent"
            },
            {
                "name": "Psilencer",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "6",
                "skill": "3+",
                "strength": "5",
                "ap": "0",
                "damage": "1",
                "keywords": "Precision, Psychic, Sustained Hits 1"
            },
            {
                "name": "Psycannon",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "3",
                "skill": "3+",
                "strength": "8",
                "ap": "-1",
                "damage": "2",
                "keywords": "Psychic"
            }
        ],
        "abilities": [
            {
                "name": "Righteous Persecution",
                "description": "In your Shooting phase, after this unit has shot, select one enemy unit (excluding Monsters or Vehicles) hit by one or more of those attacks; until the start of your next turn, that enemy unit is pinned. While a unit is pinned, subtract 2 from that unit's Move characteristic and subtract 2 from Charge rolls made for it."
            }
        ]
    },
    "Purifier Squad": {
        "stats": {
            "stat_movement": "6\"",
            "stat_toughness": 4,
            "stat_save": "2+",
            "stat_wounds": 2,
            "stat_leadership": "6+",
            "stat_oc": 1,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Nemesis force weapon",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "3",
                "skill": "3+",
                "strength": "6",
                "ap": "-2",
                "damage": "2",
                "keywords": "Psychic"
            },
            {
                "name": "Storm bolter",
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
                "name": "Purifying Flame",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "4",
                "ap": "-2",
                "damage": "1",
                "keywords": "Anti-Infantry 2+, Ignores Cover, Psychic"
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
                "name": "Incinerator",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "D6",
                "skill": "N/A",
                "strength": "6",
                "ap": "-1",
                "damage": "1",
                "keywords": "Ignores Cover, Torrent"
            },
            {
                "name": "Psilencer",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "6",
                "skill": "3+",
                "strength": "5",
                "ap": "0",
                "damage": "1",
                "keywords": "Precision, Psychic, Sustained Hits 1"
            },
            {
                "name": "Psycannon",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "3",
                "skill": "3+",
                "strength": "8",
                "ap": "-1",
                "damage": "2",
                "keywords": "Psychic"
            }
        ],
        "abilities": [
            {
                "name": "Sanctity of Purpose",
                "description": "Each time a model in this unit makes an attack, re-roll a Wound roll of 1. If the target is within range of an objective marker, you can re-roll the Wound roll instead."
            }
        ]
    },
    "Razorback": {
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
                "name": "Storm bolter",
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
                "name": "Hunter-killer missile",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "1",
                "skill": "2+",
                "strength": "14",
                "ap": "-3",
                "damage": "D6",
                "keywords": "One Shot"
            },
            {
                "name": "Armoured tracks",
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
                "name": "Twin lascannon",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "12",
                "ap": "-3",
                "damage": "D6+1",
                "keywords": "Twin-linked"
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
            }
        ],
        "abilities": [
            {
                "name": "Fire Focus",
                "description": "In your Shooting phase, after this model has shot, select one enemy unit hit by one or more of those attacks. Until the end of the turn, each time a friendly model that disembarked from this Transport this turn makes an attack that targets that enemy unit, improve the Armour Penetration characteristic of that attack by 1. The same enemy unit can only be affected by this ability once per turn."
            }
        ]
    },
    "Rhino": {
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
                "name": "Storm bolter",
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
                "name": "Hunter-killer missile",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "1",
                "skill": "2+",
                "strength": "14",
                "ap": "-3",
                "damage": "D6",
                "keywords": "One Shot"
            },
            {
                "name": "Armoured tracks",
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
                "name": "Truesilver Aegis (Psychic)",
                "description": "While a friendly Grey Knights unit is wholly within 6\" of this model, models in that unit have the Feel No Pain 6+ ability against mortal wounds."
            }
        ]
    },
    "Stormhawk Interceptor": {
        "stats": {
            "stat_movement": "-",
            "stat_toughness": 9,
            "stat_save": "3+",
            "stat_wounds": 10,
            "stat_leadership": "6+",
            "stat_oc": None,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
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
                "name": "\u27a4 Typhoon missile launcher - frag",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "2D6",
                "skill": "3+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Blast"
            },
            {
                "name": "\u27a4 Typhoon missile launcher - krak",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "2",
                "skill": "3+",
                "strength": "9",
                "ap": "-2",
                "damage": "D6",
                "keywords": "-"
            },
            {
                "name": "Skyhammer missile launcher",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "3",
                "skill": "3+",
                "strength": "8",
                "ap": "-1",
                "damage": "D3",
                "keywords": "Anti-Fly 2+"
            },
            {
                "name": "Las-talon",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "2",
                "skill": "3+",
                "strength": "10",
                "ap": "-3",
                "damage": "D6+1",
                "keywords": "-"
            },
            {
                "name": "Icarus stormcannon",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "6",
                "skill": "3+",
                "strength": "7",
                "ap": "-1",
                "damage": "2",
                "keywords": "Anti-Fly 2+"
            }
        ],
        "abilities": [
            {
                "name": "Interceptor",
                "description": "Each time this model makes a ranged attack that targets a unit that can Fly, add 1 to the Hit roll."
            }
        ]
    },
    "Stormraven Gunship": {
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
                "name": "Armoured hull",
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
                "name": "Stormstrike missile launcher",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "10",
                "ap": "-3",
                "damage": "D6+2",
                "keywords": "-"
            },
            {
                "name": "\u27a4 Twin heavy plasma cannon - standard",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "3",
                "skill": "3+",
                "strength": "7",
                "ap": "-2",
                "damage": "2",
                "keywords": "Blast, Twin-linked"
            },
            {
                "name": "\u27a4 Twin heavy plasma cannon - supercharge",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "3",
                "skill": "3+",
                "strength": "8",
                "ap": "-3",
                "damage": "3",
                "keywords": "Blast, Hazardous, Twin-linked"
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
                "keywords": "Twin-linked"
            },
            {
                "name": "Twin multi-melta",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "2",
                "skill": "3+",
                "strength": "9",
                "ap": "-4",
                "damage": "D6",
                "keywords": "Melta 2, Twin-linked"
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
                "name": "\u27a4 Typhoon missile launcher - frag",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "2D6",
                "skill": "3+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Blast"
            },
            {
                "name": "\u27a4 Typhoon missile launcher - krak",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "2",
                "skill": "3+",
                "strength": "9",
                "ap": "-2",
                "damage": "D6",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Armoured Resilience",
                "description": "Each time an attack is allocated to this model, subtract 1 from the Damage characteristic of that attack."
            }
        ]
    },
    "Stormtalon Gunship": {
        "stats": {
            "stat_movement": "-",
            "stat_toughness": 9,
            "stat_save": "3+",
            "stat_wounds": 10,
            "stat_leadership": "6+",
            "stat_oc": None,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
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
                "name": "Twin lascannon",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "12",
                "ap": "-3",
                "damage": "D6+1",
                "keywords": "Twin-linked"
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
                "name": "\u27a4 Typhoon missile launcher - frag",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "2D6",
                "skill": "3+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Blast"
            },
            {
                "name": "\u27a4 Typhoon missile launcher - krak",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "2",
                "skill": "3+",
                "strength": "9",
                "ap": "-2",
                "damage": "D6",
                "keywords": "-"
            },
            {
                "name": "Skyhammer missile launcher",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "3",
                "skill": "3+",
                "strength": "8",
                "ap": "-1",
                "damage": "D3",
                "keywords": "Anti-Fly 2+"
            }
        ],
        "abilities": [
            {
                "name": "Strafing Run",
                "description": "Each time this model makes a ranged attack that targets a unit that cannot Fly, add 1 to the Hit roll"
            }
        ]
    },
    "Strike Squad": {
        "stats": {
            "stat_movement": "6\"",
            "stat_toughness": 4,
            "stat_save": "2+",
            "stat_wounds": 2,
            "stat_leadership": "6+",
            "stat_oc": 2,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Nemesis force weapon",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "3",
                "skill": "3+",
                "strength": "6",
                "ap": "-2",
                "damage": "2",
                "keywords": "Psychic"
            },
            {
                "name": "Storm bolter",
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
                "name": "Incinerator",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "D6",
                "skill": "N/A",
                "strength": "6",
                "ap": "-1",
                "damage": "1",
                "keywords": "Ignores Cover, Torrent"
            },
            {
                "name": "Psycannon",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "3",
                "skill": "3+",
                "strength": "8",
                "ap": "-1",
                "damage": "2",
                "keywords": "Psychic"
            },
            {
                "name": "Psilencer",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "6",
                "skill": "3+",
                "strength": "5",
                "ap": "0",
                "damage": "1",
                "keywords": "Precision, Psychic, Sustained Hits 1"
            }
        ],
        "abilities": [
            {
                "name": "Sanctifying Ritual (Psychic)",
                "description": "At the end of your Command phase, if this unit is within range of an objective marker that you control, that objective marker remains under you control until your opponent's Level of Control over that objective marker is greater than yours at the end of a phase."
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
                "name": "\u27a4 Heavy plasma cannon - standard",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "D3",
                "skill": "3+",
                "strength": "7",
                "ap": "-2",
                "damage": "2",
                "keywords": "Blast"
            },
            {
                "name": "\u27a4 Heavy plasma cannon - supercharge",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "D3",
                "skill": "3+",
                "strength": "8",
                "ap": "-3",
                "damage": "3",
                "keywords": "Blast, Hazardous"
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
                "keywords": "Twin-linked"
            },
            {
                "name": "Storm bolter",
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
                "name": "Dreadnought combat weapon",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "5",
                "skill": "3+",
                "strength": "12",
                "ap": "-2",
                "damage": "3",
                "keywords": "-"
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
                "name": "Guidance of the Ancients (Psychic)",
                "description": "In your Shooting phase, after this unit has shot, select one enemy unit hit by one or more of those attacks. Until the end of the phase, each time a Grey Knights model from your army makes an attack which targets that unit, add 1 to the Hit roll."
            }
        ]
    }
}


class Command(BaseCommand):
    """Refresh Grey Knights stat lines, weapon profiles, and abilities from BSData."""

    help = 'Refresh 11th Edition stats/weapons/abilities for Grey Knights units.'

    def add_arguments(self, parser):
        """Add --dry-run flag."""
        parser.add_argument(
            '--dry-run', action='store_true',
            help='Preview changes without writing to the database.',
        )

    def handle(self, *args, **options):
        """Iterate GREY_KNIGHTS_DATASHEETS and refresh each unit's datasheet data."""
        dry_run = options['dry_run']
        updated = 0
        skipped = 0

        with transaction.atomic():
            for name, payload in GREY_KNIGHTS_DATASHEETS.items():
                try:
                    unit = UnitType.objects.get(name=name, faction__name='Grey Knights')
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
