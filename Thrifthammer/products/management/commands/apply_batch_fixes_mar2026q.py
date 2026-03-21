"""
Management command: apply_batch_fixes_mar2026q

Seventeenth wave of March 2026 batch corrections for ThriftHammer.
Run after apply_batch_fixes_mar2026p.

Changes covered:
  Fix 1  -- Space Marine Ancient (48-34):
             - Correct eBay URL (old: 227225134085, new: 187763771459)
             - neg_kw "barachus raven"
               "Brother Barachus" -> "barachus" only (too specific a character;
               "Brother" alone is too broad).
               "Blood Raven" -> "raven" only ("blood" alone false-positives on
               Blood Angels-related searches).

  Fix 2  -- Space Marine Apothecary (48-33):
             eBay prices are already auto-updated daily by the existing
             update-ebay-prices.yml GitHub Action (03:00 UTC).  No URL or
             workflow changes required.  Documented here for audit trail.

  Fix 3  -- Space Marine Bladeguard Veterans (48-38):
             - Correct eBay URL (old: 404543935001, new: 356236367790)
             - neg_kw "indomitus" to block Indomitus starter set listings that
               include Bladeguard Veterans as a component.

  Fix 4  -- Space Marine Chaplain (48-32):
             - Correct eBay URL (old: 167058189654, new: 184024162896)
             - neg_kw "1x honoured"
               "1x" blocks single-model unit listings.
               "Honoured of the Chapter" -> "honoured" only ("of"/"the"/"chapter"
               are substring false-positive risks).

  Fix 5  -- Space Marine Combat Patrol (71-02):
             - Correct eBay URL (old: 163961378983, new: 405939586465)
             - neg_kw "suppressors" to block Suppressors unit listings that
               pass the Combat Patrol keyword threshold.

  Fix 6  -- Space Marine Company Heroes (48-37):
             - Set eBay URL -> item 157689636714 (was blank)
             - Set ebay_search_name "company heroes warhammer 40k" to avoid
               video-game "Company of Heroes" search contamination.

  Fix 7  -- Space Marine Firestrike Servo-Turrets (48-28):
             - Set eBay URL -> item 277548406500 (was blank)
             - Set ebay_search_name "Space Marine Firestrike Servo Turret"
               (removes hyphen in "Servo-Turrets" which breaks eBay search
               tokenisation).

  Fix 8  -- Space Marine Hammerfall Bunker (48-27):
             - Correct eBay URL (old: 306767323651, new: 174481298647)
             - Set ebay_search_name "hammerfall bunker" (shorter search
               avoids faction-name padding in favour of the unique model name).

  Fix 9  -- Space Marine Impulsor (48-94):
             - Set eBay URL -> item 174069466108 (was blank)

Usage:
    python manage.py apply_batch_fixes_mar2026q
    python manage.py apply_batch_fixes_mar2026q --dry-run
"""

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Product, Retailer


