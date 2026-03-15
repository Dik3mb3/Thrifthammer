"""
Management command: apply_batch_fixes_mar2026g

Seventh wave of March 2026 batch corrections for ThriftHammer.
Run after apply_batch_fixes_mar2026f.

Changes covered:
  Section 1  - Deactivate 2 SKUs
               48-36 Space Marine Judiciar (standalone hero with no reliable listing)
               48-21 Space Marine Land Raider (duplicate — 48-22 Land Raider
               Crusader/Redeemer is the canonical entry)
  Section 2  - Amazon NOT_AVAIL (1 product)
               48-96 Space Marine Incursors (B07J3PG964 was wrong product)
  Section 3  - Amazon price fixes (4 ASINs)
               48-30 Librarian B08HSS6KJ1 $35.70
               48-40 Outriders B08LZYX55N $55.25
               48-23 Predator B07WJHVDFC $68.00
               48-29 Scouts B0DH4Y2GJS $69.70 (Kill Team Scout Squad 2024)
  Section 4  - eBay fix (1 listing)
               48-29 Scouts 147126477088 $69.70
  Section 5  - Miniature Market URL fix (1 product)
               48-29 Scouts — correct 2024 Scout Squad page (out of stock)
  Section 6  - Noble Knight NOT_AVAIL (1 product)
               48-29 Scouts — no NK listing available
  Section 7  - Games Workshop URL fixes (2 products)
               48-61 Primaris Lieutenant → 2023 product page
               48-29 Scouts → Kill Team Scout Squad 2024 page
  Section 8  - Product image update (1 product)
               48-61 Primaris Lieutenant → correct GW CDN image
               (was accidentally set to the Primaris Captain image)

Usage:
    python manage.py apply_batch_fixes_mar2026g
    python manage.py apply_batch_fixes_mar2026g --dry-run
"""

import decimal

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Product, Retailer


# ===========================================================================
# SKUs TO DEACTIVATE (is_active → False)
# ===========================================================================
DEACTIVATE_SKUS = [
    # ── Space Marines ─────────────────────────────────────────────────────────
    # LESSON: 48-36 "Space Marine Judiciar" was in seed without an Amazon or
    #   eBay listing. No reliable current marketplace listing exists.
    '48-36',

    # LESSON: 48-21 "Space Marine Land Raider" is a duplicate of 48-22
    #   "Land Raider Crusader/Redeemer". Both used the same Amazon ASIN
    #   (B001GQQT2A). 48-22 is the canonical entry; 48-21 is removed.
    '48-21',
]


# ===========================================================================
# AMAZON: products with no current listing
# ===========================================================================
AMAZON_NOT_AVAIL = [
    # 48-96: B07J3PG964 at $24.97 was wrong product; Incursors not on Amazon.
    '48-96',
]


# ===========================================================================
# AMAZON: correct ASINs with verified prices
# ===========================================================================
# Format: gw_sku -> (price_str, url, in_stock)
AMAZON_FIXES = {
    # LESSON: 48-30 Librarian was seeded with B08CTK7K4F at $75.00 — wrong ASIN.
    #   B08HSS6KJ1 verified at $35.70 for the Primaris Librarian box.
    '48-30': ('35.70', 'https://www.amazon.com/dp/B08HSS6KJ1', True),  # Librarian

    # LESSON: 48-40 Outriders was seeded with B0DYJKS2JP at $34.99 — wrong ASIN.
    #   B08LZYX55N verified at $55.25 for the Space Marine Outriders box.
    '48-40': ('55.25', 'https://www.amazon.com/dp/B08LZYX55N', True),  # Outriders

    # LESSON: 48-23 Predator was seeded with B0FL3X8DFY at $28.99 — wrong ASIN.
    #   B07WJHVDFC verified at $68.00 for the Space Marines Predator box.
    '48-23': ('68.00', 'https://www.amazon.com/dp/B07WJHVDFC', True),  # Predator

    # LESSON: 48-29 Scouts was seeded with B0DH4W3XYK at $28.90 — this ASIN
    #   was the wrong match for Scouts (it was also incorrectly linked to
    #   Eradicators before wave F). Correct ASIN B0DH4Y2GJS is the
    #   Kill Team Scout Squad (2024 3rd Edition) at $69.70.
    '48-29': ('69.70', 'https://www.amazon.com/dp/B0DH4Y2GJS', True),  # Scouts (Kill Team 2024)
}


# ===========================================================================
# EBAY: correct listing IDs with verified prices
# ===========================================================================
# Format: gw_sku -> (ebay_item_id, price_str)
EBAY_FIXES = {
    # 48-29 Scouts — Kill Team Scout Squad 2024 listing, verified at $69.70.
    '48-29': ('147126477088', '69.70'),
}


# ===========================================================================
# MINIATURE MARKET URL FIXES
# ===========================================================================
# Format: gw_sku -> (new_url, in_stock, not_available)
MM_FIXES = {
    # 48-29 Scouts — correct 2024 Scout Squad product page; out of stock.
    '48-29': (
        'https://www.miniaturemarket.com/'
        'warhammer-40k-kill-team-space-marines-scout-squad-gw-103-44-2024.html',
        False, True,
    ),
}


