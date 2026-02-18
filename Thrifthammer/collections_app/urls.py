from django.urls import path

from . import views

app_name = 'collections'

urlpatterns = [
    path('', views.my_collection, name='my_collection'),
    path('add/<slug:slug>/', views.add_to_collection, name='add'),
    path('remove/<slug:slug>/', views.remove_from_collection, name='remove'),
]
