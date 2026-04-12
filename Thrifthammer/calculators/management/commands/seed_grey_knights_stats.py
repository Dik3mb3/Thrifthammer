"""
Management command: seed_grey_knights_stats

Seeds points costs, stat lines, weapon profiles, and unit abilities
for all Grey Knights units in the database. Safe to re-run — uses
delete+create for weapons/abilities and direct field writes for stats.

Usage:
    python manage.py seed_grey_knights_stats
    python manage.py seed_grey_knights_stats --dry-run
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

GREY_KNIGHTS_UNITS = [

    # -- Epic Heroes / Characters ---------------------------------------------

    ('Castellan Crowe', 90,
     stat('6"', 4, '2+', 5, '6+', 1, invuln='4+'),
     [
         rng('Purifying Flame', '18"', '3', '2+', 4, -2, 1,
             'Anti-Infantry 2+, Ignores Cover, Psychic'),
         rng('Storm bolter', '24"', '2', '2+', 4, 0, 1, 'Rapid Fire 2'),
         mel('Black Blade of Antwyr', '5', '2+', 6, -2, 2,
             'Devastating Wounds, Precision'),
     ],
     [
         ability('Leader',
                 'This model can be attached to the following unit:\n'
                 '■ Purifier Squad'),
         ability('Champion of the Order of Purifiers (Psychic)',
                 'While this model is leading a unit, add 1 to the Attacks '
                 'characteristic of Purifying Flame weapons equipped by that '
                 'unit.'),
         ability('Foesight (Psychic)',
                 'Each time this model makes an attack that targets a Character '
                 'unit, you can re-roll the Hit roll.'),
     ]),

    ('Grey Knights Grand Master Voldus', 110,
     stat('5"', 5, '2+', 7, '6+', 1, invuln='4+'),
     [
         rng('Searing Purity', '12"', 'D3+1', '2+', 12, -2, 2,
             'Devastating Wounds, Psychic'),
         rng('Storm bolter', '24"', '2', '2+', 4, 0, 1, 'Rapid Fire 2'),
         mel('Malleus Argyrum', '5', '2+', 10, -2, 3, 'Psychic'),
     ],
     [
         ability('Leader',
                 'This model can be attached to the following units:\n'
                 '■ Brotherhood Terminator Squad\n'
                 '■ Paladin Squad'),
         ability('Sanctuary (Psychic)',
                 'While this model is leading a unit, each time an attack '
                 'targets that unit, subtract 1 from the Hit roll.'),
         ability('Hammer Aflame (Psychic)',
                 'Each time this model\'s unit is selected to fight, you can '
                 'select one enemy unit within Engagement Range of this model\'s '
                 'unit and roll one D6: on a 2-3, that enemy unit suffers 1 '
                 'mortal wound; on a 4-5, that enemy unit suffers D3 mortal '
                 'wounds; on a 6+, that enemy unit suffers D3+3 mortal wounds.'),
     ]),

    ('Grand Master in Nemesis Dreadknight', 225,
     stat('8"', 8, '2+', 13, '6+', 4, invuln='4+'),
     [
         mel('Dreadfists', '6', '2+', 6, -1, 1),
     ],
     [
         ability('Surge of Wrath (Psychic)',
                 'Each time this model makes a melee attack that targets a '
                 'Monster or Vehicle unit, you can re-roll the Hit roll, you '
                 'can re-roll the Wound roll and you can re-roll the Damage '
                 'roll.'),
         ability('Warrior Strategist',
                 'Once per battle round, one unit from your army with this '
                 'ability can use it when its unit is targeted with a Stratagem. '
                 'If it does, reduce the CP cost of that use of that Stratagem '
                 'by 1CP.'),
         ability('Damaged: 1-4 Wounds Remaining',
                 'While this model has 1-4 wounds remaining, each time this '
                 'model makes an attack, subtract 1 from the Hit roll.'),
     ]),

    # -- Infantry -------------------------------------------------------------

    ('Grey Knights Strike Squad', 120,
     stat('6"', 4, '2+', 2, '6+', 2),
     [
         rng('Storm bolter (x5)', '24"', '2', '3+', 4, 0, 1, 'Rapid Fire 2'),
         mel('Nemesis force weapon (x5)', '3', '3+', 6, -2, 2, 'Psychic'),
     ],
     [
         ability('Sanctifying Ritual (Psychic)',
                 'At the end of your Command phase, if this unit is within '
                 'range of an objective marker that you control, that objective '
                 'marker remains under your control until your opponent\'s Level '
                 'of Control over that objective marker is greater than yours at '
                 'the end of a phase.'),
     ]),

    ('Grey Knights Interceptor Squad', 125,
     stat('12"', 4, '2+', 2, '6+', 1),
     [
         rng('Storm bolter (x5)', '24"', '2', '3+', 4, 0, 1, 'Rapid Fire 2'),
         mel('Nemesis force weapon (x5)', '3', '3+', 6, -2, 2, 'Psychic'),
     ],
     [
         ability('Personal Teleporters',
                 'In your Shooting phase, after this unit has shot, if it is '
                 'not within Engagement Range of one or more enemy units, it '
                 'can make a Normal move of up to 6" as if it were your '
                 'Movement phase. If it does, until the end of the turn, this '
                 'unit is not eligible to declare a charge.'),
     ]),

    ('Grey Knights Purifier Squad', 125,
     stat('6"', 4, '2+', 2, '6+', 1),
     [
         rng('Purifying Flame (x5)', '18"', '1', '3+', 4, -2, 1,
             'Anti-Infantry 2+, Ignores Cover, Psychic'),
         rng('Storm bolter (x5)', '24"', '2', '3+', 4, 0, 1, 'Rapid Fire 2'),
         mel('Nemesis force weapon (x5)', '3', '3+', 6, -2, 2, 'Psychic'),
     ],
     [
         ability('Sanctity of Purpose',
                 'Each time a model in this unit makes an attack, re-roll a '
                 'Wound roll of 1. If the target is within range of an objective '
                 'marker, you can re-roll the Wound roll instead.'),
     ]),

    ('Grey Knights Purgation Squad', 115,
     stat('6"', 4, '2+', 2, '6+', 1),
     [
         rng('Storm bolter (x5)', '24"', '2', '3+', 4, 0, 1, 'Rapid Fire 2'),
         mel('Nemesis force weapon (x5)', '3', '3+', 6, -2, 2, 'Psychic'),
     ],
     [
         ability('Righteous Persecution',
                 'In your Shooting phase, after this unit has shot, select one '
                 'enemy unit (excluding Monsters or Vehicles) hit by one or '
                 'more of those attacks; until the start of your next turn, that '
                 'enemy unit is pinned. While a unit is pinned, subtract 2 from '
                 "that unit's Move characteristic and subtract 2 from Charge "
                 'rolls made for it.'),
     ]),

    # -- Elites ---------------------------------------------------------------

    ('Grey Knights Terminators', 150,
     stat('5"', 5, '2+', 3, '6+', 2, invuln='4+'),
     [
         rng('Storm bolter (x4)', '24"', '2', '3+', 4, 0, 1, 'Rapid Fire 2'),
         mel('Nemesis force weapon (x4)', '4', '3+', 6, -2, 2, 'Psychic'),
     ],
     [
         ability('Force Edge (Psychic)',
                 'Each time a model in this unit makes a melee attack that '
                 'targets a unit (excluding Vehicles or Monsters), improve the '
                 'Armour Penetration characteristic of that attack by 1.'),
     ]),

    ('Grey Knights Paladins', 180,
     stat('5"', 5, '2+', 3, '6+', 1, invuln='4+'),
     [
         rng('Storm bolter (x4)', '24"', '2', '2+', 4, 0, 1, 'Rapid Fire 2'),
         mel('Nemesis force weapon (x4)', '4', '2+', 6, -2, 2, 'Psychic'),
     ],
     [
         ability('Attuned Onslaught (Psychic)',
                 'Each time this unit makes a Charge move, until the end of the '
                 'turn, add 1 to the Damage characteristic of melee weapons '
                 'equipped by Paladin Squad models in this unit.'),
     ]),

    # -- Vehicles / Walker ---------------------------------------------------

    ('Grey Knights Dreadknight', 210,
     stat('8"', 8, '2+', 13, '6+', 4, invuln='4+'),
     [
         mel('Dreadfists', '6', '2+', 6, -1, 1),
     ],
     [
         ability('Indomitable Spirit (Psychic)',
                 'This model is eligible to shoot and declare a charge in a '
                 'turn in which it Advanced or Fell Back.'),
         ability('Damaged: 1-4 Wounds Remaining',
                 'While this model has 1-4 wounds remaining, each time this '
                 'model makes an attack, subtract 1 from the Hit roll.'),
     ]),
]


class Command(BaseCommand):
    """Seed Grey Knights stat lines, weapon profiles, and abilities."""

    help = 'Seed Grey Knights unit stats, weapons, and abilities.'

    def add_arguments(self, parser):
        """Add --dry-run flag."""
        parser.add_argument(
            '--dry-run', action='store_true',
            help='Preview changes without writing to the database.',
        )

    def handle(self, *args, **options):
        """Iterate over GREY_KNIGHTS_UNITS and upsert stats, weapons, and abilities."""
        dry_run = options['dry_run']
        updated = 0
        skipped = 0

        with transaction.atomic():
            for db_name, pts, stats, weapons, abilities in GREY_KNIGHTS_UNITS:
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