# ===========================================================================
# GAMES WORKSHOP URL FIXES
# ===========================================================================
# Format: gw_sku -> new_url
GW_URL_FIXES = {
    # 48-61 Primaris Lieutenant — update to the 2023 product page.
    '48-61': 'https://www.warhammer.com/en-US/shop/space-marines-lieutenant-2023',

    # 48-29 Scouts — update to the Kill Team Scout Squad 2024 product page.
    '48-29': 'https://www.warhammer.com/en-WW/shop/kill-team-scout-squad-2024',
}


# ===========================================================================
# PRODUCT IMAGE UPDATES (GW CDN — confirmed via live GW page)
# ===========================================================================
# Format: gw_sku -> full image_url
# LESSON: 48-61 Primaris Lieutenant was incorrectly assigned the Primaris
#   Captain image (99120101179_PrimarisCaptain01.jpg). The correct Lieutenant
#   image confirmed from https://www.warhammer.com/en-US/shop/space-marines-lieutenant-2023
IMG_48_61_LIEUTENANT = (
    'https://www.warhammer.com/app/resources/catalog/product/920x950/'
    '99070101079_SMLieutenant1.jpg'
)

IMAGE_UPDATES = {
    '48-61': IMG_48_61_LIEUTENANT,
}


class Command(BaseCommand):
    """Seventh wave of March 2026 ThriftHammer DB corrections."""

    help = 'Apply Wave G batch corrections (March 2026).'

    def add_arguments(self, parser):
        """Add --dry-run flag to preview changes without saving."""
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Print planned changes without writing to the database.',
        )

    def handle(self, *args, **options):
        """Execute all Wave G corrections in order."""
        dry = options['dry_run']
        if dry:
            self.stdout.write(self.style.WARNING('DRY RUN — no changes will be saved.\n'))

        self._section_1_deactivate(dry)
        self._section_2_amazon_not_avail(dry)
        self._section_3_amazon_fixes(dry)
        self._section_4_ebay_fixes(dry)
        self._section_5_mm_fixes(dry)
        self._section_6_nk_not_avail(dry)
        self._section_7_gw_url_fixes(dry)
        self._section_8_image_updates(dry)

        if dry:
            self.stdout.write(self.style.WARNING('\nDRY RUN complete — nothing was saved.'))
        else:
            self.stdout.write(self.style.SUCCESS('\nWave G complete.'))

    # -----------------------------------------------------------------------
    # Helpers
    # -----------------------------------------------------------------------

    def _get_product(self, gw_sku):
        """Fetch a product by gw_sku, writing an error and raising if missing."""
        try:
            return Product.objects.get(gw_sku=gw_sku)
        except Product.DoesNotExist:
            self.stderr.write(self.style.ERROR(f'  ERROR: Product {gw_sku} not found.'))
            raise

    def _set_price(self, product, retailer, price_str, url, in_stock,
                   not_available=False, dry=False):
        """Update or create a CurrentPrice record."""
        label = f'{product.gw_sku} / {retailer.name}'
        if dry:
            action = 'NOT_AVAIL' if not_available else f'${price_str}'
            self.stdout.write(f'  [dry] {label} → {action}  {url}')
            return
        CurrentPrice.objects.update_or_create(
            product=product,
            retailer=retailer,
            defaults={
                'price': decimal.Decimal(price_str),
                'url': url,
                'in_stock': in_stock,
                'not_available': not_available,
            },
        )
        action = 'NOT_AVAIL' if not_available else f'${price_str}'
        self.stdout.write(f'  [ok] {label} → {action}')

    def _mark_not_available(self, product, retailer, dry=False):
        """Mark an existing price row as not_available; skip silently if no row."""
        label = f'{product.gw_sku} / {retailer.name}'
        try:
            cp = CurrentPrice.objects.get(product=product, retailer=retailer)
        except CurrentPrice.DoesNotExist:
            self.stdout.write(f'  [skip] {label} — no row to mark NOT_AVAIL')
            return
        if dry:
            self.stdout.write(f'  [dry] {label} → NOT_AVAIL')
            return
        cp.not_available = True
        cp.in_stock = False
        cp.save(update_fields=['not_available', 'in_stock'])
        self.stdout.write(f'  [ok] {label} → NOT_AVAIL')

    def _update_retailer_url(self, product, retailer, url, in_stock,
                             not_available, dry=False):
        """Update URL and stock flags on an existing price row."""
        label = f'{product.gw_sku} / {retailer.name}'
        try:
            cp = CurrentPrice.objects.get(product=product, retailer=retailer)
        except CurrentPrice.DoesNotExist:
            self.stdout.write(
                f'  [skip] {label} — no row found, skipping URL update'
            )
            return
        if dry:
            self.stdout.write(
                f'  [dry] {label} → url=…{url[-50:]}  not_avail={not_available}'
            )
            return
        cp.url = url
        cp.in_stock = in_stock
        cp.not_available = not_available
        cp.save(update_fields=['url', 'in_stock', 'not_available'])
        self.stdout.write(f'  [ok] {label} → url updated')

    # -----------------------------------------------------------------------
    # Sections
    # -----------------------------------------------------------------------

    def _section_1_deactivate(self, dry):
        """Section 1: Deactivate SKUs (is_active → False)."""
        self.stdout.write('\n── Section 1: Deactivate SKUs ──')
        for sku in DEACTIVATE_SKUS:
            try:
                p = self._get_product(sku)
            except Product.DoesNotExist:
                continue
            if dry:
                self.stdout.write(f'  [dry] {sku} "{p.name}" → is_active=False')
                continue
            p.is_active = False
            p.save(update_fields=['is_active'])
            self.stdout.write(f'  [ok] {sku} "{p.name}" → deactivated')

    def _section_2_amazon_not_avail(self, dry):
        """Section 2: Mark Amazon prices as not_available."""
        self.stdout.write('\n── Section 2: Amazon NOT_AVAIL ──')
        amazon = Retailer.objects.get(name='Amazon')
        for sku in AMAZON_NOT_AVAIL:
            try:
                p = self._get_product(sku)
            except Product.DoesNotExist:
                continue
            self._mark_not_available(p, amazon, dry)

    def _section_3_amazon_fixes(self, dry):
        """Section 3: Apply corrected Amazon ASINs and prices."""
        self.stdout.write('\n── Section 3: Amazon price fixes ──')
        amazon = Retailer.objects.get(name='Amazon')
        for sku, (price, url, in_stock) in AMAZON_FIXES.items():
            try:
                p = self._get_product(sku)
            except Product.DoesNotExist:
                continue
            self._set_price(p, amazon, price, url, in_stock, dry=dry)

    def _section_4_ebay_fixes(self, dry):
        """Section 4: Apply corrected eBay listing IDs and prices."""
        self.stdout.write('\n── Section 4: eBay price fixes ──')
        ebay = Retailer.objects.get(name='eBay')
        for sku, (item_id, price) in EBAY_FIXES.items():
            url = f'https://www.ebay.com/itm/{item_id}'
            try:
                p = self._get_product(sku)
            except Product.DoesNotExist:
                continue
            self._set_price(p, ebay, price, url, True, dry=dry)

    def _section_5_mm_fixes(self, dry):
        """Section 5: Fix Miniature Market URLs."""
        self.stdout.write('\n── Section 5: Miniature Market URL fixes ──')
        mm = Retailer.objects.get(name='Miniature Market')
        for sku, (url, in_stock, not_available) in MM_FIXES.items():
            try:
                p = self._get_product(sku)
            except Product.DoesNotExist:
                continue
            self._update_retailer_url(p, mm, url, in_stock, not_available, dry)

    def _section_6_nk_not_avail(self, dry):
        """Section 6: Mark Noble Knight rows as not_available where no listing exists."""
        self.stdout.write('\n── Section 6: Noble Knight NOT_AVAIL ──')
        nk = Retailer.objects.get(name='Noble Knight Games')
        for sku in ['48-29']:
            try:
                p = self._get_product(sku)
            except Product.DoesNotExist:
                continue
            self._mark_not_available(p, nk, dry)

    def _section_7_gw_url_fixes(self, dry):
        """Section 7: Fix Games Workshop retailer URLs."""
        self.stdout.write('\n── Section 7: Games Workshop URL fixes ──')
        gw = Retailer.objects.get(name='Games Workshop')
        for sku, url in GW_URL_FIXES.items():
            try:
                p = self._get_product(sku)
            except Product.DoesNotExist:
                continue
            try:
                cp = CurrentPrice.objects.get(product=p, retailer=gw)
            except CurrentPrice.DoesNotExist:
                self.stdout.write(f'  [skip] {sku} / Games Workshop — no row found')
                continue
            if dry:
                self.stdout.write(
                    f'  [dry] {sku} / Games Workshop → url=…{url[-55:]}'
                )
                continue
            cp.url = url
            cp.save(update_fields=['url'])
            self.stdout.write(f'  [ok] {sku} / Games Workshop → url updated')

    def _section_8_image_updates(self, dry):
        """Section 8: Update product image_url fields."""
        self.stdout.write('\n── Section 8: Product image updates ──')
        for sku, image_url in IMAGE_UPDATES.items():
            try:
                p = self._get_product(sku)
            except Product.DoesNotExist:
                continue
            old_url = p.image_url
            filename = image_url.split('/')[-1]
            if dry:
                old_file = old_url.split('/')[-1] if old_url else '(none)'
                self.stdout.write(
                    f'  [dry] {sku} image: {old_file} → {filename}'
                )
                continue
            p.image_url = image_url
            p.save(update_fields=['image_url'])
            self.stdout.write(f'  [ok] {sku} image → {filename}')
