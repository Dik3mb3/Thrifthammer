"""
Age of Sigmar Core Rules: allow 'hardcover' in title.

The bits blocklist includes 'hardcover' to filter individual extracted models
described as hardcover packaging, but for a rulebook product 'hardcover' is
a valid edition descriptor (not a bits signal).
"""

from django.db import migrations


def update(apps, schema_editor):
    Product = apps.get_model('products', 'Product')
    Product.objects.filter(gw_sku='80-01').update(
        ebay_allowed_title_words='hardcover',
    )


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0048_aos_core_rules_search_name_v2'),
    ]

    operations = [
        migrations.RunPython(update, migrations.RunPython.noop),
    ]
