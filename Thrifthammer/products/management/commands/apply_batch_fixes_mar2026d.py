"""
Management command: apply_batch_fixes_mar2026d

Fourth wave of March 2026 batch corrections for ThriftHammer.
Run after apply_batch_fixes_mar2026c.

Changes covered:
  Section 1  - Deactivate 14 SKUs
               (HA-011 Cataphractii + 13 Kill Team SKUs, keep KT-003 Starter Set)
  Section 2  - Fix Amazon prices (4 corrections + 1 not_available)
  Section 3  - Fix eBay prices (3 corrections)
  Section 4  - Noble Knight: update 73-06 URL (out of stock, correct link)
  Section 5  - Overhaul 73-06: rename to Leagues of Votann Einhyr Champion
               + new description
  Section 6  - Rename HA-010 to Horus Heresy MKIII Tactical Squad
  Section 7  - Fix 54-20 Armigers image (update to newer GW CDN URL)

Usage:
    python manage.py apply_batch_fixes_mar2026d
    python manage.py apply_batch_fixes_mar2026d --dry-run
"""

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Product, Retailer


# ===========================================================================
# PRODUCT IMAGE URLS
# ===========================================================================
# Armiger Warglaives — newer GW CDN listing image (confirmed in GW_IMAGES):
IMG_54_20_ARMIGERS = (
    'https://www.warhammer.com/app/resources/catalog/product/920x950/'
    '99120108049_ArmigerWarglaivesNEW01.jpg'
)


# ===========================================================================
# SKUs TO DEACTIVATE (is_active -> False)
# ===========================================================================
DEACTIVATE_SKUS = [
    # ── Horus Heresy — Cataphractii variant ───────────────────────────────
    # LESSON: HA-011 "Legiones Astartes Cataphractii Terminators" is a 2026
    #   re-release with combi-bolters & power fists, while HA-030 is the
    #   original 2022 kit with Volkite Chargers & Power Mauls.  Both cover
    #   effectively the same role.  User confirmed HA-011 should be
    #   deactivated; HA-030 remains as the canonical Cataphractii entry.
    'HA-011',

    # ── Kill Team — deactivate all except KT-003 (Starter Set) ───────────
    # LESSON: GW has discontinued or replaced most faction-specific Kill Team
    #   boxes and supplementary products from this era.  Keeping only
    #   KT-003 "Kill Team: Starter Set" which is still widely available.
    'KT-001',   # Kill Team: Nightmare
    'KT-002',   # Kill Team: Into the Dark
    'KT-100',   # Kill Team Starter Set (duplicate of KT-003)
    'KT-101',   # Kill Team: Operatives Datacard Pack 2024
    'KT-102',   # Kill Team: Void-Dancer Troupe
    'KT-103',   # Kill Team: Veteran Guardsmen
    'KT-104',   # Kill Team: Chaos Legionaries
    'KT-105',   # Kill Team: Intercession Squad
    'KT-106',   # Kill Team: Hunter Clade
    'KT-107',   # Kill Team: Exaction Squad
    'KT-108',   # Kill Team: Salvation
    'KT-109',   # Kill Team: Terrain – Killzone Essentials
    'KT-110',   # Kill Team: Compendium
]


