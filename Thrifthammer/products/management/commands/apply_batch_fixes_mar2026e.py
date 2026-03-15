"""
Management command: apply_batch_fixes_mar2026e

Fifth wave of March 2026 batch corrections for ThriftHammer.
Run after apply_batch_fixes_mar2026d.

Changes covered:
  Section 1  - Deactivate 6 SKUs
               (HA-013 Spartan dupe, 87-06 Lumineth Wardens dupe, 97-09 Plaguebearers
                dupe, NM-001 Hive War, NM-020 Underhive Terrain, 91-10 Chainrasps dupe)
  Section 2  - Fix Amazon prices (7 corrections + 1 not_available)
               83-20 Plaguebearers B0746GFZYZ, 55-12 Calgar B0FX34N7PR,
               HA-001 MKVI B0CP673J8F, NM-010 Escher B0779NTT1V,
               49-12 Doomsday Ark B08HCL7SFY, 49-13 Doom Scythe B08GC4PD6K,
               91-28 Chainrasps B07FSWK3D7; 40-02 Leviathan → NOT_AVAIL
  Section 3  - Fix eBay prices (6 corrections)
               40-02 Leviathan 198178400236, NM-010 Escher 254617917411,
               NM-012 Van Saar 183426792302, 49-20 C'tan 254751542701,
               49-17 Flayed Ones 147157319311, 49-10 Immortals 183430315879
  Section 4  - Noble Knight: fix NM-011 Goliath Gang URL (out-of-stock correct link)
  Section 5  - Fix product images
               NM-010 Escher Gang → 99120599004_EscherGang02.jpg
               NM-011 Goliath Gang → 99120599003_GoliathGang02.jpg
               40-02 Leviathan    → 60010199057_Leviathan12.jpg
  Section 6  - Update Games Workshop retailer URLs
               NM-010, NM-011, NM-012 corrected to proper 2017/2018 GW store pages
  Section 7  - Product field updates
               55-12 Calgar: add 'JoyToy' to ebay_negative_keywords
               HA-001 MKVI: add '1:18' to ebay_negative_keywords
               49-20 C'tan: set ebay_search_name to avoid apostrophe in eBay search

Usage:
    python manage.py apply_batch_fixes_mar2026e
    python manage.py apply_batch_fixes_mar2026e --dry-run
"""

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Product, Retailer


# ===========================================================================
# PRODUCT IMAGE URLS (GW CDN — confirmed via live page + Wayback Machine CDX)
# ===========================================================================
# LESSON: NM-010 previously used 60630599012_HouseBladesDigi01.jpg which is
#   the digital supplement "House of Blades" — not the physical miniature kit.
IMG_NM010_ESCHER = (
    'https://www.warhammer.com/app/resources/catalog/product/920x950/'
    '99120599004_EscherGang02.jpg'
)

# LESSON: NM-011 previously used 60630599011_HouseofChains01.jpg which is
#   the "House of Chains" game supplement — not the Goliath miniature box.
IMG_NM011_GOLIATH = (
    'https://www.warhammer.com/app/resources/catalog/product/920x950/'
    '99120599003_GoliathGang02.jpg'
)

# LESSON: 40-02 Leviathan previously used 60010199071_ENGKTStarterSet1.jpg
#   which is the Kill Team Starter Set image — wrong product entirely.
#   Correct GW CDN filename confirmed via Wayback Machine CDX (archived 2023–2024).
IMG_40_02_LEVIATHAN = (
    'https://www.warhammer.com/app/resources/catalog/product/920x950/'
    '60010199057_Leviathan12.jpg'
)


