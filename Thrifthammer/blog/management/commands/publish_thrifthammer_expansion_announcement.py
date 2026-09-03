"""
Management command: publish_thrifthammer_expansion_announcement

Creates 'ThriftHammer Expands Beyond Warhammer: Now Covering 17 Tabletop
Games' blog post. Safe to run multiple times (idempotent).

Usage:
    python manage.py publish_thrifthammer_expansion_announcement
    python manage.py publish_thrifthammer_expansion_announcement --force
"""

from django.contrib.staticfiles.storage import staticfiles_storage
from django.core.management.base import BaseCommand
from django.utils import timezone

SLUG = 'thrifthammer-expands-beyond-warhammer'
SITE_URL = 'https://thrifthammer.com'


def _static(path):
    return f'{SITE_URL}{staticfiles_storage.url(path)}'


BODY = """\
<p>When ThriftHammer first launched, the sole goal was helping Warhammer 40K players in the United States save money on popular kits.</p>

<p>Warhammer 40K is by far the most expensive miniature game, and finding the best price often means checking multiple retailers and comparing discounts over time. I built ThriftHammer to make that process easier and build a community around deal hunting so everyone can maximize their 40K spending.</p>

<p>But as time passed, I realized this problem isn't unique to Warhammer 40K or the United States. All miniature gaming is expensive, and there are deals to be found across every game system, big or small. In less than a year, ThriftHammer has expanded to cover 17 game systems, and now covers both the U.S. and the United Kingdom.</p>

<h2>Currently Covered Game Systems</h2>

<p>Here's everything you can currently browse and compare prices on:</p>

<ul>
  <li><a href="https://thrifthammer.com/products/?category=warhammer-40000&amp;sort=discount">Warhammer 40K</a></li>
  <li><a href="https://thrifthammer.com/products/?category=age-of-sigmar&amp;sort=discount">Age of Sigmar</a></li>
  <li><a href="https://thrifthammer.com/products/?category=battletech&amp;sort=discount">BattleTech</a></li>
  <li><a href="https://thrifthammer.com/products/?category=halo-flashpoint&amp;sort=discount">Halo: Flashpoint</a></li>
  <li><a href="https://thrifthammer.com/products/?category=horus-heresy&amp;sort=discount">Horus Heresy</a></li>
  <li><a href="https://thrifthammer.com/products/?category=kill-team&amp;sort=discount">Kill Team</a></li>
  <li><a href="https://thrifthammer.com/products/?category=malifaux&amp;sort=discount">Malifaux</a></li>
  <li><a href="https://thrifthammer.com/products/?category=marvel-crisis-protocol&amp;sort=discount">Marvel Crisis Protocol</a></li>
  <li><a href="https://thrifthammer.com/products/?category=middle-earth-mesbg&amp;sort=discount">Middle Earth (MESBG)</a></li>
  <li><a href="https://thrifthammer.com/products/?category=necromunda&amp;sort=discount">Necromunda</a></li>
  <li><a href="https://thrifthammer.com/products/?category=star-wars-legion&amp;sort=discount">Star Wars: Legion</a></li>
  <li><a href="https://thrifthammer.com/products/?category=star-wars-shatterpoint&amp;sort=discount">Star Wars: Shatterpoint</a></li>
  <li><a href="https://thrifthammer.com/products/?category=the-old-world&amp;sort=discount">The Old World</a></li>
  <li><a href="https://thrifthammer.com/products/?category=trench-crusade&amp;sort=discount">Trench Crusade</a></li>
  <li><a href="https://thrifthammer.com/products/?category=warcry&amp;sort=discount">Warcry</a></li>
  <li><a href="https://thrifthammer.com/products/?category=warmachine&amp;sort=discount">Warmachine</a></li>
  <li><a href="https://thrifthammer.com/products/?category=blood-bowl&amp;sort=discount">Blood Bowl</a></li>
</ul>

<h2>What's Next?</h2>

<p>Our second expansion will be even bigger than our first.</p>

<p>The short term goal is to cover popular games like Bolt Action, Infinity, and Conquest, while simultaneously growing the catalog of up-and-coming games like Moonstone and Konflikt '47.</p>

<p>In terms of geography, the United Kingdom is just the first step. The plan is to expand to 2 or more countries by the end of 2027 (I'll let you guess which ones). By the end of 2027, our second expansion should encompass 25+ categories, 4 countries, and 5,000+ available products.</p>

<p>Like we do with Warhammer, we plan to offer the following for each game system:</p>

<ul>
  <li><strong>Price Comparison</strong>: Compare prices across multiple retailers.</li>
  <li><strong>Weekly Newsletter</strong>: Discounts and special offers sent to you via email.</li>
  <li><strong>Collection Management</strong>: Keep track of the games and miniatures you own.</li>
  <li><strong>More Tools and Features</strong>: We're continuing to experiment with new tools to add to the site, with the goal of making hobbyist lives easier and better.</li>
</ul>

<p>Not every feature will be available for every game or country immediately, but that's the direction we're building toward.</p>

<h2>Vision for the Future</h2>

<p>One of the most exciting parts of this expansion, and future expansions, is being able to introduce players to games they may not have considered before.</p>

<p>Maybe you're a Warhammer player looking for something different, but you're limited by your budget and don't want to spend $100 on a new starter set since the new game might not be a good fit. What if, instead of $100, you could find an entry point for $70? I believe budget is often the #1 factor keeping people from trying out a new game.</p>

<p>If ThriftHammer can deliver average savings of 20% to 30% across all of miniature gaming, I believe we can help grow the hobby by reducing the cost of entry, and help smaller game companies reach new audiences.</p>

<h2>The ThriftHammer Ecosystem</h2>

<p>ThriftHammer has grown so quickly that it's become difficult to keep up with all the resources available. Here's the breakdown of all our major features today, all completely free.</p>

<h3>No Account Required</h3>

<ul>
  <li><strong>Price Comparison</strong>: Browse a catalog of nearly 3,000 products and compare prices across major online retailers.</li>
  <li><strong>Blog</strong>: Weekly and bi-weekly blog posts covering various miniature gaming topics.</li>
  <li><strong>Reddit Community</strong>: We have an amazing Reddit community, <a href="https://www.reddit.com/r/DealHammer/" target="_blank" rel="noopener noreferrer">r/DealHammer</a>, where top deals are posted weekly.</li>
  <li><strong>Warhammer 40K Army Calculator</strong>: See the cost to build your dream army, including in-game points, unit rules, and profiles.</li>
  <li><strong>Basic Newsletter</strong>: Receive two weekly newsletters, one for Warhammer 40K and one for Age of Sigmar.</li>
</ul>

<h3>Account Required</h3>

<ul>
  <li><strong>Custom Newsletter</strong>: Customize your newsletter to include or exclude specific factions, get deals on other game systems, and more.</li>
  <li><strong>Price Alerts</strong>: Create custom price alerts for your favorite models. Set a target price and get notified when it's reached.</li>
  <li><strong>My Armies</strong>: Save armies from the Army Calculator to view later.</li>
  <li><strong>Collection</strong>: Track your current Warhammer collection and see how much you've spent versus MSRP.</li>
</ul>

<p>Welcome to the next chapter of ThriftHammer. I want to thank our current community for their support and feedback over the last year, as this site has grown from a simple catalog of fewer than 300 Warhammer 40K kits to what it is today.</p>
"""


