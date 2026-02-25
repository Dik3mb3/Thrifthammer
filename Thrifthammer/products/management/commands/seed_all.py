"""
Management command: seed_all

Runs the full data pipeline in the correct order:
    1. populate_products  — creates/updates all Products, Factions, Prices
    2. populate_units     — creates UnitType rows for every (product, faction) pair
    3. seed_*_points      — sets points_cost on each faction's UnitType rows

Usage:
    python manage.py seed_all

Options:
    --skip-products   Skip populate_products (useful if products are already seeded)
    --skip-units      Skip populate_units (useful if units are already seeded)
    --faction NAME    Only run the seed command for a single faction
                      (e.g. --faction orks)

This command is fully idempotent — safe to re-run at any time.
"""

from django.core.management import call_command
from django.core.management.base import BaseCommand


# Ordered list of all faction seed commands.
# Add new factions here as they are created.
FACTION_SEEDS = [
    # ── Space Marines ─────────────────────────────────────────────────────────
    ('ultramarines',        'seed_ultramarines_points'),
    ('blood_angels',        'seed_blood_angels_points'),
    ('dark_angels',         'seed_dark_angels_points'),
    ('black_templars',      'seed_black_templars_points'),
    ('deathwatch',          'seed_deathwatch_points'),
    ('space_wolves',        'seed_space_wolves_points'),
    # ── Imperium ──────────────────────────────────────────────────────────────
    ('sisters',             'seed_sisters_points'),
    ('custodes',            'seed_custodes_points'),
    ('mechanicus',          'seed_mechanicus_points'),
    ('agents',              'seed_agents_points'),
    ('militarum',           'seed_militarum_points'),
    ('grey_knights',        'seed_grey_knights_points'),
    ('imperial_knights',    'seed_imperial_knights_points'),
    # ── Chaos ─────────────────────────────────────────────────────────────────
    ('chaos_daemons',       'seed_chaos_daemons_points'),
    ('chaos_space_marines', 'seed_chaos_space_marines_points'),
    ('death_guard',         'seed_death_guard_points'),
    ('emperors_children',   'seed_emperors_children_points'),
    ('thousand_sons',       'seed_thousand_sons_points'),
    ('world_eaters',        'seed_world_eaters_points'),
    ('chaos_knights',       'seed_chaos_knights_points'),
    # ── Xenos ─────────────────────────────────────────────────────────────────
    ('aeldari',             'seed_aeldari_points'),
    ('drukhari',            'seed_drukhari_points'),
    ('genestealer_cults',   'seed_genestealer_cults_points'),
    ('leagues_of_votann',   'seed_leagues_of_votann_points'),
    ('necrons',             'seed_necrons_points'),
    ('orks',                'seed_orks_points'),
    ('tau',                 'seed_tau_points'),
    ('tyranids',            'seed_tyranids_points'),
]


class Command(BaseCommand):
    """
    Run the full populate + seed pipeline in one command.

    Steps:
        1. populate_products  (can be skipped with --skip-products)
        2. populate_units     (can be skipped with --skip-units)
        3. All faction seed_*_points commands (or a single one via --faction)
    """

    help = 'Run the full data pipeline: populate products, units, and all faction points.'

    def add_arguments(self, parser):
        """Register optional CLI flags."""
        parser.add_argument(
            '--skip-products',
            action='store_true',
            help='Skip populate_products (products already in DB).',
        )
        parser.add_argument(
            '--skip-units',
            action='store_true',
            help='Skip populate_units (UnitType rows already created).',
        )
        parser.add_argument(
            '--faction',
            type=str,
            default=None,
            metavar='NAME',
            help=(
                'Only seed a single faction. Use the short name from this list: '
                + ', '.join(slug for slug, _ in FACTION_SEEDS)
            ),
        )

    def handle(self, *args, **options):
        """Entry point — run the full pipeline."""
        skip_products = options['skip_products']
        skip_units = options['skip_units']
        faction_filter = options['faction']

        self.stdout.write(self.style.MIGRATE_HEADING('\n=== ThriftHammer Full Seed Pipeline ===\n'))

        # ── Step 1: populate_products ─────────────────────────────────────────
        if skip_products:
            self.stdout.write('  [skip] populate_products (--skip-products flag set)\n')
        else:
            self.stdout.write(self.style.MIGRATE_LABEL('▶ Running populate_products…\n'))
            call_command('populate_products', verbosity=1)
            self.stdout.write(self.style.SUCCESS('✓ populate_products complete\n'))

        # ── Step 2: populate_units ────────────────────────────────────────────
        if skip_units:
            self.stdout.write('  [skip] populate_units (--skip-units flag set)\n')
        else:
            self.stdout.write(self.style.MIGRATE_LABEL('▶ Running populate_units…\n'))
            call_command('populate_units', verbosity=1)
            self.stdout.write(self.style.SUCCESS('✓ populate_units complete\n'))

        # ── Step 3: faction seed commands ─────────────────────────────────────
        if faction_filter:
            # Find the matching seed command
            match = next(
                ((slug, cmd) for slug, cmd in FACTION_SEEDS if slug == faction_filter),
                None,
            )
            if not match:
                valid = ', '.join(slug for slug, _ in FACTION_SEEDS)
                self.stdout.write(self.style.ERROR(
                    f'Unknown faction "{faction_filter}". Valid options: {valid}'
                ))
                return
            seeds_to_run = [match]
        else:
            seeds_to_run = FACTION_SEEDS

        self.stdout.write(self.style.MIGRATE_LABEL(
            f'\n▶ Seeding points for {len(seeds_to_run)} faction(s)…\n'
        ))

        success_count = 0
        error_count = 0

        for slug, command_name in seeds_to_run:
            self.stdout.write(f'\n  ── {command_name} ──')
            try:
                call_command(command_name, verbosity=1)
                success_count += 1
            except Exception as exc:  # noqa: BLE001
                self.stdout.write(self.style.ERROR(
                    f'  ERROR running {command_name}: {exc}'
                ))
                error_count += 1

        # ── Summary ───────────────────────────────────────────────────────────
        self.stdout.write(self.style.MIGRATE_HEADING(
            f'\n=== Pipeline complete: {success_count} succeeded, {error_count} failed ===\n'
        ))

        if error_count:
            self.stdout.write(self.style.WARNING(
                'Some seed commands failed. Check the output above for details.'
            ))
        else:
            self.stdout.write(self.style.SUCCESS(
                'All faction points seeded successfully!'
            ))
