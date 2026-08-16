"""
Management command: apply_batch_fixes_aug2026w

Targeted eBay negative-keyword corrections, per user clarification
2026-08-16: the previous session's AM-038 block (aug2026v) was meant for
the UK listing, not US -- reverted here. ebay_negative_keywords is shared
between the US and UK matchers (no separate _uk field), but numeric
item-ID blocks are inherently marketplace-specific (a UK item ID never
appears in US search results and vice versa), so this is safe either way.

- AM-038 (Astra Militarum Primaris Psyker): removes the US item ID
  167183855437 added in aug2026v (reverted -- was blocked in error), adds
  the UK item ID 398266022644 (the actual listing the user wants blocked,
  https://www.ebay.co.uk/itm/398266022644).
- 51-42 (Genestealer Cults Broodcoven): blocks UK item 227476720296
  (https://www.ebay.co.uk/itm/227476720296).

Usage:
    python manage.py apply_batch_fixes_aug2026w
"""

from django.core.management.base import BaseCommand

from products.models import Product

FIXES = [
    # (gw_sku, new_ebay_negative_keywords)
    ('AM-038', 'legions imperialis Resin 04-113 100th 1926 TShirt Plushie Plush Proxies Foil magazine issue x5 5x x10 10x x2 2x 3x x3 x4 4x 398266022644'),
    ('51-42', 'legions imperialis Resin 04-113 Proxies Foil Magus magazine issue x5 5x x10 10x x2 2x 3x x3 x4 4x 227476720296'),
]


class Command(BaseCommand):
    """Apply targeted eBay negative-keyword corrections (UK listing blocks)."""

    help = 'apply_batch_fixes_aug2026w — eBay negative-keyword corrections (2 SKUs, UK)'

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
            f'apply_batch_fixes_aug2026w complete. {updated} product(s) updated.'
        ))
