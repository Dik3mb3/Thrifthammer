from django.core.management.base import BaseCommand
from products.models import Product


class Command(BaseCommand):
    help = 'Jul 2026c: deactivate KT-108 (Kill Team: Salvation)'

    def handle(self, *args, **options):
        fixes = [
            ('is_active', 'KT-108', False),
        ]

        for field, sku, value in fixes:
            updated = Product.objects.filter(gw_sku=sku).update(**{field: value})
            self.stdout.write(f'{sku} {field}=[{value}] rows={updated}')

        self.stdout.write(self.style.SUCCESS('apply_batch_fixes_jul2026c done'))
