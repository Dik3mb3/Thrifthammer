"""
Change Flesh Hounds search name to the natural eBay phrase sellers use.
"Flesh Hounds of Khorne" surfaces sealed plastic box listings reliably
and reduces validator keyword requirement to 2 of 3 (flesh, hounds, khorne).
"""

from django.db import migrations


def update(apps, schema_editor):
    Product = apps.get_model('products', 'Product')
    Product.objects.filter(gw_sku='P-KHORNE-FLESHHOUNDS').update(
        ebay_search_name='Flesh Hounds of Khorne',
    )


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0040_fire_prism_night_spinner_search_names'),
    ]

    operations = [
        migrations.RunPython(update, migrations.RunPython.noop),
    ]
