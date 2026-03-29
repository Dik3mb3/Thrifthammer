"""
Migration 0005 — Create UnitType entries for all Combat Patrol combo boxes.

Creates one UnitType per faction that has a tagged Combat Patrol product,
using the 'combo_box' category added in migration 0004.
Points are set to 0 and will be updated via a follow-up migration once
the user provides the correct values.
"""

from django.db import migrations

# (product_name, faction_name) pairs used to look up product and faction
COMBAT_PATROLS = [
    ('Adeptus Mechanicus Combat Patrol', 'Adeptus Mechanicus'),
    ('Aeldari Combat Patrol',            'Aeldari'),
    ('Astra Militarum Combat Patrol',    'Astra Militarum'),
    ('Black Templars Combat Patrol',     'Black Templars'),
    ('Blood Angels Combat Patrol',       'Blood Angels'),
    ('Chaos Space Marines Combat Patrol','Chaos Space Marines'),
    ('Adeptus Custodes Combat Patrol',   'Custodes'),
    ('Dark Angels Combat Patrol',        'Dark Angels'),
    ('Death Guard Combat Patrol',        'Death Guard'),
    ('Drukhari Combat Patrol',           'Drukhari'),
    ('Genestealer Cults Combat Patrol',  'Genestealer Cults'),
    ('Grey Knights Combat Patrol',       'Grey Knights'),
    ('Leagues of Votann Combat Patrol',  'Leagues of Votann'),
    ('Necron Combat Patrol',             'Necrons'),
    ('Ork Combat Patrol',                'Orks'),
    ('Adepta Sororitas Combat Patrol',   'Sisters of Battle'),
    ('Space Marine Combat Patrol',       'Space Marines'),
    ('Space Wolves Combat Patrol',       'Space Wolves'),
    ("T'au Combat Patrol",               "T'au Empire"),
    ('Thousand Sons Combat Patrol',      'Thousand Sons'),
    ('Tyranid Combat Patrol',            'Tyranids'),
    ('World Eaters Combat Patrol',       'World Eaters'),
]


def create_combat_patrol_units(apps, schema_editor):
    """Create a combo_box UnitType for every Combat Patrol product."""
    UnitType = apps.get_model('calculators', 'UnitType')
    Product  = apps.get_model('products',    'Product')
    Faction  = apps.get_model('products',    'Faction')

    for product_name, faction_name in COMBAT_PATROLS:
        product = Product.objects.filter(name=product_name, is_active=True).first()
        faction = Faction.objects.filter(name=faction_name).first()

        if not product or not faction:
            continue

        UnitType.objects.update_or_create(
            product=product,
            faction=faction,
            defaults={
                'name':             product.name,
                'category':         'combo_box',
                'points_cost':      0,
                'typical_quantity': 1,
                'description':      '',
                'is_active':        True,
            },
        )


def remove_combat_patrol_units(apps, schema_editor):
    """Remove combo_box UnitType entries created by this migration."""
    UnitType = apps.get_model('calculators', 'UnitType')
    UnitType.objects.filter(category='combo_box').delete()


class Migration(migrations.Migration):
    dependencies = [('calculators', '0004_add_combo_box_category')]
    operations = [migrations.RunPython(create_combat_patrol_units, remove_combat_patrol_units)]
