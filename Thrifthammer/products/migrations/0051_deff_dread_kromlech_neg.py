"""
Ork Deff Dread: add 'kromlech' to neg keywords.

Kromlech is a third-party miniature company that makes Ork-themed mechs with
"Deff Dread" in their listing titles. They rank highly in eBay search but use
CALCULATED shipping, pushing the real GW listing out of the top 10.
"""

from django.db import migrations


def update(apps, schema_editor):
    Product = apps.get_model('products', 'Product')
    Product.objects.filter(gw_sku='50-16').update(
        ebay_negative_keywords=(
            'kromlech kaptin artel bluddklaw legions imperialis Resin 04-113'
        ),
    )


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0050_deff_dread_search_name'),
    ]

    operations = [
        migrations.RunPython(update, migrations.RunPython.noop),
    ]
