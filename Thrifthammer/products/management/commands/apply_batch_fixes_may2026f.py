"""
Management command: apply_batch_fixes_may2026f

Targeted ebay_negative_keywords update.

Changes:
  55-23  Black Templars Sword Brethren
         Add: 1x, Crusader
         Before: 'x1'
         After:  'x1 1x Crusader'

Idempotent — safe to re-run.
"""

from django.core.management.base import BaseCommand

from products.models import Product


class Command(BaseCommand):
    """Apply batch fixes may2026f — eBay negative keyword additions."""

    help = 'Targeted ebay_negative_keywords update for Black Templars Sword Brethren.'

    def handle(self, *args, **options):
        """Run the command."""
        updated = Product.objects.filter(gw_sku='55-23').update(
            ebay_negative_keywords='x1 1x Crusader',
        )
        self.stdout.write(self.style.SUCCESS(
            f'apply_batch_fixes_may2026f complete. Updated {updated} record(s).'
        ))
