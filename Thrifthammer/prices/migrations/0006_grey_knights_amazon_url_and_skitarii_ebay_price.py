# Generated 2026-05-02
#
# Two data fixes applied via migration so they deploy automatically:
#
# 1. Grey Knights shared Amazon listing (ASIN B00MYGOM3Y) applied to four
#    products — Purifier Squad, Purgation Squad, Strike Squad, Interceptor Squad.
#    Price set to $58.65; manual_url_override left False so the price batch
#    command can update it automatically on the next run.
#
# 2. Adeptus Mechanicus Skitarii Vanguard eBay price temporarily set to $51.00
#    while the eBay API is down. manual_url_override is NOT set so the scraper
#    will overwrite it when it next runs.

from django.db import migrations
from decimal import Decimal

AMAZON_URL = 'https://www.amazon.com/dp/B00MYGOM3Y?tag=thrifthammer7-20'
AMAZON_PRICE = Decimal('58.65')

# GW SKUs for the four Grey Knight products sharing this Amazon listing
GK_SKUS = ['57-27', '57-26', '57-06', '57-24']

SKITARII_SKU = '59-11'
SKITARII_EBAY_PRICE = Decimal('51.00')


def apply_fixes(apps, schema_editor):
    """Update Amazon URLs/prices for GK products and Skitarii eBay price."""
    Product = apps.get_model('products', 'Product')
    CurrentPrice = apps.get_model('prices', 'CurrentPrice')

    # Grey Knights Amazon rows
    for sku in GK_SKUS:
        product = Product.objects.filter(gw_sku=sku).first()
        if not product:
            continue
        cp = CurrentPrice.objects.filter(
            product=product,
            retailer__name='Amazon',
        ).first()
        if not cp:
            continue
        cp.url = AMAZON_URL
        cp.price = AMAZON_PRICE
        cp.manual_url_override = False
        cp.save(update_fields=['url', 'price', 'manual_url_override'])

    # Skitarii Vanguard eBay price
    product = Product.objects.filter(gw_sku=SKITARII_SKU).first()
    if product:
        cp = CurrentPrice.objects.filter(
            product=product,
            retailer__name='eBay',
        ).first()
        if cp:
            cp.price = SKITARII_EBAY_PRICE
            cp.save(update_fields=['price'])


def reverse_fixes(apps, schema_editor):
    """No meaningful reverse — leave prices as-is on rollback."""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('prices', '0005_add_manual_url_override'),
        ('products', '0036_sku_specific_negative_keywords'),
    ]

    operations = [
        migrations.RunPython(apply_fixes, reverse_fixes),
    ]
