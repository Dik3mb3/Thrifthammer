"""
Management command: apply_batch_fixes_mar2026ac

Twenty-eighth wave of March 2026 batch corrections for ThriftHammer.
Run after apply_batch_fixes_mar2026ab.

Changes covered:
  Fix 1  -- Adeptus Mechanicus Skitarii Rangers (59-10):
             Correct Noble Knight URL — previous URL pointed to an Aeldari
             Rangers listing (wrong faction). Correct NK product ID is
             2147924590 (Skitarii Rangers, Adeptus Mechanicus).

  Fix 2  -- Bust stale product detail caches for wave-AB gw_url updates:
             Wave AB (Fix 15) set Product.gw_url for 13 SKUs but did not
             invalidate the product detail page cache.  The "View on GW"
             button was therefore invisible until the 30-min cache TTL
             expired naturally.  This fix explicitly clears the cache for
             every affected product slug so the button appears immediately.
             SKUs: 54-21, HA-021, NM-010, NM-011, NM-012, 56-14, 48-29,
                   96-12, 48-61, 43-56, 51-42, 59-20, 44-09.
"""

from django.core.cache import cache
from django.core.management.base import BaseCommand
from django.db import transaction

from prices.models import CurrentPrice
from products.models import Product, Retailer

# SKUs whose gw_url was set in wave-AB Fix 15 — caches need busting.
_WAVE_AB_GW_URL_SKUS = [
    '54-21', 'HA-021', 'NM-010', 'NM-011', 'NM-012',
    '56-14', '48-29', '96-12', '48-61', '43-56',
    '51-42', '59-20', '44-09',
]


class Command(BaseCommand):
    """Apply wave-AC March 2026 batch corrections to products."""

    help = 'Apply wave-AC March 2026 batch corrections.'

    def handle(self, *args, **options):
        """Apply all fixes atomically."""
        self.stdout.write('\napply_batch_fixes_mar2026ac')
        self.stdout.write('=' * 50)

        with transaction.atomic():
            self._fix_1_skitarii_rangers_nk()

        # Cache busting runs outside the transaction (cache is not DB-transactional).
        self._fix_2_bust_gw_url_caches()

        self.stdout.write(self.style.SUCCESS('\nAll wave-AC fixes applied successfully.'))

    # -------------------------------------------------------------------------
    # Individual fixes
    # -------------------------------------------------------------------------

    def _fix_1_skitarii_rangers_nk(self):
        """Correct Noble Knight URL for Adeptus Mechanicus Skitarii Rangers (59-10)."""
        try:
            product = Product.objects.get(gw_sku='59-10')
        except Product.DoesNotExist:
            self.stdout.write(self.style.WARNING('  Fix 1: 59-10 Skitarii Rangers not found — skipped'))
            return

        try:
            retailer = Retailer.objects.get(slug='noble-knight-games')
        except Retailer.DoesNotExist:
            self.stdout.write(self.style.WARNING('  Fix 1: noble-knight-games retailer not found — skipped'))
            return

        new_url = 'https://www.nobleknight.com/P/2147924590/Skitarii'
        cp, created = CurrentPrice.objects.get_or_create(
            product=product,
            retailer=retailer,
            defaults={'url': new_url},
        )
        if not created:
            old_url = cp.url
            if old_url == new_url:
                self.stdout.write('  Fix 1: 59-10 NK URL already correct — skipped')
                return
            cp.url = new_url
            cp.save(update_fields=['url'])
            self.stdout.write(self.style.SUCCESS(
                f'  Fix 1: 59-10 Skitarii Rangers NK URL → {new_url} (was {old_url or "(blank)"})'
            ))
        else:
            self.stdout.write(self.style.SUCCESS(
                f'  Fix 1: 59-10 Skitarii Rangers NK CurrentPrice created → {new_url}'
            ))

    def _fix_2_bust_gw_url_caches(self):
        """Clear stale product detail caches for products whose gw_url was set in wave AB."""
        busted = 0
        for gw_sku in _WAVE_AB_GW_URL_SKUS:
            try:
                product = Product.objects.get(gw_sku=gw_sku)
            except Product.DoesNotExist:
                continue
            if product.slug:
                cache.delete(f'product_detail|{product.slug}')
                busted += 1
        self.stdout.write(self.style.SUCCESS(
            f'  Fix 2: Busted {busted} product detail caches for wave-AB gw_url updates.'
        ))
