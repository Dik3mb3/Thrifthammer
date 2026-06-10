"""
Management command: apply_batch_fixes_may2026k

Changes:
  prod4870187   Warlocks (Aeldari)
                ebay_search_name: '' → 'Aeldari Warlocks Warhammer'
                ebay_negative_keywords: add Rise, Fall, CD to existing defaults

Idempotent — safe to re-run.
"""

from django.core.management.base import BaseCommand

from products.models import Product


class Command(BaseCommand):
    """Apply batch fixes may2026k — Warlocks eBay search name and negative keywords."""

    help = 'Warlocks eBay search name and negative keyword update.'

    def handle(self, *args, **options):
        """Run all fixes."""
        updated = Product.objects.filter(gw_sku='prod4870187').update(
            ebay_search_name='Aeldari Warlocks Warhammer',
            ebay_negative_keywords=(
                'legions imperialis Resin 04-113 D&D 5e 100th 1926 TShirt Plushie Plush Rise Fall CD'
            ),
        )
        self.stdout.write(f'Warlocks: {updated} product(s) updated.')
        self.stdout.write(self.style.SUCCESS('apply_batch_fixes_may2026k complete.'))
