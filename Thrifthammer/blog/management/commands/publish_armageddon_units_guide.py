"""
Management command: publish_armageddon_units_guide

Creates the 'Warhammer 40K Armageddon Box: Individual Units Price Guide' blog post.
Safe to run multiple times (idempotent).

Usage:
    python manage.py publish_armageddon_units_guide
    python manage.py publish_armageddon_units_guide --force  # overwrite existing
"""

from django.contrib.staticfiles.storage import staticfiles_storage
from django.core.management.base import BaseCommand
from django.utils import timezone

SLUG = 'armageddon-individual-units-price-guide'
BASE_URL = 'https://thrifthammer.com'

BODY = """\
<p>The Warhammer 40K 11th edition Armageddon Box is an incredible value for those new and old to Warhammer 40K. While buying an entire box is already good value, some players may not be interested in adding more intercessors or adding another 20 Ork Boyz to their 120+ Ork Boyz collections (cough cough, this writer).</p>

<p>Buying individual units from the box provides a great opportunity to pick and choose the individual Warhammer minis of the box you need for your army while still benefiting from reduced prices. Today we dig around eBay, r/Miniswap, and Facebook to figure out a reasonable value to pay for these individual units so you can score the best possible deal.</p>

<p>The chart below breaks down every Space Marine and Ork unit in the Armageddon box set side by side showing the average price of each unit on the secondhand market. I will also include the best prices I have seen personally for each unit during my research, but understand these are often outliers not the standard price you will typically see.</p>

<h2>Individual Unit Prices: 11th Edition Armageddon Box</h2>

<style>
/* ── Armageddon Individual Units Post ─────────────────────────────────── */

/* Data tables */
.arm-tbl-wrap {
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
  width: 100%;
  margin: 1rem 0;
  border-radius: 6px;
  border: 1px solid var(--border-subtle, rgba(255,255,255,0.08));
}
#arm-sm-tbl,
#arm-ok-tbl,
#arm-bk-tbl {
  min-width: 480px;
  width: 100%;
  border-collapse: collapse;
  font-size: 0.87rem;
  background: var(--bg-card, #1a1b1c);
}
#arm-sm-tbl thead th,
#arm-ok-tbl thead th,
#arm-bk-tbl thead th {
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
#arm-sm-tbl tbody tr,
#arm-ok-tbl tbody tr,
#arm-bk-tbl tbody tr {
  border-bottom: 1px solid rgba(255,255,255,0.06);
}
#arm-sm-tbl tbody tr:last-child,
#arm-ok-tbl tbody tr:last-child,
#arm-bk-tbl tbody tr:last-child {
  border-bottom: none;
}
#arm-sm-tbl tbody tr:nth-child(even),
#arm-ok-tbl tbody tr:nth-child(even),
#arm-bk-tbl tbody tr:nth-child(even) {
  background: rgba(255,255,255,0.03);
}
#arm-sm-tbl tbody tr:hover,
#arm-ok-tbl tbody tr:hover,
#arm-bk-tbl tbody tr:hover {
  background: rgba(200,146,26,0.08);
}
#arm-sm-tbl td,
#arm-ok-tbl td,
#arm-bk-tbl td {
  padding: 0.5rem 0.7rem;
  vertical-align: middle;
  color: var(--text-primary, #e8e8e8);
}
#arm-sm-tbl td a,
#arm-ok-tbl td a,
#arm-bk-tbl td a {
  color: var(--accent-gold-lt, #d4a832);
  text-decoration: none;
  font-weight: 600;
}
#arm-sm-tbl td a:hover,
#arm-ok-tbl td a:hover,
#arm-bk-tbl td a:hover {
  text-decoration: underline;
}
.arm-num { text-align: right; white-space: nowrap; }
.arm-tg  { color: #4aab72; font-weight: 700; }
.arm-to  { color: #c8922a; font-weight: 700; }
.arm-tm  { color: #5c6480; }
.arm-tot-row { border-top: 2px solid rgba(255,255,255,0.15) !important; }
.arm-footnote {
  font-size: 0.72rem;
  color: var(--text-muted, #777);
  margin-top: 0.2rem;
  font-style: italic;
}
</style>

<h3>Space Marine Half</h3>

<!-- ── Space Marine Data Table ────────────────────────────────────────── -->
<div class="arm-tbl-wrap">
  <table id="arm-sm-tbl">
    <thead>
      <tr>
        <th>Unit</th>
        <th>Best Price Seen *</th>
        <th>Avg Market *</th>
        <th>Est. GW **</th>
        <th>Avg vs. GW</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td><a href="/products/armageddon-captain-with-relic-shield/">Captain with Relic Shield</a></td>
        <td class="arm-num">$15</td>
        <td class="arm-num">$23</td>
        <td class="arm-num">$43.50</td>
        <td class="arm-num arm-to">-47%</td>
      </tr>
      <tr>
        <td><a href="/products/armageddon-librarian/">Librarian</a></td>
        <td class="arm-num">$20</td>
        <td class="arm-num">$24</td>
        <td class="arm-num">$42.00</td>
        <td class="arm-num arm-to">-43%</td>
      </tr>
      <tr>
        <td><a href="/products/armageddon-chaplain-with-jump-pack/">Chaplain with Jump Pack</a></td>
        <td class="arm-num">$25</td>
        <td class="arm-num">$31</td>
        <td class="arm-num">$42.00</td>
        <td class="arm-num arm-tm">-26%</td>
      </tr>
      <tr>
        <td><a href="/products/armageddon-ancient/">Ancient &#9733;</a></td>
        <td class="arm-num">$10</td>
        <td class="arm-num">$16</td>
        <td class="arm-num">$43.50</td>
        <td class="arm-num arm-tg">-63%</td>
      </tr>
      <tr>
        <td><a href="/products/armageddon-intercessors/">Intercessors</a></td>
        <td class="arm-num">$22</td>
        <td class="arm-num">$36</td>
        <td class="arm-num">$65.00</td>
        <td class="arm-num arm-to">-45%</td>
      </tr>
      <tr>
        <td><a href="/products/armageddon-vanguard-veterans-with-jump-packs/">Vanguard Veterans with Jump Packs</a></td>
        <td class="arm-num">$34</td>
        <td class="arm-num">$40</td>
        <td class="arm-num">$65.00</td>
        <td class="arm-num arm-to">-38%</td>
      </tr>
      <tr>
        <td><a href="/products/armageddon-eradicators-with-heavy-bolters/">Eradicators with Heavy Bolters</a></td>
        <td class="arm-num">$30</td>
        <td class="arm-num">$36</td>
        <td class="arm-num">$60.00</td>
        <td class="arm-num arm-to">-40%</td>
      </tr>
      <tr>
        <td><a href="/products/armageddon-land-speeder/">Land Speeder</a></td>
        <td class="arm-num">$40</td>
        <td class="arm-num">$54</td>
        <td class="arm-num">$82.00</td>
        <td class="arm-num arm-to">-34%</td>
      </tr>
      <tr class="arm-tot-row">
        <td><strong>Total (each unit individually)</strong></td>
        <td class="arm-num">$196</td>
        <td class="arm-num">$260</td>
        <td class="arm-num">$443</td>
        <td class="arm-num arm-to">-41%</td>
      </tr>
    </tbody>
  </table>
</div>
<p class="arm-footnote">&#9733; Best deal on the Space Marine side &nbsp;&middot;&nbsp; * Average and best prices from top eBay and r/Miniswap listings at time of writing, approx. July 2026 &nbsp;&middot;&nbsp; ** GW retail prices are estimated based on similar models or existing kit prices</p>

<h3>Ork Half</h3>

<!-- ── Ork Data Table ─────────────────────────────────────────────────── -->
<div class="arm-tbl-wrap">
  <table id="arm-ok-tbl">
    <thead>
      <tr>
        <th>Unit</th>
        <th>Best Price Seen *</th>
        <th>Avg Market *</th>
        <th>Est. GW **</th>
        <th>Avg vs. GW</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td><a href="/products/armageddon-warboss/">Warboss &#9733;</a></td>
        <td class="arm-num">$10</td>
        <td class="arm-num">$15</td>
        <td class="arm-num">$43.50</td>
        <td class="arm-num arm-tg">-66%</td>
      </tr>
      <tr>
        <td><a href="/products/armageddon-bannernob/">Bannernob &#9733;</a></td>
        <td class="arm-num">$10</td>
        <td class="arm-num">$15</td>
        <td class="arm-num">$43.50</td>
        <td class="arm-num arm-tg">-66%</td>
      </tr>
      <tr>
        <td><a href="/products/armageddon-big-boss/">Big Boss &#9733;</a></td>
        <td class="arm-num">$10</td>
        <td class="arm-num">$14</td>
        <td class="arm-num">$43.50</td>
        <td class="arm-num arm-tg">-68%</td>
      </tr>
      <tr>
        <td><a href="/products/armageddon-painboy/">Painboy &#9733;</a></td>
        <td class="arm-num">$10</td>
        <td class="arm-num">$15</td>
        <td class="arm-num">$43.50</td>
        <td class="arm-num arm-tg">-66%</td>
      </tr>
      <tr>
        <td><a href="/products/armageddon-weirdboy/">Weirdboy &#9733;</a></td>
        <td class="arm-num">$10</td>
        <td class="arm-num">$15</td>
        <td class="arm-num">$43.50</td>
        <td class="arm-num arm-tg">-66%</td>
      </tr>
      <tr>
        <td><a href="/products/armageddon-ork-boyz/">Ork Boyz (x10)</a></td>
        <td class="arm-num">$20</td>
        <td class="arm-num">$29</td>
        <td class="arm-num">$48.00</td>
        <td class="arm-num arm-to">-40%</td>
      </tr>
      <tr>
        <td><a href="/products/armageddon-gretchin/">Gretchin</a></td>
        <td class="arm-num">$15</td>
        <td class="arm-num">$17</td>
        <td class="arm-num">$27.00</td>
        <td class="arm-num arm-to">-37%</td>
      </tr>
      <tr>
        <td><a href="/products/armageddon-wartrakk/">Wartrakk &#9733;</a></td>
        <td class="arm-num">$25</td>
        <td class="arm-num">$27</td>
        <td class="arm-num">$60.00</td>
        <td class="arm-num arm-tg">-55%</td>
      </tr>
      <tr>
        <td><a href="/products/armageddon-big-mek-dakkarig/">Big Mek Dakkarig</a></td>
        <td class="arm-num">$35</td>
        <td class="arm-num">$49</td>
        <td class="arm-num">$65.00</td>
        <td class="arm-num arm-tm">-25%</td>
      </tr>
      <tr class="arm-tot-row">
        <td><strong>Total (each unit individually) &dagger;</strong></td>
        <td class="arm-num">$165</td>
        <td class="arm-num">$225</td>
        <td class="arm-num">$465.50</td>
        <td class="arm-num arm-tg">-52%</td>
      </tr>
    </tbody>
  </table>
</div>
<p class="arm-footnote">&#9733; Best deals in the Ork half &nbsp;&middot;&nbsp; &dagger; Total includes 20 Ork Boyz (2&times; the 10x SKU) to match full box contents &nbsp;&middot;&nbsp; * Average and best prices from top eBay and r/Miniswap listings at time of writing, approx. July 2026 &nbsp;&middot;&nbsp; ** GW retail prices are estimated based on similar models or existing kit prices</p>

<h2>Best Bargains</h2>

<p>Every unit in this box can be considered a bargain. Games Workshop will immediately slap a $40 to $60+ price tag on all these units in the next few months. Most prices you see right now will be relatively great value compared to future prices.</p>

<p>However, this doesn't mean all the individual unit deals we see for Space Marines and Orks can be treated the same way. There are some truly magnificent deals you can find right now for these boxes, especially on the Ork side.</p>

<p>The best discounts against estimated GW retail price in this whole set:</p>

<ul>
  <li><a href="/products/armageddon-warboss/">Ork Warboss</a>, <a href="/products/armageddon-bannernob/">Bannernob</a>, <a href="/products/armageddon-painboy/">Painboy</a>, <a href="/products/armageddon-big-boss/">Big Boss</a>, <a href="/products/armageddon-weirdboy/">Weirdboy</a>, essentially every Ork character is being sold at a fire sale. Discounts sit around 66% off our estimated GW price! You can buy 4 Ork characters for less than the price of a standard $60 Games Workshop kit. As someone planning to run Greentide in 11th edition, having multiples of each of these characters is great, and the price was too good to pass up.</li>
  <li><a href="/products/armageddon-ancient/">Space Marine Ancient</a>, 63% off, the best deal on the Space Marine side by a wide margin. The model is by far the least flashy of the group, but with a bit of hobby magic you can get this model looking table-top ready for the price of a meal.</li>
  <li><a href="/products/armageddon-wartrakk/">Ork Wartrakk</a>, coming in at a 55% discount, this might be the biggest vehicle discount in the set. Picking up 2 or 3 of these for around $75 could be worth it if you want to run Speed Freeks.</li>
  <li><a href="/products/armageddon-captain-with-relic-shield/">Space Marine Captain with Relic Shield</a> and <a href="/products/armageddon-librarian/">Librarian</a>, 40%+ discount on both makes these nice pickups for any Space Marine army. Personally I think the Librarian is the best non-Ork model in the box and would make an awesome hobby project.</li>
</ul>

<h2>Sprue Bundles</h2>

<p>If you really want to save money, buy a sprue bundle. Many of the Armageddon Individual Units are being sold secondhand by the sprue. This means certain characters and units are often sold in a bundle, which is cheaper than buying them individually.</p>

<p>For example:</p>
<ul>
  <li><a href="/products/armageddon-big-boss-painboy-bannernob/">Big Boss + Painboy + Bannernob</a>: $30 - $35</li>
  <li>Ork Boyz + Gretchin: $30 - $40</li>
</ul>

<p>I personally bought the Ork Sprue bundle containing the Painboy, Bannernob, and Big Boss for $20 a sprue on Facebook Marketplace. You might not find a deal like that yourself by the time you read this, but even at $30 that is an average of $10 per character, a 25% savings compared to buying them individually! The <a href="/products/armageddon-ork-boyz/">Ork Boyz</a> and <a href="/products/armageddon-gretchin/">Gretchin</a> sprue bundle is also interesting for anyone starting an Ork army in 2026. Ork Boyz and Gretchin are crucial foundational pieces to an Ork army, helping you control objectives, generate command points, and screen. Unless you are specifically looking for one particular character or unit, sprue bundles provide the best value for your dollar.</p>

<h2>What About the Armageddon Books?</h2>

<p>Don't worry, lore fans and tabletop players, I did not forget about you! You can buy the books from the box set individually as well, but it's difficult to say what is a good deal or not because the value of these is personal. Below you can find price data for all the Warhammer 40K Armageddon book content.</p>

<!-- ── Books Data Table ───────────────────────────────────────────────── -->
<div class="arm-tbl-wrap">
  <table id="arm-bk-tbl">
    <thead>
      <tr>
        <th>Item</th>
        <th>Best Price Seen *</th>
        <th>Avg Market *</th>
        <th>Est. GW **</th>
        <th>Avg vs. GW</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td><a href="/products/armageddon-warhammer-40k-11th-edition-core-rulebook/">Core Rulebook &#9733;</a></td>
        <td class="arm-num">$15</td>
        <td class="arm-num">$19</td>
        <td class="arm-num">$69.00</td>
        <td class="arm-num arm-tg">-72%</td>
      </tr>
      <tr>
        <td><a href="/products/armageddon-chapter-approved-2026-2027-mission-deck/">Chapter Approved 2026-2027: Mission Deck</a></td>
        <td class="arm-num">$25</td>
        <td class="arm-num">$30</td>
        <td class="arm-num">$35.00</td>
        <td class="arm-num arm-tm">-14%</td>
      </tr>
      <tr>
        <td><a href="/products/armageddon-operation-imperator-book/">Imperator Lore Book</a></td>
        <td class="arm-num">$10</td>
        <td class="arm-num">$13</td>
        <td class="arm-num">$20.00</td>
        <td class="arm-num arm-to">-35%</td>
      </tr>
      <tr>
        <td><a href="/products/armageddon-dominatus-narrative-campaign-deck/">Dominatus Narrative Campaign Deck &#9733;</a></td>
        <td class="arm-num">$10 or free</td>
        <td class="arm-num">$12</td>
        <td class="arm-num">$43.50</td>
        <td class="arm-num arm-tg">-72%</td>
      </tr>
    </tbody>
  </table>
</div>
<p class="arm-footnote">&#9733; Best value book purchases &nbsp;&middot;&nbsp; * Average and best prices from top eBay and r/Miniswap listings at time of writing, approx. July 2026 &nbsp;&middot;&nbsp; ** GW retail prices are estimated based on similar models or existing kit prices</p>

<h2>How to Stay Safe Buying Secondhand Warhammer Kits and Products</h2>

<p>Currently, Thrifthammer.com only shows prices from reputable online retailers that have consumer protections in place. These prices may be more expensive than peer-to-peer marketplaces, so please look at places like r/Miniswap and Facebook to find the best of the best deals. However, it's important to stay safe, and for anyone new to these marketplaces, I would recommend the following:</p>

<ul>
  <li>Cross check and scrutinize the seller's photos to verify their listing does not use stock images or have any damage</li>
  <li>Compare the asking price to the average market price in the table above. A price far below the average is a signal to ask more questions.</li>
  <li>Only pay using PayPal Goods and Services, not PayPal Friends and Family (or equivalent), to avoid scams.</li>
  <li>Make sure their account is not brand new, as this could be an indicator of a scam</li>
  <li>When in doubt, don't buy. Follow your gut, don't risk losing your money to save a few dollars.</li>
</ul>

<h2>Warning: Don't Buy Each Box Half Individually</h2>

<p>While I 100% endorse buying individual units from the box, I will warn those who are actively shopping: if you're looking to buy more than 50% of an army half, you might as well buy an entire half of the box. There is a reason why sellers are splitting the boxes into individual units: they can make 2x the money!</p>

<p>Currently, if you were to buy every Space Marine unit individually, you would be spending on average $260 vs $130 (on average) for the <a href="/products/armageddon-box-space-marine-half/">entire box half</a>. For Ork players, it's a bit better at $225 individually compared to the <a href="/products/armageddon-box-ork-half/">Ork half</a>, but still pricey. You can always sell/trade the models you don't want, so make sure to budget and price out potential purchases first.</p>

<h2>Track Every Armageddon Individual Unit With Thrifthammer's Deals Page</h2>

<p>I strongly believe the 11th edition Armageddon starter box will continue to offer top-notch value through this edition. As more and more box sets get into people's hands, supply will eventually hit its peak. Like every 40K edition, we will see some new player turnover, and we should see a constant stream of plastic hitting eBay and other marketplaces. For those interested, Thrifthammer has built a deals page specifically to track individual Armageddon Warhammer 40k units.</p>

<p>You can visit <a href="/factions/warhammer-40k-armageddon-11th-edition/">here</a> to see these individual units with their current prices, or <a href="/accounts/register/">sign up</a> for an account if you want to create a watchlist where you receive pricing alerts for when these prices hit certain thresholds.</p>

<h2>Never Miss a Deal: Join the Thrifthammer Newsletter</h2>

<p>If you are looking to build out your Space Marine or Ork army, sign up for our newsletter! You receive a free weekly email showing you the best deals we are seeing. If you want to customize your newsletter to only show a certain faction, <a href="/accounts/register/">register for a free account</a>.</p>
"""


