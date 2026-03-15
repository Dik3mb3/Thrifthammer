"""
Management command: apply_batch_fixes_mar2026i

Ninth wave of March 2026 batch corrections for ThriftHammer.
Run after apply_batch_fixes_mar2026h.

Changes covered:
  Section 1  - Deactivate 1 SKU
               71-55 Stormcast Eternals Vanguard (duplicate starter set entry)
  Section 2  - Amazon NOT_AVAIL (2 products)
               96-11 Stormcast Eternals Liberators — no current product on Amazon
               96-14 Stormcast Eternals Lord-Celestant — no current product on Amazon
  Section 3  - Amazon price fixes (9 corrections / additions)
               70-09 Spearhead: Ossiarch Bonereapers B0D6N7B7GZ $127.51 (new)
               96-12 Knight-Judicator with Gryph-hounds B09FXBFW1P $31.46
               96-50 Vindictors B09K4JGTVX $51.00
               56-13 T'au Broadside Battlesuit B011KPL5BQ $53.03
               56-19 T'au Pathfinders B016S4S9OK $40.80
               43-30 Ahriman B09KFQYBJ8 $40.80
               43-02 Magnus the Red B09HJNFB65 $150.17
               51-06 Tyranid Carnifex B00HSS263G $104.88 (new)
               51-16 Tyranid Termagants B0CGV6V47P $40.80
  Section 4  - eBay price fixes (6 listings)
               70-04 Spearhead: Slaves to Darkness 137045926869 $125.99
               96-12 Knight-Judicator with Gryph-hounds 133886645829 $31.45
               56-25 T'au Combat Patrol 176351775345 $144.50
               56-19 T'au Pathfinders 136871790017 $40.00
               43-30 Ahriman 173676990524 $40.80
               43-38 Exalted Sorcerers 173463434432 $55.25
  Section 5  - Noble Knight price + URL fix (1 product)
               96-55 Praetors → $44.95 (correct URL)
  Section 6  - Games Workshop URL fixes (2 products)
               96-12 Knight-Judicator with Gryph-hounds → 2021 product page
               56-14 T'au Stealth Battlesuits → Kill Team XV26 2026 page
  Section 7  - Product rename (1 product)
               96-12 "Stormcast Eternals Judicators" →
               "Stormcast Eternals Knight-Judicator with Gryph-hounds"
               (slug updated to match)
  Section 8  - Product field updates (eBay negative keywords)
               56-25 T'au Combat Patrol: add 'spare parts' (filters parts listings)
               56-19 T'au Pathfinders: add 'datacards Apex' (filters wrong kits)
               43-02 Magnus the Red: add 'JoyToy' (filters action figures)

Usage:
    python manage.py apply_batch_fixes_mar2026i
    python manage.py apply_batch_fixes_mar2026i --dry-run
"""

import decimal

from django.core.management.base import BaseCommand
from django.utils.text import slugify

from prices.models import CurrentPrice
from products.models import Product, Retailer


# ===========================================================================
# SKUs TO DEACTIVATE (is_active → False)
# ===========================================================================
DEACTIVATE_SKUS = [
    # 71-55 "Stormcast Eternals Vanguard" — a duplicate starter-set entry that
    # shared the same Amazon ASIN as Judicators (1785813609, a rulebook).
    # Deactivating to clean up the product list.
    '71-55',
]


# ===========================================================================
# AMAZON: mark as NOT_AVAIL (no current listing on Amazon)
# ===========================================================================
AMAZON_NOT_AVAIL = [
    # 96-11 Liberators — previously linked to B0CJPDMR9C at $85.00; that ASIN
    # is not a current GW Liberators product. No valid replacement found.
    '96-11',
    # 96-14 Lord-Celestant — previously linked to B09CV9CD6J at $162.35; that
    # ASIN does not correspond to the current GW product. No valid replacement.
    '96-14',
]


