"""
Management command: publish_warhammer_academy_is_live

Creates 'Warhammer Academy Is Live: A Free New Way to Learn Warhammer
40,000' blog post. Safe to run multiple times (idempotent).

Usage:
    python manage.py publish_warhammer_academy_is_live
    python manage.py publish_warhammer_academy_is_live --force
"""

from django.contrib.staticfiles.storage import staticfiles_storage
from django.core.management.base import BaseCommand
from django.utils import timezone

SLUG = 'warhammer-academy-is-live'
SITE_URL = 'https://thrifthammer.com'


def _static(path):
    try:
        return f'{SITE_URL}{staticfiles_storage.url(path)}'
    except Exception:
        return ''


BODY = """\
<p>Games Workshop just launched Warhammer Academy, their free online learning platform built for new people interested in Warhammer. The goal of the Academy is to take a brand new person from "what is Warhammer?" to building and painting their first army. It's available right now at <a href="https://academy.warhammer.com/en-gb" target="_blank" rel="noopener noreferrer">academy.warhammer.com</a>. All you have to do is create a free My Warhammer account.</p>

<p>The site went live yesterday, July 21, 2026, and already includes dozens of hours of learning content from painting & hobbying, faction lore, and learning how to play. I had many questions about how the platform would work following its reveal at Games Workshop's Big Summer Preview back in June. Would this just be another clunky, buggy Games Workshop digital product, or a successful onboarding platform for new fans?</p>

<p>Here's what it offers, what it gets right, and where it has room to grow.</p>

<h2>What Is the Warhammer Academy?</h2>

<p>Warhammer Academy is a completely free dedicated learning & content platform. At launch it includes over 150 videos covering Warhammer 40,000, organized into three distinct learning categories.</p>

<ul>
  <li><strong>Collecting & Lore</strong> - lore tidbits for all Warhammer 40K factions, giving newcomers some lore foundation to help their faction selection.</li>
  <li><strong>Building and Painting</strong> - videos around model assembly and painting techniques. Videos are a step-by-step process on how to take a new model and turn it into a replica of the model you see on the front of a Warhammer kit.</li>
  <li><strong>Gaming</strong> - how to play Warhammer 40K, from setting up a table and moving units to shooting & combat.</li>
</ul>

<p>The site is available in eight languages, and Games Workshop has already confirmed that Age of Sigmar content is planned for a future expansion. To access the Academy, all you will need to do is create an account at the link above.</p>

<h2>The Highlights</h2>

<p><strong>It doesn't feel like an advertisement.</strong> This was my biggest worry going in. This could have easily been built as a glorified advertising website that pushes miniature sales over being a useful community resource. So far it doesn't feel that way at all. Warhammer Academy feels like it was built with the clear vision of helping new players learn about the Warhammer universe. While there is always a risk that this eventually will turn into an advertising engine, as of today it does not feel like that at all.</p>

<p><strong>It's easy to use.</strong> We have seen this story play out before. Games Workshop releases a new digital product and it's immediately riddled with bugs, poor UI, and lack of polish. I am glad to report the site is smooth, well-built, and polished. When you enter the site, there's a short walkthrough if you want one, and immediate access to pre-built learning paths for each faction and learning category. Games Workshop does a good job in directing brand-new players where they should start. For a company not historically known for polished digital products, this is a real step up.</p>

<p><strong>The painting and hobby videos are solid.</strong> If you've been painting miniatures for multiple years, the tutorials here probably won't teach you much. But for newer hobbyists, the tutorials are solid going over the basics, and I'll admit I picked up a technique or two myself. The individual model painting tutorials are some of my favorite videos as you can follow along step by step while you paint. Games Workshop cleverly uses its combat patrol box and <a href="/products/?category=discount-box-splits&amp;faction=warhammer-40k-armageddon-11th-edition&amp;sort=discount">Armageddon starter box</a> models as the focus of its painting videos. With new players likely picking up those boxes first, it makes perfect sense to showcase those models first on the platform.</p>

<h2>Is It Better Than YouTube?</h2>

<p>Short answer, no, but that is no fault of Warhammer Academy. YouTube is a behemoth in the Warhammer space with thousands of videos on a variety of topics. If you are interested in leveling up your painting game, you have creators like Vince Venturella who is both an expert painter and entertaining content creator. If you want to learn how to play, there are dozens of creators, each with different teaching styles, that you have access to. YouTube should continue to be your main source of learning and discovering the joy of Warhammer, but this doesn't mean Warhammer Academy is useless.</p>

<p>YouTube's biggest weakness is often discovery. There's no clear starting point and it's easy to accidentally land on a video that's either too advanced, is out of date, or has a teaching style that doesn't jive with how you like to learn. Many times, to find the right video on YouTube, it's trial and error, which could lead to frustration and newbies giving up too early. Warhammer Academy solves that problem by simplifying the process and creating streamlined learning pathways that remove the friction points of YouTube.</p>

<p>Don't expect Warhammer Academy to replace YouTube as your main Warhammer content hub, but it's another alternative to growing our community. The more options we give people, the higher chances we have in growing the community we love.</p>

<h2>Who Should Use Warhammer Academy</h2>

<p>If you're brand new to Warhammer 40,000, or you played an older edition and want a refresher, this is worth your time. It's very structured, providing you a clear on-ramp: pick a faction, learn the lore, learn to build and paint your models, then learn the rules. This platform has all the basics to get started with Warhammer 40K, even if you are starting from square one.</p>

<p>If you're a veteran Warhammer fan, Warhammer Academy likely won't teach you anything you already know. However, this is a totally free platform, so try it out, and you may pick up a thing or two. Hopefully, over time, Games Workshop creates content for more veteran hobbyists. Expanding the platform to assist a large demographic of the community could help the platform maintain a steady stream of users over the long term.</p>

<h2>Wishlist for Warhammer Academy</h2>

<p>My biggest wish for the Warhammer Academy is expansion beyond <a href="/products/?category=warhammer-40000&amp;sort=discount">Warhammer 40K</a> and <a href="/products/?category=age-of-sigmar&amp;sort=discount">Age of Sigmar</a>. Specialist games like <a href="/products/?category=blood-bowl&amp;sort=discount">Blood Bowl</a> and <a href="/products/?category=necromunda&amp;sort=discount">Necromunda</a> have a fraction of the tutorial and hobby content that 40K enjoys. Warhammer Academy can serve as an onboarding ramp for these games, helping grow their wider community.</p>

<p>I would also love to see more expert-level content. As someone who is a middling painter and hobbyist, I would happily watch videos on more complex painting techniques. Lore-wise, I wouldn't mind long-form content like I see on YouTube for individual factions or key lore events. I can see why Games Workshop has focused their attention on the new player experience, but for the platform to see long-term success, it must grow with its user base.</p>

<p>More personality! This is not a criticism of the content itself, but the videos on the platform felt a bit too safe. Games Workshop seemingly took no creative risks in the creation of the videos. The videos felt similar, lacking the creative hook that keeps you engaged when watching your favorite creators. It would be far more interesting in the future if Games Workshop tried different content formats or partnered with established online creators to create unique pieces of content.</p>

<h2>Final Verdict</h2>

<p>At ThriftHammer, the thing we love more than a good discount is a totally free product. Warhammer Academy is worth checking at minimum because it costs you nothing, and at best it will get you excited about the Warhammer universe and teach you a thing or two. Props to Games Workshop for successfully launching a platform to help make the hobby more approachable for new players. It remains to be seen whether Games Workshop will continue to support this platform long-term, but as of today, ThriftHammer gives Warhammer Academy two thumbs up.</p>

<h2>New to Warhammer?</h2>

<p>Check out these previous articles to help you start the hobby at the cheapest possible cost. Also, sign up for our newsletter to stay up to date on the latest hobby deals and article releases.</p>

<ul>
  <li><a href="/blog/cheap-warhammer-miniatures-target/">Target Warhammer Board Games: The Cheapest Way to Buy Warhammer Miniatures?</a></li>
  <li><a href="/blog/armageddon-individual-units-price-guide/">Warhammer 40K Armageddon Box: Individual Units Price Guide</a></li>
  <li><a href="/blog/warhammer-40k-battleforce-boxes-11th-edition-ranked/">Warhammer 40K Battleforce Boxes 11th Edition Ranked</a></li>
  <li><a href="/blog/how-to-choose-warhammer-40k-faction/">How to Choose Your Next Warhammer 40K Faction (Complete 2026 Guide)</a></li>
  <li><a href="/blog/best-warhammer-40k-books/">Best Warhammer 40K Books: A Complete Reading Guide</a></li>
  <li><a href="/blog/best-value-miniature-paints/">The Best Value Miniature Paints for Your Money</a></li>
  <li><a href="/blog/best-budget-warhammer-40k-hobby-tools/">The Best Budget Warhammer 40K Hobby Tools Every Player Should Own</a></li>
</ul>

<p>Welcome to the hobby! Hope to see you at a local event, enjoy the journey through one of the coolest gaming universes in the world.</p>
"""


