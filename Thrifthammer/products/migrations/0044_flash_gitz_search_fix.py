"""
Ork Flash Gitz: simplify eBay search.

The product has 12 negative keywords in its query, making it so complex
that valid listings like "ORKS FLASH GITZ" ($55) never appear in the top 10.
Remove character names (nookah, elektro, rokker, bluddklaw) that cannot
appear in sealed box titles — the validator already catches individual model
listings via digit/bits checks. Set an explicit short search name so eBay
ranks sealed box listings first.
"""

from django.db import migrations


def update(apps, schema_editor):
    Product = apps.get_model('products', 'Product')
    Product.objects.filter(gw_sku='50-20').update(
        ebay_search_name='Flash Gitz Ork Warhammer',
        ebay_negative_keywords=(
            'meganobz mek kaptin artel bluddklaw legions imperialis Resin 04-113'
        ),
    )


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0043_rangers_search_name_fix'),
    ]

    operations = [
        migrations.RunPython(update, migrations.RunPython.noop),
    ]
