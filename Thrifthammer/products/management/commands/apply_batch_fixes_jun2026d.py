"""
Management command: apply_batch_fixes_jun2026d

eBay negative keyword additions (2026-06-27).  All values are complete strings.

  54-22  Imperial Knight Questoris
    ebay_negative_keywords: + 'Avenger Gatling Cannon'

  AS-013  Adepta Sororitas Repentia Squad
    ebay_negative_keywords: + 'used'

  50-26  Big Mek
  50-27  Big Mek in Mega Armour
  50-28  Big Mek with Shokk Attack Gun
    ebay_negative_keywords: + 'Dakkarig'
"""

from django.core.management.base import BaseCommand

from products.models import Product


class Command(BaseCommand):
    """eBay negative keyword additions for 3 products."""

    help = 'apply_batch_fixes_jun2026d — eBay negative keyword additions'

    def handle(self, *args, **options):
        """Run the command."""
        fixes = [
            ('54-22',  'legions imperialis Resin 04-113 Proxies Avenger Gatling Cannon'),
            ('AS-013', 'legions imperialis Resin 04-113 100th 1926 TShirt Plushie Plush Proxies used'),
            ('50-26',  'legions imperialis Resin 04-113 D&D 5e 100th 1926 TShirt Plushie Plush Proxies Dakkarig'),
            ('50-27',  'legions imperialis Resin 04-113 D&D 5e 100th 1926 TShirt Plushie Plush Proxies Dakkarig'),
            ('50-28',  'legions imperialis Resin 04-113 D&D 5e 100th 1926 TShirt Plushie Plush Proxies Dakkarig'),
        ]

        for sku, value in fixes:
            updated = Product.objects.filter(gw_sku=sku).update(ebay_negative_keywords=value)
            if updated:
                self.stdout.write(f'  {sku}: ebay_negative_keywords set to {repr(value)}')
            else:
                self.stdout.write(self.style.WARNING(f'  {sku}: not found'))

        self.stdout.write(self.style.SUCCESS('apply_batch_fixes_jun2026d complete.'))
