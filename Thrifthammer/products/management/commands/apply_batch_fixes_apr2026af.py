"""
Batch fix apr2026af — Update Amazon URL for Orruk Warclans Ironjawz Brutes.

The old ASIN (B01EVDPFBK) had no live price.  The new ASIN (B09HJM9413)
has an active listing at $54.93.

URL is updated to the clean /dp/ format so the Amazon price scraper can
read and update the price automatically on its next run.

Idempotent: only runs if the URL still contains the old ASIN.
"""

from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from prices.models import CurrentPrice
from products.models import Product, Retailer


_OLD_ASIN   = 'B01EVDPFBK'
_NEW_URL    = 'https://www.amazon.com/dp/B09HJM9413?tag=thrifthammer7-20'
_NEW_PRICE  = Decimal('54.93')
_PRODUCT_SLUG = 'orruk-warclans-ironjawz-brutes'
_RETAILER_NAME = 'Amazon'


class Command(BaseCommand):
    """Update Amazon listing URL for Orruk Warclans Ironjawz Brutes."""

    help = 'Fix Amazon URL for Orruk Warclans Ironjawz Brutes (old ASIN had no price).'

    def handle(self, *args, **options):
        """Update URL and seed current price if old ASIN is still in URL."""
        try:
            product = Product.objects.get(slug=_PRODUCT_SLUG)
        except Product.DoesNotExist:
            self.stdout.write(self.style.ERROR(
                f'Product {_PRODUCT_SLUG!r} not found — skipping.'
            ))
            return

        try:
            retailer = Retailer.objects.get(name=_RETAILER_NAME)
        except Retailer.DoesNotExist:
            self.stdout.write(self.style.ERROR(
                f'Retailer {_RETAILER_NAME!r} not found — skipping.'
            ))
            return

        try:
            price_record = CurrentPrice.objects.get(product=product, retailer=retailer)
        except CurrentPrice.DoesNotExist:
            self.stdout.write(self.style.ERROR(
                'No Amazon CurrentPrice record found for Orruk Brutes — skipping.'
            ))
            return

        if _OLD_ASIN not in price_record.url:
            self.stdout.write('  already updated, skipping.')
            return

        with transaction.atomic():
            price_record.url   = _NEW_URL
            price_record.price = _NEW_PRICE
            price_record.in_stock      = True
            price_record.not_available = False
            price_record.save()

        self.stdout.write(self.style.SUCCESS(
            f'  Updated Orruk Brutes Amazon URL to {_NEW_URL}\n'
            f'  Price set to ${_NEW_PRICE} (scraper will update on next run).'
        ))
