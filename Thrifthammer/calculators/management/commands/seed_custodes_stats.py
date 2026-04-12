"""
Management command: seed_custodes_stats

Seeds points costs, stat lines, weapon profiles, and unit abilities
for all Adeptus Custodes units in the database. Safe to re-run.

Usage:
    python manage.py seed_custodes_stats
    python manage.py seed_custodes_stats --dry-run
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from calculators.models import UnitAbility, UnitType, WeaponProfile


# ── Helpers ──────────────────────────────────────────────────────────────────

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


# ── Unit Data ─────────────────────────────────────────────────────────────────
# Format: (db_unit_name, points, stats_dict, [weapons], [abilities])
# Weapon/ability text sourced from parsed New Recruit HTML (2026-04-12).

CUSTODES_UNITS = [

    # ── Epic Heroes ──────────────────────────────────────────────────────────

    ('Adeptus Custodes Trajann Valoris', 140,
     stat('6"', 6, '2+', 7, '5+', 2, invuln='4+'),
     [
         rng("Eagle's Scream", '24"', '2', '2+', 5, -2, 3, 'Assault'),
         mel("Watcher's Axe",  '6',   '2+', 10, -2, 3),
     ],
     [
         ability('Leader',
                 'This model can be attached to the following units:\n'
                 '■ Custodian Guard\n'
                 '■ Custodian Wardens'),
         ability('Captain-General',
                 'While this model is leading a unit, each time a model in '
                 'that unit makes an attack, you can ignore any or all '
                 'modifiers to that attack\'s Ballistic Skill or Weapon Skill '
                 'characteristics and/or all modifiers to the Hit roll.'),
         ability('Moment Shackle',
                 'Once per battle, at the start of the Fight phase, you can '
                 'select one of the following to take effect until the end of '
                 'the phase:\n'
                 '■ This model\'s Watcher\'s Axe melee weapon has an Attacks '
                 'characteristic of 12.\n'
                 '■ This model has a 2+ invulnerable save.'),
     ]),

    # ── Characters ───────────────────────────────────────────────────────────

    ('Adeptus Custodes Shield-Captain', 120,
     stat('6"', 6, '2+', 6, '6+', 2, invuln='4+'),
     [
         rng('Guardian Spear', '24"', '2', '2+', 4, -1, 2, 'Assault'),
         mel('Guardian Spear', '7',   '2+', 7, -2, 2),
     ],
     [
         ability('Master of the Stances',
                 'Once per battle, when this model\'s unit is selected to '
                 'fight, it can use this ability. If it does, until that fight '
                 'is resolved, both Ka\'tah Stances are active for that unit, '
                 'instead of only one.'),
         ability('Leader',
                 'This model can be attached to the following units:\n'
                 '■ Custodian Guard\n'
                 '■ Custodian Wardens'),
         ability('Strategic Mastery',
                 'Once per battle round, one unit from your army with this '
                 'ability can use it when its unit is targeted with a '
                 'Stratagem. If it does, reduce the CP cost of that use of '
                 'that Stratagem by 1CP.'),
     ]),

    # ── Infantry ─────────────────────────────────────────────────────────────

    ('Adeptus Custodes Custodian Guard', 160,
     stat('6"', 6, '2+', 3, '6+', 2, invuln='4+'),
     [
         rng('Guardian Spear (x4)', '24"', '2', '2+', 4, -1, 2, 'Assault'),
         mel('Guardian Spear (x4)', '5',   '2+', 7, -2, 2),
     ],
     [
         ability('Stand Vigil',
                 'Each time a model in this unit makes an attack, re-roll a '
                 'Wound roll of 1. While this unit is within range of an '
                 'objective marker you control, you can re-roll the Wound roll '
                 'instead.'),
         ability('Sentinel Storm',
                 'Once per battle, in your Shooting phase, after the unit has '
                 'shot, it can shoot again.'),
     ]),

    ('Adeptus Custodes Custodian Wardens', 210,
     stat('6"', 6, '2+', 3, '6+', 2, invuln='4+'),
     [
         rng('Guardian Spear (x4)', '24"', '2', '2+', 4, -1, 2, 'Assault'),
         mel('Guardian Spear (x4)', '5',   '2+', 7, -2, 2),
     ],
     [
         ability('Resolute Will',
                 'While a CHARACTER is leading this unit, each time an attack '
                 'targets this unit, if the Strength characteristic of that '
                 'attack is greater than the Toughness characteristic of this '
                 'unit, subtract 1 from the Wound roll.'),
         ability('Living Fortress',
                 'Once per battle, at the start of any phase, this unit can '
                 'use this ability. If it does, until the end of the phase, '
                 'models in this unit have the Feel No Pain 4+ ability.'),
     ]),

    # ── Mounted ──────────────────────────────────────────────────────────────

    ('Adeptus Custodes Vertus Praetors', 150,
     stat('12"', 7, '2+', 5, '6+', 2, invuln='4+'),
     [
         rng('Salvo launcher (x2)',    '24"', '1', '2+', 10, -3, 'D6+1',
             'Twin-linked'),
         mel('Interceptor lance (x2)', '5',   '2+', 7, -2, 2, 'Lance'),
     ],
     [
         ability('Turbo Boost',
                 'Each time this unit Advances, do not make an Advance roll. '
                 'Instead, until the end of the phase, add 6" to the Move '
                 'characteristic of models in this unit.'),
         ability('Quicksilver Execution',
                 'Once per battle, after this unit ends a normal or Advance '
                 'move, you can select one enemy unit (excluding MONSTER and '
                 'VEHICLE units) that it moved over during that move, then '
                 'roll one D6 for each model in this unit; for each 2+, that '
                 'enemy unit suffers 2 mortal wounds.'),
     ]),

    ('Adeptus Custodes Combat Patrol', 600,
     stat('', None, '', None, '', None),
     [], []),
]


class Command(BaseCommand):
    """Seed Adeptus Custodes stat lines, weapon profiles, and abilities."""

    help = 'Seed Adeptus Custodes unit stats, weapons, and abilities.'

    def add_arguments(self, parser):
        """Add --dry-run flag."""
        parser.add_argument(
            '--dry-run', action='store_true',
            help='Preview changes without writing to the database.',
        )

    def handle(self, *args, **options):
        """Iterate over CUSTODES_UNITS and upsert stats, weapons, and abilities."""
        dry_run = options['dry_run']
        updated = 0
        skipped = 0

        with transaction.atomic():
            for db_name, pts, stats, weapons, abilities in CUSTODES_UNITS:
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
