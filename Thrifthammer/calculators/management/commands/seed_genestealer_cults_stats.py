"""
Management command: seed_genestealer_cults_stats

Seeds points costs, stat lines, weapon profiles, and unit abilities for
Genestealer Cults units in the database. Safe to re-run — uses
delete+create for weapons/abilities and direct field writes for stats.

Mapped units (5 products → 5 UnitTypes):
  Genestealer Cults Aberrants, Genestealer Cults Acolyte Hybrids
  (Autopistols loadout), Genestealer Cults Broodcoven (Patriarch),
  Genestealer Cults Magus, Genestealer Cults Neophyte Hybrids

Usage:
    python manage.py seed_genestealer_cults_stats
    python manage.py seed_genestealer_cults_stats --dry-run
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
# common loadout is used (Autopistols for Acolyte Hybrids, Patriarch for
# Broodcoven).

GSC_UNITS = [

    # -- Elites ---------------------------------------------------------------

    ('Genestealer Cults Aberrants', 135,
     stat('6"', 6, '5+', 3, '7+', 1, fnp='5+'),
     [
         mel('Aberrant weapons (x5)', 3, '3+', 7, -2, 2),
     ],
     [
         ability('Hulking Bodyguards',
                 'While a CHARACTER is leading this unit, each time an attack '
                 'targets this unit, if the Strength characteristic of that '
                 'attack is greater than the Toughness characteristic of this '
                 'unit, subtract 1 from the Wound roll.'),
     ]),

    # -- Infantry -------------------------------------------------------------

    # Acolyte Hybrids: Autopistols loadout (65pts) used as representative.
    # Hand Flamers variant costs 70pts and uses the same product box.

    ('Genestealer Cults Acolyte Hybrids', 65,
     stat('6"', 4, '5+', 1, '7+', 2),
     [
         rng('Autopistol (x5)', '12"', 1, '4+', 3, 0, 1, 'Pistol'),
         mel('Cult claws and knife (x5)', 3, '3+', 4, -1, 1),
     ],
     [
         ability('Claimed for the Cult',
                 'At the start of your Command phase, roll one D6 for each '
                 'objective marker that you control that has one or more units '
                 'from your army with this ability within range of it. If one '
                 'or more of the results is a 4+, you gain 1CP.'),
     ]),

    ('Genestealer Cults Neophyte Hybrids', 65,
     stat('6"', 3, '5+', 1, '7+', 2),
     [
         rng('Autopistol', '12"', 1, '3+', 3, 0, 1, 'Pistol'),
         rng('Hybrid firearm (x10)', '24"', 1, '4+', 3, 0, 1, 'Rapid Fire 1'),
         mel('Close combat weapon (x10)', 1, '4+', 3, 0, 1),
     ],
     [
         ability('A Plan Generations in the Making',
                 'At the end of your Command phase, if this unit is within '
                 'range of an objective marker you control, that objective '
                 'marker remains under your control, even if you have no '
                 'models within range of it, until your opponent controls it '
                 'at the start or end of any turn.'),
     ]),

    # -- Characters -----------------------------------------------------------

    # Broodcoven box contains Patriarch, Primus and Magus. The Broodcoven
    # UnitType is seeded with the Patriarch (the faction leader, 75pts).

    ('Genestealer Cults Broodcoven', 75,
     stat('8"', 5, '4+', 6, '6+', 1),
     [
         mel("Patriarch's claws", 5, '2+', 6, -2, 2,
             'Devastating Wounds, Twin-linked'),
     ],
     [
         ability('Leader',
                 'This model can be attached to the following unit:\n'
                 '\u25a0 Purestrain Genestealers'),
     ]),

    ('Genestealer Cults Magus', 50,
     stat('6"', 3, '5+', 4, '6+', 1),
     [
         rng('Autopistol', '12"', 1, '3+', 3, 0, 1, 'Pistol'),
         mel('Force stave', 3, '3+', 5, -1, 'D3', 'Psychic'),
     ],
     [
         ability('Leader',
                 'This model can be attached to the following units:\n'
                 '\u25a0 Acolyte Hybrids\n'
                 '\u25a0 Hybrid Metamorphs\n'
                 '\u25a0 Neophyte Hybrids'),
     ]),

]


# -- Command ------------------------------------------------------------------

class Command(BaseCommand):
    """Seed Genestealer Cults stat lines, weapons, and abilities."""

    help = 'Seed Genestealer Cults unit stats, weapon profiles, and abilities.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run', action='store_true',
            help='Preview changes without writing to the database.',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        updated = skipped = 0

        with transaction.atomic():
            for db_name, points, stats, weapons, abilities in GSC_UNITS:
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

                unit.points_cost = points
                for field, value in stats.items():
                    setattr(unit, field, value)
                unit.save()

                unit.weapon_profiles.all().delete()
                for order, wp in enumerate(weapons):
                    WeaponProfile.objects.create(unit=unit, order=order, **wp)

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
                f'\nGenestealer Cults seed complete: '
                f'{updated} updated, {skipped} skipped.'
            )
        )
