# Generated 2026-05-03
#
# Fixes Skitarii Rangers (59-10) and Skitarii Vanguard (59-11) returning
# no eBay results.
#
# Root cause: the global negative keyword string stored on these products
# contains "ny rangers york" as three separate space-separated words.
# shlex.split() tokenises them individually, so "rangers" becomes a
# standalone -rangers exclusion in the eBay search query — which blocks
# every Skitarii Rangers listing.
#
# Fix: replace "ny rangers" with '"ny rangers"' (quoted) so shlex.split()
# yields the single phrase token "ny rangers", producing -"ny rangers" in
# the query instead of -rangers.

from django.db import migrations


SKUS = ['59-10', '59-11']


def fix_keywords(apps, schema_editor):
    """Quote 'ny rangers' so it is treated as a phrase, not two words."""
    Product = apps.get_model('products', 'Product')
    for sku in SKUS:
        product = Product.objects.filter(gw_sku=sku).first()
        if not product:
            continue
        kw = product.ebay_negative_keywords or ''
        if 'ny rangers' in kw and '"ny rangers"' not in kw:
            kw = kw.replace('ny rangers', '"ny rangers"')
            product.ebay_negative_keywords = kw
            product.save(update_fields=['ebay_negative_keywords'])
            print(f'  Fixed {sku}: {kw}')


def reverse_fix(apps, schema_editor):
    """Restore unquoted 'ny rangers' (best-effort reverse)."""
    Product = apps.get_model('products', 'Product')
    for sku in SKUS:
        product = Product.objects.filter(gw_sku=sku).first()
        if not product:
            continue
        kw = (product.ebay_negative_keywords or '').replace('"ny rangers"', 'ny rangers')
        product.ebay_negative_keywords = kw
        product.save(update_fields=['ebay_negative_keywords'])


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0037_add_sku_negative_keywords_may2026'),
    ]

    operations = [
        migrations.RunPython(fix_keywords, reverse_fix),
    ]
