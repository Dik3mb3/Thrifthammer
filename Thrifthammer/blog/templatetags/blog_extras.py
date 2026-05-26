"""
Custom template filters for the blog app.
"""
import nh3
from django import template
from django.utils.safestring import mark_safe

register = template.Library()

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
    'div':        {'class', 'id'},
    'table':      {'id', 'class'},
    'td':         {'class'},
    'th':         {'class'},
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
