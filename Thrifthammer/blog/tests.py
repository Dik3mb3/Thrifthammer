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


@override_settings(STORAGES=_TEST_STORAGES)
class BlogSitemapLastmodTest(TestCase):
    """Only the kept-up-to-date Black Friday post reports its last edit; every other post keeps its publication date."""

    def _lastmod(self, xml, slug):
        """The lastmod line of one post inside the sitemap."""
        return xml.split(f'/blog/{slug}/')[1].split('</url>')[0]

    def test_black_friday_post_follows_updated_at_other_posts_keep_published_at(self):
        """An edited Black Friday post shows updated_at; an ordinary edited post still shows published_at; drafts stay out."""
        published = timezone.now() - datetime.timedelta(days=30)
        edited = timezone.now() - datetime.timedelta(days=2)
        live = _make_post('warhammer-black-friday-deals', published_at=published)
        ordinary = _make_post('ordinary-post', published_at=published)
        # auto_now would overwrite updated_at on save, so set a known edit date directly.
        Post.objects.filter(pk__in=[live.pk, ordinary.pk]).update(updated_at=edited)
        _make_post('hidden-draft', status=Post.STATUS_DRAFT)

        xml = self.client.get('/sitemap.xml').content.decode()
        self.assertIn(f'<lastmod>{edited:%Y-%m-%d}</lastmod>', self._lastmod(xml, 'warhammer-black-friday-deals'))
        self.assertIn(f'<lastmod>{published:%Y-%m-%d}</lastmod>', self._lastmod(xml, 'ordinary-post'))
        self.assertNotIn(f'{edited:%Y-%m-%d}', self._lastmod(xml, 'ordinary-post'))
        self.assertNotIn('hidden-draft', xml)

    def test_miniature_wargaming_black_friday_post_follows_updated_at(self):
        """The sister Black Friday post is also kept up to date, so its lastmod follows its last edit."""
        published = timezone.now() - datetime.timedelta(days=30)
        edited = timezone.now() - datetime.timedelta(days=2)
        post = _make_post('miniature-wargaming-black-friday-deals', published_at=published)
        Post.objects.filter(pk=post.pk).update(updated_at=edited)

        xml = self.client.get('/sitemap.xml').content.decode()
        self.assertIn(f'<lastmod>{edited:%Y-%m-%d}</lastmod>', self._lastmod(xml, 'miniature-wargaming-black-friday-deals'))


class LiveBestPriceTest(TestCase):
    """A <span data-th-best="slug"> in a post shows the product's current cheapest price and follows the scrapers."""

    def setUp(self):
        """One product with a single eBay price."""
        from decimal import Decimal

        from prices.models import CurrentPrice
        from products.models import Category, Product, Retailer

        category = Category.objects.create(name='Warhammer 40,000', slug='warhammer-40000')
        self.product = Product.objects.create(
            name='Test Battleforce', slug='test-battleforce', gw_sku='TB-1', msrp=Decimal('255'), category=category, is_active=True,
        )
        self.ebay = Retailer.objects.create(name='eBay', slug='ebay', website='https://ebay.com')
        self.amazon = Retailer.objects.create(name='Amazon', slug='amazon', website='https://amazon.com')
        self.mm = Retailer.objects.create(name='Miniature Market', slug='miniature-market', website='https://miniaturemarket.com')
        CurrentPrice.objects.create(product=self.product, retailer=self.ebay, price=Decimal('195.10'), currency='USD',
                                    url='https://www.ebay.com/itm/1', in_stock=True)
        self.body = '<ul><li>Best: <span class="th-best" data-th-best="test-battleforce">fallback text</span></li></ul>'

    def _render(self):
        """Run a post body through the same two filters the template uses."""
        from django.core.cache import cache

        from blog.templatetags.blog_extras import live_prices, sanitize_html

        cache.clear()
        return live_prices(sanitize_html(self.body))

    def test_shows_cheapest_retailer_and_price_with_a_sponsored_link(self):
        """The fallback text is replaced by 'eBay $195.10' linking to the listing, marked sponsored."""
        out = self._render()
        self.assertIn('eBay <span class="bf-price">$195.10</span>', out)
        self.assertNotIn('fallback text', out)
        self.assertIn('href="https://www.ebay.com/itm/1"', out)
        self.assertIn('rel="noopener noreferrer sponsored"', out)

    def test_follows_a_new_cheaper_price_and_a_non_sponsored_retailer(self):
        """When a scraper records a cheaper price at another retailer, the blog shows that retailer."""
        from decimal import Decimal

        from prices.models import CurrentPrice

        CurrentPrice.objects.create(product=self.product, retailer=self.mm, price=Decimal('180.00'), currency='USD',
                                    url='https://www.miniaturemarket.com/x', in_stock=True)
        out = self._render()
        self.assertIn('Miniature Market <span class="bf-price">$180</span>', out)
        self.assertNotIn('sponsored', out)

    def test_unknown_product_keeps_the_fallback_text(self):
        """A slug that matches no active product leaves the written text alone."""
        self.body = self.body.replace('test-battleforce', 'no-such-product')
        self.assertIn('fallback text', self._render())


