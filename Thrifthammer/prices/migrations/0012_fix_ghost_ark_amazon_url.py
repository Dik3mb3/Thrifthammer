"""
Patch: correct the Ghost Ark Amazon URL.

Migration 0010 set prod4390157 (Ghost Ark) to B08HCL7SFY (correct), then
accidentally overwrote it with B09TLBQLG7 (wrong) because the Howling
Banshees entry used the wrong product ID. This migration restores the
correct ASIN.
"""

from django.db import migrations


def fix_ghost_ark_url(apps, schema_editor):
    """Set Ghost Ark Amazon URL to the correct ASIN B08HCL7SFY."""
    CurrentPrice = apps.get_model('prices', 'CurrentPrice')
    CurrentPrice.objects.filter(
        product__gw_sku='prod4390157',
        retailer__slug='amazon',
    ).update(url='https://www.amazon.com/dp/B08HCL7SFY?tag=thrifthammer7-20')


def reverse_fix(apps, schema_editor):
    """Restore the (incorrect) URL from migration 0010 on rollback."""
    CurrentPrice = apps.get_model('prices', 'CurrentPrice')
    CurrentPrice.objects.filter(
        product__gw_sku='prod4390157',
        retailer__slug='amazon',
    ).update(url='https://www.amazon.com/dp/B09TLBQLG7?tag=thrifthammer7-20')


class Migration(migrations.Migration):

    dependencies = [
        ('prices', '0011_seraphon_and_wraiths_amazon_urls'),
    ]

    operations = [
        migrations.RunPython(fix_ghost_ark_url, reverse_code=reverse_fix),
    ]
