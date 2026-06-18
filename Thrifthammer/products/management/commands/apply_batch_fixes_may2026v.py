"""
Management command: apply_batch_fixes_may2026v

Changes:
  DOK-003  Bloodwrack Shrine
    ebay_negative_keywords: 'Bloodwrack Melusai'
    Old: ''
    New: 'Bloodwrack Melusai'

  DOK-004  Slaughter Queen on Cauldron of Blood
    ebay_negative_keywords: 'Bloodwrack Melusai'
    Old: ''
    New: 'Bloodwrack Melusai'

  DOK-005  Hag Queen on Cauldron of Blood
    ebay_negative_keywords: 'Bloodwrack Melusai'
    Old: ''
    New: 'Bloodwrack Melusai'

Reason: all three share the "Cauldron of Blood Daughters Khaine" eBay search
name; excluding "Bloodwrack Melusai" prevents matching the Bloodwrack Shrine
listing which shares the kit.
"""

from django.core.management.base import BaseCommand

from products.models import Product


class Command(BaseCommand):
    """Add Bloodwrack Melusai eBay negative keywords to DOK Cauldron of Blood SKUs."""

    help = 'apply_batch_fixes_may2026v — eBay negative keyword fixes for DOK-003/004/005'

    def handle(self, *args, **options):
        """Run the command."""
        fixes = [
            ('DOK-003', 'Bloodwrack Melusai'),
            ('DOK-004', 'Bloodwrack Melusai'),
            ('DOK-005', 'Bloodwrack Melusai'),
        ]

        for sku, keywords in fixes:
            updated = Product.objects.filter(gw_sku=sku).update(
                ebay_negative_keywords=keywords,
            )
            if updated:
                self.stdout.write(f'  {sku}: ebay_negative_keywords set to {repr(keywords)}')
            else:
                self.stdout.write(self.style.WARNING(f'  {sku}: not found'))

        self.stdout.write(self.style.SUCCESS('apply_batch_fixes_may2026v complete.'))
