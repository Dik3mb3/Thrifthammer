"""
Management command: apply_batch_fixes_aug2026v

Targeted eBay negative-keyword corrections for 3 SKUs, per user-confirmed
match/mismatch review 2026-08-16.

- GC-010 (Genestealer Cults Goliath Rockgrinder): "drilldozer" excludes a
  known mismatched listing.
- AM-018 (Astra Militarum Death Korps of Krieg): "heavy" excludes a known
  mismatched listing.
- AM-038 (Astra Militarum Primaris Psyker): blocks item 167183855437
  ("Warhammer 40k Astra Militarum Primaris Psyker New in Box") by numeric
  eBay item ID -- user-confirmed wrong, no usable title keyword to exclude
  it any other way.

Usage:
    python manage.py apply_batch_fixes_aug2026v
"""

from django.core.management.base import BaseCommand

from products.models import Product

FIXES = [
    # (gw_sku, new_ebay_negative_keywords)
    ('GC-010', '100th 1926 TShirt Plushie Plush legions imperialis Resin 04-113 Proxies Foil magazine issue x5 5x x10 10x x2 2x 3x x3 x4 4x drilldozer'),
    ('AM-018', 'legions imperialis Resin 04-113 100th 1926 TShirt Plushie Plush Proxies Foil magazine issue x5 5x x10 10x x2 2x 3x x3 x4 4x heavy'),
    ('AM-038', 'legions imperialis Resin 04-113 100th 1926 TShirt Plushie Plush Proxies Foil magazine issue x5 5x x10 10x x2 2x 3x x3 x4 4x 167183855437'),
]


class Command(BaseCommand):
    """Apply targeted eBay negative-keyword corrections for 3 SKUs."""

    help = 'apply_batch_fixes_aug2026v — eBay negative-keyword corrections (3 SKUs)'

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
            f'apply_batch_fixes_aug2026v complete. {updated} product(s) updated.'
        ))
