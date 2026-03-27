"""
Migration: add last_alerted_at to WatchlistItem.

Replaces the single last_alerted_price (which only prevented re-alerts
when price improved) with a timestamp so we can re-alert weekly while the
condition remains met, regardless of whether the price has changed.
"""
from django.db import migrations, models


class Migration(migrations.Migration):
    """Add last_alerted_at DateTimeField to WatchlistItem."""

    dependencies = [
        ('accounts', '0003_watchlist_alerts'),
    ]

    operations = [
        migrations.AddField(
            model_name='watchlistitem',
            name='last_alerted_at',
            field=models.DateTimeField(
                blank=True,
                null=True,
                help_text='Timestamp of the last price-alert email sent for this item.',
            ),
        ),
    ]
