"""
Management command: apply_batch_fixes_mar2026

Applies all March 2026 batch database corrections requested by the site admin:

  • Deactivates duplicate / discontinued SKUs
  • Renames Blood Angels Death Company products
  • Fixes wrong Amazon, eBay, Noble Knight, and GW CurrentPrice entries
  • Adds missing CurrentPrice entries (Sentinel, Commissar, Plastic Glue …)
  • Updates product images to show actual product photos
  • Clears MSRP on paint products where GW does not sell the item
  • Fixes Astra Militarum Infantry Squad (47-19) 505 error by ensuring all
    retailers have a CurrentPrice row (not_available=True when not stocked)

Usage:
    python manage.py apply_batch_fixes_mar2026
    python manage.py apply_batch_fixes_mar2026 --dry-run

This command is fully idempotent — safe to re-run.

Why things were wrong and how to avoid the same mistakes in future:
  See the inline LESSON comments throughout this file.
"""

import decimal

from django.core.management.base import BaseCommand, CommandError

from prices.models import CurrentPrice
from products.models import Product, Retailer


# ===========================================================================
# IMAGE URLS
# Image URLs to update.  Amazon images use the m.media-amazon.com CDN.
# eBay images use the i.ebayimg.com CDN.
# These were verified manually in March 2026.
# ===========================================================================

# Amazon product images (fetched from product page main image):
IMG_BP001_AMAZON   = 'https://m.media-amazon.com/images/I/71KpQQ7bHBL._AC_SL1200_.jpg'   # Base Paint single B007RQ4060
IMG_CP003_AMAZON   = 'https://m.media-amazon.com/images/I/71LsPGgKl8L._AC_SL1200_.jpg'   # Contrast Blood Angels Red B07SRQ88S2
IMG_SP001_AMAZON   = 'https://m.media-amazon.com/images/I/71Y7PZTHC4L._AC_SL1200_.jpg'   # Shade Nuln Oil B01H7JECW8
IMG_SP010_AMAZON   = 'https://m.media-amazon.com/images/I/61UM-C-FFML._AC_SL1200_.jpg'   # Chaos Black Spray B000A5CHHE
IMG_SP012_AMAZON   = 'https://m.media-amazon.com/images/I/71V+kAVCmQL._AC_SL1200_.jpg'   # Wraithbone Spray B08ZHWMFX3 (used for Grey Seer too)
IMG_CSP004_AMAZON  = 'https://m.media-amazon.com/images/I/71iFMHGTyvL._AC_SL1200_.jpg'   # Zandri Dust Spray B00T86KNJK

# eBay product images (fetched from individual listing pages):
IMG_BS001_EBAY     = 'https://i.ebayimg.com/images/g/PuAAAOSwq-1kz5A2/s-l500.jpg'        # Base Paint Set BS-001
IMG_LP001_EBAY     = 'https://i.ebayimg.com/images/g/JdQAAOSw4U9jm-cV/s-l500.jpg'        # Layer Paint LP-001
IMG_SP020_EBAY     = 'https://i.ebayimg.com/images/g/5HQAAOSwlBZm5x1y/s-l500.jpg'        # Munitorum Varnish SP-020
IMG_SP002_EBAY     = 'https://i.ebayimg.com/images/g/HLYAAOSwfeBiOByH/s-l500.jpg'        # Agrax Earthshade SP-002
IMG_SP003_EBAY     = 'https://i.ebayimg.com/images/g/OWsAAOSwp5dkdQ9T/s-l500.jpg'        # Reikland Fleshshade SP-003
IMG_CSP003_EBAY    = 'https://i.ebayimg.com/images/g/FdEAAOSwB4hkjOr1/s-l500.jpg'        # Corax White Spray CSP-003
IMG_TCP001_EBAY    = 'https://i.ebayimg.com/images/g/LdEAAOSwQ8hm5GBT/s-l500.jpg'        # Technical Paint TCP-001

# GW Death Company image — correct product photo (not the codex cover)
IMG_41_07_GW = 'https://www.warhammer.com/app/resources/catalog/product/920x950/99120101402_BADeathCompanyMarines02.jpg'


