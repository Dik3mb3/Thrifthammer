"""
Views for Warhammer faction landing pages.

Each faction page surfaces the best current deals for that faction,
a quick-stats snapshot, an SEO synopsis, and related blog posts.
"""

from django.db.models import Min
from django.utils import timezone
from django.views.generic import DetailView

from blog.models import Post
from products.models import Faction


class FactionDetailView(DetailView):
    """
    Faction landing page.

    Sections rendered:
    - Hero (name, tagline, optional image)
    - Quick Stats bar (model count, difficulty, painting, playstyle, price range)
    - SEO synopsis block
    - Top Deals (up to 10 products sorted by biggest % discount vs MSRP)
    - Related Blog Posts (via faction's linked blog tag)

    Only factions with a synopsis are considered 'live' — the product
    detail badge only links to the faction page when synopsis is set.
    """

    model = Faction
    template_name = 'factions/faction_detail.html'
    context_object_name = 'faction'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'

    def get_context_data(self, **kwargs):
        """Build deals list and related posts for the faction page."""
        context = super().get_context_data(**kwargs)
        faction = self.object

        # ── Top Deals ────────────────────────────────────────────────────────
        # Annotate each product with its lowest current price, then calculate
        # discount vs MSRP in Python so we can sort without a complex DB expr.
        products_qs = (
            faction.products
            .filter(is_active=True, msrp__isnull=False, msrp__gt=0)
            .prefetch_related('current_prices__retailer')
            .annotate(min_price=Min('current_prices__price'))
            .filter(min_price__isnull=False)
        )

        deals = []
        for product in products_qs:
            discount_pct = float((1 - product.min_price / product.msrp) * 100)
            best_price_obj = (
                product.current_prices
                .filter(not_available=False)
                .order_by('price')
                .first()
            )
            if best_price_obj:
                deals.append({
                    'product': product,
                    'min_price': product.min_price,
                    'discount_pct': round(discount_pct, 1),
                    'retailer': best_price_obj.retailer,
                    'buy_url': best_price_obj.url,
                    'in_stock': best_price_obj.in_stock,
                })

        deals.sort(key=lambda x: x['discount_pct'], reverse=True)
        context['deals'] = deals[:10]

        # ── Related Blog Posts ────────────────────────────────────────────────
        related_posts = []
        if faction.blog_tag:
            related_posts = list(
                Post.objects
                .filter(
                    status='published',
                    tags=faction.blog_tag,
                    published_at__lte=timezone.now(),
                )
                .prefetch_related('tags')
                .order_by('-published_at')[:3]
            )
        context['related_posts'] = related_posts

        return context
