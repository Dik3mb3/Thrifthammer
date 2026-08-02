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
    'home':                           {'priority': 1.0, 'changefreq': 'daily'},
    'products:list':                  {'priority': 0.9, 'changefreq': 'daily'},
    # ── Army Calculator — generic + per-faction pages ─────────────────────────
    'calculators:space_marines':      {'priority': 0.9, 'changefreq': 'weekly'},
    'calculators:ultramarines':       {'priority': 0.9, 'changefreq': 'weekly'},
    'calculators:blood_angels':       {'priority': 0.9, 'changefreq': 'weekly'},
    'calculators:dark_angels':        {'priority': 0.9, 'changefreq': 'weekly'},
    'calculators:black_templars':     {'priority': 0.9, 'changefreq': 'weekly'},
    'calculators:grey_knights':       {'priority': 0.9, 'changefreq': 'weekly'},
    'calculators:space_wolves':       {'priority': 0.9, 'changefreq': 'weekly'},
    'calculators:deathwatch':         {'priority': 0.9, 'changefreq': 'weekly'},
    'calculators:iron_hands':         {'priority': 0.9, 'changefreq': 'weekly'},
    'calculators:salamanders':        {'priority': 0.9, 'changefreq': 'weekly'},
    'calculators:imperial_fists':     {'priority': 0.9, 'changefreq': 'weekly'},
    'calculators:white_scars':        {'priority': 0.9, 'changefreq': 'weekly'},
    'calculators:raven_guard':        {'priority': 0.9, 'changefreq': 'weekly'},
    'calculators:drukhari':           {'priority': 0.9, 'changefreq': 'weekly'},
    # ── Phase 2 / 3 factions ──────────────────────────────────────────────────
    'calculators:emperors_children':   {'priority': 0.9, 'changefreq': 'weekly'},
    'calculators:chaos_space_marines': {'priority': 0.9, 'changefreq': 'weekly'},
    'calculators:death_guard':         {'priority': 0.9, 'changefreq': 'weekly'},
    'calculators:thousand_sons':       {'priority': 0.9, 'changefreq': 'weekly'},
    'calculators:world_eaters':        {'priority': 0.9, 'changefreq': 'weekly'},
    'calculators:necrons':             {'priority': 0.9, 'changefreq': 'weekly'},
    'calculators:orks':                {'priority': 0.9, 'changefreq': 'weekly'},
    'calculators:aeldari':             {'priority': 0.9, 'changefreq': 'weekly'},
    'calculators:tau_empire':          {'priority': 0.9, 'changefreq': 'weekly'},
    'calculators:tyranids':            {'priority': 0.9, 'changefreq': 'weekly'},
    'calculators:genestealer_cults':   {'priority': 0.9, 'changefreq': 'weekly'},
    'calculators:adeptus_mechanicus':  {'priority': 0.9, 'changefreq': 'weekly'},
    'calculators:astra_militarum':     {'priority': 0.9, 'changefreq': 'weekly'},
    'calculators:sisters_of_battle':   {'priority': 0.9, 'changefreq': 'weekly'},
    'calculators:custodes':            {'priority': 0.9, 'changefreq': 'weekly'},
    'calculators:imperial_knights':    {'priority': 0.9, 'changefreq': 'weekly'},
    'calculators:chaos_knights':       {'priority': 0.9, 'changefreq': 'weekly'},
    'calculators:leagues_of_votann':   {'priority': 0.9, 'changefreq': 'weekly'},
    # ── Other static pages ────────────────────────────────────────────────────
    'factions:index':                 {'priority': 0.8, 'changefreq': 'weekly'},
    'blog:post_list':                 {'priority': 0.7, 'changefreq': 'weekly'},
    'about':                          {'priority': 0.6, 'changefreq': 'monthly'},
    'faq':                            {'priority': 0.6, 'changefreq': 'monthly'},
    'privacy_policy':                 {'priority': 0.4, 'changefreq': 'monthly'},
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


class ProductSitemapUK(Sitemap):
    """
    Sitemap entry for every active product's UK page (/uk/products/<slug>/).

    Same product set as ProductSitemap (US) -- every active product has
    either a live UK retailer price or a msrp_gbp reference price, so
    none of these pages render blank.
    """

    priority = 0.8
    changefreq = 'daily'

    def items(self):
        """Return all active products ordered by name."""
        return Product.objects.filter(is_active=True).order_by('name')

    def location(self, obj):
        return f'/uk/products/{obj.slug}/'

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

    def lastmod(self, obj):
        """Signal to Google when the faction page content last changed."""
        return obj.updated_at


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
