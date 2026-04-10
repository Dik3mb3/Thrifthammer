"""
Management command: seed_aeldari_stats

Seeds points costs, stat lines, weapon profiles, and unit abilities
for all Aeldari units in the database. Safe to re-run -- uses update_or_create.

Usage:
    python manage.py seed_aeldari_stats
    python manage.py seed_aeldari_stats --dry-run
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from calculators.models import UnitAbility, UnitType, WeaponProfile
from products.models import Faction


# -- Helpers ------------------------------------------------------------------

def stat(m, t, sv, w, ld, oc, invuln='', fnp=''):
    return dict(
        stat_movement=m, stat_toughness=t, stat_save=sv,
        stat_wounds=w, stat_leadership=ld, stat_oc=oc,
        stat_invuln=invuln, stat_fnp=fnp,
    )


def rng(name, rng_val, a, skill, s, ap, d, kw=''):
    return dict(name=name, weapon_type='ranged', range=rng_val,
                attacks=str(a), skill=skill, strength=str(s), ap=str(ap), damage=str(d), keywords=kw)


def mel(name, a, skill, s, ap, d, kw=''):
    return dict(name=name, weapon_type='melee', range='Melee',
                attacks=str(a), skill=skill, strength=str(s), ap=str(ap), damage=str(d), keywords=kw)


def ability(name, desc):
    return dict(name=name, description=desc)


# -- Unit Data ----------------------------------------------------------------
# Format: (db_unit_name, points, stats_dict, [weapons], [abilities])

AELDARI_UNITS = [

    # -- Epic Heroes ----------------------------------------------------------

    ('Asurmen', 135,
     stat('7"', 3, '2+', 5, '6+', 1, invuln='4+'),
     [
         rng('The Bloody Twins', '24"', 6, '2+', 5, -1, 2, 'Assault, Pistol'),
         mel('The Sword of Asur', 6, '2+', 6, -3, 3, 'Devastating Wounds'),
     ],
     [
         ability('Invulnerable Save (4+)', 'Asurmen has a 4+ invulnerable save.'),
         ability('Leader', 'Can be attached to: Dire Avengers.'),
         ability('Hand of Asuryan', 'Once per battle, when this model is selected to shoot, until the end of the phase, this model\'s The Bloody Twins weapon has the [LETHAL HITS] ability, and each hit scores 2 additional hits.'),
     ]),

    ('Avatar of Khaine', 280,
     stat('10"', 11, '2+', 14, '6+', 5),
     [
         rng('The Wailing Doom', '12"', 1, '2+', 16, -4, 'D6+2', 'Sustained Hits D3'),
         mel('The Wailing Doom - Strike', 6, '2+', 16, -4, 'D6+2'),
         mel('The Wailing Doom - Sweep', 12, '2+', 8, -2, 2),
     ],
     [
         ability('Molten Form', 'Each time an attack is allocated to this model, halve the Damage characteristic of that attack.'),
         ability('The Bloody Handed (Aura)', 'While an enemy unit is within 9" of this model, subtract 1 from the Leadership and Objective Control characteristics of models in that unit.'),
     ]),

    ('Baharroth', 115,
     stat('14"', 3, '2+', 5, '6+', 1, invuln='4+'),
     [
         rng('Fury of the Tempest', '24"', 4, '2+', 6, -1, 2, 'Assault, Lethal Hits'),
         mel('The Shining Blade', 6, '2+', 5, -2, 2, 'Sustained Hits 1'),
     ],
     [
         ability('Invulnerable Save (4+)', 'Baharroth has a 4+ invulnerable save.'),
         ability('Leader', 'Can be attached to: Swooping Hawks.'),
         ability('Cry of the Wind', 'Each time this model is set-up on the battlefield, until the end of the turn, each time this model makes a ranged attack, a successful unmodified Hit roll scores a Critical Hit.'),
     ]),

    ('Eldrad Ulthran', 120,
     stat('7"', 4, '6+', 5, '6+', 1, invuln='4+'),
     [
         rng('Mind War', '18"', 1, '2+', 5, -2, 'D6', 'Anti-Character 4+, Precision, Psychic'),
         rng('Shuriken Pistol', '12"', 1, '2+', 4, -1, 1, 'Assault, Pistol'),
         mel('Staff of Ulthamar', 3, '2+', 5, -1, 2, 'Anti-Infantry 2+, Psychic'),
     ],
     [
         ability('Invulnerable Save (4+)', 'Eldrad Ulthran has a 4+ invulnerable save.'),
         ability('Leader', 'Can be attached to: Guardian Defenders, Storm Guardians, Warlock Conclave.'),
         ability('Diviner of the Futures', 'At the start of your Command phase, roll 3D6 and store them. Once per phase, before making a roll, you can discard one stored dice to substitute it for the stored result.'),
     ]),

    ('Fuegan', 120,
     stat('7"', 3, '2+', 5, '6+', 1, invuln='4+'),
     [
         rng('Searsong - Beam', '12"', 3, '2+', 8, -3, 2, 'Assault, Melta 1, Sustained Hits 2'),
         rng('Searsong - Lance', '18"', 1, '2+', 14, -4, 'D6', 'Assault, Melta 6'),
         mel('The Fire Axe', 6, '2+', 5, -4, 3),
     ],
     [
         ability('Invulnerable Save (4+)', 'Fuegan has a 4+ invulnerable save.'),
         ability('Leader', 'Can be attached to: Fire Dragons.'),
         ability('Burning Lance', 'While this model is leading a unit, add 6" to the Range of Melta weapons equipped by models in that unit.'),
     ]),

    ('Jain Zar', 120,
     stat('8"', 3, '2+', 5, '6+', 1, invuln='4+'),
     [
         rng('Silent Death', '12"', 6, '2+', 6, -2, 1, 'Assault'),
         mel('Blade of Destruction', 8, '2+', 6, -3, 2, 'Anti-Infantry 3+'),
     ],
     [
         ability('Invulnerable Save (4+)', 'Jain Zar has a 4+ invulnerable save.'),
         ability('Leader', 'Can be attached to: Howling Banshees.'),
         ability('Whirling Death', 'While this model is leading a unit, each time that unit Advances, add 6" to the Move characteristic and ignore vertical distance during that move.'),
     ]),

    ('Kharseth', 95,
     stat('7"', 3, '6+', 4, '6+', 1, invuln='4+'),
     [
         rng('Dread of the Deep Void', '24"', 'D6+2', '3+', 3, -2, 1, 'Anti-Infantry 2+, Blast, Hazardous, Ignores Cover, Psychic'),
         mel('Waystave', 3, '2+', 3, 0, 3, 'Anti-Infantry 2+, Psychic'),
     ],
     [
         ability('Invulnerable Save (4+)', 'Kharseth has a 4+ invulnerable save.'),
         ability('Leader', 'Can be attached to: Corsair Voidreavers, Corsair Voidscarred.'),
         ability('Aethersense (Psychic)', 'Enemy units that are set up on the battlefield from Reserves cannot be set up within 12" of this model.'),
     ]),

    ('Lhykhis', 135,
     stat('12"', 3, '2+', 5, '6+', 1, invuln='4+'),
     [
         rng('Brood Twain', '12"', 'D6+3', 'N/A', 6, -2, 1, 'Ignores Cover, Torrent, Twin-Linked'),
         mel('Spider\'s Fangs', 5, '2+', 4, -2, 1, 'Extra Attacks, Lethal Hits'),
         mel('Weaverender', 5, '2+', 6, -2, 2, 'Lethal Hits'),
     ],
     [
         ability('Invulnerable Save (4+)', 'Lhykhis has a 4+ invulnerable save.'),
         ability('Leader', 'Can be attached to: Warp Spiders.'),
         ability('Whispering Web', 'In your Shooting phase, after this model has shot, select one enemy unit hit. Until the end of the turn, each time a friendly Aeldari model makes an attack targeting that unit, an unmodified Hit roll of 5+ scores a Critical Hit.'),
     ]),

    ('Maugan Ra', 100,
     stat('7"', 3, '2+', 5, '6+', 1, invuln='4+'),
     [
         rng('Maugetar', '36"', 6, '2+', 7, -2, 2, 'Devastating Wounds, Ignores Cover'),
         mel('Maugetar', 5, '2+', 6, -2, 2),
     ],
     [
         ability('Invulnerable Save (4+)', 'Maugan Ra has a 4+ invulnerable save.'),
         ability('Leader', 'Can be attached to: Dark Reapers.'),
         ability('Face of Death', 'In your Shooting phase, after this model has shot, select one enemy unit hit. That enemy unit must take a Battle-shock test, subtracting 1 from the result.'),
     ]),

    ('Prince Yriel', 95,
     stat('7"', 3, '3+', 5, '6+', 1, invuln='4+'),
     [
         rng('Shuriken Pistol', '12"', 1, '2+', 4, -1, 1, 'Assault, Pistol'),
         rng('The Eye of Wrath', '6"', 3, '2+', 6, -2, 2, 'Assault, Pistol'),
         mel('The Spear of Twilight', 5, '2+', 7, -3, 3, 'Lance'),
     ],
     [
         ability('Invulnerable Save (4+)', 'Prince Yriel has a 4+ invulnerable save.'),
         ability('Leader', 'Can be attached to: Corsair Voidreavers, Corsair Voidscarred.'),
         ability('Piratical Hero', 'While this model is leading a unit, each time a model in that unit makes an attack, that attack has [Sustained Hits 1] and add 1 to the Hit roll.'),
     ]),

    ('Solitaire', 115,
     stat('12"', 3, '6+', 4, '6+', 1, invuln='4+'),
     [],
     [
         ability('Invulnerable Save (4+)', 'This model has a 4+ invulnerable save.'),
         ability('Blitz', 'Once per battle, before this model makes a Normal move, until the end of the turn, add 2D6" to Move and add 3 to the Attacks of this model\'s Solitaire weapons.'),
         ability('Blur of Movement', 'This model is eligible to declare a charge in a turn in which it Advanced.'),
     ]),

    # -- Characters -----------------------------------------------------------

    ('Autarch', 85,
     stat('7"', 3, '3+', 4, '6+', 1, invuln='4+'),
     [
         rng('Shuriken Pistol', '12"', 1, '2+', 4, -1, 1, 'Assault, Pistol'),
         mel('Star Glaive', 4, '2+', 6, -3, 3),
     ],
     [
         ability('Invulnerable Save (4+)', 'An Autarch has a 4+ invulnerable save.'),
         ability('Leader', 'Can be attached to: Dark Reapers, Dire Avengers, Fire Dragons, Guardian Defenders, Howling Banshees, Storm Guardians, Striking Scorpions.'),
         ability('Superlative Strategist', 'While this model is leading a unit, you can re-roll Advance rolls made for that unit.'),
     ]),

    ('Autarch Wayleaper', 80,
     stat('14"', 3, '3+', 4, '6+', 1),
     [
         rng('Shuriken Pistol', '12"', 1, '2+', 4, -1, 1, 'Assault, Pistol'),
         mel('Star Glaive', 4, '2+', 6, -3, 3),
     ],
     [
         ability('Invulnerable Save (4+)', 'An Autarch Wayleaper has a 4+ invulnerable save.'),
         ability('Leader', 'Can be attached to: Swooping Hawks, Warp Spiders.'),
         ability('Path of Command', 'Once per battle round, one model from your army with this ability can reduce the CP cost of a Stratagem by 1CP when its unit is targeted.'),
     ]),

    ('Death Jester', 90,
     stat('8"', 3, '6+', 4, '6+', 1, invuln='4+'),
     [
         rng('Shrieker Cannon', '24"', 3, '2+', 6, -2, 2),
         mel('Jester\'s Blade', 4, '2+', 4, 0, 1),
     ],
     [
         ability('Invulnerable Save (4+)', 'This unit has a 4+ invulnerable save.'),
         ability('Death is Not Enough', 'In your Shooting phase, after this model has shot, select one enemy unit (excluding Monsters and Vehicles) hit. That enemy unit must take a Battle-shock test. If one or more models flee, it suffers D3 mortal wounds.'),
         ability('Lone Operative', 'This model can only be targeted in the Shooting phase if the attacking model is within 12".'),
     ]),

    ('Farseer Skyrunner', 80,
     stat('14"', 4, '6+', 5, '6+', 2, invuln='4+'),
     [
         rng('Eldritch Storm', '24"', 'D6', '3+', 6, -2, 'D3', 'Blast, Psychic'),
         rng('Twin Shuriken Catapult', '18"', 2, '3+', 4, -1, 1, 'Assault, Twin-Linked'),
         mel('Witchblade', 2, '2+', 3, 0, 2, 'Anti-Infantry 2+, Psychic'),
     ],
     [
         ability('Invulnerable Save (4+)', 'A Farseer Skyrunner has a 4+ invulnerable save.'),
         ability('Leader', 'Can be attached to: Warlock Skyrunners, Windriders.'),
         ability('Branching Fates (Psychic)', 'While this model is leading a unit, once per phase you can change the result of one Hit roll, Wound roll, or Damage roll made for a model in that unit.'),
     ]),

    ('Shadowseer', 60,
     stat('8"', 3, '6+', 4, '6+', 1, invuln='4+'),
     [
         rng('Shuriken Pistol', '12"', 1, '2+', 4, -1, 1, 'Assault, Pistol'),
         mel('Miststave', 4, '2+', 5, -1, 'D3', 'Psychic'),
     ],
     [
         ability('Invulnerable Save (4+)', 'This unit has a 4+ invulnerable save.'),
         ability('Leader', 'Can be attached to: Troupe.'),
         ability('Fog of Dreams (Psychic)', 'While this model is leading a unit, that unit can only be selected as the target of a ranged attack if the attacking model is within 18".'),
     ]),

    ('Spiritseer', 65,
     stat('7"', 3, '6+', 3, '6+', 1, invuln='4+'),
     [
         rng('Shuriken Pistol', '12"', 1, '2+', 4, -1, 1, 'Assault, Pistol'),
         mel('Witch Staff', 2, '2+', 3, 0, 'D3', 'Anti-Infantry 2+, Psychic'),
     ],
     [
         ability('Invulnerable Save (4+)', 'A Spiritseer has a 4+ invulnerable save.'),
         ability('Spirit Mark (Psychic)', 'Once per turn, when this model starts or ends a move, select one friendly Wraithguard or Wraithblades unit within 9" -- that unit can shoot as if it were your Shooting phase.'),
     ]),

    ('Warlocks', 45,
     stat('7"', 3, '6+', 2, '6+', 1, invuln='4+'),
     [
         rng('Destructor', '12"', 'D6', 'N/A', 5, -1, 1, 'Psychic, Torrent'),
         rng('Shuriken Pistol', '12"', 1, '3+', 4, -1, 1, 'Assault, Pistol'),
         mel('Witchblade', 2, '3+', 3, 0, 2, 'Anti-Infantry 2+, Psychic'),
     ],
     [
         ability('Invulnerable Save (4+)', 'A Warlock has a 4+ invulnerable save.'),
         ability('Runes of Fortune (Psychic)', 'Each time an enemy unit declares a charge, if one or more units with this ability are targeted, subtract 2 from the Charge roll.'),
         ability('Leader', 'Can be attached to: Guardian Defenders, Storm Guardians.'),
     ]),

    ('Warlock Skyrunner', 45,
     stat('14"', 4, '6+', 3, '6+', 2),
     [
         rng('Destructor', '12"', 'D6', 'N/A', 5, -1, 1, 'Psychic, Torrent'),
         rng('Twin Shuriken Catapult', '18"', 2, '3+', 4, -1, 1, 'Assault, Twin-Linked'),
         mel('Witchblade', 2, '3+', 3, 0, 2, 'Anti-Infantry 2+, Psychic'),
     ],
     [
         ability('Invulnerable Save (4+)', 'A Warlock Skyrunner has a 4+ invulnerable save.'),
         ability('Psychic Communion (Psychic)', 'Each time this unit is selected to shoot, for each Warlock model in this unit, add 1 to the Attacks and Strength of its Destructor weapon (max +3).'),
     ]),

    # -- Infantry (Craftworld) ------------------------------------------------

    ('Aeldari Farseer', 70,
     stat('7"', 3, '6+', 4, '6+', 1),
     [
         rng('Eldritch Storm', '24"', 'D6', '3+', 6, -2, 'D3', 'Blast, Psychic'),
         rng('Shuriken Pistol', '12"', 1, '3+', 4, -1, 1, 'Assault, Pistol'),
         mel('Witchblade', 2, '2+', 3, 0, 2, 'Anti-Infantry 2+, Psychic'),
     ],
     [
         ability('Leader', 'Can be attached to: Guardian Defenders, Storm Guardians, Warlock Conclave.'),
         ability('Branching Fates (Psychic)', 'While this model is leading a unit, once per phase you can change the result of one Hit roll, Wound roll, or Damage roll made for a model in that unit.'),
     ]),

    ('Aeldari Dire Avengers', 75,
     stat('7"', 3, '4+', 1, '6+', 1),
     [
         rng('Avenger Shuriken Catapult (x5)', '18"', 4, '3+', 4, -1, 1, 'Assault'),
         mel('Close Combat Weapon (x5)', 2, '3+', 3, 0, 1),
     ],
     [
         ability('Invulnerable Save (5+)', 'This unit has a 5+ invulnerable save.'),
         ability('Bladestorm', 'Ranged weapons equipped by models in this unit have the [Sustained Hits 1] ability while targeting an enemy unit within half range.'),
     ]),

    ('Aeldari Fire Dragons', 120,
     stat('7"', 3, '3+', 1, '6+', 1, invuln='5+'),
     [
         rng('Dragon Fusion Gun (x4)', '12"', 1, '3+', 9, -4, 'D6', 'Assault, Melta 3'),
         rng('Exarch\'s Dragon Fusion Gun', '12"', 1, '3+', 9, -4, 'D6', 'Assault, Melta 6'),
         mel('Close combat weapon (x5)', 2, '3+', 3, 0, 1),
     ],
     [
         ability('Invulnerable Save (5+)', 'This unit has a 5+ invulnerable save.'),
         ability('Assured Destruction', 'In your Shooting phase, each time a model in this unit makes an attack with a Melta weapon that targets a Vehicle, re-roll a Wound roll of 1.'),
     ]),

    ('Aeldari Guardians', 100,
     stat('7"', 3, '4+', 1, '7+', 2),
     [
         rng('Shuriken Catapult (x10)', '18"', 2, '3+', 4, -1, 1, 'Assault'),
         rng('Shuriken Cannon', '24"', 3, '3+', 6, -1, 2, 'Lethal Hits'),
         mel('Close Combat Weapon (x11)', 1, '3+', 3, 0, 1),
     ],
     [
         ability('Fleet of Foot', 'This unit can perform the Fade Back Agile Manoeuvre without spending a Battle Focus token.'),
         ability('Battle Focus', 'In your Shooting phase, this unit can make a Normal move after shooting, but cannot charge this turn.'),
     ]),

    ('Aeldari Wave Serpent', 125,
     stat('14"', 9, '3+', 13, '7+', 2, invuln='5+'),
     [
         rng('Twin Shuriken Cannon', '24"', 3, '3+', 6, -1, 2, 'Lethal Hits, Twin-Linked'),
         rng('Twin Shuriken Catapult', '18"', 2, '3+', 4, -1, 1, 'Assault, Twin-Linked'),
         mel('Wraithbone Hull', 3, '4+', 6, 0, 1),
     ],
     [
         ability('Invulnerable Save (5+)', 'This model has a 5+ invulnerable save.'),
         ability('Wave Serpent Shield', 'Each time a ranged attack targets this model, if the Strength of that attack is greater than this model\'s Toughness, subtract 1 from the Wound roll.'),
         ability('Damaged: 1-4 wounds remaining', 'While this model has 1-4 wounds remaining, subtract 1 from Hit rolls.'),
     ]),

    ('Aeldari Wraithguard', 160,
     stat('6"', 6, '2+', 3, '8+', 1),
     [
         rng('Wraithcannon (x5)', '18"', 1, '4+', 14, -4, 'D6+1'),
         mel('Close Combat Weapon (x5)', 3, '4+', 5, 0, 1),
     ],
     [
         ability('War Construct', 'This unit is eligible to shoot in a turn in which it Fell Back.'),
         ability('Psychic Guidance', 'While within 12" of a friendly Aeldari Psyker, models in this unit have a Leadership of 6+.'),
     ]),

    ('Corsair Voidreavers', 65,
     stat('7"', 3, '4+', 1, '7+', 2),
     [
         rng('Shuriken Pistol', '12"', 1, '3+', 4, -1, 1, 'Assault, Pistol'),
         rng('Shuriken Rifle (x4)', '24"', 1, '3+', 4, -1, 1, 'Assault, Rapid Fire 1'),
         mel('Close Combat Weapon (x5)', 2, '3+', 3, 0, 1),
         mel('Power Sword', 2, '3+', 4, -2, 1),
     ],
     [
         ability('Reavers of the Void', 'Each time a model in this unit makes an attack, re-roll a Hit roll of 1.'),
         ability('Battle Focus', 'In your Shooting phase, this unit can make a Normal move after shooting, but cannot charge this turn.'),
     ]),

    ('Corsair Skyreavers', 75,
     stat('12"', 3, '5+', 1, '7+', 1),
     [
         rng('Shuriken Pistol (x5)', '12"', 1, '3+', 4, -1, 1, 'Assault, Pistol'),
         mel('Corsair Blade (x5)', 3, '3+', 4, -2, 1),
     ],
     [
         ability('Raid and Run', 'At the end of the Fight phase, if this unit was eligible to fight this phase and is not within Engagement Range of enemy units, it can make a Normal move of up to 6".'),
         ability('Deep Strike', 'During the Declare Battle Formations step, you can set up this unit in Reserves.'),
     ]),

    ('Dark Reapers', 90,
     stat('6"', 3, '3+', 1, '6+', 1, invuln='5+'),
     [
         rng('Reaper Launcher - Starshot (x5)', '48"', 1, '3+', 10, -2, 3, 'Ignores Cover'),
         rng('Reaper Launcher - Starswarm (x5)', '48"', 2, '3+', 5, -2, 1, 'Ignores Cover'),
         mel('Close combat weapon (x5)', 2, '3+', 3, 0, 1),
     ],
     [
         ability('Invulnerable Save (5+)', 'This unit has a 5+ invulnerable save.'),
         ability('Inescapable Accuracy', 'Each time a model in this unit makes a ranged attack, the target does not receive the benefits of Light Cover.'),
     ]),

    ('Guardian Defenders', 100,
     stat('7"', 3, '4+', 1, '7+', 2),
     [
         rng('Shuriken Catapult (x10)', '18"', 2, '3+', 4, -1, 1, 'Assault'),
         rng('Shuriken Cannon', '24"', 3, '3+', 6, -1, 2, 'Lethal Hits'),
         mel('Close Combat Weapon (x11)', 1, '3+', 3, 0, 1),
     ],
     [
         ability('Fleet of Foot', 'This unit can perform the Fade Back Agile Manoeuvre without spending a Battle Focus token.'),
         ability('Battle Focus', 'In your Shooting phase, this unit can make a Normal move after shooting, but cannot charge this turn.'),
     ]),

    ('Harlequin Troupe', 85,
     stat('8"', 3, '6+', 1, '6+', 1, invuln='4+'),
     [
         rng('Shuriken Pistol (x5)', '12"', 1, '3+', 4, -1, 1, 'Assault, Pistol'),
         mel('Harlequin\'s Blade (x5)', 5, '3+', 3, -1, 1, 'Devastating Wounds'),
     ],
     [
         ability('Invulnerable Save (4+)', 'This unit has a 4+ invulnerable save.'),
         ability('Dance of Death', 'At the start of the Fight phase, select Hero\'s Prowess (re-roll Hit rolls of 1), Villain\'s Doom (add 1 to Wound rolls), or Trickster\'s Grace (subtract 1 from Hit rolls targeting this unit).'),
     ]),

    ('Howling Banshees', 95,
     stat('8"', 3, '4+', 1, '6+', 1, invuln='5+'),
     [
         rng('Shuriken Pistol (x5)', '12"', 1, '3+', 4, -1, 1, 'Assault, Pistol'),
         mel('Banshee Blade (x5)', 2, '2+', 4, -2, 2, 'Anti-Infantry 3+'),
     ],
     [
         ability('Invulnerable Save (5+)', 'This unit has a 5+ invulnerable save (4+ against melee attacks).'),
         ability('Acrobatic', 'This unit is eligible to declare a charge in a turn in which it Advanced.'),
         ability('Piercing Strikes', 'Melee weapons equipped by models in this unit have the [FIGHTS FIRST] ability.'),
     ]),

    ('Rangers', 55,
     stat('7"', 3, '5+', 1, '7+', 1, invuln='5+'),
     [
         rng('Long Rifle (x5)', '36"', 1, '3+', 4, -1, 2, 'Heavy, Precision'),
         rng('Shuriken Pistol (x5)', '12"', 1, '2+', 4, -1, 1, 'Assault, Pistol'),
         mel('Close Combat Weapon (x5)', 1, '3+', 3, 0, 1),
     ],
     [
         ability('Invulnerable Save (5+, ranged only)', 'Models in this unit have a 5+ invulnerable save against ranged attacks only.'),
         ability('Path of the Outcast', 'Once per turn, when an enemy unit ends a Normal, Advance, or Fall Back move within 9" of this unit, this unit can make a Normal move of up to 3".'),
     ]),

    ('Shining Spears', 110,
     stat('14"', 4, '3+', 2, '6+', 2, invuln='5+'),
     [
         rng('Twin Shuriken Catapult (x3)', '18"', 2, '3+', 4, -1, 1, 'Assault, Twin-Linked'),
         rng('Laser Lance (x3)', '6"', 1, '3+', 6, -2, 3, 'Assault'),
         mel('Laser Lance (x3)', 3, '3+', 5, -2, 3, 'Anti-Monster 3+, Anti-Vehicle 3+, Lance'),
     ],
     [
         ability('Invulnerable Save (5+)', 'This unit has a 5+ invulnerable save.'),
         ability('Extreme Mobility', 'Each time this unit makes a Normal move, it can move through other models.'),
     ]),

    ('Shroud Runners', 80,
     stat('14"', 4, '5+', 3, '7+', 2, invuln='5+'),
     [
         rng('Long Rifle (x3)', '36"', 1, '2+', 4, -1, 2, 'Precision'),
         rng('Scatter Laser (x3)', '36"', 6, '3+', 5, 0, 1, 'Sustained Hits 1'),
         mel('Close Combat Weapon (x3)', 1, '3+', 3, 0, 1),
     ],
     [
         ability('Invulnerable Save (5+, ranged only)', 'Models have a 5+ invulnerable save against ranged attacks only.'),
         ability('Target Acquisition', 'Each time a model in this unit makes an attack with a Long Rifle, if that attack targets a Character, add 1 to the Hit roll.'),
         ability('Scouts 6"', 'This unit can move up to 6" before the first battle round.'),
     ]),

    ('Skyweavers', 95,
     stat('14"', 4, '4+', 3, '6+', 2, invuln='4+'),
     [
         rng('Shuriken Cannon (x2)', '24"', 3, '3+', 6, -1, 2, 'Lethal Hits'),
         rng('Star Bolas (x2)', '12"', 'D3', '3+', 7, -2, 2),
         mel('Close Combat Weapon (x2)', 4, '3+', 3, 0, 1),
     ],
     [
         ability('Invulnerable Save (4+)', 'This unit has a 4+ invulnerable save.'),
         ability('Acrobatic Grace', 'Each time an attack targets this unit, subtract 1 from the Hit roll.'),
     ]),

    ('Swooping Hawks', 95,
     stat('14"', 3, '4+', 1, '6+', 1, invuln='5+'),
     [
         rng('Hawk\'s Talon', '24"', 2, '3+', 6, -2, 2, 'Lethal Hits'),
         rng('Lasblaster (x4)', '24"', 4, '3+', 4, 0, 1, 'Assault, Lethal Hits'),
         mel('Close Combat Weapon (x5)', 2, '3+', 3, 0, 1),
     ],
     [
         ability('Invulnerable Save (5+)', 'This unit has a 5+ invulnerable save.'),
         ability('Grenade Pack Flyover', 'Once per turn, in your Movement phase, when this unit is selected to make a Normal move, one enemy unit it moves over suffers D3 mortal wounds.'),
         ability('Deep Strike', 'During the Declare Battle Formations step, you can set up this unit in Reserves.'),
     ]),

    ('Warp Spiders', 105,
     stat('12"', 3, '3+', 1, '6+', 1),
     [
         rng('Death Spinner (x4)', '12"', 'D6', 'N/A', 4, -1, 1, 'Ignores Cover, Torrent'),
         rng('Exarch\'s Deathspinner', '12"', 'D6', 'N/A', 6, -2, 1, 'Ignores Cover, Torrent'),
         mel('Close Combat Weapon (x5)', 2, '3+', 3, 0, 1),
     ],
     [
         ability('Flickerjump', 'In your Movement phase, each time this unit is selected to make a Normal move, it can use Flickerjump -- remove from the battlefield and set up anywhere more than 9" from enemy models.'),
         ability('Deep Strike', 'During the Declare Battle Formations step, you can set up this unit in Reserves.'),
     ]),

    ('Windriders', 80,
     stat('14"', 4, '4+', 2, '7+', 2),
     [
         rng('Twin Shuriken Catapult (x3)', '18"', 2, '3+', 4, -1, 1, 'Assault, Twin-Linked'),
         mel('Close Combat Weapon (x3)', 3, '3+', 3, 0, 1),
     ],
     [
         ability('Swift Demise', 'Each time a model in this unit makes a ranged attack, re-roll a Hit roll of 1. If the target is the closest eligible target, you can re-roll the entire Hit roll.'),
         ability('Battle Focus', 'In your Shooting phase, this unit can make a Normal move after shooting, but cannot charge this turn.'),
     ]),

    ('Wraithblades', 150,
     stat('6"', 6, '2+', 3, '8+', 1),
     [
         mel('Ghostswords (x5)', 5, '4+', 5, -2, 2),
     ],
     [
         ability('Malevolent Souls', 'Each time a model in this unit is destroyed by a melee attack, if that model has not fought this phase, roll one D6. On a 3+, that destroyed model can fight after the attacking unit finishes making its attacks.'),
         ability('War Construct', 'This unit is eligible to shoot in a turn in which it Fell Back.'),
     ]),

    ('Wraithguard', 160,
     stat('6"', 6, '2+', 3, '8+', 1),
     [
         rng('Wraithcannon (x5)', '18"', 1, '4+', 14, -4, 'D6+1'),
         mel('Close Combat Weapon (x5)', 3, '4+', 5, 0, 1),
     ],
     [
         ability('War Construct', 'This unit is eligible to shoot in a turn in which it Fell Back.'),
         ability('Psychic Guidance', 'While within 12" of a friendly Aeldari Psyker, models in this unit have Leadership 6+.'),
     ]),

    # -- Vehicles / Monsters --------------------------------------------------

    ('Crimson Hunter', 160,
     stat('20+"', 8, '3+', 12, '6+', 0),
     [
         rng('Pulse Laser', '48"', 3, '3+', 9, -2, 'D6'),
         rng('Starcannon (x2)', '36"', 2, '3+', 8, -3, 2),
         mel('Wraithbone Hull', 3, '4+', 6, 0, 1),
     ],
     [
         ability('Skyhunter', 'Each time this model makes a ranged attack targeting a unit that can Fly, add 1 to the Hit roll and add 1 to the Wound roll.'),
         ability('Damaged: 1-4 wounds remaining', 'While this model has 1-4 wounds remaining, subtract 1 from Hit rolls.'),
     ]),

    ('Fire Prism', 150,
     stat('14"', 9, '3+', 12, '7+', 3),
     [
         rng('Prism Cannon - Dispersed Pulse', '60"', '2D6', '3+', 6, -2, 2, 'Blast'),
         rng('Prism Cannon - Focused Lances', '60"', 2, '3+', 18, -4, 6, 'Linked Fire'),
         rng('Twin Shuriken Catapult', '18"', 2, '3+', 4, -1, 1, 'Assault, Twin-Linked'),
         mel('Wraithbone Hull', 3, '4+', 6, 0, 1),
     ],
     [
         ability('Linked Fire', 'In your Shooting phase, after this model has shot, one other friendly Fire Prism within 18" can combine its fire -- add 1 to Strength, AP, and Damage of the first Fire Prism\'s next Prism Cannon attack.'),
         ability('Damaged: 1-4 wounds remaining', 'While this model has 1-4 wounds remaining, subtract 1 from Hit rolls.'),
     ]),

    ('Hemlock Wraithfighter', 155,
     stat('20+"', 8, '3+', 12, '6+', 0),
     [
         rng('Heavy D-Scythe (x2)', '18"', 'D6', '4+', 12, -4, 2, 'Blast'),
         mel('Wraithbone Hull', 3, '4+', 6, 0, 1),
     ],
     [
         ability('Mindshock Pod (Aura, Psychic)', 'While an enemy unit is within 9" of this model, subtract 1 from Battle-shock and Leadership tests taken for that unit.'),
         ability('Damaged: 1-4 wounds remaining', 'While this model has 1-4 wounds remaining, subtract 1 from Hit rolls.'),
     ]),

    ('Night Spinner', 190,
     stat('14"', 9, '3+', 12, '7+', 3),
     [
         rng('Doomweaver', '48"', 'D6+3', '3+', 7, -1, 2, 'Blast, Indirect Fire, Twin-Linked'),
         rng('Twin Shuriken Catapult', '18"', 2, '3+', 4, -1, 1, 'Assault, Twin-Linked'),
         mel('Wraithbone Hull', 3, '4+', 6, 0, 1),
     ],
     [
         ability('Monofilament Snare', 'After this model shoots with its Doomweaver, select one enemy unit hit -- that unit\'s Move characteristic is reduced by D6" until the end of the turn.'),
         ability('Damaged: 1-4 wounds remaining', 'While this model has 1-4 wounds remaining, subtract 1 from Hit rolls.'),
     ]),

    ('Starfang', 75,
     stat('14"', 6, '3+', 6, '7+', 2),
     [
         rng('Disintegrator Cannon', '36"', 3, '3+', 6, -3, 2, 'Assault'),
         rng('Starfang Grenade Launcher', '36"', 'D3', '3+', 6, -3, 2, 'Assault, Blast'),
         mel('Wraithbone Hull', 3, '4+', 6, 0, 1),
     ],
     [
         ability('Hallucinogen Grenades', 'At the start of your opponent\'s Shooting phase, select one Aeldari Infantry unit from your army visible to this model -- until the end of the phase, ranged attacks cannot target that unit.'),
     ]),

    ('Starweaver', 80,
     stat('14"', 6, '4+', 6, '6+', 2, invuln='4+'),
     [
         rng('Shuriken Cannon (x2)', '24"', 3, '3+', 6, -1, 2, 'Lethal Hits'),
         mel('Close Combat Weapon', 4, '3+', 3, 0, 1),
     ],
     [
         ability('Invulnerable Save (4+)', 'This model has a 4+ invulnerable save.'),
         ability('Rapid Embarkation', 'At the end of the Fight phase, if no models are embarked within this Transport, select one friendly Harlequins Infantry unit within 3" -- it can embark.'),
     ]),

    ('Voidweaver', 125,
     stat('14"', 6, '4+', 6, '6+', 2, invuln='4+'),
     [
         rng('Shuriken Cannon (x2)', '24"', 3, '3+', 6, -1, 2, 'Lethal Hits'),
         rng('Voidweaver Haywire Cannon', '24"', 3, '3+', 4, -1, 3, 'Anti-Vehicle 4+, Devastating Wounds'),
         mel('Close Combat Weapon', 4, '3+', 3, 0, 1),
     ],
     [
         ability('Invulnerable Save (4+)', 'This unit has a 4+ invulnerable save.'),
         ability('Polychromatic Camouflage', 'This unit can only be selected as the target of a ranged attack if the attacking model is within 18".'),
     ]),

    ('Vyper', 75,
     stat('14"', 6, '3+', 6, '7+', 2),
     [
         rng('Bright Lance', '48"', 1, '3+', 12, -3, 'D6+2'),
         rng('Shuriken Cannon', '24"', 3, '3+', 6, -1, 2, 'Lethal Hits'),
         mel('Wraithbone Hull', 3, '4+', 6, 0, 1),
     ],
     [
         ability('Harassment Fire', 'In your Shooting phase, after this unit has shot, select one enemy unit hit -- until the start of your next turn, that unit is suppressed (cannot use Overwatch).'),
     ]),

    ('War Walkers', 85,
     stat('10"', 7, '3+', 6, '7+', 2, invuln='5+'),
     [
         rng('Shuriken Cannon (x2)', '24"', 3, '3+', 6, -1, 2, 'Lethal Hits'),
         mel('War Walker Feet', 3, '3+', 5, 0, 1),
     ],
     [
         ability('Invulnerable Save (5+)', 'This model has a 5+ invulnerable save.'),
         ability('Crystalline Targeting', 'After this unit has shot, select one enemy unit hit -- until the end of the phase, each time a friendly Aeldari model makes an attack targeting that unit, re-roll a Hit roll of 1.'),
     ]),

    ('Wraithknight', 435,
     stat('12"', 12, '2+', 18, '6+', 10),
     [
         rng('Suncannon', '48"', 'D6+4', '3+', 10, -3, 3, 'Blast'),
         mel('Titanic Feet', 5, '3+', 8, -1, 2),
         mel('Titanic Ghostglaive - Strike', 5, '3+', 16, -3, 6),
         mel('Titanic Ghostglaive - Sweep', 15, '3+', 8, -2, 2),
     ],
     [
         ability('Titanic Strides', 'This model can move through models and terrain features 4" or less in height.'),
         ability('Damaged: 1-6 wounds remaining', 'While this model has 1-6 wounds remaining, subtract 5 from OC and subtract 1 from Hit rolls.'),
         ability('Scattershield', 'The bearer has a 4+ invulnerable save and subtract 1 from Damage of attacks allocated to the bearer.'),
     ]),

    ('Wraithlord', 130,
     stat('8"', 10, '2+', 10, '8+', 3),
     [
         rng('Shuriken Catapult (x2)', '18"', 2, '4+', 4, -1, 1, 'Assault'),
         mel('Wraithbone Fists', 4, '4+', 7, -2, 2),
     ],
     [
         ability('Fated Hero', 'At the start of the battle, select one keyword: Infantry, Monster, Mounted, or Vehicle. Each time this model makes an attack targeting a unit with that keyword, re-roll a Hit roll of 1.'),
         ability('War Construct', 'This unit is eligible to shoot in a turn in which it Fell Back.'),
     ]),

    # -- Skipped entries (no stats) -------------------------------------------

    ('Codex: Aeldari', 0,
     stat('', None, '', None, '', None),
     [],
     []),

    ('Support Weapon', 0,
     stat('', None, '', None, '', None),
     [],
     []),

    ('Aeldari Combat Patrol', 395,
     stat('', None, '', None, '', None),
     [],
     []),

    ('Combat Patrol: Aeldari Corsairs', 455,
     stat('', None, '', None, '', None),
     [],
     []),
]


class Command(BaseCommand):
    """Seed Aeldari stat lines, weapon profiles, and abilities."""

    help = 'Seed Aeldari unit stats, weapons, and abilities.'

    def add_arguments(self, parser):
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
                    unit = UnitType.objects.get(name=db_name)
                except UnitType.DoesNotExist:
                    self.stdout.write(self.style.WARNING(f'  SKIP (not found): {db_name}'))
                    skipped += 1
                    continue

                if dry_run:
                    self.stdout.write(f'  DRY-RUN: would update {db_name!r} -> {pts}pts')
                    continue

                # Update points and stat line
                update_fields = {'points_cost': pts, **stats}
                for field, val in update_fields.items():
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
            f'\nDone. {updated} units updated, {skipped} skipped.'
        ))
