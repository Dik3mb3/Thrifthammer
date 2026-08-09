"""Management command: clear_cache — clears the entire Django cache table."""

from django.conf import settings
from django.core.cache import cache
from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    """Clear all entries from the Django cache backend."""

    help = 'Clear all entries from the Django cache (DatabaseCache backend).'

    def handle(self, *args, **options):
        """Empty the cache table.

        Uses TRUNCATE instead of cache.clear() (a plain DELETE) when the
        backend is the DatabaseCache, so storage is reclaimed immediately
        instead of left as reusable-but-unshrunk space. Running a
        DELETE-based clear on every deploy let this table's TOAST storage
        grow to 300+ MB over time despite holding only ~10 MB of real
        cached data at any given moment.
        """
        backend = settings.CACHES['default']['BACKEND']
        if 'db.DatabaseCache' in backend:
            table = settings.CACHES['default'].get('LOCATION', 'django_cache')
            quoted_table = connection.ops.quote_name(table)
            with connection.cursor() as cursor:
                cursor.execute(f'TRUNCATE TABLE {quoted_table}')
            self.stdout.write(self.style.SUCCESS('Cache table truncated successfully.'))
        else:
            cache.clear()
            self.stdout.write(self.style.SUCCESS('Cache cleared successfully.'))
