"""
Publish: The Best Budget Warhammer 40K Hobby Tools Every Player Should Own

Idempotent — safe to run repeatedly. Use --force to overwrite an existing post.
"""
import datetime

from django.core.management.base import BaseCommand
from django.utils import timezone

SLUG = 'best-budget-warhammer-40k-hobby-tools'

BODY = """
<p class="post-intro">Warhammer 40K is already expensive. Your hobby tools should not be.</p>

<p>The right hobby tools will help you save money, improve your paint quality, speed up hobby time,
and reduce frustration. Whether you are building your first army or your tenth, these budget friendly
tools provide the best value for Warhammer players.</p>

<p>Here are the best budget Warhammer hobby tools every player should consider. You can also
<a href="/products/">compare prices on Warhammer kits</a> on ThriftHammer to make sure you are
always getting the best deal before you buy.</p>

<nav class="post-toc">
  <strong>Jump to:</strong>
  <a href="#sprue-cutters">Sprue Cutters</a> &middot;
  <a href="#plastic-glue">Plastic Glue</a> &middot;
  <a href="#hobby-knife">Hobby Knife</a> &middot;
  <a href="#paint-brushes">Paint Brushes</a> &middot;
  <a href="#wet-palette">Wet Palette</a> &middot;
  <a href="#hobby-mat">Hobby Mat</a> &middot;
  <a href="#primer">Primer</a> &middot;
  <a href="#tweezers">Tweezers</a> &middot;
  <a href="#painting-handle">Painting Handle</a> &middot;
  <a href="#storage">Storage</a>
</nav>

<hr>

<h2 id="sprue-cutters">1. Sprue Cutters &mdash; The Absolute Must Have</h2>

<p>If you are still using scissors, a knife, or an exacto blade to remove models from sprues, please
stop immediately. This is one of the easiest ways to damage models or injure yourself.</p>

<p>A good pair of hobby clippers makes building faster, safer, and cleaner. You will spend less time
cleaning up rough cuts and more time actually enjoying the hobby.</p>

<p>Sprue cutters are also one of the best long term purchases. You will use them when building your
first army and still be using them years later.</p>

<div class="blog-product-pair">
  <a href="https://amzn.to/4m35J6N" target="_blank" rel="noopener noreferrer sponsored" class="blog-product-card">
    <img src="https://m.media-amazon.com/images/I/51vjKkXbAeL._AC_SL200_.jpg"
         alt="BXQINLENX Professional 8 PCS Model Tools Kit" loading="lazy" width="120" height="120">
    <div class="blog-product-card-body">
      <div class="blog-product-card-label">Budget Option</div>
      <div class="blog-product-card-name">BXQINLENX 8-Piece Hobby Model Tools Kit</div>
      <span class="blog-product-card-btn">View on Amazon &rarr;</span>
    </div>
  </a>
  <a href="https://amzn.to/4cnoiOT" target="_blank" rel="noopener noreferrer sponsored" class="blog-product-card">
    <img src="https://m.media-amazon.com/images/I/61igeH5eKrL._AC_SL200_.jpg"
         alt="Tamiya Modellers Diagonal Cutters" loading="lazy" width="120" height="120">
    <div class="blog-product-card-body">
      <div class="blog-product-card-label">Recommended</div>
      <div class="blog-product-card-name">Tamiya Modellers Diagonal Cutters</div>
      <span class="blog-product-card-btn">View on Amazon &rarr;</span>
    </div>
  </a>
</div>

<p>When choosing sprue cutters, look for good reviews, sharp blades, and a comfortable grip.
This is one of the highest value hobby purchases you can make.</p>

<hr>

<h2 id="plastic-glue">2. Plastic Glue &mdash; Better Than Super Glue</h2>

<p>Plastic glue is essential for Warhammer miniatures. Super glue is not an adequate replacement.
Plastic glue creates a stronger bond, cleaner finish, and easier assembly.</p>

<p>Super glue still has a place in the hobby, especially when working with resin, metal, or
kitbashing models. However, plastic glue should be your primary tool for standard Warhammer kits.</p>

<a href="https://amzn.to/3NDAB1b" target="_blank" rel="noopener noreferrer sponsored" class="blog-product-card">
  <img src="https://m.media-amazon.com/images/I/71lSWstECJL._AC_SL200_.jpg"
       alt="Tamiya Extra Thin Cement Glue Fine Tip 40ml 2 Pack" loading="lazy" width="120" height="120">
  <div class="blog-product-card-body">
    <div class="blog-product-card-label">Budget Option</div>
    <div class="blog-product-card-name">Tamiya Extra Thin Cement Glue &mdash; Fine Tip 40ml (2 Pack)</div>
    <span class="blog-product-card-btn">View on Amazon &rarr;</span>
  </div>
</a>

<div class="blog-tip-box">
  <strong>ThriftHammer Tip:</strong> Keep both plastic glue and super glue available.
  Each has its own purpose and using the right one will make your hobby experience much better.
</div>

<hr>

<h2 id="hobby-knife">3. Hobby Knife &mdash; One of the Most Underrated Tools</h2>

<p>A hobby knife is one of the lowest cost investments you can make and one of the most useful.
It helps remove mold lines, clean sprue marks, and perform small conversions.</p>

<p>Cleaning mold lines might seem tedious, but it makes a massive difference in your final paint
job. Many hobbyists regret skipping this step once their painting improves.</p>

<a href="https://amzn.to/4bYbXA9" target="_blank" rel="noopener noreferrer sponsored" class="blog-product-card">
  <img src="https://m.media-amazon.com/images/I/619Bd4aDXcL._AC_SL200_.jpg"
       alt="DIYSELF Craft Knife with 10 Extra Blades" loading="lazy" width="120" height="120">
  <div class="blog-product-card-body">
    <div class="blog-product-card-label">Budget Option</div>
    <div class="blog-product-card-name">DIYSELF Precision Craft Knife with 10 Extra #11 Blades</div>
    <span class="blog-product-card-btn">View on Amazon &rarr;</span>
  </div>
</a>

<hr>

<h2 id="paint-brushes">4. Cheap Paint Brushes &mdash; You Do Not Need Expensive Ones</h2>

<p>Many new hobbyists overspend on premium brushes. Expensive brushes require careful maintenance
and experience to fully utilize. For most hobbyists, budget brushes perform perfectly well.</p>

<p>Cheap brushes are ideal for base coating, dry brushing, and washes. These are the tasks that
wear brushes down the fastest, so using budget options saves money long term.</p>

<a href="https://amzn.to/4dni2J0" target="_blank" rel="noopener noreferrer sponsored" class="blog-product-card">
  <img src="https://m.media-amazon.com/images/I/71dAV+POL4L._AC_SL200_.jpg"
       alt="10PC Miniature Paint Brush Set for Fine Detailing" loading="lazy" width="120" height="120">
  <div class="blog-product-card-body">
    <div class="blog-product-card-label">Budget Option</div>
    <div class="blog-product-card-name">10-Piece Miniature Paint Brush Set &mdash; Fine Detailing &amp; 40K</div>
    <span class="blog-product-card-btn">View on Amazon &rarr;</span>
  </div>
</a>

<div class="blog-tip-box">
  <strong>ThriftHammer Tip:</strong> Use cheap brushes for heavy work. Save premium brushes for
  detail work once you gain more experience. Do not waste the money if you have never painted a
  miniature before.
</div>

<hr>

<h2 id="wet-palette">5. Wet Palette &mdash; A Huge Upgrade for Painters</h2>

<p>A wet palette is one of the easiest upgrades you can make to improve painting. It keeps paint
usable longer, improves blending, and reduces wasted paint.</p>

<p>You can even make your own wet palette using a plastic container, paper towel, and wax paper.
This is one of the best budget friendly hacks in the hobby.</p>

<a href="https://amzn.to/4tjOKQ3" target="_blank" rel="noopener noreferrer sponsored" class="blog-product-card">
  <img src="https://m.media-amazon.com/images/I/716Wa3h5EwL._AC_SL200_.jpg"
       alt="The Army Painter Wet Palette for Miniature Painting" loading="lazy" width="120" height="120">
  <div class="blog-product-card-body">
    <div class="blog-product-card-label">Recommended</div>
    <div class="blog-product-card-name">The Army Painter Wet Palette &mdash; Incl. 50 Hydro Sheets</div>
    <span class="blog-product-card-btn">View on Amazon &rarr;</span>
  </div>
</a>

<p>Whether you build your own or buy one, a wet palette is a major quality of life improvement.</p>

<hr>

<h2 id="hobby-mat">6. Hobby Mat &mdash; Protect Your Workspace</h2>

<p>If you are occasionally clumsy, a hobby mat is a smart purchase. It protects your table, makes
cutting safer, and improves workspace organization.</p>

<p>A hobby mat also creates a dedicated hobby area which helps keep your tools organized and
accessible.</p>

<a href="https://amzn.to/4ckf4nq" target="_blank" rel="noopener noreferrer sponsored" class="blog-product-card">
  <img src="https://m.media-amazon.com/images/I/71FQTneo2PL._AC_SL200_.jpg"
       alt="The Army Painter Self-Healing Cutting Mat A4" loading="lazy" width="120" height="120">
  <div class="blog-product-card-body">
    <div class="blog-product-card-label">Recommended</div>
    <div class="blog-product-card-name">The Army Painter Self-Healing Cutting Mat &mdash; A4 Double-Sided</div>
    <span class="blog-product-card-btn">View on Amazon &rarr;</span>
  </div>
</a>

<hr>

<h2 id="primer">7. Primer Spray &mdash; Essential Before Painting</h2>

<p>Primer is one of the most overlooked beginner purchases, but it is critical. Without primer,
paint struggles to stick to models and can chip easily over time.</p>

<p>Primer improves paint quality, prevents chipping, and makes painting significantly easier.
Use <a href="/products/?q=citadel+primer">Citadel primer</a> or one of these budget alternatives
to get the same results at a lower cost.</p>

<div class="blog-product-pair">
  <a href="https://amzn.to/4s6gFlq" target="_blank" rel="noopener noreferrer sponsored" class="blog-product-card">
    <img src="https://m.media-amazon.com/images/I/61S7k2O6MYL._AC_SL200_.jpg"
         alt="The Army Painter Base Primer Matt Black 400ml" loading="lazy" width="120" height="120">
    <div class="blog-product-card-body">
      <div class="blog-product-card-label">Budget Option</div>
      <div class="blog-product-card-name">The Army Painter Base Primer &mdash; Matt Black 400ml</div>
      <span class="blog-product-card-btn">View on Amazon &rarr;</span>
    </div>
  </a>
  <a href="https://amzn.to/4tgtCdp" target="_blank" rel="noopener noreferrer sponsored" class="blog-product-card">
    <img src="https://m.media-amazon.com/images/I/71RtaoftmvL._AC_SL200_.jpg"
         alt="Citadel Chaos Black Spray Primer" loading="lazy" width="120" height="120">
    <div class="blog-product-card-body">
      <div class="blog-product-card-label">Official GW Option</div>
      <div class="blog-product-card-name">Citadel Chaos Black Spray Primer &mdash; 10oz</div>
      <span class="blog-product-card-btn">View on Amazon &rarr;</span>
    </div>
  </a>
</div>

<div class="blog-tip-box">
  <strong>Popular Primer Colors:</strong>
  <ul style="margin:8px 0 0 0;padding-left:18px;">
    <li><strong>Black</strong> &mdash; most forgiving, best for dark armies</li>
    <li><strong>Grey</strong> &mdash; balanced middle ground for any color scheme</li>
    <li><strong>White</strong> &mdash; best for bright or vibrant color schemes</li>
  </ul>
  When in doubt, use black primer.
</div>

<hr>

<h2 id="tweezers">8. Tweezers &mdash; For the Tiny Bits</h2>

<p>Tweezers are extremely helpful when assembling small parts. Many Warhammer kits include tiny
pieces that are difficult to position with fingers. Tweezers help with precise gluing, kitbashing,
and conversions.</p>

<a href="https://amzn.to/3PFQdBS" target="_blank" rel="noopener noreferrer sponsored" class="blog-product-card">
  <img src="https://m.media-amazon.com/images/I/51tmaGDqpHL._AC_SL200_.jpg"
       alt="iFixit Precision Tweezers Set" loading="lazy" width="120" height="120">
  <div class="blog-product-card-body">
    <div class="blog-product-card-label">Recommended</div>
    <div class="blog-product-card-name">iFixit Precision Tweezers Set &mdash; Extra Fine, Angled &amp; Blunt Tips</div>
    <span class="blog-product-card-btn">View on Amazon &rarr;</span>
  </div>
</a>

<hr>

<h2 id="painting-handle">9. Painting Handle &mdash; A Big Quality Upgrade</h2>

<p>Holding models while painting is harder than most people expect. A painting handle improves
control and prevents smudging your work.</p>

<p>You can even use a wine cork as an ultra budget friendly solution. But if you want something
purpose built, these handles make a noticeable difference in comfort and control.</p>

<a href="https://amzn.to/4dnOCdF" target="_blank" rel="noopener noreferrer sponsored" class="blog-product-card">
  <img src="https://m.media-amazon.com/images/I/51c3L01MiUL._AC_SL200_.jpg"
       alt="Painting Handle for Warhammer Miniatures" loading="lazy" width="120" height="120">
  <div class="blog-product-card-body">
    <div class="blog-product-card-label">Budget Option</div>
    <div class="blog-product-card-name">Warhammer Miniature Painting Handle &mdash; DND &amp; Scale Models</div>
    <span class="blog-product-card-btn">View on Amazon &rarr;</span>
  </div>
</a>

<hr>

<h2 id="storage">10. Storage and Hobby Organizer</h2>

<p>Once you start the hobby, tools and models multiply quickly. A simple organizer keeps your
workspace clean and prevents losing tools. You do not need anything fancy. Empty boxes, plastic
bins, and cabinets work perfectly for storing your pile of shame.</p>

<div class="blog-product-pair">
  <a href="https://amzn.to/4cjJg20" target="_blank" rel="noopener noreferrer sponsored" class="blog-product-card">
    <img src="https://m.media-amazon.com/images/I/71zUDsxzCGL._AC_SL200_.jpg"
         alt="CRAFTSMAN Lockable Tool Box 13-inch" loading="lazy" width="120" height="120">
    <div class="blog-product-card-body">
      <div class="blog-product-card-label">Option 1</div>
      <div class="blog-product-card-name">CRAFTSMAN Lockable Tool Box &mdash; 13 Inch Red/Black</div>
      <span class="blog-product-card-btn">View on Amazon &rarr;</span>
    </div>
  </a>
  <a href="https://amzn.to/4v5IsoV" target="_blank" rel="noopener noreferrer sponsored" class="blog-product-card">
    <img src="https://m.media-amazon.com/images/I/71LA9eeGDsL._AC_SL200_.jpg"
         alt="Geinxurn 3-Drawer Mini Tool Box" loading="lazy" width="120" height="120">
    <div class="blog-product-card-body">
      <div class="blog-product-card-label">Option 2</div>
      <div class="blog-product-card-name">Geinxurn 3-Drawer Stackable Mini Tool Box &mdash; Magnetic Lock</div>
      <span class="blog-product-card-btn">View on Amazon &rarr;</span>
    </div>
  </a>
</div>

<hr>

<div class="blog-top3-box">
  <h3>My Top 3 Must Buy Budget Tools</h3>
  <p style="margin-bottom:12px;">If you are just starting out, buy these first:</p>
  <ol>
    <li>Sprue Cutters</li>
    <li>Plastic Glue</li>
    <li>Cheap Brush Set</li>
  </ol>
  <p style="margin-top:12px;font-size:0.9rem;">These three tools form the core of your hobby setup.
  Everything else can be added over time.</p>
</div>

<h2>Final Thoughts</h2>

<p>Warhammer 40K is expensive, but your hobby tools do not need to be. These budget friendly tools
provide the best value and improve your hobby experience without breaking the bank.</p>

<p>Start with the essentials, build your collection over time, and focus on tools that make your
hobbying easier and less frustrating.</p>

<p>Once you have your tools sorted, use <a href="/">ThriftHammer</a> to make sure you are always
buying your kits at the best price. You can also use our
<a href="/army-calculator/">Army Calculator</a> to plan your next army before you spend a penny,
or check out the <a href="/faq/">FAQ</a> for more money saving tips.</p>

<p>Special thanks to the communities at
<a href="https://www.reddit.com/r/DealHammer/" target="_blank" rel="noopener">r/DealHammer</a> and
<a href="https://www.reddit.com/r/Warhammer/" target="_blank" rel="noopener">r/Warhammer</a>
for suggestions, feedback, and support.</p>

<div class="blog-tip-box" style="margin-top:32px;">
  <strong>Affiliate Disclosure:</strong> ThriftHammer is supported by readers. Some links on this
  page are affiliate links, which means we may earn a small commission if you make a purchase through
  them at no extra cost to you. We only recommend tools and products that offer strong value to
  Warhammer players. Using these links helps support the site and keeps ThriftHammer free to use.
</div>
"""