class BlogThumbnailTest(TestCase):
    """A <span data-th-thumb="slug"> in a post shows that product's real picture, and nothing when there is none."""

    def setUp(self):
        """One product with an image, one without."""
        from decimal import Decimal

        from products.models import Category, Product

        category = Category.objects.create(name='Warhammer 40,000', slug='warhammer-40000')
        self.with_image = Product.objects.create(
            name='Tom & Jerry Battleforce', slug='with-image', gw_sku='TI-1', msrp=Decimal('255'), category=category, is_active=True,
            image_url='https://www.warhammer.com/app/resources/catalog/product/920x950/99120101001_Box01.jpg',
        )
        self.no_image = Product.objects.create(
            name='No Picture Box', slug='no-image', gw_sku='TI-2', msrp=Decimal('100'), category=category, is_active=True,
        )

    def _render(self, body):
        """Run a post body through the same two filters the template uses."""
        from blog.templatetags.blog_extras import live_prices, sanitize_html

        return live_prices(sanitize_html(body))

    def test_thumbnail_is_a_small_webp_picture_with_size_and_alt(self):
        """A WebP source via the site's resizer plus the original image, with width, height, lazy loading and escaped alt text."""
        out = self._render('<p><span class="th-thumb" data-th-thumb="with-image"></span><strong>Box</strong></p>')
        self.assertIn('<picture><source srcset="https://wsrv.nl/?url=https%3A%2F%2Fwww.warhammer.com', out)
        self.assertIn('output=webp&amp;w=144&amp;h=144&amp;fit=cover" type="image/webp">', out)
        self.assertIn('alt="Tom &amp; Jerry Battleforce"', out)
        self.assertIn('width="72" height="72" loading="lazy"', out)
        self.assertIn('src="https://www.warhammer.com/app/resources/catalog/product/920x950/99120101001_Box01.jpg"', out)
        self.assertNotIn('data-th-thumb', out)

    def test_no_image_unknown_or_inactive_product_shows_nothing(self):
        """Never a placeholder: the marker simply disappears."""
        from products.models import Product

        Product.objects.filter(pk=self.with_image.pk).update(is_active=False)
        for slug in ('no-image', 'no-such-product', 'with-image'):
            out = self._render(f'<p><span data-th-thumb="{slug}"></span>Box</p>')
            self.assertEqual(out, '<p>Box</p>', slug)

    def test_host_that_blocks_the_resizer_gets_the_plain_image(self):
        """iwata-airbrush.com 404s through the resizer, so it is loaded directly like on the product cards."""
        from products.models import Product

        Product.objects.filter(pk=self.with_image.pk).update(image_url='https://iwata-airbrush.com/media/x.jpg')
        out = self._render('<p><span data-th-thumb="with-image"></span></p>')
        self.assertNotIn('wsrv.nl', out)
        self.assertIn('<img src="https://iwata-airbrush.com/media/x.jpg"', out)


