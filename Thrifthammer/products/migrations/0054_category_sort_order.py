"""Add sort_order to Category so WH40K can be pinned first."""

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0053_global_neg_dnd_5e'),
    ]

    operations = [
        migrations.AddField(
            model_name='category',
            name='sort_order',
            field=models.IntegerField(
                default=50,
                help_text='Lower numbers sort first. Use to pin categories above alphabetical order.',
            ),
        ),
    ]
