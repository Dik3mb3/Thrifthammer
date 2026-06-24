"""
Management command to set featured_image_url on blog posts that have
local static images committed to the repo.

Run AFTER collectstatic so staticfiles_storage.url() resolves the
correct (hashed) filename via the WhiteNoise manifest.

Idempotent — skips posts that already have a featured image.
"""

from django.contrib.staticfiles.storage import staticfiles_storage
from django.core.management.base import BaseCommand

from blog.models import Post

# ---------------------------------------------------------------------------
# Map: post slug  →  static file path + alt text
# Add new entries here whenever a blog post gets its own image.
# ---------------------------------------------------------------------------
BLOG_IMAGES = [
    {
        'slug': 'hidden-costs-warhammer-40k',
        'static_path': 'images/blog/hidden-costs-warhammer.png',
        'alt': 'Warhammer 40K painted miniatures, dice, storage case and Space Marines codex',
    },
    {
        'slug': '40k-hot-takes-warm-spicy-and-scorching',
        'static_path': 'images/blog/40k-hot-takes.png',
        'alt': 'Warhammer 40K hot takes — warm, spicy, and scorching opinions',
    },
    {
        'slug': 'warhammer-40k-launch-box-prices-economics-part-1',
        'static_path': 'images/blog/economics-of-warhammer.png',
        'alt': (
            'Chart showing Warhammer 40K launch box prices across editions — '
            'is Warhammer getting more expensive?'
        ),
    },
    {
        'slug': 'the-thrifthammer-roadmap-explained',
        'static_path': 'images/blog/blog-roadmap.png',
        'alt': 'ThriftHammer roadmap, upcoming features and planned improvements',
    },
    {
        'slug': 'best-starter-warhammer-40k-armies-2026',
        'static_path': 'images/blog/blog-best-starter-armies.jpg',
        'alt': 'Best starter Warhammer 40K armies for new players in 2026',
    },
    {
        'slug': '5-warhammer-kit-hacks-more-minis-for-your-money',
        'static_path': 'images/blog/blog-best-warhammer-kits.jpg',
        'alt': 'Warhammer kit hacks to get more miniatures for your money',
    },
    {
        'slug': 'best-value-miniature-paints',
        'static_path': 'images/blog/blog-mini-paints.png',
        'alt': 'Best value miniature paints for Warhammer, compared by cost per ml',
    },
    {
        'slug': '3-best-3-worst-warhammer-video-games',
        'static_path': 'images/blog/blog-video-games.jpg',
        'alt': 'The 3 best and 3 worst Warhammer video games',
    },
    {
        'slug': 'best-budget-warhammer-40k-hobby-tools',
        'static_path': 'images/blog/blog-hobby-supplies.jpg',
        'alt': 'Best budget Warhammer 40K hobby tools and supplies every player should own',
    },
    {
        'slug': 'top-5-warhammer-content-creators',
        'static_path': 'images/blog/blog-best-content-creators.jpg',
        'alt': 'Top 5 Warhammer content creators worth following on YouTube and social media',
    },
    {
        'slug': 'warhammer-40k-faction-popularity-ranking',
        'static_path': 'images/blog/blog-faction-popularity-ranking.jpg',
        'alt': 'Most popular Warhammer 40K factions ranked by Reddit, Instagram, and tournament data',
    },
    {
        'slug': 'warhammer-40k-armageddon-11th-edition-box-contents-revealed',
        'static_path': 'images/blog/11th-edition-box.png',
        'alt': 'Warhammer 40K Armageddon 11th Edition launch box contents revealed',
    },
    {
        'slug': 'warhammer-40k-battleforce-boxes-11th-edition-ranked',
        'static_path': 'images/blog/blog-11th-edition-battleforces.png',
        'alt': 'Warhammer 40K 11th Edition Battleforce boxes: Astra Militarum, Tyranids, Chaos Space Marines, and Necrons',
    },
]

BASE_URL = 'https://thrifthammer.com'


class Command(BaseCommand):
    """Set featured images on blog posts using committed static files."""

    help = 'Set featured_image_url on blog posts using local static images'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Overwrite featured_image_url even if already set',
        )

    def handle(self, *args, **options):
        force = options['force']
        updated = 0
        skipped = 0

        for entry in BLOG_IMAGES:
            slug = entry['slug']
            post = Post.objects.filter(slug=slug).first()

            if not post:
                self.stdout.write(self.style.WARNING(f'  [skip] Post not found: {slug}'))
                skipped += 1
                continue

            if post.featured_image_url and not force:
                self.stdout.write(f'  [skip] Already has image: {slug}')
                skipped += 1
                continue

            try:
                relative_url = staticfiles_storage.url(entry['static_path'])
                full_url = f'{BASE_URL}{relative_url}'
                post.featured_image_url = full_url
                post.featured_image_alt = entry['alt']
                post.save(update_fields=['featured_image_url', 'featured_image_alt'])
                self.stdout.write(self.style.SUCCESS(f'  [ok]   {post.title}'))
                self.stdout.write(f'         → {full_url}')
                updated += 1
            except Exception as exc:
                self.stdout.write(self.style.ERROR(f'  [err]  {slug}: {exc}'))

        self.stdout.write(
            self.style.SUCCESS(f'\nDone — {updated} updated, {skipped} skipped.')
        )
