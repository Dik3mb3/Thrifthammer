"""
Management command: publish_target_miniatures

Creates 'Target Warhammer Board Games: Are They the Cheapest Way to Buy
Warhammer Miniatures?' blog post. Safe to run multiple times (idempotent).

Usage:
    python manage.py publish_target_miniatures
    python manage.py publish_target_miniatures --force
"""

from django.contrib.staticfiles.storage import staticfiles_storage
from django.core.management.base import BaseCommand
from django.utils import timezone

SLUG = 'cheap-warhammer-miniatures-target'
SITE_URL = 'https://thrifthammer.com'


def _static(path):
    try:
        return f'{SITE_URL}{staticfiles_storage.url(path)}'
    except Exception:
        return ''


def _gallery(gallery_id, images):
    """Return a swipeable (scroll-snap) image gallery, no JS required for the swipe itself."""
    slides = '\n'.join(
        f'    <div class="tm-gallery-slide" id="{gallery_id}-{i + 1}">'
        f'<img src="{src}" alt="{alt}" width="{w}" height="{h}" loading="lazy"></div>'
        for i, (src, alt, w, h) in enumerate(images)
    )
    dots = '\n'.join(
        f'    <a href="#{gallery_id}-{i + 1}" class="tm-gallery-dot{" tm-gallery-dot-active" if i == 0 else ""}" '
        f'aria-label="Image {i + 1} of {len(images)}"></a>'
        for i in range(len(images))
    )
    return (
        f'<div class="tm-gallery" data-gallery="{gallery_id}">\n'
        f'  <div class="tm-gallery-track" id="{gallery_id}-track">\n'
        f'{slides}\n'
        f'  </div>\n'
        f'  <div class="tm-gallery-nav">\n'
        f'{dots}\n'
        f'  </div>\n'
        f'</div>'
    )


_BASE = 'https://thrifthammer.com/static/images/blog'

TACTICUS_GALLERY = _gallery('tacticus', [
    (f'{_BASE}/target-miniatures-tacticus-1.webp',
     'Warhammer 40,000: Tacticus board game box and contents including datacards, dice, and game board',
     554, 554),
    (f'{_BASE}/target-miniatures-tacticus-2.webp',
     'Tacticus box back cover showing the game board setup and included Space Marine and Death Guard miniatures',
     480, 638),
])

DOW_GALLERY = _gallery('dow', [
    (f'{_BASE}/target-miniatures-dow-1.webp',
     'Warhammer 40,000: Dawn of War Onslaught board game box art featuring a Blood Angels Space Marine',
     800, 800),
    (f'{_BASE}/target-miniatures-dow-2.webp',
     'Dawn of War Onslaught box contents spread including rulebook, game board, cards, and Blood Angels miniatures',
     800, 800),
    (f'{_BASE}/target-miniatures-dow-3.webp',
     'Nine unpainted red plastic Blood Angels Space Marine miniatures included in the Dawn of War Onslaught box',
     800, 800),
])

HEROES_GALLERY = _gallery('heroes', [
    (f'{_BASE}/target-miniatures-heroes-1.webp',
     'Warhammer Heroes blind box case showing a full box of individually wrapped miniature boxes',
     436, 436),
    (f'{_BASE}/target-miniatures-heroes-2.webp',
     'A single opened Warhammer Heroes box showing the sprue, rules card, and packaging',
     309, 273),
    (f'{_BASE}/target-miniatures-heroes-3.webp',
     'Warhammer Heroes Series 6 Strike Force Variel box art featuring three Dark Angels miniatures',
     574, 606),
    (f'{_BASE}/target-miniatures-heroes-4.webp',
     'Insert card listing all seven collectible Space Marine miniatures in the Warhammer Heroes Strike Force Justian series',
     678, 452),
])

