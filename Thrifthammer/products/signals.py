"""
Product signals for the products app.

Cache bust (post_save):
  Whenever a Product record is saved, this signal:

  1. Deletes the product's detail-page cache entry so field changes (e.g.
     gw_url, image_url, description, name) from batch fixes or the admin
     appear immediately instead of waiting for the 30-minute TTL.

  2. Increments the shared ``product_list_generation`` counter so that every
     cached product-list page (search bar, browse page) is also considered
     stale.  The list view reads this counter into its cache key, so
     incrementing it is equivalent to flushing every list-page variant at once
     without needing to enumerate them individually.

Together with the same counter increment in prices/signals.py (which fires on
CurrentPrice saves), this ensures that scraper runs, batch fixes, and admin
edits all propagate to every page on the site automatically — no manual cache
clearing required.
"""

from django.core.cache import cache
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Product


@receiver(post_save, sender=Product)
def bust_product_caches(sender, instance, **kwargs):
    """
    Invalidate all caches affected by a Product field change.

    Clears:
      - product_detail|{slug}     — detail page cache (30 min TTL)
      - product_list_generation   — shared counter that invalidates all list
                                    page cache variants simultaneously
    """
    if instance.slug:
        cache.delete(f'product_detail|{instance.slug}')
    # Bust all list-page caches by incrementing the shared generation counter.
    # timeout=None keeps the counter alive indefinitely; without it the key can
    # expire and reset to 0, allowing the list view to hit orphaned gen=0 entries.
    cache.add('product_list_generation', 0, timeout=None)
    cache.incr('product_list_generation')
