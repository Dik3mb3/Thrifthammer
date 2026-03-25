"""
Management command: apply_batch_fixes_mar2026ag

Thirty-second wave of March 2026 batch corrections for ThriftHammer.

Changes covered:
  Fix 1  -- Force-set GW CurrentPrice rows for 14 SKUs whose msrp field is
             None on production (causing waves AE and AF to skip them).
             MSRP values sourced directly from populate_products.py.
             Sets price, url (from product.gw_url), in_stock=True,
             not_available=False independently per product so one failure
             cannot block the others.
"""

import decimal

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Product, Retailer

# MSRP values sourced from populate_products.py for products whose
# product.msrp is None on production.
_GW_MSRPS = {
    '59-20': decimal.Decimal('35.00'),   # Adeptus Mechanicus Electropriests
    '44-09': decimal.Decimal('47.50'),   # Dark Angels Ravenwing Command Squad
    '43-56': decimal.Decimal('42.50'),   # Death Guard Deathshroud Bodyguard
    '51-42': decimal.Decimal('40.00'),   # Genestealer Cults Broodcoven
    'HA-021': decimal.Decimal('75.00'),  # Horus Heresy Leviathan Dreadnought
    '54-21': decimal.Decimal('118.00'),  # Imperial Knight Dominus
    'NM-010': decimal.Decimal('45.00'),  # Necromunda Escher Gang
    'NM-011': decimal.Decimal('45.00'),  # Necromunda Goliath Gang
    'NM-012': decimal.Decimal('45.00'),  # Necromunda Van Saar Gang
    '48-61': decimal.Decimal('27.50'),   # Space Marine Primaris Lieutenant
    '48-29': decimal.Decimal('30.00'),   # Space Marine Scouts
    '70-12': decimal.Decimal('87.50'),   # Spearhead: Daughters of Khaine
    '96-12': decimal.Decimal('42.50'),   # Stormcast Eternals Knight-Judicator
    '56-14': decimal.Decimal('35.00'),   # T'au Stealth Battlesuits
}


class Command(BaseCommand):
    """Apply wave-AG March 2026 batch corrections to products."""

    help = 'Apply wave-AG March 2026 batch corrections.'

    def handle(self, *args, **options):
        """Apply all fixes."""
        self.stdout.write('\napply_batch_fixes_mar2026ag')
        self.stdout.write('=' * 50)
        self._fix_1_force_gw_price_rows()
        self.stdout.write(self.style.SUCCESS('\nAll wave-AG fixes applied successfully.'))

    def _fix_1_force_gw_price_rows(self):
        """
        Force GW CurrentPrice to price=MSRP, url=gw_url, in_stock=True,
        not_available=False for each of the 14 SKUs.  Each product is saved
        independently — no shared transaction — so one failure cannot roll back
        the others.
        """
        try:
            gw_retailer = Retailer.objects.get(slug='games-workshop')
        except Retailer.DoesNotExist:
            self.stdout.write(self.style.ERROR('  Fix 1: games-workshop retailer not found'))
            return

        updated = 0
        already_ok = 0
        not_found = 0

        for gw_sku, msrp in _GW_MSRPS.items():
            try:
                product = Product.objects.get(gw_sku=gw_sku)
            except Product.DoesNotExist:
                self.stdout.write(self.style.WARNING(f'  Fix 1: {gw_sku} -- NOT FOUND'))
                not_found += 1
                continue

            target_url = product.gw_url  # set by wave AB Fix 15

            cp, created = CurrentPrice.objects.get_or_create(
                product=product,
                retailer=gw_retailer,
                defaults={
                    'price': msrp,
                    'url': target_url,
                    'in_stock': True,
                    'not_available': False,
                },
            )

            if created:
                self.stdout.write(self.style.SUCCESS(
                    f'  Fix 1: {gw_sku} [{product.name[:40]}]'
                    f' -- CREATED price=${msrp} url={target_url[:60]}'
                ))
                updated += 1
                continue

            changed_fields = []
            if cp.price != msrp:
                cp.price = msrp
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
                    f'  Fix 1: {gw_sku} [{product.name[:40]}]'
                    f' -- FIXED {changed_fields} price=${msrp}'
                ))
                updated += 1
            else:
                self.stdout.write(
                    f'  Fix 1: {gw_sku} [{product.name[:40]}] -- already correct'
                )
                already_ok += 1

        self.stdout.write(
            f'  Fix 1 summary: {updated} fixed/created, {already_ok} already correct,'
            f' {not_found} not found.'
        )
