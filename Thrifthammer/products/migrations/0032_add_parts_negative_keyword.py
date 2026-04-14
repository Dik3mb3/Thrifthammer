# Generated 2026-04-13

from django.db import migrations


# Keyword added to ALL products — filters out spare-parts listings
# (e.g. "Ork Boy Parts", "Necron Warrior parts lot") from eBay results.
KEYWORD = 'parts'


def add_keyword(apps, schema_editor):
    """Append 'parts' to every product that does not already have it."""
    Product = apps.get_model('products', 'Product')
    for product in Product.objects.all():
        existing = product.ebay_negative_keywords or ''
        if KEYWORD not in existing.lower():
            separator = ' ' if existing else ''
            product.ebay_negative_keywords = existing + separator + KEYWORD
            product.save(update_fields=['ebay_negative_keywords'])


def remove_keyword(apps, schema_editor):
    """Strip 'parts' back out (best-effort reverse)."""
    Product = apps.get_model('products', 'Product')
    for product in Product.objects.all():
        if not product.ebay_negative_keywords:
            continue
        kw = product.ebay_negative_keywords
        kw = kw.replace(' ' + KEYWORD, '').replace(KEYWORD + ' ', '').replace(KEYWORD, '')
        product.ebay_negative_keywords = kw.strip()
        product.save(update_fields=['ebay_negative_keywords'])


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0031_populate_ork_gw_skus'),
    ]

    operations = [
        migrations.RunPython(add_keyword, remove_keyword),
    ]
