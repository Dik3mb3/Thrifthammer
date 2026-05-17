"""
Management command: publish_free_tools_guide

Creates 'The 20 Best Free Online Websites and Apps for Warhammer 40K' blog post
if it does not already exist.  Safe to run multiple times (idempotent).

Usage:
    python manage.py publish_free_tools_guide
    python manage.py publish_free_tools_guide --force  # overwrite existing post
"""

from django.core.management.base import BaseCommand
from django.utils import timezone

SLUG  = 'best-free-warhammer-40k-websites-apps'
TITLE = 'The 20 Best Free Online Websites and Apps for Warhammer 40K'

BODY = """\
<p class="post-lead">From army builders to crusade trackers, the Warhammer community has built an incredible library of free tools for every part of the hobby.</p>

<p>Warhammer 40K is a complex hobby. From model assembly to painting to list building and finally gameplay, there are so many parts to Warhammer 40K. Some of these parts have spawned their own separate communities filled with passionate hobbyists who have built free tools to support their communities.</p>

<p>Today there are a massive number of free tools, websites, apps, and hobby resources that you can access at your fingertips.</p>

<p>Whether you are:</p>
<ul>
  <li>Building competitive lists</li>
  <li>Painting and assembling your next army</li>
  <li>Tracking gameplay or campaigns</li>
  <li>Trying to find an STL for your next proxy</li>
  <li>Or looking for lore for your favorite faction</li>
</ul>

<p>There is probably a free tool that will help you along the way.</p>

<p>Today we cover the best free Warhammer 40K tools available to everyone. In the future we plan to dig deeper into each of these categories, but for today expect a small description of each tool and our personal use cases for it.</p>

<h2>Table of Contents</h2>
<ol>
  <li><a href="#painting-hobby-tools">Painting and Hobby Tools</a></li>
  <li><a href="#army-building-gameplay">Army Building and Gameplay Apps</a></li>
  <li><a href="#tournament-competitive">Tournament and Competitive Tools</a></li>
  <li><a href="#lore-reference">Lore and Reference Websites</a></li>
  <li><a href="#stl-3d-printing">STL and 3D Printing Resources</a></li>
  <li><a href="#campaign-crusade">Campaign and Crusade Management</a></li>
  <li><a href="#utility-tools">Utility Tools</a></li>
</ol>

<h2 id="painting-hobby-tools">Best Painting and Hobby Tools for Warhammer 40K</h2>

<h3>1. Dakka Dakka Paint Compatibility Table</h3>
<p><strong>Best For:</strong> Finding paint equivalents across different brands.</p>
<p>One of the most useful hobby references online. If a painting tutorial uses Citadel paints but you own Vallejo or Army Painter, this chart helps find close matches. Rather than going out to buy more paints for a new color scheme, this helps you maximize the paints you already own.</p>
<p><a href="https://www.dakkadakka.com/wiki/en/paint_range_compatibility_chart" rel="noopener noreferrer">Visit Dakka Dakka Paint Chart</a></p>

<h3>2. PaintRack (iOS and Google)</h3>
<p><strong>Best For:</strong> Tracking your paint collection.</p>
<p>PaintRack is a digital inventory system for hobby paints. Great for avoiding duplicate purchases and planning color schemes. Comes with a preloaded library of 27,000 paints from major manufacturers.</p>
<p><strong>Free vs Paid:</strong> The free version is likely enough for most hobbyists. For a one-time fee of $5 you get access to batch barcode scanning, color matching, mixing suggestions, cloud sync, and custom recipes.</p>
<p>
  <a href="https://apps.apple.com/us/app/paintrack/id1490523130" rel="noopener noreferrer">Download on iOS</a> |
  <a href="https://play.google.com/store/apps/details?id=com.courageousoctopus.paintrack&amp;hl=en_US" rel="noopener noreferrer">Download on Android</a>
</p>

<h3>3. Pinterest</h3>
<p><strong>Best For:</strong> Finding color scheme inspiration.</p>
<p>One of the best places online for discovering army schemes, basing ideas, and conversion ideas. I recently found my next color scheme for a group of <a href="/products/ork-burna-boyz/">Burna Boyz</a> I had sitting in my pile of shame.</p>
<p><a href="https://pin.it/5IkGwkao5" rel="noopener noreferrer">Visit Pinterest</a></p>

<h3>4. Reddit (Assembly Guides)</h3>
<p><strong>Best For:</strong> Finding assembly instructions for second-hand models.</p>
<p>This alone has saved me multiple times when buying used kits. A surprising number of assembly guides are archived on Reddit. If you buy models second-hand you can find high-quality images of assembly guides for pretty much any model, regardless of whether it is OldHammer or modern Warhammer.</p>

<h2 id="army-building-gameplay">Best Army Builder and Gameplay Apps</h2>

<h3>5. New Recruit</h3>
<p><strong>Best For:</strong> Free army list building.</p>
<p>In my experience, this is one of the best free alternatives to the official Warhammer app. Works great on mobile and desktop and is my go-to app for list building. This beats the Warhammer 40K official app and its content paywall.</p>
<p><a href="https://www.newrecruit.eu/" rel="noopener noreferrer">Visit New Recruit</a></p>

<h3>6. War Organ (iOS and Google)</h3>
<p><strong>Best For:</strong> Free army list building.</p>
<p>The hot new list building app. This one is getting a lot of buzz with its free features, easily digestible interface, and improving functionality. While I remain a New Recruit fan, you cannot go wrong with either of these apps.</p>
<p>
  <a href="https://apps.apple.com/gr/app/war-organ/id6737458881" rel="noopener noreferrer">Download on iOS</a> |
  <a href="https://play.google.com/store/apps/details?id=com.zenchovey.warorgan&amp;hl=en_US" rel="noopener noreferrer">Download on Android</a>
</p>

<h3>7. UnitCrunch</h3>
<p><strong>Best For:</strong> Warhammer probability calculations.</p>
<p>A Warhammer math simulator. For any math hammer fans this is a great resource for more complex calculations and simulations. Great for:</p>
<ul>
  <li>Damage calculations</li>
  <li>Expected wounds</li>
  <li>Evaluating unit efficiency</li>
</ul>
<p><a href="https://www.unitcrunch.com/" rel="noopener noreferrer">Visit UnitCrunch</a></p>

<h3>8. RollHammer (iOS and Google)</h3>
<p><strong>Best For:</strong> Fast digital dice rolling on your phone.</p>
<p>Handles all the complexities of dice rolling in Warhammer 40K including Sustained Hits, Devastating Wounds, Mortal Wounds, and Warhammer's many rerolls.</p>
<p>Not one I use most of the time (I love rolling dice) but useful for speeding up games when you or your opponent has time constraints.</p>
<p>
  <a href="https://apps.apple.com/us/app/rollhammer-battle-dice/id1548870360" rel="noopener noreferrer">Download on iOS</a> |
  <a href="https://play.google.com/store/apps/details?id=com.lastlevel.dicecup&amp;hl=en_US" rel="noopener noreferrer">Download on Android</a>
</p>

<h2 id="tournament-competitive">Best Tournament and Competitive Warhammer Tools</h2>

<h3>9. Best Coast Pairings</h3>
<p><strong>Best For:</strong> Tournament pairings and event management.</p>
<p>Best Coast Pairings (BCP) has become standard infrastructure for competitive 40K. It is used for pairings, tracking standings, event discovery, score tracking, and analytics.</p>
<p><strong>Free vs Paid:</strong> If you are a tournament organizer expect to pay for premium features ($5/month), but the free version still provides a lot of value for small competitive tournaments or narrative events.</p>
<p><a href="https://www.bestcoastpairings.com/" rel="noopener noreferrer">Visit Best Coast Pairings</a></p>

<h3>10. Tabletop Battles (iOS and Google)</h3>
<p><strong>Best For:</strong> Secondary objective tracking.</p>
<p>Clean interface built for easy scoring during games. The official Warhammer 40K App is expected to replace Tabletop Battles for 11th edition, but until I see it I will continue to recommend Tabletop Battles.</p>
<p>
  <a href="https://apps.apple.com/us/app/tabletop-battles/id1636901651" rel="noopener noreferrer">Download on iOS</a> |
  <a href="https://play.google.com/store/apps/details?id=com.goonhammer.ttba&amp;hl=en_US" rel="noopener noreferrer">Download on Android</a>
</p>

<h2 id="lore-reference">Best Warhammer Lore and Reference Websites</h2>

<h3>11. Wahapedia</h3>
<p><strong>Best For:</strong> Rules reference.</p>
<p>Probably the single most-used unofficial 40K reference site online. Wahapedia can be a single source for all your Warhammer 40K questions. The interface and mass amount of ads make this site a pain to use sometimes, but it remains my go-to site for rules questions.</p>
<p><a href="https://wahapedia.ru/" rel="noopener noreferrer">Visit Wahapedia</a></p>

<h3>12. Lexicanum</h3>
<p><strong>Best For:</strong> Well-researched Warhammer 40K lore.</p>
<p>A focused, more accurate database of Warhammer 40K lore than fandom-style wiki pages. A trustworthy lore site that you can lose hours in while digging into the lore of your favorite factions.</p>
<p><a href="https://wh40k.lexicanum.com/wiki/Main_Page" rel="noopener noreferrer">Visit Lexicanum</a></p>

<h2 id="stl-3d-printing">Best Free STL and 3D Printing Resources for Warhammer</h2>

<h3>13. Thingiverse | 14. Cults 3D | 15. My Mini Factory</h3>
<p><strong>Best For:</strong> STL files for proxies.</p>
<p>These sites provide a wide variety of free STL files that will bring any project to life. You will gain access to STL files for:</p>
<ul>
  <li>Terrain</li>
  <li>Conversion bits</li>
  <li>Proxy models</li>
</ul>
<p>You will not find official Warhammer STL files, but if you dig around you will find that these sites have a community of creators who have made Warhammer-adjacent STL files that help you create excellent proxies. I do not recommend any particular site over the other as they each have their own strengths and weaknesses.</p>
<ul>
  <li><a href="https://www.thingiverse.com/" rel="noopener noreferrer">Visit Thingiverse</a></li>
  <li><a href="https://cults3d.com/" rel="noopener noreferrer">Visit Cults 3D</a></li>
  <li><a href="https://www.myminifactory.com/" rel="noopener noreferrer">Visit My Mini Factory</a></li>
</ul>

<h2 id="campaign-crusade">Best Crusade and Campaign Management Tools</h2>

<h3>16. Administratum</h3>
<p><strong>Best For:</strong> Crusade tracking.</p>
<p>Warhammer 40K 11th edition is ending Crusade as we have known it. I expect that many players will continue using their 10th edition crusade books through the edition. Managing Crusade manually becomes painful fast. Administratum automates a huge amount of bookkeeping and will remain an important Crusade resource even during 11th edition.</p>
<p><strong>Free vs Paid:</strong> The free version gives you basic roster management, which for most will be perfectly fine. If you sign up for Goonhammer's Patreon Tier ($5/month) you get access to all campaign tools and features.</p>
<p><a href="https://administratum.goonhammer.com/" rel="noopener noreferrer">Visit Administratum</a></p>

<h3>17. Mundamanager</h3>
<p><strong>Best For:</strong> Necromunda campaign tracking.</p>
<p>Necromunda bookkeeping gets absurd quickly. This tool has seemingly replaced YakTribe (RIP, it was a great resource) and from my initial review it is a solid campaign tracker for Necromunda.</p>
<p><a href="https://www.mundamanager.com/" rel="noopener noreferrer">Visit Mundamanager</a></p>

<h2 id="utility-tools">Best General Warhammer Utility Tools</h2>

<h3>18. Google Sheets and Pages</h3>
<p><strong>Best For:</strong> Keeping track of your collection and data.</p>
<p>Microsoft Excel and Office is expensive and unless you are using it for business purposes it is probably not necessary. Google Sheets and Pages is a great free alternative to Microsoft Office, giving you the same features at no cost.</p>
<p>While this is not a typical Warhammer tool there are many good use cases such as collection tracking, logging your hobby sessions, and Crusade notes and management.</p>

<h3>19. BoardGameGeek</h3>
<p><strong>Best For:</strong> Warhammer board games, auctions, and forums.</p>
<p>The Warhammer Universe does not span just tabletop or video games but also board games. If you are interested in some spinoff Warhammer board games, this is the site to check out. Sometimes you can find auctions that include Warhammer products and forums talking about different editions of the game.</p>
<p>If you are interested in this side of the hobby, check out <a href="https://boardgamegeek.com/geeksearch.php?action=search&amp;q=Warhammer&amp;objecttype=boardgame" rel="noopener noreferrer">every Warhammer 40K board game ever released</a> with ratings and reviews.</p>
<p><a href="https://boardgamegeek.com/" rel="noopener noreferrer">Visit BoardGameGeek</a></p>

<h3>20. MiniCompare.info</h3>
<p><strong>Best For:</strong> Miniature size comparisons.</p>
<p>I was recently recommended this site and so far it has been very helpful for scaling proxies and helping with conversions I am working on for my Ork army. I do not think I will use it more than a few times a year, but it is a very useful niche tool that many hobbyists probably do not know about.</p>
<p><a href="https://minicompare.info/" rel="noopener noreferrer">Visit MiniCompare.info</a></p>

<h2>Also Consider Thrifthammer.com as a Free Resource</h2>

<p>Thrifthammer.com is a free price tracking tool for miniature kits across major online retailers. Our one goal is to save you as much money as possible for whatever game you enjoy playing.</p>

<p>We offer a growing roster of tools such as our core <a href="/products/">browser page</a> which shows the best discounts for models across a variety of game systems, and our <a href="/army-calculator/space-marines/">army cost calculator</a> for building the army list you want at the lowest possible cost.</p>

<p>If you sign up for a free account, Thrifthammer.com also offers the ability to keep track of your at-home mini collection and access to daily price alerts for your wishlisted models. We plan to keep expanding our tools and database to deliver the best prices and experience to our community.</p>

<div class="blog-video-wrap">
  <video controls playsinline preload="metadata" style="width:100%;border-radius:6px;display:block;" aria-label="ThriftHammer website walkthrough">
    <source src="/static/videos/thrifthammer-walkthrough.mp4" type="video/mp4">
  </video>
</div>

<h2>There Is a Tool for Everyone</h2>

<p>The best part about modern Warhammer is that the community has built an incredible ecosystem of free tools around the hobby to help with every pain point big or small.</p>

<p>At Thrifthammer.com we are elated to be part of this community of tools serving the community the best way we know how.</p>

<p>If I missed any great free Warhammer apps or websites, let me know. I am always looking for more hobby resources to test. Expect future articles revisiting each category of tools, giving you our hands-on analysis of the best tools in each category so you can find the best option for you.</p>

<p>If you are interested in keeping up with our blog or the best deals on miniatures, feel free to sign up for a free weekly newsletter below.</p>
"""


