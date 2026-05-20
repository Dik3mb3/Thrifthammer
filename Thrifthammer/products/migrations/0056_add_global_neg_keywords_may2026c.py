# Generated 2026-05-20
#
# Adds two keywords to ALL products' ebay_negative_keywords:
#   'Plushie' — soft-toy / plush merchandise listings
#   'Plush'   — same (shorter variant used by some sellers)

from django.db import migrations


KEYWORDS = ['Plushie', 'Plush']


def add_keywords(apps, schema_editor):
    """Append keywords to every product that does not already have them."""
    Product = apps.get_model('products', 'Product')
    for product in Product.objects.all():
        existing = product.ebay_negative_keywords or ''
        existing_lower = existing.lower()
        to_add = [kw for kw in KEYWORDS if kw.lower() not in existing_lower]
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
        ('products', '0055_add_global_neg_keywords_may2026b'),
    ]

    operations = [
        migrations.RunPython(add_keywords, remove_keywords),
    ]
