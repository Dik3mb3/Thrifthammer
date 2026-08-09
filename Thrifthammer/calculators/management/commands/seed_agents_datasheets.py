"""
Management command: seed_agents_datasheets

Refreshes stat lines, weapon profiles, and abilities for all Agents of the
Imperium units using 11th Edition data sourced from BSData/wh40k-11e
("Imperium - Agents of the Imperium.json") -- the same source used by
seed_agents_points.py.

Usage:
    python manage.py seed_agents_datasheets
    python manage.py seed_agents_datasheets --dry-run

Notes:
- Does NOT touch points_cost or category -- those are handled entirely by
  seed_agents_points.py. This command only refreshes stat_* fields,
  WeaponProfile rows, and UnitAbility rows.
- Per-field safety rule: a unit's stats/weapons/abilities are only
  overwritten when BSData actually has that data for it. If extraction
  found nothing, the existing DB value/rows are left untouched rather than
  blanked.
- Weapon profiles list EVERY weapon option reachable for a unit, each as
  its own row -- same as every other faction.
- All 24 active units (including the cross-faction shared-SKU rows --
  Deathwatch/Grey Knights/Sisters of Battle/Space Marines/Astra Militarum
  products reused under this faction, and the Greyfax/generic-Inquisitor
  same-faction shared SKU) resolved cleanly on the first pass using the
  full accumulated extraction methodology (top-level selectionEntries
  recursion, sharedProfiles fallback by name, infoLinks(type="profile")
  resolution by id) -- 0 missing stats, weapons, or abilities.
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from calculators.models import UnitAbility, UnitType, WeaponProfile

# (name -> {stats?, weapons?, abilities?}). Missing keys mean "no data
# found for this field -- leave existing DB data untouched."
AGENTS_DATASHEETS = {
    "Callidus Assassin": {
        "stats": {
            "stat_movement": "7\"",
            "stat_toughness": 4,
            "stat_save": "6+",
            "stat_wounds": 4,
            "stat_leadership": "6+",
            "stat_oc": 1,
            "stat_invuln": "4+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Neural shredder",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "D6",
                "skill": "N/A",
                "strength": "5",
                "ap": "-2",
                "damage": "1",
                "keywords": "Anti-INFANTRY 2+, Precision, Torrent"
            },
            {
                "name": "Phase sword and poison blades",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "5",
                "skill": "2+",
                "strength": "5",
                "ap": "-4",
                "damage": "2",
                "keywords": "Lethal Hits, Precision"
            }
        ],
        "abilities": [
            {
                "name": "Reign of Confusion",
                "description": "Once per turn, when your opponent targets a unit from their army within 12\u201d of this model with a stratagem, this model can use this ability. If you do increase the CP cost of that use of that stratagem by 1CP."
            },
            {
                "name": "Acrobatic Escape",
                "description": "- At the end of the Fight phase, if this unit is engaged, this unit can make a fall-back move of up to D6\".\n- At the end of your opponent\u2019s turn, if this unit is more than 3\" from all enemy units, you can use this ability. If you do:\n- Place this unit in strategic reserves.\n- This unit must make an ingress move in your next Movement phase (including in your first turn)."
            },
            {
                "name": "Shadow Assignment",
                "description": "This model cannot be selected as your WARLORD. If your army faction is AGENTS OF THE IMPERIUM, then during the Declare Battle Formations step, you can replace this model with a different OFFICIO ASSASSINORUM model, provided that the points value of the new model does not exceed the points value of the model it replaced. Your army cannot include duplicates of the same model (i.e. after replacing this model with this rule, your army cannot have more than 1 VINDICARE ASSASSIN, it cannot have more than 1 CULEXUS ASSASSIN, it cannot have more than 1 EVERSOR ASSASSIN and it cannot have more than 1 CALLIDUS ASSASSIN)."
            },
            {
                "name": "Decoy Targets",
                "description": "Twice per battle, in your Movement phase, you can select one other friendly INFANTRY model that is on the battlefield and not within Engagement Range of one or more enemy units. The selected model is destroyed (ignoring any rules that are triggered when a model is destroyed) and this model is removed from the battlefield and set up again as close as possible to where that destroyed model was and not within Engagement Range of one or more enemy units. This ability cannot be used more than once in the same battle round."
            }
        ]
    },
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
                "description": "This model has a transport capacity of 12 DEATHWATCH INFANTRY models."
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
    "Culexus Assassin": {
        "stats": {
            "stat_movement": "7\"",
            "stat_toughness": 4,
            "stat_save": "6+",
            "stat_wounds": 4,
            "stat_leadership": "6+",
            "stat_oc": 1,
            "stat_invuln": "4+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Life-draining touch",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "2+",
                "strength": "4",
                "ap": "-2",
                "damage": "2",
                "keywords": "Anti-PSYKER 2+, Devastating Wounds, Precision"
            },
            {
                "name": "Animus speculum",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "3",
                "skill": "2+",
                "strength": "5",
                "ap": "-2",
                "damage": "D3",
                "keywords": "Anti-PSYKER 2+, Assault, Precision, Psychic Assassin"
            }
        ],
        "abilities": [
            {
                "name": "Abomination",
                "description": "This model has the Feel No Pain 2+ ability against Psychic Attacks."
            },
            {
                "name": "Soulless Horror",
                "description": "Once per battle, at the start of any Command phase, this model can use this ability. If it does, each enemy unit within 9\" of this model must take a Battle-shock test, subtracting 1 from that test (or subtracting 2 if that unit is a PSYKER)."
            },
            {
                "name": "Etheric Emergence",
                "description": "In your Movement phase, when this model is set up on the battlefield using the Deep Strike ability, it can perform an etheric emergence. If it does, this model can be set up anywhere on the battlefield that is more than 6\" horizontally away from all enemy units, but until the end of the turn, it is not eligible to declare a charge."
            },
            {
                "name": "Shadow Assignment",
                "description": "This model cannot be selected as your WARLORD. If your army faction is AGENTS OF THE IMPERIUM, then during the Declare Battle Formations step, you can replace this model with a different OFFICIO ASSASSINORUM model, provided that the points value of the new model does not exceed the points value of the model it replaced. Your army cannot include duplicates of the same model (i.e. after replacing this model with this rule, your army cannot have more than 1 VINDICARE ASSASSIN, it cannot have more than 1 CULEXUS ASSASSIN, it cannot have more than 1 EVERSOR ASSASSIN and it cannot have more than 1 CALLIDUS ASSASSIN)."
            },
            {
                "name": "Esoteric Explosives",
                "description": "Each time this model is targeted with the Grenades Stratagem, 1 mortal wound is inflicted for each D6 roll of 3+ instead of for each 4+"
            }
        ]
    },
    "Deathwatch Kill Team": {
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
                "skill": "3+",
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
                "keywords": "Ignores cover, Torrent"
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
                "range": "18\"",
                "attacks": "2",
                "skill": "3+",
                "strength": "4",
                "ap": "0",
                "damage": "2",
                "keywords": "Assault"
            },
            {
                "name": "Black Shield blades",
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
                "name": "Combi-weapon",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "1",
                "skill": "4+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Anti-Infantry 4+, Devastating Wounds, Rapid Fire 1"
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
                "description": "Each time a model in this unit makes an attack, re-roll a Hit roll of 1. If the target of that attack does not have the IMPERIUM or CHAOS keywords, you can re-roll the Hit roll instead."
            },
            {
                "name": "Astartes shield",
                "description": "The bearer has a 4+ invulnerable save."
            }
        ]
    },
    "Eversor Assassin": {
        "stats": {
            "stat_movement": "9\"",
            "stat_toughness": 4,
            "stat_save": "6+",
            "stat_wounds": 4,
            "stat_leadership": "6+",
            "stat_oc": 1,
            "stat_invuln": "4+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Executioner pistol",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "4",
                "skill": "2+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Anti-INFANTRY 3+, Pistol, Precision, Sustained Hits 3"
            },
            {
                "name": "Power sword and neuro gauntlet",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "6",
                "skill": "2+",
                "strength": "5",
                "ap": "-2",
                "damage": "2",
                "keywords": "Anti-INFANTRY 3+, Precision, Sustained Hits 3"
            }
        ],
        "abilities": [
            {
                "name": "Frenzon",
                "description": "This model is eligible to shoot and declare a charge in a turn in which it Advanced."
            },
            {
                "name": "Overkill",
                "description": "Once per battle, in your Movement phase, this model can use this ability before it makes a Normal move. If it does, until the end of the turn, add 6\" to this model's Movement characteristic and add 3 to the Attacks characteristic of this model's melee weapons."
            },
            {
                "name": "Shadow Assignment",
                "description": "This model cannot be selected as your WARLORD. If your army faction is AGENTS OF THE IMPERIUM, then during the Declare Battle Formations step, you can replace this model with a different OFFICIO ASSASSINORUM model, provided that the points value of the new model does not exceed the points value of the model it replaced. Your army cannot include duplicates of the same model (i.e. after replacing this model with this rule, your army cannot have more than 1 VINDICARE ASSASSIN, it cannot have more than 1 CULEXUS ASSASSIN, it cannot have more than 1 EVERSOR ASSASSIN and it cannot have more than 1 CALLIDUS ASSASSIN)."
            },
            {
                "name": "Intra-neural Biotech",
                "description": "Once per battle round, you can target this model with the Heroic Intervention or Counter-offensive Stratagem for 0CP, and can do so even if you have already used that Stratagem on a different unit this phase."
            }
        ]
    },
    "Grey Knights Terminator Squad": {
        "stats": {
            "stat_movement": "5\"",
            "stat_toughness": 5,
            "stat_save": "2+",
            "stat_wounds": 3,
            "stat_leadership": "6+",
            "stat_oc": 2,
            "stat_invuln": "4+",
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
                "keywords": "Psychic, Sustained Hits 1"
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
                "name": "Rites of Teleportation",
                "description": "If one or more INQUISITOR units are attached to this unit during the Declare Battle Formations step, models in those units have the Deep Strike ability."
            },
            {
                "name": "Hammerhand (Psychic)",
                "description": "Each time this unit makes a Charge move, until the end of the turn, melee weapons equipped by models in this unit have the [LETHAL HITS] ability."
            },
            {
                "name": "Ancient's Banner",
                "description": "Add 1 to the Objective Control characteristic of models in the bearer's unit."
            },
            {
                "name": "Narthecium",
                "description": "In your Command phase, you can return 1 destroyed model (excluding CHARACTERS) to the bearer's unit."
            }
        ]
    },
    "Imperial Rhino": {
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
            }
        ],
        "abilities": [
            {
                "name": "Self-repair",
                "description": "At the start of your Command phase, this model regains 1 lost wound."
            }
        ]
    },
    "Inquisitor": {
        "stats": {
            "stat_movement": "6\"",
            "stat_toughness": 3,
            "stat_save": "4+",
            "stat_wounds": 4,
            "stat_leadership": "6+",
            "stat_oc": 1,
            "stat_invuln": "5+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Inquisitorial melee weapon",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "5",
                "skill": "3+",
                "strength": "4",
                "ap": "-2",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "Force weapon",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "3+",
                "strength": "5",
                "ap": "-2",
                "damage": "D3",
                "keywords": "Psychic"
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
                "name": "Combi-weapon",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "4",
                "ap": "-2",
                "damage": "1",
                "keywords": "Anti-INFANTRY 4+, Devastating Wounds, Rapid Fire 1"
            },
            {
                "name": "Psychic Shock Wave",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "2D6",
                "skill": "N/A",
                "strength": "3",
                "ap": "-2",
                "damage": "1",
                "keywords": "Devastating Wounds, Psychic, Torrent"
            }
        ],
        "abilities": [
            {
                "name": "Leader",
                "description": "This model can be attached to the following units: AQUILA KILL TEAM, BATTLELINE IMPERIUM INFANTRY, EXACTION SQUAD, GREY KNIGHTS TERMINATOR SQUAD, IMPERIAL NAVY BREACHERS, INQUISITORIAL AGENTS, SANCTIFIERS, SISTERS OF BATTLE SQUAD, SUBDUCTOR SQUAD, VIGILANT SQUAD"
            },
            {
                "name": "Authority of the Inquisition",
                "description": "While this model is leading a unit, it can embark within any Transport that its Bodyguard unit can embark within."
            },
            {
                "name": "Power of the Rosette",
                "description": "Each time you target this model\u2019s unit with a Stratagem, roll one D6: on a 3+, you gain 1CP."
            },
            {
                "name": "Blessed Wardings",
                "description": "While this model is leading a unit, models in that unit have a 6+ invulnerable save."
            },
            {
                "name": "Psychic gifts",
                "description": "The bearer has the PSYKER keyword."
            }
        ]
    },
    "Inquisitor Coteaz": {
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
                "name": "Psychic Blast",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "D6",
                "skill": "3+",
                "strength": "3",
                "ap": "-1",
                "damage": "1",
                "keywords": "Anti-DAEMON 4+, Anti-INFANTRY 5+, Devastating Wounds, Psychic"
            },
            {
                "name": "Nemesis daemon hammer",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "3",
                "skill": "3+",
                "strength": "9",
                "ap": "-3",
                "damage": "3",
                "keywords": "Psychic"
            }
        ],
        "abilities": [
            {
                "name": "Malefic Wardings (Psychic)",
                "description": "While this model is leading a unit, models in that unit have a 6+ invulnerable save, and 4+ invulnerable save against Psychic Attacks and attacks made by DAEMON models."
            },
            {
                "name": "Spy Network",
                "description": "Each time your opponent gains a CP as the result of an ability, roll one D6: on a 2+, you also gain 1CP."
            },
            {
                "name": "Leader",
                "description": "This model can be attached to the following units: BATTLELIINE IMPERIUM INFANTRY, EXACTION SQUAD, GREY KNIGHTS TERMINATOR SQUAD, IMPERIAL NAVY BREACHERS, INQUISITORIAL AGENTS, SUBDUCTOR SQUAD, VIGILANT SQUAD"
            },
            {
                "name": "Authority of the Inquisition",
                "description": "While this model is leading a unit, it can embark within any Transport that its Bodyguard unit can embark within."
            },
            {
                "name": "Glovodan Psyber-eagle",
                "description": "In your Command phase, you can select one enemy unit within 18\" of the bearer. Until the start of your next Command phase, that unit cannot have the Benefit of Cover."
            }
        ]
    },
    "Inquisitor Draxus": {
        "stats": {
            "stat_movement": "6\"",
            "stat_toughness": 3,
            "stat_save": "3+",
            "stat_wounds": 4,
            "stat_leadership": "6+",
            "stat_oc": 1,
            "stat_invuln": "5+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Dirgesinger",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "4",
                "skill": "3+",
                "strength": "4",
                "ap": "0",
                "damage": "2",
                "keywords": "Anti-INFANTRY 4+, Assault, Devastating Wounds"
            },
            {
                "name": "Psychic Tempest",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "6",
                "skill": "3+",
                "strength": "6",
                "ap": "0",
                "damage": "2",
                "keywords": "Psychic, Sustained Hits 2"
            },
            {
                "name": "Power fist",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "3",
                "skill": "3+",
                "strength": "6",
                "ap": "-2",
                "damage": "2",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Xenos Hunter",
                "description": "While this model is leading a unit, each time a model in that unit makes an attack that targets an enemy unit that does not have the IMPERIUM or CHAOS keywords, add 1 to the Hit roll."
            },
            {
                "name": "Psychic Veil (Psychic)",
                "description": "In your Command phase, this PSYKER can use this ability. If it does, roll one D6: on a 1, this PSYKER\u2019s unit suffers D3 mortal wounds; on a 2+, until the start of your next Command phase, this PSYKER\u2019s unit can only be selected as the target of a ranged attack if the attacking model is within 18\"."
            },
            {
                "name": "Leader",
                "description": "This model can be attached to the following units: AQUILA KILL TEAM, BATTLELINE IMPERIUM INFANTRY, EXACTION SQUAD, IMPERIAL NAVY BREACHERS, INQUISITORIAL AGENTS, SUBDUCTOR SQUAD, VIGILANT SQUAD"
            },
            {
                "name": "Authority of the Inquisition",
                "description": "While this model is leading a unit, it can embark within any Transport that its Bodyguard unit can embark within."
            }
        ]
    },
    "Inquisitor Greyfax": {
        "stats": {
            "stat_movement": "6\"",
            "stat_toughness": 3,
            "stat_save": "3+",
            "stat_wounds": 4,
            "stat_leadership": "6+",
            "stat_oc": 1,
            "stat_invuln": "5+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Castigation",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "8",
                "ap": "-2",
                "damage": "3",
                "keywords": "Anti-CHARACTER 4+, Devastating Wounds, Precision, Psychic"
            },
            {
                "name": "Condemnor stake",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Anti-PSYKER 2+, Devastating Wounds, Precision, Rapid Fire 1"
            },
            {
                "name": "Master-crafted power sword",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "3+",
                "strength": "4",
                "ap": "-2",
                "damage": "2",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Psyoculum",
                "description": "While this model is leading a unit, ranged weapons equipped by models in that unit have the [ANTI-PSYKER 4+] ability."
            },
            {
                "name": "No Mercy",
                "description": "While this model is leading a unit, each time a model in that unit makes an attack that targets a unit that is Below Half-strength, add 1 to the Hit roll."
            },
            {
                "name": "Leader",
                "description": "This model can be attached to the following units: EXACTION SQUAD, IMPERIUM BATTLELINE INFANTRY, IMPERIAL NAVY BREACHERS, INQUISITORIAL AGENTS, SISTERS OF BATTLE SQUAD, SUBDUCTOR SQUAD, VIGILANT SQUAD"
            },
            {
                "name": "Authority of the Inquisition",
                "description": "While this model is leading a unit, it can embark within any Transport that its Bodyguard unit can embark within."
            }
        ]
    },
    "Inquisitor Kroyle": {
        "stats": {
            "stat_movement": "12\"",
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
                "name": "Jindarii tox-cycler",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "1",
                "skill": "2+",
                "strength": "6",
                "ap": "-2",
                "damage": "2",
                "keywords": "Anti-Monster 2+, Heavy, Precision"
            },
            {
                "name": "Stubcarbine",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "2",
                "skill": "2+",
                "strength": "5",
                "ap": "-2",
                "damage": "2",
                "keywords": "Pistol"
            },
            {
                "name": "Butcher blade",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "5",
                "skill": "3+",
                "strength": "4",
                "ap": "-2",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "Garralisk's claws and teeth",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "4+",
                "strength": "5",
                "ap": "-1",
                "damage": "1",
                "keywords": "Extra Attacks"
            }
        ],
        "abilities": [
            {
                "name": "On My Signal, Fire!",
                "description": "After this unit has shot, you can select one enemy unit hit by those attacks. Until the end of the phase, each time an Agents of the Imperium or Imperium Infantry Battleline model from your army makes an attack that targets that enemy unit, you can re-roll the Hit roll."
            },
            {
                "name": "Tox-cycler",
                "description": "In your Shooting phase, after this unit has shot, if this model scored a hit with its Jindarii tox-cycler, until the end of the battle, add 2 to the Strength and Damage characteristics of that weapon (to a maximum Damage characteristic of 6)."
            }
        ]
    },
    "Inquisitorial Agents": {
        "stats": {
            "stat_movement": "6\"",
            "stat_toughness": 3,
            "stat_save": "5+",
            "stat_wounds": 1,
            "stat_leadership": "7+",
            "stat_oc": 1,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Agent melee weapon",
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
                "name": "Agent firearm",
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
                "name": "\u27a4 Plasma pistol - standard",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "7",
                "ap": "-1",
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
                "ap": "-2",
                "damage": "2",
                "keywords": "Hazardous, Pistol"
            },
            {
                "name": "Eviscerator",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "2",
                "skill": "3+",
                "strength": "6",
                "ap": "-2",
                "damage": "2",
                "keywords": "Devastating Wounds"
            },
            {
                "name": "Mystic stave",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "2",
                "skill": "3+",
                "strength": "5",
                "ap": "-1",
                "damage": "D3",
                "keywords": "Anti-INFANTRY 4+, Psychic"
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
                "name": "\u27a4 Plasma cannon - standard",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "D3",
                "skill": "4+",
                "strength": "7",
                "ap": "-1",
                "damage": "1",
                "keywords": "Blast, Heavy"
            },
            {
                "name": "\u27a4 Plasma cannon - supercharge",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "D3",
                "skill": "4+",
                "strength": "8",
                "ap": "-2",
                "damage": "2",
                "keywords": "Blast, Hazardous, Heavy"
            }
        ],
        "abilities": [
            {
                "name": "Loyal Henchmen",
                "description": "While an INQUISITOR model is leading this unit, each time an attack targets this unit, subtract 1 from the Wound roll."
            },
            {
                "name": "Inquisitorial Henchmen",
                "description": "If your Army Faction is not AGENTS OF THE IMPERIUM, then for each INQUISITOR unit you include in your army, you can include one INQUISITORIAL AGENTS unit in your army that does not count towards the number of RETINUE units your army can include."
            },
            {
                "name": "Tome-skull",
                "description": "Once per battle for each Tome-skull this unit is equipped with, at the start of any phase, you can select one other friendly AGENTS OF THE IMPERIUM unit that is Battle-shocked and within 6\" of this unit or one enemy unit within 6\" of this unit. If you select a friendly unit, that unit is no longer Battle-shocked. If you select an enemy unit, it must take a Battle-shock test."
            }
        ]
    },
    "Inquisitorial Chimera": {
        "stats": {
            "stat_movement": "10\"",
            "stat_toughness": 9,
            "stat_save": "3+",
            "stat_wounds": 11,
            "stat_leadership": "7+",
            "stat_oc": 2,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Lasgun array",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "6",
                "skill": "4+",
                "strength": "3",
                "ap": "0",
                "damage": "1",
                "keywords": "Rapid Fire 6"
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
                "name": "Heavy bolter",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "3",
                "skill": "4+",
                "strength": "5",
                "ap": "-1",
                "damage": "2",
                "keywords": "Sustained Hits 1"
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
                "name": "Storm bolter",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "2",
                "skill": "4+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Rapid Fire 2"
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
                "name": "Multi-laser",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "4",
                "skill": "4+",
                "strength": "6",
                "ap": "0",
                "damage": "1",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Rapid Deployment",
                "description": "Units can disembark from this TRANSPORT after it has Advanced. Units that do so count as having made a Normal move that phase, and cannot declare a charge in the same turn, but can otherwise act normally."
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
                "skill": "4+",
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
                "name": "Zealot",
                "description": "Once per battle, in the Fight phase, this model can use this ability. If it does, until the end of the phase, improve the Strength and Attacks characteristics of melee weapons equipped by this model by 3."
            },
            {
                "name": "Holy Hatred",
                "description": "While this model is leading a unit, melee weapons equipped by that unit have the [SUSTAINED HITS 1] ability."
            },
            {
                "name": "Support",
                "description": "This model can be attached to the following units: INQUISITORIAL AGENTS, IMPERIAL NAVY BREACHERS, SUBDUCTOR SQUAD, EXACTION SQUAD, VIGILANT SQUAD, SISTERS OF BATTLE SQUAD.\n\n\nYou can attach this model to an INQUISITORIAL AGENTS unit, even if one INQUISITOR unit has already been attached to it. If you do, and that Bodyguard unit is destroyed, the Leader units attached to it become separate units, with their original Starting Strength."
            }
        ]
    },
    "Navigator": {
        "stats": {
            "stat_movement": "6\"",
            "stat_toughness": 3,
            "stat_save": "5+",
            "stat_wounds": 3,
            "stat_leadership": "7+",
            "stat_oc": 1,
            "stat_invuln": "4+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Force-orb cane",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "3",
                "skill": "4+",
                "strength": "6",
                "ap": "-1",
                "damage": "D3",
                "keywords": "Psychic"
            },
            {
                "name": "Laspistol",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "1",
                "skill": "4+",
                "strength": "3",
                "ap": "0",
                "damage": "1",
                "keywords": "Pistol"
            }
        ],
        "abilities": [
            {
                "name": "Third Eye (Psychic)",
                "description": "At the start of your Shooting phase, select one enemy unit within 12\" of and visible to this model. That enemy unit must take a Battle-shock test, subtracting 2 from the result if it is an INFANTRY unit; if the test is failed, that enemy unit suffers 3 mortal wounds."
            },
            {
                "name": "Gaze into the Empyrean (Psychic)",
                "description": "Enemy units that are set up on the battlefield as Reinforcements cannot be set up within 12\" of this model."
            },
            {
                "name": "Leader",
                "description": "This model can be attached to the following units: IMPERIAL NAVY BREACHERS, VOIDSMEN-AT-ARMS"
            }
        ]
    },
    "Rogue Trader Entourage": {
        "stats": {
            "stat_movement": "6\"",
            "stat_toughness": 3,
            "stat_save": "4+",
            "stat_wounds": 4,
            "stat_leadership": "6+",
            "stat_oc": 1,
            "stat_invuln": "4+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Monomolecular cane-rapier",
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
                "name": "Household pistol",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "2",
                "skill": "3+",
                "strength": "5",
                "ap": "-2",
                "damage": "2",
                "keywords": "Pistol, Devastating Wounds"
            },
            {
                "name": "Dartmask",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "1",
                "skill": "4+",
                "strength": "2",
                "ap": "-1",
                "damage": "D3",
                "keywords": "Anti-INFANTRY 2+, Pistol, Precision"
            },
            {
                "name": "Death Cult power blade",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "5",
                "skill": "2+",
                "strength": "4",
                "ap": "-2",
                "damage": "1",
                "keywords": "Precision"
            },
            {
                "name": "Voltaic pistol",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "3",
                "skill": "3+",
                "strength": "4",
                "ap": "-2",
                "damage": "1",
                "keywords": "Pistol, Sustained Hits 2"
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
                "name": "Laspistol",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "1",
                "skill": "4+",
                "strength": "3",
                "ap": "0",
                "damage": "1",
                "keywords": "Pistol"
            }
        ],
        "abilities": [
            {
                "name": "Backroom Deals",
                "description": "If your army contains one or more units with this ability, during the Declare Battle Formations step, select one of those units. While the selected unit is leading a unit, models in that unit have the Infiltrators ability."
            },
            {
                "name": "Leader",
                "description": "This model can be attached to the following units: IMPERIAL NAVY BREACHERS, VOIDSMEN-AT-ARMS"
            },
            {
                "name": "Warrant of Trade",
                "description": "If your army contains one or more models with this ability, after both players have deployed their armies, select up to D3 IMPERIUM BATTLELINE units from your army and redeploy them. When doing so, you can set those units up in Strategic Reserve, regardless of how many units are already in Strategic Reserve."
            },
            {
                "name": "Healing Serum",
                "description": "At the start of your Command phase, if the bearer's unit is below its Starting Strength, you can return up to D3 destroyed models (excluding CHARACTERS) to the bearer's unit."
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
                "name": "Death Cult blades",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "2+",
                "strength": "4",
                "ap": "-2",
                "damage": "1",
                "keywords": "Precision"
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
                "name": "Ministorum hand flamer",
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
                "name": "Ministorum Sermon",
                "description": "While this unit contains a Ministorum Priest, each time a model in this unit makes a melee attack, add 1 to the Wound roll."
            },
            {
                "name": "Cherub",
                "description": "Once per battle, you can target this unit with the Command Re-roll Stratagem for 0CP, and can do so even if you have already targeted a different unit with that Stratagem this phase."
            },
            {
                "name": "Attached Unit",
                "description": "If a Ministorum Priest or Inquisitor model from your army with the Leader ability can be attached to a Sisters of Battle Squad, it can be attached to this unit instead. If a Ministorum Priest or Inquisitor model from your army is attached to this unit during the Declare Battle Formations step, that model gains the Scouts 6\" ability."
            },
            {
                "name": "Salvationist Medikit",
                "description": "In your Command phase, if the bearer is on the battlefield, you can return up to D3 destroyed models (excluding Character models) to this unit."
            },
            {
                "name": "Simulacrum Imperialis",
                "description": "Improve the Leadership characteristic of models in the bearer\u2019s unit by 1."
            }
        ]
    },
    "Sisters of Battle Immolator": {
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
                "name": "Heavy bolter",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "3",
                "skill": "4+",
                "strength": "5",
                "ap": "-1",
                "damage": "2",
                "keywords": "Sustained Hits 1"
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
                "name": "Immolation flamers",
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
                "name": "Twin heavy bolter",
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
                "name": "Twin multi-melta",
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
                "description": "This model has a transport capacity of 6 ORDO HERETICUS INFANTRY models.\n\nAt the start of the Declare Battle Formations step, you can select one SISTERS OF BATTLE SQUAD from your army. If you do, that unit is split into two units, each containing as equal a number of models as possible (when splitting a unit in this way, make a note of which models form each of the two new units). One of these units must start the battle embarked within this TRANSPORT; the other can start the battle embarked within another TRANSPORT, or it can be deployed as a separate unit."
            },
            {
                "name": "Purge and Cleanse",
                "description": "Each time this model has shot, select one enemy unit hit by one or more of those attacks. Until the end of the phase, that enemy unit cannot have the Benefit of Cover."
            }
        ]
    },
    "Sisters of Battle Squad": {
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
                "ap": "-1",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "Chainsword",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "3",
                "skill": "4+",
                "strength": "3",
                "ap": "-1",
                "damage": "1",
                "keywords": "-"
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
                "name": "Condemnor boltgun",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Anti-Psyker 2+, Devastating Wounds, Precision, Rapid Fire 1"
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
                "name": "Heavy bolter",
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
                "name": "Artificer-crafted storm bolter",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "2",
                "skill": "3+",
                "strength": "4",
                "ap": "0",
                "damage": "2",
                "keywords": "Rapid Fire 2"
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
                "name": "Multi-melta",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "2",
                "skill": "4+",
                "strength": "9",
                "ap": "-4",
                "damage": "D6",
                "keywords": "Heavy, Melta 2"
            }
        ],
        "abilities": [
            {
                "name": "Defenders of the Faith",
                "description": "If you control an objective marker at the end of your Command phase and this unit is within range of that objective marker, that objective marker remains under your control, even if you have no models in range of it, until your opponent controls it at the start or end of any turn."
            },
            {
                "name": "Incensor Cherub",
                "description": "Once per battle, you can target this unit with the Command Re-roll Stratagem for 0CP and can do so if you have already targeted a different unit with that Stratagem this phase."
            },
            {
                "name": "Simulacrum Imperialis",
                "description": "Improve the Leadership characteristic of models in the bearer's unit by 1."
            }
        ]
    },
    "Vindicare Assassin": {
        "stats": {
            "stat_movement": "7\"",
            "stat_toughness": 4,
            "stat_save": "6+",
            "stat_wounds": 4,
            "stat_leadership": "6+",
            "stat_oc": 1,
            "stat_invuln": "4+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Exitus pistol",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "3",
                "skill": "2+",
                "strength": "6",
                "ap": "-2",
                "damage": "3",
                "keywords": "Devastating Wounds, Ignores Cover, Pistol, Precision"
            },
            {
                "name": "Exitus rifle",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "1",
                "skill": "2+",
                "strength": "8",
                "ap": "-3",
                "damage": "D3+3",
                "keywords": "Devastating Wounds, Heavy, Ignores Cover, Precision"
            },
            {
                "name": "Vindicare combat knife",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "2+",
                "strength": "4",
                "ap": "-1",
                "damage": "1",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Shieldbreaker",
                "description": "Once per battle, when selecting targets for this model\u2019s exitus rifle, it can fire a shieldbreaker round. If it does, until the end of the phase, each time this model makes an attack with that weapon, add 1 to the Wound roll and any successful Wound roll scores a Critical Wound."
            },
            {
                "name": "Dead-shot",
                "description": "When this unit is selected to shoot, until this unit has shot:\n- Enemy units do not have Lone Operative.\n- Hidden enemy units have +15\" detection range.'"
            },
            {
                "name": "Shadow Assignment",
                "description": "This model cannot be selected as your WARLORD. If your army faction is AGENTS OF THE IMPERIUM, then during the Declare Battle Formations step, you can replace this model with a different OFFICIO ASSASSINORUM model, provided that the points value of the new model does not exceed the points value of the model it replaced. Your army cannot include duplicates of the same model (i.e. after replacing this model with this rule, your army cannot have more than 1 VINDICARE ASSASSIN, it cannot have more than 1 CULEXUS ASSASSIN, it cannot have more than 1 EVERSOR ASSASSIN and it cannot have more than 1 CALLIDUS ASSASSIN)."
            },
            {
                "name": "Micromelta Round",
                "description": "This model\u2019s exitus rifle has the [ANTI-MONSTER 4+] and [ANTI-VEHICLE 4+] abilities."
            }
        ]
    },
    "Voidsmen-at-Arms": {
        "stats": {
            "stat_movement": "6\"",
            "stat_toughness": 3,
            "stat_save": "4+",
            "stat_wounds": 1,
            "stat_leadership": "7+",
            "stat_oc": 2,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Artificer shotgun",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "2",
                "skill": "4+",
                "strength": "4",
                "ap": "0",
                "damage": "2",
                "keywords": "Assault"
            },
            {
                "name": "Laspistol",
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
                "name": "Vicious bite",
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
                "name": "Lasgun",
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
                "name": "Voidsman rotor cannon",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "6",
                "skill": "5+",
                "strength": "6",
                "ap": "0",
                "damage": "1",
                "keywords": "Heavy, Sustained Hits 1"
            }
        ],
        "abilities": [
            {
                "name": "Masters of Close Confines",
                "description": "Each time a model in this unit makes a ranged attack that targets the closest eligible target, that attack has the [LETHAL HITS] ability."
            },
            {
                "name": "Navy Bodyguards",
                "description": "If your Army Faction is not AGENTS OF THE IMPERIUM, then for each VOIDFARERS CHARACTER unit you include in your army, you can include one VOIDSMEN-AT-ARMS unit in your army that does not count towards the number of RETINUE units your army can include."
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
            "stat_invuln": "4+",
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
                "name": "Tactical Instinct",
                "description": "While this model is leading a unit, weapons equipped by models in that unit have the [LETHAL HITS] ability."
            },
            {
                "name": "Unstoppable Champion",
                "description": "The first time this model is destroyed, roll one D6 at the end of the phase. On a 2+, set this model back up on the battlefield, as close as possible to where it was destroyed and not within Engagement Range of any enemy units, with 1 wound remaining."
            },
            {
                "name": "Leader",
                "description": "This model can be attached to the following units: AQUILA KILL TEAM, DEATHWATCH KILL TEAM"
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
            "stat_invuln": "4+",
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
                "name": "Strategic Knowledge",
                "description": "While this model is leading a unit, that unit is eligible to shoot and declare a charge in a turn in which it Advanced or Fell Back."
            },
            {
                "name": "Rites of Battle",
                "description": "Once per battle round, one unit from your army with this ability can use it when its unit is targeted with a Stratagem. If it does, reduce the CP cost of that use of that Stratagem by 1CP."
            },
            {
                "name": "Leader",
                "description": "This model can be attached to the following units: AQUILA KILL TEAM, DEATHWATCH KILL TEAM"
            }
        ]
    }
}


class Command(BaseCommand):
    """Refresh Agents of the Imperium stat lines, weapon profiles, and abilities from BSData."""

    help = 'Refresh 11th Edition stats/weapons/abilities for Agents of the Imperium units.'

    def add_arguments(self, parser):
        """Add --dry-run flag."""
        parser.add_argument(
            '--dry-run', action='store_true',
            help='Preview changes without writing to the database.',
        )

    def handle(self, *args, **options):
        """Iterate AGENTS_DATASHEETS and refresh each unit's datasheet data."""
        dry_run = options['dry_run']
        updated = 0
        skipped = 0

        with transaction.atomic():
            for name, payload in AGENTS_DATASHEETS.items():
                try:
                    unit = UnitType.objects.get(name=name, faction__name='Agents of the Imperium')
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
