"""URL configuration for the products app."""

from django.urls import path
from django.views.generic import RedirectView

from . import views

app_name = 'products'

# 301 redirects for old warhammer-40000 product slugs → warhammer-40k
_40k_redirects = [
    'chapter-approved-leviathan',
    'core-rules',
    'dice-set',
    'measuring-tape',
    'starter-set',
]

urlpatterns = [
    # Permanent redirects: warhammer-40000-* → warhammer-40k-*
    *[
        path(
            f'warhammer-40000-{suffix}/',
            RedirectView.as_view(url=f'/products/warhammer-40k-{suffix}/', permanent=True),
        )
        for suffix in _40k_redirects
    ],

    # Product catalog list with search/filter/sort/pagination
    path('', views.product_list, name='list'),
    # JSON autocomplete endpoint for the search bar
    path('search/autocomplete/', views.search_autocomplete, name='search_autocomplete'),
    # Product detail page — must come after any other fixed paths to avoid slug conflicts
    path('<slug:slug>/', views.product_detail, name='detail'),
    # Toggle watchlist membership (POST only, login required)
    path('<slug:slug>/watchlist/', views.toggle_watchlist, name='toggle_watchlist'),
    # Report a data issue on a product page (GET/POST, no login required)
    path('<slug:slug>/report/', views.report_issue, name='report_issue'),
    # Newsletter unsubscribe — token-based, no login required
    path('newsletter/unsubscribe/<uuid:token>/', views.newsletter_unsubscribe, name='newsletter_unsubscribe'),
    # Newsletter confirmation — new homepage signups confirm their email via this link
    path('newsletter/confirm/<uuid:token>/', views.newsletter_confirm, name='newsletter_confirm'),
]
