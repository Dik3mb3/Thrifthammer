"""
Batch fix apr2026ae — Deactivate Space Marines UnitTypes whose excluded
mapping rows had blank db_name, causing the deactivation lookup to fail
(card_name did not match the actual UnitType.name in the DB).

Units deactivated:
  - Space Marine Judiciar     — mapping row "Judiciar" had blank db_name
  - Space Marine Suppressors  — mapping row "Suppressor Squad" had blank db_name
  - Suppressors               — bare-name duplicate, no SKU

Safe to re-run (idempotent).
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from calculators.models import UnitType
from products.models import Faction


_DEACTIVATE = [
    "Space Marine Judiciar",
    "Space Marine Suppressors",
    "Suppressors",
]


class Command(BaseCommand):
    """Hide Space Marines UnitTypes that the mapping excluded but whose lookup
    previously failed due to a name mismatch (blank db_name in mapping CSV)."""

    help = (
        'Deactivate Space Marines UnitTypes that were not caught by the '
        'import_faction_stats deactivation loop due to blank db_name in the '
        'mapping CSV.'
    )

    def handle(self, *args, **options):
        """Deactivate each named UnitType in the Space Marines faction."""
        try:
            faction = Faction.objects.get(name='Space Marines')
        except Faction.DoesNotExist:
            self.stdout.write(self.style.ERROR(
                'Space Marines faction not found — skipping.'
            ))
            return

        with transaction.atomic():
            hidden = 0
            already = 0
            missing = 0

            for name in _DEACTIVATE:
                try:
                    unit = UnitType.objects.get(name=name, faction=faction)
                except UnitType.DoesNotExist:
                    self.stdout.write(f'  NOT FOUND: {name!r}')
                    missing += 1
                    continue

                if not unit.is_active:
                    self.stdout.write(f'  already hidden: {name!r}')
                    already += 1
                    continue

                unit.is_active = False
                unit.save(update_fields=['is_active'])
                self.stdout.write(
                    self.style.WARNING(f'  HIDDEN: {name!r}')
                )
                hidden += 1

        self.stdout.write(self.style.SUCCESS(
            f'\napr2026ae complete: {hidden} hidden, '
            f'{already} already hidden, {missing} not found.'
        ))
