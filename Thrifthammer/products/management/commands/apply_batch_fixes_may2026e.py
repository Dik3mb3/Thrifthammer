"""
Management command: apply_batch_fixes_may2026e

Targeted ebay_negative_keywords update.

Changes:
  73-25  Leagues of Votann Combat Patrol
         Add: Magazine, Magazines
         Before: 'legions imperialis Resin 04-113 52026 Complete'
         After:  'legions imperialis Resin 04-113 52026 Complete Magazine Magazines'

Idempotent — safe to re-run.
"""

from django.core.management.base import BaseCommand

from products.models import Product


class Command(BaseCommand):
    """Apply batch fixes may2026e — eBay negative keyword additions."""

    help = 'Targeted ebay_negative_keywords update for Leagues of Votann Combat Patrol.'

    def handle(self, *args, **options):
        """Run the command."""
        updated = Product.objects.filter(gw_sku='73-25').update(
            ebay_negative_keywords='legions imperialis Resin 04-113 52026 Complete Magazine Magazines',
        )
        self.stdout.write(self.style.SUCCESS(
            f'apply_batch_fixes_may2026e complete. Updated {updated} record(s).'
        ))
