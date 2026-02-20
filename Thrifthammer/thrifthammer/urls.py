from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import path, include
from django.views.generic import TemplateView

from products.views import about, home, privacy_policy
from thrifthammer.sitemaps import BlogPostSitemap, ProductSitemap, StaticViewSitemap

SITEMAPS = {
    'static': StaticViewSitemap,
    'products': ProductSitemap,
    'blog': BlogPostSitemap,
}

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home, name='home'),
    path('about/', about, name='about'),
    path('privacy-policy/', privacy_policy, name='privacy_policy'),
    path('sitemap.xml', sitemap, {'sitemaps': SITEMAPS}, name='django.contrib.sitemaps.views.sitemap'),
    path('robots.txt', TemplateView.as_view(template_name='robots.txt', content_type='text/plain')),
    path('accounts/', include('accounts.urls')),
    path('products/', include('products.urls')),
    path('prices/', include('prices.urls')),
    path('collection/', include('collections_app.urls')),
    path('army-calculator/', include('calculators.urls')),
    path('blog/', include('blog.urls')),
]