class Command(BaseCommand):
    """Seventeenth wave of March 2026 ThriftHammer DB corrections."""

    help = (
        'Apply Wave Q batch corrections (March 2026) -- '
        'Space Marine eBay URLs, neg_kw, search name overrides.'
    )

    def add_arguments(self, parser):
        """Add --dry-run flag to preview changes without saving."""
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Print planned changes without writing to the database.',
        )

    def handle(self, *args, **options):
        """Execute all Wave Q corrections in order."""
        dry = options['dry_run']
        if dry:
            self.stdout.write(self.style.WARNING('DRY RUN -- no changes will be saved.\n'))

        self._fix_1_sm_ancient(dry)
        self._fix_2_sm_apothecary_note(dry)
        self._fix_3_sm_bladeguard(dry)
        self._fix_4_sm_chaplain(dry)
        self._fix_5_sm_combat_patrol(dry)
        self._fix_6_sm_company_heroes(dry)
        self._fix_7_sm_firestrike(dry)
        self._fix_8_sm_hammerfall(dry)
        self._fix_9_sm_impulsor(dry)

        if dry:
            self.stdout.write(self.style.WARNING('\nDRY RUN complete -- nothing was saved.'))
        else:
            self.stdout.write(self.style.SUCCESS('\nWave Q complete.'))

    # -----------------------------------------------------------------------
    # Helpers
    # -----------------------------------------------------------------------

    def _get_product(self, gw_sku):
        """Fetch a product by gw_sku, writing an error and returning None if missing."""
        try:
            return Product.objects.get(gw_sku=gw_sku)
        except Product.DoesNotExist:
            self.stderr.write(self.style.ERROR(f'  ERROR: Product {gw_sku} not found.'))
            return None

    def _set_url(self, product, retailer_name, new_url, dry):
        """Update a CurrentPrice URL; create row if missing; skip if already correct."""
        try:
            retailer = Retailer.objects.get(name=retailer_name)
        except Retailer.DoesNotExist:
            self.stderr.write(
                self.style.ERROR(f'  ERROR: Retailer "{retailer_name}" not found.')
            )
            return

        cp, created = CurrentPrice.objects.get_or_create(
            product=product,
            retailer=retailer,
            defaults={'price': None, 'in_stock': False, 'url': new_url},
        )
        if created:
            self.stdout.write(f'  [ok] Created {retailer_name} entry: {new_url[:70]}')
            return

        if cp.url == new_url:
            self.stdout.write(f'  [skip] {retailer_name}: URL already correct')
            return

        old_url = cp.url or '(blank)'
        if dry:
            self.stdout.write(
                f'  [dry] {retailer_name}: {old_url[:55]}\n'
                f'             -> {new_url[:55]}'
            )
            return

        cp.url = new_url
        cp.save(update_fields=['url'])
        self.stdout.write(f'  [ok] {retailer_name}: {old_url[:50]} -> {new_url[:50]}')

    def _add_neg_kw(self, product, new_kw, dry):
        """
        Append new_kw word(s) to product.ebay_negative_keywords if not already present.

        new_kw is space-separated; each word is checked independently by the eBay
        client (title and description substring checks + eBay query -word suffix).
        Words already present are skipped.
        """
        current = (product.ebay_negative_keywords or '').strip()
        existing = {w.lower() for w in current.split()} if current else set()
        to_add = [w for w in new_kw.split() if w.lower() not in existing]

        if not to_add:
            self.stdout.write(f'  [skip] neg_kw already contains: "{new_kw}"')
            return

        new_val = (current + ' ' + ' '.join(to_add)).strip() if current else ' '.join(to_add)
        if dry:
            self.stdout.write(f'  [dry] neg_kw: "{current or "(empty)"}" -> "{new_val}"')
            return
        product.ebay_negative_keywords = new_val
        product.save(update_fields=['ebay_negative_keywords'])
        self.stdout.write(f'  [ok] neg_kw: "{current or "(empty)"}" -> "{new_val}"')

    def _set_search_name(self, product, new_search, dry):
        """Set product.ebay_search_name; skip if already correct."""
        current = (product.ebay_search_name or '').strip()
        if current == new_search:
            self.stdout.write(f'  [skip] ebay_search_name already "{new_search}"')
            return
        if dry:
            self.stdout.write(
                f'  [dry] ebay_search_name: "{current or "(empty)"}" -> "{new_search}"'
            )
            return
        product.ebay_search_name = new_search
        product.save(update_fields=['ebay_search_name'])
        self.stdout.write(f'  [ok] ebay_search_name -> "{new_search}"')

    # -----------------------------------------------------------------------
    # Fixes
    # -----------------------------------------------------------------------

    def _fix_1_sm_ancient(self, dry):
        """Fix 1: Space Marine Ancient -- eBay URL + neg_kw (48-34)."""
        self.stdout.write('\nFix 1: Space Marine Ancient -- eBay URL + neg_kw')
        p = self._get_product('48-34')
        if p is None:
            return
        self._set_url(p, 'eBay', 'https://www.ebay.com/itm/187763771459', dry)
        # barachus: blocks "Brother Barachus" named-character listings
        # raven:    blocks "Blood Ravens" (different SM chapter) listings
        #           Using "raven" not "blood" -- "blood" false-positives on
        #           Blood Angels faction listings.
        self._add_neg_kw(p, 'barachus raven', dry)

    def _fix_2_sm_apothecary_note(self, dry):
        """
        Fix 2: Space Marine Apothecary -- eBay prices already auto-updated.

        The existing update-ebay-prices.yml GitHub Action (03:00 UTC daily)
        already runs update_ebay_prices and refreshes both the URL and price for
        every active product, including 48-33.  No additional workflow is needed.
        The stale price visible on the website will be corrected at the next run.
        """
        self.stdout.write('\nFix 2: Space Marine Apothecary -- [INFO] eBay price auto-updated daily')
        self.stdout.write(
            '  eBay prices are refreshed every day at 03:00 UTC by the existing\n'
            '  update-ebay-prices.yml GitHub Action.  No DB or workflow change needed.'
        )

    def _fix_3_sm_bladeguard(self, dry):
        """Fix 3: Space Marine Bladeguard Veterans -- eBay URL + neg_kw (48-38)."""
        self.stdout.write('\nFix 3: Space Marine Bladeguard Veterans -- eBay URL + neg_kw')
        p = self._get_product('48-38')
        if p is None:
            return
        self._set_url(p, 'eBay', 'https://www.ebay.com/itm/356236367790', dry)
        # indomitus: blocks Indomitus starter set listings where Bladeguard
        # Veterans appear as a component alongside other models.
        self._add_neg_kw(p, 'indomitus', dry)

    def _fix_4_sm_chaplain(self, dry):
        """Fix 4: Space Marine Chaplain -- eBay URL + neg_kw (48-32)."""
        self.stdout.write('\nFix 4: Space Marine Chaplain -- eBay URL + neg_kw')
        p = self._get_product('48-32')
        if p is None:
            return
        self._set_url(p, 'eBay', 'https://www.ebay.com/itm/184024162896', dry)
        # 1x:      blocks single-model "1x Chaplain" listings (individual resale)
        # honoured: blocks "Honoured of the Chapter" product variant listings
        #            Storing only "honoured"; "of"/"the"/"chapter" are too broad.
        self._add_neg_kw(p, '1x honoured', dry)

    def _fix_5_sm_combat_patrol(self, dry):
        """Fix 5: Space Marine Combat Patrol -- eBay URL + neg_kw (71-02)."""
        self.stdout.write('\nFix 5: Space Marine Combat Patrol -- eBay URL + neg_kw')
        p = self._get_product('71-02')
        if p is None:
            return
        self._set_url(p, 'eBay', 'https://www.ebay.com/itm/405939586465', dry)
        # suppressors: blocks Suppressors-only unit listings that share enough
        # keywords with the Combat Patrol search to pass the match threshold.
        self._add_neg_kw(p, 'suppressors', dry)

    def _fix_6_sm_company_heroes(self, dry):
        """Fix 6: Space Marine Company Heroes -- set eBay URL + search name (48-37)."""
        self.stdout.write('\nFix 6: Space Marine Company Heroes -- eBay URL + search name')
        p = self._get_product('48-37')
        if p is None:
            return
        self._set_url(p, 'eBay', 'https://www.ebay.com/itm/157689636714', dry)
        # The default search "Space Marine Company Heroes" returns video-game
        # "Company of Heroes" listings.  Adding "warhammer" disambiguates.
        self._set_search_name(p, 'company heroes warhammer 40k', dry)

    def _fix_7_sm_firestrike(self, dry):
        """Fix 7: Space Marine Firestrike Servo-Turrets -- set eBay URL + search name (48-28)."""
        self.stdout.write('\nFix 7: Space Marine Firestrike Servo-Turrets -- eBay URL + search name')
        p = self._get_product('48-28')
        if p is None:
            return
        self._set_url(p, 'eBay', 'https://www.ebay.com/itm/277548406500', dry)
        # The hyphen in "Servo-Turrets" breaks eBay search tokenisation.
        # Removing it produces a cleaner keyword query.
        self._set_search_name(p, 'Space Marine Firestrike Servo Turret', dry)

    def _fix_8_sm_hammerfall(self, dry):
        """Fix 8: Space Marine Hammerfall Bunker -- eBay URL + search name (48-27)."""
        self.stdout.write('\nFix 8: Space Marine Hammerfall Bunker -- eBay URL + search name')
        p = self._get_product('48-27')
        if p is None:
            return
        self._set_url(p, 'eBay', 'https://www.ebay.com/itm/174481298647', dry)
        # "hammerfall bunker" is the exact phrase sellers use in eBay titles.
        # Dropping "Space Marine" avoids the generic faction prefix reducing
        # match specificity, and matches the seller search pattern in the
        # provided correct listing URL.
        self._set_search_name(p, 'hammerfall bunker', dry)

    def _fix_9_sm_impulsor(self, dry):
        """Fix 9: Space Marine Impulsor -- set eBay URL (48-94)."""
        self.stdout.write('\nFix 9: Space Marine Impulsor -- set eBay URL')
        p = self._get_product('48-94')
        if p is None:
            return
        self._set_url(p, 'eBay', 'https://www.ebay.com/itm/174069466108', dry)
