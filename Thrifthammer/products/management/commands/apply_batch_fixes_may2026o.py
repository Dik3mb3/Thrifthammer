"""
Management command: apply_batch_fixes_may2026o

Changes:
  aeldari-howling-banshees  Amazon URL correction
    Old ASIN: B08HCL7SFY  (wrong product)
    New ASIN: B09TLBQLG7  (Warhammer 40k Howling Banshees, confirmed by user 2026-06-10)
"""

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Product, Retailer


class Command(BaseCommand):
    """Correct Amazon URL for Howling Banshees (wrong ASIN was seeded)."""

    help = 'Fix Amazon URL for aeldari-howling-banshees: B08HCL7SFY -> B09TLBQLG7.'

    def handle(self, *args, **options):
        """Run the command."""
        amazon = Retailer.objects.filter(name='Amazon').first()
        if not amazon:
            self.stderr.write(self.style.ERROR('Amazon retailer not found.'))
            return

        try:
            product = Product.objects.get(slug='aeldari-howling-banshees')
        except Product.DoesNotExist:
            self.stderr.write(self.style.ERROR('aeldari-howling-banshees not found.'))
            return

        updated = CurrentPrice.objects.filter(
            product=product,
            retailer=amazon,
        ).update(
            url='https://www.amazon.com/dp/B09TLBQLG7?tag=thrifthammer7-20',
            manual_url_override=False,
        )

        if updated:
            self.stdout.write(self.style.SUCCESS(
                f'apply_batch_fixes_may2026o complete. '
                f'Updated Amazon URL for {product.name} ({product.gw_sku}).'
            ))
        else:
            self.stdout.write(self.style.WARNING(
                'No Amazon CurrentPrice record found for aeldari-howling-banshees — skipping.'
            ))