# ===========================================================================
# AMAZON PRICE FIXES
# ===========================================================================
AMAZON_FIXES = {
    # LESSON: HA-041 Sicaran Battle Tank had ASIN B0F29RQ8JH at $68.00 —
    #   likely a wrong/unrelated product listing.  Correct ASIN confirmed by
    #   user: B0B8ZM7M3T (Games Workshop Legiones Astartes Sicaran Battle
    #   Tank) at $75.65.
    'HA-041': ('75.65', 'https://www.amazon.com/dp/B0B8ZM7M3T', True),

    # LESSON: HA-040 Spartan Assault Tank had ASIN B0F29NXG8C at $89.08 —
    #   wrong product.  Correct ASIN confirmed by user: B0B8ZNSRXZ (Games
    #   Workshop Legiones Astartes Spartan) at $101.30.  Note: HA-013
    #   "Legiones Astartes Spartan Assault Tank" already carries this correct
    #   ASIN; HA-040 "Horus Heresy Spartan Assault Tank" is now corrected to
    #   match.
    'HA-040': ('101.30', 'https://www.amazon.com/dp/B0B8ZNSRXZ', True),

    # LESSON: HA-010 MKIII Tactical Squad had ASIN B0D6RF8C3V at $45.05 —
    #   price far too low for a 20-model infantry kit; likely a wrong listing
    #   (small accessory or book).  Correct ASIN confirmed by user:
    #   B0CKRY88GB at $66.95.
    'HA-010': ('66.95', 'https://www.amazon.com/dp/B0CKRY88GB', True),

    # LESSON: 73-06 Einhyr Champion previously showed NOT_AVAIL on Amazon.
    #   Correct ASIN confirmed by user: B0BK9MJ83N (Leagues of Votann
    #   Einhyr Champion) at $36.00.
    '73-06': ('36.00', 'https://www.amazon.com/dp/B0BK9MJ83N', True),
}

# Products where Amazon does NOT stock the item.
AMAZON_NOT_AVAILABLE = [
    # LESSON: 54-15 Imperial Knight Preceptor/Canis Rex had ASIN B0FPDM6H37
    #   at $158.77 — user confirmed Amazon does not carry this product.
    #   The ASIN likely belongs to a third-party reseller or wrong listing.
    '54-15',
]


# ===========================================================================
# EBAY PRICE FIXES
# ===========================================================================
EBAY_FIXES = {
    # LESSON: 54-20 Armigers had eBay listing 276855413389 at $75.00 —
    #   outdated/incorrect listing.  Correct sealed listing confirmed by
    #   user: 376876899446 at $80.80.
    '54-20': ('80.80', 'https://www.ebay.com/itm/376876899446', True),

    # LESSON: 73-06 Einhyr Champion had no eBay listing (NOT_AVAIL).
    #   Correct sealed listing confirmed by user: 185635655254 at $36.98.
    '73-06': ('36.98', 'https://www.ebay.com/itm/185635655254', True),

    # LESSON: HA-010 MKIII Tactical Squad had no eBay listing (NOT_AVAIL).
    #   Correct sealed listing confirmed by user: 127407224531 at $68.00.
    'HA-010': ('68.00', 'https://www.ebay.com/itm/127407224531', True),
}


# ===========================================================================
# 73-06 EINHYR CHAMPION OVERHAUL
# LESSON: The product was stored as "Leagues of Votann Kahl / Uthar the
#   Destined" — wrong name.  The GW URL (lov-einhyr-champion-2022) and the
#   existing image (99120118012_EinhyrChampLead.jpg) already reference the
#   Einhyr Champion.  The product name, slug, and description are corrected
#   here.  All retailer links are also fixed (Section 2/3 handle Amazon/eBay;
#   Section 4 handles Noble Knight URL; MM remains not_available — no listing).
# ===========================================================================
EI_CHAMPION_NEW_NAME = 'Leagues of Votann Einhyr Champion'
EI_CHAMPION_NEW_SLUG = 'leagues-of-votann-einhyr-champion'
EI_CHAMPION_NEW_DESC = (
    'A heavily-armoured Leagues of Votann champion in exo-armour, wielding a '
    'crushing mass hammer or darkstar axe alongside an Autoch-pattern '
    'combi-bolter. Kit includes choice of crests, head options, and '
    'shield plate designs.'
)

# Noble Knight has the product but it is currently out of stock.
# Store the URL so it can be checked for restocks; flag not_available for now.
NK_73_06_URL = 'https://www.nobleknight.com/P/2148011890/Einhyr-Champion'


# ===========================================================================
# HA-010 RENAME
# LESSON: "Legiones Astartes MKIII Infantry Squad" is the GW-branded name
#   for the Horus Heresy box.  GW later updated the product listing title to
#   "MKIII Tactical Squad" — correcting here to match current GW naming.
# ===========================================================================
HA010_NEW_NAME = 'Horus Heresy MKIII Tactical Squad'
HA010_NEW_SLUG = 'horus-heresy-mkiii-tactical-squad'


