"""
Management command: apply_batch_fixes_may2026m

Changes:
  TE-020  T'au Empire Devilfish
          ebay_negative_keywords: add Smart, Turrets

  47-12   Astra Militarum Sentinel
          ebay_negative_keywords: add Imperial, Guard

Idempotent — safe to re-run.
"""

from django.core.management.base import BaseCommand

from products.models import Product


class Command(BaseCommand):
    """Apply batch fixes may2026m — Devilfish and Sentinel negative keyword updates."""

    help = "Devilfish and Sentinel eBay negative keyword updates."

    def handle(self, *args, **options):
        """Run all fixes."""
        updated = Product.objects.filter(gw_sku='TE-020').update(
            ebay_negative_keywords=(
                'legions imperialis Resin 04-113 100th 1926 TShirt Plushie Plush Smart Turrets'
            ),
        )
        self.stdout.write(f"Devilfish: {updated} product(s) updated.")

        updated = Product.objects.filter(gw_sku='47-12').update(
            ebay_negative_keywords='h / Imperial Guard',
        )
        self.stdout.write(f"Sentinel: {updated} product(s) updated.")

        self.stdout.write(self.style.SUCCESS('apply_batch_fixes_may2026m complete.'))
