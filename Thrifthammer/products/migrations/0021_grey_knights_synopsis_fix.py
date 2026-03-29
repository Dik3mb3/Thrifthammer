"""Migration 0021 — Remove outdated faction-punishing line from Grey Knights synopsis."""

from django.db import migrations


OLD = (
    " The faction punishes daemon and Chaos armies especially hard, but holds its own "
    "across the board through sheer resilience and output per model."
)


def apply(apps, schema_editor):
    Faction = apps.get_model('products', 'Faction')
    gk = Faction.objects.filter(name='Grey Knights').first()
    if gk and OLD in gk.synopsis:
        Faction.objects.filter(name='Grey Knights').update(synopsis=gk.synopsis.replace(OLD, ''))


def reverse(apps, schema_editor):
    pass  # Non-reversible content edit


class Migration(migrations.Migration):
    dependencies = [('products', '0020_faction_stats_corrections3')]
    operations = [migrations.RunPython(apply, reverse)]
