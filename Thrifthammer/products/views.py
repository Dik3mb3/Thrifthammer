"""
Views for the products app.

Includes the home page, product list (with filtering/sorting/pagination),
product detail (with price comparison), watchlist toggle, and a JSON
endpoint for search autocomplete.

Performance strategy:
- Annotate product list queryset with min_price so the template never
  triggers per-card DB queries (eliminates the N+1 on the list page).
- select_related / prefetch_related on all other querysets.
- Manual cache with stable keys — cache is busted on Product.save().
- Pagination at 30 products per page.
- Autocomplete limited to 10 results, cached 5 minutes.
"""

from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.core.paginator import InvalidPage, Paginator
from django.db.models import DecimalField, Min, OuterRef, Q, Subquery
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET

from accounts.models import WatchlistItem
from prices.models import CurrentPrice

from .models import Category, Faction, Product

# Products shown per page on the list view
PRODUCTS_PER_PAGE = 30

# Allowed sort keys → ORM order_by expressions.
# All values are validated against this whitelist before use to prevent
# any possibility of ORM injection via the sort= query parameter.
SORT_OPTIONS = {
    'name':       'name',
    'name_desc':  '-name',
    'price_asc':  'min_price',   # requires Min annotation (added below)
    'price_desc': '-min_price',  # requires Min annotation (added below)
    'newest':     '-created_at',
}


def home(request):
    """
    Landing page — category grid and recent price drops.

    Cached for 15 minutes because the data only changes when scrapers run.
    """
    cache_key = 'home_page_data'
    ctx = cache.get(cache_key)
    if ctx is None:
        categories = list(Category.objects.all())
        recent_drops = list(
            CurrentPrice.objects
            .select_related('product', 'retailer')
            .filter(product__is_active=True)
            .order_by('-last_seen')[:12]
        )
        ctx = {'categories': categories, 'recent_drops': recent_drops}
        cache.set(cache_key, ctx, timeout=900)  # 15 minutes

    return render(request, 'home.html', ctx)


def product_list(request):
    """
    Browse and search the product catalogue.

    Supports search (q=), category filter, faction filter, sort, and
    pagination. Results are cached per unique parameter combination for
    15 minutes.

    Performance: the queryset is annotated with min_price so the template
    can display the best price without any per-card DB queries (no N+1).
    """
    query        = request.GET.get('q', '').strip()
    category_slug = request.GET.get('category', '').strip()
    faction_slug  = request.GET.get('faction', '').strip()
    sort          = request.GET.get('sort', 'name').strip()
    page_number   = request.GET.get('page', '1').strip()

    # Whitelist sort to prevent ORM injection
    if sort not in SORT_OPTIONS:
        sort = 'name'

    # Stable cache key covers every filter dimension
    cache_key = (
        f'product_list|q={query}|cat={category_slug}'
        f'|fac={faction_slug}|sort={sort}|page={page_number}'
    )
    cached = cache.get(cache_key)
    if cached:
        return render(request, 'products/product_list.html', cached)

    # --- Build queryset ---
    # select_related covers category/faction (avoids N+1 for badges in template).
    # Annotate min_price in a single SQL JOIN so the template shows the best
    # price per card without any additional queries.
    products = (
        Product.objects
        .filter(is_active=True)
        .select_related('category', 'faction')
        .annotate(min_price=Min('current_prices__price'))
    )

    if query:
        products = products.filter(
            Q(name__icontains=query)
            | Q(description__icontains=query)
            | Q(gw_sku__icontains=query)
        )
    if category_slug:
        products = products.filter(category__slug=category_slug)
    if faction_slug:
        products = products.filter(faction__slug=faction_slug)

    products = products.order_by(SORT_OPTIONS[sort])

    # Sidebar dropdowns — small tables, fetched once
    categories = list(Category.objects.all())
    factions   = list(Faction.objects.select_related('category').all())

    # Paginate — evaluate to a plain list so the context is cache-safe
    paginator = Paginator(products, PRODUCTS_PER_PAGE)
    try:
        page_obj = paginator.page(page_number)
    except InvalidPage:
        page_obj = paginator.page(1)

    # Evaluate the page queryset to a list before caching — a lazy QuerySet
    # would re-execute on cache retrieval and lose the annotation.
    product_list_evaluated = list(page_obj.object_list)

    ctx = {
        'page_obj':          page_obj,
        'products':          product_list_evaluated,
        'paginator':         paginator,
        'categories':        categories,
        'factions':          factions,
        'query':             query,
        'selected_category': category_slug,
        'selected_faction':  faction_slug,
        'sort':              sort,
        'sort_options': [
            ('name',       'Name (A–Z)'),
            ('name_desc',  'Name (Z–A)'),
            ('price_asc',  'Price (low to high)'),
            ('price_desc', 'Price (high to low)'),
            ('newest',     'Newest first'),
        ],
        'total_count': paginator.count,
    }

    # Cache for 15 minutes — prices update via scrapers, not in real time
    cache.set(cache_key, ctx, timeout=900)
    return render(request, 'products/product_list.html', ctx)


