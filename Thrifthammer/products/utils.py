"""
Shared utility functions for the products app and other apps.
"""

from django.utils.text import slugify


def unique_slug(base_text, model_class, max_len=220, exclude_pk=None):
    """
    Generate a unique slug for a model instance.

    Slugifies base_text, then appends an incrementing counter (-1, -2, …)
    until no collision exists in the database.

    Args:
        base_text:   Text to slugify (e.g. a title or name).
        model_class: The Django model to check for collisions.
        max_len:     Maximum slug length before counter is appended. Default 220.
        exclude_pk:  Exclude this PK from the collision check (for updates).

    Returns:
        str: A slug guaranteed unique within model_class.
    """
    base = slugify(base_text)[:max_len]
    slug = base
    counter = 1
    while model_class.objects.filter(slug=slug).exclude(pk=exclude_pk).exists():
        slug = f"{base}-{counter}"
        counter += 1
    return slug
