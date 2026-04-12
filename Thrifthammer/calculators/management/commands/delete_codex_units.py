"""
Management command: delete_codex_units

Removes all codex/supplement book entries from the UnitType table so
they no longer appear in the army calculator. Safe to re-run.

Usage:
    python manage.py delete_codex_units
    python manage.py delete_codex_units --dry-run
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from calculators.models import UnitType


class Command(BaseCommand):
    """Delete codex and codex supplement UnitType entries from the army calculator."""

    help = 'Remove codex book entries from the army calculator UnitType table.'

    def add_arguments(self, parser):
        """Add --dry-run flag."""
        parser.add_argument(
            '--dry-run', action='store_true',
            help='Preview deletions without writing to the database.',
        )

    def handle(self, *args, **options):
        """Find and delete all UnitType entries whose names start with Codex."""
        dry_run = options['dry_run']

        qs = UnitType.objects.filter(name__icontains='codex')
        count = qs.count()

        if count == 0:
            self.stdout.write(self.style.SUCCESS('No codex entries found — nothing to do.'))
            return

        for unit in qs.order_by('name'):
            self.stdout.write(f'  {"DRY-RUN " if dry_run else ""}DELETE: [{unit.pk}] {unit.name}')

        if dry_run:
            self.stdout.write(self.style.WARNING(
                f'\nDry run -- {count} entries would be deleted, no changes written.'
            ))
            return

        with transaction.atomic():
            qs.delete()

        self.stdout.write(self.style.SUCCESS(f'\nDone. {count} codex entries deleted.'))
