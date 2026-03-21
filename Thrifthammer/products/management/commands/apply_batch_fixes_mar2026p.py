"""
Management command: apply_batch_fixes_mar2026p

Sixteenth wave of March 2026 batch corrections for ThriftHammer.
Run after apply_batch_fixes_mar2026o.

Changes covered:
  Fix 1  -- Nighthaunt Combat Patrol: SKU not present in DB — no-op, logged.

  Fix 2  -- Nighthaunt Knight of Shrouds (91-15):
             Amazon does not carry this product.
             Clear Amazon URL (set to '') and price (set to None).

  Fix 3  -- Ork Combat Patrol (71-18):
             - Correct eBay URL (old: 165068018505, new: 167251862951)
             - Add neg_kw "(10)" to block listings for 10-model packs rather
               than the full Combat Patrol box.

  Fix 4  -- Ork Deff Dread (50-16):
             - Add Amazon URL -> https://www.amazon.com/dp/B003B1V9D2
             - Correct eBay URL (old: 175109538085, new: 327055474234)

  Fix 5  -- Ork Flash Gitz (50-20):
             eBay URL already correct (173478243700).
             Add neg_kw "meganobz mek nookah" to block:
               meganobz - Meganobz unit listings
               mek      - Mek Gunz unit listings
               nookah   - Nookah 3D-print resin alternative models

  Fix 6  -- Ork Lootas (50-14):
             - Correct eBay URL (old: 175109538093, new: 327054187904)
             - Add neg_kw "DaBoom! Artel" to block:
               DaBoom! - DaBoom! brand alternative models
               Artel   - Artel W resin alternative models

  Fix 7  -- Ork Trukk (50-11):
             - Correct eBay URL (old: 406740497352, new: 173507270296)
             - Add neg_kw "driver" to block "No Driver" incomplete kit listings.
               (Storing only "driver"; "no" as a substring is too broad and
               would false-positive on "not", "know", etc. in other titles.)

  Fix 8  -- Skaven Clanrats (90-10):
             - Clear Amazon URL and price (Amazon does not carry this product)
             - Correct Noble Knight URL to direct product page

Usage:
    python manage.py apply_batch_fixes_mar2026p
    python manage.py apply_batch_fixes_mar2026p --dry-run
"""

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Product, Retailer


