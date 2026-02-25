"""
Custom template context processors for ThriftHammer.

Registered in settings.TEMPLATES['OPTIONS']['context_processors'].
Every value returned here is available in every template automatically —
no need to pass it explicitly from views.
"""

from django.core.cache import cache

from products.models import Product


def site_stats(request):
    """
    Inject live site statistics into every template context.

    Currently provides:
        product_count  — total number of active products in the DB,
                         rounded down to the nearest 10 and displayed with a
                         trailing '+' in templates (e.g. 350+).

    Cached for 1 hour — the count only changes when populate_products runs,
    so a short TTL is fine and avoids a DB hit on every page load.
    """
    cache_key = 'site_stats_product_count'
    count = cache.get(cache_key)
    if count is None:
        count = Product.objects.filter(is_active=True).count()
        cache.set(cache_key, count, timeout=3600)  # 1 hour

    # Round down to nearest 10 for the display value (e.g. 357 → 350)
    display_count = (count // 10) * 10

    return {
        'product_count': count,           # exact count if needed
        'product_count_display': f'{display_count}+',  # e.g. "350+"
    }
