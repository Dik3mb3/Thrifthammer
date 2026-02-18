from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .forms import RegistrationForm
from .models import WatchlistItem


def register(request):
    """Register a new user account."""
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Account created! You can now log in.')
            return redirect('accounts:login')
    else:
        form = RegistrationForm()
    return render(request, 'accounts/register.html', {'form': form})


@login_required
def profile(request):
    """Show the user's profile with a summary of their watchlist."""
    watchlist = request.user.watchlist_items.select_related('product').all()
    return render(request, 'accounts/profile.html', {'watchlist': watchlist})


@login_required
def watchlist(request):
    """
    Show all products the user is watching, with current prices and alerts.

    Annotates each item with a price_dropped flag when the current best
    price is below the user's target price.
    """
    items = (
        WatchlistItem.objects
        .filter(user=request.user)
        .select_related('product', 'product__category', 'product__faction')
        .prefetch_related('product__current_prices__retailer')
        .order_by('-created_at')
    )

    # Annotate each item with current best price and price-drop flag
    enriched = []
    for item in items:
        best = item.product.get_cheapest_price()
        price_dropped = (
            best is not None
            and item.target_price is not None
            and best.price < item.target_price
        )
        enriched.append({
            'item': item,
            'best': best,
            'price_dropped': price_dropped,
        })

    return render(request, 'accounts/watchlist.html', {
        'enriched': enriched,
        'total': len(enriched),
    })
