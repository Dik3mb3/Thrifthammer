"""
Management command: apply_batch_fixes_jun2026f

eBay negative keyword additions (2026-06-27).  All values are complete strings.

  50-26  Big Mek
  50-27  Big Mek in Mega Armour
    ebay_negative_keywords: + 'Shokk Attack'

  50-28 (Big Mek with Shokk Attack Gun) intentionally excluded — those words
  are part of its own product name and would filter out its own listings.
"""

from django.core.management.base import BaseCommand

from products.models import Product


class Command(BaseCommand):
    """eBay negative keyword additions for 2 products."""

    help = 'apply_batch_fixes_jun2026f — eBay negative keyword additions'

    def handle(self, *args, **options):
        """Run the command."""
        fixes = [
            ('50-26', 'legions imperialis Resin 04-113 D&D 5e 100th 1926 TShirt Plushie Plush Proxies Dakkarig Shokk Attack'),
            ('50-27', 'legions imperialis Resin 04-113 D&D 5e 100th 1926 TShirt Plushie Plush Proxies Dakkarig Shokk Attack'),
        ]

        for sku, value in fixes:
            updated = Product.objects.filter(gw_sku=sku).update(ebay_negative_keywords=value)
            if updated:
                self.stdout.write(f'  {sku}: ebay_negative_keywords set to {repr(value)}')
            else:
                self.stdout.write(self.style.WARNING(f'  {sku}: not found'))

        self.stdout.write(self.style.SUCCESS('apply_batch_fixes_jun2026f complete.'))
