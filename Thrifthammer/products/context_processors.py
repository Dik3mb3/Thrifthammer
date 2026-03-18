"""
Custom template context processors for ThriftHammer.

Registered in settings.TEMPLATES['OPTIONS']['context_processors'].
Every value returned here is available in every template automatically —
no need to pass it explicitly from views.
"""

from django.core.cache import cache
from django.db.models import Max

from prices.models import CurrentPrice
from products.models import Product


def site_stats(request):
    """
    Inject live site statistics into every template context.

    Provides:
        product_count        — total active products (exact int).
        product_count_display — rounded down to nearest 10 with '+' suffix.
        last_price_update    — datetime of the most recent CurrentPrice save,
                               or None if no prices exist.  Powered by the
                               auto_now ``last_seen`` field on CurrentPrice,
                               so it updates automatically every time any
                               import command or batch-fix wave touches a row.

    Cached for 15 minutes — balances freshness against DB overhead.
    """
    count = cache.get('site_stats_product_count')
    if count is None:
        count = Product.objects.filter(is_active=True).count()
        cache.set('site_stats_product_count', count, timeout=3600)  # 1 hour

    last_update = cache.get('site_last_price_update')
    if last_update is None:
        last_update = CurrentPrice.objects.aggregate(m=Max('last_seen'))['m']
        cache.set('site_last_price_update', last_update, timeout=900)  # 15 min

    # Round down to nearest 10 for the display value (e.g. 357 → "350+")
    display_count = (count // 10) * 10

    return {
        'product_count': count,
        'product_count_display': f'{display_count}+',
        'last_price_update': last_update,
    }