class Command(BaseCommand):
    """Publish the Armageddon Individual Units Price Guide post (idempotent)."""

    help = 'Publishes the Warhammer 40K Armageddon Box Individual Units Price Guide blog post.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Overwrite the post body/meta even if it already exists.',
        )

    def _static(self, path):
        """Return the absolute static URL for a committed image, or empty string if missing."""
        try:
            return f'{BASE_URL}{staticfiles_storage.url(path)}'
        except Exception:
            return ''

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
            title='Warhammer 40K Armageddon Box: Individual Units Price Guide',
            excerpt=(
                'Compare every Space Marine and Ork unit from the 11th Edition Armageddon box '
                'to estimated GW retail prices. Find the best secondhand deals and learn which '
                'units offer the biggest discounts on eBay and r/Miniswap.'
            ),
            body=BODY,
            status=Post.STATUS_PUBLISHED,
            meta_title='Warhammer 40K Armageddon Box Individual Units Price Guide',
            meta_description=(
                'Compare every Space Marine and Ork Armageddon unit price to GW retail and find '
                'the best secondhand deals before buying the whole 40k box set.'
            ),
            featured_image_url=self._static('images/blog/armageddon-units-guide-header.webp'),
            featured_image_alt=(
                'ThriftHammer Recommends: Must Buy Units, featuring the Warhammer 40,000 '
                'Armageddon boxed set'
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
            post = Post(**defaults, published_at=timezone.now())
            post.save()
            self.stdout.write(
                self.style.SUCCESS(f'Created post (pk={post.pk}, slug={post.slug}).')
            )

        tag_names = ['Warhammer 40K', 'Pricing', 'Orks', 'Space Marines', 'Budget Tips']
        for name in tag_names:
            tag, _ = Tag.objects.get_or_create(name=name)
            post.tags.add(tag)
        self.stdout.write(self.style.SUCCESS(f'Tags attached: {tag_names}'))