# ===========================================================================
# AMAZON: correct ASINs with verified prices
# ===========================================================================
# Format: gw_sku -> (price_str, url, in_stock)
AMAZON_FIXES = {
    # ── AoS Spearhead ─────────────────────────────────────────────────────────
    # 70-09: Spearhead: Ossiarch Bonereapers — no Amazon price was previously
    #   set. B0D6N7B7GZ confirmed at $127.51 for this Spearhead box.
    '70-09': ('127.51', 'https://www.amazon.com/dp/B0D6N7B7GZ', True),

    # ── Stormcast Eternals ────────────────────────────────────────────────────
    # LESSON: 96-12 was seeded as "Judicators" with ASIN 1785813609 (a rulebook)
    #   at $22.72. The product is actually "Knight-Judicator with Gryph-hounds";
    #   B09FXBFW1P confirmed at $31.46 for the correct single-model plastic kit.
    #   Product is renamed in Section 7.
    '96-12': ('31.46',  'https://www.amazon.com/dp/B09FXBFW1P', True),

    # LESSON: 96-50 Vindictors was seeded with B0C1P2G6ZS at $35.00 — wrong
    #   ASIN. B09K4JGTVX confirmed at $51.00 for the correct 5-model kit.
    '96-50': ('51.00',  'https://www.amazon.com/dp/B09K4JGTVX', True),

    # ── T'au Empire ───────────────────────────────────────────────────────────
    # LESSON: 56-13 Broadside Battlesuit was seeded with B000CEQBSY at $55.25 —
    #   old/wrong ASIN. B011KPL5BQ confirmed at $53.03 for the current XV88 kit.
    '56-13': ('53.03',  'https://www.amazon.com/dp/B011KPL5BQ', True),

    # LESSON: 56-19 Pathfinders was seeded with B07KW5TRCL at $21.87 — wrong
    #   ASIN. B016S4S9OK confirmed at $40.80 for the correct Pathfinder Team box.
    '56-19': ('40.80',  'https://www.amazon.com/dp/B016S4S9OK', True),

    # ── Thousand Sons ─────────────────────────────────────────────────────────
    # LESSON: 43-30 Ahriman was seeded with B0B2PKL77J at $29.75 — wrong/cheap
    #   ASIN. B09KFQYBJ8 confirmed at $40.80 for the current single-model kit.
    '43-30': ('40.80',  'https://www.amazon.com/dp/B09KFQYBJ8', True),

    # LESSON: 43-02 Magnus the Red was seeded with B0F4QTPVS4 at $125.99 — wrong
    #   ASIN. B09HJNFB65 confirmed at $150.17 for the correct large plastic kit.
    #   JoyToy action figures contaminate searches; exclude in neg kw (Section 8).
    '43-02': ('150.17', 'https://www.amazon.com/dp/B09HJNFB65', True),

    # ── Tyranids ──────────────────────────────────────────────────────────────
    # 51-06 Carnifex — previously removed (comment noted "Broodlord ASIN wrong;
    #   no correct listing found"). B00HSS263G confirmed at $104.88 for the
    #   Carnifex Brood plastic kit; adding back as a new entry.
    '51-06': ('104.88', 'https://www.amazon.com/dp/B00HSS263G', True),

    # LESSON: 51-16 Termagants was seeded with B0D5ZSGDC3 at $22.65 — wrong
    #   ASIN. B0CGV6V47P confirmed at $40.80 for the 2023 Termagants box.
    '51-16': ('40.80',  'https://www.amazon.com/dp/B0CGV6V47P', True),
}


