from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Product, Retailer


class Command(BaseCommand):
    help = 'Jun 2026o: eBay keyword fixes, KT-104 deletion, AL-018 Amazon URL correction'

    def handle(self, *args, **options):
        # ── eBay negative keyword updates ─────────────────────────────────────
        # Complete replacement strings — includes all prior keywords plus new additions.
        neg_fixes = [
            # CM-012 Tech-thralls Covenant: current='Imperialis' (jun2026n); add '10'
            ('CM-012', 'Imperialis 10'),
            # KT-032 Blades of Khaine: current='' (no prior fixes); add 'x5 5x'
            ('KT-032', 'x5 5x'),
            # KT-029 Canoptek Circle: current='' (no prior fixes); add 'Geomancer model'
            ('KT-029', 'Geomancer model'),
            # NM-056: current='x1' (jun2026g); add '1x'
            ('NM-056', 'x1 1x'),
            # NM-063: current='x1' (jun2026g); add '1x'
            ('NM-063', 'x1 1x'),
        ]
        for sku, value in neg_fixes:
            updated = Product.objects.filter(gw_sku=sku).update(ebay_negative_keywords=value)
            self.stdout.write(f'{sku} ebay_negative_keywords=[{value}] rows={updated}')

        # ── Delete KT-104 (Kill Team: Chaos Legionaries) ─────────────────────
        deleted, _ = Product.objects.filter(gw_sku='KT-104').delete()
        self.stdout.write(f'KT-104 deleted rows={deleted}')

        # ── AL-018 Amazon URL correction ──────────────────────────────────────
        # Cataphractii Terminators with Combi-bolters and Power Fists
        # Previous ASIN was wrong; correct ASIN: B0GJV364PB
        try:
            amazon = Retailer.objects.get(slug='amazon')
            updated = CurrentPrice.objects.filter(
                product__gw_sku='AL-018',
                retailer=amazon,
            ).update(
                url='https://www.amazon.com/dp/B0GJV364PB?tag=thrifthammer7-20',
                manual_url_override=True,
            )
            self.stdout.write(f'AL-018 Amazon url=B0GJV364PB manual_url_override=True rows={updated}')
        except Retailer.DoesNotExist:
            self.stdout.write('Amazon retailer not found — skipping AL-018')

        self.stdout.write(self.style.SUCCESS('apply_batch_fixes_jun2026o done'))
