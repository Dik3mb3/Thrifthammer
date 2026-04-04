"""URL configuration for the calculators app."""

from django.urls import path
from django.views.generic import RedirectView

from . import views

app_name = 'calculators'

_calc = views.ArmyCalculatorView.as_view()

urlpatterns = [
    # ── Main calculator (Space Marines / generic) ─────────────────────────────
    path('', _calc, name='space_marines'),
    # Legacy redirect: old /army-calculator/space-marines/ URL → root
    path('space-marines/', RedirectView.as_view(url='/army-calculator/', permanent=True)),

    # ── Faction-specific calculator URLs (SEO-friendly) ───────────────────────
    # The third positional arg to path() passes URL kwargs into self.kwargs,
    # which ArmyCalculatorView.get_context_data reads via self.kwargs.get('faction').
    #
    # Phase-1 / existing factions
    path('ultramarines/',   _calc, {'faction': 'ultramarines'},   name='ultramarines'),
    path('blood-angels/',   _calc, {'faction': 'blood-angels'},   name='blood_angels'),
    path('dark-angels/',    _calc, {'faction': 'dark-angels'},    name='dark_angels'),
    path('black-templars/', _calc, {'faction': 'black-templars'}, name='black_templars'),
    path('grey-knights/',   _calc, {'faction': 'grey-knights'},   name='grey_knights'),
    path('space-wolves/',   _calc, {'faction': 'space-wolves'},   name='space_wolves'),
    path('deathwatch/',     _calc, {'faction': 'deathwatch'},     name='deathwatch'),
    # Phase-2 successor chapters (added 2026-04-04)
    path('iron-hands/',     _calc, {'faction': 'iron-hands'},     name='iron_hands'),
    path('salamanders/',    _calc, {'faction': 'salamanders'},    name='salamanders'),
    path('imperial-fists/', _calc, {'faction': 'imperial-fists'}, name='imperial_fists'),
    path('white-scars/',    _calc, {'faction': 'white-scars'},    name='white_scars'),
    path('raven-guard/',    _calc, {'faction': 'raven-guard'},    name='raven_guard'),

    # ── Functional endpoints ──────────────────────────────────────────────────
    path('save/',                     views.SaveArmyView.as_view(),      name='save_army'),
    path('share/<slug:slug>/',        views.ViewSavedArmyView.as_view(), name='view_army'),
    path('api/calculate/',            views.CalculateArmyCostView.as_view(), name='api_calculate'),
    path('my-armies/',                views.UserArmiesListView.as_view(), name='my_armies'),
    path('share/<slug:slug>/delete/', views.DeleteArmyView.as_view(),    name='delete_army'),
]
