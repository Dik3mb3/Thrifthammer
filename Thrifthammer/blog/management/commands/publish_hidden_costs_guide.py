"""
Publish: The Hidden Costs of Warhammer 40K: What You Don't Expect and Eventually Pay For

Idempotent — safe to run repeatedly. Use --force to overwrite an existing post.
Also tags 'Best Starter Warhammer 40K Armies: 2026 Edition' as Beginner Guide.
"""

import datetime

from django.core.management.base import BaseCommand
from django.utils import timezone

from blog.models import Post, Tag

SLUG = 'hidden-costs-warhammer-40k'

BODY = """
<p class="post-intro">Getting started in Warhammer 40,000 is an exciting journey. You pick your
first faction, buy your first box, and battle your buddies with the models you spent hours
assembling and painting.</p>

<p>You look at the cost of the models you want, add in some hobby supplies, and expect that to be
the total cost of Warhammer 40K. Unfortunately, that is not how things play out. Warhammer 40K,
and Warhammer in general, is a long-term hobby that continues to ask you to open your wallet to
stay up to date. Whether you are a casual player or someone who enjoys competitive play, new costs
appear as you become more invested.</p>

<p>This guide breaks down hidden expenses that can catch both new and experienced players off guard.
If you are just starting out, our
<a href="/blog/best-starter-warhammer-40k-armies-2026/">Best Starter Warhammer 40K Armies: 2026 Edition</a>
guide is a great companion read to help you choose a faction that fits your budget.</p>

<nav class="post-toc">
  <strong>Jump to:</strong>
  <a href="#dice">Dice</a> &middot;
  <a href="#storage">Storage &amp; Transport</a> &middot;
  <a href="#terrain">Terrain</a> &middot;
  <a href="#edition-subscriptions">Edition Subscriptions</a> &middot;
  <a href="#gw-shenanigans">GW Shenanigans</a>
</nav>

<hr>

<h2 id="dice">Hidden Cost 1: Dice, Dice, and More Dice</h2>

<p>Warhammer 40K is a dice chucker of a game, with some armies rolling an absurd number of dice at
once. My personal favorite example is the classic twenty Ork Boyz with choppas led by a Warboss
rolling sixty or more dice in a single combat. In previous editions, certain units could roll close
to one hundred dice at one time.</p>

<p>You need a large number of six-sided dice to play Warhammer. You will use them for attacks,
wound tracking, command points, and sometimes even marking deployment zones. While starter sets
occasionally include dice, most players quickly realize they need far more.</p>

<p>If you buy official Games Workshop dice (please don&rsquo;t do it), you could easily be looking
at over one hundred dollars just for dice. That is ridiculous for something as simple as a cube
with six different numbers on it.</p>

<p>The better approach is to use dice from other games such as board games or tabletop RPGs, then
supplement them with bulk dice. Brands like
<a href="https://www.amazon.com/Chessex-Opaque-Black-Dice-Block/dp/B0011WOEQ2/" target="_blank" rel="noopener noreferrer sponsored">Chessex</a>
offer thirty-six dice for ten dollars. Buy two of these and you are set for most armies in the
game. This is the route I personally use and recommend to all players.</p>

<hr>

<h2 id="storage">Hidden Cost 2: Storage and Transport</h2>

<p>Now that you have a growing collection of models, dice, and hobby supplies, the next question
becomes where you store everything and how you transport it safely to games.</p>

<p>At home, storage can be simple. Cabinets, shelves, or spare boxes all work. Personally, I use
an old Ikea cabinet that I magnetized to store multiple armies. Each shelf is labeled, which helps
keep everything organized and easy to access.</p>

<p>If you do not have spare furniture or extra space,
<a href="https://www.amazon.com/Plastic-Storage-Modular-Stackable-Latching/dp/B06ZZ3XHBW/" target="_blank" rel="noopener noreferrer sponsored">plastic bins</a>
are another great option. Adding a metal sheet to the bottom and magnetizing your models creates a
simple storage solution that can fit in any corner of your home.</p>

<p>This type of storage can also double as transport for smaller elite armies such as Knights,
Custodes, or Grey Knights. Horde armies are another story. Bringing multiple bins quickly becomes
inconvenient and difficult to manage.</p>

<p>There are several dedicated transport options available if you need a more premium solution.
Foam cases remain a popular choice, although I am personally not a big fan. If you are considering
foam, companies like
<a href="https://us.battlefoam.com/warhammer-40-000/" target="_blank" rel="noopener noreferrer sponsored">Battlefoam</a>
offer a wide range of options designed for different army sizes. These cases can range from $50 to
$300, but they provide strong protection and peace of mind. Even as someone who prefers magnetized
storage, Battlefoam produces great quality products.</p>

<p>My personal favorite solution is the
<a href="https://tabletopstronghold.com/products/magcase-mdf-magnetic-carrying-case-display-case-for-miniatures-miniature-storage-designed-for-warhammer-40k-aos-dnd-and-more?variant=42844602532027" target="_blank" rel="noopener noreferrer sponsored">MagCase 2.0</a>,
which uses metal trays and magnets for storage. The case is sturdy, looks great, and is easy to
build. The main downside is weight, though carrying two thousand points of Orks is never going to
be light no matter what solution you choose.</p>

<p>There are also lesser-known brands that can often be found online at lower prices. These options
may lack some of the sturdiness of premium cases, but many players find them perfectly adequate.
Look at reviews, be careful, and you should be fine with any case you choose. I have used
<a href="https://www.amazon.com/WELIDAY-Miniatures-Storage-Transport-Aluminum/dp/B0DK6L83CJ/" target="_blank" rel="noopener noreferrer sponsored">this particular case</a>
myself and it is still going strong years later.</p>

<p>Storage and transport is one area where investing in quality can save you frustration in the
long run.</p>

<hr>

<h2 id="terrain">Hidden Cost 3: Terrain</h2>

<p>Terrain is essential for Warhammer 40K. Whether you are using spare boxes, plastic cups, or
fully painted buildings, the game relies on terrain to function properly.</p>

<p>I am not going to try to convince you to buy Games Workshop terrain or even third-party terrain
because I do not own a single piece of official terrain at home.</p>

<p><strong>Terrain is one of the biggest money traps in Warhammer 40K.</strong></p>

<p>Terrain often changes from edition to edition, meaning certain pieces become less useful over
time. It also takes up a massive amount of space, requires additional storage, and can be difficult
to transport. On top of that, terrain is a surprisingly sensitive topic. How much terrain is
enough? Who brings it? What type should be used? These questions can vary widely between local
groups.</p>

<p>My recommendation is to find a local gaming store and use their terrain. Most stores have a wide
range available, and you never have to worry about transporting or storing it yourself. If you
regularly play with friends, someone in the group often ends up owning terrain that everyone
uses.</p>

<p>If you are relying on friends for terrain, try to contribute in other ways. Offer to help paint
it, buy lunch after games, or pitch in financially to help expand the collection. Support your
local terrain friend so you don&rsquo;t have to spend the money and time to get your own set.</p>

<p>If you want to be the terrain person in your group, 3D printing is often the best place to
start. If that is not an option, third-party companies offer high-quality terrain at a fraction of
official pricing.</p>

<hr>

<h2 id="edition-subscriptions">Hidden Cost 4: Edition Subscriptions</h2>

<p>Every edition of Warhammer 40K introduces new materials that players often feel pressured to buy
to stay current. This typically includes:</p>

<ul>
  <li>Core rulebook</li>
  <li>Faction Codex</li>
  <li>Mission packs</li>
</ul>

<p>You can choose to ignore these releases, but Warhammer is an evolving game. Staying current is
often the only way to find consistent games in your area.</p>

<p>The costs for these are significant:</p>

<ul>
  <li><strong>Core Rulebook:</strong> $60</li>
  <li><strong>Codex:</strong> $50&ndash;$60</li>
  <li><strong>Mission Packs:</strong> $90 ($30 per pack; 3 per edition)</li>
</ul>

<p>Thanks to the amazing Warhammer 40K community, there are ways to reduce these costs. Online
resources like <a href="https://wahapedia.ru" target="_blank" rel="noopener noreferrer">Wahapedia</a>,
list building tools like <a href="https://www.newrecruit.eu" target="_blank" rel="noopener noreferrer">New Recruit</a>,
and YouTube make it easier than ever to stay informed without purchasing every release. I will
always recommend buying a core rulebook, especially if you are learning the game, and the mission
packs if your friends do not plan on buying them.</p>

<hr>

<h2 id="gw-shenanigans">Hidden Cost 5: Games Workshop Shenanigans</h2>

<p>Games Workshop makes decisions every edition that can have a real impact on your wallet. Veteran
players learn to expect this, but newer players can be surprised when parts of their army become
irrelevant or when new purchases become necessary.</p>

<h3>Legends</h3>

<p>Legends is a sensitive subject. Unsupported with questionable balance, Legend models are not
allowed in most tournaments, and even casual players may be hesitant to play against them. If a
portion of your army is put into Legends, you will need to replace it with non-Legends models to
play in tournaments and in certain local groups. Games Workshop&rsquo;s Legends selection is
arbitrary at times, leaving you holding a bag of models that are less playable in the new edition
than in the past.</p>

<h3>Balance</h3>

<p>Balance dataslates are great, and Games Workshop deserves credit for their dedication to
supporting game balance. However, your army is subject to the whims of Games Workshop, which can
leave your army in the bottom rungs of win rate. While all of us play this game for enjoyment, not
necessarily to win, it is no fun facing an uphill battle every time you bring out your army.</p>

<p>If you dedicate yourself to one army, it could be months or even years before your army is
competitive, or the units you love are good enough to play without being crushed. The balance
hammer Games Workshop doles out comes for all armies at some point. If you are a one-army player,
it can have an outsized impact on your enjoyment.</p>

<h3>Faction Expansion and Compression</h3>

<p>When your favorite faction gets compressed into another faction &mdash; cough, Harlequins
&mdash; it is a definite feels bad. Games Workshop promises support, but you are left with a
half-baked faction with rules that rarely change in an army you probably did not care to own in
the first place. Games Workshop has essentially forced you to invest in another faction without
your consent, and now you are looking to fill out your list with units that have real rules and
synergies.</p>

<p>On the other hand, faction expansion is treated with mostly applause. Everyone loves adding a
new faction into the game, right? Well, the cost of adding a new faction is something all
non-Space Marine armies feel over the next few years. Time, lore, and production that may have
gone to the army you own is now being split with another army.</p>

<p>This new army &mdash; cough, Emperor&rsquo;s Children &mdash; then comes out with limited
models, and Games Workshop is left with another half-baked faction they need to build out over
years. This can cause your army to feel ignored and support to dry up, leaving you with stale
units and rules that may push you toward buying another army or additional units to add variety to
your gameplay.</p>

<h3>Tricky Pricing</h3>

<p>Games Workshop is, most of the time, transparent with their pricing, telling you exactly what
you get when you buy. But Games Workshop can still be tricky on the margins.</p>

<p>Kill Team sets have become a fancy way to box refreshed basic troops for 40K behind higher than
normal pricing, then wait a few months to release them for 40K, hoping you buy them at the
premium. The Warhammer app is another example, with third-party choices like New Recruit often
being better for free or at a lower monthly charge. Space Marine Lieutenant number 387 is the same
model sold again with a slightly different look at increased pricing.</p>

<p>There are many pricing traps in Warhammer 40K that can make an army cost more than you
expect.</p>

<hr>

<h2>Final Thoughts</h2>

<p>At ThriftHammer, the goal is to help players find deals, save money, and help
<a href="/blog/tag/beginner-guide/">newer players</a>
navigate the hobby more effectively. Warhammer 40K can be an expensive hobby, but understanding
these hidden costs helps set expectations early.</p>

<p>If you are new to the hobby, starting slowly is highly recommended. Paint a single model, read
the lore, or watch battle reports before committing hundreds of dollars to an army. There is no
need to rush into building a full army immediately.</p>

<p>Warhammer 40K is a long-term hobby that evolves over time. Know your budget. Avoid FOMO. And
most importantly, <a href="/products/">stay on the hunt for the best deals</a>.</p>
"""


