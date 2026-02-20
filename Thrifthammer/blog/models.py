"""
Models for the ThriftHammer blog.

The blog is focused on helping Warhammer 40K players save money on the hobby
and improving organic SEO. Articles are created by staff in the Django admin.
"""

from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify


class Tag(models.Model):
    """A lightweight content tag for grouping related blog posts."""

    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        """Auto-generate slug from name if not set."""
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Post(models.Model):
    """
    A single blog post.

    Fields support full SEO metadata (meta_title, meta_description) so each
    post can be independently optimised for search. Posts are only visible
    once status is PUBLISHED and published_at is a past datetime.
    """

    STATUS_DRAFT = 'draft'
    STATUS_PUBLISHED = 'published'
    STATUS_CHOICES = [
        (STATUS_DRAFT, 'Draft'),
        (STATUS_PUBLISHED, 'Published'),
    ]

    # Core content
    title = models.CharField(max_length=200, help_text='Post headline — also used as H1.')
    slug = models.SlugField(
        max_length=220,
        unique=True,
        blank=True,
        help_text='URL slug — auto-generated from title if blank.',
    )
    excerpt = models.TextField(
        max_length=300,
        blank=True,
        help_text='Short summary shown on the list page and in social cards. Max 300 chars.',
    )
    body = models.TextField(
        help_text='Full post content. Supports HTML.',
    )

    # Publication
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_DRAFT,
        db_index=True,
    )
    published_at = models.DateTimeField(
        null=True,
        blank=True,
        db_index=True,
        help_text='Set to a past datetime to make the post live.',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Taxonomy
    tags = models.ManyToManyField(
        Tag,
        blank=True,
        related_name='posts',
        help_text='Optional content tags (e.g. "Space Marines", "Budget Tips").',
    )

    # SEO overrides
    meta_title = models.CharField(
        max_length=70,
        blank=True,
        help_text='<title> tag override. Leave blank to use the post title. Aim for 60 chars or less.',
    )
    meta_description = models.CharField(
        max_length=160,
        blank=True,
        help_text='Meta description for search engines. Aim for 120-160 chars.',
    )

    # Optional featured image URL
    featured_image_url = models.URLField(
        blank=True,
        help_text='Full URL to a featured header image.',
    )
    featured_image_alt = models.CharField(
        max_length=200,
        blank=True,
        help_text='Alt text for the featured image — required for accessibility and SEO.',
    )

    class Meta:
        ordering = ['-published_at', '-created_at']
        indexes = [
            models.Index(fields=['status', 'published_at']),
        ]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        """Auto-generate unique slug from title if not already set."""
        if not self.slug:
            base = slugify(self.title)[:210]
            slug = base
            counter = 1
            while Post.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        """Return the canonical URL for this post."""
        return reverse('blog:post_detail', kwargs={'slug': self.slug})

    @property
    def is_published(self):
        """True if the post is published and its publish date is in the past."""
        return (
            self.status == self.STATUS_PUBLISHED
            and self.published_at is not None
            and self.published_at <= timezone.now()
        )

    @property
    def effective_meta_title(self):
        """Return SEO title override or fall back to the post title."""
        return self.meta_title or self.title

    @property
    def effective_meta_description(self):
        """Return SEO meta description or fall back to the excerpt."""
        return self.meta_description or self.excerpt
