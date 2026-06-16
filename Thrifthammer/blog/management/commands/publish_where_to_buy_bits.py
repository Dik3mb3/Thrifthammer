"""
Publish: Where to Buy Warhammer 40K & Age of Sigmar Bits

Idempotent -- safe to run repeatedly. Use --force to overwrite an existing post.
"""
import datetime

from django.contrib.staticfiles.storage import staticfiles_storage
from django.core.management.base import BaseCommand

BASE_URL = 'https://thrifthammer.com'

SLUG = 'where-to-buy-warhammer-bits'

BODY = """
<p>If you are looking for specific individual bits, there are a number of
online retailers who specialize in legit Warhammer bits or 3D-printed alternatives for your hobby
project. These retailers are not created equal. Prices vary on a bit-by-bit basis, and shipping
can often be the most expensive part of your purchase.</p>

<p>For those of us living in the U.S., buying from these retailers can be excruciating right now.
Tariffs currently in place have significantly impacted shipping prices, and many of the retailers
we cover are headquartered in the United Kingdom or France. Some have suspended U.S. shipping
entirely, while others have raised international shipping costs to uncomfortable levels.</p>

<nav class="post-toc">
  <strong>Jump to:</strong>
  <a href="#how-we-compared">How We Compared</a> &middot;
  <a href="#recommendations">Thrifthammer Recommendations</a> &middot;
  <a href="#local-community">Local Community</a> &middot;
  <a href="#ebay">eBay</a> &middot;
  <a href="#social-media">Social Media</a> &middot;
  <a href="#3d-printing">3D Printing</a> &middot;
  <a href="#resin-bits">Resin Bits</a> &middot;
  <a href="#full-kits">Full Kits</a>
</nav>

<hr>

<h2 id="how-we-compared">How We Compared These Bits Retailers</h2>

<h3>Total Price</h3>
<ul>
  <li>I took a sample of 20 unique individual bits across all retailers and added them to my cart
  to establish a baseline &ldquo;retail price&rdquo;</li>
  <li>Domestic, U.S., and international shipping was then added to the retail price for a
  Total Price (local) and Total Price (U.S.)</li>
  <li>All totals were converted to U.S. dollars using the correct exchange rate at time of
  comparison</li>
</ul>

<h3>Shipping Capabilities</h3>
<ul>
  <li>Does the retailer ship to the U.S?</li>
  <li>How much does shipping affect the overall price?</li>
</ul>

<h3>Customer Experience</h3>
<ul>
  <li>Trustpilot Score - customer reviews on the retailer (limited data on some)</li>
</ul>

<h3>Data Limitations</h3>
<ul>
  <li>A sample of 20 bits is extremely small compared to the thousands of bits sold on some of
  these sites. Take the retail price comparison with a grain of salt. Depending on what you buy,
  these prices could change significantly.</li>
  <li>Retailers categorize their bits differently and stock slightly different items. The original
  sample was 50 SKUs, but it was impossible to find all 50 stocked across every retailer. The
  sample was trimmed to 20 to make the price comparison easier across all sites.</li>
  <li>Warhammer bits are a niche part of a niche community, so gathering customer reviews was
  difficult. Your experience may vary.</li>
</ul>

<style>
/* ── Bits Retailer Comparison Table ── */
#btc-wrap {
  overflow-x: auto;
  margin: 1.5rem 0;
  border-radius: 6px;
}
#btc-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.85rem;
  background: var(--bg-card, #1a1b1c);
  border: 1px solid var(--border-subtle, #2a2e3a);
  border-radius: 6px;
  overflow: hidden;
  white-space: nowrap;
}
#btc-table thead th {
  background: #9a6e10;
  color: #fff;
  padding: 0.6rem 0.85rem;
  text-align: left;
  font-size: 0.76rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  white-space: nowrap;
  border-bottom: 2px solid rgba(255,255,255,0.12);
}
#btc-table thead th[data-sort] {
  cursor: pointer;
  user-select: none;
}
#btc-table thead th[data-sort]:hover {
  background: #b07e18;
}
.btc-arrow {
  display: inline-block;
  margin-left: 0.3rem;
  font-size: 0.68rem;
  opacity: 0.7;
}
#btc-table tbody tr {
  border-bottom: 1px solid var(--border-subtle, rgba(255,255,255,0.06));
  transition: background 0.1s;
}
#btc-table tbody tr:last-child {
  border-bottom: none;
}
#btc-table tbody tr:nth-child(even) {
  background: rgba(255,255,255,0.025);
}
#btc-table tbody tr:hover {
  background: rgba(200,146,26,0.07);
}
#btc-table td {
  padding: 0.55rem 0.85rem;
  vertical-align: middle;
  color: var(--text-primary, #e8e8e8);
}
#btc-table td a {
  color: var(--accent-gold-lt, #d4a832);
  text-decoration: none;
  font-weight: 600;
}
#btc-table td a:hover {
  text-decoration: underline;
}
.btc-ships-yes { color: #5cb85c; font-weight: 600; }
.btc-ships-no  { color: #d9534f; font-weight: 600; }
.btc-na        { color: var(--text-muted, #777); }
.btc-num       { text-align: right; }
.btc-best      { color: var(--accent-gold-lt, #d4a832); font-weight: 700; }
</style>

<div id="btc-wrap">
  <table id="btc-table">
    <thead>
      <tr>
        <th>Retailer</th>
        <th>Country</th>
        <th>Ships to U.S</th>
        <th data-sort="3" class="btc-num">Retail Price <span class="btc-arrow">&#x21C5;</span></th>
        <th data-sort="4" class="btc-num">Total Price - Local <span class="btc-arrow">&#x21C5;</span></th>
        <th data-sort="5" class="btc-num">Total Price - U.S <span class="btc-arrow">&#x21C5;</span></th>
        <th data-sort="6" class="btc-num">Trustpilot Score <span class="btc-arrow">&#x21C5;</span></th>
        <th data-sort="7" class="btc-num">Avg / Bit <span class="btc-arrow">&#x21C5;</span></th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td><a href="https://www.bitsandkits.co.uk/" target="_blank" rel="noopener noreferrer">Bits and Kits</a></td>
        <td>United Kingdom</td>
        <td class="btc-ships-yes">Yes</td>
        <td class="btc-num" data-val="2238">$22.38</td>
        <td class="btc-num" data-val="2747">$27.47</td>
        <td class="btc-num" data-val="3377">$33.77</td>
        <td class="btc-num" data-val="19">1.9/5</td>
        <td class="btc-num" data-val="137">$1.37</td>
      </tr>
      <tr>
        <td><a href="https://www.bitzbox.co.uk/" target="_blank" rel="noopener noreferrer">Bitz Box</a></td>
        <td>United Kingdom</td>
        <td class="btc-ships-yes">Yes</td>
        <td class="btc-num" data-val="2732">$27.32</td>
        <td class="btc-num" data-val="3100">$31.00</td>
        <td class="btc-num" data-val="3736">$37.36</td>
        <td class="btc-num" data-val="47">4.7/5</td>
        <td class="btc-num" data-val="155">$1.55</td>
      </tr>
      <tr>
        <td><a href="https://www.bitzstore.com/" target="_blank" rel="noopener noreferrer">Bitz Store</a></td>
        <td>France</td>
        <td class="btc-ships-yes">Yes</td>
        <td class="btc-num" data-val="2539">$25.39</td>
        <td class="btc-num" data-val="3038">$30.38</td>
        <td class="btc-num" data-val="4339">$43.39</td>
        <td class="btc-num" data-val="36">3.6/5</td>
        <td class="btc-num" data-val="152">$1.52</td>
      </tr>
      <tr>
        <td><a href="https://www.bitzarium.com/" target="_blank" rel="noopener noreferrer">Bitzarium</a></td>
        <td>France</td>
        <td class="btc-ships-no">No</td>
        <td class="btc-num" data-val="2500">$25.00</td>
        <td class="btc-num" data-val="3000">$30.00</td>
        <td class="btc-num btc-na" data-val="9999">N/A</td>
        <td class="btc-num btc-na" data-val="0">N/A</td>
        <td class="btc-num" data-val="150">$1.50</td>
      </tr>
      <tr>
        <td>Egg Head Miniatures</td>
        <td>United Kingdom</td>
        <td class="btc-ships-yes">Yes</td>
        <td class="btc-num" data-val="3900">$39.00</td>
        <td class="btc-num" data-val="4435">$44.35</td>
        <td class="btc-num" data-val="5700">$57.00</td>
        <td class="btc-num" data-val="37">3.7/5</td>
        <td class="btc-num" data-val="222">$2.22</td>
      </tr>
      <tr>
        <td><a href="https://www.bitsforbattle.co.uk/" target="_blank" rel="noopener noreferrer">Bitsforbattle</a></td>
        <td>United Kingdom</td>
        <td class="btc-ships-no">No</td>
        <td class="btc-num" data-val="2302">$23.02</td>
        <td class="btc-num" data-val="2904">$29.04</td>
        <td class="btc-num btc-na" data-val="9999">N/A</td>
        <td class="btc-num btc-na" data-val="0">N/A</td>
        <td class="btc-num" data-val="145">$1.45</td>
      </tr>
      <tr>
        <td><a href="https://thebitzbarn.com/?srsltid=AfmBOorKdvygZRRLhLJxervbk6TEWJFHUrBsxQfTK6M5L5SKporn80Jx" target="_blank" rel="noopener noreferrer">Bitzbarn</a></td>
        <td>United States</td>
        <td class="btc-ships-yes">Yes</td>
        <td class="btc-num btc-best" data-val="2075">$20.75</td>
        <td class="btc-num btc-best" data-val="2675">$26.75</td>
        <td class="btc-num btc-best" data-val="2675">$26.75</td>
        <td class="btc-num btc-na" data-val="0">N/A</td>
        <td class="btc-num btc-best" data-val="134">$1.34</td>
      </tr>
    </tbody>
  </table>
</div>

<hr>

<h2 id="recommendations">Thrifthammer Recommendations</h2>

<h3>United Kingdom</h3>

<p><a href="https://www.bitzbox.co.uk/" target="_blank" rel="noopener noreferrer">Bitzbox</a> is
the clear number one option. Pricing is a little higher, typically 10-15% above the lowest-cost
alternatives, but reviews are consistently excellent across the board. Bitzbox is well regarded in
the community. I found the website to be polished and very easy to navigate.</p>

<p><a href="https://www.bitsandkits.co.uk/" target="_blank" rel="noopener noreferrer">Bits and Kits</a>
and <a href="https://www.bitsforbattle.co.uk/" target="_blank" rel="noopener noreferrer">Bits for Battle</a>
are solid alternatives. Both are very price competitive. Bits and Kits has a long history in the
space, but be aware that recent customer reviews have been negative, so there is a chance you may
run into issues. Bits for Battle is a great option if you live in the UK, but they do not offer
international shipping, so if you are outside the UK this one is off the table.</p>

<h3>United States</h3>

<p>You only have one reasonable domestic option and that is
<a href="https://thebitzbarn.com/?srsltid=AfmBOorKdvygZRRLhLJxervbk6TEWJFHUrBsxQfTK6M5L5SKporn80Jx" target="_blank" rel="noopener noreferrer">Bitz Barn</a>.
The good news is Bitz Barn is pretty great and has some of the best prices across all the
retailers we reviewed. The drawback is a more limited selection of bits compared to the larger
European catalogues, and a website that isn&rsquo;t the best looking or the easiest to
navigate.</p>

<p>If you are willing to pay for international shipping, the UK retailers offer a far more diverse
selection of bits. Just be prepared to add 25% or more to your total order cost when you factor in
shipping. Some of these retailers quoted me $18 shipping on my sub $30 order. My recommendation:
check Bitz Barn first. If you cannot find what you need, hold your order until you have a larger
list of bits you need. The more bits you order at once, the more value you get out of the shipping
cost.</p>

<h3>France</h3>

<p>You cannot go wrong with either
<a href="https://www.bitzstore.com/" target="_blank" rel="noopener noreferrer">Bitzstore</a> or
<a href="https://www.bitzarium.com/" target="_blank" rel="noopener noreferrer">Bitzarium</a>. Both
offer very similar pricing, and selection appeared comparable when browsing across both sites. If
you live in France, these are the obvious go-to options. For international buyers, both ship
worldwide, though Bitzarium has temporarily suspended U.S. shipments due to the current tariff
situation.</p>

<hr>

<h2>Other Sources for Warhammer 40K and Age of Sigmar Bits</h2>

<h3 id="local-community">1. Local Community</h3>

<p><strong>Pros</strong></p>
<ul>
  <li>Bits can often be found for free if you are an active member of a local group. Players are
  frequently willing to donate bits if you simply ask.</li>
  <li>Local hobbyists with 3D printers often offer the best prices and most personalized
  service.</li>
  <li>If you play
  <a href="/products/?category=warhammer-40000&amp;faction=space-marines&amp;sort=discount">Space Marines</a>
  you are nearly guaranteed to find exactly the bits you need due to the sheer size of that
  faction&rsquo;s player base.</li>
</ul>

<p><strong>Cons</strong></p>
<ul>
  <li>You are limited to the bits of armies that local players play/collect. Players of smaller
  or less popular factions like
  <a href="/products/?category=warhammer-40000&amp;faction=adeptus-mechanicus&amp;sort=discount">Adeptus Mechanicus</a>
  may struggle to find what they need.</li>
  <li>Some local game stores ban bits and model trading to protect their own model sales. Be
  mindful of store rules before making offers on premises.</li>
</ul>

<div class="blog-tip-box">
  <strong>How to find a local group:</strong> Search online for local game stores near you. Most
  have Discord communities where players trade bits, do exchanges, and help each other with hobby
  projects. If your current group does not actively trade bits, be the first to offer some unused
  ones from your own collection. Once one person leads, others tend to follow.
</div>

<h3 id="ebay">2. eBay</h3>

<p><strong>Pros</strong></p>
<ul>
  <li>Enormous selection of bits from sellers worldwide.</li>
  <li>Access to &ldquo;job lots,&rdquo; which are bundles of models in poor condition that offer a
  cheaper route to getting spare parts for kit bashing. Strip down old or damaged models for
  components you can use on your next project.</li>
  <li>Trusted marketplace with buyer protections in place to guard you against scams and dodgy
  vendors.</li>
</ul>

<p><strong>Cons</strong></p>
<ul>
  <li>Prices vary wildly. If you are not willing to shop around, you will not find the best
  deal.</li>
  <li>Job lots require work to get into usable condition. Some are in such bad shape that very
  little is salvageable.</li>
</ul>

<div class="blog-tip-box">
  <strong>How to use eBay for bits:</strong>
  <p>Here is a practical example from a real project:</p>
  <p>Hobby Project: Primaris-sizing my
  <a href="/products/?category=warhammer-40000&amp;faction=grey-knights&amp;sort=discount">Grey Knights</a>
  army and kit bashing Grey Knight characters<br>Bits required: Space Marine torsos, heads, and
  legs</p>
  <ol>
    <li>Go to eBay and search &ldquo;Space Marine job lots&rdquo;</li>
    <li>Buy a listing that fits your budget and contains the bits you need</li>
    <li>When it arrives, strip any paint and break each model down into individual components</li>
    <li>A standard Primaris Intercessor has over a dozen individual plastic components. A listing
    of 10 Intercessors could generate 120+ individual bits you can recycle for future
    projects.</li>
  </ol>
  <p>On dedicated bits sites, individual components can range from $0.50 to $2.00 each. If you
  need 10 torsos, 10 heads, and 10 legs, you could be spending $15 to $60 buying individually,
  versus $20 to $40 on a job lot that gets you three to four times the bits.</p>
  <p>If you plan to be a lifelong kit basher, excess bits will save you over and over again. Worst
  case, trade them locally or sell them back on eBay to recoup some of what you spent.</p>
</div>

<h3 id="social-media">3. Social Media Groups</h3>

<p><strong>Pros</strong></p>
<ul>
  <li>Local community feel with the ability to ship bits across regions.</li>
  <li>Access to a larger pool of hobbyists gives you more faction options than your local group
  alone.</li>
</ul>

<p><strong>Cons</strong></p>
<ul>
  <li>Fewer buyer protections compared to eBay or dedicated retailers. Be more cautious with who
  you deal with.</li>
  <li>Stock is limited and unpredictable. Popular listings get snapped up fast.</li>
</ul>

<div class="blog-top3-box">
  <h3>Thrifthammer Recommended Communities:</h3>
  <ul>
    <li><a href="https://www.reddit.com/r/miniswap/" target="_blank" rel="noopener noreferrer">Reddit: r/miniswap</a></li>
    <li><a href="https://www.facebook.com/groups/1893457864307288/" target="_blank" rel="noopener noreferrer">Facebook: Sprue King</a></li>
  </ul>
</div>

<h3 id="3d-printing">4. 3D Printing</h3>

<p><strong>Pros</strong></p>
<ul>
  <li>Access to thousands of STLs, giving you near-unlimited creative freedom for
  conversions.</li>
  <li>Often the cheapest long-term route once you get past the learning curve of 3D printing.</li>
  <li>You can sell or trade bits you print to other hobbyists, which helps offset your hobby
  costs.</li>
</ul>

<p><strong>Cons</strong></p>
<ul>
  <li>3D printing is a hobby within a hobby. There is a real learning curve and trial and error
  involved before you get consistent results.</li>
</ul>

<h3 id="resin-bits">5. Third-Party Resin Bits</h3>

<p><strong>Pros</strong></p>
<ul>
  <li>A diverse range of aesthetic options. Great for truly unique conversions.</li>
  <li>No need to learn 3D printing, but you get a similar level of customization.</li>
  <li>These retailers tend to offer the best customer experience because their businesses run on
  repeat purchases and word of mouth advertising.</li>
</ul>

<p><strong>Cons</strong></p>
<ul>
  <li>Mixing plastic and resin may not appeal to every hobbyist, especially those interested in
  competitive play.</li>
  <li>Third-party resin bits are typically more expensive per bit than Games Workshop plastic or
  3D printing your own.</li>
</ul>

<div class="blog-tip-box">
  <strong>Thrifthammer Recommends:
  <a href="https://archiesforge.com/" target="_blank" rel="noopener noreferrer">Archie&rsquo;s Forge</a></strong>
  <p>Located in the UK, Archie&rsquo;s Forge produces resin conversion bits to support kit bashing
  projects. Well-regarded in the Warhammer community with fair pricing in the $1 to $2 per bit
  range, Archie&rsquo;s Forge is a great option if you are looking for non-Games Workshop bits.
  They also have arguably the best website of any retailer covered in this article. If you are not
  married to plastic bits, Archie&rsquo;s Forge is worth exploring.</p>
</div>

<h3 id="full-kits">6. Buying Full-Priced Kits</h3>

<p><strong>Pros</strong></p>
<ul>
  <li>Brand new components with no risk of receiving damaged or imperfect bits.</li>
  <li>Excess bits from a full kit can be traded or sold to help offset the cost.</li>
</ul>

<p><strong>Cons</strong></p>
<ul>
  <li>The most expensive route if you only need one or two specific components from a kit.</li>
</ul>

<p>Thrifthammer was built for exactly this situation.</p>

<p>At Thrifthammer we help hobbyists find the best prices for new Warhammer kits online. If you
are buying a full kit for the bits, use our <a href="/products/">browse page</a> to compare prices
across retailers and find the best deal before you buy.</p>

<hr>

<h2>Are Warhammer Bits Worth Buying?</h2>

<p>Absolutely, even if you are a committed 3D printer. Whether you are after Games Workshop
plastic bits or resin alternatives, there is a strong community of retailers and hobbyists ready
to help.</p>

<p>3D printing will always offer the cheapest route to producing exactly the bits you need for any
project. But many of us either do not own a printer or are not ready to dive into that side of the
hobby. 3D printing is its own thing, and while the upside is real, Warhammer bits are plentiful
online and available to buy right now.</p>

<h2>Final Thoughts</h2>

<p>Finding quality Warhammer 40K bits and Age of Sigmar bits online has never been easier. Whether
you are searching for rare conversion parts, replacement components, or spare hobby materials there
are solid retailers and marketplaces available regardless of your budget or location.</p>

<p>The best option depends on your budget, your faction, your project goals, and where you live.
By comparing pricing, selection, and availability across multiple sources, hobbyists can save money
while building more unique and personal armies. The retailer comparison in this article is one data
point, not the final word. Price shop, check shipping costs before you commit, and remember that
shipping is often the deciding factor on whether a purchase is actually good value or not.</p>
"""


