"""
apply_batch_fixes_apr2026s
~~~~~~~~~~~~~~~~~~~~~~~~~~
- Necrons Royal Court: clear gw_sku (prod4900147 was a bundle SKU that no
  longer maps cleanly to individual units — removing it stops the GW scraper
  from matching the wrong product).
- Contemptor Dreadnought (HA-002): add 'osiron' as eBay negative keyword so
  Osiron Pattern Contemptor listings are not matched against the standard kit.

Idempotent — safe to re-run.
"""

from django.core.management.base import BaseCommand

from products.models import Product


class Command(BaseCommand):
    """Clear Necrons Royal Court SKU; add osiron avoid kw to Contemptor."""

    help = 'Apr-2026-s: Necrons Royal Court SKU clear; Contemptor osiron neg kw.'

    def handle(self, *args, **options):
        """Apply both fixes."""
        self._clear_royal_court_sku()
        self._add_contemptor_osiron_kw()
        self.stdout.write(self.style.SUCCESS('Done.'))

    def _clear_royal_court_sku(self):
        """Remove gw_sku from Necrons Royal Court product."""
        product = Product.objects.filter(slug='necrons-royal-court').first()
        if not product:
            self.stdout.write(self.style.WARNING(
                'necrons-royal-court not found — skipping.'
            ))
            return
        old_sku = product.gw_sku
        product.gw_sku = ''
        product.save(update_fields=['gw_sku'])
        self.stdout.write(
            f'necrons-royal-court: gw_sku cleared (was "{old_sku}").'
        )

    def _add_contemptor_osiron_kw(self):
        """Add osiron to Contemptor Dreadnought eBay negative keywords."""
        product = Product.objects.filter(slug='contemptor-dreadnought').first()
        if not product:
            self.stdout.write(self.style.WARNING(
                'contemptor-dreadnought not found — skipping.'
            ))
            return
        existing = set((product.ebay_negative_keywords or '').split())
        existing.add('osiron')
        product.ebay_negative_keywords = ' '.join(sorted(existing))
        product.save(update_fields=['ebay_negative_keywords'])
        self.stdout.write(
            f'contemptor-dreadnought: ebay_negative_keywords -> '
            f'"{product.ebay_negative_keywords}".'
        )
