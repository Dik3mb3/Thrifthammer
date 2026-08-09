from django.core.management.base import BaseCommand
from products.models import Product


class Command(BaseCommand):
    help = (
        'Aug 2026l: add more eBay negative keywords per user request '
        '2026-08-09. 43-50 "Death Guard Plague Marines": add '
        '"plaguespitter" "heroes" "Space". Combined with the aug2026k '
        'value this hit 218 chars, 18 over ebay_negative_keywords\' '
        'max_length=200 -- trimmed the pack-size block from '
        '"x5 5x x10 10x x2 2x 3x x3 x4 4x" (31 chars) down to just '
        '"x5 5x x10 10x" (13 chars, frees exactly 18), dropping the '
        'smaller/less-common 2x/3x/4x multiples while keeping the 5- and '
        '10-pack forms (the classic GW sprue/bits bulk-listing sizes). '
        'Confirmed with user 2026-08-09 rather than guessing which terms '
        'to cut. Final value is exactly 200 chars.'
    )

    def handle(self, *args, **options):
        updated = Product.objects.filter(gw_sku='43-50').update(
            ebay_negative_keywords=(
                'belcher spewer Plaguecaster "kill team" launcher '
                'magazine issue x5 5x x10 10x Icon Despair Flail '
                'Corruption Character Heavy Warrior Fighter Bearer Gunner '
                'Bombardier Champion plaguespitter heroes Space'
            )
        )
        self.stdout.write(f'43-50 ebay_negative_keywords updated, rows={updated}')

        self.stdout.write(self.style.SUCCESS('apply_batch_fixes_aug2026l done'))
