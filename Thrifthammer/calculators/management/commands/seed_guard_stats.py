"""
Management command: seed_guard_stats

Seeds points costs, stat lines, weapon profiles, and unit abilities
for all Astra Militarum units in the database. Safe to re-run — uses update_or_create.

Usage:
    python manage.py seed_guard_stats
    python manage.py seed_guard_stats --dry-run
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from calculators.models import UnitAbility, UnitType, WeaponProfile


# ── Helpers ──────────────────────────────────────────────────────────────────

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


# ── Unit Data ─────────────────────────────────────────────────────────────────
# Format: (db_unit_name, points, stats_dict, [weapons], [abilities])

GUARD_UNITS = [

    # ── Characters ───────────────────────────────────────────────────────────

    ('Astra Militarum Commissar', 30,
     stat('6"', 3, '5+', 3, '6+', 1),
     [
         rng('Bolt pistol', '12"', '1', '3+', 4, 0, 1, 'Pistol'),
         mel('Chainsword', '4', '4+', 3, 0, 1),
     ],
     [
         ability('Summary Execution', 'Once per battle round, at the start of any phase, you can select one friendly Astra Militarum Infantry unit within 3" of this model. Until the end of the phase, that unit is not affected by the Battle-shock or Leadership rules. Then, roll one D6: on a 1, one model in that unit (your choice) is slain.'),
     ]),

    # ── Battleline ───────────────────────────────────────────────────────────

    ('Astra Militarum Cadian Shock Troops', 65,
     stat('6"', 3, '5+', 1, '7+', 2),
     [
         rng('Laspistol', '12"', '1', '4+', 3, 0, 1, 'Pistol'),
         rng('Lasgun (x9)', '24"', '1', '4+', 3, 0, 1, 'Rapid Fire 1'),
         mel('Chainsword', '3', '4+', 3, 0, 1),
         mel('Close combat weapon (x9)', '1', '4+', 3, 0, 1),
     ],
     [
         ability('Shock Troops', 'At the end of your Command phase, if this unit is within range of an objective marker you control, that objective marker remains under your control even if you have no models within range of it, until your opponent controls it.'),
     ]),

    ('Astra Militarum Infantry Squad', 65,
     stat('6"', 3, '5+', 1, '7+', 2),
     [
         rng('Laspistol', '12"', '1', '4+', 3, 0, 1, 'Pistol'),
         rng('Lasgun (x9)', '24"', '1', '4+', 3, 0, 1, 'Rapid Fire 1'),
         mel('Chainsword', '3', '4+', 3, 0, 1),
         mel('Close combat weapon (x9)', '1', '4+', 3, 0, 1),
     ],
     [
         ability('Shock Troops', 'At the end of your Command phase, if this unit is within range of an objective marker you control, that objective marker remains under your control even if you have no models within range of it, until your opponent controls it.'),
     ]),

    ('Astra Militarum Veteran Guardsmen', 60,
     stat('6"', 3, '5+', 1, '7+', 2),
     [
         rng('Laspistol', '12"', '1', '4+', 3, 0, 1, 'Pistol'),
         rng('Lasgun (x4)', '24"', '1', '4+', 3, 0, 1, 'Rapid Fire 1'),
         mel('Close combat weapon (x5)', '1', '4+', 3, 0, 1),
     ],
     [
         ability('Veterans', 'Each time a model in this unit makes an attack, re-roll a Hit roll of 1.'),
     ]),

    # ── Vehicles ─────────────────────────────────────────────────────────────

    ('Astra Militarum Basilisk', 140,
     stat('10"', 9, '3+', 11, '7+', 3),
     [
         rng('Earthshaker cannon', '240"', 'D6+3', '4+', 8, -2, 2, 'Blast, Heavy, Indirect Fire'),
         rng('Heavy bolter', '36"', '3', '4+', 5, -1, 2, 'Sustained Hits 1'),
         mel('Armoured tracks', '3', '4+', 6, 0, 1),
     ],
     [
         ability('Earthshaker Rounds', 'In your Shooting phase, after this model has shot, select one enemy unit hit by one or more of those attacks. Until the start of your next turn, that enemy unit is suppressed. While a unit is suppressed, halve its Move characteristic and it cannot use the Heroic Intervention or Fire Overwatch Stratagems.'),
         ability('Damaged: 1-4 wounds remaining', 'While this model has 1-4 wounds remaining, each time this model makes an attack, subtract 1 from the Hit roll.'),
     ]),

    ('Astra Militarum Chimera', 85,
     stat('10"', 9, '3+', 11, '7+', 2),
     [
         rng('Lasgun array', '24"', '6', '4+', 3, 0, 1, 'Rapid Fire 6'),
         rng('Multi-laser', '36"', '4', '4+', 6, 0, 1),
         rng('Heavy bolter', '36"', '3', '4+', 5, -1, 2, 'Sustained Hits 1'),
         mel('Armoured tracks', '3', '4+', 6, 0, 1),
     ],
     [
         ability('Mobile Command Vehicle', 'In your Command phase, one Officer model embarked within this Transport can issue Orders even though it is not on the battlefield. When doing so, measure distances from this model.'),
         ability('Damaged: 1-4 wounds remaining', 'While this model has 1-4 wounds remaining, each time this model makes an attack, subtract 1 from the Hit roll.'),
     ]),

    ('Astra Militarum Hellhound', 125,
     stat('10"', 10, '2+', 11, '7+', 3),
     [
         rng('Inferno cannon', '18"', '2D6', 'N/A', 6, -2, 1, 'Ignores Cover, Torrent'),
         rng('Heavy flamer', '12"', 'D6', 'N/A', 5, -1, 1, 'Ignores Cover, Torrent'),
         mel('Armoured tracks', '3', '4+', 6, 0, 1),
     ],
     [
         ability('Flush Them Out', 'In your Shooting phase, after this model has shot, select one enemy unit hit by one or more of those attacks. Until the end of the turn, that enemy unit cannot have the Benefit of Cover.'),
         ability('Damaged: 1-4 wounds remaining', 'While this model has 1-4 wounds remaining, each time this model makes an attack, subtract 1 from the Hit roll.'),
     ]),

    ('Astra Militarum Leman Russ Battle Tank', 185,
     stat('10"', 11, '2+', 13, '7+', 3),
     [
         rng('Leman Russ battle cannon', '48"', 'D6+3', '4+', 10, -1, 3, 'Blast'),
         rng('Lascannon', '48"', '1', '4+', 12, -3, 'D6+1'),
         mel('Armoured tracks', '6', '4+', 7, 0, 1),
     ],
     [
         ability('Armoured Spearhead', 'Each time this model makes an attack that targets a Monster or Vehicle unit, add 1 to the Hit roll.'),
         ability('Damaged: 1-4 wounds remaining', 'While this model has 1-4 wounds remaining, each time this model makes an attack, subtract 1 from the Hit roll.'),
     ]),

    ('Astra Militarum Sentinel', 55,
     stat('10"', 7, '3+', 7, '7+', 2),
     [
         rng('Multi-laser', '36"', '4', '4+', 6, 0, 1),
         mel('Close combat weapon', '3', '4+', 6, 0, 1),
     ],
     [
         ability('Daring Recon', 'At the start of your Shooting phase, select one enemy unit within 18" of and visible to this unit. Until the end of the phase, each time a friendly Astra Militarum model makes an attack that targets that unit, you can re-roll the Hit roll.'),
     ]),

    # ── Combat Patrol ────────────────────────────────────────────────────────

    ('Astra Militarum Combat Patrol', 0,
     stat('', None, '', None, '', None),
     [],
     []),
]


class Command(BaseCommand):
    """Seed Astra Militarum stat lines, weapon profiles, and abilities."""

    help = 'Seed Astra Militarum unit stats, weapons, and abilities.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run', action='store_true',
            help='Preview changes without writing to the database.',
        )

    def handle(self, *args, **options):
        """Iterate over GUARD_UNITS and upsert stats, weapons, and abilities."""
        dry_run = options['dry_run']
        updated = 0
        skipped = 0

        with transaction.atomic():
            for db_name, pts, stats, weapons, abilities in GUARD_UNITS:
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
            f'\nDone. {updated} units updated, {skipped} skipped.'
        ))
