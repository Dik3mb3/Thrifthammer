"""
Management command: publish_11th_edition_battleforce_ranking

Creates the 'Warhammer 40K Battleforce Boxes 11th Edition Ranked' blog post.
Safe to run multiple times (idempotent).

Usage:
    python manage.py publish_11th_edition_battleforce_ranking
    python manage.py publish_11th_edition_battleforce_ranking --force
"""

from django.core.management.base import BaseCommand
from django.utils import timezone

SLUG = 'warhammer-40k-battleforce-boxes-11th-edition-ranked'

BODY = """\
<p class="post-lead">New edition, new Battleforce boxes. Like clockwork, Games Workshop is releasing its first wave of discount boxes to take advantage of the 11th Edition hype train.</p>

<p>Games Workshop recently announced four new Warhammer 40K Battleforces featuring <a href="/products/?category=warhammer-40000&amp;faction=astra-militarum">Astra Militarum</a>, <a href="/products/?category=warhammer-40000&amp;faction=tyranids">Tyranids</a>, <a href="/products/?category=warhammer-40000&amp;faction=chaos-space-marines">Chaos Space Marines</a>, and <a href="/products/?category=warhammer-40000&amp;faction=necrons">Necrons</a>.</p>

<p>Today we answer the age old Games Workshop question: are these boxes worth the expected $250+ price tag?</p>

<p>I compared each box based on total points, discount versus Games Workshop pricing, discount versus online retail, and the content quality of the box.</p>

<h2>11th Edition Battleforce Ranking</h2>

<p>Let's start with an overall ranking before we explore each one individually.</p>

<!-- ── BATTLEFORCE RANKING TABLE ─────────────────────────────────────────── -->
<style>
#bf-rank-wrap {
  overflow-x: auto;
  margin: var(--sp-6, 1.5rem) 0;
  width: fit-content;
  max-width: 100%;
}
#bf-rank-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.88rem;
  background: var(--bg-card, #1a1b1c);
  border: 1px solid var(--border-subtle, rgba(255,255,255,0.08));
  border-radius: 6px;
  overflow: hidden;
}
#bf-rank-table thead th {
  background: #9a6e10;
  color: #fff;
  padding: 0.6rem 0.75rem;
  text-align: left;
  font-size: 0.78rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  white-space: nowrap;
  border-bottom: 2px solid var(--border-subtle, rgba(255,255,255,0.12));
}
#bf-rank-table tbody tr {
  border-bottom: 1px solid var(--border-subtle, rgba(255,255,255,0.06));
  transition: background 0.1s;
}
#bf-rank-table tbody tr:last-child {
  border-bottom: none;
}
#bf-rank-table tbody tr:nth-child(even) {
  background: rgba(255,255,255,0.03);
}
#bf-rank-table tbody tr:hover {
  background: rgba(200,146,26,0.08);
}
#bf-rank-table td {
  padding: 0.55rem 0.75rem;
  vertical-align: middle;
  color: var(--text-primary, #e8e8e8);
}
.bf-rank {
  font-weight: 700;
  font-size: 0.9rem;
  display: inline-block;
  width: 2rem;
  text-align: center;
}
.bf-rank-gold   { color: #c8921a; }
.bf-rank-silver { color: #a0a0a0; }
.bf-rank-bronze { color: #a0522d; }
.bf-rank-low    { color: var(--text-muted, #777); }
#bf-rank-table td a {
  color: var(--accent-gold-lt, #d4a832);
  text-decoration: none;
  font-weight: 600;
}
#bf-rank-table td a:hover {
  text-decoration: underline;
}
.bf-num { text-align: center; }
.bf-good { color: #4aab72; font-weight: 600; }
.bf-ok   { color: var(--text-primary, #e8e8e8); }
.bf-low  { color: #c8922a; font-weight: 600; }
.bf-bad  { color: #d44040; font-weight: 600; }
</style>

<div id="bf-rank-wrap">
  <table id="bf-rank-table">
    <thead>
      <tr>
        <th>Rank</th>
        <th>Battleforce</th>
        <th>Points</th>
        <th>GW Discount</th>
        <th>Retail Discount</th>
        <th>Points / Dollar</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td><span class="bf-rank bf-rank-gold">#1</span></td>
        <td><a href="/products/?category=warhammer-40000&amp;faction=astra-militarum">Astra Militarum</a></td>
        <td class="bf-num bf-ok">635</td>
        <td class="bf-num bf-good">32%</td>
        <td class="bf-num bf-good">20%</td>
        <td class="bf-num bf-ok">2.5</td>
      </tr>
      <tr>
        <td><span class="bf-rank bf-rank-silver">#2</span></td>
        <td><a href="/products/?category=warhammer-40000&amp;faction=chaos-space-marines">Chaos Space Marines</a></td>
        <td class="bf-num bf-good">700</td>
        <td class="bf-num bf-low">25%</td>
        <td class="bf-num bf-low">15%</td>
        <td class="bf-num bf-good">2.7</td>
      </tr>
      <tr>
        <td><span class="bf-rank bf-rank-bronze">#3</span></td>
        <td><a href="/products/?category=warhammer-40000&amp;faction=necrons">Necrons</a></td>
        <td class="bf-num bf-ok">585</td>
        <td class="bf-num bf-ok">26%</td>
        <td class="bf-num bf-ok">17%</td>
        <td class="bf-num bf-low">2.3</td>
      </tr>
      <tr>
        <td><span class="bf-rank bf-rank-low">#4</span></td>
        <td><a href="/products/?category=warhammer-40000&amp;faction=tyranids">Tyranids</a></td>
        <td class="bf-num bf-bad">535</td>
        <td class="bf-num bf-bad">24%</td>
        <td class="bf-num bf-bad">11%</td>
        <td class="bf-num bf-bad">2.1</td>
      </tr>
    </tbody>
  </table>
</div>
<p style="font-size:0.72rem;color:var(--text-muted);margin-top:0.25rem;font-style:italic;">GW Discount: savings vs Games Workshop MSRP &nbsp;&middot;&nbsp; Retail Discount: savings vs online retailers &nbsp;&middot;&nbsp; Points / Dollar: 11th Edition points per dollar spent</p>

<p>I am going to spoil part of the review: only the top two, the <a href="/products/?category=warhammer-40000&amp;faction=astra-militarum">Astra Militarum</a> Platoon and <a href="/products/?category=warhammer-40000&amp;faction=chaos-space-marines">Chaos Space Marines</a> Warband, are worth your time and money.</p>

<p>But stick around for an individual review of each box's contents and our rationale for why you should or shouldn't consider them for purchase.</p>

<h2>Astra Militarum Battleforce Review</h2>

<h3>Value at a Glance</h3>

<ul>
  <li>635 Points</li>
  <li>32% Discount vs Games Workshop</li>
  <li>20% Discount vs Retail</li>
  <li>2.5 Points Per Dollar</li>
</ul>

<h3>Contents</h3>

<ul>
  <li><a href="/products/astra-militarum-rogal-dorn-battle-tank/">Rogal Dorn Battle Tank</a></li>
  <li><a href="/products/astra-militarum-basilisk/">Basilisk</a></li>
  <li><a href="/products/astra-militarum-field-ordnance-battery/">Field Ordnance Battery</a></li>
  <li><a href="/products/astra-militarum-cadian-command-squad/">Cadian Command Squad</a></li>
  <li><a href="/products/astra-militarum-cadian-shock-troops/">Cadian Shock Troops</a></li>
  <li><a href="/products/astra-militarum-commissar/">Commissar</a></li>
</ul>

<h3>My Thoughts</h3>

<p>This is my favorite of the four Battleforces.</p>

<p>The <a href="/products/astra-militarum-rogal-dorn-battle-tank/">Rogal Dorn</a> is exactly the type of model I want to see in a discount box. It is a large centerpiece kit, looks great on the table, and is a joy to paint and hobby.</p>

<p>The rest of the box is very solid and supports a classic combined-arms Guard army. Combined arms is one of the most popular archetypes for Guard and will appeal to both new and existing players and hobbyists. You get the full package: infantry, artillery, a tank commander, and a heavy battle tank.</p>

<p>The weak point of this box is the inclusion of a <a href="/products/astra-militarum-commissar/">Commissar</a>. Like many Games Workshop characters, it inflates the box value more than it adds to the army itself. Many Guard players already have one, and there are countless kitbashes and third-party alternatives available. A 30-point upscaled Guardsman does not scream $40 kit, and adding it here is very dubious and inflates that 32% discount.</p>

<p>It is also worth pointing out that the <a href="/products/astra-militarum-basilisk/">Basilisk</a> is an old 40K kit that may not appeal to you. It has not been particularly playable on the tabletop over the last few years. This kit may be updated sooner rather than later, so you may be investing in old stock. If this bothers you, this is a major strike against buying this box.</p>

<p>This box is easy to recommend for new <a href="/products/?category=warhammer-40000&amp;faction=astra-militarum">Guard</a> players. Existing Guard collectors may find less use for it. Many Guard players I know already own 100 Cadian bodies and 3 Rogal Dorns. If you are looking into Guard, this is a pretty solid discount and entry point into all the different aspects of the faction.</p>

<h2>Chaos Space Marines Battleforce Review</h2>

<h3>Value at a Glance</h3>

<ul>
  <li>700 Points</li>
  <li>25% Discount vs Games Workshop</li>
  <li>15% Discount vs Retail</li>
  <li>2.7 Points Per Dollar</li>
</ul>

<h3>Contents</h3>

<ul>
  <li><a href="/products/chaos-space-marine-lord-discordant-on-helstalker/">Lord Discordant</a></li>
  <li><a href="/products/chaos-space-marine-venomcrawler-and-obliterators/">Venomcrawler</a></li>
  <li><a href="/products/chaos-space-marine-venomcrawler-and-obliterators/">Obliterators</a></li>
  <li>10 <a href="/products/chaos-space-marines-legionaries/">Legionaries</a></li>
  <li>20 <a href="/products/chaos-space-marine-chaos-cultists/">Cultists</a></li>
</ul>

<h3>My Thoughts</h3>

<p>The <a href="/products/?category=warhammer-40000&amp;faction=chaos-space-marines">Chaos Space Marines</a> Warband Battleforce is a clear second place, basically by default. Seven hundred points in a box is really good and allows a new player to get tabletop-ready in no time.</p>

<p>What holds it back from first place is that we have seen this box before. Players who picked up the 2025 Christmas Battleforce are going to experience some serious deja vu. The box is almost identical; however, instead of 20 Cultists, you got 5 Havocs and a Chaos Rhino. In my opinion, that box was just better.</p>

<p>Including 20 Cultists is a very questionable choice by Games Workshop. New players to the faction will appreciate them, as Cultists are an important part of the army. Veteran <a href="/products/?category=warhammer-40000&amp;faction=chaos-space-marines">Chaos Space Marines</a> players probably have enough <a href="/products/chaos-space-marine-chaos-cultists/">Cultists</a> to last a lifetime. Games Workshop could have easily replaced 10 of those <a href="/products/chaos-space-marine-chaos-cultists/">Cultists</a> with something else more appealing for existing <a href="/products/?category=warhammer-40000&amp;faction=chaos-space-marines">Chaos Space Marine</a> players.</p>

<p>Still, all the models in the box are useful, and the sculpts are great quality. Grab this box if you can't grab the 2025 Christmas Battleforce and do not own a ton of <a href="/products/chaos-space-marine-chaos-cultists/">Cultists</a> already.</p>

<h2>Necrons Battleforce Review</h2>

<h3>Value at a Glance</h3>

<ul>
  <li>585 Points</li>
  <li>26% Discount vs Games Workshop</li>
  <li>17% Discount vs Retail</li>
  <li>2.3 Points Per Dollar</li>
</ul>

<h3>Contents</h3>

<ul>
  <li><a href="/products/necron-catacomb-command-barge/">Command Barge / Annihilation Barge</a></li>
  <li><a href="/products/necron-canoptek-doomstalker/">Canoptek Doomstalker</a></li>
  <li><a href="/products/necron-flayed-ones/">Flayed Ones</a></li>
  <li><a href="/products/necron-ophydian-destroyers/">Ophydian Destroyers</a></li>
  <li>20 <a href="/products/necron-warriors/">Necron Warriors</a></li>
</ul>

<h3>My Thoughts</h3>

<p>This box is very disappointing and a non-starter in my humble opinion.</p>

<p>The highlight is the <a href="/products/necron-ophydian-destroyers/">Ophydian Destroyers</a>. Their inclusion gives existing <a href="/products/?category=warhammer-40000&amp;faction=necrons">Necron</a> players something different that may be a value for their collection. Unfortunately, the same cannot be said for the <a href="/products/necron-warriors/">Warriors</a> and <a href="/products/necron-flayed-ones/">Flayed Ones</a>. Both kits have appeared in so many Necron bundles over the years that they have lost most of their appeal. The <a href="/products/necron-flayed-ones/">Flayed Ones</a> kit is one of the worst Warhammer 40K kits I have ever purchased. While I do like the aesthetic, the kit is painful to put together, and the spindly bits are prone to breaking and getting caught on other models.</p>

<p>The discount is respectable, but there is nothing here that makes me excited. The lack of a centerpiece model is the most disappointing part. We had a Battleforce last year that came with a whole C'tan! The best Games Workshop could do is a <a href="/products/necron-catacomb-command-barge/">Command Barge</a>? You can pass on this one.</p>

<h2>Tyranids Battleforce Review</h2>

<h3>Value at a Glance</h3>

<ul>
  <li>535 Points</li>
  <li>24% Discount vs Games Workshop</li>
  <li>11% Discount vs Retail</li>
  <li>2.1 Points Per Dollar</li>
</ul>

<h3>Contents</h3>

<ul>
  <li><a href="/products/tyranid-hive-tyrant/">Hive Tyrant</a> / <a href="/products/tyranid-the-swarmlord/">Swarmlord</a></li>
  <li><a href="/products/tyranid-warriors/">Tyranid Warriors</a></li>
  <li><a href="/products/tyranid-lictor/">Lictor</a></li>
  <li><a href="/products/tyranid-von-ryans-leapers/">Von Ryan's Leapers</a></li>
  <li><a href="/products/tyranid-hormagaunts/">Hormagaunts</a></li>
  <li><a href="/products/tyranid-termagants/">Termagants</a></li>
</ul>

<h3>My Thoughts</h3>

<p>This is the only Battleforce I would classify as a strong non-recommendation.</p>

<p>The models in the box are great. <a href="/products/?category=warhammer-40000&amp;faction=tyranids">Tyranid</a> models are some of the coolest across the entire game. Most of them are perfectly usable in-game, especially with the release of the faction's new detachments. <a href="/products/tyranid-warriors/">Tyranid Warrior</a> stocks are up after a dreadful 10th Edition!</p>

<p>The problem is that eBay and other marketplaces are still flooded with Tyranid models from the Leviathan 10th Edition Starter Box. <a href="/products/tyranid-termagants/">Termagants</a> and <a href="/products/tyranid-von-ryans-leapers/">Von Ryan's Leapers</a> can often be found for $20-$30 on eBay if you're willing to buy loose sprues. If you're patient and a shrewd shopper, you can find these kits and sprues individually for less than the price of the Battleforce box.</p>

<p>If this box came out 2-3 years from now, I would rank it higher. In a world where I couldn't find cheaper Leviathan versions of these kits, this might be decent value. This seems like bad timing from Games Workshop. I suspect they had too much unsold stock of these kits and saw this Battleforce as a way to liquidate 10th Edition stock.</p>

<p><a href="/products/?category=warhammer-40000&amp;faction=tyranids">Tyranid</a> players should resist purchasing this and hunt down the last remaining Leviathan stock before prices rise.</p>

<h2>Final Ranking</h2>

<ol>
  <li><a href="/products/?category=warhammer-40000&amp;faction=astra-militarum">Astra Militarum</a> Battleforce</li>
  <li><a href="/products/?category=warhammer-40000&amp;faction=chaos-space-marines">Chaos Space Marines</a> Battleforce</li>
  <li><a href="/products/?category=warhammer-40000&amp;faction=necrons">Necrons</a> Battleforce</li>
  <li><a href="/products/?category=warhammer-40000&amp;faction=tyranids">Tyranids</a> Battleforce</li>
</ol>

<p>None of these four boxes are phenomenal. They all have their weak points and seem to be imitations of previously launched Battleforce boxes that were, in many cases, better. Maybe Christmas will bring more creative and better-value Battleforce boxes.</p>

<p>Unless one of these boxes speaks to you, be patient. You will have many opportunities to grab discount boxes throughout the edition, just like the <a href="/blog/warhammer-40k-armageddon-11th-edition-box-contents-revealed/">11th Edition Armageddon box</a>, which is a really great starter set, especially if you share the cost with a friend.</p>

<p>If you are interested, here is our full review: <a href="/blog/warhammer-40k-armageddon-11th-edition-box-contents-revealed/">Warhammer 40K Armageddon 11th Edition Box Contents Revealed</a>.</p>
"""


