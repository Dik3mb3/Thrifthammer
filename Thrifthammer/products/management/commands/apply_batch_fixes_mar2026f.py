"""
Management command: apply_batch_fixes_mar2026f

Sixth wave of March 2026 batch corrections for ThriftHammer.
Run after apply_batch_fixes_mar2026e.

Changes covered:
  Section 1  - Deactivate 2 duplicate SKUs
               (50-05 Ork Warboss dupe of 50-02;
                83-10 Chaos Warriors (12) dupe of 83-18)
  Section 2  - Rename 3 products
               70-10 → "Nighthaunt Spearhead"
               83-18 → "Slaves to Darkness Chaos Warriors" (drop count suffix)
               48-98 → "Space Marine Primaris Eliminators"
  Section 3  - Amazon NOT_AVAIL (3 products)
               91-15 Knight of Shrouds, 50-16 Deff Dread, 90-10 Skaven Clanrats
  Section 4  - Fix Amazon prices (9 ASINs)
               89-30 Ardboys B0CHRYV6WD $55.25
               HA-020 Solar Auxilia Lasrifle Section B0CYCQJ4NQ $67.15
               48-92 Aggressors B0746GR78Q $51.00
               48-32 Chaplain B074DSM6W1 $35.70
               71-02 Space Marine Combat Patrol B0CLVTKD9K $147.58
               71-18 Ork Combat Patrol B0D14VVJ26 $144.50
               48-39 Eradicators B08VHF72L8 $51.00
               48-28 Firestrike Servo-Turrets B08KHQPW8M $33.15
               48-98 Eliminators B08MVMPLJQ $50.00
  Section 5  - Fix eBay prices (16 listings)
               70-10, 50-10, 71-18, 50-16, 50-14, 50-11, 90-10,
               48-34, 48-38, 48-32, 71-02, 48-37, 48-98, 48-39, 48-28, 48-94
  Section 6  - Miniature Market URL fixes
               70-10 Nighthaunt Spearhead (NOT_AVAIL — correct page found)
               89-22 Gutrippaz (NOT_AVAIL — correct page found)
  Section 7  - Noble Knight URL fixes
               70-10 Nighthaunt Spearhead (NOT_AVAIL — new correct URL)
               83-18 Chaos Warriors (NOT_AVAIL — was pointing to Datacards!)
  Section 8  - Games Workshop URL fix
               70-10 → https://www.warhammer.com/en-US/shop/spearhead-cursed-shacklehorde-2025
  Section 9  - Product field updates
               90-10 Clanrats: add '1989' to ebay_negative_keywords
               50-10 Ork Boyz: add 'lootas' to ebay_negative_keywords
               50-16 Deff Dread: set ebay_search_name to "Ork Deff Dread 40000"

Usage:
    python manage.py apply_batch_fixes_mar2026f
    python manage.py apply_batch_fixes_mar2026f --dry-run
"""

import decimal

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Product, Retailer


# ===========================================================================
# SKUs TO DEACTIVATE (is_active → False)
# ===========================================================================
DEACTIVATE_SKUS = [
    # ── Orks ─────────────────────────────────────────────────────────────────
    # LESSON: 50-05 "Ork Warboss" was a duplicate of 50-02 "Warboss in Mega
    #   Armour". Both shared identical Amazon ASIN (B09NSSWG75) and eBay data.
    #   50-02 is the canonical active entry; 50-05 is redundant.
    '50-05',

    # ── Slaves to Darkness ───────────────────────────────────────────────────
    # LESSON: 83-10 "Slaves to Darkness Chaos Warriors (12)" was a duplicate of
    #   83-18 "Chaos Warriors (10)". Both referenced the same ASIN B0BRY3JPBX
    #   (same dual-build plastic kit). 83-18 is the canonical entry; 83-10 removed.
    '83-10',
]


