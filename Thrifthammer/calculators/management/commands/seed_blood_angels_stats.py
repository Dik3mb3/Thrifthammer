"""
Management command: seed_blood_angels_stats

Seeds points costs, stat lines, weapon profiles, and unit abilities
for Blood Angels units in the database. Safe to re-run — uses
delete+create for weapons/abilities and direct field writes for stats.

Units that don't exist in the Blood Angels faction are skipped cleanly.
Shared SM units use the Blood Angels UnitType name (e.g. 'Aggressor Squad',
not 'Space Marine Aggressors') — the exact names from populate_units.py.

Usage:
    python manage.py seed_blood_angels_stats
    python manage.py seed_blood_angels_stats --dry-run
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from calculators.models import UnitAbility, UnitType, WeaponProfile

FACTION_NAME = 'Blood Angels'


# -- Helpers ------------------------------------------------------------------

def stat(m, t, sv, w, ld, oc, invuln='', fnp=''):
    """Return a stat dict for a unit."""
    return dict(
        stat_movement=m, stat_toughness=t, stat_save=sv,
        stat_wounds=w, stat_leadership=ld, stat_oc=oc,
        stat_invuln=invuln, stat_fnp=fnp,
    )


def rng(name, rng_val, a, skill, s, ap, d, kw=''):
    """Return a ranged weapon profile dict."""
    return dict(name=name, weapon_type='ranged', range=rng_val,
                attacks=str(a), skill=skill, strength=str(s),
                ap=str(ap), damage=str(d), keywords=kw)


def mel(name, a, skill, s, ap, d, kw=''):
    """Return a melee weapon profile dict."""
    return dict(name=name, weapon_type='melee', range='Melee',
                attacks=str(a), skill=skill, strength=str(s),
                ap=str(ap), damage=str(d), keywords=kw)


def ability(name, desc):
    """Return an ability dict."""
    return dict(name=name, description=desc)


# -- Unit Data ----------------------------------------------------------------
# Format: (db_unit_name, points, stats_dict, [weapons], [abilities])
# Weapon/ability text sourced from parsed New Recruit HTML (2026-04-14).
# db_unit_name must match the existing UnitType.name in the Blood Angels faction.

BLOOD_ANGELS_UNITS = [

    # ── Blood Angels Exclusives ───────────────────────────────────────────────

    ('Blood Angels Astorath', 85,
     stat('12"', 4, '2+', 5, '5+', 1, invuln='4+'),
     [
         mel("The Executioner's Axe", 6, '2+', 7, -3, 2,
             'Devastating Wounds, Precision'),
     ],
     [
         ability('Redeemer of the Lost',
                 'While this model is leading a unit, each time a model in '
                 'that unit is destroyed by a melee attack, if that model has '
                 'not fought this phase, roll one D6. On a 4+, do not remove '
                 'it from play; that destroyed model can fight after the '
                 "attacking model's unit has finished making its attacks, and "
                 'is then removed from play.'),
         ability('Mass of Doom',
                 "Each time this model's unit makes a Charge move, until the "
                 'end of the turn, melee weapons equipped by models in that '
                 'unit have the [DEVASTATING WOUNDS] ability.'),
         ability('Leader',
                 'This model can be attached to the following unit:\n'
                 '\u25a0 Death Company Marines with Jump Packs'),
     ]),

    ('Blood Angels Mephiston', 120,
     stat('7"', 5, '2+', 6, '6+', 1, invuln='5+'),
     [
         rng('Fury of the Ancients - Witchfire', '18"', 3, '2+', 4, -1,
             'D3', 'Pistol, Psychic, Sustained Hits 1'),
         rng('Fury of the Ancients - Focused Witchfire', '18"', 3, '2+', 5,
             -2, 'D3', 'Hazardous, Pistol, Psychic, Sustained Hits 3'),
         rng('Plasma pistol - supercharge', '12"', 1, '2+', 8, -3, 2,
             'Hazardous, Pistol'),
         rng('Plasma pistol - standard', '12"', 1, '2+', 7, -2, 1, 'Pistol'),
         mel('Vitarus', 6, '2+', 9, -3, 'D3', 'Lethal Hits, Psychic'),
     ],
     [
         ability('The Quickening [Psychic]',
                 'This model is eligible to declare a charge in a turn which '
                 'it Advanced.'),
         ability('Transfixing Gaze [Aura, Psychic]',
                 'While an enemy unit is within 6" of this model, each time '
                 'that unit is selected to Fall Back, it must take a '
                 'Leadership test. If that test is failed, that unit must '
                 'Remain Stationary this phase instead.'),
         ability('Invulnerable Save 5+',
                 'This model has a 5+ invulnerable save'),
     ]),

    ('Blood Angels Commander Dante', 120,
     stat('12"', 4, '2+', 6, '6+', 1, invuln='4+'),
     [
         rng('Perdition', '6"', 1, '2+', 9, -4, 'D6',
             'Melta 2, Pistol, Sustained Hits D3'),
         mel('The Axe Mortalis', 8, '2+', 8, -3, 2, 'Lethal Hits'),
     ],
     [
         ability('Death Mask of Sanguinius',
                 'At the start of the Fight phase, each enemy unit within 6" '
                 'of this model must take a Battle-shock test, subtracting 1 '
                 'from that test when they do'),
         ability('Lord Regent of the Imperium Nihilus',
                 'While this model is leading a unit, add 1 to Advance and '
                 'Charge rolls made for that unit and each time a model in '
                 'that unit makes an attack, add 1 to the Hit roll.'),
         ability('Leader',
                 'This model can be attached to the following units:\n'
                 '\u25a0 Assault Squad with Jump Packs\n'
                 '\u25a0 Sanguinary Guard\n'
                 '\u25a0 Vanguard Veteran Squad with Jump Packs\n'
                 '\u25a0 Assault Intercessors with Jump Packs'),
     ]),

    ('Blood Angels Lemartes', 100,
     stat('12"', 4, '3+', 4, '5+', 1, invuln='4+'),
     [
         rng('Absolvor Bolt Pistol', '18"', 1, '2+', 5, -1, 2, 'Pistol'),
         mel('The Blood Crozius', 5, '2+', 6, -2, 2, 'Lethal Hits'),
     ],
     [
         ability('Guardian of the Lost',
                 'While this model is leading a unit, each time an attack is '
                 'allocated to a model in that unit, subtract 1 from the '
                 'Damage characteristic of that attack.'),
         ability('Fury Unbound',
                 'While this model is leading a unit, melee weapons equipped '
                 'by models in that unit have the [LETHAL HITS] ability.'),
         ability('Leader',
                 'This model can be attached to the following unit:\n'
                 '\u25a0 Death Company Marines with Jump Packs'),
     ]),

    ('Blood Angels The Sanguinor', 130,
     stat('12"', 4, '2+', 7, '6+', 1, invuln='4+'),
     [
         mel('Encarmine Broadsword', 8, '2+', 6, -3, 2, 'Devastating Wounds'),
     ],
     [
         ability('Aura of Fervour (Aura)',
                 'While a friendly Adeptus Astartes unit is within 6" of this '
                 'model, you can re-roll Battle-shock and Leadership tests '
                 'taken for that unit'),
         ability('Miraculous Savior',
                 "Once per battle, at the end of your opponent's Charge phase, "
                 'if this model is still in Reserves, you can select one enemy '
                 'unit that made a Charge move this phase. Set this model up '
                 'on the battlefield within Engagement Range of that enemy '
                 'unit.'),
     ]),

    ('Blood Angels Captain', 80,
     stat('6"', 4, '3+', 5, '6+', 1, invuln='4+'),
     [
         rng('Heavy Bolt Pistol', '18"', 1, '2+', 4, -1, 1, 'Pistol'),
         mel('Master-crafted Chainsword', 7, '2+', 4, -1, 2),
     ],
     [
         ability('Leader',
                 'This model can be attached to the following units:\n'
                 '\u25a0 Assault Intercessor Squad\n'
                 '\u25a0 Infernus Squad\n'
                 '\u25a0 Intercessor Squad\n'
                 '\u25a0 Sternguard Veteran Squad\n'
                 '\u25a0 Company Heroes\n'
                 '\u25a0 Tactical Squad'),
         ability('Rites of Battle',
                 'Once per battle round, one unit from your army with this '
                 'ability can use it when its unit is targeted with a '
                 'Stratagem. If it does, reduce the CP cost of that use of '
                 'that Stratagem by 1CP.'),
         ability('Finest Hour',
                 'Once per battle, at the start of the Fight phase, this model '
                 'can use this ability. If it does, until the end of the phase, '
                 'add 3 to the Attacks characteristic of melee weapons equipped '
                 'by this model and those weapons have the [DEVASTATING WOUNDS] '
                 'ability.'),
     ]),

    ('Blood Angels Chaplain With Jump Pack', 75,
     stat('12"', 4, '3+', 4, '5+', 1, invuln='4+'),
     [
         rng('Bolt pistol', '12"', 1, '3+', 4, 0, 1, 'Pistol'),
         mel('Crozius arcanum', 5, '2+', 6, -1, 2),
     ],
     [
         ability('Exhortation of Rage',
                 "Each time this model's unit is selected to fight, you can "
                 "select one enemy unit within Engagement Range of this model's "
                 'unit and roll one D6: on a 4-5, that enemy unit suffers D3 '
                 'mortal wounds; on a 6, that enemy unit suffers 3 mortal '
                 'wounds.'),
         ability('Leader',
                 'This model can be attached to the following units:\n'
                 '\u25a0 Assault Intercessors with Jump Packs\n'
                 '\u25a0 Vanguard Veteran Squad with Jump Packs'),
         ability('Litany of Hate',
                 'While this model is leading a unit, each time a model in '
                 'that unit makes a melee attack, add 1 to the Wound roll.'),
     ]),

    ('Blood Angels Librarian in Terminator Armour', 75,
     stat('5"', 5, '2+', 5, '6+', 1, invuln='4+'),
     [
         rng('Smite - Witchfire', '24"', 'D6', '3+', 5, -1, 'D3', 'Psychic'),
         rng('Smite - Focused Witchfire', '24"', 'D6', '3+', 6, -2, 'D3',
             'Devastating Wounds, Hazardous, Psychic'),
         mel('Force weapon', 4, '3+', 6, -1, 'D3', 'Psychic'),
     ],
     [
         ability('Veil of Time [Psychic]',
                 'While this model is leading a unit, weapons equipped by '
                 'models in that unit have the [SUSTAINED HITS 1] ability.'),
         ability('Leader',
                 'This model can be attached to the following units:\n'
                 '\u25a0 Relic Terminator Squad\n'
                 '\u25a0 Terminator Assault Squad\n'
                 '\u25a0 Terminator Squad'),
         ability('Psychic Hood',
                 'While this model is leading a unit, models in that unit '
                 'have the Feel No Pain 4+ ability against Psychic Attacks.'),
     ]),

    ('Blood Angels Sanguinary Guard', 125,
     stat('12"', 4, '2+', 3, '6+', 1, invuln='4+'),
     [
         rng('Angelus Boltgun (x3)', '12"', 2, '3+', 4, 0, 1, 'Pistol'),
         mel('Encarmine Blade (x3)', 4, '2+', 6, -3, 2),
     ],
     [
         ability('Angelic Visage',
                 'Each time a melee attack targets this unit, subtract 1 from '
                 'the Hit roll'),
         ability('Heirs of Azkaellon',
                 'While a Character model is leading this unit, each time a '
                 'melee attack targets this unit, subtract 1 from the Wound '
                 'roll.'),
         ability('Attached Unit',
                 'If a Captain model from your army with the Leader ability '
                 'can be attached to Assault Intercessors with Jump Packs, '
                 'it can be attached to this unit instead.'),
     ]),

    ('Blood Angels Sanguinary Priest', 75,
     stat('6"', 4, '3+', 4, '6+', 1),
     [
         rng('Absolver bolt pistol', '18"', 1, '3+', 5, -1, 2, 'Pistol'),
         mel('Astartes Chainsword', 5, '3+', 4, -1, 1),
     ],
     [
         ability('Sanguinary Priest',
                 'While this model is leading a unit, models in that unit '
                 'have the Feel No Pain 5+ ability'),
         ability('Blood Chalice',
                 'While this model is leading a unit, improve the Armour '
                 'Penetration characteristic of melee weapons equipped by '
                 'models in that unit by 1.'),
         ability('Leader',
                 'This model can be attached to the following units:\n'
                 '\u25a0 Assault Intercessor Squad\n'
                 '\u25a0 Bladeguard Veteran Squad\n'
                 '\u25a0 Desolation Squad\n'
                 '\u25a0 Devastator Squad\n'
                 '\u25a0 Hellblaster Squad\n'
                 '\u25a0 Infernus Squad\n'
                 '\u25a0 Intercessor Squad\n'
                 '\u25a0 Tactical Squad\n'
                 '\u25a0 Sternguard Veteran Squad'),
     ]),

    # ── Shared Characters ─────────────────────────────────────────────────────

    ('Ancient', 50,
     stat('6"', 4, '3+', 4, '6+', 1),
     [
         rng('Bolt pistol', '12"', 1, '3+', 4, 0, 1, 'Pistol'),
         rng('Bolt Rifle', '24"', 2, '3+', 4, -1, 1, 'Assault, Heavy'),
         mel('Close combat weapon', 5, '2+', 4, 0, 1),
     ],
     [
         ability('Unbreakable Duty',
                 'While this model is within range of an objective marker '
                 'and/or within 6" of the centre of the battlefield, this '
                 'model has the Feel No Pain 4+ ability.'),
         ability('Leader',
                 'This model can be attached to the following units:\n'
                 '\u25a0 Assault Intercessor Squad\n'
                 '\u25a0 Devastator Squad\n'
                 '\u25a0 Hellblaster Squad\n'
                 '\u25a0 Infernus Squad\n'
                 '\u25a0 Intercessor Squad\n'
                 '\u25a0 Sternguard Veteran Squad\n'
                 '\u25a0 Desolation Squad\n'
                 '\u25a0 Tactical Squad\n'
                 'You can attach this model to one of the above units even if '
                 'one Captain, Chapter Master or Lieutenant model has already '
                 'been attached to it. If you do, and that Bodyguard unit is '
                 'destroyed, the Leader units attached to it become separate '
                 'units, with their original Starting Strengths.'),
         ability('Astartes Banner',
                 'While this model is leading a unit, add 1 to the Objective '
                 'Control characteristic of models in that unit.'),
     ]),

    ('Apothecary', 50,
     stat('6"', 4, '3+', 4, '6+', 1),
     [
         rng('Absolver bolt pistol', '18"', 1, '3+', 5, -1, 2, 'Pistol'),
         rng('Reductor Pistol', '3"', 1, '3+', 4, -4, 2, 'Pistol'),
         mel('Close combat weapon', 4, '3+', 4, 0, 1),
     ],
     [
         ability('Narthecium',
                 'While this model is leading a unit, in your Command phase, '
                 'you can return 1 destroyed model (excluding Character models) '
                 'to that unit.'),
         ability('Gene Seed Recovery',
                 "When this model's Bodyguard unit is destroyed, roll one D6: "
                 'on a 2+, you gain 1CP.'),
         ability('Leader',
                 'This model can be attached to the following units:\n'
                 '\u25a0 Assault Intercessor Squad\n'
                 '\u25a0 Desolation Squad\n'
                 '\u25a0 Devastator Squad\n'
                 '\u25a0 Hellblaster Squad\n'
                 '\u25a0 Infernus Squad\n'
                 '\u25a0 Intercessor Squad\n'
                 '\u25a0 Sternguard Veteran Squad\n'
                 '\u25a0 Tactical Squad\n'
                 'You can attach this model to one of the above units even if '
                 'one Captain, Chapter Master or Lieutenant model has already '
                 'been attached to it. If you do, and that Bodyguard unit is '
                 'destroyed, the Leader units attached to it become separate '
                 'units, with their original Starting Strengths.'),
     ]),

    # db_name 'Captain' covers the generic SM captain card_name "Captain"
    ('Captain', 80,
     stat('6"', 4, '3+', 5, '6+', 1, invuln='4+'),
     [
         rng('Bolt pistol', '12"', 1, '2+', 4, 0, 1, 'Pistol'),
         rng('Master-crafted bolter', '24"', 2, '2+', 4, -1, 2),
         mel('Close combat weapon', 6, '2+', 4, 0, 1),
     ],
     [
         ability('Leader',
                 'This model can be attached to the following units:\n'
                 '\u25a0 Assault Intercessor Squad\n'
                 '\u25a0 Bladeguard Veteran Squad*\n'
                 '\u25a0 Hellblaster Squad*\n'
                 '\u25a0 Infernus Squad\n'
                 '\u25a0 Intercessor Squad\n'
                 '\u25a0 Sternguard Veteran Squad\n'
                 '\u25a0 Company Heroes\n'
                 '\u25a0 Tactical Squad\n\n'
                 'This model cannot be attached to a Bladeguard Veteran Squad '
                 'unless it is equipped with a relic shield, and cannot be '
                 'attached to a Hellblaster Squad unless it is equipped with '
                 'a plasma pistol.'),
         ability('Finest Hour',
                 'Once per battle, at the start of the Fight phase, this model '
                 'can use this ability. If it does, until the end of the phase, '
                 'add 3 to the Attacks characteristic of melee weapons equipped '
                 'by this model and those weapons have the [DEVASTATING WOUNDS] '
                 'ability.'),
         ability('Rites of Battle',
                 'Once per battle round, one unit from your army with this '
                 'ability can use it when its unit is targeted with a '
                 'Stratagem. If it does, reduce the CP cost of that use of '
                 'that Stratagem by 1CP.'),
     ]),

    ('Chaplain', 60,
     stat('6"', 4, '3+', 4, '5+', 1, invuln='4+'),
     [
         rng('Absolver bolt pistol', '18"', 1, '3+', 5, -1, 2, 'Pistol'),
         mel('Crozius arcanum', 5, '2+', 6, -1, 2),
     ],
     [
         ability('Leader',
                 'This model can be attached to the following units:\n'
                 '\u25a0 Assault Intercessor Squad\n'
                 '\u25a0 Bladeguard Veteran Squad\n'
                 '\u25a0 Hellblaster Squad\n'
                 '\u25a0 Infernus Squad\n'
                 '\u25a0 Intercessor Squad\n'
                 '\u25a0 Sternguard Veteran Squad\n'
                 '\u25a0 Tactical Squad'),
         ability('Litany of Hate',
                 'While this model is leading a unit, each time a model in '
                 'that unit makes a melee attack, add 1 to the Wound roll.'),
         ability('Spiritual Leader',
                 'Once per battle, at the start of any phase, you can select '
                 'one friendly Adeptus Astartes unit that is Battle-shocked '
                 'and within 12" of this model. That unit is no longer '
                 'Battle-shocked.'),
     ]),

    ('Librarian', 65,
     stat('6"', 4, '3+', 4, '6+', 1),
     [
         rng('Bolt pistol', '12"', 1, '3+', 4, 0, 1, 'Pistol'),
         rng('Smite - Witchfire', '24"', 'D6', '3+', 5, -1, 'D3', 'Psychic'),
         rng('Smite - Focused Witchfire', '24"', 'D6', '3+', 6, -2, 'D3',
             'Devastating Wounds, Hazardous, Psychic'),
         mel('Force weapon', 4, '3+', 6, -1, 'D3', 'Psychic'),
     ],
     [
         ability('Mental Fortress [Psychic]',
                 'While this model is leading a unit, models in that unit '
                 'have a 4+ invulnerable save.'),
         ability('Leader',
                 'This model can be attached to the following units:\n'
                 '\u25a0 Assault Intercessor Squad\n'
                 '\u25a0 Desolation Squad\n'
                 '\u25a0 Devastator Squad\n'
                 '\u25a0 Hellblaster Squad\n'
                 '\u25a0 Infernus Squad\n'
                 '\u25a0 Intercessor Squad\n'
                 '\u25a0 Sternguard Veteran Squad\n'
                 '\u25a0 Tactical Squad'),
         ability('Psychic Hood',
                 'While this model is leading a unit, models in that unit '
                 'have the Feel No Pain 4+ ability against Psychic Attacks.'),
     ]),

    ('Lieutenant', 55,
     stat('6"', 4, '3+', 4, '6+', 1),
     [
         rng('Bolt pistol', '12"', 1, '2+', 4, 0, 1, 'Pistol'),
         rng('Master-crafted bolter', '24"', 2, '2+', 4, -1, 2),
         mel('Close combat weapon', 5, '2+', 4, 0, 1),
     ],
     [
         ability('Leader',
                 'This model can be attached to the following units:\n'
                 '\u25a0 Assault Intercessor Squad\n'
                 '\u25a0 Bladeguard Veteran Squad\n'
                 '\u25a0 Company Heroes\n'
                 '\u25a0 Hellblaster Squad\n'
                 '\u25a0 Infernus Squad\n'
                 '\u25a0 Intercessor Squad\n'
                 '\u25a0 Sternguard Veteran Squad\n'
                 '\u25a0 Tactical Squad\n'
                 'You can attach this model to a unit it can lead even if one '
                 'Captain or Chapter Master model has already been attached to '
                 'it. If you do, and that Bodyguard unit is destroyed, the '
                 'Leader units attached to it become separate units, with '
                 'their original Starting Strengths.'),
         ability('Target Priority',
                 "This model's unit is eligible to shoot and declare a charge "
                 'in a turn in which it Fell Back'),
         ability('Tactical Precision',
                 'While this model is leading a unit, weapons equipped by '
                 'models in that unit have the [LETHAL HITS] ability.'),
     ]),

    # ── Shared Infantry ────────────────────────────────────────────────────────

    ('Assault Intercessor Squad', 75,
     stat('6"', 4, '3+', 2, '6+', 2),
     [
         rng('Heavy Bolt Pistol (x5)', '18"', 1, '3+', 4, -1, 1, 'Pistol'),
         mel('Astartes Chainsword (x5)', 4, '3+', 4, -1, 1),
     ],
     [
         ability('Shock Assault',
                 'Each time a model in this unit targets an enemy unit with a '
                 'melee attack, re-roll a Wound roll of 1. If that enemy unit '
                 'is within range of an objective marker, you can re-roll the '
                 'Wound roll instead.'),
     ]),

    ('Aggressor Squad', 95,
     stat('5"', 6, '3+', 3, '6+', 1),
     [
         rng('Flamestorm Gauntlets (x3)', '12"', 'D6+1', 'N/A', 4, 0, 1,
             'Ignores Cover, Torrent, Twin-linked'),
         mel('Twin power fist (x3)', 3, '3+', 8, -2, 2, 'Twin-linked'),
     ],
     [
         ability('Close-quarters Firepower',
                 'Each time a model in this unit makes a ranged attack that '
                 'targets the closest eligible target, improve the Armour '
                 'Penetration characteristic of that attack by 1.'),
     ]),

    ('Bladeguard Veteran Squad', 80,
     stat('6"', 4, '3+', 3, '6+', 1, invuln='4+'),
     [
         rng('Heavy Bolt Pistol (x3)', '18"', 1, '3+', 4, -1, 1, 'Pistol'),
         mel('Master-crafted power weapon (x3)', 4, '3+', 5, -2, 2),
     ],
     [
         ability('Bladeguard',
                 'At the start of the Fight phase, you can select one of the '
                 'following abilities to apply to models in this unit until '
                 'the end of the phase:\n'
                 '\u25a0 Swords of the Imperium: Each time a model in this '
                 'unit makes a melee attack, re-roll a Hit roll of 1.\n'
                 '\u25a0 Shields of the Imperium: Each time an invulnerable '
                 'saving throw is made for a model in this unit, re-roll a '
                 'saving throw of 1.'),
     ]),

    ('Company Heroes', 105,
     stat('6"', 4, '3+', 4, '6+', 1),
     [
         rng('Bolt pistol (x4)', '12"', 1, '3+', 4, 0, 1, 'Pistol'),
         rng('Bolt Rifle', '24"', 2, '3+', 4, -1, 1),
         rng('Master-crafted Bolt Rifle', '24"', 2, '2+', 4, -1, 2,
             'Devastating Wounds, Rapid Fire 1'),
         rng('Master-crafted Heavy Bolter', '36"', 3, '3+', 5, -1, 3,
             'Heavy, Sustained Hits 2'),
         mel('Close combat weapon (x3)', 5, '3+', 4, 0, 1),
         mel('Master-crafted Power Weapon', 6, '2+', 5, -2, 2, 'Precision'),
     ],
     [
         ability('Ancient Banner',
                 'While this unit contains an Ancient, add 1 to the Objective '
                 'Control characteristic of models in this unit'),
         ability('Command Squad',
                 'While a Character model is leading this unit, each time an '
                 'attack targets this unit, subtract 1 from the Wound roll.'),
         ability('Company Heroes',
                 'You must attach one Captain or Chapter Master model to this '
                 'unit. If this is not possible, this unit does not take part '
                 'in the battle and counts as having been destroyed.'),
     ]),

    ('Devastator Squad', 120,
     stat('6"', 4, '3+', 2, '6+', 1),
     [
         rng('Bolt pistol (x5)', '12"', 1, '3+', 4, 0, 1, 'Pistol'),
         rng('Boltgun', '24"', 2, '3+', 4, 0, 1),
         rng('Grav-cannon (x4)', '24"', 3, '4+', 6, -1, 3,
             'Anti-vehicle 2+, Heavy'),
         mel('Close combat weapon (x5)', 2, '3+', 4, 0, 1),
     ],
     [
         ability('Signum',
                 'Each time this unit Remains Stationary, until the start of '
                 'your next Movement phase, ranged weapons equipped by models '
                 'in this unit have the [IGNORES COVER] ability.'),
         ability('Armorium Cherub',
                 'Once per battle, after making a Hit roll for a model in '
                 'this unit, you can change that roll to an unmodified 6.'),
     ]),

    ('Eliminator Squad', 85,
     stat('6"', 4, '3+', 2, '6+', 1),
     [
         rng('Bolt pistol (x3)', '12"', 1, '3+', 4, 0, 1, 'Pistol'),
         rng('Bolt Sniper Rifle (x3)', '36"', 1, '3+', 5, -2, 3,
             'Heavy, Precision'),
         mel('Close combat weapon (x3)', 3, '3+', 4, 0, 1),
     ],
     [
         ability('Reposition Under Covering Fire',
                 'In your Shooting phase, after this unit has shot, if it '
                 'contains an Eliminator Sergeant equipped with an instigator '
                 'bolt carbine, this unit can make a Normal move. If it does '
                 'so, until the end of the turn, this unit is not eligible to '
                 'declare a charge.'),
         ability('Mark the Target',
                 'Each time this unit Remains Stationary, until the start of '
                 'your next Movement phase, ranged weapons equipped by models '
                 'in this unit have the [DEVASTATING WOUNDS] ability.'),
     ]),

    ('Eradicator Squad', 90,
     stat('5"', 6, '3+', 3, '6+', 1),
     [
         rng('Bolt pistol (x3)', '12"', 1, '3+', 4, 0, 1, 'Pistol'),
         rng('Melta rifle (x3)', '18"', 1, '3+', 9, -4, 'D6',
             'Heavy, Melta 2'),
         mel('Close combat weapon (x3)', 3, '3+', 4, 0, 1),
     ],
     [
         ability('Total Obliteration',
                 'Each time a ranged attack made by a model in this unit '
                 'targets a Monster or Vehicle model, you can re-roll the Hit '
                 'roll, you can re-roll the Wound roll and you can re-roll the '
                 'Damage roll.'),
     ]),

    ('Inceptor Squad', 120,
     stat('10"', 6, '3+', 3, '6+', 1),
     [
         rng('Assault Bolters (x3)', '18"', 3, '3+', 5, -1, 2,
             'Assault, Pistol, Sustained Hits 2, Twin-linked'),
         mel('Close combat weapon (x3)', 3, '3+', 4, 0, 1),
     ],
     [
         ability('Meteoric Descent',
                 'In your Movement phase, when this unit is set up on the '
                 'battlefield using the Deep Strike ability, it can perform a '
                 'meteoric descent. If it does, this unit can be set up '
                 'anywhere on the battlefield that is more than 6" '
                 'horizontally away from all enemy units, but until the end '
                 'of the turn, it is not eligible to declare a charge.'),
     ]),

    ('Incursor Squad', 80,
     stat('6"', 4, '3+', 2, '6+', 1),
     [
         rng('Bolt pistol (x5)', '12"', 1, '3+', 4, 0, 1, 'Pistol'),
         rng('Occulus Bolt Carbine (x5)', '24"', 2, '3+', 4, 0, 1,
             'Assault, Ignores Cover'),
         mel('Paired Combat Blades (x5)', 3, '3+', 4, -1, 1, 'Sustained Hits 1'),
     ],
     [
         ability('Multi-spectrum Array',
                 'In your Shooting phase, after this unit has shot, select '
                 'one enemy unit that was hit by one or more attacks made by '
                 'this unit this phase. Until the end of the phase, each time '
                 'a friendly Adeptus Astartes unit makes an attack that '
                 'targets that enemy unit, add 1 to the Hit roll.'),
     ]),

    ('Infernus Squad', 90,
     stat('6"', 4, '3+', 2, '6+', 1),
     [
         rng('Bolt pistol (x5)', '12"', 1, '3+', 4, 0, 1, 'Pistol'),
         rng('Pyreblaster (x5)', '12"', 'D6', 'N/A', 5, -1, 1,
             'Ignores Cover, Torrent'),
         mel('Close combat weapon (x5)', 3, '3+', 4, 0, 1),
     ],
     [
         ability('Purge the Foe',
                 'In your Shooting phase, after this unit has shot, you can '
                 'select one enemy Infantry unit hit by one or more of those '
                 'attacks made with a pyreblaster. That enemy unit must take '
                 'a Battle-shock test, subtracting 1 from that test.'),
     ]),

    ('Infiltrator Squad', 100,
     stat('6"', 4, '3+', 2, '6+', 1),
     [
         rng('Bolt pistol (x5)', '12"', 1, '3+', 4, 0, 1, 'Pistol'),
         rng('Marksman Bolt Carbine (x5)', '24"', 2, '3+', 4, 0, 1, 'Heavy'),
         mel('Close combat weapon (x5)', 3, '3+', 4, 0, 1),
     ],
     [
         ability('Omni-scramblers',
                 'Enemy units that are set up on the battlefield from Reserves '
                 'cannot be set up within 12" of this unit.'),
     ]),

    ('Intercessor Squad', 80,
     stat('6"', 4, '3+', 2, '6+', 2),
     [
         rng('Bolt pistol (x5)', '12"', 1, '3+', 4, 0, 1, 'Pistol'),
         rng('Bolt Rifle (x5)', '24"', 2, '3+', 4, -1, 1, 'Assault, Heavy'),
         mel('Close combat weapon (x5)', 3, '3+', 4, 0, 1),
     ],
     [
         ability('Objective Secured',
                 'If you control an objective marker at the end of your '
                 'Command phase and this unit is within range of that '
                 'objective marker, that objective marker remains under your '
                 'control, even if you have no models within range of it, '
                 'until your opponent controls it at the start or end of any '
                 'turn.'),
         ability('Target Elimination',
                 'Each time this unit is selected to shoot, it can use this '
                 'ability. If it does, until the end of the phase, add 2 to '
                 'the Attacks characteristic of bolt rifles equipped by models '
                 'in this unit and you can only select one enemy unit as the '
                 "target of all of this unit's attacks"),
     ]),

    ('Scout Squad', 70,
     stat('6"', 4, '4+', 2, '6+', 1),
     [
         rng('Bolt pistol (x5)', '12"', 1, '3+', 4, 0, 1, 'Pistol'),
         rng('Boltgun (x5)', '24"', 2, '3+', 4, 0, 1),
         mel('Close combat weapon (x5)', 2, '3+', 4, 0, 1),
     ],
     [
         ability('Guerrilla Tactics',
                 "At the end of your opponent's turn, if this unit is more "
                 'than 6" away from all enemy models, you can remove this '
                 'unit from the battlefield and place it into Strategic '
                 'Reserves.'),
     ]),

    ('Sternguard Veteran Squad', 100,
     stat('6"', 4, '3+', 2, '6+', 1),
     [
         rng('Sternguard Bolt Pistol (x5)', '12"', 1, '3+', 4, 0, 1,
             'Devastating Wounds, Pistol'),
         rng('Sternguard Bolt Rifle (x5)', '24"', 2, '3+', 4, -1, 1,
             'Assault, Devastating Wounds, Heavy, Rapid Fire 1'),
         mel('Close combat weapon (x5)', 4, '3+', 4, 0, 1),
     ],
     [
         ability('Sternguard Focus',
                 'Each time a model in this unit makes an attack that targets '
                 "your Oath of Moment Target, you can re-roll the wound roll"),
     ]),

    ('Tactical Squad', 140,
     stat('6"', 4, '3+', 2, '6+', 2),
     [
         rng('Bolt pistol (x10)', '12"', 1, '3+', 4, 0, 1, 'Pistol'),
         rng('Boltgun (x10)', '24"', 2, '3+', 4, 0, 1),
         mel('Close combat weapon (x10)', 2, '3+', 4, 0, 1),
     ],
     [
         ability('Combat Squads',
                 'At the start of the Declare Battle Formations step, before '
                 'any units have been set up, this unit can be split into two '
                 'units, each containing five models'),
     ]),

    ('Terminator Squad', 170,
     stat('5"', 5, '2+', 3, '6+', 1, invuln='4+'),
     [
         rng('Storm bolter (x5)', '24"', 2, '3+', 4, 0, 1, 'Rapid Fire 2'),
         mel('Power fist (x5)', 3, '3+', 8, -2, 2),
     ],
     [
         ability('Teleport Homer',
                 'At the start of the battle, you can set up one Teleport '
                 'Homer token for this unit anywhere on the battlefield that '
                 "is not in your opponent's deployment zone. If you do, once "
                 'per battle, you can target this unit with the Rapid Ingress '
                 'Stratagem for 0CP, but when resolving that Stratagem, you '
                 'must set this unit up within 3" horizontally of that token '
                 'and not within 9" horizontally of any enemy models. That '
                 'token is then removed.'),
         ability('Fury of the First',
                 'Each time a model in this unit makes an attack that targets '
                 'your Oath of Moment target, add 1 to the Hit roll.'),
     ]),

    ('Vanguard Veteran Squad', 100,
     stat('12"', 4, '3+', 2, '6+', 1),
     [
         rng('Bolt pistol (x5)', '12"', 1, '3+', 4, 0, 1, 'Pistol'),
         mel('Vanguard Veteran Weapon (x5)', 4, '3+', 5, -1, 1),
     ],
     [
         ability('Vanguard Assault',
                 'Each time this unit ends a Charge move, until the end of '
                 'the turn, melee weapons equipped by models in this unit '
                 'have the [LETHAL HITS] ability.'),
     ]),

    # ── Vehicles ──────────────────────────────────────────────────────────────

    ('Blood Angels Baal Predator', 125,
     stat('12"', 10, '3+', 11, '6+', 3),
     [
         rng('Baal Flamestorm Cannon', '18"', 'D6+3', 'N/A', 6, -2, 2,
             'Assault, Ignores Cover, Torrent'),
         mel('Armoured Tracks', 3, '4+', 6, 0, 1),
     ],
     [
         ability('Overcharged Engines',
                 'You can re-roll Advance rolls made for this model.'),
         ability('Damaged: 1-4 Wounds Remaining',
                 'While this model has 1-4 wounds remaining, each time this '
                 'model makes an attack, subtract 1 from the Hit roll.'),
     ]),

    ('Ballistus Dreadnought', 150,
     stat('8"', 10, '2+', 12, '6+', 4),
     [
         rng('Ballistus Lascannon', '48"', 2, '3+', 12, -3, 'D6+1'),
         rng('Ballistus Missile Launcher - Frag', '48"', '2D6', '3+', 5, 0,
             1, 'Blast'),
         rng('Ballistus Missile Launcher - Krak', '48"', 2, '3+', 10, -2,
             'D6'),
         rng('Twin Storm Bolter', '24"', 2, '3+', 4, 0, 1,
             'Rapid Fire 2, Twin-linked'),
         mel('Armoured Feet', 5, '3+', 7, 0, 1),
     ],
     [
         ability('Ballistus Strike',
                 'Each time this model makes a ranged attack that targets a '
                 'unit that is not Below Half-strength, you can re-roll the '
                 'Hit roll.'),
         ability('Damaged: 1-4 Wounds Remaining',
                 'While this model has 1-4 wounds remaining, each time this '
                 'model makes an attack, subtract 1 from the Hit roll.'),
     ]),

    ('Brutalis Dreadnought', 160,
     stat('8"', 10, '2+', 12, '6+', 4),
     [
         rng('Twin Icarus ironhail heavy stubber', '36"', 3, '3+', 4, 0, 1,
             'Anti-FLY 4+, Rapid Fire 3, Twin-linked'),
         rng('Brutalis Bolt Rifles', '24"', 4, '3+', 4, -1, 1, 'Twin-linked'),
         rng('Twin heavy bolter', '36"', 3, '3+', 5, -1, 2,
             'Sustained Hits 1, Twin-linked'),
         mel('Brutalis Fists', 6, '3+', 12, -2, 3, 'Twin-linked'),
     ],
     [
         ability('Brutalis Charge',
                 'Each time this model ends a Charge move, select one enemy '
                 'unit within Engagement Range of it and roll one D6: on a '
                 '2-3, that enemy unit suffers D3 mortal wounds; on a 4-5, '
                 'that enemy unit suffers 3 mortal wounds; on a 6, that enemy '
                 'unit suffers D3+3 mortal wounds'),
         ability('Damaged: 1-4 Wounds Remaining',
                 'While this model has 1-4 wounds remaining, each time this '
                 'model makes an attack, subtract 1 from the Hit roll.'),
     ]),

    ('Firestrike Servo-Turrets', 75,
     stat('3"', 6, '2+', 6, '6+', 2),
     [
         rng('Twin Firestrike Las-talon', '36"', 2, '2+', 10, -3, 'D6+1',
             'Twin-linked'),
         mel('Close combat weapon', 3, '3+', 4, 0, 1),
     ],
     [
         ability('Sentinel Protocols',
                 'Each time you select this unit for the Fire Overwatch '
                 'Stratagem, hits are scored on unmodified Hit rolls of 4+ '
                 'when resolving that Stratagem.'),
     ]),

    ('Hammerfall Bunker', 175,
     stat('-', 12, '2+', 14, '6+', 0),
     [
         rng('Hammerfall Missile Launcher - Superfrag', '48"', '2d6+2', '4+',
             5, 0, 1, 'Blast'),
         rng('Hammerfall Missile Launcher - Superkrak', '48"', 2, '4+', 10,
             -2, 'D6+1'),
         rng('Hammerfall Heavy Bolter Array', '36"', 6, '4+', 5, -1, 2,
             'Defensive Array, Sustained Hits 1, Twin-linked'),
     ],
     [
         ability('Fortification',
                 'While an enemy unit is only within Engagement Range of one '
                 'or more Fortifications from your army:\n'
                 '\u25a0 That unit can still be selected as the target of '
                 'ranged attacks, but each time such an attack is made, unless '
                 'it is made with a Pistol, subtract 1 from the Hit roll.\n'
                 '\u25a0 Models in that unit do not need to take Desperate '
                 'Escape tests due to Falling Back while Battle-shocked, '
                 'except for those that will move over enemy models when doing '
                 'so.'),
         ability('Ceramite Cover',
                 'Each time a ranged attack is allocated to a model, if that '
                 'model is not fully visible to every model in the attacking '
                 'unit because of this Fortification, that model has the '
                 'Benefit of Cover against that attack.'),
         ability('Damaged: 1-4 Wounds Remaining',
                 'While this model has 1-4 wounds remaining, each time this '
                 'model makes an attack, subtract 1 from the Hit roll.'),
         ability('Defensive Array',
                 'You can target this Fortification with the Fire Overwatch '
                 'Strategem for 0CP, and can do so even if you have already '
                 'targeted another unit with that Stratagem this turn. This '
                 'Fortification can only be targeted with that Stratagem once '
                 'per turn.'),
     ]),

    ('Impulsor', 80,
     stat('12"', 9, '3+', 11, '6+', 2),
     [
         rng('Fragstorm grenade launcher (x2)', '18"', 'D6', '3+', 4, 0, 1,
             'Blast'),
         mel('Armoured Hull', 3, '4+', 6, 0, 1),
     ],
     [
         ability('Transport',
                 'This model has a transport capacity of 7 TACTICUS or PHOBOS '
                 'INFANTRY models. It cannot transport JUMP PACK models.'),
         ability('Assault Vehicle',
                 'Units can disembark from this Transport after it has '
                 'Advanced. Units that do so count as having made a Normal '
                 'move, and cannot declare a charge that turn.'),
     ]),

    ('Invader ATV', 60,
     stat('12"', 5, '3+', 8, '6+', 2),
     [
         rng('Bolt pistol', '12"', 1, '3+', 4, 0, 1, 'Pistol'),
         rng('Twin bolt rifle', '24"', 2, '3+', 4, -1, 1, 'Twin-linked'),
         rng('Onslaught gatling cannon', '24"', 8, '3+', 5, 0, 1,
             'Devastating Wounds'),
         mel('Close combat weapon', 5, '3+', 4, 0, 1),
     ],
     [
         ability('Outrider Escort',
                 "Once per turn, in your opponent's Shooting phase, when "
                 'another friendly Adeptus Astartes Mounted unit within 6" '
                 'of this model is selected as the target of an attack, one '
                 'model from your army with this ability can use it. If it '
                 'does, after that enemy unit has finished making its attacks, '
                 'that model can shoot as if it were your Shooting phase, but '
                 'when resolving those attacks it can only target that enemy '
                 'unit [and only if it is an eligible target).'),
     ]),

    ('Land Raider Crusader', 220,
     stat('12"', 12, '2+', 16, '6+', 5),
     [
         rng('Hurricane Bolter (x2)', '24"', 6, '3+', 4, 0, 1,
             'Rapid Fire 6, Twin-linked'),
         rng('Twin assault cannon', '24"', 6, '3+', 6, 0, 1,
             'Devastating wounds, Twin-linked'),
         mel('Armoured Tracks', 6, '4+', 8, 0, 1),
     ],
     [
         ability('Transport',
                 'This model has a transport capacity of 16 Adeptus Astartes '
                 'Infantry models. Each Jump Pack, Wulfen, Gravis or '
                 'Terminator model takes up the space of 2 models and each '
                 'Centurion model takes up the space of 3 models.'),
         ability('Assault Ramp',
                 'Each time a unit disembarks from this model after it has '
                 'made a Normal move, that unit is still eligible to declare '
                 'a charge this turn.'),
         ability('Damaged: 1-5 Wounds Remaining',
                 'While this model has 1-5 wounds remaining, each time this '
                 'model makes an attack, subtract 1 from the Hit roll.'),
     ]),

    ('Outrider Squad', 80,
     stat('12"', 5, '3+', 4, '6+', 2),
     [
         rng('Heavy Bolt Pistol (x3)', '18"', 1, '3+', 4, -1, 1, 'Pistol'),
         rng('Twin bolt rifle (x3)', '24"', 2, '3+', 4, -1, 1, 'Twin-linked'),
         mel('Astartes Chainsword (x3)', 4, '3+', 4, -1, 1),
     ],
     [
         ability('Thunderous Impact',
                 'Each time a model in this unit makes a melee attack, if '
                 'this unit made a Charge move this turn, improve the Strength '
                 'and Damage characteristics of that attack by 1'),
     ]),

    ('Predator Destructor', 140,
     stat('10"', 10, '3+', 11, '6+', 3),
     [
         rng('Predator Autocannon', '48"', 4, '3+', 9, -1, 3, 'Rapid Fire 2'),
         mel('Armoured Tracks', 3, '4+', 6, 0, 1),
     ],
     [
         ability('Destructor',
                 'Each time this model makes a ranged attack that targets an '
                 'Infantry unit, improve the Armour Penetration characteristic '
                 'of that attack by 1.'),
         ability('Damaged: 1-4 Wounds Remaining',
                 'While this model has 1-4 wounds remaining, each time this '
                 'model makes an attack, subtract 1 from the Hit roll.'),
     ]),

    ('Redemptor Dreadnought', 205,
     stat('8"', 10, '2+', 12, '6+', 4),
     [
         rng('Heavy Onslaught Gatling Cannon', '24"', 12, '3+', 6, 0, 1,
             'Devastating Wounds'),
         rng('Heavy Flamer', '12"', 'D6', 'N/A', 5, -1, 1,
             'Ignores Cover, Torrent'),
         rng('Twin Fragstorm Grenade Launcher', '18"', 'D6', '3+', 4, 0, 1,
             'Blast, Twin-linked'),
         mel('Redemptor Fist', 5, '3+', 12, -2, 3),
     ],
     [
         ability('Duty Eternal',
                 'Each time an attack is allocated to this model, subtract 1 '
                 'from the Damage characteristic of that attack'),
         ability('Damaged: 1-4 Wounds Remaining',
                 'While this model has 1-4 wounds remaining, each time this '
                 'model makes an attack, subtract 1 from the Hit roll.'),
     ]),

    ('Repulsor Executioner', 230,
     stat('10"', 12, '3+', 16, '6+', 5),
     [
         rng('Heavy Onslaught Gatling Cannon', '24"', 12, '3+', 6, 0, 1,
             'Devastating Wounds'),
         rng('Repulsor Executioner Defensive Array', '24"', 10, '3+', 4, 0,
             1),
         rng('Twin heavy bolter', '36"', 3, '3+', 5, -1, 2,
             'Sustained Hits 1, Twin-linked'),
         rng('Twin Icarus ironhail heavy stubber', '36"', 3, '3+', 4, 0, 1,
             'Anti-FLY 4+, Rapid Fire 3, Twin-linked'),
         rng('Macro Plasma Incinerator - Standard', '36"', 'D6+1', '3+', 8,
             -3, 2, 'Blast'),
         rng('Macro Plasma Incinerator - Supercharge', '36"', 'D6+1', '3+',
             9, -4, 3, 'Blast, Hazardous'),
         mel('Armoured Hull', 6, '4+', 8, 0, 1),
     ],
     [
         ability('Transport',
                 'This model has a transport capacity of 7 Adeptus Astartes '
                 'Infantry models. Each Jump Pack, Wulfen, Gravis or '
                 'Terminator model takes up the space of 2 models and each '
                 'Centurion model takes up the space of 3 models.'),
         ability('Executioner',
                 'Each time this model makes an attack that targets a unit '
                 'that is Below Half-strength, add 1 to the Hit roll.'),
         ability('Damaged: 1-5 Wounds Remaining',
                 'While this model has 1-5 wounds remaining, each time this '
                 'model makes an attack, subtract 1 from the Hit roll.'),
     ]),

    ('Vindicator', 185,
     stat('9"', 11, '2+', 11, '6+', 3),
     [
         rng('Demolisher Cannon', '24"', 'D6+3', '3+', 14, -3, 'D6', 'Blast'),
         mel('Armoured Tracks', 3, '4+', 6, 0, 1),
     ],
     [
         ability('Siege Shield',
                 'When making ranged attacks with its demolisher cannon, this '
                 'model can target enemy units within Engagement Range of it '
                 '(provided no other friendly units are also within Engagement '
                 'Range of that enemy unit). In addition, when making ranged '
                 'attacks, this model does not suffer the penalty to its Hit '
                 'rolls for being within Engagement Range of one or more enemy '
                 'units.'),
         ability('Damaged: 1-4 Wounds Remaining',
                 'While this model has 1-4 wounds remaining, each time this '
                 'model makes an attack, subtract 1 from the Hit roll.'),
     ]),

    ('Whirlwind', 190,
     stat('10"', 10, '3+', 11, '6+', 3),
     [
         rng('Whirlwind Vengeance Launcher', '72"', 'D6+3', '3+', 8, -2, 2,
             'Blast, Indirect Fire'),
         mel('Armoured Tracks', 3, '4+', 6, 0, 1),
     ],
     [
         ability('Pinning Bombardment',
                 'In your Shooting phase, after this model has shot, if one '
                 'or more of those attacks made with its Whirlwind vengeance '
                 'launcher scored a hit against an enemy Infantry unit, that '
                 'unit must take a Battle-shock test.'),
         ability('Damaged: 1-4 Wounds Remaining',
                 'While this model has 1-4 wounds remaining, each time this '
                 'model makes an attack, subtract 1 from the Hit roll.'),
     ]),

]


# -- Command ------------------------------------------------------------------

class Command(BaseCommand):
    """Seed Blood Angels unit stats, weapon profiles, and abilities."""

    help = 'Seed Blood Angels stat data into the army calculator'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run', action='store_true',
            help='Preview changes without writing to the database.',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        updated = skipped = 0

        with transaction.atomic():
            for db_name, points, stats, weapons, abilities in BLOOD_ANGELS_UNITS:
                try:
                    unit = UnitType.objects.get(
                        name=db_name, faction__name=FACTION_NAME,
                    )
                except UnitType.DoesNotExist:
                    self.stdout.write(f'  SKIP (not found): {db_name}')
                    skipped += 1
                    continue

                if dry_run:
                    self.stdout.write(
                        f'  DRY-RUN: would update {db_name} '
                        f'({points}pts, T{stats["stat_toughness"]})'
                    )
                    updated += 1
                    continue

                # Update stat fields
                unit.points_cost = points
                for field, value in stats.items():
                    setattr(unit, field, value)
                unit.save()

                # Replace weapon profiles
                unit.weapon_profiles.all().delete()
                for order, wp in enumerate(weapons):
                    WeaponProfile.objects.create(unit_type=unit, order=order, **wp)

                # Replace abilities
                unit.abilities.all().delete()
                for order, ab in enumerate(abilities):
                    UnitAbility.objects.create(
                        unit_type=unit, order=order,
                        name=ab['name'], description=ab['description'],
                    )

                self.stdout.write(f'  OK: {db_name}')
                updated += 1

            if dry_run:
                transaction.set_rollback(True)

        self.stdout.write(
            self.style.SUCCESS(
                f'\nBlood Angels seed complete: '
                f'{updated} updated, {skipped} skipped.'
            )
        )
