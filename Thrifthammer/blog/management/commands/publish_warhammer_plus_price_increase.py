"""
Management command: publish_warhammer_plus_price_increase

Creates 'Warhammer+ Subscription Price Increases: Here's What Changed'
blog post. Safe to run multiple times (idempotent).

Usage:
    python manage.py publish_warhammer_plus_price_increase
    python manage.py publish_warhammer_plus_price_increase --force
"""

from django.contrib.staticfiles.storage import staticfiles_storage
from django.core.management.base import BaseCommand
from django.utils import timezone

SLUG = 'warhammer-plus-price-increase-2026'
SITE_URL = 'https://thrifthammer.com'


def _static(path):
    try:
        return f'{SITE_URL}{staticfiles_storage.url(path)}'
    except Exception:
        return ''


def _gallery(gallery_id, images):
    """Return a swipeable (scroll-snap) image gallery, no JS required for the swipe itself."""
    slides = '\n'.join(
        f'    <div class="whp-gallery-slide" id="{gallery_id}-{i + 1}">'
        f'<img src="{src}" alt="{alt}" width="{w}" height="{h}" loading="lazy"></div>'
        for i, (src, alt, w, h) in enumerate(images)
    )
    dots = '\n'.join(
        f'    <a href="#{gallery_id}-{i + 1}" class="whp-gallery-dot{" whp-gallery-dot-active" if i == 0 else ""}" '
        f'aria-label="Image {i + 1} of {len(images)}"></a>'
        for i in range(len(images))
    )
    return (
        f'<div class="whp-gallery" data-gallery="{gallery_id}">\n'
        f'  <div class="whp-gallery-track" id="{gallery_id}-track">\n'
        f'{slides}\n'
        f'  </div>\n'
        f'  <div class="whp-gallery-nav">\n'
        f'{dots}\n'
        f'  </div>\n'
        f'</div>'
    )


MODELS_GALLERY = _gallery('whp-models', [
    (_static('images/blog/warhammer-plus-price-increase-2026-40k-model.webp'),
     '2026 Warhammer 40K Warhammer+ exclusive Space Marine miniature', 700, 967),
    (_static('images/blog/warhammer-plus-price-increase-2026-aos-model.webp'),
     '2026 Age of Sigmar Warhammer+ exclusive Chaos miniature', 700, 914),
    (_static('images/blog/warhammer-plus-price-increase-2026-yearbook.webp'),
     'Warhammer Yearbook 2026 cover', 700, 630),
])