# ===========================================================================
# SKUS TO DEACTIVATE  (is_active → False)
# These products are either:
#   a) Duplicates of another active SKU
#   b) Discontinued / removed from catalogue
# ===========================================================================
DEACTIVATE_SKUS = [
    # ── Duplicate spray primers ──────────────────────────────────────────
    # LESSON: CSP-xxx were early placeholder SKUs before we consolidated
    #   all sprays under SP-xxx.  CSP-001 duplicates SP-010 (Chaos Black);
    #   CSP-002 duplicates SP-011 (Wraithbone).  Keep the SP-xxx entries
    #   because they have more price links.
    'CSP-001',   # Citadel Spray Chaos Black — duplicate of SP-010
    'CSP-002',   # Citadel Spray Wraithbone  — duplicate of SP-011

    # ── Duplicate Bloodletters ───────────────────────────────────────────
    # LESSON: 97-10 was a data entry duplicate of 97-08.  97-08 is the
    #   canonical SKU (5 price links vs 97-10's 4); deactivate 97-10.
    '97-10',     # Blades of Khorne Bloodletters — duplicate of 97-08

    # ── Age of Sigmar Starter Set ────────────────────────────────────────
    # LESSON: This product was discontinued by GW and is no longer relevant
    '80-15',     # Age of Sigmar Warrior Starter Set

    # ── Blood Angels SKUs no longer sold ────────────────────────────────
    '41-11',     # Blood Angels Death Company Dreadnought
    '41-15',     # Blood Angels Librarian Dreadnought

    # ── Citadel paint bundles and hobby supplies ─────────────────────────
    # LESSON: Generic bundle SKUs (CP-005, CP-010, etc.) caused confusion
    #   because the eBay scraper kept matching them to random paint sets.
    #   Individual paints are better tracked per-product.
    'CP-005',    # Contrast Paint Bundle x5
    'BS-002',    # Colour Shade Set
    'CP-010',    # Contrast Paint Bundle x10
    'CP-002',    # Contrast Wraithbone 18ml paint — DIFFERENT from SP-011 spray
    'DB-001',    # Detail Brush Set
    'DP-001',    # Dry Paint (single, generic)
    'HK-001',    # Hobby Knife
    'PM-001',    # Painting Mat
    'SG-001',    # Super Glue
    'TE-001',    # Technical Paint: Nihilakh Oxide
    'TP-001',    # Texture Paint: Astrogranite
    'WP-001',    # Water Pot
]


