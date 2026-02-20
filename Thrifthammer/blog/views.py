"""
Views for the ThriftHammer blog.

Provides:
- PostListView: paginated list of published posts, filterable by tag
- PostDetailView: full post with SEO meta tags
"""

from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.views.generic import DetailView, ListView

from .models import Post, Tag

POSTS_PER_PAGE = 12


class PostListView(ListView):
    """
    Paginated list of published blog posts.

    Supports optional tag filtering via ?tag=<slug>.
    Only posts whose status is published AND published_at is in the past
    are shown to site visitors.
    """

    model = Post
    template_name = 'blog/post_list.html'
    context_object_name = 'posts'
    paginate_by = POSTS_PER_PAGE

    def get_queryset(self):
        """Return published posts; filter by tag if provided."""
        qs = (
            Post.objects
            .filter(
                status=Post.STATUS_PUBLISHED,
                published_at__lte=timezone.now(),
            )
            .prefetch_related('tags')
            .order_by('-published_at')
        )

        tag_slug = self.request.GET.get('tag', '').strip()
        if tag_slug:
            qs = qs.filter(tags__slug=tag_slug)

        return qs

    def get_context_data(self, **kwargs):
        """Add tag list and active tag to context."""
        context = super().get_context_data(**kwargs)
        tag_slug = self.request.GET.get('tag', '').strip()
        active_tag = None
        if tag_slug:
            active_tag = Tag.objects.filter(slug=tag_slug).first()

        context['all_tags'] = list(Tag.objects.filter(posts__isnull=False).distinct().order_by('name'))
        context['active_tag'] = active_tag
        return context


class PostDetailView(DetailView):
    """
    Full blog post detail page with SEO meta tags.

    Only published posts with a past published_at date are accessible.
    Drafts return 404 to avoid accidental preview leaks.
    """

    model = Post
    template_name = 'blog/post_detail.html'
    context_object_name = 'post'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'

    def get_queryset(self):
        """Only allow access to published posts."""
        return Post.objects.filter(
            status=Post.STATUS_PUBLISHED,
            published_at__lte=timezone.now(),
        ).prefetch_related('tags')

    def get_context_data(self, **kwargs):
        """Add recent posts sidebar to context."""
        context = super().get_context_data(**kwargs)
        context['recent_posts'] = list(
            Post.objects
            .filter(
                status=Post.STATUS_PUBLISHED,
                published_at__lte=timezone.now(),
            )
            .exclude(pk=self.object.pk)
            .order_by('-published_at')[:5]
        )
        return context
