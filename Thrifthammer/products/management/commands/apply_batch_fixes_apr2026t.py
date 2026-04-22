"""
apply_batch_fixes_apr2026t — Strip ?queryID= from all GW URLs; clear dead product pages.

Background
----------
GW URLs stored in Product.gw_url and CurrentPrice.url (retailer GW) have Algolia
?queryID= tracking parameters baked in from when they were first captured.  These
parameters expire and cause 4xx errors for Googlebot and users — Screaming Frog
found 8 such 4xx external links on thrifthammer.com.

The queryID parameter is search-analytics-only; the base URL without it is the
canonical product page.  Stripping it globally fixes all 262 affected products.

Additionally, three products link to GW pages that no longer exist (discontinued
product lines with no current GW shop URL).  Their gw_url is cleared so the
"View on GW" button is hidden rather than leading to a 404.
"""

import re

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Product

RETAILER_GW = 1  # Games Workshop

# Confirmed-dead GW product page URLs (no queryID, just genuinely 404).
# Clear gw_url so the "View on GW" button is hidden for these products.
DEAD_GW_URL_SLUGS = [
    'horus-heresy-leviathan-dreadnought',  # Night-Lords-Leviathan-Dreadnought-2019
    'necron-cryptek',                       # Necron-Cryptek-2020
    'codex-emperors-children',              # codex-emperors-children-2025-eng (URL changed)
]


def _strip_query_id(url: str) -> str:
    """Remove ?queryID=... (and any subsequent params) from a GW URL."""
    return re.sub(r'\?queryID=[^#]*', '', url).rstrip('?&')


class Command(BaseCommand):
    """Strip ?queryID= tracking params from GW URLs; clear confirmed-dead pages."""

    help = 'Strip ?queryID= from all GW URLs and clear dead product page links.'

    def handle(self, *args, **options):
        """Run all fixes."""
        self._strip_query_ids_from_gw_url()
        self._strip_query_ids_from_current_prices()
        self._clear_dead_gw_urls()
        self.stdout.write(self.style.SUCCESS('\nDone.'))

    def _strip_query_ids_from_gw_url(self):
        """Strip ?queryID= from Product.gw_url for all affected products."""
        products = Product.objects.filter(gw_url__icontains='queryID')
        updated = 0
        for product in products:
            clean = _strip_query_id(product.gw_url)
            if clean != product.gw_url:
                product.gw_url = clean
                product.save(update_fields=['gw_url'])
                updated += 1
        self.stdout.write(
            self.style.SUCCESS(f'  Product.gw_url: stripped queryID from {updated} products')
        )

    def _strip_query_ids_from_current_prices(self):
        """Strip ?queryID= from GW retailer CurrentPrice.url entries."""
        prices = CurrentPrice.objects.filter(
            retailer_id=RETAILER_GW,
            url__icontains='queryID',
        )
        updated = 0
        for cp in prices:
            clean = _strip_query_id(cp.url)
            if clean != cp.url:
                cp.url = clean
                cp.save(update_fields=['url'])
                updated += 1
        self.stdout.write(
            self.style.SUCCESS(f'  CurrentPrice (GW): stripped queryID from {updated} entries')
        )

    def _clear_dead_gw_urls(self):
        """Clear gw_url for products whose GW page no longer exists."""
        for slug in DEAD_GW_URL_SLUGS:
            try:
                product = Product.objects.get(slug=slug)
                old = product.gw_url
                product.gw_url = ''
                product.save(update_fields=['gw_url'])
                self.stdout.write(
                    self.style.SUCCESS(f'  Cleared dead gw_url for {slug}: {old}')
                )
            except Product.DoesNotExist:
                self.stdout.write(self.style.WARNING(f'  Not found: {slug}'))
