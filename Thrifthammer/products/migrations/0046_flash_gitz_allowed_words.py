"""
Flash Gitz: set ebay_allowed_title_words = 'nib'.

Products with ebay_allowed_title_words set skip the description-mirrors-title
validator check, allowing listings like "Ork Flash Gitz Warhammer 40K NIB"
where a short description echoes the title but the listing is genuine.
"""

from django.db import migrations


def update(apps, schema_editor):
    Product = apps.get_model('products', 'Product')
    Product.objects.filter(gw_sku='50-20').update(
        ebay_allowed_title_words='nib',
    )


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0045_flash_gitz_yellow_neg'),
    ]

    operations = [
        migrations.RunPython(update, migrations.RunPython.noop),
    ]
