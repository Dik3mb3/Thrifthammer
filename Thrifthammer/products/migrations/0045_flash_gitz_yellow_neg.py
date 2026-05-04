"""
Flash Gitz: add 'yellow' to neg keywords.

"Flash Gitz Yellow" is a Citadel layer paint that floods eBay search results
for "Flash Gitz", pushing the actual miniature box beyond position 10.
Blocking 'yellow' removes paint listings and lets the $55 miniature listings
surface in the top 10.
"""

from django.db import migrations


def update(apps, schema_editor):
    Product = apps.get_model('products', 'Product')
    Product.objects.filter(gw_sku='50-20').update(
        ebay_negative_keywords=(
            'yellow meganobz mek kaptin artel bluddklaw legions imperialis Resin 04-113'
        ),
    )


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0044_flash_gitz_search_fix'),
    ]

    operations = [
        migrations.RunPython(update, migrations.RunPython.noop),
    ]
