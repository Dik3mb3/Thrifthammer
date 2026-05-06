"""Add 'Dice' eBay negative keyword to all Blood Bowl products."""

from django.core.management.base import BaseCommand
from products.models import Product


class Command(BaseCommand):
    help = 'Add Dice to ebay_negative_keywords for all Blood Bowl products.'

    def handle(self, *args, **options):
        updated = 0
        for product in Product.objects.filter(batch_tag='blood-bowl', is_active=True):
            existing = product.ebay_negative_keywords or ''
            if 'dice' not in existing.lower():
                product.ebay_negative_keywords = (existing + ' Dice').strip()
                product.save(update_fields=['ebay_negative_keywords'])
                updated += 1
        self.stdout.write(self.style.SUCCESS(f'Updated {updated} Blood Bowl products with Dice negative keyword.'))
