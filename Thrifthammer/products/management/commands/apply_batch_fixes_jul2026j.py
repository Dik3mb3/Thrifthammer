from django.core.management.base import BaseCommand
from products.models import Product


class Command(BaseCommand):
    help = (
        'Jul 2026j: SWL-078 (Bad Batch) still stealing "Operative '
        'Expansion" listings after blocking one item ID -- exclude the '
        'whole "operative" word so it stops matching that different '
        'sibling product line. Also try search-name wording closer to '
        'confirmed real listings for SWL-028 and SWL-102.'
    )

    def handle(self, *args, **options):
        fixes = [
            ('ebay_negative_keywords', 'SWL-078', '176430904333 operative'),
            ('ebay_search_name', 'SWL-028', 'Star Wars: Legion - TX-130 Saber-Class Tank'),
            ('ebay_search_name', 'SWL-102', 'Atomic Mass Star Wars Legion Battle Deck Card Pack II'),
        ]

        for field, sku, value in fixes:
            updated = Product.objects.filter(gw_sku=sku).update(**{field: value})
            self.stdout.write(f'{sku} {field}=[{value}] rows={updated}')

        self.stdout.write(self.style.SUCCESS('apply_batch_fixes_jul2026j done'))