# ===========================================================================
# EBAY: correct listing IDs with verified prices
# ===========================================================================
# Format: gw_sku -> (ebay_item_id, price_str)
EBAY_FIXES = {
    # 70-04 Spearhead: Slaves to Darkness — listing 137045926869 verified at
    #   $125.99. Title: "Spearhead Slaves to Darkness Darkoath Raiders (2024)"
    '70-04': ('137045926869', '125.99'),

    # 96-12 Knight-Judicator with Gryph-hounds — listing 133886645829 verified
    #   at $31.45. Title: "Warhammer Age of Sigmar Knight-Judicator with
    #   Gryph-Hounds NIB"
    '96-12': ('133886645829', '31.45'),

    # 56-25 T'au Combat Patrol — listing 176351775345 verified at $144.50.
    #   Title: "(2024 ver.) Combat Patrol: Tau Empire Warhammer 40K"
    '56-25': ('176351775345', '144.50'),

    # 56-19 T'au Pathfinders — listing 136871790017 verified at $40.00.
    #   Title: "Games Workshop Warhammer 40K T'au Empire - Pathfinder Team
    #   56-09 NEW NIB Sealed"
    '56-19': ('136871790017', '40.00'),

    # 43-30 Ahriman — listing 173676990524 verified at $40.80.
    #   Title: "Ahriman Arch-Sorcerer of Tzeentch Chaos Space Marines
    #   Warhammer 40K NIB"
    '43-30': ('173676990524', '40.80'),

    # 43-38 Exalted Sorcerers — listing 173463434432 verified at $55.25.
    #   Title: "Exalted Sorcerers Thousand Sons Chaos Space Marines
    #   Warhammer 40K NIB"
    '43-38': ('173463434432', '55.25'),
}


# ===========================================================================
# NOBLE KNIGHT: price + URL fixes
# ===========================================================================
# Format: gw_sku -> (new_price_str, url, in_stock)
NK_PRICE_FIXES = {
    # LESSON: 96-55 Praetors had a wrong Noble Knight URL. Correct URL is
    #   /P/2147934892/Praetors; price confirmed at $44.95.
    '96-55': (
        '44.95',
        'https://www.nobleknight.com/P/2147934892/Praetors',
        True,
    ),
}


# ===========================================================================
# GAMES WORKSHOP URL FIXES
# ===========================================================================
# Format: gw_sku -> new_url
GW_URL_FIXES = {
    # 96-12 Knight-Judicator with Gryph-hounds — update to the correct 2021
    #   product page (previously pointed to Judicators page).
    '96-12': 'https://www.warhammer.com/en-US/shop/stormcast-eternals-knight-judicator-with-gryph-hounds-2021',

    # 56-14 T'au Stealth Battlesuits — update to the current Kill Team XV26
    #   Stealth Battlesuits 2026 product page.
    '56-14': 'https://www.warhammer.com/en-US/shop/kill-team-xv26-stealth-battlesuits-2026',
}


# ===========================================================================
# PRODUCT RENAMES
# ===========================================================================
# Format: gw_sku -> new_name
# Slug is recomputed automatically from the new name.
PRODUCT_RENAMES = {
    # LESSON: 96-12 was incorrectly named "Stormcast Eternals Judicators"
    #   (a 10-model bow-armed unit from an older edition).  The actual product
    #   in the DB is the single-model "Knight-Judicator with Gryph-hounds" kit,
    #   confirmed by the Amazon listing title, eBay listing, and GW product page.
    '96-12': 'Stormcast Eternals Knight-Judicator with Gryph-hounds',
}


