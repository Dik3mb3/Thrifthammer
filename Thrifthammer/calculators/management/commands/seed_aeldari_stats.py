"""
Management command: seed_aeldari_stats

Seeds points costs, stat lines, weapon profiles, and unit abilities
for all Aeldari units in the database. Safe to re-run — uses
delete+create for weapons/abilities and direct field writes for stats.

Usage:
    python manage.py seed_aeldari_stats
    python manage.py seed_aeldari_stats --dry-run
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from calculators.models import UnitAbility, UnitType, WeaponProfile

# Faction filter — prevents MultipleObjectsReturned once units with the same
# name (e.g. Daemon Prince) exist across several factions.
FACTION_NAME = 'Aeldari'


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
# Skipped duplicates per mapping rules:
#   Corsair Voidscarred       → same db_name as Corsair Voidreavers (skip)
#   Shadow Weaver Platform,
#   Vibro Cannon Platform     → same db_name as D-Cannon Platform / Support Weapon (skip)
#   Wave Serpent              → same db_name as Falcon / Aeldari Wave Serpent (skip)
#   Warlock Conclave          → same db_name as Warlock / Warlocks (skip)
#   Wraithknight w/ Ghostglaive → same db_name as Wraithknight (skip)
#   Phantom Titan,
#   Revenant Titan,
#   Troupe Master,
#   Striking Scorpions,
#   Other Ynnari army units   → no db_name in CSV (skip)
# Yvraine, The Visarch, The Yncarne → seeded in the Ynnari section below

AELDARI_UNITS = [

    # -- Epic Heroes ----------------------------------------------------------

    ('Asurmen', 135,
     stat('7"', 3, '2+', 5, '6+', 1, invuln='4+'),
     [
         rng('The Bloody Twins', '24"', 6, '2+', 5, -1, 2,
             'Assault, Pistol'),
         mel('The Sword of Asur', 6, '2+', 6, -3, 3,
             'Devastating Wounds'),
     ],
     [
         ability('Hand of Asuryan',
                 'Once per battle, when this model is selected to shoot, it can '
                 'use this ability. If it does, until the end of the phase, its '
                 'Bloody Twins weapon has a Damage characteristic of 3 and the '
                 '[Anti-Infantry 5+] and [Devastating Wounds] abilities.'),
         ability('Tactical Acumen',
                 'While this model is leading a unit, in your Shooting phase, '
                 'after that unit has shot, it can make a Normal move of up to '
                 '6". If it does, until the end of the turn, that unit is not '
                 'eligible to declare a charge.'),
         ability('Leader',
                 'This model can be attached to the following unit:\n'
                 '\u25a0 Dire Avengers'),
     ]),

    ('Baharroth', 115,
     stat('14"', 3, '2+', 5, '6+', 1, invuln='4+'),
     [
         rng('Fury of the Tempest', '24"', 4, '2+', 6, -1, 2,
             'Assault, Lethal Hits'),
         mel('The Shining Blade', 6, '2+', 5, -2, 2, 'Sustained Hits 1'),
     ],
     [
         ability('Leader',
                 'This model can be attached to the following unit:\n'
                 '\u25a0 Swooping Hawks'),
         ability('Cry of the Wind',
                 'Each time this model is set-up on the battlefield, until the '
                 'end of the turn, each time this model makes a ranged attack, a '
                 'successful unmodified Hit roll scores a Critical Hit.'),
         ability('Cloudstrider',
                 'While this model is leading a unit, at the end of your '
                 "opponent's turn, if that unit is not within Engagement Range of "
                 'one or more enemy units, you can remove it from the battlefield '
                 'and place it into Strategic Reserves. In addition, while this '
                 'model is leading a unit, when that unit is set-up on the '
                 'battlefield using the Deep Strike ability, in your Movement '
                 'phase, it can use this ability. if it does, that unit can be '
                 'set-up anywhere on the battlefield that is more than 6" '
                 'horizontally away from all enemy models, but until the end of '
                 'the turn, it is not eligible to declare a charge.'),
     ]),

    ('Eldrad Ulthran', 120,
     stat('7"', 4, '6+', 5, '6+', 1, invuln='4+'),
     [
         rng('Mind War', '18"', 1, '2+', 5, -2, 'D6',
             'Anti-character 4+, Precision, Psychic'),
         rng('Shuriken Pistol', '12"', 1, '2+', 4, -1, 1,
             'Assault, Pistol'),
         mel('Staff of Ulthamar and witchblade', 3, '2+', 5, -1, 2,
             'Anti-Infantry 2+, Psychic'),
     ],
     [
         ability('Diviner of the Futures',
                 'At the start of your Command phase, if this model is on the '
                 'battlefield, you gain 1CP.'),
         ability('Doom (Psychic)',
                 'At the end of your Movement phase, select one enemy unit within '
                 '18" of and visible to this model. Until the start of your next '
                 'Command phase, each time a friendly Aeldari model makes an '
                 'attack that targets that enemy unit, add 1 to the Wound roll'),
         ability('Leader',
                 'This model can be attached to the following units:\n'
                 '\u25a0 Guardian Defenders\n'
                 '\u25a0 Storm Guardians\n'
                 '\u25a0 Warlock Conclave'),
     ]),

    ('Fuegan', 120,
     stat('7"', 3, '2+', 5, '6+', 1, invuln='4+'),
     [
         rng('Searsong - Beam', '12"', 3, '2+', 8, -3, 2,
             'Assault, Melta 1, Sustained hits 2'),
         rng('Searsong - Lance', '18"', 1, '2+', 14, -4, 'D6',
             'Assault, Melta 6'),
         mel('The Fire Axe', 6, '2+', 5, -4, 3),
     ],
     [
         ability('Burning Lance',
                 'While this model is leading a unit, add 6" to the Range '
                 'characteristic of Melta weapons equipped by models in that '
                 'unit.'),
         ability('Unquenchable Resolve',
                 'The first time this model is destroyed, at the end of the '
                 'phase, roll one D6. On a 2+, set this model back up on the '
                 'battlefield as close as possible to where it was destroyed and '
                 'not within Engagement Range of one or more enemy units, with '
                 'its full wounds remaining.'),
         ability('Leader',
                 'This model can be attached to the following unit:\n'
                 '\u25a0 Fire Dragons'),
     ]),

    ('Jain Zar', 120,
     stat('8"', 3, '2+', 5, '6+', 1, invuln='4+'),
     [
         rng('Silent Death', '12"', 6, '2+', 6, -2, 1, 'Assault'),
         mel('Blade of Destruction', 8, '2+', 6, -3, 2,
             'Anti-Infantry 3+'),
     ],
     [
         ability('Leader',
                 'This model can be attached to the following unit:\n'
                 '\u25a0 Howling Banshees'),
         ability('Whirling Death',
                 'While this model is leading a unit, each time that unit '
                 'Advances, do not make an Advance roll. Instead, until the end '
                 'of the phase, add 6" to the Move characteristic of models in '
                 'that unit and each time a model in that unit makes an Advance '
                 'move, ignore any vertical distance when determining the total '
                 'distance that model can be moved during that move.'),
         ability('Storm of Silence',
                 'Each time this model makes an attack that targets a Character '
                 'unit, you can re-roll the Wound roll.'),
     ]),

    ('Kharseth', 95,
     stat('7"', 3, '6+', 4, '6+', 1, invuln='4+'),
     [
         rng('Dread of the Deep Void', '24"', 'D6+2', '3+', 3, -2, 1,
             'Anti-Infantry 2+, Blast, Hazardous, Ignores Cover, Psychic'),
         mel('Waystave', 3, '2+', 3, 0, 3,
             'Anti-Infantry 2+, Psychic'),
     ],
     [
         ability('Leader',
                 'This model can be attached to the following units:\n'
                 '\u25a0 Corsair Voidreavers\n'
                 '\u25a0 Corsair Voidscarred'),
         ability('Aethersense (Psychic)',
                 'Enemy units that are set up on the battlefield from Reserves '
                 'cannot be set up within 12" of this model.'),
         ability('Fury of the Void (Psychic)',
                 "In your Shooting phase, after this model's unit has shot, "
                 'select one enemy unit hit by one or more attacks made with this '
                 "model's Dread of the Deep Void. Until the end of the turn, "
                 'that unit is riven. Each time an Aeldari model from your army '
                 'makes an attack that targets a riven unit, add 1 to the '
                 'Strength characteristic of that attack.'),
     ]),

    ('Lhykhis', 135,
     stat('12"', 3, '2+', 5, '6+', 1, invuln='4+'),
     [
         rng('Brood Twain', '12"', 'D6+3', 'N/A', 6, -2, 1,
             'Ignores Cover, Torrent, Twin-Linked'),
         mel("Spider's Fangs", 5, '2+', 4, -2, 1,
             'Extra Attacks, Lethal Hits'),
         mel('Weaverender', 5, '2+', 6, -2, 2, 'Lethal Hits'),
     ],
     [
         ability('Leader',
                 'This model can be attached to the following unit:\n'
                 '\u25a0 Warp Spiders'),
         ability('Empyric Ambush',
                 'While this model is leading a unit, that unit is eligible to '
                 'declare a charge in a turn in which it used its Flickerjump '
                 'ability.'),
         ability('Whispering Web',
                 'In your Shooting phase, after this model has shot, select one '
                 'enemy unit hit by one or more of those attacks. Until the end '
                 'of the turn, each time a friendly Aeldari model makes an '
                 'attack that targets that unit, an unmodified Hit roll of 5+ '
                 'scores a Critical Hit.'),
     ]),

    ('Maugan Ra', 100,
     stat('7"', 3, '2+', 5, '6+', 1, invuln='4+'),
     [
         rng('Maugetar', '36"', 6, '2+', 7, -2, 2,
             'Devastating wounds, Ignores cover'),
         mel('Maugetar', 5, '2+', 6, -2, 2),
     ],
     [
         ability('Leader',
                 'This model can be attached to the following unit:\n'
                 '\u25a0 Dark Reapers'),
         ability('Harvester of Souls',
                 'While this model is leading a unit, in your Shooting phase, '
                 "after selecting targets for that unit's attacks, if every "
                 'attack targets the same unit, roll one D6 for the target unit '
                 'and one D6 for every other enemy unit within 3" of the target '
                 'unit. On a 5+, the unit being rolled for is struck by explosive '
                 'debris; after resolving all of that unit\'s attacks against the '
                 'target unit, each unit struck by explosive debris suffers D3 '
                 'mortal wounds.'),
         ability('Face of Death',
                 'In your Shooting phase, after this model has shot, select one '
                 'enemy unit hit by one or more of those attacks. That enemy unit '
                 'must take a Battle-shock test, subtracting 1 from the result.'),
     ]),

    ('Prince Yriel', 95,
     stat('7"', 3, '3+', 5, '6+', 1, invuln='4+'),
     [
         rng('Shuriken Pistol', '12"', 1, '2+', 4, -1, 1,
             'Assault, Pistol'),
         rng('The Eye of Wrath', '6"', 3, '2+', 6, -2, 2,
             'Assault, Pistol'),
         mel('The Spear of Twilight', 5, '2+', 7, -3, 3, 'Lance'),
     ],
     [
         ability('Leader',
                 'This model can be attached to the following units:\n'
                 '\u25a0 Corsair Voidreavers\n'
                 '\u25a0 Corsair Voidscarred'),
         ability('Piratical Hero',
                 'While this model is leading a unit, each time a model in that '
                 'unit makes an attack, that attack has the [Sustained Hits 1] '
                 'ability and add 1 to the Hit roll.'),
         ability('Prince of Corsairs',
                 'After both players have deployed their armies, if this model is '
                 'on the battlefield (or any Transport it is embarked within is '
                 'on the battlefield), select up to three Aeldari units from your '
                 'army and redeploy them. When doing so, you can set those units '
                 'up in Strategic Reserves, regardless of how many units are '
                 'already in Strategic Reserves.'),
     ]),

    ('Solitaire', 115,
     stat('12"', 3, '6+', 4, '6+', 1, invuln='4+'),
     [
         mel('Solitaire Weapons', 9, '2+', 6, -2, 2, 'Precision'),
     ],
     [
         ability('Blitz',
                 'Once per battle, in your Movement phase, before this model '
                 "makes a Normal move it can use this ability. If it does, until "
                 "the end of the turn, add 2D6\" to this model's Move "
                 "characteristic and add 3 to the Attacks characteristic of this "
                 "model's Solitaire weapons."),
         ability('Blur of Movement',
                 'This model is eligible to declare a charge in a turn in which '
                 'it Advanced.'),
         ability('Flip Belt',
                 "Each time the bearer's unit makes a Normal, Advance, Fall Back "
                 'or Charge move, ignore any vertical distance when determining '
                 'the total distance the bearer can be moved during that move.'),
     ]),

    # -- Characters -----------------------------------------------------------

    ('Autarch', 85,
     stat('7"', 3, '3+', 4, '6+', 1, invuln='4+'),
     [
         rng('Shuriken Pistol', '12"', 1, '2+', 4, -1, 1,
             'Assault, Pistol'),
         mel('Star Glaive', 4, '2+', 6, -3, 3),
     ],
     [
         ability('Superlative Strategist',
                 'While this model is leading a unit, you can re-roll Advance '
                 'rolls made for that unit, and you can re-roll any rolls made '
                 'for that unit while it is performing an Agile Manoeuvre.'),
         ability('Path of Command',
                 'Once per battle round, one model from your army with this '
                 'ability can use it when its unit is targeted with a Stratagem. '
                 'If it does, reduce the CP cost of that usage of that stratagem '
                 'by 1CP.'),
         ability('Leader',
                 'This model can be attached to the following units:\n'
                 '\u25a0 Dark Reapers\n'
                 '\u25a0 Dire Avengers\n'
                 '\u25a0 Fire Dragons\n'
                 '\u25a0 Guardian Defenders\n'
                 '\u25a0 Howling Banshees\n'
                 '\u25a0 Storm Guardians\n'
                 '\u25a0 Striking Scorpions'),
         ability('Aspect Training',
                 'While this model is leading a Howling Banshees unit, it has '
                 'the Fights First ability.\n'
                 'While this model is leading a Striking Scorpions unit, it has '
                 'the Infiltrators, Scouts 7" and Stealth abilities.'),
     ]),

    ('Autarch Wayleaper', 80,
     stat('14"', 3, '3+', 4, '6+', 1, invuln='4+'),
     [
         rng('Shuriken Pistol', '12"', 1, '2+', 4, -1, 1,
             'Assault, Pistol'),
         mel('Star Glaive', 4, '2+', 6, -3, 3),
     ],
     [
         ability('Path of Command',
                 'Once per battle round, one model from your army with this '
                 'ability can use it when its unit is targeted with a Stratagem. '
                 'If it does, reduce the CP cost of that usage of that stratagem '
                 'by 1CP.'),
         ability('Indomitable Strength of Will',
                 'While this model is leading a unit, each time you spend a '
                 'Battle Focus token to enable that unit to perform an Agile '
                 'Manoeuvre, roll one D6: on a 3+ you gain 1 Battle Focus '
                 'token.'),
         ability('Leader',
                 'This model can be attached to the following units:\n'
                 '\u25a0 Swooping Hawks\n'
                 '\u25a0 Warp Spiders'),
     ]),

    ('Death Jester', 90,
     stat('8"', 3, '6+', 4, '6+', 1, invuln='4+'),
     [
         rng('Shrieker Cannon', '24"', 3, '2+', 6, -2, 2),
         mel("Jester's Blade", 4, '2+', 4, 0, 1),
     ],
     [
         ability('Death is Not Enough',
                 'In your Shooting phase, after this model has shot, select one '
                 'enemy unit (excluding Monsters and Vehicles) hit by one or '
                 'more of those attacks. That enemy unit must take a Battle-shock '
                 'test. If one or more of those attacks destroyed a model in that '
                 'enemy unit, subtract 1 from that test.'),
         ability('Cruel Amusement',
                 'In your Shooting phase, each time this model is selected to '
                 "shoot, select one of the abilities below. Until the end of the "
                 "phase, this model's Shrieker Cannon has that ability:\n"
                 '\u25a0 [IGNORES COVER]\n'
                 '\u25a0 [PRECISION]\n'
                 '\u25a0 [SUSTAINED HITS 3]'),
         ability('Flip Belt',
                 "Each time the bearer's unit makes a Normal, Advance, Fall Back "
                 'or Charge move, ignore any vertical distance when determining '
                 'the total distance the bearer can be moved during that move.'),
         ability('Travelling Players',
                 'Unless otherwise stated, you cannot include more than one of '
                 'this model in your army.'),
     ]),

    ('Aeldari Farseer', 70,
     stat('7"', 3, '6+', 4, '6+', 1, invuln='4+'),
     [
         rng('Eldritch Storm', '24"', 'D6', '3+', 6, -2, 'D3',
             'Blast, Psychic'),
         rng('Shuriken Pistol', '12"', 1, '3+', 4, -1, 1,
             'Assault, Pistol'),
         mel('Witchblade', 2, '2+', 3, 0, 2,
             'Anti-Infantry 2+, Psychic'),
     ],
     [
         ability('Branching Fates (Psychic)',
                 'While this model is leading a unit, once per phase you can '
                 'change the result of one Hit roll, one Wound roll, or one '
                 'Damage roll made for a model in that unit (excluding Support '
                 'Weapon models) to an unmodified 6.'),
         ability('Guide (Psychic)',
                 'At the end of your Movement phase, select one enemy unit within '
                 '18" of and visible to this model. Until the start of your next '
                 'Command phase, each time a friendly Aeldari model makes an '
                 'attack that targets that enemy unit, add 1 to the Hit roll. '
                 'Each unit can only be selected for this ability once per turn.'),
         ability('Leader',
                 'This model can be attached to the following units:\n'
                 '\u25a0 Guardian Defenders\n'
                 '\u25a0 Storm Guardians\n'
                 '\u25a0 Warlock Conclave'),
     ]),

    ('Farseer Skyrunner', 80,
     stat('14"', 4, '6+', 5, '6+', 2, invuln='4+'),
     [
         rng('Eldritch Storm', '24"', 'D6', '3+', 6, -2, 'D3',
             'Blast, Psychic'),
         rng('Shuriken Pistol', '12"', 1, '3+', 4, -1, 1,
             'Assault, Pistol'),
         rng('Twin Shuriken Catapult', '18"', 2, '3+', 4, -1, 1,
             'Assault, Twin Linked'),
         mel('Witchblade', 2, '2+', 3, 0, 2,
             'Anti-Infantry 2+, Psychic'),
     ],
     [
         ability('Branching Fates (Psychic)',
                 'While this model is leading a unit, once per phase you can '
                 'change the result of one Hit roll, one Wound roll, or one '
                 'Damage roll made for a model in that unit to an unmodified 6.'),
         ability('Misfortune (Psychic)',
                 'At the end of your Movement phase, select one enemy unit within '
                 '18" of and visible to this model. Until the start of your next '
                 'Command phase, each time a model in that unit makes an attack, '
                 'subtract 1 from the Wound roll. Each unit can only be selected '
                 'for this ability once per turn.'),
         ability('Leader',
                 'This model can be attached to the following units:\n'
                 '\u25a0 Warlock Skyrunners\n'
                 '\u25a0 Windriders'),
     ]),

    ('Shadowseer', 60,
     stat('8"', 3, '6+', 4, '6+', 1, invuln='4+'),
     [
         rng('Shuriken Pistol', '12"', 1, '2+', 4, -1, 1,
             'Assault, Pistol'),
         mel('Miststave', 4, '2+', 5, -1, 'D3', 'Psychic'),
     ],
     [
         ability('Leader',
                 'This model can be attached to the following unit:\n'
                 '\u25a0 Troupe'),
         ability('Fog of Dreams (Psychic)',
                 'While this model is leading a unit, that unit can only be '
                 'selected as the target of a ranged attack if the attacking '
                 'model is within 18".'),
         ability('Treacherous Illusion (Psychic)',
                 'Melee weapons equipped by enemy models have the [Hazardous] '
                 "ability while targeting this model's unit."),
         ability('Travelling Players',
                 'Unless otherwise stated, you cannot include more than one of '
                 'this model in your army.'),
         ability('Flip Belt',
                 "Each time the bearer's unit makes a Normal, Advance, Fall Back "
                 'or Charge move, ignore any vertical distance when determining '
                 'the total distance the bearer can be moved during that move.'),
     ]),

    ('Spiritseer', 65,
     stat('7"', 3, '6+', 3, '6+', 1, invuln='4+'),
     [
         rng('Shuriken Pistol', '12"', 1, '2+', 4, -1, 1,
             'Assault, Pistol'),
         mel('Witch Staff', 2, '2+', 3, 0, 'D3',
             'Anti-infantry 2+, Psychic'),
     ],
     [
         ability('Spirit Mark (Psychic)',
                 'Once per turn, in your Movement phase, when this model starts '
                 'or ends a move, select one friendly Wraith Construct unit '
                 'within 6" of this model (excluding Titanic units) and one '
                 'enemy unit visible to this model. Until the start of your next '
                 'Movement phase, weapons equipped by models in that friendly '
                 'unit have the [Sustained Hits 1] ability while targeting that '
                 'enemy unit.'),
         ability('Tears of Isha (Psychic)',
                 'In your Command phase, select one friendly Wraith Construct '
                 'unit within 6" of this model. If one or more models in that '
                 'unit are destroyed, you can return one destroyed model to that '
                 'unit. Otherwise, one model in that unit regains up to D3 lost '
                 'wounds. Each unit can only be selected for this ability once '
                 'per turn.'),
         ability('Spiritseer',
                 'While this model is within 3" of one or more friendly Wraith '
                 'Construct units, this model has the Lone Operative ability.'),
     ]),

    ('Warlocks', 45,
     stat('7"', 3, '6+', 2, '6+', 1, invuln='4+'),
     [
         rng('Destructor', '12"', 'D6', 'N/A', 5, -1, 1,
             'Psychic, Torrent'),
         rng('Shuriken Pistol', '12"', 1, '3+', 4, -1, 1,
             'Assault, Pistol'),
         mel('Witchblade', 2, '3+', 3, 0, 2,
             'Anti-Infantry 2+, Psychic'),
     ],
     [
         ability('Leader',
                 'This model can be attached to the following units:\n'
                 '\u25a0 Guardian Defenders\n'
                 '\u25a0 Storm Guardians\n'
                 'You can attach this model to a unit, even  if one Autarch or '
                 'Farseer model has already been attached to it. If you do, and '
                 'that Bodyguard unit is destroyed, the Leader units attached to '
                 'it become separate units, with their original Starting '
                 'Strengths.'),
         ability('Runes of Fortune (Psychic)',
                 'Each time an enemy unit declares a charge, if one or more '
                 'units with this ability are selected as a target of that '
                 'charge, subtract 2 from the Charge roll.'),
         ability('Psychic Communion (Psychic)',
                 'Each time this model is selected to shoot, until the end of '
                 'the phase, add 1 to the Attacks and Strength characteristics '
                 'of its Destructor weapon for each other friendly Aeldari '
                 'Psyker  model within 6" of this model (to a maximum of +2).'),
     ]),

    # -- Infantry -------------------------------------------------------------

    ('Corsair Voidreavers', 65,
     stat('7"', 3, '4+', 1, '7+', 2),
     [
         rng('Shuriken pistol', '12"', 1, '3+', 4, -1, 1,
             'Assault, Pistol'),
         rng('Shuriken rifle (x4)', '24"', 1, '3+', 4, -1, 1,
             'Assault, Rapid Fire 1'),
         mel('Close Combat Weapon (x5)', 2, '3+', 3, 0, 1),
         mel('Power sword', 2, '3+', 4, -2, 1),
     ],
     [
         ability('Reavers of the Void',
                 'Each time a model in this unit makes an attack, re-roll a Hit '
                 'roll of 1. If the target of that attack is an enemy unit within '
                 'range of an objective marker, you can re-roll the Hit roll '
                 'instead.'),
     ]),

    ('Guardian Defenders', 100,
     stat('7"', 3, '4+', 1, '7+', 2),
     [
         rng('Shuriken Catapult (x10)', '18"', 2, '3+', 4, -1, 1,
             'Assault'),
         rng('Shuriken Cannon', '24"', 3, '3+', 6, -1, 2,
             'Lethal Hits'),
         mel('Close Combat Weapon (x11)', 1, '3+', 3, 0, 1),
     ],
     [
         ability('Fleet of Foot',
                 'This unit can perform the Fade Back Agile Manoeuvre without '
                 'spending a Battle Focus token to do so. It can do so even if '
                 'other units have done so in the same phase, and doing so does '
                 'not prevent other units from performing the same Agile '
                 'Manoeuvre in the same phase.'),
         ability('Crewed Platform',
                 'When the last Guardian Defender model in this unit is '
                 'destroyed, any remaining Heavy Weapon Platform models in this '
                 'unit are also destroyed.'),
     ]),

    # Storm Guardians → db_name "Aeldari Guardians"
    ('Aeldari Guardians', 110,
     stat('7"', 3, '4+', 1, '7+', 2),
     [
         rng('Shuriken Pistol (x10)', '12"', 1, '3+', 4, -1, 1,
             'Assault, Pistol'),
         mel('Close Combat Weapon (x11)', 2, '3+', 3, 0, 1),
     ],
     [
         ability('Stormblades',
                 'At the end of your Command phase, if this unit is within range '
                 "of an objective marker you control, that objective marker "
                 "remains under your control until your opponent's Level of "
                 'Control over that objective marker is greater than yours at the '
                 'end of a phase.'),
         ability('Crewed Platform',
                 'When the last Storm Guardian model in this unit is destroyed, '
                 "any remaining Serpent's Scale Platform models in this unit are "
                 'also destroyed.'),
         ability('Serpent Shield',
                 "Models in the bearer's unit have a 5+ invulnerable save."),
     ]),

    ('Corsair Skyreavers', 75,
     stat('12"', 3, '5+', 1, '7+', 1),
     [
         rng('Shuriken pistol', '12"', 1, '3+', 4, -1, 1,
             'Assault, Pistol'),
         rng('Shuriken Pistol (x4)', '12"', 1, '3+', 4, -1, 1,
             'Assault, Pistol'),
         mel('Corsair Blade (x5)', 3, '3+', 4, -2, 1),
     ],
     [
         ability('Raid and Run',
                 'At the end of the Fight phase, if this unit was eligible to '
                 'fight this phase, and is not within Engagement Range of one or '
                 'more enemy units, it can make a Normal move of up to D3+3". '
                 'Otherwise, if this unit was eligible to fight this phase, this '
                 'unit can make a Fall Back move of up to D3+3".'),
     ]),

    # D-Cannon Platform → db_name "Support Weapon" (first occurrence in mapping)
    ('Support Weapon', 125,
     stat('7"', 6, '4+', 5, '7+', 1),
     [
         rng('D-cannon', '24"', 'D3', '3+', 16, -4, 'D6+2',
             'Blast, Devastating Wounds, Indirect Fire'),
         rng('Shuriken Catapult', '18"', 2, '3+', 4, -1, 1, 'Assault'),
         mel('Close Combat Weapon', 2, '3+', 3, 0, 1),
     ],
     [
         ability('Structural Collapse',
                 'Each time this model makes an attack with its D-Cannon, '
                 're-roll a Damage roll of 1. If that attack targets a Titanic '
                 'unit, you can re-roll the Damage roll instead.'),
         ability('Support Artillery',
                 'At the start of the Declare Battle Formations step, this model '
                 'can join one Guardian Defenders unit from your army (a unit '
                 'cannot have more than one Support Weapon model joined to it). '
                 'This model then counts as part of that Guardians unit for the '
                 "rest of the battle, and that unit's Starting Strength is "
                 'increased accordingly.\n'
                 'This model, and any unit it is joined to, cannot embark within '
                 'a Transport.'),
         ability('Support Weapon',
                 "Each time an attack targets this model's unit, it that unit "
                 'contains one or more other models, until that attack is '
                 'resolved, this model has a Toughness characteristic of 3.'),
     ]),

    ('Dark Reapers', 90,
     stat('6"', 3, '3+', 2, '6+', 1, invuln='5+'),
     [
         rng('Reaper Launcher - Starshot (x5)', '48"', 1, '3+', 10, -2, 3,
             'Ignores Cover'),
         rng('Reaper Launcher - Starswarm (x5)', '48"', 2, '3+', 5, -2, 1,
             'Ignores Cover'),
         mel('Close combat weapon (x5)', 2, '3+', 3, 0, 1),
     ],
     [
         ability('Inescapable Accuracy',
                 'Each time a model in this unit makes a ranged attack, you can '
                 "ignore any or all modifiers to that attack's Ballistic Skill "
                 'characteristic and any or all modifiers to the Hit roll.'),
     ]),

    ('Aeldari Dire Avengers', 75,
     stat('7"', 3, '4+', 2, '6+', 1, invuln='5+'),
     [
         rng('Avenger Shuriken Catapult (x5)', '18"', 4, '3+', 4, -1, 1,
             'Assault'),
         mel('Close Combat Weapon (x5)', 2, '3+', 3, 0, 1),
     ],
     [
         ability('Bladestorm',
                 'Ranged weapons equipped by models in this unit have the '
                 '[Sustained Hits 1] ability while targeting an enemy unit '
                 'within half range.'),
     ]),

    ('Aeldari Fire Dragons', 120,
     stat('7"', 3, '3+', 2, '6+', 1, invuln='5+'),
     [
         rng("Exarch's Dragon Fusion Gun", '12"', 1, '3+', 9, -4, 'D6',
             'Assault, Melta 6'),
         rng('Dragon Fusion Gun (x4)', '12"', 1, '3+', 9, -4, 'D6',
             'Assault, Melta 3'),
         mel('Close combat weapon (x5)', 2, '3+', 3, 0, 1),
     ],
     [
         ability('Assured Destruction',
                 'In your Shooting phase, each time a model in this unit makes '
                 'a ranged attack that targets a Monster or Vehicle unit, you '
                 'can re-roll the Hit roll, you can re-roll the Wound roll and '
                 'you can re-roll the Damage roll.'),
     ]),

    ('Howling Banshees', 95,
     stat('8"', 3, '4+', 2, '6+', 1, invuln='5+'),
     [
         rng('Shuriken Pistol (x5)', '12"', 1, '3+', 4, -1, 1,
             'Assault, Pistol'),
         mel('Banshee Blade (x5)', 2, '2+', 4, -2, 2,
             'Anti-Infantry 3+'),
     ],
     [
         ability('Acrobatic',
                 'This unit is eligible to declare a charge in a turn in which '
                 'it Advanced or Fell Back'),
     ]),

    ('Rangers', 55,
     stat('7"', 3, '5+', 1, '7+', 1, invuln='5+'),
     [
         rng('Long rifle (x5)', '36"', 1, '3+', 4, -1, 2,
             'Heavy, Precision'),
         rng('Shuriken Pistol (x5)', '12"', 1, '2+', 4, -1, 1,
             'Assault, Pistol'),
         mel('Close Combat Weapon (x5)', 1, '3+', 3, 0, 1),
     ],
     [
         ability('Path of the Outcast',
                 'Once per turn, when an enemy unit ends a Normal, Advance or '
                 'Fall Back move within 9" of this unit, it can make a Normal '
                 'move of up to D6".'),
     ]),

    ('Swooping Hawks', 95,
     stat('14"', 3, '4+', 2, '6+', 1, invuln='5+'),
     [
         rng("Hawk's Talon", '24"', 2, '3+', 6, -2, 2, 'Lethal Hits'),
         rng('Lasblaster (x4)', '24"', 4, '3+', 4, 0, 1,
             'Assault, Lethal Hits'),
         mel('Close Combat Weapon (x5)', 2, '3+', 3, 0, 1),
     ],
     [
         ability('Grenade Pack Flyover',
                 'Once per turn, in your Movement phase, when this unit is '
                 'set-up on the battlefield or ends a Normal, Advance or Fall '
                 'Back move, it can use this ability. If it does, select one '
                 'enemy unit within 8" of and visible to this unit and roll one '
                 'D6 for each Swooping Hawks model in this unit. For each 4+, '
                 'that enemy unit suffers 1 mortal wound (to a maximum of 6 '
                 'mortal wounds). Each time this unit uses this ability , until '
                 'the end of the turn, you cannot target this unit with the '
                 'Grenades Stratagem.'),
     ]),

    ('Warp Spiders', 105,
     stat('12"', 3, '3+', 2, '6+', 1, invuln='5+'),
     [
         rng("Exarch's Deathspinner", '12"', 'D6', 'N/A', 6, -2, 1,
             'Ignores Cover, Torrent'),
         rng('Death spinner (x4)', '12"', 'D6', 'N/A', 4, -1, 1,
             'Ignores Cover, Torrent'),
         mel('Close Combat Weapon (x5)', 2, '3+', 3, 0, 1),
     ],
     [
         ability('Flickerjump',
                 'Once per turn, in your Movement phase, when this unit makes '
                 'a Normal move, you can use this ability. If you do, each '
                 'model in this unit can move up to 24" until the end of the '
                 'turn, and this unit is not eligible to declare a charge this '
                 'turn. At the end of the Movement phase, roll one D6 for each '
                 'model in this unit: on a 1, this unit suffers 1 mortal wound.'),
     ]),

    ('Harlequin Troupe', 85,
     stat('8"', 3, '6+', 1, '6+', 1, invuln='4+'),
     [
         rng('Shuriken Pistol (x5)', '12"', 1, '3+', 4, -1, 1,
             'Assault, Pistol'),
         mel("Harlequin's Blade (x5)", 5, '3+', 3, -1, 1,
             'Devastating Wounds'),
     ],
     [
         ability('Dance of Death',
                 'At the start of the Fight phase, select one of the following '
                 'abilities for this unit to gain until the end of the phase:\n'
                 "\u25a0 Hero's Prowess: Each time a model in this unit makes an "
                 'attack, re-roll a Hit roll of 1.\n'
                 "\u25a0 Villain's Doom: Each time a model in this unit makes an "
                 'attack, add 1 to the Wound roll.\n'
                 "\u25a0 Trickster's Grace: Each time an attack targets this "
                 'unit, subtract 1 from the Hit roll.'),
         ability('Flip Belt',
                 "Each time the bearer's unit makes a Normal, Advance, Fall Back "
                 'or Charge move, ignore any vertical distance when determining '
                 'the total distance the bearer can be moved during that move.'),
     ]),

    # -- Elites ---------------------------------------------------------------

    ('Wraithblades', 150,
     stat('6"', 6, '2+', 3, '8+', 1),
     [
         mel('Ghostswords (x5)', 5, '4+', 5, -2, 2),
     ],
     [
         ability('Malevolent Souls',
                 'Each time a model in this unit is destroyed by a melee attack, '
                 'if that model has not fought this phase, roll one D6. On a 3+, '
                 'do not remove it from play; that destroyed model can fight '
                 "after the attacking model's unit has finished making its "
                 'attacks, and is then removed from play.'),
         ability('Psychic Guidance',
                 'While this unit is within 12" of one or more friendly Aeldari '
                 'Psyker models, models in this unit have a Leadership '
                 'characteristic of 6+ and each time a model in this unit makes '
                 'an attack, add 1 to the Hit roll.'),
     ]),

    ('Wraithguard', 160,
     stat('6"', 6, '2+', 3, '8+', 1),
     [
         rng('Wraithcannon (x5)', '18"', 1, '4+', 14, -4, 'D6+1'),
         mel('Close Combat Weapon (x5)', 3, '4+', 5, 0, 1),
     ],
     [
         ability('War Construct',
                 'This unit is eligible to shoot in a turn in which it Fell '
                 'Back.'),
         ability('Psychic Guidance',
                 'While this unit is within 12" of one or more friendly Aeldari '
                 'Psyker models, models in this unit have a Leadership '
                 'characteristic of 6+ and each time a model in this unit makes '
                 'an attack, add 1 to the Hit roll.'),
     ]),

    # -- Fast Attack ----------------------------------------------------------

    ('Shining Spears', 110,
     stat('14"', 4, '3+', 3, '6+', 2, invuln='5+'),
     [
         rng('Twin Shuriken Catapult (x3)', '18"', 2, '3+', 4, -1, 1,
             'Assault, Twin Linked'),
         rng('Laser Lance (x3)', '6"', 1, '3+', 6, -2, 3, 'Assault'),
         mel('Laser Lance (x3)', 3, '3+', 5, -2, 3,
             'Anti-Monster 3+, Anti-Vehicle 3+, Lance'),
     ],
     [
         ability('Extreme Mobility',
                 'Each time this unit makes a Normal, Advance, Fall Back or '
                 'Charge move, ignore any vertical distance when determining the '
                 'total distance models in this unit can be moved during that '
                 'move.'),
     ]),

    ('Shroud Runners', 80,
     stat('14"', 4, '5+', 3, '7+', 2, invuln='5+'),
     [
         rng('Long rifle (x3)', '36"', 1, '2+', 4, -1, 2, 'Precision'),
         rng('Scatter Laser (x3)', '36"', 6, '3+', 5, 0, 1,
             'Sustained Hits 1'),
         rng('Shuriken Pistol (x3)', '12"', 1, '2+', 4, -1, 1,
             'Assault, Pistol'),
         mel('Close Combat Weapon (x3)', 1, '3+', 3, 0, 1),
     ],
     [
         ability('Target Acquisition',
                 'In your Shooting phase, after this unit has shot, select one '
                 'enemy unit hit by one or more of those attacks made with a '
                 'long rifle. Until the end of the phase, that enemy unit cannot '
                 'have the Benefit of Cover.'),
     ]),

    ('Skyweavers', 95,
     stat('14"', 4, '4+', 3, '6+', 2, invuln='4+'),
     [
         rng('Shuriken Cannon (x2)', '24"', 3, '3+', 6, -1, 2,
             'Lethal Hits'),
         rng('Star Bolas (x2)', '12"', 'D3', '3+', 7, -2, 2),
         mel('Close Combat Weapon (x2)', 4, '3+', 3, 0, 1),
     ],
     [
         ability('Acrobatic Grace',
                 'Each time an attack targets this unit, subtract 1 from the '
                 'Hit roll.'),
     ]),

    ('Warlock Skyrunner', 45,
     stat('14"', 4, '6+', 3, '6+', 2, invuln='4+'),
     [
         rng('Destructor', '12"', 'D6', 'N/A', 5, -1, 1,
             'Psychic, Torrent'),
         rng('Shuriken Pistol', '12"', 1, '3+', 4, -1, 1,
             'Assault, Pistol'),
         rng('Twin Shuriken Catapult', '18"', 2, '3+', 4, -1, 1,
             'Assault, Twin Linked'),
         mel('Witchblade', 2, '3+', 3, 0, 2,
             'Anti-Infantry 2+, Psychic'),
     ],
     [
         ability('Psychic Communion (Psychic)',
                 'Each time this unit is selected to shoot, for each Warlock '
                 'model in this unit, until the end of the phase, add 1 to the '
                 "Attacks and Strength characteristics of that model's Destructor "
                 'weapon for each other friendly Aeldari Psyker model within 6" '
                 'of this model (to a maximum of +2).'),
         ability('Leader',
                 'At the start of the Declare Battle Formations step, if this '
                 'unit is not an Attached unit, this unit can join one Windriders '
                 'unit from your army (a unit cannot have more than one Warlock '
                 'Skyrunners unit joined to it). If it does, until the end of '
                 'the battle, every model in this unit counts as being part of '
                 "that Bodyguard unit, and that Bodyguard unit's Starting "
                 'Strength is increased accordingly.'),
         ability('Runes of Battle (Psychic)',
                 'Weapons equipped by models in this unit have the [Ignores '
                 'Cover] ability.'),
     ]),

    ('Windriders', 80,
     stat('14"', 4, '4+', 2, '7+', 2, invuln='6+'),
     [
         rng('Twin Shuriken Catapult (x3)', '18"', 2, '3+', 4, -1, 1,
             'Assault, Twin Linked'),
         mel('Close Combat Weapon (x3)', 3, '3+', 3, 0, 1),
     ],
     [
         ability('Swift Demise',
                 'Each time a model in this unit makes a ranged attack, re-roll '
                 'a Hit roll of 1. If the target of that attack is the closest '
                 'eligible target, you can re-roll the Hit roll instead.'),
     ]),

    # -- Heavy Support --------------------------------------------------------

    ('Starfang', 75,
     stat('14"', 6, '3+', 6, '7+', 2),
     [
         rng('Disintegrator Cannon', '36"', 3, '3+', 6, -3, 2, 'Assault'),
         rng('Starfang Grenade Launcher', '36"', 'D3', '3+', 6, -3, 2,
             'Assault, Blast'),
         mel('Wraithbone Hull', 3, '4+', 6, 0, 1),
     ],
     [
         ability('Hallucinogen Grenades',
                 "At the start of your opponent's Shooting phase, this unit can "
                 'use this ability. If it does, select one Aeldari Infantry unit '
                 'from your army visible to and within 36" of this unit: until '
                 'the end of the phase, that unit has the Stealth ability.'),
     ]),

    # -- Vehicles / Transports ------------------------------------------------

    # Falcon card → db_name "Aeldari Wave Serpent" (Wave Serpent card skipped)
    ('Aeldari Wave Serpent', 130,
     stat('14"', 9, '3+', 12, '7+', 3),
     [
         rng('Pulse Laser', '48"', 3, '3+', 9, -2, 'D6'),
         rng('Shuriken Cannon', '24"', 3, '3+', 6, -1, 2, 'Lethal Hits'),
         rng('Twin Shuriken Catapult', '18"', 2, '3+', 4, -1, 1,
             'Assault, Twin Linked'),
         mel('Wraithbone hull', 3, '4+', 6, 0, 1),
     ],
     [
         ability('Damaged: 1-4 Wounds Remaining',
                 'While this model has 1-4 wounds remaining, each time this '
                 'model makes an attack, subtract 1 from the Hit roll.'),
         ability('Fire Support',
                 'In your Shooting phase, after this model has shot, select one '
                 'enemy unit hit by one or more of those attacks. Until the end '
                 'of the turn, each time a friendly model that disembarked from '
                 'this Transport this turn makes an attack that targets that '
                 'enemy unit, you can re-roll the Wound roll'),
     ]),

    ('Crimson Hunter', 160,
     stat('20+"', 8, '3+', 12, '6+', 0, invuln='5+'),
     [
         rng('Pulse Laser', '48"', 3, '3+', 9, -2, 'D6'),
         rng('Starcannon (x2)', '36"', 2, '3+', 8, -3, 2),
         mel('Wraithbone Hull', 3, '4+', 6, 0, 1),
     ],
     [
         ability('Skyhunter',
                 'Each time this model makes a ranged attack that targets a unit '
                 'that can Fly, add 1 to the Hit roll and add 1 to the Wound '
                 'roll.'),
         ability('Damaged: 1-4 Wounds Remaining',
                 'While this model has 1-4 wounds remaining, each time this '
                 'model makes an attack, subtract 1 from the Hit roll.'),
     ]),

    ('Fire Prism', 150,
     stat('14"', 9, '3+', 12, '7+', 3),
     [
         rng('Prism Cannon - dispersed pulse', '60"', '2D6', '3+', 6, -2, 2,
             'Blast'),
         rng('Prism Cannon - focused lances', '60"', 2, '3+', 18, -4, 6,
             'Linked Fire'),
         rng('Twin Shuriken Catapult', '18"', 2, '3+', 4, -1, 1,
             'Assault, Twin Linked'),
         mel('Wraithbone Hull', 3, '4+', 6, 0, 1),
     ],
     [
         ability('Damaged: 1-4 Wounds Remaining',
                 'While this model has 1-4 wounds remaining, each time this '
                 'model makes an attack, subtract 1 from the Hit roll.'),
         ability('Crystal Matrix',
                 'Each time this model is selected to shoot, you can re-roll one '
                 'Hit roll and you can re-roll one Wound roll when resolving '
                 'those attacks.'),
     ]),

    ('Hemlock Wraithfighter', 155,
     stat('20+"', 8, '3+', 12, '6+', 0),
     [
         rng('Heavy D-Scythe (x2)', '18"', 'D6', '4+', 12, -4, 2, 'Blast'),
         mel('Wraithbone Hull', 3, '4+', 6, 0, 1),
     ],
     [
         ability('Mindshock Pod (Aura, Psychic)',
                 'While an enemy unit is within 9" of this model, subtract 1 '
                 'from Battle-shock and Leadership tests taken for that unit.'),
         ability('Damaged: 1-4 Wounds Remaining',
                 'While this model has 1-4 wounds remaining, each time this '
                 'model makes an attack, subtract 1 from the Hit roll.'),
     ]),

    ('Night Spinner', 190,
     stat('14"', 9, '3+', 12, '7+', 3),
     [
         rng('Doomweaver', '48"', 'D6+3', '3+', 7, -1, 2,
             'Blast, Indirect Fire, Twin Linked'),
         rng('Twin Shuriken Catapult', '18"', 2, '3+', 4, -1, 1,
             'Assault, Twin Linked'),
         mel('Wraithbone Hull', 3, '4+', 6, 0, 1),
     ],
     [
         ability('Damaged: 1-4 Wounds Remaining',
                 'While this model has 1-4 wounds remaining, each time this '
                 'model makes an attack, subtract 1 from the Hit roll.'),
         ability('Monofilament Web',
                 'In your Shooting phase, after this model has shot, if one or '
                 'more of those attacks made with its doomweaver scored a hit '
                 'against an enemy unit, until the start of your next turn, that '
                 'enemy unit is pinned. While a unit is pinned, subtract 2 from '
                 "that unit's Move characteristic and subtract 2 from Charge "
                 'rolls made for it.'),
     ]),

    ('Starweaver', 80,
     stat('14"', 6, '4+', 6, '6+', 2, invuln='4+'),
     [
         rng('Shuriken Cannon (x2)', '24"', 3, '3+', 6, -1, 2,
             'Lethal Hits'),
         mel('Close Combat Weapon', 4, '3+', 3, 0, 1),
     ],
     [
         ability('Rapid Embarkation',
                 'At the end of the Fight phase, if there are no models currently '
                 'embarked within this Transport, you can select one friendly '
                 'Harlequins Infantry unit that has 6 or fewer models that is '
                 'wholly within 6" of this Transport. Unless that unit is within '
                 'Engagement Range of one or more enemy units, it can embark '
                 'within this Transport.'),
     ]),

    ('Voidweaver', 125,
     stat('14"', 6, '4+', 6, '6+', 2, invuln='4+'),
     [
         rng('Shuriken Cannon (x2)', '24"', 3, '3+', 6, -1, 2,
             'Lethal Hits'),
         rng('Voidweaver Haywire Cannon', '24"', 3, '3+', 4, -1, 3,
             'Anti-vehicle 4+, Devastating Wounds'),
         mel('Close Combat Weapon', 4, '3+', 3, 0, 1),
     ],
     [
         ability('Polychromatic Camoflage',
                 'This unit can only be selected as the target of a ranged '
                 'attack if the attacking model is within 18".'),
     ]),

    ('Vyper', 75,
     stat('14"', 6, '3+', 6, '7+', 2),
     [
         rng('Bright Lance', '48"', 1, '3+', 12, -3, 'D6+2'),
         rng('Shuriken Cannon', '24"', 3, '3+', 6, -1, 2, 'Lethal Hits'),
         mel('Wraithbone Hull', 3, '4+', 6, 0, 1),
     ],
     [
         ability('Harassment Fire',
                 'In your Shooting phase, after this unit has shot, select one '
                 'enemy unit hit by one or more of those attacks. Until the start '
                 'of your next turn, that enemy unit is suppressed. While a unit '
                 'is suppressed, each time a model in that unit makes an attack, '
                 'subtract 1 from the Hit roll.'),
     ]),

    ('War Walkers', 85,
     stat('10"', 7, '3+', 6, '7+', 2, invuln='5+'),
     [
         rng('Shuriken Cannon (x2)', '24"', 3, '3+', 6, -1, 2,
             'Lethal Hits'),
         mel('War Walker feet', 3, '3+', 5, 0, 1),
     ],
     [
         ability('Crystalline Targeting',
                 'In your Shooting phase, after this unit has shot, select one '
                 'enemy unit hit by one or more of those attacks. Until the end '
                 'of the phase, each time a friendly Aeldari unit makes an '
                 'attack that targets that enemy unit, improve the Armour '
                 'Penetration characteristic of that attack by 1. Each unit can '
                 'only be selected for that ability once per turn.'),
     ]),

    # -- Lords of War ---------------------------------------------------------

    ('Avatar of Khaine', 280,
     stat('10"', 11, '2+', 14, '6+', 5, invuln='4+'),
     [
         rng('The Wailing Doom', '12"', 1, '2+', 16, -4, 'D6+2',
             'Sustained Hits D3'),
         mel('The Wailing Doom - Strike', 6, '2+', 16, -4, 'D6+2'),
         mel('The Wailing Doom - Sweep', 12, '2+', 8, -2, 2),
     ],
     [
         ability('Molten Form',
                 'Each time an attack is allocated to this model, halve the '
                 'Damage characteristic of that attack.'),
         ability('The Bloody Handed (Aura)',
                 'While a friendly Aeldari unit is within 6" of this model, add '
                 '1 to Advance and Charge rolls made for that unit.'),
         ability('Damaged: 1-5 Wounds Remaining',
                 'While this model has 1-5 wounds remaining, each time this '
                 'model makes an attack, subtract 1 from the Hit roll.'),
     ]),

    ('Wraithknight', 435,
     stat('12"', 12, '2+', 18, '6+', 10),
     [
         rng('Suncannon', '48"', 'D6+4', '3+', 10, -3, 3, 'Blast'),
         mel('Titanic Feet', 5, '3+', 8, -1, 2),
     ],
     [
         ability('Damaged: 1-6 Wounds Remaining',
                 'While this model has 1-6 wounds remaining, subtract 5 from '
                 "this model's Objective Control characteristic and each time "
                 'this model makes an attack, subtract 1 from the Hit roll.'),
         ability('Titanic Strides',
                 'Each time this model makes a Normal, Advance or Fall Back '
                 'move, it can move through models (excluding Titanic models) '
                 'and sections of terrain features that are 4" or less in '
                 'height. When doing so:\n'
                 'It can move within Engagement Range of enemy models, but '
                 'cannot end that move within Engagement Range of them.\n'
                 'It can also move through sections of terrain features that are '
                 'more than 4" in height, but if it does, after it has moved, '
                 'roll one D6: on a 1, this model is battle-shocked.'),
         ability('Point-blank Devastation',
                 "Each time this model's Heavy Wraithcannon or Suncannon targets "
                 'a unit within half range, you can re-roll the dice to determine '
                 'the number of attacks made.'),
         ability('Scattershield',
                 'The bearer has a 4+ invulnerable save and each time an attack '
                 'is allocated to the bearer, subtract 1 from the Damage '
                 'characteristic of that attack.'),
     ]),

    ('Wraithlord', 130,
     stat('8"', 10, '2+', 10, '8+', 3),
     [
         rng('Shuriken Catapult (x2)', '18"', 2, '4+', 4, -1, 1,
             'Assault'),
         mel('Wraithbone Fists', 4, '4+', 7, -2, 2),
     ],
     [
         ability('Fated Hero',
                 'At the start of the battle, select one of the following '
                 'keywords: Infantry, Monster, Mounted, Vehicle. Each time this '
                 'model makes an attack that targets a unit with the selected '
                 'keyword, re-roll a Hit roll of 1 and re-roll a Wound roll of '
                 '1.'),
         ability('Psychic Guidance',
                 'While this model is within 12" of one or more friendly Aeldari '
                 'Psyker models, improve the Ballistic Skill and Weapon Skill '
                 'characteristics of weapons equipped by this model by 1 and it '
                 'has a Leadership characteristic of 6+.'),
     ]),

    # -- Ynnari ---------------------------------------------------------------

    ('Yvraine', 100,
     stat('8"', 3, '6+', 4, '6+', 1, invuln='4+'),
     [
         rng('Storm of Whispers', '12"', 'D6+3', '2+', 2, -2, 1,
             'Anti-Infantry 2+, Devastating Wounds, Psychic'),
         mel('Kha-vir', 5, '2+', 4, -3, 2,
             'Devastating Wounds'),
     ],
     [
         ability('Herald of Ynnead',
                 'At the start of the Fight phase, select one enemy unit within '
                 'Engagement Range of this model. Until the end of the phase, '
                 'each time a friendly Aeldari model makes an attack that targets '
                 'that unit, you can re-roll a Wound roll of 1.'),
         ability('Word of the Phoenix (Psychic)',
                 'While this model is leading a unit, in your Command phase, '
                 'roll one D6: on a 2+, D3+1 destroyed Bodyguard models '
                 '(excluding Support Weapon models) are returned to that unit '
                 'with their full wounds remaining.'),
     ]),

    ('The Visarch', 90,
     stat('8"', 3, '2+', 5, '6+', 1, invuln='4+'),
     [
         mel('Asu-var - quicksilver stance', 8, '2+', 4, -1, 1,
             'Sustained Hits 2'),
         mel('Asu-var - duellist stance', 6, '2+', 5, -2, 2,
             'Devastating Wounds, Precision'),
         mel('Asu-var - mythic stance', 4, '2+', 3, -4, 3,
             'Anti-Epic Hero 2+, Precision'),
     ],
     [
         ability('Way of the Blade',
                 'While this model is leading a unit, models in that unit have '
                 'the Fights First ability.'),
         ability("Yvraine's Champion",
                 'While this model is leading a unit, other Character models '
                 'attached to that unit have the Feel No Pain 4+ ability.'),
     ]),

    ('The Yncarne', 260,
     stat('10"', 10, '2+', 12, '6+', 3, invuln='4+'),
     [
         rng('Swirling soul energy', '12"', 'D6+3', 'N/A', 7, -1, 'D3',
             'Ignores Cover, Psychic, Torrent'),
         mel('Vilith-zhar - Strike', 5, '2+', 12, -4, 'D6+1'),
         mel('Vilith-zhar - Sweep', 10, '2+', 6, -4, 1),
     ],
     [
         ability('Inevitable Death',
                 "Once in each of your opponent's turns, if this model is on the "
                 'battlefield when another friendly Aeldari unit is destroyed, '
                 'just after removing the last model in that unit, you can remove '
                 'this model from the battlefield and set it up as close as '
                 'possible to where that destroyed model was destroyed and not '
                 'within Engagement Range of one or more enemy units.'),
         ability('Ethereal Form',
                 'Each time this model destroys an enemy unit it regains up to '
                 'D3 lost wounds.'),
     ]),
]


class Command(BaseCommand):
    """Seed Aeldari stat lines, weapon profiles, and abilities."""

    help = 'Seed Aeldari unit stats, weapons, and abilities.'

    def add_arguments(self, parser):
        """Add --dry-run flag."""
        parser.add_argument(
            '--dry-run', action='store_true',
            help='Preview changes without writing to the database.',
        )

    def handle(self, *args, **options):
        """Iterate over AELDARI_UNITS and upsert stats, weapons, and abilities."""
        dry_run = options['dry_run']
        updated = 0
        skipped = 0

        with transaction.atomic():
            for db_name, pts, stats, weapons, abilities in AELDARI_UNITS:
                try:
                    unit = UnitType.objects.get(name=db_name, faction__name=FACTION_NAME)
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