class Command(BaseCommand):
    """Publish the Free Tools Guide blog post if it is not already present."""

    help = 'Publishes The 20 Best Free Warhammer 40K Websites and Apps post (idempotent).'

    def add_arguments(self, parser):
        """Add optional --force flag to overwrite an existing post."""
        parser.add_argument(
            '--force',
            action='store_true',
            help='Overwrite the post body/meta even if it already exists.',
        )

    def handle(self, *args, **options):
        """Create or update the free tools guide post."""
        from blog.models import Post, Tag

        # Look up by canonical slug first; fall back to title in case the post
        # was created before the slug constant was set correctly.
        existing = (
            Post.objects.filter(slug=SLUG).first()
            or Post.objects.filter(title=TITLE).first()
        )

        if existing:
            # One-time slug correction: fix any auto-generated slug mismatch.
            if existing.slug != SLUG:
                self.stdout.write(self.style.WARNING(
                    f'  Correcting slug: {existing.slug!r} -> {SLUG!r}'
                ))
                existing.slug = SLUG
                existing.save(update_fields=['slug'])

            # Remove any duplicate posts created before the slug fix.
            duplicates = Post.objects.filter(title=TITLE).exclude(pk=existing.pk)
            dup_count = duplicates.count()
            if dup_count:
                dup_pks = list(duplicates.values_list('pk', flat=True))
                duplicates.delete()
                self.stdout.write(self.style.SUCCESS(
                    f'  Removed {dup_count} duplicate post(s) (PKs: {dup_pks}).'
                ))

            if not options['force']:
                self.stdout.write(
                    self.style.SUCCESS(f'Post already exists (pk={existing.pk}) — skipping.')
                )
                return

        defaults = dict(
            title=TITLE,
            slug=SLUG,
            excerpt=(
                'From army builders to crusade trackers, discover the 20 best free '
                'Warhammer 40K websites and apps. Our picks cover painting, list building, '
                'competitive play, lore, 3D printing, and more.'
            ),
            body=BODY,
            status=Post.STATUS_PUBLISHED,
            published_at=timezone.now(),
            meta_title='The 20 Best Free Warhammer 40K Websites and Apps (2026)',
            meta_description=(
                'Discover the 20 best free Warhammer 40K websites and apps. '
                'Army builders, crusade trackers, lore sites, STL resources, and more. '
                'All free, all tested.'
            ),
        )

        if existing:
            for attr, val in defaults.items():
                setattr(existing, attr, val)
            existing.save()
            post = existing
            self.stdout.write(
                self.style.SUCCESS(f'Updated existing post (pk={post.pk}, slug={post.slug}).')
            )
        else:
            post = Post(**defaults)
            post.save()
            self.stdout.write(
                self.style.SUCCESS(f'Created post (pk={post.pk}, slug={post.slug}).')
            )

        # Attach tags
        tag_names = ['Warhammer 40K', 'Free Tools', 'Hobby Resources', 'Beginner Guide']
        for name in tag_names:
            tag, _ = Tag.objects.get_or_create(name=name)
            post.tags.add(tag)
        self.stdout.write(self.style.SUCCESS(f'Tags attached: {tag_names}'))
