"""
UK-specific product views.

Completely isolated from views.py (US side).  No imports from views.py.
UK pages live at /uk/products/ and /uk/products/<slug>/.

All prices are GBP.  Reference price is the games-workshop-uk CurrentPrice
when available, falling back to product.msrp_gbp.
"""

import json

from django.core.cache import cache
from django.core.paginator import InvalidPage, Paginator
from django.db.models import (
    Case,
    DecimalField,
    ExpressionWrapper,
    F,
    FloatField,
    Min,
    OuterRef,
    Q,
    Subquery,
    Value,
    When,
)
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_GET

from accounts.models import WatchlistItem
from calculators.models import UnitType
from prices.models import CurrentPrice

from .models import Category, Faction, Product

PRODUCTS_PER_PAGE = 30

SORT_OPTIONS = {
    'name':       'name',
    'name_desc':  '-name',
    'price_asc':  'min_price',
    'price_desc': '-min_price',
    'newest':     '-created_at',
    'discount':   '-min_discount_pct',
}


def product_list_uk(request):
    """
    UK browse page at /uk/products/.

    Identical structure to the US product_list view but:
    - min_price uses UK retailer prices (GBP) only
    - gw_ref_price uses games-workshop-uk instead of games-workshop
    - ref_price falls back to msrp_gbp (not msrp)
    - Renders products/product_list_uk.html
    """
    query         = request.GET.get('q', '').strip()
    category_slug = request.GET.get('category', '').strip()
    faction_slug  = request.GET.get('faction', '').strip()
    sort          = request.GET.get('sort', 'discount').strip()
    page_number   = request.GET.get('page', '1').strip()

    if sort not in SORT_OPTIONS:
        sort = 'discount'

    list_gen = cache.get('product_list_generation', 0)
    cache_key = (
        f'product_list_uk_v1|gen={list_gen}|q={query}|cat={category_slug}'
        f'|fac={faction_slug}|sort={sort}|page={page_number}'
    )
    cached = cache.get(cache_key)
    if cached:
        return render(request, 'products/product_list_uk.html', cached)

    # Live GW UK price as the discount reference (GBP equivalent of games-workshop on US side)
    gw_ref_price_sq = Subquery(
        CurrentPrice.objects
        .filter(
            product=OuterRef('pk'),
            retailer__slug='games-workshop-uk',
            not_available=False,
            price__isnull=False,
        )
        .order_by('price')
        .values('price')[:1]
    )

    # Only UK retailer in-stock prices for min_price
    _min_price_filter = Q(
        current_prices__not_available=False,
        current_prices__in_stock=True,
        current_prices__retailer__is_uk=True,
    )

    products = (
        Product.objects
        .filter(is_active=True)
        .select_related('category', 'faction')
        .annotate(
            min_price=Min('current_prices__price', filter=_min_price_filter)
        )
        .annotate(gw_ref_price=gw_ref_price_sq)
        .annotate(
            # GBP ref: GW UK live price if tracked, else msrp_gbp
            ref_price=Case(
                When(gw_ref_price__isnull=False, then=F('gw_ref_price')),
                When(msrp_gbp__isnull=False, then=F('msrp_gbp')),
                default=None,
                output_field=DecimalField(),
            )
        )
        .annotate(
            min_discount_pct=Case(
                When(
                    ref_price__gt=0,
                    min_price__isnull=False,
                    then=ExpressionWrapper(
                        (F('ref_price') - F('min_price')) / F('ref_price') * Value(100),
                        output_field=FloatField(),
                    ),
                ),
                default=None,
                output_field=FloatField(),
            )
        )
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

    if sort == 'discount':
        products = products.order_by(F('min_discount_pct').desc(nulls_last=True))
    else:
        products = products.order_by(SORT_OPTIONS[sort])

    categories = list(Category.objects.all())
    if category_slug:
        factions = list(
            Faction.objects
            .filter(category__slug=category_slug)
            .select_related('category')
            .order_by('name')
        )
    else:
        factions = []

    paginator = Paginator(products, PRODUCTS_PER_PAGE)
    try:
        page_obj = paginator.page(page_number)
    except InvalidPage:
        page_obj = paginator.page(1)

    product_list_evaluated = list(page_obj.object_list)

    selected_category_obj = next((c for c in categories if c.slug == category_slug), None)
    selected_faction_obj  = next((f for f in factions  if f.slug == faction_slug),  None)

    ctx = {
        'page_obj':              page_obj,
        'products':              product_list_evaluated,
        'paginator':             paginator,
        'categories':            categories,
        'factions':              factions,
        'query':                 query,
        'selected_category':     category_slug,
        'selected_faction':      faction_slug,
        'selected_category_obj': selected_category_obj,
        'selected_faction_obj':  selected_faction_obj,
        'sort':                  sort,
        'sort_options': [
            ('discount',   'Best Discount'),
            ('price_asc',  'Price: Low to High'),
            ('price_desc', 'Price: High to Low'),
            ('name',       'Name: A to Z'),
            ('name_desc',  'Name: Z to A'),
            ('newest',     'Newest Arrivals'),
        ],
        'total_count': paginator.count,
    }

    cache.set(cache_key, ctx, timeout=900)
    return render(request, 'products/product_list_uk.html', ctx)


def product_detail_uk(request, slug):
    """
    UK product detail page at /uk/products/<slug>/.

    Uses only games-workshop-uk, ebay-uk, amazon-uk prices (GBP).
    gw_ref_price is the GW UK MSRP; falls back to product.msrp_gbp.
    gw_uk_url is the GW UK product page URL (from the CurrentPrice record).
    """
    cache_key  = f'product_detail_uk|{slug}'
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
            .filter(product=product, retailer__is_uk=True)
            .select_related('retailer')
            .order_by('not_available', '-in_stock', 'price')
        )

        # Related products with GBP min_price
        _rp_filter = Q(
            current_prices__not_available=False,
            current_prices__in_stock=True,
            current_prices__retailer__is_uk=True,
        )
        exclude_pk = product.pk
        related_products = list(
            Product.objects
            .filter(faction=product.faction, category=product.category, is_active=True)
            .exclude(pk=exclude_pk)
            .select_related('category', 'faction')
            .annotate(min_price=Min('current_prices__price', filter=_rp_filter))
            .order_by('name')[:4]
        )
        if len(related_products) < 4 and product.faction_id:
            existing_pks = {p.pk for p in related_products} | {exclude_pk}
            more = list(
                Product.objects
                .filter(faction=product.faction, is_active=True)
                .exclude(pk__in=existing_pks)
                .select_related('category', 'faction')
                .annotate(min_price=Min('current_prices__price', filter=_rp_filter))
                .order_by('name')[:4 - len(related_products)]
            )
            related_products.extend(more)
        if len(related_products) < 4:
            existing_pks = {p.pk for p in related_products} | {exclude_pk}
            more = list(
                Product.objects
                .filter(category=product.category, is_active=True)
                .exclude(pk__in=existing_pks)
                .select_related('category', 'faction')
                .annotate(min_price=Min('current_prices__price', filter=_rp_filter))
                .order_by('name')[:4 - len(related_products)]
            )
            related_products.extend(more)

        # GW UK reference price and URL for "View on GW" button
        gw_uk_cp = next(
            (
                cp for cp in current_prices
                if cp.retailer.slug == 'games-workshop-uk'
                and not cp.not_available
                and cp.price
            ),
            None,
        )
        gw_ref_price = gw_uk_cp.price if gw_uk_cp else product.msrp_gbp
        gw_uk_url    = gw_uk_cp.url   if gw_uk_cp else None

        schema_prices = [cp for cp in current_prices if cp.price and not cp.not_available]

        schema_dict: dict = {
            '@context': 'https://schema.org',
            '@type': 'Product',
            'name': product.name,
            'brand': {'@type': 'Brand', 'name': 'Games Workshop'},
        }
        if product.category:
            schema_dict['category'] = product.category.name
        if product.image_url:
            schema_dict['image'] = product.image_url
        if product.description:
            schema_dict['description'] = product.description[:200]
        if product.gw_sku:
            schema_dict['sku'] = product.gw_sku
        if schema_prices:
            schema_dict['offers'] = [
                {
                    '@type': 'Offer',
                    'seller': {'@type': 'Organization', 'name': cp.retailer.name},
                    'price': float(cp.price),
                    'priceCurrency': 'GBP',
                    'availability': (
                        'https://schema.org/InStock' if cp.in_stock
                        else 'https://schema.org/OutOfStock'
                    ),
                    'url': cp.url or '',
                }
                for cp in schema_prices
            ]
        json_ld = json.dumps(schema_dict, ensure_ascii=False)

        # SEO title — same enrichment logic as US side
        _SUFFIX = ' | ThriftHammer'
        _MAX    = 60
        _MIN    = 30
        _name   = product.name
        _max_name_len = _MAX - len(_SUFFIX)
        if len(_name) > _max_name_len:
            _trimmed = _name[:_max_name_len - 1].rsplit(' ', 1)[0]
            _name = _trimmed + '…'
        _base_title = f"{_name}{_SUFFIX}"
        if len(_base_title) < _MIN:
            if product.faction:
                _candidate = f"{_name} — {product.faction.name}{_SUFFIX}"
                if len(_candidate) <= _MAX:
                    _base_title = _candidate
            if len(_base_title) < _MIN:
                _candidate = f"{_name} — Warhammer{_SUFFIX}"
                if len(_candidate) <= _MAX:
                    _base_title = _candidate
        page_title = _base_title

        # Unit datasheets
        _all_unit_types = list(
            UnitType.objects
            .filter(
                product=product,
                is_active=True,
                stat_movement__isnull=False,
                stat_toughness__isnull=False,
            )
            .select_related('faction')
            .prefetch_related('weapon_profiles', 'abilities')
            .order_by('faction__name', 'name')
        )
        _seen = set()
        unit_types = []
        for _u in _all_unit_types:
            _fp = (
                _u.name,
                _u.stat_movement, _u.stat_toughness, _u.stat_save,
                _u.stat_wounds,   _u.stat_leadership, _u.stat_oc,
                _u.stat_invuln,   _u.stat_fnp,
            )
            if _fp not in _seen:
                _seen.add(_fp)
                unit_types.append(_u)

        # Points per pound — 40K products only
        _unit_points = None
        if (
            product.faction_id
            and product.category
            and product.category.slug == 'warhammer-40000'
        ):
            _unit_points = (
                UnitType.objects
                .filter(product=product, faction_id=product.faction_id, is_active=True)
                .values_list('points_cost', flat=True)
                .first()
            )
        pts_per_pound = None
        if _unit_points and current_prices and current_prices[0].price:
            pts_per_pound = round(float(_unit_points) / float(current_prices[0].price), 1)

        cached_ctx = {
            'product':          product,
            'current_prices':   current_prices,
            'schema_prices':    schema_prices,
            'related_products': related_products,
            'gw_ref_price':     gw_ref_price,
            'gw_uk_url':        gw_uk_url,
            'json_ld':          json_ld,
            'page_title':       page_title,
            'unit_types':       unit_types,
            'pts_per_pound':    pts_per_pound,
        }
        cache.set(cache_key, cached_ctx, timeout=1800)

    on_watchlist = (
        request.user.is_authenticated
        and WatchlistItem.objects.filter(
            user=request.user,
            product=cached_ctx['product'],
        ).exists()
    )

    return render(request, 'products/product_detail_uk.html', {
        **cached_ctx,
        'on_watchlist': on_watchlist,
    })


@require_GET
def search_autocomplete_uk(request):
    """
    JSON autocomplete for the UK product list search bar.

    Returns min_price in GBP from UK retailers only.
    """
    query = request.GET.get('q', '').strip()[:100]

    if len(query) < 2:
        return JsonResponse({'results': []})

    cache_key = f'autocomplete_uk_v1|{query.lower()}'
    cached    = cache.get(cache_key)
    if cached is not None:
        return JsonResponse({'results': cached})

    matches = (
        Product.objects
        .filter(is_active=True)
        .filter(Q(name__icontains=query) | Q(gw_sku__icontains=query))
        .annotate(
            min_price=Min(
                'current_prices__price',
                filter=Q(
                    current_prices__not_available=False,
                    current_prices__in_stock=True,
                    current_prices__retailer__is_uk=True,
                ),
            )
        )
        .values('name', 'slug', 'min_price')
        .order_by('name')[:10]
    )

    results = [
        {
            'name':      p['name'],
            'slug':      p['slug'],
            'min_price': str(p['min_price']) if p['min_price'] else None,
        }
        for p in matches
    ]

    cache.set(cache_key, results, timeout=300)
    return JsonResponse({'results': results})
