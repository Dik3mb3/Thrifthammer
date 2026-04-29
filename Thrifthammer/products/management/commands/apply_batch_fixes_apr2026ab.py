"""
Management command: apply_batch_fixes_apr2026ab

Delete stale Daemon Prince "with Wings" (capital W) UnitType records left
behind after the sync_cross_faction_units rename to lowercase "wings".

Background: sync_cross_faction_units uses update_or_create keyed on
(name, faction). When the name changed from "with Wings" → "with wings",
it created a NEW row (lowercase) instead of updating the old one (capital),
leaving both in the DB and producing duplicates in the army calculator.

Affected factions: Death Guard, Thousand Sons, World Eaters.
Emperor's Children is intentionally excluded — its CSV still uses capital W
and its sync entry was never changed, so no duplicate was created there.

Idempotent — safe to re-run (does nothing if records are already gone).
"""

from django.core.management.base import BaseCommand

from calculators.models import UnitType


STALE_RECORDS = [
    ("Death Guard",    "Daemon Prince of Nurgle with Wings"),
    ("Thousand Sons",  "Daemon Prince of Tzeentch with Wings"),
    ("World Eaters",   "Daemon Prince of Khorne with Wings"),
]


class Command(BaseCommand):
    """Delete stale capital-W Daemon Prince with Wings UnitType duplicates."""

    help = (
        'Remove stale "Daemon Prince of X with Wings" (capital W) UnitType '
        'records left over from the sync_cross_faction_units rename.'
    )

    def handle(self, *args, **options):
        """Run the cleanup."""
        deleted_total = 0

        for faction_name, unit_name in STALE_RECORDS:
            qs = UnitType.objects.filter(
                name=unit_name,
                faction__name=faction_name,
            )
            count = qs.count()
            if count == 0:
                self.stdout.write(
                    f'  [skip] "{unit_name}" ({faction_name}) — already gone.'
                )
                continue

            qs.delete()
            deleted_total += count
            self.stdout.write(self.style.SUCCESS(
                f'  [deleted] "{unit_name}" ({faction_name})'
            ))

        self.stdout.write(self.style.SUCCESS(
            f'\nDone. {deleted_total} stale record(s) removed.'
        ))
