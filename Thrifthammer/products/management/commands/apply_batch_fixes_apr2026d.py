"""
Management command: apply_batch_fixes_apr2026d

Adds 'legions imperialis' as negative keywords to every active product
in the database that does not already have them.

Root cause: Some products (e.g. Space Marine Drop Pod) were returning
Legions Imperialis listings on eBay because LI uses the same unit names
as 40K but at 8mm/Epic scale. Adding 'legions' and 'imperialis' as
per-SKU negative keywords blocks all LI listings site-wide.

Implementation:
  - Appends 'legions imperialis' to existing ebay_negative_keywords,
    preserving any product-specific negatives already set.
  - Skips products that already contain both words.
  - Uses update_fields=['ebay_negative_keywords'] for efficiency.

Idempotent — safe to re-run.
"""

from django.core.management.base import BaseCommand

from products.models import Product

LI_TERMS = 'legions imperialis'


class Command(BaseCommand):
    """Add 'legions imperialis' negative keywords to every active product."""

    help = (
        'Appends "legions imperialis" to ebay_negative_keywords on every active product '
        'to prevent Legions Imperialis (Epic-scale) listings from matching 40K searches. '
        'Idempotent.'
    )

    def handle(self, *args, **options):
        """Run the command."""
        products = Product.objects.filter(is_active=True)
        updated = 0
        skipped = 0

        for product in products:
            existing = (product.ebay_negative_keywords or '').lower()

            # Skip if both words already present
            if 'legions' in existing and 'imperialis' in existing:
                skipped += 1
                continue

            current = (product.ebay_negative_keywords or '').strip()
            if current:
                product.ebay_negative_keywords = f'{current} {LI_TERMS}'
            else:
                product.ebay_negative_keywords = LI_TERMS

            product.save(update_fields=['ebay_negative_keywords'])
            updated += 1

        self.stdout.write(self.style.SUCCESS(
            f'\napply_batch_fixes_apr2026d complete.\n'
            f'  {updated} products updated with "legions imperialis" negative keywords.\n'
            f'  {skipped} products already had these keywords (skipped).'
        ))
