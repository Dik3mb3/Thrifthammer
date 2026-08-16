"""
Management command: publish_warlord_games_sprue_recycling

Creates 'Warlord Games Launches Sprue Recycling Program: 10 Dead Sprues
for 1 New Sprue' blog post. Safe to run multiple times (idempotent).

Usage:
    python manage.py publish_warlord_games_sprue_recycling
    python manage.py publish_warlord_games_sprue_recycling --force
"""

from django.contrib.staticfiles.storage import staticfiles_storage
from django.core.management.base import BaseCommand
from django.utils import timezone

SLUG = 'warlord-games-sprue-recycling-program'
SITE_URL = 'https://thrifthammer.com'


def _static(path):
    try:
        return f'{SITE_URL}{staticfiles_storage.url(path)}'
    except Exception:
        return ''


BODY = """\
<p>Whether you're a new player or an established collector of miniatures, you probably have a pile of sprues either sitting in your trash can or waiting to be used for a future project.</p>

<p>Did you know that these sprues can often sit in landfills for years before breaking down? Or that certain countries and regions are not able to accept them as recyclable materials?</p>

<p>If you didn't, no worries, I was totally oblivious to these facts and have been throwing away hundreds of sprue frames that I didn't reuse to make sprue goo. What can we do to put our sprues to better use? Warlord Games has a phenomenal solution: give Warlord 10 dead sprues, get 1 new sprue for free.</p>

<p>Warlord Games, most known for Bolt Action and Konflikt '47, has launched a new sprue recycling program in the UK, allowing hobbyists to bring in 10 used Warlord Games sprues in exchange for one new sprue at their Nottingham store.</p>

<p>It's a simple idea, but I think it's a great incentive for something that can otherwise be difficult to recycle and/or inconvenient for hobbyists to do routinely.</p>

<h2>How Does the Warlord Games Sprue Recycling Program Work?</h2>

<p>The program is currently available in the UK, beginning at Warlord Games' HQ store in Nottingham and at events that Warlord Games attends.</p>

<p>It's super simple:</p>

<ul>
  <li>Bring in 10 used Warlord Games sprues to the store</li>
  <li>Deposit the dead sprues in a Warlord recycling bin</li>
  <li>Receive one new sprue in return</li>
</ul>

<p>According to Warlord Games, the new sprue you will receive can come from old stock, recent releases, and pre-releases. So you don't necessarily know what you're going to receive, but 10 dead sprues is not a lot, especially if you're planning on starting a new hobby project.</p>

<p>There are a few catches. Warlord Games is only accepting Warlord Games sprues, so you can't bring your old <a href="https://thrifthammer.com/products/?category=warhammer-40000&amp;sort=discount">Warhammer 40K</a> or <a href="https://thrifthammer.com/products/?category=star-wars-legion&amp;sort=discount">Star Wars Legion</a> sprues and expect a sprue in return. Also, the singular location makes this very limited. As someone living in the U.S., it's unfortunate that I can't participate, and those living outside of Nottingham likely won't be able to take advantage of this program unless you visit one of their events in the UK.</p>

<p><strong>Warlord Games Announcement:</strong> <a href="https://warlord-community.warlordgames.com/bring-out-yer-dead-sprues/" target="_blank" rel="noopener noreferrer">Read the official Warlord Games announcement</a></p>

<h2>Why Is Recycling Miniature Sprues Difficult?</h2>

<p>My first question reading this announcement was, why can't UK and U.S. recycling programs accept sprues as recyclable materials?</p>

<p>Apparently, just because sprues are made from plastic doesn't necessarily mean they can be placed in your regular recycling bin.</p>

<p>Sprues are plastics that are made of different chemical compositions depending on the manufacturer (that's why Warlord does not accept other companies' sprues). Miniature manufacturers use specific types of plastic that local recycling systems aren't built to process, jamming machines and causing bottlenecks. Games Workshop identifies its miniature sprues as being made from High Impact Polystyrene (HIPS), which aren't accepted through many local authority curbside recycling programs.</p>

<p>That leaves us with relatively few options. Either reuse them, dump them in the trash, or find a specialized recycling center. If you're constantly working on hobby projects, you will likely be flooded with too many sprues to use in the near future, and finding a specialized recycling center is very inconvenient. I love that Warlord Games has added an incentive to motivate the community, even on a small scale, to help make our hobby a bit more sustainable.</p>

<h2>Games Workshop Also Offers Sprue Recycling</h2>

<p>Warlord Games isn't the only major miniature manufacturer working on this problem. Games Workshop is currently working with TerraCycle to provide recycling options at specific stores across the United States.</p>

<p>The program is free, although availability depends on participating stores. If you are interested, you can <a href="https://www.terracycle.com/en-US/brigades/warhammer" target="_blank" rel="noopener noreferrer">find a participating Warhammer recycling location through TerraCycle</a>.</p>

<p>Games Workshop's TerraCycle program doesn't offer a new miniature or sprue in exchange, but if you live locally to one of these locations, it might be worth it to pass by and drop off any excess sprues.</p>

<h2>Other Ideas for Reusing Sprues</h2>

<p>Recycling isn't the only option. Sprues are very versatile materials you can use for any hobby project.</p>

<p>Personally, I use most of my leftover sprues for sprue goo. Sprue goo can be used to fill in gaps in miniatures (very useful for kitbashing) or fix errors from assembly. <strong>New Player Tip:</strong> place cut up sprue into Tamiya extra thin plastic cement (the best glue for plastic miniatures) and let it dissolve over time to create sprue goo.</p>

<p>Other more creative uses for sprues include:</p>

<ul>
  <li>Creating sturdy homemade terrain for your miniature games</li>
  <li>Basing materials for your miniatures</li>
  <li>Scenery for your game tables (barricades, rubble, battlefield debris)</li>
  <li>Custom paint handles</li>
  <li>Trying out paints before applying them to your models</li>
  <li>Creating objective and in-game markers</li>
</ul>

<p>Worst case, if you're like me and your creativity stops with sprue goo, give them to a friend who can make use of it!</p>

<p>If you're reading this and new to Warhammer and don't know where to start, we have guides covering <a href="/blog/best-budget-warhammer-40k-hobby-tools/">Best Budget Hobby Tools</a>, <a href="/blog/best-value-miniature-paints/">Best Value Miniature Paints for the Money</a>, <a href="/blog/best-starter-warhammer-40k-armies-2026/">Best Starter Armies For Beginners</a>, and much more!</p>
"""


