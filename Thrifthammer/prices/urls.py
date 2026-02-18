from django.urls import path

from . import views

app_name = 'prices'

urlpatterns = [
    path('api/history/<slug:product_slug>/', views.price_history_api, name='history_api'),
]
