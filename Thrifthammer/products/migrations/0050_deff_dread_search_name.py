"""
Ork Deff Dread: fix search name.

"Ork Deff Dread 40000" fails to surface listings titled "Deff Dread Orks
Warhammer 40k" because eBay doesn't equate "40000" with "40k".
3 keywords with 2 required gives flexibility: "Deff Dread Ork" matches
any seller title containing the unit name regardless of faction prefix.
"""

from django.db import migrations


def update(apps, schema_editor):
    Product = apps.get_model('products', 'Product')
    Product.objects.filter(gw_sku='50-16').update(
        ebay_search_name='Deff Dread Ork',
    )


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0049_aos_core_rules_allowed_words'),
    ]

    operations = [
        migrations.RunPython(update, migrations.RunPython.noop),
    ]
