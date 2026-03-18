"""App configuration for the prices app."""

from django.apps import AppConfig


class PricesConfig(AppConfig):
    """Configuration for the prices app — registers price-history signals."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'prices'

    def ready(self):
        """Connect price history signal when Django starts."""
        import prices.signals  # noqa: F401 — imported for side-effects (signal registration)
