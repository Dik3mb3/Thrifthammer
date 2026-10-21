"""
Shared helper for the deal newsletters (weekly, Friday, Monday, Sunday and
their UK twins).

Some kits are listed as more than one product on the site (for example the
Dracothian Guard box is both "Stormcast Eternals Tempestors" and "Stormcast
Eternals Lord-Celestant on Dracoth"). Both products point at the same
retailer listing, so a digest would show the same deal twice. pick_unique_deals
keeps the best-ranked product for each listing and moves on to the next one.
"""

from urllib.parse import urlsplit

from prices.models import CurrentPrice


def _listing_key(price_row):
    """Return a key identifying the retailer listing, ignoring the query string."""
    parts = urlsplit(price_row.url or '')
    if not parts.netloc:
        return None
    return (parts.netloc.lower(), parts.path.rstrip('/'))


def _best_price_row(product, uk):
    """Return the in-stock price row that gives the product its lowest price."""
    return (
        CurrentPrice.objects
        .filter(
            product=product,
            in_stock=True,
            not_available=False,
            price=product.min_price,
            retailer__is_uk=uk,
        )
        .select_related('retailer')
        .first()
    )


def pick_unique_deals(sorted_candidates, limit, uk=False):
    """
    Return up to `limit` products from `sorted_candidates` (best deal first),
    skipping any product whose cheapest listing was already picked.

    Products with no usable listing URL are never treated as duplicates.
    """
    picked, seen = [], set()
    for product in sorted_candidates:
        row = _best_price_row(product, uk)
        key = _listing_key(row) if row else None
        if key is not None and key in seen:
            continue
        if key is not None:
            seen.add(key)
        picked.append(product)
        if len(picked) == limit:
            break
    return picked
