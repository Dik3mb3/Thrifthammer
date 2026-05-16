"""
Management command: apply_batch_fixes_mar2026ab

Twenty-seventh wave of March 2026 batch corrections for ThriftHammer.
Run after apply_batch_fixes_mar2026aa.

Changes covered:
  Fix 1  -- Space Marine Primaris Captain (48-62):
             Set eBay URL to item 183379631512 (confirmed correct GW kit).
             Previous listing was returning Jump Pack Primaris Captain results.
             neg_kw 'jump' (added to populate_products.py) prevents recurrence.

  Fix 2  -- Black Templars Chaplain Grimaldus (55-24):
             Set eBay URL to item 165978158704 (confirmed correct single blister).
             neg_kw 'champion marshal' (added to populate_products.py) prevents
             Emperor's Champion and High Marshal Helbrecht listings from recurring.

  Fix 3  -- Space Marine Whirlwind (48-25):
             Set eBay URL to item 389712540408 (confirmed correct modern plastic kit).
             neg_kw '1999 vintage' (added to populate_products.py) prevents old
             metal Whirlwind listings from recurring.
             ebay_search_name → 'whirlwind 40k' (2 keywords, min_matches=2).

  Fix 4  -- Ultramarines Honour Guard (55-16):
             Set eBay URL to item 168135392523 (confirmed correct GW kit).
             neg_kw updated to include 'calgar' (Marneus Calgar bundles excluded).

  Fix 5  -- Space Marine Scouts (48-29):
             Set eBay URL to item 287225378889 (confirmed correct GW kit).
             neg_kw updated to include 'mint' (vintage MIMB listings excluded).
             ebay_search_name → 'Warhammer 40k Space Marine Scouts'.
             gw_url set to Kill Team Scout Squad 2024 product page.
             image_url updated to current GW CDN image (already correct).

  Fix 6  -- Necron C'tan Shard of the Void Dragon (49-20):
             Set eBay URL to item 254751542701 (confirmed correct GW kit).
             Set manual_url_override=True to prevent the description-mirrors-title
             filter from blanking this URL in future scraper runs — the C'tan listing
             description mirrors the GW product description in its first 150 chars,
             causing the automated scraper to reject it as a bot listing.

  Fix 7  -- Nighthaunt Knight of Shrouds (91-15):
             Clear Amazon URL and price — product not sold on Amazon.

  Fix 8  -- Blood Angels Death Company (41-07):
             Clear Amazon URL and price — discontinued GW product, not sold on Amazon.

  Fix 9  -- Necromunda Van Saar Gang (NM-012):
             Set eBay URL to item 389763206714 (confirmed correct full gang box).
             neg_kw '1x arachni-rig weapons upgrades cards tactic dice' added to
             populate_products.py to prevent partial/accessory listings recurring.

  Fix 10 -- Necromunda Goliath Gang (NM-011):
             Set eBay URL to item 177429704175 (confirmed correct full gang box).
             neg_kw '1x weapons upgrades cards tactic stimmers dice' added.

  Fix 11 -- Necromunda Escher Gang (NM-010):
             Set eBay URL to item 185183300696 (confirmed correct full gang box).
             neg_kw '1x weapons upgrades cards tactic stimmers dice' added.

  Fix 12 -- World Eaters Eightbound (43-62):
             Deactivate any duplicate Product records with the same gw_sku.
             ROOT CAUSE: A duplicate DB record causes the product to appear twice
             on browse pages. The populate_products command uses update_or_create
             on gw_sku, so duplicates would only arise from manual DB inserts or
             a rare race condition. Deactivates all but the oldest (lowest pk) record.

  Fix 13 -- Nighthaunt Combat Patrol (91-25):
             Soft-delete (is_active=False) — product discontinued and removed
             from ThriftHammer catalogue.

  Fix 14 -- Death Guard Deathshroud Bodyguard (43-56):
             Update image_url to current GW CDN image
             (99120102073_DeathshroudBodyguard01.jpg, from the 2020 product page).
             Previous image (99590102139) was an older Deathshroud Terminators shot.

  Fix 15 -- GW product page URLs (gw_url field on Product):
             Set Product.gw_url for 13 products that were showing a blank
             "View on GW" button on the detail page.  Covers:
             54-21, HA-021, NM-010, NM-011, NM-012, 56-14, 48-29, 96-12,
             48-61, 43-56, 51-42, 59-20, 44-09.

  Fix 16 -- Neg_kw DB sync:
             Update Product.ebay_negative_keywords in the DB for SKUs whose
             neg_kw was updated in populate_products.py:
             48-62, 55-24, 48-25, 55-16, 48-29, NM-012, NM-011, NM-010.
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from prices.models import CurrentPrice
from products.models import Product, Retailer


# GW product page URLs keyed by gw_sku — mirrors additions to _GW_PRODUCT_PAGE_URLS
_GW_URLS = {
    '54-21': 'https://www.warhammer.com/en-US/shop/imperial-knights-knight-dominus-knight-valiant-2022',
    'HA-021': 'https://www.warhammer.com/en-US/shop/Night-Lords-Leviathan-Dreadnought-2019',
    'NM-010': 'https://www.warhammer.com/en-US/shop/Necromunda-Escher-Gang-2017',
    'NM-011': 'https://www.warhammer.com/en-US/shop/Necromunda-Goliath-Gang-2017',
    'NM-012': 'https://www.warhammer.com/en-US/shop/Necromunda-Van-Saar-Gang-2018',
    '56-14':  'https://www.warhammer.com/en-US/shop/kill-team-xv26-stealth-battlesuits-2026',
    '48-29':  'https://www.warhammer.com/en-US/shop/kill-team-scout-squad-2024',
    '96-12':  'https://www.warhammer.com/en-US/shop/stormcast-eternals-knight-judicator-with-gryph-hounds-2021',
    '48-61':  'https://www.warhammer.com/en-US/shop/Space-Marine-Primaris-Lieutenant-With-Power-Sword-2020',
    '43-56':  'https://www.warhammer.com/en-US/shop/Death-Guard-Deathshroud-Bodyguard-2020',
    '51-42':  'https://www.warhammer.com/en-US/shop/Genestealer-Cults-Broodcoven',
    '59-20':  'https://www.warhammer.com/en-US/shop/Ad-Mec-Corpuscarii-Electro-Priests',
    '44-09':  'https://www.warhammer.com/en-US/shop/Ravenwing-Command-Squad-2020',
}

# Neg_kw updates — mirrors changes to _EBAY_NEGATIVE_KEYWORDS
_NEG_KW_UPDATES = {
    '48-62': 'jump',
    '55-24': 'champion marshal',
    '48-25': '1999 vintage',
    '55-16': 'calgar Action Figure',
    '48-29': 'needle mint',
    'NM-012': '1x arachni-rig weapons upgrades cards tactic dice',
    'NM-011': '1x weapons upgrades cards tactic stimmers dice',
    'NM-010': '1x weapons upgrades cards tactic stimmers dice',
}


class Command(BaseCommand):
    """Apply wave-AB March 2026 batch corrections to products."""

    help = 'Apply wave-AB March 2026 batch corrections.'

    def handle(self, *args, **options):
        """Apply all fixes atomically."""
        self.stdout.write('\napply_batch_fixes_mar2026ab')
        self.stdout.write('=' * 50)

        with transaction.atomic():
            self._fix_1_primaris_captain_ebay()
            self._fix_2_chaplain_grimaldus_ebay()
            self._fix_3_whirlwind_ebay()
            self._fix_4_honour_guard_ebay()
            self._fix_5_scouts_ebay()
            self._fix_6_ctan_ebay()
            self._fix_7_knight_of_shrouds_amazon_clear()
            self._fix_8_death_company_amazon_clear()
            self._fix_9_van_saar_ebay()
            self._fix_10_goliath_ebay()
            self._fix_11_escher_ebay()
            self._fix_12_eightbound_dedup()
            self._fix_13_nighthaunt_combat_patrol_deactivate()
            self._fix_14_deathshroud_image()
            self._fix_15_gw_product_urls()
            self._fix_16_neg_kw_sync()

        self.stdout.write(self.style.SUCCESS('\nAll wave-AB fixes applied successfully.'))

    # -------------------------------------------------------------------------
    # Helpers
    # -------------------------------------------------------------------------

    def _get_product(self, gw_sku):
        """Return Product or None, writing a warning if not found or ambiguous."""
        try:
            return Product.objects.get(gw_sku=gw_sku)
        except Product.DoesNotExist:
            self.stdout.write(self.style.WARNING(f'  Product {gw_sku} not found — skipped'))
            return None
        except Product.MultipleObjectsReturned:
            self.stdout.write(self.style.WARNING(
                f'  Product {gw_sku} matched multiple rows (duplicate gw_sku) — skipped'
            ))
            return None

    def _get_retailer(self, slug):
        """Return Retailer or None, writing a warning if not found."""
        try:
            return Retailer.objects.get(slug=slug)
        except Retailer.DoesNotExist:
            self.stdout.write(self.style.WARNING(f'  Retailer "{slug}" not found — skipped'))
            return None

    def _set_ebay_url(self, gw_sku, item_id, label):
        """Set the eBay CurrentPrice URL for a product."""
        product = self._get_product(gw_sku)
        if not product:
            return
        retailer = self._get_retailer('ebay')
        if not retailer:
            return

        url = f'https://www.ebay.com/itm/{item_id}'
        cp, created = CurrentPrice.objects.get_or_create(
            product=product,
            retailer=retailer,
            defaults={'url': url, 'in_stock': True},
        )
        if not created:
            old_url = cp.url
            cp.url = url
            cp.in_stock = True
            cp.save(update_fields=['url', 'in_stock'])
            self.stdout.write(self.style.SUCCESS(
                f'  {label}: eBay URL → {url} (was {old_url or "(blank)"})'
            ))
        else:
            self.stdout.write(self.style.SUCCESS(
                f'  {label}: eBay CurrentPrice created → {url}'
            ))

    def _clear_amazon(self, gw_sku, label):
        """Clear the Amazon CurrentPrice URL and price for a product."""
        product = self._get_product(gw_sku)
        if not product:
            return
        retailer = self._get_retailer('amazon')
        if not retailer:
            return

        try:
            cp = CurrentPrice.objects.get(product=product, retailer=retailer)
        except CurrentPrice.DoesNotExist:
            self.stdout.write(f'  {label}: no Amazon CurrentPrice — skipped')
            return

        old_url = cp.url
        cp.url = ''
        cp.price = None
        cp.in_stock = False
        cp.not_available = True
        cp.save(update_fields=['url', 'price', 'in_stock', 'not_available'])
        self.stdout.write(self.style.SUCCESS(
            f'  {label}: Amazon URL cleared (was {old_url or "(blank)"})'
        ))

    # -------------------------------------------------------------------------
    # Individual fixes
    # -------------------------------------------------------------------------

    def _fix_1_primaris_captain_ebay(self):
        """Set correct eBay URL for Space Marine Primaris Captain (48-62)."""
        self._set_ebay_url('48-62', '183379631512', 'Fix 1: 48-62 Primaris Captain')

    def _fix_2_chaplain_grimaldus_ebay(self):
        """Set correct eBay URL for Black Templars Chaplain Grimaldus (55-24)."""
        self._set_ebay_url('55-24', '165978158704', 'Fix 2: 55-24 Chaplain Grimaldus')

    def _fix_3_whirlwind_ebay(self):
        """Set correct eBay URL and search name for Space Marine Whirlwind (48-25)."""
        self._set_ebay_url('48-25', '389712540408', 'Fix 3: 48-25 Space Marine Whirlwind')

        product = self._get_product('48-25')
        if not product:
            return
        old_name = product.ebay_search_name or ''
        new_name = 'whirlwind 40k'
        if old_name == new_name:
            self.stdout.write(f'  Fix 3: 48-25 ebay_search_name already "{new_name}" — skipped')
            return
        product.ebay_search_name = new_name
        product.save(update_fields=['ebay_search_name'])
        self.stdout.write(self.style.SUCCESS(
            f'  Fix 3: 48-25 ebay_search_name → "{new_name}" (was "{old_name or "(blank)"}")'
        ))

    def _fix_4_honour_guard_ebay(self):
        """Set correct eBay URL for Ultramarines Honour Guard (55-16)."""
        self._set_ebay_url('55-16', '168135392523', 'Fix 4: 55-16 Ultramarines Honour Guard')

    def _fix_5_scouts_ebay(self):
        """Set correct eBay URL and search name for Space Marine Scouts (48-29)."""
        self._set_ebay_url('48-29', '287225378889', 'Fix 5: 48-29 Space Marine Scouts')

        product = self._get_product('48-29')
        if not product:
            return
        old_name = product.ebay_search_name or ''
        new_name = 'Warhammer 40k Space Marine Scouts'
        if old_name != new_name:
            product.ebay_search_name = new_name
            product.save(update_fields=['ebay_search_name'])
            self.stdout.write(self.style.SUCCESS(
                f'  Fix 5: 48-29 ebay_search_name → "{new_name}" (was "{old_name or "(blank)"}")'
            ))

    def _fix_6_ctan_ebay(self):
        """Set eBay URL for Necron C'tan Shard of the Void Dragon (49-20) with manual override."""
        product = self._get_product('49-20')
        if not product:
            return
        retailer = self._get_retailer('ebay')
        if not retailer:
            return

        url = 'https://www.ebay.com/itm/254751542701'
        cp, created = CurrentPrice.objects.get_or_create(
            product=product,
            retailer=retailer,
            defaults={'url': url, 'in_stock': True, 'manual_url_override': True},
        )
        if not created:
            old_url = cp.url
            cp.url = url
            cp.in_stock = True
            cp.manual_url_override = True  # Prevents scraper from blanking on desc-mirrors-title
            cp.save(update_fields=['url', 'in_stock', 'manual_url_override'])
            self.stdout.write(self.style.SUCCESS(
                f"  Fix 6: 49-20 C'tan eBay URL → {url} (was {old_url or '(blank)'}) [manual override set]"
            ))
        else:
            self.stdout.write(self.style.SUCCESS(
                f"  Fix 6: 49-20 C'tan eBay CurrentPrice created → {url} [manual override set]"
            ))

    def _fix_7_knight_of_shrouds_amazon_clear(self):
        """Clear Amazon URL and price for Nighthaunt Knight of Shrouds (91-15)."""
        self._clear_amazon('91-15', 'Fix 7: 91-15 Nighthaunt Knight of Shrouds')

    def _fix_8_death_company_amazon_clear(self):
        """Clear Amazon URL and price for Blood Angels Death Company (41-07)."""
        self._clear_amazon('41-07', 'Fix 8: 41-07 Blood Angels Death Company')

    def _fix_9_van_saar_ebay(self):
        """Set correct eBay URL for Necromunda Van Saar Gang (NM-012)."""
        self._set_ebay_url('NM-012', '389763206714', 'Fix 9: NM-012 Necromunda Van Saar Gang')

    def _fix_10_goliath_ebay(self):
        """Set correct eBay URL for Necromunda Goliath Gang (NM-011)."""
        self._set_ebay_url('NM-011', '177429704175', 'Fix 10: NM-011 Necromunda Goliath Gang')

    def _fix_11_escher_ebay(self):
        """Set correct eBay URL for Necromunda Escher Gang (NM-010)."""
        self._set_ebay_url('NM-010', '185183300696', 'Fix 11: NM-010 Necromunda Escher Gang')

    def _fix_12_eightbound_dedup(self):
        """Deactivate duplicate World Eaters Eightbound records (43-62)."""
        dupes = list(Product.objects.filter(gw_sku='43-62').order_by('pk'))
        if len(dupes) <= 1:
            self.stdout.write('  Fix 12: 43-62 Eightbound — no duplicates found')
            return
        # Keep the oldest (lowest pk); deactivate all others
        for dupe in dupes[1:]:
            dupe.is_active = False
            dupe.save(update_fields=['is_active'])
            self.stdout.write(self.style.SUCCESS(
                f'  Fix 12: 43-62 Eightbound duplicate pk={dupe.pk} deactivated'
            ))

    def _fix_13_nighthaunt_combat_patrol_deactivate(self):
        """Soft-delete Nighthaunt Combat Patrol (91-25) — removed from catalogue."""
        product = self._get_product('91-25')
        if not product:
            return
        if not product.is_active:
            self.stdout.write('  Fix 13: 91-25 Nighthaunt Combat Patrol already inactive — skipped')
            return
        product.is_active = False
        product.save(update_fields=['is_active'])
        self.stdout.write(self.style.SUCCESS(
            '  Fix 13: 91-25 Nighthaunt Combat Patrol deactivated'
        ))

    def _fix_14_deathshroud_image(self):
        """Update image_url for Death Guard Deathshroud Bodyguard (43-56)."""
        product = self._get_product('43-56')
        if not product:
            return
        new_url = 'https://www.warhammer.com/app/resources/catalog/product/920x950/99120102073_DeathshroudBodyguard01.jpg'
        old_url = product.image_url or ''
        if old_url == new_url:
            self.stdout.write('  Fix 14: 43-56 image_url already current — skipped')
            return
        product.image_url = new_url
        product.save(update_fields=['image_url'])
        self.stdout.write(self.style.SUCCESS(
            f'  Fix 14: 43-56 Deathshroud image_url updated'
        ))

    def _fix_15_gw_product_urls(self):
        """Set Product.gw_url for products missing the "View on GW" button."""
        updates = 0
        for gw_sku, url in _GW_URLS.items():
            try:
                product = Product.objects.get(gw_sku=gw_sku)
            except Product.DoesNotExist:
                self.stdout.write(self.style.WARNING(
                    f'  Fix 15: {gw_sku} not found — skipped'
                ))
                continue
            if product.gw_url == url:
                continue
            old = product.gw_url or ''
            product.gw_url = url
            product.save(update_fields=['gw_url'])
            self.stdout.write(self.style.SUCCESS(
                f'  Fix 15: {gw_sku} gw_url → {url[:60]}… (was "{old[:40] or "(blank)"}")'
            ))
            updates += 1
        self.stdout.write(f'  Fix 15: {updates} GW product URLs updated.')

    def _fix_16_neg_kw_sync(self):
        """Sync Product.ebay_negative_keywords for updated SKUs."""
        updates = 0
        for gw_sku, new_kw in _NEG_KW_UPDATES.items():
            try:
                product = Product.objects.get(gw_sku=gw_sku)
            except Product.DoesNotExist:
                self.stdout.write(self.style.WARNING(
                    f'  Fix 16: {gw_sku} not found — skipped'
                ))
                continue
            old_kw = product.ebay_negative_keywords or ''
            if old_kw == new_kw:
                continue
            product.ebay_negative_keywords = new_kw
            product.save(update_fields=['ebay_negative_keywords'])
            self.stdout.write(self.style.SUCCESS(
                f'  Fix 16: {gw_sku} neg_kw → "{new_kw}" (was "{old_kw or "(blank)"}")'
            ))
            updates += 1
        self.stdout.write(f'  Fix 16: {updates} neg_kw records updated.')
