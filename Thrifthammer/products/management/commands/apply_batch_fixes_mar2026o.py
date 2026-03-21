"""
Management command: apply_batch_fixes_mar2026o

Fifteenth wave of March 2026 batch corrections for ThriftHammer.
Run after apply_batch_fixes_mar2026n.

Changes covered:
  Fix 1  -- Imperial Knight Armigers (54-20): Update image URL
             Old URL was 404; replaced with current GW CDN asset.

  Fix 2  -- Imperial Knight Dominus (54-21):
             - Add neg_kw "magnetizing" to block magnetizing-kit eBay listings
             - Update GW URL to direct product page
             - Update image URL to current GW CDN asset

  Fix 3  -- Legiones Astartes Predator (HA-012): Correct eBay URL
             Old item: 305653373032   New item: 127366089879

  Fix 4  -- Leviathan (10th Edition Starter Set) (40-02): Deactivate

  Fix 5  -- Marneus Calgar (55-12): Correct Amazon price -> $47.18

  Fix 6  -- Necromunda Escher Gang (NM-010):
             - Correct eBay URL (old: 275982366253, new: 185183300696)
             - Update GW URL to direct product page

  Fix 7  -- Necromunda Goliath Gang (NM-011):
             - Correct eBay URL (old: 116057319462, new: 256911689520)
             - Update GW URL to direct product page

  Fix 8  -- Necromunda Van Saar Gang (NM-012):
             - Correct eBay URL (old: 166509615348, new: 183426792302)

  Fix 9  -- Necron C'tan Shard of the Void Dragon (49-20):
             - Correct eBay URL (old: 317801197991, new: 254751542701)

  Fix 10 -- Necron Flayed Ones (49-17):
             - Add neg_kw "2004" to block old 2004-era metal model listings
             - Correct eBay URL (old: 227221279831, new: 177543986299)

Usage:
    python manage.py apply_batch_fixes_mar2026o
    python manage.py apply_batch_fixes_mar2026o --dry-run
"""

import decimal

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Product, Retailer


