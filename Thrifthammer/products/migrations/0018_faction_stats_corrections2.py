"""Migration 0018 — Correct stats for Black Templars, Blood Angels, CSM, Dark Angels, Death Guard."""

from django.db import migrations


CORRECTIONS = {
    'Black Templars': {
        'difficulty': 'Easy-Intermediate',
        'model_count_rating': 'Medium-High',
        'price_range_display': '$$$',
    },
    'Blood Angels': {
        'difficulty': 'Easy',
        'model_count_rating': 'Medium',
        'painting_complexity': 'Easy',
        'playstyle': 'Aggressive Melee',
        'price_range_display': '$$',
    },
    'Chaos Space Marines': {
        'difficulty': 'Easy-Intermediate',
    },
    'Dark Angels': {
        'difficulty': 'Beginner Friendly',
        'painting_complexity': 'Easy',
        'playstyle': 'Varies',
    },
    'Death Guard': {
        'model_count_rating': 'Medium',
        'painting_complexity': 'Easy-Medium',
        'playstyle': 'Debuff Focus/Durable',
        'price_range_display': '$$',
    },
}


def apply(apps, schema_editor):
    Faction = apps.get_model('products', 'Faction')
    for name, fields in CORRECTIONS.items():
        Faction.objects.filter(name=name).update(**fields)


def reverse(apps, schema_editor):
    Faction = apps.get_model('products', 'Faction')
    originals = {
        'Black Templars': {'difficulty': 'Beginner Friendly', 'model_count_rating': 'Low-Medium', 'price_range_display': '$$'},
        'Blood Angels': {'difficulty': 'Intermediate', 'model_count_rating': 'Low-Medium', 'painting_complexity': 'Medium', 'playstyle': 'Assault Elite', 'price_range_display': '$$'},
        'Chaos Space Marines': {'difficulty': 'Intermediate'},
        'Dark Angels': {'difficulty': 'Intermediate', 'painting_complexity': 'Medium', 'playstyle': 'Balanced Dual-Wing'},
        'Death Guard': {'model_count_rating': 'Low-Medium', 'painting_complexity': 'Medium-High', 'playstyle': 'Attrition', 'price_range_display': '$$'},
    }
    for name, fields in originals.items():
        Faction.objects.filter(name=name).update(**fields)


class Migration(migrations.Migration):
    dependencies = [('products', '0017_five_faction_pages')]
    operations = [migrations.RunPython(apply, reverse)]
