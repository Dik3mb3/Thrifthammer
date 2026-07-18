"""
Management command: apply_batch_fixes_mar2026af

Thirty-first wave of March 2026 batch corrections for ThriftHammer.

Changes covered:
  Fix 1  -- General sweep: for every active product whose Product.gw_url
             points to warhammer.com (i.e. a genuine GW product page, not a
             brand site repurposing this field for its own "View" button --
             see Marvel Crisis Protocol, Star Wars: Legion, BattleTech,
             Trench Crusade, Malifaux), ensure the Games Workshop
             CurrentPrice row is healthy:
               price         = product.msrp  (GW sells at full retail)
               url           = product.gw_url
               in_stock      = True
               not_available = False

             A row is considered broken if any of the following are true:
               - not_available = True
               - price is None
               - url is blank / missing

             Products with no MSRP are skipped — we cannot invent a price.
             Products already healthy are left untouched.

             This covers wave AE's 13 SKUs (safety net in case msrp was None
             on production at wave AE run-time) plus any additional products
             such as 70-12 Spearhead: Daughters of Khaine.

             2026-07-17: scoped the candidate query to gw_url containing
             "warhammer.com" (was: any non-empty gw_url). This command runs
             on every deploy via the Procfile, and without the domain check
             it was resurrecting a bogus "Games Workshop" CurrentPrice row
             -- priced at product.msrp, linked to the brand site's own URL
             -- for every product in the non-GW categories listed above,
             every single deploy.
"""

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Product, Retailer


class Command(BaseCommand):
    """Apply wave-AF March 2026 batch corrections to products."""

    help = 'Apply wave-AF March 2026 batch corrections.'

    def handle(self, *args, **options):
        """Apply all fixes."""
        self.stdout.write('\napply_batch_fixes_mar2026af')
        self.stdout.write('=' * 50)
        self._fix_1_sweep_gw_prices()
        self.stdout.write(self.style.SUCCESS('\nAll wave-AF fixes applied successfully.'))

    # -------------------------------------------------------------------------
    # Individual fixes
    # -------------------------------------------------------------------------

    def _fix_1_sweep_gw_prices(self):
        """
        Sweep all active products with gw_url set. For any whose GW
        CurrentPrice row is missing or broken, restore it to a healthy state.
        """
        try:
            gw_retailer = Retailer.objects.get(slug='games-workshop')
        except Retailer.DoesNotExist:
            self.stdout.write(self.style.ERROR('  Fix 1: games-workshop retailer not found — aborting'))
            return

        candidates = (
            Product.objects
            .filter(is_active=True, gw_url__icontains='warhammer.com')
            .order_by('name')
        )
        self.stdout.write(f'  Fix 1: scanning {candidates.count()} products with a warhammer.com gw_url...')

        updated = 0
        already_ok = 0
        skipped_no_msrp = 0

        for product in candidates:
            if not product.msrp:
                skipped_no_msrp += 1
                self.stdout.write(self.style.WARNING(
                    f'  Fix 1: {product.gw_sku} [{product.name[:40]}] -- no MSRP, skipped'
                ))
                continue

            target_price = product.msrp
            target_url = product.gw_url

            cp, created = CurrentPrice.objects.get_or_create(
                product=product,
                retailer=gw_retailer,
                defaults={
                    'price': target_price,
                    'url': target_url,
                    'in_stock': True,
                    'not_available': False,
                },
            )

            if created:
                self.stdout.write(self.style.SUCCESS(
                    f'  Fix 1: {product.gw_sku} [{product.name[:40]}]'
                    f' -- CREATED price=${target_price}'
                ))
                updated += 1
                continue

            # Check if existing row needs repair.
            is_broken = cp.not_available or cp.price is None or not cp.url
            if not is_broken:
                already_ok += 1
                continue

            changed_fields = []
            if cp.price != target_price:
                cp.price = target_price
                changed_fields.append('price')
            if cp.url != target_url and target_url:
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
                    f'  Fix 1: {product.gw_sku} [{product.name[:40]}]'
                    f' -- FIXED {changed_fields} price=${target_price}'
                ))
                updated += 1
            else:
                already_ok += 1

        self.stdout.write(
            f'  Fix 1 summary: {updated} fixed/created, {already_ok} already healthy,'
            f' {skipped_no_msrp} skipped (no MSRP).'
        )
