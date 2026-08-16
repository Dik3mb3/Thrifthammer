from django.core.management.base import BaseCommand
from products.models import Product


class Command(BaseCommand):
    help = (
        'Aug 2026q: three eBay matching fixes for Warcry-tagged products, '
        'all verified via non-saving shadow tests before writing, per '
        'user-supplied listings 2026-08-09. '
        '(1) DOK-012 "Khainite Shadowstalkers": set ebay_allow_no_box=True '
        '-- the correct $59.50 listing says "NO BOX" in the title (loose/ '
        'unboxed sprues, not a red flag), which was blocked by default. '
        '(2) S2D-021 "Fomoroid Crusher": same fix, ebay_allow_no_box=True '
        '-- correct listing is $46.90, also titled "NO BOX". '
        '(3) COS-015 "Wildercorps Hunters": removed "x2" "2x" "3x" from '
        'ebay_negative_keywords -- the correct $60.00 listing\'s '
        'description lists "2x Citadel 40mm Round Bases, 3x Citadel 32mm '
        'Round Bases" (standard GW box-count boilerplate), which the '
        'negative keywords were incorrectly excluding as bulk-lot '
        'indicators. Kept x4/4x/x5/5x/x10/10x since this description '
        'does not contain those counts.'
    )

    def handle(self, *args, **options):
        updated = Product.objects.filter(gw_sku='DOK-012').update(ebay_allow_no_box=True)
        self.stdout.write(f'DOK-012 ebay_allow_no_box=True, rows={updated}')

        updated = Product.objects.filter(gw_sku='S2D-021').update(ebay_allow_no_box=True)
        self.stdout.write(f'S2D-021 ebay_allow_no_box=True, rows={updated}')

        updated = Product.objects.filter(gw_sku='COS-015').update(
            ebay_negative_keywords=(
                'legions imperialis Resin 04-113 Proxies Foil magazine '
                'issue x5 5x x10 10x x3 x4 4x'
            )
        )
        self.stdout.write(f'COS-015 ebay_negative_keywords updated, rows={updated}')

        self.stdout.write(self.style.SUCCESS('apply_batch_fixes_aug2026q done'))
