"""
Management command: apply_batch_fixes_apr2026x

Globally removes the standalone word 'new' from every product's
ebay_negative_keywords field.

ROOT CAUSE:
  Migration 0029 added 'new york' to all products as plain space-separated
  text (stored as: "logo ny rangers new york").  When the eBay API client
  builds the search query it prefixes each space-separated word with '-', so
  every product's query contains '-new'.  The eBay '-new' exclusion blocks
  any listing whose title contains the word "new" — including "Brand New",
  "New Sealed", "New in Box (NIB)" — which is the standard phrasing on
  virtually every sealed retail Warhammer kit.

  This means '-new' has been silently discarding the cheapest sealed listings
  across the entire site, not just Great Unclean One.

FIX:
  Strip the standalone word 'new' (word-boundary match) from every active
  product's ebay_negative_keywords.  After removal:
    - 'new york' → 'york'  (preserves the -york exclusion)
    - 'ny rangers' remains intact  (still blocks NY Rangers sports listings)
    - No other keyword is affected  (no keyword in the system contains 'new'
      as a substring except the 'new york' phrase from migration 0029)

  ╔══════════════════════════════════════════════════════════════════════╗
  ║  This is the ONLY command that removes tokens from                  ║
  ║  ebay_negative_keywords globally.  Do not combine with other        ║
  ║  keyword changes.  Every other keyword in the system is preserved   ║
  ║  exactly as set by populate_products.py + the batch fixes chain.    ║
  ╚══════════════════════════════════════════════════════════════════════╝

Idempotent — safe to re-run.
"""

import re

from django.core.management.base import BaseCommand

from products.models import Product


class Command(BaseCommand):
    """Remove standalone 'new' from all products' ebay_negative_keywords."""

    help = (
        "Removes the word 'new' (word-boundary) from every product's "
        "ebay_negative_keywords.  Unblocks Brand New / NIB eBay listings globally.  "
        "Idempotent."
    )

    def handle(self, *args, **options):
        """Run the fix."""
        updated = 0
        already_clean = 0

        for product in Product.objects.filter(is_active=True):
            raw = product.ebay_negative_keywords or ''
            if not raw:
                already_clean += 1
                continue

            # Remove any standalone occurrence of the word 'new'
            # (word boundary so we never touch 'renewal', 'knew', etc.)
            cleaned = re.sub(r'\bnew\b', '', raw)
            # Collapse double-spaces left by the removal, then strip edges
            cleaned = re.sub(r'  +', ' ', cleaned).strip()

            if cleaned == raw.strip():
                already_clean += 1
                continue

            product.ebay_negative_keywords = cleaned
            product.save(update_fields=['ebay_negative_keywords'])
            self.stdout.write(self.style.SUCCESS(
                f'  [{product.slug}] removed "new"\n'
                f'    was: "{raw}"\n'
                f'    now: "{cleaned}"'
            ))
            updated += 1

        self.stdout.write(self.style.SUCCESS(
            f'\nDone. {updated} product(s) updated, {already_clean} already clean / empty.'
        ))
