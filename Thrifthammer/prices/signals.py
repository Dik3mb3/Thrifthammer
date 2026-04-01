"""
Price signals for the prices app.

1. Price history (pre_save):
   Automatically records a PriceHistory snapshot whenever a CurrentPrice row
   is created or updated with a meaningful change (price moves or stock status
   flips).  This powers future price-trend charts without requiring any changes
   to the import commands themselves — every code path that writes a
   CurrentPrice (Octoparse imports, batch-fix waves, eBay scraper, etc.) is
   captured automatically.

   Logic:
     - On CREATE: record initial history if price is not None.
     - On UPDATE: record history if price OR in_stock changed.
     - Skips recording when price is None (not_available products have no
       meaningful price to chart).
     - Skips recording when nothing changed (idempotent re-runs stay clean).

2. Cache bust (post_save):
   Deletes the product's detail-page cache entry and the home-page cache entry
   whenever a CurrentPrice is saved.  Without this, the 30-minute detail cache
   and the 15-minute list/home caches can fall out of sync after a scraper run,
   causing the search card and the SKU page to show different prices.

   List-page caches use too many key variants (one per query/filter/sort combo)
   to enumerate and delete individually.  Instead, a shared integer counter
   ``product_list_generation`` is incremented on every price save.  The list
   view includes this counter in its cache key, so a single increment
   effectively invalidates every cached list page at once.
"""

from django.core.cache import cache
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from .models import CurrentPrice, PriceHistory


@receiver(pre_save, sender=CurrentPrice)
def track_price_history(sender, instance, **kwargs):
    """
    Record a PriceHistory snapshot on meaningful CurrentPrice changes.

    Fires before every CurrentPrice.save(), including those triggered by
    update_or_create, save(update_fields=[...]), and direct saves.
    """
    # Nothing to chart if the price is unknown / product is not available.
    if instance.price is None:
        return

    if instance.pk:
        # ── UPDATE path: compare new values against what is in the DB ─────────
        try:
            old = CurrentPrice.objects.get(pk=instance.pk)
        except CurrentPrice.DoesNotExist:
            # Race condition edge-case — treat as create.
            PriceHistory.objects.create(
                product=instance.product,
                retailer=instance.retailer,
                price=instance.price,
                in_stock=instance.in_stock,
            )
            return

        price_changed = old.price != instance.price
        stock_changed = old.in_stock != instance.in_stock

        if price_changed or stock_changed:
            PriceHistory.objects.create(
                product=instance.product,
                retailer=instance.retailer,
                price=instance.price,
                in_stock=instance.in_stock,
            )
    else:
        # ── CREATE path: always record initial snapshot ────────────────────────
        PriceHistory.objects.create(
            product=instance.product,
            retailer=instance.retailer,
            price=instance.price,
            in_stock=instance.in_stock,
        )


@receiver(post_save, sender=CurrentPrice)
def bust_price_caches(sender, instance, **kwargs):
    """
    Invalidate all cached pages whenever a CurrentPrice record is saved.

    Clears:
      - product_detail|{slug}        — product detail page cache (30 min TTL)
      - home_page_data_v6            — home page Top 10 Deals cache (15 min TTL)
      - cheapest_price_{product_id}  — per-product cheapest price cache (1 hr TTL)
                                       used on product cards and list pages
      - site_last_price_update       — footer "prices last updated" timestamp (15 min TTL)
      - product_list_generation      — counter included in all list cache keys;
                                       incrementing it invalidates every cached list
                                       page variant at once without enumerating keys

    This keeps the home page deals, list cards, and detail pages all in sync
    immediately after any scraper run updates a CurrentPrice record.
    """
    slug = getattr(instance.product, 'slug', None)
    if slug:
        cache.delete(f'product_detail|{slug}')
    cache.delete('home_page_data_v6')
    cache.delete(f'cheapest_price_{instance.product_id}')
    cache.delete('site_last_price_update')
    # Bust all list-page caches by incrementing the shared generation counter.
    # timeout=None → key never expires on its own; without this the default
    # 5-minute TTL can cause the counter to reset to 0, allowing the list view
    # to hit old gen=0 cache entries that are still within their 15-minute TTL.
    cache.add('product_list_generation', 0, timeout=None)
    cache.incr('product_list_generation')