class Command(BaseCommand):
    """Apply fourth wave of March 2026 batch database corrections."""

    help = (
        'Apply batch fixes wave D (March 2026): Kill Team deactivations, '
        'Amazon/eBay link corrections, Einhyr Champion rename, HA-010 rename, '
        'Armigers image fix.'
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
        # SECTION 4: Noble Knight — update 73-06 URL (out of stock)
        # ==================================================================
        self.stdout.write(self.style.MIGRATE_HEADING(
            f'\n{prefix}=== Section 4: Noble Knight 73-06 URL ==='))
        einhyr = self._get_product('73-06')
        if einhyr:
            self.stdout.write(
                f'  [{"dry" if dry_run else "set"}] 73-06     '
                f'Noble Knight Games     NOT_AVAIL (url updated)')
            if not dry_run:
                CurrentPrice.objects.update_or_create(
                    product=einhyr,
                    retailer=r_nk,
                    defaults={
                        'price': None,
                        'url': NK_73_06_URL,
                        'in_stock': False,
                        'not_available': True,
                        'listing_title': '',
                    },
                )

        # ==================================================================
        # SECTION 5: Overhaul 73-06 → Leagues of Votann Einhyr Champion
        # ==================================================================
        self.stdout.write(self.style.MIGRATE_HEADING(
            f'\n{prefix}=== Section 5: Overhaul 73-06 Einhyr Champion ==='))
        einhyr = self._get_product('73-06')
        if einhyr:
            self.stdout.write(
                f'  [{"dry" if dry_run else "rename"}] 73-06  '
                f"'{einhyr.name}' -> '{EI_CHAMPION_NEW_NAME}'")
            self.stdout.write(
                f'  [{"dry" if dry_run else "desc"}] 73-06  '
                f'description updated')
            if not dry_run:
                einhyr.name = EI_CHAMPION_NEW_NAME
                einhyr.slug = EI_CHAMPION_NEW_SLUG
                einhyr.description = EI_CHAMPION_NEW_DESC
                einhyr.save(update_fields=['name', 'slug', 'description'])
        else:
            self.stdout.write(self.style.WARNING('  [skip] 73-06 not found'))

        # ==================================================================
        # SECTION 6: Rename HA-010 → Horus Heresy MKIII Tactical Squad
        # ==================================================================
        self.stdout.write(self.style.MIGRATE_HEADING(
            f'\n{prefix}=== Section 6: Rename HA-010 MKIII Tactical Squad ==='))
        mkiii = self._get_product('HA-010')
        if mkiii:
            self.stdout.write(
                f'  [{"dry" if dry_run else "rename"}] HA-010  '
                f"'{mkiii.name}' -> '{HA010_NEW_NAME}'")
            if not dry_run:
                mkiii.name = HA010_NEW_NAME
                mkiii.slug = HA010_NEW_SLUG
                mkiii.save(update_fields=['name', 'slug'])
        else:
            self.stdout.write(self.style.WARNING('  [skip] HA-010 not found'))

        # ==================================================================
        # SECTION 7: Fix 54-20 Armigers image
        # ==================================================================
        self.stdout.write(self.style.MIGRATE_HEADING(
            f'\n{prefix}=== Section 7: Fix 54-20 Armigers image ==='))
        armigers = self._get_product('54-20')
        if armigers:
            self.stdout.write(
                f'  [{"dry" if dry_run else "image"}] 54-20  '
                f'image_url -> {IMG_54_20_ARMIGERS[:70]}...')
            if not dry_run:
                armigers.image_url = IMG_54_20_ARMIGERS
                armigers.save(update_fields=['image_url'])
        else:
            self.stdout.write(self.style.WARNING('  [skip] 54-20 not found'))

        self.stdout.write(self.style.SUCCESS(
            f'\n{prefix}=== All sections complete! ==='))