# ===========================================================================
# PRICE DATA: Amazon corrections
# Format: gw_sku -> (price_str, amazon_asin, in_stock)
# LESSON: Always check Amazon page title matches the product name before
#   trusting the price.  Mismatches found in the previous scrape were due
#   to ASINs that redirect to other products or outdated listings.
# ===========================================================================
AMAZON_FIXES = {
    # ── Adeptus Custodes ──────────────────────────────────────────────────
    # LESSON: 01-07 Shield-Captain — old ASIN B0795XTD6L was a placeholder
    #   that resolved to a different Custodes character blister.
    #   B0D639NL6S is the correct current ASIN for Shield-Captain on Bike.
    '01-07': ('35.70', 'https://www.amazon.com/dp/B0D639NL6S', True),    # Shield-Captain

    # LESSON: 01-02 Trajann — ASIN was correct but price outdated.
    #   Amazon price dropped from $62.48 to $40.80.
    '01-02': ('40.80', 'https://www.amazon.com/dp/B0795Y92B5', True),    # Trajann Valoris (price update)

    # ── Adeptus Mechanicus ────────────────────────────────────────────────
    # LESSON: 59-20 Electropriests — old ASIN B095J6PXFF was a Prime-only
    #   bundle listing; actual unit box is B00YHWCMO4 at $48.99.
    '59-20': ('48.99', 'https://www.amazon.com/dp/B00YHWCMO4', True),    # Electropriests

    # LESSON: 59-18 Kataphron Destroyers — old ASIN B0CNTVKXZD was
    #   incorrect (pointed to Kastelans).  B00XTZUSB4 is the correct box.
    '59-18': ('55.25', 'https://www.amazon.com/dp/B00XTZUSB4', True),    # Kataphron Destroyers

    # ── Astra Militarum ───────────────────────────────────────────────────
    # LESSON: 47-08 Commissar — old ASIN B0DHLRML9F was too cheap ($26.99)
    #   and pointed to a Datasheet card pack, not the miniature kit.
    #   B0BVMGVP2X is the actual Commissar miniature.
    '47-08': ('33.15', 'https://www.amazon.com/dp/B0BVMGVP2X', True),    # Commissar

    # LESSON: 47-12 Sentinel — was omitted from the original Amazon seed
    #   because the first scrape found only a JoyToy (toy figure) ASIN.
    #   B0BSFPTZWJ is the correct GW Sentinel kit.
    '47-12': ('40.80', 'https://www.amazon.com/dp/B0BSFPTZWJ', True),    # Sentinel (new entry)

    # ── Blood Angels ──────────────────────────────────────────────────────
    # LESSON: 41-05 Lemartes — old ASIN B0FPR7Q65F was the Librarian
    #   Dreadnought (41-15), a totally different product.  Always verify
    #   ASIN product title matches the GW product name exactly.
    '41-05': ('38.99', 'https://www.amazon.com/dp/B0DJFF398H', True),    # Lemartes

    # ── Citadel Paints ────────────────────────────────────────────────────
    # LESSON: BS-001 Colour Base Paint Set — old ASIN B0B6Z81PKV was a
    #   single paint pot (price $4.55), not the full set ($38.25).
    #   Always check price plausibility — if a "set" costs $4, it's wrong.
    'BS-001': ('38.25', 'https://www.amazon.com/dp/B0CBKHZY3V', True),   # Colour Base Paint Set

    # PG-001 Plastic Glue — previously omitted.  B004CDA3GC is the correct kit.
    'PG-001': ('12.49', 'https://www.amazon.com/dp/B004CDA3GC', True),   # Plastic Glue
}

# ASINs to mark not_available on Amazon (product removed / wrong match):
AMAZON_NOT_AVAILABLE = [
    # LESSON: 47-17 Basilisk — Amazon listing found was a toy tank at $29.75,
    #   not the GW kit (MSRP $57.50).  When price is less than half of MSRP,
    #   it is almost certainly a wrong match.  Removed until a correct listing
    #   is found.
    '47-17',   # Basilisk — wrong listing removed

    # LESSON: CSP-003 Corax White Spray — Amazon listing was for the old
    #   smaller size.  No correct in-stock listing found.
    'CSP-003',  # Corax White spray — not available on Amazon
]


# ===========================================================================
# PRICE DATA: eBay corrections
# Format: gw_sku -> (price_str, url, in_stock)
# LESSON: Always use a specific eBay item URL, not a search URL.  The scraper
#   re-runs frequently and will re-find the correct listing if the URL is right.
#   Search URLs (?_skw=...) can drift and match different listings over time.
# ===========================================================================
EBAY_FIXES = {
    # LESSON: 47-30 Cadian Shock Troops — eBay was returning "Cadian Command
    #   Squad" because the search term was too generic ("Cadian").
    #   Use "Warhammer Cadian Shock Troops" to force the right keywords.
    '47-30': ('45.05', 'https://www.ebay.com/itm/185745187601', True),   # Cadian Shock Troops

    # LESSON: 47-08 Commissar — eBay link was pointing to a codex supplement
    #   rather than the miniature blister.  Verified listing 374526420774
    #   shows the correct single-model Commissar.
    '47-08': ('33.15', 'https://www.ebay.com/itm/374526420774', True),   # Commissar

    # LESSON: 55-24 Grimaldus — old eBay link was for a generic Black Templars
    #   lot, not Grimaldus specifically.  175018174961 is the correct single
    #   blister listing.
    '55-24': ('51.00', 'https://www.ebay.com/itm/175018174961', True),   # Chaplain Grimaldus

    # 97-08 Bloodletters — eBay price update to the verified listing.
    '97-08': ('39.95', 'https://www.ebay.com/itm/356317127568', True),   # Bloodletters

    # LESSON: 41-07 Death Company — eBay was returning wrong kit.
    #   366248667923 is the correct Death Company Marines listing.
    '41-07': ('39.95', 'https://www.ebay.com/itm/366248667923', True),   # Death Company Marines
}

