"""
Management command: delete_legacy_guard_units

Removes the two Guard UnitType rows that were created without a product
mapping and should not appear in the Army Calculator.

Units removed:
  - Astra Militarum Infantry Squad
  - Astra Militarum Veteran Guardsmen

Safe to re-run — silently skips units that are already gone.

Usage:
    python manage.py delete_legacy_guard_units
    python manage.py delete_legacy_guard_units --dry-run
"""

from django.core.management.base import BaseCommand

from calculators.models import UnitType

LEGACY_NAMES = [
    'Astra Militarum Infantry Squad',
    'Astra Militarum Veteran Guardsmen',
]


class Command(BaseCommand):
    """Delete unmapped legacy Guard units from the Army Calculator."""

    help = 'Remove legacy Astra Militarum units that have no product mapping.'

    def add_arguments(self, parser):
        """Add --dry-run flag."""
        parser.add_argument(
            '--dry-run', action='store_true',
            help='Preview deletions without writing to the database.',
        )

    def handle(self, *args, **options):
        """Delete each legacy unit by name."""
        dry_run = options['dry_run']

        for name in LEGACY_NAMES:
            try:
                unit = UnitType.objects.get(name=name)
                if dry_run:
                    self.stdout.write(f'  DRY-RUN: would delete {name!r}')
                else:
                    unit.delete()
                    self.stdout.write(self.style.SUCCESS(f'  Deleted: {name!r}'))
            except UnitType.DoesNotExist:
                self.stdout.write(self.style.WARNING(f'  Not found (already gone): {name!r}'))

        if dry_run:
            self.stdout.write(self.style.WARNING('\nDry run — no changes written.'))
        else:
            self.stdout.write(self.style.SUCCESS('\nDone.'))
