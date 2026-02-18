from django.urls import path

from . import views

app_name = 'products'

urlpatterns = [
    path('', views.product_list, name='list'),
    path('<slug:slug>/', views.product_detail, name='detail'),
    path('<slug:slug>/watchlist/', views.toggle_watchlist, name='toggle_watchlist'),
]