# eBay listing to copy to 41-12 (Death Company with Jump Packs uses same eBay listing)
EBAY_41_12 = ('39.95', 'https://www.ebay.com/itm/366248667923', True)


# ===========================================================================
# PRICE DATA: GW corrections
# Format: gw_sku -> (price_str, url, in_stock, not_available)
# ===========================================================================
GW_FIXES = {
    # LESSON: 59-10 Skitarii Rangers — GW link pointed to "Aeldari Rangers"
    #   (an Eldar Pathfinder kit, completely different faction/product).
    #   The Skitarii Rangers are AdMech — correct URL contains "Skitarii-Rangers".
    #   Always verify faction and product name in the URL path match the product.
    '59-10': ('60.00', 'https://www.warhammer.com/en-US/shop/Skitarii-Rangers-2017', True, False),
}


# ===========================================================================
# PRICE DATA: Noble Knight corrections
# ===========================================================================
NK_FIXES = {
    # LESSON: 47-08 Commissar NK link — old NK link (2148070226) was for
    #   "The Commissar's Duty" (a novel/codex), not the miniature.
    #   Always check that the NK product page title contains the model name,
    #   not a book title.
    '47-08': ('35.95', 'https://www.nobleknight.com/P/2148037160/Commissar', True, False),  # Commissar
}

# Noble Knight listings to mark not_available (wrong product / out of stock):
NK_NOT_AVAILABLE = [
    # LESSON: 59-11 Skitarii Vanguard NK link — pointed to "Vanguard Veteran
    #   Squad" (a Space Marine product, completely different army).
    #   Removing until a correct AdMech Vanguard NK listing is found.
    '59-11',   # Skitarii Vanguard — wrong NK product
    # LESSON: 41-10 Baal Predator NK link — product is out of stock / delisted.
    '41-10',   # Baal Predator — no longer available at Noble Knight
]


# ===========================================================================
# PRODUCT IMAGE UPDATES
# Format: gw_sku -> new image_url
# These replace incorrect GW CDN thumbnail images with actual product photos.
# ===========================================================================
IMAGE_UPDATES = {
    # ── Blood Angels ──────────────────────────────────────────────────────
    # LESSON: 41-07 and 41-12 both had the Blood Angels Codex cover as their
    #   image (60030101063_EngBACodex01).  The correct image is the Death
    #   Company miniatures product photo.
    '41-07': IMG_41_07_GW,
    '41-12': IMG_41_07_GW,   # Death Company Jump Packs — use same image as Marines

    # ── Citadel Paints: use Amazon/eBay product photos ────────────────────
    # LESSON: GW's image CDN often returns tool/accessory images for paint
    #   products (e.g. a brush for Nuln Oil).  Amazon and eBay listings
    #   consistently show the actual paint pot/spray can.
    'BP-001':  IMG_BP001_AMAZON,   # Base Paint — Amazon image shows the pot
    'BS-001':  IMG_BS001_EBAY,     # Base Paint Set — eBay image shows the set box
    'CP-003':  IMG_CP003_AMAZON,   # Contrast Blood Angels Red — Amazon image
    'LP-001':  IMG_LP001_EBAY,     # Layer Paint — eBay image shows the pot
    'SP-020':  IMG_SP020_EBAY,     # Munitorum Varnish — eBay image shows the can
    'SP-002':  IMG_SP002_EBAY,     # Agrax Earthshade — eBay image shows the pot
    'SP-001':  IMG_SP001_AMAZON,   # Nuln Oil — Amazon image shows the pot
    'SP-003':  IMG_SP003_EBAY,     # Reikland Fleshshade — eBay image shows the pot
    'SP-010':  IMG_SP010_AMAZON,   # Chaos Black Spray — Amazon image shows the can
    'CSP-003': IMG_CSP003_EBAY,    # Corax White Spray — eBay image
    'CSP-004': IMG_CSP004_AMAZON,  # Zandri Dust Spray — Amazon image
    # SP-012 Grey Seer: user requested using the Wraithbone spray image
    # LESSON: Grey Seer and Wraithbone are both grey/bone coloured primers;
    #   the Wraithbone Amazon image is clearer/higher quality.
    'SP-012':  IMG_SP012_AMAZON,
    'TCP-001': IMG_TCP001_EBAY,    # Technical Paint — eBay image shows the pot
}


