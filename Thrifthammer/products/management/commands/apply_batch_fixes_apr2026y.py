"""
Management command: apply_batch_fixes_apr2026y

Fix 1 — Thousand Sons Ahriman (43-30): add negative keywords 'Omnibus John French'.
  Root cause: eBay returns listings for Warhammer 40,000: Dark Heresy or similar
  Horus Heresy Omnibus books authored by John French that contain "Ahriman" in
  the title.  These pass keyword matching because 'ahriman' appears in book titles.
  Excluding 'Omnibus', 'John', and 'French' at eBay query level removes all such
  book listings before they reach our validator.

Fix 2 — World Eaters Angron (43-04): update Amazon CurrentPrice to $133.00.
  The seeded price ($140.00) is stale.  The Amazon listing currently shows $133.
  This fix only applies if the stored price is still the original seeded value
  ($140.00) — once the Amazon scraper updates it to any other value, this
  fix becomes a no-op automatically.

Idempotent — safe to re-run.
"""

from decimal import Decimal

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Product

# ── Fix 1: Ahriman negative keywords ─────────────────────────────────────────
AHRIMAN_GW_SKU   = '43-30'
AHRIMAN_ADD_KWS  = ['Omnibus', 'John', 'French']

# ── Fix 2: Angron Amazon price ────────────────────────────────────────────────
ANGRON_SLUG        = 'world-eaters-angron'
ANGRON_AMAZON_ASIN = 'B0BTDDDLD5'
ANGRON_STALE_PRICE = Decimal('140.00')   # old seeded value — only update if still here
ANGRON_NEW_PRICE   = Decimal('133.00')   # confirmed current Amazon price (2026-04-26)


class Command(BaseCommand):
    """Apply April 2026 wave-Y fixes: Ahriman neg-kw + Angron Amazon price."""

    help = (
        'Adds Omnibus/John/French to Ahriman neg-kw; '
        'updates Angron Amazon price to $133 if still at stale $140. '
        'Idempotent.'
    )

    def handle(self, *args, **options):
        """Run all fixes."""
        self._fix_ahriman_neg_kw()
        self._fix_angron_amazon_price()
        self.stdout.write(self.style.SUCCESS('\nDone.'))

    # -------------------------------------------------------------------------

    def _fix_ahriman_neg_kw(self):
        """Append Omnibus / John / French to Ahriman's ebay_negative_keywords."""
        try:
            product = Product.objects.get(gw_sku=AHRIMAN_GW_SKU)
        except Product.DoesNotExist:
            self.stdout.write(self.style.WARNING(
                f'  [ahriman] SKU {AHRIMAN_GW_SKU} not found — skipping.'
            ))
            return

        existing = product.ebay_negative_keywords or ''
        existing_lower = existing.lower()

        to_add = [kw for kw in AHRIMAN_ADD_KWS if kw.lower() not in existing_lower]
        if not to_add:
            self.stdout.write(
                f'  [ahriman] neg_kw already contains all of '
                f'{AHRIMAN_ADD_KWS} — no change.'
            )
            return

        new_val = (existing + ' ' + ' '.join(to_add)).strip()
        product.ebay_negative_keywords = new_val
        product.save(update_fields=['ebay_negative_keywords'])
        self.stdout.write(self.style.SUCCESS(
            f'  [ahriman] appended {to_add} to ebay_negative_keywords\n'
            f'    was: "{existing}"\n'
            f'    now: "{new_val}"'
        ))

    # -------------------------------------------------------------------------

    def _fix_angron_amazon_price(self):
        """
        Update Angron's Amazon CurrentPrice to $133.00.

        Only applies when the stored price is still the original seeded value
        ($140.00).  Once the Amazon scraper updates the price to anything else,
        this fix becomes a no-op and will never overwrite a live scraped price.
        """
        try:
            product = Product.objects.get(slug=ANGRON_SLUG)
        except Product.DoesNotExist:
            self.stdout.write(self.style.WARNING(
                f'  [angron] Product {ANGRON_SLUG!r} not found — skipping.'
            ))
            return

        try:
            entry = CurrentPrice.objects.get(
                product=product,
                retailer__slug='amazon',
            )
        except CurrentPrice.DoesNotExist:
            self.stdout.write(self.style.WARNING(
                f'  [angron] No Amazon CurrentPrice row found — skipping.'
            ))
            return

        if entry.price != ANGRON_STALE_PRICE:
            self.stdout.write(
                f'  [angron] Amazon price is ${entry.price} (not the stale '
                f'${ANGRON_STALE_PRICE}) — no change.  Scraper has already updated it.'
            )
            return

        entry.price = ANGRON_NEW_PRICE
        entry.in_stock = True
        entry.not_available = False
        entry.save(update_fields=['price', 'in_stock', 'not_available'])
        self.stdout.write(self.style.SUCCESS(
            f'  [angron] Amazon price ${ANGRON_STALE_PRICE} → ${ANGRON_NEW_PRICE}'
        ))