@override_settings(STORAGES=_TEST_STORAGES)
class BlogGalleryTest(TestCase):
    """The swipe gallery markup survives sanitising, and its script loads only on posts that contain one."""

    GALLERY = (
        '<div class="th-gallery" role="region" aria-label="Store sale flyers" tabindex="0">'
        '<div><img src="/static/images/blog/flyer-1.webp" alt="Flyer one" width="640" height="800" loading="lazy"></div>'
        '<div><img src="/static/images/blog/flyer-2.webp" alt="Flyer two" width="640" height="800" loading="lazy"></div>'
        '</div><script>alert(1)</script>'
    )

    def test_gallery_markup_survives_and_scripts_do_not(self):
        """Region role, label, keyboard focus and the image attributes stay; an injected script is removed."""
        from blog.templatetags.blog_extras import sanitize_html

        out = sanitize_html(self.GALLERY)
        for expected in ('class="th-gallery"', 'role="region"', 'aria-label="Store sale flyers"', 'tabindex="0"',
                         'width="640" height="800"', 'loading="lazy"', 'alt="Flyer two"'):
            self.assertIn(expected, out)
        self.assertNotIn('<script', out)

    def test_script_only_on_posts_with_a_gallery(self):
        """A post with a gallery loads the arrows script; an ordinary post does not."""
        with_gallery = _make_post('with-gallery', published_at=timezone.now())
        Post.objects.filter(pk=with_gallery.pk).update(body=self.GALLERY)
        _make_post('without-gallery', published_at=timezone.now())

        self.assertContains(self.client.get('/blog/with-gallery/'), 'th-gallery-btn')
        self.assertNotContains(self.client.get('/blog/without-gallery/'), 'th-gallery-btn')


class BlogOffBadgeTest(TestCase):
    """<span data-th-off="slug"> shows the live percent off MSRP, and disappears when there is no real discount."""

    def setUp(self):
        """A 200 dollar product with one eBay price."""
        from decimal import Decimal

        from prices.models import CurrentPrice
        from products.models import Category, Product, Retailer

        category = Category.objects.create(name='Warhammer 40,000', slug='warhammer-40000')
        self.product = Product.objects.create(name='Box', slug='off-box', gw_sku='OF-1', msrp=Decimal('200'), category=category, is_active=True)
        ebay = Retailer.objects.create(name='eBay', slug='ebay', website='https://ebay.com')
        self.row = CurrentPrice.objects.create(product=self.product, retailer=ebay, price=Decimal('150.00'), currency='USD',
                                               url='https://www.ebay.com/itm/9', in_stock=True)

    def _render(self):
        """Run a post body through the same two filters the template uses."""
        from django.core.cache import cache

        from blog.templatetags.blog_extras import live_prices, sanitize_html

        cache.clear()
        return live_prices(sanitize_html('<h4>Box <span class="x" data-th-off="off-box"></span></h4>'))

    def test_badge_follows_the_live_price(self):
        """25 percent off at 150 on 200; a cheaper price moves the badge; at MSRP or above the badge is gone."""
        from decimal import Decimal

        self.assertIn('<span class="bf-badge">25% off</span>', self._render())
        type(self.row).objects.filter(pk=self.row.pk).update(price=Decimal('120.00'))
        self.assertIn('40% off', self._render())
        type(self.row).objects.filter(pk=self.row.pk).update(price=Decimal('200.00'))
        self.assertNotIn('off', self._render().replace('data-th-off', ''))


