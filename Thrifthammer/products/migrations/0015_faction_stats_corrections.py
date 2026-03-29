"""Migration 0015 — Correct quick-stat values for AdMech, Aeldari, Astra Militarum."""

from django.db import migrations


CORRECTIONS = {
    'Adeptus Mechanicus': {
        'difficulty': 'Advanced',
        'model_count_rating': 'High',
        'painting_complexity': 'Extreme',
        'price_range_display': '$$$$$',
    },
    'Aeldari': {
        'model_count_rating': 'Low-Medium',
        'painting_complexity': 'Medium',
        'playstyle': 'Speed',
        'price_range_display': '$$$',
    },
    'Astra Militarum': {
        'difficulty': 'Intermediate-Advanced',
        'model_count_rating': 'High',
        'painting_complexity': 'High',
        'playstyle': 'Horde/Vehicle Shooting',
        'price_range_display': '$$$$',
    },
}

ORIGINALS = {
    'Adeptus Mechanicus': {
        'difficulty': 'Intermediate',
        'model_count_rating': 'Medium',
        'painting_complexity': 'High',
        'price_range_display': '$',
    },
    'Aeldari': {
        'model_count_rating': 'Medium',
        'painting_complexity': 'Medium-High',
        'playstyle': 'Speed and Flexibility',
        'price_range_display': '$$',
    },
    'Astra Militarum': {
        'difficulty': 'Beginner Friendly',
        'model_count_rating': 'High',
        'painting_complexity': 'Easy-Medium',
        'playstyle': 'Horde Shooting',
        'price_range_display': '$',
    },
}


def apply_corrections(apps, schema_editor):
    Faction = apps.get_model('products', 'Faction')
    for name, fields in CORRECTIONS.items():
        Faction.objects.filter(name=name).update(**fields)


def reverse_corrections(apps, schema_editor):
    Faction = apps.get_model('products', 'Faction')
    for name, fields in ORIGINALS.items():
        Faction.objects.filter(name=name).update(**fields)


class Migration(migrations.Migration):
    dependencies = [('products', '0014_three_faction_pages')]
    operations = [migrations.RunPython(apply_corrections, reverse_corrections)]
