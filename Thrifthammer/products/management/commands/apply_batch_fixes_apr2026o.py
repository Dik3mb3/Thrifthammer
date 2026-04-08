"""
apply_batch_fixes_apr2026o
~~~~~~~~~~~~~~~~~~~~~~~~~~
Delete all inactive (is_active=False) products so their URLs stop returning
404s and stop appearing in Google Search Console as crawl errors.
"""

from django.core.management.base import BaseCommand

from products.models import Product


class Command(BaseCommand):
    help = 'Apr-2026-o: Delete all inactive products to eliminate 404 crawl errors.'

    def handle(self, *args, **options):
        inactive = Product.objects.filter(is_active=False)
        count = inactive.count()
        slugs = list(inactive.values_list('slug', flat=True))
        inactive.delete()
        for slug in slugs:
            self.stdout.write(f'  Deleted: {slug}')
        self.stdout.write(self.style.SUCCESS(f'Done. Deleted {count} inactive products.'))
