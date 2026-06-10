from django.conf import settings
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import path, include
from django.views.generic import RedirectView, TemplateView

# Admin URL is configured via the DJANGO_ADMIN_URL environment variable so
# the real path never appears in source control. Defaults to 'admin/' locally.
_ADMIN_URL = getattr(settings, 'ADMIN_URL', 'admin/')

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
    # ── 301 redirects for old/deleted product URLs indexed by Google ──────────
    path(
        'products/space-marine-marneus-calgar/',
        RedirectView.as_view(url='/products/marneus-calgar/', permanent=True),
    ),
    path(
        'products/slaves-to-darkness-chaos-warriors-10/',
        RedirectView.as_view(
            url='/products/?category=age-of-sigmar&faction=slaves-to-darkness',
            permanent=True,
        ),
    ),
    path(
        'products/warhammer-40000-core-rules/',
        RedirectView.as_view(url='/products/?category=warhammer-40000', permanent=True),
    ),
    path(
        'products/warhammer-40000-starter-set/',
        RedirectView.as_view(url='/products/?category=warhammer-40000', permanent=True),
    ),
    path(
        'products/space-marine-judiciar/',
        RedirectView.as_view(
            url='/products/?category=warhammer-40000&faction=space-marines',
            permanent=True,
        ),
    ),
    path(
        'products/space-marine-land-raider/',
        RedirectView.as_view(
            url='/products/?category=warhammer-40000&faction=space-marines',
            permanent=True,
        ),
    ),
    path(
        'products/deathwatch-veteran-squad/',
        RedirectView.as_view(
            url='/products/?category=warhammer-40000&faction=deathwatch',
            permanent=True,
        ),
    ),
    path(
        'products/deathwatch-decimus-kill-team/',
        RedirectView.as_view(
            url='/products/?category=warhammer-40000&faction=deathwatch',
            permanent=True,
        ),
    ),
    # adeptus-custodes was accidentally created as a duplicate of the real
    # custodes faction (discovered 2026-05-24). Redirect to canonical page.
    path(
        'factions/adeptus-custodes/',
        RedirectView.as_view(url='/factions/custodes/', permanent=True),
    ),
    # ─────────────────────────────────────────────────────────────────────────
    path(_ADMIN_URL, admin.site.urls),
    path('', home, name='home'),
    path('about/', about, name='about'),
    path('privacy-policy/', privacy_policy, name='privacy_policy'),
    path('faq/', faq, name='faq'),
    path('newsletter/signup/', newsletter_signup, name='newsletter_signup'),
    path('sitemap.xml', sitemap, {'sitemaps': SITEMAPS}, name='django.contrib.sitemaps.views.sitemap'),
    path('robots.txt', TemplateView.as_view(template_name='robots.txt', content_type='text/plain')),
    path('accounts/', include('accounts.urls')),
    path('products/', include('products.urls')),
    path('uk/products/', include('products.urls_uk')),
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
