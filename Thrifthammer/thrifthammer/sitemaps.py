"""
Sitemap configuration for ThriftHammer.

Registers static pages, all active products, live faction pages,
and published blog posts/tags for search engine crawling.

Priority guide:
  1.0  Home page
  0.9  Primary destination pages (Browse, Army Calculator)
  0.8  Individual product & faction pages, Faction index
  0.7  Blog posts, About
  0.5  Blog tag pages
  0.4  Privacy Policy

changefreq guide:
  daily   — home, browse, products (prices update constantly)
  weekly  — faction pages, blog index, calculator, blog tags
  monthly — individual blog posts, about, privacy policy
"""

from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from blog.models import Post, Tag
from products.models import Faction, Product


# Per-URL config for static named-view pages.
# To add a new static page: append its named URL here.
# When www support is added, update robots.txt with a second Sitemap: line.
_STATIC_PAGE_CONFIG = {
    'home':                      {'priority': 1.0, 'changefreq': 'daily'},
    'products:list':             {'priority': 0.9, 'changefreq': 'daily'},
    'calculators:space_marines': {'priority': 0.9, 'changefreq': 'weekly'},
    'factions:index':            {'priority': 0.8, 'changefreq': 'weekly'},
    'blog:post_list':            {'priority': 0.7, 'changefreq': 'weekly'},
    'about':                     {'priority': 0.6, 'changefreq': 'monthly'},
    'faq':                       {'priority': 0.6, 'changefreq': 'monthly'},
    'privacy_policy':            {'priority': 0.4, 'changefreq': 'monthly'},
}


class StaticViewSitemap(Sitemap):
    """
    Sitemap for static / named-URL pages.

    Priority and changefreq are configured per-URL in _STATIC_PAGE_CONFIG
    so each page gets the correct crawl hint rather than a blanket value.
    """

    def items(self):
        """Return named URL patterns in priority order."""
        return list(_STATIC_PAGE_CONFIG.keys())

    def location(self, item):
        """Resolve the named URL to its path."""
        return reverse(item)

    def priority(self, item):
        """Return per-page priority hint for search engines."""
        return _STATIC_PAGE_CONFIG[item]['priority']

    def changefreq(self, item):
        """Return per-page crawl frequency hint."""
        return _STATIC_PAGE_CONFIG[item]['changefreq']


class ProductSitemap(Sitemap):
    """
    Sitemap entry for every active Warhammer product.

    High priority (0.8) and daily changefreq because prices update
    continuously — Google should re-crawl these often.
    """

    priority = 0.8
    changefreq = 'daily'

    def items(self):
        """Return all active products ordered by name."""
        return Product.objects.filter(is_active=True).order_by('name')

    def location(self, obj):
        return f'/products/{obj.slug}/'

    def lastmod(self, obj):
        """Use the product's most recent update timestamp."""
        return getattr(obj, 'updated_at', None) or getattr(obj, 'created_at', None)


class FactionSitemap(Sitemap):
    """
    Sitemap entry for each live faction landing page.

    Only factions with a synopsis (i.e. published pages) are included.
    Priority matches product pages — these are primary content destinations.
    """

    priority = 0.8
    changefreq = 'weekly'

    def items(self):
        """Return factions that have a published faction page."""
        return Faction.objects.exclude(synopsis='').order_by('slug')

    def location(self, obj):
        return f'/factions/{obj.slug}/'


class BlogPostSitemap(Sitemap):
    """Sitemap entry for every published blog post."""

    priority = 0.7
    changefreq = 'monthly'

    def items(self):
        """Return all published blog posts newest-first."""
        return Post.objects.filter(status='published').order_by('-published_at')

    def location(self, obj):
        return obj.get_absolute_url()

    def lastmod(self, obj):
        """Use the post's publication date as the last-modified signal."""
        return obj.published_at


class BlogTagSitemap(Sitemap):
    """Sitemap entry for each blog tag that has at least one published post."""

    priority = 0.5
    changefreq = 'weekly'

    def items(self):
        """Return tags with at least one published post."""
        return Tag.objects.filter(posts__status='published').distinct().order_by('slug')

    def location(self, obj):
        return f'/blog/tag/{obj.slug}/'
