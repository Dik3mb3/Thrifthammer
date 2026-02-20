"""URL configuration for the blog app."""

from django.urls import path

from . import views

app_name = 'blog'

urlpatterns = [
    # Blog index — paginated list of all published posts
    path('', views.PostListView.as_view(), name='post_list'),
    # Individual post detail
    path('<slug:slug>/', views.PostDetailView.as_view(), name='post_detail'),
]
