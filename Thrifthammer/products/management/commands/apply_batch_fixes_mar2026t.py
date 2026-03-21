"""
Management command: apply_batch_fixes_mar2026t

Twentieth wave of March 2026 batch corrections for ThriftHammer.
Run after apply_batch_fixes_mar2026s.

Changes covered:
  Fix 1  -- Stormcast Eternals Knight-Judicator with Gryph-hounds (96-12):
             - Update GW URL from generic search to direct product page.
               Note: the product is stored in the DB under gw_sku 96-12 and is
               seeded as "Stormcast Eternals Knight-Judicator with Gryph-hounds"
               in populate_products.py (image also confirms this: KnightJudicator
               GryphHoundsLead.jpg).

  Fix 2  -- Stormcast Eternals Lord-Celestant (96-14):
             - Correct Amazon URL (ASIN was B09CV9CD6J at $162.35 — collector/
               third-party price, clearly wrong for a $27.50 retail product).
               New ASIN: B0DJM335L2

  Fix 3  -- Stormcast Eternals Vindictors (96-50):
             - Correct eBay URL (old: 286701814529, new: 174989329392)
             - neg_kw "paint" (SKU-specific only)
               Blocks "Vindictors Paint Set" bundle listings which bundle the
               miniatures with paints — these are priced higher and are a
               different product from the standalone kit.
               "paint" alone is specific enough; "set" would be too broad.

  Fix 4  -- T'au Pathfinders (56-19):
             - Correct eBay URL (old: 116876256071 at $33.99, new: 147214676067)
             - Set ebay_search_name "pathfinders 40k"
               The default "T'au Pathfinders" search has two problems: (1) the
               apostrophe in "T'au" can break eBay's tokenisation, (2) the full
               faction-name prefix causes eBay Best Match to surface overpriced
               BIN listings at near-MSRP.  "pathfinders 40k" is clean, specific
               to the game system, and matches the seller keyword conventions.

  Fix 5  -- T'au Stealth Battlesuits (56-14):
             - Correct Amazon URL (old ASIN B075X58BFJ is OOS/unavailable).
               New ASIN: B0GHPCGWN3
             - Update GW URL to direct product page
               (new 2026 Kill Team Stealth Battlesuits release).
             - Set eBay URL from blank to item 168150067585.
             - Set ebay_search_name "stealth battlesuits"
               The product name contains the Tau faction abbreviation which can
               confuse eBay's index.  "stealth battlesuits" alone is highly
               specific and matches the dominant seller titling convention.

  Fix 6  -- Thousand Sons Ahriman (43-30):
             - Correct eBay URL (old: 358326235778, new: 137102564657)
             - Set ebay_search_name "ahriman 40k"
               "Thousand Sons Ahriman" returns many Horus Heresy and old-edition
               metal sculpts that mix into results.  "ahriman 40k" is the clean,
               short form sellers use and surfaces the current plastic kit.
             - neg_kw "horus" (SKU-specific only)
               Blocks "Horus Heresy" era Ahriman sculpts (the older clampack
               character released in the Horus Heresy range) which share all
               Ahriman keywords but are a different, usually cheaper product.
             - Correct Noble Knight URL
               (old: generic search fallback, new: direct product page).

  Fix 7  -- Thousand Sons Exalted Sorcerers (43-38):
             - Correct eBay URL (old: 402506753199, new: 356204459902)
             - neg_kw "walking" (SKU-specific only)
               Blocks "walking" conversion listings where sellers have replaced
               the hovering/flying-base poses with walking/grounded poses.
               These are custom conversions, not the standard sealed kit.

Usage:
    python manage.py apply_batch_fixes_mar2026t
    python manage.py apply_batch_fixes_mar2026t --dry-run
"""

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Product, Retailer


