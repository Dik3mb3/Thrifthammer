"""Migration 0006 — Set correct points costs for all Combat Patrol combo boxes."""

from django.db import migrations

# (faction_name, points_cost)
PATROL_POINTS = [
    ('Adeptus Mechanicus',  295),
    ('Aeldari',             490),
    ('Astra Militarum',     295),
    ('Black Templars',      380),
    ('Blood Angels',        490),
    ('Chaos Space Marines', 390),
    ('Custodes',            780),   # DB name is Custodes
    ('Dark Angels',         445),
    ('Death Guard',         405),
    ('Drukhari',            460),
    ('Genestealer Cults',   380),
    ('Grey Knights',        675),
    ('Leagues of Votann',   370),
    ('Necrons',             450),
    ('Orks',                430),
    ('Sisters of Battle',   365),
    ('Space Marines',       430),
    ('Space Wolves',        430),
    ("T'au Empire",         370),
    ('Thousand Sons',       405),
    ('Tyranids',            445),
    ('World Eaters',        505),
]


def set_points(apps, schema_editor):
    """Update points_cost on all combo_box UnitType entries."""
    UnitType = apps.get_model('calculators', 'UnitType')
    Faction  = apps.get_model('products',    'Faction')

    for faction_name, pts in PATROL_POINTS:
        faction = Faction.objects.filter(name=faction_name).first()
        if not faction:
            continue
        UnitType.objects.filter(
            faction=faction,
            category='combo_box',
        ).update(points_cost=pts)


def clear_points(apps, schema_editor):
    """Reset points_cost to 0 (reverse migration)."""
    UnitType = apps.get_model('calculators', 'UnitType')
    UnitType.objects.filter(category='combo_box').update(points_cost=0)


class Migration(migrations.Migration):
    dependencies = [('calculators', '0005_combat_patrol_unit_types')]
    operations = [migrations.RunPython(set_points, clear_points)]