class Command(BaseCommand):
    """Publish the ThriftHammer expansion announcement blog post (idempotent)."""

    help = 'Publishes the ThriftHammer expansion announcement blog post.'

    def add_arguments(self, parser):
        """Add --force flag."""
        parser.add_argument(
            '--force',
            action='store_true',
            help='Overwrite existing post body/meta. Never changes published_at.',
        )
        parser.add_argument(
            '--publish',
            action='store_true',
            help='Set status to PUBLISHED. Without this flag the post is created as a DRAFT (not visible on the live site).',
        )

    def handle(self, *args, **options):
        from blog.models import Post, Tag

        existing = Post.objects.filter(slug=SLUG).first()
        status = Post.STATUS_PUBLISHED if options['publish'] else Post.STATUS_DRAFT

        if existing and not options['force']:
            self.stdout.write(
                self.style.SUCCESS(f'Post already exists (pk={existing.pk}) -- skipping.')
            )
            return

        image_url = _static('images/blog/thrifthammer-expansion-1-header.webp')
        if not image_url or 'thrifthammer-expansion-1-header' not in image_url:
            self.stdout.write(self.style.ERROR(
                f'featured_image_url resolved to unexpected value: {image_url!r} -- aborting, run collectstatic first.'
            ))
            return

        defaults = dict(
            slug=SLUG,
            title="ThriftHammer Expands Beyond Warhammer: Now Covering 17 Tabletop Games",
            excerpt=(
                "ThriftHammer started as a Warhammer 40K price tracker. One year later, we cover "
                "17 tabletop game systems across the U.S. and UK, with more countries and games "
                "on the way."
            ),
            body=BODY,
            status=status,
            # published_at is NOT here -- it never belongs in defaults
            meta_title='ThriftHammer Expands: Now Covering 17 Tabletop Games',
            meta_description=(
                "ThriftHammer has grown from Warhammer 40K to 17 tabletop game systems across the "
                "U.S. and UK. See what's covered now and what's coming next."
            ),
            featured_image_url=image_url,
            featured_image_alt='ThriftHammer Expansion #1 announcement banner',
        )

        if existing:
            for attr, val in defaults.items():
                setattr(existing, attr, val)
            existing.save()
            post = existing
            self.stdout.write(self.style.SUCCESS(f'Updated post (pk={post.pk}), status={status}.'))
        else:
            # published_at is ONLY set here, on the creation path
            post = Post(**defaults, published_at=timezone.now())
            post.save()
            self.stdout.write(self.style.SUCCESS(f'Created post (pk={post.pk}), status={status}.'))

        tag_names = ['Community', 'Site News']
        for name in tag_names:
            tag, _ = Tag.objects.get_or_create(name=name)
            post.tags.add(tag)
        self.stdout.write(self.style.SUCCESS(f'Tags: {tag_names}'))
