"""App configuration for the calculators app."""

from django.apps import AppConfig


class CalculatorsConfig(AppConfig):
    """Configuration for the Space Marine Army Cost Calculator app."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'calculators'
    verbose_name = 'Army Calculators'
