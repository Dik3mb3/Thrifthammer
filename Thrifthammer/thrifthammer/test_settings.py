"""
Settings for running the test suite safely.

Run with:
    python manage.py test products --settings=thrifthammer.test_settings

Starts from the normal settings, then:
- uses a throwaway in-memory SQLite database, so a test run can never touch the
  production database that .env points at;
- skips migrations and builds the tables straight from the models. The data
  migration products/0023_votann_chaos_knights_pages assumes the production
  'Warhammer 40,000' category already exists, so it fails on an empty database.
"""

from .settings import *  # noqa: F401,F403

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}


class _DisableMigrations:
    """MIGRATION_MODULES stand-in that tells Django no app has migrations."""

    def __contains__(self, item):
        """Every app is treated as having a migrations override."""
        return True

    def __getitem__(self, item):
        """A None module means "do not run this app's migrations"."""
        return None


MIGRATION_MODULES = _DisableMigrations()
