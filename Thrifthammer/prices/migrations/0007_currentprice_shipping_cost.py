# Generated 2026-05-02
#
# Adds a nullable shipping_cost field to CurrentPrice.
# eBay only — stores the shipping component so we can display a clear
# "eBay prices include shipping" footnote without changing the price field
# (which already stores the total: item price + shipping).

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('prices', '0006_grey_knights_amazon_url_and_skitarii_ebay_price'),
    ]

    operations = [
        migrations.AddField(
            model_name='currentprice',
            name='shipping_cost',
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                help_text=(
                    'eBay only — the shipping component included in the price. '
                    'The price field stores the total (item price + shipping).'
                ),
                max_digits=8,
                null=True,
            ),
        ),
    ]
