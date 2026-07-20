from django.core.management.base import BaseCommand
from products.models import Product


class Command(BaseCommand):
    help = (
        'Jul 2026s: eBay negative keyword addition -- 43-50 (Death Guard '
        'Plague Marines) gets "launcher" to stop matching listings for '
        'Plague Marines with a plasma gun / launcher weapon-option variant.'
    )

    def handle(self, *args, **options):
        fixes = [
            ('ebay_negative_keywords', '43-50', 'legions imperialis Resin 04-113 Proxies Foil belcher spewer Plaguecaster "kill team" launcher'),
        ]

        for field, sku, value in fixes:
            updated = Product.objects.filter(gw_sku=sku).update(**{field: value})
            self.stdout.write(f'{sku} {field}=[{value}] rows={updated}')

        self.stdout.write(self.style.SUCCESS('apply_batch_fixes_jul2026s done'))
