"""
Management command: apply_batch_fixes_jun2026e

eBay negative keyword additions (2026-06-27).  All values are complete strings.

  50-10  Ork Boyz
    ebay_negative_keywords: + 'Wrecka Krew Breaka Tankbustas'
"""

from django.core.management.base import BaseCommand

from products.models import Product


class Command(BaseCommand):
    """eBay negative keyword additions for 1 product."""

    help = 'apply_batch_fixes_jun2026e — eBay negative keyword additions'

    def handle(self, *args, **options):
        """Run the command."""
        fixes = [
            ('50-10', 'lootas legions imperialis Resin 04-113 Proxies Bosspole knives Eavy Wrecka Krew Breaka Tankbustas'),
        ]

        for sku, value in fixes:
            updated = Product.objects.filter(gw_sku=sku).update(ebay_negative_keywords=value)
            if updated:
                self.stdout.write(f'  {sku}: ebay_negative_keywords set to {repr(value)}')
            else:
                self.stdout.write(self.style.WARNING(f'  {sku}: not found'))

        self.stdout.write(self.style.SUCCESS('apply_batch_fixes_jun2026e complete.'))
