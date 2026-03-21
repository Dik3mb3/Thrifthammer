"""
Management command: apply_batch_fixes_mar2026s

Nineteenth wave of March 2026 batch corrections for ThriftHammer.
Run after apply_batch_fixes_mar2026r.

Changes covered:
  Fix 1  -- Space Marine Primaris Lieutenant (48-61):
             - Correct Noble Knight URL
               Old: /P/2147802124/Primaris-Lieutenant-500th-Store-Exclusi
                    (500th Store Anniversary exclusive collector's item — not the
                     standard retail kit; listed at $129.95)
               New: /P/2147831538/Primaris-Lieutenant-w-Power-Sword-2020-Edition

  Fix 2  -- Space Marine Repulsor Executioner (48-95):
             - Correct eBay URL (old: 317219826251 at ~$122, new: 173939906742)
             - Set ebay_search_name "repulsor executioner 40k"
               Removing "Space Marine Primaris" prefix and adding "40k" shifts
               eBay Best Match toward the correct sealed-box listing rather
               than high-engagement overpriced BIN listings.

  Fix 3  -- Space Marine Scouts (48-29):
             - Correct eBay URL (old: 206101242197 at $40, new: 287196272221)
             - Update GW URL to direct product page (was generic search query)
               New: https://www.warhammer.com/en-WW/shop/kill-team-scout-squad-2024
             - neg_kw "needle" (SKU-specific only)
               Blocks "Needle Sniper Rifle" conversion variant listings that
               share Scout keywords but are not the standard kit.
             - Update image_url to the 2024 Kill Team Scout Squad product image
               (old image was a codex book cover — not the miniature kit)
               New: .../99120101422_KTScoutSquad1.jpg

  Fix 4  -- Space Marine Sternguard Veteran Squad (48-43):
             - Set eBay URL (was blank): item 186099358998
             - Set ebay_search_name "Sternguard Veteran Squad warhammer 40k"
               The blank eBay URL indicates the daily scraper found no acceptable
               listing for the default search.  Adding "warhammer 40k" and dropping
               "Space Marine" prefix helps eBay Best Match surface the correct
               sealed-box listing, which sellers often title without the faction
               prefix (e.g. "Sternguard Veterans Warhammer 40,000").

  Fix 5  -- Space Marine Tactical Squad (48-07):
             - Correct eBay URL (old: 167541228489 at $29.90, new: 137040197561)
             - neg_kw "power fist" (SKU-specific only)
               power: contributes to "Power Fist" upgrade conversion listings
               fist:  the more specific of the two; together they block listings
                      explicitly advertising the Power Fist weapon option (partial
                      kits / conversions rather than the standard sealed box).

  Fix 6  -- Spearhead: Slaves to Darkness (70-04):
             - Correct eBay URL (old: 316735169137 at $44.99, new: 186801446976)
             - neg_kw "sorcerer lord" (SKU-specific only)
               sorcerer: blocks Chaos Sorcerer Lord single-model blister listings
               lord:     blocks generic Slaves to Darkness "Chaos Lord" single-
                         model listings that match enough Spearhead keywords
             - Set ebay_search_name "Age of Sigmar Spearhead Slaves to Darkness"
               The product name "Spearhead: Slaves to Darkness" omits the AoS
               game-system prefix and contains a colon (stripped by URL encoding).
               Adding "Age of Sigmar" up front disambiguates from Old World /
               40K Chaos Warriors products and matches how eBay sellers title
               the Spearhead box set.

Usage:
    python manage.py apply_batch_fixes_mar2026s
    python manage.py apply_batch_fixes_mar2026s --dry-run
"""

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Product, Retailer


