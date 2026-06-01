"""
Management command: apply_batch_fixes_may2026g

Targeted ebay_search_name update.

Changes:
  99120201130  Daemon Prince
               Before: 'Daemon Prince Warhammer Chaos'
               After:  'Daemon Prince Warhammer'

Idempotent — safe to re-run.
"""

from django.core.management.base import BaseCommand

from products.models import Product


class Command(BaseCommand):
    """Apply batch fixes may2026g — eBay search name update."""

    help = 'Targeted ebay_search_name update for Daemon Prince.'

    def handle(self, *args, **options):
        """Run the command."""
        updated = Product.objects.filter(gw_sku='99120201130').update(
            ebay_search_name='Daemon Prince Warhammer',
        )
        self.stdout.write(self.style.SUCCESS(
            f'apply_batch_fixes_may2026g complete. Updated {updated} record(s).'
        ))
