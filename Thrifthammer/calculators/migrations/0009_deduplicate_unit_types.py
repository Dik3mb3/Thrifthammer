"""
Migration 0009: Delete all duplicate UnitType entries.

For each (name, faction) group with more than one entry, keep the entry
with the highest points_cost (i.e. the seeded one). When all entries in a
group share the same points_cost, keep the one with the lowest pk (the
original). All others are deleted.

Affected groups found on 2026-04-12:
  - Roboute Guilliman (Space Marines)           x43 duplicates, all 0pts
  - Marneus Calgar in Armour of Antilochus      x43 duplicates, all 0pts
  - Seraptek Heavy Construct with Synaptic Obliterators  x5, all 0pts
  - Rhino (Space Marines)                       x2  — keep pk with 70pts
  - Techmarine (Space Marines)                  x2  — keep pk with 70pts
"""

from django.db import migrations


def deduplicate_unit_types(apps, schema_editor):
    """Keep one canonical UnitType per (name, faction) — delete the rest."""
    UnitType = apps.get_model('calculators', 'UnitType')

    # Collect all (name, faction_id) groups that have more than one entry.
    seen = {}
    for unit in UnitType.objects.order_by('pk'):
        key = (unit.name, unit.faction_id)
        seen.setdefault(key, []).append(unit)

    to_delete = []
    for key, units in seen.items():
        if len(units) <= 1:
            continue
        # Pick the keeper: highest points_cost first, then lowest pk.
        keeper = max(units, key=lambda u: (u.points_cost or 0, -u.pk))
        for unit in units:
            if unit.pk != keeper.pk:
                to_delete.append(unit.pk)

    if to_delete:
        deleted, _ = UnitType.objects.filter(pk__in=to_delete).delete()
        print(f'  Deleted {deleted} duplicate UnitType entries.')


class Migration(migrations.Migration):

    dependencies = [
        ('calculators', '0008_delete_seraptek_duplicates'),
    ]

    operations = [
        migrations.RunPython(
            code=deduplicate_unit_types,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
