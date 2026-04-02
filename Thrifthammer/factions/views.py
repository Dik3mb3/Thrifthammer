"""
Views for Warhammer faction landing pages.

Each faction page surfaces the best current deals for that faction,
a quick-stats snapshot, an SEO synopsis, and related blog posts.
"""

from django.db.models import Min, Q
from django.utils import timezone
from django.views.generic import DetailView, TemplateView

from blog.models import Post
from products.models import Category, Faction, Product

# Grand alliance groupings for the Warhammer 40K factions index page.
# Factions not listed here appear under whichever group matches their name,
# or are omitted if the category is not 40K.
_IMPERIUM = {
    'Adeptus Mechanicus', 'Astra Militarum', 'Black Templars', 'Blood Angels',
    'Custodes', 'Dark Angels', 'Deathwatch', 'Grey Knights', 'Imperial Knights',
    'Sisters of Battle', 'Space Marines', 'Space Wolves', 'Ultramarines',
}
_CHAOS = {
    "Chaos Space Marines", 'Chaos Knights', 'Death Guard', 'Thousand Sons',
    'World Eaters', 'Chaos Daemons', "Emperor's Children",
}
_XENOS = {
    'Aeldari', 'Drukhari', 'Genestealer Cults', 'Leagues of Votann',
    'Necrons', 'Orks', "T'au Empire", 'Tyranids',
}


class FactionIndexView(TemplateView):
    """
    Warhammer 40K faction directory.

    Groups all 40K factions under Imperium, Chaos, and Xenos headings.
    Live factions (synopsis set) link to their landing page; others
    display a 'Coming Soon' state.
    """

    template_name = 'factions/faction_index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        category_40k = Category.objects.filter(name='Warhammer 40,000').first()
        all_factions = list(
            Faction.objects
            .filter(category=category_40k)
            .order_by('name')
        )

        imperium, chaos, xenos, other = [], [], [], []
        for f in all_factions:
            if f.name in _IMPERIUM:
                imperium.append(f)
            elif f.name in _CHAOS:
                chaos.append(f)
            elif f.name in _XENOS:
                xenos.append(f)
            else:
                other.append(f)

        context['groups'] = [
            {'title': 'Imperium', 'factions': imperium},
            {'title': 'Chaos',    'factions': chaos},
            {'title': 'Xenos',    'factions': xenos},
        ]
        if other:
            context['groups'].append({'title': 'Other', 'factions': other})

        return context


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
        # Include products from the faction itself plus any parent faction
        # (e.g. Emperor's Children page also shows shared CSM kits).
        faction_filter = Q(faction=faction)
        if faction.parent_faction_id:
            faction_filter |= Q(faction=faction.parent_faction)

        products_qs = (
            Product.objects
            .filter(faction_filter, is_active=True, msrp__isnull=False, msrp__gt=0)
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
