"""
apply_batch_fixes_apr2026r
~~~~~~~~~~~~~~~~~~~~~~~~~~
Fix eBay search configuration for two Space Wolves products.

Logan Grimnar
-------------
Problem: ebay_negative_keywords contains 'wolves', which blocks every
listing for a Space Wolves character.  Also contains stale per-product
keywords ('imperialis', 'legions', 'rocks') that don't apply to him.
Fix: reset negative keywords to the standard global set only, and
simplify ebay_search_name to 'Logan Grimnar' (the search term that
surfaces the correct Best Match listing).

Murderfang
----------
Problem: Murderfang is a Space Wolves Venerable Dreadnought variant.
eBay has sparse specific listings but plenty of Venerable Dreadnought
listings for the same kit.
Fix: set ebay_search_name = 'space wolves venerable dreadnought' so
the scraper finds the most relevant Best Match listing.

Both fixes survive redeploys — populate_sm_phase3_products does not
touch ebay_search_name or ebay_negative_keywords.

Idempotent — safe to re-run.
"""

from django.core.management.base import BaseCommand

from products.models import Product

# Global negative keywords applied to every product by migrations 0029/0032/0034.
# Used as the clean baseline when resetting per-product junk keywords.
GLOBAL_NEGATIVE_KEYWORDS = 'logo ny rangers new york parts replacement dermaplane'


class Command(BaseCommand):
    """Fix eBay search settings for Logan Grimnar and Murderfang."""

    help = 'Apr-2026-r: Fix Logan Grimnar and Murderfang eBay search config.'

    def handle(self, *args, **options):
        """Apply eBay search name and negative keyword fixes."""
        self._fix_logan_grimnar()
        self._fix_murderfang()

    def _fix_logan_grimnar(self):
        """Remove self-blocking 'wolves' keyword; simplify search name."""
        product = Product.objects.filter(slug='space-wolves-logan-grimnar').first()
        if not product:
            self.stdout.write(self.style.ERROR('Logan Grimnar not found.'))
            return

        product.ebay_search_name = 'Logan Grimnar'
        product.ebay_negative_keywords = GLOBAL_NEGATIVE_KEYWORDS
        product.save(update_fields=['ebay_search_name', 'ebay_negative_keywords'])
        self.stdout.write(self.style.SUCCESS(
            'Logan Grimnar: ebay_search_name -> "Logan Grimnar", '
            'negative keywords reset to global defaults (removed wolves/rocks/imperialis/legions)'
        ))

    def _fix_murderfang(self):
        """Point Murderfang search at Venerable Dreadnought listings."""
        product = Product.objects.filter(slug='space-wolves-murderfang').first()
        if not product:
            self.stdout.write(self.style.ERROR('Murderfang not found.'))
            return

        product.ebay_search_name = 'space wolves venerable dreadnought'
        product.save(update_fields=['ebay_search_name'])
        self.stdout.write(self.style.SUCCESS(
            'Murderfang: ebay_search_name -> "space wolves venerable dreadnought"'
        ))