@override_settings(STORAGES=_TEST_STORAGES)
class BlogUpdatedLineTest(TestCase):
    """The Black Friday post shows 'Updated <date>' once edited on a later day; no other post ever shows it."""

    def test_updated_date_only_on_the_black_friday_post(self):
        """Black Friday: same-day shows nothing, a later edit shows the real date; an ordinary post edited later shows nothing."""
        published = timezone.now() - datetime.timedelta(days=5)
        edited = timezone.now() - datetime.timedelta(days=1)
        live = _make_post('warhammer-black-friday-deals', published_at=published)
        ordinary = _make_post('ordinary-edited-post', published_at=published)
        Post.objects.filter(pk__in=[live.pk, ordinary.pk]).update(updated_at=edited)

        self.assertIn('Updated <time datetime="', self.client.get('/blog/warhammer-black-friday-deals/').content.decode())
        self.assertNotIn('Updated <time', self.client.get('/blog/ordinary-edited-post/').content.decode())
        Post.objects.filter(pk=live.pk).update(updated_at=published)
        self.assertNotIn('Updated <time', self.client.get('/blog/warhammer-black-friday-deals/').content.decode())


@override_settings(STORAGES=_TEST_STORAGES)
class BlackFridayCrawlReadinessTest(TestCase):
    """Once published, the Black Friday post is indexable, canonical, structured and listed in the sitemap."""

    def setUp(self):
        """A published post with the header image, as it will be on the live site."""
        self.published = timezone.now() - datetime.timedelta(hours=1)
        self.post = Post.objects.create(
            title='Warhammer Black Friday & Cyber Monday Deals 2026', slug='warhammer-black-friday-deals',
            excerpt='Every deal.', body='<h2 id="bf-battleforce">Battleforce Deals</h2><p>Body.</p>', status=Post.STATUS_PUBLISHED,
            published_at=self.published, author='ThriftHammer', meta_title='Warhammer Black Friday Deals 2026 | ThriftHammer',
            meta_description='Every Warhammer Black Friday and Cyber Monday deal in one place.',
            featured_image_url='https://thrifthammer.com/static/images/blog/black-friday-2026-header.5ae28d235469.webp',
            featured_image_alt='Black Friday graphic',
        )

    def test_page_is_indexable_with_one_h1_canonical_and_valid_structured_data(self):
        """200, no noindex anywhere, self canonical, one H1, og:image, and Article JSON-LD with both dates."""
        import json
        import re

        response = self.client.get('/blog/warhammer-black-friday-deals/')
        html = response.content.decode()
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('X-Robots-Tag', response.headers)
        self.assertIn('<meta name="robots" content="index, follow">', html)
        self.assertNotIn('noindex', html)
        self.assertIn('<link rel="canonical" href="https://thrifthammer.com/blog/warhammer-black-friday-deals/">', html)
        self.assertEqual(len(re.findall(r'<h1\b', html)), 1)
        self.assertIn('<meta property="og:image" content="https://thrifthammer.com/static/images/blog/black-friday-2026-header.5ae28d235469.webp">', html)
        blocks = [json.loads(b) for b in re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.S)]
        article = next(b for b in blocks if b.get('@type') == 'Article')
        self.assertIn('datePublished', article)
        self.assertIn('dateModified', article)
        self.assertEqual(article['image'], self.post.featured_image_url)

    def test_published_post_is_in_the_sitemap_and_robots_points_to_it(self):
        """The sitemap lists the post with a lastmod; robots.txt allows the blog and names the sitemap."""
        xml = self.client.get('/sitemap.xml').content.decode()
        self.assertIn('/blog/warhammer-black-friday-deals/</loc>', xml)
        self.assertIn('<lastmod>', xml.split('/blog/warhammer-black-friday-deals/')[1].split('</url>')[0])
        robots = self.client.get('/robots.txt').content.decode()
        self.assertIn('Sitemap: https://thrifthammer.com/sitemap.xml', robots)
        self.assertNotIn('Disallow: /blog', robots)