# ===========================================================================
# SKUs TO DEACTIVATE (is_active -> False)
# ===========================================================================
DEACTIVATE_SKUS = [
    # ── Horus Heresy ─────────────────────────────────────────────────────────
    # LESSON: HA-013 "Legiones Astartes Spartan Assault Tank" is a duplicate
    #   of HA-040 "Horus Heresy Spartan Assault Tank".  HA-040 is the canonical
    #   entry (corrected in wave D); HA-013 is redundant.
    'HA-013',

    # ── Lumineth Realm-lords ──────────────────────────────────────────────────
    # LESSON: 87-06 "Lumineth Realm-lords Vanari Auralan Wardens (10)" is a
    #   duplicate of 87-10.  Both have the same Amazon ASIN B08HK4QRK7.  87-10
    #   is the canonical entry; 87-06 is removed.
    '87-06',

    # ── Maggotkin of Nurgle ───────────────────────────────────────────────────
    # LESSON: 97-09 "Maggotkin of Nurgle Plaguebearers" is a duplicate of
    #   83-20.  97-09 had a wrong Amazon ASIN (B09PF8BHJY at $17.00 — likely
    #   a cheap unrelated item).  83-20 is the canonical entry (fixed in
    #   Section 2); 97-09 is removed.
    '97-09',

    # ── Necromunda ────────────────────────────────────────────────────────────
    # LESSON: NM-001 "Necromunda: Hive War" had a completely wrong image
    #   (Tyranid Hive Guard).  The Hive War box set is also discontinued and
    #   unavailable at all tracked retailers.
    'NM-001',

    # LESSON: NM-020 "Necromunda Underhive Terrain Set" is a GW-exclusive
    #   terrain kit that is no longer widely available.  Deactivating to reduce
    #   clutter; can be reactivated if stock reappears.
    'NM-020',

    # ── Nighthaunt ────────────────────────────────────────────────────────────
    # LESSON: 91-10 "Nighthaunt Chainrasps" is a duplicate of 91-28.  The eBay
    #   CurrentPrice rows for both pointed at effectively the same listing.
    #   91-28 is the canonical entry (Amazon fixed in Section 2); 91-10 removed.
    '91-10',
]


# ===========================================================================
# AMAZON PRICE FIXES
# ===========================================================================
AMAZON_FIXES = {
    # LESSON: 83-20 Maggotkin of Nurgle Plaguebearers had no Amazon listing
    #   (NOT_AVAIL).  Correct ASIN confirmed by user: B0746GFZYZ at $36.98.
    '83-20': ('36.98', 'https://www.amazon.com/dp/B0746GFZYZ', True),

    # LESSON: 55-12 Marneus Calgar had ASIN B0F5GGH8LH at $69.29 — likely a
    #   wrong or superseded listing.  Correct ASIN confirmed by user:
    #   B0FX34N7PR.  Price carried forward from previous entry ($69.29).
    '55-12': ('69.29', 'https://www.amazon.com/dp/B0FX34N7PR', True),

    # LESSON: HA-001 MKVI Tactical Squad had ASIN B0CWBVGDKG at $44.00 —
    #   wrong listing (possibly a different Heresy kit or accessories bundle).
    #   Correct ASIN confirmed by user: B0CP673J8F.  Price carried forward.
    'HA-001': ('44.00', 'https://www.amazon.com/dp/B0CP673J8F', True),

    # LESSON: NM-010 Escher Gang had ASIN B0BNJ3ZHVR at $19.99 — that ASIN is
    #   the Necromunda: Escher Gang DICE SET, not the miniature box.  Correct
    #   ASIN confirmed by user: B0779NTT1V (Escher Gang miniature kit) at $45.05
    #   (confirmed via Amazon live check, March 2026).
    'NM-010': ('45.05', 'https://www.amazon.com/dp/B0779NTT1V', True),

    # LESSON: 49-12 Doomsday Ark had ASIN B0FNN67JTJ at $18.00 — clearly wrong
    #   (no Necron vehicle kit costs $18; likely a cheap card/token product).
    #   Correct ASIN confirmed by user: B08HCL7SFY at $58.65 (confirmed via
    #   Amazon live check, March 2026).  Note: Amazon may show this as "Ghost
    #   Ark" — it is a dual-build kit (Ghost Ark / Doomsday Ark) so the ASIN
    #   covers both variants.
    '49-12': ('58.65', 'https://www.amazon.com/dp/B08HCL7SFY', True),

    # LESSON: 49-13 Doom Scythe had no Amazon listing (NOT_AVAIL).  Correct
    #   ASIN confirmed by user: B08GC4PD6K at $65.45.
    '49-13': ('65.45', 'https://www.amazon.com/dp/B08GC4PD6K', True),

    # LESSON: 91-28 Nighthaunt Chainrasps (canonical entry) had no Amazon
    #   listing (NOT_AVAIL).  Correct ASIN confirmed by user: B07FSWK3D7
    #   (Nighthaunt Chainrasp Hordes) at $40.80 (confirmed March 2026; 5 left
    #   in stock).
    '91-28': ('40.80', 'https://www.amazon.com/dp/B07FSWK3D7', True),
}

