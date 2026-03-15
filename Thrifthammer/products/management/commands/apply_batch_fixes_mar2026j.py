"""
Management command: apply_batch_fixes_mar2026j

Tenth wave of March 2026 batch corrections for ThriftHammer.
Run after apply_batch_fixes_mar2026i.

Changes covered:
  Section 1  - Deactivate 9 SKUs
               WC-100 Warcry Starter Set
               WC-101 Warcry: Heart of Ghur
               WC-102 Warcry: Hunter and Hunted
               40-01  Warhammer 40,000 Core Rules
               40-03  Warhammer 40,000 Starter Set
               40-10  Warhammer 40,000 Chapter Approved: Leviathan
               40-20  Warhammer 40,000 Dice Set
               40-21  Warhammer 40,000 Measuring Tape
               HA-050 Warhammer Horus Heresy: Legiones Astartes - Praetor &
                      Chaplain Consul
  Section 2  - Amazon price fixes (2)
               55-16 Ultramarines Honour Guard B0FXNDT7XR $92.42
               43-04 World Eaters Angron B0BTDDDLD5 $140.00
  Section 3  - Games Workshop URL fix (1)
               43-04 World Eaters Angron → 2023 product page
  Section 4  - Product field updates (negative keywords)
               55-16 Ultramarines Honour Guard: add 'Action Figure'

Usage:
    python manage.py apply_batch_fixes_mar2026j
    python manage.py apply_batch_fixes_mar2026j --dry-run
"""

import decimal

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Product, Retailer


# ===========================================================================
# SKUs TO DEACTIVATE
# ===========================================================================
DEACTIVATE_SKUS = [
    # Warcry products — removed from site scope
    'WC-100',   # Warcry Starter Set
    'WC-101',   # Warcry: Heart of Ghur
    'WC-102',   # Warcry: Hunter and Hunted

    # Warhammer 40,000 accessories / rulebooks — out of scope for ThriftHammer
    '40-01',    # Warhammer 40,000 Core Rules
    '40-03',    # Warhammer 40,000 Starter Set
    '40-10',    # Warhammer 40,000 Chapter Approved: Leviathan
    '40-20',    # Warhammer 40,000 Dice Set
    '40-21',    # Warhammer 40,000 Measuring Tape

    # Horus Heresy — Praetor & Chaplain Consul combined kit removed
    'HA-050',   # Warhammer Horus Heresy: Legiones Astartes - Praetor & Chaplain Consul
]


# ===========================================================================
# AMAZON: correct ASINs with verified prices
# ===========================================================================
AMAZON_FIXES = {
    # LESSON: 55-16 Ultramarines Honour Guard was seeded with B0F9DPFMP3 at
    #   $28.99 — wrong ASIN. B0FXNDT7XR confirmed at $92.42 for the 2025
    #   Victrix Honour Guard kit. Add 'Action Figure' neg kw to avoid JoyToy-
    #   style listings.
    '55-16': ('92.42', 'https://www.amazon.com/dp/B0FXNDT7XR', True),

    # LESSON: 43-04 World Eaters Angron was seeded with B0DZZNHNJ2 at $345.00 —
    #   wrong ASIN (appears to be a third-party or inflated listing).
    #   B0BTDDDLD5 confirmed at $140.00 for the correct Games Workshop kit.
    '43-04': ('140.00', 'https://www.amazon.com/dp/B0BTDDDLD5', True),
}


# ===========================================================================
# GAMES WORKSHOP URL FIXES
# ===========================================================================
GW_URL_FIXES = {
    # 43-04 World Eaters Angron — update to the correct 2023 product page.
    '43-04': 'https://www.warhammer.com/en-US/shop/world-eaters-angron-daemon-primarch-of-khorne-2023',
}


class Command(BaseCommand):
    """Tenth wave of March 2026 ThriftHammer DB corrections."""

    help = 'Apply Wave J batch corrections (March 2026).'

    def add_arguments(self, parser):
        """Add --dry-run flag to preview changes without saving."""
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Print planned changes without writing to the database.',
        )

    def handle(self, *args, **options):
        """Execute all Wave J corrections in order."""
        dry = options['dry_run']
        if dry:
            self.stdout.write(self.style.WARNING('DRY RUN — no changes will be saved.\n'))

        self._section_1_deactivate(dry)
        self._section_2_amazon_fixes(dry)
        self._section_3_gw_url_fixes(dry)
        self._section_4_product_field_updates(dry)

        if dry:
            self.stdout.write(self.style.WARNING('\nDRY RUN complete — nothing was saved.'))
        else:
            self.stdout.write(self.style.SUCCESS('\nWave J complete.'))

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
        self.stdout.write(f'  [ok] {label} → ${price_str}')

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

    def _section_2_amazon_fixes(self, dry):
        """Section 2: Apply corrected Amazon ASINs and prices."""
        self.stdout.write('\n── Section 2: Amazon price fixes ──')
        amazon = Retailer.objects.get(name='Amazon')
        for sku, (price, url, in_stock) in AMAZON_FIXES.items():
            try:
                p = self._get_product(sku)
            except Product.DoesNotExist:
                continue
            self._set_price(p, amazon, price, url, in_stock, dry=dry)

    def _section_3_gw_url_fixes(self, dry):
        """Section 3: Fix Games Workshop retailer URLs."""
        self.stdout.write('\n── Section 3: Games Workshop URL fixes ──')
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
                self.stdout.write(f'  [dry] {sku} / Games Workshop → url=…{url[-55:]}')
                continue
            cp.url = url
            cp.save(update_fields=['url'])
            self.stdout.write(f'  [ok] {sku} / Games Workshop → url updated')

    def _section_4_product_field_updates(self, dry):
        """Section 4: Update product fields (eBay negative keywords)."""
        self.stdout.write('\n── Section 4: Product field updates ──')
        updates = [
            # 55-16 Ultramarines Honour Guard — action-figure listings (JoyToy
            # and similar) contaminate eBay results.  Excluding "Action Figure"
            # narrows to the correct plastic miniature kit.
            ('55-16', 'ebay_negative_keywords', 'Action Figure'),
        ]
        for sku, field, value in updates:
            try:
                p = self._get_product(sku)
            except Product.DoesNotExist:
                continue
            current = getattr(p, field, '')
            if dry:
                self.stdout.write(f'  [dry] {sku} {field}: "{current}" → "{value}"')
                continue
            setattr(p, field, value)
            p.save(update_fields=[field])
            self.stdout.write(f'  [ok] {sku} {field} → "{value}"')