# ===========================================================================
# PRODUCT RENAME
# ===========================================================================
PRODUCT_RENAMES = {
    # LESSON: 41-07 was named "Blood Angels Death Company Marines" but GW
    #   and eBay sellers both list it simply as "Blood Angels Death Company".
    #   Shorter name matches search behaviour better.
    '41-07': {
        'name': 'Blood Angels Death Company',
        'slug': 'blood-angels-death-company',
    },
}


# ===========================================================================
# EBAY SEARCH NAME UPDATES
# These fix the ebay_search_name field so future eBay price refreshes find
# the correct listing.
# ===========================================================================
EBAY_SEARCH_NAME_UPDATES = {
    # LESSON: 47-30 Cadian Shock Troops — search was returning Cadian Command
    #   Squad.  Adding "Warhammer" prefix narrows results to the correct kit.
    '47-30': 'Warhammer Cadian Shock Troops',

    # LESSON: 47-08 Commissar — the generic search "Astra Militarum Commissar"
    #   was matching old metal codex supplements.  The correct term includes
    #   the faction name to avoid cross-faction confusion.
    '47-08': 'Astra Militarum Commissar',

    # LESSON: 55-24 Grimaldus — search term was too generic and matching other
    #   Black Templars characters.  Using "Chaplain Grimaldus" is specific
    #   enough to find only the correct blister.
    '55-24': 'Chaplain Grimaldus',
}


