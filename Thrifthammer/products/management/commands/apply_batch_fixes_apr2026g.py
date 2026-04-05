"""
Management command: apply_batch_fixes_apr2026g

Two follow-up search-name tweaks for Necron products that returned
"not found" after apply_batch_fixes_apr2026f.

Fix 1 - necron-trazyn-the-infinite
  Previous: 'trazyn the infinite necron'
  New:      'trazyn the infinite'
  Reason:   The extra word 'necron' over-filters the single known listing.
            User's confirmed eBay URL uses _skw=trazyn+the+infinite only.

Fix 2 - necron-ctan-shard-of-the-deceiver
  Previous: "C'tan Shard of The Deceiver Necron"
  New:      'ctan shard deceiver necrons'
  Reason:   The apostrophe in C'tan can cause eBay Browse API query
            encoding issues. Simplified query without punctuation is
            more reliable and still specific enough to find the listing.

Obelisk and Tesseract Vault remain on the shared search
'Obelisk Transcendent Ctan necron' -- no change needed, the listing
will auto-populate next time one appears on eBay.

Idempotent -- safe to re-run.
"""

from django.core.management.base import BaseCommand

from products.models import Product

FIXES = [
    ('necron-trazyn-the-infinite',        'trazyn the infinite'),
    ('necron-ctan-shard-of-the-deceiver', 'ctan shard deceiver necrons'),
]


class Command(BaseCommand):
    """Refine eBay search names for Trazyn and C'tan Deceiver."""

    help = (
        'Simplifies ebay_search_name for Trazyn the Infinite and C\'tan Shard of The Deceiver '
        'to improve eBay Browse API match rate. Idempotent.'
    )

    def handle(self, *args, **options):
        """Run the command."""
        self.stdout.write(self.style.MIGRATE_HEADING(
            '\n  -- apply_batch_fixes_apr2026g: Necron search-name refinements --'
        ))

        for slug, new_name in FIXES:
            product = Product.objects.filter(slug=slug).first()
            if not product:
                self.stdout.write(self.style.WARNING(f'  [skip] {slug} -- not found'))
                continue
            if product.ebay_search_name == new_name:
                self.stdout.write(f'  [no-op] {product.name} -- already set to "{new_name}"')
                continue
            old_name = product.ebay_search_name
            product.ebay_search_name = new_name
            product.save(update_fields=['ebay_search_name'])
            self.stdout.write(self.style.SUCCESS(
                f'  Updated: {product.name}\n'
                f'    "{old_name}" -> "{new_name}"'
            ))

        self.stdout.write(self.style.SUCCESS('\napply_batch_fixes_apr2026g complete.'))
