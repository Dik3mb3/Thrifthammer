"""
Management command to seed the initial ThriftHammer blog posts.

Run this on any environment (local or production) to populate the blog:
    python manage.py seed_blog
"""

from django.core.management.base import BaseCommand
from django.utils import timezone

from blog.models import Post, Tag


POSTS = [
    {
        'title': '5 Warhammer Kit Hacks: How to Get More Minis for Your Money',
        'slug': '5-warhammer-kit-hacks-more-minis-for-your-money',
        'excerpt': (
            'Five clever kit-bashing and buying tricks to stretch your hobby budget — '
            'from hidden Kabalites in the Ravager box to the old Ork Boyz secret weapon.'
        ),
        'meta_title': '5 Warhammer Kit Hacks: Get More Minis for Less Money',
        'meta_description': (
            'Five clever kit-bashing tricks to stretch your Warhammer budget — '
            'hidden Kabalites, Necron bit buffets, endless Intercessor sprues and more.'
        ),
        'tags': ['Budget Tips', 'Kit Hacks', 'Drukhari', 'Necrons', 'Space Marines', 'Orks', 'Tyranids'],
        'body': """<p>If you've ever stared at your hobby budget and muttered, <em>"I swear these sprues used to come with more bits,"</em> you're not alone. Welcome to the thrifty side of the hobby — where saving money doesn't mean giving up your love for plastic glory.</p>

<p>Here are our top 5 kit hacks to squeeze maximum value (and fun) from your purchases.</p>

<hr>

<h2>1. The Ravager (Drukhari) — Free Kabalites for Days</h2>
<p>The Ravager isn't just a skimmer of doom — it's secretly a Kabalite Warrior value pack.</p>
<p>Ignore the instructions and take those Kabalites seated on the pirate ship and kitbash them into a squad of Kabalite Warriors. If you're super-thrifty, pair those leftovers with bits from your friends' spare elf boxes, and boom — you've got an entire extra squad's worth of Drukhari.</p>

<h2>2. The Necron Warrior Box — The Endless Bit Buffet</h2>
<p>Necrons might sleep for millennia, but this box never rests when it comes to value. You get Gauss Flayers <em>and</em> Reapers for all 10 models, meaning whichever weapon you don't use becomes future conversion gold.</p>
<p>Build one full squad with Reapers and use the spare Flayers to kitbash your old Warriors — they'll rise again, cheaper than ever. Combine that with used bits from eBay, and you'll be fielding the dreaded silver horde for a fraction of the cost.</p>

<h2>3. Space Marine Intercessors — Chapter of Endless Options</h2>
<p>Each Intercessor sprue comes loaded with so many spare arms, helmets, and purity seals you could start a small relic shop. Combine them with leftover Assault Intercessor bodies and you'll have unique veterans ready to serve the Emperor.</p>
<p>As a Grey Knights player, I've bought my fair share of Space Marine bits online — and let me tell you, those extras are worth their weight in gold.</p>

<h2>4. The Old Ork Boyz Box — Da More, Da Merrier</h2>
<p>Sometimes, new ain't betta. The old Ork Boyz kit absolutely kicks da teef outta the newer one. A single box gives you more Orky goodness for kitbashing and spreading the WAAAGH.</p>
<p>You'll find an extra Ork body and a ton of wargear options to create the customized horde of your dreams. Grab one old Boyz box and one new — combine 'em for Da Bestest Boyz Mob this side of Armageddon.</p>

<h2>5. Tyranid Warriors — The Biomorph Bonanza</h2>
<p>Every sprue in this kit includes all possible biomorph weapons — bone swords, lash whips, venom cannons, and more. Build one loadout now and save the rest for magnetizing later or customizing smaller creatures.</p>
<p>If you're starting Tyranids, this is the value kit to anchor your swarm — both financially and tactically.</p>

<hr>

<h2>Bonus: Start Collecting &amp; Combat Patrol Boxes — The Ultimate Hack</h2>
<p>Sometimes the best hack is the most obvious — buy bundled boxes strategically. Combat Patrols often offer 30–40% more models for the same price compared to individual kits.</p>
<p>If you're strapped for cash, start with the <strong>Adeptus Custodes Combat Patrol</strong> — over 700 points of gold-clad demigods ready to punch holes through the legions of Chaos and Xenos alike.</p>
<p><a href="/products/">Compare Combat Patrol prices across retailers right now on ThriftHammer</a>.</p>

<hr>

<p>Warhammer will always test both your tactical and financial skills — but with a little creativity and a sharp hobby knife, you can build beautiful armies and keep your wallet intact.</p>
<p>Whether you're kitbashing Orks or resurrecting Necrons, remember: <strong>every sprue hides a secret unit.</strong></p>""",
    },
]


class Command(BaseCommand):
    """Seed initial blog posts into the database."""

    help = 'Seeds the initial ThriftHammer blog posts. Safe to re-run — skips existing slugs.'

    def handle(self, *args, **options):
        """Create tags and posts if they do not already exist."""
        created_count = 0
        skipped_count = 0

        for post_data in POSTS:
            if Post.objects.filter(slug=post_data['slug']).exists():
                self.stdout.write(f"  [skip]  {post_data['title']}")
                skipped_count += 1
                continue

            # Resolve / create tags
            tags = []
            for tag_name in post_data.get('tags', []):
                tag, _ = Tag.objects.get_or_create(name=tag_name)
                tags.append(tag)

            post = Post.objects.create(
                title=post_data['title'],
                slug=post_data['slug'],
                excerpt=post_data['excerpt'],
                body=post_data['body'],
                status=Post.STATUS_PUBLISHED,
                published_at=timezone.now(),
                meta_title=post_data.get('meta_title', ''),
                meta_description=post_data.get('meta_description', ''),
            )
            post.tags.set(tags)

            self.stdout.write(f"  [new]   {post.title}")
            created_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'\nDone! Created: {created_count}  |  Skipped: {skipped_count}'
            )
        )