class Command(BaseCommand):
    """Publish the Warlord Games sprue recycling blog post (idempotent)."""

    help = 'Publishes the Warlord Games sprue recycling program blog post.'

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

        defaults = dict(
            slug=SLUG,
            title="Warlord Games Launches Sprue Recycling Program: 10 Dead Sprues for 1 New Sprue",
            excerpt=(
                "Warlord Games has launched a UK sprue recycling program: bring in 10 dead sprues "
                "and get one new sprue free. Here's how it works, why miniature sprues are hard "
                "to recycle, and other ways to reuse your extras."
            ),
            body=BODY,
            status=status,
            # published_at is NOT here — it never belongs in defaults
            meta_title='Warlord Games Sprue Recycling: 10 Dead Sprues for 1 Free',
            meta_description=(
                'Warlord Games now lets hobbyists trade 10 used sprues for one free new sprue at '
                "their Nottingham store. Here's how the recycling program works."
            ),
            featured_image_url=_static('images/blog/warlord-games-sprue-recycling-header.webp'),
            featured_image_alt='Warlord Games Dead Sprues recycling bin next to a pile of used plastic miniature sprues',
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

        tag_names = ['Community', 'Hobby Resources', 'Bits & Kitbashing']
        for name in tag_names:
            tag, _ = Tag.objects.get_or_create(name=name)
            post.tags.add(tag)
        self.stdout.write(self.style.SUCCESS(f'Tags: {tag_names}'))
