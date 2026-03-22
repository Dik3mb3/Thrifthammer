"""
Management command: apply_batch_fixes_mar2026y

Twenty-fourth wave of March 2026 batch corrections for ThriftHammer.
Run after apply_batch_fixes_mar2026x.

Changes covered:
  Fix 1  -- T'au Pathfinders (56-19):
             - Append 'mantic enforcer firefight' to neg_kw.
               eBay returns Mantic Games "Deadzone Firefight" Enforcers
               (a different sci-fi miniature game) whose listings include
               "Pathfinders" as a unit name — these pass keyword matching
               but are the wrong product entirely.

  Fix 2  -- Adepta Sororitas Battle Sisters Squad (52-20):
             - Set neg_kw to 'repentia'.
               eBay returns Sisters of Repentance/Repentia listings
               which share "Sisters" + "Battle" keywords with the
               Battle Sisters Squad — wrong unit from the same faction.
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from products.models import Product


class Command(BaseCommand):
    """Apply wave-Y March 2026 batch corrections to products."""

    help = 'Apply wave-Y March 2026 batch corrections.'

    def handle(self, *args, **options):
        """Apply all fixes atomically."""
        self.stdout.write('\napply_batch_fixes_mar2026y')
        self.stdout.write('=' * 50)

        with transaction.atomic():
            self._fix_1_pathfinders_neg_kw()
            self._fix_2_battle_sisters_neg_kw()

        self.stdout.write(self.style.SUCCESS('\nAll wave-Y fixes applied successfully.'))

    # -------------------------------------------------------------------------
    # Individual fixes
    # -------------------------------------------------------------------------

    def _fix_1_pathfinders_neg_kw(self):
        """Append Mantic/Enforcer/Firefight keywords to T'au Pathfinders (56-19)."""
        try:
            p = Product.objects.get(gw_sku='56-19')
        except Product.DoesNotExist:
            self.stdout.write(self.style.WARNING('  Fix 1: 56-19 not found — skipped'))
            return

        existing = p.ebay_negative_keywords or ''
        if 'mantic' in existing and 'enforcer' in existing and 'firefight' in existing:
            self.stdout.write(f'  Fix 1: 56-19 neg_kw already has mantic/enforcer/firefight — skipped')
            return

        # Append to existing keywords rather than replace
        extra = 'mantic enforcer firefight'
        new_kw = f'{existing} {extra}'.strip() if existing else extra
        p.ebay_negative_keywords = new_kw
        p.save()
        self.stdout.write(self.style.SUCCESS(
            f'  Fix 1: 56-19 neg_kw → "{new_kw}" (was "{existing}")'
        ))

    def _fix_2_battle_sisters_neg_kw(self):
        """Set Battle Sisters Squad neg_kw to 'repentia' (52-20)."""
        try:
            p = Product.objects.get(gw_sku='52-20')
        except Product.DoesNotExist:
            self.stdout.write(self.style.WARNING('  Fix 2: 52-20 not found — skipped'))
            return

        existing = p.ebay_negative_keywords or ''
        if 'repentia' in existing:
            self.stdout.write(f'  Fix 2: 52-20 neg_kw already has repentia — skipped')
            return

        new_kw = f'{existing} repentia'.strip() if existing else 'repentia'
        p.ebay_negative_keywords = new_kw
        p.save()
        self.stdout.write(self.style.SUCCESS(
            f'  Fix 2: 52-20 neg_kw → "{new_kw}" (was "{existing}")'
        ))
