"""URL configuration for the calculators app."""

from django.urls import path
from . import views

app_name = 'calculators'

_calc = views.ArmyCalculatorView.as_view()

urlpatterns = [
    # ── Main calculator (Space Marines / generic) ─────────────────────────────
    path('', _calc, name='space_marines'),
    path('space-marines/', _calc, {'faction': 'space-marines'}, name='space_marines_faction'),

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

    # Phase-2/3 factions (added 2026-04-08)
    path('emperors-children/',    _calc, {'faction': 'emperors-children'},    name='emperors_children'),
    path('chaos-space-marines/',  _calc, {'faction': 'chaos-space-marines'},  name='chaos_space_marines'),
    path('death-guard/',          _calc, {'faction': 'death-guard'},          name='death_guard'),
    path('thousand-sons/',        _calc, {'faction': 'thousand-sons'},        name='thousand_sons'),
    path('world-eaters/',         _calc, {'faction': 'world-eaters'},         name='world_eaters'),
    path('necrons/',              _calc, {'faction': 'necrons'},              name='necrons'),
    path('orks/',                 _calc, {'faction': 'orks'},                 name='orks'),
    path('aeldari/',              _calc, {'faction': 'aeldari'},              name='aeldari'),
    path('tau-empire/',           _calc, {'faction': 'tau-empire'},           name='tau_empire'),
    path('tyranids/',             _calc, {'faction': 'tyranids'},             name='tyranids'),
    path('genestealer-cults/',    _calc, {'faction': 'genestealer-cults'},    name='genestealer_cults'),
    path('adeptus-mechanicus/',   _calc, {'faction': 'adeptus-mechanicus'},   name='adeptus_mechanicus'),
    path('astra-militarum/',      _calc, {'faction': 'astra-militarum'},      name='astra_militarum'),
    path('sisters-of-battle/',    _calc, {'faction': 'sisters-of-battle'},    name='sisters_of_battle'),
    path('custodes/',             _calc, {'faction': 'custodes'},             name='custodes'),
    path('imperial-knights/',     _calc, {'faction': 'imperial-knights'},     name='imperial_knights'),
    path('chaos-knights/',        _calc, {'faction': 'chaos-knights'},        name='chaos_knights'),
    path('leagues-of-votann/',    _calc, {'faction': 'leagues-of-votann'},    name='leagues_of_votann'),
    path('drukhari/',             _calc, {'faction': 'drukhari'},             name='drukhari'),

    # ── Functional endpoints ──────────────────────────────────────────────────
    path('save/',                     views.SaveArmyView.as_view(),      name='save_army'),
    path('share/<slug:slug>/',        views.ViewSavedArmyView.as_view(), name='view_army'),
    path('api/calculate/',            views.CalculateArmyCostView.as_view(), name='api_calculate'),
    path('my-armies/',                views.UserArmiesListView.as_view(), name='my_armies'),
    path('share/<slug:slug>/delete/', views.DeleteArmyView.as_view(),    name='delete_army'),
]
