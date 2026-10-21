"""Tests for the blog app: who can open a post detail page."""
import datetime

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from .models import Post, Tag

User = get_user_model()

_TEST_STORAGES = {
    'staticfiles': {'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage'},
}


def _make_post(slug, status=Post.STATUS_PUBLISHED, published_at=None):
    """Create and return a minimal Post for testing."""
    return Post.objects.create(
        title=f'Post {slug}',
        slug=slug,
        excerpt='Excerpt.',
        body='<p>Body.</p>',
        status=status,
        published_at=published_at,
        author='ThriftHammer',
    )


@override_settings(STORAGES=_TEST_STORAGES)
class PostDetailVisibilityTest(TestCase):
    """Drafts and scheduled posts are hidden from visitors but open to staff."""

    def setUp(self):
        """Create a live post, a draft, a scheduled post and three kinds of user."""
        past = timezone.now() - datetime.timedelta(days=1)
        future = timezone.now() + datetime.timedelta(days=1)
        self.live = _make_post('live-post', published_at=past)
        self.draft = _make_post('draft-post', status=Post.STATUS_DRAFT)
        self.scheduled = _make_post('scheduled-post', published_at=future)
        self.member = User.objects.create_user('member', password='testpass123')
        self.staff = User.objects.create_user('editor', password='testpass123', is_staff=True)

    def _get(self, post):
        """Fetch the detail page for a post."""
        return self.client.get(reverse('blog:post_detail', kwargs={'slug': post.slug}))

    def test_visitor_sees_live_post_only(self):
        """Anonymous visitors get the live post and 404 for the draft and scheduled post."""
        self.assertEqual(self._get(self.live).status_code, 200)
        self.assertEqual(self._get(self.draft).status_code, 404)
        self.assertEqual(self._get(self.scheduled).status_code, 404)

    def test_regular_member_cannot_open_draft(self):
        """A logged-in non-staff user is treated like any visitor."""
        self.client.force_login(self.member)
        self.assertEqual(self._get(self.draft).status_code, 404)
        self.assertEqual(self._get(self.scheduled).status_code, 404)

    def test_staff_can_preview_draft_and_scheduled(self):
        """Staff can open drafts and scheduled posts to proofread them."""
        self.client.force_login(self.staff)
        self.assertEqual(self._get(self.draft).status_code, 200)
        self.assertEqual(self._get(self.scheduled).status_code, 200)
        self.assertEqual(self._get(self.live).status_code, 200)

    def test_draft_never_listed_publicly(self):
        """The draft does not appear in the public blog list, even for staff."""
        self.client.force_login(self.staff)
        response = self.client.get(reverse('blog:post_list'))
        self.assertNotContains(response, 'Post draft-post')


@override_settings(STORAGES=_TEST_STORAGES)
class CheatSheetPrintButtonTest(TestCase):
    """The Download PDF button script is attached to both keyword cheat sheet posts only."""

    def _page(self, slug):
        """Return the rendered detail page for a published post with this slug."""
        _make_post(slug, published_at=timezone.now() - datetime.timedelta(days=1))
        return self.client.get(reverse('blog:post_detail', kwargs={'slug': slug})).content.decode()

    def test_both_cheat_sheets_get_exactly_one_print_handler(self):
        """The 40K and Age of Sigmar cheat sheet pages each carry one window.print() handler."""
        for slug in ('warhammer-40k-11th-edition-core-keywords-cheat-sheet',
                     'age-of-sigmar-4th-edition-core-keywords-cheat-sheet'):
            self.assertEqual(self._page(slug).count('window.print()'), 1, slug)

    def test_other_posts_have_no_print_handler(self):
        """An ordinary post does not load the cheat sheet print script."""
        self.assertEqual(self._page('an-ordinary-post').count('window.print()'), 0)


@override_settings(STORAGES=_TEST_STORAGES)
class TagPageTest(TestCase):
    """Tag pages only exist for tags that have at least one published post."""

    def setUp(self):
        """Create a tag with a live post, a tag with only a draft, and an unused tag."""
        past = timezone.now() - datetime.timedelta(days=1)
        self.live_tag = Tag.objects.create(name='Live Tag')
        self.draft_tag = Tag.objects.create(name='Draft Tag')
        self.unused_tag = Tag.objects.create(name='Unused Tag')
        _make_post('tagged-live', published_at=past).tags.add(self.live_tag)
        _make_post('tagged-draft', status=Post.STATUS_DRAFT).tags.add(self.draft_tag)

    def _get(self, slug):
        """Fetch a tag page."""
        return self.client.get(reverse('blog:tag_list', kwargs={'tag_slug': slug}))

    def test_tag_with_published_post_is_ok(self):
        """A tag with a published post renders normally."""
        self.assertEqual(self._get(self.live_tag.slug).status_code, 200)

    def test_empty_tags_and_unknown_slugs_are_404(self):
        """Unused tags, draft-only tags and made-up slugs return a real 404."""
        for slug in (self.unused_tag.slug, self.draft_tag.slug, 'does-not-exist'):
            self.assertEqual(self._get(slug).status_code, 404, slug)
