"""
Management command: apply_batch_fixes_apr2026aa

Fix 1 — Bloodcrushers of Khorne SKU-specific negative keyword:
  Add 'Sealed' to ebay_negative_keywords for khorne-bloodcrushers.
  Blocks sealed/unopened box listings that tend to skew prices.

Idempotent — safe to re-run.
"""

import shlex

from django.core.management.base import BaseCommand

from products.models import Product


SLUG    = 'khorne-bloodcrushers'
ADD_KWS = ['Sealed']


class Command(BaseCommand):
    """Add 'Sealed' as a negative keyword for Bloodcrushers of Khorne."""

    help = 'Bloodcrushers of Khorne: add "Sealed" to ebay_negative_keywords.'

    def handle(self, *args, **options):
        """Run the fix."""
        try:
            product = Product.objects.get(slug=SLUG)
        except Product.DoesNotExist:
            self.stdout.write(self.style.WARNING(
                f'[bloodcrushers] Product slug "{SLUG}" not found — skipping.'
            ))
            return

        raw = product.ebay_negative_keywords or ''

        try:
            existing_tokens = shlex.split(raw)
        except ValueError:
            existing_tokens = raw.split()

        existing_lower = [t.lower() for t in existing_tokens]
        to_add = [kw for kw in ADD_KWS if kw.lower() not in existing_lower]

        if not to_add:
            self.stdout.write(
                f'[bloodcrushers] Already has all keywords — no change.'
            )
            return

        product.ebay_negative_keywords = (raw + ' ' + ' '.join(to_add)).strip()
        product.save(update_fields=['ebay_negative_keywords'])
        self.stdout.write(self.style.SUCCESS(
            f'[bloodcrushers] Added: {to_add}  →  "{product.ebay_negative_keywords}"'
        ))
