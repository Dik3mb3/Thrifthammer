"""
Views for the ThriftHammer blog.

Provides:
- PostListView: paginated list of published posts, filterable by tag
- PostDetailView: full post with comments and SEO meta tags
"""

from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.generic import DetailView, ListView

from .forms import CommentForm
from .models import Comment, Post, Tag

POSTS_PER_PAGE = 12


class PostListView(ListView):
    """
    Paginated list of published blog posts.

    Supports tag filtering via clean path (/blog/tag/<slug>/) or legacy
    query string (?tag=<slug>, which 301-redirects to the clean path).
    Only posts whose status is published AND published_at is in the past
    are shown to site visitors.
    """

    model = Post
    template_name = 'blog/post_list.html'
    context_object_name = 'posts'
    paginate_by = POSTS_PER_PAGE

    def _get_tag_slug(self):
        """Return tag slug from URL path kwarg (preferred) or GET param (legacy)."""
        return self.kwargs.get('tag_slug') or self.request.GET.get('tag', '').strip()

    def get(self, request, *args, **kwargs):
        """301-redirect legacy ?tag= query-string URLs to clean /blog/tag/<slug>/."""
        legacy_tag = request.GET.get('tag', '').strip()
        if legacy_tag and 'tag_slug' not in self.kwargs:
            return redirect(reverse('blog:tag_list', kwargs={'tag_slug': legacy_tag}), permanent=True)
        return super().get(request, *args, **kwargs)

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

        tag_slug = self._get_tag_slug()
        if tag_slug:
            qs = qs.filter(tags__slug=tag_slug)

        return qs

    def get_context_data(self, **kwargs):
        """Add tag list, active tag, hero post, and grid posts to context."""
        context = super().get_context_data(**kwargs)
        tag_slug = self._get_tag_slug()
        active_tag = Tag.objects.filter(slug=tag_slug).first() if tag_slug else None

        context['all_tags'] = list(Tag.objects.filter(posts__isnull=False).distinct().order_by('name'))
        context['active_tag'] = active_tag
        # True when the tag is expressed as a URL path segment (not a query param)
        context['tag_in_path'] = bool(self.kwargs.get('tag_slug'))

        # Split posts into hero / latest sidebar / stream grid — page 1 only
        posts = list(context['posts'])
        page_obj = context['page_obj']
        if page_obj.number == 1 and posts:
            context['hero_post']    = posts[0]
            context['latest_posts'] = posts[1:6]   # up to 5 in sidebar
            context['stream_posts'] = posts[6:]    # remainder in 4-col grid
        else:
            context['hero_post']    = None
            context['latest_posts'] = []
            context['stream_posts'] = posts

        return context


class PostDetailView(DetailView):
    """
    Full blog post detail page with comments and SEO meta tags.

    Only published posts with a past published_at date are accessible.
    Drafts return 404 to avoid accidental preview leaks.

    GET:  renders the post with existing comments and an empty CommentForm.
    POST: saves a new comment (login required); redirects back to #comments
          to prevent duplicate submissions on refresh.
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
        """Add recent posts, related posts, comments, and comment form to context."""
        context = super().get_context_data(**kwargs)
        published_qs = Post.objects.filter(
            status=Post.STATUS_PUBLISHED,
            published_at__lte=timezone.now(),
        )

        # Recent posts for sidebar (exclude current)
        context['recent_posts'] = list(
            published_qs.exclude(pk=self.object.pk).order_by('-published_at')[:5]
        )

        # Related posts — by shared tag first, topped up with recent if needed
        post_tags = self.object.tags.all()
        related = list(
            published_qs
            .filter(tags__in=post_tags)
            .exclude(pk=self.object.pk)
            .distinct()
            .order_by('-published_at')[:3]
        )
        if len(related) < 3:
            exclude_pks = [self.object.pk] + [p.pk for p in related]
            extra = list(
                published_qs
                .exclude(pk__in=exclude_pks)
                .order_by('-published_at')[:3 - len(related)]
            )
            related += extra
        context['related_posts'] = related

        context['comments'] = self.object.comments.select_related('author').all()
        context['comment_form'] = CommentForm()
        return context

    def post(self, request, *args, **kwargs):
        """Handle comment submission — login required."""
        if not request.user.is_authenticated:
            return redirect(f'{request.build_absolute_uri("/accounts/login/")}?next={request.path}')

        post_obj = self.get_object()
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.post = post_obj
            comment.author = request.user
            comment.save()
            return redirect(post_obj.get_absolute_url() + '#comments')

        # If form invalid, re-render page with errors
        self.object = post_obj
        context = self.get_context_data()
        context['comment_form'] = form  # replace with the invalid form to show errors
        return self.render_to_response(context)
