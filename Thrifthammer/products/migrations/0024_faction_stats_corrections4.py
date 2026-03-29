"""Migration 0024 — Stat corrections for Sisters of Battle, Space Wolves, T'au Empire,
Thousand Sons, Tyranids, World Eaters."""

from django.db import migrations

CORRECTIONS = {
    'Sisters of Battle': {
        'difficulty': 'Intermediate-Advanced',
        'model_count_rating': 'Medium-High',
        'playstyle': 'Aggressive Glass Cannon',
        'price_range_display': '$$$$',
    },
    'Space Wolves': {
        'difficulty': 'Beginner Friendly',
        'model_count_rating': 'Medium',
        'painting_complexity': 'Easy-Medium',
    },
    "T'au Empire": {
        'difficulty': 'Intermediate-Advanced',
        'model_count_rating': 'Medium',
        'painting_complexity': 'Medium',
        'playstyle': 'Pure Gunline',
        'price_range_display': '$$$$',
    },
    'Thousand Sons': {
        'painting_complexity': 'Extreme',
        'price_range_display': '$$',
    },
    'Tyranids': {
        'model_count_rating': 'Medium-High',
        'painting_complexity': 'Easy-Medium',
        'playstyle': 'Monster Mash / Horde Swarm',
        'price_range_display': '$$-$$$$',
    },
    'World Eaters': {
        'difficulty': 'Easy-Intermediate',
        'painting_complexity': 'High',
        'playstyle': 'Pure Melee Pressure',
        'price_range_display': '$$$',
    },
}

ORIGINALS = {
    'Sisters of Battle': {
        'difficulty': 'Intermediate',
        'model_count_rating': 'Medium',
        'playstyle': 'Faith-Powered Shooting',
        'price_range_display': '$$$',
    },
    'Space Wolves': {
        'difficulty': 'Intermediate',
        'model_count_rating': 'Low-Medium',
        'painting_complexity': 'Medium',
    },
    "T'au Empire": {
        'difficulty': 'Intermediate',
        'model_count_rating': 'Low-Medium',
        'painting_complexity': 'Easy-Medium',
        'playstyle': 'Long-Range Shooting',
        'price_range_display': '$$$',
    },
    'Thousand Sons': {
        'painting_complexity': 'High',
        'price_range_display': '$$$',
    },
    'Tyranids': {
        'model_count_rating': 'Very High',
        'painting_complexity': 'Easy',
        'playstyle': 'Horde Assault',
        'price_range_display': '$$',
    },
    'World Eaters': {
        'difficulty': 'Beginner Friendly',
        'painting_complexity': 'Easy-Medium',
        'playstyle': 'All-In Melee',
        'price_range_display': '$$',
    },
}


def apply(apps, schema_editor):
    Faction = apps.get_model('products', 'Faction')
    for name, fields in CORRECTIONS.items():
        Faction.objects.filter(name=name).update(**fields)


def reverse(apps, schema_editor):
    Faction = apps.get_model('products', 'Faction')
    for name, fields in ORIGINALS.items():
        Faction.objects.filter(name=name).update(**fields)


class Migration(migrations.Migration):
    dependencies = [('products', '0023_votann_chaos_knights_pages')]
    operations = [migrations.RunPython(apply, reverse)]
