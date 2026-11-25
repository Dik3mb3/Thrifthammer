"""
Custom template filters for the blog app.
"""
import re
from urllib.parse import quote

import nh3
from django import template
from django.utils.html import escape
from django.utils.safestring import mark_safe

register = template.Library()

# <span class="th-best" data-th-best="<product slug>">fallback text</span> in a post body.
# Attribute order is not guaranteed after sanitising, so match the data attribute anywhere in the tag.
_LIVE_PRICE_RE = re.compile(r'<span\b([^>]*\bdata-th-best="([a-z0-9-]+)"[^>]*)>(.*?)</span>', re.S)

# <span data-th-thumb="<product slug>"></span> in a post body becomes that product's small picture.
_THUMB_RE = re.compile(r'<span\b[^>]*\bdata-th-thumb="([a-z0-9-]+)"[^>]*>.*?</span>', re.S)

# <span data-th-off="<product slug>"></span> becomes '26% off', the best price against MSRP, or nothing.
_OFF_RE = re.compile(r'<span\b[^>]*\bdata-th-off="([a-z0-9-]+)"[^>]*>.*?</span>', re.S)

# <span data-th-save="<product slug>"></span> becomes '(MSRP: $210) – Save 26% / Save $55.01' for the best price, or nothing.
_SAVE_RE = re.compile(r'<span\b[^>]*\bdata-th-save="([a-z0-9-]+)"[^>]*>.*?</span>', re.S)

# Thumbnail size in CSS pixels; the WebP copy is requested at twice this for sharp screens.
_THUMB_SIZE = 72

# Retailers whose links earn us commission; every other link is a plain outbound link.
_SPONSORED_RETAILERS = {'amazon', 'ebay', 'noble-knight-games'}

# Tags allowed in blog post bodies. Excludes <script> and other executable tags.
_ALLOWED_TAGS = {
    'a', 'blockquote', 'br', 'div', 'em', 'h2', 'h3', 'h4', 'hr',
    'img', 'li', 'nav', 'ol', 'p', 'span', 'strong', 'style',
    'table', 'tbody', 'td', 'th', 'thead', 'tr', 'ul',
}

# Per-tag attribute allowlists.
_ALLOWED_ATTRIBUTES = {
    'a':          {'href', 'target', 'rel', 'class'},
    'img':        {'src', 'alt', 'class', 'width', 'height', 'loading', 'fetchpriority'},
    'span':       {'class', 'id', 'aria-hidden'},
    'div':        {'class', 'id', 'role', 'aria-label', 'tabindex'},
    'table':      {'id', 'class'},
    'td':         {'class', 'colspan', 'rowspan'},
    'th':         {'class', 'colspan', 'rowspan'},
    'tr':         {'class'},
    'nav':        {'class', 'aria-label'},
    'p':          {'class'},
    'ul':         {'class'},
    'ol':         {'class', 'start'},
    'li':         {'class'},
    'h2':         {'class', 'id'},
    'h3':         {'class', 'id'},
    'h4':         {'class', 'id'},
    'blockquote': {'class'},
}

# Tags whose content is also stripped (not just the tag itself).
_CLEAN_CONTENT_TAGS = {'script', 'noscript', 'iframe', 'object', 'embed'}


@register.filter(is_safe=True)
def sanitize_html(value):
    """
    Strip executable tags (script, iframe, etc.) from blog post HTML while
    preserving safe markup including <style> blocks and data-* attributes.
    """
    if not value:
        return value
    return mark_safe(
        nh3.clean(
            value,
            tags=_ALLOWED_TAGS,
            clean_content_tags=_CLEAN_CONTENT_TAGS,
            attributes=_ALLOWED_ATTRIBUTES,
            generic_attribute_prefixes={'data-'},
            link_rel=None,
            strip_comments=True,
        )
    )


def _format_price(amount):
    """Return a price as $12 for whole dollars or $12.34 otherwise."""
    return f'${amount:,.0f}' if amount == amount.to_integral_value() else f'${amount:,.2f}'


def _live_price_link(product):
    """
    Return '<a>Retailer $price</a>' for the product's cheapest in-stock US price, or None.

    Uses Product.get_cheapest_price(), the same lowest price the product page shows, so
    the blog follows the scrapers (eBay, Amazon, Miniature Market and the rest) with no edits.
    """
    cheapest = product.get_cheapest_price()
    if cheapest is None or cheapest.price is None:
        return None
    text = f'{escape(cheapest.retailer.name)} <span class="bf-price">{escape(_format_price(cheapest.price))}</span>'
    if not cheapest.url:
        return text
    rel = 'noopener noreferrer sponsored' if cheapest.retailer.slug in _SPONSORED_RETAILERS else 'noopener noreferrer'
    return f'<a href="{escape(cheapest.url)}" target="_blank" rel="{rel}">{text}</a>'


