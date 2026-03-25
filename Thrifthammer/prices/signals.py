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

   The list-page cache (keyed by query/filter/sort) is intentionally left intact
   because there are too many possible keys to enumerate.  The detail page is the
   one users land on after clicking a search card, so busting it on every price
   change is the highest-value invalidation target.
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
    Invalidate cached pages whenever a CurrentPrice record is saved.

    Clears:
      - product_detail|{slug}  — the product detail page cache (30 min TTL)
      - home_page_data_v4      — the home page Top 10 deals cache (15 min TTL)

    This prevents the search card price (from the 15-min list cache) and the
    SKU detail page (from the 30-min detail cache) from diverging after a
    scraper run updates a CurrentPrice record.
    """
    slug = getattr(instance.product, 'slug', None)
    if slug:
        cache.delete(f'product_detail|{slug}')
    cache.delete('home_page_data_v4')
