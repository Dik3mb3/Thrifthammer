"""
Management command: apply_batch_fixes_mar2026x

Twenty-third wave of March 2026 batch corrections for ThriftHammer.
Run after apply_batch_fixes_mar2026w.

Changes covered:
  Fix 1  -- Thousand Sons Ahriman (43-30):
             - Update neg_kw from 'horus' to 'horus azhek ahzek'.
               eBay listings for the Horus Heresy era version of Ahriman
               use the HH-era character spelling "Azhek/Ahzek Ahriman"
               rather than "Horus Heresy" explicitly in the title.
               'horus' alone missed those listings; 'azhek'/'ahzek' are
               unambiguous HH-exclusive name spellings.

  Fix 2  -- Astra Militarum Cadian Shock Troops (47-30):
             - Clear ebay_search_name (blank it).
               The override 'Warhammer Cadian Shock Troops' was set to avoid
               wrong Cadian kits but the new description-mirrors-title bot
               detection in _is_valid_result now handles spam storefronts
               (e.g. "2ndarms") that previously ranked first.  Using the
               full product name 'Astra Militarum Cadian Shock Troops' gives
               better eBay search results without the old override.
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from products.models import Product


class Command(BaseCommand):
    """Apply wave-X March 2026 batch corrections to products."""

    help = 'Apply wave-X March 2026 batch corrections.'

    def handle(self, *args, **options):
        """Apply all fixes atomically."""
        self.stdout.write('\napply_batch_fixes_mar2026x')
        self.stdout.write('=' * 50)

        with transaction.atomic():
            self._fix_1_ahriman_neg_kw()
            self._fix_2_cadian_search_name()

        self.stdout.write(self.style.SUCCESS('\nAll wave-X fixes applied successfully.'))

    # -------------------------------------------------------------------------
    # Individual fixes
    # -------------------------------------------------------------------------

    def _fix_1_ahriman_neg_kw(self):
        """Update Thousand Sons Ahriman neg_kw to include azhek/ahzek (43-30)."""
        try:
            p = Product.objects.get(gw_sku='43-30')
        except Product.DoesNotExist:
            self.stdout.write(self.style.WARNING('  Fix 1: 43-30 not found — skipped'))
            return

        new_kw = 'horus azhek ahzek'
        existing = p.ebay_negative_keywords or ''
        if 'azhek' in existing and 'ahzek' in existing:
            self.stdout.write(f'  Fix 1: 43-30 neg_kw already has azhek/ahzek — skipped')
            return

        p.ebay_negative_keywords = new_kw
        p.save()
        self.stdout.write(self.style.SUCCESS(
            f'  Fix 1: 43-30 neg_kw → "{new_kw}" (was "{existing}")'
        ))

    def _fix_2_cadian_search_name(self):
        """Clear Cadian Shock Troops ebay_search_name override (47-30)."""
        try:
            p = Product.objects.get(gw_sku='47-30')
        except Product.DoesNotExist:
            self.stdout.write(self.style.WARNING('  Fix 2: 47-30 not found — skipped'))
            return

        old_name = p.ebay_search_name or ''
        if not old_name:
            self.stdout.write(f'  Fix 2: 47-30 ebay_search_name already blank — skipped')
            return

        p.ebay_search_name = ''
        p.save()
        self.stdout.write(self.style.SUCCESS(
            f'  Fix 2: 47-30 ebay_search_name cleared (was "{old_name}")'
        ))
