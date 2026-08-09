"""
Management command: seed_leagues_of_votann_datasheets

Refreshes stat lines, weapon profiles, and abilities for Leagues of
Votann units using 11th Edition data sourced from BSData/wh40k-11e
("Leagues of Votann.json") -- the same source used by
seed_leagues_of_votann_points.py. Supersedes the older hand-authored
seed_votann_stats.py -- left in place, not deleted.

Usage:
    python manage.py seed_leagues_of_votann_datasheets
    python manage.py seed_leagues_of_votann_datasheets --dry-run

Notes:
- Does NOT touch points_cost or category -- those are handled entirely by
  seed_leagues_of_votann_points.py. This command only refreshes stat_*
  fields, WeaponProfile rows, and UnitAbility rows.
- Includes 'Kapricus Defenders' -- BSData has no costs value for this
  unit (points is user-supplied, see the points command's docstring),
  but its stats/weapons/abilities ARE fully defined in BSData and were
  extracted normally, then cross-checked against an in-game army-builder
  screenshot for accuracy (2026-08-07).
- Per-field safety rule: a unit's stats/weapons/abilities are only
  overwritten when BSData actually has that data for it. If extraction
  found nothing, the existing DB value/rows are left untouched.
- All 22 active units resolved cleanly -- 0 missing stats/weapons/
  abilities, 0 overlong stat fields.
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from calculators.models import UnitAbility, UnitType, WeaponProfile

# (name -> {stats?, weapons?, abilities?}). Missing keys mean "no data
# found for this field -- leave existing DB data untouched."
LEAGUES_OF_VOTANN_DATASHEETS = {
    "Arkanyst Evaluator": {
        "stats": {
            "stat_movement": "5\"",
            "stat_toughness": 5,
            "stat_save": "3+",
            "stat_wounds": 4,
            "stat_leadership": "7+",
            "stat_oc": 1,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "➤ Transmatter inverter - half charge",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "3",
                "skill": "2+",
                "strength": "8",
                "ap": "-1",
                "damage": "1",
                "keywords": "Rapid Fire 1"
            },
            {
                "name": "➤ Transmatter inverter - full charge",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "3",
                "skill": "2+",
                "strength": "8",
                "ap": "-2",
                "damage": "2",
                "keywords": "Hazardous, Rapid Fire 2"
            },
            {
                "name": "➤ Transmatter inverter - overcharge",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "3",
                "skill": "2+",
                "strength": "8",
                "ap": "-3",
                "damage": "3",
                "keywords": "Hazardous, Overcharge, Rapid Fire 3"
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
            }
        ],
        "abilities": [
            {
                "name": "Science Guild Support",
                "description": "While this model is within 3\" of one or more other friendly Leagues of Votann Infantry units (excluding units with the Lone Operative ability), this model has the Lone Operative ability."
            },
            {
                "name": "Resource Transmutation",
                "description": "Once per turn, in your Shooting phase, one model with this ability can choose to use it when it is selected to shoot. If it does, you must spend 1YP and, until the end of the phase, ranged weapons equipped by that model have the [Sustained Hits 1] ability and, after that model has shot this phase, if one or more enemy units were destroyed by those attacks, you can gain up to 2YP."
            },
            {
                "name": "Guerrilla Adepts",
                "description": "In your Shooting phase, just after this unit is selected to shoot, this unit can use this ability. If it does, select one enemy unit (excluding Monsters and Vehicles). Until the end of the phase, attacks made by models in this unit can only attack that enemy unit (and only if it is an eligible target) and, after resolving those attacks, if one or more of those attacks hit that enemy unit, until the start of your next Shooting phase, that enemy unit is assailed (this simply labels that unit for the purposes of this ability and some Enhancements or Stratagems). If that unit is already assailed, until the start of your next Shooting phase, it is also pinned. While a unit is pinned, subtract 2\" from its Move characteristic and subtract 2 from Charge rolls made for it."
            }
        ]
    },
    "Berehk Stornbrow": {
        "stats": {
            "stat_movement": "6\"",
            "stat_toughness": 6,
            "stat_save": "5+",
            "stat_wounds": 5,
            "stat_leadership": "7+",
            "stat_oc": 1,
            "stat_invuln": "5+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "➤ Kromlôk's Revenge - graviton strikes",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "2+",
                "strength": "10",
                "ap": "-2",
                "damage": "4",
                "keywords": "Anti-Monster 3+, Anti-Vehicle 3+, Sustained Hits 1"
            },
            {
                "name": "➤ Kromlôk's Revenge - plasma sweeps",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "8",
                "skill": "2+",
                "strength": "7",
                "ap": "-2",
                "damage": "2",
                "keywords": "Sustained Hits 1"
            },
            {
                "name": "Warforge gauntlets",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "2",
                "skill": "2+",
                "strength": "6",
                "ap": "-2",
                "damage": "1",
                "keywords": "Extra Attacks, Sustained Hits 1"
            }
        ],
        "abilities": [
            {
                "name": "Break the Foe",
                "description": "Melee weapons equipped by models in this unit have the [Sustained Hits 1] ability."
            },
            {
                "name": "Relentless Avalanche",
                "description": "You can target this model's unit with the Heroic Intervention Stratagem for 0CP, and can do so even if you have already targeted a different unit with that Stratagem this phase."
            },
            {
                "name": "Leader",
                "description": "This model can be attached to the following units: Cthonian Beserks"
            }
        ]
    },
    "Brokhyr Iron-master": {
        "stats": {
            "stat_movement": "5\"",
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
                "name": "Graviton hammer",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "3",
                "skill": "4+",
                "strength": "9",
                "ap": "-1",
                "damage": "3",
                "keywords": "Anti-MONSTER 3+, Anti-VEHICLE 3+"
            },
            {
                "name": "Graviton rifle",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "3",
                "skill": "3+",
                "strength": "5",
                "ap": "-1",
                "damage": "3",
                "keywords": "Anti-MONSTER 3+, Anti-VEHICLE 3+"
            },
            {
                "name": "Autoch-pattern bolt pistol",
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
                "name": "Plasma torch",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "1",
                "skill": "4+",
                "strength": "6",
                "ap": "-3",
                "damage": "2",
                "keywords": "-"
            },
            {
                "name": "Manipulator arms",
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
                "name": "Las-beam cutter",
                "weapon_type": "ranged",
                "range": "6\"",
                "attacks": "1",
                "skill": "4+",
                "strength": "6",
                "ap": "-3",
                "damage": "1",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Multi-spectral visor",
                "description": "Each time a model in this unit makes a ranged attack, re-roll a Wound roll of 1."
            },
            {
                "name": "Brôkhyr Guild Support",
                "description": "While this unit is within 3\" of one or more friendly Leagues of Votann Vehicle or Ironkin Steeljacks units, if this unit is not an attached unit, it has the Lone Operative ability."
            },
            {
                "name": "Leader",
                "description": "This model can be attached to the following unit:\n- HEARTHKYN WARRIORS\n- BRÔKHYR THUNDERKYN"
            },
            {
                "name": "Unit Composition",
                "description": "If this unit’s Brôkhyr Iron-master model is ever destroyed, all of this unit’s remaining E-COG models are also destroyed. While embarking within a Transport and while embarked within a Transport, each E-COG model takes up the space of 0 models."
            },
            {
                "name": "Forgewrought Expertise",
                "description": "At the end of your Movement phase, this model can repair one friendly Leagues of Votann Vehicle, Exoframe or Ironkin Steeljacks unit within 3\" of it. One model in that unit regains up to D3 lost wounds, or up to 3 lost wounds if this unit contains an Ironkin Assistant model. Each unit can only be repaired once per turn."
            },
            {
                "name": "Guerrilla Adepts",
                "description": "In your Shooting phase, just after this unit is selected to shoot, this unit can use this ability. If it does, select one enemy unit (excluding Monsters and Vehicles). Until the end of the phase, attacks made by models in this unit can only attack that enemy unit (and only if it is an eligible target) and, after resolving those attacks, if one or more of those attacks hit that enemy unit, until the start of your next Shooting phase, that enemy unit is assailed (this simply labels that unit for the purposes of this ability and some Enhancements or Stratagems). If that unit is already assailed, until the start of your next Shooting phase, it is also pinned. While a unit is pinned, subtract 2\" from its Move characteristic and subtract 2 from Charge rolls made for it."
            }
        ]
    },
    "Brokhyr Thunderkyn": {
        "stats": {
            "stat_movement": "5\"",
            "stat_toughness": 6,
            "stat_save": "3+",
            "stat_wounds": 2,
            "stat_leadership": "7+",
            "stat_oc": 1,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Close combat weapon",
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
                "name": "Bolt cannon",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "3",
                "skill": "4+",
                "strength": "6",
                "ap": "-1",
                "damage": "2",
                "keywords": "Sustained Hits 2"
            },
            {
                "name": "Graviton blast cannon",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "3",
                "skill": "4+",
                "strength": "5",
                "ap": "-2",
                "damage": "3",
                "keywords": "Anti-MONSTER 3+, Anti-VEHICLE 3+"
            },
            {
                "name": "SP conversion beamer",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "2",
                "skill": "4+",
                "strength": "7",
                "ap": "-2",
                "damage": "3",
                "keywords": "Conversion, Lethal Hits"
            }
        ],
        "abilities": [
            {
                "name": "Breaching Fire",
                "description": "In your Shooting phase, after this unit has shot, select one enemy unit hit by one or more of those attacks. Until the start of your next Shooting phase, that enemy unit cannot have the Benefit of Cover."
            },
            {
                "name": "Guerrilla Adepts",
                "description": "In your Shooting phase, just after this unit is selected to shoot, this unit can use this ability. If it does, select one enemy unit (excluding Monsters and Vehicles). Until the end of the phase, attacks made by models in this unit can only attack that enemy unit (and only if it is an eligible target) and, after resolving those attacks, if one or more of those attacks hit that enemy unit, until the start of your next Shooting phase, that enemy unit is assailed (this simply labels that unit for the purposes of this ability and some Enhancements or Stratagems). If that unit is already assailed, until the start of your next Shooting phase, it is also pinned. While a unit is pinned, subtract 2\" from its Move characteristic and subtract 2 from Charge rolls made for it."
            }
        ]
    },
    "Buri Aegnirssen": {
        "stats": {
            "stat_movement": "5\"",
            "stat_toughness": 6,
            "stat_save": "3+",
            "stat_wounds": 5,
            "stat_leadership": "6+",
            "stat_oc": 1,
            "stat_invuln": "4+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Autoch-pattern bolt pistol",
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
                "name": "➤ Bane - strike",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "5",
                "skill": "2+",
                "strength": "12",
                "ap": "-3",
                "damage": "3",
                "keywords": "Precision"
            },
            {
                "name": "➤ Bane - sweep",
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
                "name": "Grudge-fuelled Fortitude",
                "description": "The first time this model is destroyed, at the end of the phase, roll one D6: on a 2+, set this model back up on the battlefield as close as possible to where it was destroyed and not within Engagement Range of one or more enemy units, with its full wounds remaining."
            },
            {
                "name": "Unhinged Vengeance",
                "description": "In your opponent’s Shooting phase, when an enemy unit has shot, if this model lost one or more wounds as a result of those attacks, this unit can make a surge move of up to D6+2\"."
            },
            {
                "name": "Guerrilla Adepts",
                "description": "In your Shooting phase, just after this unit is selected to shoot, this unit can use this ability. If it does, select one enemy unit (excluding Monsters and Vehicles). Until the end of the phase, attacks made by models in this unit can only attack that enemy unit (and only if it is an eligible target) and, after resolving those attacks, if one or more of those attacks hit that enemy unit, until the start of your next Shooting phase, that enemy unit is assailed (this simply labels that unit for the purposes of this ability and some Enhancements or Stratagems). If that unit is already assailed, until the start of your next Shooting phase, it is also pinned. While a unit is pinned, subtract 2\" from its Move characteristic and subtract 2 from Charge rolls made for it."
            }
        ]
    },
    "Cthonian Berserks": {
        "stats": {
            "stat_movement": "6\"",
            "stat_toughness": 6,
            "stat_save": "5+",
            "stat_wounds": 1,
            "stat_leadership": "7+",
            "stat_oc": 1,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Concussion maul",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "3",
                "skill": "4+",
                "strength": "5",
                "ap": "-2",
                "damage": "3",
                "keywords": "Anti-MONSTER 3+, Anti-VEHICLE 3+"
            },
            {
                "name": "Heavy plasma axe",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "3",
                "skill": "4+",
                "strength": "7",
                "ap": "-2",
                "damage": "3",
                "keywords": "-"
            },
            {
                "name": "Twin concussion gauntlets",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "4+",
                "strength": "9",
                "ap": "-2",
                "damage": "2",
                "keywords": "Twin-linked"
            },
            {
                "name": "Mole grenade launcher",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "D6",
                "skill": "5+",
                "strength": "5",
                "ap": "-1",
                "damage": "1",
                "keywords": "Blast, Indirect Fire"
            }
        ],
        "abilities": [
            {
                "name": "Cyberstimms",
                "description": "Each time a model in this unit is destroyed by a melee attack, if that model has not fought this phase, roll one D6, adding one to the result if units from your army have Fortify Takeover: on a 4+, do not remove it from play. The destroyed model can fight after the attacking unit has finished making its attacks, and is then removed from play."
            },
            {
                "name": "Guerrilla Adepts",
                "description": "In your Shooting phase, just after this unit is selected to shoot, this unit can use this ability. If it does, select one enemy unit (excluding Monsters and Vehicles). Until the end of the phase, attacks made by models in this unit can only attack that enemy unit (and only if it is an eligible target) and, after resolving those attacks, if one or more of those attacks hit that enemy unit, until the start of your next Shooting phase, that enemy unit is assailed (this simply labels that unit for the purposes of this ability and some Enhancements or Stratagems). If that unit is already assailed, until the start of your next Shooting phase, it is also pinned. While a unit is pinned, subtract 2\" from its Move characteristic and subtract 2 from Charge rolls made for it."
            },
            {
                "name": "Subterranean Explosives",
                "description": "In your Shooting phase, after this unit has shot, select one enemy unit (excluding Monsters and Vehicles) that was hit by one or more of those attacks made with a mole grenade launcher. Until the start of your next Shooting phase, that enemy unit cannot be targeted with the Fire Overwatch Stratagem."
            }
        ]
    },
    "Cthonian Earthshakers": {
        "stats": {
            "stat_movement": "4\"",
            "stat_toughness": 6,
            "stat_save": "4+",
            "stat_wounds": 6,
            "stat_leadership": "7+",
            "stat_oc": 2,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Plasma picks",
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
                "name": "Autoch-pattern bolt pistol",
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
                "name": "Breacher ordnance",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "D6+1",
                "skill": "5+",
                "strength": "10",
                "ap": "-1",
                "damage": "2",
                "keywords": "Blast, Heavy, Indirect Fire"
            },
            {
                "name": "Tremor shells",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "D6+4",
                "skill": "5+",
                "strength": "6",
                "ap": "-1",
                "damage": "1",
                "keywords": "Blast, Heavy, Indirect Fire"
            }
        ],
        "abilities": [
            {
                "name": "Guerrilla Adepts",
                "description": "In your Shooting phase, just after this unit is selected to shoot, this unit can use this ability. If it does, select one enemy unit (excluding Monsters and Vehicles). Until the end of the phase, attacks made by models in this unit can only attack that enemy unit (and only if it is an eligible target) and, after resolving those attacks, if one or more of those attacks hit that enemy unit, until the start of your next Shooting phase, that enemy unit is assailed (this simply labels that unit for the purposes of this ability and some Enhancements or Stratagems). If that unit is already assailed, until the start of your next Shooting phase, it is also pinned. While a unit is pinned, subtract 2\" from its Move characteristic and subtract 2 from Charge rolls made for it."
            },
            {
                "name": "Geomantic Hunters",
                "description": "Up to twice per battle, in your Shooting phase, when this unit is selected to shoot, it can use this ability. If it does, until the end of the phase, each time a model in this unit makes an attack with its breacher ordnance, you can re-roll the Wound roll."
            },
            {
                "name": "Destabilising Quakes",
                "description": "In your Shooting phase, after this unit has shot, select one enemy unit hit by one or more of those attacks made with its tremor shells. That unit must take a Battle-shock test, subtracting 1 from the result."
            }
        ]
    },
    "Einhyr Champion": {
        "stats": {
            "stat_movement": "5\"",
            "stat_toughness": 5,
            "stat_save": "2+",
            "stat_wounds": 5,
            "stat_leadership": "7+",
            "stat_oc": 1,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Autoch-pattern combi-bolter",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "4",
                "skill": "2+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "Mass hammer",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "3",
                "skill": "3+",
                "strength": "12",
                "ap": "-3",
                "damage": "D6+1",
                "keywords": "-"
            },
            {
                "name": "Darkstar axe",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "6",
                "skill": "2+",
                "strength": "6",
                "ap": "-3",
                "damage": "2",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Leader",
                "description": "This model can be attached to the following unit:\n- EINHYR HEARTHGUARD"
            },
            {
                "name": "Exemplar of the Einhyr",
                "description": "While this model is leading a unit, add 1 to Advance and Charge rolls made for that unit."
            },
            {
                "name": "Mass Driver Accelerators",
                "description": "Each time this model ends a Charge move, you can select one enemy unit within Engagement Range of this model and roll one D6: on a 2-5, that enemy unit suffers D3 mortal wounds; on a 6, that enemy unit suffers D3+3 mortal wounds."
            },
            {
                "name": "Guerrilla Adepts",
                "description": "In your Shooting phase, just after this unit is selected to shoot, this unit can use this ability. If it does, select one enemy unit (excluding Monsters and Vehicles). Until the end of the phase, attacks made by models in this unit can only attack that enemy unit (and only if it is an eligible target) and, after resolving those attacks, if one or more of those attacks hit that enemy unit, until the start of your next Shooting phase, that enemy unit is assailed (this simply labels that unit for the purposes of this ability and some Enhancements or Stratagems). If that unit is already assailed, until the start of your next Shooting phase, it is also pinned. While a unit is pinned, subtract 2\" from its Move characteristic and subtract 2 from Charge rolls made for it."
            },
            {
                "name": "Weavefield crest",
                "description": "The bearer has a 4+ invulnerable save."
            },
            {
                "name": "Teleport crest",
                "description": "While the bearer is leading a unit, models in that unit have the Deep Strike ability."
            }
        ]
    },
    "Einhyr Hearthguard": {
        "stats": {
            "stat_movement": "5\"",
            "stat_toughness": 5,
            "stat_save": "2+",
            "stat_wounds": 2,
            "stat_leadership": "7+",
            "stat_oc": 1,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Exo-armour grenade launcher",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "D3",
                "skill": "3+",
                "strength": "3",
                "ap": "0",
                "damage": "1",
                "keywords": "Blast"
            },
            {
                "name": "EtaCarn plasma gun",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "7",
                "ap": "-3",
                "damage": "2",
                "keywords": "Rapid Fire 1"
            },
            {
                "name": "Volkanite disintegrator",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "3",
                "skill": "3+",
                "strength": "5",
                "ap": "0",
                "damage": "1",
                "keywords": "Devastating Wounds"
            },
            {
                "name": "Concussion gauntlet",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "2",
                "skill": "3+",
                "strength": "8",
                "ap": "-2",
                "damage": "2",
                "keywords": "-"
            },
            {
                "name": "Plasma blade gauntlet",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "3",
                "skill": "3+",
                "strength": "6",
                "ap": "-2",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "Graviton hammer",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "3",
                "skill": "4+",
                "strength": "9",
                "ap": "-1",
                "damage": "3",
                "keywords": "Anti-MONSTER 3+, Anti-VEHICLE 3+"
            }
        ],
        "abilities": [
            {
                "name": "Decisive Destruction",
                "description": "Each time a model in this unit makes a ranged attack that targets the closest eligible target, re-roll a Hit roll of 1."
            },
            {
                "name": "Guerrilla Adepts",
                "description": "In your Shooting phase, just after this unit is selected to shoot, this unit can use this ability. If it does, select one enemy unit (excluding Monsters and Vehicles). Until the end of the phase, attacks made by models in this unit can only attack that enemy unit (and only if it is an eligible target) and, after resolving those attacks, if one or more of those attacks hit that enemy unit, until the start of your next Shooting phase, that enemy unit is assailed (this simply labels that unit for the purposes of this ability and some Enhancements or Stratagems). If that unit is already assailed, until the start of your next Shooting phase, it is also pinned. While a unit is pinned, subtract 2\" from its Move characteristic and subtract 2 from Charge rolls made for it."
            },
            {
                "name": "Teleport crest",
                "description": "Models in the bearer's unit have the Deep Strike ability."
            },
            {
                "name": "Weavefield crest",
                "description": "Models in the bearer's unit have a 5+ invulnerable save."
            }
        ]
    },
    "Grimnyr": {
        "stats": {
            "stat_movement": "5\"",
            "stat_toughness": 5,
            "stat_save": "4+",
            "stat_wounds": 4,
            "stat_leadership": "6+",
            "stat_oc": 1,
            "stat_invuln": "4+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Ancestral ward stave",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "2",
                "skill": "3+",
                "strength": "7",
                "ap": "-1",
                "damage": "D3",
                "keywords": "Psychic"
            },
            {
                "name": "➤ Ancestral Wrath - witchfire",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "3",
                "skill": "3+",
                "strength": "6",
                "ap": "-2",
                "damage": "D3",
                "keywords": "Psychic"
            },
            {
                "name": "➤ Ancestral Wrath - focused witchfire",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "6",
                "skill": "3+",
                "strength": "6",
                "ap": "-2",
                "damage": "D3",
                "keywords": "Hazardous, Psychic"
            },
            {
                "name": "Autoch-pattern bolter",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "2",
                "skill": "4+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "-"
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
            }
        ],
        "abilities": [
            {
                "name": "Leader",
                "description": "This model can be attached to the following unit:\n- HEARTHKYN WARRIORS"
            },
            {
                "name": "Fortify (Psychic)",
                "description": "While this model is leading a unit, models in that unit have the Feel No Pain 5+ ability."
            },
            {
                "name": "Grimnyr's Regard",
                "description": "Once per battle, at the start of any phase, you can select one friendly Leagues of Votann unit that is Battle-shocked and within 12\" of this unit's Grimnyr model. That unit is no longer Battle-shocked."
            },
            {
                "name": "Unit Composition",
                "description": "If this unit’s Grimnyr model is ever destroyed, all of this unit’s remaining CORV models are also destroyed. While embarking within a Transport and while embarked within a Transport, each CORV model takes up the space of 0 models.’"
            },
            {
                "name": "Guerrilla Adepts",
                "description": "In your Shooting phase, just after this unit is selected to shoot, this unit can use this ability. If it does, select one enemy unit (excluding Monsters and Vehicles). Until the end of the phase, attacks made by models in this unit can only attack that enemy unit (and only if it is an eligible target) and, after resolving those attacks, if one or more of those attacks hit that enemy unit, until the start of your next Shooting phase, that enemy unit is assailed (this simply labels that unit for the purposes of this ability and some Enhancements or Stratagems). If that unit is already assailed, until the start of your next Shooting phase, it is also pinned. While a unit is pinned, subtract 2\" from its Move characteristic and subtract 2 from Charge rolls made for it."
            }
        ]
    },
    "Hearthkyn Warriors": {
        "stats": {
            "stat_movement": "5\"",
            "stat_toughness": 5,
            "stat_save": "4+",
            "stat_wounds": 1,
            "stat_leadership": "7+",
            "stat_oc": 2,
            "stat_invuln": "5+",
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
                "name": "Theyn's melee weapon",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "2",
                "skill": "4+",
                "strength": "5",
                "ap": "-2",
                "damage": "2",
                "keywords": "-"
            },
            {
                "name": "Autoch-pattern bolt pistol",
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
                "name": "Autoch-pattern bolter",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "2",
                "skill": "4+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "Ion blaster",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "1",
                "skill": "4+",
                "strength": "5",
                "ap": "-2",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "Theyn's pistol",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "1",
                "skill": "4+",
                "strength": "8",
                "ap": "-2",
                "damage": "1",
                "keywords": "Pistol"
            },
            {
                "name": "Plasma knife",
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
                "name": "HYLas rotary cannon",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "6",
                "skill": "5+",
                "strength": "6",
                "ap": "-1",
                "damage": "1",
                "keywords": "Heavy, Sustained Hits 1"
            },
            {
                "name": "HYLas auto rifle",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "3",
                "skill": "4+",
                "strength": "6",
                "ap": "-1",
                "damage": "1",
                "keywords": "Assault, Rapid Fire 3"
            },
            {
                "name": "➤ L7 missile launcher - blast",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "D6",
                "skill": "4+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Blast"
            },
            {
                "name": "➤ L7 missile launcher - focused",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "1",
                "skill": "4+",
                "strength": "9",
                "ap": "-2",
                "damage": "D6"
            },
            {
                "name": "Magna-rail rifle",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "1",
                "skill": "5+",
                "strength": "12",
                "ap": "-3",
                "damage": "D3+3",
                "keywords": "Devastating Wounds, Heavy"
            },
            {
                "name": "EtaCarn plasma beamer",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "1",
                "skill": "4+",
                "strength": "8",
                "ap": "-3",
                "damage": "2",
                "keywords": "Sustained Hits D3"
            }
        ],
        "abilities": [
            {
                "name": "Luck Has, Need Keeps, Toil Earns",
                "description": "At the end of your Command phase, if this unit is within range of an objective marker you control, that objective marker remains under your control, until your opponent's Level of Control over that is greater than yours at the end of a phase."
            },
            {
                "name": "Pan-spectral Scanning",
                "description": "Each time a model in this unit makes a ranged attack, re-roll a Hit roll of 1."
            },
            {
                "name": "Guerrilla Adepts",
                "description": "In your Shooting phase, just after this unit is selected to shoot, this unit can use this ability. If it does, select one enemy unit (excluding Monsters and Vehicles). Until the end of the phase, attacks made by models in this unit can only attack that enemy unit (and only if it is an eligible target) and, after resolving those attacks, if one or more of those attacks hit that enemy unit, until the start of your next Shooting phase, that enemy unit is assailed (this simply labels that unit for the purposes of this ability and some Enhancements or Stratagems). If that unit is already assailed, until the start of your next Shooting phase, it is also pinned. While a unit is pinned, subtract 2\" from its Move characteristic and subtract 2 from Charge rolls made for it."
            },
            {
                "name": "Weavefield crest",
                "description": "Models in the bearer's unit have a 5+ invulnerable save."
            }
        ]
    },
    "Hekaton Land Fortress": {
        "stats": {
            "stat_movement": "10\"",
            "stat_toughness": 12,
            "stat_save": "2+",
            "stat_wounds": 16,
            "stat_leadership": "7+",
            "stat_oc": 5,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Armoured wheels",
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
                "name": "MATR autocannon",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "6",
                "skill": "4+",
                "strength": "7",
                "ap": "-1",
                "damage": "2",
                "keywords": "Assault, Sustained Hits 1"
            },
            {
                "name": "SP heavy conversion beamer",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "4",
                "skill": "4+",
                "strength": "10",
                "ap": "-2",
                "damage": "4",
                "keywords": "Conversion, Lethal Hits"
            },
            {
                "name": "Heavy magna-rail cannon",
                "weapon_type": "ranged",
                "range": "30\"",
                "attacks": "2",
                "skill": "4+",
                "strength": "18",
                "ap": "-4",
                "damage": "D6+4",
                "keywords": "Devastating Wounds, Heavy"
            },
            {
                "name": "Cyclic ion cannon",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "D6+2",
                "skill": "4+",
                "strength": "7",
                "ap": "-2",
                "damage": "2",
                "keywords": "Blast"
            },
            {
                "name": "Twin ion beamer",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "D3+1",
                "skill": "4+",
                "strength": "8",
                "ap": "-2",
                "damage": "1",
                "keywords": "Blast, Twin-linked"
            },
            {
                "name": "Twin bolt cannon",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "3",
                "skill": "4+",
                "strength": "6",
                "ap": "-1",
                "damage": "2",
                "keywords": "Sustained Hits 2, Twin-linked"
            },
            {
                "name": "Hekaton warhead",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "D6+3",
                "skill": "4+",
                "strength": "7",
                "ap": "-2",
                "damage": "2",
                "keywords": "Blast, One Shot"
            }
        ],
        "abilities": [
            {
                "name": "MultiCOG Targeting",
                "description": "Each time this model makes a ranged attack, you can ignore any or all modifiers to the following: that attack's Ballistic Skill characteristic, the Hit roll."
            },
            {
                "name": "Damaged: 1-5 wounds remaining",
                "description": "While this model has 1-5 wounds remaining, each time this model makes an attack, subtract 1 from the Hit roll."
            },
            {
                "name": "Guerrilla Adepts",
                "description": "In your Shooting phase, just after this unit is selected to shoot, this unit can use this ability. If it does, select one enemy unit (excluding Monsters and Vehicles). Until the end of the phase, attacks made by models in this unit can only attack that enemy unit (and only if it is an eligible target) and, after resolving those attacks, if one or more of those attacks hit that enemy unit, until the start of your next Shooting phase, that enemy unit is assailed (this simply labels that unit for the purposes of this ability and some Enhancements or Stratagems). If that unit is already assailed, until the start of your next Shooting phase, it is also pinned. While a unit is pinned, subtract 2\" from its Move characteristic and subtract 2 from Charge rolls made for it."
            },
            {
                "name": "Firebase Control (Aura)",
                "description": "While a friendly Leagues of Votann Infantry unit is wholly within 6\" of this Transport, ranged weapons equipped by models in that Infantry unit have the [sustained hits 1] ability."
            },
            {
                "name": "Pan spectral scanner",
                "description": "Each time a model in the bearer's unit makes a ranged attack, re-roll a Hit roll of 1."
            }
        ]
    },
    "Hernkyn Pioneers": {
        "stats": {
            "stat_movement": "12\"",
            "stat_toughness": 6,
            "stat_save": "4+",
            "stat_wounds": 3,
            "stat_leadership": "7+",
            "stat_oc": 2,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Bolt revolver",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "1",
                "skill": "4+",
                "strength": "5",
                "ap": "0",
                "damage": "1",
                "keywords": "Pistol"
            },
            {
                "name": "Bolt shotgun",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "2",
                "skill": "4+",
                "strength": "5",
                "ap": "0",
                "damage": "1",
                "keywords": "Assault"
            },
            {
                "name": "Magna-coil autocannon",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "3",
                "skill": "4+",
                "strength": "7",
                "ap": "-1",
                "damage": "2",
                "keywords": "-"
            },
            {
                "name": "Plasma knife",
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
                "name": "HYLas rotary cannon",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "6",
                "skill": "4+",
                "strength": "6",
                "ap": "-1",
                "damage": "1",
                "keywords": "Sustained Hits 1"
            },
            {
                "name": "Ion beamer",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "D3+1",
                "skill": "4+",
                "strength": "8",
                "ap": "-2",
                "damage": "1",
                "keywords": "Blast"
            }
        ],
        "abilities": [
            {
                "name": "Outflanking Mag-Riders",
                "description": "At the end of your opponent’s turn, if this unit is wholly within 9\" of one or more battlefield edges and not within Engagement Range of one or more enemy units, you can remove it from the battlefield and place it into Strategic Reserves."
            },
            {
                "name": "Guerrilla Adepts",
                "description": "In your Shooting phase, just after this unit is selected to shoot, this unit can use this ability. If it does, select one enemy unit (excluding Monsters and Vehicles). Until the end of the phase, attacks made by models in this unit can only attack that enemy unit (and only if it is an eligible target) and, after resolving those attacks, if one or more of those attacks hit that enemy unit, until the start of your next Shooting phase, that enemy unit is assailed (this simply labels that unit for the purposes of this ability and some Enhancements or Stratagems). If that unit is already assailed, until the start of your next Shooting phase, it is also pinned. While a unit is pinned, subtract 2\" from its Move characteristic and subtract 2 from Charge rolls made for it."
            },
            {
                "name": "Comms array",
                "description": "Each time you target the bearer’s unit with a Stratagem, roll one D6: on a 5+, you gain 1CP."
            },
            {
                "name": "Pan-spectral scanner",
                "description": "Each time a model in the bearer's unit makes a ranged attack, re-roll a Hit roll of 1."
            },
            {
                "name": "Rollbar searchlight",
                "description": "Each time a model in the bearer's unit makes a ranged attack, you can ignore any or all modifiers to the Hit roll."
            },
            {
                "name": "Pan-spectral Lockons",
                "description": "In your Shooting phase, you can select one visible enemy unit within 12\" of this unit. That enemy unit is spotted:\n- While a unit is spotted, that unit has +3\" detection range."
            }
        ]
    },
    "Hernkyn Yaegirs": {
        "stats": {
            "stat_movement": "6\"",
            "stat_toughness": 5,
            "stat_save": "5+",
            "stat_wounds": 1,
            "stat_leadership": "7+",
            "stat_oc": 1,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Bolt shotgun",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "2",
                "skill": "4+",
                "strength": "5",
                "ap": "0",
                "damage": "1",
                "keywords": "Assault"
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
                "name": "APM launcher",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "1",
                "skill": "4+",
                "strength": "6",
                "ap": "-2",
                "damage": "D6",
                "keywords": "Anti-MONSTER 3+, Anti-VEHICLE 3+"
            },
            {
                "name": "Magna-coil rifle",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "1",
                "skill": "4+",
                "strength": "5",
                "ap": "-2",
                "damage": "2",
                "keywords": "Ignores Cover, Precision"
            },
            {
                "name": "Bolt revolver",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "1",
                "skill": "4+",
                "strength": "5",
                "ap": "0",
                "damage": "1",
                "keywords": "Pistol"
            },
            {
                "name": "Plasma knife",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "2",
                "skill": "4+",
                "strength": "4",
                "ap": "-2",
                "damage": "1",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Pragmatic Hunters",
                "description": "In your opponent's Movement phase, if an enemy unit ends a move within 8” of this unit, if this unit is not within Engagement Range of one or more enemy units, this unit can make a Normal move of up to D6”.'"
            },
            {
                "name": "Guerrilla Adepts",
                "description": "In your Shooting phase, just after this unit is selected to shoot, this unit can use this ability. If it does, select one enemy unit (excluding Monsters and Vehicles). Until the end of the phase, attacks made by models in this unit can only attack that enemy unit (and only if it is an eligible target) and, after resolving those attacks, if one or more of those attacks hit that enemy unit, until the start of your next Shooting phase, that enemy unit is assailed (this simply labels that unit for the purposes of this ability and some Enhancements or Stratagems). If that unit is already assailed, until the start of your next Shooting phase, it is also pinned. While a unit is pinned, subtract 2\" from its Move characteristic and subtract 2 from Charge rolls made for it."
            },
            {
                "name": "Shroudwërke Talismans",
                "description": "This unit has -3\" detection range."
            }
        ]
    },
    "Ironkin Steeljacks with Heavy Volkanite Disintegrators": {
        "stats": {
            "stat_movement": "5\"",
            "stat_toughness": 6,
            "stat_save": "2+",
            "stat_wounds": 3,
            "stat_leadership": "7+",
            "stat_oc": 1,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Heavy volkanite disintegrator",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "6",
                "skill": "4+",
                "strength": "6",
                "ap": "-1",
                "damage": "1",
                "keywords": "Devastating Wounds"
            },
            {
                "name": "Plasma knife",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "2",
                "skill": "3+",
                "strength": "6",
                "ap": "-2",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "Autoch-pattern bolter",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "2",
                "skill": "4+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Pistol"
            },
            {
                "name": "Plasma sword",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "6",
                "skill": "3+",
                "strength": "6",
                "ap": "-2",
                "damage": "1",
                "keywords": "Sustained Hits 1"
            }
        ],
        "abilities": [
            {
                "name": "Purge Response",
                "description": "Each time you target this unit with the Fire Overwatch Stratagem, hits are scored on unmodified Hit rolls of 5+ while resolving that Stratagem. If units from your army have Fortify Takeover, hits are scored on unmodified Hit rolls of 4+ while resolving that Stratagem instead."
            },
            {
                "name": "Guerrilla Adepts",
                "description": "In your Shooting phase, just after this unit is selected to shoot, this unit can use this ability. If it does, select one enemy unit (excluding Monsters and Vehicles). Until the end of the phase, attacks made by models in this unit can only attack that enemy unit (and only if it is an eligible target) and, after resolving those attacks, if one or more of those attacks hit that enemy unit, until the start of your next Shooting phase, that enemy unit is assailed (this simply labels that unit for the purposes of this ability and some Enhancements or Stratagems). If that unit is already assailed, until the start of your next Shooting phase, it is also pinned. While a unit is pinned, subtract 2\" from its Move characteristic and subtract 2 from Charge rolls made for it."
            },
            {
                "name": "Preymark crest",
                "description": "Each time a model in the bearer's unit makes an attack that targets an enemy unit within range of one or more objective markers, on a Critical Wound, that attack has the [Precision] ability."
            }
        ]
    },
    "Ironkin Steeljacks with Melee Weapons": {
        "stats": {
            "stat_movement": "5\"",
            "stat_toughness": 6,
            "stat_save": "2+",
            "stat_wounds": 3,
            "stat_leadership": "7+",
            "stat_oc": 1,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Autoch-pattern bolter",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "2",
                "skill": "4+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Pistol"
            },
            {
                "name": "Plasma sword",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "6",
                "skill": "3+",
                "strength": "6",
                "ap": "-2",
                "damage": "1",
                "keywords": "Sustained Hits 1"
            },
            {
                "name": "Concussion gauntlet",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "3",
                "skill": "4+",
                "strength": "10",
                "ap": "-2",
                "damage": "2",
                "keywords": "Lethal Hits"
            }
        ],
        "abilities": [
            {
                "name": "Merciless Eradication",
                "description": "Each time an enemy unit (excluding Monsters and Vehicles) that is within Engagement Range of this unit Falls Back, all models in that enemy unit must take a Desperate Escape test. When doing so, if that enemy unit is Battle-shocked, subtract 1 from each of those tests."
            },
            {
                "name": "Guerrilla Adepts",
                "description": "In your Shooting phase, just after this unit is selected to shoot, this unit can use this ability. If it does, select one enemy unit (excluding Monsters and Vehicles). Until the end of the phase, attacks made by models in this unit can only attack that enemy unit (and only if it is an eligible target) and, after resolving those attacks, if one or more of those attacks hit that enemy unit, until the start of your next Shooting phase, that enemy unit is assailed (this simply labels that unit for the purposes of this ability and some Enhancements or Stratagems). If that unit is already assailed, until the start of your next Shooting phase, it is also pinned. While a unit is pinned, subtract 2\" from its Move characteristic and subtract 2 from Charge rolls made for it."
            },
            {
                "name": "Preymark crest",
                "description": "Each time a model in the bearer's unit makes an attack that targets an enemy unit within range of one or more objective markers, on a Critical Wound, that attack has the [Precision] ability."
            }
        ]
    },
    "Kahl": {
        "stats": {
            "stat_movement": "5\"",
            "stat_toughness": 5,
            "stat_save": "3+",
            "stat_wounds": 4,
            "stat_leadership": "7+",
            "stat_oc": 1,
            "stat_invuln": "4+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Mass gauntlet",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "3",
                "skill": "3+",
                "strength": "8",
                "ap": "-3",
                "damage": "3",
                "keywords": "-"
            },
            {
                "name": "Forgewrought plasma axe",
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
                "name": "Autoch-pattern combi-bolter",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "4",
                "skill": "2+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "Volkanite disintegrator",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "3",
                "skill": "2+",
                "strength": "5",
                "ap": "0",
                "damage": "1",
                "keywords": "Devastating Wounds"
            }
        ],
        "abilities": [
            {
                "name": "Kindred Hero",
                "description": "While this model is leading a unit, weapons equipped by models in that unit have the [LETHAL HITS] ability."
            },
            {
                "name": "Leader",
                "description": "This model can be attached to the following units:\n- EINHYR HEARTHGUARD\n- HEARTHKYN WARRIORS"
            },
            {
                "name": "Seized Opportunity",
                "description": "Once per phase, one model from your army with this ability can use it when its unit destroys an enemy unit. If it does, gain 1YP."
            },
            {
                "name": "Guerrilla Adepts",
                "description": "In your Shooting phase, just after this unit is selected to shoot, this unit can use this ability. If it does, select one enemy unit (excluding Monsters and Vehicles). Until the end of the phase, attacks made by models in this unit can only attack that enemy unit (and only if it is an eligible target) and, after resolving those attacks, if one or more of those attacks hit that enemy unit, until the start of your next Shooting phase, that enemy unit is assailed (this simply labels that unit for the purposes of this ability and some Enhancements or Stratagems). If that unit is already assailed, until the start of your next Shooting phase, it is also pinned. While a unit is pinned, subtract 2\" from its Move characteristic and subtract 2 from Charge rolls made for it."
            },
            {
                "name": "Rampart crest",
                "description": "While the bearer is leading a unit, models in that unit have a 5+ invulnerable save."
            },
            {
                "name": "Teleport crest",
                "description": "While the bearer is leading a unit, models in that unit have the Deep Strike ability."
            }
        ]
    },
    "Kapricus Carrier": {
        "stats": {
            "stat_movement": "12\"",
            "stat_toughness": 7,
            "stat_save": "4+",
            "stat_wounds": 7,
            "stat_leadership": "7+",
            "stat_oc": 2,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Magna-coil autocannon",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "3",
                "skill": "4+",
                "strength": "7",
                "ap": "-1",
                "damage": "2",
                "keywords": "-"
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
                "name": "Twin magna-coil autocannon",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "3",
                "skill": "4+",
                "strength": "7",
                "ap": "-1",
                "damage": "2",
                "keywords": "Twin-linked"
            }
        ],
        "abilities": [
            {
                "name": "Scanner Uplinks",
                "description": "In your shooting phase, after this model has shot, select one enemy unit (excluding Monsters and Vehicles) hit by one or more of those attacks. Until the start of your next turn, that enemy unit is suppressed. While a unit is suppressed, each time a model in that unit makes an attack, subtract 1 from the Hit roll."
            },
            {
                "name": "Guerrilla Adepts",
                "description": "In your Shooting phase, just after this unit is selected to shoot, this unit can use this ability. If it does, select one enemy unit (excluding Monsters and Vehicles). Until the end of the phase, attacks made by models in this unit can only attack that enemy unit (and only if it is an eligible target) and, after resolving those attacks, if one or more of those attacks hit that enemy unit, until the start of your next Shooting phase, that enemy unit is assailed (this simply labels that unit for the purposes of this ability and some Enhancements or Stratagems). If that unit is already assailed, until the start of your next Shooting phase, it is also pinned. While a unit is pinned, subtract 2\" from its Move characteristic and subtract 2 from Charge rolls made for it."
            },
            {
                "name": "Firebase Control (Aura)",
                "description": "While a friendly Leagues of Votann Infantry unit is wholly within 6\" of this Transport, ranged weapons equipped by models in that Infantry unit have the [sustained hits 1] ability."
            },
            {
                "name": "Smoke Launcher",
                "description": "The bearer has the Smoke keyword."
            }
        ]
    },
    "Kapricus Defenders": {
        "stats": {
            "stat_movement": "12\"",
            "stat_toughness": 7,
            "stat_save": "4+",
            "stat_wounds": 7,
            "stat_leadership": "7+",
            "stat_oc": 2,
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
                "name": "Twin magna-coil autocannon",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "3",
                "skill": "4+",
                "strength": "7",
                "ap": "-1",
                "damage": "2",
                "keywords": "Twin-linked"
            },
            {
                "name": "Magna-rail cannon",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "1",
                "skill": "4+",
                "strength": "14",
                "ap": "-4",
                "damage": "D3+3",
                "keywords": "Devastating Wounds, Heavy"
            },
            {
                "name": "HYLas rotary cannon",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "6",
                "skill": "4+",
                "strength": "6",
                "ap": "-1",
                "damage": "2",
                "keywords": "Sustained Hits 1"
            }
        ],
        "abilities": [
            {
                "name": "Opportunistic Manoeuvre",
                "description": "In your Shooting phase, after this unit has shot, it can make a Normal Move of up to D6\". If it does, until the end of the turn, this unit is not eligible to declare a charge."
            },
            {
                "name": "Guerrilla Adepts",
                "description": "In your Shooting phase, just after this unit is selected to shoot, this unit can use this ability. If it does, select one enemy unit (excluding Monsters and Vehicles). Until the end of the phase, attacks made by models in this unit can only attack that enemy unit (and only if it is an eligible target) and, after resolving those attacks, if one or more of those attacks hit that enemy unit, until the start of your next Shooting phase, that enemy unit is assailed (this simply labels that unit for the purposes of this ability and some Enhancements or Stratagems). If that unit is already assailed, until the start of your next Shooting phase, it is also pinned. While a unit is pinned, subtract 2\" from its Move characteristic and subtract 2 from Charge rolls made for it."
            },
            {
                "name": "Smoke Launcher",
                "description": "The bearer has the Smoke keyword."
            }
        ]
    },
    "Memnyr Strategist": {
        "stats": {
            "stat_movement": "5\"",
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
                "name": "Autoch-pattern bolt pistol",
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
                "name": "Close combat weapon",
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
                "name": "Computational Mastermind",
                "description": "At the end of your Command phase, before you determine if units from your army have Hostile Acquisition or Fortify Takeover, for each objective marker you control that has one or more models with this ability in range of it, you can spend 1YP or gain 1YP."
            },
            {
                "name": "Predictive Guidance",
                "description": "Once per battle round, when you target this unit with the Fire Overwatch/Heroic Intervention stratagem, you can use this ability. If you do, that use of that stratagem is -1 CP."
            },
            {
                "name": "Leader",
                "description": "This model can be attached to the following units: Ironkin Steeljacks with Heavy Volkanite Disintegrators, Ironkin Steeljacks with Melee Weapons"
            },
            {
                "name": "Guerrilla Adepts",
                "description": "In your Shooting phase, just after this unit is selected to shoot, this unit can use this ability. If it does, select one enemy unit (excluding Monsters and Vehicles). Until the end of the phase, attacks made by models in this unit can only attack that enemy unit (and only if it is an eligible target) and, after resolving those attacks, if one or more of those attacks hit that enemy unit, until the start of your next Shooting phase, that enemy unit is assailed (this simply labels that unit for the purposes of this ability and some Enhancements or Stratagems). If that unit is already assailed, until the start of your next Shooting phase, it is also pinned. While a unit is pinned, subtract 2\" from its Move characteristic and subtract 2 from Charge rolls made for it."
            }
        ]
    },
    "Sagitaur": {
        "stats": {
            "stat_movement": "12\"",
            "stat_toughness": 9,
            "stat_save": "3+",
            "stat_wounds": 9,
            "stat_leadership": "7+",
            "stat_oc": 2,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Armoured wheels",
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
                "name": "Twin bolt cannon",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "3",
                "skill": "4+",
                "strength": "6",
                "ap": "-1",
                "damage": "2",
                "keywords": "Sustained Hits 2, Twin-linked"
            },
            {
                "name": "HYLas beam cannon",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "2",
                "skill": "4+",
                "strength": "12",
                "ap": "-3",
                "damage": "D6+1"
            },
            {
                "name": "Sagitaur missile launcher",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "2",
                "skill": "4+",
                "strength": "10",
                "ap": "-3",
                "damage": "3"
            },
            {
                "name": "➤ L7 missile launcher - blast",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "D6",
                "skill": "4+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Blast"
            },
            {
                "name": "➤ L7 missile launcher - focused",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "1",
                "skill": "4+",
                "strength": "9",
                "ap": "-2",
                "damage": "D6"
            },
            {
                "name": "MATR autocannon",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "6",
                "skill": "4+",
                "strength": "7",
                "ap": "-1",
                "damage": "2",
                "keywords": "Assault, Sustained Hits 1"
            }
        ],
        "abilities": [
            {
                "name": "Blistering Advance",
                "description": "Units can disembark from this Transport after it has Advanced. Units that do so count as having made a Normal move that phase, and cannot declare a charge in the same turn, but can otherwise act normally in the remainder of the turn."
            },
            {
                "name": "Guerrilla Adepts",
                "description": "In your Shooting phase, just after this unit is selected to shoot, this unit can use this ability. If it does, select one enemy unit (excluding Monsters and Vehicles). Until the end of the phase, attacks made by models in this unit can only attack that enemy unit (and only if it is an eligible target) and, after resolving those attacks, if one or more of those attacks hit that enemy unit, until the start of your next Shooting phase, that enemy unit is assailed (this simply labels that unit for the purposes of this ability and some Enhancements or Stratagems). If that unit is already assailed, until the start of your next Shooting phase, it is also pinned. While a unit is pinned, subtract 2\" from its Move characteristic and subtract 2 from Charge rolls made for it."
            },
            {
                "name": "Firebase Control (Aura)",
                "description": "While a friendly Leagues of Votann Infantry unit is wholly within 6\" of this Transport, ranged weapons equipped by models in that Infantry unit have the [sustained hits 1] ability."
            },
            {
                "name": "Saturation Rounds",
                "description": "This unit’s ranged attacks have [IGNORES COVER]."
            },
            {
                "name": "Optimised Attack Lines",
                "description": "This unit has MOBILE."
            }
        ]
    },
    "Uthar the Destined": {
        "stats": {
            "stat_movement": "5\"",
            "stat_toughness": 5,
            "stat_save": "3+",
            "stat_wounds": 5,
            "stat_leadership": "6+",
            "stat_oc": 1,
            "stat_invuln": "4+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Blade of the Ancestors",
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
                "name": "Volkanite disintegrator",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "3",
                "skill": "2+",
                "strength": "5",
                "ap": "0",
                "damage": "1",
                "keywords": "Devastating Wounds"
            }
        ],
        "abilities": [
            {
                "name": "Ancestral Fortune",
                "description": "Once per turn, you can spend 1YP to change one Hit roll, one Wound roll or one saving throw made for this model to an unmodified 6."
            },
            {
                "name": "Leader",
                "description": "This model can be attached to the following units:\n- Einhyr Hearthguard\n- Hearthkyn Warriors"
            },
            {
                "name": "Grim Efficiency",
                "description": "Once per battle round, when a friendly Leagues of Votann unit within 12\" of this model is targeted with a Stratagem, this model can use this ability. If it does, reduce the CP cost of that Stratagem by 1CP."
            },
            {
                "name": "Guerrilla Adepts",
                "description": "In your Shooting phase, just after this unit is selected to shoot, this unit can use this ability. If it does, select one enemy unit (excluding Monsters and Vehicles). Until the end of the phase, attacks made by models in this unit can only attack that enemy unit (and only if it is an eligible target) and, after resolving those attacks, if one or more of those attacks hit that enemy unit, until the start of your next Shooting phase, that enemy unit is assailed (this simply labels that unit for the purposes of this ability and some Enhancements or Stratagems). If that unit is already assailed, until the start of your next Shooting phase, it is also pinned. While a unit is pinned, subtract 2\" from its Move characteristic and subtract 2 from Charge rolls made for it."
            },
            {
                "name": "Rampart crest",
                "description": "While the bearer is leading a unit, models in that unit have a 5+ invulnerable save."
            }
        ]
    }
}


class Command(BaseCommand):
    """Refresh Leagues of Votann stat lines, weapon profiles, and abilities from BSData."""

    help = 'Refresh 11th Edition stats/weapons/abilities for Leagues of Votann units.'

    def add_arguments(self, parser):
        """Add --dry-run flag."""
        parser.add_argument(
            '--dry-run', action='store_true',
            help='Preview changes without writing to the database.',
        )

    def handle(self, *args, **options):
        """Iterate LEAGUES_OF_VOTANN_DATASHEETS and refresh each unit's datasheet data."""
        dry_run = options['dry_run']
        updated = 0
        skipped = 0

        with transaction.atomic():
            for name, payload in LEAGUES_OF_VOTANN_DATASHEETS.items():
                try:
                    unit = UnitType.objects.get(name=name, faction__name='Leagues of Votann')
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
