"""Migration 0025 — Difficulty corrections for Orks, Astra Militarum, Deathwatch,
Grey Knights, Space Wolves, Genestealer Cults, T'au Empire."""

from django.db import migrations

CORRECTIONS = {
    'Orks': {'difficulty': 'Intermediate'},
    'Astra Militarum': {'difficulty': 'Intermediate'},
    'Deathwatch': {'difficulty': 'Intermediate-Advanced'},
    'Grey Knights': {'difficulty': 'Intermediate'},
    'Space Wolves': {'difficulty': 'Beginner Friendly'},
    'Genestealer Cults': {'difficulty': 'Advanced'},
    "T'au Empire": {'difficulty': 'Intermediate'},
}

ORIGINALS = {
    'Orks': {'difficulty': 'Beginner Friendly'},
    'Astra Militarum': {'difficulty': 'Intermediate-Advanced'},
    'Deathwatch': {'difficulty': 'Advanced'},
    'Grey Knights': {'difficulty': 'Intermediate-Advanced'},
    'Space Wolves': {'difficulty': 'Beginner Friendly'},
    'Genestealer Cults': {'difficulty': 'Extreme'},
    "T'au Empire": {'difficulty': 'Intermediate-Advanced'},
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
    dependencies = [('products', '0024_faction_stats_corrections4')]
    operations = [migrations.RunPython(apply, reverse)]
