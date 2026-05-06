"""
Global eBay negative keywords: add 'D&D' and '5e'.

D&D / Dungeons & Dragons branded miniatures and 5th-edition tabletop
accessories appear in eBay searches for Warhammer kits because they
share painting and hobby terminology. Neither term is relevant to any
Games Workshop product so they are safe to exclude globally.
"""

from django.db import migrations

KEYWORDS = ['D&D', '5e']


def add_keywords(apps, schema_editor):
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
    Product = apps.get_model('products', 'Product')
    for product in Product.objects.all():
        if not product.ebay_negative_keywords:
            continue
        kws = product.ebay_negative_keywords
        for kw in KEYWORDS:
            kws = kws.replace(' ' + kw, '').replace(kw + ' ', '').replace(kw, '')
        product.ebay_negative_keywords = kws.strip()
        product.save(update_fields=['ebay_negative_keywords'])


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0052_deff_dread_search_name_v2'),
    ]

    operations = [
        migrations.RunPython(add_keywords, remove_keywords),
    ]
