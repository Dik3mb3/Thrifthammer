"""
apply_batch_fixes_apr2026q
~~~~~~~~~~~~~~~~~~~~~~~~~~
Set ebay_search_name = "heavy intercessors 40k" on the Heavy Intercessor
Squad (Space Marines) product.

The scraper's default query ("Heavy Intercessor Squad") produces different
Best Match results than the user-facing eBay search, missing the cheapest
sealed-kit listing.  The corrected search name aligns the scraper with
eBay's own Best Match ranking for this product.

Idempotent — safe to re-run.
"""

from django.core.management.base import BaseCommand

from products.models import Product


class Command(BaseCommand):
    """Set eBay search name on Heavy Intercessor Squad."""

    help = 'Apr-2026-q: Fix Heavy Intercessor Squad eBay search name.'

    def handle(self, *args, **options):
        """Update ebay_search_name for Heavy Intercessor Squad."""
        product = Product.objects.filter(
            slug='space-marine-heavy-intercessor-squad',
        ).first()

        if not product:
            self.stdout.write(self.style.ERROR('Heavy Intercessor Squad not found.'))
            return

        product.ebay_search_name = 'heavy intercessors 40k'
        product.save(update_fields=['ebay_search_name'])
        self.stdout.write(self.style.SUCCESS(
            'Heavy Intercessor Squad ebay_search_name -> "heavy intercessors 40k"'
        ))