BODY = """\
<style>
/* ── Target Miniatures post ─────────────────────────────────────────────── */

/* Small-print footnote paragraphs */
.tm-footnote { font-size: 0.78rem; color: var(--text-muted, #777); margin-top: -0.25rem; }
.tm-fnref { font-size: 0.7em; vertical-align: super; color: var(--text-muted, #999); }

/* Swipeable image gallery — native CSS scroll-snap, no JS required to swipe */
.tm-gallery { margin: 1.25rem 0; }
.tm-gallery-track {
  display: flex;
  overflow-x: auto;
  scroll-snap-type: x mandatory;
  -webkit-overflow-scrolling: touch;
  scrollbar-width: none;
  border-radius: 10px;
  background: #111318;
}
.tm-gallery-track::-webkit-scrollbar { display: none; }
.tm-gallery-slide {
  flex: 0 0 100%;
  scroll-snap-align: start;
  scroll-snap-stop: always;
  display: flex;
  align-items: center;
  justify-content: center;
}
.tm-gallery-slide img {
  width: 100%;
  height: auto;
  max-height: 420px;
  object-fit: contain;
  display: block;
}
.tm-gallery-nav {
  display: flex;
  justify-content: center;
  gap: 0.5rem;
  margin-top: 0.65rem;
}
.tm-gallery-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: rgba(255,255,255,0.22);
  display: inline-block;
}
.tm-gallery-dot-active { background: #c8922a; }

/* Value-breakdown table (mobile-safe: wrapper scrolls, table never clips) */
#tm-dow-tbl-wrap {
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
  width: 100%;
  margin: 1rem 0;
  border-radius: 6px;
  border: 1px solid var(--border-subtle, rgba(255,255,255,0.08));
}
#tm-dow-tbl {
  min-width: 380px;
  width: 100%;
  border-collapse: collapse;
  font-size: 0.87rem;
  background: var(--bg-card, #1a1b1c);
}
#tm-dow-tbl thead th {
  background: #9a6e10;
  color: #fff;
  padding: 0.55rem 0.7rem;
  text-align: left;
  font-size: 0.77rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  white-space: nowrap;
  border-bottom: 2px solid rgba(255,255,255,0.12);
}
#tm-dow-tbl tbody tr { border-bottom: 1px solid rgba(255,255,255,0.06); }
#tm-dow-tbl tbody tr:last-child { border-bottom: none; }
#tm-dow-tbl tbody tr:nth-child(even) { background: rgba(255,255,255,0.03); }
#tm-dow-tbl td {
  padding: 0.5rem 0.7rem;
  vertical-align: middle;
  color: var(--text-primary, #e8e8e8);
}
</style>

<p>At ThriftHammer, we find the best <a href="/products/?category=warhammer-40000">Warhammer 40K deals</a> online on eBay, Amazon, and other tabletop hobby stores. However, the most under the radar source for the cheapest Warhammer 40K has to be Target, whose access to Games Workshop exclusive board games and aggressive clearances of their hobby games leads to incredible deals.</p>

<h2>Really, Target?</h2>

<p>Over the last few years, Games Workshop has partnered with Target to release several semi-exclusive board games that include genuine push-fit Warhammer miniatures. These board games are Games Workshop's attempt to expand into the $400 million board game market<span class="tm-fnref">3</span> and attract younger and more casual audiences to their more expensive miniatures games. Since competition in the board game market is very competitive, Games Workshop has priced these games at lower prices than a typical one-off $60 kit. Yet these boxes often include more models than a standard $60 Games Workshop kit and cheaper alternate sculpts of individual characters, which can cost $35+ each! As a bonus, you get an actual board game to play with your friends or family.</p>

<p class="tm-footnote"><span class="tm-fnref">3</span> According to the <a href="https://www.slideshare.net/slideshow/icv2-hobby-games-white-paper-2025-gama-expo-2026/286373737" target="_blank" rel="noopener noreferrer">ICv2 GAMA Expo 2026 Presentation</a></p>

<p>I will discuss some of the Target-exclusive Warhammer products you can find today, and the value each box presents alongside information about the actual board game itself.</p>

<h2>Warhammer 40,000: Tacticus</h2>

<p>MSRP: $49.99 | Release Date: Unreleased (2026)</p>

{tacticus_gallery}

<h3>Gameplay Overview</h3>

<p>Tacticus is built around small-scale tactical skirmishes rather than full armies. Each player controls a squad of three heroes: <a href="/products/?category=warhammer-40000&amp;faction=space-marines&amp;sort=discount">Space Marines</a> vs <a href="/products/?category=warhammer-40000&amp;faction=death-guard&amp;sort=discount">Death Guard</a>. Each has their own abilities, attacks, and special rules. Games are played on a compact battlefield, they take turns moving their miniatures using special abilities, and attacking opponents while trying to control key areas of the board and eliminate the enemy team. Overall, Tacticus is an approachable small scale skirmish board game for any level of gamer and serves as an entry point to the great Warhammer universe.</p>

<h3>Contents</h3>

<p><strong>Space Marines</strong></p>
<ul>
  <li>1 Heavy Intercessor</li>
  <li>1 Eliminator</li>
  <li>1 Sternguard Veteran</li>
</ul>
<p><strong>Death Guard</strong></p>
<ul>
  <li>1 Plaguecaster</li>
  <li>1 Plague Champion</li>
  <li>1 Plague Marine</li>
</ul>
<p><strong>Tacticus Mobile Game Code</strong></p>
<ul>
  <li>Access to the Dark Angels Character Ramus in game</li>
</ul>

<h3>Value Verdict</h3>

<p>Whether this is an incredible deal or just meh comes down to how much you want the Plaguecaster &amp; Plague Champion. The Plaguecaster is one of the most annoying models to collect in Warhammer 40K, being locked to the Kill Team Starter Set or the <a href="/products/death-guard-chosen-of-mortarion/">Chosen of Mortarion Box</a>, both costing more than $70+. The Plaguecaster on its own typically sells secondhand for $35-$40 by itself. For an additional $10 you get access to 5 official push-fit Games Workshop models ($2 per model!). While these models lack as much in-game use as the Plaguecaster, they make phenomenal hobby projects. With a bit of creativity and ingenuity you can easily kit bash your own Space Marine and Death Guard characters from these options or treat them as art projects for display.</p>

<h3>ThriftHammer New Player Tip</h3>

<p>These models make great first time canvases for new painters. You can likely sell the Plaguecaster for $20-$30, subsidizing your initial costs so you can freely paint the remaining models as practice. If you're new to painting, it's much better to make mistakes on 5 models costing you $20-$30 (assuming you sell the Plaguecaster) than a standard $60 Warhammer 40K kit.</p>

<h2>Warhammer 40,000: Dawn of War</h2>

<p>MSRP: $49.99 | BoardGameGeek Rating: 6.8/10 | Target Rating: 4.2/5</p>

{dow_gallery}

<h3>Gameplay Overview</h3>

<p>Warhammer 40,000: Dawn of War is a fast-paced cooperative strategy board game that emphasizes tactical decision-making in 45-60 minutes. You take control of the Blood Ravens chapter of the <a href="/products/?category=warhammer-40000&amp;faction=space-marines&amp;sort=discount">Space Marines</a> as you fend off waves of Orks either solo or with friends. A light survival tower defense game, Dawn of War won't set your world on fire, but could be useful as a way to share your love of Warhammer 40K with those uninterested in the large game system.</p>

<h3>Contents</h3>

<ul>
  <li>3 Eradicators</li>
  <li>3 Blade Guard</li>
  <li>1 Judiciar</li>
  <li>1 Chaplain</li>
  <li>1 Ancient</li>
</ul>

<h3>Value Verdict</h3>

<p>This is a must buy for any Space Marine collector. 9 models for $50 is an absolute steal at today's GW prices, and as a bonus you get an entire board game to go with it!</p>

<p>The value breakdown:</p>

<div id="tm-dow-tbl-wrap">
  <table id="tm-dow-tbl">
    <thead>
      <tr><th>Component</th><th>GW MSRP</th><th>Points</th></tr>
    </thead>
    <tbody>
      <tr><td>3 Eradicators</td><td>$60</td><td>90 pts</td></tr>
      <tr><td>3 Blade Guard</td><td>$60</td><td>80 pts</td></tr>
      <tr><td>1 Judiciar<span class="tm-fnref">1</span></td><td>$42</td><td>55 pts</td></tr>
      <tr><td>1 Chaplain</td><td>$42</td><td>60 pts</td></tr>
      <tr><td>1 Ancient</td><td>$43.50</td><td>40 pts</td></tr>
    </tbody>
  </table>
</div>
<p class="tm-footnote"><span class="tm-fnref">1</span> Judiciar not sold separately, currently sold via the Honoured of the Chapter (GW MSRP: $170)</p>

<p>Be warned, like all Target exclusive Warhammer board game minis, to get some of these game ready could require conversions. These models do not come out with optimal or many times in-game legal weapon options, so you may need to use your pile of bits at home to convert them to usable units. For those uncomfortable with working with push fit models or who do not like converting, this may not be the best purchase. However, if you only want some cool models to paint and/or are willing to convert, the value here speaks for itself. This group of miniatures retails for $247 at Games Workshop, but can be yours for $50 at a Target near you. There is a reason why this box usually sells out quickly, grabbing one or two copies is recommended.</p>

<h3>ThriftHammer New Player Tip</h3>

<p>If you're planning to do conversions and have never worked with push fit models, I recommend shaving down or cutting the pegs down and using plastic glue to snugly connect all the pieces together. Dry fitting the pieces together is a bad idea long-term. Order some greenstuff<span class="tm-fnref">2</span> from <a href="https://www.amazon.com/dp/B001AE5ZQO?tag=thrifthammer7-20" target="_blank" rel="noopener noreferrer sponsored">Amazon</a>, which can be used to plug any gaps or holes left from modifying the models' pose or changing their weapon option. Many videos can be found on YouTube, TikTok, and social media that can help you convert your models how you want.</p>

<p class="tm-footnote"><span class="tm-fnref">2</span> ThriftHammer earns a small commission on Amazon from any purchases you make using our links</p>

<h2>Warhammer Heroes</h2>

<p>MSRP: $64 (8 boxes), $8-$10 per singles (not available at all stores)</p>

{heroes_gallery}

<h3>Box Overview</h3>

<p>This is not a board game, rather Warhammer Heroes is a blind box where you get one random miniature from a range of different options. Sold in large boxes of 8 individual boxes or as separate individual boxes, Warhammer Heroes is essentially Games Workshop's version of popular trendy gacha/blind box products like Labubu. In defense of Games Workshop, Warhammer Heroes provides greater value than most other gacha products (being both collectable and playable in game). Target also guarantees only 1-2 duplicates max per big box. There are even ways to figure out the miniature in the box by looking at the box numbers, eliminating much of the randomness.</p>

<p><strong>Warhammer Heroes Ranges:</strong></p>
<ul>
  <li>Series 6: Strike Force Variel (2025) - Dark Angels</li>
  <li>Series 5: Stormcast Eternals (2024) - Age of Sigmar</li>
  <li>Series 4: Strike Force Justian (2023) - Space Marines</li>
  <li>Series 3: Death Guard (2020)</li>
  <li>Series 2: Terminators (2018)</li>
  <li>Series 1: Ultramarines (2017)</li>
</ul>

<h3>Value Verdict</h3>

<p>This is a product Games Workshop should expand to all other factions. While I dislike gacha and blind boxes in general, this is a relatively inexpensive purchase in which you get access to a legit Games Workshop model at a reasonable price point of $8-$10 compared to a singular character model, which routinely sells for over $40 at Games Workshop.</p>

<p>Now I won't recommend you buy more than 1 big box or a few individual boxes, as the more you purchase the higher chance you receive duplicates, which eliminates much of the value savings. Like I said before, these models may need some conversions to make them in-game viable, but as a solo product these make excellent gifts whether you're planning to use them in your army or not.</p>

<h3>This Product Is Extremely Difficult to Find</h3>

<p>If you are interested in buying Warhammer Heroes you are facing an uphill battle when it comes to finding one. The product is notoriously always out of stock, partly because of its overall popularity but also some people trying to resell it at higher prices online. It's a shame, because this is one of Games Workshop's best ideas in a long time. Let's hope Games Workshop does not sit on this idea and looks to expand each series to include more factions than just Space Marines.</p>

<h2>Previously Stocked Target Warhammer Board Games</h2>

<p>Target has always carried many exclusive and non-exclusive Warhammer board games that players through the years have used to bolster their armies.</p>

<p>Let's take a quick dive into some of Target's historic highlight Warhammer products:</p>

<h3>Warhammer 40,000: Space Marine - The Board Game</h3>

<p>MSRP: $39.99 | BoardGameGeek Rating: 3.7/10</p>

<p>A terrible board game that is not even worth discussing mechanically, the box was a goldmine for players looking for a bunch of miniatures at a discounted price to Games Workshop.</p>

<p><strong>Contents:</strong></p>
<ul>
  <li>Lieutenant Titus</li>
  <li>20 Termagants</li>
  <li>2 Ripper Swarms</li>
</ul>

<p>Lieutenant Titus was the definite draw of the box, but the addition of 20 <a href="/products/tyranid-termagants/">Termagants</a> ($48 per 10 at Games Workshop) makes this a deal. If you want Titus, you sell the Termagants and recoup some if not all your money, and if you want the Termagants, selling Titus will be the easiest transaction of your life. This box notoriously went on clearance everywhere as the actual board game was a flop, so many Warhammer 40K players picked these models up at even better prices.</p>

<h3>Space Marine Adventures: Tyranid Attack!</h3>

<p>MSRP: $39.99 | BoardGameGeek Rating: 7.3/10</p>

<p>This one is the exception to the rule, where the board game is probably better than the miniatures inside. Ranked positively, with most comments referring to the gameplay itself as the selling point of the box rather than the miniatures, Space Marine Adventures might be worth getting if you want to play an entry Warhammer game with family and friends rather than pillaging the box for the miniatures.</p>

<p><strong>Contents:</strong></p>
<ul>
  <li>Sergeant Maximus (Ultramarines)</li>
  <li>Brother Raphael (Blood Angels)</li>
  <li>Brother Vorne (Iron Hands)</li>
  <li>Brother Adrix (Salamanders)</li>
  <li>Brother Lukas (Space Wolves)</li>
</ul>

<h2>The Target Clearance Opportunity</h2>

<p>If you're patient, you can get all of these games significantly cheaper during January and July. Target usually clears out unsold inventory during these time periods to make space for new games. Sometimes these games can reach -75% off for the last wave of product. With Games Workshop not supporting any of these solo releases long-term, they are often replaced with the next Games Workshop board game, requiring Target to aggressively sell these excess games. Their loss is your potential gain. Visit Target post-holidays, as you can often see not just their board games, but video games, clothing, and household products all sold at rock bottom prices.</p>

<p>At 25%-75% discounts we are talking about models being priced at $2-$6 per model! This is better than the push-fit models being currently sold separately from the <a href="/blog/armageddon-individual-units-price-guide/">Warhammer 11th Edition Armageddon Box</a>. If you are looking to grow your army at a budget, Target is the perfect source of low cost miniatures that you can easily integrate into various lists. If you are interested in more great deals, please sign up for our newsletter below so you can keep up to date on the best Warhammer deals going on.</p>
"""
BODY = (
    BODY
    .replace('{tacticus_gallery}', TACTICUS_GALLERY)
    .replace('{dow_gallery}', DOW_GALLERY)
    .replace('{heroes_gallery}', HEROES_GALLERY)
)


