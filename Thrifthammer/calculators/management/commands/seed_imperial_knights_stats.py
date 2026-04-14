"""
Management command: seed_imperial_knights_stats

Seeds points costs, stat lines, weapon profiles, and unit abilities for
Imperial Knights units in the database. Safe to re-run — uses
delete+create for weapons/abilities and direct field writes for stats.

Mapped units (7 products → 7 UnitTypes):
  Cerastus Knight Acheron, Cerastus Knight Castigator, Cerastus Knight
  Lancer, Imperial Knight Armigers (Warglaive loadout), Imperial Knight
  Dominus (Knight Castellan loadout), Imperial Knight Preceptor / Canis
  Rex (Knight Preceptor loadout), Imperial Knight Questoris (Knight
  Paladin loadout)

Usage:
    python manage.py seed_imperial_knights_stats
    python manage.py seed_imperial_knights_stats --dry-run
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
# common loadout is used (Warglaive for Armigers, Knight Castellan for
# Dominus, Knight Preceptor for Preceptor/Canis Rex box, Knight Paladin
# for Questoris).
# Note: invuln save on Knights is ranged-only (denoted 5+* in datasheets).

KNIGHTS_UNITS = [

    # -- Cerastus Knights -----------------------------------------------------

    ('Cerastus Knight Acheron', 395,
     stat('12"', 11, '3+', 28, '6+', 10),
     [
         rng('Acheron flame cannon', '18"', '2D6', 'N/A', 8, -1, 2,
             'Ignores Cover, Torrent'),
         rng('Twin heavy bolter', '36"', 3, '3+', 5, -1, 2,
             'Sustained Hits 1, Twin-linked'),
         mel('Reaper chainfist - strike', 4, '3+', 14, -4, 6),
         mel('Reaper chainfist - sweep', 12, '3+', 9, -3, 2),
     ],
     [
         ability("Acheron's Duty (Bondsman)",
                 'While a model is affected by this ability, at the start of '
                 'the Fight phase, each enemy unit within Engagement Range of '
                 'one or more units with this ability must take a '
                 'Battle-shock test, subtracting 1 from the result when they '
                 'do.'),
         ability('Damaged: 1-10 Wounds Remaining',
                 'While this model has 1-10 wounds remaining, subtract 5 from '
                 'this model\'s Objective Control characteristic and each time '
                 'this model makes an attack, subtract 1 from the Hit roll.'),
     ]),

    ('Cerastus Knight Castigator', 395,
     stat('12"', 11, '3+', 28, '6+', 10),
     [
         rng('Castigator bolt cannon', '36"', 18, '3+', 6, -2, 2,
             'Twin-linked'),
         mel('Tempest warblade - strike', 4, '3+', 14, -4, 6),
         mel('Tempest warblade - sweep', 12, '3+', 9, -3, 2),
     ],
     [
         ability("Castigator's Duty (Bondsman)",
                 'While a model is affected by this ability, its ranged '
                 'weapons have the [SUSTAINED HITS 1] ability and the Armour '
                 'Penetration characteristic of its ranged weapons is '
                 'improved by 1.'),
         ability('Damaged: 1-10 Wounds Remaining',
                 'While this model has 1-10 wounds remaining, subtract 5 from '
                 'this model\'s Objective Control characteristic and each time '
                 'this model makes an attack, subtract 1 from the Hit roll.'),
     ]),

    ('Cerastus Knight Lancer', 395,
     stat('12"', 11, '3+', 28, '6+', 10),
     [
         rng('Cerastus shock lance', '12"', 6, '3+', 6, 0, 2,
             'Assault, Sustained Hits 2'),
         mel('Cerastus shock lance - strike', 5, '2+', 20, -3, 8, 'Lance'),
         mel('Cerastus shock lance - sweep', 10, '2+', 10, -2, 3),
     ],
     [
         ability("Lancer's Duty (Bondsman)",
                 'While a model is affected by this ability, it is eligible '
                 'to declare a charge in a turn in which it Advanced.'),
         ability('Damaged: 1-10 Wounds Remaining',
                 'While this model has 1-10 wounds remaining, subtract 5 from '
                 'this model\'s Objective Control characteristic and each time '
                 'this model makes an attack, subtract 1 from the Hit roll.'),
     ]),

    # -- Armigers -------------------------------------------------------------

    # Armiger Warglaive (140pts) used as representative — most popular melee
    # variant. Armiger Helverin (135pts) is the ranged autocannon variant.

    ('Imperial Knight Armigers', 140,
     stat('12"', 9, '3+', 14, '7+', 6, invuln='5+*'),
     [
         rng('Thermal spear', '18"', 2, '3+', 12, -4, 'D6', 'Melta 4'),
         rng('Questoris heavy stubber', '36"', 3, '3+', 4, -1, 1,
             'Rapid Fire 3'),
         mel('Reaper chain-cleaver - strike', 4, '3+', 10, -3, 3),
         mel('Reaper chain-cleaver - sweep', 8, '3+', 8, -2, 1),
     ],
     [
         ability('Impetuous Glory',
                 'Each time this model makes a charge move, until the end of '
                 'the turn, add 1 to the Attacks characteristic of this '
                 'model\'s reaper chain-cleaver - strike profile, and add 2 '
                 'to the Attacks characteristic of this model\'s reaper '
                 'chain-cleaver - sweep profile.'),
         ability('Damaged: 1-5 Wounds Remaining',
                 'While this model has 1-5 wounds remaining, subtract 3 from '
                 'this model\'s Objective Control characteristic and each '
                 'time this model makes an attack, subtract 1 from the Hit '
                 'roll.'),
         ability('Invulnerable Save (5+*)',
                 'This model has a 5+ invulnerable save against ranged '
                 'attacks.'),
     ]),

    # -- Dominus Knights ------------------------------------------------------

    # Knight Castellan (410pts) used as representative — ranged fire support
    # titan. Knight Valiant (410pts) is the alternative build.

    ('Imperial Knight Dominus', 410,
     stat('8"', 12, '3+', 28, '6+', 10, invuln='5+*'),
     [
         rng('Plasma decimator - standard', '48"', 'D6+3', '3+', 8, -3, 2,
             'Blast'),
         rng('Plasma decimator - supercharge', '48"', 'D6+3', '3+', 9, -4, 3,
             'Blast, Hazardous'),
         rng('Twin meltagun (x2)', '12"', 1, '3+', 9, -4, 'D6',
             'Melta 2, Twin-linked'),
         rng('Volcano lance', '72"', 'D3', '3+', 18, -5, 'D6+8', 'Blast'),
         rng('Shieldbreaker missile launcher (x2)', '72"', 1, '3+', 12, -6,
             'D6+1', 'Anti-Titanic 4+, Devastating Wounds'),
         rng('Twin siegebreaker cannon', '36"', 'D6', '3+', 6, 0, 1,
             'Blast, Twin-linked'),
         mel('Titanic feet', 4, '4+', 8, -1, 2),
     ],
     [
         ability('Titan Hunter',
                 'Each time a ranged attack made by this model is allocated '
                 'to a Monster or Vehicle model, you can re-roll the Damage '
                 'roll.'),
         ability('Invulnerable Save (5+*)',
                 'This model has a 5+ invulnerable save against ranged '
                 'attacks.'),
         ability('Damaged: 1-10 Wounds Remaining',
                 'While this model has 1-10 wounds remaining, subtract 5 from '
                 'this model\'s Objective Control characteristic and each time '
                 'this model makes an attack, subtract 1 from the Hit roll.'),
         ability('Ion Aegis (Aura)',
                 'While a friendly Armiger model is within 6" of this model, '
                 'each time a ranged attack targets that model, it has the '
                 'Benefit of Cover against that attack.'),
     ]),

    # -- Questoris Knights ----------------------------------------------------

    # Knight Preceptor (365pts) used as representative for the Preceptor /
    # Canis Rex product box. Canis Rex is the named character at 415pts.

    ('Imperial Knight Preceptor / Canis Rex', 365,
     stat('10"', 11, '3+', 26, '6+', 10),
     [
         rng('Las-impulsor - high intensity', '24"', 'D6', '3+', 14, -3, 4,
             'Blast'),
         rng('Las-impulsor - low intensity', '36"', '2D6', '3+', 7, -1, 2,
             'Blast'),
         rng('Preceptor multi-laser', '36"', 4, '3+', 6, 0, 1),
         mel('Reaper chainsword - strike', 4, '3+', 14, -4, 6),
         mel('Reaper chainsword - sweep', 12, '3+', 9, -3, 2),
     ],
     [
         ability('Mentor (Bondsman)',
                 'Each time a model affected by this ability makes an attack '
                 'that targets this model\'s quarry, you can re-roll the '
                 'Wound roll.'),
         ability('Damaged: 1-9 Wounds Remaining',
                 'While this model has 1-9 wounds remaining, subtract 5 from '
                 'this model\'s Objective Control characteristic and each time '
                 'this model makes an attack, subtract 1 from the Hit roll.'),
     ]),

    # Knight Paladin (375pts) used as representative for the Questoris box,
    # which can build 6 configurations (Crusader, Defender, Errant, Gallant,
    # Paladin, Warden). Paladin is the classic long-range battle cannon build.

    ('Imperial Knight Questoris', 375,
     stat('10"', 11, '3+', 26, '6+', 10),
     [
         rng('Questoris heavy stubber', '36"', 3, '3+', 4, -1, 1,
             'Rapid Fire 3'),
         rng('Rapid-fire battle cannon', '72"', 'D6+3', '3+', 10, -1, 3,
             'Blast, Rapid Fire D6+3'),
         rng('Meltagun', '12"', 1, '3+', 9, -4, 'D6', 'Melta 2'),
         mel('Reaper chainsword - strike', 4, '3+', 14, -4, 6),
         mel('Reaper chainsword - sweep', 12, '3+', 9, -3, 2),
     ],
     [
         ability("Paladin's Duty (Bondsman)",
                 'While a model is affected by this ability, weapons equipped '
                 'by that model have the [LETHAL HITS] ability, and melee '
                 'weapons equipped by that model have the [LANCE] ability.'),
         ability('Damaged: 1-9 Wounds Remaining',
                 'While this model has 1-9 wounds remaining, subtract 5 from '
                 'this model\'s Objective Control characteristic and each time '
                 'this model makes an attack, subtract 1 from the Hit roll.'),
     ]),

]


# -- Command ------------------------------------------------------------------

class Command(BaseCommand):
    """Seed Imperial Knights stat lines, weapons, and abilities."""

    help = 'Seed Imperial Knights unit stats, weapon profiles, and abilities.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run', action='store_true',
            help='Preview changes without writing to the database.',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        updated = skipped = 0

        with transaction.atomic():
            for db_name, points, stats, weapons, abilities in KNIGHTS_UNITS:
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
                    WeaponProfile.objects.create(unit_type=unit, order=order, **wp)

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
                f'\nImperial Knights seed complete: '
                f'{updated} updated, {skipped} skipped.'
            )
        )
