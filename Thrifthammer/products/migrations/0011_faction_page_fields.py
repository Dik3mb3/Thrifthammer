"""Add faction page content fields to Faction model."""

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    """Add synopsis, quick stats, hero image, and blog tag to Faction."""

    dependencies = [
        ('blog', '0002_comment'),
        ('products', '0010_newsletter_token'),
    ]

    operations = [
        migrations.AddField(
            model_name='faction',
            name='hero_tagline',
            field=models.CharField(blank=True, default='', max_length=200),
        ),
        migrations.AddField(
            model_name='faction',
            name='hero_image_url',
            field=models.URLField(blank=True, default=''),
        ),
        migrations.AddField(
            model_name='faction',
            name='synopsis',
            field=models.TextField(blank=True, default=''),
        ),
        migrations.AddField(
            model_name='faction',
            name='difficulty',
            field=models.CharField(blank=True, default='', max_length=50),
        ),
        migrations.AddField(
            model_name='faction',
            name='model_count_rating',
            field=models.CharField(blank=True, default='', max_length=50),
        ),
        migrations.AddField(
            model_name='faction',
            name='painting_complexity',
            field=models.CharField(blank=True, default='', max_length=50),
        ),
        migrations.AddField(
            model_name='faction',
            name='playstyle',
            field=models.CharField(blank=True, default='', max_length=100),
        ),
        migrations.AddField(
            model_name='faction',
            name='price_range_display',
            field=models.CharField(blank=True, default='', max_length=50),
        ),
        migrations.AddField(
            model_name='faction',
            name='blog_tag',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='factions',
                to='blog.tag',
            ),
        ),
    ]
