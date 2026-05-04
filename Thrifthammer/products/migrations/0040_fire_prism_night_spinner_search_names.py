"""
Fix Fire Prism and Night Spinner eBay search names.

Both products share a single GW dual-build kit. The eBay listing title uses
the old name "Eldar" not the current GW name "Aeldari", so searches for
"Aeldari" fail to surface the listing. Switching to "Eldar" matches real titles
like "Games Workshop Warhammer 40k Eldar Fire Prism/Night Spinner".
"""

from django.db import migrations


def update_search_names(apps, schema_editor):
    Product = apps.get_model('products', 'Product')
    Product.objects.filter(gw_sku='prod770019a').update(
        ebay_search_name='Fire Prism Eldar Warhammer 40k',
    )
    Product.objects.filter(gw_sku='prod2180123').update(
        ebay_search_name='Night Spinner Eldar Warhammer 40k',
    )


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0039_bloodcrushers_search_name'),
    ]

    operations = [
        migrations.RunPython(update_search_names, migrations.RunPython.noop),
    ]