class Command(BaseCommand):
    """Apply March 2026 batch database corrections."""

    help = (
        'Apply all March 2026 batch DB corrections: '
        'deactivate SKUs, fix prices, update images. '
        'Idempotent — safe to re-run.'
    )

    def add_arguments(self, parser):
        """Add --dry-run flag."""
        parser.add_argument(
            '--dry-run',
            action='store_true',
            default=False,
            help='Print planned actions without writing to the database.',
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _get_product(self, gw_sku):
        """Return Product for gw_sku (including inactive), or None."""
        try:
            return Product.objects.get(gw_sku=gw_sku)
        except Product.DoesNotExist:
            return None

    def _set_price(self, product, retailer, price_str, url, in_stock,
                   not_available=False, dry_run=False):
        """Upsert a CurrentPrice row."""
        price = decimal.Decimal(price_str) if price_str else None
        action = 'dry' if dry_run else 'set'
        self.stdout.write(
            f'  [{action}] {product.gw_sku:8s}  {retailer.name:14s}  '
            f'{"$"+price_str if price_str else "—":>10s}  '
            f'{"NOT_AVAIL" if not_available else "IN_STOCK" if in_stock else "OUT_STOCK":9s}'
        )
        if not dry_run:
            CurrentPrice.objects.update_or_create(
                product=product,
                retailer=retailer,
                defaults={
                    'price'        : price,
                    'url'          : url,
                    'in_stock'     : in_stock,
                    'not_available': not_available,
                    'listing_title': '',
                },
            )

    def _mark_not_available(self, product, retailer, dry_run=False):
        """Mark an existing CurrentPrice as not_available, or create one."""
        action = 'dry' if dry_run else 'set'
        self.stdout.write(
            f'  [{action}] {product.gw_sku:8s}  {retailer.name:14s}  NOT_AVAIL'
        )
        if not dry_run:
            CurrentPrice.objects.update_or_create(
                product=product,
                retailer=retailer,
                defaults={
                    'price'        : None,
                    'url'          : '',
                    'in_stock'     : False,
                    'not_available': True,
                    'listing_title': '',
                },
            )

    # ------------------------------------------------------------------
    # Entry point
    # ------------------------------------------------------------------
    def handle(self, *args, **options):
        """Run all batch fixes."""
        dry_run = options['dry_run']
        prefix = '[DRY RUN] ' if dry_run else ''

        # ── Load retailers ─────────────────────────────────────────────
        try:
            r_amazon = Retailer.objects.get(name='Amazon')
            r_ebay   = Retailer.objects.get(name='eBay')
            r_gw     = Retailer.objects.get(name='Games Workshop')
            r_nk     = Retailer.objects.get(name__icontains='Noble Knight')
            r_mm     = Retailer.objects.get(name='Miniature Market')
        except Retailer.DoesNotExist as exc:
            raise CommandError(f'Retailer not found: {exc}') from exc

        all_retailers = [r_amazon, r_ebay, r_gw, r_nk, r_mm]

        # ==================================================================
        # SECTION 1: Deactivate duplicate / discontinued SKUs
        # ==================================================================
        self.stdout.write(self.style.MIGRATE_HEADING(
            f'\n{prefix}=== Section 1: Deactivate SKUs ==='))
        deactivated = 0
        for sku in DEACTIVATE_SKUS:
            product = self._get_product(sku)
            if not product:
                self.stdout.write(self.style.WARNING(
                    f'  [skip] {sku} — not found in DB'))
                continue
            if not product.is_active:
                self.stdout.write(f'  [skip] {sku} — already inactive')
                continue
            self.stdout.write(f'  [{"dry" if dry_run else "deactivate"}] '
                              f'{sku}  {product.name}')
            if not dry_run:
                product.is_active = False
                product.save(update_fields=['is_active'])
            deactivated += 1
        self.stdout.write(self.style.SUCCESS(
            f'{prefix}Deactivated: {deactivated}'))

        # ==================================================================
        # SECTION 2: Rename products
        # ==================================================================
        self.stdout.write(self.style.MIGRATE_HEADING(
            f'\n{prefix}=== Section 2: Rename products ==='))
        for sku, fields in PRODUCT_RENAMES.items():
            product = self._get_product(sku)
            if not product:
                self.stdout.write(self.style.WARNING(
                    f'  [skip] {sku} — not found'))
                continue
            self.stdout.write(
                f'  [{"dry" if dry_run else "rename"}] {sku}  '
                f'{product.name!r} -> {fields["name"]!r}')
            if not dry_run:
                for field, value in fields.items():
                    setattr(product, field, value)
                product.save(update_fields=list(fields.keys()))

        # ==================================================================
        # SECTION 3: Update eBay search names
        # ==================================================================
        self.stdout.write(self.style.MIGRATE_HEADING(
            f'\n{prefix}=== Section 3: Update eBay search names ==='))
        for sku, search_name in EBAY_SEARCH_NAME_UPDATES.items():
            product = self._get_product(sku)
            if not product:
                self.stdout.write(self.style.WARNING(
                    f'  [skip] {sku} — not found'))
                continue
            self.stdout.write(
                f'  [{"dry" if dry_run else "set"}] {sku}  '
                f'ebay_search_name -> {search_name!r}')
            if not dry_run:
                product.ebay_search_name = search_name
                product.save(update_fields=['ebay_search_name'])

        # ==================================================================
        # SECTION 4: Update product images
        # ==================================================================
        self.stdout.write(self.style.MIGRATE_HEADING(
            f'\n{prefix}=== Section 4: Update product images ==='))
        for sku, image_url in IMAGE_UPDATES.items():
            product = self._get_product(sku)
            if not product:
                self.stdout.write(self.style.WARNING(
                    f'  [skip] {sku} — not found'))
                continue
            self.stdout.write(
                f'  [{"dry" if dry_run else "set"}] {sku}  image_url -> '
                f'{image_url[:60]}...')
            if not dry_run:
                product.image_url = image_url
                product.save(update_fields=['image_url'])

        # ==================================================================
        # SECTION 5: Fix Amazon CurrentPrice entries
        # ==================================================================
        self.stdout.write(self.style.MIGRATE_HEADING(
            f'\n{prefix}=== Section 5: Fix Amazon prices ==='))
        for sku, (price_str, url, in_stock) in AMAZON_FIXES.items():
            product = self._get_product(sku)
            if not product:
                self.stdout.write(self.style.WARNING(
                    f'  [skip] {sku} — not found'))
                continue
            self._set_price(product, r_amazon, price_str, url, in_stock,
                            dry_run=dry_run)

        for sku in AMAZON_NOT_AVAILABLE:
            product = self._get_product(sku)
            if not product:
                self.stdout.write(self.style.WARNING(
                    f'  [skip] {sku} — not found'))
                continue
            self._mark_not_available(product, r_amazon, dry_run=dry_run)

        # ==================================================================
        # SECTION 6: Fix eBay CurrentPrice entries
        # ==================================================================
        self.stdout.write(self.style.MIGRATE_HEADING(
            f'\n{prefix}=== Section 6: Fix eBay prices ==='))
        for sku, (price_str, url, in_stock) in EBAY_FIXES.items():
            product = self._get_product(sku)
            if not product:
                self.stdout.write(self.style.WARNING(
                    f'  [skip] {sku} — not found'))
                continue
            self._set_price(product, r_ebay, price_str, url, in_stock,
                            dry_run=dry_run)

        # Copy 41-07 eBay listing to 41-12 (Death Company with Jump Packs)
        p_41_12 = self._get_product('41-12')
        if p_41_12:
            price_str, url, in_stock = EBAY_41_12
            self.stdout.write(
                f'  [{"dry" if dry_run else "set"}] 41-12  eBay  '
                f'(copy from 41-07 Death Company listing)')
            if not dry_run:
                CurrentPrice.objects.update_or_create(
                    product=p_41_12,
                    retailer=r_ebay,
                    defaults={
                        'price'        : decimal.Decimal(price_str),
                        'url'          : url,
                        'in_stock'     : in_stock,
                        'not_available': False,
                        'listing_title': '',
                    },
                )
        else:
            self.stdout.write(self.style.WARNING('  [skip] 41-12 — not found'))

        # ==================================================================
        # SECTION 7: Fix GW CurrentPrice entries
        # ==================================================================
        self.stdout.write(self.style.MIGRATE_HEADING(
            f'\n{prefix}=== Section 7: Fix GW prices ==='))
        for sku, (price_str, url, in_stock, not_avail) in GW_FIXES.items():
            product = self._get_product(sku)
            if not product:
                self.stdout.write(self.style.WARNING(
                    f'  [skip] {sku} — not found'))
                continue
            self._set_price(product, r_gw, price_str, url, in_stock,
                            not_available=not_avail, dry_run=dry_run)

        # ==================================================================
        # SECTION 8: Fix Noble Knight CurrentPrice entries
        # ==================================================================
        self.stdout.write(self.style.MIGRATE_HEADING(
            f'\n{prefix}=== Section 8: Fix Noble Knight prices ==='))
        for sku, (price_str, url, in_stock, not_avail) in NK_FIXES.items():
            product = self._get_product(sku)
            if not product:
                self.stdout.write(self.style.WARNING(
                    f'  [skip] {sku} — not found'))
                continue
            self._set_price(product, r_nk, price_str, url, in_stock,
                            not_available=not_avail, dry_run=dry_run)

        for sku in NK_NOT_AVAILABLE:
            product = self._get_product(sku)
            if not product:
                self.stdout.write(self.style.WARNING(
                    f'  [skip] {sku} — not found'))
                continue
            self._mark_not_available(product, r_nk, dry_run=dry_run)

        # ==================================================================
        # SECTION 9: Fix Astra Militarum Infantry Squad (47-19) 505 error
        #
        # LESSON: A product with zero CurrentPrice rows can cause a 505 error
        #   if the template or view code expects at least one price row.
        #   Always ensure every active product has at least a not_available=True
        #   row for each retailer so the page renders cleanly.
        # ==================================================================
        self.stdout.write(self.style.MIGRATE_HEADING(
            f'\n{prefix}=== Section 9: Fix 47-19 Infantry Squad 505 error ==='))
        p_47_19 = self._get_product('47-19')
        if p_47_19:
            for retailer in all_retailers:
                existing = CurrentPrice.objects.filter(
                    product=p_47_19, retailer=retailer).first()
                if existing:
                    self.stdout.write(
                        f'  [skip] 47-19  {retailer.name:14s} — row exists '
                        f'(not_avail={existing.not_available})')
                else:
                    self.stdout.write(
                        f'  [{"dry" if dry_run else "add"}] 47-19  '
                        f'{retailer.name:14s}  NOT_AVAIL (new row)')
                    if not dry_run:
                        CurrentPrice.objects.create(
                            product=p_47_19,
                            retailer=retailer,
                            price=None,
                            url='',
                            in_stock=False,
                            not_available=True,
                            listing_title='',
                        )
        else:
            self.stdout.write(self.style.WARNING('  [skip] 47-19 — not found'))

        # ==================================================================
        # SECTION 10: Copy GW link from 41-07 to 41-12
        #
        # Both "Death Company Marines" and "Death Company with Jump Packs"
        # link to the same GW product page (the kit builds both variants).
        # ==================================================================
        self.stdout.write(self.style.MIGRATE_HEADING(
            f'\n{prefix}=== Section 10: Copy 41-07 GW link -> 41-12 ==='))
        p_41_07 = self._get_product('41-07')
        p_41_12 = self._get_product('41-12')
        if p_41_07 and p_41_12:
            gw_41_07 = CurrentPrice.objects.filter(
                product=p_41_07, retailer=r_gw).first()
            if gw_41_07 and not gw_41_07.not_available:
                self.stdout.write(
                    f'  [{"dry" if dry_run else "copy"}] 41-07 GW '
                    f'-> 41-12  url={gw_41_07.url[:60]}')
                if not dry_run:
                    CurrentPrice.objects.update_or_create(
                        product=p_41_12,
                        retailer=r_gw,
                        defaults={
                            'price'        : gw_41_07.price,
                            'url'          : gw_41_07.url,
                            'in_stock'     : gw_41_07.in_stock,
                            'not_available': gw_41_07.not_available,
                            'listing_title': '',
                        },
                    )
            else:
                self.stdout.write('  [skip] 41-07 GW row not found or not_available')
        else:
            self.stdout.write(self.style.WARNING(
                '  [skip] 41-07 or 41-12 not found'))

        # ==================================================================
        # SECTION 11: Clear MSRP on products where GW shows "not available"
        #
        # LESSON: When the GW CurrentPrice row has not_available=True, the
        #   product template was still showing a discount % because msrp was
        #   set.  Setting msrp=None removes the discount calculation entirely.
        #   This only applies to paint products where GW does not sell
        #   individual pots — the msrp field should only be set when GW
        #   actively sells the product.
        # ==================================================================
        self.stdout.write(self.style.MIGRATE_HEADING(
            f'\n{prefix}=== Section 11: Clear MSRP for GW not-available products ==='))
        cleared = 0
        gw_not_avail_qs = CurrentPrice.objects.filter(
            retailer=r_gw,
            not_available=True,
        ).select_related('product')
        for cp in gw_not_avail_qs:
            product = cp.product
            if product.msrp is not None:
                self.stdout.write(
                    f'  [{"dry" if dry_run else "clear"}] {product.gw_sku:8s}  '
                    f'{product.name}  msrp {product.msrp} → None')
                if not dry_run:
                    product.msrp = None
                    product.save(update_fields=['msrp'])
                cleared += 1
        if cleared == 0:
            self.stdout.write('  [info] No products found with GW not_available + msrp set')
        else:
            self.stdout.write(self.style.SUCCESS(
                f'{prefix}Cleared MSRP: {cleared} products'))

        # ==================================================================
        # Done
        # ==================================================================
        self.stdout.write(self.style.SUCCESS(
            f'\n{prefix}=== All sections complete! ==='))
        if dry_run:
            self.stdout.write(self.style.WARNING(
                'Re-run without --dry-run to commit changes.'))
