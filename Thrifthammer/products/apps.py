from django.apps import AppConfig


class ProductsConfig(AppConfig):
    """Configuration for the products app — registers product cache-bust signals."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'products'

    def ready(self):
        import products.signals  # noqa: F401 — imported for side-effects (signal registration)
