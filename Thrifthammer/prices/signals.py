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

2. Cache bust (post_save on CurrentPrice and BookFormatPrice):
   Deletes the product's detail-page cache entry and the home-page cache entry
   whenever a price row is saved.  Without this, the 30-minute detail cache
   and the 15-minute list/home caches can fall out of sync after a scraper run,
   causing the search card and the SKU page to show different prices.

   product_detail's cache key is region-suffixed (`product_detail|{slug}|us`
   or `|uk` -- see product_detail() in products/views.py), so both region
   variants are deleted since this signal doesn't know which one the caller
   cares about. (Found 2026-09-06: this delete previously used the bare
   `product_detail|{slug}` key with no region suffix at all, which never
   matched the real cache key -- a no-op that had been silently failing to
   bust ANY product's detail-page cache, sitewide, for both regions, since
   the region feature was added.)

   List-page caches use too many key variants (one per query/filter/sort combo)
   to enumerate and delete individually.  Instead, a shared integer counter
   ``product_list_generation`` is incremented on every price save.  The list
   view includes this counter in its cache key, so a single increment
   effectively invalidates every cached list page at once.

   BookFormatPrice shares the same bust logic as CurrentPrice (same cache
   keys, same product) but not the price-history tracking above -- there is
   no book equivalent of PriceHistory yet.
"""

import logging

from django.core.cache import cache
from django.db import InterfaceError, OperationalError
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from .models import BookFormatPrice, CurrentPrice, PriceHistory

logger = logging.getLogger(__name__)


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


def _bust_product_caches(product_id, slug):
    """
    Invalidate all cached pages for one product.

    Clears:
      - product_detail|{slug}|us     — product detail page cache, US region (30 min TTL)
      - product_detail|{slug}|uk     — product detail page cache, UK region (30 min TTL)
      - home_page_data_v6            — home page Top 10 Deals cache (15 min TTL)
      - cheapest_price_{product_id}  — per-product cheapest price cache (1 hr TTL)
                                       used on product cards and list pages
      - site_last_price_update       — footer "prices last updated" timestamp (15 min TTL)
      - product_list_generation      — counter included in all list cache keys;
                                       incrementing it invalidates every cached list
                                       page variant at once without enumerating keys

    Both region variants are deleted unconditionally since the caller (a
    CurrentPrice or BookFormatPrice save) doesn't know which region's page
    actually shows this row -- deleting an unused region's key is a harmless
    no-op, but skipping the region that DOES matter leaves it stale.

    The cache backend is DatabaseCache (a Postgres table), so every call
    below is itself a DB query on the same connection the caller's save()
    just used. Called synchronously inside every price-row save, in every
    command that writes prices -- including ones with no connection-retry
    protection of their own. Exceptions are the caller's responsibility to
    catch (see the OperationalError/InterfaceError handling in each receiver
    below) so a dropped connection here never crashes the caller's save.
    """
    if slug:
        cache.delete(f'product_detail|{slug}|us')
        cache.delete(f'product_detail|{slug}|uk')
    cache.delete('home_page_data_v6')
    cache.delete(f'cheapest_price_{product_id}')
    cache.delete('site_last_price_update')
    # Bust all list-page caches by incrementing the shared generation counter.
    # timeout=None → key never expires on its own; without this the default
    # 5-minute TTL can cause the counter to reset to 0, allowing the list view
    # to hit old gen=0 cache entries that are still within their 15-minute TTL.
    cache.add('product_list_generation', 0, timeout=None)
    cache.incr('product_list_generation')


@receiver(post_save, sender=CurrentPrice)
def bust_price_caches(sender, instance, **kwargs):
    """
    Invalidate all cached pages whenever a CurrentPrice record is saved.

    This keeps the home page deals, list cards, and detail pages all in sync
    immediately after any scraper run updates a CurrentPrice record.

    Cache-busting is best-effort: on a DB connection failure, skip it and log
    a warning -- worst case is a stale list/detail cache for a few minutes
    until the next successful save, not a crashed batch job.
    """
    try:
        _bust_product_caches(instance.product_id, getattr(instance.product, 'slug', None))
    except (OperationalError, InterfaceError) as exc:
        logger.warning(
            'bust_price_caches: skipped cache invalidation for CurrentPrice pk=%s '
            'after a DB connection error: %s',
            instance.pk, exc,
        )


@receiver(post_save, sender=BookFormatPrice)
def bust_book_price_caches(sender, instance, **kwargs):
    """
    Invalidate all cached pages whenever a BookFormatPrice record is saved.

    Same rationale and cache keys as bust_price_caches above -- a book
    product's detail/list pages are cached identically to a miniature
    product's. Every book-price command (populate_*_books, find_amazon_book_asins,
    update_amazon_book_prices, update_ebay_book_prices, seed_nk_*_books_prices)
    writes BookFormatPrice rows and previously triggered no cache invalidation
    at all, since this signal didn't exist -- book detail pages could show
    stale/missing prices for up to 30 minutes after a real update.
    """
    try:
        _bust_product_caches(instance.product_id, getattr(instance.product, 'slug', None))
    except (OperationalError, InterfaceError) as exc:
        logger.warning(
            'bust_book_price_caches: skipped cache invalidation for BookFormatPrice pk=%s '
            'after a DB connection error: %s',
            instance.pk, exc,
        )