# ===========================================================================
# RENAMES — name + slug applied directly to the Product row
# ===========================================================================
# Format: gw_sku -> (new_name, new_slug)
RENAMES = {
    # 70-10: The official GW box was titled "Spearhead: Nighthaunt – Cursed
    #   Shacklehorde" but is universally searched as "Nighthaunt Spearhead".
    #   Rename for consistency with other Spearhead box entries (70-17, 70-12, etc.)
    '70-10': ('Nighthaunt Spearhead', 'nighthaunt-spearhead'),

    # 83-18: Remove the "(10)" count now that the duplicate 83-10 "(12)" entry
    #   has been deactivated. The plain name is cleaner and avoids confusion.
    '83-18': ('Slaves to Darkness Chaos Warriors', 'slaves-to-darkness-chaos-warriors'),

    # 48-98: Add "Primaris" to match the official GW product name and improve
    #   search accuracy. Avoids conflation with older (non-Primaris) Eliminators.
    '48-98': ('Space Marine Primaris Eliminators', 'space-marine-primaris-eliminators'),
}


# ===========================================================================
# AMAZON: products with no current listing
# ===========================================================================
AMAZON_NOT_AVAIL = [
    # 91-15: B0FLZJWWGP placeholder confirmed incorrect; no active Amazon listing.
    '91-15',

    # 50-16: The seed previously carried the Lootas ASIN (B09HJBSNNW) by mistake.
    #   Deff Dread has no correct Amazon listing; mark row NOT_AVAIL.
    '50-16',

    # 90-10: B0DFWN8F73 listing confirmed out of stock / unavailable.
    '90-10',
]


# ===========================================================================
# AMAZON: correct ASINs with verified prices
# ===========================================================================
# Format: gw_sku -> (price_str, url, in_stock)
AMAZON_FIXES = {
    # ── Orruk Warclans ────────────────────────────────────────────────────────
    # LESSON: 89-30 Ardboys was seeded with B0CHRXGQ8N at $33.15 — wrong ASIN/price.
    #   Correct ASIN B0CHRYV6WD verified at $55.25.
    '89-30': ('55.25',  'https://www.amazon.com/dp/B0CHRYV6WD',  True),  # Ardboys

    # ── Horus Heresy ──────────────────────────────────────────────────────────
    # LESSON: HA-020 was seeded with B0CYCSZ4QV at $29.75 — wrong ASIN.
    #   Correct ASIN B0CYCQJ4NQ verified at $67.15 for Solar Auxilia Lasrifle Section.
    'HA-020': ('67.15',  'https://www.amazon.com/dp/B0CYCQJ4NQ', True),  # Solar Auxilia Lasrifle Section

    # ── Space Marines ─────────────────────────────────────────────────────────
    # LESSON: 48-92 Aggressors was seeded with B0CJS1MKVJ at $33.15 — wrong ASIN.
    #   B0746GR78Q verified at $51.00 for Space Marines Aggressors box.
    '48-92': ('51.00',  'https://www.amazon.com/dp/B0746GR78Q',  True),  # Aggressors

    # LESSON: 48-32 Chaplain was seeded with B0055UCUR6 at $69.95 — wrong ASIN.
    #   B074DSM6W1 verified at $35.70 for Space Marine Primaris Chaplain.
    '48-32': ('35.70',  'https://www.amazon.com/dp/B074DSM6W1',  True),  # Chaplain

    # 71-02: Space Marine Combat Patrol — previously NOT_AVAIL on Amazon.
    #   B0CLVTKD9K confirmed in stock at $147.58.
    '71-02': ('147.58', 'https://www.amazon.com/dp/B0CLVTKD9K',  True),  # Space Marine Combat Patrol

    # 71-18: Ork Combat Patrol — previously NOT_AVAIL on Amazon.
    #   B0D14VVJ26 confirmed in stock at $144.50.
    '71-18': ('144.50', 'https://www.amazon.com/dp/B0D14VVJ26',  True),  # Ork Combat Patrol

    # LESSON: 48-39 Eradicators was seeded with B0DH4W3XYK at $28.90 — this
    #   ASIN belongs to Scouts (48-29). Correct ASIN B08VHF72L8 verified at $51.00.
    '48-39': ('51.00',  'https://www.amazon.com/dp/B08VHF72L8',  True),  # Eradicators

    # LESSON: 48-28 Firestrike Servo-Turrets was seeded with B0FTZYXRQV at $152.50
    #   — price wildly high for this unit. Correct ASIN B08KHQPW8M verified at $33.15.
    '48-28': ('33.15',  'https://www.amazon.com/dp/B08KHQPW8M',  True),  # Firestrike Servo-Turrets

    # LESSON: 48-98 Eliminators was seeded with B0D3FN245T at $42.99 — wrong ASIN.
    #   B08MVMPLJQ title confirmed "Space Marines Primaris Eliminators", price $50.00.
    '48-98': ('50.00',  'https://www.amazon.com/dp/B08MVMPLJQ',  True),  # Primaris Eliminators
}


