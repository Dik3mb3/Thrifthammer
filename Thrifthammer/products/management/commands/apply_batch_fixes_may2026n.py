"""
Batch fix may2026n — eBay negative keyword additions for Gloomspite Gitz Arachnarok/Troggoths.

Adds "Fantasy" to ebay_negative_keywords for:
  GG-030  Skitterstrand Arachnarok
  GG-031  Arachnarok Spider with Flinger
  GG-032  Webspinner Shaman on Arachnarok Spider
  GG-034  Arachnarok Spider with Spiderfang Warparty

Previous value: 'legions imperialis Resin 04-113'
New value:      'legions imperialis Resin 04-113 Fantasy'
"""

from django.core.management.base import BaseCommand
from products.models import Product


class Command(BaseCommand):
    """Add Fantasy eBay negative keyword to GG-030, GG-031, GG-032, GG-034."""

    help = 'Batch fix may2026n: add Fantasy eBay negative keyword to Arachnarok SKUs.'

    def handle(self, *args, **options):
        """Run the batch fix."""
        skus = ['GG-030', 'GG-031', 'GG-032', 'GG-034']
        new_value = 'legions imperialis Resin 04-113 Fantasy'

        updated = Product.objects.filter(gw_sku__in=skus).update(
            ebay_negative_keywords=new_value,
        )
        self.stdout.write(
            self.style.SUCCESS(
                f'apply_batch_fixes_may2026n complete. Updated {updated} product(s).'
            )
        )