class Command(BaseCommand):
    """Ninth wave of March 2026 ThriftHammer DB corrections."""

    help = 'Apply Wave I batch corrections (March 2026).'

    def add_arguments(self, parser):
        """Add --dry-run flag to preview changes without saving."""
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Print planned changes without writing to the database.',
        )

    def handle(self, *args, **options):
        """Execute all Wave I corrections in order."""
        dry = options['dry_run']
        if dry:
            self.stdout.write(self.style.WARNING('DRY RUN — no changes will be saved.\n'))

        self._section_1_deactivate(dry)
        self._section_2_amazon_not_avail(dry)
        self._section_3_amazon_fixes(dry)
        self._section_4_ebay_fixes(dry)
        self._section_5_nk_price_fixes(dry)
        self._section_6_gw_url_fixes(dry)
        self._section_7_product_renames(dry)
        self._section_8_product_field_updates(dry)

        if dry:
            self.stdout.write(self.style.WARNING('\nDRY RUN complete — nothing was saved.'))
        else:
            self.stdout.write(self.style.SUCCESS('\nWave I complete.'))

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
                'price': decimal.Decimal(price_str) if price_str else decimal.Decimal('0'),
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

    def _section_2_amazon_not_avail(self, dry):
        """Section 2: Mark Amazon entries as NOT_AVAIL (no valid listing)."""
        self.stdout.write('\n── Section 2: Amazon NOT_AVAIL ──')
        amazon = Retailer.objects.get(name='Amazon')
        for sku in AMAZON_NOT_AVAIL:
            try:
                p = self._get_product(sku)
            except Product.DoesNotExist:
                continue
            label = f'{sku} / Amazon'
            if dry:
                self.stdout.write(f'  [dry] {label} → NOT_AVAIL')
                continue
            obj, created = CurrentPrice.objects.update_or_create(
                product=p,
                retailer=amazon,
                defaults={
                    'price': decimal.Decimal('0'),
                    'url': '',
                    'in_stock': False,
                    'not_available': True,
                },
            )
            verb = 'created' if created else 'updated'
            self.stdout.write(f'  [ok] {label} → NOT_AVAIL ({verb})')

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

    def _section_5_nk_price_fixes(self, dry):
        """Section 5: Fix Noble Knight prices and URLs."""
        self.stdout.write('\n── Section 5: Noble Knight price + URL fixes ──')
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
                    f'  [dry] {label} → ${old_price} → ${price}  {url}'
                )
                continue
            cp.price = decimal.Decimal(price)
            cp.url = url
            cp.in_stock = in_stock
            cp.not_available = False
            cp.save(update_fields=['price', 'url', 'in_stock', 'not_available'])
            self.stdout.write(f'  [ok] {label} → ${old_price} → ${price}')

    def _section_6_gw_url_fixes(self, dry):
        """Section 6: Fix Games Workshop retailer URLs."""
        self.stdout.write('\n── Section 6: Games Workshop URL fixes ──')
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

    def _section_7_product_renames(self, dry):
        """Section 7: Rename products and update slugs."""
        self.stdout.write('\n── Section 7: Product renames ──')
        for sku, new_name in PRODUCT_RENAMES.items():
            try:
                p = self._get_product(sku)
            except Product.DoesNotExist:
                continue
            old_name = p.name
            new_slug = slugify(new_name)
            if dry:
                self.stdout.write(
                    f'  [dry] {sku} name: "{old_name}" → "{new_name}"'
                )
                self.stdout.write(
                    f'  [dry] {sku} slug: "{p.slug}" → "{new_slug}"'
                )
                continue
            p.name = new_name
            p.slug = new_slug
            p.save(update_fields=['name', 'slug'])
            self.stdout.write(f'  [ok] {sku} renamed → "{new_name}"')

    def _section_8_product_field_updates(self, dry):
        """Section 8: Update eBay negative keywords."""
        self.stdout.write('\n── Section 8: Product field updates ──')
        updates = [
            # 56-25 T'au Combat Patrol — eBay returns spare-parts/damaged lots
            # that pass keyword matching.  Excluding "spare parts" at query
            # level removes these from results.
            ('56-25', 'ebay_negative_keywords', 'spare parts'),

            # 56-19 T'au Pathfinders — eBay returns T'au Pathfinder Datacards
            # (a separate product) and "Apex" brand items that pass keyword
            # matching.  Excluding both at query level narrows to the correct kit.
            ('56-19', 'ebay_negative_keywords', 'datacards Apex'),

            # 43-02 Magnus the Red — JoyToy produces 1:18-scale action figures
            # including Magnus, which contaminate eBay search results.
            # Excluding "JoyToy" at query level removes these.
            ('43-02', 'ebay_negative_keywords', 'JoyToy'),
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
