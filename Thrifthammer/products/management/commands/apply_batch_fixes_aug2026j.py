from django.core.management.base import BaseCommand
from products.models import Product


class Command(BaseCommand):
    help = (
        'Aug 2026j: align Land Raider Redeemer (48-119) ebay_negative_keywords '
        'with Land Raider Crusader (48-22)\'s -- both already share the same '
        'ebay_search_name ("land raider crusader 40k", since it\'s the same '
        'dual-build kit), but Redeemer had extra terms Crusader didn\'t '
        '("D&D 5e 100th 1926 TShirt Plushie Plush") that shifted eBay\'s own '
        'returned result set, excluding a real $98 listing that Crusader '
        'already correctly matches. Verified via a non-saving dry test '
        '2026-08-08 that aligning the keywords surfaces that same listing '
        'for Redeemer too.'
    )

    def handle(self, *args, **options):
        updated = Product.objects.filter(gw_sku='48-119').update(
            ebay_negative_keywords=(
                'legions imperialis Resin 04-113 Proxies Foil magazine issue '
                'x5 5x x10 10x x2 2x 3x x3 x4 4x'
            )
        )
        self.stdout.write(f'48-119 ebay_negative_keywords updated, rows={updated}')

        self.stdout.write(self.style.SUCCESS('apply_batch_fixes_aug2026j done'))
