"""
Add ebay_allowed_title_words field to Product.

Allows per-product bypasses for words/digits that the eBay validator normally
blocks (bits keywords, standalone digit counts). Seeded for Bloodcrushers of
Khorne: 'nos 6' allows "NOS" (New Old Stock sealed box) and model count "6"
in listing titles.
"""

from django.db import migrations, models


def seed_allowed_words(apps, schema_editor):
    Product = apps.get_model('products', 'Product')
    Product.objects.filter(gw_sku='P-KHORNE-BLOODCRUSHERS').update(
        ebay_allowed_title_words='nos 6',
    )


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0037_add_sku_negative_keywords_may2026'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='ebay_allowed_title_words',
            field=models.CharField(
                blank=True,
                default='',
                help_text=(
                    'Space-separated words/digits that are normally blocked by the validator '
                    'but should be allowed for this product. '
                    'e.g. "nos 6" for Bloodcrushers allows "NOS" (New Old Stock) listings '
                    'and titles that include the model count "6".'
                ),
                max_length=200,
            ),
        ),
        migrations.RunPython(seed_allowed_words, migrations.RunPython.noop),
    ]
