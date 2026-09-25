"""
URL patterns for the UK product pages (/uk/products/...).

Routes to the same views as products/urls.py (US) -- product_list,
product_detail, search_autocomplete each resolve region from the request
path (request.path.startswith('/uk/')), so one implementation serves both
region prefixes correctly. There is no separate UK view/template set to
keep in sync; see views_uk.py's docstring history for why that used to
exist and what it was missing (book format tabs, Amazon UK links, ISBN
resolution, OneLink -- none of it was ever ported over).
"""

from django.urls import path

from . import views

app_name = 'products_uk'

urlpatterns = [
    path('', views.product_list, name='list'),
    path('search/autocomplete/', views.search_autocomplete, name='search_autocomplete'),
    path('<slug:slug>/', views.product_detail, name='detail'),
]
