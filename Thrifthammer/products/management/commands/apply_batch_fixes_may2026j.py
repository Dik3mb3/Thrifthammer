"""
Management command: apply_batch_fixes_may2026j

Blog post: warhammer-40k-faction-popularity-ranking

Changes:
  1. All /factions/<slug>/ links → /products/?faction=<slug>
     Affects: main rankings table, h3 section headings, and inline prose
     paragraphs (26 currently-linked factions, all locations in one regex pass).

  2. Add browse link for Chaos Daemons (rank 22) — currently plain text in
     the table with no anchor tag.
     <td>Chaos Daemons</td>
       → <td><a href="/products/?faction=chaos-daemons">Chaos Daemons</a></td>

  3. Add browse link for Imperial Agents (rank 28) — currently plain text in
     the table. Faction slug on ThriftHammer is agents-of-the-imperium.
     <td>Imperial Agents</td>
       → <td><a href="/products/?faction=agents-of-the-imperium">Imperial Agents</a></td>

Idempotent — safe to re-run.
"""

import re

from django.core.management.base import BaseCommand

from blog.models import Post

_BLOG_SLUG = 'warhammer-40k-faction-popularity-ranking'


class Command(BaseCommand):
    """Apply batch fixes may2026j — faction links in popularity ranking post."""

    help = 'Repoint faction links in popularity ranking blog post to products browse page.'

    def handle(self, *args, **options):
        """Run all fixes."""
        try:
            post = Post.objects.get(slug=_BLOG_SLUG)
        except Post.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'Blog post not found: {_BLOG_SLUG}'))
            return

        body = post.body

        # ── 1. Replace all /factions/<slug>/ hrefs → /products/?faction=<slug> ──
        new_body, count = re.subn(
            r'href="/factions/([^/]+)/"',
            r'href="/products/?faction=\1"',
            body,
        )
        self.stdout.write(f'Faction href replacements: {count}')

        # ── 2. Add link for Chaos Daemons (plain text → anchor) ────────────────
        cd_old = '<td>Chaos Daemons</td>'
        cd_new = '<td><a href="/products/?faction=chaos-daemons">Chaos Daemons</a></td>'
        if cd_old in new_body:
            new_body = new_body.replace(cd_old, cd_new)
            self.stdout.write('Chaos Daemons: link added.')
        else:
            self.stdout.write('Chaos Daemons: plain-text cell not found (already linked or different markup).')

        # ── 3. Add link for Imperial Agents → agents-of-the-imperium ───────────
        ia_old = '<td>Imperial Agents</td>'
        ia_new = '<td><a href="/products/?faction=agents-of-the-imperium">Imperial Agents</a></td>'
        if ia_old in new_body:
            new_body = new_body.replace(ia_old, ia_new)
            self.stdout.write('Imperial Agents: link added.')
        else:
            self.stdout.write('Imperial Agents: plain-text cell not found (already linked or different markup).')

        if new_body != body:
            post.body = new_body
            post.save(update_fields=['body'])
            self.stdout.write(self.style.SUCCESS('Blog post saved.'))
        else:
            self.stdout.write('No changes made (all already up to date).')

        self.stdout.write(self.style.SUCCESS('apply_batch_fixes_may2026j complete.'))