def product_detail(request, slug):
    """
    Product detail page with full price comparison table and related products.

    The bulk of the context is cached for 30 minutes. Watchlist status is
    per-user and is always fetched fresh outside the cache block.
    """
    cache_key  = f'product_detail|{slug}'
    cached_ctx = cache.get(cache_key)

    if cached_ctx is None:
        product = get_object_or_404(
            Product.objects
            .select_related('category', 'faction')
            .filter(is_active=True),
            slug=slug,
        )
        current_prices = list(
            CurrentPrice.objects
            .filter(product=product)
            .select_related('retailer')
            .order_by('price')
        )
        related_products = list(
            Product.objects
            .filter(category=product.category, is_active=True)
            .exclude(pk=product.pk)
            .select_related('category', 'faction')
            .order_by('name')[:4]
        )
        savings = product.get_savings_vs_retail()

        cached_ctx = {
            'product':          product,
            'current_prices':   current_prices,
            'related_products': related_products,
            'savings':          savings,
        }
        cache.set(cache_key, cached_ctx, timeout=1800)  # 30 minutes

    # Watchlist status is user-specific — never include in shared cache
    on_watchlist = (
        request.user.is_authenticated
        and WatchlistItem.objects.filter(
            user=request.user,
            product=cached_ctx['product'],
        ).exists()
    )

    return render(request, 'products/product_detail.html', {
        **cached_ctx,
        'on_watchlist': on_watchlist,
    })


@require_GET
def search_autocomplete(request):
    """
    JSON endpoint for the search bar autocomplete dropdown.

    Returns up to 10 matching active products. Query must be at least
    2 characters. Results are cached for 5 minutes.

    Security: query is stripped and capped at 100 characters; only
    name, slug, and msrp are returned — no sensitive fields.
    """
    query = request.GET.get('q', '').strip()[:100]

    if len(query) < 2:
        return JsonResponse({'results': []})

    cache_key = f'autocomplete|{query.lower()}'
    cached    = cache.get(cache_key)
    if cached is not None:
        return JsonResponse({'results': cached})

    matches = (
        Product.objects
        .filter(is_active=True)
        .filter(Q(name__icontains=query) | Q(gw_sku__icontains=query))
        .values('name', 'slug', 'msrp')
        .order_by('name')[:10]
    )

    results = [
        {
            'name': p['name'],
            'slug': p['slug'],
            'msrp': str(p['msrp']) if p['msrp'] else None,
        }
        for p in matches
    ]

    cache.set(cache_key, results, timeout=300)  # 5 minutes
    return JsonResponse({'results': results})


@login_required
def toggle_watchlist(request, slug):
    """
    Toggle a product on/off the authenticated user's watchlist.

    Only POST is honoured — GET silently redirects to the product page
    without making any changes, protecting against link prefetch.
    """
    if request.method != 'POST':
        return redirect('products:detail', slug=slug)

    product = get_object_or_404(Product.objects.filter(is_active=True), slug=slug)
    item, created = WatchlistItem.objects.get_or_create(
        user=request.user, product=product,
    )
    if not created:
        item.delete()

    return redirect('products:detail', slug=slug)
