"""URL configuration for faction landing pages."""

from django.urls import path

from . import views

app_name = 'factions'

urlpatterns = [
    path('', views.FactionIndexView.as_view(), name='index'),
    path('<slug:slug>/', views.FactionDetailView.as_view(), name='detail'),
]
