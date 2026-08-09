from django.core.management.base import BaseCommand
from products.models import Product


class Command(BaseCommand):
    help = (
        'Aug 2026i: fix ebay_search_name and ebay_allowed_title_words for '
        'the shared prod3590140 SKU (Obelisk & Transcendent C\'tan / '
        'Tesseract Vault, id 611 and 612) -- neither product had a real '
        'eBay match; the old search name "Tesseract Vault Necron '
        'Warhammer" never returned the real dual-build listing. User '
        'found a real listing titled "Tesseract Vault / Obelisk & '
        'Transcendent C\'tan Necrons Warhammer 40K" ($167.45) -- verified '
        'via a non-saving dry test 2026-08-08 that the corrected search '
        'name surfaces it as both eBay Best Match #1 and cheapest valid. '
        'ebay_allowed_title_words="&" is required to bypass the bundle-'
        'detection filter (rejects any title containing " & " otherwise).'
    )

    def handle(self, *args, **options):
        updated = Product.objects.filter(gw_sku='prod3590140').update(
            ebay_search_name="Tesseract Vault / Obelisk & Transcendent C'tan",
            ebay_allowed_title_words='&',
        )
        self.stdout.write(f'prod3590140 (both rows) updated, rows={updated}')

        self.stdout.write(self.style.SUCCESS('apply_batch_fixes_aug2026i done'))
