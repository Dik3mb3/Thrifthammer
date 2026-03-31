"""URL configuration for the calculators app."""

from django.urls import path
from django.views.generic import RedirectView

from . import views

app_name = 'calculators'

urlpatterns = [
    # Main calculator page — lives at /army-calculator/
    path('', views.ArmyCalculatorView.as_view(), name='space_marines'),
    # Legacy redirect: old /army-calculator/space-marines/ URL → new root URL
    path('space-marines/', RedirectView.as_view(url='/army-calculator/', permanent=True)),
    # AJAX: save a named army
    path('save/', views.SaveArmyView.as_view(), name='save_army'),
    # Shareable army detail page
    path('share/<slug:slug>/', views.ViewSavedArmyView.as_view(), name='view_army'),
    # AJAX: calculate cost totals from a unit list
    path('api/calculate/', views.CalculateArmyCostView.as_view(), name='api_calculate'),
    # User dashboard: list of saved armies
    path('my-armies/', views.UserArmiesListView.as_view(), name='my_armies'),
    # Delete a saved army (POST only, owner only)
    path('share/<slug:slug>/delete/', views.DeleteArmyView.as_view(), name='delete_army'),
]
