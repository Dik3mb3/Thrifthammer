"""
Management command: set_parent_factions

Assigns parent_faction relationships so sub-factions automatically inherit
base-faction units in the Army Calculator.

Current mappings (10th Edition):
  Space Marines sub-factions -> Space Marines base
    - Ultramarines, Blood Angels, Dark Angels, Black Templars,
      Space Wolves, Deathwatch
  Excluded (use own datasheets only):
    - Grey Knights (removed -- GK don't use generic SM datasheets)

Idempotent — safe to re-run; only updates rows where parent_faction differs.

Usage:
    python manage.py set_parent_factions
"""

from django.core.management.base import BaseCommand

from products.models import Faction

# Map sub-faction name -> parent faction name
PARENT_FACTION_MAP = {
    # Space Marines chapters -> Space Marines base rules
    'Ultramarines':  'Space Marines',
    'Blood Angels':  'Space Marines',
    'Dark Angels':   'Space Marines',
    'Black Templars': 'Space Marines',
    'Space Wolves':  'Space Marines',
    'Deathwatch':    'Space Marines',
    # Grey Knights intentionally excluded -- they use their own datasheets only.
    # GK Brotherhood Chaplain and Librarian are added as explicit GK UnitType
    # records by apply_unit_classification_fixes.
}


class Command(BaseCommand):
    """Set parent_faction FK for sub-factions that inherit base-faction units."""

    help = 'Assign parent_faction relationships for sub-factions (e.g. Ultramarines -> Space Marines).'

    def handle(self, *args, **options):
        """Iterate mappings and update parent_faction where needed."""
        self.stdout.write('Setting parent faction relationships…\n')
        updated = 0
        skipped = 0

        for sub_name, parent_name in PARENT_FACTION_MAP.items():
            parent = Faction.objects.filter(name=parent_name).first()
            if not parent:
                self.stdout.write(self.style.WARNING(
                    f'  [skip]  Parent "{parent_name}" not found — run populate_products first.'
                ))
                skipped += 1
                continue

            rows = Faction.objects.filter(name=sub_name).exclude(parent_faction=parent)
            count = rows.update(parent_faction=parent)
            if count:
                self.stdout.write(f'  [set]   {sub_name} -> {parent_name}')
                updated += 1
            else:
                self.stdout.write(f'  [ok]    {sub_name} -> {parent_name} (already set)')
                skipped += 1

        self.stdout.write(self.style.SUCCESS(
            f'\nDone! Updated: {updated}  |  Already correct: {skipped}'
        ))