# ===========================================================================
# EBAY: correct listing IDs with verified prices
# ===========================================================================
# Format: gw_sku -> (ebay_item_id, price_str)
EBAY_FIXES = {
    # ── Nighthaunt ────────────────────────────────────────────────────────────
    '70-10': ('227231298347',  '115.00'),  # Nighthaunt Spearhead

    # ── Orks ──────────────────────────────────────────────────────────────────
    '50-10': ('137117828682',   '40.80'),  # Ork Boyz
    '71-18': ('177944179445',  '144.50'),  # Ork Combat Patrol
    '50-16': ('389640413564',   '58.50'),  # Ork Deff Dread
    '50-14': ('183199561434',   '35.70'),  # Ork Lootas
    '50-11': ('137031040549',   '51.00'),  # Ork Trukk

    # ── Skaven ────────────────────────────────────────────────────────────────
    '90-10': ('174718271038',   '34.95'),  # Skaven Clanrats

    # ── Space Marines ─────────────────────────────────────────────────────────
    '48-34': ('256911694044',   '36.98'),  # Space Marine Ancient
    '48-38': ('356236367790',   '45.95'),  # Space Marine Bladeguard Veterans
    '48-32': ('184024162896',   '35.70'),  # Space Marine Chaplain
    '71-02': ('405939586465',  '109.00'),  # Space Marine Combat Patrol
    '48-37': ('317968367882',   '52.91'),  # Space Marine Company Heroes
    '48-98': ('183953646056',   '51.00'),  # Space Marine Primaris Eliminators
    '48-39': ('146925673541',   '51.00'),  # Space Marine Eradicators
    '48-28': ('184474535689',   '33.15'),  # Space Marine Firestrike Servo-Turrets
    '48-94': ('174069466108',   '75.65'),  # Space Marine Impulsor
}


# ===========================================================================
# MINIATURE MARKET URL FIXES
# ===========================================================================
# Format: gw_sku -> (new_url, in_stock, not_available)
MM_FIXES = {
    # 70-10 Nighthaunt Spearhead — correct MM product page confirmed; NOT_AVAIL.
    '70-10': (
        'https://www.miniaturemarket.com/'
        'warhammer-age-sigmar-spearhead-nighthaunt-cursed-shacklehorde-gw-70-914.html',
        False, True,
    ),

    # 89-22 Gutrippaz — correct MM product page for GW SKU 89-70; out of stock.
    '89-22': (
        'https://www.miniaturemarket.com/gw-89-70.html',
        False, True,
    ),
}


# ===========================================================================
# NOBLE KNIGHT URL FIXES
# ===========================================================================
# Format: gw_sku -> (new_url, in_stock, not_available)
NK_FIXES = {
    # 70-10 Nighthaunt Spearhead — new NK listing found; NOT_AVAIL.
    #   Row may not exist yet; section 7 will create it if missing.
    '70-10': (
        'https://www.nobleknight.com/P/2148332055/Spearhead---Nighthaunt',
        False, True,
    ),

    # LESSON: 83-18 Chaos Warriors NK row was pointing to
    #   "Datacards---Chaos-Knights" at $7.95 — entirely wrong product.
    #   Fix to the correct Chaos Warriors page.
    '83-18': (
        'https://www.nobleknight.com/P/2148030863/Chaos-Warriors',
        False, True,
    ),
}


