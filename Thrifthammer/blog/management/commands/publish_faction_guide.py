"""
Management command: publish_faction_guide

Creates the 'How to Choose Your Next Warhammer 40K Faction' blog post if it
does not already exist. Safe to run multiple times (idempotent).

Usage:
    python manage.py publish_faction_guide
    python manage.py publish_faction_guide --force  # overwrite existing post
"""

from django.core.management.base import BaseCommand
from django.utils import timezone

SLUG = 'how-to-choose-warhammer-40k-faction'

BODY = """\
<p class="post-lead">Choosing your next Warhammer 40K faction is one of the biggest decisions in the hobby.</p>

<p>Your army choice determines:</p>
<ul>
  <li>How much you spend</li>
  <li>How many models you paint</li>
  <li>Your playstyle on the tabletop</li>
  <li>How competitive you can be</li>
  <li>How much you enjoy the hobby long-term</li>
</ul>

<p>With 30+ Warhammer 40K factions, choosing the right one can feel overwhelming. Many players end up picking an army that looks cool, only to realize it is expensive, not their playstyle, or requires too much hobby time to fit their schedule.</p>

<p>This guide breaks down the 5 most important factors when choosing your next Warhammer 40K army, ranked by importance.</p>

<h2>The 5 Most Important Factors When Choosing a Warhammer 40K Faction</h2>

<p><strong>Ranked by Importance:</strong></p>
<ol>
  <li>Cost (Most Important)</li>
  <li>Playstyle</li>
  <li>Cool Factor</li>
  <li>Hobby Requirements</li>
  <li>Competitiveness</li>
</ol>

<p>Let us break them down.</p>

<h2>1. Cost</h2>

<p>Warhammer 40K is an expensive hobby, and some armies cost 2 to 3 times more than others.</p>

<p>For example:</p>
<ul>
  <li>Elite armies like <a href="/factions/adeptus-custodes/">Adeptus Custodes</a> can routinely be built for $300 to $600 for 2000 points</li>
  <li>Horde armies like <a href="/factions/astra-militarum/">Imperial Guard</a>, <a href="/factions/genestealer-cults/">Genestealer Cults</a>, and <a href="/factions/adeptus-mechanicus/">Adeptus Mechanicus</a> can easily exceed $1,000 for the same army size</li>
</ul>

<p><strong>What impacts army cost the most? Model count.</strong></p>

<p>More Models = More Money. The more models you field on the table, the bigger your budget needs to be. Understand your budget constraints before going down the rabbit hole of horde armies.</p>

<h3>Cost Categories (General Guide)</h3>

<p><strong>Cheapest 40K Armies</strong></p>
<ul>
  <li><a href="/factions/adeptus-custodes/">Adeptus Custodes</a></li>
  <li><a href="/factions/grey-knights/">Grey Knights</a></li>
</ul>

<p><strong>Mid-Range Cost Armies</strong></p>
<ul>
  <li><a href="/factions/space-marines/">Space Marines</a></li>
  <li><a href="/factions/chaos-space-marines/">Chaos Space Marines</a></li>
  <li><a href="/factions/necrons/">Necrons</a></li>
  <li><a href="/factions/death-guard/">Death Guard</a></li>
  <li><a href="/factions/thousand-sons/">Thousand Sons</a></li>
</ul>

<p><strong>Most Expensive Armies</strong></p>
<ul>
  <li><a href="/factions/orks/">Orks</a></li>
  <li><a href="/factions/astra-militarum/">Imperial Guard</a></li>
  <li><a href="/factions/genestealer-cults/">Genestealer Cults</a></li>
  <li><a href="/factions/adeptus-mechanicus/">Adeptus Mechanicus</a></li>
</ul>

<p><strong>ThriftHammer Tip:</strong> Elite armies often offer the best value overall and are usually the cheapest way to get started in Warhammer 40K. Use our <a href="/products/">price comparison tool</a> to see exactly what each faction costs before committing.</p>

<h2>2. Playstyle (How You Actually Play the Game)</h2>

<p>Every Warhammer 40K faction plays differently, yet many armies share similar play patterns and fall into established archetypes.</p>

<p>Some armies:</p>
<ul>
  <li>Are shooting focused</li>
  <li>Are melee focused</li>
  <li>Focus on objective control and mission play</li>
  <li>Overwhelm with numbers</li>
  <li>Use elite powerful units</li>
</ul>

<p>Choosing a playstyle you enjoy is critical.</p>

<p>Personal anecdote: My first Warhammer 40K army was <a href="/factions/drukhari/">Drukhari</a>, chosen solely because of how cool they looked and their pirate-style ships (I love the pirate theme). However, I did not research their playstyle enough. After a few games, I realized I did not enjoy the glass-cannon playstyle. Months of hobbying down the drain that could have easily been prevented with a bit of research.</p>

<h3>Common 40K Playstyles</h3>

<p><strong>Shooting Focus</strong></p>
<ul>
  <li><a href="/factions/tau-empire/">T'au Empire</a></li>
  <li><a href="/factions/astra-militarum/">Imperial Guard</a></li>
  <li><a href="/factions/adeptus-mechanicus/">Adeptus Mechanicus</a></li>
</ul>

<p><strong>Melee Focus</strong></p>
<ul>
  <li><a href="/factions/world-eaters/">World Eaters</a></li>
  <li><a href="/factions/orks/">Orks</a></li>
  <li><a href="/factions/adeptus-custodes/">Adeptus Custodes</a></li>
</ul>

<p><strong>Objective Control / Mission Play</strong></p>
<ul>
  <li><a href="/factions/astra-militarum/">Imperial Guard</a></li>
  <li><a href="/factions/adeptus-mechanicus/">Adeptus Mechanicus</a></li>
  <li><a href="/factions/genestealer-cults/">Genestealer Cults</a></li>
</ul>

<p><strong>Balanced, All-Rounders</strong></p>
<ul>
  <li><a href="/factions/space-marines/">Space Marines</a></li>
  <li><a href="/factions/sisters-of-battle/">Sisters of Battle</a></li>
  <li><a href="/factions/leagues-of-votann/">Leagues of Votann</a></li>
</ul>

<p><strong>Movement Focus / Tricksy</strong></p>
<ul>
  <li><a href="/factions/aeldari/">Aeldari</a></li>
  <li><a href="/factions/drukhari/">Drukhari</a></li>
  <li><a href="/factions/grey-knights/">Grey Knights</a></li>
</ul>

<h2>3. Cool Factor (Rule of Cool Still Matters)</h2>

<p>This is often called the Rule of Cool, and for many players it is the number one rule. ThriftHammer disagrees, but it is still massively important when selecting your next army.</p>

<p>Selecting an army you love aesthetically and from a lore perspective is important because you are going to:</p>
<ul>
  <li>Paint and assemble these models</li>
  <li>Play them for years</li>
  <li>Build your collection over time</li>
</ul>

<p>If you do not love the army, you may lose motivation over time. I cannot tell you what you will think is cool, but you will know when you see it.</p>

<h2>4. Hobby Requirements</h2>

<p>This is often overlooked but extremely important. Some armies require:</p>
<ul>
  <li>100+ models</li>
  <li>Complex painting (Chaos trim is a significant challenge)</li>
  <li>Kitbashing and conversions</li>
</ul>

<p>Others are much easier, with classic color schemes that are achievable even for brand new painters.</p>

<h3>Easy Hobby Armies</h3>
<ul>
  <li><a href="/factions/adeptus-custodes/">Adeptus Custodes</a></li>
  <li><a href="/factions/imperial-knights/">Imperial Knights</a></li>
  <li><a href="/factions/space-marines/">Space Marines</a></li>
  <li><a href="/factions/necrons/">Necrons</a></li>
  <li><a href="/factions/grey-knights/">Grey Knights</a></li>
</ul>

<p>Why? These armies typically have low model counts, simple color schemes, and a large amount of painting tutorials online to guide you through the process.</p>

<h3>Hard Hobby Armies</h3>
<ul>
  <li><a href="/factions/orks/">Orks</a></li>
  <li><a href="/factions/genestealer-cults/">Genestealer Cults</a></li>
  <li><a href="/factions/astra-militarum/">Imperial Guard</a></li>
  <li><a href="/factions/adeptus-mechanicus/">Adeptus Mechanicus</a></li>
  <li>Most Chaos armies</li>
</ul>

<h2>5. Competitiveness</h2>

<p>The Warhammer 40K meta constantly changes. The best army today might be the weakest next year.</p>

<p>However, it is important that your faction feels competitive regardless of win rates. No one enjoys being crushed game after game. Feeling like you have no chance to win can often lead players to drop out of the hobby entirely.</p>

<p>The good news: Games Workshop has done an admirable job keeping factions within roughly 45% to 55% win rates during 10th Edition, making competitiveness less of a concern over time.</p>

<h3>Historically Strong Factions Across Editions</h3>
<ul>
  <li><a href="/factions/space-marines/">Space Marines</a></li>
  <li><a href="/factions/aeldari/">Aeldari</a></li>
  <li><a href="/factions/necrons/">Necrons</a></li>
</ul>

<p><strong>Important:</strong> Do not choose an army only because it is strong right now. Consider the core faction rules, internal detachment balance, and your local meta. This will help determine whether the army you are choosing is viable long-term.</p>

<h2>Best Warhammer 40K Armies for Beginners (2026)</h2>

<ul>
  <li><strong>Best Overall:</strong> <a href="/factions/space-marines/">Space Marines</a></li>
  <li><strong>Best Budget Army:</strong> <a href="/factions/adeptus-custodes/">Adeptus Custodes</a></li>
  <li><strong>Easiest to Paint:</strong> <a href="/factions/necrons/">Necrons</a> / <a href="/factions/grey-knights/">Grey Knights</a></li>
  <li><strong>Most Fun:</strong> <a href="/factions/orks/">Orks</a> (my personal bias)</li>
  <li><strong>Most Competitive:</strong> <a href="/factions/aeldari/">Aeldari</a></li>
</ul>

<h2>Once You Choose Your Army</h2>

<p>Before buying, check:</p>
<ul>
  <li><a href="/army-calculator/">Combat Patrol and Combo box deals</a> (our Army Calculator tracks points and cost for every Combat Patrol box)</li>
  <li>Starter box value — the 11th Edition Starter Box will likely be the best deal if you are interested in <a href="/factions/space-marines/">Space Marines</a> or <a href="/factions/orks/">Orks</a></li>
  <li>Points per dollar</li>
</ul>

<p>Visit <a href="/products/">ThriftHammer</a> to compare prices across all major US retailers before committing to your next army. If you want to plan your full army budget in advance, our free <a href="/army-calculator/">Army Cost Calculator</a> lets you build a complete roster and see real retailer prices side by side.</p>
"""


