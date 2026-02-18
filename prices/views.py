from django.http import JsonResponse
from django.shortcuts import get_object_or_404

from products.models import Product

from .models import PriceHistory


def price_history_api(request, product_slug):
    """Return JSON price history for chart rendering."""
    product = get_object_or_404(Product, slug=product_slug)
    retailer_slug = request.GET.get('retailer', '')

    history = PriceHistory.objects.filter(product=product).select_related('retailer')
    if retailer_slug:
        history = history.filter(retailer__slug=retailer_slug)
    history = history.order_by('recorded_at')[:365]

    data = [
        {
            'date': record.recorded_at.isoformat(),
            'price': float(record.price),
            'retailer': record.retailer.name,
            'in_stock': record.in_stock,
        }
        for record in history
    ]
    return JsonResponse({'product': product.name, 'history': data})
