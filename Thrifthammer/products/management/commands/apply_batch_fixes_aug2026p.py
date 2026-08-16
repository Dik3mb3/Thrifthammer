from django.core.management.base import BaseCommand
from products.models import Product


class Command(BaseCommand):
    help = (
        'Aug 2026p: remaining eBay fixes for Bloodcrushers of Khorne per '
        'user request 2026-08-09, completing the aug2026o change. '
        'P-KHORNE-BLOODCRUSHERS: (1) removes the bare "3" from '
        'ebay_negative_keywords -- was excluding any listing containing '
        'a standalone "3" (e.g. "(3)" model-count in a title), including '
        'the target listing; kept "3x"/"x3" which correctly catch actual '
        'bulk-lot listings. (2) sets ebay_allow_no_box=True -- the '
        'target listing and at least one other real candidate are '
        'explicitly "NEW NO BOX" (loose/unboxed sprues, not used or '
        'incomplete). Verified via non-saving shadow test that this '
        'combination plus the already-applied allowed-title-word change '
        'resolves to the user-supplied listing (item 176527069824, '
        '$59.95).'
    )

    def handle(self, *args, **options):
        updated = Product.objects.filter(gw_sku='P-KHORNE-BLOODCRUSHERS').update(
            ebay_negative_keywords=(
                'Sealed legions imperialis Resin 04-113 D&D 5e 100th 1926 '
                'TShirt Plushie Plush Proxies Foil 164558591084 magazine '
                'issue x5 5x x10 10x x2 2x 3x x3 x4 4x'
            ),
            ebay_allow_no_box=True,
        )
        self.stdout.write(f'P-KHORNE-BLOODCRUSHERS updated, rows={updated}')

        self.stdout.write(self.style.SUCCESS('apply_batch_fixes_aug2026p done'))