class Command(BaseCommand):
    """Publish the Where to Buy Warhammer Bits guide."""

    help = 'Publish the Warhammer bits buying guide blog post (idempotent)'

    def _static(self, path):
        """Return the absolute static URL for a committed image, or empty string if missing."""
        try:
            return f'{BASE_URL}{staticfiles_storage.url(path)}'
        except Exception:
            return ''

    def add_arguments(self, parser):
        """Add --force flag to overwrite an existing post."""
        parser.add_argument(
            '--force',
            action='store_true',
            default=False,
            help='Overwrite the post if it already exists.',
        )

    def handle(self, *args, **options):
        """Create or update the blog post."""
        from blog.models import Post, Tag

        existing = Post.objects.filter(slug=SLUG).first()
        if existing and not options['force']:
            self.stdout.write(
                f'Post "{SLUG}" already exists -- skipping. Use --force to overwrite.'
            )
            return

        featured_img = self._static('img/blog/where-to-buy-bits/where-to-buy-bits-featured.png')

        defaults = {
            'title': 'Where to Buy Warhammer 40K and Age of Sigmar Bits',
            'excerpt': (
                'If you are looking for specific individual bits, there are a number of online '
                'retailers who specialize in legit Warhammer bits or 3D-printed alternatives. '
                'UK, US, and France retailers compared by price, shipping, and selection.'
            ),
            'body': BODY,
            'status': Post.STATUS_PUBLISHED,
            'published_at': datetime.datetime(2026, 6, 15, 10, 0, 0,
                                              tzinfo=datetime.timezone.utc),
            'meta_title': 'Where to Buy Warhammer 40K & AoS Bits (2026) | ThriftHammer',
            'meta_description': (
                'The best places to buy Warhammer 40K and Age of Sigmar bits online. '
                'UK, US, and France retailers compared by price, shipping, and selection.'
            ),
            'featured_image_url': featured_img,
            'featured_image_alt': 'Where to Buy Warhammer Bitz - ThriftHammer retailer comparison guide',
        }

        if existing and options['force']:
            for key, value in defaults.items():
                setattr(existing, key, value)
            existing.save()
            post = existing
            self.stdout.write('Updated existing post.')
        else:
            post = Post(slug=SLUG, **defaults)
            post.save()
            self.stdout.write('Created new post.')

        tag_names = [
            'Warhammer 40K',
            'Age of Sigmar',
            'Buying Guide',
            'Bits & Kitbashing',
        ]
        for name in tag_names:
            tag, _ = Tag.objects.get_or_create(name=name)
            post.tags.add(tag)

        self.stdout.write(self.style.SUCCESS(
            f'Published: "{post.title}" -> /blog/{SLUG}/'
        ))