class Command(BaseCommand):
    """Sixteenth wave of March 2026 ThriftHammer DB corrections."""

    help = (
        'Apply Wave P batch corrections (March 2026) -- '
        'Nighthaunt, Ork eBay URLs/neg_kw, Clanrats Amazon clear.'
    )

    def add_arguments(self, parser):
        """Add --dry-run flag to preview changes without saving."""
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Print planned changes without writing to the database.',
        )

    def handle(self, *args, **options):
        """Execute all Wave P corrections in order."""
        dry = options['dry_run']
        if dry:
            self.stdout.write(self.style.WARNING('DRY RUN -- no changes will be saved.\n'))

        self._fix_1_nighthaunt_cp(dry)
        self._fix_2_knight_of_shrouds_amazon(dry)
        self._fix_3_ork_combat_patrol(dry)
        self._fix_4_ork_deff_dread(dry)
        self._fix_5_ork_flash_gitz(dry)
        self._fix_6_ork_lootas(dry)
        self._fix_7_ork_trukk(dry)
        self._fix_8_skaven_clanrats(dry)

        if dry:
            self.stdout.write(self.style.WARNING('\nDRY RUN complete -- nothing was saved.'))
        else:
            self.stdout.write(self.style.SUCCESS('\nWave P complete.'))

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
        """
        Update a CurrentPrice URL for a given retailer.

        Creates the row if it does not exist; skips if URL already matches.
        """
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
                f'  [dry] {retailer_name}: {old_url[:60]}\n'
                f'             -> {new_url[:60]}'
            )
            return

        cp.url = new_url
        cp.save(update_fields=['url'])
        self.stdout.write(f'  [ok] {retailer_name}: {old_url[:55]} -> {new_url[:55]}')

    def _clear_retailer(self, product, retailer_name, dry):
        """
        Clear URL and price for a given retailer (product not available there).

        Sets url='' and price=None to avoid NOT NULL violations in PostgreSQL.
        """
        try:
            retailer = Retailer.objects.get(name=retailer_name)
        except Retailer.DoesNotExist:
            self.stderr.write(
                self.style.ERROR(f'  ERROR: Retailer "{retailer_name}" not found.')
            )
            return

        try:
            cp = CurrentPrice.objects.get(product=product, retailer=retailer)
        except CurrentPrice.DoesNotExist:
            self.stdout.write(f'  [skip] No {retailer_name} row to clear')
            return

        if not cp.url and cp.price is None:
            self.stdout.write(f'  [skip] {retailer_name}: already blank')
            return

        if dry:
            self.stdout.write(
                f'  [dry] {retailer_name}: clear URL ({(cp.url or "(blank)")[:50]}) '
                f'and price ({cp.price})'
            )
            return

        cp.url = ''
        cp.price = None
        cp.in_stock = False
        cp.save(update_fields=['url', 'price', 'in_stock'])
        self.stdout.write(f'  [ok] {retailer_name}: URL and price cleared')

    def _add_neg_kw(self, product, new_kw, dry):
        """
        Append new_kw word(s) to product.ebay_negative_keywords if not already present.

        new_kw is a space-separated list; each word is checked independently by
        the eBay client.  Words already present are skipped.
        """
        current = (product.ebay_negative_keywords or '').strip()
        existing = set(w.lower() for w in current.split()) if current else set()
        to_add = [w for w in new_kw.split() if w.lower() not in existing]

        if not to_add:
            self.stdout.write(f'  [skip] neg_kw already contains all of: "{new_kw}"')
            return

        new_val = (current + ' ' + ' '.join(to_add)).strip() if current else ' '.join(to_add)
        if dry:
            self.stdout.write(f'  [dry] neg_kw: "{current}" -> "{new_val}"')
            return
        product.ebay_negative_keywords = new_val
        product.save(update_fields=['ebay_negative_keywords'])
        self.stdout.write(f'  [ok] neg_kw: "{current or "(empty)"}" -> "{new_val}"')

    # -----------------------------------------------------------------------
    # Fixes
    # -----------------------------------------------------------------------

    def _fix_1_nighthaunt_cp(self, dry):
        """Fix 1: Nighthaunt Combat Patrol -- not present in DB, nothing to do."""
        self.stdout.write('\nFix 1: Nighthaunt Combat Patrol -- SKU lookup')
        # This product has no DB entry; deactivation not possible.
        self.stdout.write(
            '  [skip] "Nighthaunt Combat Patrol" not found in DB -- no action taken'
        )

    def _fix_2_knight_of_shrouds_amazon(self, dry):
        """Fix 2: Nighthaunt Knight of Shrouds -- clear Amazon URL + price (91-15)."""
        self.stdout.write('\nFix 2: Nighthaunt Knight of Shrouds -- clear Amazon')
        p = self._get_product('91-15')
        if p:
            self._clear_retailer(p, 'Amazon', dry)

    def _fix_3_ork_combat_patrol(self, dry):
        """Fix 3: Ork Combat Patrol -- correct eBay URL + add neg_kw "(10)" (71-18)."""
        self.stdout.write('\nFix 3: Ork Combat Patrol -- eBay URL + neg_kw "(10)"')
        p = self._get_product('71-18')
        if p is None:
            return
        self._set_url(p, 'eBay', 'https://www.ebay.com/itm/167251862951', dry)
        # Block listings for "10 Orks" packs — these are individual unit bundles
        # (e.g. "Ork Boyz x10") that share keywords with the Combat Patrol search.
        self._add_neg_kw(p, '(10)', dry)

    def _fix_4_ork_deff_dread(self, dry):
        """Fix 4: Ork Deff Dread -- add Amazon URL + correct eBay URL (50-16)."""
        self.stdout.write('\nFix 4: Ork Deff Dread -- Amazon URL + eBay URL')
        p = self._get_product('50-16')
        if p is None:
            return
        self._set_url(p, 'Amazon', 'https://www.amazon.com/dp/B003B1V9D2', dry)
        self._set_url(p, 'eBay', 'https://www.ebay.com/itm/327055474234', dry)

    def _fix_5_ork_flash_gitz(self, dry):
        """Fix 5: Ork Flash Gitz -- add neg_kw (eBay URL already correct) (50-20)."""
        self.stdout.write('\nFix 5: Ork Flash Gitz -- neg_kw (eBay URL already correct)')
        p = self._get_product('50-20')
        if p is None:
            return
        # meganobz: block Meganobz unit listings (different Ork heavy unit)
        # mek:      block Mek Gunz unit listings
        # nookah:   block Nookah brand 3D-print resin alternative models
        self._add_neg_kw(p, 'meganobz mek nookah', dry)

    def _fix_6_ork_lootas(self, dry):
        """Fix 6: Ork Lootas -- correct eBay URL + add neg_kw (50-14)."""
        self.stdout.write('\nFix 6: Ork Lootas -- eBay URL + neg_kw')
        p = self._get_product('50-14')
        if p is None:
            return
        self._set_url(p, 'eBay', 'https://www.ebay.com/itm/327054187904', dry)
        # DaBoom!: block DaBoom! brand alternative model listings
        # Artel:   block Artel W brand resin alternative model listings
        self._add_neg_kw(p, 'DaBoom! Artel', dry)

    def _fix_7_ork_trukk(self, dry):
        """Fix 7: Ork Trukk -- correct eBay URL + add neg_kw "driver" (50-11)."""
        self.stdout.write('\nFix 7: Ork Trukk -- eBay URL + neg_kw "driver"')
        p = self._get_product('50-11')
        if p is None:
            return
        self._set_url(p, 'eBay', 'https://www.ebay.com/itm/173507270296', dry)
        # "driver" blocks "No Driver" incomplete kit listings (missing the Trukk
        # driver model).  Storing only "driver" -- "no" as a substring is too
        # broad and causes false positives on "not", "unopened", etc.
        self._add_neg_kw(p, 'driver', dry)

    def _fix_8_skaven_clanrats(self, dry):
        """Fix 8: Skaven Clanrats -- clear Amazon, correct Noble Knight URL (90-10)."""
        self.stdout.write('\nFix 8: Skaven Clanrats -- clear Amazon + NK URL')
        p = self._get_product('90-10')
        if p is None:
            return
        self._clear_retailer(p, 'Amazon', dry)
        self._set_url(
            p, 'Noble Knight Games',
            'https://www.nobleknight.com/P/2148050436/Clanrats',
            dry,
        )