class Command(BaseCommand):
    """Publish the Faction Guide blog post if it is not already present."""

    help = 'Publishes the How to Choose Your Warhammer 40K Faction guide post (idempotent).'

    def add_arguments(self, parser):
        """Add optional --force flag to overwrite an existing post."""
        parser.add_argument(
            '--force',
            action='store_true',
            help='Overwrite the post body/meta even if it already exists.',
        )

    def handle(self, *args, **options):
        """Create or update the faction guide post."""
        from blog.models import Post, Tag

        existing = Post.objects.filter(slug=SLUG).first()

        if existing and not options['force']:
            self.stdout.write(
                self.style.SUCCESS(f'Post already exists (pk={existing.pk}) — skipping.')
            )
            return

        defaults = dict(
            title='How to Choose Your Next Warhammer 40K Faction (Complete 2026 Guide)',
            excerpt=(
                'Choosing the right Warhammer 40K faction is one of the most important '
                'decisions in the hobby. This guide ranks the 5 key factors — cost, '
                'playstyle, cool factor, hobby requirements, and competitiveness — '
                'so you pick the right army the first time.'
            ),
            body=BODY,
            status=Post.STATUS_PUBLISHED,
            published_at=timezone.now(),
            meta_title='How to Choose a Warhammer 40K Faction (Complete 2026 Guide)',
            meta_description=(
                'Choosing a Warhammer 40K faction? This guide ranks the 5 most important '
                'factors: cost, playstyle, cool factor, hobby requirements, and '
                'competitiveness. Find the right army for you.'
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
        tag_names = ['Warhammer 40K', 'Faction Guide', 'Beginner Tips', 'Beginner Guide']
        for name in tag_names:
            tag, _ = Tag.objects.get_or_create(name=name)
            post.tags.add(tag)
        self.stdout.write(self.style.SUCCESS(f'Tags attached: {tag_names}'))
