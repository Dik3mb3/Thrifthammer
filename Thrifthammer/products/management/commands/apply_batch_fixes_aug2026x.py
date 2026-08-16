"""
Management command: apply_batch_fixes_aug2026x

Targeted eBay negative-keyword correction for TY-003 (Tyranid Broodlord),
per user request 2026-08-16 -- adds "poster" to exclude a mismatched
listing. (A catalog-wide "poster" exclusion was discussed but explicitly
not applied -- this is scoped to Broodlord only.)

Usage:
    python manage.py apply_batch_fixes_aug2026x
"""

from django.core.management.base import BaseCommand

from products.models import Product

FIXES = [
    # (gw_sku, new_ebay_negative_keywords)
    ('TY-003', 'legions imperialis Resin 04-113 100th 1926 TShirt Plushie Plush Proxies Foil magazine issue x5 5x x10 10x x2 2x 3x x3 x4 4x poster'),
]


class Command(BaseCommand):
    """Add 'poster' negative keyword to Tyranid Broodlord."""

    help = 'apply_batch_fixes_aug2026x — eBay negative-keyword correction (1 SKU)'

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
            f'apply_batch_fixes_aug2026x complete. {updated} product(s) updated.'
        ))
