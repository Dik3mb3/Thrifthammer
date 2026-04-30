"""
Batch fix apr2026ag

1. Mark Spearhead: Ossiarch Bonereapers Amazon price as not_available so
   the site shows '-' instead of a stale $14.49 price.  The URL is
   preserved so the Amazon price checker can auto-update it when the
   listing becomes purchasable again.

2. Add product-specific eBay negative keywords:
   - T'au Pathfinders:        "8080C", "2000"
   - Lokhust Destroyer Squadron: "Heavy"
   - Plague Drones of Nurgle: "Icon", "Bearer"

Safe to re-run (idempotent).
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from prices.models import CurrentPrice
from products.models import Product, Retailer


# ── Amazon not_available fix ──────────────────────────────────────────────────
_OSSIARCH_SLUG = 'spearhead-ossiarch-bonereapers'

# ── eBay keyword additions ────────────────────────────────────────────────────
_EBAY_ADDITIONS = [
    # (product_slug, [new keywords to add])
    ('tau-pathfinders',                 ['8080C', '2000']),
    ('necron-lokhust-destroyer-squadron', ['Heavy']),
    ('nurgle-plague-drones',            ['Icon', 'Bearer']),
]


class Command(BaseCommand):
    """Mark Ossiarch Bonereapers Spearhead as N/A on Amazon; add eBay avoid keywords."""

    help = (
        'Mark Spearhead: Ossiarch Bonereapers Amazon price not_available; '
        'add eBay negative keywords to T\'au Pathfinders, Lokhust Destroyer '
        'Squadron, and Plague Drones of Nurgle.'
    )

    def handle(self, *args, **options):
        """Apply both fixes."""
        with transaction.atomic():
            self._fix_amazon_price()
            self._add_ebay_keywords()

        self.stdout.write(self.style.SUCCESS('\napr2026ag complete.'))

    # ── Part 1: Amazon not_available ──────────────────────────────────────────

    def _fix_amazon_price(self):
        """Set not_available=True for the Ossiarch Bonereapers Spearhead Amazon listing."""
        try:
            product = Product.objects.get(slug=_OSSIARCH_SLUG)
        except Product.DoesNotExist:
            self.stdout.write(self.style.ERROR(
                f'  Product {_OSSIARCH_SLUG!r} not found — skipping Amazon fix.'
            ))
            return

        try:
            amazon = Retailer.objects.get(name='Amazon')
        except Retailer.DoesNotExist:
            self.stdout.write(self.style.ERROR(
                '  Amazon retailer not found — skipping.'
            ))
            return

        price_record = CurrentPrice.objects.filter(
            product=product, retailer=amazon,
        ).first()

        if not price_record:
            self.stdout.write(
                f'  No Amazon price record for {product.name!r} — skipping.'
            )
            return

        if price_record.not_available:
            self.stdout.write(
                f'  already not_available: {product.name!r} — skipping.'
            )
            return

        price_record.not_available = True
        price_record.save(update_fields=['not_available'])
        self.stdout.write(self.style.WARNING(
            f'  MARKED N/A: {product.name!r} Amazon price '
            f'(URL preserved for auto-update by price checker)'
        ))

    # ── Part 2: eBay negative keywords ───────────────────────────────────────

    def _add_ebay_keywords(self):
        """Append new negative keywords to each product without duplicating."""
        for slug, new_words in _EBAY_ADDITIONS:
            try:
                product = Product.objects.get(slug=slug)
            except Product.DoesNotExist:
                self.stdout.write(self.style.ERROR(
                    f'  Product {slug!r} not found — skipping keyword update.'
                ))
                continue

            existing_raw = (product.ebay_negative_keywords or '').strip()
            existing_lower = {w.lower() for w in existing_raw.split()} if existing_raw else set()

            to_add = [w for w in new_words if w.lower() not in existing_lower]

            if not to_add:
                self.stdout.write(
                    f'  keywords already present on {product.name!r} — skipping.'
                )
                continue

            separator = ' ' if existing_raw else ''
            product.ebay_negative_keywords = existing_raw + separator + ' '.join(to_add)
            product.save(update_fields=['ebay_negative_keywords'])

            self.stdout.write(self.style.SUCCESS(
                f'  KEYWORDS ADDED to {product.name!r}: {to_add}'
            ))
