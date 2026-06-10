# Generated 2026-06-10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0061_add_secondary_factions'),
    ]

    operations = [
        migrations.AddField(
            model_name='retailer',
            name='is_uk',
            field=models.BooleanField(
                default=False,
                help_text='True for UK-only retailers (GBP prices). Used to isolate UK prices from US pages.',
            ),
        ),
    ]
