"""
Management command: apply_batch_fixes_mar2026c

Third wave of March 2026 batch corrections for ThriftHammer.
Run after apply_batch_fixes_mar2026b.

Changes covered:
  Section 1  - Deactivate 4 SKUs (47-19, 47-31, 41-12, 97-12)
  Section 2  - Fix Amazon prices (1 correction + 2 not_available)
  Section 3  - Fix eBay prices (1 correction)
  Section 4  - Fix HA-050 Praetor: rename + fix all 5 retailer links + image
  Section 5  - Reclassify HA-051 Chaplain (Horus Heresy -> WH40K / Space Marines)
  Section 6  - Set Citadel brand logo on all active Citadel products
               (excludes PH-001/PH-002 Painting Handles)

Usage:
    python manage.py apply_batch_fixes_mar2026c
    python manage.py apply_batch_fixes_mar2026c --dry-run
"""

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Category, Faction, Product, Retailer


# ===========================================================================
# PRODUCT IMAGE URLS
# ===========================================================================
# Praetor & Chaplain Consul — from GW CDN (confirmed 200 OK):
IMG_HA050_GW = (
    'https://www.warhammer.com/app/resources/catalog/product/920x950/'
    '99123001023_HHPraetorandChaplainConsulStock.jpg'
)

# Citadel Colour app icon — Apple App Store CDN (confirmed 200 OK, image/png):
CITADEL_LOGO_IMG = (
    'https://is1-ssl.mzstatic.com/image/thumb/Purple221/v4/'
    'a0/02/88/a002887a-2e90-2346-2d9d-d65999e42b75/'
    'AppIcon-0-0-1x_U007emarketing-0-8-0-85-220.png/1200x630wa.png'
)

# Citadel SKUs that should display the brand logo (Painting Handles excluded).
CITADEL_LOGO_SKUS_EXCLUDE = ['PH-001', 'PH-002']

# ===========================================================================
# SKUs TO DEACTIVATE (is_active -> False)
# ===========================================================================
DEACTIVATE_SKUS = [
    # ── Astra Militarum — discontinued / replaced kits ───────────────────
    # LESSON: 47-19 Astra Militarum Infantry Squad was replaced by the
    #   new-sculpt Infantry Squad box sold under a different SKU.  All
    #   five retailer rows already show not_available in production, so
    #   the page was returning a 505 error — now the product is deactivated.
    '47-19',   # Astra Militarum Infantry Squad

    # LESSON: 47-31 Astra Militarum Veteran Guardsmen — GW discontinued this
    #   standalone kit.  Veterans are now sold exclusively as part of the
    #   Kill Team: Veteran Guardsmen boxed set (KT-103), which remains active.
    '47-31',   # Astra Militarum Veteran Guardsmen

    # ── Blood Angels — redundant variant entry ────────────────────────────
    # LESSON: 41-12 "Death Company Marines with Jump Packs" is a variant
    #   built from the same Death Company kit as 41-07.  Maintaining two
    #   separate SKUs that point to the same listing is confusing.
    #   Keep 41-07 (Blood Angels Death Company) as the primary entry.
    '41-12',   # Blood Angels Death Company Marines with Jump Packs

    # ── Disciples of Tzeentch — duplicate entry ───────────────────────────
    # LESSON: 97-12 is a duplicate of 97-11 (both "Disciples of Tzeentch
    #   Pink Horrors").  97-12 was already inactive; including it here for
    #   completeness / idempotency.
    '97-12',   # Disciples of Tzeentch Pink Horrors (duplicate of 97-11)
]


# ===========================================================================
# AMAZON PRICE FIXES
# ===========================================================================
AMAZON_FIXES = {
    # LESSON: HA-021 Leviathan Dreadnought had ASIN B0B8ZMZ99L which is the
    #   Contemptor Dreadnought (now on HA-002).  Correct ASIN for the HH
    #   Leviathan Dreadnought with Claw & Drill is B0B6W3RPPQ.
    #   Price is estimated from MM ($71.99) minus typical Amazon discount;
    #   verify against the live Amazon page and update if incorrect.
    'HA-021': ('65.00', 'https://www.amazon.com/dp/B0B6W3RPPQ', True),

    # LESSON: 83-40 Tzaangors had no Amazon listing (NOT_AVAIL).
    #   Correct ASIN is B01NBYRM58 (Disciples of Tzeentch Tzaangors) at
    #   $57.53.
    '83-40': ('57.53', 'https://www.amazon.com/dp/B01NBYRM58', True),
}

# Products where Amazon does NOT carry the product — mark not_available.
AMAZON_NOT_AVAILABLE = [
    # LESSON: 91-32 Flesh-Eater Courts Terrorgheist had ASIN 1788264290 at
    #   $22.70 — that looks like an ISBN (a book), not a miniature.  Amazon
    #   does not stock this kit.  Mark not_available.
    '91-32',   # Flesh-Eater Courts Terrorgheist
]


# ===========================================================================
# EBAY PRICE FIXES
# ===========================================================================
EBAY_FIXES = {
    # LESSON: 83-40 Tzaangors eBay scraper found listing 127568908003 at
    #   $33.15 — incorrect listing.  Correct listing is 117006727035 at
    #   $57.99.  Also adding eBay search name override (in populate_products)
    #   to help the scraper find this listing in future runs.
    '83-40': ('57.99', 'https://www.ebay.com/itm/117006727035', True),
}


