"""
Management command: apply_batch_fixes_mar2026u

Twenty-first wave of March 2026 batch corrections for ThriftHammer.
Run after apply_batch_fixes_mar2026t.

Changes covered:
  Fix 1  -- Thousand Sons Scarab Occult Terminators (43-36):
             - Correct eBay URL (old: 406383869535 at $36.99, new: 356204431370)
             - neg_kw "4x" (SKU-specific only)
               Blocks "4x Scarab Occult Terminators" partial-squad listings
               (sellers breaking up kits and listing 4 models instead of the
               standard 5-man sealed box).

  Fix 2  -- Warcry: Red Harvest:
             ** NOT IN DB — product was never seeded or has already been removed.
             ** Nothing to deactivate; this fix is a no-op with a logged notice.

  Fix 3  -- World Eaters Angron (43-04):
             - GW price corrected: $145.00 → $175.00 (GW URL is fine).
               GW raised the retail price after the initial release.  The
               product.msrp and the Games Workshop CurrentPrice.price are both
               updated so eBay price-floor calculations and display remain
               consistent.

  Fix 4  -- World Eaters Berzerkers (43-60):
             - Correct eBay URL (old: 317907440877 at $29.99, new: 397740814391)
             - neg_kw "kharn" (SKU-specific only)
               Blocks "Kharn the Betrayer" special-character listings and
               "World Eaters Berzerkers with Kharn" bundle listings that share
               enough Berzerker keywords to pass match threshold but are a
               different (usually more expensive) product.

Usage:
    python manage.py apply_batch_fixes_mar2026u
    python manage.py apply_batch_fixes_mar2026u --dry-run
"""

import decimal

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Product, Retailer


