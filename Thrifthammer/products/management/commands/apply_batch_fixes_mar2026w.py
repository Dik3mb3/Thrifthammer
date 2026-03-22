"""
Management command: apply_batch_fixes_mar2026w

Twenty-second wave of March 2026 batch corrections for ThriftHammer.
Run after apply_batch_fixes_mar2026v.

Changes covered:
  Fix 1  -- Ork Flash Gitz (50-20):
             - Append neg_kw "elektro rokker" to existing neg_kw.
               "Ork Elektro Rokker Wargame Exclusive" is a GW wargame-
               exclusive limited release that shares Flash Gitz keywords
               but is a completely different non-retail product.
               Also covered globally by the new 'exclusive' entry added
               to _BITS_KEYWORDS in ebay_api_client.py (this wave).

  Fix 2  -- Legiones Astartes Predator (HA-012):
             - neg_kw "imperialis" (new, SKU-specific)
               eBay returns "Predator Squadron Legiones Astartes Imperialis
               Sealed" — a Legiones Imperialis (6mm-scale) product that shares
               the "Legiones Astartes Predator" keyword combination but is a
               completely different game system and scale.

  Fix 3  -- Daughters of Khaine Witch Aelves (85-06):
             - Set Amazon URL to the correct ASIN B07B27617B.
               The URL was blank; the correct listing was confirmed by user.

  Fix 4  -- Ork Deff Dread (50-16):
             - Blank Amazon URL (ASIN B003B1V9D2 was wrong — maps to
               "Games Workshop Death Zkatola - Orks", a completely different
               product). Marking not_available until correct ASIN is found.
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from prices.models import CurrentPrice
from products.models import Product, Retailer


class Command(BaseCommand):
    """Apply wave-W March 2026 batch corrections to products and prices."""

    help = 'Apply wave-W March 2026 batch corrections.'

    def handle(self, *args, **options):
        """Apply all fixes atomically."""
        self.stdout.write('\napply_batch_fixes_mar2026w')
        self.stdout.write('=' * 50)

        with transaction.atomic():
            self._fix_1_flash_gitz_neg_kw()
            self._fix_2_la_predator_neg_kw()
            self._fix_3_witch_aelves_amazon()
            self._fix_4_deff_dread_amazon()

        self.stdout.write(self.style.SUCCESS('\nAll wave-W fixes applied successfully.'))

    # -------------------------------------------------------------------------
    # Individual fixes
    # -------------------------------------------------------------------------

    def _fix_1_flash_gitz_neg_kw(self):
        """Append 'elektro rokker' to Ork Flash Gitz neg_kw (50-20)."""
        try:
            p = Product.objects.get(gw_sku='50-20')
        except Product.DoesNotExist:
            self.stdout.write(self.style.WARNING('  Fix 1: 50-20 not found — skipped'))
            return

        existing = p.ebay_negative_keywords or ''
        new_kw = 'meganobz mek nookah elektro rokker'
        if 'elektro' in existing and 'rokker' in existing:
            self.stdout.write(f'  Fix 1: 50-20 neg_kw already has elektro/rokker — skipped')
            return

        p.ebay_negative_keywords = new_kw
        p.save()
        self.stdout.write(self.style.SUCCESS(
            f'  Fix 1: 50-20 neg_kw → "{new_kw}"'
        ))

    def _fix_2_la_predator_neg_kw(self):
        """Set Legiones Astartes Predator neg_kw to 'imperialis' (HA-012)."""
        try:
            p = Product.objects.get(gw_sku='HA-012')
        except Product.DoesNotExist:
            self.stdout.write(self.style.WARNING('  Fix 2: HA-012 not found — skipped'))
            return

        new_kw = 'imperialis'
        if 'imperialis' in (p.ebay_negative_keywords or ''):
            self.stdout.write(f'  Fix 2: HA-012 neg_kw already has imperialis — skipped')
            return

        p.ebay_negative_keywords = new_kw
        p.save()
        self.stdout.write(self.style.SUCCESS(
            f'  Fix 2: HA-012 neg_kw → "{new_kw}"'
        ))

    def _fix_3_witch_aelves_amazon(self):
        """Set Daughters of Khaine Witch Aelves Amazon URL (85-06)."""
        try:
            p = Product.objects.get(gw_sku='85-06')
            amazon = Retailer.objects.get(slug='amazon')
        except (Product.DoesNotExist, Retailer.DoesNotExist) as exc:
            self.stdout.write(self.style.WARNING(f'  Fix 3: {exc} — skipped'))
            return

        correct_url = 'https://www.amazon.com/Games-Workshop-Daughters-Khaine-Warhammer/dp/B07B27617B'
        cp, _ = CurrentPrice.objects.get_or_create(product=p, retailer=amazon)

        if cp.url == correct_url:
            self.stdout.write(f'  Fix 3: 85-06 Amazon URL already correct — skipped')
            return

        cp.url = correct_url
        cp.not_available = False
        cp.save()
        self.stdout.write(self.style.SUCCESS(
            f'  Fix 3: 85-06 Witch Aelves Amazon URL set to {correct_url}'
        ))

    def _fix_4_deff_dread_amazon(self):
        """Blank Ork Deff Dread Amazon URL — ASIN B003B1V9D2 maps to wrong product (50-16)."""
        try:
            p = Product.objects.get(gw_sku='50-16')
            amazon = Retailer.objects.get(slug='amazon')
        except (Product.DoesNotExist, Retailer.DoesNotExist) as exc:
            self.stdout.write(self.style.WARNING(f'  Fix 4: {exc} — skipped'))
            return

        wrong_asin = 'B003B1V9D2'
        try:
            cp = CurrentPrice.objects.get(product=p, retailer=amazon)
        except CurrentPrice.DoesNotExist:
            self.stdout.write(f'  Fix 4: 50-16 no Amazon record — skipped')
            return

        if wrong_asin not in (cp.url or ''):
            self.stdout.write(f'  Fix 4: 50-16 Amazon URL is not the wrong ASIN — skipped')
            return

        cp.url = ''
        cp.price = None
        cp.in_stock = False
        cp.not_available = True
        cp.save()
        self.stdout.write(self.style.SUCCESS(
            f'  Fix 4: 50-16 Deff Dread Amazon URL blanked (was wrong ASIN {wrong_asin})'
        ))
