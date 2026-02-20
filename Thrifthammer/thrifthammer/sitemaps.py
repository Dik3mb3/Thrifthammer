"""
Sitemap configuration for ThriftHammer.

Registers static pages, all active products, and published blog posts
for search engine crawling.
"""

from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from blog.models import Post
from products.models import Product


class StaticViewSitemap(Sitemap):
    """Sitemap for static pages (home, about, browse, calculator, blog index)."""

    priority = 0.8
    changefreq = 'weekly'

    def items(self):
        """Return list of named URL patterns to include."""
        return [
            'home',
            'about',
            'privacy_policy',
            'products:list',
            'calculators:space_marines',
            'blog:post_list',
        ]

    def location(self, item):
        """Resolve named URL to its path."""
        return reverse(item)


class ProductSitemap(Sitemap):
    """Sitemap entry for every active Warhammer product."""

    priority = 0.6
    changefreq = 'daily'

    def items(self):
        """Return all active products ordered by name."""
        return Product.objects.filter(is_active=True).order_by('name')

    def location(self, obj):
        """Build the product detail URL."""
        return f'/products/{obj.slug}/'

    def lastmod(self, obj):
        """Use the product's updated_at timestamp if available."""
        return getattr(obj, 'updated_at', None) or getattr(obj, 'created_at', None)


class BlogPostSitemap(Sitemap):
    """Sitemap entry for every published blog post."""

    priority = 0.7
    changefreq = 'monthly'

    def items(self):
        """Return all published blog posts ordered by publication date."""
        return Post.objects.filter(status='published').order_by('-published_at')

    def location(self, obj):
        """Use the post's own get_absolute_url method."""
        return obj.get_absolute_url()

    def lastmod(self, obj):
        """Use the post's publication date as last-modified."""
        return obj.published_at
