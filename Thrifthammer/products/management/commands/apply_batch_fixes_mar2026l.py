"""
Management command: apply_batch_fixes_mar2026l

Twelfth wave of March 2026 batch corrections for ThriftHammer.
Run after apply_batch_fixes_mar2026k.

Changes covered:
  Section 1  - Blood Angels MM URL correction (long-form slug fix)
               The DB held short-form URLs (e.g. gw-41-38.html) for four
               Blood Angels products.  Miniature Market redirects short-form
               product URLs to long-form slugs, but the short forms currently
               return 404.  The correct long-form URLs were confirmed via
               same-origin browser fetch on 2026-03-17.

               All four products are Out of Stock at MM; in_stock is set to
               False for each.  Prices are updated to match MM's current
               listed price.

               Products fixed:
                 41-03  Blood Angels Astorath the Grim        → $38.99 OOS
                 41-04  Blood Angels Commander Dante          → $38.99 OOS
                 41-05  Blood Angels Lemartes                 → $38.99 OOS
                 41-06  Blood Angels Sanguinary Guard         → $51.00 OOS

               Root cause: Wave K excluded these four SKUs from the mass
               OOS correction because the JS fetch check reported them as
               "in stock" (404 pages don't contain the schema.org/OutOfStock
               marker, so the detector treated them as valid/in-stock pages).
               A parallel WebFetch agent identified them as 404s, but its
               results arrived after Wave K was already deployed.

Usage:
    python manage.py apply_batch_fixes_mar2026l
    python manage.py apply_batch_fixes_mar2026l --dry-run
"""

import decimal

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Product, Retailer


# ===========================================================================
# Blood Angels MM corrections — correct long-form slug URLs (verified OOS)
# ===========================================================================
BLOOD_ANGELS_MM_FIXES = {
    # gw_sku: (new_url, new_price)
    '41-03': (
        'https://www.miniaturemarket.com/warhammer-40k-blood-angels-astorath-grim-gw-41-38.html',
        decimal.Decimal('38.99'),
    ),
    '41-04': (
        'https://www.miniaturemarket.com/warhammer-40k-blood-angels-commander-dante-gw-41-40.html',
        decimal.Decimal('38.99'),
    ),
    '41-05': (
        'https://www.miniaturemarket.com/warhammer-40k-blood-angels-lemartes-gw-41-36.html',
        decimal.Decimal('38.99'),
    ),
    '41-06': (
        'https://www.miniaturemarket.com/warhammer-40k-blood-angels-sanguinary-guard-gw-41-31.html',
        decimal.Decimal('51.00'),
    ),
}


class Command(BaseCommand):
    """Twelfth wave of March 2026 ThriftHammer DB corrections."""

    help = 'Apply Wave L batch corrections (March 2026) — Blood Angels MM URL + OOS fix.'

    def add_arguments(self, parser):
        """Add --dry-run flag to preview changes without saving."""
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Print planned changes without writing to the database.',
        )

    def handle(self, *args, **options):
        """Execute all Wave L corrections in order."""
        dry = options['dry_run']
        if dry:
            self.stdout.write(self.style.WARNING('DRY RUN — no changes will be saved.\n'))

        self._section_1_blood_angels_mm_url_fix(dry)

        if dry:
            self.stdout.write(self.style.WARNING('\nDRY RUN complete — nothing was saved.'))
        else:
            self.stdout.write(self.style.SUCCESS('\nWave L complete.'))

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

    # -----------------------------------------------------------------------
    # Sections
    # -----------------------------------------------------------------------

    def _section_1_blood_angels_mm_url_fix(self, dry):
        """
        Section 1: Fix Blood Angels MM URLs and mark as OOS.

        The DB stored short-form URLs (gw-41-XX.html) that now return 404.
        MM's canonical product URLs use long-form slugs.  This section
        updates the URL, corrects the price, and sets in_stock=False for
        all four affected Blood Angels products.
        """
        self.stdout.write('\n── Section 1: Blood Angels MM URL + OOS correction ──')
        mm = Retailer.objects.get(name='Miniature Market')

        updated = 0
        skipped = 0

        for sku, (new_url, new_price) in BLOOD_ANGELS_MM_FIXES.items():
            p = self._get_product(sku)
            if p is None:
                skipped += 1
                continue

            try:
                cp = CurrentPrice.objects.get(product=p, retailer=mm)
            except CurrentPrice.DoesNotExist:
                self.stdout.write(f'  [skip] {sku} — no MM row found')
                skipped += 1
                continue

            old_url = cp.url
            old_price = cp.price
            old_in_stock = cp.in_stock

            already_correct = (
                cp.url == new_url
                and cp.price == new_price
                and not cp.in_stock
            )
            if already_correct:
                if dry:
                    self.stdout.write(f'  [dry-skip] {sku} already correct')
                skipped += 1
                continue

            if dry:
                self.stdout.write(
                    f'  [dry] {sku} "{p.name[:40]}"\n'
                    f'         url:      {old_url}\n'
                    f'                → {new_url}\n'
                    f'         price:    {old_price} → {new_price}\n'
                    f'         in_stock: {old_in_stock} → False'
                )
                continue

            cp.url = new_url
            cp.price = new_price
            cp.in_stock = False
            cp.save(update_fields=['url', 'price', 'in_stock'])
            self.stdout.write(
                f'  [ok] {sku} "{p.name[:40]}" → URL updated, price={new_price}, in_stock=False'
            )
            updated += 1

        if not dry:
            self.stdout.write(
                self.style.SUCCESS(
                    f'  Section 1 done: {updated} updated, {skipped} skipped.'
                )
            )
