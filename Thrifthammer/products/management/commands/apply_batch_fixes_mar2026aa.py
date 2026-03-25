"""
Management command: apply_batch_fixes_mar2026aa

Twenty-sixth wave of March 2026 batch corrections for ThriftHammer.
Run after apply_batch_fixes_mar2026z.

Changes covered:
  Fix 1  -- Space Marine Ballistus Dreadnought (48-46):
             Set ebay_search_name to 'ballistus dreadnought' (2 keywords,
             min_matches=2).  The default 4-keyword product name requires
             min_matches=3; most eBay listings omit "Space Marine" so they
             score only 2/3 and are rejected, leaving the slot blank.
             Dropping to 2 keywords lets those listings score 2/2 → PASS.

  Fix 2  -- Space Marine Impulsor (48-94):
             Set ebay_search_name to 'impulsor warhammer' (2 keywords,
             min_matches=2).  The Impulsor has a sparse secondary market on
             eBay; combined with the description-mirrors-title filter this
             left the slot blank.  A 2-keyword query broadens eBay Best
             Match reach without introducing ambiguous tokens.
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from products.models import Product


class Command(BaseCommand):
    """Apply wave-AA March 2026 batch corrections to products."""

    help = 'Apply wave-AA March 2026 batch corrections.'

    def handle(self, *args, **options):
        """Apply all fixes atomically."""
        self.stdout.write('\napply_batch_fixes_mar2026aa')
        self.stdout.write('=' * 50)

        with transaction.atomic():
            self._fix_1_ballistus_search_name()
            self._fix_2_impulsor_search_name()

        self.stdout.write(self.style.SUCCESS('\nAll wave-AA fixes applied successfully.'))

    # -------------------------------------------------------------------------
    # Individual fixes
    # -------------------------------------------------------------------------

    def _fix_1_ballistus_search_name(self):
        """Set ebay_search_name for Space Marine Ballistus Dreadnought (48-46)."""
        self._set_ebay_search_name(
            '48-46',
            'ballistus dreadnought',
            'Fix 1: 48-46 Space Marine Ballistus Dreadnought',
        )

    def _fix_2_impulsor_search_name(self):
        """Set ebay_search_name for Space Marine Impulsor (48-94)."""
        self._set_ebay_search_name(
            '48-94',
            'impulsor warhammer',
            'Fix 2: 48-94 Space Marine Impulsor',
        )

    # -------------------------------------------------------------------------
    # Helper
    # -------------------------------------------------------------------------

    def _set_ebay_search_name(self, gw_sku, search_name, label):
        """Set Product.ebay_search_name for the given SKU."""
        try:
            p = Product.objects.get(gw_sku=gw_sku)
        except Product.DoesNotExist:
            self.stdout.write(self.style.WARNING(f'  {label}: product not found — skipped'))
            return

        old = p.ebay_search_name or ''
        if old == search_name:
            self.stdout.write(f'  {label}: ebay_search_name already "{search_name}" — skipped')
            return

        p.ebay_search_name = search_name
        p.save(update_fields=['ebay_search_name'])
        self.stdout.write(self.style.SUCCESS(
            f'  {label}: ebay_search_name → "{search_name}" (was "{old or "(blank)"}")'
        ))
