# Generated 2026-04-23

from django.db import migrations


# Keywords added to ALL products — filters out non-miniature listings:
#   'america' — US-branded merchandise and apparel that shares product terminology
KEYWORDS = ['america']


def add_keywords(apps, schema_editor):
    """Append keywords to every product that does not already have them."""
    Product = apps.get_model('products', 'Product')
    for product in Product.objects.all():
        existing = product.ebay_negative_keywords or ''
        existing_lower = existing.lower()
        to_add = [kw for kw in KEYWORDS if kw not in existing_lower]
        if to_add:
            separator = ' ' if existing else ''
            product.ebay_negative_keywords = existing + separator + ' '.join(to_add)
            product.save(update_fields=['ebay_negative_keywords'])


def remove_keywords(apps, schema_editor):
    """Strip the added keywords back out (best-effort reverse)."""
    Product = apps.get_model('products', 'Product')
    for product in Product.objects.all():
        if not product.ebay_negative_keywords:
            continue
        kw = product.ebay_negative_keywords
        for keyword in KEYWORDS:
            kw = kw.replace(' ' + keyword, '').replace(keyword + ' ', '').replace(keyword, '')
        product.ebay_negative_keywords = kw.strip()
        product.save(update_fields=['ebay_negative_keywords'])


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0034_add_replacement_dermaplane_negative_keywords'),
    ]

    operations = [
        migrations.RunPython(add_keywords, remove_keywords),
    ]