class Command(BaseCommand):
    """Publish the 11th Edition Battleforce ranking post (idempotent)."""

    help = 'Publishes the Warhammer 40K Battleforce Boxes 11th Edition Ranked post.'

    def add_arguments(self, parser):
        """Register CLI arguments."""
        parser.add_argument(
            '--force',
            action='store_true',
            help='Overwrite the post body/meta even if it already exists.',
        )

    def handle(self, *args, **options):
        """Create or update the blog post."""
        from blog.models import Post, Tag

        existing = Post.objects.filter(slug=SLUG).first()

        if existing and not options['force']:
            self.stdout.write(
                self.style.SUCCESS(f'Post already exists (pk={existing.pk}) -- skipping.')
            )
            return

        defaults = dict(
            slug=SLUG,
            title='Warhammer 40K Battleforce Boxes 11th Edition Ranked',
            excerpt=(
                'We ranked all four 11th Edition Warhammer 40K Battleforce boxes by points, '
                'discount, and value. Only two of the four are worth your time and money. '
                'Here is our full breakdown.'
            ),
            body=BODY,
            status=Post.STATUS_PUBLISHED,
            published_at=timezone.now(),
            meta_title='Warhammer 40K 11th Edition Battleforces: Are They Worth It?',
            meta_description=(
                'We ranked all four 11th Edition Warhammer 40K Battleforce boxes by points, '
                'discount, and value. Only two are worth buying. Find out which ones make the cut.'
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

        tag_names = ['Warhammer 40K', 'New Releases', 'Pricing', 'Astra Militarum', 'Chaos Space Marines', 'Necrons', 'Tyranids']
        for name in tag_names:
            tag, _ = Tag.objects.get_or_create(name=name)
            post.tags.add(tag)
        self.stdout.write(self.style.SUCCESS(f'Tags attached: {tag_names}'))