class Command(BaseCommand):
    """Twentieth wave of March 2026 ThriftHammer DB corrections."""

    help = (
        'Apply Wave T batch corrections (March 2026) -- '
        'Stormcast GW/Amazon fixes, T\'au eBay fixes, '
        'Thousand Sons Ahriman/Exalted Sorcerers eBay/NK fixes.'
    )

    def add_arguments(self, parser):
        """Add --dry-run flag to preview changes without saving."""
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Print planned changes without writing to the database.',
        )

    def handle(self, *args, **options):
        """Execute all Wave T corrections in order."""
        dry = options['dry_run']
        if dry:
            self.stdout.write(self.style.WARNING('DRY RUN -- no changes will be saved.\n'))

        self._fix_1_knight_judicator_gw(dry)
        self._fix_2_lord_celestant_amazon(dry)
        self._fix_3_vindictors(dry)
        self._fix_4_pathfinders(dry)
        self._fix_5_stealth_battlesuits(dry)
        self._fix_6_ahriman(dry)
        self._fix_7_exalted_sorcerers(dry)

        if dry:
            self.stdout.write(self.style.WARNING('\nDRY RUN complete -- nothing was saved.'))
        else:
            self.stdout.write(self.style.SUCCESS('\nWave T complete.'))

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

    # -----------------------------------------------------------------------
    # Fixes
    # -----------------------------------------------------------------------

    def _fix_1_knight_judicator_gw(self, dry):
        """Fix 1: Knight-Judicator with Gryph-hounds -- GW product page URL (96-12)."""
        self.stdout.write('\nFix 1: Stormcast Eternals Knight-Judicator with Gryph-hounds -- GW URL')
        p = self._get_product('96-12')
        if p is None:
            return
        self._set_url(
            p, 'Games Workshop',
            'https://www.warhammer.com/en-WW/shop/stormcast-eternals-knight-judicator-with-gryph-hounds-2021',
            dry,
        )

    def _fix_2_lord_celestant_amazon(self, dry):
        """Fix 2: Stormcast Eternals Lord-Celestant -- correct Amazon ASIN (96-14)."""
        self.stdout.write('\nFix 2: Stormcast Eternals Lord-Celestant -- Amazon URL')
        p = self._get_product('96-14')
        if p is None:
            return
        # Old ASIN B09CV9CD6J was showing at $162.35 — a third-party collector
        # price, not the correct product listing.
        self._set_url(p, 'Amazon', 'https://www.amazon.com/dp/B0DJM335L2', dry)

    def _fix_3_vindictors(self, dry):
        """Fix 3: Stormcast Eternals Vindictors -- eBay URL + neg_kw (96-50)."""
        self.stdout.write('\nFix 3: Stormcast Eternals Vindictors -- eBay URL + neg_kw')
        p = self._get_product('96-50')
        if p is None:
            return
        self._set_url(p, 'eBay', 'https://www.ebay.com/itm/174989329392', dry)
        # paint: blocks "Vindictors Paint Set" bundle listings (includes paints,
        # priced higher, different product from the standalone miniature kit).
        # "set" alone would be far too broad; "paint" is the distinctive word.
        self._add_neg_kw(p, 'paint', dry)

    def _fix_4_pathfinders(self, dry):
        """Fix 4: T'au Pathfinders -- eBay URL + search name (56-19)."""
        self.stdout.write('\nFix 4: T\'au Pathfinders -- eBay URL + search name')
        p = self._get_product('56-19')
        if p is None:
            return
        self._set_url(p, 'eBay', 'https://www.ebay.com/itm/147214676067', dry)
        # Apostrophe in "T'au" breaks eBay tokenisation; shorter query avoids
        # overpriced BIN results that the full faction name attracts.
        self._set_search_name(p, 'pathfinders 40k', dry)

    def _fix_5_stealth_battlesuits(self, dry):
        """Fix 5: T'au Stealth Battlesuits -- Amazon + GW + eBay URLs + search name (56-14)."""
        self.stdout.write('\nFix 5: T\'au Stealth Battlesuits -- Amazon + GW + eBay + search name')
        p = self._get_product('56-14')
        if p is None:
            return
        # Old Amazon ASIN B075X58BFJ was OOS/unavailable (price=None, in_stock=False).
        self._set_url(p, 'Amazon', 'https://www.amazon.com/dp/B0GHPCGWN3', dry)
        # Update to the 2026 Kill Team XV26 Stealth Battlesuits product page.
        self._set_url(
            p, 'Games Workshop',
            'https://www.warhammer.com/en-WW/shop/kill-team-xv26-stealth-battlesuits-2026',
            dry,
        )
        # eBay row was blank — set the correct listing.
        self._set_url(p, 'eBay', 'https://www.ebay.com/itm/168150067585', dry)
        # "stealth battlesuits" is concise, specific, and avoids the T'au
        # apostrophe tokenisation issue; matches dominant seller titling.
        self._set_search_name(p, 'stealth battlesuits', dry)

    def _fix_6_ahriman(self, dry):
        """Fix 6: Thousand Sons Ahriman -- eBay URL + search name + neg_kw + NK URL (43-30)."""
        self.stdout.write('\nFix 6: Thousand Sons Ahriman -- eBay URL + search name + neg_kw + NK')
        p = self._get_product('43-30')
        if p is None:
            return
        self._set_url(p, 'eBay', 'https://www.ebay.com/itm/137102564657', dry)
        # "ahriman 40k" is the clean short-form sellers use; avoids Horus Heresy
        # and old-edition metal sculpt contamination from the full faction prefix.
        self._set_search_name(p, 'ahriman 40k', dry)
        # horus: blocks Horus Heresy-era Ahriman clamp-pack listings (older
        # sculpt released in the Horus Heresy character range) which share all
        # Ahriman keywords but are a different product, usually cheaper.
        self._add_neg_kw(p, 'horus', dry)
        # Update Noble Knight to direct product page (was generic search fallback).
        self._set_url(
            p, 'Noble Knight Games',
            'https://www.nobleknight.com/P/2147936751/Ahriman-the-Sorcerer',
            dry,
        )

    def _fix_7_exalted_sorcerers(self, dry):
        """Fix 7: Thousand Sons Exalted Sorcerers -- eBay URL + neg_kw (43-38)."""
        self.stdout.write('\nFix 7: Thousand Sons Exalted Sorcerers -- eBay URL + neg_kw')
        p = self._get_product('43-38')
        if p is None:
            return
        self._set_url(p, 'eBay', 'https://www.ebay.com/itm/356204459902', dry)
        # walking: blocks custom conversion listings where sellers have replaced
        # the kit's hovering/flying-base poses with grounded "walking" poses.
        # These are conversions, not the standard sealed retail kit.
        self._add_neg_kw(p, 'walking', dry)
