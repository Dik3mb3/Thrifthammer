"""URL configuration for the calculators app."""

from django.urls import path

from . import views

app_name = 'calculators'

urlpatterns = [
    # Main calculator page
    path('space-marines/', views.ArmyCalculatorView.as_view(), name='space_marines'),
    # AJAX: save a named army
    path('save/', views.SaveArmyView.as_view(), name='save_army'),
    # Shareable army detail page
    path('share/<slug:slug>/', views.ViewSavedArmyView.as_view(), name='view_army'),
    # AJAX: calculate cost totals from a unit list
    path('api/calculate/', views.CalculateArmyCostView.as_view(), name='api_calculate'),
    # User dashboard: list of saved armies
    path('my-armies/', views.UserArmiesListView.as_view(), name='my_armies'),
]
