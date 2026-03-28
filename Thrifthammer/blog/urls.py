"""URL configuration for the blog app."""

from django.urls import path

from . import views

app_name = 'blog'

urlpatterns = [
    # Blog index — paginated list of all published posts
    path('', views.PostListView.as_view(), name='post_list'),
    # Tag filtered list — clean path for SEO (/blog/tag/space-marines/)
    path('tag/<slug:tag_slug>/', views.PostListView.as_view(), name='tag_list'),
    # Individual post detail
    path('<slug:slug>/', views.PostDetailView.as_view(), name='post_detail'),
]
