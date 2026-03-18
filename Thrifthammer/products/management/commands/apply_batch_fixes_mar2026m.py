"""
Management command: apply_batch_fixes_mar2026m

Thirteenth wave of March 2026 batch corrections for ThriftHammer.
Run after apply_batch_fixes_mar2026l.

Changes covered (all Noble Knight):
  Section 1 — OOS corrections (verified via live browser fetch 2026-03-17)
               NK shows no "Add to Cart" button for these products.
               Five SKUs confirmed out of stock at Noble Knight.
               Note: 43-09 also has a price discrepancy (DB $72.95 → live
               $69.95) so its price is corrected here as well.

                 01-11  Vertus Praetors          $56.95  → OOS
                 43-09  Chaos Predator            $72.95  → $69.95 OOS
                 48-23  Space Marine Predator     (price unchanged) → OOS
                 53-02  Ragnar Blackmane          $43.95  → OOS
                 59-10  Skitarii Rangers          $56.95  → OOS

  Section 2 — Price updates (14 SKUs verified via live browser fetch)
               These products are in stock at NK but their prices have changed.

                 43-03  Mortarion                $157.95 → $148.75
                 47-12  Sentinel                  $74.95 → $79.95
                 48-08  Vanguard Veterans         $53.95 → $54.95
                 48-15  Devastator Squad          $55.95 → $58.95
                 48-39  Eradicators               $53.95 → $54.95
                 48-76  Assault Intercessors      $57.95 → $58.95
                 50-14  Ork Lootas                $35.70 → $37.95
                 52-20  Battle Sisters Squad      $56.95 → $58.95
                 53-10  Thunderwolf Cavalry       $55.00 → $58.95
                 54-20  Knight Armigers           $85.95 → $85.00
                 56-15  Crisis Battlesuits        $75.95 → $76.95
                 59-25  Combat Patrol: AdMech    $274.95 → $279.95
                 73-10  Hearthkyn Warriors        $53.95 → $54.95
                 HA-041 Sicaran Battle Tank       $75.65 → $80.95

  Section 3 — Wrong URL → not_available (4 SKUs)
               These NK URLs link to completely different products, making
               price data meaningless.  Marked not_available until correct
               NK listings can be confirmed.

                 57-08  Grey Knights Terminators  (URL → Blightlord Terminators)
                 71-55  Stormcast Eternals Vanguard (URL → SM Vanguard Veteran Squad)
                 83-10  Chaos Warriors (12)       (URL → Datacards: Chaos Knights)
                 48-21  Space Marine Land Raider  (URL → Land Raider Crusader/Redeemer)

Usage:
    python manage.py apply_batch_fixes_mar2026m
    python manage.py apply_batch_fixes_mar2026m --dry-run
"""

import decimal

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Product, Retailer


# ===========================================================================
# Section 1 — Noble Knight OOS corrections
# gw_sku: (new_price_or_None_to_keep_existing,)
# A new_price of None means "keep whatever is in the DB; just mark OOS".
# ===========================================================================
NK_OOS_FIXES = {
    # gw_sku: new_price (None = keep existing)
    '01-11': None,                     # Vertus Praetors — price already correct
    '43-09': decimal.Decimal('69.95'), # Chaos Predator — price also changed
    '48-23': None,                     # Space Marine Predator — price unchanged
    '53-02': None,                     # Ragnar Blackmane — price already correct
    '59-10': None,                     # Skitarii Rangers — price already correct
}


