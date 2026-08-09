"""
Management command: seed_orks_datasheets

Refreshes stat lines, weapon profiles, and abilities for all Orks units
using 11th Edition data sourced from BSData/wh40k-11e (Orks.json) -- the
same source used by seed_orks_points.py.

Usage:
    python manage.py seed_orks_datasheets
    python manage.py seed_orks_datasheets --dry-run

Notes:
- Does NOT touch points_cost or category -- those are handled entirely by
  seed_orks_points.py. This command only refreshes stat_* fields,
  WeaponProfile rows, and UnitAbility rows.
- Per-field safety rule: a unit's stats/weapons/abilities are only
  overwritten when BSData actually has that data for it. If extraction
  found nothing for a given field, the existing DB value/rows are left
  untouched rather than blanked -- never destroy data with a failed lookup.
- Weapon profiles list EVERY weapon option reachable for a unit (not just
  a guessed "default" loadout), each as its own row -- per user direction,
  since determining a single canonical default from BattleScribe's nested
  wargear-choice tree is unreliable to automate.
- Known gaps, left untouched (existing data kept as-is):
  * Weapons: Ghazghkull Thraka, Boss Snikrot, Mozrog Skragbad, Zodgrod
    Wortsnagga -- their unique signature weapons aren't present in this
    catalogue file at all (likely defined in a separate shared library
    catalogue not yet pulled in).
  * Stats: Deffkoptas, Ghazghkull Thraka, Killa Kans, Mek Gunz -- stat
    profile not resolvable from this file's structure for these units.
  * Abilities: Kill Rig -- no ability profiles found.
"""

import re

from django.core.management.base import BaseCommand
from django.db import transaction

from calculators.models import UnitAbility, UnitType, WeaponProfile


def _clean_markdown(text):
    """
    Strip BSData's markdown-style formatting (**bold**, ^^highlight^^,
    *italic*) from ability text. Our templates render this as plain text
    with no markdown parser, so the literal asterisks/carets would
    otherwise show up on the page.
    """
    if not text:
        return text
    t = text.replace(' ', ' ')
    t = re.sub(r'\*\*(.*?)\*\*', r'\1', t)
    t = re.sub(r'\^\^(.*?)\^\^', r'\1', t)
    t = re.sub(r'\*(.*?)\*', r'\1', t)
    t = re.sub(r'[ \t]+', ' ', t)
    t = re.sub(r' *\n *', '\n', t)
    return t.strip()