class Command(BaseCommand):
    """Twenty-first wave of March 2026 ThriftHammer DB corrections."""

    help = (
        'Apply Wave U batch corrections (March 2026) -- '
        'Scarab Occult eBay fix, Angron GW price fix, '
        'Berzerkers eBay fix.'
    )

    def add_arguments(self, parser):
        """Add --dry-run flag to preview changes without saving."""
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Print planned changes without writing to the database.',
        )

    def handle(self, *args, **options):
        """Execute all Wave U corrections in order."""
        dry = options['dry_run']
        if dry:
            self.stdout.write(self.style.WARNING('DRY RUN -- no changes will be saved.\n'))

        self._fix_1_scarab_occult(dry)
        self._fix_2_red_harvest_noop()
        self._fix_3_angron_gw_price(dry)
        self._fix_4_berzerkers(dry)

        if dry:
            self.stdout.write(self.style.WARNING('\nDRY RUN complete -- nothing was saved.'))
        else:
            self.stdout.write(self.style.SUCCESS('\nWave U complete.'))

    # -----------------------------------------------------------------------
    # Helpers
    # -----------------------------------------------------------------------

    def _get_product(self, gw_sku):
        """Fetch a product by gw_sku; write an error and return None if missing."""
        try:
            return Product.objects.get(gw_sku=gw_sku)
        except Product.DoesNotExist:
            self.stderr.write(self.style.ERROR(f'  ERROR: Product {gw_sku} not found.'))
            return None

    def _set_url(self, product, retailer_name, new_url, dry):
        """Update a CurrentPrice URL; create row if missing; skip if already correct."""
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
                f'  [dry] {retailer_name}: {old_url[:55]}\n'
                f'             -> {new_url[:55]}'
            )
            return

        cp.url = new_url
        cp.save(update_fields=['url'])
        self.stdout.write(f'  [ok] {retailer_name}: {old_url[:50]} -> {new_url[:50]}')

    def _set_price(self, product, retailer_name, new_price, dry):
        """
        Update a CurrentPrice.price; also updates product.msrp when retailer
        is 'Games Workshop' (GW price IS the MSRP for this project).

        new_price must be a Decimal or a string convertible to Decimal.
        """
        new_price = decimal.Decimal(str(new_price))
        try:
            retailer = Retailer.objects.get(name=retailer_name)
        except Retailer.DoesNotExist:
            self.stderr.write(
                self.style.ERROR(f'  ERROR: Retailer "{retailer_name}" not found.')
            )
            return

        try:
            cp = CurrentPrice.objects.get(product=product, retailer=retailer)
        except CurrentPrice.DoesNotExist:
            self.stderr.write(
                self.style.ERROR(
                    f'  ERROR: No CurrentPrice row for {product.gw_sku} / {retailer_name}.'
                )
            )
            return

        old_price = cp.price
        if old_price == new_price:
            self.stdout.write(f'  [skip] {retailer_name} price already ${new_price}')
        else:
            if dry:
                self.stdout.write(
                    f'  [dry] {retailer_name} price: ${old_price} -> ${new_price}'
                )
            else:
                cp.price = new_price
                cp.save(update_fields=['price'])
                self.stdout.write(f'  [ok] {retailer_name} price: ${old_price} -> ${new_price}')

        # GW price IS the MSRP — keep product.msrp in sync.
        if retailer_name == 'Games Workshop':
            old_msrp = product.msrp
            if old_msrp == new_price:
                self.stdout.write(f'  [skip] product.msrp already ${new_price}')
            else:
                if dry:
                    self.stdout.write(
                        f'  [dry] product.msrp: ${old_msrp} -> ${new_price}'
                    )
                else:
                    product.msrp = new_price
                    product.save(update_fields=['msrp'])
                    self.stdout.write(f'  [ok] product.msrp: ${old_msrp} -> ${new_price}')

    def _add_neg_kw(self, product, new_kw, dry):
        """
        Append new_kw word(s) to product.ebay_negative_keywords if not already present.

        new_kw is space-separated; each word is checked independently by the eBay
        client.  Words already present are skipped.
        """
        current = (product.ebay_negative_keywords or '').strip()
        existing = {w.lower() for w in current.split()} if current else set()
        to_add = [w for w in new_kw.split() if w.lower() not in existing]

        if not to_add:
            self.stdout.write(f'  [skip] neg_kw already contains: "{new_kw}"')
            return

        new_val = (current + ' ' + ' '.join(to_add)).strip() if current else ' '.join(to_add)
        if dry:
            self.stdout.write(f'  [dry] neg_kw: "{current or "(empty)"}" -> "{new_val}"')
            return
        product.ebay_negative_keywords = new_val
        product.save(update_fields=['ebay_negative_keywords'])
        self.stdout.write(f'  [ok] neg_kw: "{current or "(empty)"}" -> "{new_val}"')

    # -----------------------------------------------------------------------
    # Fixes
    # -----------------------------------------------------------------------

    def _fix_1_scarab_occult(self, dry):
        """Fix 1: Thousand Sons Scarab Occult Terminators -- eBay URL + neg_kw (43-36)."""
        self.stdout.write('\nFix 1: Thousand Sons Scarab Occult Terminators -- eBay URL + neg_kw')
        p = self._get_product('43-36')
        if p is None:
            return
        self._set_url(p, 'eBay', 'https://www.ebay.com/itm/356204431370', dry)
        # 4x: blocks partial-squad listings selling 4 models out of the standard
        # 5-man sealed kit (sellers advertising "4x Scarab Occult Terminators").
        self._add_neg_kw(p, '4x', dry)

    def _fix_2_red_harvest_noop(self):
        """Fix 2: Warcry: Red Harvest -- product not in DB, nothing to do."""
        self.stdout.write('\nFix 2: Warcry: Red Harvest')
        self.stdout.write(
            self.style.WARNING(
                '  [notice] "Warcry: Red Harvest" is not present in the database '
                '(was never seeded or has already been removed).  No action taken.'
            )
        )

    def _fix_3_angron_gw_price(self, dry):
        """Fix 3: World Eaters Angron -- GW retail price + msrp $145 -> $175 (43-04)."""
        self.stdout.write('\nFix 3: World Eaters Angron -- GW price + msrp update')
        p = self._get_product('43-04')
        if p is None:
            return
        # GW raised the retail price after initial release.
        # _set_price updates both CurrentPrice.price and product.msrp for GW rows.
        self._set_price(p, 'Games Workshop', '175.00', dry)

    def _fix_4_berzerkers(self, dry):
        """Fix 4: World Eaters Berzerkers -- eBay URL + neg_kw (43-60)."""
        self.stdout.write('\nFix 4: World Eaters Berzerkers -- eBay URL + neg_kw')
        p = self._get_product('43-60')
        if p is None:
            return
        self._set_url(p, 'eBay', 'https://www.ebay.com/itm/397740814391', dry)
        # kharn: blocks "Kharn the Betrayer" special-character listings and
        # "Berzerkers with Kharn" bundle listings that share enough Berzerker
        # keywords to pass match threshold but are a different product.
        self._add_neg_kw(p, 'kharn', dry)
