"""
Management command: apply_batch_fixes_may2026p

Changes:
  BB-012  Human Blood Bowl Team  -- add Dugouts, Pitch to ebay_negative_keywords
    Old: 'Dice'
    New: 'Dice Dugouts Pitch'

  BB-094  Orc Blood Bowl Team    -- add Dugouts, Pitch to ebay_negative_keywords
    Old: 'Dice'
    New: 'Dice Dugouts Pitch'
"""

from django.core.management.base import BaseCommand

from products.models import Product


_FIXES = [
    ('BB-012', 'Human Blood Bowl Team',  'Dice Dugouts Pitch'),
    ('BB-094', 'Orc Blood Bowl Team',    'Dice Dugouts Pitch'),
]


class Command(BaseCommand):
    """Add Dugouts and Pitch to eBay negative keywords for Human and Orc Blood Bowl Teams."""

    help = (
        'Sets ebay_negative_keywords for BB-012 and BB-094 to '
        '"Dice Dugouts Pitch". Idempotent.'
    )

    def handle(self, *args, **options):
        """Run the command."""
        updated_total = 0

        for gw_sku, name, keywords in _FIXES:
            updated = Product.objects.filter(gw_sku=gw_sku).update(
                ebay_negative_keywords=keywords,
            )
            if updated:
                self.stdout.write(f'  Updated: {name} ({gw_sku}) -> "{keywords}"')
                updated_total += updated
            else:
                self.stdout.write(self.style.WARNING(
                    f'  Not found: {name} ({gw_sku}) -- skipped.'
                ))

        self.stdout.write(self.style.SUCCESS(
            f'apply_batch_fixes_may2026p complete. {updated_total} product(s) updated.'
        ))
