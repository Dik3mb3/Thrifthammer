"""
Management command: apply_batch_fixes_apr2026w

Refines the eBay search name for Great Unclean One so valid listings are found.

ROOT CAUSE — 4-keyword search name:
  'Great Unclean One Nurgle Daemon Warhammer' produces 4 search keywords.
  Our validator requires ceil(4 * 0.65) = 3 matches.  AoS/40K crossover listing
  titles (e.g. "Maggotkin of Nurgle Great Unclean One NIB") only match on
  'great', 'unclean', 'nurgle' = 3 / 4 — this just barely passes, but many
  real listings are rejected, leaving the expensive outlier listing.

  Additionally, the stored value 'new york' in ebay_negative_keywords produces
  a '-new' eBay exclusion (because it is stored as two plain-text words).
  This blocks all "Brand New" / "New Sealed" / "NIB" listings at the eBay
  query level.  That global issue is fixed separately by apply_batch_fixes_apr2026x,
  which runs immediately after this command.

FIX (this command):
  Change ebay_search_name to 'Great Unclean One Warhammer' (3 keywords,
  requires ceil(3 * 0.65) = 2 matches).  AoS-style titles match on
  'great'/'unclean' + 'warhammer' = 2 / 3 → passes.  40K-style titles match
  all 3 → also passes.

  ebay_negative_keywords is NOT touched here — keyword changes are global
  and handled exclusively by apply_batch_fixes_apr2026x.

Idempotent — safe to re-run.
"""

from django.core.management.base import BaseCommand

from products.models import Product

SLUG = 'nurgle-great-unclean-one'
NEW_SEARCH_NAME = 'Great Unclean One Warhammer'


class Command(BaseCommand):
    """Refine GUO eBay search name only — no keyword changes."""

    help = "Fix GUO eBay listing: set ebay_search_name to 3-keyword pattern. No keyword changes."

    def handle(self, *args, **options):
        """Run the fix."""
        try:
            product = Product.objects.get(slug=SLUG)
        except Product.DoesNotExist:
            self.stdout.write(self.style.WARNING(f'  [{SLUG}] not found — skipping.'))
            return

        if product.ebay_search_name != NEW_SEARCH_NAME:
            old_name = product.ebay_search_name or '(none)'
            product.ebay_search_name = NEW_SEARCH_NAME
            product.save(update_fields=['ebay_search_name'])
            self.stdout.write(self.style.SUCCESS(
                f'  [{SLUG}] ebay_search_name "{old_name}" → "{NEW_SEARCH_NAME}"'
            ))
        else:
            self.stdout.write(
                f'  [{SLUG}] ebay_search_name already correct — no change.'
            )

        self.stdout.write(self.style.SUCCESS('\nDone.'))
