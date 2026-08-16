from django.core.management.base import BaseCommand
from products.models import Product


class Command(BaseCommand):
    help = (
        'Aug 2026o: eBay allowed-title-word addition per user request '
        '2026-08-09. P-KHORNE-BLOODCRUSHERS "Bloodcrushers of Khorne": '
        'add "3" to ebay_allowed_title_words (was "nos 6", now '
        '"nos 6 3") -- exempts the "(3)" model-count in a listing title '
        'from the standalone-count-digit filter. Note: user explicitly '
        'scoped this to only the allowed-title-word change, not the '
        'other two changes tested alongside it (removing the bare "3" '
        'negative keyword, enabling ebay_allow_no_box) -- this change '
        'alone does not make the specific listing the user asked about '
        'match, since it is still independently blocked by both of '
        'those other filters.'
    )

    def handle(self, *args, **options):
        updated = Product.objects.filter(gw_sku='P-KHORNE-BLOODCRUSHERS').update(
            ebay_allowed_title_words='nos 6 3'
        )
        self.stdout.write(f'P-KHORNE-BLOODCRUSHERS ebay_allowed_title_words updated, rows={updated}')

        self.stdout.write(self.style.SUCCESS('apply_batch_fixes_aug2026o done'))