# Products where Amazon does NOT stock the item.
AMAZON_NOT_AVAILABLE = [
    # LESSON: 40-02 Leviathan (10th Edition Starter Set) was a 2023 limited
    #   launch box.  The previous ASIN B0B8ZP1BDL appears to belong to a
    #   different product (GW no longer sells Leviathan on Amazon).  User
    #   confirmed Amazon does not carry this SKU.
    '40-02',
]


# ===========================================================================
# EBAY PRICE FIXES
# ===========================================================================
EBAY_FIXES = {
    # LESSON: 40-02 Leviathan had no eBay listing (NOT_AVAIL).  Correct sealed
    #   listing confirmed by user: 198178400236 (Games Workshop Warhammer 40K
    #   Leviathan Box Set NEW) at $399.99 (confirmed March 2026).
    '40-02': ('399.99', 'https://www.ebay.com/itm/198178400236', True),

    # LESSON: NM-010 Escher Gang had eBay listing at $22.95 — outdated/wrong
    #   listing.  Correct sealed listing confirmed by user: 254617917411 at
    #   $45.05 (confirmed March 2026; seller FlipSide Gaming).
    'NM-010': ('45.05', 'https://www.ebay.com/itm/254617917411', True),

    # LESSON: NM-012 Van Saar Gang eBay listing confirmed by user:
    #   183426792302 at $45.05 (confirmed March 2026; seller FlipSide Gaming).
    'NM-012': ('45.05', 'https://www.ebay.com/itm/183426792302', True),

    # LESSON: 49-20 Necron C'tan Shard of the Void Dragon had eBay at $49.99 —
    #   far too low for a £100+ centrepiece model (MSRP ~$130).  Correct sealed
    #   listing confirmed by user: 254751542701 at $110.50 (confirmed March 2026;
    #   114 sold, trending).
    '49-20': ('110.50', 'https://www.ebay.com/itm/254751542701', True),

    # LESSON: 49-17 Necron Flayed Ones had eBay at $35.00 — wrong listing.
    #   Correct sealed listing confirmed by user: 147157319311 at $51.00.
    '49-17': ('51.00', 'https://www.ebay.com/itm/147157319311', True),

    # LESSON: 49-10 Necron Immortals had eBay at $34.90 — wrong listing.
    #   Correct sealed listing confirmed by user: 183430315879 at $40.80
    #   (confirmed March 2026; seller FlipSide Gaming).
    '49-10': ('40.80', 'https://www.ebay.com/itm/183430315879', True),
}


# ===========================================================================
# NOBLE KNIGHT URL FIX
# ===========================================================================
# LESSON: NM-011 Goliath Gang had Noble Knight link pointing to
#   /P/2147682885/Goliath-Gang-Dice-Set-8 — a Dice Set, not the miniature
#   box.  Correct (out-of-stock) product page: /P/2147682879/Goliath-Gang.
NK_NM011_URL = 'https://www.nobleknight.com/P/2147682879/Goliath-Gang'