# (name -> {stats?, weapons?, abilities?}). Missing keys mean "no data
# found for this field -- leave existing DB data untouched."
ORKS_DATASHEETS = {
    "Bannernob": {
        "stats": {
            "stat_movement": "6\"",
            "stat_toughness": 5,
            "stat_save": "4+",
            "stat_wounds": 4,
            "stat_leadership": "7+",
            "stat_oc": 6,
            "stat_invuln": "5+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Shoota",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "2",
                "skill": "5+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Rapid Fire 1"
            },
            {
                "name": "Choppa",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "5",
                "skill": "3+",
                "strength": "4",
                "ap": "-1",
                "damage": "1"
            }
        ],
        "abilities": [
            {
                "name": "Waaagh! Banner",
                "description": "- This unit has a 5+ InSv.\n- While the Waaagh! is active for this unit, this unit has\u00a0+1 T."
            },
            {
                "name": "Leader",
                "description": "This model can be attached to the following units:\u00a0\n- **BOYZ**\n- **BREAKA BOYZ**\n- **BURNA BOYZ**\n- **FLASH GITZ**\n- **LOOTAS**\n- **NOBZ**\n- **TANKBUSTAS**"
            }
        ]
    },
    "Battlewagon": {
        "stats": {
            "stat_movement": "10\"",
            "stat_toughness": 10,
            "stat_save": "3+",
            "stat_wounds": 16,
            "stat_leadership": "7+",
            "stat_oc": 5,
            "stat_invuln": "6+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Lobba",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "D6",
                "skill": "5+",
                "strength": "5",
                "ap": "0",
                "damage": "1",
                "keywords": "Blast, Indirect Fire"
            },
            {
                "name": "Wreckin' ball",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "1",
                "skill": "4+",
                "strength": "10",
                "ap": "0",
                "damage": "D6",
                "keywords": "Extra Attacks"
            },
            {
                "name": "Grabbin' klaw",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "2",
                "skill": "3+",
                "strength": "8",
                "ap": "-2",
                "damage": "2",
                "keywords": "Extra Attacks"
            },
            {
                "name": "Big shoota",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "3",
                "skill": "5+",
                "strength": "5",
                "ap": "0",
                "damage": "1",
                "keywords": "Rapid Fire 2"
            },
            {
                "name": "Killkannon",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "D6+1",
                "skill": "5+",
                "strength": "9",
                "ap": "-2",
                "damage": "2",
                "keywords": "-"
            },
            {
                "name": "Zzap gun",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "1",
                "skill": "5+",
                "strength": "D6+6",
                "ap": "-3",
                "damage": "5",
                "keywords": "Anti-Vehicle 4+"
            },
            {
                "name": "\u27a4 Kannon - shell",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "1",
                "skill": "5+",
                "strength": "10",
                "ap": "-2",
                "damage": "D6",
                "keywords": "-"
            },
            {
                "name": "\u27a4 Kannon - frag",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "D6+3",
                "skill": "5+",
                "strength": "6",
                "ap": "0",
                "damage": "1",
                "keywords": "Blast"
            },
            {
                "name": "Deff rolla",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "6",
                "skill": "3+",
                "strength": "9",
                "ap": "-1",
                "damage": "2",
                "keywords": "-"
            },
            {
                "name": "Tracks and wheels",
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
                "name": "Ramshackle but Rugged",
                "description": "Each time an attack is allocated to this model, worsen the Armour Penetration characteristic of that attack by 1."
            },
            {
                "name": "\u2019Ard Case",
                "description": "Add 2 to the bearer\u2019s Toughness characteristic, but it no longer has the Firing Deck ability."
            }
        ]
    },
    "Beast Snagga Boyz": {
        "stats": {
            "stat_movement": "6\"",
            "stat_toughness": 5,
            "stat_save": "5+",
            "stat_wounds": 1,
            "stat_leadership": "7+",
            "stat_oc": 2,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Slugga",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "1",
                "skill": "5+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Close-Quarters"
            },
            {
                "name": "Choppa",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "3",
                "skill": "3+",
                "strength": "5",
                "ap": "-1",
                "damage": "1",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Monster Hunters",
                "description": "Each time a model in this unit makes an attack that targets a MONSTER or VEHICLE unit, you can re-roll the Hit roll."
            }
        ]
    },
    "Beastboss": {
        "stats": {
            "stat_movement": "6\"",
            "stat_toughness": 5,
            "stat_save": "4+",
            "stat_wounds": 6,
            "stat_leadership": "6+",
            "stat_oc": 1,
            "stat_invuln": "5+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Beast Snagga klaw",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "3+",
                "strength": "10",
                "ap": "-2",
                "damage": "2",
                "keywords": "Anti-Monster 4+, Anti-Vehicle 4+"
            },
            {
                "name": "Shoota",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "2",
                "skill": "4+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Rapid Fire 1"
            },
            {
                "name": "Beastchoppa",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "6",
                "skill": "2+",
                "strength": "6",
                "ap": "-1",
                "damage": "2",
                "keywords": "Anti-Monster 4+, Anti-Vehicle 4+"
            }
        ],
        "abilities": [
            {
                "name": "Beastboss",
                "description": "While this model is leading a unit, each time a model in that unit makes a melee attack, add 1 to the Hit roll."
            },
            {
                "name": "Ferocious Rage",
                "description": "Each time this model makes a Charge move, until the end of the turn, melee weapons it is equipped with have the **[DEVASTATING WOUNDS]** ability."
            },
            {
                "name": "Leader",
                "description": "This model can be attached to the following unit:\n- **^^Beast Snagga Boyz^^**"
            }
        ]
    },
    "Beastboss on Squigosaur": {
        "stats": {
            "stat_movement": "10\"",
            "stat_toughness": 8,
            "stat_save": "3+",
            "stat_wounds": 8,
            "stat_leadership": "6+",
            "stat_oc": 3,
            "stat_invuln": "5+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Squigosaur\u2019s jaws",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "3",
                "skill": "4+",
                "strength": "7",
                "ap": "-2",
                "damage": "3",
                "keywords": "Devastating Wounds, Extra Attacks"
            },
            {
                "name": "Beastchoppa",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "6",
                "skill": "2+",
                "strength": "6",
                "ap": "-1",
                "damage": "2",
                "keywords": "Anti-Monster 4+, Anti-Vehicle 4+"
            },
            {
                "name": "Slugga",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "1",
                "skill": "5+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Close-quarters"
            },
            {
                "name": "Thump gun",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "D3",
                "skill": "5+",
                "strength": "6",
                "ap": "0",
                "damage": "2",
                "keywords": "Blast"
            }
        ],
        "abilities": [
            {
                "name": "Thundering Stampede",
                "description": "While this model is leading a unit, add 1 to Charge rolls made for that unit."
            },
            {
                "name": "Single-minded Predator",
                "description": "You can target this unit with the **Heroic Intervention stratagem**,\u00a0regardless of any other uses of that **stratagem** this phase. If you do:\n\u25aa That use is \u20111 CP.\n\u25aa That use does not prevent any uses of that **stratagem** on other units\u00a0this phase."
            }
        ]
    },
    "Big Mek": {
        "stats": {
            "stat_movement": "6\"",
            "stat_toughness": 5,
            "stat_save": "3+",
            "stat_wounds": 6,
            "stat_leadership": "7+",
            "stat_oc": 1,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Drilla",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "2",
                "skill": "3+",
                "strength": "12",
                "ap": "-3",
                "damage": "3",
                "keywords": "-"
            },
            {
                "name": "Power klaw",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "3+",
                "strength": "9",
                "ap": "-2",
                "damage": "2",
                "keywords": "-"
            },
            {
                "name": "Traktor blasta",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "1",
                "skill": "5+",
                "strength": "10",
                "ap": "-2",
                "damage": "D6+1",
                "keywords": "Anti-Fly 3+, Devastating Wounds"
            },
            {
                "name": "Kustom mega-blasta",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "3",
                "skill": "5+",
                "strength": "9",
                "ap": "-2",
                "damage": "D6",
                "keywords": "Hazardous"
            }
        ],
        "abilities": [
            {
                "name": "More Dakka",
                "description": "While this model is leading a unit, each time a model in that unit makes a ranged attack, re-roll a Hit roll of 1."
            },
            {
                "name": "Shokk-boosta",
                "description": "You can re\u2011roll Advance rolls made for this model\u2019s unit. In addition,\u00a0each time this model\u2019s unit makes a Normal, Advance or Fall Back move,\u00a0models in that unit can move through models and terrain features.\u00a0When doing so, they can move within Engagement Range of such\u00a0models but cannot end that move within Engagement Range of them,\u00a0and any Desperate Escape test is automatically passed."
            },
            {
                "name": "Leader",
                "description": "This model can be attached to the following units:\n- **BOYZ**\n- **BREAKA BOYZ**\n- **LOOTAS**\n- **MEK GUNZ**\n- **NOBZ**\n- **TANKBUSTAS**"
            }
        ]
    },
    "Big Mek Dakkarig": {
        "stats": {
            "stat_movement": "8\"",
            "stat_toughness": 8,
            "stat_save": "3+",
            "stat_wounds": 11,
            "stat_leadership": "7+",
            "stat_oc": 3,
            "stat_invuln": "5+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Stompy feet",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "3+",
                "strength": "6",
                "ap": "-1",
                "damage": "1"
            },
            {
                "name": "Blitzkannon",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "8",
                "skill": "5+",
                "strength": "7",
                "ap": "-2",
                "damage": "2",
                "keywords": "Heavy, Sustained Hits 1"
            },
            {
                "name": "Rokkit launcha",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "6",
                "skill": "5+",
                "strength": "10",
                "ap": "-2",
                "damage": "3",
                "keywords": "Heavy"
            }
        ],
        "abilities": [
            {
                "name": "Dakkablitz",
                "description": "In your Shooting phase, while making\u00a0attacks with this unit, if its blitzkannon targeted a\u00a0non\u2011**MONSTER/VEHICLE** unit, that weapon has +6 **A**."
            }
        ]
    },
    "Big Mek in Mega Armour": {
        "stats": {
            "stat_movement": "5\"",
            "stat_toughness": 6,
            "stat_save": "2+",
            "stat_wounds": 5,
            "stat_leadership": "7+",
            "stat_oc": 1,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Power klaw",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "3+",
                "strength": "9",
                "ap": "-2",
                "damage": "2",
                "keywords": "-"
            },
            {
                "name": "Tellyport blasta",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "3",
                "skill": "5+",
                "strength": "8",
                "ap": "-1",
                "damage": "3",
                "keywords": "Blast"
            },
            {
                "name": "Kustom mega-blasta",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "3",
                "skill": "5+",
                "strength": "9",
                "ap": "-2",
                "damage": "D6",
                "keywords": "Hazardous"
            },
            {
                "name": "Kustom shoota",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "4",
                "skill": "5+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Rapid Fire 2"
            },
            {
                "name": "Kombi-weapon",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "1",
                "skill": "5+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Anti-Infantry 4+, Devastating Wounds, Rapid Fire 1"
            },
            {
                "name": "Killsaw",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "3",
                "skill": "4+",
                "strength": "12",
                "ap": "-3",
                "damage": "2",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "More Dakka",
                "description": "While this model is leading a unit, each time a model in that unit makes a ranged attack, re-roll a Hit roll of 1."
            },
            {
                "name": "Fix Dat Armour Up",
                "description": "While this model is leading a unit, in your Command phase, you can return 1 destroyed Bodyguard model to that unit."
            },
            {
                "name": "Kustom Force Field",
                "description": "While the bearer is leading a unit, models in that unit have a 4+ invulnerable save against ranged attacks."
            },
            {
                "name": "Grot Oiler",
                "description": "Once per battle, at the end of your Movement phase, one model in the bearer\u2019s unit regains D3 lost wounds.\nDesigner\u2019s Note: Place a Grot Oiler token next to the unit, removing it once this ability has been used."
            }
        ]
    },
    "Big Mek with Shokk Attack Gun": {
        "stats": {
            "stat_movement": "6\"",
            "stat_toughness": 5,
            "stat_save": "4+",
            "stat_wounds": 5,
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
                "attacks": "4",
                "skill": "3+",
                "strength": "5",
                "ap": "0",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "Shokk attack gun",
                "weapon_type": "ranged",
                "range": "60\"",
                "attacks": "D6+1",
                "skill": "5+",
                "strength": "9",
                "ap": "-4",
                "damage": "D6",
                "keywords": "Blast, Heavy"
            }
        ],
        "abilities": [
            {
                "name": "More Dakka",
                "description": "While this model is leading a unit, each time a model in that unit makes a ranged attack, re-roll a Hit roll of 1."
            },
            {
                "name": "Deranged Snotling Assault",
                "description": "In your Shooting phase, after this model has shot, select one enemy unit hit by one or more of those attacks; that unit must take a Battle-shock test."
            },
            {
                "name": "Leader",
                "description": "This model can be attached to the following units:\n- **BOYZ**\n- **BREAKA BOYZ**\n- **LOOTAS**\n- **MEK GUNZ**\n- **NOBZ**\n- **TANKBUSTAS**"
            },
            {
                "name": "Grot Assistant",
                "description": "Once per battle, after rolling to determine how many attacks the bearer\u2019s shokk attack gun makes, you can re-roll that dice.\n\n**Designer\u2019s Note:** *Place a Grot Assistant token next to the bearer, removing it once this ability has been used.*"
            }
        ]
    },
    "Big'ed Bossbunka": {
        "stats": {
            "stat_movement": "-",
            "stat_toughness": 10,
            "stat_save": "3+",
            "stat_wounds": 12,
            "stat_leadership": "7+",
            "stat_oc": 0,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Big shoota",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "3",
                "skill": "5+",
                "strength": "5",
                "ap": "0",
                "damage": "1",
                "keywords": "Rapid Fire 2"
            }
        ],
        "abilities": [
            {
                "name": "Ramshackle Cover",
                "description": "Each time a ranged attack is allocated to a model, if that model is not fully visible to every model in the attacking unit because of this FORTIFICATION, that model has the Benefit of Cover against that attack."
            },
            {
                "name": "Shoutin\u2019 Pole (Aura)",
                "description": "While a friendly ORKS unit is within 6\" of this FORTIFICATION, improve the Leadership characteristic of models in that unit by 1."
            }
        ]
    },
    "Blitza-bommer": {
        "stats": {
            "stat_movement": "-",
            "stat_toughness": 9,
            "stat_save": "3+",
            "stat_wounds": 12,
            "stat_leadership": "7+",
            "stat_oc": None,
            "stat_invuln": "6+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Big shoota",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "3",
                "skill": "5+",
                "strength": "5",
                "ap": "0",
                "damage": "1",
                "keywords": "Rapid Fire 2"
            },
            {
                "name": "Twin supa-shoota",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "4",
                "skill": "5+",
                "strength": "6",
                "ap": "-1",
                "damage": "1",
                "keywords": "Rapid Fire 2, Sustained Hits 1, Twin-linked"
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
            }
        ],
        "abilities": [
            {
                "name": "Boom Bomb",
                "description": "At the end of your opponent\u2019s Fight phase, select one visible enemy\u00a0unit (excluding Lone Operative units) within 24\" of this unit, and roll\u00a0one D6 for that unit: On a 4+, that unit suffers D6 mortal wounds."
            }
        ]
    },
    "Boomdakka Snazzwagon": {
        "stats": {
            "stat_movement": "12\"",
            "stat_toughness": 7,
            "stat_save": "4+",
            "stat_wounds": 9,
            "stat_leadership": "7+",
            "stat_oc": 3,
            "stat_invuln": "6+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Mek speshul",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "12",
                "skill": "5+",
                "strength": "5",
                "ap": "-1",
                "damage": "1",
                "keywords": "Assault, Rapid Fire 4, Sustained Hits 1"
            },
            {
                "name": "Big shoota",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "3",
                "skill": "5+",
                "strength": "5",
                "ap": "0",
                "damage": "1",
                "keywords": "Rapid Fire 2"
            },
            {
                "name": "Grot blasta",
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
                "name": "Spiked wheels",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "4+",
                "strength": "7",
                "ap": "-1",
                "damage": "2",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Billowing Fumes (Aura)",
                "description": "While an enemy unit (excluding **MONSTER/VEHICLE** units) is within 6\" of\u00a0this unit, when that enemy unit is **selected to shoot**, that unit\u2019s targets\u00a0have the **benefit of cover** until that unit has shot."
            }
        ]
    },
    "Boss Snikrot": {
        "stats": {
            "stat_movement": "6\"",
            "stat_toughness": 5,
            "stat_save": "5+",
            "stat_wounds": 6,
            "stat_leadership": "6+",
            "stat_oc": 1,
            "stat_invuln": "5+",
            "stat_fnp": ""
        },
        "abilities": [
            {
                "name": "Red Skull Kommandos",
                "description": "This unit has +1 **Sv** against ranged attacks."
            },
            {
                "name": "Kunnin\u2019 Infiltrator (Once per battle, per army)",
                "description": "In your Movement\u00a0phase, if this unit is unengaged, you can use this ability. If you do:\n- Place this unit in strategic reserves.\n- This unit has **Deep Strike**.\n- This unit must make an **ingress move** this phase (including in\u00a0your first turn)."
            }
        ]
    },
    "Boyz": {
        "stats": {
            "stat_movement": "6\"",
            "stat_toughness": 5,
            "stat_save": "5+",
            "stat_wounds": 1,
            "stat_leadership": "7+",
            "stat_oc": 2,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Choppa",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "3",
                "skill": "3+",
                "strength": "4",
                "ap": "-1",
                "damage": "1"
            },
            {
                "name": "Slugga",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "1",
                "skill": "5+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Close-Quarters"
            },
            {
                "name": "Shoota",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "2",
                "skill": "5+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Rapid Fire 1"
            },
            {
                "name": "Big shoota",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "3",
                "skill": "5+",
                "strength": "5",
                "ap": "0",
                "damage": "1",
                "keywords": "Rapid Fire 2"
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
                "name": "Rokkit launcha",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "D3",
                "skill": "5+",
                "strength": "9",
                "ap": "-2",
                "damage": "3",
                "keywords": "Blast"
            },
            {
                "name": "Big choppa",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "3",
                "skill": "3+",
                "strength": "7",
                "ap": "-1",
                "damage": "2",
                "keywords": "-"
            },
            {
                "name": "Kustom shoota",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "4",
                "skill": "5+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Rapid Fire 2"
            },
            {
                "name": "Kombi-shoota",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "2",
                "skill": "5+",
                "strength": "4",
                "ap": "0",
                "damage": "1"
            },
            {
                "name": "Kombi-rokkit",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "1",
                "skill": "5+",
                "strength": "10",
                "ap": "-2",
                "damage": "3"
            },
            {
                "name": "Power klaw",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "3",
                "skill": "4+",
                "strength": "9",
                "ap": "-2",
                "damage": "2",
                "keywords": "-"
            },
            {
                "name": "Kombi-weapon",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "1",
                "skill": "5+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Anti-Infantry 4+, Devastating Wounds, Rapid Fire 1"
            }
        ],
        "abilities": [
            {
                "name": "Get Da Good Bitz",
                "description": "At the end of your Command phase, if this unit is within range of an objective marker you control, that objective marker remains under your control, even if you have no models within range of it, until your opponent controls it at the start or end of any turn."
            }
        ]
    },
    "Burna Boyz": {
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
                "name": "Burna",
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
                "name": "Big shoota",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "3",
                "skill": "5+",
                "strength": "5",
                "ap": "0",
                "damage": "1",
                "keywords": "Rapid Fire 2"
            },
            {
                "name": "Kustom mega-blasta",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "3",
                "skill": "5+",
                "strength": "9",
                "ap": "-2",
                "damage": "D6",
                "keywords": "Hazardous"
            },
            {
                "name": "Rokkit launcha",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "D3",
                "skill": "5+",
                "strength": "9",
                "ap": "-2",
                "damage": "3",
                "keywords": "Blast"
            }
        ],
        "abilities": [
            {
                "name": "Pyromaniaks",
                "description": "Each time a model in this unit makes a ranged attack with a burna that targets an enemy unit within 6\", re-roll a Wound roll of 1. If the target of that attack is also within range of an objective marker, you can re-roll the Wound roll instead."
            }
        ]
    },
    "Burna-bommer": {
        "stats": {
            "stat_movement": "-",
            "stat_toughness": 9,
            "stat_save": "3+",
            "stat_wounds": 12,
            "stat_leadership": "7+",
            "stat_oc": None,
            "stat_invuln": "6+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Twin big shoota",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "3",
                "skill": "5+",
                "strength": "5",
                "ap": "0",
                "damage": "1",
                "keywords": "Rapid Fire 2, Twin-linked"
            },
            {
                "name": "Twin supa-shoota",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "4",
                "skill": "5+",
                "strength": "6",
                "ap": "-1",
                "damage": "1",
                "keywords": "Rapid Fire 2, Sustained Hits 1, Twin-linked"
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
                "name": "Skorcha missile rack",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "2D6",
                "skill": "5+",
                "strength": "5",
                "ap": "-1",
                "damage": "1",
                "keywords": "Blast, Ignores Cover"
            }
        ],
        "abilities": [
            {
                "name": "Burna Bomb",
                "description": "At the end of your opponent\u2019s Fight phase, you can select one **visible**\u00a0enemy unit (excluding **Lone Operative** units) within 24\" of this unit:\n- Friendly **ORKS** units' ranged attacks that target that enemy unit have **[IGNORES COVER]** until the end of your next turn.\n- Roll one D6 for each model in that enemy unit:\n-- For each 6, that enemy unit suffers 1 **mortal wound**."
            }
        ]
    },
    "Dakkajet": {
        "stats": {
            "stat_movement": "-",
            "stat_toughness": 9,
            "stat_save": "3+",
            "stat_wounds": 12,
            "stat_leadership": "7+",
            "stat_oc": None,
            "stat_invuln": "6+",
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
                "name": "Twin supa-shoota",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "4",
                "skill": "5+",
                "strength": "6",
                "ap": "-1",
                "damage": "1",
                "keywords": "Rapid Fire 2, Sustained Hits 1, Twin-linked"
            }
        ],
        "abilities": [
            {
                "name": "Dakkastorm",
                "description": "Each time this model makes a ranged attack, every successful Hit roll scores a Critical Hit."
            }
        ]
    },
    "Deff Dread": {
        "stats": {
            "stat_movement": "8\"",
            "stat_toughness": 9,
            "stat_save": "2+",
            "stat_wounds": 8,
            "stat_leadership": "7+",
            "stat_oc": 3,
            "stat_invuln": "6+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Stompy feet",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "3+",
                "strength": "5",
                "ap": "0",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "Dread klaw",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "3+",
                "strength": "12",
                "ap": "-2",
                "damage": "3",
                "keywords": "Dead Choppy"
            },
            {
                "name": "Big shoota",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "3",
                "skill": "5+",
                "strength": "5",
                "ap": "0",
                "damage": "1",
                "keywords": "Rapid Fire 2"
            },
            {
                "name": "Kustom mega-blasta",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "3",
                "skill": "5+",
                "strength": "9",
                "ap": "-2",
                "damage": "D6",
                "keywords": "Hazardous"
            },
            {
                "name": "Rokkit launcha",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "D3",
                "skill": "5+",
                "strength": "9",
                "ap": "-2",
                "damage": "3",
                "keywords": "Blast"
            },
            {
                "name": "Skorcha",
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
                "name": "Piston-driven Brutality",
                "description": "Each time this model ends a Charge move, select one enemy unit\u00a0within Engagement Range of it and roll one D6: on a 2\u20115, that enemy\u00a0unit suffers D3 mortal wounds; on a 6, that enemy unit suffers D3+3\u00a0mortal wounds."
            }
        ]
    },
    "Deffkilla Wartrike": {
        "stats": {
            "stat_movement": "12\"",
            "stat_toughness": 6,
            "stat_save": "4+",
            "stat_wounds": 9,
            "stat_leadership": "6+",
            "stat_oc": 3,
            "stat_invuln": "5+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Deffkilla boomstikks",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "6",
                "skill": "5+",
                "strength": "5",
                "ap": "0",
                "damage": "1",
                "keywords": "Assault"
            },
            {
                "name": "\u27a4 Killa jet - burna",
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
                "name": "\u27a4 Killa jet - cutta",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "1",
                "skill": "5+",
                "strength": "9",
                "ap": "-4",
                "damage": "D6",
                "keywords": "Melta 2"
            },
            {
                "name": "Snagga klaw",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "3+",
                "strength": "10",
                "ap": "-2",
                "damage": "2",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Speedboss",
                "description": "While this model is leading a unit, each time a model in that unit makes a melee attack, add 1 to the Hit roll."
            },
            {
                "name": "Fuel-mixa Grot",
                "description": "Each time this model\u2019s unit Advances, do not make an Advance roll for it. Instead, until the end of the phase, add 6\" to the Move characteristic of models in that unit."
            },
            {
                "name": "Leader",
                "description": "This model can be attached to the following unit:\n- **NOBZ ON WARBIKES**\n- **SKORCHAS**\n- **WARBIKERS**\n- **WARBUGGIES**"
            }
        ]
    },
    "Deffkoptas": {
        "weapons": [
            {
                "name": "Kopta rokkits",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "D3",
                "skill": "5+",
                "strength": "9",
                "ap": "-2",
                "damage": "3",
                "keywords": "Blast, Twin-linked"
            },
            {
                "name": "Slugga",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "1",
                "skill": "5+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Close-quarters"
            },
            {
                "name": "Spinnin\u2019 blades",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "6",
                "skill": "3+",
                "strength": "5",
                "ap": "0",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "Kustom mega-blasta",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "3",
                "skill": "5+",
                "strength": "9",
                "ap": "-2",
                "damage": "D6",
                "keywords": "Hazardous"
            }
        ],
        "abilities": [
            {
                "name": "Deff from Above",
                "description": "Each time this unit ends a Normal move, you can select one enemy unit it moved over during that move and roll one D6 for each model in this unit: for each 4+, that enemy unit suffers 1 mortal wound."
            }
        ]
    },
    "Flash Gitz": {
        "stats": {
            "stat_movement": "6\"",
            "stat_toughness": 5,
            "stat_save": "4+",
            "stat_wounds": 2,
            "stat_leadership": "7+",
            "stat_oc": 1,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Choppa",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "3+",
                "strength": "5",
                "ap": "-1",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "Snazzgun",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "3",
                "skill": "5+",
                "strength": "6",
                "ap": "-1",
                "damage": "2",
                "keywords": "Heavy, Sustained Hits 1"
            }
        ],
        "abilities": [
            {
                "name": "Gun-crazy Show-offs",
                "description": "Each time a model in this unit targets the closest eligible target with its snazzgun, until the end of the phase, that weapon has an Attacks characteristic of 4."
            },
            {
                "name": "Ammo Runt",
                "description": "Once per battle, when this unit is selected to shoot, it can use this ability. If it does, until the end of the phase, ranged weapons equipped by models in this unit have the **[LETHAL HITS]** ability.\n\n**Designer\u2019s Note:** *Place an Ammo Runt token next to the unit, removing it after this ability has been used.*"
            }
        ]
    },
    "Ghazghkull Thraka": {
        "abilities": [
            {
                "name": "Supreme Commander",
                "description": "If this unit is in your army, its Ghazghkull Thraka model must be your **^^Warlord^^**."
            },
            {
                "name": "Prophet of Da Great Waaagh!",
                "description": "While this unit is leading a unit, each time a model in that unit makes\u00a0a melee attack, add 1 to the Hit roll and add 1 to the Wound roll and\u00a0if the Waaagh! is active for your army, a Critical Hit is scored on a\u00a0successful unmodified Hit roll of 5+."
            },
            {
                "name": "Ghazghkull\u2019s Waaagh! Banner (Aura)",
                "description": "While a friendly **ORKS** unit is within 12\" of Makari, if the Waaagh! is\u00a0active for your army, melee weapons equipped by models in that unit\u00a0have the **[LETHAL HITS]** ability."
            },
            {
                "name": "Leader",
                "description": "This unit can be attached to the following units:\n- **BOYZ**\n- **BREAKA BOYZ**\n- **MEGANOBZ**\n- **NOBZ**"
            }
        ]
    },
    "Gorkanaut": {
        "stats": {
            "stat_movement": "8\"",
            "stat_toughness": 12,
            "stat_save": "3+",
            "stat_wounds": 20,
            "stat_leadership": "7+",
            "stat_oc": 8,
            "stat_invuln": "6+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Deffstorm mega-shoota",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "20",
                "skill": "5+",
                "strength": "6",
                "ap": "-1",
                "damage": "1",
                "keywords": "Rapid Fire 10"
            },
            {
                "name": "\u27a4 Klaw of Gork - strike",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "5",
                "skill": "3+",
                "strength": "18",
                "ap": "-3",
                "damage": "6",
                "keywords": "-"
            },
            {
                "name": "\u27a4 Klaw of Gork - sweep",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "15",
                "skill": "3+",
                "strength": "8",
                "ap": "-1",
                "damage": "2",
                "keywords": "-"
            },
            {
                "name": "Rokkit launcha",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "D3",
                "skill": "5+",
                "strength": "9",
                "ap": "-2",
                "damage": "3",
                "keywords": "Blast"
            },
            {
                "name": "Skorcha",
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
                "name": "Twin big shoota",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "3",
                "skill": "5+",
                "strength": "5",
                "ap": "0",
                "damage": "1",
                "keywords": "Rapid Fire 2, Twin-linked"
            }
        ],
        "abilities": [
            {
                "name": "Clankin\u2019 Forward",
                "description": "Each time this model makes a Normal, Advance or Fall Back move, it can move over enemy models (excluding MONSTER and VEHICLE models) and terrain features that are 4\" or less in height as if they were not there."
            },
            {
                "name": "Big an\u2019 Stompy",
                "description": "Each time this model makes a melee attack, if the Waaagh! is active for your army, add 1 to the Hit roll."
            }
        ]
    },
    "Gretchin": {
        "stats": {
            "stat_movement": "6\"",
            "stat_toughness": 5,
            "stat_save": "5+",
            "stat_wounds": 2,
            "stat_leadership": "7+",
            "stat_oc": 1,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Slugga",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "1",
                "skill": "5+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Close-quarters"
            }
        ],
        "abilities": [
            {
                "name": "Runtherd",
                "description": "Each time an attack targets this unit, if it contains one or more Gretchin models, until that attack is resolved, Runtherd models in this unit have a Toughness characteristic of 2."
            },
            {
                "name": "Thievin\u2019 Scavengers",
                "description": "At the start of your Movement phase, roll one D6 for each objective\u00a0marker you control that has one or more units from your army with this\u00a0ability within range of it (excluding Battle\u2011shocked units). If one or more\u00a0of those rolls is a 4+, you gain 1CP."
            }
        ]
    },
    "Hunta Rig": {
        "stats": {
            "stat_movement": "10\"",
            "stat_toughness": 10,
            "stat_save": "3+",
            "stat_wounds": 16,
            "stat_leadership": "7+",
            "stat_oc": 5,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "\u2019Eavy lobba",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "D6",
                "skill": "5+",
                "strength": "6",
                "ap": "0",
                "damage": "2",
                "keywords": "Blast, Indirect Fire"
            },
            {
                "name": "Butcha boyz",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "3+",
                "strength": "5",
                "ap": "-1",
                "damage": "1",
                "keywords": "Anti-Monster 4+, Anti-Vehicle 4+, Extra Attacks"
            },
            {
                "name": "Savage horns and hooves",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "4+",
                "strength": "8",
                "ap": "-1",
                "damage": "3",
                "keywords": "Extra Attacks, Lance"
            },
            {
                "name": "Saw blades",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "6",
                "skill": "3+",
                "strength": "10",
                "ap": "-2",
                "damage": "2",
                "keywords": "-"
            },
            {
                "name": "Stikka kannon",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "1",
                "skill": "5+",
                "strength": "12",
                "ap": "-2",
                "damage": "3",
                "keywords": "Anti-Monster 2+, Anti-Vehicle 2+, Snagged"
            }
        ],
        "abilities": [
            {
                "name": "On Da Hunt",
                "description": "For each model embarked within this TRANSPORT, add 1 to the Attacks characteristic of this model\u2019s butcha boyz weapon (to a maximum of +6)."
            }
        ]
    },
    "Kill Rig": {
        "stats": {
            "stat_movement": "10\"",
            "stat_toughness": 10,
            "stat_save": "3+",
            "stat_wounds": 16,
            "stat_leadership": "7+",
            "stat_oc": 5,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Wurrtower",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "D3",
                "skill": "N/A",
                "strength": "12",
                "ap": "-3",
                "damage": "D6",
                "keywords": "Hazardous, Psychic, Torrent"
            },
            {
                "name": "\u2019Eavy lobba",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "D6",
                "skill": "5+",
                "strength": "6",
                "ap": "0",
                "damage": "2",
                "keywords": "Blast, Indirect Fire"
            },
            {
                "name": "Butcha boyz",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "3+",
                "strength": "5",
                "ap": "-1",
                "damage": "1",
                "keywords": "Anti-Monster 4+, Anti-Vehicle 4+, Extra Attacks"
            },
            {
                "name": "Savage horns and hooves",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "4+",
                "strength": "8",
                "ap": "-1",
                "damage": "3",
                "keywords": "Extra Attacks, Lance"
            },
            {
                "name": "Saw blades",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "6",
                "skill": "3+",
                "strength": "10",
                "ap": "-2",
                "damage": "2",
                "keywords": "-"
            },
            {
                "name": "Stikka kannon",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "1",
                "skill": "5+",
                "strength": "12",
                "ap": "-2",
                "damage": "3",
                "keywords": "Anti-Monster 2+, Anti-Vehicle 2+, Snagged"
            }
        ]
    },
    "Killa Kans": {
        "weapons": [
            {
                "name": "Kan shoota",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "3",
                "skill": "4+",
                "strength": "5",
                "ap": "0",
                "damage": "1",
                "keywords": "Devastating Wounds, Rapid Fire 2"
            },
            {
                "name": "Kan klaw",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "3",
                "skill": "4+",
                "strength": "8",
                "ap": "-2",
                "damage": "3",
                "keywords": "-"
            },
            {
                "name": "Grotzooka",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "D3+3",
                "skill": "4+",
                "strength": "6",
                "ap": "-1",
                "damage": "1",
                "keywords": "Blast, Ignores Cover"
            },
            {
                "name": "Rokkit launcha",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "D3",
                "skill": "4+",
                "strength": "9",
                "ap": "-2",
                "damage": "3",
                "keywords": "Blast"
            },
            {
                "name": "Skorcha",
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
                "name": "Shooty Power Trip",
                "description": "Each time this unit is selected to shoot, you can roll one D6:\n- On a 1\u20112, this unit suffers D3 mortal wounds.\n- On a 3\u20114, until the end of the phase, add 1 to the Strength\u00a0characteristic of ranged weapons equipped by models in this unit.\n- On a 5\u20116, until the end of the phase, add 1 to the Attacks characteristic\u00a0of ranged weapons equipped by models in this unit."
            }
        ]
    },
    "Kommandos": {
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
                "name": "Slugga",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "1",
                "skill": "5+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Close-Quarters"
            },
            {
                "name": "Choppa",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "3",
                "skill": "3+",
                "strength": "4",
                "ap": "-1",
                "damage": "1"
            },
            {
                "name": "Kustom shoota",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "4",
                "skill": "5+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Rapid Fire 2"
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
                "name": "Burna",
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
                "name": "Rokkit launcha",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "D3",
                "skill": "5+",
                "strength": "9",
                "ap": "-2",
                "damage": "3",
                "keywords": "Blast"
            },
            {
                "name": "Power klaw",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "3",
                "skill": "4+",
                "strength": "9",
                "ap": "-2",
                "damage": "2",
                "keywords": "-"
            },
            {
                "name": "Big choppa",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "3+",
                "strength": "7",
                "ap": "-1",
                "damage": "2",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Sneaky Gitz",
                "description": "Enemy units cannot target this unit with **snap shooting** attacks."
            },
            {
                "name": "Patrol Squad",
                "description": "At the start of the Declare Battle\u00a0Formations step this unit can be split into two units, each containing\u00a0five models. (when splitting a unit in this way, make a note of which\u00a0models form each of the two new units. If you are splitting a unit that\u00a0is equipped with 1 bomb squig and/or 1 distraction grot, only one of\u00a0the new units can use that ability during the battle \u2013 make a note of\u00a0which of the new units this will be)."
            },
            {
                "name": "Distraction Grot",
                "description": "Once per battle, in your opponent\u2019s Shooting phase, before making a saving throw for a model in this unit, it can deploy the distraction grot. If it does, until the end of the phase, models in this unit have a 5+ invulnerable save.\n\n**Designer\u2019s Note:** *Place a Distraction Grot token next to the unit, removing it when this unit uses this ability.*"
            }
        ]
    },
    "Kustom Boosta-blasta": {
        "stats": {
            "stat_movement": "12\"",
            "stat_toughness": 7,
            "stat_save": "4+",
            "stat_wounds": 9,
            "stat_leadership": "7+",
            "stat_oc": 3,
            "stat_invuln": "6+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Burna exhausts",
                "weapon_type": "ranged",
                "range": "6\"",
                "attacks": "2D6",
                "skill": "N/A",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Ignores Cover, Torrent, Twin-linked"
            },
            {
                "name": "Rivet kannon",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "6",
                "skill": "5+",
                "strength": "8",
                "ap": "-1",
                "damage": "2",
                "keywords": "Assault, Rapid Fire 3"
            },
            {
                "name": "Grot blasta",
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
                "name": "Spiked wheels",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "4+",
                "strength": "7",
                "ap": "-1",
                "damage": "2",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Rivetin\u2019 Dakka",
                "description": "In your Shooting phase, after this model has shot, select one enemy unit hit by one or more of those attacks made with a rivet kannon. Until the start of your next turn, that enemy unit is suppressed. While a unit is suppressed, each time a model in that unit makes a ranged attack, subtract 1 from the Hit roll."
            }
        ]
    },
    "Lootas": {
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
                "name": "Big shoota",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "3",
                "skill": "5+",
                "strength": "5",
                "ap": "0",
                "damage": "1",
                "keywords": "Rapid Fire 2"
            },
            {
                "name": "Kustom mega-blasta",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "3",
                "skill": "5+",
                "strength": "9",
                "ap": "-2",
                "damage": "D6",
                "keywords": "Hazardous"
            },
            {
                "name": "Rokkit launcha",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "D3",
                "skill": "5+",
                "strength": "9",
                "ap": "-2",
                "damage": "3",
                "keywords": "Blast"
            }
        ],
        "abilities": [
            {
                "name": "Dat\u2019s Our Loot!",
                "description": "Each time a model in this unit makes a ranged attack, re-roll a Hit roll of 1. If that attack targets a unit that is within range of an objective marker, you can re-roll the Hit roll instead."
            }
        ]
    },
    "Meganobz": {
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
                "name": "Kustom shoota",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "4",
                "skill": "5+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Rapid Fire 2"
            },
            {
                "name": "Power klaw",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "3",
                "skill": "4+",
                "strength": "9",
                "ap": "-2",
                "damage": "2",
                "keywords": "-"
            },
            {
                "name": "Kombi-weapon",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "1",
                "skill": "5+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Anti-Infantry 4+, Devastating Wounds, Rapid Fire 1"
            },
            {
                "name": "Killsaw",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "2",
                "skill": "4+",
                "strength": "12",
                "ap": "-3",
                "damage": "2",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Krumpin\u2019 Time",
                "description": "While the Waaagh! is active for your army, models in this unit have the\u00a0Feel No Pain 5+ ability."
            }
        ]
    },
    "Megatrakk Scrapjet": {
        "stats": {
            "stat_movement": "12\"",
            "stat_toughness": 7,
            "stat_save": "4+",
            "stat_wounds": 9,
            "stat_leadership": "7+",
            "stat_oc": 3,
            "stat_invuln": "6+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Nose drill",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "4+",
                "strength": "8",
                "ap": "-1",
                "damage": "2",
                "keywords": "-"
            },
            {
                "name": "Rokkit cannon",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "D6+1",
                "skill": "5+",
                "strength": "9",
                "ap": "-2",
                "damage": "3",
                "keywords": "Blast"
            },
            {
                "name": "Wing missiles",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "1",
                "skill": "5+",
                "strength": "9",
                "ap": "-2",
                "damage": "3",
                "keywords": "-"
            },
            {
                "name": "Twin big shoota",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "3",
                "skill": "5+",
                "strength": "5",
                "ap": "0",
                "damage": "1",
                "keywords": "Rapid Fire 2, Twin-linked"
            }
        ],
        "abilities": [
            {
                "name": "Drill Through",
                "description": "Each time this model ends a Charge move, select one enemy unit within Engagement Range of it and roll one D6: on a 2-5, that enemy unit suffers D3 mortal wounds; on a 6, that enemy unit suffers 3 mortal wounds."
            }
        ]
    },
    "Mek": {
        "stats": {
            "stat_movement": "6\"",
            "stat_toughness": 5,
            "stat_save": "5+",
            "stat_wounds": 4,
            "stat_leadership": "7+",
            "stat_oc": 1,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Kustom mega-slugga",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "D3",
                "skill": "5+",
                "strength": "8",
                "ap": "-2",
                "damage": "D6",
                "keywords": "Blast, Hazardous"
            },
            {
                "name": "Wrench",
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
                "name": "Killsaw",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "1",
                "skill": "4+",
                "strength": "12",
                "ap": "-3",
                "damage": "2",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Know-wotz",
                "description": "While this model is within 3\" of one or more friendly ORKS VEHICLE units, this model has the Lone Operative ability."
            },
            {
                "name": "Mekaniak",
                "description": "At the end of your Movement phase, you can select one friendly ORKS VEHICLE model within 3\" of this model. That VEHICLE model regains up to D3 lost wounds, and, until the start of your next Movement phase, each time that VEHICLE model makes an attack, add 1 to the Hit roll. Each model can only be selected for this ability once per turn."
            },
            {
                "name": "Leader",
                "description": "This model can be attached to the following units:\n- **BOYZ**\n- **LOOTAS**\n- **MEK GUNZ**\n- **NOBZ**\n- **TANKBUSTAS**"
            }
        ]
    },
    "Mek Gunz": {
        "weapons": [
            {
                "name": "Smasha gun",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "D3+1",
                "skill": "4+",
                "strength": "9",
                "ap": "-3",
                "damage": "3",
                "keywords": "Blast"
            },
            {
                "name": "Grot crew",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "6",
                "skill": "5+",
                "strength": "2",
                "ap": "0",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "1-2 Bubblechukka - big bubble",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "2D6",
                "skill": "4+",
                "strength": "6",
                "ap": "-1",
                "damage": "1",
                "keywords": "Blast, Bubblechukka"
            },
            {
                "name": "3-4 Bubblechukka - wobbly bubble",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "D6",
                "skill": "4+",
                "strength": "9",
                "ap": "-2",
                "damage": "3",
                "keywords": "Blast, Bubblechukka"
            },
            {
                "name": "5-6 Bubblechukka - dense bubble",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "D3",
                "skill": "4+",
                "strength": "12",
                "ap": "-3",
                "damage": "D6+3",
                "keywords": "Blast, Bubblechukka"
            },
            {
                "name": "Kustom mega-kannon",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "D6",
                "skill": "4+",
                "strength": "12",
                "ap": "-1",
                "damage": "D6",
                "keywords": "Blast, Hazardous"
            },
            {
                "name": "Traktor kannon",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "1",
                "skill": "4+",
                "strength": "10",
                "ap": "-2",
                "damage": "D6+1",
                "keywords": "Anti-Fly 2+, Devastating Wounds"
            }
        ],
        "abilities": [
            {
                "name": "Splat!",
                "description": "Each time a model in this unit makes a ranged attack that targets a unit that is at its Starting Strength (excluding MONSTERS and VEHICLES), re-roll a Hit roll of 1."
            }
        ]
    },
    "Morkanaut": {
        "stats": {
            "stat_movement": "8\"",
            "stat_toughness": 12,
            "stat_save": "3+",
            "stat_wounds": 20,
            "stat_leadership": "7+",
            "stat_oc": 8,
            "stat_invuln": "5+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "\u27a4 Klaw of Mork - strike",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "3+",
                "strength": "18",
                "ap": "-3",
                "damage": "6",
                "keywords": "-"
            },
            {
                "name": "\u27a4 Klaw of Mork - sweep",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "12",
                "skill": "3+",
                "strength": "8",
                "ap": "-1",
                "damage": "2",
                "keywords": "-"
            },
            {
                "name": "Kustom mega-zappa",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "D6+3",
                "skill": "5+",
                "strength": "10",
                "ap": "-2",
                "damage": "D6",
                "keywords": "Blast, Hazardous"
            },
            {
                "name": "Kustom mega-blasta",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "3",
                "skill": "5+",
                "strength": "9",
                "ap": "-2",
                "damage": "D6",
                "keywords": "Hazardous"
            },
            {
                "name": "Rokkit launcha",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "D3",
                "skill": "5+",
                "strength": "9",
                "ap": "-2",
                "damage": "3",
                "keywords": "Blast"
            },
            {
                "name": "Twin big shoota",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "3",
                "skill": "5+",
                "strength": "5",
                "ap": "0",
                "damage": "1",
                "keywords": "Rapid Fire 2, Twin-linked"
            }
        ],
        "abilities": [
            {
                "name": "Clankin\u2019 Forward",
                "description": "Each time this model makes a Normal, Advance or Fall Back move, it can move over enemy models (excluding MONSTER and VEHICLE models) and terrain features that are 4\" or less in height as if they were not there."
            },
            {
                "name": "Big an\u2019 Shooty",
                "description": "Each time this model makes a ranged attack, if the Waaagh! is active for\u00a0your army, add 1 to the Hit roll."
            }
        ]
    },
    "Mozrog Skragbad": {
        "stats": {
            "stat_movement": "10\"",
            "stat_toughness": 8,
            "stat_save": "3+",
            "stat_wounds": 8,
            "stat_leadership": "6+",
            "stat_oc": 3,
            "stat_invuln": "4+",
            "stat_fnp": ""
        },
        "abilities": [
            {
                "name": "Da Bigger Dey Iz\u2026",
                "description": "Each time this model makes an attack that targets a **^^Monster^^** or **^^Vehicle^^** unit, add 1 to the Damage characteristic of that attack. Each time this model makes an attack that targets a **^^Titanic^^** unit, add 2 to the Damage characteristic of that attack instead."
            },
            {
                "name": "One Last Kill",
                "description": "While this model is leading a unit, each time a model in that unit is destroyed by a melee attack, if it has not fought this phase, roll on D6; on a 4+, do not remove it from play. The destroyed model can fight after the attacking unit has finished making its attacks, and is then removed from play."
            },
            {
                "name": "Leader",
                "description": "This model can be attached to the following unit:\n- **^^Squighog Boyz^^**"
            }
        ]
    },
    "Nobz": {
        "stats": {
            "stat_movement": "6\"",
            "stat_toughness": 5,
            "stat_save": "4+",
            "stat_wounds": 2,
            "stat_leadership": "7+",
            "stat_oc": 1,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Slugga",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "1",
                "skill": "5+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Close-Quarters"
            },
            {
                "name": "Big choppa",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "3",
                "skill": "3+",
                "strength": "7",
                "ap": "-1",
                "damage": "2",
                "keywords": "-"
            },
            {
                "name": "Power klaw",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "3",
                "skill": "4+",
                "strength": "9",
                "ap": "-2",
                "damage": "2",
                "keywords": "-"
            },
            {
                "name": "Close combat weapon",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "3",
                "skill": "3+",
                "strength": "5",
                "ap": "0",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "Kombi-weapon",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "1",
                "skill": "5+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Anti-Infantry 4+, Devastating Wounds, Rapid Fire 1"
            }
        ],
        "abilities": [
            {
                "name": "Da Boss\u2019 Ladz",
                "description": "While a WARBOSS model is leading this unit, each time an attack targets this unit, if the Strength characteristic of that attack is greater than the Toughness characteristic of this unit, subtract 1 from the Wound roll."
            },
            {
                "name": "Ammo Runt",
                "description": "Once per battle for each ammo runt this unit has, when this unit is selected to shoot, it can use this ability. If it does, until the end of the phase, ranged weapons equipped by models in this unit have the [LETHAL HITS] ability.\nDesigner\u2019s Note: Place the relevant number of Ammo Runt tokens next to the unit, removing one each time the unit uses this ability."
            }
        ]
    },
    "Ork Gargantuan Squiggoth": {
        "stats": {
            "stat_movement": "10\"",
            "stat_toughness": 13,
            "stat_save": "3+",
            "stat_wounds": 30,
            "stat_leadership": "7+",
            "stat_oc": 12,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "\u27a4 Huge tusks - strike",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "6",
                "skill": "3+",
                "strength": "14",
                "ap": "-3",
                "damage": "12",
                "keywords": "Lance"
            },
            {
                "name": "\u27a4 Huge tusks - sweep",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "18",
                "skill": "3+",
                "strength": "9",
                "ap": "-2",
                "damage": "3",
                "keywords": "-"
            },
            {
                "name": "Supa-kannon",
                "weapon_type": "ranged",
                "range": "60\"",
                "attacks": "2D6",
                "skill": "5+",
                "strength": "12",
                "ap": "-2",
                "damage": "3",
                "keywords": "Blast"
            },
            {
                "name": "\u27a4 Kannon - shell",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "1",
                "skill": "5+",
                "strength": "9",
                "ap": "-2",
                "damage": "D6",
                "keywords": "-"
            },
            {
                "name": "\u27a4 Kannon - frag",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "D6",
                "skill": "5+",
                "strength": "5",
                "ap": "0",
                "damage": "1",
                "keywords": "Blast"
            }
        ],
        "abilities": [
            {
                "name": "Gargantuan",
                "description": "Each time this model makes a Normal, Advance or Fall Back move, it can move over models (excluding TITANIC models) and terrain features that are 4\" or less in height as if they were not there."
            },
            {
                "name": "Walking Bastion",
                "description": "This model does not suffer the penalty to its Hit rolls for making ranged attacks while enemy units are within Engagement Range of it."
            },
            {
                "name": "Damaged: 1-10 Wounds Remaining",
                "description": "While this model has 1-10 wounds remaining, subtract 6 from this model\u2019s Objective Control characteristic and each time this model makes an attack, subtract 1 from the Hit roll."
            }
        ]
    },
    "Painboss": {
        "stats": {
            "stat_movement": "6\"",
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
                "name": "Beast Snagga klaw",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "3",
                "skill": "4+",
                "strength": "9",
                "ap": "-2",
                "damage": "2",
                "keywords": "Anti-Monster 4+, Anti-Vehicle 4+"
            }
        ],
        "abilities": [
            {
                "name": "Dok\u2019s Toolz",
                "description": "While this model is leading a unit, models in that unit have the Feel No Pain 5+ ability."
            },
            {
                "name": "Sawbonez",
                "description": "At the end of your Movement phase, select one friendly BEAST SNAGGA CHARACTER model within 3\" of this model. That model is healed and regains up to 3 lost wounds. Each model can only be healed once per turn"
            },
            {
                "name": "Leader",
                "description": "This model can be attached to the following unit:\n- **BEAST SNAGGA BOYZ**"
            },
            {
                "name": "Grot Orderly",
                "description": "Once per battle, in your Command phase, if the bearer is leading a unit that is below its Starting Strength, you can return up to D3 destroyed Bodyguard models to that unit.\n\n**Designer\u2019s Note:** *Place a Grot Orderly token next to the unit, removing it once this ability has been used.*"
            }
        ]
    },
    "Painboy": {
        "stats": {
            "stat_movement": "6\"",
            "stat_toughness": 5,
            "stat_save": "5+",
            "stat_wounds": 3,
            "stat_leadership": "7+",
            "stat_oc": 1,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "\u2019Urty syringe",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "1",
                "skill": "3+",
                "strength": "2",
                "ap": "0",
                "damage": "1",
                "keywords": "Anti-Infantry 4+, Extra Attacks, Precision"
            },
            {
                "name": "Power klaw",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "3",
                "skill": "4+",
                "strength": "9",
                "ap": "-2",
                "damage": "2",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Dok\u2019s Toolz",
                "description": "While this model is leading a unit, models in that unit have the Feel No Pain 5+ ability."
            },
            {
                "name": "Hold Still and Say \u2018Aargh!\u2019",
                "description": "Each time an attack made by this model with its \u2019urty syringe scores a Critical Wound against a unit (excluding VEHICLE units), that unit suffers D6 mortal wounds."
            },
            {
                "name": "Leader",
                "description": "This model can be attached to the following units:\n- **BOYZ**\n- **BREAKA BOYZ**\n- **BURNA BOYZ**\n- **LOOTAS**\n- **NOBZ**\n- **TANKBUSTAS**"
            },
            {
                "name": "Grot Orderly",
                "description": "Once per battle, in your Command phase, if the bearer is leading a unit that is below its Starting Strength, you can return up to D3 destroyed Bodyguard models to that unit.\n\n**Designer\u2019s Note:** *Place a Grot Orderly token next to the unit, removing it once this ability has been used.*"
            }
        ]
    },
    "Rukkatrukk Squigbuggy": {
        "stats": {
            "stat_movement": "12\"",
            "stat_toughness": 7,
            "stat_save": "4+",
            "stat_wounds": 9,
            "stat_leadership": "7+",
            "stat_oc": 3,
            "stat_invuln": "6+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Sawn-off shotgun",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "2",
                "skill": "5+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Assault"
            },
            {
                "name": "Squig launchas",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "D6+6",
                "skill": "5+",
                "strength": "5",
                "ap": "-1",
                "damage": "2",
                "keywords": "Blast, Ignores Cover, Indirect Fire"
            },
            {
                "name": "Saw blades",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "4+",
                "strength": "7",
                "ap": "-1",
                "damage": "2",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Buzzer Squigs",
                "description": "In your Shooting phase, after this model has shot, select one enemy unit (excluding MONSTERS and VEHICLES) hit by one or more of those attacks made with squig-launchas and roll one D6; on a 4+, until the end of your opponent's next turn, that enemy unit is hindered. While a unit is hindered, subtract 2\" from its Move characteristic and subtract 2 from Advance and Charge rolls made for it."
            },
            {
                "name": "Squig Mine",
                "description": "Once per battle, at the start of any phase, select one enemy unit within 3\" of this model and roll one D6: on a 4+, that enemy unit suffers D6 mortal wounds.\nDesigner\u2019s Note: Place a Squig Mine token next to the model, removing it once this ability has been used."
            }
        ]
    },
    "Shokkjump Dragsta": {
        "stats": {
            "stat_movement": "12\"",
            "stat_toughness": 7,
            "stat_save": "4+",
            "stat_wounds": 9,
            "stat_leadership": "7+",
            "stat_oc": 3,
            "stat_invuln": "6+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Kustom shokk rifle",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "1",
                "skill": "3+",
                "strength": "8",
                "ap": "-2",
                "damage": "D6+1",
                "keywords": "Devastating Wounds, Hazardous, Precision"
            },
            {
                "name": "Rokkit launcha",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "D3",
                "skill": "5+",
                "strength": "9",
                "ap": "-2",
                "damage": "3",
                "keywords": "Blast"
            },
            {
                "name": "Saw blades",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "4+",
                "strength": "7",
                "ap": "-1",
                "damage": "2",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Shokk Tunnel",
                "description": "In your Movement phase, when this unit is selected to make an **advance move**, you can use this ability. If you do:\n- That move has no **maximum distance**.\n- This unit can move through all types of model (including enemy\u00a0models and **MONSTER/VEHICLE** models).\n- After moving, your unit must be more than 8\" horizontally from all\u00a0enemy units."
            }
        ]
    },
    "Squighog Boyz": {
        "stats": {
            "stat_movement": "10\"",
            "stat_toughness": 7,
            "stat_save": "4+",
            "stat_wounds": 4,
            "stat_leadership": "7+",
            "stat_oc": 2,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Squig jaws",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "3",
                "skill": "4+",
                "strength": "6",
                "ap": "-1",
                "damage": "2",
                "keywords": "Extra Attacks"
            },
            {
                "name": "Slugga",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "1",
                "skill": "5+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Close-quarters"
            },
            {
                "name": "Saddlegit weapons",
                "weapon_type": "ranged",
                "range": "9\"",
                "attacks": "1",
                "skill": "4+",
                "strength": "3",
                "ap": "0",
                "damage": "1",
                "keywords": "Assault"
            }
        ],
        "abilities": [
            {
                "name": "Wild Ride",
                "description": "You can ignore any or all modifiers to this unit\u2019s Move characteristic and to Advance and Charge rolls made for this unit."
            }
        ]
    },
    "Stompa": {
        "stats": {
            "stat_movement": "10\"",
            "stat_toughness": 14,
            "stat_save": "2+",
            "stat_wounds": 30,
            "stat_leadership": "6+",
            "stat_oc": 12,
            "stat_invuln": "6+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Deffkannon",
                "weapon_type": "ranged",
                "range": "72\"",
                "attacks": "3D6",
                "skill": "5+",
                "strength": "14",
                "ap": "-3",
                "damage": "D6",
                "keywords": "Blast"
            },
            {
                "name": "\u27a4 Mega-choppa - strike",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "6",
                "skill": "3+",
                "strength": "24",
                "ap": "-5",
                "damage": "10",
                "keywords": "-"
            },
            {
                "name": "\u27a4 Mega-choppa - sweep",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "18",
                "skill": "3+",
                "strength": "10",
                "ap": "-2",
                "damage": "3",
                "keywords": "-"
            },
            {
                "name": "Supa-gatler",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "20",
                "skill": "5+",
                "strength": "7",
                "ap": "-1",
                "damage": "2",
                "keywords": "Sustained Hits 1"
            },
            {
                "name": "Supa-rokkits",
                "weapon_type": "ranged",
                "range": "100\"",
                "attacks": "D6",
                "skill": "5+",
                "strength": "12",
                "ap": "-3",
                "damage": "D6+2",
                "keywords": "Blast"
            },
            {
                "name": "Big shoota",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "3",
                "skill": "5+",
                "strength": "5",
                "ap": "0",
                "damage": "1",
                "keywords": "Rapid Fire 2"
            },
            {
                "name": "Skorcha",
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
                "name": "Twin big shoota",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "3",
                "skill": "5+",
                "strength": "5",
                "ap": "0",
                "damage": "1",
                "keywords": "Rapid Fire 2, Twin-linked"
            }
        ],
        "abilities": [
            {
                "name": "Damaged: 1-10 Wounds Remaining",
                "description": "While this model has 1-10 wounds remaining, subtract 6 from this model\u2019s Objective Control characteristic and each time this model makes an attack, subtract 1 from the Hit roll."
            },
            {
                "name": "Waaagh! Effigy (Aura)",
                "description": "While a friendly ORKS unit is within 12\" of this model, each time you take a Battle-shock test for that unit, add 1 to that test."
            },
            {
                "name": "Stompin\u2019 Forward",
                "description": "Each time this model makes a Normal, Advance or Fall Back move, it can move over models (excluding **^^Titanic^^** models) and terrain features that are 4\" or less in height as if they were not there."
            }
        ]
    },
    "Stormboyz": {
        "stats": {
            "stat_movement": "12\"",
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
                "name": "Slugga",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "1",
                "skill": "5+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Close-Quarters"
            },
            {
                "name": "Choppa",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "3",
                "skill": "3+",
                "strength": "4",
                "ap": "-1",
                "damage": "1"
            },
            {
                "name": "Power klaw",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "3",
                "skill": "4+",
                "strength": "9",
                "ap": "-2",
                "damage": "2",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Full Throttle",
                "description": "This unit is eligible to declare a charge in a turn in which it Advanced or Fell Back."
            }
        ]
    },
    "Trukk": {
        "stats": {
            "stat_movement": "12\"",
            "stat_toughness": 8,
            "stat_save": "4+",
            "stat_wounds": 10,
            "stat_leadership": "7+",
            "stat_oc": 2,
            "stat_invuln": "6+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Big shoota",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "3",
                "skill": "5+",
                "strength": "5",
                "ap": "0",
                "damage": "1",
                "keywords": "Rapid Fire 2"
            },
            {
                "name": "Wreckin' ball",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "1",
                "skill": "4+",
                "strength": "10",
                "ap": "0",
                "damage": "D6",
                "keywords": "Extra Attacks"
            },
            {
                "name": "Spiked wheel",
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
                "name": "Grot Riggers",
                "description": "At the start of your Command phase, this model regains 1 lost wound."
            }
        ]
    },
    "Warbikers": {
        "stats": {
            "stat_movement": "12\"",
            "stat_toughness": 6,
            "stat_save": "4+",
            "stat_wounds": 4,
            "stat_leadership": "7+",
            "stat_oc": 2,
            "stat_invuln": "6+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Twin dakkagun",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "3",
                "skill": "5+",
                "strength": "5",
                "ap": "0",
                "damage": "1",
                "keywords": "Assault, Rapid Fire 2, Twin-linked"
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
                "name": "Slugga",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "1",
                "skill": "5+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Close-Quarters"
            },
            {
                "name": "Choppa",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "3",
                "skill": "3+",
                "strength": "4",
                "ap": "-1",
                "damage": "1"
            },
            {
                "name": "Big choppa",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "3",
                "skill": "3+",
                "strength": "7",
                "ap": "-1",
                "damage": "2",
                "keywords": "-"
            },
            {
                "name": "Power klaw",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "3",
                "skill": "4+",
                "strength": "9",
                "ap": "-2",
                "damage": "2",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Drive-by Dakka",
                "description": "Each time a model in this unit makes a ranged attack that targets a unit within 9\", improve the Armour Penetration characteristic of that attack by 1."
            }
        ]
    },
    "Warboss": {
        "stats": {
            "stat_movement": "6\"",
            "stat_toughness": 5,
            "stat_save": "4+",
            "stat_wounds": 6,
            "stat_leadership": "6+",
            "stat_oc": 1,
            "stat_invuln": "5+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Attack Squig",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "2",
                "skill": "4+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Extra Attacks"
            },
            {
                "name": "Kombi-weapon",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "1",
                "skill": "5+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Anti-Infantry 4+, Devastating Wounds, Rapid Fire 1"
            },
            {
                "name": "Big choppa",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "5",
                "skill": "2+",
                "strength": "8",
                "ap": "-1",
                "damage": "2",
                "keywords": "-"
            },
            {
                "name": "Kustom shoota",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "4",
                "skill": "5+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Rapid Fire 2"
            },
            {
                "name": "Power klaw",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "3+",
                "strength": "10",
                "ap": "-2",
                "damage": "2",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Might is Right",
                "description": "While this model is leading a unit, each time a model in that unit makes a melee attack, add 1 to the Hit roll."
            },
            {
                "name": "Da Biggest and da Best",
                "description": "While the Waaagh! is active for your army, add 4 to the Attacks\u00a0characteristic of this model\u2019s melee weapons."
            },
            {
                "name": "Leader",
                "description": "This model can be attached to the following units:\n- **BOYZ**\n- **BREAKA BOYZ**\n- **NOBZ**"
            }
        ]
    },
    "Warboss in Mega Armour": {
        "stats": {
            "stat_movement": "5\"",
            "stat_toughness": 6,
            "stat_save": "2+",
            "stat_wounds": 7,
            "stat_leadership": "6+",
            "stat_oc": 1,
            "stat_invuln": "5+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Big shoota",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "3",
                "skill": "4+",
                "strength": "5",
                "ap": "0",
                "damage": "1",
                "keywords": "Rapid Fire 2"
            },
            {
                "name": "\u2019Uge choppa",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "2+",
                "strength": "12",
                "ap": "-2",
                "damage": "2",
                "keywords": "-"
            }
        ],
        "abilities": [
            {
                "name": "Might is Right",
                "description": "While this model is leading a unit, each time a model in that unit makes a melee attack, add 1 to the Hit roll."
            },
            {
                "name": "Dead Brutal",
                "description": "While the Waaagh! is active for your army, this model\u2019s \u2019uge choppa has\u00a0a Damage characteristic of 3."
            },
            {
                "name": "Leader",
                "description": "This model can be attached to the following unit:\n- **^^Meganobz^^**"
            }
        ]
    },
    "Wartrakk": {
        "stats": {
            "stat_movement": "12\"",
            "stat_toughness": 6,
            "stat_save": "4+",
            "stat_wounds": 7,
            "stat_leadership": "7+",
            "stat_oc": 3,
            "stat_invuln": "6+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Choppas",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "5",
                "skill": "3+",
                "strength": "4",
                "ap": "-1",
                "damage": "1"
            },
            {
                "name": "Rokkit launcha",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "D3+3",
                "skill": "5+",
                "strength": "10",
                "ap": "-2",
                "damage": "3"
            },
            {
                "name": "Kustom shoota",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "2",
                "skill": "5+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "Rapid Fire 2"
            }
        ],
        "abilities": [
            {
                "name": "Indiscriminate Detonations",
                "description": "In your Shooting phase, when\u00a0this unit has resolved its attacks, select one enemy unit\u00a0hit by one or more of those attacks. That enemy unit is **suppressed** until the start of your next Command phase.\u00a0(While a unit is **suppressed**, it has \u20111 to **hit rolls**.)"
            }
        ]
    },
    "Wazbom Blastajet": {
        "stats": {
            "stat_movement": "-",
            "stat_toughness": 9,
            "stat_save": "3+",
            "stat_wounds": 12,
            "stat_leadership": "7+",
            "stat_oc": None,
            "stat_invuln": "6+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Smasha gun",
                "weapon_type": "ranged",
                "range": "48\"",
                "attacks": "D3",
                "skill": "4+",
                "strength": "9",
                "ap": "-3",
                "damage": "4",
                "keywords": "Blast"
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
                "name": "Twin wazbom mega-kannon",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "D3",
                "skill": "4+",
                "strength": "12",
                "ap": "-2",
                "damage": "D6",
                "keywords": "Blast, Hazardous, Twin-linked"
            },
            {
                "name": "Twin tellyport mega-blasta",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "3",
                "skill": "5+",
                "strength": "9",
                "ap": "-1",
                "damage": "D6+1",
                "keywords": "Blast, Twin-linked"
            },
            {
                "name": "Twin supa-shoota",
                "weapon_type": "ranged",
                "range": "36\"",
                "attacks": "4",
                "skill": "4+",
                "strength": "6",
                "ap": "-1",
                "damage": "1",
                "keywords": "Rapid Fire 2, Sustained Hits 1, Twin-linked"
            }
        ],
        "abilities": [
            {
                "name": "Blastajet Attack Run",
                "description": "Each time this model makes a ranged attack that targets a unit that cannot FLY, re-roll a Hit roll of 1."
            },
            {
                "name": "Blastajet Force Field",
                "description": "The bearer has a 4+ invulnerable save, but it loses the **^^Grenades^^** keyword."
            }
        ]
    },
    "Weirdboy": {
        "stats": {
            "stat_movement": "6\"",
            "stat_toughness": 5,
            "stat_save": "5+",
            "stat_wounds": 4,
            "stat_leadership": "7+",
            "stat_oc": 1,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Weirdboy staff",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "3",
                "skill": "3+",
                "strength": "8",
                "ap": "-1",
                "damage": "D3",
                "keywords": "Psychic"
            },
            {
                "name": "\u2019Eadbanger",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "1",
                "skill": "4+",
                "strength": "6",
                "ap": "-3",
                "damage": "1",
                "keywords": "Precision, Psychic"
            }
        ],
        "abilities": [
            {
                "name": "Da Jump (Psychic)",
                "description": "Once per turn, at the end of your Movement phase, one WEIRDBOY from your army can use this ability. If it does, roll one D6: on a 1, that WEIRDBOY\u2019s unit suffers D6 mortal wounds; on a 2+, remove this WEIRDBOY\u2019s unit from the battlefield and set it up again anywhere on the battlefield that is more than 8\" horizontally away from all enemy models."
            },
            {
                "name": "Waaagh! Energy",
                "description": "While this model is leading a unit, add 1 to the Strength and Damage characteristics of this model\u2019s \u2019Eadbanger weapon for every 5 models in that unit (rounding down), but while that unit contains 10 or more models, that weapon has the **[HAZARDOUS]** ability."
            },
            {
                "name": "Leader",
                "description": "This model can be attached to the following unit:\n- **BOYZ**\n- **BREAKA BOYZ**"
            }
        ]
    },
    "Zodgrod Wortsnagga": {
        "stats": {
            "stat_movement": "6\"",
            "stat_toughness": 5,
            "stat_save": "5+",
            "stat_wounds": 5,
            "stat_leadership": "7+",
            "stat_oc": 1,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "abilities": [
            {
                "name": "Super Runts",
                "description": "While this model is leading a unit:\n- Models in that unit have the Scouts 9\" ability.\n- Each time a model in that unit makes an attack, add 1 to the Hit roll and add 1 to the Wound roll.\n- Each time an attack targets that unit, subtract 1 from the Wound roll."
            },
            {
                "name": "Special Dose",
                "description": "While the Waaagh! is active for your army, add 6\" to the Move\u00a0characteristic of models in this model\u2019s unit."
            },
            {
                "name": "Leader",
                "description": "This model can be attached to the following unit:\n- **^^Gretchin^^**"
            }
        ]
    }
}


class Command(BaseCommand):
    """Refresh Orks stat lines, weapon profiles, and abilities from BSData."""

    help = 'Refresh 11th Edition stats/weapons/abilities for Orks units.'

    def add_arguments(self, parser):
        """Add --dry-run flag."""
        parser.add_argument(
            '--dry-run', action='store_true',
            help='Preview changes without writing to the database.',
        )

    def handle(self, *args, **options):
        """Iterate ORKS_DATASHEETS and refresh each unit's datasheet data."""
        dry_run = options['dry_run']
        updated = 0
        skipped = 0

        with transaction.atomic():
            for name, payload in ORKS_DATASHEETS.items():
                try:
                    unit = UnitType.objects.get(name=name, faction__name='Orks')
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
                        ab = {**ab, 'description': _clean_markdown(ab['description'])}
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
