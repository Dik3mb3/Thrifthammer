"""Migration 0016 — Fix Aeldari model_count_rating to Medium."""

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [('products', '0015_faction_stats_corrections')]

    operations = [
        migrations.RunPython(
            lambda apps, se: apps.get_model('products', 'Faction').objects.filter(name='Aeldari').update(model_count_rating='Medium'),
            lambda apps, se: apps.get_model('products', 'Faction').objects.filter(name='Aeldari').update(model_count_rating='Low-Medium'),
        )
    ]