# ===========================================================================
# Section 2 — Noble Knight price updates (all in stock)
# ===========================================================================
NK_PRICE_UPDATES = {
    '43-03':  decimal.Decimal('148.75'),   # Mortarion
    '47-12':  decimal.Decimal('79.95'),    # Sentinel
    '48-08':  decimal.Decimal('54.95'),    # Vanguard Veterans
    '48-15':  decimal.Decimal('58.95'),    # Devastator Squad
    '48-39':  decimal.Decimal('54.95'),    # Eradicators
    '48-76':  decimal.Decimal('58.95'),    # Assault Intercessors
    '50-14':  decimal.Decimal('37.95'),    # Ork Lootas
    '52-20':  decimal.Decimal('58.95'),    # Battle Sisters Squad
    '53-10':  decimal.Decimal('58.95'),    # Thunderwolf Cavalry
    '54-20':  decimal.Decimal('85.00'),    # Knight Armigers
    '56-15':  decimal.Decimal('76.95'),    # Crisis Battlesuits
    '59-25':  decimal.Decimal('279.95'),   # Combat Patrol: AdMech
    '73-10':  decimal.Decimal('54.95'),    # Hearthkyn Warriors
    'HA-041': decimal.Decimal('80.95'),    # Sicaran Battle Tank
}


# ===========================================================================
# Section 3 — Wrong URL → not_available
# These NK URLs link to the wrong product entirely.
# ===========================================================================
NK_WRONG_URL_SKUS = [
    '57-08',  # GK Terminators URL → Blightlord Terminators
    '71-55',  # Stormcast Vanguard URL → SM Vanguard Veteran Squad
    '83-10',  # Chaos Warriors (12) URL → Datacards: Chaos Knights
    '48-21',  # SM Land Raider URL → Land Raider Crusader/Redeemer
]


