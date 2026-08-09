"""
Management command: seed_sisters_of_battle_datasheets

Refreshes stat lines, weapon profiles, and abilities for Sisters of
Battle units using 11th Edition data sourced from BSData/wh40k-11e
("Imperium - Adepta Sororitas.json") -- the same source used by
seed_sisters_of_battle_points.py. Supersedes the older hand-authored
seed_sisters_of_battle_stats.py -- left in place, not deleted.

Usage:
    python manage.py seed_sisters_of_battle_datasheets
    python manage.py seed_sisters_of_battle_datasheets --dry-run

Notes:
- Does NOT touch points_cost or category -- those are handled entirely by
  seed_sisters_of_battle_points.py. This command only refreshes stat_*
  fields, WeaponProfile rows, and UnitAbility rows.
- Per-field safety rule: a unit's stats/weapons/abilities are only
  overwritten when BSData actually has that data for it. If extraction
  found nothing, the existing DB value/rows are left untouched.
- All 33 active units resolved cleanly -- 0 missing stats/weapons/
  abilities, 0 overlong stat fields.
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from calculators.models import UnitAbility, UnitType, WeaponProfile

# (name -> {stats?, weapons?, abilities?}). Missing keys mean "no data
# found for this field -- leave existing DB data untouched."
SISTERS_OF_BATTLE_DATASHEETS = {
    "Aestred Thurga and Agathae Dolan": {
        "stats": {
            "stat_movement": "6\"",
            "stat_toughness": 3,
            "stat_save": "2+",
            "stat_wounds": 4,
            "stat_leadership": "6+",
            "stat_oc": 1,
            "stat_invuln": "4+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Blade of Vigil",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "2+",
                "strength": "5",
                "ap": "-2",
                "damage": "2",
                "keywords": "-"
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
            },
            {
                "name": "Scribe's staff",
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
                "name": "Auto-Tapestry of the Emperor's Judgement",
                "description": "While this unit is leading a unit and contains an Aestred Thurga model, weapons equipped by models in that unit have the [DEVASTATING WOUNDS] ability"
            },
            {
                "name": "Recount the Deeds of the Saints",
                "description": "While this unit is leading a unit and contains and Agathae Dolan model, each time that unit destroys an enemy unit, you gain 1 Miracle dice. When that Agathae Dolan model is destroyed, you gain D3 Miracle dice."
            }
        ]
    },
    "Arco-Flagellants": {
        "stats": {
            "stat_movement": "7\"",
            "stat_toughness": 3,
            "stat_save": "7+",
            "stat_wounds": 2,
            "stat_leadership": "8+",
            "stat_oc": 1,
            "stat_invuln": "6+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Arco-flails",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "4+",
                "strength": "5",
                "ap": "0",
                "damage": "1",
                "keywords": "Sustained Hits 1"
            }
        ],
        "abilities": [
            {
                "name": "Extremis Trigger Word",
                "description": "Each time this unit is selected to fight, you can choose to invoke its extremis trigger word. If you do, then until the end of the phase, arco-flails equipped by models in this unit have an Attacks characteristic of 6 and the HAZARDOUS ability."
            }
        ]
    },
    "Battle Sisters Squad": {
        "stats": {
            "stat_movement": "6\"",
            "stat_toughness": 3,
            "stat_save": "3+",
            "stat_wounds": 1,
            "stat_leadership": "7+",
            "stat_oc": 2,
            "stat_invuln": "6+",
            "stat_fnp": ""
        },
        "weapons": [
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
                "name": "Boltgun",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Rapid Fire 1"
            }
        ],
        "abilities": [
            {
                "name": "Defenders of the Faith",
                "description": "At the end of your Command phase, if this unit is within range of an objective marker you control, that objective marker remains under your control, even if you have no models within range of it, until your opponent controls it at the start or end of any turn."
            },
            {
                "name": "Cherub",
                "description": "Once per battle, after this unit has performed an Act of Faith, you gain 1 Miracle dice."
            },
            {
                "name": "Simulacrum Imperialis",
                "description": "At the end of your Command phase, for each objective marker you control that has one or more units from your army with this ability within range of it, roll one D6: on a 4+, you gain 1 Miracle dice showing a value equal to that result."
            }
        ]
    },
    "Canoness": {
        "stats": {
            "stat_movement": "6\"",
            "stat_toughness": 3,
            "stat_save": "3+",
            "stat_wounds": 4,
            "stat_leadership": "7+",
            "stat_oc": 1,
            "stat_invuln": "4+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Brazier of Holy Fire",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "D6",
                "skill": "N/A",
                "strength": "6",
                "ap": "-1",
                "damage": "2",
                "keywords": "Ignores Cover, One Shot, Torrent"
            },
            {
                "name": "Blessed blade",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "2+",
                "strength": "6",
                "ap": "-2",
                "damage": "2",
                "keywords": "Lethal Hits"
            },
            {
                "name": "Power weapon",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "2+",
                "strength": "4",
                "ap": "-2",
                "damage": "2",
                "keywords": "-"
            },
            {
                "name": "Hallowed Chainsword",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "5",
                "skill": "2+",
                "strength": "3",
                "ap": "-1",
                "damage": "1",
                "keywords": "-"
            },
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
                "name": "Condemnor boltgun",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "1",
                "skill": "2+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Anti-Psyker 2+, Devastating Wounds, Precision, Rapid Fire 1"
            },
            {
                "name": "Inferno Pistol",
                "weapon_type": "ranged",
                "range": "6\"",
                "attacks": "1",
                "skill": "2+",
                "strength": "8",
                "ap": "-4",
                "damage": "D3",
                "keywords": "Melta 2, Pistol"
            },
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
                "ap": "-3",
                "damage": "2",
                "keywords": "Hazardous, Pistol"
            }
        ],
        "abilities": [
            {
                "name": "The Emperor's Grace",
                "description": "Once per battle, at the start of any phase, this model can use this ability. If it does, until the end of the phase, this model has a 2+ invulnerable save."
            },
            {
                "name": "Sacred Command",
                "description": "Once per battle round, one unit from your army with this ability can use it when its unit is targeted with a Stratagem. If it does, reduce the CP cost of that use of that Stratagem by 1CP."
            },
            {
                "name": "Null Rod",
                "description": "Models in the bearer\u2019s unit have the Feel No Pain 4+ ability against mortal wounds and Psychic Attacks."
            },
            {
                "name": "Rod of Office",
                "description": "Each time a model in the bearer's unit makes an attack, re-roll a Hit roll of 1."
            }
        ]
    },
    "Canoness with Jump Pack": {
        "stats": {
            "stat_movement": "12\"",
            "stat_toughness": 3,
            "stat_save": "3+",
            "stat_wounds": 3,
            "stat_leadership": "7+",
            "stat_oc": 1,
            "stat_invuln": "4+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Blessed Halberd",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "5",
                "skill": "2+",
                "strength": "5",
                "ap": "-2",
                "damage": "2",
                "keywords": "-"
            },
            {
                "name": "Power weapon",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "2+",
                "strength": "4",
                "ap": "-2",
                "damage": "2",
                "keywords": "-"
            },
            {
                "name": "Ministorum hand flamer",
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
                "name": "Holy Eviscerator",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "3",
                "skill": "2+",
                "strength": "6",
                "ap": "-2",
                "damage": "2",
                "keywords": "Sustained Hits 1"
            }
        ],
        "abilities": [
            {
                "name": "Divine Deliverance",
                "description": "Once per battle, at the start of the Fight phase, this model can use this ability. If it does, until the end of the phase, add 3 to the Attacks characteristic of melee weapons equipped by the model and those weapons have the [DEVASTATING WOUNDS] ability"
            },
            {
                "name": "Sacred Command",
                "description": "Once per battle round, one unit from your army with this ability can use it when its unit is targeted with a Stratagem. If it does, reduce the CP cost of that use of that Stratagem by 1CP."
            },
            {
                "name": "Condemnatory Psalms",
                "description": "In your Shooting phase, this unit can select one visible enemy unit within 12\". That enemy unit is condemned:\n- While a unit is condemned, that unit has +3\" detection range."
            }
        ]
    },
    "Castigator": {
        "stats": {
            "stat_movement": "10\"",
            "stat_toughness": 10,
            "stat_save": "3+",
            "stat_wounds": 11,
            "stat_leadership": "7+",
            "stat_oc": 3,
            "stat_invuln": "6+",
            "stat_fnp": ""
        },
        "weapons": [
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
                "name": "Castigator autocannons",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "4",
                "skill": "3+",
                "strength": "9",
                "ap": "-1",
                "damage": "3",
                "keywords": "Twin-Linked, Rapid Fire 4"
            },
            {
                "name": "Castigator battle cannon",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "D6+3",
                "skill": "3+",
                "strength": "10",
                "ap": "-1",
                "damage": "3",
                "keywords": "Blast, Ignores Cover"
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
            }
        ],
        "abilities": [
            {
                "name": "Rites of Castigation",
                "description": "In your Shooting phase, after this model has shot, select one enemy unit hit by one or more of those attacks. Until the end of the turn, each time a friendly Adepta Sororitas unit makes a ranged attack that targets that enemy unit, improve the Armour Penetration characteristic of that attack by 1. The same enemy unit can only be affected by this ability once per turn."
            },
            {
                "name": "Damaged: 1-4 Wounds Remaining",
                "description": "While this model has 1-4 wounds remaining, each time this model makes an attack, subtract 1 from the Hit roll."
            }
        ]
    },
    "Celestian Insidiants": {
        "stats": {
            "stat_movement": "6\"",
            "stat_toughness": 3,
            "stat_save": "3+",
            "stat_wounds": 1,
            "stat_leadership": "7+",
            "stat_oc": 1,
            "stat_invuln": "5+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Null mace",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "3",
                "skill": "3+",
                "strength": "4",
                "ap": "-1",
                "damage": "1",
                "keywords": "Anti-PSYKER 4+, Devastating Wounds"
            },
            {
                "name": "Inferno pistol",
                "weapon_type": "ranged",
                "range": "6\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "8",
                "ap": "-4",
                "damage": "D3",
                "keywords": "Melta 2, Pistol"
            },
            {
                "name": "Condemnor bolt pistol",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Anti-PSYKER 4+, Devastating Wounds, Pistol"
            },
            {
                "name": "Ministorum hand flamer",
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
                "name": "Blessed sword",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "3",
                "skill": "3+",
                "strength": "4",
                "ap": "-2",
                "damage": "2",
                "keywords": "Lethal Hits"
            },
            {
                "name": "Virge of Admonition",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "3",
                "skill": "4+",
                "strength": "6",
                "ap": "-2",
                "damage": "3",
                "keywords": "Anti-PSYKER 4+, Devastating Wounds"
            }
        ],
        "abilities": [
            {
                "name": "Rituale Nullificatus",
                "description": "Models in this unit have the Feel No Pain 4+ ability against Psychic Attacks and mortal wounds."
            },
            {
                "name": "Virtue of Intolerance",
                "description": "At the start of the battle, select one unit from your opponent\u2019s army to be this unit\u2019s quarry. Each time a model in this unit makes an attack that targets its quarry, that attack has the [Precision] ability and you can re-roll the Hit roll. This ability can be used even if this unit is embarked within a Transport."
            },
            {
                "name": "Attached Unit",
                "description": "If a Character unit from your army can be attached to a Dominion Squad unit, it can be attached to this unit instead."
            },
            {
                "name": "Denuncia Oratory",
                "description": "Each time the bearer\u2019s unit\u2019s quarry is destroyed, you can select a new unit from your opponent\u2019s army to be its quarry."
            },
            {
                "name": "Simulacrum Imperialis",
                "description": "At the end of your Command phase, for each objective marker you control that has one or more units from your army with this ability within range of it, roll one D6: on a 4+, you gain 1 Miracle dice showing a value equal to that result."
            }
        ]
    },
    "Celestian Sacresants": {
        "stats": {
            "stat_movement": "6\"",
            "stat_toughness": 3,
            "stat_save": "3+",
            "stat_wounds": 1,
            "stat_leadership": "7+",
            "stat_oc": 1,
            "stat_invuln": "4+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Spear of the Faithful",
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
                "name": "Anointed Halberd",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "3",
                "skill": "3+",
                "strength": "5",
                "ap": "-2",
                "damage": "1",
                "keywords": "Sustained Hits 1"
            },
            {
                "name": "Hallowed Mace",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "3",
                "skill": "3+",
                "strength": "4",
                "ap": "-1",
                "damage": "2",
                "keywords": "Lethal Hits"
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
                "name": "Sworn Protectors",
                "description": "While an Adepta Sororitas Character is leading this unit, each time an attack targets this unit, subtract 1 from the Wound roll."
            },
            {
                "name": "Writ of Compunction",
                "description": "This unit has +1 OC."
            }
        ]
    },
    "Daemonifuge": {
        "stats": {
            "stat_movement": "8\"",
            "stat_toughness": 3,
            "stat_save": "3+",
            "stat_wounds": 5,
            "stat_leadership": "7+",
            "stat_oc": 1,
            "stat_invuln": "4+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Sanctity",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "2+",
                "strength": "6",
                "ap": "-2",
                "damage": "2",
                "keywords": "Anti-Chaos 2+, Precision"
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
            },
            {
                "name": "The Outcast's Blades",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "6",
                "skill": "2+",
                "strength": "4",
                "ap": "-2",
                "damage": "1",
                "keywords": "Precision"
            }
        ],
        "abilities": [
            {
                "name": "Holy Judgement",
                "description": "At the start of your Shooting phase, select one enemy unit within 12\" of and visible to this unit's Ephrael Stern model. That unit must take a Battle-shock test, subtracting 2 from the result if it is a Chaos unit. If the test is failed, that enemy unit suffers 3 mortal wounds."
            },
            {
                "name": "Mysterious Saviours",
                "description": "You can target this unit with the Heroic Intervention stratagem, regardless of any other uses of that stratagem this phase. If you do:\n- That use is -1 CP.\n- That use does not prevent any uses of that stratagem on other units this phase.'"
            }
        ]
    },
    "Dialogus": {
        "stats": {
            "stat_movement": "6\"",
            "stat_toughness": 3,
            "stat_save": "3+",
            "stat_wounds": 3,
            "stat_leadership": "6+",
            "stat_oc": 1,
            "stat_invuln": "4+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Dialogus staff",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "3",
                "skill": "4+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "-"
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
                "name": "Laud Hailer",
                "description": "Once per battle, at the start of any phase, you can select one friendly Adepta Sororitas unit that is Battle-shocked and within 12\" of this model. That unit is no longer Battle-shocked."
            },
            {
                "name": "Stirring Rhetoric",
                "description": "While this model is leading a unit, each time that unit performs an Act of Faith, the value of one of the Miracle dice used in that Act of Faith is first changed to a 6."
            },
            {
                "name": "Support",
                "description": "This model can be attached to the following units:\n\u25a0 Battle Sisters Squad\n\u25a0 Celestian Sacresants\n\u25a0 Dominion Squad\n\u25a0 Retributor Squad\n\u25a0 Sisters Novitiate Squad\nThis model can be attached to a Battle Sisters Squad, even if one Canoness, Palatine, Junith Eruita, or Aestred Thurga unit has already been attached to it. If you do, and that Bodyguard unit is destroyed, the Leader units attached to it become separate units, with their original Starting Strengths."
            }
        ]
    },
    "Dogmata": {
        "stats": {
            "stat_movement": "6\"",
            "stat_toughness": 3,
            "stat_save": "3+",
            "stat_wounds": 3,
            "stat_leadership": "6+",
            "stat_oc": 1,
            "stat_invuln": "6+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Mace of the Righteous",
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
                "name": "Executioner of Heretics (Aura)",
                "description": "While an enemy unit is within 6\" of this model, worsen the Leadership characteristic of models in that unit by 1."
            },
            {
                "name": "Unflinching Determination",
                "description": "While this model is leading a unit, add 1 to the Objective Control characteristic of models in that unit."
            },
            {
                "name": "Support",
                "description": "This model can be attached to the following units:\n\u25a0 Battle Sisters Squad\n\u25a0 Celestian Sacresants\n\u25a0 Dominion Squad\n\u25a0 Retributor Squad\nThis model can be attached to a Battle Sisters Squad, even if one Canoness, Palatine, Junith Eruita, or Aestred Thurga unit has already been attached to it. If you do, and that Bodyguard unit is destroyed, the Leader units attached to it become separate units, with their original Starting Strengths."
            }
        ]
    },
    "Dominion Squad": {
        "stats": {
            "stat_movement": "6\"",
            "stat_toughness": 3,
            "stat_save": "3+",
            "stat_wounds": 1,
            "stat_leadership": "7+",
            "stat_oc": 1,
            "stat_invuln": "6+",
            "stat_fnp": ""
        },
        "weapons": [
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
                "name": "Boltgun",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Rapid Fire 1"
            },
            {
                "name": "Artificer-crafted storm bolter",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "2",
                "skill": "3+",
                "strength": "4",
                "ap": "0",
                "damage": "2",
                "keywords": "Rapid Fire 2, Assault"
            },
            {
                "name": "Meltagun",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "9",
                "ap": "-4",
                "damage": "D6",
                "keywords": "Melta 2, Assault"
            },
            {
                "name": "Ministorum flamer",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "D6",
                "skill": "N/A",
                "strength": "5",
                "ap": "0",
                "damage": "1",
                "keywords": "Assault, Ignores Cover, Torrent"
            }
        ],
        "abilities": [
            {
                "name": "Holy Vanguard",
                "description": "If this unit has a Leader unit attached to it during the Declare Battle Formations step and this unit starts the battle embarked within a Transport, that Leader unit gains the Scouts 6\" ability."
            },
            {
                "name": "Righteous Awareness",
                "description": "In your opponent's Movement phase, if an enemy unit ends a move within 8\u201d of this unit, if this unit is not within Engagement Range of one or more enemy units it can make a Normal move of up to D6\u201d."
            },
            {
                "name": "Cherub",
                "description": "Once per battle, after this unit has performed an Act of Faith, you gain 1 Miracle dice."
            },
            {
                "name": "Simulacrum Imperialis",
                "description": "At the end of your Command phase, for each objective marker you control that has one or more units from your army with this ability within range of it, roll one D6: on a 4+, you gain 1 Miracle dice showing a value equal to that result."
            }
        ]
    },
    "Exorcist": {
        "stats": {
            "stat_movement": "10\"",
            "stat_toughness": 10,
            "stat_save": "3+",
            "stat_wounds": 11,
            "stat_leadership": "7+",
            "stat_oc": 3,
            "stat_invuln": "6+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Heavy Bolter",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "3",
                "skill": "3+",
                "strength": "5",
                "ap": "-1",
                "damage": "2",
                "keywords": "Sustained Hits 1"
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
                "name": "Exorcist Missile Launcher",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "D6+2",
                "skill": "3+",
                "strength": "10",
                "ap": "-3",
                "damage": "D6",
                "keywords": "Indirect Fire"
            },
            {
                "name": "Exorcist Conflagration Rockets",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "3D6",
                "skill": "3+",
                "strength": "6",
                "ap": "-1",
                "damage": "1",
                "keywords": "Blast, Ignores Cover, Indirect Fire"
            }
        ],
        "abilities": [
            {
                "name": "Damaged: 1-4 Wounds Remaining",
                "description": "While this model has 1-4 wounds remaining, each time this model makes an attack, subtract 1 from the Hit roll."
            },
            {
                "name": "Devastating Refrain",
                "description": "In your Shooting phase, after this model has shot, if one or more of those attacks made with an Indirect Fire weapon scored a hit against an enemy unit, that unit must take a Battle-shock test. Each time such an attack destroys an enemy model that has the Deadly Demise ability, the model's Deadly Demise ability inflicts mortal wounds on a D6 roll of 5+ instead of a 6."
            },
            {
                "name": "Symphonic Payload",
                "description": "This unit can re-roll rolls to determine the A of a weapon."
            }
        ]
    },
    "Hospitaller": {
        "stats": {
            "stat_movement": "6\"",
            "stat_toughness": 3,
            "stat_save": "3+",
            "stat_wounds": 3,
            "stat_leadership": "7+",
            "stat_oc": 1,
            "stat_invuln": "6+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Chirugeon's tools",
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
                "name": "Medicus Ministorum",
                "description": "While this model is leading a unit, models in that unit have the Feel No Pain 5+ ability."
            },
            {
                "name": "Sacred Healing",
                "description": "While this model is leading a unit, in your Command phase, you can return up to 1 destroyed model (excluding Character models) to that unit. If you wish, you first discard 1 Miracle dice; if you do, you can return up to D3+1 destroyed models (excluding Character models) to that unit instead."
            },
            {
                "name": "Support",
                "description": "This model can be attached to the following units:\n\u25a0 Battle Sisters Squad\n\u25a0 Celestian Sacresants\n\u25a0 Dominion Squad\n\u25a0 Retributor Squad\n\u25a0 Sisters Novitiate Squad\nThis model can be attached to a Battle Sisters Squad, even if one Canoness, Palatine, Junith Eruita, or Aestred Thurga unit has already been attached to it. If you do, and that Bodyguard unit is destroyed, the Leader units attached to it become separate units, with their original Starting Strengths."
            }
        ]
    },
    "Imagifier": {
        "stats": {
            "stat_movement": "6\"",
            "stat_toughness": 3,
            "stat_save": "3+",
            "stat_wounds": 3,
            "stat_leadership": "6+",
            "stat_oc": 1,
            "stat_invuln": "4+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Close combat weapon",
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
                "name": "Bolt pistol",
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
                "name": "Boltgun",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Rapid Fire 1"
            }
        ],
        "abilities": [
            {
                "name": "Litany of Deeds",
                "description": "Each time you gain a Miracle dice as the result of a friendly ADEPTA SORORITAS unit or model being destroyed, if that unit or model was destroyed within 12\" of this model, you can re-roll the result of that Miracle dice before adding it to your Miracle dice pool."
            },
            {
                "name": "Stanchion of Holy Martyrs",
                "description": "While this model is leading a unit, models in that unit have a Save characteristic of 2+ and a 4+ invulnerable save."
            },
            {
                "name": "Support",
                "description": "This model can be attached to the following units:\n\u25a0 Battle Sisters Squad\n\u25a0 Celestian Sacresants\n\u25a0 Dominion Squad\n\u25a0 Retributor Squad\nThis model can be attached to a Battle Sisters Squad, even if one Canoness, Palatine, Junith Eruita, or Aestred Thurga unit has already been attached to it. If you do, and that Bodyguard unit is destroyed, the Leader units attached to it become separate units, with their original Starting Strengths."
            }
        ]
    },
    "Immolator": {
        "stats": {
            "stat_movement": "12\"",
            "stat_toughness": 10,
            "stat_save": "3+",
            "stat_wounds": 11,
            "stat_leadership": "7+",
            "stat_oc": 2,
            "stat_invuln": "6+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Heavy Bolter",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "3",
                "skill": "3+",
                "strength": "5",
                "ap": "-1",
                "damage": "2",
                "keywords": "Sustained Hits 1"
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
                "name": "Immolation Flamers",
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
                "name": "Twin Heavy Bolter",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "3",
                "skill": "3+",
                "strength": "5",
                "ap": "-1",
                "damage": "2",
                "keywords": "Sustained Hits 2, Twin-Linked"
            },
            {
                "name": "Twin Multi-melta",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "2",
                "skill": "3+",
                "strength": "9",
                "ap": "-4",
                "damage": "D6",
                "keywords": "Melta 2, Twin-Linked"
            }
        ],
        "abilities": [
            {
                "name": "Transport",
                "description": "This model has a transport capacity of 6 ADEPTA SORORITAS INFANTRY models. It cannot transport JUMP PACK models or the Triumph of Saint Katherine.\n\nAt the start of the Declare Battle Formations step, you can select one BATTLE SISTERS SQUAD, DOMINION SQUAD or SISTERS NOVITIATE SQUAD from your army. If you do, that unit is split into two units, each containing as equal a number of models as possible (when splitting a unit in this way, make a note of which models form each of the two new units. If you are splitting a unit that has the Cherub ability, only one of the new units can use that ability during the battle \u2013 make a note of which of the new units this will be). One of these units must start the battle embarked within this TRANSPORT; the other can start the battle embarked within another TRANSPORT, or it can be deployed as a separate unit."
            },
            {
                "name": "Purge and Cleanse",
                "description": "In your Shooting phase, after this model has shot, select one enemy unit hit by one or more of those attacks. Until the end of the phase, that enemy unit cannot have the Benefit of Cover."
            }
        ]
    },
    "Intranzia Fraye": {
        "stats": {
            "stat_movement": "8\"",
            "stat_toughness": 7,
            "stat_save": "3+",
            "stat_wounds": 8,
            "stat_leadership": "6+",
            "stat_oc": 3,
            "stat_invuln": "4+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Heavy bolter",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "3",
                "skill": "2+",
                "strength": "5",
                "ap": "-1",
                "damage": "2",
                "keywords": "Sustained Hits 1"
            },
            {
                "name": "Melta missile array",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "2",
                "skill": "2+",
                "strength": "9",
                "ap": "-2",
                "damage": "D3",
                "keywords": "Melta 2"
            },
            {
                "name": "Mace of Saint Praxedes",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "2+",
                "strength": "6",
                "ap": "-2",
                "damage": "2",
                "keywords": "Sustained Hits 1"
            },
            {
                "name": "Throne of Blame",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "4+",
                "strength": "6",
                "ap": "0",
                "damage": "1",
                "keywords": "Extra Attacks"
            },
            {
                "name": "Ministorum heavy flamer",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "D6",
                "skill": "N/A",
                "strength": "6",
                "ap": "-1",
                "damage": "1",
                "keywords": "Ignores Cover, Torrent"
            }
        ],
        "abilities": [
            {
                "name": "Righteous Denunciation",
                "description": "At the start of the Fight phase, each enemy unit within 6\" of this model must take a Battle-shock test, subtracting 1 from that test."
            },
            {
                "name": "Judged for Execution",
                "description": "At the end of your Movement phase, you can select one enemy unit within 18\" of and visible to this model. Until the start of your next Command phase, each time a friendly Adepta Sororitas model makes an attack that targets that enemy unit, that attack has the [LETHAL HITS] ability."
            }
        ]
    },
    "Junith Eruita": {
        "stats": {
            "stat_movement": "8\"",
            "stat_toughness": 5,
            "stat_save": "2+",
            "stat_wounds": 8,
            "stat_leadership": "6+",
            "stat_oc": 2,
            "stat_invuln": "4+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Twin Ministorum Heavy Flamer",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "D6",
                "skill": "N/A",
                "strength": "6",
                "ap": "-1",
                "damage": "1",
                "keywords": "Ignores Cover, Torrent, Twin-Linked"
            },
            {
                "name": "Mace of Castigation",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "2+",
                "strength": "6",
                "ap": "-2",
                "damage": "2",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "The Pulpit of Saint Holline\u2019s Basilica",
                "description": "- This unit has Stealth.\n- Melee attacks that target this unit have -1 to hit rolls."
            },
            {
                "name": "Fiery Conviction",
                "description": "If this model is on the battlefield at the start\nof your Command phase, you can choose one of the following:\n\u25a0 Discard 1 Miracle dice and gain 1CP.\n\u25a0 Take a Leadership test for this model, if that test is passed, gain 1CP."
            }
        ]
    },
    "Ministorum Priest": {
        "stats": {
            "stat_movement": "6\"",
            "stat_toughness": 3,
            "stat_save": "6+",
            "stat_wounds": 3,
            "stat_leadership": "7+",
            "stat_oc": 1,
            "stat_invuln": "4+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Holy Pistol",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "3",
                "skill": "4+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Pistol"
            },
            {
                "name": "Power weapon",
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
                "name": "Zealot's vindictor",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "D6",
                "skill": "N/A",
                "strength": "5",
                "ap": "0",
                "damage": "1",
                "keywords": "Ignores Cover, Torrent"
            },
            {
                "name": "Zealot's vindictor",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "3",
                "skill": "4+",
                "strength": "5",
                "ap": "-1",
                "damage": "2",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Righteous Smiting",
                "description": "While this model is leading a unit, each time a model in that unit makes a melee attack, add 1 to the Wound roll."
            },
            {
                "name": "Zealot",
                "description": "Once per battle, in the Fight phase, this model can use this ability. If it does, until the end of the phase, improve the Strength and Attacks characteristics of melee weapons equipped by this model by 3."
            },
            {
                "name": "Holy Mission",
                "description": "If this model is attached to a Dominion Squad during the Declare Battle Formations step, it gains the Scouts 6\" ability. If this model is attached to a Sisters Novitiate Squad during the Declare Battle Formations step, it gains the Infiltrators ability."
            }
        ]
    },
    "Mortifiers": {
        "stats": {
            "stat_movement": "8\"",
            "stat_toughness": 6,
            "stat_save": "4+",
            "stat_wounds": 5,
            "stat_leadership": "7+",
            "stat_oc": 2,
            "stat_invuln": "6+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Twin Penitent Buzz-Blades",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "3+",
                "strength": "10",
                "ap": "-3",
                "damage": "2",
                "keywords": "Sustained Hits 1,Twin-Linked"
            },
            {
                "name": "Twin Penitent Flails",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "8",
                "skill": "3+",
                "strength": "5",
                "ap": "-1",
                "damage": "1",
                "keywords": "Sustained Hits 1, Twin-Linked"
            },
            {
                "name": "Penitent Buzz-Blade",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "3+",
                "strength": "10",
                "ap": "-3",
                "damage": "2",
                "keywords": "Sustained Hits 1"
            },
            {
                "name": "Penitent Flail",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "8",
                "skill": "3+",
                "strength": "5",
                "ap": "-1",
                "damage": "1",
                "keywords": "Sustained Hits 1"
            },
            {
                "name": "Heavy Bolter",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "3",
                "skill": "3+",
                "strength": "5",
                "ap": "-1",
                "damage": "2",
                "keywords": "Sustained Hits 1"
            },
            {
                "name": "Mortifier flamer",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "D6",
                "skill": "n/a",
                "strength": "5",
                "ap": "0",
                "damage": "1",
                "keywords": "Ignores Cover, Torrent, Twin-Linked"
            }
        ],
        "abilities": [
            {
                "name": "Anguish of the Unredeemed",
                "description": "Each time a model in this unit is destroyed by a melee attack, if that model has not fought this phase, roll one D6. On a 2+, do not remove it from play; that destroyed model can fight after attacking unit has finished making its attacks, and is then removed from play."
            },
            {
                "name": "Anchorite Sarcophagus",
                "description": "The bearer has a Move characteristic of 7\" and a Save Characteristic of 3+."
            }
        ]
    },
    "Morvenn Vahl": {
        "stats": {
            "stat_movement": "8\"",
            "stat_toughness": 7,
            "stat_save": "2+",
            "stat_wounds": 8,
            "stat_leadership": "6+",
            "stat_oc": 3,
            "stat_invuln": "4+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "\u27a4 Lance of Illumination - strike",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "5",
                "skill": "2+",
                "strength": "8",
                "ap": "-2",
                "damage": "3",
                "keywords": "Devastating Wounds"
            },
            {
                "name": "\u27a4 Lance of Illumination - sweep",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "10",
                "skill": "2+",
                "strength": "5",
                "ap": "-1",
                "damage": "1",
                "keywords": "Devastating Wounds"
            },
            {
                "name": "Fidelis",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "3",
                "skill": "2+",
                "strength": "6",
                "ap": "-1",
                "damage": "2",
                "keywords": "Sustained Hits 1"
            },
            {
                "name": "\u27a4 Paragon missile launcher - prioris",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "2",
                "skill": "2+",
                "strength": "9",
                "ap": "-2",
                "damage": "D6",
                "keywords": "-"
            },
            {
                "name": "\u27a4 Paragon missile launcher - sanctorum",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "2D6",
                "skill": "2+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Blast"
            }
        ],
        "abilities": [
            {
                "name": "Abbess Sanctorum",
                "description": "While this model is leading a unit, each time a model in that unit makes an attack, you can re-roll the Hit roll and you can re-roll the Wound roll."
            },
            {
                "name": "Righteous Repugnance",
                "description": "Each time this model's unit is selected to shoot or fight, you can discard 1 Miracle dice. If you do, until the end of the phase, add 3 to the Attacks characteristic of Fidelis and the Lance of Illumination. Each time an enemy unit is destroyed by this model, you gain 1 Miracle dice."
            }
        ]
    },
    "Palatine": {
        "stats": {
            "stat_movement": "6\"",
            "stat_toughness": 3,
            "stat_save": "3+",
            "stat_wounds": 4,
            "stat_leadership": "7+",
            "stat_oc": 1,
            "stat_invuln": "4+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Palatine blade",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "2+",
                "strength": "4",
                "ap": "-2",
                "damage": "2",
                "keywords": "-"
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
            },
            {
                "name": "\u27a4 Plasma pistol - supercharge",
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
                "name": "\u27a4 Plasma pistol - standard",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "1",
                "skill": "2+",
                "strength": "7",
                "ap": "-2",
                "damage": "1",
                "keywords": "Pistol"
            }
        ],
        "abilities": [
            {
                "name": "Fury of the Righteous",
                "description": "While this model is leading a unit, weapons equipped by models in that unit have the [LETHAL HITS] ability."
            },
            {
                "name": "Rapturous Blows",
                "description": "Each time this model\u2019s unit is selected to fight, you can discard 1 Miracle dice. If you do, then until the end of the phase, each time a melee attack made by this model scores a wound, the target of that attack suffers 1 mortal wound in addition to any normal damage."
            }
        ]
    },
    "Paragon Warsuits": {
        "stats": {
            "stat_movement": "8\"",
            "stat_toughness": 7,
            "stat_save": "2+",
            "stat_wounds": 4,
            "stat_leadership": "7+",
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
                "skill": "3+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Pistol"
            },
            {
                "name": "Paragon Storm Bolters",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "2",
                "skill": "3+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Rapid Fire 2, Twin-Linked"
            },
            {
                "name": "Paragon Grenade Launchers",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "9",
                "ap": "-2",
                "damage": "D3",
                "keywords": "Twin-Linked"
            },
            {
                "name": "Paragon War Blade",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "3+",
                "strength": "8",
                "ap": "-2",
                "damage": "2",
                "keywords": "-"
            },
            {
                "name": "Paragon War Mace",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "3",
                "skill": "3+",
                "strength": "12",
                "ap": "-1",
                "damage": "3",
                "keywords": "-"
            },
            {
                "name": "Heavy Bolter",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "3",
                "skill": "3+",
                "strength": "5",
                "ap": "-1",
                "damage": "2",
                "keywords": "Sustained Hits 1"
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
                "name": "Ministorum heavy flamer",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "D6",
                "skill": "N/A",
                "strength": "6",
                "ap": "-1",
                "damage": "1",
                "keywords": "Ignores Cover, Torrent"
            }
        ],
        "abilities": [
            {
                "name": "Righteous Paragons",
                "description": "Each time a model in this unit makes an attack that targets a MONSTER or VEHICLE unit, add 1 to the Hit roll and add 1 to the Wound roll."
            }
        ]
    },
    "Penitent Engines": {
        "stats": {
            "stat_movement": "8\"",
            "stat_toughness": 6,
            "stat_save": "4+",
            "stat_wounds": 5,
            "stat_leadership": "7+",
            "stat_oc": 2,
            "stat_invuln": "6+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Penitent Flamers",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "2D6",
                "skill": "N/A",
                "strength": "5",
                "ap": "0",
                "damage": "1",
                "keywords": "Assault, Ignores Cover, Torrent, Twin-Linked"
            },
            {
                "name": "Twin Penitent Buzz-Blades",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "4+",
                "strength": "10",
                "ap": "-3",
                "damage": "2",
                "keywords": "Sustained Hits 1, Twin-Linked"
            },
            {
                "name": "Twin Penitent Flails",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "8",
                "skill": "4+",
                "strength": "5",
                "ap": "-1",
                "damage": "1",
                "keywords": "Sustained Hits 1, Twin-Linked"
            },
            {
                "name": "Penitent Buzz-Blade",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "4+",
                "strength": "10",
                "ap": "-3",
                "damage": "2",
                "keywords": "Sustained Hits 1"
            },
            {
                "name": "Penitent Flail",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "8",
                "skill": "4+",
                "strength": "5",
                "ap": "-1",
                "damage": "1",
                "keywords": "Sustained Hits 1"
            }
        ],
        "abilities": [
            {
                "name": "Endless Suffering",
                "description": "This unit is eligible to declare a charge in a turn in which it Advanced"
            }
        ]
    },
    "Repentia Squad": {
        "stats": {
            "stat_movement": "7\"",
            "stat_toughness": 3,
            "stat_save": "7+",
            "stat_wounds": 1,
            "stat_leadership": "8+",
            "stat_oc": 1,
            "stat_invuln": "6+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Penitent Eviscerator",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "2",
                "skill": "4+",
                "strength": "6",
                "ap": "-2",
                "damage": "2",
                "keywords": "Sustained Hits 1"
            },
            {
                "name": "Neural Whips",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "3+",
                "strength": "3",
                "ap": "-1",
                "damage": "1",
                "keywords": "Anti-Infantry 4+"
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
                "name": "Overseer of Redemption",
                "description": "While this unit contains a Repentia Superior model, each time a Sisters Repentia model in this unit makes a melee attack, you can re-roll the Hit roll and you can re-roll the Wound roll."
            }
        ]
    },
    "Retributor Squad": {
        "stats": {
            "stat_movement": "6\"",
            "stat_toughness": 3,
            "stat_save": "3+",
            "stat_wounds": 1,
            "stat_leadership": "7+",
            "stat_oc": 1,
            "stat_invuln": "6+",
            "stat_fnp": ""
        },
        "weapons": [
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
                "name": "Bolt pistol",
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
                "name": "Ministorum heavy flamer",
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
                "name": "Multi-melta",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "2",
                "skill": "4+",
                "strength": "9",
                "ap": "-4",
                "damage": "D6",
                "keywords": "Heavy, Melta 2"
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
                "keywords": "Heavy, Sustained Hits 1"
            }
        ],
        "abilities": [
            {
                "name": "Cherubs",
                "description": "Twice per battle, after this unit has performed an Act of Faith, you gain 1 Miracle dice."
            },
            {
                "name": "Storm of Retribution",
                "description": "Each time a model in this unit makes a ranged attack, re-roll a Hit roll of 1 and re-roll a Wound roll of 1. If such an attack targets an enemy unit that has destroyed one or more Adepta Sororitas units from your army during the battle, add 1 to the Hit roll and add 1 to the Wound roll as well."
            }
        ]
    },
    "Saint Celestine": {
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
                "name": "The Ardent Blade",
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
                "name": "The Ardent Blade",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "5",
                "skill": "2+",
                "strength": "6",
                "ap": "-3",
                "damage": "2",
                "keywords": "Devastating Wounds"
            },
            {
                "name": "Power Weapon",
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
                "name": "Bolt Pistol",
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
                "name": "Healing Tears",
                "description": "While this unit contains a Celestine model, in your Command phase, if this unit is below its Starting Strength, either one destroyed Geminae Superia model or up to D3 other Bodyguard models are returned to this unit."
            },
            {
                "name": "Lifewards",
                "description": "While this unit contains one or more Geminae Superia models, Celestine has the Feel No Pain 4+ ability."
            },
            {
                "name": "Miraculous Intervention",
                "description": "The first time this unit\u2019s Celestine model is destroyed, roll one D6 at the end of the phase. On a 2+, set that Celestine model back up on the battlefield, as close as possible to where it was destroyed and not within Engagement Range of any enemy units, with its full wounds remaining."
            }
        ]
    },
    "Sanctifiers": {
        "stats": {
            "stat_movement": "6\"",
            "stat_toughness": 3,
            "stat_save": "6+",
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
                "name": "Ministorum hand flamer",
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
                "name": "Holy fire",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "D6",
                "skill": "N/A",
                "strength": "6",
                "ap": "-1",
                "damage": "2",
                "keywords": "Ignores Cover, One Shot, Torrent"
            },
            {
                "name": "Sanctifier melee weapon",
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
                "name": "\u27a4 Plasma gun - standard",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "7",
                "ap": "-2",
                "damage": "1",
                "keywords": "Rapid Fire 1"
            },
            {
                "name": "\u27a4 Plasma gun - supercharge",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "8",
                "ap": "-3",
                "damage": "2",
                "keywords": "Hazardous, Rapid Fire 1"
            },
            {
                "name": "Meltagun",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "1",
                "skill": "4+",
                "strength": "9",
                "ap": "-4",
                "damage": "D6",
                "keywords": "Melta 2"
            },
            {
                "name": "Burning hands",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "1",
                "skill": "2+",
                "strength": "6",
                "ap": "-2",
                "damage": "3",
                "keywords": "Devastating Wounds"
            },
            {
                "name": "Death Cult blades",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "2+",
                "strength": "4",
                "ap": "-2",
                "damage": "1",
                "keywords": "Precision"
            }
        ],
        "abilities": [
            {
                "name": "Ministorum Sermon",
                "description": "While this unit contains a Ministorum Priest, melee weapons equipped by models in this unit have the [SUSTAINED HITS 1] ability."
            },
            {
                "name": "Cherub",
                "description": "Once per battle, after this unit has performed an Act of Faith, you gain 1 Miracle dice."
            },
            {
                "name": "Attached Unit",
                "description": "If a Ministorum Priest model from your army with the Leader ability can be attached to a Battle Sisters Squad, it can be attached to this unit instead. If a Ministorum Priest model from your army is attached to this unit during the Declare Battle Formations step, that model gains the Scouts 6\" ability."
            },
            {
                "name": "Simulacrum Imperialis",
                "description": "At the end of your Command phase, for each objective marker you control that has one or more units from your army with this ability within range of it, roll one D6: on a 4+, you gain 1 Miracle dice showing a value equal to that result."
            },
            {
                "name": "Salvationist Medikit",
                "description": "In your Command phase, if the bearer is on the battlefield, you can return up to D3 destroyed models (excluding Character models) to this unit."
            }
        ]
    },
    "Seraphim Squad": {
        "stats": {
            "stat_movement": "12\"",
            "stat_toughness": 3,
            "stat_save": "3+",
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
                "name": "Bolt pistol",
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
            },
            {
                "name": "Power Weapon",
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
                "name": "Chainsword",
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
                "name": "Ministorum hand flamer",
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
                "name": "Inferno Pistol",
                "weapon_type": "ranged",
                "range": "6\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "8",
                "ap": "-4",
                "damage": "D3",
                "keywords": "Melta 2, Pistol"
            }
        ],
        "abilities": [
            {
                "name": "Angelic Ascent",
                "description": "In your Shooting phase, after this unit has shot, if it is not within Engagement Range of any enemy units, it can make a Normal move of up to 6\". If it does, until the end of the turn, this unit is not eligible to declare a charge."
            },
            {
                "name": "Condemnatory Psalms",
                "description": "In your Shooting phase, this unit can select one visible enemy unit within 12\". That enemy unit is condemned:\n- While a unit is condemned, that unit has +3\" detection range."
            }
        ]
    },
    "Sisters Novitiate Squad": {
        "stats": {
            "stat_movement": "6\"",
            "stat_toughness": 3,
            "stat_save": "3+",
            "stat_wounds": 1,
            "stat_leadership": "7+",
            "stat_oc": 2,
            "stat_invuln": "6+",
            "stat_fnp": ""
        },
        "weapons": [
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
            },
            {
                "name": "Boltgun",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Rapid Fire 1"
            },
            {
                "name": "Power weapon",
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
                "name": "Novitiate autopistol",
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
                "name": "Ministorum flamer",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "D6",
                "skill": "N/A",
                "strength": "5",
                "ap": "0",
                "damage": "1",
                "keywords": "Ignores Cover, Torrent"
            },
            {
                "name": "Novitiate autogun",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "3",
                "ap": "0",
                "damage": "1",
                "keywords": "Rapid Fire 1"
            },
            {
                "name": "Novitiate melee weapon",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "2",
                "skill": "4+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Impetuous Fervour",
                "description": "Impetuous Fervour: Each time a model in this unit makes an attack, re-roll a Hit roll of 1. If the target of that attack is an enemy unit within range of an objective marker, you can re-roll the Hit roll instead."
            },
            {
                "name": "Sacred Banner",
                "description": "You can re-roll Advance and Charge rolls made for the bearer\u2019s unit."
            },
            {
                "name": "Simulacrum Imperialis",
                "description": "At the end of your Command phase, for each objective marker you control that has one or more units from your army with this ability within range of it, roll one D6: on a 4+, you gain 1 Miracle dice showing a value equal to that result."
            }
        ]
    },
    "Sororitas Rhino": {
        "stats": {
            "stat_movement": "12\"",
            "stat_toughness": 9,
            "stat_save": "3+",
            "stat_wounds": 10,
            "stat_leadership": "7+",
            "stat_oc": 2,
            "stat_invuln": "6+",
            "stat_fnp": ""
        },
        "weapons": [
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
                "name": "Transport",
                "description": "This model has a transport capacity of 12 ADEPTA SORORITAS INFANTRY models. It cannot transport JUMP PACK models or the TRIUMPH OF SAINT KATHERINE."
            },
            {
                "name": "Self Repair",
                "description": "At the start of your Command phase, this model regains 1 lost wound."
            }
        ]
    },
    "Triumph of Saint Katherine": {
        "stats": {
            "stat_movement": "6\"",
            "stat_toughness": 3,
            "stat_save": "3+",
            "stat_wounds": 18,
            "stat_leadership": "6+",
            "stat_oc": 6,
            "stat_invuln": "4+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Bolt Pistols",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "6",
                "skill": "2+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Pistol"
            },
            {
                "name": "Relic Weapons",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "18",
                "skill": "2+",
                "strength": "5",
                "ap": "-2",
                "damage": "1",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Damaged: 1-6 Wounds Remaining",
                "description": "While this model has 1-6 wounds remaining, the Attacks characteristics of all of its weapons are halved, and you can only select one ability when using its Relics of the Matriarchs ability, instead of up to two."
            },
            {
                "name": "Relics of the Matriarchs",
                "description": "At the start of the battle round, select up to two of the abilities in the Relics of the Matriarchs section. Until the start of the next battle round, this model has those abilities."
            },
            {
                "name": "Relic of the Matriarch - The Fiery Heart (Aura)",
                "description": "While a friendly Adepta Sororitas unit is within 6\" of this model, add 2\" to that unit's Move characteristic and add 1 to the Advance and Charge rolls made for that unit."
            },
            {
                "name": "Relic of the Matriarch - Censer of the Sacred Rose (Aura)",
                "description": "While a friendly Adepta Sororitas unit is within 6\" of this model, you can re-roll all Battle-shock tests taken for that unit."
            },
            {
                "name": "Relic of the Matriarch - Simulacrum of the Ebon Chalice (Aura)",
                "description": "While a friendly Adepta Sororitas unit is within 6\" of this model, that unit can perform up to two Acts of Faith per phase, instead of only one."
            },
            {
                "name": "Relic of the Matriarch - Simulacrum of the Argent Shroud (Aura)",
                "description": "While a friendly Adepta Sororitas unit is within 6\" of this model, each time a model in that unit makes a ranged attack, re-roll a Wound roll of 1."
            },
            {
                "name": "Relic of the Matriarch - Icon of the Valorous Heart (Aura)",
                "description": "While a friendly Adepta Sororitas unit is within 6\" of this model, models in that unit have the Feel No Pain 6+ ability."
            },
            {
                "name": "Relic of the Matriarch - Petals of the Bloody Rose (Aura)",
                "description": "While a friendly Adepta Sororitas unit is within 6\" of this model, improve the Armour Penetration characteristic of melee weapons equipped by model in that unit by 1."
            },
            {
                "name": "Solemn Procession",
                "description": "Each time you gain 1 Miracle dice at the start of the battle round, if this model is on the battlefield, do not roll one D6 to determine the value of that Miracle dice; it has a value of 6.\u2019"
            }
        ]
    },
    "Zephyrim Squad": {
        "stats": {
            "stat_movement": "12\"",
            "stat_toughness": 3,
            "stat_save": "3+",
            "stat_wounds": 1,
            "stat_leadership": "7+",
            "stat_oc": 1,
            "stat_invuln": "5+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Power weapon",
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
                "name": "Bolt pistol",
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
                "name": "Embodied Prophecy",
                "description": "Each time this unit is selected to fight, select one of the following abilities to apply to melee weapons equipped by models in this unit until the end of the phase:\n- Sustained Hits 1\n- Lethal Hits\n\nIf this unit made a Charge move this turn, until the end of the phase, select both abilities above to apply to melee weapons equipped by models in this unit instead."
            },
            {
                "name": "Condemnatory Psalms",
                "description": "In your Shooting phase, this unit can select one visible enemy unit within 12\". That enemy unit is condemned:\n- While a unit is condemned, that unit has +3\" detection range."
            },
            {
                "name": "Sacred Banner",
                "description": "You can re-roll Advance and Charge rolls made for the bearer\u2019s unit."
            }
        ]
    }
}


class Command(BaseCommand):
    """Refresh Sisters of Battle stat lines, weapon profiles, and abilities from BSData."""

    help = 'Refresh 11th Edition stats/weapons/abilities for Sisters of Battle units.'

    def add_arguments(self, parser):
        """Add --dry-run flag."""
        parser.add_argument(
            '--dry-run', action='store_true',
            help='Preview changes without writing to the database.',
        )

    def handle(self, *args, **options):
        """Iterate SISTERS_OF_BATTLE_DATASHEETS and refresh each unit's datasheet data."""
        dry_run = options['dry_run']
        updated = 0
        skipped = 0

        with transaction.atomic():
            for name, payload in SISTERS_OF_BATTLE_DATASHEETS.items():
                try:
                    unit = UnitType.objects.get(name=name, faction__name='Sisters of Battle')
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
