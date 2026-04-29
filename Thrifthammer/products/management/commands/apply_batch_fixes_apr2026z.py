"""
Management command: apply_batch_fixes_apr2026z

Fix 1 — Global negative keywords (all active products):
  Add 'Resin' and '04-113' to ebay_negative_keywords.
  'Resin' blocks resin-cast third-party miniatures polluting results.
  '04-113' is a GW catalogue code that appears in wrong-product listings.
  Both are appended only if not already present (idempotent).

Fix 2 — Rhino ebay_search_name:
  Product slug 'space-marine-rhino' (name 'Rhino') is too generic and
  matches Chaos Rhino listings on eBay.
  New search name: 'Space Marine Rhino' — more specific, still returns
  the correct kit.

Idempotent — safe to re-run.
"""

import shlex

from django.core.management.base import BaseCommand

from products.models import Product


GLOBAL_ADD_KEYWORDS = ['Resin', '04-113']

RHINO_SLUG            = 'space-marine-rhino'
RHINO_NEW_SEARCH_NAME = 'Space Marine Rhino'


class Command(BaseCommand):
    """Add global eBay negative keywords and fix Rhino search name."""

    help = (
        'Global: add Resin + 04-113 to ebay_negative_keywords. '
        'Rhino: set ebay_search_name to "Space Marine Rhino".'
    )

    def handle(self, *args, **options):
        """Run the fixes."""
        self._fix_global_keywords()
        self._fix_rhino_search_name()

    # ------------------------------------------------------------------

    def _fix_global_keywords(self):
        """Append Resin and 04-113 to every active product's negative keywords."""
        added    = 0
        skipped  = 0

        for product in Product.objects.filter(is_active=True).order_by('gw_sku'):
            raw = product.ebay_negative_keywords or ''

            try:
                existing_tokens = shlex.split(raw)
            except ValueError:
                existing_tokens = raw.split()

            existing_lower = [t.lower() for t in existing_tokens]
            to_add = [
                kw for kw in GLOBAL_ADD_KEYWORDS
                if kw.lower() not in existing_lower
            ]

            if not to_add:
                skipped += 1
                continue

            product.ebay_negative_keywords = (raw + ' ' + ' '.join(to_add)).strip()
            product.save(update_fields=['ebay_negative_keywords'])
            added += 1

        self.stdout.write(self.style.SUCCESS(
            f'[keywords] Added to {added} product(s). '
            f'{skipped} already had all keywords — skipped.'
        ))

    def _fix_rhino_search_name(self):
        """Set Space Marine Rhino ebay_search_name."""
        try:
            rhino = Product.objects.get(slug=RHINO_SLUG)
        except Product.DoesNotExist:
            self.stdout.write(self.style.WARNING(
                f'[rhino] Product slug "{RHINO_SLUG}" not found — skipping.'
            ))
            return

        if rhino.ebay_search_name == RHINO_NEW_SEARCH_NAME:
            self.stdout.write(
                f'[rhino] Already "{RHINO_NEW_SEARCH_NAME}" — no change.'
            )
            return

        old = rhino.ebay_search_name or '(none)'
        rhino.ebay_search_name = RHINO_NEW_SEARCH_NAME
        rhino.save(update_fields=['ebay_search_name'])
        self.stdout.write(self.style.SUCCESS(
            f'[rhino] "{old}" → "{RHINO_NEW_SEARCH_NAME}"'
        ))
