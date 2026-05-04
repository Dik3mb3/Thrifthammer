"""
Rangers: 3 keywords (need 2 of 3) instead of 2 (need 2 of 2).
Sellers use "Aeldari Rangers" or "Skitarii Rangers" interchangeably —
either pair passes, but plain "Rangers" alone still fails.
"""

from django.db import migrations


def update(apps, schema_editor):
    Product = apps.get_model('products', 'Product')
    Product.objects.filter(gw_sku='prod4900144').update(
        ebay_search_name='Aeldari Rangers Skitarii',
    )


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0042_ebay_search_name_fixes'),
    ]

    operations = [
        migrations.RunPython(update, migrations.RunPython.noop),
    ]
