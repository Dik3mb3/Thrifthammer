"""
Add the 'Beginner Guide' tag to existing posts that belong in the
beginner guide category. Safe to run repeatedly.

Posts targeted:
  - 5-warhammer-kit-hacks-more-minis-for-your-money
"""
from django.core.management.base import BaseCommand

from blog.models import Post, Tag

SLUGS = [
    '5-warhammer-kit-hacks-more-minis-for-your-money',
]

TAG_NAME = 'Beginner Guide'


class Command(BaseCommand):
    """Tag specified existing blog posts with the Beginner Guide tag."""

    help = 'Adds the Beginner Guide tag to specified blog posts. Safe to re-run.'

    def handle(self, *args, **options):
        """Resolve or create the tag then attach it to each post."""
        tag, created = Tag.objects.get_or_create(name=TAG_NAME)
        if created:
            self.stdout.write(f'Created tag: {TAG_NAME} (slug: {tag.slug})')
        else:
            self.stdout.write(f'Found tag: {TAG_NAME} (slug: {tag.slug})')

        for slug in SLUGS:
            try:
                post = Post.objects.get(slug=slug)
                post.tags.add(tag)
                self.stdout.write(self.style.SUCCESS(f'  Tagged: "{post.title}"'))
            except Post.DoesNotExist:
                self.stdout.write(self.style.WARNING(f'  Not found (slug={slug}) — skipping'))
