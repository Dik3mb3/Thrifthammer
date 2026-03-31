from django.conf import settings
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import path, include
from django.views.generic import TemplateView

from products.views import about, faq, home, newsletter_signup, privacy_policy
from thrifthammer.sitemaps import BlogPostSitemap, BlogTagSitemap, FactionSitemap, ProductSitemap, StaticViewSitemap

SITEMAPS = {
    'static': StaticViewSitemap,
    'products': ProductSitemap,
    'blog': BlogPostSitemap,
    'blog_tags': BlogTagSitemap,
    'factions': FactionSitemap,
}

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home, name='home'),
    path('about/', about, name='about'),
    path('privacy-policy/', privacy_policy, name='privacy_policy'),
    path('faq/', faq, name='faq'),
    path('newsletter/signup/', newsletter_signup, name='newsletter_signup'),
    path('sitemap.xml', sitemap, {'sitemaps': SITEMAPS}, name='django.contrib.sitemaps.views.sitemap'),
    path('robots.txt', TemplateView.as_view(template_name='robots.txt', content_type='text/plain')),
    path('accounts/', include('accounts.urls')),
    path('products/', include('products.urls')),
    path('prices/', include('prices.urls')),
    path('collection/', include('collections_app.urls')),
    path('army-calculator/', include('calculators.urls')),
    path('blog/', include('blog.urls')),
    path('factions/', include('factions.urls')),
]

if settings.DEBUG:
    try:
        import debug_toolbar  # noqa: F401
        urlpatterns += [path('__debug__/', include('debug_toolbar.urls'))]
    except ImportError:
        pass
