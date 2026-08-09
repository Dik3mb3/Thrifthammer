"""
Management command: seed_thousand_sons_datasheets

Refreshes stat lines, weapon profiles, and abilities for Thousand Sons
units using 11th Edition data sourced from BSData/wh40k-11e ("Chaos -
Thousand Sons.json") -- the same source used by
seed_thousand_sons_points.py.

Usage:
    python manage.py seed_thousand_sons_datasheets
    python manage.py seed_thousand_sons_datasheets --dry-run

Notes:
- Does NOT touch points_cost or category -- those are handled entirely by
  seed_thousand_sons_points.py. This command only refreshes stat_* fields,
  WeaponProfile rows, and UnitAbility rows.
- Scope is all 32 real-unit active Thousand Sons rows (excludes the
  Combat Patrol bundle and Tzaangor Upgrade Pack, neither of which is a
  deployable unit in BSData -- they simply aren\'t in this command\'s
  payload and get skipped).
- Per-field safety rule: a unit\'s stats/weapons/abilities are only
  overwritten when BSData actually has that data for it. If extraction
  found nothing, the existing DB value/rows are left untouched.
- All 32 real units resolved cleanly on the first pass -- 0 missing
  stats, weapons, or abilities, 0 overlong stat fields.
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from calculators.models import UnitAbility, UnitType, WeaponProfile

# (name -> {stats?, weapons?, abilities?}). Missing keys mean "no data
# found for this field -- leave existing DB data untouched."
THOUSAND_SONS_DATASHEETS = {
    "Blue Horrors and Brimstone Horrors": {
        "stats": {
            "stat_movement": "6\"",
            "stat_toughness": 3,
            "stat_save": "7+",
            "stat_wounds": 1,
            "stat_leadership": "8+",
            "stat_oc": 0,
            "stat_invuln": "4+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Coruscating Yellow flames (ref. only)",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "2",
                "skill": "5+",
                "strength": "2",
                "ap": "-1",
                "damage": "1",
                "keywords": "Pistol, Psychic"
            },
            {
                "name": "Yellow claws (ref. only)",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "2",
                "skill": "5+",
                "strength": "2",
                "ap": "0",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "Coruscating Blue flames",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "2",
                "skill": "4+",
                "strength": "3",
                "ap": "-1",
                "damage": "1",
                "keywords": "Pistol, Psychic"
            },
            {
                "name": "Blue claws",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "1",
                "skill": "5+",
                "strength": "3",
                "ap": "0",
                "damage": "1",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Split",
                "description": "Each time a Blue Horror model in this unit is destroyed, after the attacking unit has finished making its attacks, if this unit is not destroyed, roll one D6 for that model. On a 4+, add one Brimstone Horror model to this unit."
            },
            {
                "name": "Sullen Malevolence (Aura)",
                "description": "While an enemy unit is within 6\" of this unit, if this unit contains one or more Blue Horror models, worsen the Leadership characteristic of models in that enemy unit by 1."
            },
            {
                "name": "Exploding Horrors",
                "description": "Each time this unit is selected to fight, you can select one enemy unit within Engagement Range of it, then select one or more Brimstone Horror models in this unit. For each Brimstone Horror model you select, roll one D6: on a 4+, that model is destroyed and that enemy unit suffers 1 mortal wound."
            },
            {
                "name": "Daemonic Illusions (Aura)",
                "description": "While a friendly Thousand Sons Psyker unit is within 6\" of and visible to this unit, models in that unit have a 4+ invulnerable save against ranged attacks."
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
                "attacks": "6",
                "skill": "4+",
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
                "skill": "3+",
                "strength": "12",
                "ap": "-3",
                "damage": "D6+1",
                "keywords": "-"
            },
            {
                "name": "Havoc launcher",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "D6",
                "skill": "3+",
                "strength": "5",
                "ap": "0",
                "damage": "1",
                "keywords": "Blast"
            },
            {
                "name": "Twin inferno heavy bolter",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "3",
                "skill": "3+",
                "strength": "5",
                "ap": "-2",
                "damage": "2",
                "keywords": "Sustained Hits 1, Twin-linked"
            },
            {
                "name": "Inferno combi-bolter",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "2",
                "skill": "3+",
                "strength": "4",
                "ap": "-2",
                "damage": "1",
                "keywords": "Rapid Fire 2"
            },
            {
                "name": "Inferno combi-weapon",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "1",
                "skill": "4+",
                "strength": "4",
                "ap": "-2",
                "damage": "1",
                "keywords": "Anti-Infantry 4+, Devastating Wounds, Rapid Fire 1"
            }
        ],
        "abilities": [
            {
                "name": "Assault Ramp",
                "description": "Each time a unit disembarks from this Transport after it has made a Normal move, that unit is still eligible to declare a charge this turn."
            },
            {
                "name": "Damaged: 1-5 wounds remaining",
                "description": "While this model has 1-5 wounds remaining, each time this model makes an attack, subtract 1 from the Hit roll."
            },
            {
                "name": "Mortal Sorcery (Aura)",
                "description": "While a friendly Scintillating Legions Psyker unit from your army is within 6\" of and visible to this unit, that Scintillating Legions unit has the Cabal of Sorcerers ability."
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
                "skill": "3+",
                "strength": "14",
                "ap": "-3",
                "damage": "D6+1",
                "keywords": "Twin-linked"
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
                "name": "Havoc launcher",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "D6",
                "skill": "3+",
                "strength": "5",
                "ap": "0",
                "damage": "1",
                "keywords": "Blast"
            },
            {
                "name": "Inferno combi-bolter",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "2",
                "skill": "3+",
                "strength": "4",
                "ap": "-2",
                "damage": "1",
                "keywords": "Rapid Fire 2"
            },
            {
                "name": "Inferno combi-weapon",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "1",
                "skill": "4+",
                "strength": "4",
                "ap": "-2",
                "damage": "1",
                "keywords": "Anti-Infantry 4+, Devastating Wounds, Rapid Fire 1"
            },
            {
                "name": "Inferno heavy bolter",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "3",
                "skill": "3+",
                "strength": "5",
                "ap": "-2",
                "damage": "2",
                "keywords": "Sustained Hits 1"
            },
            {
                "name": "Lascannon",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "12",
                "ap": "-3",
                "damage": "D6+1",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Ensorcelled Annihilation",
                "description": "Each time this model makes a ranged attack that targets a Monster or Vehicle unit that was hit by one or more Psychic attacks made by a Thousand Sons Psyker unit from your army this turn, you can re-roll the Hit roll and you can re-roll the Damage roll."
            },
            {
                "name": "Mortal Sorcery (Aura)",
                "description": "While a friendly Scintillating Legions Psyker unit from your army is within 6\" of and visible to this unit, that Scintillating Legions unit has the Cabal of Sorcerers ability."
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
                "skill": "3+",
                "strength": "9",
                "ap": "-1",
                "damage": "3",
                "keywords": "Rapid Fire 2"
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
                "name": "Havoc launcher",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "D6",
                "skill": "3+",
                "strength": "5",
                "ap": "0",
                "damage": "1",
                "keywords": "Blast"
            },
            {
                "name": "Inferno combi-bolter",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "2",
                "skill": "3+",
                "strength": "4",
                "ap": "-2",
                "damage": "1",
                "keywords": "Rapid Fire 2"
            },
            {
                "name": "Inferno combi-weapon",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "1",
                "skill": "4+",
                "strength": "4",
                "ap": "-2",
                "damage": "1",
                "keywords": "Anti-Infantry 4+, Devastating Wounds, Rapid Fire 1"
            },
            {
                "name": "Inferno heavy bolter",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "3",
                "skill": "3+",
                "strength": "5",
                "ap": "-2",
                "damage": "2",
                "keywords": "Sustained Hits 1"
            },
            {
                "name": "Lascannon",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "12",
                "ap": "-3",
                "damage": "D6+1",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Ensorcelled Destruction",
                "description": "Each time this model makes a ranged attack that targets a unit (excluding Monsters and Vehicles) that was hit by one or more Psychic attacks made by a Thousand Sons Psyker unit from your army this turn, improve the Strength and Armour Penetration characteristic of that attack by 1."
            },
            {
                "name": "Mortal Sorcery (Aura)",
                "description": "While a friendly Scintillating Legions Psyker unit from your army is within 6\" of and visible to this unit, that Scintillating Legions unit has the Cabal of Sorcerers ability."
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
                "attacks": "3",
                "skill": "4+",
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
                "skill": "3+",
                "strength": "5",
                "ap": "0",
                "damage": "1",
                "keywords": "Blast"
            },
            {
                "name": "Inferno combi-bolter",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "2",
                "skill": "3+",
                "strength": "4",
                "ap": "-2",
                "damage": "1",
                "keywords": "Rapid Fire 2"
            },
            {
                "name": "Inferno combi-weapon",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "1",
                "skill": "4+",
                "strength": "4",
                "ap": "-2",
                "damage": "1",
                "keywords": "Anti-Infantry 4+, Devastating Wounds, Rapid Fire 1"
            }
        ],
        "abilities": [
            {
                "name": "Sorcerous Support",
                "description": "In your Shooting phase, after this model has shot, select one enemy unit hit by one or more of those attacks. Until the end of the phase, each time a friendly model that disembarked from this Transport this turn makes a Psychic attack that targets that enemy unit, add 1 to the Hit roll and add 1 to the Wound roll."
            },
            {
                "name": "Mortal Sorcery (Aura)",
                "description": "While a friendly Scintillating Legions Psyker unit from your army is within 6\" of and visible to this unit, that Scintillating Legions unit has the Cabal of Sorcerers ability."
            }
        ]
    },
    "Chaos Spawn": {
        "stats": {
            "stat_movement": "8\"",
            "stat_toughness": 5,
            "stat_save": "4+",
            "stat_wounds": 4,
            "stat_leadership": "7+",
            "stat_oc": 1,
            "stat_invuln": "5+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Hideous Mutations",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "D6+2",
                "skill": "4+",
                "strength": "5",
                "ap": "-1",
                "damage": "2"
            }
        ],
        "abilities": [
            {
                "name": "Regenerating Monstrosities",
                "description": "At the start of each player\u2019s Command phase, one model in this unit regains up to 3 lost wounds."
            },
            {
                "name": "Mortal Sorcery (Aura)",
                "description": "While a friendly Scintillating Legions Psyker unit from your army is within 6\" of and visible to this unit, that Scintillating Legions unit has the Cabal of Sorcerers ability."
            }
        ]
    },
    "Chaos Vindicator": {
        "stats": {
            "stat_movement": "9\"",
            "stat_toughness": 11,
            "stat_save": "2+",
            "stat_wounds": 11,
            "stat_leadership": "6+",
            "stat_oc": 3,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Demolisher cannon",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "D6+3",
                "skill": "3+",
                "strength": "14",
                "ap": "-3",
                "damage": "D6",
                "keywords": "Blast"
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
                "name": "Havoc launcher",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "D6",
                "skill": "3+",
                "strength": "5",
                "ap": "0",
                "damage": "1",
                "keywords": "Blast"
            },
            {
                "name": "Inferno combi-bolter",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "2",
                "skill": "3+",
                "strength": "4",
                "ap": "-2",
                "damage": "1",
                "keywords": "Rapid Fire 2"
            },
            {
                "name": "Inferno combi-weapon",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "1",
                "skill": "4+",
                "strength": "4",
                "ap": "-2",
                "damage": "1",
                "keywords": "Anti-Infantry 4+, Devastating Wounds, Rapid Fire 1"
            }
        ],
        "abilities": [
            {
                "name": "Siege Shield",
                "description": "When making ranged attacks with its demolisher cannon, this model can target enemy units within Engagement Range of it (provided no other friendly units are also within Engagement Range of that enemy unit). In addition, when making ranged attacks, this model does not suffer the penalty to its Hit rolls for being within Engagement Range of one or more enemy units."
            },
            {
                "name": "Mortal Sorcery (Aura)",
                "description": "While a friendly Scintillating Legions Psyker unit from your army is within 6\" of and visible to this unit, that Scintillating Legions unit has the Cabal of Sorcerers ability."
            }
        ]
    },
    "Daemon Prince of Tzeentch": {
        "stats": {
            "stat_movement": "9\"",
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
                "name": "Dark Blessing",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "9",
                "skill": "2+",
                "strength": "4",
                "ap": "-1",
                "damage": "1",
                "keywords": "Ignores Cover, Psychic, Sustained Hits 1"
            },
            {
                "name": "\u27a4 Hellforged weapons - strike",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "6",
                "skill": "2+",
                "strength": "8",
                "ap": "-2",
                "damage": "3",
                "keywords": "Devastating Wounds, Psychic"
            },
            {
                "name": "\u27a4 Hellforged weapons - sweep",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "12",
                "skill": "2+",
                "strength": "6",
                "ap": "-1",
                "damage": "1",
                "keywords": "Devastating Wounds, Psychic"
            },
            {
                "name": "Infernal cannon",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "3",
                "skill": "2+",
                "strength": "5",
                "ap": "-2",
                "damage": "2",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Spirit Snare",
                "description": "Each time a friendly Thousand Sons Psyker model with the Cabal of Sorcerers ability is destroyed while within 9\" of one or more models with this ability, select one of those models with this ability: until the end of the battle, each time the selected model attempts a Ritual, add 1 to the Psychic test result (to a maximum of +2)."
            },
            {
                "name": "Servile Pawns",
                "description": "While this model is within 3\" of one or more friendly Thousand Sons Infantry units, this model has the Lone Operative ability."
            },
            {
                "name": "Glamour of Tzeentch (Aura, Psychic)",
                "description": "While a friendly Thousand Sons Infantry unit is within 6\" of this model, models in that unit have the Stealth ability."
            },
            {
                "name": "Mortal Sorcery (Aura)",
                "description": "While a friendly Scintillating Legions Psyker unit from your army is within 6\" of and visible to this unit, that Scintillating Legions unit has the Cabal of Sorcerers ability."
            }
        ]
    },
    "Daemon Prince of Tzeentch with wings": {
        "stats": {
            "stat_movement": "13\"",
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
                "name": "Dark Blessing",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "9",
                "skill": "2+",
                "strength": "4",
                "ap": "-1",
                "damage": "1",
                "keywords": "Ignores Cover, Psychic, Sustained Hits 1"
            },
            {
                "name": "\u27a4 Hellforged weapons - strike",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "6",
                "skill": "2+",
                "strength": "8",
                "ap": "-2",
                "damage": "3",
                "keywords": "Devastating Wounds, Psychic"
            },
            {
                "name": "\u27a4 Hellforged weapons - sweep",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "12",
                "skill": "2+",
                "strength": "6",
                "ap": "-1",
                "damage": "1",
                "keywords": "Devastating Wounds, Psychic"
            },
            {
                "name": "Infernal cannon",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "3",
                "skill": "2+",
                "strength": "5",
                "ap": "-2",
                "damage": "2",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Aetherstride (Psychic)",
                "description": "In your Movement phase, when this model is set up on the battlefield using the Deep Strike ability, it can perform an aetherstride. If it does:\n- It can be set up anywhere on the battlefield more than 6\" horizontally away from all enemy units.\n- Until the end of the turn, its Dark Blessing has the [Sustained Hits D3] ability.\n- Until the end of the turn, it is not eligible to declare a charge."
            },
            {
                "name": "Hunter of Souls",
                "description": "Each time this model makes an attack that targets a Character unit, re-roll a Hit roll of 1 and re-roll a Wound roll of 1 (if that attack targets a Psyker Character unit, you can re-roll the Hit roll and you can re-roll the Wound roll instead). Each time this model destroys a Character unit, this model regains up to D3 lost wounds (if that Character unit was a Psyker, this model regains up to 3 lost wounds instead)."
            },
            {
                "name": "Mortal Sorcery (Aura)",
                "description": "While a friendly Scintillating Legions Psyker unit from your army is within 6\" of and visible to this unit, that Scintillating Legions unit has the Cabal of Sorcerers ability."
            }
        ]
    },
    "Defiler": {
        "stats": {
            "stat_movement": "12\"",
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
                "attacks": "5",
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
                "attacks": "10",
                "skill": "3+",
                "strength": "6",
                "ap": "-2",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "\u27a4 Heavy missile launcher - frag",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "2D6",
                "skill": "3+",
                "strength": "5",
                "ap": "-1",
                "damage": "1",
                "keywords": "Blast"
            },
            {
                "name": "\u27a4 Heavy missile launcher - krak",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "2",
                "skill": "3+",
                "strength": "10",
                "ap": "-2",
                "damage": "D6+1",
                "keywords": "-"
            },
            {
                "name": "Electroscourge",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "5",
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
                "skill": "3+",
                "strength": "12",
                "ap": "-3",
                "damage": "D6+1",
                "keywords": "-"
            },
            {
                "name": "Heavy reaper autocannon",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "4",
                "skill": "3+",
                "strength": "9",
                "ap": "-2",
                "damage": "3",
                "keywords": "Devastating Wounds, Sustained Hits 1"
            },
            {
                "name": "Hades battle cannon",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "D6+3",
                "skill": "3+",
                "strength": "10",
                "ap": "-1",
                "damage": "3",
                "keywords": "Blast"
            },
            {
                "name": "Ectoplasma destructor",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "D6",
                "skill": "3+",
                "strength": "12",
                "ap": "-3",
                "damage": "3",
                "keywords": "Blast"
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
                "skill": "3+",
                "strength": "6",
                "ap": "-2",
                "damage": "2",
                "keywords": "-"
            },
            {
                "name": "Pyraflux magma cutter",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "2",
                "skill": "3+",
                "strength": "10",
                "ap": "-4",
                "damage": "D6",
                "keywords": "Melta 2"
            }
        ],
        "abilities": [
            {
                "name": "Scuttling Walker",
                "description": "Each time this unit makes a Normal, Advance or Fall Back move, it can move through models (excluding Titanic models) and terrain features. When doing so, it can move within Engagement Range of enemy models, but cannot end that move within Engagement Range of them, and any Desperate Escape test is automatically passed."
            },
            {
                "name": "Destroyer of Futures (Once per phase, per unit)",
                "description": "You can target this unit with the Counteroffensive stratagem, regardless of any other uses of that stratagem this phase. If you do:\n- That use is -1 CP.\n- That use does not prevent any uses of that stratagem on other units this phase.'"
            }
        ]
    },
    "Exalted Sorcerer": {
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
                "name": "Astral Blast",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "D6",
                "skill": "2+",
                "strength": "6",
                "ap": "-2",
                "damage": "D3",
                "keywords": "Blast, Devastating Wounds, Psychic"
            },
            {
                "name": "Prosperine khopesh",
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
                "name": "Force weapon",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "3+",
                "strength": "6",
                "ap": "-1",
                "damage": "D3",
                "keywords": "Psychic"
            },
            {
                "name": "Inferno bolt pistol",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "1",
                "skill": "2+",
                "strength": "4",
                "ap": "-1",
                "damage": "1",
                "keywords": "Pistol"
            }
        ],
        "abilities": [
            {
                "name": "Arcane Shield (Psychic)",
                "description": "While this model is leading a unit, models in that unit have a 4+ invulnerable save."
            },
            {
                "name": "Rebind Rubricae (Psychic)",
                "description": "In your Command phase, if this model is leading a unit, you can roll one D6: on a 1, that unit suffers D3 mortal wounds; on a 2-5, you can return 1 destroyed Bodyguard model to that unit; on a 6, you can return up to 2 destroyed Bodyguard models to that unit."
            },
            {
                "name": "Leader",
                "description": "This model can be attached to the following unit: Rubric Marines"
            },
            {
                "name": "Mortal Sorcery (Aura)",
                "description": "While a friendly Scintillating Legions Psyker unit from your army is within 6\" of and visible to this unit, that Scintillating Legions unit has the Cabal of Sorcerers ability."
            }
        ]
    },
    "Exalted Sorcerer on Disc of Tzeentch": {
        "stats": {
            "stat_movement": "10\"",
            "stat_toughness": 4,
            "stat_save": "3+",
            "stat_wounds": 6,
            "stat_leadership": "6+",
            "stat_oc": 2,
            "stat_invuln": "4+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Arcane Fire",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "D6",
                "skill": "N/A",
                "strength": "6",
                "ap": "-2",
                "damage": "D3",
                "keywords": "Ignores Cover, Psychic, Torrent"
            },
            {
                "name": "Prosperine khopesh",
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
                "name": "Force weapon",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "3+",
                "strength": "6",
                "ap": "-1",
                "damage": "D3",
                "keywords": "Psychic"
            },
            {
                "name": "Inferno bolt pistol",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "1",
                "skill": "2+",
                "strength": "4",
                "ap": "-1",
                "damage": "1",
                "keywords": "Pistol"
            }
        ],
        "abilities": [
            {
                "name": "Arcane Shield (Psychic)",
                "description": "While this model is leading a unit, that unit can only be selected as the target of a ranged attack if the attacking model is within 18\"."
            },
            {
                "name": "Binding Tendrils (Psychic)",
                "description": "In your Shooting phase, after this model has shot, select one enemy Infantry unit hit by one or more of those attacks made with Arcane Fire. Until the start of your next turn, that unit is ensnared. While a unit is ensnared, subtract 2\" from its Move characteristic and subtract 2 from Charge rolls made for it."
            },
            {
                "name": "Leader",
                "description": "This model can be attached to the following unit: Rubric Marines, Tzaangor Enlightened"
            },
            {
                "name": "Mortal Sorcery (Aura)",
                "description": "While a friendly Scintillating Legions Psyker unit from your army is within 6\" of and visible to this unit, that Scintillating Legions unit has the Cabal of Sorcerers ability."
            }
        ]
    },
    "Flamers of Tzeentch": {
        "stats": {
            "stat_movement": "9\"",
            "stat_toughness": 4,
            "stat_save": "7+",
            "stat_wounds": 3,
            "stat_leadership": "7+",
            "stat_oc": 1,
            "stat_invuln": "4+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Flamer mouths",
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
                "name": "Flickering flames",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "D6",
                "skill": "N/A",
                "strength": "4",
                "ap": "-1",
                "damage": "1",
                "keywords": "Ignores Cover, Psychic, Torrent"
            }
        ],
        "abilities": [
            {
                "name": "Bounding Leaps",
                "description": "This unit is eligible to shoot in a turn in which it Fell Back."
            },
            {
                "name": "Daemonic Illusions (Aura)",
                "description": "While a friendly Thousand Sons Psyker unit is within 6\" of and visible to this unit, models in that unit have a 4+ invulnerable save against ranged attacks."
            }
        ]
    },
    "Forgefiend": {
        "stats": {
            "stat_movement": "8\"",
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
                "skill": "3+",
                "strength": "10",
                "ap": "-3",
                "damage": "3",
                "keywords": "Blast"
            },
            {
                "name": "Hades autocannon",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "6",
                "skill": "3+",
                "strength": "8",
                "ap": "-2",
                "damage": "2",
                "keywords": "-"
            },
            {
                "name": "Forgefiend claws",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "3",
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
                "attacks": "5",
                "skill": "3+",
                "strength": "7",
                "ap": "0",
                "damage": "2",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Blazing Salvos",
                "description": "In your Shooting phase, after this model has shot, select one enemy unit that was hit by one or more of those attacks. Until the start of your next turn, that enemy unit is suppressed. While a unit is suppressed, each time a model in that unit makes an attack, subtract 1 from the hit roll."
            },
            {
                "name": "Mortal Sorcery (Aura)",
                "description": "While a friendly Scintillating Legions Psyker unit from your army is within 6\" of and visible to this unit, that Scintillating Legions unit has the Cabal of Sorcerers ability."
            }
        ]
    },
    "Helbrute": {
        "stats": {
            "stat_movement": "8\"",
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
                "name": "Close combat weapon",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "5",
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
                "attacks": "5",
                "skill": "3+",
                "strength": "12",
                "ap": "-2",
                "damage": "3",
                "keywords": "-"
            },
            {
                "name": "Inferno combi-bolter",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "2",
                "skill": "3+",
                "strength": "4",
                "ap": "-2",
                "damage": "1",
                "keywords": "Rapid Fire 2"
            },
            {
                "name": "Heavy flamer",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "D6",
                "skill": "N/A",
                "strength": "5",
                "ap": "-2",
                "damage": "1",
                "keywords": "Ignores Cover, Torrent"
            },
            {
                "name": "\u27a4 Missile launcher - frag",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "D6",
                "skill": "3+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Blast"
            },
            {
                "name": "\u27a4 Missile launcher - krak",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "9",
                "ap": "-2",
                "damage": "D6",
                "keywords": "-"
            },
            {
                "name": "Helbrute hammer",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "5",
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
                "attacks": "8",
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
                "skill": "3+",
                "strength": "9",
                "ap": "-4",
                "damage": "D6",
                "keywords": "Melta 2"
            },
            {
                "name": "Twin autocannon",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "2",
                "skill": "3+",
                "strength": "9",
                "ap": "-1",
                "damage": "3",
                "keywords": "Twin-linked"
            },
            {
                "name": "Helbrute plasma cannon",
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
                "name": "Twin inferno heavy bolter",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "3",
                "skill": "3+",
                "strength": "5",
                "ap": "-2",
                "damage": "2",
                "keywords": "Sustained Hits 1, Twin-linked"
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
            }
        ],
        "abilities": [
            {
                "name": "Terrifying Assault",
                "description": "In your Shooting phase and the Fight phase, after this model has shot, select one enemy unit hit by one or more of those attacks. That unit must take a Battle-shock test, subtracting 1 if that unit is within 9\" of one or more Thousand Sons Psyker units from your army."
            },
            {
                "name": "Devoted to Destruction",
                "description": "If this model is equipped with 2 melee weapons in addition to its close combat weapon, add 2 to the Attacks characteristic of those two weapons."
            },
            {
                "name": "Mortal Sorcery (Aura)",
                "description": "While a friendly Scintillating Legions Psyker unit from your army is within 6\" of and visible to this unit, that Scintillating Legions unit has the Cabal of Sorcerers ability."
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
                "attacks": "5",
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
                "ap": "-2",
                "damage": "2",
                "keywords": "Ignores Cover, Torrent"
            },
            {
                "name": "Hades autocannon",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "6",
                "skill": "3+",
                "strength": "8",
                "ap": "-2",
                "damage": "2",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Flame-wreathed",
                "description": "Each time this model ends a Normal move, select one enemy unit it moved over during that move. Until the end of the turn, models in that unit cannot have the Benefit of Cover."
            },
            {
                "name": "Mortal Sorcery (Aura)",
                "description": "While a friendly Scintillating Legions Psyker unit from your army is within 6\" of and visible to this unit, that Scintillating Legions unit has the Cabal of Sorcerers ability."
            }
        ]
    },
    "Kairos Fateweaver": {
        "stats": {
            "stat_movement": "12\"",
            "stat_toughness": 10,
            "stat_save": "6+",
            "stat_wounds": 20,
            "stat_leadership": "6+",
            "stat_oc": 5,
            "stat_invuln": "4+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "\u27a4 Infernal Gateway - witchfire",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "D6+3",
                "skill": "2+",
                "strength": "9",
                "ap": "-2",
                "damage": "D3",
                "keywords": "Blast, Indirect Fire, Psychic"
            },
            {
                "name": "\u27a4 Infernal Gateway - focused witchfire",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "D3+6",
                "skill": "2+",
                "strength": "9",
                "ap": "-2",
                "damage": "3",
                "keywords": "Blast, Hazardous, Indirect Fire, Psychic"
            },
            {
                "name": "Staff of Tomorrow",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "5",
                "skill": "3+",
                "strength": "8",
                "ap": "-2",
                "damage": "2D3",
                "keywords": "Psychic"
            }
        ],
        "abilities": [
            {
                "name": "One Head Looks Forward",
                "description": "At the end of your Command phase, if this model is on the battlefield, take a Leadership test for this model; if that test is passed, you gain 1CP."
            },
            {
                "name": "One Head Looks Back (Aura)",
                "description": "Once per turn, when your opponent targets a unit from their army within 12\" of this model with a stratagem, you can use this ability. If you do, increase the CP cost of that use of that stratagem by 1CP"
            },
            {
                "name": "Damaged: 1-7 wounds remaining",
                "description": "While this model has 1-7 wounds remaining, each time this model makes an attack, subtract 1 from the Hit roll."
            },
            {
                "name": "Daemonic Illusions (Aura)",
                "description": "While a friendly Thousand Sons Psyker unit is within 6\" of and visible to this unit, models in that unit have a 4+ invulnerable save against ranged attacks."
            }
        ]
    },
    "Lord of Change": {
        "stats": {
            "stat_movement": "12\"",
            "stat_toughness": 10,
            "stat_save": "6+",
            "stat_wounds": 18,
            "stat_leadership": "6+",
            "stat_oc": 5,
            "stat_invuln": "4+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "\u27a4 Bolt of Change - witchfire",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "9",
                "skill": "2+",
                "strength": "9",
                "ap": "-1",
                "damage": "1",
                "keywords": "Psychic"
            },
            {
                "name": "\u27a4 Bolt of Change - focused witchfire",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "9",
                "skill": "2+",
                "strength": "9",
                "ap": "-2",
                "damage": "3",
                "keywords": "Hazardous, Psychic"
            },
            {
                "name": "Staff of Tzeentch",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "5",
                "skill": "3+",
                "strength": "6",
                "ap": "-1",
                "damage": "3",
                "keywords": "Psychic"
            },
            {
                "name": "Rod of sorcery",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "6",
                "skill": "2+",
                "strength": "8",
                "ap": "-1",
                "damage": "2",
                "keywords": "Psychic"
            },
            {
                "name": "Baleful sword",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "3",
                "skill": "3+",
                "strength": "7",
                "ap": "-2",
                "damage": "3",
                "keywords": "Extra Attacks"
            }
        ],
        "abilities": [
            {
                "name": "Damaged: 1-7 wounds remaining",
                "description": "While this model has 1-7 wounds remaining, each time this model makes an attack, subtract 1 from the Hit roll."
            },
            {
                "name": "Daemon Lord of Tzeentch (Aura)",
                "description": "While a friendly Scintillating Legions unit is within 6\" of this model, each time a model in that unit makes a ranged attack, add 1 to the Strength characteristic of that attack."
            },
            {
                "name": "Master of Magicks (Aura)",
                "description": "In your Shooting phase, select one of the following abilities: [Ignores Cover], [Lethal Hits], [Sustained Hits D3]. Until the end of the phase, this model's Bolt of Change has that ability."
            },
            {
                "name": "Daemonic Illusions (Aura)",
                "description": "While a friendly Thousand Sons Psyker unit is within 6\" of and visible to this unit, models in that unit have a 4+ invulnerable save against ranged attacks."
            }
        ]
    },
    "Maulerfiend": {
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
                "name": "Maulerfiend fists",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "6",
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
                "skill": "3+",
                "strength": "9",
                "ap": "-4",
                "damage": "D6",
                "keywords": "Melta 2"
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
                "name": "Snarling Protector",
                "description": "You can target this unit with the Heroic Intervention stratagem, regardless of any other uses of that stratagem this phase. If you do:\n- That use is -1 CP.\n- That use does not prevent any uses of that stratagem on other units this phase.\n- When this unit declares a charge, if a friendly engaged PSYKER unit is within 12\" of this unit, you can use this part of this ability.\nIf you do:\n- This unit can re-roll that charge roll.\n- This unit must end that charge move engaged with an enemy unit engaged with that friendly PSYKER unit."
            },
            {
                "name": "Mortal Sorcery (Aura)",
                "description": "While a friendly Scintillating Legions Psyker unit from your army is within 6\" of and visible to this unit, that Scintillating Legions unit has the Cabal of Sorcerers ability."
            }
        ]
    },
    "Mutalith Vortex Beast": {
        "stats": {
            "stat_movement": "10\"",
            "stat_toughness": 10,
            "stat_save": "4+",
            "stat_wounds": 13,
            "stat_leadership": "6+",
            "stat_oc": 4,
            "stat_invuln": "5+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Betentacled maw",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "15",
                "skill": "3+",
                "strength": "7",
                "ap": "0",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "Mutalith claws",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "5",
                "skill": "3+",
                "strength": "10",
                "ap": "-2",
                "damage": "3",
                "keywords": "-"
            },
            {
                "name": "\u27a4 Warp vortex - blast",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "D6+3",
                "skill": "3+",
                "strength": "9",
                "ap": "-2",
                "damage": "2",
                "keywords": "Blast"
            },
            {
                "name": "\u27a4 Warp vortex - beam",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "18",
                "ap": "-3",
                "damage": "D6+6",
                "keywords": "Devastating Wounds"
            },
            {
                "name": "\u27a4 Warp vortex - torrent",
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
                "name": "Mutating Vortex (Aura)",
                "description": "At the end of your Movement phase, roll one D6 for each enemy unit within 6\" of this model: on a 2-3, that unit suffers 1 mortal wound; on a 4-5, that unit suffers D3 mortal wounds; on a 6, that unit suffers D6 mortal wounds. Each enemy unit within range of this ability must then take a Battle-shock test."
            },
            {
                "name": "Immaterial Flare (Aura)",
                "description": "While a friendly Thousand Sons Psyker model is within 6\" of this model, each time that model Channels the Warp, add 1 to the Psychic test result. This is not cumulative with any other modifiers to the Psychic test result."
            },
            {
                "name": "Mortal Sorcery (Aura)",
                "description": "While a friendly Scintillating Legions Psyker unit from your army is within 6\" of and visible to this unit, that Scintillating Legions unit has the Cabal of Sorcerers ability."
            }
        ]
    },
    "Pink Horrors of Tzeentch": {
        "stats": {
            "stat_movement": "6\"",
            "stat_toughness": 3,
            "stat_save": "7+",
            "stat_wounds": 1,
            "stat_leadership": "8+",
            "stat_oc": 0,
            "stat_invuln": "4+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Blue claws (ref. only)",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "1",
                "skill": "5+",
                "strength": "3",
                "ap": "0",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "Coruscating blue flames (ref. only)",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "2",
                "skill": "4+",
                "strength": "3",
                "ap": "-1",
                "damage": "1",
                "keywords": "Pistol, Psychic"
            },
            {
                "name": "Coruscating yellow flames (ref. only)",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "2",
                "skill": "5+",
                "strength": "2",
                "ap": "-1",
                "damage": "1",
                "keywords": "Pistol, Psychic"
            },
            {
                "name": "Yellow claws (ref. only)",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "2",
                "skill": "5+",
                "strength": "2",
                "ap": "0",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "Coruscating pink flames",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "2",
                "skill": "3+",
                "strength": "4",
                "ap": "-1",
                "damage": "1",
                "keywords": "Pistol, Psychic"
            },
            {
                "name": "Pink claws",
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
                "name": "Split",
                "description": "Each time a Pink Horror or Blue Horror model in this unit is destroyed, after the attacking unit has finished making its attacks, if this unit is not destroyed, roll one D6 for that model. On a 4+, if it was a Pink Horror, add 2 Blue Horror models to this unit and if it was a Blue Horror, add one Brimstone Horror model to this unit."
            },
            {
                "name": "Horrors are Pink. Horrors are Blue. Where once there was one, now there are two.",
                "description": "If, at any point, this unit contains no Pink Horrors models, use the Blue Horrors datasheet for this unit.\n\n_Designer\u2019s Note: While this unit contains one or more Pink Horrors models, the Sullen Malevolence and Exploding Horrors abilities from the Blue Horrors datasheet do not apply to this unit._"
            },
            {
                "name": "Daemonic Illusions (Aura)",
                "description": "While a friendly Thousand Sons Psyker unit is within 6\" of and visible to this unit, models in that unit have a 4+ invulnerable save against ranged attacks."
            },
            {
                "name": "Daemonic Icon",
                "description": "Models in the bearer's unit have a Leadership characteristic of 6+"
            },
            {
                "name": "Instrument of Chaos",
                "description": "Add 1 to Charge rolls made for the bearer's unit."
            }
        ]
    },
    "Screamers of Tzeentch": {
        "stats": {
            "stat_movement": "14\"",
            "stat_toughness": 4,
            "stat_save": "6+",
            "stat_wounds": 3,
            "stat_leadership": "7+",
            "stat_oc": 1,
            "stat_invuln": "4+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Lamprey bite",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "3",
                "skill": "3+",
                "strength": "6",
                "ap": "-2",
                "damage": "2",
                "keywords": "Anti-MONSTER 4+, Anti-VEHICLE 4+"
            }
        ],
        "abilities": [
            {
                "name": "Slashing Dive",
                "description": "In your Movement phase, after this unit ends a Normal move, select one enemy unit it moved over during that move and roll one D6 for each model in this unit: for each 4+, that enemy unit suffers 1 mortal wound."
            },
            {
                "name": "Daemonic Illusions (Aura)",
                "description": "While a friendly Thousand Sons Psyker unit is within 6\" of and visible to this unit, models in that unit have a 4+ invulnerable save against ranged attacks."
            }
        ]
    },
    "Thousand Sons Ahriman": {
        "stats": {
            "stat_movement": "10\"",
            "stat_toughness": 4,
            "stat_save": "3+",
            "stat_wounds": 6,
            "stat_leadership": "6+",
            "stat_oc": 2,
            "stat_invuln": "4+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Transmogrifying Blast",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "D6+1",
                "skill": "2+",
                "strength": "6",
                "ap": "-1",
                "damage": "D3",
                "keywords": "Blast, Psychic"
            },
            {
                "name": "Black Staff of Ahriman",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "5",
                "skill": "2+",
                "strength": "7",
                "ap": "-1",
                "damage": "3",
                "keywords": "Psychic"
            },
            {
                "name": "Inferno bolt pistol",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "1",
                "skill": "2+",
                "strength": "4",
                "ap": "-1",
                "damage": "1",
                "keywords": "Pistol"
            }
        ],
        "abilities": [
            {
                "name": "Scryer of Fates (Psychic)",
                "description": "if your army includes this model, after both players have deployed their armies, you can select up to 3 Thousand Sons units from your army and redeploy them. When doing so, you can set those units up in Strategic Reserves if you wish, regardless of how many units are already in Strategic Reserves."
            },
            {
                "name": "Arch-Sorcerer of Tzeentch (Psychic)",
                "description": "Each time this model attempts a Ritual, add 1 to the Psychic test result."
            },
            {
                "name": "Leader",
                "description": "This model can be attached to the following unit: Rubric Marines, Tzaangor Enlightened, Tzaangor Enlightened with Fatecaster Greatbows"
            },
            {
                "name": "Mortal Sorcery (Aura)",
                "description": "While a friendly Scintillating Legions Psyker unit from your army is within 6\" of and visible to this unit, that Scintillating Legions unit has the Cabal of Sorcerers ability."
            }
        ]
    },
    "Thousand Sons Infernal Master": {
        "stats": {
            "stat_movement": "6\"",
            "stat_toughness": 4,
            "stat_save": "3+",
            "stat_wounds": 4,
            "stat_leadership": "6+",
            "stat_oc": 1,
            "stat_invuln": "5+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "\u27a4 Fires of the Abyss - witchfire",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "D6",
                "skill": "N/A",
                "strength": "6",
                "ap": "-2",
                "damage": "1",
                "keywords": "Psychic, Torrent"
            },
            {
                "name": "\u27a4 Fires of the Abyss - focused witchfire",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "2D6",
                "skill": "N/A",
                "strength": "6",
                "ap": "-2",
                "damage": "1",
                "keywords": "Hazardous, Psychic, Torrent"
            },
            {
                "name": "Force weapon",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "3+",
                "strength": "6",
                "ap": "-1",
                "damage": "D3",
                "keywords": "Psychic"
            },
            {
                "name": "Inferno bolt pistol",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "1",
                "skill": "2+",
                "strength": "4",
                "ap": "-1",
                "damage": "1",
                "keywords": "Pistol"
            }
        ],
        "abilities": [
            {
                "name": "Malefic Maelstrom (Psychic)",
                "description": "While this model is leading a unit, weapons equipped by models in that unit have the [SUSTAINED HITS 1] ability."
            },
            {
                "name": "Glimpse of Eternity (Psychic)",
                "description": "Once per turn, you can change the result of one Hit roll, one Wound roll or one saving throw made for this model to an unmodified 6."
            },
            {
                "name": "Leader",
                "description": "This model can be attached to the following unit: Rubric Marines"
            },
            {
                "name": "Mortal Sorcery (Aura)",
                "description": "While a friendly Scintillating Legions Psyker unit from your army is within 6\" of and visible to this unit, that Scintillating Legions unit has the Cabal of Sorcerers ability."
            }
        ]
    },
    "Thousand Sons Magnus the Red": {
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
                "name": "Gaze of Magnus",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "3D3",
                "skill": "2+",
                "strength": "11",
                "ap": "-2",
                "damage": "3",
                "keywords": "Devastating Wounds, Psychic"
            },
            {
                "name": "\u27a4 Blade of Magnus - strike",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "7",
                "skill": "2+",
                "strength": "16",
                "ap": "-3",
                "damage": "3",
                "keywords": "Devastating Wounds, Psychic"
            },
            {
                "name": "\u27a4 Blade of Magnus - sweep",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "14",
                "skill": "2+",
                "strength": "8",
                "ap": "-1",
                "damage": "2",
                "keywords": "Psychic"
            },
            {
                "name": "Tzeentch's Firestorm",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "D6+3",
                "skill": "2+",
                "strength": "6",
                "ap": "-1",
                "damage": "2",
                "keywords": "Blast, Ignores Cover, Psychic"
            }
        ],
        "abilities": [
            {
                "name": "Damaged: 1-6 wounds remaining",
                "description": "While this model has 1-6 wounds remaining, each time this model makes an attack, subtract 1 from the Hit roll."
            },
            {
                "name": "Unearthly Power",
                "description": "At the start of the battle round, select one of the abilities in the Crimson King section. Until the start of the next battle round, this model has that ability."
            },
            {
                "name": "Lord of the Planet of the Sorcerers (Psychic)",
                "description": "This model can attempt up to 2 Rituals per turn instead of one, and each time this model attempts a Ritual, add 2 to the Psychic test result."
            },
            {
                "name": "Mortal Sorcery (Aura)",
                "description": "While a friendly Scintillating Legions Psyker unit from your army is within 6\" of and visible to this unit, that Scintillating Legions unit has the Cabal of Sorcerers ability."
            }
        ]
    },
    "Thousand Sons Rubric Marines": {
        "stats": {
            "stat_movement": "6\"",
            "stat_toughness": 4,
            "stat_save": "3+",
            "stat_wounds": 2,
            "stat_leadership": "7+",
            "stat_oc": 2,
            "stat_invuln": "5+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Force weapon",
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
                "name": "Malefic Curse",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "3",
                "skill": "3+",
                "strength": "4",
                "ap": "-3",
                "damage": "1",
                "keywords": "Anti-INFANTRY 4+, Devastating Wounds, Psychic"
            },
            {
                "name": "Inferno bolt pistol",
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
                "name": "Warpflame pistol",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "D6",
                "skill": "N/A",
                "strength": "3",
                "ap": "-1",
                "damage": "1",
                "keywords": "Ignores Cover, Pistol, Torrent"
            },
            {
                "name": "Inferno boltgun",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "2",
                "skill": "3+",
                "strength": "4",
                "ap": "-2",
                "damage": "1",
                "keywords": "-"
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
                "name": "Warpflamer",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "D6",
                "skill": "N/A",
                "strength": "4",
                "ap": "-1",
                "damage": "1",
                "keywords": "Ignores Cover, Torrent"
            },
            {
                "name": "Soulreaper cannon",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "6",
                "skill": "3+",
                "strength": "6",
                "ap": "-2",
                "damage": "1",
                "keywords": "Devastating Wounds"
            }
        ],
        "abilities": [
            {
                "name": "Bringers of Change",
                "description": "Each time a model in this unit makes a ranged attack, re-roll a Wound roll of 1. If the attack targets a unit within range of an objective marker you do not control, you can re-roll the Wound roll instead."
            },
            {
                "name": "Mortal Sorcery (Aura)",
                "description": "While a friendly Scintillating Legions Psyker unit from your army is within 6\" of and visible to this unit, that Scintillating Legions unit has the Cabal of Sorcerers ability."
            },
            {
                "name": "Icon of Flame",
                "description": "Ranged weapons equipped by models in the bearer's unit (excluding Characters) have the [Ignores Cover] ability."
            }
        ]
    },
    "Thousand Sons Scarab Occult Terminators": {
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
                "name": "Force weapon",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "3+",
                "strength": "6",
                "ap": "-1",
                "damage": "D3",
                "keywords": "Psychic"
            },
            {
                "name": "Malefic Curse",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "3",
                "skill": "3+",
                "strength": "4",
                "ap": "-3",
                "damage": "1",
                "keywords": "Anti-INFANTRY 4+, Devastating Wounds, Psychic"
            },
            {
                "name": "Prosperine khopesh",
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
                "name": "Inferno combi-bolter",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "2",
                "skill": "3+",
                "strength": "4",
                "ap": "-2",
                "damage": "1",
                "keywords": "Rapid Fire 2"
            },
            {
                "name": "Hellfyre missile rack",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "2",
                "skill": "3+",
                "strength": "10",
                "ap": "-2",
                "damage": "3",
                "keywords": "-"
            },
            {
                "name": "Heavy warpflamer",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "D6",
                "skill": "N/A",
                "strength": "5",
                "ap": "-2",
                "damage": "1",
                "keywords": "Ignores Cover, Torrent"
            },
            {
                "name": "Soulreaper cannon",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "6",
                "skill": "3+",
                "strength": "6",
                "ap": "-2",
                "damage": "1",
                "keywords": "Devastating Wounds"
            }
        ],
        "abilities": [
            {
                "name": "Rites of Coalescence",
                "description": "While this unit contains one or more Psyker models, each time an attack targets this unit, subtract 1 from the\nWound roll."
            },
            {
                "name": "Mortal Sorcery (Aura)",
                "description": "While a friendly Scintillating Legions Psyker unit from your army is within 6\" of and visible to this unit, that Scintillating Legions unit has the Cabal of Sorcerers ability."
            }
        ]
    },
    "Thousand Sons Sekhetar Robots": {
        "stats": {
            "stat_movement": "8\"",
            "stat_toughness": 6,
            "stat_save": "3+",
            "stat_wounds": 4,
            "stat_leadership": "7+",
            "stat_oc": 1,
            "stat_invuln": "5+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Pyreflux meltagun",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "1",
                "skill": "4+",
                "strength": "10",
                "ap": "-4",
                "damage": "D6",
                "keywords": "Melta 2"
            },
            {
                "name": "Close combat weapon",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "3",
                "skill": "4+",
                "strength": "5",
                "ap": "0",
                "damage": "1"
            },
            {
                "name": "Heavy warpflamer",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "D6",
                "skill": "N/A",
                "strength": "5",
                "ap": "-2",
                "damage": "1",
                "keywords": "Ignores Cover, Torrent"
            },
            {
                "name": "Hellfyre missile rack",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "2",
                "skill": "4+",
                "strength": "10",
                "ap": "-2",
                "damage": "3"
            },
            {
                "name": "Power claw",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "3",
                "skill": "4+",
                "strength": "10",
                "ap": "-2",
                "damage": "2",
                "keywords": "-"
            },
            {
                "name": "Warpflame projector",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "D3",
                "skill": "N/A",
                "strength": "3",
                "ap": "-1",
                "damage": "1",
                "keywords": "Ignores Cover, Torrent"
            }
        ],
        "abilities": [
            {
                "name": "Prophetic Sentinels",
                "description": "Once per turn, when you target this unit with the Fire Overwatch/ Heroic Intervention stratagem, that use is -1 CP."
            },
            {
                "name": "Mortal Sorcery (Aura)",
                "description": "While a friendly Scintillating Legions Psyker unit from your army is within 6\" of and visible to this unit, that Scintillating Legions unit has the Cabal of Sorcerers ability."
            }
        ]
    },
    "Thousand Sons Tzaangors": {
        "stats": {
            "stat_movement": "6\"",
            "stat_toughness": 4,
            "stat_save": "6+",
            "stat_wounds": 1,
            "stat_leadership": "7+",
            "stat_oc": 1,
            "stat_invuln": "6+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Chainsword",
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
                "name": "Tzaangor blades",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "2",
                "skill": "4+",
                "strength": "5",
                "ap": "0",
                "damage": "1",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Ambushing Hunters",
                "description": "At the end of your opponent's turn, if this unit is more than 6\" horizontally away from all enemy units, you can remove this unit from the battlefield and place it into Strategic Reserves."
            },
            {
                "name": "Mortal Sorcery (Aura)",
                "description": "While a friendly Scintillating Legions Psyker unit from your army is within 6\" of and visible to this unit, that Scintillating Legions unit has the Cabal of Sorcerers ability."
            },
            {
                "name": "Brayhorn",
                "description": "You can re-roll Advance and Charge rolls made for the bearer\u2019s unit."
            },
            {
                "name": "Herd banner",
                "description": "While the bearer's unit is within range of one or more objective markers you control, improve the Leadership characteristic of models in the bearer's unit by 1."
            }
        ]
    },
    "Tzaangor Enlightened": {
        "stats": {
            "stat_movement": "10\"",
            "stat_toughness": 4,
            "stat_save": "5+",
            "stat_wounds": 2,
            "stat_leadership": "7+",
            "stat_oc": 2,
            "stat_invuln": "5+",
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
                "name": "Chainsword",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "6",
                "skill": "4+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Precision"
            },
            {
                "name": "Divining spear",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "3",
                "skill": "4+",
                "strength": "5",
                "ap": "-1",
                "damage": "2",
                "keywords": "Lance, Precision"
            }
        ],
        "abilities": [
            {
                "name": "Prophesied Doom",
                "description": "Each time this unit makes a Charge move, select one enemy unit within Engagement Range of it, then roll one D6 for each model in this unit that is within Engagement Range of that enemy unit: for each 4+, that enemy unit suffers 1 mortal wound."
            },
            {
                "name": "Mortal Sorcery (Aura)",
                "description": "While a friendly Scintillating Legions Psyker unit from your army is within 6\" of and visible to this unit, that Scintillating Legions unit has the Cabal of Sorcerers ability."
            }
        ]
    },
    "Tzaangor Enlightened with Fatecaster greatbows": {
        "stats": {
            "stat_movement": "10\"",
            "stat_toughness": 4,
            "stat_save": "5+",
            "stat_wounds": 2,
            "stat_leadership": "7+",
            "stat_oc": 2,
            "stat_invuln": "5+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Fatecaster greatbow",
                "weapon_type": "ranged",
                "range": "30\"",
                "attacks": "2",
                "skill": "4+",
                "strength": "5",
                "ap": "-2",
                "damage": "2",
                "keywords": "Ignores Cover, Lethal Hits, Precision"
            },
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
            }
        ],
        "abilities": [
            {
                "name": "Malign Trickery",
                "description": "In your opponent's Movement phase, if an enemy unit ends a move within 8\" of this unit, if this unit is not within Engagement Range of one or more enemy units, this unit can make a Normal move of up to D6\"."
            },
            {
                "name": "Mortal Sorcery (Aura)",
                "description": "While a friendly Scintillating Legions Psyker unit from your army is within 6\" of and visible to this unit, that Scintillating Legions unit has the Cabal of Sorcerers ability."
            }
        ]
    },
    "Tzaangor Shaman": {
        "stats": {
            "stat_movement": "10\"",
            "stat_toughness": 4,
            "stat_save": "5+",
            "stat_wounds": 4,
            "stat_leadership": "7+",
            "stat_oc": 2,
            "stat_invuln": "5+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Baleful Devolution",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "D6",
                "skill": "3+",
                "strength": "9",
                "ap": "0",
                "damage": "1",
                "keywords": "Blast, Devastating Wounds, Psychic"
            },
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
            }
        ],
        "abilities": [
            {
                "name": "Sacrificial Blessing",
                "description": "While this model is leading a unit, in your Shooting phase and the Fight phase, each time that unit is selected to shoot or fight, this model can use this ability. If it does, select one Bodyguard model in that unit; that Bodyguard model is destroyed and, until the end of the phase, add D3 to the Attacks and Strength characteristics of Psychic weapons equipped by this model."
            },
            {
                "name": "Bestial Prophet",
                "description": "While this model is leading a unit, each time a model in that unit makes an attack, add 1 to the Hit roll."
            },
            {
                "name": "Leader",
                "description": "This model can be attached to the following units: Tzaangor Enlightened, Tzaangors"
            },
            {
                "name": "Mortal Sorcery (Aura)",
                "description": "While a friendly Scintillating Legions Psyker unit from your army is within 6\" of and visible to this unit, that Scintillating Legions unit has the Cabal of Sorcerers ability."
            }
        ]
    }
}


class Command(BaseCommand):
    """Refresh Thousand Sons stat lines, weapon profiles, and abilities from BSData."""

    help = 'Refresh 11th Edition stats/weapons/abilities for Thousand Sons units.'

    def add_arguments(self, parser):
        """Add --dry-run flag."""
        parser.add_argument(
            '--dry-run', action='store_true',
            help='Preview changes without writing to the database.',
        )

    def handle(self, *args, **options):
        """Iterate THOUSAND_SONS_DATASHEETS and refresh each unit's datasheet data."""
        dry_run = options['dry_run']
        updated = 0
        skipped = 0

        with transaction.atomic():
            for name, payload in THOUSAND_SONS_DATASHEETS.items():
                try:
                    unit = UnitType.objects.get(name=name, faction__name='Thousand Sons')
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
