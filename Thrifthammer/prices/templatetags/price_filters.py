"""
Custom template filters for price display.

Usage in templates:
    {% load price_filters %}
    {{ cp.price|discount_vs:gw_ref_price }}
"""
from decimal import Decimal, InvalidOperation

from django import template

register = template.Library()


@register.filter
def discount_vs(price, reference):
    """
    Return the % discount of price vs a reference price (e.g. GW retail).

    Positive result  → retailer is CHEAPER than GW  (e.g. 26.2 means −26%)
    Negative result  → retailer is MORE EXPENSIVE    (e.g. −5.0 means +5% above GW)
    None             → missing price data

    Example:
        {{ cp.price|discount_vs:gw_ref_price }}
    """
    try:
        p = Decimal(str(price))
        r = Decimal(str(reference))
        if r <= 0:
            return None
        return round(float((1 - p / r) * 100), 1)
    except (TypeError, ValueError, InvalidOperation):
        return None
