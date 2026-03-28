"""URL configuration for faction landing pages."""

from django.urls import path

from . import views

app_name = 'factions'

urlpatterns = [
    # Faction landing page — /factions/<slug>/
    path('<slug:slug>/', views.FactionDetailView.as_view(), name='detail'),
]
