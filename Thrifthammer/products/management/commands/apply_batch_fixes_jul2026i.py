from django.core.management.base import BaseCommand
from products.models import Product


class Command(BaseCommand):
    help = (
        'Jul 2026i: allow "card"/"upgrade" bits-filter words for 3 Star '
        'Wars: Legion SKUs whose real product names collide with the '
        'global bits-filter blocklist; block a wrong eBay item ID for '
        'SWL-078 (Bad Batch) that was stealing SWL-014\'s listing.'
    )

    def handle(self, *args, **options):
        fixes = [
            ('ebay_allowed_title_words', 'SWL-057', 'card upgrade 1 2 3 4 5 6 7 8 9'),
            ('ebay_allowed_title_words', 'SWL-094', 'card 1 2 3 4 5 6 7 8 9'),
            ('ebay_allowed_title_words', 'SWL-100', 'card 1 2 3 4 5 6 7 8 9'),
            ('ebay_negative_keywords', 'SWL-078', '176430904333'),
        ]

        for field, sku, value in fixes:
            updated = Product.objects.filter(gw_sku=sku).update(**{field: value})
            self.stdout.write(f'{sku} {field}=[{value}] rows={updated}')

        self.stdout.write(self.style.SUCCESS('apply_batch_fixes_jul2026i done'))