class Command(BaseCommand):
    """Publish the Budget Warhammer 40K Hobby Tools guide."""

    help = 'Publish the budget hobby tools blog post (idempotent)'

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
            self.stdout.write(f'Post "{SLUG}" already exists — skipping. Use --force to overwrite.')
            return

        defaults = {
            'title': 'The Best Budget Warhammer 40K Hobby Tools Every Player Should Own',
            'excerpt': (
                'Warhammer 40K is already expensive. Your hobby tools should not be. '
                'Here are the best budget hobby tools every player should own: sprue '
                'cutters, plastic glue, brushes, primer, and more.'
            ),
            'body': BODY,
            'status': Post.STATUS_PUBLISHED,
            'published_at': datetime.datetime(2026, 4, 1, 10, 0, 0,
                                              tzinfo=datetime.timezone.utc),
            'meta_title': 'Best Budget Warhammer 40K Hobby Tools (2026 Guide) | ThriftHammer',
            'meta_description': (
                'The best budget Warhammer 40K hobby tools: sprue cutters, plastic glue, '
                'brushes, primer, wet palette and more. Save money without sacrificing quality.'
            ),
            'featured_image_url': 'https://m.media-amazon.com/images/I/51vjKkXbAeL._AC_SL500_.jpg',
            'featured_image_alt': 'Budget Warhammer 40K hobby tools kit',
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
            'Hobby Tools',
            'Beginner Guide',
            'Budget Tips',
        ]
        for name in tag_names:
            tag, _ = Tag.objects.get_or_create(name=name)
            post.tags.add(tag)

        self.stdout.write(self.style.SUCCESS(
            f'Published: "{post.title}" → /blog/{SLUG}/'
        ))
