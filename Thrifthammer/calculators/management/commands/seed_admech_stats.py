"""
Management command: seed_admech_stats

Seeds points costs, stat lines, weapon profiles, and unit abilities
for all Adeptus Mechanicus units in the database. Safe to re-run — uses update_or_create.

Usage:
    python manage.py seed_admech_stats
    python manage.py seed_admech_stats --dry-run
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from calculators.models import UnitAbility, UnitType, WeaponProfile
from products.models import Faction


# ── Helpers ──────────────────────────────────────────────────────────────────

def stat(m, t, sv, w, ld, oc, invuln='', fnp=''):
    return dict(
        stat_movement=m, stat_toughness=t, stat_save=sv,
        stat_wounds=w, stat_leadership=ld, stat_oc=oc,
        stat_invuln=invuln, stat_fnp=fnp,
    )


def rng(name, rng_val, a, skill, s, ap, d, kw=''):
    return dict(name=name, weapon_type='ranged', range=rng_val,
                attacks=a, skill=skill, strength=str(s), ap=str(ap), damage=str(d), keywords=kw)


def mel(name, a, skill, s, ap, d, kw=''):
    return dict(name=name, weapon_type='melee', range='Melee',
                attacks=a, skill=skill, strength=str(s), ap=str(ap), damage=str(d), keywords=kw)


def ability(name, desc):
    return dict(name=name, description=desc)


# ── Unit Data ─────────────────────────────────────────────────────────────────
# Format: (db_unit_name, points, stats_dict, [weapons], [abilities])

ADMECH_UNITS = [

    # ── Characters ───────────────────────────────────────────────────────────

    ('Adeptus Mechanicus Tech-Priest Dominus', 65,
     stat('6"', 4, '2+', 4, '7+', 1, invuln='5+'),
     [
         rng('Macrostubber', '12"', '5', '3+', 4, 0, 1, 'Pistol'),
         rng('Volkite blaster', '24"', '3', '3+', 5, 0, 2, 'Devastating Wounds'),
         mel('Omnissian axe', '4', '3+', 6, -2, 2),
     ],
     [
         ability('Invulnerable Save (5+)', 'This model has a 5+ invulnerable save.'),
         ability('Leader', 'This model can be attached to the following units: Corpuscarii Electro-Priests, Fulgurite Electro-Priests, Kataphron Breachers, Kataphron Destroyers, Skitarii Rangers, Skitarii Vanguard.'),
         ability('Lord of the Machine Cult', 'While this model is leading a unit, models in that unit have the Feel No Pain 5+ ability. If that unit has the Electro-Priests keyword, models in that unit have the Feel No Pain 4+ ability instead.'),
         ability('Data-spike', 'At the start of the Fight phase, you can select one enemy Vehicle unit within Engagement Range of this model\'s unit and roll one D6: on a 4+, that enemy unit suffers D6 mortal wounds and, until the end of the phase, the Weapon Skill characteristic of melee weapons equipped by that enemy unit is worsened by 1.'),
     ]),

    # ── Battleline ───────────────────────────────────────────────────────────

    ('Adeptus Mechanicus Skitarii Rangers', 85,
     stat('6"', 3, '4+', 1, '7+', 2, invuln='5+'),
     [
         rng('Galvanic rifle (x10)', '30"', '2', '4+', 4, 0, 1),
         mel('Close combat weapon (x10)', '1', '4+', 3, 0, 1),
     ],
     [
         ability('Invulnerable Save (5+)', 'Models in this unit have a 5+ invulnerable save.'),
         ability('Objective Scouted', 'At the end of your Command phase, if this unit is within range of an objective marker you control, that objective marker remains under your control, even if you have no models within range of it, until your opponent controls it at the start or end of any turn.'),
     ]),

    ('Adeptus Mechanicus Skitarii Vanguard', 95,
     stat('6"', 3, '4+', 1, '7+', 2, invuln='5+'),
     [
         rng('Radium carbine (x10)', '18"', '3', '4+', 3, 0, 1, 'Anti-Infantry 4+'),
         mel('Close combat weapon (x10)', '1', '4+', 3, 0, 1),
     ],
     [
         ability('Invulnerable Save (5+)', 'Models in this unit have a 5+ invulnerable save.'),
         ability('Rad-saturation (Aura)', 'While an enemy unit (excluding Vehicle units) is within 3" of this unit, subtract 1 from the Objective Control characteristic of models in that unit.'),
     ]),

    # ── Infantry ─────────────────────────────────────────────────────────────

    ('Adeptus Mechanicus Electropriests', 65,
     stat('6"', 3, '7+', 1, '7+', 1, invuln='5+', fnp='5+'),
     [
         rng('Electrostatic gauntlets (x5)', '12"', '3', '3+', 5, 0, 1, 'Pistol, Sustained Hits 2'),
         mel('Electrostatic gauntlets (x5)', '3', '4+', 5, 0, 1, 'Sustained Hits 2'),
     ],
     [
         ability('Invulnerable Save (5+)', 'Models in this unit have a 5+ invulnerable save.'),
         ability('Feel No Pain (5+)', 'Models in this unit have the Feel No Pain 5+ ability.'),
         ability('Electro-shock', 'In your Shooting phase, after this unit has shot, select one enemy unit (excluding Monsters and Vehicles) hit by one or more of those attacks. Until the end of your opponent\'s next turn, that enemy unit is shocked. While a unit is shocked, subtract 2" from its Move characteristic and subtract 2 from Advance and Charge rolls made for it.'),
     ]),

    ('Adeptus Mechanicus Kataphron Destroyers', 105,
     stat('5"', 6, '3+', 3, '7+', 1, invuln='6+'),
     [
         rng('Heavy grav-cannon (x3)', '30"', '4', '4+', 6, -1, 2, 'Anti-Vehicle 2+'),
         rng('Phosphor blaster (x3)', '24"', '1', '4+', 5, 0, 1, 'Ignores Cover, Rapid Fire 1'),
         mel('Close combat weapon (x3)', '2', '4+', 5, 0, 1),
     ],
     [
         ability('Invulnerable Save (6+)', 'Models in this unit have a 6+ invulnerable save.'),
         ability('Sentinel Directive', 'Each time you target this unit with the Fire Overwatch Stratagem, hits are scored on unmodified Hit rolls of 5+ when resolving that Stratagem.'),
     ]),

    # ── Vehicles ─────────────────────────────────────────────────────────────

    ('Adeptus Mechanicus Ironstrider Ballistarii', 85,
     stat('10"', 7, '3+', 7, '7+', 2, invuln='5+'),
     [
         rng('Twin cognis autocannon', '48"', '4', '4+', 9, -1, 3, 'Sustained Hits 1, Twin-linked'),
         mel('Ironstrider feet', '3', '4+', 5, 0, 1),
     ],
     [
         ability('Invulnerable Save (5+)', 'Models in this unit have a 5+ invulnerable save.'),
         ability('Elevated Strider', 'This unit is eligible to shoot in a turn in which it Fell Back or Advanced, and you can re-roll Desperate Escape tests taken for models in this unit.'),
         ability('Broad Spectrum Data-tether', 'Each time you select this unit as the target of a Stratagem, roll one D6: on a 5+, you gain 1CP.'),
     ]),

    ('Adeptus Mechanicus Dunecrawler', 155,
     stat('8"', 10, '2+', 11, '7+', 3, invuln='4+'),
     [
         rng('Eradication beamer – dissipated', '36"', '3D3', '4+', 9, -2, 2, 'Blast, Sustained Hits 1'),
         rng('Eradication beamer – focused', '18"', '3D3', '4+', 10, -3, 3, 'Blast, Sustained Hits 1'),
         mel('Dunecrawler legs', '3', '4+', 6, 0, 1),
     ],
     [
         ability('Invulnerable Save (4+)', 'This model has a 4+ invulnerable save.'),
         ability('Emanatus Forcefield (Aura)', 'While a friendly Adeptus Mechanicus Battleline model is wholly within 6" of this model, that Battleline model has a 4+ invulnerable save against ranged attacks.'),
         ability('Scuttling Walker', 'Each time this model makes a Normal, Advance or Fall Back move, it can move through friendly Monster and Vehicle models and sections of terrain features that are 4" or less in height.'),
         ability('Damaged: 1-4 wounds remaining', 'While this model has 1-4 wounds remaining, each time this model makes an attack, subtract 1 from the Hit roll.'),
     ]),

    # ── Combat Patrol ────────────────────────────────────────────────────────

    ('Adeptus Mechanicus Combat Patrol', 290,
     stat('', None, '', None, '', None),
     [],
     []),
]


class Command(BaseCommand):
    """Seed Adeptus Mechanicus stat lines, weapon profiles, and abilities."""

    help = 'Seed Adeptus Mechanicus unit stats, weapons, and abilities.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run', action='store_true',
            help='Preview changes without writing to the database.',
        )

    def handle(self, *args, **options):
        """Iterate over ADMECH_UNITS and upsert stats, weapons, and abilities."""
        dry_run = options['dry_run']
        updated = 0
        skipped = 0

        with transaction.atomic():
            for db_name, pts, stats, weapons, abilities in ADMECH_UNITS:
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
                    f'  OK: {db_name!r} — {pts}pts, '
                    f'{len(weapons)} weapons, {len(abilities)} abilities'
                )
                updated += 1

            if dry_run:
                self.stdout.write(self.style.WARNING('Dry run — no changes written.'))
                transaction.set_rollback(True)

        self.stdout.write(self.style.SUCCESS(
            f'\nDone. {updated} units updated, {skipped} skipped.'
        ))
