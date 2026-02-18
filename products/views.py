from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from accounts.models import WatchlistItem
from prices.models import CurrentPrice

from .models import Category, Faction, Product


def home(request):
    """Landing page — featured deals and categories."""
    categories = Category.objects.all()
    recent_drops = CurrentPrice.objects.select_related(
        'product', 'retailer'
    ).order_by('-last_seen')[:12]
    return render(request, 'home.html', {
        'categories': categories,
        'recent_drops': recent_drops,
    })


def product_list(request):
    """Browse / search products."""
    products = Product.objects.select_related('category', 'faction')
    query = request.GET.get('q', '').strip()
    category_slug = request.GET.get('category', '')
    faction_slug = request.GET.get('faction', '')

    if query:
        products = products.filter(
            Q(name__icontains=query) | Q(gw_sku__icontains=query)
        )
    if category_slug:
        products = products.filter(category__slug=category_slug)
    if faction_slug:
        products = products.filter(faction__slug=faction_slug)

    categories = Category.objects.all()
    factions = Faction.objects.all()
    return render(request, 'products/product_list.html', {
        'products': products[:60],
        'categories': categories,
        'factions': factions,
        'query': query,
        'selected_category': category_slug,
        'selected_faction': faction_slug,
    })


def product_detail(request, slug):
    """Product page with price history from all retailers."""
    product = get_object_or_404(Product.objects.select_related('category', 'faction'), slug=slug)
    current_prices = CurrentPrice.objects.filter(product=product).select_related('retailer').order_by('price')
    on_watchlist = False
    if request.user.is_authenticated:
        on_watchlist = WatchlistItem.objects.filter(user=request.user, product=product).exists()
    return render(request, 'products/product_detail.html', {
        'product': product,
        'current_prices': current_prices,
        'on_watchlist': on_watchlist,
    })


@login_required
def toggle_watchlist(request, slug):
    """Add or remove a product from the user's watchlist."""
    product = get_object_or_404(Product, slug=slug)
    item, created = WatchlistItem.objects.get_or_create(user=request.user, product=product)
    if not created:
        item.delete()
    return redirect('products:detail', slug=slug)
