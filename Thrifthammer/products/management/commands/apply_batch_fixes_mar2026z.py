"""
Management command: apply_batch_fixes_mar2026z

Twenty-fifth wave of March 2026 batch corrections for ThriftHammer.
Run after apply_batch_fixes_mar2026y.

Changes covered:
  Fix 1  -- Space Marine Predator (48-23):
             Set eBay URL to item 167371155634 (confirmed correct GW kit).
             Previous listing matched Kenner "Aliens Predator" toys; neg_kw
             'kenner apone aliens' (added to populate_products.py) prevents
             recurrence.

  Fix 2  -- Skaven Clanrats (90-10):
             Clear Amazon URL and price.  The stored Amazon URL was pointing
             back to the ThriftHammer site itself (a self-referential URL),
             not a valid Amazon product page.  Clearing prevents the scraper
             from hitting our own site on every Amazon run.

  Fix 3  -- Horus Heresy MKVI Tactical Squad (HA-001):
             Update Amazon URL to ASIN B0B4KCWRS6 (correct GW product,
             confirmed by user March 2026).  Previous ASIN B0CP673J8F was
             the MKVI Assault Marines (jump-pack infantry), not the Tactical
             Squad (bolter infantry).

  Fix 4  -- Space Marine Intercessors (48-75):
             Set eBay URL to item 183397331782 (confirmed correct GW kit).
             Previous listing was wrong; neg_kw 'jump pack' (added to
             populate_products.py) prevents Assault Intercessors with Jump
             Packs listings from overwriting this in future runs.

  Fix 5  -- Space Marine Terminator Squad (48-06):
             Set eBay URL to item 256911691932 (standard bolter Terminator
             Squad, confirmed by user).  Previous listing was the Terminator
             Assault Squad; neg_kw 'assault' (added to populate_products.py)
             prevents recurrence.

  Fix 6  -- Space Marine Terminator Squad (48-06):
             Update Amazon URL to ASIN B0CJS2HQ3B (standard Terminator
             Squad, confirmed by user).  Previous ASIN B0G3D2F6BH was the
             Terminator Assault Squad (different loadout/kit).

  Fix 7  -- Space Marine Impulsor (48-94):
             Set eBay URL to item 174069466108 (confirmed correct GW kit,
             provided by user).
             ROOT CAUSE: The Impulsor has a sparse secondary market on eBay
             (transport vehicles trade less frequently than infantry), and the
             description-mirrors-title filter was rejecting most available
             listings because sellers copy the GW product description verbatim.
             The scraper found zero valid results, leaving the URL blank.
             No neg_kw change needed — the correct listing is set directly.

  Fix 8  -- T'au Pathfinders (56-19):
             Set eBay URL to item 183384691833 (correct GW Pathfinder Team
             kit, confirmed by user).  Previous listing was returning wrong
             results; neg_kw 'grav-inhibitor' (added to populate_products.py)
             prevents Grav-inhibitor drone conversion listings from recurring.

  Fix 9  -- Space Marine Ballistus Dreadnought (48-46):
             Set eBay URL to item 177217563002 (confirmed correct GW kit,
             provided by user).
             ROOT CAUSE: Most eBay listings for the Ballistus Dreadnought
             omit "Space Marine" from the title (sellers write just "Ballistus
             Dreadnought 40K").  With 4 search keywords and min_matches=3
             required (ceil(4 × 0.65)), listings matching only "ballistus" +
             "dreadnought" score 2/3 — one short of the threshold — and are
             rejected.  The scraper found zero valid results, leaving the URL
             blank.  No neg_kw needed; correct listing set directly.
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from prices.models import CurrentPrice
from products.models import Product, Retailer


class Command(BaseCommand):
    """Apply wave-Z March 2026 batch corrections to products."""

    help = 'Apply wave-Z March 2026 batch corrections.'

    def handle(self, *args, **options):
        """Apply all fixes atomically."""
        self.stdout.write('\napply_batch_fixes_mar2026z')
        self.stdout.write('=' * 50)

        with transaction.atomic():
            self._fix_1_predator_ebay()
            self._fix_2_clanrats_amazon_clear()
            self._fix_3_mkvi_tactical_amazon()
            self._fix_4_intercessors_ebay()
            self._fix_5_terminator_squad_ebay()
            self._fix_6_terminator_squad_amazon()
            self._fix_7_impulsor_ebay()
            self._fix_8_pathfinders_ebay()
            self._fix_9_ballistus_ebay()

        self.stdout.write(self.style.SUCCESS('\nAll wave-Z fixes applied successfully.'))

    # -------------------------------------------------------------------------
    # Helpers
    # -------------------------------------------------------------------------

    def _get_product(self, gw_sku):
        """Return Product or None, writing a warning if not found."""
        try:
            return Product.objects.get(gw_sku=gw_sku)
        except Product.DoesNotExist:
            self.stdout.write(self.style.WARNING(f'  Product {gw_sku} not found — skipped'))
            return None

    def _get_retailer(self, slug):
        """Return Retailer or None, writing a warning if not found."""
        try:
            return Retailer.objects.get(slug=slug)
        except Retailer.DoesNotExist:
            self.stdout.write(self.style.WARNING(f'  Retailer "{slug}" not found — skipped'))
            return None

    def _set_ebay_url(self, gw_sku, item_id, label):
        """Set the eBay CurrentPrice URL for a product."""
        product = self._get_product(gw_sku)
        if not product:
            return
        retailer = self._get_retailer('ebay')
        if not retailer:
            return

        url = f'https://www.ebay.com/itm/{item_id}'
        cp, created = CurrentPrice.objects.get_or_create(
            product=product,
            retailer=retailer,
            defaults={'url': url, 'in_stock': True},
        )
        if not created:
            old_url = cp.url
            cp.url = url
            cp.in_stock = True
            cp.save(update_fields=['url', 'in_stock'])
            self.stdout.write(self.style.SUCCESS(
                f'  {label}: eBay URL → {url} (was {old_url or "(blank)"})'
            ))
        else:
            self.stdout.write(self.style.SUCCESS(
                f'  {label}: eBay CurrentPrice created → {url}'
            ))

    def _set_amazon_url(self, gw_sku, asin, label):
        """Set the Amazon CurrentPrice URL for a product."""
        product = self._get_product(gw_sku)
        if not product:
            return
        retailer = self._get_retailer('amazon')
        if not retailer:
            return

        url = f'https://www.amazon.com/dp/{asin}'
        cp, created = CurrentPrice.objects.get_or_create(
            product=product,
            retailer=retailer,
            defaults={'url': url, 'in_stock': True},
        )
        if not created:
            old_url = cp.url
            cp.url = url
            cp.save(update_fields=['url'])
            self.stdout.write(self.style.SUCCESS(
                f'  {label}: Amazon URL → {url} (was {old_url or "(blank)"})'
            ))
        else:
            self.stdout.write(self.style.SUCCESS(
                f'  {label}: Amazon CurrentPrice created → {url}'
            ))

    # -------------------------------------------------------------------------
    # Individual fixes
    # -------------------------------------------------------------------------

    def _fix_1_predator_ebay(self):
        """Set correct eBay URL for Space Marine Predator (48-23)."""
        self._set_ebay_url('48-23', '167371155634', 'Fix 1: 48-23 Space Marine Predator')

    def _fix_2_clanrats_amazon_clear(self):
        """Clear the self-referential Amazon URL and price for Skaven Clanrats (90-10)."""
        product = self._get_product('90-10')
        if not product:
            return
        retailer = self._get_retailer('amazon')
        if not retailer:
            return

        try:
            cp = CurrentPrice.objects.get(product=product, retailer=retailer)
        except CurrentPrice.DoesNotExist:
            self.stdout.write('  Fix 2: 90-10 Skaven Clanrats has no Amazon CurrentPrice — skipped')
            return

        old_url = cp.url
        cp.url = ''
        cp.price = None
        cp.in_stock = False
        cp.not_available = True
        cp.save(update_fields=['url', 'price', 'in_stock', 'not_available'])
        self.stdout.write(self.style.SUCCESS(
            f'  Fix 2: 90-10 Skaven Clanrats Amazon URL cleared (was {old_url})'
        ))

    def _fix_3_mkvi_tactical_amazon(self):
        """Update Amazon URL for Horus Heresy MKVI Tactical Squad (HA-001)."""
        self._set_amazon_url('HA-001', 'B0B4KCWRS6', 'Fix 3: HA-001 MKVI Tactical Squad')

    def _fix_4_intercessors_ebay(self):
        """Set correct eBay URL for Space Marine Intercessors (48-75)."""
        self._set_ebay_url('48-75', '183397331782', 'Fix 4: 48-75 Space Marine Intercessors')

    def _fix_5_terminator_squad_ebay(self):
        """Set correct eBay URL for Space Marine Terminator Squad (48-06)."""
        self._set_ebay_url('48-06', '256911691932', 'Fix 5: 48-06 Space Marine Terminator Squad')

    def _fix_6_terminator_squad_amazon(self):
        """Update Amazon URL for Space Marine Terminator Squad (48-06)."""
        self._set_amazon_url('48-06', 'B0CJS2HQ3B', 'Fix 6: 48-06 Space Marine Terminator Squad')

    def _fix_7_impulsor_ebay(self):
        """Set correct eBay URL for Space Marine Impulsor (48-94)."""
        self._set_ebay_url('48-94', '174069466108', 'Fix 7: 48-94 Space Marine Impulsor')

    def _fix_8_pathfinders_ebay(self):
        """Set correct eBay URL for T'au Pathfinders (56-19)."""
        self._set_ebay_url('56-19', '183384691833', "Fix 8: 56-19 T'au Pathfinders")

    def _fix_9_ballistus_ebay(self):
        """Set correct eBay URL for Space Marine Ballistus Dreadnought (48-46)."""
        self._set_ebay_url('48-46', '177217563002', 'Fix 9: 48-46 Space Marine Ballistus Dreadnought')
