"""
Views for the gundam app.

Mirrors products/views.py's product_list/product_detail pattern (search,
filter, sort, pagination; price comparison on the detail page), simplified
since the Gundam catalog doesn't have the Warhammer side's book-format,
UK-region, or GW-reference-price complexity yet.
"""

from django.core.paginator import InvalidPage, Paginator
from django.db.models import Min, Q
from django.shortcuts import get_object_or_404, render

from .models import CurrentPrice, Product, Series

PRODUCTS_PER_PAGE = 30

SORT_OPTIONS = {
    'name':       'name',
    'name_desc':  '-name',
    'price_asc':  'min_price',
    'price_desc': '-min_price',
    'newest':     '-created_at',
}

GRADE_CHOICES = Product.GRADE_CHOICES


def product_list(request):
    """Browse and filter the Gundam catalog by series, grade, and search term."""
    query       = request.GET.get('q', '').strip()
    series_slug = request.GET.get('series', '').strip()
    grade       = request.GET.get('grade', '').strip()
    sort        = request.GET.get('sort', 'name').strip()
    page_number = request.GET.get('page', '1').strip()

    if sort not in SORT_OPTIONS:
        sort = 'name'
    if grade not in dict(GRADE_CHOICES):
        grade = ''

    products = (
        Product.objects
        .filter(is_active=True)
        .select_related('series')
        .annotate(
            min_price=Min(
                'current_prices__price',
                filter=Q(current_prices__not_available=False, current_prices__in_stock=True),
            )
        )
    )

    if query:
        products = products.filter(Q(name__icontains=query) | Q(description__icontains=query))

    if series_slug:
        secondary_pks = Product.objects.filter(secondary_series__slug=series_slug).values('pk')
        products = products.filter(Q(series__slug=series_slug) | Q(pk__in=secondary_pks))

    if grade:
        products = products.filter(grade=grade)

    products = products.order_by(SORT_OPTIONS[sort])

    series_list = list(Series.objects.order_by('name'))

    paginator = Paginator(products, PRODUCTS_PER_PAGE)
    try:
        page_obj = paginator.page(page_number)
    except InvalidPage:
        page_obj = paginator.page(1)

    selected_series_obj = next((s for s in series_list if s.slug == series_slug), None)

    ctx = {
        'page_obj':            page_obj,
        'products':            list(page_obj.object_list),
        'paginator':           paginator,
        'series_list':         series_list,
        'grade_choices':       GRADE_CHOICES,
        'query':               query,
        'selected_series':     series_slug,
        'selected_series_obj': selected_series_obj,
        'selected_grade':      grade,
        'selected_grade_label': dict(GRADE_CHOICES).get(grade, ''),
        'sort':                sort,
        'sort_options': [
            ('name',       'Name: A to Z'),
            ('name_desc',  'Name: Z to A'),
            ('price_asc',  'Price: Low to High'),
            ('price_desc', 'Price: High to Low'),
            ('newest',     'Newest Arrivals'),
        ],
        'total_count': paginator.count,
    }
    return render(request, 'gundam/product_list.html', ctx)


def product_detail(request, slug):
    """Product detail page with price comparison across tracked retailers."""
    product = get_object_or_404(Product.objects.filter(is_active=True).select_related('series'), slug=slug)

    current_prices = list(
        CurrentPrice.objects
        .filter(product=product)
        .select_related('retailer')
        .order_by('not_available', '-in_stock', 'price')
    )

    related_products = list(
        Product.objects
        .filter(series=product.series, is_active=True)
        .exclude(pk=product.pk)
        .select_related('series')
        .annotate(
            min_price=Min(
                'current_prices__price',
                filter=Q(current_prices__not_available=False, current_prices__in_stock=True),
            )
        )
        .order_by('name')[:4]
    )

    return render(request, 'gundam/product_detail.html', {
        'product':          product,
        'current_prices':   current_prices,
        'related_products': related_products,
    })
