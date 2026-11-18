"""
Shared helper for the deal newsletters (weekly, Friday, Monday, Sunday and
their UK twins).

Some kits are listed as more than one product on the site (for example the
Dracothian Guard box is both "Stormcast Eternals Tempestors" and "Stormcast
Eternals Lord-Celestant on Dracoth"). Both products point at the same
retailer listing, so a digest would show the same deal twice. pick_unique_deals
keeps the best-ranked product for each listing and moves on to the next one.
"""

import datetime
from urllib.parse import urlsplit

from django.utils import timezone

from prices.models import CurrentPrice

# "Most $ Saved" tab: only products at least this far below MSRP qualify.
SAVED_TAB_MIN_PCT = 20

# A curated list not edited for more than this many days is left out of the
# email, so last week's picks are never sent a second time.
CURATED_STALE_AFTER_DAYS = 6

# Title of the Curated tab when the list has no name of its own.
CURATED_TAB_LABEL = 'Curated Picks'

# Shown under the deal tabs in the Wednesday and Friday emails (HTML and text).
DEAL_FOOTNOTE = (
    'The prices you see may not be available when you view due to changing '
    'prices or the listing selling out.'
)


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


def deal_pct(product):
    """Return the % discount of a candidate vs its live reference (MSRP) price."""
    return float(product.gw_ref_price - product.min_price) / float(product.gw_ref_price) * 100


def order_candidates(candidates, by='pct'):
    """
    Order annotated candidate products (they carry gw_ref_price and min_price).

    by='pct'   -> biggest % discount first (the "Best Discount" tab).
    by='saved' -> biggest amount saved first, only for products at least
                  SAVED_TAB_MIN_PCT below MSRP (the "Most $ Saved" tab).
    """
    if by == 'saved':
        eligible = [p for p in candidates if deal_pct(p) >= SAVED_TAB_MIN_PCT]
        return sorted(
            eligible,
            key=lambda p: (p.gw_ref_price - p.min_price, deal_pct(p)),
            reverse=True,
        )
    return sorted(candidates, key=deal_pct, reverse=True)


def get_curated_entries(digest, region, now=None):
    """
    Return (product_ids, status) for the weekly curated list of one digest/region.

    product_ids is a list of product ids in position order, or [] when the
    tab should be left out. status is a short message saying why, for the
    command's log: the list is missing, empty, or stale (not edited for more
    than CURATED_STALE_AFTER_DAYS days).
    """
    from products.models import CuratedDealList  # local import: models import this app's helpers at load time

    now = now or timezone.now()
    deal_list = CuratedDealList.objects.filter(digest=digest, region=region).first()
    if deal_list is None:
        return [], 'no curated list set up'
    age = now - deal_list.updated_at
    if age > datetime.timedelta(days=CURATED_STALE_AFTER_DAYS):
        return [], f'curated list is stale (last edited {age.days} days ago), tab left out'
    product_ids = list(
        deal_list.items.filter(product__is_active=True).values_list('product_id', flat=True)
    )
    if not product_ids:
        return [], 'curated list is empty, tab left out'
    return product_ids, f'{len(product_ids)} curated pick(s)'


def get_curated_label(digest, uk):
    """
    Return the title of the Curated tab for one digest and region.

    It is the name typed on the curated list in the admin (for example "Elves &
    Orcs"), or "Curated Picks" when the list has none.
    """
    from products.models import CuratedDealList  # local import, same reason as get_curated_entries

    title = (
        CuratedDealList.objects.filter(digest=digest, region='uk' if uk else 'us')
        .values_list('title', flat=True).first()
    )
    return (title or '').strip() or CURATED_TAB_LABEL


def build_deal_tabs(curated, discount, saved, currency_symbol='$', curated_label=None):
    """
    Return the non-empty tabs in display order: Curated, Best Discount, Most Saved.

    Each tab is a dict with key, label and deals. A tab with no deals is left
    out entirely, so an empty curated list never shows an empty tab. The
    Curated tab is titled ``curated_label`` (default "Curated Picks").
    """
    candidates = (
        ('curated', curated_label or CURATED_TAB_LABEL, curated),
        ('discount', 'Best Discount', discount),
        ('saved', f'Most {currency_symbol} Saved', saved),
    )
    return [
        {'key': key, 'label': label, 'deals': deals}
        for key, label, deals in candidates if deals
    ]


