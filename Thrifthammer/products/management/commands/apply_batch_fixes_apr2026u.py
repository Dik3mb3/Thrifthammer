"""
Management command: apply_batch_fixes_apr2026u

Fixes:
- death-guard-chosen-of-mortarion: add phrase "Chaos Marines" to
  ebay_negative_keywords so eBay search excludes listings containing that
  exact phrase but still allows listings with "Chaos" or "Marines" alone.

The phrase is stored with surrounding double-quotes so shlex.split() treats
it as a single token:  "Chaos Marines"
The eBay query builder then emits:  -"Chaos Marines"

Idempotent — safe to re-run.
"""

from django.core.management.base import BaseCommand

from products.models import Product

SLUG = 'death-guard-chosen-of-mortarion'
PHRASE = '"Chaos Marines"'


class Command(BaseCommand):
    """Add "Chaos Marines" phrase avoid keyword to Chosen of Mortarion."""

    help = 'Add "Chaos Marines" phrase negative keyword to Chosen of Mortarion.'

    def handle(self, *args, **options):
        """Run the fix."""
        try:
            product = Product.objects.get(slug=SLUG)
        except Product.DoesNotExist:
            self.stdout.write(self.style.WARNING(f'  [{SLUG}] not found — skipping.'))
            return

        existing = product.ebay_negative_keywords or ''

        if PHRASE in existing:
            self.stdout.write(f'  [{SLUG}] already has {PHRASE!r} — no change.')
            return

        product.ebay_negative_keywords = f'{existing} {PHRASE}'.strip()
        product.save(update_fields=['ebay_negative_keywords'])
        self.stdout.write(self.style.SUCCESS(
            f'  [{SLUG}] ebay_negative_keywords → "{product.ebay_negative_keywords}"'
        ))
