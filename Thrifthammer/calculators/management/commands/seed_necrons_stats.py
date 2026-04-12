"""
Management command: seed_necrons_stats

Seeds points costs, stat lines, weapon profiles, and unit abilities
for all Necrons units in the database. Safe to re-run — uses
delete+create for weapons/abilities and direct field writes for stats.

Usage:
    python manage.py seed_necrons_stats
    python manage.py seed_necrons_stats --dry-run
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from calculators.models import UnitAbility, UnitType, WeaponProfile


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
# Weapon/ability text sourced from parsed New Recruit HTML (2026-04-12).
# Mapping: necrons_mapping.csv; duplicates resolved per instructions
# (first card wins for shared db_name entries).

NECRONS_UNITS = [

    # -- Epic Heroes / Named Characters ---------------------------------------

    ('Illuminor Szeras', 165,
     stat('8"', 8, '2+', 9, '6+', 3, invuln='4+'),
     [
         rng('Eldritch lance', '36"', '3', '3+', 9, -3, 3),
         mel('Eldritch lance', '4', '3+', 9, -3, 3),
         mel('Impaling legs', '4', '3+', 6, -1, 1, 'Extra Attacks'),
     ],
     [
         ability('Illuminor',
                 'While this model is within 3" of one or more other friendly '
                 'NECRONS units, this model has the Lone Operative ability.'),
         ability('Mechanical Augmentation (Aura)',
                 'While a friendly NECRONS BATTLELINE unit is within 3" of this '
                 'model, each time a model in that unit makes an attack, improve '
                 'the Armour Penetration characteristic of that attack by 1, and '
                 'each time an attack targets that unit, worsen the Armour '
                 'Penetration characteristic of that attack by 1.'),
         ability('Atomic Energy Manipulator',
                 'At the end of the Fight phase, if this model destroyed one or '
                 'more models this phase, until the end of the battle, add 3" to '
                 'the range of its Mechanical Augmentation ability (to a maximum '
                 'of 12").'),
     ]),

    ('Imotekh the Stormlord', 100,
     stat('5"', 5, '2+', 6, '6+', 1, invuln='4+'),
     [
         rng('Gauntlet of Fire', '12"', 'D6', 'N/A', 5, -1, 1,
             'Ignores Cover, Torrent'),
         rng('Staff of the Destroyer', '18"', '3', '2+', 6, -3, 2),
         mel('Staff of the Destroyer', '4', '2+', 6, -3, 2,
             'Devastating Wounds'),
     ],
     [
         ability('Leader',
                 'This model can be attached to the following units:\n'
                 '\u25a0 IMMORTALS\n'
                 '\u25a0 LYCHGUARD\n'
                 '\u25a0 NECRON WARRIORS'),
         ability('Grand Strategist',
                 'At the start of your Command phase, if this model is on the '
                 'battlefield, you gain 1CP.'),
         ability('Lord of the Storm',
                 'Once per battle, at the end of your Command phase, this model '
                 'can use this ability. If it does, roll one D6 for each enemy '
                 'unit within 12" of this model: on a 2-5, that enemy unit '
                 'suffers D3 mortal wounds; on a 6, that enemy unit suffers '
                 'D3+3 mortal wounds.'),
     ]),

    ('Nekrosor Ammentar', 185,
     stat('10"', 8, '3+', 9, '6+', 3, invuln='4+'),
     [
         rng('Enmitic disintegrators', '18"', '4', '2+', 6, -2, 1,
             'Ignores Cover, Pistol, Sustained Hits 2'),
         mel('Blade tail and whip coils', '6', '2+', 6, -1, 1, 'Extra Attacks'),
         mel('Unmaker gauntlet', '6', '2+', 10, -3, 3),
     ],
     [
         ability('Protective Disciples',
                 'While this model is within 3" of one or more other friendly '
                 'Destroyer Cult units, this model has the Lone Operative '
                 'ability.'),
         ability('Infectious Murder\u2011madness (Aura)',
                 'While a friendly Necrons unit (excluding Monster and Titanic '
                 'units) is within 6" of this model, each time a model in that '
                 'unit makes an attack, if that model has the Destroyer Cult '
                 'keyword or that enemy unit is the closest eligible target, that '
                 'attack has the [SUSTAINED HITS 1] ability.'),
         ability('Prophet of Destruction',
                 'Each time this model destroys an enemy unit, select one other '
                 'friendly Destroyer Cult unit within 9" of it. Until the end of '
                 'the phase, each time a model in that unit makes an attack, '
                 're\u2011roll a Wound roll of 1.'),
         ability('Nullstone Field Generator (Aura)',
                 'While a friendly Necrons unit is within 6" of the bearer, '
                 'models in that unit have the Feel No Pain 5+ ability against '
                 'mortal wounds and Psychic Attacks.'),
     ]),

    ('Orikan the Diviner', 80,
     stat('5"', 4, '4+', 4, '6+', 1, invuln='4+'),
     [
         mel('Staff of Tomorrow', '2', '3+', 4, -3, 'D3', 'Devastating Wounds'),
     ],
     [
         ability('Master Chronomancer',
                 'While this model is leading a unit, models in that unit have '
                 'a 4+ invulnerable save.'),
         ability('The Stars Are Right',
                 'Once per battle, at the start of the Fight phase, this model '
                 'can use this ability. If it does, until the end of the phase, '
                 'triple the Attacks and Strength characteristics of this '
                 'model\u2019s Staff of Tomorrow and every successful Wound roll '
                 'made for this model\u2019s attacks scores a Critical Wound.'),
         ability('Leader',
                 'This model can be attached to the following units:\n'
                 '\u25a0 IMMORTALS\n'
                 '\u25a0 NECRON WARRIORS\n'
                 'You can attach this model to one of the above units even if '
                 'one ROYAL WARDEN or NOBLE model has already been attached to '
                 'it. If you do, and that Bodyguard unit is destroyed, the '
                 'Leader units attached to it become separate units, with their '
                 'original Starting Strengths.'),
     ]),

    # Szarekh, The Silent King — use primary_stats (Szarekh model)
    ('Szarekh, The Silent King', 400,
     stat('8"', 10, '2+', 16, '6+', 6, invuln='4+'),
     [
         rng('Sceptre of Eternal Glory', '24"', '2', '2+', 10, -3, 3,
             'Devastating Wounds'),
         rng('Staff of Stars', '24"', '12', '2+', 6, -1, 1, 'Indirect Fire'),
         rng('Annihilator beam (x2)', '24"', '1', '2+', 14, -4, 6),
         mel('Weapons of the Final Triarch', '12', '2+', 8, -3, 2, 'Lethal Hits'),
         mel('Armoured bulk (x2)', '1', '4+', 4, 0, 1),
     ],
     [
         ability('Damaged: 1-6 wounds remaining',
                 'While this unit\u2019s Szarekh model has 1-6 wounds remaining, '
                 'halve the Attacks characteristic of that model\u2019s weapons, '
                 'and each time this unit makes an attack, subtract 1 from the '
                 'Hit roll.'),
         ability('Voice of the Triarch',
                 'At the start of the battle round, select one Triarch ability. '
                 'Until the start of the next battle round, this unit has that '
                 'ability.'),
         ability('The Silent King (Aura)',
                 'While a friendly NECRONS unit is within 6" of this unit\'s '
                 'Szarekh model, improve that unit\'s Leadership characteristic '
                 'by 1.'),
         ability('Triarchal Menhirs',
                 'If this unit\u2019s Szarekh model is destroyed, all of this '
                 'unit\u2019s remaining Triarchal Menhir models are also '
                 'destroyed.'),
     ]),

    ('Trazyn the Infinite', 75,
     stat('5"', 5, '2+', 6, '6+', 1, invuln='4+'),
     [
         mel('Empathic Obliterator', '4', '2+', 7, 0, 'D3', 'Sustained Hits D3'),
     ],
     [
         ability('Leader',
                 'This model can be attached to the following units:\n'
                 '\u25a0 IMMORTALS\n'
                 '\u25a0 LYCHGUARD\n'
                 '\u25a0 NECRON WARRIORS'),
         ability('Ancient Collector',
                 'While this model is leading a unit, at the end of your Command '
                 'phase, if that unit is within range of an objective marker you '
                 'control, that objective marker remains under your control, even '
                 'if you have no models within range of it, until your opponent '
                 'controls it at start or end of any turn.'),
         ability('Surrogate Hosts',
                 'At the start of your Command phase, if this model is on the '
                 'battlefield, you can select one other friendly NECRONS INFANTRY '
                 'CHARACTER model on the battlefield (excluding SKORPEKH LORD or '
                 'EPIC HERO models). The selected model is destroyed (ignoring '
                 'any rules that are triggered when a model is destroyed) and '
                 'this model is put\nin its place, with all of its wounds '
                 'remaining (if the selected model was leading a unit, this model '
                 'now attaches to that unit as its Leader).'),
     ]),

    # -- Characters / Leaders -------------------------------------------------

    ('Chronomancer', 65,
     stat('5"', 4, '4+', 4, '6+', 1, invuln='4+'),
     [
         rng("Chronomancer's stave", '18"', 'D6', '4+', 5, -1, 1, 'Blast'),
         mel("Chronomancer's stave", '3', '4+', 5, -1, 1),
     ],
     [
         ability('Leader',
                 'This model can be attached to the following units:\n'
                 '\u25a0 IMMORTALS\n'
                 '\u25a0 NECRON WARRIORS\n'
                 'You can attach this model to one of the above units even if '
                 'one ROYAL WARDEN or NOBLE model has already been attached to '
                 'it. If you do, and that Bodyguard unit is destroyed, the '
                 'Leader units attached to it become separate units, with their '
                 'original Starting Strengths.'),
         ability('Timesplinter Mantle',
                 'While this model is leading a unit, each time an attack '
                 'targets that unit, subtract 1 from the Hit roll.'),
         ability('Chronometron',
                 'In your Shooting phase, after this model\u2019s unit has shot, '
                 'if it is not within Engagement Range of any enemy units, that '
                 'unit can make a Normal move of up to 5". If it does, until the '
                 'end of the turn, that unit is not eligible to declare a charge.'),
     ]),

    # Technomancer card → db_name "Cryptek"
    ('Cryptek', 80,
     stat('10"', 4, '4+', 4, '6+', 1),
     [
         rng('Staff of light', '18"', '3', '4+', 5, -2, 1),
         mel('Staff of light', '2', '4+', 5, -2, 1),
     ],
     [
         ability('Leader',
                 'This model can be attached to the following units:\n'
                 '\u25a0 CANOPTEK WRAITHS\n'
                 '\u25a0 IMMORTALS\n'
                 '\u25a0 NECRON WARRIORS\n'
                 'You can attach this model to one of the above units even if '
                 'one ROYAL WARDEN or NOBLE model has already been attached to '
                 'it. If you do, and that Bodyguard unit is destroyed, the '
                 'Leader units attached to it become separate units, with their '
                 'original Starting Strengths.'),
         ability('Rites of Reanimation',
                 'While this model is leading a unit, models in that unit have '
                 'the Feel No Pain 5+ ability.'),
         ability('Technomancer',
                 'At the end of your Movement phase, select one friendly NECRONS '
                 'model within 6" of the bearer. That model regains up to D3 '
                 'lost wounds. Each model can only be selected for this ability '
                 'once per turn.'),
     ]),

    ('Hexmark Destroyer', 75,
     stat('8"', 5, '3+', 5, '6+', 1),
     [
         rng('Enmitic disintegrator pistols', '18"', '6', '2+', 6, -2, 1,
             'Ignores Cover, Pistol'),
         mel('Close combat weapon', '4', '3+', 5, 0, 1),
     ],
     [
         ability('Inescapable Death',
                 'Once per turn, one unit from your army with this ability can '
                 'be targeted with the Fire Overwatch Stratagem for 0CP, even '
                 'if you have already used that Stratagem on a different unit '
                 'this phase. In addition, each time you target this unit with '
                 'the Fire Overwatch Stratagem, while resolving that Stratagem, '
                 'hits are scored on unmodified Hit rolls of 2+.'),
         ability('Multi-threat Eliminator',
                 'Once per turn, in your opponent\'s Shooting phase, when an '
                 'enemy unit makes a ranged attack that targets a friendly '
                 'NECRONS unit within 3" of a model with this ability, after '
                 'that enemy has shot, one model with this ability that is '
                 'within 3" of that target can shoot as if it were your Shooting '
                 'phase, but must target that enemy unit when doing so, and can '
                 'only do so if that enemy unit is an eligible target.'),
     ]),

    # Necron Overlord
    ('Necron Overlord', 85,
     stat('5"', 5, '2+', 6, '6+', 1),
     [
         rng('Tachyon arrow', '72"', '1', '2+', 16, -5, 'D6+2', 'One Shot'),
         mel("Overlord's blade", '4', '2+', 8, -3, 2, 'Devastating Wounds'),
     ],
     [
         ability('Leader',
                 'This model can be attached to the following units:\n'
                 '\u25a0 IMMORTALS\n'
                 '\u25a0 LYCHGUARD\n'
                 '\u25a0 NECRON WARRIORS'),
     ]),

    # Overlord with Translocation Shroud card → db_name "Overlord with Tachyon Arrow"
    ('Overlord with Tachyon Arrow', 85,
     stat('5"', 5, '2+', 6, '6+', 1),
     [
         mel("Overlord's blade", '4', '2+', 8, -3, 2, 'Devastating Wounds'),
     ],
     [
         ability('Leader',
                 'This model can be attached to the following units:\n'
                 '\u25a0 IMMORTALS\n'
                 '\u25a0 LYCHGUARD\n'
                 '\u25a0 NECRON WARRIORS'),
     ]),

    # Necron Psychomancer
    ('Necron Psychomancer', 55,
     stat('5"', 4, '4+', 4, '6+', 1),
     [
         rng('Abyssal lance', '18"', '1', '4+', 6, -3, 3),
         mel('Abyssal lance', '1', '4+', 6, -3, 3),
     ],
     [
         ability('Leader',
                 'This model can be attached to the following units:\n'
                 '\u25a0 IMMORTALS\n'
                 '\u25a0 NECRON WARRIORS\n'
                 'You can attach this model to one of the above units even if '
                 'one ROYAL WARDEN or NOBLE model has already been attached to '
                 'it. If you do, and that Bodyguard unit is destroyed, the '
                 'Leader units attached to it become separate units, with their '
                 'original Starting Strengths.'),
         ability('Nightmare Shroud (Aura)',
                 'In the Battle-shock step of your opponent\'s Command phase, '
                 'if an enemy unit that is below its Starting Strength is within '
                 '6" of this model, that enemy unit must take a Battle-shock '
                 'test, subtracting 1 from the roll when it does so.'),
         ability('Harbinger of Despair',
                 'Once per turn, at the start of your Command, Movement, '
                 'Shooting, Charge or Fight phase, you can select one enemy unit '
                 'within 18" of this model. That unit must take a Battle-shock '
                 'test, subtracting 1 from the roll when it does so.'),
     ]),

    # Necron Royal Warden
    ('Necron Royal Warden', 50,
     stat('5"', 5, '3+', 4, '6+', 1),
     [
         rng('Relic gauss blaster', '24"', '2', '3+', 5, -1, 2,
             'Lethal Hits, Rapid Fire 2'),
         mel('Close combat weapon', '4', '3+', 5, 0, 1),
     ],
     [
         ability('Leader',
                 'This model can be attached to the following units:\n'
                 '\u25a0 IMMORTALS\n'
                 '\u25a0 NECRON WARRIORS'),
         ability('Adaptive Strategy',
                 'This model\'s unit is eligible to shoot and declare a charge '
                 'in a turn in which it Fell Back.'),
         ability('Engrammatic Logic',
                 'Once per battle, at the start of any phase, you can select '
                 'one friendly NECRONS unit that is Battle-shocked and within '
                 '12" of this model. That unit is no longer Battle-shocked.'),
     ]),

    # Skorpekh Lord card → db_name "Necrons Royal Court" (first of 4 duplicates)
    # Per instructions, use Canoptek Reanimator card (first in CSV) for Royal Court.
    # Canoptek Reanimator is listed first (row 30), so use its stats.
    ('Necrons Royal Court', 75,
     stat('8"', 6, '3+', 6, '8+', 3),
     [
         rng('Atomiser beam (x2)', '12"', '3', '4+', 6, -2, 1),
         mel("Reanimator's claws", '4', '4+', 5, 0, 1),
     ],
     [
         ability('Nanoscarab Reanimation Beam (Aura)',
                 'While a friendly NECRONS unit is within 3" of this model, '
                 'each time that unit\u2019s Reanimation Protocols activate, '
                 'that unit reanimates an additional D3 wounds.'),
     ]),

    # -- Infantry -------------------------------------------------------------

    ('Deathmarks', 60,
     stat('5"', 5, '3+', 1, '7+', 1),
     [
         rng('Synaptic disintegrator (x5)', '36"', '1', '3+', 5, -2, 2,
             'Heavy, Precision'),
         mel('Close combat weapon (x5)', '2', '3+', 4, 0, 1),
     ],
     [
         ability('Hyperspace Hunters',
                 'Once per turn, in the Reinforcements step of your opponent\u2019s '
                 'Movement phase, when an enemy unit is set up on the battlefield '
                 'from Reserves within 18" of and visible to this unit, this unit '
                 'can shoot as if it were your Shooting phase, but must only '
                 'target that enemy unit when doing so, and can only do so if '
                 'that enemy unit is an eligible target.'),
     ]),

    ('Necron Flayed Ones', 60,
     stat('5"', 4, '4+', 1, '7+', 1),
     [
         mel('Flayer claws (x5)', '4', '3+', 4, -1, 1,
             'Sustained Hits 1, Twin-linked'),
     ],
     [
         ability('Flesh Hunger',
                 'Each time a model in this unit makes a melee attack, if the '
                 'target of that attack is Below Half-strength, a successful Hit '
                 'roll scores a Critical Hit.'),
     ]),

    ('Necron Immortals', 70,
     stat('5"', 5, '3+', 1, '7+', 2),
     [
         rng('Gauss blaster (x5)', '24"', '2', '3+', 5, -1, 1, 'Lethal Hits'),
         mel('Close combat weapon (x5)', '2', '3+', 4, 0, 1),
     ],
     [
         ability('Implacable Eradication',
                 'Each time a model in this unit makes an attack, re-roll a '
                 'Wound roll of 1. If the target of that attack is an enemy unit '
                 'within range of an objective marker, you can re-roll the Wound '
                 'roll instead.'),
     ]),

    ('Necron Lychguard', 85,
     stat('5"', 5, '3+', 2, '7+', 1),
     [
         mel('Warscythe (x5)', '2', '3+', 8, -3, 2, 'Devastating Wounds'),
     ],
     [
         ability('Guardian Protocols',
                 'While a NOBLE model is leading this unit, each time an attack '
                 'targets this unit, if the Strength characteristic of that '
                 'attack is greater than the Toughness characteristic of this '
                 'unit, subtract 1 from the Wound roll.'),
     ]),

    ('Necron Warriors', 90,
     stat('5"', 4, '4+', 1, '7+', 2),
     [
         rng('Gauss flayer (x10)', '24"', '1', '4+', 4, 0, 1,
             'Lethal Hits, Rapid Fire 1'),
         mel('Close combat weapon (x10)', '1', '4+', 4, 0, 1),
     ],
     [
         ability('Their Number is Legion',
                 'Each time this unit\u2019s Reanimation Protocols activate, '
                 'you can re-roll the dice to see how many wounds are '
                 'regenerated.'),
     ]),

    ('Ophydian Destroyers', 80,
     stat('10"', 5, '4+', 3, '7+', 2),
     [
         mel('Ophydian hyperphase weapons (x3)', '5', '3+', 4, -2, 2),
     ],
     [
         ability('Tunnelling Horrors',
                 'At the end of your opponent\u2019s turn, if this unit is not '
                 'within Engagement Range of one or more enemy units, you can '
                 'remove this unit from the battlefield. In the Reinforcements '
                 'step of your next Movement phase, set it up anywhere on the '
                 'battlefield that is more than 9" horizontally away from all '
                 'enemy models.'),
     ]),

    ('Skorpekh Destroyers', 90,
     stat('8"', 6, '3+', 3, '7+', 2),
     [
         mel('Skorpekh hyperphase weapons (x3)', '4', '3+', 7, -2, 2),
     ],
     [
         ability('Whirling Onslaught',
                 'Each time a model in this unit makes a melee attack, re-roll '
                 'a Hit roll of 1. If this unit made a Charge move this turn, '
                 'you can re-roll the Hit roll instead.'),
     ]),

    ('Triarch Praetorians', 90,
     stat('10"', 5, '3+', 2, '7+', 1),
     [
         rng('Rod of covenant (x5)', '12"', '1', '3+', 5, -2, 2),
         mel('Rod of covenant (x5)', '3', '3+', 5, -2, 2),
     ],
     [
         ability('Relentless Combatants',
                 'You can re-roll Charge rolls made for this unit, and this '
                 'unit is eligible to declare a charge in a turn in which it '
                 'Fell Back.'),
     ]),

    # Lokhust Destroyers card → db_name "Lokhust Destroyer Squadron"
    ('Lokhust Destroyer Squadron', 40,
     stat('8"', 6, '3+', 3, '7+', 2),
     [
         rng('Gauss cannon', '24"', '3', '3+', 5, -2, 2, 'Lethal Hits'),
         mel('Close combat weapon', '2', '3+', 4, 0, 1),
     ],
     [
         ability('Hard-wired for Destruction',
                 'Each time a model in this unit makes a ranged attack that '
                 'targets the closest eligible enemy unit, re-roll a Hit roll '
                 'of 1. If the target of that attack is within range of an '
                 'objective marker your opponent controls, you can re-roll the '
                 'Hit roll instead.'),
     ]),

    # Lokhust Heavy Destroyers card → db_name "Lokhust Heavy Destroyer"
    ('Lokhust Heavy Destroyer', 55,
     stat('8"', 6, '3+', 4, '7+', 2),
     [
         rng('Enmitic exterminator', '36"', '6', '3+', 6, -1, 1,
             'Heavy, Rapid Fire 6, Sustained Hits 1'),
         mel('Close combat weapon', '2', '3+', 4, 0, 1),
     ],
     [
         ability('Optimised for Slaughter',
                 'Each time a model in this unit makes an attack with an enmitic '
                 'exterminator that targets a unit (excluding MONSTERS and '
                 'VEHICLES), re-roll a Wound roll of 1. Each time a model in '
                 'this unit makes an attack with a gauss destructor against a '
                 'MONSTER or VEHICLE unit, re-roll a Wound roll of 1.'),
     ]),

    ('Tomb Blades', 75,
     stat('12"', 5, '4+', 2, '7+', 2),
     [
         rng('Twin gauss blaster (x3)', '24"', '2', '3+', 5, -1, 1,
             'Lethal Hits, Twin-linked'),
         mel('Close combat weapon (x3)', '1', '4+', 4, 0, 1),
     ],
     [
         ability('Evasion Engrams',
                 'In your Shooting phase, after this unit has shot, it can make '
                 'a Normal Move of up to 6". If it does, until the end of the '
                 'turn, this unit is not eligible to declare a charge.'),
     ]),

    ('Canoptek Wraiths', 110,
     stat('10"', 6, '3+', 4, '8+', 2, invuln='4+'),
     [
         mel('Vicious claws (x3)', '4', '4+', 6, -1, 2),
     ],
     [
         ability('Wraith Form',
                 'Each time this unit ends a Normal move, you can select one '
                 'enemy unit it moved over during that move and roll one D6 for '
                 'each model in this unit: for each 4+, that enemy unit suffers '
                 '1 mortal wound.'),
     ]),

    # -- Monsters / C'tan Shards ---------------------------------------------

    # C'tan Shard of the Deceiver → db_name "C'tan Shard of The Deceiver"
    ("C'tan Shard of The Deceiver", 310,
     stat('8"', 11, '3+', 16, '6+', 4, invuln='4+'),
     [
         rng('Cosmic insanity', '18"', '6', '2+', 6, -2, 2,
             'Anti-CHARACTER 4+, Devastating Wounds, Precision'),
         mel('Golden fists', '8', '2+', 10, -3, 3),
     ],
     [
         ability('Grand Illusion',
                 'If your army includes this model, after both players have '
                 'deployed their armies, select up to three NECRONS units from '
                 'your army and redeploy them. When doing so, any of those units '
                 'can be placed in Strategic Reserves, regardless of how many '
                 'units are already in Strategic Reserves.'),
         ability('Necrodermis',
                 'Each time an attack is allocated to this model, subtract 1 '
                 'from the Damage characteristic of that attack.'),
         ability('Enslaved Star God',
                 'This model cannot be your WARLORD.'),
     ]),

    ("C'tan Shard of the Nightbringer", 340,
     stat('10"', 11, '3+', 16, '6+', 4, invuln='4+'),
     [
         rng('Gaze of death', '18"', 'D3', '2+', 12, -3, 'D6+3'),
         mel('Scythe of the Nightbringer - strike', '6', '2+', 14, -4, 'D6+2',
             'Devastating Wounds'),
         mel('Scythe of the Nightbringer - sweep', '14', '2+', 8, -2, 2),
     ],
     [
         ability('Drain Life',
                 'At the end of the Fight phase, roll one D6 for each enemy '
                 'unit within 6" of this model: on a 4+, that enemy unit '
                 'suffers D3 mortal wounds.'),
         ability('Necrodermis',
                 'Each time an attack is allocated to this model, subtract 1 '
                 'from the Damage characteristic of that attack.'),
         ability('Enslaved Star God',
                 'This model cannot be your WARLORD.'),
     ]),

    # C'tan Shard of the Void Dragon → db_name uses Unicode right single quote \u2019
    ('Necron C\u2019tan Shard of the Void Dragon', 330,
     stat('10"', 11, '3+', 16, '6+', 4, invuln='4+'),
     [
         rng('Spear of the Void Dragon', '12"', 'D3', '2+', 8, -3, 'D6+2',
             'Anti-VEHICLE 2+'),
         rng('Voltaic storm', '18"', 'D6+3', '2+', 7, -1, 2,
             'Blast, Sustained Hits 2'),
         mel('Canoptek tail blades', '6', '2+', 6, -1, 1, 'Extra Attacks'),
         mel('Spear of the Void Dragon - strike', '5', '2+', 12, -4, 'D6+2',
             'Anti-VEHICLE 2+'),
         mel('Spear of the Void Dragon - sweep', '10', '2+', 8, -1, 2),
     ],
     [
         ability('Matter Absorption',
                 'At the start of your Shooting phase, select one enemy VEHICLE '
                 'unit within 12" of this model and roll one D6: on a 2+, that '
                 'enemy unit suffers D3 mortal wounds and this model regains up '
                 'to that many lost wounds.'),
         ability('Necrodermis',
                 'Each time an attack is allocated to this model, subtract 1 '
                 'from the Damage characteristic of that attack.'),
         ability('Enslaved Star God',
                 'This model cannot be your WARLORD.'),
     ]),

    # Obelisk card → db_name "Obelisk & Transcendent C'tan" (first in CSV)
    # Transcendent C'tan is skipped as duplicate
    ("Obelisk & Transcendent C'tan", 300,
     stat('8"', 13, '2+', 24, '7+', 8),
     [
         rng('Tesla sphere (x4)', '24"', '6', '3+', 7, 0, 1,
             'Anti-FLY 4+, Sustained Hits 2'),
         mel('Armoured bulk', '6', '4+', 8, 0, 1),
     ],
     [
         ability('Damaged: 1-8 wounds remaining',
                 'While this model has 1-8 wounds remaining, subtract 4 from '
                 'its Objective Control characteristic and each time this model '
                 'makes an attack, subtract 1 from the Hit roll.'),
         ability('Gravitic Pulse',
                 'At the start of your opponent\u2019s Movement phase, you can '
                 'select one enemy unit within 18" of and visible to this model. '
                 'Until the end of the turn, halve the Move characteristic of '
                 'models in that unit and halve Advance and Charge rolls made '
                 'for that unit. In addition, if that unit can FLY, until the '
                 'start of your next Movement phase, roll one D6 each time that '
                 'unit ends any type of move: on a 4+, that unit suffers D3 '
                 'mortal wounds.'),
     ]),

    # -- Vehicles / Walkers --------------------------------------------------

    # Necron Catacomb Command Barge
    ('Necron Catacomb Command Barge', 120,
     stat('10"', 8, '3+', 9, '6+', 3, invuln='4+'),
     [
         rng('Gauss cannon', '24"', '3', '3+', 5, -2, 2, 'Lethal Hits'),
         rng('Staff of light', '18"', '3', '2+', 5, -2, 1),
         mel('Staff of light', '4', '3+', 5, -2, 1),
     ],
     [
         ability('Carrier Wave (Aura)',
                 'While a friendly NECRONS unit is within 6" of this model, '
                 'add 1 to the Objective Control characteristic of models in '
                 'that unit.'),
         ability('Advanced Quantum Shielding',
                 'Each time an attack targets this model, if the Strength '
                 'characteristic of that attack is greater than this model\u2019s '
                 'Toughness characteristic, subtract 1 from the Wound roll.'),
     ]),

    ('Annihilation Barge', 105,
     stat('10"', 8, '3+', 9, '7+', 3, invuln='4+'),
     [
         rng('Twin tesla destructor', '36"', '6', '3+', 8, 0, 2,
             'Sustained Hits 2, Twin-linked'),
         rng('Gauss cannon', '24"', '3', '3+', 5, -2, 2, 'Lethal Hits'),
         mel('Armoured bulk', '3', '4+', 6, 0, 1),
     ],
     [
         ability('Malevolent Arcing',
                 'In your Shooting phase, each time you select a target for '
                 'this model\u2019s twin tesla destructor, roll one D6 for the '
                 'target unit and one D6 for every other enemy unit within 3" '
                 'of the target unit. On a 5+, the unit being rolled for is '
                 'struck by arcing energies; after resolving all of this '
                 'model\u2019s attacks against the target unit, each unit '
                 'struck by arcing energies suffers D3 mortal wounds.'),
     ]),

    ('Canoptek Doomstalker', 140,
     stat('8"', 8, '3+', 12, '8+', 4, invuln='4+'),
     [
         rng('Doomsday blaster', '48"', 'D6+1', '4+', 14, -3, 3,
             'Blast, Heavy'),
         rng('Twin gauss flayer', '24"', '1', '4+', 4, 0, 1,
             'Lethal Hits, Rapid Fire 1, Twin-linked'),
         mel('Doomstalker limbs', '3', '4+', 6, 0, 1),
     ],
     [
         ability('Damaged: 1-4 wounds remaining',
                 'While this model has 1-4 wounds remaining, each time this '
                 'model makes an attack, subtract 1 from the Hit roll.'),
         ability('Sentinel Construct',
                 'Each time you target this unit with the Fire Overwatch '
                 'Stratagem, while resolving that Stratagem, hits are scored '
                 'on unmodified Hit rolls of 5+.'),
     ]),

    # Canoptek Spyders card → db_name "Necron Canoptek Spyder"
    ('Necron Canoptek Spyder', 75,
     stat('5"', 7, '3+', 6, '8+', 2),
     [
         mel('Automaton claws', '5', '4+', 8, -2, 2),
     ],
     [
         ability('Canoptek Swarm',
                 'In your Command phase, select one friendly CANOPTEK SCARAB '
                 'SWARM unit within 6" of this unit. One destroyed model is '
                 'returned to that CANOPTEK SCARAB SWARM unit for each SPYDER '
                 'model in this unit.'),
     ]),

    # Necron Doom Scythe
    ('Necron Doom Scythe', 230,
     stat('20+"', 9, '3+', 12, '7+', 0),
     [
         rng('Heavy death ray', '36"', '3', '3+', 16, -4, 'D6+1',
             'Sustained Hits D3'),
         rng('Twin tesla destructor', '36"', '6', '3+', 8, 0, 2,
             'Sustained Hits 2, Twin-linked'),
         mel('Armoured bulk', '3', '4+', 6, 0, 1),
     ],
     [
         ability('Atavistic Instigation',
                 'Each time this model targets an enemy unit with its heavy '
                 'death ray, your opponent must declare if that unit will stand '
                 'firm or duck for cover:\n'
                 '\u25a0 If it stands firm, when resolving attacks against that '
                 'unit this phase, a successful unmodified Hit roll of 5+ scores '
                 'a Critical Hit.\n'
                 '\u25a0 If it ducks for cover, until the start of your next '
                 'Shooting phase, each time a model in that unit makes an '
                 'attack, subtract 1 from the Hit roll.'),
         ability('Damaged: 1-4 wounds remaining',
                 'While this model has 1-4 wounds remaining, each time this '
                 'model makes an attack, subtract 1 from the Hit roll.'),
     ]),

    # Necron Doomsday Ark
    ('Necron Doomsday Ark', 200,
     stat('10"', 9, '3+', 14, '7+', 5, invuln='4+'),
     [
         rng('Doomsday cannon', '72"', 'D6+1', '3+', 18, -4, 4, 'Blast, Heavy'),
         rng('Gauss flayer array (x2)', '24"', '5', '3+', 4, 0, 1,
             'Lethal Hits, Rapid Fire 5'),
         mel('Armoured bulk', '3', '4+', 6, 0, 1),
     ],
     [
         ability('Damaged: 1-5 wounds remaining',
                 'While this model has 1-5 wounds remaining, each time this '
                 'model makes an attack, subtract 1 from the Hit roll.'),
         ability('Overwhelming Obliteration',
                 'In your Movement phase, if this model Remains Stationary, '
                 'until the end of the turn, its doomsday cannon has the '
                 '[DEVASTATING WOUNDS] ability.'),
     ]),

    ('Ghost Ark', 115,
     stat('10"', 9, '3+', 14, '7+', 3, invuln='4+'),
     [
         rng('Gauss flayer array (x2)', '24"', '5', '3+', 4, 0, 1,
             'Lethal Hits, Rapid Fire 5'),
         mel('Armoured bulk', '3', '4+', 6, 0, 1),
     ],
     [
         ability('Repair Barge',
                 'Once per turn, just after an enemy unit finishes making its '
                 'attacks, if one or more friendly NECRON WARRIORS units within '
                 '3" of this model lost one or more wounds as a result of those '
                 'attacks, this model can use this ability. If it does, select '
                 'one of those NECRON WARRIORS units; that unit\u2019s '
                 'Reanimation Protocols activate. The same NECRON WARRIORS unit '
                 'cannot be selected for this ability more than once per turn.'),
     ]),

    # Necron Monolith
    ('Necron Monolith', 400,
     stat('8"', 13, '2+', 22, '7+', 8),
     [
         rng('Particle whip', '24"', '3D6', '3+', 8, -1, 2,
             'Blast, Devastating Wounds'),
         rng('Gauss flux arc (x4)', '24"', '3', '3+', 6, -1, 1,
             'Lethal Hits, Rapid Fire 3'),
         mel('Portal of exile', '6', '2+', 8, -2, 3),
     ],
     [
         ability('Damaged: 1-7 wounds remaining',
                 'While this model has 1-7 wounds remaining, subtract 4 from '
                 'its Objective Control characteristic and each time this model '
                 'makes an attack, subtract 1 from the Hit roll.'),
         ability('Eternity Gate',
                 'In the Reinforcements step of your Movement phase, you can '
                 'select one NECRONS INFANTRY unit from your army that is '
                 'either in Reserves or on the battlefield (if you select the '
                 'latter, remove that unit from the battlefield and place it '
                 'into Reserves). That unit is then set up anywhere on the '
                 'battlefield that is wholly within 6" of this model and not '
                 'within Engagement Range of any enemy models. That unit cannot '
                 'declare a charge this turn.'),
     ]),

    ('Night Scythe', 145,
     stat('20+"', 9, '3+', 12, '7+', 0),
     [
         rng('Twin tesla destructor', '36"', '6', '3+', 8, 0, 2,
             'Sustained Hits 2, Twin-linked'),
         mel('Armoured bulk', '3', '4+', 6, 0, 1),
     ],
     [
         ability('Invasion Beams',
                 'At the end of the Fight phase, if there are no models '
                 'currently embarked within this TRANSPORT, you can select one '
                 'friendly NECRONS INFANTRY unit wholly within 6" of this '
                 'TRANSPORT. Unless that unit is within Engagement Range of one '
                 'or more enemy units, it can embark within this TRANSPORT.'),
         ability('Damaged: 1-4 wounds remaining',
                 'While this model has 1-4 wounds remaining, each time this '
                 'model makes an attack, subtract 1 from the Hit roll.'),
         ability('Quantum Invader',
                 'This model can be set up in the Reinforcements step of your '
                 'first, second or third Movement phase, regardless of any '
                 'mission rules.'),
     ]),

    ('Tesseract Vault', 425,
     stat('8"', 12, '2+', 24, '7+', 8, invuln='4+'),
     [
         rng('Tesla sphere (x4)', '24"', '6', '3+', 7, 0, 1, 'Sustained Hits 2'),
         mel('Armoured bulk', '6', '4+', 8, 0, 1),
     ],
     [
         ability('Damaged: 1-8 wounds remaining',
                 'While this model has 1-8 wounds remaining, subtract 4 from '
                 'its Objective Control characteristic and you can only select '
                 'one of the C\u2019tan Powers weapons in your Shooting phase, '
                 'instead of two.'),
         ability('Powers of the C\u2019tan',
                 'In your Shooting phase, when this model is selected to shoot, '
                 'first select up to 2 different C\u2019tan Powers weapons. '
                 'Until the end of the phase, this model is equipped with those '
                 'weapons in addition to its other weapons (this model cannot '
                 'make attacks with any other C\u2019tan Powers weapon you did '
                 'not select in this way this phase).'),
     ]),

    ('Triarch Stalker', 110,
     stat('8"', 8, '3+', 12, '7+', 4, invuln='4+'),
     [
         rng('Heat ray - dispersed', '12"', '2D6', 'N/A', 5, -1, 1,
             'Ignores Cover, Torrent'),
         rng('Heat ray - focused', '18"', '2', '3+', 9, -4, 'D6', 'Melta 4'),
         mel("Stalker's forelimbs", '4', '3+', 7, -1, 3),
     ],
     [
         ability('Targeting Relay',
                 'In your Shooting phase, after this model has shot, select '
                 'one enemy unit hit by one or more of those attacks. Until the '
                 'end of the phase, that unit cannot have the Benefit of Cover.'),
     ]),

    # -- Fortifications -------------------------------------------------------

    ('Convergence of Dominion', 60,
     stat('-', 9, '3+', 7, '8+', 0),
     [
         rng('Transdimensional abductor', '18"', '3', '4+', 6, -2, 3),
     ],
     [
         ability('Reanimation Nodes (Aura)',
                 'While a friendly NECRONS INFANTRY unit is within 6\u201d of '
                 'this FORTIFICATION, models in that unit have the Feel No Pain '
                 '6+ ability.'),
         ability('Ancient Cover',
                 'Each time a ranged attack is allocated to a model, if that '
                 'model is not fully visible to every model in the attacking '
                 'unit because of this FORTIFICATION, that model has the Benefit '
                 'of Cover against that attack.'),
         ability('Deployment',
                 'When this unit is first set up on the battlefield, its models '
                 'do not have to be set up in Unit Coherency. Instead, each '
                 'model must be set up wholly within 12" of one other model '
                 'from its unit. From that point on, each model in this unit is '
                 'treated as a separate unit.'),
         ability('Fortification',
                 'While an enemy unit is only within Engagement Range of one or '
                 'more Fortifications from your army:\n\nThat unit can still be '
                 'selected as the target of ranged attacks, but each time such '
                 'an attack is made, unless it is made with a Pistol, subtract '
                 '1 from the Hit roll.\nModels in that unit do not need to take '
                 'Desperate Escape tests due to Falling Back while '
                 'Battle-shocked, except for those that will move over enemy '
                 'models when doing so.'),
     ]),

    # Skorpekh Lord card → db_name "Necrons Royal Court" (skipped — Canoptek
    # Reanimator used above as first entry for that db_name)

]


class Command(BaseCommand):
    """Seed Necrons stat lines, weapon profiles, and abilities."""

    help = 'Seed Necrons unit stats, weapons, and abilities.'

    def add_arguments(self, parser):
        """Add --dry-run flag."""
        parser.add_argument(
            '--dry-run', action='store_true',
            help='Preview changes without writing to the database.',
        )

    def handle(self, *args, **options):
        """Iterate over NECRONS_UNITS and upsert stats, weapons, and abilities."""
        dry_run = options['dry_run']
        updated = 0
        skipped = 0

        with transaction.atomic():
            for db_name, pts, stats, weapons, abilities in NECRONS_UNITS:
                try:
                    unit = UnitType.objects.get(name=db_name)
                except UnitType.DoesNotExist:
                    self.stdout.write(self.style.WARNING(
                        f'  SKIP (not found): {db_name}'
                    ))
                    skipped += 1
                    continue

                if dry_run:
                    self.stdout.write(
                        f'  DRY-RUN -> {db_name!r} '
                        f'{pts}pts | {len(weapons)}w {len(abilities)}a'
                    )
                    continue

                # Update points and stat fields
                for field, val in {'points_cost': pts, **stats}.items():
                    setattr(unit, field, val)
                unit.save()

                # Replace weapon profiles
                WeaponProfile.objects.filter(unit_type=unit).delete()
                for order, wp in enumerate(weapons):
                    WeaponProfile.objects.create(unit_type=unit, order=order, **wp)

                # Replace abilities
                UnitAbility.objects.filter(unit_type=unit).delete()
                for order, ab in enumerate(abilities):
                    UnitAbility.objects.create(unit_type=unit, order=order, **ab)

                self.stdout.write(
                    f'  OK: {db_name!r} -- {pts}pts, '
                    f'{len(weapons)} weapons, {len(abilities)} abilities'
                )
                updated += 1

            if dry_run:
                self.stdout.write(self.style.WARNING('Dry run -- no changes written.'))
                transaction.set_rollback(True)

        self.stdout.write(self.style.SUCCESS(
            f'\nDone. {updated} updated, {skipped} skipped.'
        ))
