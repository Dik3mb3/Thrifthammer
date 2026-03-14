"""
Management command: apply_batch_fixes_mar2026b

Second wave of March 2026 batch corrections for ThriftHammer.
Run after apply_batch_fixes_mar2026.

Changes covered:
  Section 1  - Deactivate 10 SKUs (Deathwing Terminator, Ravenwing Darkshroud,
               and all Deathwatch except Watch Master)
  Section 2  - Fix Amazon prices (7 corrections + 2 not_available)
  Section 3  - Fix Noble Knight prices (3 not_available)
  Section 4  - Fix eBay prices (2 corrections)
  Section 5  - Fix Miniature Market prices (1 correction)

Usage:
    python manage.py apply_batch_fixes_mar2026b
    python manage.py apply_batch_fixes_mar2026b --dry-run
"""

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Product, Retailer


# ===========================================================================
# SKUs TO DEACTIVATE (is_active -> False)
# ===========================================================================
DEACTIVATE_SKUS = [
    # ── Dark Angels — discontinued / consolidated kits ────────────────────
    # LESSON: 44-11 Deathwing Terminator Squad shares the same physical kit
    #   as the Space Marines Terminator Squad (SM-xxx). No need for a
    #   DA-specific entry; deactivate the duplicate.
    '44-11',   # Dark Angels Deathwing Terminator Squad — duplicate of SM kit
    # LESSON: 44-15 Ravenwing Darkshroud shares the kit with 44-14 Ravenwing
    #   Dark Talon. Two active SKUs for one box is confusing; keep Dark Talon.
    '44-15',   # Dark Angels Ravenwing Darkshroud — same kit as Dark Talon (44-14)

    # ── Deathwatch — faction discontinued from GW catalogue ─────────────
    # LESSON: GW has discontinued the standalone Deathwatch faction range.
    #   Deactivate all Deathwatch SKUs except the Watch Master (39-02) which
    #   is still sold and widely listed by third-party retailers.
    '39-03',   # Deathwatch Decimus Kill Team
    '39-05',   # Deathwatch Terminator Squad
    '39-06',   # Deathwatch Veteran Squad
    '39-07',   # Deathwatch Fortis Kill Team
    '39-08',   # Deathwatch Indomitor Kill Team
    '39-09',   # Deathwatch Spectrus Kill Team
    '39-10',   # Deathwatch Kill Team
    '39-11',   # Deathwatch Talonstrike Kill Team
]


# ===========================================================================
# AMAZON PRICE FIXES
# ===========================================================================
AMAZON_FIXES = {
    # LESSON: HA-002 Contemptor Dreadnought had the wrong ASIN (B0CRH15FDS).
    #   Correct ASIN from GW product page is B0B8ZMZ99L at $55.25.
    'HA-002': ('55.25', 'https://www.amazon.com/dp/B0B8ZMZ99L', True),

    # LESSON: 46-25 Craftworlds Combat Patrol had the right ASIN (B0DYFB9D4G)
    #   but empty price and in_stock=False. Price is $136.00.
    '46-25': ('136.00', 'https://www.amazon.com/dp/B0DYFB9D4G', True),

    # LESSON: 46-02 Craftworlds Farseer had a wrong ASIN (B09WNGQTBT) and
    #   empty price. Correct ASIN is B0B2X2C51V — the 2013 edition Farseer.
    '46-02': ('29.75', 'https://www.amazon.com/dp/B0B2X2C51V', True),

    # LESSON: 46-14 Craftworlds Fire Dragons had ASIN B0D3CPJRSC at $7.99
    #   which was a paint pot or similar — completely wrong. Correct listing
    #   is B0DV41T8NQ (Aeldari Fire Dragons) at $53.11.
    '46-14': ('53.11', 'https://www.amazon.com/dp/B0DV41T8NQ', True),

    # LESSON: 44-20 Dark Angels Combat Patrol had ASIN B0F53YP53G at $40.95
    #   which is wrong. Correct ASIN is B0CVXCZ5YL at $136.00.
    #   Note: Amazon price estimated based on comparable Combat Patrols; verify.
    '44-20': ('136.00', 'https://www.amazon.com/dp/B0CVXCZ5YL', True),

    # LESSON: 44-06 Dark Angels Lion El'Jonson had ASIN B0CKPSLCQ4 at $155.99
    #   which is incorrect. Correct ASIN is B0CB1BFQCZ at $62.48.
    '44-06': ('62.48', 'https://www.amazon.com/dp/B0CB1BFQCZ', True),

    # LESSON: 44-12 Dark Angels Ravenwing Black Knights had ASIN B0CVXP43B1
    #   at $39.95 — same ASIN as 44-05 Belial, so clearly wrong.
    #   Correct ASIN is B00AYUGFZ0 (Ravenwing Command Squad) at $55.25.
    '44-12': ('55.25', 'https://www.amazon.com/dp/B00AYUGFZ0', True),
}

# Products where Amazon does NOT sell the product — mark not_available.
AMAZON_NOT_AVAILABLE = [
    # LESSON: 44-02 Ezekiel had ASIN B01MTF7TGE at $9.99 — the $9.99 price
    #   suggests it was a digital product or incorrect listing. Amazon does
    #   not carry this character model. Mark not_available.
    '44-02',   # Dark Angels Ezekiel

    # LESSON: 44-16 Land Speeder Vengeance had ASIN B0CVXCZ5YL at $133 —
    #   that ASIN is actually the Dark Angels Combat Patrol (now on 44-20).
    #   The Land Speeder Vengeance is not sold on Amazon. Mark not_available.
    '44-16',   # Dark Angels Land Speeder Vengeance
]


