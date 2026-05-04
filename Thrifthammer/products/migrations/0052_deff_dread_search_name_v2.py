"""
Ork Deff Dread: simplify search name to two keywords.

'Deff Dread Ork' (3 keywords) still fails to surface the target listing
because eBay Best Match doesn't rank it in the top 10 for that query.
Dropping to 'Deff Dread' (2 keywords) broadens the search slightly and
removes the 'Ork' term that may be suppressing relevant results — eBay
sellers often omit the faction name from the title.

With 2 search words the validator requires both to appear in the listing
title (65% threshold → ceil(0.65 × 2) = 2), which is satisfied by any
title containing "Deff Dread".
"""

from django.db import migrations


def update(apps, schema_editor):
    Product = apps.get_model('products', 'Product')
    Product.objects.filter(gw_sku='50-16').update(
        ebay_search_name='Deff Dread',
    )


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0051_deff_dread_kromlech_neg'),
    ]

    operations = [
        migrations.RunPython(update, migrations.RunPython.noop),
    ]
