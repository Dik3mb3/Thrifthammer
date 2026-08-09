"""
Management command: seed_death_guard_datasheets

Refreshes stat lines, weapon profiles, and abilities for all Death Guard
units using 11th Edition data sourced from BSData/wh40k-11e
("Chaos - Death Guard.json") -- the same source used by
seed_death_guard_points.py.

Usage:
    python manage.py seed_death_guard_datasheets
    python manage.py seed_death_guard_datasheets --dry-run

Notes:
- Does NOT touch points_cost or category -- those are handled entirely by
  seed_death_guard_points.py. This command only refreshes stat_* fields,
  WeaponProfile rows, and UnitAbility rows.
- Unlike the loyalist Space Marine chapters, Death Guard's file is fully
  self-contained and includes its own rules for units that look "generic"
  (Chaos Predator, Chaos Rhino, etc.) -- these get their own
  Death-Guard-specific datasheet here, not a fallback to Chaos Space
  Marines. Confirmed with user 2026-08-07: every Chaos legion may have
  different points AND abilities for shared-name units, not just points.
- Per-field safety rule: a unit's stats/weapons/abilities are only
  overwritten when BSData actually has that data for it. If extraction
  found nothing, the existing DB value/rows are left untouched.
- All 36 active units resolved cleanly -- 0 missing stats/weapons/
  abilities, 0 overlong stat fields. 'Beasts of Nurgle' and
  'Myphitic Blight-hauler' have real stat/weapon/ability data despite
  lacking an independent BSData points value (that's user-supplied in the
  points command).
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from calculators.models import UnitAbility, UnitType, WeaponProfile

# (name -> {stats?, weapons?, abilities?}). Missing keys mean "no data
# found for this field -- leave existing DB data untouched."
DEATH_GUARD_DATASHEETS = {
    "Beasts of Nurgle": {
        "stats": {
            "stat_movement": "6\"",
            "stat_toughness": 9,
            "stat_save": "6+",
            "stat_wounds": 7,
            "stat_leadership": "7+",
            "stat_oc": 3,
            "stat_invuln": "5+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Putrid appendages",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "6",
                "skill": "4+",
                "strength": "6",
                "ap": "-1",
                "damage": "2",
                "keywords": "Devastating Wounds"
            }
        ],
        "abilities": [
            {
                "name": "Grotesque Regeneration",
                "description": "At the end of each phase, if a Beasts of Nurgle model in this unit has lost any wounds but is not destroyed, that model regains all of its lost wounds."
            }
        ]
    },
    "Biologus Putrifier": {
        "stats": {
            "stat_movement": "5\"",
            "stat_toughness": 6,
            "stat_save": "3+",
            "stat_wounds": 4,
            "stat_leadership": "6+",
            "stat_oc": 1,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Hyper blight grenades",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "D6",
                "skill": "3+",
                "strength": "7",
                "ap": "-1",
                "damage": "2",
                "keywords": "Assault, Blast, Lethal Hits"
            },
            {
                "name": "Injector pistol",
                "weapon_type": "ranged",
                "range": "3\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "4",
                "ap": "-1",
                "damage": "3",
                "keywords": "Anti-INFANTRY 2+, Pistol, Precision"
            },
            {
                "name": "Plague knives",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "3+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Lethal Hits"
            }
        ],
        "abilities": [
            {
                "name": "Extraction of Fresh Disease",
                "description": "The first time this model's unit destroys an enemy unit as a result of a melee attack, until the end of the battle, add 6 to the Objective Control characteristic of this model."
            },
            {
                "name": "Foul Infusion",
                "description": "While this model is leading a unit, weapons equipped by models in that unit have the [Lethal Hits] ability. In addition, each time a model in that unit makes an attack, a Critical Hit is scored on an unmodified Hit roll of 5+, instead of only on a 6."
            },
            {
                "name": "Leader",
                "description": "This model can be attached to the following unit: Plague Marines\nYou can attach this model to a Plague Marines unit, even if one other Leader unit has already been attached to it (you cannot attach more than one of the same Leader to the same unit). If you do, and that Bodyguard unit is destroyed, the Leader units attached to it become separate units, with their original Starting Strengths."
            }
        ]
    },
    "Blightlord Terminators": {
        "stats": {
            "stat_movement": "5\"",
            "stat_toughness": 7,
            "stat_save": "2+",
            "stat_wounds": 3,
            "stat_leadership": "6+",
            "stat_oc": 1,
            "stat_invuln": "4+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Bubotic blade",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "3",
                "skill": "3+",
                "strength": "5",
                "ap": "-2",
                "damage": "2",
                "keywords": "Lethal Hits"
            },
            {
                "name": "Combi-bolter",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "2",
                "skill": "3+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Lethal Hits, Rapid Fire 2"
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
                "keywords": "Anti-INFANTRY 4+, Devastating Wounds, Rapid Fire 1"
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
                "name": "Plague spewer",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "D6",
                "skill": "N/A",
                "strength": "5",
                "ap": "-1",
                "damage": "1",
                "keywords": "Anti-INFANTRY 2+, Ignores Cover, Torrent"
            },
            {
                "name": "Flail of corruption",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "6",
                "skill": "3+",
                "strength": "5",
                "ap": "-1",
                "damage": "2",
                "keywords": "Lethal Hits"
            },
            {
                "name": "Blight launcher",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "D3",
                "skill": "3+",
                "strength": "6",
                "ap": "-1",
                "damage": "2",
                "keywords": "Blast, Lethal Hits"
            },
            {
                "name": "Reaper autocannon",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "4",
                "skill": "3+",
                "strength": "7",
                "ap": "-1",
                "damage": "1",
                "keywords": "Devastating Wounds, Sustained Hits 1"
            }
        ],
        "abilities": [
            {
                "name": "Blistering Fusillade",
                "description": "If this unit has a Starting Strength of 5 or more, or if a Character is leading this unit, then each time a model in this unit makes a ranged attack that targets an Afflicted unit, improve the Strength and Armour Penetration characteristics of that attack by 1."
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
                "name": "Twin heavy bolter",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "3",
                "skill": "3+",
                "strength": "5",
                "ap": "-1",
                "damage": "2",
                "keywords": "Lethal Hits, Sustained Hits 1, Twin-linked"
            },
            {
                "name": "Combi-bolter",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "2",
                "skill": "3+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Lethal Hits, Rapid Fire 2"
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
                "keywords": "Anti-INFANTRY 4+, Devastating Wounds, Rapid Fire 1"
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
                "name": "Combi-bolter",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "2",
                "skill": "3+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Lethal Hits, Rapid Fire 2"
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
                "keywords": "Anti-INFANTRY 4+, Devastating Wounds, Rapid Fire 1"
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
                "keywords": "Lethal Hits, Sustained Hits 1"
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
                "name": "Metalophagic Infection",
                "description": "In your Shooting phase, after this model has shot, select one enemy Monster or Vehicle unit hit by one or more of those attacks. Roll one D6, adding 1 to the result if that unit is Afflicted; on a 5+, that unit suffers D3 mortal wounds."
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
                "keywords": "Lethal Hits, Rapid Fire 2"
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
                "name": "Combi-bolter",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "2",
                "skill": "3+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Lethal Hits, Rapid Fire 2"
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
                "keywords": "Anti-INFANTRY 4+, Devastating Wounds, Rapid Fire 1"
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
                "keywords": "Lethal Hits, Sustained Hits 1"
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
                "name": "Hail of Corrosive Disease",
                "description": "In your Shooting phase, after this model has shot, select one enemy unit (excluding Monsters and Vehicles) hit by one or more of those attacks. Until the end of the phase, each time a friending Death Guard unit makes a ranged attack that targets that enemy unit, improve the Armour Penetration characteristic of that attack by 1. The same enemy unit can only be affected by this ability once per phase."
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
                "name": "Combi-bolter",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "2",
                "skill": "3+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Lethal Hits, Rapid Fire 2"
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
                "name": "Combi-weapon",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "1",
                "skill": "4+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Anti-INFANTRY 4+, Devastating Wounds, Rapid Fire 1"
            }
        ],
        "abilities": [
            {
                "name": "Fire Support",
                "description": "In your Shooting phase, after this model has shot, select one enemy unit hit by one or more of those attacks. Until the end of the phase, each time a friendly model that disembarked from this Transport this turn makes an attack that targets that unit, you can re-roll the Wound roll."
            }
        ]
    },
    "Chaos Spawn": {
        "stats": {
            "stat_movement": "8\"",
            "stat_toughness": 7,
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
                "attacks": "D6+2",
                "skill": "4+",
                "strength": "5",
                "ap": "-1",
                "damage": "2",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Lethal Ichor",
                "description": "Each time a melee attack is allocated to a model in this unit, after the attacking unit has finished making its attacks, roll one D6 (to a maximum of six D6 per attacking unit): for each 4+, the attacking unit suffers 1 mortal wound."
            }
        ]
    },
    "Daemon Prince of Nurgle": {
        "stats": {
            "stat_movement": "8\"",
            "stat_toughness": 12,
            "stat_save": "2+",
            "stat_wounds": 10,
            "stat_leadership": "6+",
            "stat_oc": 3,
            "stat_invuln": "4+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "\u27a4 Hellforged weapons - strike",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "7",
                "skill": "2+",
                "strength": "8",
                "ap": "-2",
                "damage": "3",
                "keywords": "Lethal Hits"
            },
            {
                "name": "\u27a4 Hellforged weapons - sweep",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "14",
                "skill": "2+",
                "strength": "6",
                "ap": "-1",
                "damage": "1",
                "keywords": "Lethal Hits"
            },
            {
                "name": "Infernal cannon",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "3",
                "skill": "2+",
                "strength": "5",
                "ap": "-1",
                "damage": "2",
                "keywords": "Lethal Hits"
            }
        ],
        "abilities": [
            {
                "name": "Death Guard Defenders",
                "description": "While this model is within 3\" of one or more friendly Death Guard Infantry units, this model has the Lone Operative ability."
            },
            {
                "name": "Fevered Strategist",
                "description": "Once per Battle Round, one model from your army with this ability can use it when a friendly Death Guard unit within 12\" of that model is targeted with a Stratagem. If it does, reduce the CP cost of that Stratagem by 1CP."
            },
            {
                "name": "Miasma of Pestilence (Aura)",
                "description": "While a friendly Death Guard unit is within 6\" of this model, each time a ranged attack targets that unit, models in that unit have the Benefit of Cover against that attack."
            }
        ]
    },
    "Daemon Prince of Nurgle with wings": {
        "stats": {
            "stat_movement": "12\"",
            "stat_toughness": 11,
            "stat_save": "2+",
            "stat_wounds": 10,
            "stat_leadership": "6+",
            "stat_oc": 3,
            "stat_invuln": "4+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Infernal cannon",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "3",
                "skill": "2+",
                "strength": "7",
                "ap": "-1",
                "damage": "2",
                "keywords": "Lethal Hits"
            },
            {
                "name": "\u27a4 Hellforged weapons - strike",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "7",
                "skill": "2+",
                "strength": "8",
                "ap": "-2",
                "damage": "3",
                "keywords": "Lethal Hits"
            },
            {
                "name": "\u27a4 Hellforged weapons - sweep",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "14",
                "skill": "2+",
                "strength": "6",
                "ap": "-1",
                "damage": "1",
                "keywords": "Lethal Hits"
            }
        ],
        "abilities": [
            {
                "name": "Horrifying Visage",
                "description": "Each time this model ends a Charge move, select one enemy unit within Engagement Range of it. That unit must take a Battle-shock test, subtracting 1 from that test."
            },
            {
                "name": "Enfeebling Miasma (Aura)",
                "description": "While an enemy unit (excluding Monsters and Vehicles*) is within 6\" of this model, each time that unit is selected to Fall Back, models in that enemy unit must take Desperate Escape tests. When doing so, if that enemy unit is Battle-shocked, subtract 1 from each of those Desperate Escape tests."
            }
        ]
    },
    "Deathshroud Terminators": {
        "stats": {
            "stat_movement": "5\"",
            "stat_toughness": 7,
            "stat_save": "2+",
            "stat_wounds": 4,
            "stat_leadership": "6+",
            "stat_oc": 1,
            "stat_invuln": "4+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "\u27a4 Manreaper - strike",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "2+",
                "strength": "8",
                "ap": "-2",
                "damage": "2",
                "keywords": "Lethal Hits"
            },
            {
                "name": "\u27a4 Manreaper - sweep",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "8",
                "skill": "3+",
                "strength": "4",
                "ap": "-1",
                "damage": "1",
                "keywords": "Lethal Hits"
            },
            {
                "name": "Plaguespurt gauntlet",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "D6",
                "skill": "N/A",
                "strength": "3",
                "ap": "0",
                "damage": "1",
                "keywords": "Anti-INFANTRY 4+, Ignores Cover, Pistol, Torrent"
            }
        ],
        "abilities": [
            {
                "name": "Silent Bodyguard",
                "description": "While a Character model is leading this unit, that Character model has the Feel No Pain 4+ ability."
            },
            {
                "name": "Death Approaches",
                "description": "In your Movement phase, when this unit is set up on the battlefield using the Deep Strike ability, it can be set up anywhere on the battlefield that is more than 6\" horizontally away from all Afflicted enemy units, and more than 8\" horizontally away from any other enemy units."
            },
            {
                "name": "Icon of Despair (Aura)",
                "description": "While an enemy unit is within 6\" of the bearer, worsen the Leadership characteristic of models in that unit by 1."
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
                "keywords": "Lethal Hits"
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
                "keywords": "Lethal Hits"
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
                "keywords": "Blast, Lethal Hits"
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
                "keywords": "Lethal Hits"
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
                "keywords": "Lethal Hits"
            },
            {
                "name": "Heavy reaper autocannon",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "4",
                "skill": "3+",
                "strength": "9",
                "ap": "-1",
                "damage": "3",
                "keywords": "Devastating Wounds, Lethal Hits, Sustained Hits 1"
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
                "keywords": "Blast, Lethal Hits"
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
                "keywords": "Blast, Lethal Hits"
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
                "ap": "-1",
                "damage": "2",
                "keywords": "Lethal Hits"
            },
            {
                "name": "Magma cutter",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "2",
                "skill": "3+",
                "strength": "9",
                "ap": "-4",
                "damage": "D6",
                "keywords": "Lethal Hits, Melta 2"
            }
        ],
        "abilities": [
            {
                "name": "Scuttling Walker",
                "description": "Each time this unit makes a Normal, Advance or Fall Back move, it can move through models (excluding Titanic models) and terrain features. When doing so, it can move within Engagement Range of enemy models, but cannot end that move within Engagement Range of them, and any Desperate Escape test is automatically passed."
            },
            {
                "name": "Barrage of Filth",
                "description": "In your Shooting phase, after this model has shot, select one enemy unit hit by one or more of those attacks. Until the end of the phase, that unit cannot have the Benefit of Cover."
            }
        ]
    },
    "Foetid Bloat-drone": {
        "stats": {
            "stat_movement": "10\"",
            "stat_toughness": 9,
            "stat_save": "3+",
            "stat_wounds": 10,
            "stat_leadership": "6+",
            "stat_oc": 3,
            "stat_invuln": "5+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Plague probe",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "3",
                "skill": "3+",
                "strength": "6",
                "ap": "-1",
                "damage": "1",
                "keywords": "Lethal Hits"
            },
            {
                "name": "Plaguespitter",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "D6",
                "skill": "N/A",
                "strength": "6",
                "ap": "-1",
                "damage": "1",
                "keywords": "Anti-INFANTRY 2+, Ignores Cover, Torrent"
            },
            {
                "name": "Fleshmower",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "10",
                "skill": "3+",
                "strength": "7",
                "ap": "-1",
                "damage": "2",
                "keywords": "Lethal Hits"
            }
        ],
        "abilities": [
            {
                "name": "Hovering Death",
                "description": "This model is eligible to shoot and declare a charge in a turn in which it Fell Back."
            }
        ]
    },
    "Foetid Bloat-drone with heavy blight launcher": {
        "stats": {
            "stat_movement": "10\"",
            "stat_toughness": 9,
            "stat_save": "3+",
            "stat_wounds": 10,
            "stat_leadership": "6+",
            "stat_oc": 3,
            "stat_invuln": "5+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Heavy blight launcher",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "D6+2",
                "skill": "3+",
                "strength": "10",
                "ap": "-2",
                "damage": "3",
                "keywords": "Blast, Lethal Hits"
            },
            {
                "name": "Plague probe",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "3",
                "skill": "3+",
                "strength": "6",
                "ap": "-1",
                "damage": "1",
                "keywords": "Lethal Hits"
            }
        ],
        "abilities": [
            {
                "name": "Explosive Blight",
                "description": "In your Shooting phase, each time this model makes an attack that destroys an enemy unit, before removing the last model in that unit from play, roll a D6, adding 1 to the result if that unit is Afflicted; on a 5+, each enemy unit within 6\" of that model is Afflicted until the start of your next turn."
            }
        ]
    },
    "Foul Blightspawn": {
        "stats": {
            "stat_movement": "5\"",
            "stat_toughness": 6,
            "stat_save": "3+",
            "stat_wounds": 4,
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
                "attacks": "4",
                "skill": "3+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "Plague sprayer",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "D6",
                "skill": "N/A",
                "strength": "7",
                "ap": "-2",
                "damage": "2",
                "keywords": "Anti-INFANTRY 2+, Ignores Cover, Torrent"
            }
        ],
        "abilities": [
            {
                "name": "Putrefying Stink",
                "description": "Enemy models cannot start or end an Advance move within 9\" of this model."
            },
            {
                "name": "Blinding Spray",
                "description": "In the Fight phase, you can select one model from your army with this ability to use this ability. If you do, until the end of that phase, that model's unit has the Fights First ability. Each model can only be selected for this ability once per battle."
            },
            {
                "name": "Leader",
                "description": "This model can be attached to the following unit: Plague Marines\nYou can attach this model to a Plague Marines unit, even if one other Leader unit has already been attached to it (you cannot attach more than one of the same Leader to the same unit). If you do, and that Bodyguard unit is destroyed, the Leader units attached to it become separate units, with their original Starting Strengths."
            }
        ]
    },
    "Great Unclean One": {
        "stats": {
            "stat_movement": "7\"",
            "stat_toughness": 12,
            "stat_save": "5+",
            "stat_wounds": 20,
            "stat_leadership": "6+",
            "stat_oc": 5,
            "stat_invuln": "4+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Putrid vomit",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "D6+3",
                "skill": "N/A",
                "strength": "5",
                "ap": "-2",
                "damage": "1",
                "keywords": "Ignores Cover, Torrent"
            },
            {
                "name": "Plague flail",
                "weapon_type": "ranged",
                "range": "6\"",
                "attacks": "D6+1",
                "skill": "3+",
                "strength": "7",
                "ap": "-2",
                "damage": "2",
                "keywords": "-"
            },
            {
                "name": "Bileblade",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "3",
                "skill": "2+",
                "strength": "6",
                "ap": "-2",
                "damage": "2",
                "keywords": "Extra Attacks, Lethal Hits"
            },
            {
                "name": "\u27a4 Bilesword - strike",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "6",
                "skill": "2+",
                "strength": "10",
                "ap": "-2",
                "damage": "D6+1",
                "keywords": "Lethal Hits"
            },
            {
                "name": "\u27a4 Bilesword - sweep",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "12",
                "skill": "2+",
                "strength": "7",
                "ap": "-1",
                "damage": "1",
                "keywords": "Lethal Hits"
            },
            {
                "name": "Doomsday bell",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "6",
                "skill": "2+",
                "strength": "7",
                "ap": "-1",
                "damage": "2",
                "keywords": "Lethal Hits, Reverberating Summons"
            }
        ],
        "abilities": [
            {
                "name": "Daemon Lord of Nurgle (Aura)",
                "description": "While a friendly Plague Legions unit is within 6\" of this model, add 1 to the Toughness characteristic of models in that unit."
            },
            {
                "name": "Nurgle\u2019s Rot (Psychic)",
                "description": "At the end of your Movement phase, you can select one enemy unit within 12\" of this model. Until the start of your next Movement phase, that unit is rotted. While a unit is rotted, subtract 1 from the Toughness characteristic of models in that unit."
            },
            {
                "name": "Damaged: 1-7 wounds remaining",
                "description": "While this model has 1-7 wounds remaining, each time this model makes an attack, subtract 1 from the Hit roll."
            }
        ]
    },
    "Helbrute": {
        "stats": {
            "stat_movement": "7\"",
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
                "name": "Combi-bolter",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "2",
                "skill": "3+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Lethal Hits, Rapid Fire 2"
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
                "attacks": "4",
                "skill": "3+",
                "strength": "14",
                "ap": "-3",
                "damage": "D6+1",
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
                "keywords": "Lethal Hits, Melta 2"
            },
            {
                "name": "Twin autocannon",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "2",
                "skill": "3+",
                "strength": "10",
                "ap": "-1",
                "damage": "3",
                "keywords": "Twin-linked, Lethal Hits"
            },
            {
                "name": "Plasma cannon",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "D3",
                "skill": "3+",
                "strength": "8",
                "ap": "-3",
                "damage": "3",
                "keywords": "Blast, Hazardous, Lethal Hits"
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
                "keywords": "Lethal Hits, Sustained Hits 1, Twin-linked"
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
                "name": "Diseased Malice",
                "description": "Each time this model makes an attack that targets an Afflicted unit, add 1 to the Wound roll."
            },
            {
                "name": "Froth-spattered Frenzy",
                "description": "If this model is equipped with two melee weapons in addition to its close combat weapon, add 2 to the Attacks characteristic of those two weapons."
            }
        ]
    },
    "Icon Bearer": {
        "stats": {
            "stat_movement": "5\"",
            "stat_toughness": 6,
            "stat_save": "3+",
            "stat_wounds": 4,
            "stat_leadership": "5+",
            "stat_oc": 1,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Plague knife",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "3+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Lethal Hits"
            },
            {
                "name": "Boltgun",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "2",
                "skill": "3+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Lethal Hits"
            }
        ],
        "abilities": [
            {
                "name": "Unclean Icon",
                "description": "While this model is leading a unit, add 1 to the Objective Control characteristic of models in that unit."
            },
            {
                "name": "Blessed Icon of Disease",
                "description": "Once per battle, at the start of any phase, you can select one friendly Death Guard unit that is Battle-shocked and within 12\" of this model. That unit is no longer Battle-shocked."
            },
            {
                "name": "Leader",
                "description": "This model can be attached to the following unit: Plague Marines\nYou can attach this model to a Plague Marines unit, even if one other Leader unit has already been attached to it (you cannot attach more than one of the same Leader to the same unit). If you do, and that Bodyguard unit is destroyed, the Leader units attached to it become separate units, with their original Starting Strengths."
            }
        ]
    },
    "Lord of Contagion": {
        "stats": {
            "stat_movement": "5\"",
            "stat_toughness": 7,
            "stat_save": "2+",
            "stat_wounds": 6,
            "stat_leadership": "6+",
            "stat_oc": 1,
            "stat_invuln": "4+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "\u27a4 Manreaper - strike",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "5",
                "skill": "2+",
                "strength": "9",
                "ap": "-2",
                "damage": "3",
                "keywords": "Lethal Hits"
            },
            {
                "name": "\u27a4 Manreaper - sweep",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "10",
                "skill": "2+",
                "strength": "6",
                "ap": "-1",
                "damage": "1",
                "keywords": "Lethal Hits"
            }
        ],
        "abilities": [
            {
                "name": "Vector of Disease",
                "description": "While this model is leading a unit, melee weapons equipped by models in that unit have the [Sustained Hits 1] and [Lance] abilties."
            },
            {
                "name": "Unholy Resilience",
                "description": "The first time a model with this ability is destroyed in a battle round, roll one D6 at the end of the phase. On a 2+, set that model back up on the battlefield, as close as possible to where it was destroyed and not within Engagement Range of any enemy units, with 3 wounds remaining. Each model can only be set up in this way once per battle."
            },
            {
                "name": "Leader",
                "description": "This model can be attached to the following units:\n- Blightlord Terminators\n- Deathshroud Terminators"
            }
        ]
    },
    "Lord of Poxes": {
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
                "name": "Great plague blade",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "6",
                "skill": "2+",
                "strength": "8",
                "ap": "-2",
                "damage": "2",
                "keywords": "Devastating Wounds, Lethal Hits"
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
                "name": "\u27a4 Plasma pistol - supercharge",
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
                "name": "Leader",
                "description": "This model can be attached to the following units:\n- Plague Marines"
            },
            {
                "name": "Gift of Poxes",
                "description": "Add 3\" to the range of this model's Contagion Range."
            },
            {
                "name": "Shroud of Disease",
                "description": "While this model is leading a unit, that unit cannot be targeted by ranged attacks unless the attacking unit is within 18\"."
            }
        ]
    },
    "Lord of Virulence": {
        "stats": {
            "stat_movement": "5\"",
            "stat_toughness": 7,
            "stat_save": "2+",
            "stat_wounds": 6,
            "stat_leadership": "6+",
            "stat_oc": 1,
            "stat_invuln": "4+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Power fist",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "5",
                "skill": "2+",
                "strength": "8",
                "ap": "-2",
                "damage": "2",
                "keywords": "Lethal Hits"
            },
            {
                "name": "Twin plague spewer",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "D6",
                "skill": "N/A",
                "strength": "5",
                "ap": "-1",
                "damage": "1",
                "keywords": "Anti-INFANTRY 2+, Ignores Cover, Torrent, Twin-linked"
            }
        ],
        "abilities": [
            {
                "name": "Virulent Aura",
                "description": "While this model is leading a unit, each time a model in that unit makes a ranged attack, you can re-roll the Wound roll."
            },
            {
                "name": "Blight Bombardment",
                "description": "At the start of your Shooting phase, select one enemy unit within 30\" of and visible to this model. Until the end of the phase, each time a friendly Death Guard unit makes a ranged attack that targets that unit, re-roll a Hit roll of 1 (if that attack is made with a Blast weapon, you can re-roll the Hit roll instead)."
            },
            {
                "name": "Leader",
                "description": "This model can be attached to the following units:\n- Blightlord Terminators\n- Deathshroud Terminators"
            }
        ]
    },
    "Malignant Plaguecaster": {
        "stats": {
            "stat_movement": "5\"",
            "stat_toughness": 6,
            "stat_save": "3+",
            "stat_wounds": 4,
            "stat_leadership": "6+",
            "stat_oc": 1,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Corrupted staff",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "3+",
                "strength": "6",
                "ap": "-1",
                "damage": "D3",
                "keywords": "Lethal Hits, Psychic"
            },
            {
                "name": "\u27a4 Plague Wind - witchfire",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "D6",
                "skill": "N/A",
                "strength": "4",
                "ap": "-1",
                "damage": "D3",
                "keywords": "Psychic, Torrent"
            },
            {
                "name": "\u27a4 Plague Wind - focused witchfire",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "D6+3",
                "skill": "N/A",
                "strength": "6",
                "ap": "-2",
                "damage": "D3",
                "keywords": "Hazardous, Psychic, Torrent"
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
                "keywords": "Lethal Hits, Pistol"
            }
        ],
        "abilities": [
            {
                "name": "Gift of Contagion (Psychic)",
                "description": "While this model is leading a unit, each time a model in that unit makes an attack which targets a unit which is Afflicted, that attack has the [Sustained Hits 1] ability."
            },
            {
                "name": "Pestilent Fallout (Psychic)",
                "description": "In your Shooting phase, after this model has shot, select one enemy Infantry unit hit by one or more of those attacks made with its Plague Wind. Until the end of your opponent's next turn, that unit is enfeebled. While a unit is enfeebled, subtract 2\" from the Move characteristic of models in that unit."
            },
            {
                "name": "Leader",
                "description": "This model can be attached to the following units:\nPlague Marines, Poxwalkers"
            }
        ]
    },
    "Miasmic Malignifier": {
        "stats": {
            "stat_movement": "-",
            "stat_toughness": 10,
            "stat_save": "3+",
            "stat_wounds": 12,
            "stat_leadership": "6+",
            "stat_oc": 0,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Miasmic gouts",
                "weapon_type": "ranged",
                "range": "9\"",
                "attacks": "2D6",
                "skill": "N/A",
                "strength": "3",
                "ap": "0",
                "damage": "1",
                "keywords": "Ignores Cover, Torrent"
            }
        ],
        "abilities": [
            {
                "name": "Putrescent Fog (Aura)",
                "description": "Enemy units that are set up on the battlefield as Reinforcements cannot be set up within 12\" of this model."
            },
            {
                "name": "Diseased Cover",
                "description": "Each time a ranged attack is allocated to a model, if that model is not fully visible to every model in the attacking unit because of this Fortification, that model has the Benefit of Cover against that attack."
            },
            {
                "name": "Deployment",
                "description": "Both parts of this Fortification must be deployed within 1\" of each other. Both parts are then treated as a single model for all rules purposes."
            }
        ]
    },
    "Mortarion": {
        "stats": {
            "stat_movement": "10\"",
            "stat_toughness": 12,
            "stat_save": "2+",
            "stat_wounds": 16,
            "stat_leadership": "5+",
            "stat_oc": 6,
            "stat_invuln": "4+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Rotwind",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "D6+3",
                "skill": "2+",
                "strength": "7",
                "ap": "-2",
                "damage": "1",
                "keywords": "Blast, Devastating Wounds, Lethal Hits, Psychic"
            },
            {
                "name": "Lantern",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "1",
                "skill": "2+",
                "strength": "10",
                "ap": "-3",
                "damage": "3",
                "keywords": "Pistol, Sustained Hits D3"
            },
            {
                "name": "\u27a4 Silence - strike",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "5",
                "skill": "2+",
                "strength": "14",
                "ap": "-3",
                "damage": "D6+1",
                "keywords": "Devastating Wounds, Lethal Hits"
            },
            {
                "name": "\u27a4 Silence - sweep",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "15",
                "skill": "2+",
                "strength": "8",
                "ap": "-2",
                "damage": "2",
                "keywords": "Lethal Hits, Sustained Hits 1"
            }
        ],
        "abilities": [
            {
                "name": "Host of Plagues",
                "description": "At the end of your Movement phase, roll one D6 for each enemy unit within 6\" of this model, adding 1 to the result if that unit is Afflicted; on a 3+, that enemy unit suffers D3 mortal wounds."
            },
            {
                "name": "Lord of the Death Guard",
                "description": "Once per turn, this model can use one of the Lord of the Death Guard abilties."
            },
            {
                "name": "Damaged: 1-6 wounds remaining",
                "description": "While this model has 1-6 wounds remaining, each time this model makes an attack, subtract 1 from the Hit roll."
            }
        ]
    },
    "Myphitic Blight-hauler": {
        "stats": {
            "stat_movement": "10\"",
            "stat_toughness": 9,
            "stat_save": "3+",
            "stat_wounds": 10,
            "stat_leadership": "6+",
            "stat_oc": 3,
            "stat_invuln": "5+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Bile spurt",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "3",
                "skill": "3+",
                "strength": "5",
                "ap": "0",
                "damage": "1",
                "keywords": "Lethal Hits"
            },
            {
                "name": "Gnashing maw",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "3+",
                "strength": "6",
                "ap": "-1",
                "damage": "1",
                "keywords": "Lethal Hits"
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
                "name": "Multi-melta",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "2",
                "skill": "3+",
                "strength": "9",
                "ap": "-4",
                "damage": "D6",
                "keywords": "Lethal Hits, Melta 2"
            }
        ],
        "abilities": [
            {
                "name": "Tank Hunters",
                "description": "In your Shooting phase, each time a model in this unit makes a attack that targets a Monster or Vehicle unit, add 1 to the Hit roll and add 1 to the Wound roll."
            }
        ]
    },
    "Noxious Blightbringer": {
        "stats": {
            "stat_movement": "5\"",
            "stat_toughness": 6,
            "stat_save": "3+",
            "stat_wounds": 4,
            "stat_leadership": "6+",
            "stat_oc": 1,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Cursed plague bell",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "5",
                "skill": "3+",
                "strength": "4",
                "ap": "0",
                "damage": "2",
                "keywords": "Anti-PSYKER 2+, Lethal Hits"
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
                "name": "\u27a4 Plasma pistol - supercharge",
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
                "name": "Sickening Vitality",
                "description": "While this model is leading a unit, add 1\" to the Move characteristic of models in that unit and you can re-roll Advance and Charge rolls made for that unit."
            },
            {
                "name": "Tocsin of Misery (Aura)",
                "description": "In the Battle-shock step of your opponent's Command phase, if an enemy unit that is below its Starting Strength is within 9\" of this model, that enemy unit must take a Battle-shock test, subtracting 1 from that test if it is a Psyker unit."
            },
            {
                "name": "Leader",
                "description": "This model can be attached to the following units: Plague Marines, Poxwalkers\nYou can attach this model to a Plague Marines or Poxwalkers unit, even if one other Leader unit has already been attached to it (you cannot attach more than one of the same Leader to the same unit). If you do, and that Bodyguard unit is destroyed, the Leader units attached to it become separate units, with their original Starting Strengths."
            }
        ]
    },
    "Nurglings": {
        "stats": {
            "stat_movement": "5\"",
            "stat_toughness": 3,
            "stat_save": "7+",
            "stat_wounds": 4,
            "stat_leadership": "8+",
            "stat_oc": 0,
            "stat_invuln": "5+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Diseased claws and teeth",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "5+",
                "strength": "2",
                "ap": "0",
                "damage": "1",
                "keywords": "Lethal Hits"
            }
        ],
        "abilities": [
            {
                "name": "Mischief Makers (Aura)",
                "description": "Each time an enemy unit (excluding Titanic units) within Engagement Range of one or more units with this ability is selected to fight, until the end of the phase, each time a model in that enemy unit makes a melee attack, subtract 1 from the Hit roll."
            }
        ]
    },
    "Plague Drones": {
        "stats": {
            "stat_movement": "10\"",
            "stat_toughness": 8,
            "stat_save": "6+",
            "stat_wounds": 5,
            "stat_leadership": "7+",
            "stat_oc": 2,
            "stat_invuln": "5+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Death's heads",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "D3",
                "skill": "4+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Blast, Lethal Hits"
            },
            {
                "name": "Foul mouthparts",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "2",
                "skill": "4+",
                "strength": "5",
                "ap": "-1",
                "damage": "2",
                "keywords": "Extra Attacks, Lethal Hits"
            },
            {
                "name": "Plaguesword",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "2",
                "skill": "3+",
                "strength": "4",
                "ap": "-1",
                "damage": "1",
                "keywords": "Lethal Hits"
            }
        ],
        "abilities": [
            {
                "name": "Death\u2019s Heads",
                "description": "In your Shooting phase, after this unit has shot, select one enemy unit hit by one or more of those attacks. Until the end of the turn, each time a friendly NURGLE LEGIONES DAEMONICA unit makes an attack that targets that unit, you can re-roll the Wound roll."
            },
            {
                "name": "Daemonic Icon",
                "description": "Models in the bearer\u2019s unit have a Leadership characteristic of 6+."
            },
            {
                "name": "Instrument of Chaos",
                "description": "Add 1 to Charge rolls made for the bearer\u2019s unit."
            }
        ]
    },
    "Plague Marines": {
        "stats": {
            "stat_movement": "5\"",
            "stat_toughness": 6,
            "stat_save": "3+",
            "stat_wounds": 2,
            "stat_leadership": "6+",
            "stat_oc": 2,
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
                "keywords": "Lethal Hits"
            },
            {
                "name": "Plague knives",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "3",
                "skill": "3+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Lethal Hits"
            },
            {
                "name": "Bubotic weapons",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "3+",
                "strength": "5",
                "ap": "-2",
                "damage": "1",
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
                "keywords": "Lethal Hits, Pistol"
            },
            {
                "name": "Boltgun",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "2",
                "skill": "3+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Lethal Hits"
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
                "name": "Heavy plague weapon",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "3",
                "skill": "4+",
                "strength": "8",
                "ap": "-2",
                "damage": "2",
                "keywords": "Lethal Hits"
            },
            {
                "name": "Blight launcher",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "D3",
                "skill": "3+",
                "strength": "6",
                "ap": "-1",
                "damage": "2",
                "keywords": "Blast, Lethal Hits"
            },
            {
                "name": "Plague spewer",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "D6",
                "skill": "N/A",
                "strength": "5",
                "ap": "-1",
                "damage": "1",
                "keywords": "Anti-INFANTRY 2+, Ignores Cover, Torrent"
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
                "keywords": "Melta 2"
            },
            {
                "name": "Plague belcher",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "D6",
                "skill": "N/A",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Anti-INFANTRY 4+, Ignores Cover, Torrent"
            }
        ],
        "abilities": [
            {
                "name": "Infused with the Blessings of Nurgle",
                "description": "In your Shooting phase, each time this unit is selected to shoot, after this unit has shot, select one enemy unit hit by one or more of those attacks. Until the start of your next turn, that unit is Afflicted."
            },
            {
                "name": "Icon of Despair (Aura)",
                "description": "While an enemy unit is within 6\" of the bearer, worsen the Leadership characteristic of models in that unit by 1."
            },
            {
                "name": "Insectile Murmuration",
                "description": "When this unit\u2019s attacks target a unit within Contagion Range of a friendly unit, those attacks can re-roll wound rolls of 1."
            },
            {
                "name": "Plagueveil",
                "description": "This unit has -3\" detection range."
            }
        ]
    },
    "Plague Surgeon": {
        "stats": {
            "stat_movement": "5\"",
            "stat_toughness": 6,
            "stat_save": "3+",
            "stat_wounds": 4,
            "stat_leadership": "6+",
            "stat_oc": 1,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Balesword",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "3+",
                "strength": "5",
                "ap": "-2",
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
                "keywords": "Lethal Hits, Pistol"
            }
        ],
        "abilities": [
            {
                "name": "Tainted Narthecium",
                "description": "While this model is leading a unit, in your Command phase, you can return 1 destroyed Bodyguard model to that unit."
            },
            {
                "name": "Inflamed Infections",
                "description": "At the start of the Fight phase, select one enemy unit within Engagement Range of this model. Until the end of the phase, each time this model makes an attack that targets that unit, an unmodified Hit roll of 5+ scores a Critical Hit. If that unit is below Half-strength, an unmodified Hit roll of 4+ scores a Critical Hit instead."
            },
            {
                "name": "Leader",
                "description": "This model can be attached to the following unit: Plague Marines\nYou can attach this model to a Plague Marines unit, even if one other Leader unit has already been attached to it (you cannot attach more than one of the same Leader to the same unit). If you do, and that Bodyguard unit is destroyed, the Leader units attached to it become separate units, with their original Starting Strengths."
            }
        ]
    },
    "Plaguebearers": {
        "stats": {
            "stat_movement": "5\"",
            "stat_toughness": 5,
            "stat_save": "7+",
            "stat_wounds": 2,
            "stat_leadership": "7+",
            "stat_oc": 2,
            "stat_invuln": "5+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Plaguesword",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "2",
                "skill": "3+",
                "strength": "4",
                "ap": "-1",
                "damage": "1",
                "keywords": "Lethal Hits"
            }
        ],
        "abilities": [
            {
                "name": "Infected Outbreak",
                "description": "If you control an objective marker at the end of your Command phase and this unit is within range of that objective marker, that objective marker remains under your control, even if you have no models within range of it, until your opponent controls it at the start or end of any turn."
            },
            {
                "name": "Daemonic Icon",
                "description": "Models in the bearer\u2019s unit have a Leadership characteristic of 6+."
            },
            {
                "name": "Instrument of Chaos",
                "description": "Add 1 to Charge rolls made for the bearer\u2019s unit."
            }
        ]
    },
    "Plagueburst Crawler": {
        "stats": {
            "stat_movement": "10\"",
            "stat_toughness": 10,
            "stat_save": "2+",
            "stat_wounds": 12,
            "stat_leadership": "6+",
            "stat_oc": 3,
            "stat_invuln": "5+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Plagueburst mortar",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "D6+3",
                "skill": "3+",
                "strength": "8",
                "ap": "-1",
                "damage": "2",
                "keywords": "Blast, Indirect Fire, Lethal Hits"
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
                "name": "Rothail volley gun",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "3",
                "skill": "3+",
                "strength": "5",
                "ap": "0",
                "damage": "1",
                "keywords": "Lethal Hits, Rapid Fire 3"
            },
            {
                "name": "Heavy slugger",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "4",
                "skill": "3+",
                "strength": "5",
                "ap": "-1",
                "damage": "1",
                "keywords": "Lethal Hits"
            },
            {
                "name": "Entropy cannon",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "10",
                "ap": "-3",
                "damage": "D6+1",
                "keywords": "Lethal Hits"
            },
            {
                "name": "Plaguespitter",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "D6",
                "skill": "N/A",
                "strength": "6",
                "ap": "-1",
                "damage": "1",
                "keywords": "Anti-INFANTRY 2+, Ignores Cover, Torrent"
            }
        ],
        "abilities": [
            {
                "name": "Spore-laced Shock Waves",
                "description": "In your Shooting phase, each time you select a target for this model's Plagueburst mortar, roll one D6 for the target unit and every other enemy unit within 3\" of the target unit, adding 1 to that roll if the unit being rolled for is Afflicted. On a 6+, the unit being rolled for is struck by spores; after resolving all of this model's attacks against the target unit, each unit struck by spores suffers D3 mortal wounds."
            }
        ]
    },
    "Poxwalkers": {
        "stats": {
            "stat_movement": "5\"",
            "stat_toughness": 4,
            "stat_save": "7+",
            "stat_wounds": 1,
            "stat_leadership": "8+",
            "stat_oc": 1,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Improvised weapons",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "2",
                "skill": "5+",
                "strength": "3",
                "ap": "0",
                "damage": "1",
                "keywords": "Lethal Hits"
            }
        ],
        "abilities": [
            {
                "name": "Curse of the Walking Pox",
                "description": "Each time a Poxwalker model in this unit makes an attack that destroys an enemy model (excluding Monster and Vehicle models), after this unit has resolved its attacks, you can return one destroyed Poxwalker model to this unit.\n\nWhile Typhus is leading this unit, enemy models destroyed as a result of Typhus\u2019 Eater Plague ability count as enemy models destroyed by an attack made by a Poxwalker model in this unit for the purposes of this ability."
            }
        ]
    },
    "Rotigus": {
        "stats": {
            "stat_movement": "7\"",
            "stat_toughness": 12,
            "stat_save": "5+",
            "stat_wounds": 22,
            "stat_leadership": "6+",
            "stat_oc": 5,
            "stat_invuln": "4+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Streams of brackish filth",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "2D6",
                "skill": "N/A",
                "strength": "8",
                "ap": "-2",
                "damage": "1",
                "keywords": "Devastating Wounds, Ignores Cover, Torrent"
            },
            {
                "name": "\u27a4 Gnarlrod - strike",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "7",
                "skill": "2+",
                "strength": "10",
                "ap": "-3",
                "damage": "3",
                "keywords": "Lethal Hits, Psychic"
            },
            {
                "name": "\u27a4 Gnarlrod - sweep",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "14",
                "skill": "2+",
                "strength": "8",
                "ap": "-1",
                "damage": "1",
                "keywords": "Lethal Hits, Psychic"
            }
        ],
        "abilities": [
            {
                "name": "Virulent Blessing (Psychic)",
                "description": "At the start of the Fight phase, you can select one enemy unit within 24\" of and visible to this model. Until the end of the phase, each time an attack made by a Plague Legions model is allocated to a model in that unit, add 1 to the Damage characteristic of that attack."
            },
            {
                "name": "Deluge of Nurgle (Aura)",
                "description": "While an enemy unit is within 6\" of this model, subtract 2 from the Move characteristic and subtract 1 from the Objective Control characteristic of models in that unit."
            },
            {
                "name": "Damaged: 1-7 wounds remaining",
                "description": "While this model has 1-7 wounds remaining, each time this model makes an attack, subtract 1 from the Hit roll."
            }
        ]
    },
    "Tallyman": {
        "stats": {
            "stat_movement": "5\"",
            "stat_toughness": 6,
            "stat_save": "3+",
            "stat_wounds": 4,
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
                "attacks": "4",
                "skill": "3+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "-"
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
                "name": "\u27a4 Plasma pistol - supercharge",
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
                "name": "Malicious Calculations",
                "description": "While this model is leading a unit, each time a model in that unit makes an attack, you can ignore any or all modifiers to that attack's Ballistic Skill or Weapon Skill characteristics and/or any or all modifiers to the Hit roll."
            },
            {
                "name": "Seven-fold Chant",
                "description": "In your Command phase, if this model is on the battlefield, roll 2D6: on a 7+, you gain 1CP."
            },
            {
                "name": "Leader",
                "description": "This model can be attached to the following unit: Plague Marines\nYou can attach this model to a Plague Marines unit, even if one other Leader unit has already been attached to it (you cannot attach more than one of the same Leader to the same unit). If you do, and that Bodyguard unit is destroyed, the Leader units attached to it become separate units, with their original Starting Strengths."
            }
        ]
    },
    "Typhus": {
        "stats": {
            "stat_movement": "5\"",
            "stat_toughness": 7,
            "stat_save": "2+",
            "stat_wounds": 6,
            "stat_leadership": "6+",
            "stat_oc": 1,
            "stat_invuln": "4+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "\u27a4 Lakrimae - strike",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "6",
                "skill": "2+",
                "strength": "9",
                "ap": "-2",
                "damage": "3",
                "keywords": "Lethal Hits"
            },
            {
                "name": "\u27a4 Lakrimae - sweep",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "12",
                "skill": "2+",
                "strength": "6",
                "ap": "-1",
                "damage": "1",
                "keywords": "Lethal Hits"
            }
        ],
        "abilities": [
            {
                "name": "Leader",
                "description": "This model can be attached to the following units:\n\u25a0 Blightlord Terminators\n\u25a0 Deathshroud Terminators\n\u25a0 Poxwalkers"
            },
            {
                "name": "The Destroyer Hive",
                "description": "While this model is leading a unit, each time a melee attack targets that unit, subtract 1 from the Hit roll."
            },
            {
                "name": "Eater Plague (Psychic)",
                "description": "In your Shooting phase, you can select one enemy unit within 18\" of and visible to this Psyker (excluding units with the Lone Operative ability that are not part of an Attached unit and are not within 12\" of this Psyker and roll one D6: on a 1, this Psyker's unit suffers D3 mortal wounds; on a 2-5, that enemy unit suffers D6 mortal wounds; on a 6, that enemy unit suffers D3+3 mortal wounds."
            }
        ]
    }
}


class Command(BaseCommand):
    """Refresh Death Guard stat lines, weapon profiles, and abilities from BSData."""

    help = 'Refresh 11th Edition stats/weapons/abilities for Death Guard units.'

    def add_arguments(self, parser):
        """Add --dry-run flag."""
        parser.add_argument(
            '--dry-run', action='store_true',
            help='Preview changes without writing to the database.',
        )

    def handle(self, *args, **options):
        """Iterate DEATH_GUARD_DATASHEETS and refresh each unit's datasheet data."""
        dry_run = options['dry_run']
        updated = 0
        skipped = 0

        with transaction.atomic():
            for name, payload in DEATH_GUARD_DATASHEETS.items():
                try:
                    unit = UnitType.objects.get(name=name, faction__name='Death Guard')
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