# ===========================================================================
# NOBLE KNIGHT PRICE FIXES (not_available)
# ===========================================================================
# LESSON: These Noble Knight links point to the wrong products entirely:
#   46-02 Farseer -> Farseer Skyrunner (different variant)
#   46-14 Fire Dragons -> Fire Warriors (Tau product — completely wrong faction)
#   44-10 Deathwing Knights -> Deathwing Command Squad (older product)
# Mark all three not_available until correct NKG links are found.
NK_NOT_AVAILABLE = [
    '46-02',   # Craftworlds Farseer
    '46-14',   # Craftworlds Fire Dragons
    '44-10',   # Dark Angels Deathwing Knights
]


# ===========================================================================
# EBAY PRICE FIXES
# ===========================================================================
EBAY_FIXES = {
    # LESSON: 44-13 Inner Circle Companions eBay scraper found listing
    #   404856927887 at $26.50 — this is a used/incomplete listing.
    #   The correct sealed listing is 176254333774 at $51.00.
    '44-13': ('51.00', 'https://www.ebay.com/itm/176254333774', True),

    # LESSON: 44-16 Land Speeder Vengeance had no eBay listing found (scraper
    #   returned NOT_AVAIL). Correct listing is 174202381018 at $77.90.
    '44-16': ('77.90', 'https://www.ebay.com/itm/174202381018', True),
}


# ===========================================================================
# MINIATURE MARKET PRICE FIXES
# ===========================================================================
MM_FIXES = {
    # LESSON: 39-02 Watch Master had MM link gw-39-02.html at $8.99 which is
    #   a wrong product (too cheap for a miniature). Correct link is
    #   gw-39-14.html at $31.99 (Deathwatch Watch Master).
    '39-02': ('31.99', 'https://www.miniaturemarket.com/gw-39-14.html', True),
}


class Command(BaseCommand):
    """Apply second wave of March 2026 batch database corrections."""

    help = 'Apply batch fixes wave B (March 2026): deactivations, price/link corrections.'

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
        """Return the Product for *gw_sku*, or None with a warning."""
        try:
            return Product.objects.get(gw_sku=gw_sku)
        except Product.DoesNotExist:
            self.stdout.write(self.style.WARNING(f'  [warn] SKU {gw_sku} not found in DB'))
            return None

    def _set_price(self, product, retailer, price_str, url, in_stock, *, dry_run):
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

    def _mark_not_available(self, product, retailer, *, dry_run):
        """Mark a retailer's CurrentPrice for this product as not_available."""
        self.stdout.write(
            f'  [{"dry" if dry_run else "set"}] {product.gw_sku:<10}'
            f'{retailer.name[:22]:<22} NOT_AVAIL')
        if not dry_run:
            CurrentPrice.objects.update_or_create(
                product=product,
                retailer=retailer,
                defaults={
                    'price': None,
                    'url': '',
                    'in_stock': False,
                    'not_available': True,
                    'listing_title': '',
                },
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
        r_gw = Retailer.objects.get(name='Games Workshop')
        r_nk = Retailer.objects.get(name__icontains='Noble Knight')
        r_mm = Retailer.objects.get(name='Miniature Market')

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
                f'  [{"dry" if dry_run else "deact"}] {sku}  '
                f'{product.name}')
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

        self.stdout.write(f'  --- Amazon not_available ---')
        for sku in AMAZON_NOT_AVAILABLE:
            product = self._get_product(sku)
            if product:
                self._mark_not_available(product, r_amazon, dry_run=dry_run)

        # ==================================================================
        # SECTION 3: Fix Noble Knight prices (not_available)
        # ==================================================================
        self.stdout.write(self.style.MIGRATE_HEADING(
            f'\n{prefix}=== Section 3: Fix Noble Knight prices ==='))
        for sku in NK_NOT_AVAILABLE:
            product = self._get_product(sku)
            if product:
                self._mark_not_available(product, r_nk, dry_run=dry_run)

        # ==================================================================
        # SECTION 4: Fix eBay prices
        # ==================================================================
        self.stdout.write(self.style.MIGRATE_HEADING(
            f'\n{prefix}=== Section 4: Fix eBay prices ==='))
        for sku, (price_str, url, in_stock) in EBAY_FIXES.items():
            product = self._get_product(sku)
            if product:
                self._set_price(product, r_ebay, price_str, url, in_stock,
                                dry_run=dry_run)

        # ==================================================================
        # SECTION 5: Fix Miniature Market prices
        # ==================================================================
        self.stdout.write(self.style.MIGRATE_HEADING(
            f'\n{prefix}=== Section 5: Fix Miniature Market prices ==='))
        for sku, (price_str, url, in_stock) in MM_FIXES.items():
            product = self._get_product(sku)
            if product:
                self._set_price(product, r_mm, price_str, url, in_stock,
                                dry_run=dry_run)

        self.stdout.write(self.style.SUCCESS(
            f'\n{prefix}=== All sections complete! ==='))
