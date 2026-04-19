"""
Management command: publish_roadmap_post

Creates the 'ThriftHammer Roadmap Explained' blog post if it does not already
exist.  Safe to run multiple times — exits cleanly if the post is already
present (idempotent).

Usage:
    python manage.py publish_roadmap_post
    python manage.py publish_roadmap_post --force  # overwrite existing post
"""

from django.core.management.base import BaseCommand
from django.utils import timezone

SLUG = 'the-thrifthammer-roadmap-explained'

BODY = """\
<p class="post-lead">I started ThriftHammer with a simple goal: reduce the barrier to entry for Warhammer players and help people save money on their hobby.</p>

<p>The site is still in beta, but over the next year we're planning to expand our capabilities significantly. With limited time and resources, we want to make sure we're focusing on what actually matters.</p>

<p>That's where you come in.</p>

<p>Today, I want to walk through the ThriftHammer roadmap at a high level: what we're building next, why it matters, and most importantly, how you can help shape the future.</p>

<h2>Why a Roadmap Matters</h2>

<p>Too many tools focus on adding features instead of delivering real value. That's not the goal here.</p>

<p>At ThriftHammer, every decision is guided by three principles:</p>

<ul>
  <li>Every feature should help you save money on Warhammer.</li>
  <li>Every update should improve the user experience or benefit the community.</li>
  <li>Every addition should make the site more useful and efficient.</li>
</ul>

<p>If something doesn't align with those principles, we won't build it.</p>

<h2>The Core Pillars of ThriftHammer</h2>

<p>Everything we build falls into a few key pillars. These are the foundation of the roadmap and where the biggest improvements are coming.</p>

<h3>1. Price Intelligence &amp; Deal Tracking</h3>

<p>This is the backbone of ThriftHammer, what sets it apart as a Warhammer price tracker and deal-finding tool.</p>

<p><strong>What you can do right now:</strong></p>
<ul>
  <li>Compare prices across 4 major US retailers</li>
  <li>Avoid overpriced listings</li>
  <li>Browse without hassle, no account required</li>
</ul>

<p><strong>What's coming next:</strong></p>
<ul>
  <li>Price history tracking</li>
  <li>Deal ratings (Good / Average / Great)</li>
  <li>A more robust Top Deals Today system</li>
  <li>Continued bug fixes and data accuracy improvements</li>
</ul>

<p><strong>What we need from you:</strong></p>
<p>Push the system. Break it. Stress test it. Report bugs, flag incorrect prices, and share constructive feedback. This is how we improve accuracy and build trust.</p>

<h3>2. Army Cost Planning (The Big One)</h3>

<p>This is the feature that can truly set ThriftHammer apart.</p>

<p>Warhammer isn't just about buying one product. It's about building an army over time. Costs add up quickly, and most players don't have a clear way to optimise their spending.</p>

<p><strong>Current functionality:</strong></p>
<ul>
  <li>Build out your army unit by unit</li>
  <li>Track total cost vs. GW MSRP</li>
  <li>Save your armies to revisit in the future</li>
</ul>

<p><strong>Where we're going:</strong></p>
<ul>
  <li>Budget-based army building (e.g. "If I have $1,000, how many points can I build?")</li>
  <li>Army suggestions by value, competitiveness, or sub-faction focus</li>
  <li>An expanded product catalogue for deeper, more accurate builds</li>
</ul>

<p><strong>What we need from you:</strong></p>
<ul>
  <li>Which armies and models should we prioritise?</li>
  <li>What game systems matter most (40K, AoS, others)?</li>
  <li>What UI changes would make the calculator actually useful for how you play?</li>
</ul>

<h3>3. Collection Tracking &amp; Savings Metrics</h3>

<p>This pillar is about tracking your entire Warhammer collection, from active armies to your pile of shame.</p>

<p><strong>Planned features:</strong></p>
<ul>
  <li>Average discount tracking across your collection</li>
  <li>Painted vs. unpainted categorisation</li>
  <li>Estimated resale value</li>
  <li>Share your collection with others</li>
</ul>

<p><strong>What we need from you:</strong> Which of these features matters most to you?</p>

<h3>4. Alerts, Watchlists, and Automation</h3>

<p>The goal here is simple: let the deals come to you.</p>

<p><strong>Planned features:</strong></p>
<ul>
  <li>Faster, more reliable price alerts</li>
  <li>Watchlists with customisable notifications</li>
  <li>Potential Discord integration</li>
</ul>

<p><strong>What we need from you:</strong></p>
<ul>
  <li>How do we improve alerts without becoming annoying?</li>
  <li>What types of alerts are most useful: army-specific, game system, or individual products?</li>
</ul>

<h3>5. Community &amp; User-Driven Features (Future Focus)</h3>

<p>This is the long-term vision for ThriftHammer, but we need to start planning today.</p>

<p><strong>Ideas being explored:</strong></p>
<ul>
  <li>Community-driven deal lists (e.g. "Best Deals, Voted by the Community")</li>
  <li>Support for local game stores (FLGS)</li>
  <li>Retailer and product reviews</li>
  <li>Hobby-related tools</li>
  <li>Expansion to other game systems</li>
  <li>Archive of assembly instructions</li>
  <li>Second-hand product tracking</li>
  <li>Expansion to other regions</li>
</ul>

<p><strong>What we need from you:</strong> Help us prioritise. What do you want to see? What do you <em>not</em> want to see? Where should we focus over the next few years?</p>

<h2>How the Roadmap Will Evolve</h2>

<p>This is not a fixed plan.</p>

<p>We expect the roadmap to evolve based on user feedback, what's technically possible, and how quickly the site grows. We can't predict the future or guarantee success, but we will strive for transparency and keep sharing updates as things progress.</p>

<h2>Have Your Say</h2>

<p>Leave a comment below or reach out directly at <a href="mailto:Thrifthammer.com@gmail.com">Thrifthammer.com@gmail.com</a>.</p>

<p>We're excited about what's ahead and want to build this alongside the community. Thanks for being part of it. Expect more updates soon.</p>
"""


