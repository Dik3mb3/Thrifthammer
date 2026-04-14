"""
Management command: seed_tau_stats

Seeds points costs, stat lines, weapon profiles, and unit abilities
for T'au Empire units in the database. Safe to re-run — uses
delete+create for weapons/abilities and direct field writes for stats.

Mapped units (8 products → 8 UnitTypes):
  T'au Broadside Battlesuit, T'au Crisis Battlesuits (Fireknife loadout),
  T'au Ethereal, T'au Fire Warriors (Strike Team loadout),
  T'au Hammerhead Gunship, T'au Pathfinders,
  T'au Riptide Battlesuit, T'au Stealth Battlesuits

Usage:
    python manage.py seed_tau_stats
    python manage.py seed_tau_stats --dry-run
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
# Weapon/ability text sourced from parsed New Recruit HTML (2026-04-13).
# Where multiple datasheet variants share one product, the standard/most
# common loadout is used (Fireknife for Crisis, Strike Team for Fire Warriors).

TAU_UNITS = [

    # -- Battlesuits (Heavy) --------------------------------------------------

    ("T'au Broadside Battlesuit", 80,
     stat('5"', 6, '2+', 8, '7+', 2),
     [
         rng('Heavy rail rifle', '60"', 2, '4+', 12, -4, 'D6+1',
             'Heavy, Devastating Wounds'),
         mel('Crushing bulk', 3, '5+', 6, 0, 1),
     ],
     [
         ability('Advanced Armour Plating',
                 'Each time an attack is allocated to this model, if the Damage '
                 'characteristic of that attack is 1, that attack has a Damage '
                 'characteristic of 0.'),
     ]),

    # -- Crisis Battlesuits: Fireknife loadout (120pts) is used as the
    #    representative entry since all 3 configurations share one product box.

    ("T'au Crisis Battlesuits", 120,
     stat('10"', 5, '3+', 4, '7+', 2),
     [
         rng('Missile pod (x3)', '30"', 2, '4+', 7, -1, 2),
         rng('Plasma rifle (x3)', '18"', 1, '4+', 8, -3, 3),
         mel('Battlesuit fists (x3)', 3, '5+', 5, 0, 1),
     ],
     [
         ability('Fireknife',
                 'Each time a model in this unit makes a ranged attack, '
                 're-roll a Hit roll of 1.'),
         ability('Weapon Support System',
                 'Each time a model in this unit makes a ranged attack, '
                 'ignore any or all modifiers to the Hit roll.'),
     ]),

    # -- Characters -----------------------------------------------------------

    ("T'au Ethereal", 50,
     stat('6"', 3, '5+', 3, '6+', 1),
     [
         mel('Honour stave', 2, '4+', 5, 0, 1),
     ],
     [
         ability('Failure Is Not an Option',
                 'While a friendly T\'au Empire Infantry unit is within 6" of '
                 'this model, models in that unit have a 5+ Feel No Pain.'),
         ability('Leader',
                 'This model can be attached to the following units:\n'
                 '\u25a0 Breacher Team\n'
                 '\u25a0 Strike Team'),
     ]),

    # -- Infantry -------------------------------------------------------------

    # Fire Warriors: Strike Team loadout (70pts) used as the representative
    # entry; Breacher Team uses the same product box at 90pts.

    ("T'au Fire Warriors", 70,
     stat('6"', 3, '4+', 1, '7+', 2),
     [
         rng('Pulse pistol (x10)', '12"', 1, '4+', 5, 0, 1, 'Pistol'),
         rng('Pulse rifle (x10)', '30"', 1, '4+', 5, 0, 1, 'Rapid Fire 1'),
         rng('Support turret', '30"', 2, '5+', 5, 0, 1,
             'Indirect Fire, Twin-linked'),
         mel('Close combat weapon (x10)', 1, '5+', 3, 0, 1),
     ],
     [
         ability('Suppression Volley',
                 'Each time a model in this unit makes a ranged attack that '
                 'scores a hit against a unit, until the start of your next '
                 'turn, that unit is suppressed. While a unit is suppressed, '
                 'subtract 1 from Hit rolls made for models in that unit.'),
         ability('DS8 Support Turret',
                 'If this unit contains a Shas\'ui model and it Remains '
                 'Stationary, until the end of the turn, this unit is '
                 'equipped with one Support Turret weapon.'),
     ]),

    ("T'au Pathfinders", 90,
     stat('7"', 3, '4+', 1, '7+', 1),
     [
         rng('Pulse carbine (x10)', '20"', 2, '4+', 5, 0, 1),
         rng('Pulse pistol (x10)', '12"', 1, '4+', 5, 0, 1, 'Pistol'),
         mel('Close combat weapon (x10)', 1, '5+', 3, 0, 1),
     ],
     [
         ability('Target Uploaded',
                 'Each time a model in this unit makes a ranged attack that '
                 'targets a Spotted unit, improve the BS characteristic of '
                 'that attack by 1 and that attack has the [IGNORES COVER] '
                 'ability.'),
     ]),

    ("T'au Stealth Battlesuits", 100,
     stat('8"', 4, '3+', 2, '7+', 1),
     [
         rng('Burst cannon (x5)', '18"', 4, '4+', 5, 0, 1),
         mel('Battlesuit fists (x5)', 2, '5+', 4, 0, 1),
     ],
     [
         ability('Forward Observers',
                 'While a friendly T\'au Empire unit is being guided by a '
                 'model from this unit, each time a model in that unit makes '
                 'a ranged attack that targets their Spotted unit, re-roll a '
                 'Hit roll of 1.'),
         ability('Homing Beacon',
                 'Once per battle, at the start of your opponent\'s Charge '
                 'phase, one unit from your army can use the Rapid Ingress '
                 'Stratagem for 0CP, and when it arrives, it must be set up '
                 'within 6" of this unit.'),
     ]),

    # -- Vehicles -------------------------------------------------------------

    ("T'au Hammerhead Gunship", 145,
     stat('10"', 10, '3+', 14, '7+', 3),
     [
         rng('Railgun', '72"', 1, '4+', 20, -5, 'D6+6',
             'Heavy, Devastating Wounds'),
         rng('Twin pulse carbine (x2)', '20"', 2, '4+', 5, 0, 1,
             'Twin-linked'),
         mel('Armoured hull', 3, '5+', 6, 0, 1),
     ],
     [
         ability('Armour Hunter',
                 'Each time this model makes a ranged attack that targets a '
                 'MONSTER or VEHICLE unit, add 1 to the Hit roll.'),
         ability('Damaged: 1-5 Wounds Remaining',
                 'While this model has 1-5 wounds remaining, each time this '
                 'model makes an attack, subtract 1 from the Hit roll.'),
         ability('Targeting Array',
                 'Each time this model makes a ranged attack, you may re-roll '
                 'one Hit roll or one Wound roll.'),
     ]),

    ("T'au Riptide Battlesuit", 200,
     stat('10"', 9, '2+', 14, '7+', 4, invuln='4+'),
     [
         rng('Heavy burst cannon', '36"', 12, '4+', 6, -1, 2),
         rng('Twin plasma rifle', '18"', 1, '4+', 8, -3, 3, 'Twin-linked'),
         mel('Riptide fists', 6, '5+', 6, 0, 2),
     ],
     [
         ability('Nova Charge',
                 'Once per battle, at the start of your Shooting phase, you '
                 'can declare this model will Nova Charge. If you do, until '
                 'the end of the phase, one ranged weapon equipped by this '
                 'model has the [DEVASTATING WOUNDS] ability.'),
         ability('Damaged: 1-4 Wounds Remaining',
                 'While this model has 1-4 wounds remaining, each time this '
                 'model makes an attack, subtract 1 from the Hit roll.'),
         ability('Battlesuit Support System',
                 'If this model Fell Back this turn, it can still shoot in '
                 'the subsequent Shooting phase. If it does so, until the end '
                 'of the phase, its ranged weapons have the [ASSAULT] ability.'),
         ability('Weapon Support System',
                 'Each time this model makes a ranged attack, ignore any or '
                 'all modifiers to the Hit roll.'),
     ]),

]


# -- Command ------------------------------------------------------------------

class Command(BaseCommand):
    """Seed T'au Empire stat lines, weapons, and abilities."""

    help = "Seed T'au Empire unit stats, weapon profiles, and abilities."

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run', action='store_true',
            help='Preview changes without writing to the database.',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        updated = skipped = 0

        with transaction.atomic():
            for db_name, points, stats, weapons, abilities in TAU_UNITS:
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
                f"\nT'au Empire seed complete: "
                f'{updated} updated, {skipped} skipped.'
            )
        )