def build_text_sections(tabs, currency_symbol='$'):
    """Return plain-text lines for every tab, numbered, followed by the footnote."""
    lines = []
    for tab in tabs:
        lines += [tab['label'].upper(), '']
        for i, d in enumerate(tab['deals'], 1):
            lines.append(f'{i:>2}. {d["name"]}')
            lines.append(f'    {_text_price_line(d, currency_symbol)}')
            lines.append(f'    {d["url"]}')
            lines.append('')
    lines += [DEAL_FOOTNOTE, '']
    return lines


def _text_price_line(deal, currency_symbol):
    """
    Return the one-line price summary used in the plain-text email.

    Every tab shows both the percentage and the whole-unit amount saved, e.g.
    "save 33% / save $52 off $155.00 MSRP". The amount is rounded half up like
    the HTML badge (floatformat:0). A deal at or above MSRP shows only its price.
    """
    price = f'{currency_symbol}{deal["price"]:.2f}'
    if deal['pct_off'] <= 0:
        return f'{price} at {deal["retailer"]}'
    return (
        f'{price}  (save {deal["pct_off"]:.0f}% / save {currency_symbol}{int(deal["savings"] + 0.5)} off '
        f'{currency_symbol}{deal["msrp"]:.2f} MSRP at {deal["retailer"]})'
    )


def build_deal(product, uk, with_category=False):
    """
    Return the dict one email row is built from.

    The product must carry gw_ref_price (may be None for a curated pick with
    no reference price) and min_price. pct_off and savings are 0 when the
    price is not below the reference price, so the email shows the price
    without a discount badge.
    """
    ref = product.gw_ref_price
    price = product.min_price
    below = ref is not None and ref > 0 and price < ref
    row = _best_price_row(product, uk)
    deal = {
        'name': product.name,
        'slug': product.slug,
        'url': f'https://thrifthammer.com/products/{product.slug}/?region={"uk" if uk else "us"}',
        'price': float(price),
        'msrp': float(ref) if ref else 0.0,
        'pct_off': deal_pct(product) if below else 0.0,
        'savings': float(ref - price) if below else 0.0,
        'retailer': row.retailer.name if row and row.retailer else 'a retailer',
        'image_url': product.image_url or '',
    }
    if with_category:
        deal['category'] = product.category.name if product.category else ''
    return deal


def get_curated_deals(source, digest, uk, with_category=False):
    """
    Return (deals, status) for the Curated Picks tab of one digest and region.

    ``source`` is the send command: it supplies _annotated_products() and
    _with_cheapest_price() so the price and reference-price rules are exactly
    the ones the rest of that digest uses. A curated pick needs an in-stock
    price in the region but no minimum discount; picks without one are
    skipped and counted in the status.
    """
    product_ids, status = get_curated_entries(digest, 'uk' if uk else 'us')
    if not product_ids:
        return [], status
    queryset = source._with_cheapest_price(
        source._annotated_products(require_ref=False).filter(pk__in=product_ids)
    ).select_related('category', 'faction')
    by_pk = {product.pk: product for product in queryset}
    deals = [
        build_deal(by_pk[pid], uk, with_category=with_category)
        for pid in product_ids if pid in by_pk
    ]
    skipped = len(product_ids) - len(deals)
    status = f'{len(deals)} curated pick(s)'
    if skipped:
        status += f', {skipped} skipped (no in-stock price in this region)'
    return deals, status


def tab_log_lines(curated_status, curated, saved, currency_symbol='$', curated_label=None):
    """Return the log lines that show the Curated and Most Saved tabs next to the main deal list."""
    lines = ['', f'Curated Picks tab: {curated_status}']
    if curated_label and curated_label != CURATED_TAB_LABEL:
        lines.append(f'  Tab title this week: "{curated_label}"')
    lines += [_log_line(i, d, currency_symbol) for i, d in enumerate(curated, 1)]
    lines += ['', f'Most {currency_symbol} Saved tab ({SAVED_TAB_MIN_PCT}%+ off): {len(saved)} deal(s)']
    lines += [_log_line(i, d, currency_symbol) for i, d in enumerate(saved, 1)]
    return lines


def _log_line(index, deal, currency_symbol):
    """Return one numbered log line for a deal."""
    return (
        f'  {index:>2}. {deal["name"]:50s}  {currency_symbol}{deal["price"]:.2f}  '
        f'(save {currency_symbol}{deal["savings"]:.2f}, {deal["pct_off"]:.0f}% off {currency_symbol}{deal["msrp"]:.2f})'
    )