def _thumb_html(product):
    """
    Return the product's real picture as a small <picture> (WebP copy plus the original), or None.

    Mirrors the product cards: images come through the wsrv.nl resizer as WebP, except hosts that
    block it. A product with no image gets no thumbnail; nothing is ever substituted.
    """
    src = product.image_url
    if not src:
        return None
    img = (f'<img src="{escape(src)}" alt="{escape(product.name)}" class="th-thumb-img" '
           f'width="{_THUMB_SIZE}" height="{_THUMB_SIZE}" loading="lazy">')
    if 'iwata-airbrush.com' in src:
        return img
    size = _THUMB_SIZE * 2
    webp = f'https://wsrv.nl/?url={quote(src, safe="")}&amp;output=webp&amp;w={size}&amp;h={size}&amp;fit=cover'
    return f'<picture><source srcset="{webp}" type="image/webp">{img}</picture>'


def _off_text(product):
    """Return '26% off' for the cheapest in-stock US price against MSRP, or None when it is not a real discount."""
    cheapest = product.get_cheapest_price()
    if cheapest is None or cheapest.price is None or not product.msrp or cheapest.price >= product.msrp:
        return None
    percent = round((product.msrp - cheapest.price) / product.msrp * 100)
    return f'{percent}% off' if percent >= 1 else None


def _save_html(product):
    """
    Return '(MSRP: $210) – Save 26% / Save $55.01' for the cheapest in-stock US price against MSRP.

    Same shape as the retailer rows, so the best price row reads like the others. None when the
    best price is not below MSRP (nothing is shown rather than a stale saving).
    """
    cheapest = product.get_cheapest_price()
    if cheapest is None or cheapest.price is None or not product.msrp or cheapest.price >= product.msrp:
        return None
    amount = product.msrp - cheapest.price
    percent = round(amount / product.msrp * 100)
    if percent < 1:
        return None
    return (f'<span class="bf-msrp">(MSRP: {escape(_format_price(product.msrp))})</span> – '
            f'<span class="bf-save-pct">Save {percent}%</span> / '
            f'<span class="bf-save-amt">Save {escape(_format_price(amount))}</span>')


@register.filter(is_safe=True)
def live_prices(value):
    """
    Fill the live markers in a post body. Apply after sanitize_html.

    <span data-th-best="product-slug">: shows the product's current best price. The text written
    inside the span is only a fallback: it stays if the product is missing, inactive or has no price.
    <span data-th-thumb="product-slug"></span>: shows the product's small picture, or nothing at all
    if the product is missing, inactive or has no image.
    <span data-th-off="product-slug"></span>: shows the best price as a percent off MSRP, or nothing
    when there is no real discount (a badge is never left over from an earlier price).
    <span data-th-save="product-slug"></span>: shows '(MSRP: $210) – Save 26% / Save $55.01' for the best
    price, or nothing when the best price is not below MSRP.
    """
    if not value or not any(marker in value for marker in ('data-th-best', 'data-th-thumb', 'data-th-off', 'data-th-save')):
        return value
    from products.models import Product  # imported here to keep the blog app importable on its own

    slugs = ({m.group(2) for m in _LIVE_PRICE_RE.finditer(value)} | {m.group(1) for m in _THUMB_RE.finditer(value)}
             | {m.group(1) for m in _OFF_RE.finditer(value)} | {m.group(1) for m in _SAVE_RE.finditer(value)})
    products = {p.slug: p for p in Product.objects.filter(slug__in=slugs, is_active=True)}

    def _swap_price(match):
        product = products.get(match.group(2))
        replacement = _live_price_link(product) if product else None
        if replacement is None:
            return match.group(0)
        return f'<span{match.group(1)}>{replacement}</span>'

    def _swap_thumb(match):
        product = products.get(match.group(1))
        return (_thumb_html(product) if product else None) or ''

    def _swap_off(match):
        product = products.get(match.group(1))
        text = _off_text(product) if product else None
        return f'<span class="bf-badge">{text}</span>' if text else ''

    def _swap_save(match):
        product = products.get(match.group(1))
        return (_save_html(product) if product else None) or ''

    value = _LIVE_PRICE_RE.sub(_swap_price, value)
    value = _THUMB_RE.sub(_swap_thumb, value)
    return mark_safe(_SAVE_RE.sub(_swap_save, _OFF_RE.sub(_swap_off, value)))
