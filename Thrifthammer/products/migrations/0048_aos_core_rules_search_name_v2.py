"""
Age of Sigmar Core Rules: fix search name.

"2024" rarely appears in eBay titles, returning zero results.
"Age of Sigmar Core Rules Book" works better:
- "book" filters out the Spearhead Fire/Jade game board bundle ($59)
- Price floor (50% of £73.50 = $36.75) already drops old 3rd edition copies ($14-18)
- The current 4th edition listing ($62) passes both checks
"""

from django.db import migrations


def update(apps, schema_editor):
    Product = apps.get_model('products', 'Product')
    Product.objects.filter(gw_sku='80-01').update(
        ebay_search_name='Age of Sigmar Core Rules Book',
    )


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0047_aos_core_rules_search_name'),
    ]

    operations = [
        migrations.RunPython(update, migrations.RunPython.noop),
    ]