class Command(BaseCommand):
    """Thirteenth wave of March 2026 ThriftHammer DB corrections (Noble Knight)."""

    help = 'Apply Wave M batch corrections (March 2026) — Noble Knight OOS, prices, wrong URLs.'

    def add_arguments(self, parser):
        """Add --dry-run flag to preview changes without saving."""
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Print planned changes without writing to the database.',
        )

    def handle(self, *args, **options):
        """Execute all Wave M corrections in order."""
        dry = options['dry_run']
        if dry:
            self.stdout.write(self.style.WARNING('DRY RUN — no changes will be saved.\n'))

        nk = Retailer.objects.get(name__icontains='Noble Knight')

        self._section_1_nk_oos(dry, nk)
        self._section_2_nk_price_updates(dry, nk)
        self._section_3_nk_wrong_urls(dry, nk)

        if dry:
            self.stdout.write(self.style.WARNING('\nDRY RUN complete — nothing was saved.'))
        else:
            self.stdout.write(self.style.SUCCESS('\nWave M complete.'))

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

    def _get_current_price(self, product, retailer, gw_sku):
        """Fetch a CurrentPrice row, writing an error and returning None if missing."""
        try:
            return CurrentPrice.objects.get(product=product, retailer=retailer)
        except CurrentPrice.DoesNotExist:
            self.stderr.write(
                self.style.ERROR(f'  ERROR: No NK price row for {gw_sku} "{product.name[:40]}".')
            )
            return None

    # -----------------------------------------------------------------------
    # Sections
    # -----------------------------------------------------------------------

    def _section_1_nk_oos(self, dry, nk):
        """
        Section 1: Mark five NK products as out of stock.

        Verified 2026-03-17 via same-origin JS fetch on Noble Knight product pages.
        None of these pages contain an "Add to Cart" button; NK instead shows a
        "Notify Me" / "Pre-Order" CTA, which is their standard OOS state.

        43-09 (Chaos Predator) also has a price discrepancy (DB $72.95, live $69.95)
        so its price is corrected here alongside the stock change.
        """
        self.stdout.write('\n── Section 1: Noble Knight OOS corrections ──')
        updated = skipped = 0

        for sku, new_price in NK_OOS_FIXES.items():
            p = self._get_product(sku)
            if p is None:
                skipped += 1
                continue
            cp = self._get_current_price(p, nk, sku)
            if cp is None:
                skipped += 1
                continue

            already_oos = not cp.in_stock
            price_correct = (new_price is None) or (cp.price == new_price)
            if already_oos and price_correct:
                self.stdout.write(f'  [skip] {sku} already OOS and price correct')
                skipped += 1
                continue

            if dry:
                price_note = f', price: {cp.price} → {new_price}' if new_price else ''
                self.stdout.write(
                    f'  [dry] {sku} "{p.name[:40]}"'
                    f' — in_stock: {cp.in_stock} → False{price_note}'
                )
                continue

            fields = ['in_stock']
            cp.in_stock = False
            if new_price is not None:
                cp.price = new_price
                fields.append('price')
            cp.save(update_fields=fields)
            price_note = f', price={new_price}' if new_price else ''
            self.stdout.write(f'  [ok] {sku} "{p.name[:40]}" → in_stock=False{price_note}')
            updated += 1

        if not dry:
            self.stdout.write(
                self.style.SUCCESS(f'  Section 1 done: {updated} updated, {skipped} skipped.')
            )

    def _section_2_nk_price_updates(self, dry, nk):
        """
        Section 2: Update prices for 14 NK products that are in stock.

        All prices confirmed via same-origin JS fetch on Noble Knight product
        pages on 2026-03-17.  The regex 'Our Price.*?$(\\d+\\.?\\d*)' was used
        to extract current prices from the fetched HTML.
        """
        self.stdout.write('\n── Section 2: Noble Knight price updates ──')
        updated = skipped = 0

        for sku, new_price in NK_PRICE_UPDATES.items():
            p = self._get_product(sku)
            if p is None:
                skipped += 1
                continue
            cp = self._get_current_price(p, nk, sku)
            if cp is None:
                skipped += 1
                continue

            if cp.price == new_price:
                self.stdout.write(f'  [skip] {sku} price already {new_price}')
                skipped += 1
                continue

            if dry:
                self.stdout.write(
                    f'  [dry] {sku} "{p.name[:40]}" — price: {cp.price} → {new_price}'
                )
                continue

            old_price = cp.price
            cp.price = new_price
            cp.save(update_fields=['price'])
            self.stdout.write(
                f'  [ok] {sku} "{p.name[:40]}" — price: {old_price} → {new_price}'
            )
            updated += 1

        if not dry:
            self.stdout.write(
                self.style.SUCCESS(f'  Section 2 done: {updated} updated, {skipped} skipped.')
            )

    def _section_3_nk_wrong_urls(self, dry, nk):
        """
        Section 3: Mark four NK entries as not_available due to wrong URLs.

        Each of these NK URLs links to a completely different product than the
        one tracked in ThriftHammer.  The incorrect URLs were detected during
        the 2026-03-17 NK audit by comparing the product title returned by the
        fetched HTML against the expected product name.

        Setting not_available=True hides these rows from the price comparison
        table until correct NK listings can be identified.

        SKU details:
          57-08  Grey Knights Terminators → URL leads to Blightlord Terminators
          71-55  Stormcast Eternals Vanguard → URL leads to SM Vanguard Veteran Squad
          83-10  Chaos Warriors (12) → URL leads to Datacards: Chaos Knights ($7.95)
          48-21  Space Marine Land Raider → URL leads to Land Raider Crusader/Redeemer
        """
        self.stdout.write('\n── Section 3: Noble Knight wrong URL → not_available ──')
        updated = skipped = 0

        for sku in NK_WRONG_URL_SKUS:
            p = self._get_product(sku)
            if p is None:
                skipped += 1
                continue
            cp = self._get_current_price(p, nk, sku)
            if cp is None:
                skipped += 1
                continue

            if cp.not_available:
                self.stdout.write(f'  [skip] {sku} already not_available')
                skipped += 1
                continue

            if dry:
                self.stdout.write(
                    f'  [dry] {sku} "{p.name[:40]}" — not_available: False → True'
                    f'  (url: {cp.url[:70]})'
                )
                continue

            cp.not_available = True
            cp.in_stock = False
            cp.save(update_fields=['not_available', 'in_stock'])
            self.stdout.write(
                f'  [ok] {sku} "{p.name[:40]}" → not_available=True'
            )
            updated += 1

        if not dry:
            self.stdout.write(
                self.style.SUCCESS(f'  Section 3 done: {updated} updated, {skipped} skipped.')
            )