BODY = """\
<p class="post-lead">Games Workshop has raised Warhammer+ subscription prices for only the second time since the service launched in 2021. Here's exactly what changed and the new pricing.</p>

<h2>Warhammer+ Subscription Prices Increase</h2>

<p>Games Workshop has officially increased the price of its Warhammer+ subscription, raising the cost of both monthly and annual memberships. This is the subscription's second price increase since the service was released in 2021, with the first increase coming in August 2023.</p>

<p>Check out the chart below to see the new Warhammer+ prices compared with previous prices.</p>

<!-- ── PRICE TABLES ───────────────────────────────────────────────────────── -->
<style>
.whp-tbl-wrap {
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
  width: 100%;
  margin: var(--sp-6, 1.5rem) 0;
  border-radius: 6px;
  border: 1px solid var(--border-subtle, rgba(255,255,255,0.08));
}
.whp-tbl {
  min-width: 420px;
  width: 100%;
  border-collapse: collapse;
  font-size: 0.88rem;
  background: var(--bg-card, #1a1b1c);
}
.whp-tbl thead th {
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
.whp-tbl tbody tr {
  border-bottom: 1px solid var(--border-subtle, rgba(255,255,255,0.06));
}
.whp-tbl tbody tr:last-child { border-bottom: none; }
.whp-tbl tbody tr:nth-child(even) { background: rgba(255,255,255,0.03); }
.whp-tbl td {
  padding: 0.55rem 0.75rem;
  vertical-align: middle;
  color: var(--text-primary, #e8e8e8);
}
.whp-num { text-align: right; }
.whp-up { color: #d44040; font-weight: 600; }
.whp-note { font-size: 0.72rem; color: var(--text-muted); margin-top: 0.25rem; font-style: italic; }
.whp-tbl-row {
  display: flex;
  gap: 1.25rem;
  flex-wrap: wrap;
  margin: 1rem 0;
}
.whp-tbl-row > div { flex: 1 1 300px; }
.whp-tbl-row .whp-tbl-wrap { margin: 0.35rem 0 0 0; }
</style>

<div class="whp-tbl-row">
  <div>
    <h3>New U.S. Warhammer+ Subscription Prices</h3>
    <p class="whp-note">Prices shown are for the United States.</p>
    <div class="whp-tbl-wrap">
      <table class="whp-tbl">
        <thead>
          <tr>
            <th>Subscription</th>
            <th>Previous Price</th>
            <th>New Price</th>
            <th>Price Increase</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td>Monthly</td>
            <td class="whp-num">$6.99</td>
            <td class="whp-num">$8.49</td>
            <td class="whp-num whp-up">+21.5%</td>
          </tr>
          <tr>
            <td>Annual</td>
            <td class="whp-num">$59.99</td>
            <td class="whp-num">$74.99</td>
            <td class="whp-num whp-up">+25.0%</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>

  <div>
    <h3>New UK Warhammer+ Subscription Prices</h3>
    <p class="whp-note">Prices shown are for the United Kingdom.</p>
    <div class="whp-tbl-wrap">
      <table class="whp-tbl">
        <thead>
          <tr>
            <th>Subscription</th>
            <th>Previous Price</th>
            <th>New Price</th>
            <th>Price Increase</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td>Monthly</td>
            <td class="whp-num">£5.99</td>
            <td class="whp-num">£6.99</td>
            <td class="whp-num whp-up">+16.7%</td>
          </tr>
          <tr>
            <td>Annual</td>
            <td class="whp-num">£49.99</td>
            <td class="whp-num">£61.99</td>
            <td class="whp-num whp-up">+24.0%</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</div>

<h2>What Is Warhammer+?</h2>

<p>Warhammer+ is Games Workshop's digital subscription platform that bundles several exclusive benefits for Warhammer fans.</p>

<p>Subscribers currently receive:</p>

<ul>
  <li>Warhammer TV animations and exclusive shows</li>
  <li>Access to the Warhammer Vault, including older White Dwarf magazines and lore publications</li>
  <li>Premium/full access to the Warhammer 40K and Age of Sigmar apps</li>
  <li>The right to choose one exclusive miniature either from Warhammer 40K or Age of Sigmar every year</li>
</ul>

<p>This is a very popular and well-liked service. Warhammer+ exclusive miniatures are typically the main driver behind people subscribing. These miniatures can often sell for over $50, covering much of the cost of the subscription, essentially subsidizing the cost of the subscription if you choose to go that route.</p>

<p>What has changed:</p>

<ul>
  <li>Monthly and annual prices have increased</li>
  <li>Moving forward, every year you will receive both the Warhammer 40K and Age of Sigmar miniatures instead of just one</li>
  <li>The new addition of an Annual Yearbook, which Games Workshop described as a lavish coffee table book filled with glossy pages with art from the previous year and pictures of model releases from that year</li>
</ul>

<h2>Warhammer+ 2026 Exclusive Models</h2>

<p>If you are curious what exclusive models are part of the 2026 Warhammer+ subscription and the new Annual 2026 Yearbook, see below.</p>

<!-- ── SWIPEABLE MODEL GALLERY ────────────────────────────────────────────── -->
<style>
.whp-gallery { margin: 1.25rem 0; }
.whp-gallery-track {
  display: flex;
  overflow-x: auto;
  scroll-snap-type: x mandatory;
  -webkit-overflow-scrolling: touch;
  scrollbar-width: none;
  border-radius: 10px;
  background: #111318;
}
.whp-gallery-track::-webkit-scrollbar { display: none; }
.whp-gallery-slide {
  flex: 0 0 100%;
  scroll-snap-align: start;
  scroll-snap-stop: always;
  display: flex;
  align-items: center;
  justify-content: center;
}
.whp-gallery-slide img {
  width: 100%;
  height: auto;
  max-height: 480px;
  object-fit: contain;
  display: block;
}
.whp-gallery-nav {
  display: flex;
  justify-content: center;
  gap: 0.5rem;
  margin-top: 0.65rem;
}
.whp-gallery-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: rgba(255,255,255,0.22);
  display: inline-block;
}
.whp-gallery-dot-active { background: #c8922a; }
</style>

MODELS_GALLERY_PLACEHOLDER

<h2>Is Warhammer+ Still Worth It?</h2>

<p>If we are looking at this with a pure value perspective, yes, Warhammer+ is still a great deal and arguably better than it was before.</p>

<p>In a world where companies like Netflix and Xbox raise digital subscriptions almost annually while not adding enough content back, the Warhammer+ subscription raise comes with tangible benefits. The inclusion of both exclusive miniatures more than covers the raise in subscription price. Below you can find the secondhand prices for the exclusive Warhammer miniatures from previous years.</p>

<div class="whp-tbl-row">
  <div>
    <h3>40K Secondhand Prices</h3>
    <div class="whp-tbl-wrap">
      <table class="whp-tbl">
        <thead>
          <tr><th>Miniature</th><th>eBay Price</th></tr>
        </thead>
        <tbody>
          <tr><td>Aeldari: Infinity's Lament</td><td class="whp-num">$64</td></tr>
          <tr><td>Inquisitor Ostromandeus</td><td class="whp-num">$54</td></tr>
          <tr><td>Unbroken</td><td class="whp-num">$46</td></tr>
          <tr><td>Azrakh the Annihilator</td><td class="whp-num">$66</td></tr>
          <tr><td>Operative Umbral-Six*</td><td class="whp-num">$100</td></tr>
          <tr><td><strong>Average Price</strong></td><td class="whp-num"><strong>$66</strong></td></tr>
        </tbody>
      </table>
    </div>
  </div>

  <div>
    <h3>AoS Secondhand Prices</h3>
    <div class="whp-tbl-wrap">
      <table class="whp-tbl">
        <thead>
          <tr><th>Miniature</th><th>eBay Price</th></tr>
        </thead>
        <tbody>
          <tr><td>The Summons</td><td class="whp-num">$66</td></tr>
          <tr><td>Marshal Ashfield and Squire Udo</td><td class="whp-num">$50</td></tr>
          <tr><td>Karlina Von Karstein</td><td class="whp-num">$51</td></tr>
          <tr><td>Mibyllorr Darkfang</td><td class="whp-num">$56</td></tr>
          <tr><td>Vazdrogg Nekk-Choppa</td><td class="whp-num">$55</td></tr>
          <tr><td><strong>Average Price</strong></td><td class="whp-num"><strong>$56</strong></td></tr>
        </tbody>
      </table>
    </div>
  </div>
</div>

<p>With access to both miniatures, you can cover the annual cost 100% (and maybe even make some money back) if you decide to sell both models secondhand. Even better, if you are the type of subscriber to always keep the Warhammer 40K model (never selling), but you have no interest in Age of Sigmar, with this new system your total annual subscription is lower than before because you get access to a miniature that you can easily sell!</p>

<p>However, even though I am positive about the changes to Warhammer+, we are approaching a slippery slope where if Games Workshop sees subscription numbers growing, they might push subscription prices more aggressively over time. I can imagine a world in which Games Workshop raises prices another $1 to $2 in a few years, this time not giving another exclusive miniature, rather relying on giving out products with less secondhand value like a lore book.</p>

<p>Ultimately, whether you continue to subscribe to Warhammer+ is a personal decision. If the price hikes put a strain on your budget, think about selling off one or even both of the exclusive miniatures to subsidize your cost. If you can't afford the initial payment or the monthly cost, unsubscribe. You can always sign up later or find each of the exclusive miniatures selling on platforms like eBay if you really want one.</p>
"""

