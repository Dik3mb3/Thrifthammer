"""
Management command: apply_batch_fixes_mar2026r

Eighteenth wave of March 2026 batch corrections for ThriftHammer.
Run after apply_batch_fixes_mar2026q.

Changes covered:
  Fix 1  -- Space Marine Incursors (48-96):
             - Correct Amazon URL (old: B07J3PG964, new: B08GC37WBR)
               Old ASIN was wrong/OOS listing.

  Fix 2  -- Space Marine Invader ATV (48-42):
             - Correct eBay URL (old: 136996707290, new: 184470832471)
             - Set ebay_search_name "invader atv warhammer 40k"
               Removing "Space Marine" from query reduces match breadth;
               adding "warhammer 40k" ensures game-context specificity so
               eBay Best Match surfaces the correct standalone kit listing
               rather than high-engagement bundle/overpriced BIN listings.

  Fix 3  -- Space Marine Land Raider Crusader (48-22):
             - Correct eBay URL (old: 176266974926 at ~$115, new: 389726995331)
             - Set ebay_search_name "land raider crusader 40k"
               Root cause of expensive-listing problem: the default search
               "Space Marine Land Raider Crusader" returns eBay Best Match
               results ranked by engagement/recency.  The cheaper correct
               listing does not rank in the top N results for that query,
               so the 10%-cheaper threshold in find_best_match_for_product
               never has a chance to apply.
               Shortening to "land raider crusader 40k" removes the generic
               "Space Marine" faction prefix and adds the "40k" disambiguator,
               which shifts eBay Best Match toward the exact kit name and
               surfaces cheaper standalone-box listings earlier in results.

  Fix 4  -- Space Marine Eliminators (48-98):
             - Correct eBay URL (old: 163807263326, new: 188146430061)
             - neg_kw "vanguard task force" (SKU-specific only)
               vanguard:   blocks "Vanguard Space Marines" multi-unit set
                           listings that match Eliminators search terms.
               task:       blocks "Task Force" bundle/box set listings.
               force:      blocks "Task Force" and "Strike Force" bundle
                           listings that include Eliminators as a component.

Usage:
    python manage.py apply_batch_fixes_mar2026r
    python manage.py apply_batch_fixes_mar2026r --dry-run
"""

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Product, Retailer


class Command(BaseCommand):
    """Eighteenth wave of March 2026 ThriftHammer DB corrections."""

    help = (
        'Apply Wave R batch corrections (March 2026) -- '
        'SM Incursors Amazon, Invader ATV/LR Crusader/Eliminators eBay URL + search fixes.'
    )

    def add_arguments(self, parser):
        """Add --dry-run flag to preview changes without saving."""
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Print planned changes without writing to the database.',
        )

    def handle(self, *args, **options):
        """Execute all Wave R corrections in order."""
        dry = options['dry_run']
        if dry:
            self.stdout.write(self.style.WARNING('DRY RUN -- no changes will be saved.\n'))

        self._fix_1_sm_incursors(dry)
        self._fix_2_sm_invader_atv(dry)
        self._fix_3_sm_land_raider_crusader(dry)
        self._fix_4_sm_eliminators(dry)

        if dry:
            self.stdout.write(self.style.WARNING('\nDRY RUN complete -- nothing was saved.'))
        else:
            self.stdout.write(self.style.SUCCESS('\nWave R complete.'))

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

    def _fix_1_sm_incursors(self, dry):
        """Fix 1: Space Marine Incursors -- correct Amazon URL (48-96)."""
        self.stdout.write('\nFix 1: Space Marine Incursors -- Amazon URL')
        p = self._get_product('48-96')
        if p is None:
            return
        # Old ASIN B07J3PG964 was wrong/OOS.  Correct ASIN: B08GC37WBR.
        self._set_url(p, 'Amazon', 'https://www.amazon.com/dp/B08GC37WBR', dry)

    def _fix_2_sm_invader_atv(self, dry):
        """Fix 2: Space Marine Invader ATV -- eBay URL + search name (48-42)."""
        self.stdout.write('\nFix 2: Space Marine Invader ATV -- eBay URL + search name')
        p = self._get_product('48-42')
        if p is None:
            return
        self._set_url(p, 'eBay', 'https://www.ebay.com/itm/184470832471', dry)
        # Removing "Space Marine" and adding "warhammer 40k" shifts eBay Best
        # Match away from high-engagement overpriced BIN listings toward the
        # correct standalone-kit listing.
        self._set_search_name(p, 'invader atv warhammer 40k', dry)

    def _fix_3_sm_land_raider_crusader(self, dry):
        """Fix 3: Space Marine Land Raider Crusader -- eBay URL + search name (48-22)."""
        self.stdout.write('\nFix 3: Space Marine Land Raider Crusader -- eBay URL + search name')
        p = self._get_product('48-22')
        if p is None:
            return
        self._set_url(p, 'eBay', 'https://www.ebay.com/itm/389726995331', dry)
        # "land raider crusader 40k" drops the generic "Space Marine" prefix
        # and adds the "40k" game-context token.  This shifts eBay Best Match
        # toward exact-kit standalone listings, giving the cheaper correct
        # listing a better chance to rank in the top N results that
        # find_best_match_for_product evaluates.
        self._set_search_name(p, 'land raider crusader 40k', dry)

    def _fix_4_sm_eliminators(self, dry):
        """Fix 4: Space Marine Eliminators -- eBay URL + neg_kw (48-98)."""
        self.stdout.write('\nFix 4: Space Marine Eliminators -- eBay URL + neg_kw')
        p = self._get_product('48-98')
        if p is None:
            return
        self._set_url(p, 'eBay', 'https://www.ebay.com/itm/188146430061', dry)
        # vanguard: blocks Vanguard Space Marines multi-unit set listings
        # task:     blocks Task Force bundle listings
        # force:    blocks Strike Force / Task Force box sets containing
        #           Eliminators as a component alongside other units
        self._add_neg_kw(p, 'vanguard task force', dry)
