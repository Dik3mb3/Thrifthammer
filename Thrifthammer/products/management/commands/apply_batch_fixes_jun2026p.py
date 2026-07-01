from django.core.management.base import BaseCommand

from products.models import Product


class Command(BaseCommand):
    help = 'Jun 2026p: Delete KT-001 Kill Team Starter Set from DB'

    def handle(self, *args, **options):
        deleted, _ = Product.objects.filter(gw_sku='KT-001').delete()
        self.stdout.write(f'KT-001 deleted rows={deleted}')
        self.stdout.write(self.style.SUCCESS('apply_batch_fixes_jun2026p done'))
