"""URL patterns for the UK product pages."""

from django.urls import path

from . import views_uk

app_name = 'products_uk'

urlpatterns = [
    path('', views_uk.product_list_uk, name='list'),
    path('search/autocomplete/', views_uk.search_autocomplete_uk, name='search_autocomplete'),
    path('<slug:slug>/', views_uk.product_detail_uk, name='detail'),
]
