"""
Management command: seed_ultramarines_datasheets

Refreshes stat lines, weapon profiles, and abilities for Ultramarines
units using 11th Edition data sourced from BSData/wh40k-11e ("Imperium -
Adeptus Astartes - Ultramarines.json") -- the same source used by
seed_ultramarines_points.py.

Usage:
    python manage.py seed_ultramarines_datasheets
    python manage.py seed_ultramarines_datasheets --dry-run

Notes:
- Does NOT touch points_cost or category -- those are handled entirely by
  seed_ultramarines_points.py. This command only refreshes stat_* fields,
  WeaponProfile rows, and UnitAbility rows.
- Scope is the 8 Ultramarines-exclusive rows seeded by
  seed_ultramarines_points.py ("Ultramarines Upgrades and Transfers" is
  a transfer-sheet accessory, not a real unit, and correctly has no
  BSData match -- skipped, not a gap).
- Known gap: `Victrix Honour Guard` has 0 resolvable stat profile within
  this file -- weapons (2) and abilities (3) resolved fine, but its
  sub-models (Victrix Honour Guard/Chapter Champion/Chapter Ancient) have
  no embedded profiles and this file\'s sharedProfiles list is entirely
  empty (0 entries), so the usual name-matched fallback has nothing to
  match against either. Same class of gap as Black Templars\' Land Raider
  Crusader and Blood Angels\' Sanguinary Priest (wargear/stats defined in
  an external catalogue not included in this fetch). The DB\'s stat_*
  fields for this unit were already blank before this command -- the
  per-field safety rule leaves them blank, not a regression.
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from calculators.models import UnitAbility, UnitType, WeaponProfile

# (name -> {stats?, weapons?, abilities?}). Missing keys mean "no data
# found for this field -- leave existing DB data untouched."
ULTRAMARINES_DATASHEETS = {
    "Captain Titus": {
        "stats": {
            "stat_movement": "6\"",
            "stat_toughness": 4,
            "stat_save": "3+",
            "stat_wounds": 6,
            "stat_leadership": "6+",
            "stat_oc": 1,
            "stat_invuln": "4+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Master-crafted Chainsword",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "8",
                "skill": "2+",
                "strength": "5",
                "ap": "-1",
                "damage": "2",
                "keywords": "Anti-infantry 2+"
            },
            {
                "name": "Master-crafted Bolter",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "2",
                "skill": "2+",
                "strength": "4",
                "ap": "-1",
                "damage": "2",
                "keywords": "Assault, Heavy"
            }
        ],
        "abilities": [
            {
                "name": "Press the Attack",
                "description": "Weapons equipped by models in this model\u2019s unit have the [SUSTAINED HITS 1] ability"
            },
            {
                "name": "Honour of Ultramar",
                "description": "If this model is destroyed by a melee attack, if it has not fought this phase, roll one D6: on a 2+,\ndo not remove it from play. This model can fight after the attacking unit has finished making its attacks. If one or more enemy models are destroyed as a result of those attacks, this model regains D3 lost wounds and is not destroyed; otherwise, it is removed from play."
            },
            {
                "name": "Leader",
                "description": "This model can be attached to the following units:\n\n\n\u25a0 ASSAULT INTERCESSOR SQUAD\n\u25a0 BLADEGUARD VETERAN SQUAD\n\u25a0 COMPANY HEROES\n\u25a0 HELLBLASTER SQUAD\n\u25a0 INFERNUS SQUAD\n\u25a0 INTERCESSOR SQUAD\n\u25a0 STERNGUARD VETERAN SQUAD\n\u25a0 VICTRIX HONOUR GUARD\n\u25a0 WARDENS OF ULTRAMAR"
            }
        ]
    },
    "Cato Sicarius": {
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
                "name": "Artisan Plasma Pistol",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "1",
                "skill": "2+",
                "strength": "8",
                "ap": "-3",
                "damage": "2",
                "keywords": "Pistol"
            },
            {
                "name": "\u27a4 Talassarian Tempest Blade - Strike",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "2+",
                "strength": "6",
                "ap": "-3",
                "damage": "3",
                "keywords": "Devastating Wounds"
            },
            {
                "name": "\u27a4 Talassarian Tempest Blade - Coup de Grace",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "6",
                "skill": "2+",
                "strength": "5",
                "ap": "-2",
                "damage": "2",
                "keywords": "Precision"
            },
            {
                "name": "\u27a4 Talassarian Tempest Blade - Sweep",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "9",
                "skill": "2+",
                "strength": "5",
                "ap": "-2",
                "damage": "1",
                "keywords": "Sustained Hits 1"
            }
        ],
        "abilities": [
            {
                "name": "Knight Champion of Macragge",
                "description": "Once per turn, when an enemy unit ends a Normal, Advance or Fall Back move within 8\" of this model\u2019s unit, if this unit is not within Engagement Range of one or more enemy units, it can make a Normal move of up to 6\"."
            },
            {
                "name": "Honour or Death",
                "description": "You can target this unit with the Heroic Intervention Stratagem for 0CP, even if you have already used\nthat Stratagem on a different unit this phase."
            },
            {
                "name": "Support",
                "description": "This model can be attached to the following units:\n\n\n\u25a0 VICTRIX HONOUR GUARD\n\n\nYou can attach this model to the above unit even if a Marneus Calgar unit has already been attached\nto it. If you do, and that Bodyguard unit is destroyed, the Leader units attached to it become separate\nunits, with their original Starting Strengths"
            }
        ]
    },
    "Chief Librarian Tigurius": {
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
                "name": "\u27a4 Storm of the Emperor\u2019s Wrath - Witchfire",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "D6",
                "skill": "2+",
                "strength": "6",
                "ap": "-2",
                "damage": "2",
                "keywords": "Blast, Psychic"
            },
            {
                "name": "\u27a4 Storm of the Emperor\u2019s Wrath - Focused Witchfire",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "2D6",
                "skill": "2+",
                "strength": "6",
                "ap": "-2",
                "damage": "2",
                "keywords": "Blast, Hazardous, Psychic"
            },
            {
                "name": "Rod of Tigurius",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "5",
                "skill": "3+",
                "strength": "7",
                "ap": "-2",
                "damage": "D3",
                "keywords": "Psychic"
            }
        ],
        "abilities": [
            {
                "name": "Hood of Hellfire",
                "description": "While this model is leading a unit, models in that unit have the Feel No Pain 4+ ability against Psychic Attacks and mortal wounds."
            },
            {
                "name": "Master of Prescience (Psychic)",
                "description": "\u25aa This unit has Stealth.\n\u25aa Melee attacks that target this unit have -1 to hit rolls.\n\u25aa (Once per battle round, per army) When you target this unit with the Counteroffensive/Fire Overwatch/Heroic Intervention stratagem, that use is -1 CP."
            },
            {
                "name": "Leader",
                "description": "This model can be attached to the following units:\n\n\u25a0 ASSAULT INTERCESSOR SQUAD\n\u25a0 BLADEGUARD VETERAN SQUAD\n\u25a0 DESOLATION SQUAD\n\u25a0 DEVASTATOR SQUAD\n\u25a0 INTERCESSOR SQUAD\n\u25a0 STERNGUARD VETERAN SQUAD\n\u25a0 TACTICAL SQUAD"
            }
        ]
    },
    "Lieutenant Titus": {
        "stats": {
            "stat_movement": "6\"",
            "stat_toughness": 4,
            "stat_save": "3+",
            "stat_wounds": 5,
            "stat_leadership": "6+",
            "stat_oc": 1,
            "stat_invuln": "",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Astartes Chainsword",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "8",
                "skill": "2+",
                "strength": "4",
                "ap": "-1",
                "damage": "1",
                "keywords": "Anti-Infantry 2+"
            }
        ],
        "abilities": [
            {
                "name": "Press the Attack",
                "description": ": Weapons equipped by models in this model\u2019s unit have the [SUSTAINED HITS 1] ability."
            },
            {
                "name": "Honour of the Chapter",
                "description": "If this model is destroyed by a melee attack, if it has not fought this phase, roll one D6: on a 2+, do not remove it from play. This model can fight after the attacking unit has finished making its attacks, and is then removed from play."
            },
            {
                "name": "Leader",
                "description": "This model can be attached to the following units:\n\n\u25a0 Assault Intercessor Squad\n\u25a0 Bladeguard Veteran Squad\n\u25a0 Hellblaster Squad\n\u25a0 Infernus Squad\n\u25a0 Intercessor Squad\n\u25a0 Sternguard Veteran Squad"
            }
        ]
    },
    "Marneus Calgar in Armour of Antilochus": {
        "stats": {
            "stat_movement": "6\"",
            "stat_toughness": 6,
            "stat_save": "2+",
            "stat_wounds": 6,
            "stat_leadership": "6+",
            "stat_oc": 1,
            "stat_invuln": "4+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Gauntlets of Ultramar",
                "weapon_type": "ranged",
                "range": "18\"",
                "attacks": "4",
                "skill": "2+",
                "strength": "4",
                "ap": "-1",
                "damage": "2",
                "keywords": "Pistol, Twin-linked"
            },
            {
                "name": "Gauntlets of Ultramar",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "6",
                "skill": "2+",
                "strength": "8",
                "ap": "-3",
                "damage": "3",
                "keywords": "Twin-linked"
            }
        ],
        "abilities": [
            {
                "name": "Inspiring Leader",
                "description": "This unit is eligible to shoot and declare a charge in a turn in which it Advanced or Fell Back."
            },
            {
                "name": "Master Tactician",
                "description": "At the start of your Command phase, if this unit\u2019s Marneus Calgar model is your Warlord and is on the battlefield, you gain 1CP."
            },
            {
                "name": "Leader",
                "description": "This model can be attached to the following units:\n\n\n\u25a0 AGGRESSOR SQUAD\n\u25a0 ASSAULT INTERCESSOR SQUAD\n\u25a0 BLADEGUARD VETERAN SQUAD\n\u25a0 COMPANY HEROES\n\u25a0 ERADICATOR SQUAD\n\u25a0 HEAVY INTERCESSOR SQUAD\n\u25a0 INFERNUS SQUAD\n\u25a0 INTERCESSOR SQUAD\n\u25a0 STERNGUARD VETERAN SQUAD\n\u25a0 TACTICAL SQUAD\n\u25a0 TERMINATOR ASSAULT SQUAD\n\u25a0 TERMINATOR SQUAD\n\u25a0 VICTRIX HONOUR GUARD"
            }
        ]
    },
    "Roboute Guilliman": {
        "stats": {
            "stat_movement": "8\"",
            "stat_toughness": 9,
            "stat_save": "2+",
            "stat_wounds": 10,
            "stat_leadership": "5+",
            "stat_oc": 4,
            "stat_invuln": "4+",
            "stat_fnp": ""
        },
        "weapons": [
            {
                "name": "Hand of Dominion",
                "weapon_type": "ranged",
                "range": "30\"",
                "attacks": "2",
                "skill": "2+",
                "strength": "6",
                "ap": "-2",
                "damage": "2",
                "keywords": "Rapid Fire 2"
            },
            {
                "name": "Hand of Dominion",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "7",
                "skill": "2+",
                "strength": "14",
                "ap": "-4",
                "damage": "4",
                "keywords": "Lethal Hits"
            },
            {
                "name": "The Emperor's Sword",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "14",
                "skill": "2+",
                "strength": "8",
                "ap": "-3",
                "damage": "2",
                "keywords": "Devastating Wounds"
            }
        ],
        "abilities": [
            {
                "name": "Author of the Codex",
                "description": "At the Start of your Command phase, select two Author of the Codex abilities (see left). Until the start of your next Command phase, this model has those abilities.\u2019\n\nPrimarch of the XIII (Aura): While a friendly Adeptus Astartes unit is within 6\" of this model, add 1 to the Objective Control characteristic of models in that unit and you can re-roll Battle-shock and Leadership tests taken for that unit.\n\nMaster of Battle: After you have selected an enemy unit using the Oath of Moment ability, select a second enemy unit. Until the start of your next Command phase, if your Oath of Moment target is destroyed, that second enemy unit becomes your Oath of Moment target until you select a new one.\n\nSupreme Strategist: Once per battle round, you can target one friendly ADEPTUS ASTARTES unit within 12\" of this model with a Stratagem. If it does, reduce the CP cost of that use of that Stratagem by 1CP."
            },
            {
                "name": "Ultramarines Bodyguard",
                "description": "While this model is within 3\" of one or more friendly Adeptus Astartes Infantry units, this model has the Lone Operative ability"
            },
            {
                "name": "Armour of Fate",
                "description": "The first time this model is destroyed, roll one D6 at the end of the phase: on a 3+, set this model back up on the battlefield as close as possible to where it was destroyed and not within Engagement Range of any enemy models, with 6 wounds remaining."
            },
            {
                "name": "Supreme Commander",
                "description": "If this model is in your army, it must be your Warlord."
            }
        ]
    },
    "Victrix Honour Guard": {
        "weapons": [
            {
                "name": "Master-crafted Bolt Carbine",
                "weapon_type": "ranged",
                "range": "24\"",
                "attacks": "2",
                "skill": "2+",
                "strength": "4",
                "ap": "-1",
                "damage": "2"
            },
            {
                "name": "Blades of Honour",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "6",
                "skill": "2+",
                "strength": "5",
                "ap": "-2",
                "damage": "2",
                "keywords": "Precision, Twin-linked"
            }
        ],
        "abilities": [
            {
                "name": "Ultramarines Honour Guard",
                "description": "While a Captain or Chapter Master model is leading this unit, each time an attack targets this unit, subtract 1 from the Wound roll"
            },
            {
                "name": "Glory of Ultramar",
                "description": "In your opponent\u2019s Shooting phase, each time an enemy unit has shot, if any models from this unit\nwere destroyed as a result of those attacks, this unit can make a Surge move. To do so, roll one D6: models in this unit move a number of inches up to the result, but this unit must end that move as close as possible to the closest enemy unit (excluding Aircraft). When doing so, those models can be\nmoved within Engagement Range of that enemy unit. This unit cannot make a Surge move while it is Battle-shocked or within Engagement Range of one or more enemy units, and can only make one Surge move per phase."
            },
            {
                "name": "Banner of Macragge",
                "description": "Once per battle, at the start of the Fight phase, the bearer can use this ability. If it does, until the end of the phase, add 1 to the Strength and Attacks characteristics of melee weapons equipped by models in the bearer\u2019s unit."
            }
        ]
    },
    "Wardens of Ultramar": {
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
                "name": "Close combat weapon",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "2+",
                "strength": "4",
                "ap": "0",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "Archeotech Laspistol",
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
                "name": "Power Weapon",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "4",
                "skill": "2+",
                "strength": "4",
                "ap": "-2",
                "damage": "1",
                "keywords": "-"
            },
            {
                "name": "Astropathic Blast",
                "weapon_type": "ranged",
                "range": "12\"",
                "attacks": "D6",
                "skill": "3+",
                "strength": "4",
                "ap": "-1",
                "damage": "1",
                "keywords": "Blast, Psychic"
            },
            {
                "name": "Force Stave",
                "weapon_type": "melee",
                "range": "Melee",
                "attacks": "1",
                "skill": "2+",
                "strength": "5",
                "ap": "-2",
                "damage": "2",
                "keywords": "Psychic"
            }
        ],
        "abilities": [
            {
                "name": "Second Company Banner",
                "description": "While this unit contains Ancient Gadriel, add 1 to the Objective Control characteristic of models in this unit. While this unit contains Ancient Gadriel and Captain Titus, improve the Leadership characteristic of models in this unit by 1 as well."
            },
            {
                "name": "Strategium Command",
                "description": "After both players have deployed their armies, if this unit is on the battlefield (or any Transport it\nis embarked within is on the battlefield), select up to three Adeptus Astartes units from your army and redeploy them. When doing so, you can set those units up in Strategic Reserves, regardless of how many units are already in Strategic Reserves."
            },
            {
                "name": "Heroes of Ultramar",
                "description": "At the start of the Declare Battle Formations step, this unit can join one of the following units. This\nunit then counts as part of that unit for the rest of the battle, and that unit\u2019s Starting Strength is\nincreased accordingly.\n\n\n\u25a0 ASSAULT INTERCESSOR SQUAD\n\u25a0 BLADEGUARD VETERAN SQUAD\n\u25a0 INTERCESSOR SQUAD\n\u25a0 STERNGUARD VETERAN SQUAD\n\n\nThis unit cannot join an Attached unit, and only Captain Titus can join a unit this unit has joined."
            },
            {
                "name": "Storm Shield",
                "description": "The bearer has a 4+ Invulnerable save."
            },
            {
                "name": "Refractor Field",
                "description": "The bearer has a 5+ invulnerable save."
            }
        ]
    }
}


class Command(BaseCommand):
    """Refresh Ultramarines stat lines, weapon profiles, and abilities from BSData."""

    help = 'Refresh 11th Edition stats/weapons/abilities for Ultramarines units.'

    def add_arguments(self, parser):
        """Add --dry-run flag."""
        parser.add_argument(
            '--dry-run', action='store_true',
            help='Preview changes without writing to the database.',
        )

    def handle(self, *args, **options):
        """Iterate ULTRAMARINES_DATASHEETS and refresh each unit's datasheet data."""
        dry_run = options['dry_run']
        updated = 0
        skipped = 0

        with transaction.atomic():
            for name, payload in ULTRAMARINES_DATASHEETS.items():
                try:
                    unit = UnitType.objects.get(name=name, faction__name='Ultramarines')
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
