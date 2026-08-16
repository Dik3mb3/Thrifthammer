"""
Management command: apply_batch_fixes_aug2026s

Aligns the "Vyper" product's ebay_search_name with its dual-build sibling
"Starfang" (same physical box, same gw_sku P-240924, two build options) so
both search eBay under the same generic term. User-confirmed 2026-08-14:
Vyper was 'Vyper Starfang Aeldari Warhammer', changed to match Starfang's
existing 'Vyper Aeldari Warhammer'.

Both rows share gw_sku P-240924 -- filtered by name as well so only the
Vyper row is touched, not Starfang.

Usage:
    python manage.py apply_batch_fixes_aug2026s
"""

from django.core.management.base import BaseCommand

from products.models import Product


class Command(BaseCommand):
    """Align Vyper's ebay_search_name with Starfang's."""

    help = 'apply_batch_fixes_aug2026s — Vyper ebay_search_name matches Starfang (1 SKU)'

    def handle(self, *args, **options):
        """Run the command."""
        count = Product.objects.filter(gw_sku='P-240924', name='Vyper').update(
            ebay_search_name='Vyper Aeldari Warhammer',
        )
        if count:
            self.stdout.write('  updated: P-240924 (Vyper)')
        else:
            self.stdout.write(self.style.WARNING('  NOT FOUND: P-240924 (Vyper)'))

        self.stdout.write(self.style.SUCCESS(
            f'apply_batch_fixes_aug2026s complete. {count} product(s) updated.'
        ))
