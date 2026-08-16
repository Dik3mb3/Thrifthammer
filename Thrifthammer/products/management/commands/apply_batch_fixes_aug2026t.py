"""
Management command: apply_batch_fixes_aug2026t

Targeted eBay negative-keyword correction for 46-25 (Aeldari Combat
Patrol). User-confirmed 2026-08-14: the 2026-08-14 eBay run matched it to
"Warhammer 40K Combat Patrol: Aeldari Corsairs NEW UNOPENED" -- a listing
for the distinct "Combat Patrol: Aeldari Corsairs" product (P-240879), not
the base Combat Patrol box. "Corsairs" excludes that cross-match.

Usage:
    python manage.py apply_batch_fixes_aug2026t
"""

from django.core.management.base import BaseCommand

from products.models import Product

FIXES = [
    # (gw_sku, new_ebay_negative_keywords)
    ('46-25', 'legions imperialis Resin 04-113 Proxies Foil magazine issue x5 5x x10 10x x2 2x 3x x3 x4 4x Corsairs'),
]


class Command(BaseCommand):
    """Add 'Corsairs' negative keyword to Aeldari Combat Patrol."""

    help = 'apply_batch_fixes_aug2026t — eBay negative-keyword correction (1 SKU)'

    def handle(self, *args, **options):
        """Run the command."""
        updated = 0
        for gw_sku, new_value in FIXES:
            count = Product.objects.filter(gw_sku=gw_sku).update(
                ebay_negative_keywords=new_value,
            )
            if count:
                self.stdout.write(f'  updated: {gw_sku}')
                updated += 1
            else:
                self.stdout.write(self.style.WARNING(f'  NOT FOUND: {gw_sku}'))

        self.stdout.write(self.style.SUCCESS(
            f'apply_batch_fixes_aug2026t complete. {updated} product(s) updated.'
        ))