# ===========================================================================
# GAMES WORKSHOP RETAILER URL UPDATES
# ===========================================================================
# LESSON: NM-010 / NM-011 / NM-012 GW URLs were either stale or missing.
#   The canonical 2017/2018 GW product pages are used here.  These pages
#   remain live and are the authoritative GW listings for these gang boxes.
GW_URL_FIXES = {
    'NM-010': 'https://www.warhammer.com/en-WW/shop/Necromunda-Escher-Gang-2017',
    'NM-011': 'https://www.warhammer.com/en-WW/shop/Necromunda-Goliath-Gang-2017',
    'NM-012': 'https://www.warhammer.com/en-US/shop/Necromunda-Van-Saar-Gang-2018',
}


# ===========================================================================
# PRODUCT IMAGE URL MAP (Section 5)
# ===========================================================================
IMAGE_FIXES = {
    'NM-010': IMG_NM010_ESCHER,
    'NM-011': IMG_NM011_GOLIATH,
    '40-02':  IMG_40_02_LEVIATHAN,
}


# ===========================================================================
# EBAY NEGATIVE KEYWORDS (appended to Product.ebay_negative_keywords)
# ===========================================================================
# LESSON: 55-12 Marneus Calgar eBay searches surface JoyToy 1:18-scale action
#   figures (brand "JoyToy") that share the character name.  Excluding "JoyToy"
#   at the eBay query level prevents these from reaching our validator.
# LESSON: HA-001 MKVI Tactical Squad eBay searches surface JoyToy / third-party
#   1:18-scale action figures.  Excluding "1:18" filters these out without
#   being overly broad.
EBAY_NEG_KW_ADDITIONS = {
    '55-12':  'JoyToy',
    'HA-001': '1:18',
}

# ===========================================================================
# EBAY SEARCH NAME OVERRIDE (Section 7)
# ===========================================================================
# LESSON: 49-20 "Necron C'tan Shard of the Void Dragon" — the C'tan name uses
#   a Unicode right-single-quotation-mark (U+2019) which can break eBay search
#   URL encoding and return 0 results.  Override the eBay search query to use
#   a plain-ASCII equivalent with no apostrophe.
EBAY_SEARCH_NAME_FIXES = {
    '49-20': 'Necron Ctan Shard Void Dragon',
}


