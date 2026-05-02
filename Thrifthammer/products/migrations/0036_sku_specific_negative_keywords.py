# Generated 2026-05-02
#
# Adds SKU-specific negative keywords to individual products:
#   Adeptus Mechanicus Skitarii Vanguard (59-11): Lord, Marshal
#   Plague Drones of Nurgle: Champion

from django.db import migrations


SKU_KEYWORDS = {
    '59-11':                        ['Lord', 'Marshal'],
    'prod3610130-99129915038':      ['Champion'],
}


def add_keywords(apps, schema_editor):
    """Append SKU-specific keywords to the matching products."""
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
        ('products', '0035_add_america_negative_keyword'),
    ]

    operations = [
        migrations.RunPython(add_keywords, remove_keywords),
    ]