class Command(BaseCommand):
    """Publish the Warhammer Academy Is Live blog post (idempotent)."""

    help = 'Publishes the Warhammer Academy Is Live blog post.'

    def add_arguments(self, parser):
        """Add --force flag."""
        parser.add_argument(
            '--force',
            action='store_true',
            help='Overwrite existing post body/meta. Never changes published_at.',
        )

    def handle(self, *args, **options):
        from blog.models import Post, Tag

        existing = Post.objects.filter(slug=SLUG).first()

        if existing and not options['force']:
            self.stdout.write(
                self.style.SUCCESS(f'Post already exists (pk={existing.pk}) -- skipping.')
            )
            return

        defaults = dict(
            slug=SLUG,
            title='Warhammer Academy Is Live: A Free New Way to Learn Warhammer 40,000',
            excerpt=(
                'Games Workshop just launched Warhammer Academy, a free online learning '
                'platform for new 40K players. We review the painting, lore, and gameplay '
                'content to see if it delivers.'
            ),
            body=BODY,
            status=Post.STATUS_PUBLISHED,
            # published_at is NOT here — it never belongs in defaults
            meta_title='',
            meta_description=(
                'Games Workshop launched Warhammer Academy, a free 40K learning platform '
                'with painting, lore, and gameplay tutorials. Here is our full review.'
            ),
            featured_image_url=_static('images/blog/warhammer-academy-is-live-header.webp'),
            featured_image_alt='ThriftHammer Reviews Warhammer Academy, featuring the Warhammer and Academy logos',
        )

        if existing:
            for attr, val in defaults.items():
                setattr(existing, attr, val)
            existing.save()
            post = existing
            self.stdout.write(self.style.SUCCESS(f'Updated post (pk={post.pk}).'))
        else:
            # published_at is ONLY set here, on the creation path
            post = Post(**defaults, published_at=timezone.now())
            post.save()
            self.stdout.write(self.style.SUCCESS(f'Created post (pk={post.pk}).'))

        tag_names = ['Warhammer 40K', 'New Releases']
        for name in tag_names:
            tag, _ = Tag.objects.get_or_create(name=name)
            post.tags.add(tag)
        self.stdout.write(self.style.SUCCESS(f'Tags: {tag_names}'))
