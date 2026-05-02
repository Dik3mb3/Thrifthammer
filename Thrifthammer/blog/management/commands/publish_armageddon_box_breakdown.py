"""
Management command: publish_armageddon_box_breakdown

Creates the 'Warhammer 40K Armageddon 11th Edition Box Contents Revealed'
blog post. Safe to run multiple times (idempotent).

Usage:
    python manage.py publish_armageddon_box_breakdown
    python manage.py publish_armageddon_box_breakdown --force  # overwrite existing
"""

from django.core.management.base import BaseCommand
from django.utils import timezone

SLUG = 'warhammer-40k-armageddon-11th-edition-box-contents-revealed'

BODY = """\
<p>If you're not aware, the Warhammer 40K 11th Edition launch box contents were revealed today, and I wanted to put together a quick breakdown for anyone who missed it. I will offer my own two cents on the box, what is exciting, and what is not.</p>

<p>So here is a quick look at the 11th Edition Armageddon box contents, estimated points, possible retail price, and whether it looks worth it for Warhammer 40K players.</p>

<p><strong>Important note:</strong> These are estimates based on today's points values. Some of the new models do not have confirmed points yet, so I used similar units, older Legends profiles, or reasonable guesses.</p>

<h2>11th Edition Box Contents Overview</h2>

<h3>Total Estimated Box Value</h3>

<ul>
  <li>61 total models</li>
  <li>Estimated 1,470 points at current values</li>
  <li>Likely closer to 1,700 points after 11th Edition points changes (15% increase to today's points)</li>
  <li>Includes rulebook, cards, and bonus content</li>
</ul>

<p>There is a good amount of models and 40K content in the box, but the real debate is whether the points-per-dollar value will hold up compared to previous edition launch sets.</p>

<h2>Ork Half Breakdown</h2>

<p><strong>Orks: 38 Models, Estimated 750 Points</strong></p>

<ul>
  <li>10x Gretchin: 40 pts</li>
  <li>20x Boyz: 160 pts</li>
  <li>1x Warboss: 75 pts</li>
  <li>1x Painboy: 80 pts</li>
  <li>1x Weirdboy: 65 pts</li>
  <li>1x Ork Big Boss (new lieutenant-style character): est. 70 pts</li>
  <li>1x Bannerboy (new support character): est. 70 pts</li>
  <li>1x Wartraxx (new buggy/bike-style model): est. 60 pts</li>
  <li>1x Dakkarig (new walker model): est. 130 pts</li>
</ul>

<h3>My Take on the Ork Side</h3>

<p>I love the Ork half. The new models all look fun, are full of character, and are exactly what Ork players usually want from a launch set. The Ork half is a nice mixture of core elements of the army alongside new flashy models that both newer and existing Ork players want.</p>

<p>The Painboy is probably my least favorite sculpt, but even then, the little grot orderly is pretty awesome. I still prefer the older Painboy model personally, but it is not a deal breaker. The rest of the sculpts are great, especially the Dakkarig, which I will buy multiples of immediately when it comes out as a separate kit.</p>

<p>From a gameplay standpoint, almost 800 points for a horde army starter force is not bad at all. You get infantry, characters, and the support pieces you need to start krumpin Space Marines. For me, the Ork half carries this box.</p>

<h2>Space Marine Half Breakdown</h2>

<p><strong>Space Marines: 23 Models, Estimated 720 Points</strong></p>

<ul>
  <li>10x Intercessors: 160 pts</li>
  <li>3x Eradicators: 90 pts</li>
  <li>5x Vanguard Veterans: 100 pts</li>
  <li>1x Captain: 80 pts</li>
  <li>1x Librarian: 65 pts</li>
  <li>1x Chaplain with Jump Pack: 75 pts</li>
  <li>1x Ancient: 50 pts</li>
  <li>1x Land Speeder (estimated using Legends units): est. 100 pts</li>
</ul>

<h3>My Take on the Space Marine Side</h3>

<p>This half feels underwhelming.</p>

<p>The Librarian model looks badass, no question there. And the return of the Landspeeder is going to make a lot of entrenched players very happy. But outside of that, the unit selection feels a bit safe and not especially exciting.</p>

<p>Space Marines in starter boxes are always going to be geared toward newer players, but this box half is lacking flash. Games Workshop played it safe, and it is not a terrible selection for newer players. Compared to some previous edition launch boxes, this feels like a weaker entry point.</p>

<p>Again, Space Marine players may feel differently, but this seems to be a lackluster product. I can see the Space Marine half of this box going for cheap on the secondary market. If you see this for a decent price ($100 or less), 720 points is not bad value.</p>

<p>New players, this is a decent entry point into Space Marines for Warhammer 40K, but if you already have a decent-sized Space Marine army, just wait to buy the Land Speeder in a separate box.</p>

<h2>Other Contents Included</h2>

<h3>Core Rule Book</h3>
<p>Love the small, compact version of the rulebook. It will make transport and using it mid-game much easier.</p>

<h3>Mission Cards</h3>
<p>Similar to last edition, mission cards will work the same way, and the cards provided will last you throughout the season.</p>

<h3>Campaign Cards</h3>
<p>New campaign card system in which you combine various cards together to create a narrative battle. As you play more games with the deck, it strings together a cohesive narrative across multiple games.</p>
<p>Hopefully this does not mean that Crusade is dead. If it is an add-on way to play, it should be a very fun novelty until a Crusade book arrives.</p>

<h3>Exclusive Lore Book</h3>
<p>The coolest non-model in the box. This is how you properly set up the edition and reward fans of the universe. Very welcome addition, and I am excited to read it.</p>

<h3>Data Cards</h3>
<p>Honestly, these are not worth the paper they are printed on. They will be outdated immediately after launch and often confuse newer players rather than help.</p>

<h2>11th Edition Box Price Estimate</h2>

<p>Now for the big question everyone will ask immediately: how much will the 11th Edition box cost?</p>

<p>Historically, new editions often bring points increases and price increases. If we assume a rough 15% points bump, then the current 1,470 points becomes around 1,700 points at edition launch.</p>

<p>Last edition, the Leviathan box points per dollar was 6.7, the lowest over the last five editions. If you want to see a full breakdown of points per dollar from 2nd edition to 10th edition, <a href="/blog/warhammer-40k-launch-box-prices-economics-part-1/">visit this article</a>.</p>

<p>Assuming Games Workshop wants to provide similar value to players:</p>

<h3>At 7 Points Per $1</h3>

<p>That would price the box around $242. Realistically, that is not happening. Games Workshop has only increased prices for edition boxes since 5th edition, and last edition's box retailed for $250.</p>

<h3>At 6 Points Per $1</h3>

<p>This is what I would consider the bare minimum for a true discount starter box. The price at this points-per-dollar value would be $283. This is more realistic and makes sense considering the decrease in value since 6th edition.</p>

<h3>My Prediction</h3>

<ul>
  <li>Likely price: $285</li>
  <li>Fair price: $250</li>
  <li>Bad value: $300+</li>
</ul>

<p>If this somehow lands around $250, I would fully recommend this box. If it lands near $300, it is a skip unless you plan on splitting the cost with another person.</p>

<h2>Who Should Purchase the 11th Edition Box?</h2>

<ul>
  <li>New Ork players</li>
  <li>Existing Ork collectors</li>
  <li>Friends splitting the box</li>
  <li>Players planning on selling box contents they are not interested in</li>
  <li>New Space Marine players</li>
</ul>

<h2>How It Compares to Previous Edition Launch Boxes</h2>

<p>My initial reaction: below average value compared to the last two edition launch boxes, but still decent as long as it stays below $300.</p>

<p>That does not mean it is bad. Games Workshop has previously set a high bar with some amazing starter boxes. Look below for how each starter box stacks up in comparison to each other.</p>

<!-- ── POINTS DATA TABLE ──────────────────────────────────────────────── -->
<table style="text-align:center;">
  <thead>
    <tr>
      <th>Edition</th>
      <th>Year</th>
      <th>Launch Price</th>
      <th>2026 Value ¹</th>
      <th>Box Points</th>
      <th>Scaled Points ²</th>
      <th>Pts / 2026$ ³</th>
      <th>Scaled Pts / 2026$ ⁴</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td><strong>2nd Ed</strong></td>
      <td>1993</td>
      <td>$60</td>
      <td>$136</td>
      <td style="color:#5c6480;">&#8212;</td>
      <td style="color:#5c6480;">&#8212;</td>
      <td style="color:#5c6480;">&#8212;</td>
      <td style="color:#5c6480;">&#8212;</td>
    </tr>
    <tr>
      <td><strong>3rd Ed</strong></td>
      <td>1998</td>
      <td>$90</td>
      <td>$180</td>
      <td>500</td>
      <td>667</td>
      <td>2.8</td>
      <td style="color:#d44040;font-weight:600;">3.7</td>
    </tr>
    <tr>
      <td><strong>4th Ed</strong></td>
      <td>2004</td>
      <td>$75</td>
      <td>$130</td>
      <td>650</td>
      <td>867</td>
      <td>5.0</td>
      <td style="color:#d44040;font-weight:600;">6.7</td>
    </tr>
    <tr>
      <td><strong>5th Ed</strong></td>
      <td>2008</td>
      <td>$75</td>
      <td>$114</td>
      <td>1,000</td>
      <td>1,143</td>
      <td>8.8</td>
      <td style="color:#4aab72;font-weight:600;">10.0</td>
    </tr>
    <tr>
      <td><strong>6th Ed &#9733;</strong></td>
      <td>2012</td>
      <td>$100</td>
      <td>$142</td>
      <td>1,500</td>
      <td>1,500</td>
      <td>10.6</td>
      <td style="color:#4aab72;font-weight:600;">10.6</td>
    </tr>
    <tr>
      <td><strong>7th Ed</strong></td>
      <td>2014</td>
      <td>$110</td>
      <td>$152</td>
      <td>1,500</td>
      <td>1,500</td>
      <td>9.9</td>
      <td style="color:#4aab72;font-weight:600;">9.9</td>
    </tr>
    <tr>
      <td><strong>8th Ed</strong></td>
      <td>2017</td>
      <td>$160</td>
      <td>$213</td>
      <td>1,550</td>
      <td>1,550</td>
      <td>7.3</td>
      <td style="color:#c8922a;font-weight:600;">7.3</td>
    </tr>
    <tr>
      <td><strong>9th Ed</strong></td>
      <td>2020</td>
      <td>$200</td>
      <td>$253</td>
      <td>2,000</td>
      <td>2,000</td>
      <td>7.9</td>
      <td style="color:#c8922a;font-weight:600;">7.9</td>
    </tr>
    <tr>
      <td><strong>10th Ed</strong></td>
      <td>2023</td>
      <td>$250</td>
      <td>$268</td>
      <td>1,800</td>
      <td>1,800</td>
      <td>6.7</td>
      <td style="color:#d44040;font-weight:600;">6.7</td>
    </tr>
  </tbody>
</table>
<p style="font-size:0.72rem;color:var(--text-muted);margin-top:0.25rem;">&#9733; Best all-time value per inflation-adjusted dollar &nbsp;&middot;&nbsp; ¹ Launch price adjusted to 2026 dollars &nbsp;&middot;&nbsp; ² Points scaled to a standard 2,000pt game for cross-edition comparison &nbsp;&middot;&nbsp; ³ Points per 2026 dollar (raw box count) &nbsp;&middot;&nbsp; ⁴ Points per 2026 dollar (game-size scaled)</p>

<h2>Final Thoughts</h2>

<p>For more detail read the article on <a href="https://www.warhammer-community.com/en-gb/articles/x2allqya/warhammer-40000-armageddon-whats-in-the-box/" target="_blank" rel="noopener noreferrer">Warhammer Community</a> or continue below.</p>

<p>I am probably splitting this box with a Space Marine player I know, and I think that is the smartest route for many people. If you love both sides of the box, buy the whole thing for yourself.</p>

<p>If 11th Edition points increase more than expected, maybe the value looks better later. But based on today's numbers, this does not look like one of the all-time great Warhammer launch boxes.</p>

<p>Still, new edition hype is always fun, and I expect this box to sell extremely well. I can't wait to crack open the rulebook and start playing some games.</p>

<p>If you want to watch the full reveal or a quick recap, check out the videos below.</p>

<ul>
  <li><a href="https://www.youtube.com/watch?v=MfTSpDSQe0s" target="_blank" rel="noopener noreferrer">Full Reveal</a></li>
  <li><a href="https://www.youtube.com/watch?v=5_HcsDbkAWI" target="_blank" rel="noopener noreferrer">Quick Recap</a></li>
</ul>
"""


class Command(BaseCommand):
    """Publish the Armageddon 11th Edition box breakdown post (idempotent)."""

    help = 'Publishes the Warhammer 40K Armageddon 11th Edition box contents breakdown post.'

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
            title='Warhammer 40K Armageddon 11th Edition Box Contents Revealed: Estimated Points, Value and Price Breakdown',
            excerpt=(
                'The Warhammer 40K Armageddon box contents were revealed today. Here is a full '
                'breakdown of every model, estimated points values, what each half is worth, and '
                'what we think the price will be at launch.'
            ),
            body=BODY,
            status=Post.STATUS_PUBLISHED,
            published_at=timezone.now(),
            meta_title='Warhammer 40K Armageddon Box: Points, Value and Price Estimate',
            meta_description=(
                'Full breakdown of the Warhammer 40K Armageddon 11th Edition launch box. '
                'Estimated points for every model, price predictions, and whether it is worth buying.'
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

        tag_names = ['Warhammer 40K', 'New Releases', 'Pricing', 'Orks', 'Space Marines']
        for name in tag_names:
            tag, _ = Tag.objects.get_or_create(name=name)
            post.tags.add(tag)
        self.stdout.write(self.style.SUCCESS(f'Tags attached: {tag_names}'))