class Command(BaseCommand):
    """Publish the Hidden Costs of Warhammer 40K blog post."""

    help = 'Publish hidden costs guide and tag starter armies post as Beginner Guide.'

    def add_arguments(self, parser):
        """Add --force flag to overwrite existing post."""
        parser.add_argument(
            '--force', action='store_true',
            help='Overwrite the post if it already exists.',
        )

    def handle(self, *args, **options):
        """Create or update the post, then tag the starter armies post."""
        # ── Ensure Beginner Guide tag exists ────────────────────────────────
        beginner_tag, _ = Tag.objects.get_or_create(name='Beginner Guide')
        wh40k_tag,    _ = Tag.objects.get_or_create(name='Warhammer 40K')
        budget_tag,   _ = Tag.objects.get_or_create(name='Budget Tips')

        # ── Create / update the new post ─────────────────────────────────────
        existing = Post.objects.filter(slug=SLUG).first()

        if existing and not options['force']:
            self.stdout.write(self.style.WARNING(
                f'Post already exists (slug={SLUG!r}). Use --force to overwrite.'
            ))
        else:
            defaults = dict(
                title='The Hidden Costs of Warhammer 40K: What You Don\'t Expect and Eventually Pay For',
                slug=SLUG,
                excerpt=(
                    'Dice, terrain, rulebooks, and Games Workshop surprises: '
                    'the costs that catch new and experienced Warhammer 40K '
                    'players off guard, and how to manage them.'
                ),
                body=BODY,
                status=Post.STATUS_PUBLISHED,
                published_at=datetime.datetime(2026, 4, 12, 12, 0, 0,
                                               tzinfo=datetime.timezone.utc),
                meta_title='The Hidden Costs of Warhammer 40K | ThriftHammer',
                meta_description=(
                    'Discover the hidden costs in Warhammer 40K that surprise new '
                    'and experienced players, from dice and terrain to GW pricing '
                    'traps and edition subscriptions.'
                ),
                featured_image_url='',
                featured_image_alt='Hidden costs of Warhammer 40K hobby expenses breakdown',
            )

            if existing:
                for attr, val in defaults.items():
                    setattr(existing, attr, val)
                existing.save()
                post = existing
                self.stdout.write(self.style.SUCCESS(f'Updated: {SLUG!r}'))
            else:
                post = Post(**defaults)
                post.save()
                self.stdout.write(self.style.SUCCESS(f'Created: {SLUG!r}'))

            post.tags.add(beginner_tag, wh40k_tag, budget_tag)
            self.stdout.write('  Tags added: Beginner Guide, Warhammer 40K, Budget Tips')

        # ── Tag the starter armies post as Beginner Guide ────────────────────
        starter_post = Post.objects.filter(
            slug='best-starter-warhammer-40k-armies-2026'
        ).first()

        if starter_post:
            starter_post.tags.add(beginner_tag)
            self.stdout.write(self.style.SUCCESS(
                'Tagged "Best Starter Warhammer 40K Armies: 2026 Edition" as Beginner Guide'
            ))
        else:
            self.stdout.write(self.style.WARNING(
                'Starter armies post not found — skipping tag.'
            ))

        self.stdout.write(self.style.SUCCESS('\nDone.'))
