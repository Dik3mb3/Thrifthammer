from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from prices.models import CurrentPrice
from products.models import Product

from .forms import CollectionItemForm
from .models import CollectionItem


@login_required
def my_collection(request):
    """
    Show the user's full collection with stats.

    MSRP reference: GW's live CurrentPrice for each product (retailer_id=1).
    Falls back to product.msrp when GW has no listed price.
    price_paid is stored per-unit; total_spent = price_paid × quantity.
    """
    items = list(
        CollectionItem.objects
        .filter(user=request.user)
        .select_related('product')
    )

    # Collect all product IDs for the GW price lookup (including wishlist so
    # the MSRP column is populated on every row, not just non-wishlist).
    all_product_ids = list({i.product_id for i in items})
    non_wishlist = [i for i in items if i.status != 'wishlist']

    # GW live prices keyed by product_id (retailer_id=1 = Games Workshop)
    gw_price_map = {}
    if all_product_ids:
        for row in CurrentPrice.objects.filter(
            product_id__in=all_product_ids,
            retailer_id=1,
        ).values('product_id', 'price'):
            if row['price'] is not None:
                gw_price_map[row['product_id']] = row['price']

    def _msrp_ref(item):
        """Return the best MSRP reference: GW live price, else product.msrp."""
        return gw_price_map.get(item.product_id) or item.product.msrp

    # Compute stats in Python — avoids ORM Decimal/Integer type-inference bugs
    # Stats only count non-wishlist items (wishlist = aspirational, not owned).
    total_items = sum(i.quantity for i in non_wishlist)
    total_spent = sum(
        (i.price_paid or Decimal('0')) * i.quantity
        for i in non_wishlist
    )
    total_msrp = sum(
        (_msrp_ref(i) or Decimal('0')) * i.quantity
        for i in non_wishlist
    )
    total_saved = total_msrp - total_spent if total_msrp else Decimal('0')

    # Annotate every item (including wishlist) with its live per-unit MSRP
    for item in items:
        item.msrp_ref = _msrp_ref(item)

    owned    = [i for i in items if i.status == 'owned']
    building = [i for i in items if i.status == 'building']
    painted  = [i for i in items if i.status == 'painted']
    wishlist = [i for i in items if i.status == 'wishlist']

    return render(request, 'collections/my_collection.html', {
        'owned':       owned,
        'building':    building,
        'painted':     painted,
        'wishlist':    wishlist,
        'total_items': total_items,
        'total_spent': total_spent,
        'total_msrp':  total_msrp,
        'total_saved': total_saved,
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
