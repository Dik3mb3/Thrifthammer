"""
Management command: apply_batch_fixes_mar2026v

Twenty-first wave of March 2026 batch corrections for ThriftHammer.
Run after apply_batch_fixes_mar2026t.

Changes covered:
  Fix 1  -- Space Marine Company Heroes (48-37):
             - Correct eBay URL (old: 404556071773 at $23.50, new: 186099352635)
             - neg_kw "champion bolter fist" (SKU-specific only)
               "Champion", "Bolter", and "Fist" are upgrade/conversion listing
               terms sellers use to describe custom Company Heroes with specific
               weapon loadouts.  These are not the standard sealed retail kit.

  Fix 2  -- Space Marine Combat Patrol (71-02):
             - Correct eBay URL (old: 317915483897 at $54.99, new: 405939586465)
             - neg_kw "magazine terminators" (SKU-specific only)
               "Magazine": blocks listings that include a White Dwarf or other
               GW magazine bundled with the set — a different product.
               "Terminators": blocks Combat Patrol listings specifically called
               out as containing Terminators, which signals a different edition
               or variant box incompatible with the current retail SKU.

  Fix 3  -- Space Marine Land Raider Crusader (48-22):
             - Correct eBay URL (old: 177786026337 at $54.99, new: 175379698427)
               Note: the global "-decor" filter (added to ebay_api_client.py in
               this wave) handles decor-art listings globally, so no per-SKU
               neg_kw is required here.

  Fix 4  -- Ork Lootas (50-14):
             - Correct eBay URL (old: 225321644414 at $23.99, new: 183199561434)
             - neg_kw "rokker flash elektro wargame" (SKU-specific, appended)
               Existing neg_kw already has "DaBoom! Artel"; these four words
               cover the remaining known bad-match patterns:
               "rokker", "flash", "elektro" — musician/band-themed conversion kit
               titles that share "Lootas" but are not the standard retail box.
               "wargame" — generic hobby/gaming bundles that include Lootas as
               part of a multi-product lot (not a sealed retail single-kit sale).
             - Set ebay_search_name "ork lootas" to improve Best Match ranking
               (the faction-prefix "Ork" without full name improves relevance).

  Fix 5  -- Space Marine Incursors (48-96):
             - Correct Amazon price ($24.97 → $55.25, stale from old ASIN
               B07J3PG964 which was replaced with B08GC37WBR in Wave R).
               _set_url() was updated to detect ASIN changes and clear the stale
               price.  This fix directly updates the CurrentPrice row price and
               re-flags in_stock=True so the correct price is shown immediately.

Usage:
    python manage.py apply_batch_fixes_mar2026v
    python manage.py apply_batch_fixes_mar2026v --dry-run
"""

import re
from decimal import Decimal

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Product, Retailer


