from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, F
from django.shortcuts import get_object_or_404, redirect, render

from products.models import Product

from .forms import CollectionItemForm
from .models import CollectionItem


@login_required
def my_collection(request):
    """Show the user's full collection with stats."""
    items = CollectionItem.objects.filter(user=request.user).select_related('product')

    # Collection stats
    total_items = items.exclude(status='wishlist').aggregate(total=Sum('quantity'))['total'] or 0
    total_spent = items.exclude(status='wishlist').aggregate(
        total=Sum(F('price_paid') * F('quantity'))
    )['total'] or 0
    total_msrp = 0
    for item in items.exclude(status='wishlist'):
        if item.product.msrp:
            total_msrp += item.product.msrp * item.quantity

    owned = items.filter(status='owned')
    building = items.filter(status='building')
    painted = items.filter(status='painted')
    wishlist = items.filter(status='wishlist')

    return render(request, 'collections/my_collection.html', {
        'owned': owned,
        'building': building,
        'painted': painted,
        'wishlist': wishlist,
        'total_items': total_items,
        'total_spent': total_spent,
        'total_msrp': total_msrp,
        'total_saved': total_msrp - total_spent if total_msrp else 0,
    })


@login_required
def add_to_collection(request, slug):
    """Add a product to the user's collection."""
    product = get_object_or_404(Product, slug=slug)
    existing = CollectionItem.objects.filter(user=request.user, product=product).first()

    if request.method == 'POST':
        form = CollectionItemForm(request.POST, instance=existing)
        if form.is_valid():
            item = form.save(commit=False)
            item.user = request.user
            item.product = product
            item.save()
            messages.success(request, f'"{product.name}" updated in your collection.')
            return redirect('collections:my_collection')
    else:
        form = CollectionItemForm(instance=existing)

    return render(request, 'collections/add_to_collection.html', {
        'form': form,
        'product': product,
    })


@login_required
def remove_from_collection(request, slug):
    """Remove a product from the user's collection."""
    product = get_object_or_404(Product, slug=slug)
    CollectionItem.objects.filter(user=request.user, product=product).delete()
    messages.success(request, f'"{product.name}" removed from your collection.')
    return redirect('collections:my_collection')
