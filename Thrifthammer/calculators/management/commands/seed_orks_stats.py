"""
Management command: seed_orks_stats

Seeds points costs, stat lines, weapon profiles, and unit abilities
for all Orks units in the database. Safe to re-run — uses
delete+create for weapons/abilities and direct field writes for stats.

Usage:
    python manage.py seed_orks_stats
    python manage.py seed_orks_stats --dry-run
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

ORKS_UNITS = [

    # -- Epic Heroes / Characters ---------------------------------------------

    ('Boss Snikrot', 75,
     stat('6"', 5, '5+', 6, '6+', 1),
     [
         rng('Slugga', '12"', '1', '4+', 4, 0, 1, 'Pistol'),
         mel('Mork\'s Teeth', '6', '2+', 6, -1, 2,
             'Precision, Twin-linked'),
     ],
     [
         ability('Leader',
                 'This model can be attached to the following unit:\n\nKOMMANDOS'),
     ]),

    ('Ghazghkull Thraka', 235,
     stat('5"', 6, '2+', 10, '6+', 4),
     [
         rng('Mork\'s Roar', '36"', '12', '5+', 5, 0, 1, 'Rapid Fire 4'),
         mel('Gork\'s Klaw - strike', '6', '2+', 14, -3, 4),
         mel('Gork\'s Klaw - sweep', '12', '2+', 8, -2, 2),
         mel('Makari\'s stabba', '1', '4+', 3, 0, 1, 'Devastating Wounds'),
     ],
     [
         ability('Leader',
                 'This unit can be attached to the following units:\n\nBoyz\nMeganobz\nNobz'),
     ]),

    ('Mozrog Skragbad', 145,
     stat('10"', 8, '3+', 8, '6+', 3),
     [
         rng('Thump gun', '18"', 'D3', '5+', 6, 0, 2, 'Blast'),
         mel('Big Chompa\'s jaws', '3', '3+', 7, -2, 4,
             'Devastating Wounds, Extra Attacks'),
         mel('Gutrippa', '6', '2+', 7, -1, 3,
             'Anti-Monster 4+, Anti-Vehicle 4+'),
     ],
     [
         ability('Leader',
                 'This model can be attached to the following unit:\n\nSQUIGHOG BOYZ'),
     ]),

    ('Zodgrod Wortsnagga', 90,
     stat('6"', 5, '5+', 5, '7+', 1),
     [
         rng('Squigstoppa', '12"', '1', '5+', 4, -1, 1,
             'Anti-Monster 4+, Pistol'),
         mel('Da Grabzappa', '5', '2+', 7, -2, 2),
     ],
     [
         ability('Super Runts',
                 'While this model is leading a unit:\n\nModels in that unit have the Scouts 9\" ability.\n'
                 'Each time a model in that unit makes an attack, add 1 to the Hit roll and add 1 to the '
                 'Wound roll.\nEach time an attack targets that unit, subtract 1 from the Wound roll.'),
         ability('Special Dose',
                 'While the Waaagh! is active for your army, add 6\" to the Move characteristic of '
                 'models in this model\'s unit.'),
         ability('Leader',
                 'This model can be attached to the following unit:\n\nGretchin'),
     ]),

    ('Beastboss', 80,
     stat('6"', 5, '4+', 6, '6+', 1, invuln='5+'),
     [
         rng('Shoota', '18"', '2', '4+', 4, 0, 1, 'Rapid Fire 1'),
         mel('Beast Snagga klaw', '4', '3+', 10, -2, 2,
             'Anti-Monster 4+, Anti-Vehicle 4+'),
         mel('Beastchoppa', '6', '2+', 6, -1, 2,
             'Anti-Monster 4+, Anti-Vehicle 4+'),
     ],
     [
         ability('Beastboss',
                 'While this model is leading a unit, each time a model in that unit makes a melee '
                 'attack, add 1 to the Hit roll.'),
         ability('Ferocious Rage',
                 'Each time this model makes a Charge move, until the end of the turn, melee weapons '
                 'it is equipped with have the [DEVASTATING WOUNDS] ability.'),
         ability('Leader',
                 'This model can be attached to the following unit:\n\nBeast Snagga Boyz'),
     ]),

    ('Beastboss on Squigosaur', 110,
     stat('10"', 8, '3+', 8, '6+', 3),
     [
         rng('Slugga', '12"', '1', '5+', 4, 0, 1, 'Pistol'),
         mel('Beastchoppa', '6', '2+', 6, -1, 2,
             'Anti-Monster 4+, Anti-Vehicle 4+'),
         mel('Squigosaur\'s jaws', '3', '4+', 7, -2, 3,
             'Devastating Wounds, Extra Attacks'),
     ],
     [
         ability('Leader',
                 'This model can be attached to the following unit:\n\nSQUIGHOG BOYZ'),
     ]),

    ('Big Mek', 70,
     stat('6"', 5, '3+', 6, '7+', 1),
     [
         rng('Kustom mega-blasta', '24"', '3', '5+', 9, -2, 'D6', 'Hazardous'),
         mel('Power klaw', '4', '3+', 9, -2, 2),
     ],
     [
         ability('Leader',
                 'This model can be attached to the following units:\n\nBOYZ\nLOOTAS\nMEK GUNZ\nNOBZ'),
     ]),

    ('Big Mek in Mega Armour', 90,
     stat('5"', 6, '2+', 5, '7+', 1),
     [
         rng('Kustom mega-blasta', '24"', '3', '5+', 9, -2, 'D6', 'Hazardous'),
         mel('Power klaw', '4', '3+', 9, -2, 2),
     ],
     [
         ability('Leader',
                 'This model can be attached to the following unit:\n\nMEGANOBZ'),
     ]),

    ('Big Mek with Shokk Attack Gun', 80,
     stat('6"', 5, '4+', 5, '7+', 1),
     [
         rng('Shokk attack gun', '60"', 'D6+1', '5+', 9, -4, 'D6',
             'Blast, Heavy'),
         mel('Close combat weapon', '4', '3+', 5, 0, 1),
     ],
     [
         ability('More Dakka',
                 'While this model is leading a unit, each time a model in that unit makes a ranged '
                 'attack, re-roll a Hit roll of 1.'),
         ability('Deranged Snotling Assault',
                 'In your Shooting phase, after this model has shot, select one enemy unit hit by one '
                 'or more of those attacks; that unit must take a Battle-shock test.'),
         ability('Leader',
                 'This model can be attached to the following units:\n\nBoyz\nLootas\nMek Gunz\nNobz'),
     ]),

    ('Deffkilla Wartrike', 80,
     stat('12"', 6, '4+', 9, '6+', 3),
     [
         rng('Deffkilla boomstikks', '12"', '6', '5+', 5, 0, 1, 'Assault'),
         rng('Killa jet - burna', '12"', 'D6', 'N/A', 5, -1, 1,
             'Ignores Cover, Torrent'),
         rng('Killa jet - cutta', '12"', '1', '5+', 9, -4, 'D6', 'Melta 2'),
         mel('Snagga klaw', '4', '3+', 10, -2, 2),
     ],
     [
         ability('Leader',
                 'This model can be attached to the following unit:\n\nWARBIKERS'),
     ]),

    ('Ork Mek', 45,
     stat('6"', 5, '5+', 4, '7+', 1),
     [
         rng('Kustom mega-slugga', '12"', 'D3', '5+', 8, -2, 'D6',
             'Blast, Hazardous'),
         mel('Wrench', '3', '3+', 4, 0, 1),
     ],
     [
         ability('Leader',
                 'This model can be attached to the following units:\n\nBOYZ\nLOOTAS\nMEK GUNZ\nNOBZ\nTANKBUSTAS'),
     ]),

    ('Painboss', 70,
     stat('6"', 5, '4+', 4, '7+', 1),
     [
         mel('Beast Snagga klaw', '3', '4+', 9, -2, 2,
             'Anti-Monster 4+, Anti-Vehicle 4+'),
     ],
     [
         ability('Leader',
                 'This model can be attached to the following unit:\n\nBEAST SNAGGA BOYZ'),
     ]),

    ('Ork Painboy', 80,
     stat('6"', 5, '5+', 3, '7+', 1),
     [
         mel("'Urty syringe", '1', '3+', 2, 0, 1,
             'Anti-Infantry 4+, Extra Attacks, Precision'),
         mel('Power klaw', '3', '4+', 9, -2, 2),
     ],
     [
         ability('Leader',
                 'This model can be attached to the following units:\n\nBOYZ\nNOBZ\nLOOTAS\nBURNA BOYZ\nTANKBUSTAS'),
     ]),

    ('Weirdboy', 65,
     stat('6"', 5, '5+', 4, '7+', 1),
     [
         rng("'Eadbanger", '24"', '1', '4+', 6, -3, 1,
             'Precision, Psychic'),
         mel('Weirdboy staff', '3', '3+', 8, -1, 'D3', 'Psychic'),
     ],
     [
         ability('Da Jump (Psychic)',
                 'Once per turn, at the end of your Movement phase, one WEIRDBOY from your army can '
                 'use this ability. If it does, roll one D6: on a 1, that WEIRDBOY\'s unit suffers D6 '
                 'mortal wounds; on a 2+, remove this WEIRDBOY\'s unit from the battlefield and set it '
                 'up again anywhere on the battlefield that is more than 9\" horizontally away from all '
                 'enemy models.'),
         ability('Waaagh! Energy',
                 'While this model is leading a unit, add 1 to the Strength and Damage characteristics '
                 'of this model\'s \'Eadbanger weapon for every 5 models in that unit (rounding down), '
                 'but while that unit contains 10 or more models, that weapon has the [HAZARDOUS] '
                 'ability.'),
         ability('Leader',
                 'This model can be attached to the following unit:\n\nBoyz'),
     ]),

    # -- Infantry -------------------------------------------------------------

    ('Ork Beast Snagga Boyz', 95,
     stat('6"', 5, '5+', 2, '7+', 2),
     [
         rng('Slugga (x10)', '12"', '1', '5+', 4, 0, 1, 'Pistol'),
         mel('Power snappa', '4', '3+', 7, -1, 2),
         mel('Choppa (x9)', '3', '3+', 5, -1, 1),
     ],
     [
         ability('Monster Hunters',
                 'Each time a model in this unit makes an attack that targets a MONSTER or VEHICLE '
                 'unit, you can re-roll the Hit roll.'),
     ]),

    ('Ork Boyz', 80,
     stat('6"', 5, '5+', 2, '7+', 2),
     [
         rng('Slugga (x10)', '12"', '1', '5+', 4, 0, 1, 'Pistol'),
         mel('Big choppa', '3', '3+', 7, -1, 2),
         mel('Choppa (x9)', '3', '3+', 4, -1, 1),
     ],
     [
         ability('Get Da Good Bitz',
                 'At the end of your Command phase, if this unit is within range of an objective '
                 'marker you control, that objective marker remains under your control, even if you '
                 'have no models within range of it, until your opponent controls it at the start or '
                 'end of any turn.'),
         ability('Bodyguard',
                 'If this unit has a Starting Strength of 20, you can attach up to two Leader units '
                 'to it instead of one (but only if one of those is a WARBOSS model). If you do, and '
                 'this unit is destroyed, the Leader units attached to it become separate units with '
                 'their original Starting Strengths.'),
     ]),

    ('Ork Burna Boyz', 60,
     stat('6"', 5, '5+', 1, '7+', 1),
     [
         rng('Burna (x4)', '12"', 'D6', 'N/A', 4, 0, 1,
             'Ignores Cover, Torrent'),
         rng('Big shoota', '36"', '3', '5+', 5, 0, 1, 'Rapid Fire 2'),
         mel("Cuttin' flames (x4)", '2', '4+', 4, -2, 1),
         mel('Close combat weapon', '3', '3+', 4, 0, 1),
     ],
     [
         ability('Pyromaniaks',
                 'Each time a model in this unit makes a ranged attack with a burna that targets an '
                 'enemy unit within 6\", re-roll a Wound roll of 1. If the target of that attack is '
                 'also within range of an objective marker, you can re-roll the Wound roll instead.'),
     ]),

    ('Ork Flash Gitz', 80,
     stat('6"', 5, '4+', 2, '7+', 1),
     [
         rng('Snazzgun (x5)', '24"', '3', '5+', 6, -1, 2,
             'Heavy, Sustained Hits 1'),
         mel('Choppa (x5)', '4', '3+', 5, -1, 1),
     ],
     [
         ability('Gun-crazy Show-offs',
                 'Each time a model in this unit targets the closest eligible target with its '
                 'snazzgun, until the end of the phase, that weapon has an Attacks characteristic '
                 'of 4.'),
     ]),

    ('Ork Gretchin', 40,
     stat('6"', 2, '7+', 1, '8+', 2),
     [
         rng('Grot blasta (x10)', '12"', '1', '4+', 3, 0, 1, 'Pistol'),
         rng('Slugga', '12"', '1', '5+', 4, 0, 1, 'Pistol'),
         mel('Close combat weapon (x10)', '1', '5+', 2, 0, 1),
         mel('Grot-smacka', '3', '3+', 5, 0, 1),
     ],
     [
         ability('Runtherd',
                 'Each time an attack targets this unit, if it contains one or more Gretchin models, '
                 'until that attack is resolved, Runtherd models in this unit have a Toughness '
                 'characteristic of 2.'),
         ability('Thievin\' Scavengers',
                 'At the start of your Movement phase, roll one D6 for each objective marker you '
                 'control that has one or more units from your army with this ability within range of '
                 'it (excluding Battle-shocked units). If one or more of those rolls is a 4+, you '
                 'gain 1CP.'),
     ]),

    ('Kommandos', 120,
     stat('6"', 5, '5+', 2, '7+', 1),
     [
         rng('Slugga (x10)', '12"', '1', '5+', 4, 0, 1, 'Pistol'),
         mel('Choppa (x10)', '3', '3+', 4, -1, 1),
     ],
     [
         ability('Sneaky Surprise',
                 'Enemy units cannot use the Fire Overwatch Stratagem to shoot at this unit.'),
         ability('Patrol Squad',
                 'At the start of the Declare Battle Formations step this unit can be split into two '
                 'units, each containing five models.\n(when splitting a unit in this way, make a note '
                 'of which models form each of the two new units. If you are splitting a unit that is '
                 'equipped with 1 bomb squig and/or 1 distraction grot, only one of the new units can '
                 'use that ability during the battle \u2013 make a note of which of the new units this '
                 'will be).'),
     ]),

    ('Ork Lootas', 50,
     stat('6"', 5, '5+', 1, '7+', 1),
     [
         rng('Deffgun (x4)', '48"', '2', '6+', 8, -1, 2,
             'Heavy, Rapid Fire 1'),
         rng('Big shoota', '36"', '3', '5+', 5, 0, 1, 'Rapid Fire 2'),
         mel('Close combat weapon (x5)', '2', '3+', 4, 0, 1),
     ],
     [
         ability("Dat's Our Loot!",
                 'Each time a model in this unit makes a ranged attack, re-roll a Hit roll of 1. If '
                 'that attack targets a unit that is within range of an objective marker, you can '
                 're-roll the Hit roll instead.'),
     ]),

    ('Ork Meganobz', 65,
     stat('5"', 6, '2+', 3, '7+', 1),
     [
         rng('Kustom shoota (x2)', '18"', '4', '5+', 4, 0, 1, 'Rapid Fire 2'),
         mel('Power klaw (x2)', '3', '4+', 9, -2, 2),
     ],
     [
         ability("Krumpin' Time",
                 'While the Waaagh! is active for your army, models in this unit have the '
                 'Feel No Pain 5+ ability.'),
     ]),

    ('Ork Nobz', 105,
     stat('6"', 5, '4+', 2, '7+', 1),
     [
         rng('Slugga (x5)', '12"', '1', '5+', 4, 0, 1, 'Pistol'),
         mel('Big choppa (x5)', '3', '3+', 7, -1, 2),
     ],
     [
         ability("Da Boss' Ladz",
                 'While a WARBOSS model is leading this unit, each time an attack targets this unit, '
                 'if the Strength characteristic of that attack is greater than the Toughness '
                 'characteristic of this unit, subtract 1 from the Wound roll.'),
     ]),

    ('Ork Stormboyz', 65,
     stat('12"', 5, '5+', 2, '7+', 1),
     [
         rng('Slugga (x5)', '12"', '1', '5+', 4, 0, 1, 'Pistol'),
         mel('Choppa (x5)', '3', '3+', 4, -1, 1),
     ],
     [
         ability('Full Throttle',
                 'This unit is eligible to declare a charge in a turn in which it Advanced or '
                 'Fell Back.'),
     ]),

    ('Squighog Boyz', 150,
     stat('10"', 7, '4+', 4, '7+', 2),
     [
         rng('Slugga', '12"', '1', '5+', 4, 0, 1, 'Pistol'),
         rng('Saddlegit weapons (x3)', '9"', '1', '4+', 3, 0, 1, 'Assault'),
         rng('Stikka (ranged) (x3)', '9"', '1', '5+', 5, -1, 2,
             'Assault, Anti-Monster 4+, Anti-Vehicle 4+'),
         mel('Big choppa', '4', '3+', 6, -1, 2,
             'Anti-Monster 4+, Anti-Vehicle 4+'),
         mel('Squig jaws (x4)', '3', '4+', 6, -1, 2, 'Extra Attacks'),
         mel('Stikka (melee) (x3)', '3', '3+', 5, -1, 2,
             'Anti-Monster 4+, Anti-Vehicle 4+, Lance'),
     ],
     [
         ability('Wild Ride',
                 'You can ignore any or all modifiers to this unit\'s Move characteristic and to '
                 'Advance and Charge rolls made for this unit.'),
     ]),

    ('Ork Warbiker Mob', 65,
     stat('12"', 6, '4+', 4, '7+', 2, invuln='6+'),
     [
         rng('Twin dakkagun (x3)', '18"', '3', '5+', 5, 0, 1,
             'Assault, Rapid Fire 2, Twin-linked'),
         mel('Close combat weapon (x3)', '2', '3+', 4, 0, 1),
     ],
     [
         ability('Drive-by Dakka',
                 'Each time a model in this unit makes a ranged attack that targets a unit within 9\", '
                 'improve the Armour Penetration characteristic of that attack by 1.'),
     ]),

    # -- Characters (non-Epic Hero) -------------------------------------------

    ('Ork Warboss in Mega Armour', 80,
     stat('5"', 6, '2+', 7, '6+', 1),
     [
         rng('Big shoota', '36"', '3', '4+', 5, 0, 1, 'Rapid Fire 2'),
         mel("'Uge choppa", '4', '2+', 12, -2, 2),
     ],
     [
         ability('Leader',
                 'This model can be attached to the following unit:\n\nMEGANOBZ'),
     ]),

    # -- Vehicles / Monsters --------------------------------------------------

    ('Ork Deff Dread', 120,
     stat('8"', 9, '2+', 8, '7+', 3, invuln='6+'),
     [
         rng('Big shoota (x2)', '36"', '3', '5+', 5, 0, 1, 'Rapid Fire 2'),
         mel('Stompy feet', '4', '3+', 5, 0, 1),
         mel('Dread klaw (x2)', '4', '3+', 12, -2, 3, 'Dead Choppy'),
     ],
     [
         ability('Piston-driven Brutality',
                 'Each time this model ends a Charge move, select one enemy unit within Engagement '
                 'Range of it and roll one D6: on a 2\u20115, that enemy unit suffers D3 mortal wounds; '
                 'on a 6, that enemy unit suffers D3+3 mortal wounds.'),
     ]),

    ('Deffkoptas', 80,
     stat('12"', 6, '4+', 4, '7+', 2, invuln='6+'),
     [
         rng('Kopta rokkits (x3)', '24"', 'D3', '5+', 9, -2, 3,
             'Blast, Twin-linked'),
         rng('Slugga (x3)', '12"', '1', '5+', 4, 0, 1, 'Pistol'),
         mel('Spinnin\' blades (x3)', '6', '3+', 5, 0, 1),
     ],
     [
         ability('Deff from Above',
                 'Each time this unit ends a Normal move, you can select one enemy unit it moved '
                 'over during that move and roll one D6 for each model in this unit: for each 4+, '
                 'that enemy unit suffers 1 mortal wound.'),
     ]),

    ('Gorkanaut', 265,
     stat('8"', 12, '3+', 20, '7+', 8, invuln='6+'),
     [
         rng('Deffstorm mega-shoota', '36"', '20', '5+', 6, -1, 1,
             'Rapid Fire 10'),
         rng('Rokkit launcha (x2)', '24"', 'D3', '5+', 9, -2, 3, 'Blast'),
         rng('Skorcha', '12"', 'D6', 'N/A', 5, -1, 1,
             'Ignores Cover, Torrent'),
         rng('Twin big shoota (x2)', '36"', '3', '5+', 5, 0, 1,
             'Rapid Fire 2, Twin-linked'),
         mel('Klaw of Gork - strike', '5', '3+', 18, -3, 6),
         mel('Klaw of Gork - sweep', '15', '3+', 8, -1, 2),
     ],
     [
         ability("Clankin' Forward",
                 'Each time this model makes a Normal, Advance or Fall Back move, it can move over '
                 'enemy models (excluding MONSTER and VEHICLE models) and terrain features that are '
                 '4\" or less in height as if they were not there.'),
         ability('Big an\' Stompy',
                 'Each time this model makes a melee attack, if the Waaagh! is active for your army, '
                 'add 1 to the Hit roll.'),
         ability('Damaged: 1-7 Wounds Remaining',
                 'While this model has 1-7 wounds remaining, subtract 4 from this model\'s Objective '
                 'Control characteristic, and each time this model makes an attack, subtract 1 from '
                 'the Hit roll.'),
     ]),

    ('Hunta Rig', 135,
     stat('10"', 10, '3+', 16, '7+', 5),
     [
         rng("'Eavy lobba", '48"', 'D6', '5+', 6, 0, 2,
             'Blast, Indirect Fire'),
         rng('Stikka kannon', '12"', '1', '5+', 12, -2, 3,
             'Anti-Monster 2+, Anti-Vehicle 2+, Snagged'),
         mel('Butcha boyz', '4', '3+', 5, -1, 1,
             'Anti-Monster 4+, Anti-Vehicle 4+, Extra Attacks'),
         mel('Savage horns and hooves', '4', '4+', 8, -1, 3,
             'Extra Attacks, Lance'),
         mel('Saw blades', '6', '3+', 10, -2, 2),
     ],
     [
         ability('On Da Hunt',
                 'For each model embarked within this TRANSPORT, add 1 to the Attacks characteristic '
                 'of this model\'s butcha boyz weapon (to a maximum of +6).'),
         ability('Damaged: 1-5 Wounds Remaining',
                 'While this model has 1-5 wounds remaining, each time this model makes an attack, '
                 'subtract 1 from the Hit roll.'),
     ]),

    ('Kill Rig', 155,
     stat('10"', 10, '3+', 16, '7+', 5),
     [
         rng("'Eavy lobba", '48"', 'D6', '5+', 6, 0, 2,
             'Blast, Indirect Fire'),
         rng('Stikka kannon', '12"', '1', '5+', 12, -2, 3,
             'Anti-Monster 2+, Anti-Vehicle 2+, Snagged'),
         rng('Wurrtower', '24"', 'D3', 'N/A', 12, -3, 'D6',
             'Hazardous, Psychic, Torrent'),
         mel('Butcha boyz', '4', '3+', 5, -1, 1,
             'Anti-Monster 4+, Anti-Vehicle 4+, Extra Attacks'),
         mel('Savage horns and hooves', '4', '4+', 8, -1, 3,
             'Extra Attacks, Lance'),
         mel('Saw blades', '6', '3+', 10, -2, 2),
     ],
     [
         ability('Spirit of Gork (Psychic)',
                 'At the start of the Fight phase, you can select one friendly ORKS unit within 12\" '
                 'of this model and roll one D6: on a 1, this model suffers D3 mortal wounds; on a '
                 '2-5, until the end of the phase, add 1 to the Strength characteristic of melee '
                 'weapons equipped by models in that unit; on a 6, until the end of the phase, add 1 '
                 'to the Strength characteristic of melee weapons equipped by models in that unit and '
                 'those weapons have the [LETHAL HITS] ability.'),
     ]),

    ('Ork Battlewagon', 160,
     stat('10"', 10, '3+', 16, '7+', 5, invuln='6+'),
     [
         mel('Tracks and wheels', '6', '4+', 8, 0, 1),
     ],
     [
         ability('Ramshackle but Rugged',
                 'Each time an attack is allocated to this model, worsen the Armour Penetration '
                 'characteristic of that attack by 1.'),
         ability('Damaged: 1-5 Wounds Remaining',
                 'While this model has 1-5 wounds remaining, each time this model makes an attack, '
                 'subtract 1 from the Hit roll.'),
     ]),

    ('Blitza-Bommer', 115,
     stat('20+"', 9, '3+', 12, '7+', 0, invuln='6+'),
     [
         rng('Big shoota', '36"', '3', '5+', 5, 0, 1, 'Rapid Fire 2'),
         rng('Twin supa-shoota', '36"', '4', '5+', 6, -1, 1,
             'Rapid Fire 2, Sustained Hits 1, Twin-linked'),
         mel('Armoured hull', '3', '4+', 6, 0, 1),
     ],
     [
         ability('Boom Bomb',
                 'Each time this model ends a Normal move, you can select one enemy unit it moved '
                 'over during that move and roll one D6: on a 4+, that unit suffers D6 mortal wounds.'),
         ability('Damaged: 1-4 Wounds Remaining',
                 'While this model has 1-4 wounds remaining, each time this model makes an attack, '
                 'subtract 1 from the Hit roll.'),
     ]),

    ('Boomdakka Snazzwagon', 70,
     stat('12"', 7, '4+', 9, '7+', 3, invuln='6+'),
     [
         rng('Big shoota', '36"', '3', '5+', 5, 0, 1, 'Rapid Fire 2'),
         rng('Grot blasta', '12"', '1', '4+', 3, 0, 1, 'Pistol'),
         rng('Mek speshul', '24"', '12', '5+', 5, -1, 1,
             'Assault, Rapid Fire 4, Sustained Hits 1'),
         mel('Spiked wheels', '4', '4+', 7, -1, 2),
     ],
     [
         ability('Billowing Fumes (Aura)',
                 'While an enemy unit (excluding MONSTERS and VEHICLES) is within 6\" of this model, '
                 'each time a model in that unit makes an attack, subtract 1 from the Hit roll.'),
     ]),

    ('Burna-Bommer', 125,
     stat('20+"', 9, '3+', 12, '7+', 0, invuln='6+'),
     [
         rng('Twin big shoota', '36"', '3', '5+', 5, 0, 1,
             'Rapid Fire 2, Twin-linked'),
         rng('Twin supa-shoota', '36"', '4', '5+', 6, -1, 1,
             'Rapid Fire 2, Sustained Hits 1, Twin-linked'),
         mel('Armoured hull', '3', '4+', 6, 0, 1),
     ],
     [
         ability('Burna Bomb',
                 'Each time this model ends a Normal move, you can select one enemy unit it moved '
                 'over during that move. Until the end of the turn, models in that unit cannot have '
                 'the Benefit of Cover. In addition, roll one D6 for each model in that unit: for '
                 'each 6, that unit suffers 1 mortal wound.'),
         ability('Damaged: 1-4 Wounds Remaining',
                 'While this model has 1-4 wounds remaining, each time this model makes an attack, '
                 'subtract 1 from the Hit roll.'),
     ]),

    ('Dakkajet', 135,
     stat('20+"', 9, '3+', 12, '7+', 0, invuln='6+'),
     [
         rng('Twin supa-shoota (x2)', '36"', '4', '5+', 6, -1, 1,
             'Rapid Fire 2, Sustained Hits 1, Twin-linked'),
         mel('Armoured hull', '3', '4+', 6, 0, 1),
     ],
     [
         ability('Dakkastorm',
                 'Each time this model makes a ranged attack, every successful Hit roll scores a '
                 'Critical Hit.'),
         ability('Damaged: 1-4 Wounds Remaining',
                 'While this model has 1-4 wounds remaining, each time this model makes an attack, '
                 'subtract 1 from the Hit roll.'),
     ]),

    ('Ork Killa Kans', 125,
     stat('6"', 6, '3+', 5, '8+', 2, invuln='6+'),
     [
         rng('Kan shoota (x3)', '36"', '3', '4+', 5, 0, 1,
             'Devastating Wounds, Rapid Fire 2'),
         mel('Kan klaw (x3)', '3', '4+', 8, -2, 3),
     ],
     [
         ability('Shooty Power Trip',
                 'Each time this unit is selected to shoot, you can roll one D6:\n\nOn a 1-2, this '
                 'unit suffers D3 mortal wounds.\nOn a 3-4, until the end of the phase, add 1 to the '
                 'Strength characteristic of ranged weapons equipped by models in this unit.\nOn a 5-6, '
                 'until the end of the phase, add 1 to the Attacks characteristic of ranged weapons '
                 'equipped by models in this unit.'),
     ]),

    ('Kustom Boosta-blasta', 70,
     stat('12"', 7, '4+', 9, '7+', 3, invuln='6+'),
     [
         rng('Burna exhausts', '6"', '2D6', 'N/A', 4, 0, 1,
             'Ignores Cover, Torrent, Twin-linked'),
         rng('Grot blasta', '12"', '1', '4+', 3, 0, 1, 'Pistol'),
         rng('Rivet kannon', '36"', '6', '5+', 8, -1, 2,
             'Assault, Rapid Fire 3'),
         mel('Spiked wheels', '4', '4+', 7, -1, 2),
     ],
     [
         ability("Rivetin' Dakka",
                 'In your Shooting phase, after this model has shot, select one enemy unit hit by one '
                 'or more of those attacks made with a rivet kannon. Until the start of your next '
                 'turn, that enemy unit is suppressed. While a unit is suppressed, each time a model '
                 'in that unit makes a ranged attack, subtract 1 from the Hit roll.'),
     ]),

    ('Megatrakk Scrapjet', 75,
     stat('12"', 7, '4+', 9, '7+', 3, invuln='6+'),
     [
         rng('Rokkit cannon', '24"', 'D6+1', '5+', 9, -2, 3, 'Blast'),
         rng('Twin big shoota (x2)', '36"', '3', '5+', 5, 0, 1,
             'Rapid Fire 2, Twin-linked'),
         rng('Wing missiles', '24"', '1', '5+', 9, -2, 3),
         mel('Nose drill', '4', '4+', 8, -1, 2),
     ],
     [
         ability('Drill Through',
                 'Each time this model ends a Charge move, select one enemy unit within Engagement '
                 'Range of it and roll one D6: on a 2-5, that enemy unit suffers D3 mortal wounds; '
                 'on a 6, that enemy unit suffers 3 mortal wounds.'),
     ]),

    ('Mek Gunz: Bubblechukka', 50,
     stat('3"', 5, '5+', 6, '8+', 2, invuln='6+'),
     [
         rng('Smasha gun', '48"', 'D3+1', '4+', 9, -3, 3, 'Blast'),
         mel('Grot crew', '6', '5+', 2, 0, 1),
     ],
     [
         ability('Splat!',
                 'Each time a model in this unit makes a ranged attack that targets a unit that is at '
                 'its Starting Strength (excluding MONSTERS and VEHICLES), re-roll a Hit roll of 1.'),
     ]),

    ('Morkanaut', 280,
     stat('8"', 12, '3+', 20, '7+', 8, invuln='5+'),
     [
         rng('Kustom mega-blasta', '24"', '3', '5+', 9, -2, 'D6', 'Hazardous'),
         rng('Kustom mega-zappa', '36"', 'D6+3', '5+', 10, -2, 'D6',
             'Blast, Hazardous'),
         rng('Rokkit launcha (x2)', '24"', 'D3', '5+', 9, -2, 3, 'Blast'),
         rng('Twin big shoota (x2)', '36"', '3', '5+', 5, 0, 1,
             'Rapid Fire 2, Twin-linked'),
         mel('Klaw of Mork - strike', '4', '3+', 18, -3, 6),
         mel('Klaw of Mork - sweep', '12', '3+', 8, -1, 2),
     ],
     [
         ability("Clankin' Forward",
                 'Each time this model makes a Normal, Advance or Fall Back move, it can move over '
                 'enemy models (excluding MONSTER and VEHICLE models) and terrain features that are '
                 '4\" or less in height as if they were not there.'),
         ability("Big an' Shooty",
                 'Each time this model makes a ranged attack, if the Waaagh! is active for your army, '
                 'add 1 to the Hit roll.'),
         ability('Damaged: 1-7 Wounds Remaining',
                 'While this model has 1-7 wounds remaining, subtract 4 from this model\'s Objective '
                 'Control characteristic, and each time this model makes an attack, subtract 1 from '
                 'the Hit roll.'),
     ]),

    ('Rukkatrukk Squigbuggy', 95,
     stat('12"', 7, '4+', 9, '7+', 3, invuln='6+'),
     [
         rng('Sawn-off shotgun', '12"', '2', '5+', 4, 0, 1, 'Assault'),
         rng('Squig launchas', '36"', 'D6+6', '5+', 5, -1, 2,
             'Blast, Ignores Cover, Indirect Fire'),
         mel('Saw blades', '4', '4+', 7, -1, 2),
     ],
     [
         ability('Buzzer Squigs',
                 'In your Shooting phase, after this model has shot, select one enemy unit '
                 '(excluding MONSTERS and VEHICLES) hit by one or more of those attacks made with '
                 'squig-launchas and roll one D6; on a 4+, until the end of your opponent\'s next '
                 'turn, that enemy unit is hindered. While a unit is hindered, subtract 2\" from its '
                 'Move characteristic and subtract 2 from Advance and Charge rolls made for it.'),
         ability('Squig Mine',
                 'Once per battle, at the start of any phase, select one enemy unit within 3\" of this '
                 'model and roll one D6: on a 4+, that enemy unit suffers D6 mortal wounds.\n'
                 "Designer's Note: Place a Squig Mine token next to the model, removing it once this "
                 'ability has been used.'),
     ]),

    ('Shokkjump Dragsta', 70,
     stat('12"', 7, '4+', 9, '7+', 3, invuln='6+'),
     [
         rng('Kustom shokk rifle', '24"', '1', '3+', 8, -2, 'D6+1',
             'Devastating Wounds, Hazardous, Precision'),
         rng('Rokkit launcha', '24"', 'D3', '5+', 9, -2, 3, 'Blast'),
         mel('Saw blades', '4', '4+', 7, -1, 2),
     ],
     [
         ability('Shokk Tunnel',
                 'Each time this model is selected to Advance, you can remove it from the battlefield '
                 'and set it up again anywhere on the battlefield that is more than 9\" horizontally '
                 'away from all enemy models instead of making an Advance move (this model is still '
                 'considered to have Advanced this turn).'),
     ]),

    ('Stompa', 800,
     stat('10"', 14, '2+', 30, '6+', 12, invuln='6+'),
     [
         rng('Big shoota (x3)', '36"', '3', '5+', 5, 0, 1, 'Rapid Fire 2'),
         rng('Deffkannon', '72"', '3D6', '5+', 14, -3, 'D6', 'Blast'),
         rng('Skorcha', '12"', 'D6', 'N/A', 5, -1, 1,
             'Ignores Cover, Torrent'),
         rng('Supa-gatler', '24"', '20', '5+', 7, -1, 2, 'Sustained Hits 1'),
         rng('Supa-rokkits', '100"', 'D6', '5+', 12, -3, 'D6+2', 'Blast'),
         rng('Twin big shoota', '36"', '3', '5+', 5, 0, 1,
             'Rapid Fire 2, Twin-linked'),
         mel('Mega-choppa - strike', '6', '3+', 24, -5, 10),
         mel('Mega-choppa - sweep', '18', '3+', 10, -2, 3),
     ],
     [
         ability('Damaged: 1-10 Wounds Remaining',
                 'While this model has 1-10 wounds remaining, subtract 6 from this model\'s Objective '
                 'Control characteristic and each time this model makes an attack, subtract 1 from the '
                 'Hit roll.'),
         ability('Waaagh! Effigy (Aura)',
                 'While a friendly ORKS unit is within 12\" of this model, each time you take a '
                 'Battle-shock test for that unit, add 1 to that test.'),
         ability("Stompin' Forward",
                 'Each time this model makes a Normal, Advance or Fall Back move, it can move over '
                 'models (excluding Titanic models) and terrain features that are 4\" or less in height '
                 'as if they were not there.'),
     ]),

    ('Wazbom Blastajet', 175,
     stat('20+"', 9, '3+', 12, '7+', 0, invuln='6+'),
     [
         rng('Smasha gun', '48"', 'D3', '4+', 9, -3, 4, 'Blast'),
         rng('Twin wazbom mega-kannon', '36"', 'D3', '4+', 12, -2, 'D6',
             'Blast, Hazardous, Twin-linked'),
         mel('Armoured hull', '3', '4+', 6, 0, 1),
     ],
     [
         ability('Blastajet Attack Run',
                 'Each time this model makes a ranged attack that targets a unit that cannot FLY, '
                 're-roll a Hit roll of 1.'),
         ability('Damaged: 1-4 Wounds Remaining',
                 'While this model has 1-4 wounds remaining, each time this model makes an attack, '
                 'subtract 1 from the Hit roll.'),
     ]),

    ('Ork Trukk', 70,
     stat('12"', 8, '4+', 10, '7+', 2, invuln='6+'),
     [
         rng('Big shoota', '36"', '3', '5+', 5, 0, 1, 'Rapid Fire 2'),
         mel('Spiked wheel', '3', '4+', 6, 0, 1),
     ],
     [
         ability('Grot Riggers',
                 'At the start of your Command phase, this model regains 1 lost wound.'),
     ]),
]


class Command(BaseCommand):
    """Seed Orks stat lines, weapon profiles, and abilities."""

    help = 'Seed Orks unit stats, weapons, and abilities.'

    def add_arguments(self, parser):
        """Add --dry-run flag."""
        parser.add_argument(
            '--dry-run', action='store_true',
            help='Preview changes without writing to the database.',
        )

    def handle(self, *args, **options):
        """Iterate over ORKS_UNITS and upsert stats, weapons, and abilities."""
        dry_run = options['dry_run']
        updated = 0
        skipped = 0

        with transaction.atomic():
            for db_name, pts, stats, weapons, abilities in ORKS_UNITS:
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