class Command(BaseCommand):
    """Fifteenth wave of March 2026 ThriftHammer DB corrections."""

    help = (
        'Apply Wave O batch corrections (March 2026) -- '
        'Imperial Knights, Legiones Predator, Leviathan deactivate, '
        'Marneus Amazon price, Necromunda eBay/GW URLs, Necron neg_kw/URLs.'
    )

    def add_arguments(self, parser):
        """Add --dry-run flag to preview changes without saving."""
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Print planned changes without writing to the database.',
        )

    def handle(self, *args, **options):
        """Execute all Wave O corrections in order."""
        dry = options['dry_run']
        if dry:
            self.stdout.write(self.style.WARNING('DRY RUN -- no changes will be saved.\n'))

        self._fix_1_armigers_image(dry)
        self._fix_2_dominus(dry)
        self._fix_3_legiones_predator_ebay(dry)
        self._fix_4_leviathan_deactivate(dry)
        self._fix_5_calgar_amazon_price(dry)
        self._fix_6_necromunda_escher(dry)
        self._fix_7_necromunda_goliath(dry)
        self._fix_8_necromunda_van_saar(dry)
        self._fix_9_ctan_ebay(dry)
        self._fix_10_flayed_ones(dry)

        if dry:
            self.stdout.write(self.style.WARNING('\nDRY RUN complete -- nothing was saved.'))
        else:
            self.stdout.write(self.style.SUCCESS('\nWave O complete.'))

    # -----------------------------------------------------------------------
    # Helpers
    # -----------------------------------------------------------------------

    def _get_product(self, gw_sku):
        """Fetch a product by gw_sku, writing an error and returning None if missing."""
        try:
            return Product.objects.get(gw_sku=gw_sku)
        except Product.DoesNotExist:
            self.stderr.write(self.style.ERROR(f'  ERROR: Product {gw_sku} not found.'))
            return None

    def _set_url(self, product, retailer_name, new_url, dry):
        """
        Update a CurrentPrice URL for a given retailer.

        Creates the row if it does not exist; skips if URL already matches.
        """
        try:
            retailer = Retailer.objects.get(name=retailer_name)
        except Retailer.DoesNotExist:
            self.stderr.write(
                self.style.ERROR(f'  ERROR: Retailer "{retailer_name}" not found.')
            )
            return

        cp, created = CurrentPrice.objects.get_or_create(
            product=product,
            retailer=retailer,
            defaults={'price': None, 'in_stock': False, 'url': new_url},
        )
        if created:
            self.stdout.write(f'  [ok] Created {retailer_name} entry: {new_url[:70]}')
            return

        if cp.url == new_url:
            self.stdout.write(f'  [skip] {retailer_name}: URL already correct')
            return

        old_url = cp.url or '(blank)'
        if dry:
            self.stdout.write(
                f'  [dry] {retailer_name}: {old_url[:60]}\n'
                f'             -> {new_url[:60]}'
            )
            return

        cp.url = new_url
        cp.save(update_fields=['url'])
        self.stdout.write(f'  [ok] {retailer_name}: {old_url[:55]} -> {new_url[:55]}')

    def _add_neg_kw(self, product, new_kw, dry):
        """
        Append new_kw to product.ebay_negative_keywords if not already present.

        new_kw may be a single word or a space-separated list of words; each
        word is treated as an independent keyword by the eBay client.
        """
        current = (product.ebay_negative_keywords or '').strip()
        existing = set(current.split()) if current else set()
        to_add = [w for w in new_kw.split() if w not in existing]

        if not to_add:
            self.stdout.write(f'  [skip] neg_kw already contains "{new_kw}"')
            return

        new_val = (current + ' ' + ' '.join(to_add)).strip() if current else ' '.join(to_add)
        if dry:
            self.stdout.write(
                f'  [dry] neg_kw: "{current}" -> "{new_val}"'
            )
            return
        product.ebay_negative_keywords = new_val
        product.save(update_fields=['ebay_negative_keywords'])
        self.stdout.write(f'  [ok] neg_kw: "{current or "(empty)"}" -> "{new_val}"')

    def _set_image(self, product, new_url, dry):
        """Update product.image_url if different."""
        if product.image_url == new_url:
            self.stdout.write('  [skip] image_url already correct')
            return
        old = product.image_url or '(none)'
        if dry:
            self.stdout.write(f'  [dry] image_url: {old[:60]} -> {new_url[:60]}')
            return
        product.image_url = new_url
        product.save(update_fields=['image_url'])
        self.stdout.write(f'  [ok] image_url -> {new_url[:60]}')

    # -----------------------------------------------------------------------
    # Fixes
    # -----------------------------------------------------------------------

    def _fix_1_armigers_image(self, dry):
        """Fix 1: Update Imperial Knight Armigers image URL (54-20)."""
        self.stdout.write('\nFix 1: Imperial Knight Armigers -- image URL')
        p = self._get_product('54-20')
        if p is None:
            return
        # Old URL (ArmigerWarglaivesNEW01.jpg) has been removed from GW CDN.
        # Confirmed working replacement from live GW product page 2026-03-21.
        self._set_image(
            p,
            'https://www.warhammer.com/app/resources/catalog/product/920x950/'
            '99120108019_ImperialKnightsArmiger01.jpg',
            dry,
        )

    def _fix_2_dominus(self, dry):
        """Fix 2: Imperial Knight Dominus -- neg_kw, GW URL, image URL (54-21)."""
        self.stdout.write('\nFix 2: Imperial Knight Dominus -- neg_kw + GW URL + image')
        p = self._get_product('54-21')
        if p is None:
            return
        # Block eBay listings for "magnetizing kit" (magnetizing magnets conversion)
        # -- these sell loose, magnet-drilled models, not the sealed retail box.
        self._add_neg_kw(p, 'magnetizing', dry)
        # Update GW URL to the direct product page (was generic search fallback)
        self._set_url(
            p, 'Games Workshop',
            'https://www.warhammer.com/en-WW/shop/'
            'imperial-knights-knight-dominus-knight-castellan-2022',
            dry,
        )
        # Update image to current GW CDN asset
        self._set_image(
            p,
            'https://www.warhammer.com/app/resources/catalog/product/920x950/'
            '99120108016_IKCastellan01.jpg',
            dry,
        )

    def _fix_3_legiones_predator_ebay(self, dry):
        """Fix 3: Correct eBay URL for Legiones Astartes Predator (HA-012)."""
        self.stdout.write('\nFix 3: Legiones Astartes Predator -- eBay URL')
        p = self._get_product('HA-012')
        if p:
            self._set_url(p, 'eBay', 'https://www.ebay.com/itm/127366089879', dry)

    def _fix_4_leviathan_deactivate(self, dry):
        """Fix 4: Deactivate Leviathan (10th Edition Starter Set) (40-02)."""
        self.stdout.write('\nFix 4: Leviathan (10th Edition Starter Set) -- deactivate')
        p = self._get_product('40-02')
        if p is None:
            return
        if not p.is_active:
            self.stdout.write('  [skip] Already inactive')
            return
        if dry:
            self.stdout.write(f'  [dry] "{p.name}" -- is_active: True -> False')
            return
        p.is_active = False
        p.save(update_fields=['is_active'])
        self.stdout.write(self.style.SUCCESS(f'  [ok] "{p.name}" deactivated'))

    def _fix_5_calgar_amazon_price(self, dry):
        """Fix 5: Correct Amazon price for Marneus Calgar (55-12) -> $47.18."""
        self.stdout.write('\nFix 5: Marneus Calgar -- Amazon price')
        p = self._get_product('55-12')
        if p is None:
            return
        try:
            retailer = Retailer.objects.get(name='Amazon')
            cp = CurrentPrice.objects.get(product=p, retailer=retailer)
        except (Retailer.DoesNotExist, CurrentPrice.DoesNotExist):
            self.stderr.write(self.style.ERROR('  ERROR: Amazon price row not found for 55-12'))
            return
        new_price = decimal.Decimal('47.18')
        if cp.price == new_price:
            self.stdout.write('  [skip] Price already $47.18')
            return
        if dry:
            self.stdout.write(f'  [dry] Amazon price: {cp.price} -> {new_price}')
            return
        old_price = cp.price
        cp.price = new_price
        cp.save(update_fields=['price'])
        self.stdout.write(f'  [ok] Amazon price: {old_price} -> {new_price}')

    def _fix_6_necromunda_escher(self, dry):
        """Fix 6: Necromunda Escher Gang -- eBay URL + GW URL (NM-010)."""
        self.stdout.write('\nFix 6: Necromunda Escher Gang -- eBay + GW URLs')
        p = self._get_product('NM-010')
        if p is None:
            return
        self._set_url(p, 'eBay', 'https://www.ebay.com/itm/185183300696', dry)
        self._set_url(
            p, 'Games Workshop',
            'https://www.warhammer.com/en-WW/shop/Necromunda-Escher-Gang-2017',
            dry,
        )

    def _fix_7_necromunda_goliath(self, dry):
        """Fix 7: Necromunda Goliath Gang -- eBay URL + GW URL (NM-011)."""
        self.stdout.write('\nFix 7: Necromunda Goliath Gang -- eBay + GW URLs')
        p = self._get_product('NM-011')
        if p is None:
            return
        self._set_url(p, 'eBay', 'https://www.ebay.com/itm/256911689520', dry)
        self._set_url(
            p, 'Games Workshop',
            'https://www.warhammer.com/en-WW/shop/Necromunda-Goliath-Gang-2017',
            dry,
        )

    def _fix_8_necromunda_van_saar(self, dry):
        """Fix 8: Necromunda Van Saar Gang -- eBay URL (NM-012)."""
        self.stdout.write('\nFix 8: Necromunda Van Saar Gang -- eBay URL')
        p = self._get_product('NM-012')
        if p:
            self._set_url(p, 'eBay', 'https://www.ebay.com/itm/183426792302', dry)

    def _fix_9_ctan_ebay(self, dry):
        """Fix 9: Necron C'tan Shard of the Void Dragon -- eBay URL (49-20)."""
        self.stdout.write('\nFix 9: Necron C\'tan Shard of the Void Dragon -- eBay URL')
        p = self._get_product('49-20')
        if p:
            self._set_url(p, 'eBay', 'https://www.ebay.com/itm/254751542701', dry)

    def _fix_10_flayed_ones(self, dry):
        """Fix 10: Necron Flayed Ones -- add neg_kw '2004' + correct eBay URL (49-17)."""
        self.stdout.write('\nFix 10: Necron Flayed Ones -- neg_kw + eBay URL')
        p = self._get_product('49-17')
        if p is None:
            return
        # Block listings for the 2004-era metal model, which sells much cheaper
        # and would undercut the price of the current plastic kit.
        self._add_neg_kw(p, '2004', dry)
        self._set_url(p, 'eBay', 'https://www.ebay.com/itm/177543986299', dry)
