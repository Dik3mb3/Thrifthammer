"""
Management command: seed_sisters_of_battle_stats

Seeds points costs, stat lines, weapon profiles, and unit abilities
for Sisters of Battle (Adepta Sororitas) units in the database. Safe
to re-run — uses delete+create for weapons/abilities and direct field
writes for stats.

Usage:
    python manage.py seed_sisters_of_battle_stats
    python manage.py seed_sisters_of_battle_stats --dry-run
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

SISTERS_UNITS = [

    # -- Characters -----------------------------------------------------------

    ('Adepta Sororitas Morvenn Vahl', 185,
     stat('8"', 7, '2+', 8, '6+', 3),
     [
         rng('Fidelis', '36"', 3, '2+', 6, -1, 2, 'Sustained Hits 1'),
         rng('Paragon missile launcher - prioris', '36"', 2, '2+', 9, -2, 'D6'),
         rng('Paragon missile launcher - sanctorum', '36"', '2D6', '2+', 4, 0, 1,
             'Blast'),
         mel('Lance of Illumination - strike', 5, '2+', 8, -2, 3,
             'Devastating Wounds'),
         mel('Lance of Illumination - sweep', 10, '2+', 5, -1, 1,
             'Devastating Wounds'),
     ],
     [
         ability('Leader',
                 'This model can be attached to the following unit:\n'
                 '\u25a0 Paragon Warsuits'),
     ]),

    # -- Infantry -------------------------------------------------------------

    ('Adepta Sororitas Battle Sisters Squad', 105,
     stat('6"', 3, '3+', 1, '7+', 2, invuln='6+'),
     [
         rng('Bolt pistol (x10)', '12"', 1, '3+', 4, 0, 1, 'Pistol'),
         rng('Boltgun (x10)', '24"', 1, '3+', 4, 0, 1, 'Rapid Fire 1'),
         mel('Close combat weapon (x10)', 1, '4+', 3, 0, 1),
     ],
     [
         ability('Defenders of the Faith',
                 'At the end of your Command phase, if this unit is within range '
                 'of an objective marker you control, that objective marker remains '
                 'under your control, even if you have no models within range of it, '
                 'until your opponent controls it at the start or end of any turn.'),
         ability('Cherub',
                 'Once per battle, after this unit has performed an Act of Faith, '
                 'you gain 1 Miracle dice.'),
     ]),

    ('Adepta Sororitas Celestian Sacresants', 70,
     stat('6"', 3, '3+', 1, '7+', 1, invuln='4+'),
     [
         rng('Bolt pistol (x5)', '12"', 1, '3+', 4, 0, 1, 'Pistol'),
         mel('Hallowed Mace (x5)', 3, '3+', 4, -1, 2, 'Lethal Hits'),
     ],
     [
         ability('Sworn Protectors',
                 'While an Adepta Sororitas Character is leading this unit, each '
                 'time an attack targets this unit, subtract 1 from the Wound roll.'),
     ]),

    ('Adepta Sororitas Retributor Squad', 120,
     stat('6"', 3, '3+', 1, '7+', 1, invuln='6+'),
     [
         rng('Bolt pistol (x5)', '12"', 1, '3+', 4, 0, 1, 'Pistol'),
         rng('Boltgun', '24"', 1, '3+', 4, 0, 1, 'Rapid Fire 1'),
         rng('Heavy bolter (x4)', '36"', 3, '4+', 5, -1, 2,
             'Heavy, Sustained Hits 1'),
         mel('Close combat weapon (x5)', 1, '4+', 3, 0, 1),
     ],
     [
         ability('Cherubs',
                 'Twice per battle, after this unit has performed an Act of Faith, '
                 'you gain 1 Miracle dice.'),
         ability('Storm of Retribution',
                 'Each time a model in this unit makes a ranged attack, re-roll a '
                 'Hit roll of 1 and re-roll a Wound roll of 1. If such an attack '
                 'targets an enemy unit that has destroyed one or more Adepta '
                 'Sororitas units from your army during the battle, add 1 to the '
                 'Hit roll and add 1 to the Wound roll as well.'),
     ]),

    ('Adepta Sororitas Seraphim Squad', 80,
     stat('12"', 3, '3+', 1, '7+', 1, invuln='5+'),
     [
         rng('Bolt pistol (x10)', '12"', 1, '3+', 4, 0, 1, 'Pistol'),
         mel('Close combat weapon (x5)', 2, '3+', 3, 0, 1),
     ],
     [
         ability('Angelic Ascent',
                 'In your Shooting phase, after this unit has shot, if it is not '
                 'within Engagement Range of any enemy units, it can make a Normal '
                 'move of up to 6". If it does, until the end of the turn, this '
                 'unit is not eligible to declare a charge.'),
     ]),

    # -- Vehicles -------------------------------------------------------------

    ('Adepta Sororitas Immolator', 115,
     stat('12"', 10, '3+', 11, '7+', 2, invuln='6+'),
     [
         rng('Heavy Bolter', '36"', 3, '3+', 5, -1, 2, 'Sustained Hits 1'),
         rng('Immolation Flamers', '18"', '2D6', 'N/A', 6, -1, 1,
             'Ignores Cover, Torrent'),
         mel('Armoured tracks', 3, '4+', 6, 0, 1),
     ],
     [
         ability('Transport',
                 'This model has a transport capacity of 6 ADEPTA SORORITAS '
                 'INFANTRY models. It cannot transport JUMP PACK models or the '
                 'Triumph of Saint Katherine.'),
         ability('Purge and Cleanse',
                 'In your Shooting phase, after this model has shot, select one '
                 'enemy unit hit by one or more of those attacks. Until the end of '
                 'the phase, that enemy unit cannot have the Benefit of Cover.'),
     ]),

    ('Adepta Sororitas Exorcist', 210,
     stat('10"', 10, '3+', 11, '7+', 3, invuln='6+'),
     [
         rng('Heavy Bolter', '36"', 3, '3+', 5, -1, 2, 'Sustained Hits 1'),
         rng('Exorcist Missile Launcher', '36"', 'D6+2', '3+', 10, -3, 'D6',
             'Indirect Fire'),
         mel('Armoured tracks', 3, '4+', 6, 0, 1),
     ],
     [
         ability('Damaged: 1-4 Wounds Remaining',
                 'While this model has 1-4 wounds remaining, each time this model '
                 'makes an attack, subtract 1 from the Hit roll.'),
         ability('Devastating Refrain',
                 'In your Shooting phase, after this model has shot, if one or more '
                 'of those attacks made with an Indirect Fire weapon scored a hit '
                 'against an enemy unit, that unit must take a Battle-shock test. '
                 'Each time such an attack destroys an enemy model that has the '
                 'Deadly Demise ability, the model\'s Deadly Demise ability inflicts '
                 'mortal wounds on a D6 roll of 5+ instead of a 6.'),
     ]),
]


# -- Command ------------------------------------------------------------------

class Command(BaseCommand):
    """Seed Sisters of Battle unit stats, weapons, and abilities."""

    help = 'Seed Sisters of Battle stat data into the army calculator'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run', action='store_true',
            help='Preview changes without writing to the database.',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        updated = skipped = 0

        with transaction.atomic():
            for db_name, points, stats, weapons, abilities in SISTERS_UNITS:
                try:
                    unit = UnitType.objects.get(name=db_name)
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
                    WeaponProfile.objects.create(unit=unit, order=order, **wp)

                # Replace abilities
                unit.abilities.all().delete()
                for order, ab in enumerate(abilities):
                    UnitAbility.objects.create(
                        unit=unit, order=order,
                        name=ab['name'], description=ab['description'],
                    )

                self.stdout.write(f'  OK: {db_name}')
                updated += 1

            if dry_run:
                transaction.set_rollback(True)

        self.stdout.write(
            self.style.SUCCESS(
                f'\nSisters of Battle seed complete: '
                f'{updated} updated, {skipped} skipped.'
            )
        )
