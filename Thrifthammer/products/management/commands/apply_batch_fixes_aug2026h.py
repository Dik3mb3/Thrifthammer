from django.core.management.base import BaseCommand
from products.models import Product


class Command(BaseCommand):
    help = (
        'Aug 2026h: add eBay negative keywords per user request 2026-08-08. '
        '(1) CSM-029 "Chaos Space Marines Chaos Lord": add "Virulence" -- '
        'was "...x3 x4 4x jump pack", now "...x3 x4 4x jump pack Virulence". '
        '(2) 99129915052 "Fiends" (Emperor\'s Children): add "Ghost" "Book" '
        '"Leather" -- was "...x3 x4 4x", now "...x3 x4 4x Ghost Book Leather".'
    )

    def handle(self, *args, **options):
        updated = Product.objects.filter(gw_sku='CSM-029').update(
            ebay_negative_keywords=(
                'legions imperialis Resin 04-113 Proxies Foil magazine issue '
                'x5 5x x10 10x x2 2x 3x x3 x4 4x jump pack Virulence'
            )
        )
        self.stdout.write(f'CSM-029 ebay_negative_keywords updated, rows={updated}')

        updated = Product.objects.filter(gw_sku='99129915052').update(
            ebay_negative_keywords=(
                'legions imperialis Resin 04-113 D&D 5e 100th 1926 TShirt '
                'Plushie Plush Proxies Foil magazine issue hell x5 5x x10 10x '
                'x2 2x 3x x3 x4 4x Ghost Book Leather'
            )
        )
        self.stdout.write(f'99129915052 ebay_negative_keywords updated, rows={updated}')

        self.stdout.write(self.style.SUCCESS('apply_batch_fixes_aug2026h done'))