class Command(BaseCommand):
    """Apply fifth wave of March 2026 batch database corrections."""

    help = (
        'Apply batch fixes wave E (March 2026): 6 deactivations, '
        'Amazon/eBay link corrections, NK URL fix, image fixes, '
        'GW URL updates, ebay_negative_keywords, C\'tan search name fix.'
    )

    def add_arguments(self, parser):
        """Add --dry-run flag."""
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Preview changes without writing to the database.',
        )

    # -----------------------------------------------------------------------
    # Helper methods
    # -----------------------------------------------------------------------

    def _get_product(self, gw_sku):
        """Return Product for *gw_sku* (including inactive), or None."""
        try:
            return Product.objects.get(gw_sku=gw_sku)
        except Product.DoesNotExist:
            self.stdout.write(self.style.WARNING(
                f'  [warn] SKU {gw_sku} not found in DB'))
            return None

    def _set_price(self, product, retailer, price_str, url, in_stock,
                   *, dry_run):
        """Create or update a CurrentPrice row."""
        status = 'IN_STOCK' if in_stock else 'NOT_IN_STOCK'
        self.stdout.write(
            f'  [{"dry" if dry_run else "set"}] {product.gw_sku:<10}'
            f'{retailer.name[:22]:<22} ${price_str:<10} {status}')
        if not dry_run:
            CurrentPrice.objects.update_or_create(
                product=product,
                retailer=retailer,
                defaults={
                    'price': price_str,
                    'url': url,
                    'in_stock': in_stock,
                    'not_available': False,
                    'listing_title': '',
                },
            )

    def _mark_not_available(self, product, retailer, *, dry_run, url=''):
        """Mark a retailer's CurrentPrice as not_available.

        Pass *url* to store the retailer page URL even when the product is
        not currently available (e.g. temporarily out of stock at NK).
        """
        self.stdout.write(
            f'  [{"dry" if dry_run else "set"}] {product.gw_sku:<10}'
            f'{retailer.name[:22]:<22} NOT_AVAIL')
        if not dry_run:
            CurrentPrice.objects.update_or_create(
                product=product,
                retailer=retailer,
                defaults={
                    'price': None,
                    'url': url,
                    'in_stock': False,
                    'not_available': True,
                    'listing_title': '',
                },
            )

    def _update_retailer_url(self, product, retailer, new_url, *, dry_run):
        """Update only the URL field of an existing CurrentPrice row.

        If no row exists yet, creates one with NOT_AVAIL defaults so the URL
        is stored for future use.
        """
        self.stdout.write(
            f'  [{"dry" if dry_run else "url"}] {product.gw_sku:<10}'
            f'{retailer.name[:22]:<22} URL → {new_url[:55]}')
        if not dry_run:
            updated = CurrentPrice.objects.filter(
                product=product, retailer=retailer
            ).update(url=new_url)
            if not updated:
                # Row didn't exist — create it with the URL stored but
                # marked not_available so it shows up in future scrapes.
                CurrentPrice.objects.create(
                    product=product,
                    retailer=retailer,
                    url=new_url,
                    price=None,
                    in_stock=False,
                    not_available=True,
                    listing_title='',
                )

    # -----------------------------------------------------------------------
    # Main handler
    # -----------------------------------------------------------------------

    def handle(self, *args, **options):
        """Execute all batch fixes."""
        dry_run = options['dry_run']
        prefix = '[DRY RUN] ' if dry_run else ''

        # ------------------------------------------------------------------
        # Fetch retailer objects once
        # ------------------------------------------------------------------
        r_amazon = Retailer.objects.get(name='Amazon')
        r_ebay = Retailer.objects.get(name='eBay')
        r_nk = Retailer.objects.get(name__icontains='Noble Knight')
        r_gw = Retailer.objects.get(name='Games Workshop')

        # ==================================================================
        # SECTION 1: Deactivate SKUs
        # ==================================================================
        self.stdout.write(self.style.MIGRATE_HEADING(
            f'\n{prefix}=== Section 1: Deactivate SKUs ==='))
        deactivated = 0
        for sku in DEACTIVATE_SKUS:
            product = self._get_product(sku)
            if product is None:
                continue
            if not product.is_active:
                self.stdout.write(f'  [skip] {sku} — already inactive')
                continue
            self.stdout.write(
                f'  [{"dry" if dry_run else "deact"}] {sku}  {product.name}')
            if not dry_run:
                product.is_active = False
                product.save(update_fields=['is_active'])
            deactivated += 1

        self.stdout.write(self.style.SUCCESS(
            f'{prefix}Deactivated: {deactivated}'))

        # ==================================================================
        # SECTION 2: Fix Amazon prices
        # ==================================================================
        self.stdout.write(self.style.MIGRATE_HEADING(
            f'\n{prefix}=== Section 2: Fix Amazon prices ==='))
        for sku, (price_str, url, in_stock) in AMAZON_FIXES.items():
            product = self._get_product(sku)
            if product:
                self._set_price(product, r_amazon, price_str, url, in_stock,
                                dry_run=dry_run)

        self.stdout.write('  --- Amazon not_available ---')
        for sku in AMAZON_NOT_AVAILABLE:
            product = self._get_product(sku)
            if product:
                self._mark_not_available(product, r_amazon, dry_run=dry_run)

        # ==================================================================
        # SECTION 3: Fix eBay prices
        # ==================================================================
        self.stdout.write(self.style.MIGRATE_HEADING(
            f'\n{prefix}=== Section 3: Fix eBay prices ==='))
        for sku, (price_str, url, in_stock) in EBAY_FIXES.items():
            product = self._get_product(sku)
            if product:
                self._set_price(product, r_ebay, price_str, url, in_stock,
                                dry_run=dry_run)

        # ==================================================================
        # SECTION 4: Noble Knight — fix NM-011 Goliath Gang URL
        # ==================================================================
        self.stdout.write(self.style.MIGRATE_HEADING(
            f'\n{prefix}=== Section 4: Noble Knight NM-011 URL ==='))
        goliath = self._get_product('NM-011')
        if goliath:
            self.stdout.write(
                f'  [{"dry" if dry_run else "set"}] NM-011    '
                f'Noble Knight Games     NOT_AVAIL (url corrected)')
            if not dry_run:
                CurrentPrice.objects.update_or_create(
                    product=goliath,
                    retailer=r_nk,
                    defaults={
                        'price': None,
                        'url': NK_NM011_URL,
                        'in_stock': False,
                        'not_available': True,
                        'listing_title': '',
                    },
                )

        # ==================================================================
        # SECTION 5: Fix product images
        # ==================================================================
        self.stdout.write(self.style.MIGRATE_HEADING(
            f'\n{prefix}=== Section 5: Fix product images ==='))
        for sku, new_img in IMAGE_FIXES.items():
            product = self._get_product(sku)
            if product:
                old_img = (product.image_url or '')[-55:]
                self.stdout.write(
                    f'  [{"dry" if dry_run else "image"}] {sku:<10}'
                    f'...{old_img}')
                self.stdout.write(
                    f'             → ...{new_img[-55:]}')
                if not dry_run:
                    product.image_url = new_img
                    product.save(update_fields=['image_url'])

        # ==================================================================
        # SECTION 6: Update Games Workshop retailer URLs
        # ==================================================================
        self.stdout.write(self.style.MIGRATE_HEADING(
            f'\n{prefix}=== Section 6: Update GW retailer URLs ==='))
        for sku, new_url in GW_URL_FIXES.items():
            product = self._get_product(sku)
            if product:
                self._update_retailer_url(product, r_gw, new_url,
                                          dry_run=dry_run)

        # ==================================================================
        # SECTION 7: Product field updates
        #   a) ebay_negative_keywords — append keyword if not already present
        #   b) ebay_search_name — override for C'tan apostrophe fix
        # ==================================================================
        self.stdout.write(self.style.MIGRATE_HEADING(
            f'\n{prefix}=== Section 7: Product field updates ==='))

        # a) ebay_negative_keywords
        for sku, kw in EBAY_NEG_KW_ADDITIONS.items():
            product = self._get_product(sku)
            if product is None:
                continue
            existing = (product.ebay_negative_keywords or '').strip()
            # Idempotent: only append if the keyword isn't already present
            kw_lower = kw.lower()
            if kw_lower in existing.lower():
                self.stdout.write(
                    f'  [skip] {sku} neg_kw "{kw}" already set')
                continue
            new_val = f'{existing} {kw}'.strip() if existing else kw
            self.stdout.write(
                f'  [{"dry" if dry_run else "neg_kw"}] {sku:<10}'
                f'ebay_negative_keywords → "{new_val}"')
            if not dry_run:
                product.ebay_negative_keywords = new_val
                product.save(update_fields=['ebay_negative_keywords'])

        # b) ebay_search_name overrides
        for sku, search_name in EBAY_SEARCH_NAME_FIXES.items():
            product = self._get_product(sku)
            if product is None:
                continue
            existing = (product.ebay_search_name or '').strip()
            if existing == search_name:
                self.stdout.write(
                    f'  [skip] {sku} ebay_search_name already correct')
                continue
            self.stdout.write(
                f'  [{"dry" if dry_run else "srch"}] {sku:<10}'
                f'ebay_search_name → "{search_name}"')
            if not dry_run:
                product.ebay_search_name = search_name
                product.save(update_fields=['ebay_search_name'])

        self.stdout.write(self.style.SUCCESS(
            f'\n{prefix}=== All sections complete! ==='))
