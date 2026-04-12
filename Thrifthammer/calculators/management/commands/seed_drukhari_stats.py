"""
Management command: seed_drukhari_stats

Seeds points costs, stat lines, weapon profiles, and unit abilities
for all Drukhari units in the database. Safe to re-run — uses
delete+create for weapons/abilities and direct field writes for stats.

Usage:
    python manage.py seed_drukhari_stats
    python manage.py seed_drukhari_stats --dry-run
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

DRUKHARI_UNITS = [

    # -- Characters -----------------------------------------------------------

    ('Drukhari Archon', 80,
     stat('7"', 3, '4+', 4, '6+', 1, invuln='2+'),
     [
         rng('Splinter pistol', '12"', '1', '2+', 2, 0, 1,
             'Anti-Infantry 3+, Assault, Pistol'),
         mel('Huskblade', '4', '2+', 3, -2, 3, 'Devastating Wounds'),
     ],
     [
         ability('Leader',
                 'This model can be attached to the following units:\n'
                 '■ Hand of the Archon\n'
                 '■ Incubi\n'
                 '■ Kabalite Warriors'),
         ability('Overlord',
                 'Once per battle, at the start of any phase, you can select '
                 'one friendly Drukhari unit that is Battle-shocked and within '
                 '12" of this model. That unit is no longer Battle-shocked.'),
         ability('Devious Mastermind',
                 'Once per battle round, one model from your army with this '
                 'ability can use it when its unit is targeted with a stratagem. '
                 'If it does, reduce the CP cost of that use of that Stratagem '
                 'by 1CP.'),
         ability('Shadowfield',
                 'You cannot re-roll invulnerable saving throws made for the '
                 'bearer. The first time an invulnerable saving throw made for '
                 'the bearer is failed, until the end of the battle, the bearer '
                 'has no invulnerable save.'),
         ability('Hatred Eternal (Pain)',
                 'In your Shooting or the Fight phase, when you select this '
                 "model's unit to shoot or fight, you can spend 1 Pain token to "
                 'Empower that unit. While that unit is Empowered, each time a '
                 'model in that unit makes an attack, you can re-roll the Hit '
                 'roll.'),
     ]),

    # -- Battleline -----------------------------------------------------------

    ('Drukhari Kabalite Warriors', 115,
     stat('7"', 3, '4+', 1, '7+', 2, invuln='6+'),
     [
         rng('Splinter Rifle (x10)', '24"', '2', '3+', 2, 0, 1,
             'Anti-Infantry 3+, Assault'),
         mel('Close Combat Weapon (x10)', '2', '3+', 3, 0, 1),
     ],
     [
         ability('Cruel Enforcers',
                 'At the end of your Command phase, if this unit is within '
                 'range of an objective marker you control, that objective '
                 'marker remains under your control, until your opponent\'s '
                 'Level of Control over that objective marker is greater than '
                 'yours at the end of a phase.'),
         ability('Sadistic Raiders (Pain)',
                 'In your Shooting phase or the Fight phase, when you select '
                 'this unit to shoot or fight, you can spend 1 Pain token to '
                 'Empower this unit. While Empowered, each time a model in this '
                 'unit makes an attack, re-roll a Wound roll of 1. If the target '
                 'is within range of an objective marker, you can re-roll the '
                 'Wound roll instead.'),
     ]),

    ('Drukhari Wyches', 90,
     stat('8"', 3, '6+', 1, '7+', 2, invuln='6+ (4+ vs melee)'),
     [
         rng('Splinter Pistol (x10)', '12"', '1', '3+', 2, 0, 1,
             'Anti-Infantry 3+, Assault, Pistol'),
         mel('Hekatarii Blade (x10)', '4', '3+', 3, -1, 1),
     ],
     [
         ability('No Escape',
                 'Each time an enemy unit (excluding Monsters and Vehicles) '
                 'within Engagement Range of one or more units from your army '
                 'with this ability Falls Back, all models in that enemy unit '
                 'must take Desperate Escape tests. When doing so, if that '
                 'enemy unit is Battle-shocked, subtract 1 from each of those '
                 'tests.'),
         ability('Acrobatic Gladiators (Pain)',
                 'At the start of your Charge phase, you can spend 1 Pain token '
                 'to Empower this unit. While Empowered, this unit is eligible '
                 'to declare a charge in a turn in which it Advanced or Fell '
                 'Back.'),
     ]),

    # -- Vehicles -------------------------------------------------------------

    ('Drukhari Raider', 85,
     stat('14"', 8, '4+', 10, '7+', 2, invuln='6+'),
     [
         rng('Dark Lance', '36"', '1', '3+', 12, -3, 'D6+2'),
         mel('Bladevanes and chainsnares', 'D3+3', '4+', 6, -1, 1),
     ],
     [
         ability('Aethersails',
                 'While one or more Drukhari units are embarked within this '
                 'model, you can re-roll Advance and Charge rolls made for this '
                 'model.'),
         ability('Splinter Racks (Pain)',
                 'In your Shooting phase, when you select this model to shoot, '
                 'you can spend 1 Pain token to Empower this model. While '
                 'Empowered, if one or more units are embarked within this '
                 'model, each time this model makes an attack with a ranged '
                 'weapon that has the Anti ability, you can re-roll the Hit '
                 'roll.'),
         ability('Vanguard of the Dark City',
                 'At the start of your Command phase, select one of the '
                 'abilities in the Vanguard of the Dark City section for this '
                 'model. Until the start of your next Command phase, this model '
                 'has that ability.'),
         ability('Masters of the Shadowed Sky',
                 'At the end of your Command phase, if this model is within '
                 'range of an objective marker you control, and if one or more '
                 'Kabalite Warriors units are embarked within it, that objective '
                 'marker remains under your control until your opponent\'s Level '
                 'of Control over that objective marker is greater than yours at '
                 'the end of a phase.'),
         ability('Speed of the Kill',
                 'Each time a Wyches unit disembarks from this model (excluding '
                 'Emergency Disembarkations), models in that Wyches unit must be '
                 'set up wholly within 6" of this model.'),
         ability('Visions of Butchery',
                 'While one or more Wracks units are embarked within this model, '
                 'for each Wracks model embarked within this model, add 1 to the '
                 'Attacks characteristic of this model\'s Bladevanes and '
                 'chainsnares.'),
     ]),

    ('Drukhari Ravager', 110,
     stat('14"', 9, '4+', 11, '7+', 3, invuln='6+'),
     [
         rng('Dark Lance (x3)', '36"', '1', '3+', 12, -3, 'D6+2'),
         mel('Bladevanes', '3', '4+', 6, -1, 1),
     ],
     [
         ability('Damaged: 1-4 Wounds Remaining',
                 'While this model has 1-4 wounds remaining, each time this '
                 'model makes an attack, subtract 1 from the Hit roll.'),
         ability('Eradicate the Foe',
                 'Each time this model makes an attack that targets an enemy '
                 'unit that is at its Starting Strength, you can re-roll the '
                 'Hit roll.'),
         ability('Agonising Suppression (Pain)',
                 'In your Shooting phase, when you select this model to shoot, '
                 'you can spend 1 Pain token to Empower this model. While '
                 'Empowered, after this model has shot, select one enemy unit '
                 'hit by one or more of those attacks. Until the start of your '
                 'next turn, that enemy unit is suppressed. While a unit is '
                 'suppressed, each time a model in that unit makes an attack, '
                 'subtract 1 from the Hit roll.'),
     ]),
]


class Command(BaseCommand):
    """Seed Drukhari stat lines, weapon profiles, and abilities."""

    help = 'Seed Drukhari unit stats, weapons, and abilities.'

    def add_arguments(self, parser):
        """Add --dry-run flag."""
        parser.add_argument(
            '--dry-run', action='store_true',
            help='Preview changes without writing to the database.',
        )

    def handle(self, *args, **options):
        """Iterate over DRUKHARI_UNITS and upsert stats, weapons, and abilities."""
        dry_run = options['dry_run']
        updated = 0
        skipped = 0

        with transaction.atomic():
            for db_name, pts, stats, weapons, abilities in DRUKHARI_UNITS:
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
