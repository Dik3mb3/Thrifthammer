"""
Batch fix may2026a

Fix broken Amazon URL for Blades of Khorne Bloodletters (97-08).
The old ASIN B0DHXCGWN7 returns a 404; replace with the correct listing.

Safe to re-run (idempotent).
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from prices.models import CurrentPrice
from products.models import Product, Retailer

_SKU = '97-08'
_NEW_URL = (
    'https://www.amazon.com/Warhammer-Daemons-Chaos-Khorne-Bloodletters/dp/B076F9VWXX/'
    'ref=sr_1_1?crid=3TZY4PZOUVBE3&dib=eyJ2IjoiMSJ9.FEi69s2jROlFANV2lQeApFwcAEkGnny'
    'UMGUh-KvAPetUajz6_g1N30pppFLkKiIumtwm9rMEbZpb43yoOeKfnIl18PxVYoZGH43bplFky6Fi8'
    '7Xk4qSDHzz3Rrn44YJKjocYk3TGW4GIb-w6KPCHpGH1xmcWLW2WPBZZQoUckDC8FK0q8y9UN28Rivh'
    '-PGLgTKjofYmpvjSo2VTQ4dJG6TThOu82sQJd1f-S0wKZPWrtp0EcMEGovgKDyDXA_qRMg_m0zlc2a'
    '-rdE2NaMjd_VKGe9QOaQWNzBLEToNV74EU.f5itZrUrjDOg_wGC4oFtx_k1raiJeYwWWdZ4gjcbsa0'
    '&dib_tag=se&keywords=Blades+of+Khorne+Bloodletters&qid=1777641970'
    '&sprefix=blades+of+khorne+bloodletters%2Caps%2C249&sr=8-1'
)


class Command(BaseCommand):
    """Replace broken Amazon URL for Bloodletters (97-08) with the correct listing."""

    help = 'Fix broken Amazon URL for Blades of Khorne Bloodletters (97-08).'

    def handle(self, *args, **options):
        """Update the Amazon CurrentPrice URL for Bloodletters."""
        with transaction.atomic():
            try:
                product = Product.objects.get(gw_sku=_SKU)
            except Product.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'Product {_SKU} not found — skipping.'))
                return

            try:
                amazon = Retailer.objects.get(name='Amazon')
            except Retailer.DoesNotExist:
                self.stdout.write(self.style.ERROR('Amazon retailer not found — skipping.'))
                return

            row = CurrentPrice.objects.filter(product=product, retailer=amazon).first()
            if not row:
                self.stdout.write(self.style.ERROR(
                    f'No Amazon price row for {product.name!r} — skipping.'
                ))
                return

            if row.url == _NEW_URL:
                self.stdout.write(f'  already correct: {product.name!r} — skipping.')
                return

            row.url = _NEW_URL
            row.not_available = False
            row.save(update_fields=['url', 'not_available'])
            self.stdout.write(self.style.SUCCESS(
                f'  UPDATED: {product.name!r} Amazon URL → B076F9VWXX'
            ))

        self.stdout.write(self.style.SUCCESS('may2026a complete.'))
