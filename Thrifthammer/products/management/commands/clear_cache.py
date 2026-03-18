"""Management command: clear_cache — clears the entire Django cache table."""

from django.core.cache import cache
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    """Clear all entries from the Django cache backend."""

    help = 'Clear all entries from the Django cache (DatabaseCache backend).'

    def handle(self, *args, **options):
        """Delete every key from the cache."""
        cache.clear()
        self.stdout.write(self.style.SUCCESS('Cache cleared successfully.'))