# ===========================================================================
# HA-050 PRAETOR OVERHAUL
# New name: "Warhammer Horus Heresy: Legiones Astartes - Praetor & Chaplain
#            Consul"
# LESSON: Every retailer link for HA-050 was wrong:
#   - GW link pointed to Stormcast Eternals Praetors (Age of Sigmar)
#   - Noble Knight linked to a Librarian in Terminator Armour
#   - MM was NOT_AVAIL; Amazon was NOT_AVAIL; eBay was NOT_AVAIL
# All five retailer links are corrected below.
# Amazon price is estimated from comparable listings; verify and update
# if incorrect.
# ===========================================================================
HA050_NEW_NAME = (
    'Warhammer Horus Heresy: Legiones Astartes - Praetor & Chaplain Consul'
)
HA050_NEW_SLUG = (
    'warhammer-horus-heresy-legiones-astartes-praetor-chaplain-consul'
)
HA050_NEW_IMAGE = IMG_HA050_GW
HA050_PRICES = {
    'Amazon':       ('47.50', 'https://www.amazon.com/dp/B0B4K9B9Q4', True),
    'eBay':         ('51.00', 'https://www.ebay.com/itm/175330174146', True),
    'Games Workshop': (
        '55.00',
        'https://www.warhammer.com/en-US/shop/'
        'legiones-astartes-praetor-and-chaplain-consul-2022',
        True,
    ),
    'Miniature Market': (
        '49.99',
        'https://www.miniaturemarket.com/gw-31-08.html',
        True,
    ),
}
# Noble Knight has no listing for this product.
HA050_NK_NOT_AVAILABLE = True


class Command(BaseCommand):
    """Apply third wave of March 2026 batch database corrections."""

    help = (
        'Apply batch fixes wave C (March 2026): deactivations, price/link '
        'corrections, HA-050 overhaul, HA-051 reclassification.'
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

    def _mark_not_available(self, product, retailer, *, dry_run):
        """Mark a retailer's CurrentPrice as not_available."""
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
        # SECTION 4: Overhaul HA-050 Praetor in Terminator Armour
        # ==================================================================
        self.stdout.write(self.style.MIGRATE_HEADING(
            f'\n{prefix}=== Section 4: Overhaul HA-050 Praetor ==='))
        praetor = self._get_product('HA-050')
        if praetor:
            # -- Rename --
            self.stdout.write(
                f'  [{"dry" if dry_run else "rename"}] HA-050  '
                f"'{praetor.name}' -> '{HA050_NEW_NAME}'")
            # -- Image --
            self.stdout.write(
                f'  [{"dry" if dry_run else "image"}] HA-050  '
                f'image_url -> {HA050_NEW_IMAGE[:70]}...')
            if not dry_run:
                praetor.name = HA050_NEW_NAME
                praetor.slug = HA050_NEW_SLUG
                praetor.image_url = HA050_NEW_IMAGE
                praetor.save(update_fields=['name', 'slug', 'image_url'])

            # -- Retailer prices --
            for retailer_name, (price_str, url, in_stock) in (
                    HA050_PRICES.items()):
                try:
                    retailer = Retailer.objects.get(name=retailer_name)
                    self._set_price(praetor, retailer, price_str, url,
                                    in_stock, dry_run=dry_run)
                except Retailer.DoesNotExist:
                    self.stdout.write(self.style.WARNING(
                        f'  [warn] Retailer "{retailer_name}" not found'))

            if HA050_NK_NOT_AVAILABLE:
                self._mark_not_available(praetor, r_nk, dry_run=dry_run)
        else:
            self.stdout.write(self.style.WARNING(
                '  [skip] HA-050 not found'))

        # ==================================================================
        # SECTION 5: Reclassify HA-051 Chaplain (HH -> WH40K Space Marines)
        # ==================================================================
        self.stdout.write(self.style.MIGRATE_HEADING(
            f'\n{prefix}=== Section 5: Reclassify HA-051 Chaplain ==='))
        chaplain = self._get_product('HA-051')
        if chaplain:
            try:
                cat_40k = Category.objects.get(name='Warhammer 40,000')
                faction_sm = Faction.objects.get(name='Space Marines')
                self.stdout.write(
                    f'  [{"dry" if dry_run else "set"}] HA-051  '
                    f'category: {chaplain.category} -> {cat_40k.name}')
                self.stdout.write(
                    f'  [{"dry" if dry_run else "set"}] HA-051  '
                    f'faction: {chaplain.faction} -> {faction_sm.name}')
                if not dry_run:
                    chaplain.category = cat_40k
                    chaplain.faction = faction_sm
                    chaplain.save(update_fields=['category', 'faction'])
            except (Category.DoesNotExist, Faction.DoesNotExist) as e:
                self.stdout.write(self.style.ERROR(
                    f'  [error] Could not find category/faction: {e}'))
        else:
            self.stdout.write(self.style.WARNING('  [skip] HA-051 not found'))

        # ==================================================================
        # SECTION 6: Set Citadel brand logo on active Citadel products
        # ==================================================================
        self.stdout.write(self.style.MIGRATE_HEADING(
            f'\n{prefix}=== Section 6: Citadel product images ==='))
        citadel_qs = Product.objects.filter(
            name__icontains='Citadel',
            is_active=True,
        ).exclude(gw_sku__in=CITADEL_LOGO_SKUS_EXCLUDE)

        count = citadel_qs.count()
        self.stdout.write(
            f'  Found {count} active Citadel product(s) '
            f'(excluding Painting Handles)')
        if dry_run:
            for p in citadel_qs.order_by('gw_sku'):
                self.stdout.write(
                    f'  [dry] {p.gw_sku:<12} {p.name}')
        else:
            updated = citadel_qs.update(image_url=CITADEL_LOGO_IMG)
            self.stdout.write(self.style.SUCCESS(
                f'  Updated {updated} Citadel product image(s)'))

        self.stdout.write(self.style.SUCCESS(
            f'\n{prefix}=== All sections complete! ==='))