class Command(BaseCommand):
    """Publish the ThriftHammer Roadmap blog post if it is not already present."""

    help = 'Publishes the ThriftHammer Roadmap Explained blog post (idempotent).'

    def add_arguments(self, parser):
        """Add optional --force flag to overwrite an existing post."""
        parser.add_argument(
            '--force',
            action='store_true',
            help='Overwrite the post body/meta even if it already exists.',
        )

    def handle(self, *args, **options):
        """Create or update the roadmap post."""
        from blog.models import Post

        existing = Post.objects.filter(slug=SLUG).first()

        if existing and not options['force']:
            self.stdout.write(
                self.style.SUCCESS(f'Post already exists (pk={existing.pk}) — skipping.')
            )
            return

        defaults = dict(
            title='The ThriftHammer Roadmap Explained',
            excerpt=(
                "A look at what we're building next, why it matters, and how you can "
                "help shape the future of ThriftHammer."
            ),
            body=BODY,
            status=Post.STATUS_PUBLISHED,
            published_at=timezone.now(),
            meta_title="ThriftHammer Roadmap: What We're Building Next",
            meta_description=(
                'ThriftHammer roadmap: price intelligence, army cost planning, '
                'collection tracking, alerts, and community features. '
                'Help us shape what comes next.'
            ),
        )

        if existing:
            for attr, val in defaults.items():
                setattr(existing, attr, val)
            existing.save()
            self.stdout.write(
                self.style.SUCCESS(f'Updated existing post (pk={existing.pk}, slug={existing.slug}).')
            )
        else:
            post = Post(**defaults)
            post.save()
            self.stdout.write(
                self.style.SUCCESS(f'Created post (pk={post.pk}, slug={post.slug}).')
            )