class Command(BaseCommand):
    """Nineteenth wave of March 2026 ThriftHammer DB corrections."""

    help = (
        'Apply Wave S batch corrections (March 2026) -- '
        'SM Lieutenant NK URL, Repulsor/Scouts/Sternguard/Tactical eBay fixes, '
        'Spearhead Slaves to Darkness eBay fix.'
    )

    def add_arguments(self, parser):
        """Add --dry-run flag to preview changes without saving."""
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Print planned changes without writing to the database.',
        )

    def handle(self, *args, **options):
        """Execute all Wave S corrections in order."""
        dry = options['dry_run']
        if dry:
            self.stdout.write(self.style.WARNING('DRY RUN -- no changes will be saved.\n'))

        self._fix_1_primaris_lieutenant_nk(dry)
        self._fix_2_repulsor_executioner(dry)
        self._fix_3_scouts(dry)
        self._fix_4_sternguard(dry)
        self._fix_5_tactical_squad(dry)
        self._fix_6_spearhead_slaves(dry)

        if dry:
            self.stdout.write(self.style.WARNING('\nDRY RUN complete -- nothing was saved.'))
        else:
            self.stdout.write(self.style.SUCCESS('\nWave S complete.'))

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

    def _set_image_url(self, product, new_url, dry):
        """Update product.image_url; skip if already correct."""
        current = (product.image_url or '').strip()
        if current == new_url:
            self.stdout.write(f'  [skip] image_url already correct')
            return
        if dry:
            self.stdout.write(
                f'  [dry] image_url: "{current[:60] or "(empty)"}" -> "{new_url[:60]}"'
            )
            return
        product.image_url = new_url
        product.save(update_fields=['image_url'])
        self.stdout.write(f'  [ok] image_url -> "{new_url[:70]}"')

    # -----------------------------------------------------------------------
    # Fixes
    # -----------------------------------------------------------------------

    def _fix_1_primaris_lieutenant_nk(self, dry):
        """Fix 1: Space Marine Primaris Lieutenant -- correct Noble Knight URL (48-61)."""
        self.stdout.write('\nFix 1: Space Marine Primaris Lieutenant -- Noble Knight URL')
        p = self._get_product('48-61')
        if p is None:
            return
        # Old URL was the 500th-Store Anniversary limited-edition blister ($129.95).
        # Correct URL is the standard 2020 Edition retail product.
        self._set_url(
            p, 'Noble Knight Games',
            'https://www.nobleknight.com/P/2147831538/Primaris-Lieutenant-w-Power-Sword-2020-Edition',
            dry,
        )

    def _fix_2_repulsor_executioner(self, dry):
        """Fix 2: Space Marine Repulsor Executioner -- eBay URL + search name (48-95)."""
        self.stdout.write('\nFix 2: Space Marine Repulsor Executioner -- eBay URL + search name')
        p = self._get_product('48-95')
        if p is None:
            return
        self._set_url(p, 'eBay', 'https://www.ebay.com/itm/173939906742', dry)
        # Dropping "Space Marine Primaris" and adding "40k" shifts eBay Best Match
        # toward the correct sealed-kit listing rather than overpriced BIN results.
        self._set_search_name(p, 'repulsor executioner 40k', dry)

    def _fix_3_scouts(self, dry):
        """Fix 3: Space Marine Scouts -- eBay URL + GW URL + neg_kw + image (48-29)."""
        self.stdout.write('\nFix 3: Space Marine Scouts -- eBay URL + GW URL + neg_kw + image')
        p = self._get_product('48-29')
        if p is None:
            return
        self._set_url(p, 'eBay', 'https://www.ebay.com/itm/287196272221', dry)
        # Update to the direct 2024 Kill Team Scout Squad product page (was generic search).
        self._set_url(
            p, 'Games Workshop',
            'https://www.warhammer.com/en-WW/shop/kill-team-scout-squad-2024',
            dry,
        )
        # needle: blocks "Needle Sniper Rifle" Scout conversion variant listings
        # that pass keyword matching for the standard Scout Squad search.
        self._add_neg_kw(p, 'needle', dry)
        # Update product image to the 2024 Kill Team Scout Squad kit photo.
        # Old image was a codex book cover (60030101061_ENGSMCodex01.jpg).
        self._set_image_url(
            p,
            'https://www.warhammer.com/app/resources/catalog/product/920x950/99120101422_KTScoutSquad1.jpg',
            dry,
        )

    def _fix_4_sternguard(self, dry):
        """Fix 4: Space Marine Sternguard Veteran Squad -- set eBay URL + search name (48-43)."""
        self.stdout.write('\nFix 4: Space Marine Sternguard Veteran Squad -- eBay URL + search name')
        p = self._get_product('48-43')
        if p is None:
            return
        self._set_url(p, 'eBay', 'https://www.ebay.com/itm/186099358998', dry)
        # Adding "warhammer 40k" and dropping "Space Marine" helps surface the
        # correct listing in eBay Best Match.  Sellers frequently title this
        # kit without the faction prefix (e.g. "Sternguard Veterans Warhammer
        # 40,000") so the shorter query casts a wider but still accurate net.
        self._set_search_name(p, 'Sternguard Veteran Squad warhammer 40k', dry)

    def _fix_5_tactical_squad(self, dry):
        """Fix 5: Space Marine Tactical Squad -- eBay URL + neg_kw (48-07)."""
        self.stdout.write('\nFix 5: Space Marine Tactical Squad -- eBay URL + neg_kw')
        p = self._get_product('48-07')
        if p is None:
            return
        self._set_url(p, 'eBay', 'https://www.ebay.com/itm/137040197561', dry)
        # power: contributes to "Power Fist" upgrade listings (conversion kits)
        # fist:  blocks "Power Fist" weapon-upgrade or conversion-only listings
        #        that advertise the individual weapon option rather than the full box
        self._add_neg_kw(p, 'power fist', dry)

    def _fix_6_spearhead_slaves(self, dry):
        """Fix 6: Spearhead: Slaves to Darkness -- eBay URL + neg_kw + search name (70-04)."""
        self.stdout.write('\nFix 6: Spearhead: Slaves to Darkness -- eBay URL + neg_kw + search name')
        p = self._get_product('70-04')
        if p is None:
            return
        self._set_url(p, 'eBay', 'https://www.ebay.com/itm/186801446976', dry)
        # sorcerer: blocks Chaos Sorcerer Lord single-model blister listings
        # lord:     blocks generic Chaos Lord single-model listings that share
        #           enough Spearhead keywords to pass match threshold
        self._add_neg_kw(p, 'sorcerer lord', dry)
        # "Age of Sigmar Spearhead Slaves to Darkness" adds the AoS game-system
        # prefix (disambiguates from Old World / 40K Chaos products) and avoids
        # the colon in "Spearhead: Slaves to Darkness" that can break URL encoding.
        self._set_search_name(p, 'Age of Sigmar Spearhead Slaves to Darkness', dry)