class Command(BaseCommand):
    """Publish the Target Warhammer board games blog post (idempotent)."""

    help = 'Publishes the Target Warhammer exclusives blog post.'

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
            title='Target Warhammer Board Games: The Cheapest Way to Buy Warhammer Miniatures?',
            excerpt=(
                "Target-exclusive board games like Tacticus, Dawn of War, and Warhammer Heroes "
                "pack genuine Games Workshop miniatures at a fraction of retail price. Here's "
                "whether each one is actually worth buying."
            ),
            body=BODY,
            status=Post.STATUS_PUBLISHED,
            # published_at is NOT here — it never belongs in defaults
            meta_title='',
            meta_description=(
                'Looking for cheap Warhammer miniatures? Target-exclusive games like Tacticus, '
                'Dawn of War, and Warhammer Heroes provide GW miniatures at a fraction of the cost.'
            ),
            featured_image_url=_static('images/blog/target-warhammer-miniatures-header.webp'),
            featured_image_alt='Target logo crossed out next to hand-lettered text reading Cheap Warhammer Minis',
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

        tag_names = ['Warhammer 40K', 'Budget Tips', 'Pricing']
        for name in tag_names:
            tag, _ = Tag.objects.get_or_create(name=name)
            post.tags.add(tag)
        self.stdout.write(self.style.SUCCESS(f'Tags: {tag_names}'))
