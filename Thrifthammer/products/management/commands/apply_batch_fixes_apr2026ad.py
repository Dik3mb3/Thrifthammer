"""
Batch fix apr2026ad — Deactivate stale / unstatted Space Marines UnitTypes.

These UnitTypes exist in the DB but have no stats in the parsed card JSON and
are not mapped with include=Yes in the spacemarines mapping CSV. They were
showing in the army calculator with 0 pts. This command sets is_active=False
so they are hidden from the calculator.

Units deactivated:
  - Captain with Jump Pack and Relic Shield (48-105)  — separate kit; no JSON stats
  - Lieutenant with Power Sword          (48-122)  — not in parsed JSON
  - Lieutenant with Storm Shield         (48-123)  — not in parsed JSON
  - Space Marine Land Raider             (no SKU)  — stale duplicate; Crusader is canonical
  - Codex: Space Marines                 (48-110)  — rulebook product, not a playable unit
  - Space Marine Combat Patrol           (71-02)   — patrol box, not a playable unit

Safe to re-run (idempotent).
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from calculators.models import UnitType
from products.models import Faction


_DEACTIVATE = [
    "Captain with Jump Pack and Relic Shield",
    "Lieutenant with Power Sword",
    "Lieutenant with Storm Shield",
    "Space Marine Land Raider",
    "Codex: Space Marines",
    "Space Marine Combat Patrol",
]


class Command(BaseCommand):
    """Hide stale / unstatted Space Marines UnitTypes from the army calculator."""

    help = (
        'Deactivate stale Space Marines UnitTypes that have no parsed-card '
        'stats and should not appear in the army calculator.'
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
            f'\napr2026ad complete: {hidden} hidden, '
            f'{already} already hidden, {missing} not found.'
        ))
