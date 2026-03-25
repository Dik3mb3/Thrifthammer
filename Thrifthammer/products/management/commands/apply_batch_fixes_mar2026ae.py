"""
Management command: apply_batch_fixes_mar2026ae

Thirtieth wave of March 2026 batch corrections for ThriftHammer.

Changes covered:
  Fix 1  -- Restore Games Workshop price rows for 13 SKUs whose GW CurrentPrice
             record was marked not_available with no price.  For each SKU the
             GW row is restored to:
               price       = product.msrp  (GW always sells at full retail)
               url         = product.gw_url (the canonical GW product page URL
                             already set on the Product by wave AB Fix 15)
               in_stock    = True
               not_available = False
             SKUs: 54-21, HA-021, NM-010, NM-011, NM-012, 56-14, 48-29,
                   96-12, 48-61, 43-56, 51-42, 59-20, 44-09.
"""

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Product, Retailer

_TARGET_SKUS = [
    '54-21', 'HA-021', 'NM-010', 'NM-011', 'NM-012',
    '56-14', '48-29', '96-12', '48-61', '43-56',
    '51-42', '59-20', '44-09',
]


class Command(BaseCommand):
    """Apply wave-AE March 2026 batch corrections to products."""

    help = 'Apply wave-AE March 2026 batch corrections.'

    def handle(self, *args, **options):
        """Apply all fixes."""
        self.stdout.write('\napply_batch_fixes_mar2026ae')
        self.stdout.write('=' * 50)
        self._fix_1_restore_gw_prices()
        self.stdout.write(self.style.SUCCESS('\nAll wave-AE fixes applied successfully.'))

    # -------------------------------------------------------------------------
    # Individual fixes
    # -------------------------------------------------------------------------

    def _fix_1_restore_gw_prices(self):
        """
        Restore GW CurrentPrice rows for the 13 SKUs whose gw_url was set
        in wave AB.  All 13 had not_available=True / price=None and stale
        en-WW URLs.  Set price=msrp, url=product.gw_url, in_stock=True,
        not_available=False for each.
        """
        try:
            gw_retailer = Retailer.objects.get(slug='games-workshop')
        except Retailer.DoesNotExist:
            self.stdout.write(self.style.ERROR('  Fix 1: games-workshop retailer not found — aborting'))
            return

        updated = 0
        skipped = 0
        not_found = 0

        for gw_sku in _TARGET_SKUS:
            try:
                product = Product.objects.get(gw_sku=gw_sku)
            except Product.DoesNotExist:
                self.stdout.write(self.style.WARNING(f'  Fix 1: {gw_sku} -- product NOT FOUND'))
                not_found += 1
                continue

            if not product.msrp:
                self.stdout.write(self.style.WARNING(
                    f'  Fix 1: {gw_sku} [{product.name[:40]}] -- no MSRP, skipped'
                ))
                skipped += 1
                continue

            target_url = product.gw_url  # set by wave AB Fix 15
            target_price = product.msrp  # GW always sells at full retail

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
                    f'  Fix 1: {gw_sku} [{product.name[:40]}] -- created '
                    f'price=${target_price} url={target_url[:60]}'
                ))
                updated += 1
                continue

            # Update only if something needs changing.
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
                    f'  Fix 1: {gw_sku} [{product.name[:40]}] -- updated {changed_fields}'
                    f' price=${target_price}'
                ))
                updated += 1
            else:
                self.stdout.write(
                    f'  Fix 1: {gw_sku} [{product.name[:40]}] -- already correct'
                )
                skipped += 1

        self.stdout.write(
            f'  Fix 1 summary: {updated} updated/created, {skipped} already correct,'
            f' {not_found} not found.'
        )
