# Generated 2026-05-02
#
# Retrofits all existing eBay CurrentPrice URLs with eBay Partner Network
# (EPN) affiliate tracking parameters so clicks on existing listings
# generate affiliate revenue immediately on deploy.
#
# EPN params appended:
#   mkcid=1             — marketing channel (EPN)
#   mkrid=711-53200-19255-0 — US marketplace rotation ID
#   campid=5339151938   — ThriftHammer EPN campaign ID
#   toolid=10001        — standard EPN tool ID for direct links
#   mkevt=1             — marks click as affiliate event
#
# Safe to re-run: strips any existing EPN params before appending
# so double-migration or re-application is harmless.

from django.db import migrations

CAMPAIGN_ID = '5339151938'
EPN_PARAMS  = f'mkcid=1&mkrid=711-53200-19255-0&toolid=10001&mkevt=1&campid={CAMPAIGN_ID}'


def add_epn_params(apps, schema_editor):
    """Append EPN tracking params to all existing eBay CurrentPrice URLs."""
    CurrentPrice = apps.get_model('prices', 'CurrentPrice')

    ebay_prices = CurrentPrice.objects.filter(
        retailer__slug='ebay',
    ).exclude(url='').select_related('retailer')

    updated = 0
    for cp in ebay_prices:
        url = cp.url

        # Strip any previously appended EPN params to avoid duplication
        for marker in ('mkcid=1', '&mkcid=1'):
            idx = url.find(marker)
            if idx != -1:
                url = url[:idx].rstrip('?&')
                break

        separator = '&' if '?' in url else '?'
        cp.url = f'{url}{separator}{EPN_PARAMS}'
        cp.save(update_fields=['url'])
        updated += 1

    print(f'  EPN params added to {updated} eBay URLs')


def remove_epn_params(apps, schema_editor):
    """Strip EPN tracking params from eBay URLs (reverse migration)."""
    CurrentPrice = apps.get_model('prices', 'CurrentPrice')

    ebay_prices = CurrentPrice.objects.filter(
        retailer__slug='ebay',
    ).exclude(url='')

    for cp in ebay_prices:
        url = cp.url
        for marker in ('mkcid=1', '&mkcid=1'):
            idx = url.find(marker)
            if idx != -1:
                url = url[:idx].rstrip('?&')
                break
        if url != cp.url:
            cp.url = url
            cp.save(update_fields=['url'])


class Migration(migrations.Migration):

    dependencies = [
        ('prices', '0007_currentprice_shipping_cost'),
    ]

    operations = [
        migrations.RunPython(add_epn_params, remove_epn_params),
    ]