BODY = BODY.replace('MODELS_GALLERY_PLACEHOLDER', MODELS_GALLERY)


class Command(BaseCommand):
    """Publish the Warhammer+ Price Increase blog post (idempotent)."""

    help = 'Publishes the Warhammer+ Subscription Price Increase blog post.'

    def add_arguments(self, parser):
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
            title="Warhammer+ Subscription Price Increases: Here's What Changed",
            excerpt=(
                "Games Workshop has increased Warhammer+ subscription prices. Here's what's "
                "changed, the new monthly and annual pricing, what Warhammer+ includes, and "
                "whether it's still worth subscribing."
            ),
            body=BODY,
            status=Post.STATUS_PUBLISHED,
            # published_at is NOT here — it never belongs in defaults
            meta_title='Warhammer+ Price Increase (2026): New Subscription Prices Explained',
            meta_description=(
                "Games Workshop increased Warhammer+ subscription prices. See what changed, "
                "the new monthly and annual pricing, and whether it's still worth subscribing."
            ),
            featured_image_url=_static('images/blog/warhammer-plus-price-increase-2026-header.webp'),
            featured_image_alt='Warhammer+ logo with "More Warhammer. More often." crossed out and replaced with "Expensive better?"',
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

        tag_names = ['Warhammer 40K', 'Age of Sigmar', 'Pricing', 'New Releases']
        for name in tag_names:
            tag, _ = Tag.objects.get_or_create(name=name)
            post.tags.add(tag)
        self.stdout.write(self.style.SUCCESS(f'Tags: {tag_names}'))
