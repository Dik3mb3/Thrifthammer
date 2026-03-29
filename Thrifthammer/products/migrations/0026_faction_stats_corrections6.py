"""Migration 0026 — Stat corrections for Custodes, Space Wolves, Deathwatch, Chaos Knights."""

from django.db import migrations

CORRECTIONS = {
    'Custodes': {'playstyle': 'Elite Melee'},
    'Space Wolves': {'difficulty': 'Easy'},
    'Deathwatch': {'playstyle': 'Customizable Elite Kill Teams'},
    'Chaos Knights': {'playstyle': 'High Volume Melee/Shooting Mix'},
}

ORIGINALS = {
    'Custodes': {'playstyle': 'Melee Elite'},
    'Space Wolves': {'difficulty': 'Beginner Friendly'},
    'Deathwatch': {'playstyle': 'Customizable Elite Kill Teams'},
    'Chaos Knights': {'playstyle': 'Dread Assault'},
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
    dependencies = [('products', '0025_faction_stats_corrections5')]
    operations = [migrations.RunPython(apply, reverse)]
