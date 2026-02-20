"""
Django admin configuration for the blog app.

Staff write and publish posts here. Tags can be created inline or via
the Tag admin. SEO fields (meta_title, meta_description) are in a
collapsible section to keep the main editing area clean.
"""

from django.contrib import admin

from .models import Post, Tag


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """Admin for blog tags — simple slug+name pairs."""

    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    """
    Admin for blog posts.

    Workflow: create a Draft, write content, set published_at to now,
    then flip status to Published to make the post live.
    """

    list_display = ('title', 'status', 'published_at', 'created_at')
    list_filter = ('status', 'tags')
    search_fields = ('title', 'excerpt', 'body')
    prepopulated_fields = {'slug': ('title',)}
    date_hierarchy = 'published_at'
    filter_horizontal = ('tags',)
    list_per_page = 25

    fieldsets = (
        (None, {
            'fields': ('title', 'slug', 'status', 'published_at'),
        }),
        ('Content', {
            'fields': ('excerpt', 'body'),
            'description': (
                'excerpt: shown on the list page and used as meta description fallback. '
                'body: full HTML content.'
            ),
        }),
        ('Featured Image', {
            'fields': ('featured_image_url', 'featured_image_alt'),
            'classes': ('collapse',),
        }),
        ('Tags', {
            'fields': ('tags',),
        }),
        ('SEO Overrides', {
            'fields': ('meta_title', 'meta_description'),
            'classes': ('collapse',),
            'description': (
                'Leave blank to use the post title/excerpt as defaults. '
                'meta_title: 60 chars max. meta_description: 120-160 chars.'
            ),
        }),
    )
