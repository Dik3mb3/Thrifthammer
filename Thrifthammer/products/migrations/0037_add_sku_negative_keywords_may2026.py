# Generated 2026-05-03
#
# Adds SKU-specific negative keywords to individual products:
#   Captain with Jump Pack and Relic Shield (48-105): Jump Pack
#   Necrons Royal Court (prod4900147): Skorpekh Lord, Plasmancer, Reanimator, Overlord

from django.db import migrations


SKU_KEYWORDS = {
    '48-105':       ['Jump Pack'],
    'prod4900147':  ['Skorpekh Lord', 'Plasmancer', 'Reanimator', 'Overlord'],
}


def add_keywords(apps, schema_editor):
    """Append SKU-specific negative keywords to the matching products."""
    Product = apps.get_model('products', 'Product')
    for sku, keywords in SKU_KEYWORDS.items():
        product = Product.objects.filter(gw_sku=sku).first()
        if not product:
            continue
        existing = product.ebay_negative_keywords or ''
        existing_lower = existing.lower()
        to_add = [kw for kw in keywords if kw.lower() not in existing_lower]
        if to_add:
            separator = ' ' if existing else ''
            product.ebay_negative_keywords = existing + separator + ' '.join(to_add)
            product.save(update_fields=['ebay_negative_keywords'])


def remove_keywords(apps, schema_editor):
    """Strip the added keywords back out (best-effort reverse)."""
    Product = apps.get_model('products', 'Product')
    for sku, keywords in SKU_KEYWORDS.items():
        product = Product.objects.filter(gw_sku=sku).first()
        if not product:
            continue
        kw = product.ebay_negative_keywords or ''
        for keyword in keywords:
            kw = kw.replace(' ' + keyword, '').replace(keyword + ' ', '').replace(keyword, '')
        product.ebay_negative_keywords = kw.strip()
        product.save(update_fields=['ebay_negative_keywords'])


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0036_sku_specific_negative_keywords'),
    ]

    operations = [
        migrations.RunPython(add_keywords, remove_keywords),
    ]
