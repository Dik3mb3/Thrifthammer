"""
Views for the products app.

Includes the home page, product list (with filtering/sorting/pagination),
product detail (with price comparison), watchlist toggle, and a search
endpoint with JSON autocomplete support.

Performance strategy:
- select_related/prefetch_related on all querysets to prevent N+1 queries
- Per-view cache decorators so repeated page loads hit the cache, not the DB
- Pagination at 30 products per page on the list view
- Search autocomplete limited to 10 results
"""

import json

from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.core.paginator import InvalidPage, Paginator
from django.db.models import Min, Q
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import cache_page
from django.views.decorators.http import require_GET

from accounts.models import WatchlistItem
from prices.models import CurrentPrice

from .models import Category, Faction, Product

# How many products to show per page on the list view
PRODUCTS_PER_PAGE = 30

# Valid sort options for the product list; mapped to ORM order_by expressions
SORT_OPTIONS = {
    'name': 'name',
    'name_desc': '-name',
    'price_asc': 'min_price',   # requires annotation
    'price_desc': '-min_price',  # requires annotation
    'newest': '-created_at',
    'savings': '-savings_pct',   # requires annotation (not yet stored, so skip for now)
}


def home(request):
    """
    Landing page — featured deals and category grid.

    Cached for 15 minutes since the homepage data changes only when
    scraper runs update prices.
    """
    # Cache key is fixed because the page is the same for all visitors
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
    Browse and search the product catalog.

    Supports:
    - Full-text search across name and description (q= parameter)
    - Category filter (category= slug)
    - Faction filter (faction= slug)
    - Sort order (sort= parameter, see SORT_OPTIONS)
    - Pagination (page= parameter, 30 per page)

    Cached per unique query string for 15 minutes.
    """
    query = request.GET.get('q', '').strip()
    category_slug = request.GET.get('category', '').strip()
    faction_slug = request.GET.get('faction', '').strip()
    sort = request.GET.get('sort', 'name').strip()

    # Only allow known sort values to prevent ORM injection
    if sort not in SORT_OPTIONS:
        sort = 'name'

    # Build a stable cache key from all filter parameters
    cache_key = (
        f'product_list_{query}_{category_slug}_{faction_slug}_{sort}'
        f'_p{request.GET.get("page", 1)}'
    )
    cached = cache.get(cache_key)
    if cached:
        return render(request, 'products/product_list.html', cached)

    # Start with active products; always join category/faction to avoid N+1
    products = Product.objects.filter(is_active=True).select_related('category', 'faction')

    if query:
        products = products.filter(
            Q(name__icontains=query) | Q(description__icontains=query) | Q(gw_sku__icontains=query)
        )
    if category_slug:
        products = products.filter(category__slug=category_slug)
    if faction_slug:
        products = products.filter(faction__slug=faction_slug)

    # For price-based sorting we need the minimum price as a DB annotation
    if sort in ('price_asc', 'price_desc'):
        products = products.annotate(
            min_price=Min('current_prices__price')
        )

    products = products.order_by(SORT_OPTIONS[sort])

    # Fetch sidebar data (small tables; no caching needed)
    categories = Category.objects.all()
    factions = Faction.objects.select_related('category').all()

    # Paginate
    paginator = Paginator(products, PRODUCTS_PER_PAGE)
    page_number = request.GET.get('page', 1)
    try:
        page_obj = paginator.page(page_number)
    except InvalidPage:
        page_obj = paginator.page(1)

    ctx = {
        'page_obj': page_obj,
        'products': page_obj.object_list,
        'paginator': paginator,
        'categories': categories,
        'factions': factions,
        'query': query,
        'selected_category': category_slug,
        'selected_faction': faction_slug,
        'sort': sort,
        'sort_options': [
            ('name', 'Name (A–Z)'),
            ('name_desc', 'Name (Z–A)'),
            ('price_asc', 'Price (low to high)'),
            ('price_desc', 'Price (high to low)'),
            ('newest', 'Newest first'),
        ],
        'total_count': paginator.count,
    }

    # Cache for 15 minutes — prices update via scrapers, not in real time
    cache.set(cache_key, ctx, timeout=900)
    return render(request, 'products/product_list.html', ctx)


def product_detail(request, slug):
    """
    Product detail page with price comparison table and related products.

    Cached for 30 minutes. Cache is busted when the Product is saved
    (see Product.save()) or when a new price is scraped.

    Context includes:
    - product: the Product instance
    - current_prices: all CurrentPrice records, ordered cheapest first
    - on_watchlist: whether the current user has watchlisted this product
    - savings: result of product.get_savings_vs_retail()
    - related_products: up to 4 products in the same category
    """
    cache_key = f'product_detail_{slug}'
    cached_ctx = cache.get(cache_key)

    # Watchlist status is user-specific — never cache it
    if cached_ctx is None:
        product = get_object_or_404(
            Product.objects.select_related('category', 'faction').filter(is_active=True),
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
            'product': product,
            'current_prices': current_prices,
            'related_products': related_products,
            'savings': savings,
        }
        cache.set(cache_key, cached_ctx, timeout=1800)  # 30 minutes

    # Watchlist check is per-user; add it outside the cached block
    on_watchlist = False
    if request.user.is_authenticated:
        on_watchlist = WatchlistItem.objects.filter(
            user=request.user,
            product=cached_ctx['product'],
        ).exists()

    ctx = {**cached_ctx, 'on_watchlist': on_watchlist}
    return render(request, 'products/product_detail.html', ctx)


@require_GET
def search_autocomplete(request):
    """
    JSON endpoint for search autocomplete suggestions.

    Returns up to 10 active products matching the query parameter `q`.
    Results are cached for 5 minutes.

    Security: query is validated to be a non-empty string; max 100 chars.
    Only product name, slug, and msrp are returned — no sensitive data.
    """
    query = request.GET.get('q', '').strip()[:100]  # limit to 100 chars

    if len(query) < 2:
        # Don't bother searching for 0 or 1 character queries
        return JsonResponse({'results': []})

    cache_key = f'autocomplete_{query.lower()}'
    cached = cache.get(cache_key)
    if cached is not None:
        return JsonResponse({'results': cached})

    products = (
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
        for p in products
    ]

    cache.set(cache_key, results, timeout=300)  # 5 minutes
    return JsonResponse({'results': results})


@login_required
def toggle_watchlist(request, slug):
    """
    Add or remove a product from the authenticated user's watchlist.

    Requires POST to prevent accidental toggling from GET requests (e.g. link prefetch).
    """
    if request.method != 'POST':
        return redirect('products:detail', slug=slug)

    product = get_object_or_404(Product.objects.filter(is_active=True), slug=slug)
    item, created = WatchlistItem.objects.get_or_create(user=request.user, product=product)
    if not created:
        item.delete()
    return redirect('products:detail', slug=slug)