# ===========================================================================
# GAMES WORKSHOP URL FIXES
# ===========================================================================
# Format: gw_sku -> new_url
GW_URL_FIXES = {
    # 70-10: Clean 2025 product URL confirmed live on warhammer.com.
    '70-10': 'https://www.warhammer.com/en-US/shop/spearhead-cursed-shacklehorde-2025',
}


class Command(BaseCommand):
    """Sixth wave of March 2026 ThriftHammer DB corrections."""

    help = 'Apply Wave F batch corrections (March 2026).'

    def add_arguments(self, parser):
        """Add --dry-run flag to preview changes without saving."""
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Print planned changes without writing to the database.',
        )

    def handle(self, *args, **options):
        """Execute all Wave F corrections in order."""
        dry = options['dry_run']
        if dry:
            self.stdout.write(self.style.WARNING('DRY RUN — no changes will be saved.\n'))

        self._section_1_deactivate(dry)
        self._section_2_renames(dry)
        self._section_3_amazon_not_avail(dry)
        self._section_4_amazon_fixes(dry)
        self._section_5_ebay_fixes(dry)
        self._section_6_mm_fixes(dry)
        self._section_7_nk_fixes(dry)
        self._section_8_gw_url_fixes(dry)
        self._section_9_product_field_updates(dry)

        if dry:
            self.stdout.write(self.style.WARNING('\nDRY RUN complete — nothing was saved.'))
        else:
            self.stdout.write(self.style.SUCCESS('\nWave F complete.'))

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
        """Update or create a CurrentPrice record for the given product/retailer."""
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
        """Update the URL and stock flags on an existing price row."""
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
                f'  [dry] {label} → url=…{url[-40:]}  not_avail={not_available}'
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
        """Section 1: Deactivate duplicate SKUs (is_active → False)."""
        self.stdout.write('\n── Section 1: Deactivate duplicates ──')
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

    def _section_2_renames(self, dry):
        """Section 2: Rename products (update name + slug)."""
        self.stdout.write('\n── Section 2: Renames ──')
        for sku, (new_name, new_slug) in RENAMES.items():
            try:
                p = self._get_product(sku)
            except Product.DoesNotExist:
                continue
            old_name, old_slug = p.name, p.slug
            if dry:
                self.stdout.write(
                    f'  [dry] {sku} "{old_name}" → "{new_name}"'
                    f'  (slug: {old_slug} → {new_slug})'
                )
                continue
            p.name = new_name
            p.slug = new_slug
            p.save(update_fields=['name', 'slug'])
            self.stdout.write(f'  [ok] {sku} "{old_name}" → "{new_name}"')

    def _section_3_amazon_not_avail(self, dry):
        """Section 3: Mark Amazon prices as not_available."""
        self.stdout.write('\n── Section 3: Amazon NOT_AVAIL ──')
        amazon = Retailer.objects.get(name='Amazon')
        for sku in AMAZON_NOT_AVAIL:
            try:
                p = self._get_product(sku)
            except Product.DoesNotExist:
                continue
            self._mark_not_available(p, amazon, dry)

    def _section_4_amazon_fixes(self, dry):
        """Section 4: Apply corrected Amazon ASINs and prices."""
        self.stdout.write('\n── Section 4: Amazon price fixes ──')
        amazon = Retailer.objects.get(name='Amazon')
        for sku, (price, url, in_stock) in AMAZON_FIXES.items():
            try:
                p = self._get_product(sku)
            except Product.DoesNotExist:
                continue
            self._set_price(p, amazon, price, url, in_stock, dry=dry)

    def _section_5_ebay_fixes(self, dry):
        """Section 5: Apply corrected eBay listing IDs and prices."""
        self.stdout.write('\n── Section 5: eBay price fixes ──')
        ebay = Retailer.objects.get(name='eBay')
        for sku, (item_id, price) in EBAY_FIXES.items():
            url = f'https://www.ebay.com/itm/{item_id}'
            try:
                p = self._get_product(sku)
            except Product.DoesNotExist:
                continue
            self._set_price(p, ebay, price, url, True, dry=dry)

    def _section_6_mm_fixes(self, dry):
        """Section 6: Fix Miniature Market URLs."""
        self.stdout.write('\n── Section 6: Miniature Market URL fixes ──')
        mm = Retailer.objects.get(name='Miniature Market')
        for sku, (url, in_stock, not_available) in MM_FIXES.items():
            try:
                p = self._get_product(sku)
            except Product.DoesNotExist:
                continue
            self._update_retailer_url(p, mm, url, in_stock, not_available, dry)

    def _section_7_nk_fixes(self, dry):
        """Section 7: Fix Noble Knight URLs (create row for 70-10 if missing)."""
        self.stdout.write('\n── Section 7: Noble Knight URL fixes ──')
        nk = Retailer.objects.get(name='Noble Knight Games')
        for sku, (url, in_stock, not_available) in NK_FIXES.items():
            try:
                p = self._get_product(sku)
            except Product.DoesNotExist:
                continue
            if not CurrentPrice.objects.filter(product=p, retailer=nk).exists():
                # No row yet — create one (e.g. 70-10 Nighthaunt Spearhead).
                if dry:
                    self.stdout.write(
                        f'  [dry] {sku} / Noble Knight Games → CREATE  not_avail={not_available}'
                    )
                else:
                    CurrentPrice.objects.create(
                        product=p,
                        retailer=nk,
                        price=decimal.Decimal('0.00'),
                        url=url,
                        in_stock=False,
                        not_available=True,
                    )
                    self.stdout.write(
                        f'  [ok] {sku} / Noble Knight Games → created (NOT_AVAIL)'
                    )
            else:
                self._update_retailer_url(p, nk, url, in_stock, not_available, dry)

    def _section_8_gw_url_fixes(self, dry):
        """Section 8: Fix Games Workshop retailer URLs."""
        self.stdout.write('\n── Section 8: Games Workshop URL fixes ──')
        gw = Retailer.objects.get(name='Games Workshop')
        for sku, url in GW_URL_FIXES.items():
            try:
                p = self._get_product(sku)
            except Product.DoesNotExist:
                continue
            try:
                cp = CurrentPrice.objects.get(product=p, retailer=gw)
            except CurrentPrice.DoesNotExist:
                self.stdout.write(
                    f'  [skip] {sku} / Games Workshop — no row found'
                )
                continue
            if dry:
                self.stdout.write(
                    f'  [dry] {sku} / Games Workshop → url=…{url[-50:]}'
                )
                continue
            cp.url = url
            cp.save(update_fields=['url'])
            self.stdout.write(f'  [ok] {sku} / Games Workshop → url updated')

    def _section_9_product_field_updates(self, dry):
        """Section 9: Update eBay negative keywords and search name overrides."""
        self.stdout.write('\n── Section 9: Product field updates ──')
        updates = [
            # 90-10 Skaven Clanrats — searches surface vintage 1989 board-game
            # box sets that include "Clanrats" in their titles. Excluding "1989"
            # keeps results limited to the modern AoS plastic kit.
            ('90-10', 'ebay_negative_keywords', '1989'),

            # 50-10 Ork Boyz — eBay surfaces "Ork Lootas Boyz" listings that
            # pass keyword matching. Excluding "lootas" prevents false matches.
            ('50-10', 'ebay_negative_keywords', 'lootas'),

            # 50-16 Ork Deff Dread — set a specific eBay search name to avoid
            # Lootas confusion that previously caused the wrong ASIN to be assigned.
            ('50-16', 'ebay_search_name', 'Ork Deff Dread 40000'),
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
