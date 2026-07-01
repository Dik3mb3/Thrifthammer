from django.core.management.base import BaseCommand
from products.models import Product
from prices.models import CurrentPrice, Retailer


class Command(BaseCommand):
    help = 'Jun 2026g: eBay negative keyword fixes + NM-051 Amazon no-listing'

    def handle(self, *args, **options):
        fixes = [
            # NM-067: exclude watchtower terrain listings
            ('NM-067', 'ebay_negative_keywords', 'Watch Tower'),
            # NM-056: exclude single-model listings
            ('NM-056', 'ebay_negative_keywords', 'x1'),
            # NM-063: exclude single-model listings
            ('NM-063', 'ebay_negative_keywords', 'x1'),
            # NM-040: exclude Sanctioner listings
            ('NM-040', 'ebay_negative_keywords', 'Sanctioner'),
            # NM-041: exclude Bot listings
            ('NM-041', 'ebay_negative_keywords', 'Bot'),
            # KT-100: exclude rulebook, token, and game board listings
            ('KT-100', 'ebay_negative_keywords', 'Rules Book Tokens Game Board'),
        ]

        for sku, field, value in fixes:
            updated = Product.objects.filter(gw_sku=sku).update(**{field: value})
            self.stdout.write(f'{sku} {field}=[{value}] rows={updated}')

        # NM-051: no valid Amazon listing — lock record to prevent future overwrites
        try:
            amazon = Retailer.objects.get(name='Amazon')
            updated = CurrentPrice.objects.filter(
                product__gw_sku='NM-051',
                retailer=amazon,
            ).update(url='', price=None, manual_url_override=True)
            self.stdout.write(f'NM-051 Amazon CurrentPrice cleared rows={updated}')
        except Retailer.DoesNotExist:
            self.stdout.write('Amazon retailer not found — skipping NM-051')

        self.stdout.write(self.style.SUCCESS('apply_batch_fixes_jun2026g done'))
