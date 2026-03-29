"""
Migration 0013 — Add display_name to Faction; update Custodes page data.

Schema change:
  - Adds products.Faction.display_name (optional CharField).

Data changes (Custodes faction):
  - Sets display_name = 'Adeptus Custodes'
  - Corrects price_range_display from '$-$$$' to '$'
  - Corrects model_count_rating from 'Low (20-40 models)' to 'Low'
"""

from django.db import migrations, models


def set_custodes_display_data(apps, schema_editor):
    """Populate display_name and tidy quick-stat values for Custodes."""
    Faction = apps.get_model('products', 'Faction')
    Faction.objects.filter(name='Custodes').update(
        display_name='Adeptus Custodes',
        price_range_display='$',
        model_count_rating='Low',
    )


def reverse_custodes_display_data(apps, schema_editor):
    """Revert Custodes display fields to previous values."""
    Faction = apps.get_model('products', 'Faction')
    Faction.objects.filter(name='Custodes').update(
        display_name='',
        price_range_display='$-$$$',
        model_count_rating='Low (20-40 models)',
    )


class Migration(migrations.Migration):
    """Add display_name to Faction and update Custodes page data."""

    dependencies = [
        ('products', '0012_custodes_faction_page_data'),
    ]

    operations = [
        migrations.AddField(
            model_name='faction',
            name='display_name',
            field=models.CharField(
                blank=True,
                default='',
                help_text='Override the display name shown on the faction page '
                          '(e.g. "Adeptus Custodes"). Defaults to the faction name if blank.',
                max_length=100,
            ),
        ),
        migrations.RunPython(
            set_custodes_display_data,
            reverse_custodes_display_data,
        ),
    ]
