"""
Management command: apply_batch_fixes_may2026i

Changes:
  97-09   Maggotkin of Nurgle Plaguebearers
          image_url: ...99129915018_Plaguebearers01.jpg (404 — wrong asset ID)
                   → ...99129915008_Plaguebearers01.jpg?fm=webp&w=892&h=920

  Blog: games-workshop-11th-edition-space-marine-starter-set-leak
          Remove trailing shoutout paragraph linking to deleted YouTube channel
          @AsupexTactics (channel returns 404).

Idempotent — safe to re-run.
"""

from django.core.management.base import BaseCommand

from blog.models import Post
from products.models import Product

_OLD_IMAGE = (
    'https://www.warhammer.com/app/resources/catalog/product/920x950/'
    '99129915018_Plaguebearers01.jpg'
)
_NEW_IMAGE = (
    'https://www.warhammer.com/app/resources/catalog/product/920x950/'
    '99129915008_Plaguebearers01.jpg?fm=webp&w=892&h=920'
)

_YOUTUBE_PARAGRAPH = (
    '\n\n<p>Big shoutout to <a href="https://www.youtube.com/@AsupexTactics"'
    ' target="_blank" rel="noopener noreferrer">Asupex Tactics</a>'
    ' and his video on this box, which helped with this article.</p>'
)

_BLOG_SLUG = 'games-workshop-11th-edition-space-marine-starter-set-leak'


class Command(BaseCommand):
    """Apply batch fixes may2026i — Plaguebearers image fix and dead YouTube link removal."""

    help = 'Plaguebearers image URL fix and dead YouTube link removal.'

    def handle(self, *args, **options):
        """Run all fixes."""
        # ── Plaguebearers image URL ────────────────────────────────────────────
        updated = Product.objects.filter(image_url=_OLD_IMAGE).update(image_url=_NEW_IMAGE)
        self.stdout.write(f'Plaguebearers image: {updated} product(s) updated.')

        # ── Remove dead YouTube shoutout from blog post ────────────────────────
        try:
            post = Post.objects.get(slug=_BLOG_SLUG)
            if _YOUTUBE_PARAGRAPH in post.body:
                post.body = post.body.replace(_YOUTUBE_PARAGRAPH, '')
                post.save(update_fields=['body'])
                self.stdout.write('Blog post: YouTube shoutout paragraph removed.')
            else:
                self.stdout.write('Blog post: YouTube paragraph not found (already removed).')
        except Post.DoesNotExist:
            self.stdout.write(self.style.WARNING(f'Blog post not found: {_BLOG_SLUG}'))

        self.stdout.write(self.style.SUCCESS('apply_batch_fixes_may2026i complete.'))
