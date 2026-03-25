"""
Management command: apply_batch_fixes_mar2026ah

Thirty-third wave of March 2026 batch corrections for ThriftHammer.

Changes covered:
  Fix 1  -- Correct GW prices for 14 SKUs using live prices scraped from
             warhammer.com on 25 Mar 2026.  Wave AG set these rows using
             the stale populate_products.py MSRP values which were outdated.
             Also corrects Product.msrp to match the live GW price so future
             discount calculations are accurate.

             Prices verified from warhammer.com/en-US on 2026-03-25:
               59-20  Adeptus Mechanicus Electropriests       $60.00
               44-09  Dark Angels Ravenwing Command Squad     $65.00
               43-56  Death Guard Deathshroud Bodyguard       $65.00
               51-42  Genestealer Cults Broodcoven            $73.50
               HA-021 Horus Heresy Leviathan Dreadnought     $101.00
               54-21  Imperial Knight Dominus                 $195.00
               NM-010 Necromunda Escher Gang                  $53.00
               NM-011 Necromunda Goliath Gang                 $53.00
               NM-012 Necromunda Van Saar Gang                $53.00
               48-61  Space Marine Primaris Lieutenant         $39.00
               48-29  Kill Team Scout Squad                    $82.00
               70-12  Spearhead: Seraphon                    $150.00
               96-12  Stormcast Knight-Judicator               $39.00
               56-14  T'au XV26 Stealth Battlesuits            $69.00
"""

import decimal

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Product, Retailer

# Live prices from warhammer.com/en-US scraped 2026-03-25.
_CORRECT_PRICES = {
    '59-20':  decimal.Decimal('60.00'),
    '44-09':  decimal.Decimal('65.00'),
    '43-56':  decimal.Decimal('65.00'),
    '51-42':  decimal.Decimal('73.50'),
    'HA-021': decimal.Decimal('101.00'),
    '54-21':  decimal.Decimal('195.00'),
    'NM-010': decimal.Decimal('53.00'),
    'NM-011': decimal.Decimal('53.00'),
    'NM-012': decimal.Decimal('53.00'),
    '48-61':  decimal.Decimal('39.00'),
    '48-29':  decimal.Decimal('82.00'),
    '70-12':  decimal.Decimal('150.00'),
    '96-12':  decimal.Decimal('39.00'),
    '56-14':  decimal.Decimal('69.00'),
}


class Command(BaseCommand):
    """Apply wave-AH March 2026 batch corrections to products."""

    help = 'Apply wave-AH March 2026 batch corrections.'

    def handle(self, *args, **options):
        """Apply all fixes."""
        self.stdout.write('\napply_batch_fixes_mar2026ah')
        self.stdout.write('=' * 50)
        self._fix_1_correct_gw_prices()
        self.stdout.write(self.style.SUCCESS('\nAll wave-AH fixes applied successfully.'))

    def _fix_1_correct_gw_prices(self):
        """Update GW CurrentPrice and Product.msrp to live warhammer.com prices."""
        try:
            gw_retailer = Retailer.objects.get(slug='games-workshop')
        except Retailer.DoesNotExist:
            self.stdout.write(self.style.ERROR('  Fix 1: games-workshop retailer not found'))
            return

        updated = 0
        already_ok = 0
        not_found = 0

        for gw_sku, correct_price in _CORRECT_PRICES.items():
            try:
                product = Product.objects.get(gw_sku=gw_sku)
            except Product.DoesNotExist:
                self.stdout.write(self.style.WARNING(f'  Fix 1: {gw_sku} -- product NOT FOUND'))
                not_found += 1
                continue

            # Correct Product.msrp if it's wrong or None.
            msrp_changed = False
            if product.msrp != correct_price:
                product.msrp = correct_price
                product.save(update_fields=['msrp'])
                msrp_changed = True

            # Correct the GW CurrentPrice row.
            target_url = product.gw_url
            cp, created = CurrentPrice.objects.get_or_create(
                product=product,
                retailer=gw_retailer,
                defaults={
                    'price': correct_price,
                    'url': target_url,
                    'in_stock': True,
                    'not_available': False,
                },
            )

            if created:
                self.stdout.write(self.style.SUCCESS(
                    f'  Fix 1: {gw_sku} [{product.name[:38]}]'
                    f' -- CREATED ${correct_price}'
                ))
                updated += 1
                continue

            changed_fields = []
            if cp.price != correct_price:
                cp.price = correct_price
                changed_fields.append('price')
            if target_url and cp.url != target_url:
                cp.url = target_url
                changed_fields.append('url')
            if not cp.in_stock:
                cp.in_stock = True
                changed_fields.append('in_stock')
            if cp.not_available:
                cp.not_available = False
                changed_fields.append('not_available')

            if changed_fields:
                cp.save(update_fields=changed_fields)
                self.stdout.write(self.style.SUCCESS(
                    f'  Fix 1: {gw_sku} [{product.name[:38]}]'
                    f' -- FIXED {changed_fields} ${correct_price}'
                    + (' [msrp updated]' if msrp_changed else '')
                ))
                updated += 1
            elif msrp_changed:
                self.stdout.write(self.style.SUCCESS(
                    f'  Fix 1: {gw_sku} [{product.name[:38]}]'
                    f' -- price OK, msrp corrected to ${correct_price}'
                ))
                updated += 1
            else:
                self.stdout.write(
                    f'  Fix 1: {gw_sku} [{product.name[:38]}] -- already correct'
                )
                already_ok += 1

        self.stdout.write(
            f'  Fix 1 summary: {updated} updated, {already_ok} already correct,'
            f' {not_found} not found.'
        )
