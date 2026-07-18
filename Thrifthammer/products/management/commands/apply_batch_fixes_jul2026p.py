from django.core.management.base import BaseCommand
from products.models import Product


class Command(BaseCommand):
    help = (
        'Jul 2026p: eBay negative keyword addition for Bloodcrushers of '
        'Khorne (P-KHORNE-BLOODCRUSHERS) -- blocks a specific listing '
        '(item 164558591084) that has only 3 of the 6 models the SKU '
        'represents by its exact eBay item ID. No distinguishing title/'
        'description text exists to block it by word, and the matcher '
        'picks cheapest-valid, so it was winning over the correct '
        '"(6)" listing on price alone. This blocks the one listing only, '
        'not the seller.'
    )

    def handle(self, *args, **options):
        fixes = [
            ('ebay_negative_keywords', 'P-KHORNE-BLOODCRUSHERS', 'Sealed legions imperialis Resin 04-113 D&D 5e 100th 1926 TShirt Plushie Plush Proxies Foil 3 164558591084'),
        ]

        for field, sku, value in fixes:
            updated = Product.objects.filter(gw_sku=sku).update(**{field: value})
            self.stdout.write(f'{sku} {field}=[{value}] rows={updated}')

        self.stdout.write(self.style.SUCCESS('apply_batch_fixes_jul2026p done'))
