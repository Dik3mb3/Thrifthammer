"""Migration 0020 — Correct stats for Deathwatch, Drukhari, GSC, Grey Knights, Imperial Knights, Necrons, Orks."""

from django.db import migrations


CORRECTIONS = {
    'Deathwatch': {
        'difficulty': 'Advanced',
        'model_count_rating': 'Low-Medium',
        'playstyle': 'Customizable Elite Kill Teams',
    },
    'Drukhari': {
        'difficulty': 'Advanced',
        'model_count_rating': 'Medium-High',
        'playstyle': 'Speed',
        'price_range_display': '$$$',
    },
    'Genestealer Cults': {
        'difficulty': 'Extreme',
        'model_count_rating': 'Very High',
        'painting_complexity': 'Extreme',
        'playstyle': 'Horde Recursion',
        'price_range_display': '$$$$$',
    },
    'Grey Knights': {
        'difficulty': 'Intermediate-Advanced',
        'painting_complexity': 'Very Easy',
        'price_range_display': '$',
    },
    'Imperial Knights': {
        'painting_complexity': 'Intermediate',
        'playstyle': 'High Volume Shooting and Durability',
        'price_range_display': '$$-$$$$',
    },
    'Necrons': {
        'playstyle': 'Durable Control',
        'price_range_display': '$$$',
    },
    'Orks': {
        'painting_complexity': 'Medium-High',
        'price_range_display': '$$$$',
        'playstyle': 'High Volume High Variance Shooting/Melee',
    },
}


def apply(apps, schema_editor):
    Faction = apps.get_model('products', 'Faction')
    for name, fields in CORRECTIONS.items():
        Faction.objects.filter(name=name).update(**fields)


def reverse(apps, schema_editor):
    Faction = apps.get_model('products', 'Faction')
    originals = {
        'Deathwatch': {'difficulty': 'Intermediate', 'model_count_rating': 'Low', 'playstyle': 'Elite Strike Force'},
        'Drukhari': {'difficulty': 'Advanced', 'model_count_rating': 'Medium', 'playstyle': 'Lightning Raids', 'price_range_display': '$$'},
        'Genestealer Cults': {'difficulty': 'Advanced', 'model_count_rating': 'Medium-High', 'painting_complexity': 'Medium', 'playstyle': 'Ambush', 'price_range_display': '$$'},
        'Grey Knights': {'difficulty': 'Intermediate', 'painting_complexity': 'Medium-High', 'price_range_display': '$$$'},
        'Imperial Knights': {'painting_complexity': 'High', 'playstyle': 'Titanic Firepower', 'price_range_display': '$$$$$'},
        'Necrons': {'playstyle': 'Durable Attrition', 'price_range_display': '$$'},
        'Orks': {'painting_complexity': 'Easy', 'price_range_display': '$', 'playstyle': 'Horde Melee'},
    }
    for name, fields in originals.items():
        Faction.objects.filter(name=name).update(**fields)


class Migration(migrations.Migration):
    dependencies = [('products', '0019_seven_faction_pages')]
    operations = [migrations.RunPython(apply, reverse)]
