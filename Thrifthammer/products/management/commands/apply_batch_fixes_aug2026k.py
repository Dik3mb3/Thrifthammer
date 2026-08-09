from django.core.management.base import BaseCommand
from products.models import Product


class Command(BaseCommand):
    help = (
        'Aug 2026k: add eBay negative keywords per user request 2026-08-09. '
        '43-50 "Death Guard Plague Marines": add "Flail" "Corruption" '
        '"Character" "Heavy" "Warrior" "Fighter" "Bearer" "Gunner" '
        '"Bombardier" "Champion". The full new value (236 chars) exceeded '
        'ebay_negative_keywords\' max_length=200, so the generic shared '
        '"legions imperialis Resin 04-113 Proxies Foil" boilerplate block '
        '(unrelated product line, duplicated across most products\' '
        'keyword lists) was dropped to make room -- confirmed with user '
        '2026-08-09 rather than guessing which terms to cut. All '
        'Death-Guard-specific terms (belcher/spewer/Plaguecaster/"kill '
        'team"/launcher/magazine issue/pack-size block/Icon/Despair) and '
        'all 10 new words are kept. Final value is 191 chars.'
    )

    def handle(self, *args, **options):
        updated = Product.objects.filter(gw_sku='43-50').update(
            ebay_negative_keywords=(
                'belcher spewer Plaguecaster "kill team" launcher '
                'magazine issue x5 5x x10 10x x2 2x 3x x3 x4 4x Icon '
                'Despair Flail Corruption Character Heavy Warrior Fighter '
                'Bearer Gunner Bombardier Champion'
            )
        )
        self.stdout.write(f'43-50 ebay_negative_keywords updated, rows={updated}')

        self.stdout.write(self.style.SUCCESS('apply_batch_fixes_aug2026k done'))
