"""
Set Bloodcrushers search name to 2 keywords so the validator requires only
'bloodcrushers' + 'khorne' — matching real seller titles like
"40k World Eaters Bloodcrushers of Khorne 6 Models AoS NOS Bases/instructions"
which omit 'daemon' and 'warhammer'.
"""

from django.db import migrations


def set_search_name(apps, schema_editor):
    Product = apps.get_model('products', 'Product')
    Product.objects.filter(gw_sku='P-KHORNE-BLOODCRUSHERS').update(
        ebay_search_name='Bloodcrushers Khorne',
    )


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0038_ebay_allowed_title_words'),
    ]

    operations = [
        migrations.RunPython(set_search_name, migrations.RunPython.noop),
    ]
