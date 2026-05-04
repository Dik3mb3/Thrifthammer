"""
Age of Sigmar Core Rules: set search name to 2024 edition.
Scopes eBay results to the current edition, avoiding older/cheaper
editions that would fail the MSRP price floor check.
"""

from django.db import migrations


def update(apps, schema_editor):
    Product = apps.get_model('products', 'Product')
    Product.objects.filter(gw_sku='80-01').update(
        ebay_search_name='Age of Sigmar Core Rules 2024',
    )


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0046_flash_gitz_allowed_words'),
    ]

    operations = [
        migrations.RunPython(update, migrations.RunPython.noop),
    ]
