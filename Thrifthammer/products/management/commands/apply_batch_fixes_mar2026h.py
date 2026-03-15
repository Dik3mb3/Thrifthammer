"""
Management command: apply_batch_fixes_mar2026h

Eighth wave of March 2026 batch corrections for ThriftHammer.
Run after apply_batch_fixes_mar2026g.

Changes covered:
  Section 1  - Deactivate 1 SKU
               48-99 Space Marine Suppressors (B08MVMPLJQ wrongly used for
               both Suppressors and Eliminators; Suppressors removed)
  Section 2  - Amazon price fixes (6 corrections / additions)
               48-06 Terminator Squad B0G3D2F6BH $61.22
               53-02 Ragnar Blackmane B08LZY9Z3K $40.02
               53-10 Thunderwolf Cavalry B08MV13YVH $55.25
               70-894 Gloomspite Gitz Snarlpack Huntaz B0FQ6TJGQM $118.95
               70-11  Lumineth Realm-lords Hurakan Vanguard B0D9YTJT5Y $128.89
               70-832 Maggotkin of Nurgle Spearhead B0G9VMQW9D $127.50
  Section 3  - eBay price fixes (3 listings)
               48-43 Sternguard Veteran Squad 186099358998 $55.25
               48-06 Terminator Squad 187763771467 $58.65
               48-25 Whirlwind 389712540408 $66.60
  Section 4  - Noble Knight price fix (1 product)
               48-07 Tactical Squad → $60.00 (was $89.95)
  Section 5  - Product field updates
               48-06 Terminator Squad: set ebay_search_name to
               "Space Marine Terminator Assault Squad" (matches eBay listing
               "Space Marines: Terminator Assault Squad (2025 ver.)")
               53-02 Ragnar Blackmane: add 'JoyToy' to ebay_negative_keywords
               53-10 Thunderwolf Cavalry: add 'JoyToy' to ebay_negative_keywords

Usage:
    python manage.py apply_batch_fixes_mar2026h
    python manage.py apply_batch_fixes_mar2026h --dry-run
"""

import decimal

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Product, Retailer


# ===========================================================================
# SKUs TO DEACTIVATE (is_active → False)
# ===========================================================================
DEACTIVATE_SKUS = [
    # LESSON: 48-99 "Space Marine Suppressors" shared ASIN B08MVMPLJQ with
    #   Eliminators (48-98). Wave F corrected Eliminators to this ASIN.
    #   Suppressors has no verified standalone Amazon listing; deactivating.
    '48-99',
]


# ===========================================================================
# AMAZON: correct ASINs with verified prices
# ===========================================================================
# Format: gw_sku -> (price_str, url, in_stock)
AMAZON_FIXES = {
    # ── Space Marines ─────────────────────────────────────────────────────────
    # LESSON: 48-06 Terminator Squad was seeded with B000CEM3E0 at $51.00 —
    #   wrong/outdated ASIN. B0G3D2F6BH confirmed at $61.22 for the current box.
    '48-06': ('61.22',  'https://www.amazon.com/dp/B0G3D2F6BH', True),   # Terminator Squad

    # ── Space Wolves ──────────────────────────────────────────────────────────
    # LESSON: 53-02 Ragnar Blackmane was seeded with B0FGJVB1LQ at $62.99.
    #   B08LZY9Z3K confirmed at $40.02 for the correct GW miniature kit.
    #   JoyToy action figures contaminate searches; exclude "JoyToy" in neg kw.
    '53-02': ('40.02',  'https://www.amazon.com/dp/B08LZY9Z3K', True),   # Ragnar Blackmane

    # LESSON: 53-10 Thunderwolf Cavalry was seeded with B0DTDYR7BM at $249.00 —
    #   grossly overpriced/wrong ASIN. B08MV13YVH confirmed at $55.25.
    #   JoyToy action figures also pollute this search; exclude in neg kw.
    '53-10': ('55.25',  'https://www.amazon.com/dp/B08MV13YVH', True),   # Thunderwolf Cavalry

    # ── AoS Spearhead ─────────────────────────────────────────────────────────
    # LESSON: 70-894 Gloomspite Gitz Snarlpack Huntaz Spearhead was seeded with
    #   B0DZ32PLNB at $51.00 — wrong ASIN (another Gloomspite product).
    #   B0FQ6TJGQM confirmed at $118.95 for the Snarlpack Huntaz Spearhead box.
    '70-894': ('118.95', 'https://www.amazon.com/dp/B0FQ6TJGQM', True),  # Gloomspite Gitz Snarlpack Huntaz

    # 70-11: Spearhead: Lumineth Realm-lords (Hurakan Vanguard) — no Amazon price
    #   was previously set. B0D9YTJT5Y confirmed at $128.89 for this Spearhead.
    '70-11':  ('128.89', 'https://www.amazon.com/dp/B0D9YTJT5Y', True),  # Lumineth Hurakan Vanguard Spearhead

    # 70-832: Spearhead: Maggotkin of Nurgle — no Amazon price previously set.
    #   B0G9VMQW9D confirmed at $127.50 for the Maggotkin Spearhead box.
    '70-832': ('127.50', 'https://www.amazon.com/dp/B0G9VMQW9D', True),  # Maggotkin of Nurgle Spearhead
}


