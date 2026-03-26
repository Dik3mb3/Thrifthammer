"""URL configuration for the products app."""

from django.urls import path

from . import views

app_name = 'products'

urlpatterns = [
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
]
