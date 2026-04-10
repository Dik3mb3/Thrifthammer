"""
Management command: seed_votann_stats

Seeds points costs, stat lines, weapon profiles, and unit abilities
for all Leagues of Votann units. Safe to re-run — uses update_or_create.

Usage:
    python manage.py seed_votann_stats
    python manage.py seed_votann_stats --dry-run
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


def rng(name, rng, a, skill, s, ap, d, kw=''):
    return dict(name=name, weapon_type='ranged', range=rng,
                attacks=a, skill=skill, strength=str(s), ap=str(ap), damage=str(d), keywords=kw)


def mel(name, a, skill, s, ap, d, kw=''):
    return dict(name=name, weapon_type='melee', range='Melee',
                attacks=a, skill=skill, strength=str(s), ap=str(ap), damage=str(d), keywords=kw)


def ability(name, desc):
    return dict(name=name, description=desc)


# ── Unit Data ─────────────────────────────────────────────────────────────────
# Format: (unit_name, points, stats_dict, [weapons], [abilities])

VOTANN_UNITS = [

    # ── Epic Heroes ──────────────────────────────────────────────────────────

    ('Berehk Stornbrow', 95,
     stat('6"', 6, '5+', 5, '7+', 1, invuln='5+', fnp='4+'),
     [
         mel("Kromlôk's Revenge – graviton strikes", '4', '2+', 10, -2, 4,
             'Anti-Monster 3+, Anti-Vehicle 3+, Sustained Hits 1'),
         mel("Kromlôk's Revenge – plasma sweeps", '8', '2+', 7, -2, 2, 'Sustained Hits 1'),
         mel('Warforge gauntlets', '2', '2+', 6, -2, 1, 'Extra Attacks, Sustained Hits 1'),
     ],
     [
         ability('Invulnerable Save (5+)', 'This model has a 5+ invulnerable save.'),
         ability('Break the Foe', 'Melee weapons equipped by models in this unit have the [Sustained Hits 1] ability.'),
         ability('Relentless Avalanche', 'You can target this model\'s unit with the Heroic Intervention Stratagem for 0CP, and can do so even if you have already targeted a different unit with that Stratagem this phase.'),
         ability('Leader', 'Can be attached to: Cthonian Beserks.'),
     ]),

    ('Buri Aegnirssen', 95,
     stat('5"', 6, '3+', 5, '6+', 1, invuln='4+'),
     [
         rng('Autoch-pattern bolt pistol', '12"', '1', '2+', 4, 0, 1, 'Pistol'),
         mel('Bane – strike', '5', '2+', 12, -3, 3, 'Precision'),
         mel('Bane – sweep', '10', '2+', 6, -2, 1),
     ],
     [
         ability('Invulnerable Save (4+)', 'This model has a 4+ invulnerable save.'),
         ability('Grudge-fuelled Fortitude', 'The first time this model is destroyed, at the end of the phase, roll one D6: on a 2+, set this model back up on the battlefield as close as possible to where it was destroyed and not within Engagement Range of one or more enemy units, with its full wounds remaining.'),
         ability('Unhinged Vengeance', "In your opponent's Shooting phase, each time an enemy unit has shot, if this model lost one or more wounds, it can make a Vengeance move — roll one D6, add 2, and move up to that many inches toward the closest enemy unit, ending within Engagement Range. Cannot be used while Battle-shocked or already in Engagement Range, and only once per phase."),
         ability('Lone Operative', 'This model can only be targeted in the Shooting phase if the attacking model is within 12".'),
     ]),

    ('Uthar the Destined', 95,
     stat('5"', 5, '3+', 5, '6+', 1, invuln='4+'),
     [
         rng('Volkanite disintegrator', '24"', '3', '2+', 5, 0, 1, 'Devastating Wounds'),
         mel('Blade of the Ancestors', '5', '2+', 6, -3, 2, 'Devastating Wounds'),
     ],
     [
         ability('Invulnerable Save (4+)', 'This model has a 4+ invulnerable save.'),
         ability('Ancestral Fortune', 'Once per turn, you can spend 1YP to change one Hit roll, one Wound roll, or one saving throw made for this model to a 6.'),
         ability('Grim Efficiency', 'Once per battle round, when a friendly Leagues of Votann unit within 12" of this model is targeted with a Stratagem, reduce the CP cost of that Stratagem by 1CP.'),
         ability('Rampart crest', 'While this model is leading a unit, models in that unit have a 5+ invulnerable save.'),
         ability('Leader', 'Can be attached to: Einhyr Hearthguard, Hearthkyn Warriors.'),
     ]),

    # ── Characters ───────────────────────────────────────────────────────────

    ('Arkanyst Evaluator', 65,
     stat('5"', 5, '3+', 4, '7+', 1),
     [
         rng('Transmatter inverter – half charge', '12"', '3', '2+', 8, -1, 1, 'Rapid Fire 1'),
         rng('Transmatter inverter – full charge', '18"', '3', '2+', 8, -2, 2, 'Hazardous, Rapid Fire 2'),
         rng('Transmatter inverter – overcharge', '24"', '3', '2+', 8, -3, 3, 'Hazardous, Overcharge, Rapid Fire 3'),
         mel('Close combat weapon', '1', '4+', 3, 0, 1),
     ],
     [
         ability('Science Guild Support', 'While this model is within 3" of one or more other friendly Leagues of Votann Infantry units (excluding Lone Operative units), this model has the Lone Operative ability.'),
         ability('Resource Transmutation', 'Once per turn, in your Shooting phase, this model can spend 1YP; until end of phase ranged weapons have [Sustained Hits 1], and if one or more enemy units were destroyed, gain up to 2YP.'),
         ability('Leader', 'Can be attached to: Ironkin Steeljacks with Heavy Volkanite Disintegrators, Ironkin Steeljacks with Melee Weapons.'),
     ]),

    ('Brokhyr Iron-master', 75,
     stat('5"', 5, '4+', 4, '7+', 1),
     [
         rng('Graviton rifle', '18"', '3', '3+', 5, -1, 3, 'Anti-Monster 3+, Anti-Vehicle 3+'),
         rng('Autoch-pattern bolt pistol', '12"', '1', '3+', 4, 0, 1, 'Pistol'),
         rng('Las-beam cutter', '6"', '1', '4+', 6, -3, 1),
         mel('Graviton hammer', '3', '4+', 9, -1, 3, 'Anti-Monster 3+, Anti-Vehicle 3+'),
         mel('Close combat weapon', '1', '4+', 3, 0, 1),
         mel('Plasma torch', '1', '4+', 6, -3, 2),
         mel('Manipulator arms', '3', '4+', 3, 0, 1),
     ],
     [
         ability('Multi-spectral visor', 'Each time a model in this unit makes a ranged attack, re-roll a Wound roll of 1.'),
         ability('Brôkhyr Guild Support', 'While within 3" of one or more friendly Leagues of Votann Vehicle or Ironkin Steeljacks units (and not an attached unit), has the Lone Operative ability.'),
         ability('Forgewrought Expertise', 'At the end of your Movement phase, this model can repair one friendly Leagues of Votann Vehicle, Exoframe, or Ironkin Steeljacks unit within 3" — one model regains up to D3 lost wounds (or up to 3 if an Ironkin Assistant is present). Each unit can only be repaired once per turn.'),
         ability('Leader', 'Can be attached to: Hearthkyn Warriors, Brôkhyr Thunderkyn.'),
     ]),

    ('Leagues of Votann Einhyr Champion', 70,
     stat('5"', 5, '2+', 5, '7+', 1, invuln='4+'),
     [
         rng('Autoch-pattern combi-bolter', '24"', '4', '2+', 4, 0, 1),
         mel('Mass hammer', '3', '3+', 12, -3, 'D6+1'),
     ],
     [
         ability('Invulnerable Save (4+)', 'This model has a 4+ invulnerable save (from Weavefield crest).'),
         ability('Exemplar of the Einhyr', 'While this model is leading a unit, add 1 to Advance and Charge rolls made for that unit.'),
         ability('Mass Driver Accelerators', 'Each time this model ends a Charge move, select one enemy unit within Engagement Range and roll one D6: on a 2–5, that enemy unit suffers D3 mortal wounds; on a 6, D3+3 mortal wounds.'),
         ability('Leader', 'Can be attached to: Einhyr Hearthguard.'),
     ]),

    ('Grimnyr', 65,
     stat('5"', 5, '4+', 4, '6+', 1, invuln='4+'),
     [
         rng('Ancestral Wrath – witchfire', '24"', '3', '3+', 6, -2, 'D3', 'Psychic'),
         rng('Ancestral Wrath – focused witchfire', '24"', '6', '3+', 6, -2, 'D3', 'Hazardous, Psychic'),
         rng('Autoch-pattern bolter', '24"', '2', '4+', 4, 0, 1),
         mel('Ancestral ward stave', '2', '3+', 7, -1, 'D3', 'Psychic'),
         mel('Close combat weapon', '1', '4+', 3, 0, 1),
     ],
     [
         ability('Invulnerable Save (4+)', 'Models in this unit have a 4+ invulnerable save.'),
         ability('Fortify (Psychic)', 'While this model is leading a unit, models in that unit have the Feel No Pain 5+ ability.'),
         ability("Grimnyr's Regard", 'Once per battle, at the start of any phase, select one friendly Leagues of Votann unit that is Battle-shocked and within 12" of this unit\'s Grimnyr model — that unit is no longer Battle-shocked.'),
         ability('Leader', 'Can be attached to: Hearthkyn Warriors.'),
     ]),

    ('Kahl', 65,
     stat('5"', 5, '3+', 4, '7+', 1, invuln='4+'),
     [
         rng('Autoch-pattern combi-bolter', '24"', '4', '2+', 4, 0, 1),
         mel('Forgewrought plasma axe', '4', '2+', 5, -2, 2),
     ],
     [
         ability('Invulnerable Save (4+)', 'This model has a 4+ invulnerable save.'),
         ability('Kindred Hero', 'While this model is leading a unit, weapons equipped by models in that unit have the [Lethal Hits] ability.'),
         ability('Seized Opportunity', 'Once per phase, when its unit destroys an enemy unit, gain 1YP.'),
         ability('Rampart crest', 'While this model is leading a unit, models in that unit have a 5+ invulnerable save.'),
         ability('Leader', 'Can be attached to: Einhyr Hearthguard, Hearthkyn Warriors.'),
     ]),

    ('Memnyr Strategist', 45,
     stat('5"', 5, '4+', 4, '7+', 1),
     [
         rng('Autoch-pattern bolt pistol', '12"', '1', '4+', 4, 0, 1, 'Pistol'),
         mel('Close combat weapon', '1', '4+', 3, 0, 1),
     ],
     [
         ability('Computational Mastermind', 'At the end of your Command phase, for each objective marker you control that has one or more models with this ability in range, you can spend 1YP or gain 1YP.'),
         ability('Predictive Guidance', 'Once per battle round, this model can target its unit with the Fire Overwatch or Heroic Intervention Stratagem for 0CP.'),
         ability('Leader', 'Can be attached to: Ironkin Steeljacks with Heavy Volkanite Disintegrators, Ironkin Steeljacks with Melee Weapons.'),
     ]),

    # ── Battleline ────────────────────────────────────────────────────────────

    ('Leagues of Votann Hearthkyn Warriors', 100,
     stat('5"', 5, '4+', 1, '7+', 2, fnp='6+'),
     [
         rng('Autoch-pattern bolt pistol', '12"', '1', '4+', 4, 0, 1, 'Pistol'),
         rng('Autoch-pattern bolter', '24"', '2', '4+', 4, 0, 1),
         mel('Close combat weapon', '1', '4+', 4, 0, 1),
     ],
     [
         ability('Luck Has, Need Keeps, Toil Earns', 'At the end of your Command phase, if this unit is within range of an objective marker you control, that objective marker remains under your control until your opponent\'s Level of Control exceeds yours at the end of a phase.'),
         ability('Pan-spectral Scanning', 'Each time a model in this unit makes a ranged attack, re-roll a Hit roll of 1.'),
         ability('Weavefield crest', 'Models in the bearer\'s unit have a 5+ invulnerable save.'),
     ]),

    # ── Infantry ──────────────────────────────────────────────────────────────

    ('Brokhyr Thunderkyn', 80,
     stat('5"', 6, '3+', 2, '7+', 1),
     [
         rng('Bolt cannon', '36"', '3', '4+', 6, -1, 2, 'Sustained Hits 2'),
         mel('Close combat weapon', '2', '4+', 4, 0, 1),
     ],
     [
         ability('Breaching Fire', 'In your Shooting phase, after this unit has shot, select one enemy unit hit by one or more of those attacks. Until the start of your next Shooting phase, that enemy unit cannot have the Benefit of Cover.'),
     ]),

    ('Cthonian Berserks', 100,
     stat('6"', 6, '5+', 1, '7+', 1, fnp='4+'),
     [
         mel('Heavy plasma axe', '3', '4+', 7, -2, 3),
     ],
     [
         ability('Cyberstimms', 'Each time a model in this unit is destroyed by a melee attack, if that model has not fought this phase, roll one D6: on a 4+, do not remove it from play — it can fight after the attacking unit has finished its attacks, then is removed from play.'),
     ]),

    ('Cthonian Earthshakers', 110,
     stat('4"', 6, '4+', 6, '7+', 2),
     [
         rng('Autoch-pattern bolt pistol', '12"', '1', '4+', 4, 0, 1, 'Pistol'),
         rng('Breacher ordnance', '24"', 'D6+1', '5+', 10, -1, 2, 'Blast, Heavy, Indirect Fire'),
         mel('Plasma picks', '4', '3+', 5, -2, 1),
     ],
     [
         ability('Geomantic Hunters', 'Up to twice per battle, in your Shooting phase when this unit is selected to shoot, it can use this ability — until end of phase, each time a model makes an attack with its breacher ordnance, you can re-roll the Wound roll.'),
     ]),

    ('Leagues of Votann Einhyr Hearthguard', 135,
     stat('5"', 5, '2+', 2, '7+', 1, invuln='5+'),
     [
         rng('EtaCarn plasma gun', '24"', '1', '3+', 7, -3, 2, 'Rapid Fire 1'),
         rng('Exo-armour grenade launcher', '24"', 'D3', '3+', 3, 0, 1, 'Blast'),
         mel('Concussion gauntlet', '2', '3+', 8, -2, 2),
     ],
     [
         ability('Decisive Destruction', 'Each time a model in this unit makes a ranged attack that targets the closest eligible target, re-roll a Hit roll of 1.'),
         ability('Weavefield crest', 'Models in the bearer\'s unit have a 5+ invulnerable save.'),
     ]),

    ('Kill Team: Hernkyn Yaegirs (Leagues of Votann)', 90,
     stat('6"', 5, '5+', 1, '7+', 1),
     [
         rng('Bolt shotgun', '18"', '2', '4+', 5, 0, 1, 'Assault'),
         mel('Close combat weapon', '1', '4+', 4, 0, 1),
     ],
     [
         ability('Pragmatic Hunters', 'Once per turn, when an enemy unit ends a Normal, Advance, or Fall Back move within 9" of this unit, it can make a Normal move of up to D6".'),
         ability('Infiltrators', 'During deployment, you can set up this unit anywhere on the battlefield that is more than 9" from the enemy deployment zone and any enemy models.'),
     ]),

    ('Ironkin Steeljacks', 85,
     stat('5"', 6, '2+', 3, '7+', 1),
     [
         rng('Heavy volkanite disintegrator', '24"', '6', '4+', 6, -1, 1, 'Devastating Wounds'),
         mel('Plasma knife', '2', '3+', 6, -2, 1),
     ],
     [
         ability('Purge Response', 'Each time you target this unit with the Fire Overwatch Stratagem, hits are scored on unmodified Hit rolls of 5+ (or 4+ if units from your army have Fortify Takeover).'),
         ability('Preymark crest', 'Each time a model in the bearer\'s unit makes an attack that targets an enemy unit within range of one or more objective markers, on a Critical Wound, that attack has the [Precision] ability.'),
     ]),

    # Note: DB has a single 'Ironkin Steeljacks' entry covering both variants.

    # ── Mounted ───────────────────────────────────────────────────────────────

    ('Leagues of Votann Hernkyn Pioneers', 80,
     stat('12"', 6, '4+', 3, '7+', 2),
     [
         rng('Bolt revolver', '12"', '1', '4+', 5, 0, 1, 'Pistol'),
         rng('Bolt shotgun', '18"', '2', '4+', 5, 0, 1, 'Assault'),
         rng('Magna-coil autocannon', '24"', '3', '4+', 7, -1, 2),
         mel('Plasma knife', '2', '4+', 4, -2, 1),
     ],
     [
         ability('Outflanking Mag-Riders', 'At the end of your opponent\'s turn, if this unit is wholly within 9" of one or more battlefield edges and not within Engagement Range of any enemy units, you can remove it from the battlefield and place it into Strategic Reserves.'),
         ability('Scouts 9"', 'Before the first battle round begins, this unit can make a Normal move of up to 9".'),
     ]),

    # ── Vehicles ──────────────────────────────────────────────────────────────

    ('Hekaton Land Fortress', 240,
     stat('10"', 12, '2+', 16, '7+', 5),
     [
         rng('MATR autocannon', '24"', '6', '4+', 7, -1, 2, 'Assault, Sustained Hits 1'),
         rng('Cyclic ion cannon', '24"', 'D6+2', '4+', 7, -2, 2, 'Blast'),
         rng('Twin bolt cannon', '36"', '3', '4+', 6, -1, 2, 'Sustained Hits 2, Twin-linked'),
         mel('Armoured wheels', '6', '4+', 8, 0, 1),
     ],
     [
         ability('MultiCOG Targeting', 'Each time this model makes a ranged attack, you can ignore any or all modifiers to that attack\'s Ballistic Skill characteristic and the Hit roll.'),
         ability('Damaged (1–5 wounds remaining)', 'While this model has 1–5 wounds remaining, subtract 1 from the Hit roll each time this model makes an attack.'),
         ability('Transport', 'Carries up to 14 Leagues of Votann Infantry models. Exoarmour, Exoframe, or Ironkin Steeljack models each take up 2 spaces. Cannot transport Artillery models.'),
     ]),

    ('Kapricus Defender/Carrier', 70,
     stat('12"', 7, '4+', 7, '7+', 2),
     [
         rng('Twin magna-coil autocannon', '24"', '3', '4+', 7, -1, 2, 'Twin-linked'),
         rng('Magna-rail cannon', '24"', '1', '4+', 14, -4, 'D3+3', 'Devastating Wounds, Heavy'),
         mel('Armoured hull', '3', '4+', 6, 0, 1),
     ],
     [
         ability('Opportunistic Manoeuvre', 'In your Shooting phase, after this unit has shot, it can make a Normal Move of up to D6". If it does, until the end of the turn, this unit is not eligible to declare a charge.'),
         ability('Smoke Launcher', 'Once per game, this model can use Smoke — until the start of your next turn, ranged attacks that target this unit suffer a -1 to Hit roll.'),
         ability('Scouts 9"', 'Before the first battle round begins, this unit can make a Normal move of up to 9".'),
     ]),

    # ── Dedicated Transports ──────────────────────────────────────────────────

    # Note: Kapricus Carrier shares the 'Kapricus Defender/Carrier' DB entry above.

    ('Sagitaur', 90,
     stat('12"', 9, '3+', 9, '7+', 2),
     [
         rng('Twin bolt cannon', '36"', '3', '4+', 6, -1, 2, 'Sustained Hits 2, Twin-linked'),
         rng('HYLas beam cannon', '24"', '2', '4+', 12, -3, 'D6+1'),
         mel('Armoured wheels', '3', '4+', 6, 0, 1),
     ],
     [
         ability('Blistering Advance', 'Units can disembark from this Transport after it has Advanced. Units that do so count as having made a Normal move, cannot declare a charge in the same turn, but can otherwise act normally.'),
         ability('Transport', 'Carries up to 6 Leagues of Votann Infantry models. Cannot transport Artillery, Exoarmour, Exoframe, or Ironkin Steeljack models. At the start of Declare Battle Formations, you can split one Hearthkyn Warriors unit into two halves — one must start embarked in this Transport, the other may embark elsewhere or deploy separately.'),
     ]),
]


class Command(BaseCommand):
    """Seed Leagues of Votann stat lines, weapon profiles, and abilities."""

    help = 'Seed Leagues of Votann points, stats, weapons, and abilities.'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true',
                            help='Show what would be updated without saving.')

    @transaction.atomic
    def handle(self, *args, **options):
        dry_run = options['dry_run']

        try:
            faction = Faction.objects.get(name='Leagues of Votann')
        except Faction.DoesNotExist:
            self.stderr.write(self.style.ERROR('Leagues of Votann faction not found.'))
            return

        updated = created_w = created_a = skipped = 0

        for unit_name, points, stats, weapons, abilities in VOTANN_UNITS:
            qs = UnitType.objects.filter(faction=faction, name=unit_name)
            if not qs.exists():
                self.stdout.write(self.style.WARNING(f'  [skip] No UnitType found: "{unit_name}"'))
                skipped += 1
                continue

            unit = qs.first()

            if dry_run:
                self.stdout.write(f'  [dry-run] Would update: {unit_name} — {points}pts')
                continue

            # Update points and stat line
            for field, value in stats.items():
                setattr(unit, field, value)
            unit.points_cost = points
            unit.save()
            updated += 1

            # Replace weapon profiles
            unit.weapon_profiles.all().delete()
            for i, w in enumerate(weapons):
                WeaponProfile.objects.create(unit_type=unit, order=i, **w)
                created_w += 1

            # Replace abilities
            unit.abilities.all().delete()
            for i, a in enumerate(abilities):
                UnitAbility.objects.create(unit_type=unit, order=i, **a)
                created_a += 1

            self.stdout.write(
                self.style.SUCCESS(
                    f'  [ok] {unit_name} — {points}pts | '
                    f'{len(weapons)} weapons | {len(abilities)} abilities'
                )
            )

        self.stdout.write(
            f'\nDone — updated: {updated} | weapons: {created_w} | '
            f'abilities: {created_a} | skipped: {skipped}'
            + (' (dry run)' if dry_run else '')
        )
