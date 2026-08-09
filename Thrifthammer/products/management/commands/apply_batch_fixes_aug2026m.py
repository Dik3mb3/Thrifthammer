from django.core.management.base import BaseCommand
from products.models import Product


class Command(BaseCommand):
    help = (
        'Aug 2026m: eBay search name / negative keyword fixes for T\'au '
        'Empire products, per user request 2026-08-09. All changes '
        'verified via non-saving shadow tests before writing. '
        '(1) TE-037 "Kroot Carnivores": ebay_search_name -> "Kroot '
        'Carnivores Warhammer 40K" (was blank, falling back to the full '
        'product name which collides with the whole Kroot-family lineup '
        'and buried the target listing past the top-10 search window). '
        'Also drops "10x" from negative keywords -- was a false-positive, '
        'rejecting the target listing\'s standard "10x Citadel Round '
        'Bases" box-count boilerplate as if it were a bulk-resale '
        'indicator. '
        '(2) KT-028 "Kill Team: Stealth Battlesuits" and 56-14 "T\'au '
        'Stealth Battlesuits" (same physical kit, cross-listed under two '
        'game lines): both ebay_search_name -> "Kill Team Stealth '
        'Battlesuits Warhammer" -- resolves both to the same UK listing '
        'they already independently matched to; US still finds nothing '
        'for either (pre-existing gap, not a regression). '
        '(3) TE-019 "Sun Shark Bomber" and TE-017 "Razorshark Strike '
        'Fighter" (dual-build kit pair sharing one physical box): both '
        'ebay_search_name -> "Sun Shark Bomber" (was "Tau Sun Shark '
        'Razorshark", which required both build names in the title and '
        'excluded listings using only one name, like the single-name '
        'listing this fixes). Both resolve to the same cheaper listing '
        '($80.10 vs the previous $89.00 match).'
    )

    def handle(self, *args, **options):
        updated = Product.objects.filter(gw_sku='TE-037').update(
            ebay_search_name='Kroot Carnivores Warhammer 40K',
            ebay_negative_keywords=(
                'legions imperialis Resin 04-113 100th 1926 TShirt '
                'Plushie Plush Proxies Foil magazine issue x5 5x x2 2x '
                '3x x3 x4 4x'
            ),
        )
        self.stdout.write(f'TE-037 Kroot Carnivores updated, rows={updated}')

        updated = Product.objects.filter(gw_sku__in=['KT-028', '56-14']).update(
            ebay_search_name='Kill Team Stealth Battlesuits Warhammer',
        )
        self.stdout.write(f'KT-028 / 56-14 Stealth Battlesuits updated, rows={updated}')

        updated = Product.objects.filter(gw_sku__in=['TE-019', 'TE-017']).update(
            ebay_search_name='Sun Shark Bomber',
        )
        self.stdout.write(f'TE-019 / TE-017 Sun Shark / Razorshark updated, rows={updated}')

        self.stdout.write(self.style.SUCCESS('apply_batch_fixes_aug2026m done'))