# ===========================================================================
# EBAY: correct listing IDs with verified prices
# ===========================================================================
# Format: gw_sku -> (ebay_item_id, price_str)
EBAY_FIXES = {
    # 48-43 Sternguard Veteran Squad — listing 186099358998 verified at $55.25.
    #   Title: "2023 Sternguard Veteran Squad Space Marines Warhammer 40K"
    '48-43': ('186099358998', '55.25'),

    # 48-06 Terminator Squad — listing 187763771467 verified at $58.65.
    #   Title: "Space Marines: Terminator Assault Squad (2025 ver.) Warhammer 40K"
    #   Search name override added in Section 5 to match this listing title.
    '48-06': ('187763771467', '58.65'),

    # 48-25 Whirlwind — listing 389712540408 verified at $66.60.
    '48-25': ('389712540408', '66.60'),
}


# ===========================================================================
# NOBLE KNIGHT PRICE FIXES
# ===========================================================================
# Format: gw_sku -> (new_price_str, url, in_stock)
# Use when only the price needs correcting, not the URL.
NK_PRICE_FIXES = {
    # LESSON: 48-07 Tactical Squad NK price was $89.95 — significantly overpriced.
    #   Correct current price is $60.00 (same URL: Tactical-Squad-2017 page).
    '48-07': (
        '60.00',
        'https://www.nobleknight.com/P/2147776179/Tactical-Squad-2017',
        True,
    ),
}


class Command(BaseCommand):
    """Eighth wave of March 2026 ThriftHammer DB corrections."""

    help = 'Apply Wave H batch corrections (March 2026).'

    def add_arguments(self, parser):
        """Add --dry-run flag to preview changes without saving."""
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Print planned changes without writing to the database.',
        )

    def handle(self, *args, **options):
        """Execute all Wave H corrections in order."""
        dry = options['dry_run']
        if dry:
            self.stdout.write(self.style.WARNING('DRY RUN — no changes will be saved.\n'))

        self._section_1_deactivate(dry)
        self._section_2_amazon_fixes(dry)
        self._section_3_ebay_fixes(dry)
        self._section_4_nk_price_fixes(dry)
        self._section_5_product_field_updates(dry)

        if dry:
            self.stdout.write(self.style.WARNING('\nDRY RUN complete — nothing was saved.'))
        else:
            self.stdout.write(self.style.SUCCESS('\nWave H complete.'))

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

    def _section_3_ebay_fixes(self, dry):
        """Section 3: Apply corrected eBay listing IDs and prices."""
        self.stdout.write('\n── Section 3: eBay price fixes ──')
        ebay = Retailer.objects.get(name='eBay')
        for sku, (item_id, price) in EBAY_FIXES.items():
            url = f'https://www.ebay.com/itm/{item_id}'
            try:
                p = self._get_product(sku)
            except Product.DoesNotExist:
                continue
            self._set_price(p, ebay, price, url, True, dry=dry)

    def _section_4_nk_price_fixes(self, dry):
        """Section 4: Fix Noble Knight prices (keeping existing URLs)."""
        self.stdout.write('\n── Section 4: Noble Knight price fixes ──')
        nk = Retailer.objects.get(name='Noble Knight Games')
        for sku, (price, url, in_stock) in NK_PRICE_FIXES.items():
            try:
                p = self._get_product(sku)
            except Product.DoesNotExist:
                continue
            label = f'{sku} / Noble Knight Games'
            try:
                cp = CurrentPrice.objects.get(product=p, retailer=nk)
            except CurrentPrice.DoesNotExist:
                self.stdout.write(f'  [skip] {label} — no row found')
                continue
            old_price = cp.price
            if dry:
                self.stdout.write(
                    f'  [dry] {label} → ${old_price} → ${price}'
                )
                continue
            cp.price = decimal.Decimal(price)
            cp.url = url
            cp.in_stock = in_stock
            cp.not_available = False
            cp.save(update_fields=['price', 'url', 'in_stock', 'not_available'])
            self.stdout.write(f'  [ok] {label} → ${old_price} → ${price}')

    def _section_5_product_field_updates(self, dry):
        """Section 5: Update eBay search names and negative keywords."""
        self.stdout.write('\n── Section 5: Product field updates ──')
        updates = [
            # 48-06 Terminator Squad — the eBay listing is titled "Space Marines:
            # Terminator Assault Squad (2025 ver.)". Overriding the default search
            # name ("Space Marine Terminator Squad") to "Space Marine Terminator
            # Assault Squad" improves match accuracy for the current product box.
            ('48-06', 'ebay_search_name', 'Space Marine Terminator Assault Squad'),

            # 53-02 Ragnar Blackmane — JoyToy produces 1:18-scale action figures
            # of Space Wolf characters that contaminate eBay search results.
            # Excluding "JoyToy" at query level prevents these from appearing.
            ('53-02', 'ebay_negative_keywords', 'JoyToy'),

            # 53-10 Thunderwolf Cavalry — same JoyToy contamination issue as
            # Ragnar Blackmane. Excluding "JoyToy" filters third-party figures.
            ('53-10', 'ebay_negative_keywords', 'JoyToy'),
        ]
        for sku, field, value in updates:
            try:
                p = self._get_product(sku)
            except Product.DoesNotExist:
                continue
            current = getattr(p, field, '')
            if dry:
                self.stdout.write(
                    f'  [dry] {sku} {field}: "{current}" → "{value}"'
                )
                continue
            setattr(p, field, value)
            p.save(update_fields=[field])
            self.stdout.write(f'  [ok] {sku} {field} → "{value}"')