class Command(BaseCommand):
    """Twenty-first wave of March 2026 ThriftHammer DB corrections."""

    help = (
        'Apply Wave V batch corrections (March 2026) -- '
        'SM Company Heroes/Combat Patrol/Land Raider Crusader eBay fixes, '
        'Ork Lootas eBay fix + neg_kw, Incursors Amazon price correction.'
    )

    def add_arguments(self, parser):
        """Add --dry-run flag to preview changes without saving."""
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Print planned changes without writing to the database.',
        )

    def handle(self, *args, **options):
        """Execute all Wave V corrections in order."""
        dry = options['dry_run']
        if dry:
            self.stdout.write(self.style.WARNING('DRY RUN -- no changes will be saved.\n'))

        self._fix_1_company_heroes(dry)
        self._fix_2_combat_patrol(dry)
        self._fix_3_land_raider_crusader(dry)
        self._fix_4_ork_lootas(dry)
        self._fix_5_incursors_amazon_price(dry)

        if dry:
            self.stdout.write(self.style.WARNING('\nDRY RUN complete -- nothing was saved.'))
        else:
            self.stdout.write(self.style.SUCCESS('\nWave V complete.'))

    # -----------------------------------------------------------------------
    # Helpers
    # -----------------------------------------------------------------------

    def _get_product(self, gw_sku):
        """Fetch a product by gw_sku; write an error and return None if missing."""
        try:
            return Product.objects.get(gw_sku=gw_sku)
        except Product.DoesNotExist:
            self.stderr.write(self.style.ERROR(f'  ERROR: Product {gw_sku} not found.'))
            return None

    @staticmethod
    def _extract_asin(url):
        """Extract an Amazon ASIN from a URL, or None if not an Amazon URL."""
        if not url:
            return None
        m = re.search(r'/dp/([A-Z0-9]{10})', url)
        return m.group(1) if m else None

    def _set_url(self, product, retailer_name, new_url, dry):
        """Update a CurrentPrice URL; create row if missing; skip if already correct.

        Amazon-specific behaviour: if the URL change implies an ASIN change (i.e. the
        old URL contains a different /dp/<ASIN> than the new URL), the old price is
        cleared to None and in_stock reset to False.  This prevents stale prices from
        a superseded ASIN being displayed against the new listing.
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

        # Detect Amazon ASIN change — stale price must be cleared.
        asin_changed = False
        if retailer_name == 'Amazon':
            old_asin = self._extract_asin(cp.url)
            new_asin = self._extract_asin(new_url)
            if old_asin and new_asin and old_asin != new_asin and cp.price is not None:
                asin_changed = True

        if dry:
            msg = (
                f'  [dry] {retailer_name}: {old_url[:55]}\n'
                f'             -> {new_url[:55]}'
            )
            if asin_changed:
                msg += f'\n  [dry] ASIN change detected ({old_asin} -> {new_asin}): price will be cleared'
            self.stdout.write(msg)
            return

        update_fields = {'url': new_url}
        if asin_changed:
            update_fields['price'] = None
            update_fields['in_stock'] = False
            update_fields['not_available'] = False

        CurrentPrice.objects.filter(pk=cp.pk).update(**update_fields)

        suffix = f' [ASIN change: price cleared]' if asin_changed else ''
        self.stdout.write(f'  [ok] {retailer_name}: {old_url[:50]} -> {new_url[:50]}{suffix}')

    def _add_neg_kw(self, product, new_kw, dry):
        """
        Append new_kw word(s) to product.ebay_negative_keywords if not already present.

        new_kw is space-separated; each word is checked independently by the eBay
        client.  Words already present are skipped.
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

    def _fix_1_company_heroes(self, dry):
        """Fix 1: Space Marine Company Heroes -- eBay URL + neg_kw (48-37)."""
        self.stdout.write('\nFix 1: Space Marine Company Heroes -- eBay URL + neg_kw')
        p = self._get_product('48-37')
        if p is None:
            return
        self._set_url(p, 'eBay', 'https://www.ebay.com/itm/186099352635', dry)
        # champion: blocks conversion listings with named Champion weapon load-outs
        # bolter:   blocks single-model "Bolter" weapon-option listings
        # fist:     blocks "Power Fist" or "Fist" weapon-upgrade conversion listings
        self._add_neg_kw(p, 'champion bolter fist', dry)

    def _fix_2_combat_patrol(self, dry):
        """Fix 2: Space Marine Combat Patrol -- eBay URL + neg_kw (71-02)."""
        self.stdout.write('\nFix 2: Space Marine Combat Patrol -- eBay URL + neg_kw')
        p = self._get_product('71-02')
        if p is None:
            return
        self._set_url(p, 'eBay', 'https://www.ebay.com/itm/405939586465', dry)
        # magazine:   blocks listings that bundle a White Dwarf or other GW magazine
        # terminators: blocks alternate Combat Patrol edition/variant box that
        #              explicitly mentions Terminators in the title (different SKU)
        self._add_neg_kw(p, 'magazine terminators', dry)

    def _fix_3_land_raider_crusader(self, dry):
        """Fix 3: Space Marine Land Raider Crusader -- eBay URL (48-22)."""
        self.stdout.write('\nFix 3: Space Marine Land Raider Crusader -- eBay URL')
        p = self._get_product('48-22')
        if p is None:
            return
        # Note: decor/art listings are handled by the global "-decor" eBay query
        # filter and the 'decor'/'decors' entry in _BITS_KEYWORDS (added to
        # ebay_api_client.py in this wave) — no per-SKU neg_kw needed.
        self._set_url(p, 'eBay', 'https://www.ebay.com/itm/175379698427', dry)

    def _fix_4_ork_lootas(self, dry):
        """Fix 4: Ork Lootas -- eBay URL + neg_kw + search name (50-14)."""
        self.stdout.write('\nFix 4: Ork Lootas -- eBay URL + neg_kw + search name')
        p = self._get_product('50-14')
        if p is None:
            return
        self._set_url(p, 'eBay', 'https://www.ebay.com/itm/183199561434', dry)
        # rokker, flash, elektro: musician/band-themed third-party conversion kit
        #   titles that share "Lootas" but are not the standard GW retail box.
        # wargame: generic hobby/gaming lot bundles; not a single sealed kit sale.
        # (Existing neg_kw already contains "DaBoom! Artel" from prior waves.)
        self._add_neg_kw(p, 'rokker flash elektro wargame', dry)
        # "ork lootas" improves eBay Best Match ranking over the default full name.
        self._set_search_name(p, 'ork lootas', dry)

    def _fix_5_incursors_amazon_price(self, dry):
        """Fix 5: Space Marine Incursors -- correct Amazon price $24.97 → $55.25 (48-96).

        Root cause: Wave R updated the Amazon URL from ASIN B07J3PG964 to B08GC37WBR
        using _set_url(), which only updates the url field and leaves the old price in
        place.  B07J3PG964 had a cached price of $24.97; B08GC37WBR (the correct dual-
        kit listing) is priced at $55.25.  This fix directly corrects the price row.
        """
        self.stdout.write('\nFix 5: Space Marine Incursors -- Amazon price correction')
        p = self._get_product('48-96')
        if p is None:
            return

        try:
            amazon = Retailer.objects.get(slug='amazon')
        except Retailer.DoesNotExist:
            self.stderr.write(self.style.ERROR("  ERROR: Retailer 'amazon' not found."))
            return

        try:
            cp = CurrentPrice.objects.get(product=p, retailer=amazon)
        except CurrentPrice.DoesNotExist:
            self.stderr.write(self.style.ERROR('  ERROR: No Amazon CurrentPrice row for 48-96.'))
            return

        current_price = cp.price
        correct_price = Decimal('55.25')
        correct_url = 'https://www.amazon.com/dp/B08GC37WBR'

        if cp.price == correct_price and cp.url == correct_url and cp.in_stock:
            self.stdout.write('  [skip] Amazon price/URL/in_stock already correct')
            return

        if dry:
            self.stdout.write(
                f'  [dry] Amazon price: {current_price} -> {correct_price}\n'
                f'  [dry] Amazon URL: {(cp.url or "(blank)")[:55]} -> {correct_url[:55]}\n'
                f'  [dry] in_stock: {cp.in_stock} -> True'
            )
            return

        CurrentPrice.objects.filter(pk=cp.pk).update(
            price=correct_price,
            url=correct_url,
            in_stock=True,
            not_available=False,
        )
        self.stdout.write(
            self.style.SUCCESS(
                f'  [ok] Amazon price: {current_price} -> {correct_price} | '
                f'in_stock=True'
            )
        )
