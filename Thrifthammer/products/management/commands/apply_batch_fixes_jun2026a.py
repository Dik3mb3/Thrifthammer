"""
Management command: apply_batch_fixes_jun2026a

Changes:
  OW-023  Destruction Battletome: Orruk Warclans
    ebay_negative_keywords: '3rd Edition 3rd Ed.'
    Old: ''
    New: '3rd Edition 3rd Ed.'

Reason: eBay dry-run matched a 3rd Edition Battletome listing; excluding
'3rd Edition' and '3rd Ed.' prevents wrong-edition results.
"""

from django.core.management.base import BaseCommand

from products.models import Product


class Command(BaseCommand):
    """Add 3rd Edition eBay negative keywords to OW-023."""

    help = 'apply_batch_fixes_jun2026a — eBay negative keyword fix for OW-023'

    def handle(self, *args, **options):
        """Run the command."""
        fixes = [
            ('OW-023', '3rd Edition 3rd Ed.'),
        ]

        for sku, keywords in fixes:
            updated = Product.objects.filter(gw_sku=sku).update(
                ebay_negative_keywords=keywords,
            )
            if updated:
                self.stdout.write(f'  {sku}: ebay_negative_keywords set to {repr(keywords)}')
            else:
                self.stdout.write(self.style.WARNING(f'  {sku}: not found'))

        self.stdout.write(self.style.SUCCESS('apply_batch_fixes_jun2026a complete.'))
