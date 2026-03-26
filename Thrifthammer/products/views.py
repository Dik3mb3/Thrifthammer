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

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.core.mail import send_mail
from django.core.paginator import InvalidPage, Paginator
from django.db.models import Case, DecimalField, ExpressionWrapper, F, FloatField, Min, OuterRef, Q, Subquery, Value, When
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from accounts.models import WatchlistItem
from prices.models import CurrentPrice

from .forms import IssueReportForm
from .models import Category, Faction, NewsletterSignup, Product


# ---------------------------------------------------------------------------
# Hot Deals selection strategy
# ---------------------------------------------------------------------------
# Isolated function — change SPOTLIGHT_COUNT or the scoring formula here to
# adjust which deals appear on the home page without touching the view.

SPOTLIGHT_COUNT = 10  # Number of deals to show in the Top 10 Best Deals section


def _get_spotlight_deals(count=SPOTLIGHT_COUNT):
    """
    Return the top deals by discount percentage for the home page.

    Selection strategy:
    - Only active products with both a current price and an MSRP set.
    - Only in-stock, available entries.
    - Excludes Games Workshop (buying from GW at MSRP is never a "deal").
    - Deduplicated by product — only the single best (lowest) price per product.
    - Ranked by discount % vs GW live price (or MSRP fallback) — same reference
      used by the browse page, so rankings are consistent.
    - Returns at most `count` results.

    Returns:
        list[CurrentPrice]: Evaluated list with .product and .retailer
        pre-fetched and a .discount_pct_vs_ref attribute (float) attached
        for display.
    """
    # Fetch the live GW price per product (used as discount reference when available)
    gw_prices = dict(
        CurrentPrice.objects
        .filter(
            retailer__slug='games-workshop',
            not_available=False,
            price__isnull=False,
        )
        .values_list('product_id', 'price')
    )

    # Fetch all active, priced, in-stock entries from non-GW retailers
    candidates = list(
        CurrentPrice.objects
        .select_related('product', 'retailer')
        .filter(
            product__is_active=True,
            product__msrp__isnull=False,
            product__msrp__gt=0,
            price__isnull=False,
            in_stock=True,
            not_available=False,
        )
        .exclude(retailer__slug='games-workshop')
        .order_by('product_id', 'price')  # cheapest first per product
    )

    # Deduplicate: keep only the best (lowest) price per product
    seen_products: set = set()
    unique = []
    for cp in candidates:
        if cp.product_id not in seen_products:
            seen_products.add(cp.product_id)
            unique.append(cp)

    # Compute discount % against GW live price (or MSRP fallback) and keep
    # only entries with a positive discount — same ref_price logic as the list page.
    discounted = []
    for cp in unique:
        ref = gw_prices.get(cp.product_id) or cp.product.msrp
        if ref and ref > 0 and cp.price is not None:
            pct = float((ref - cp.price) / ref * 100)
            if pct > 0:
                cp.discount_pct_vs_ref = round(pct, 1)
                discounted.append(cp)

    # Sort by discount percentage — highest % off first
    discounted.sort(key=lambda cp: cp.discount_pct_vs_ref, reverse=True)
    return discounted[:count]


# Products shown per page on the list view
PRODUCTS_PER_PAGE = 30

# Allowed sort keys → ORM order_by expressions.
# All values are validated against this whitelist before use to prevent
# any possibility of ORM injection via the sort= query parameter.
SORT_OPTIONS = {
    'name':       'name',
    'name_desc':  '-name',
    'price_asc':  'min_price',          # requires Min annotation (added below)
    'price_desc': '-min_price',         # requires Min annotation (added below)
    'newest':     '-created_at',
    'discount':   '-min_discount_pct',  # requires min_discount_pct annotation; NULLs sort last
}


def privacy_policy(request):
    """Static privacy policy page — required for affiliate program applications."""
    return render(request, 'privacy_policy.html')


def about(request):
    """About page — who built ThriftHammer and what it does."""
    return render(request, 'about.html')


def home(request):
    """
    Landing page — Hot Deals section and hero content.

    Cached for 15 minutes because the data only changes when scrapers run.
    The hot deals are selected by _get_spotlight_deals() — edit that
    function to change the selection strategy without touching this view.
    """
    cache_key = 'home_page_data_v4'
    ctx = cache.get(cache_key)
    if ctx is None:
        categories = list(Category.objects.all())
        recent_drops = _get_spotlight_deals()
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

    # Stable cache key covers every filter dimension.
    # Bump the version suffix (v2, v3…) whenever sort_options or the card
    # template change significantly — forces a cache miss on all existing entries.
    # product_list_generation is incremented by the bust_price_caches signal on
    # every CurrentPrice save, invalidating all list page variants at once.
    list_gen = cache.get('product_list_generation', 0)
    cache_key = (
        f'product_list_v3|gen={list_gen}|q={query}|cat={category_slug}'
        f'|fac={faction_slug}|sort={sort}|page={page_number}'
    )
    cached = cache.get(cache_key)
    if cached:
        return render(request, 'products/product_list.html', cached)

    # --- Build queryset ---
    # select_related covers category/faction (avoids N+1 for badges in template).
    #
    # min_price: cheapest available price (not_available=False), matching the
    # same price pool that product_detail uses for current_prices.0.  We do NOT
    # filter by in_stock so a temporarily-OOS listing still counts — identical
    # to the detail page behaviour.
    #
    # gw_ref_price_sq: live GW price (if tracked), used as the discount reference
    # exactly like gw_ref_price in product_detail — falls back to product.msrp.
    # This ensures browse-page and detail-page discount percentages match.
    gw_ref_price_sq = Subquery(
        CurrentPrice.objects
        .filter(
            product=OuterRef('pk'),
            retailer__slug='games-workshop',
            not_available=False,
            price__isnull=False,
        )
        .order_by('price')
        .values('price')[:1]
    )

    products = (
        Product.objects
        .filter(is_active=True)
        .select_related('category', 'faction')
        .annotate(
            min_price=Min(
                'current_prices__price',
                filter=Q(current_prices__not_available=False),
            )
        )
        .annotate(gw_ref_price=gw_ref_price_sq)
        .annotate(
            # ref_price: GW live price when available, else stored msrp —
            # same logic as `gw_ref_price` in product_detail view.
            ref_price=Case(
                When(gw_ref_price__isnull=False, then=F('gw_ref_price')),
                default=F('msrp'),
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

    # Discount sort: NULLs (no live price) must go last, not first.
    # F().desc(nulls_last=True) produces "ORDER BY col DESC NULLS LAST" in PostgreSQL.
    if sort == 'discount':
        products = products.order_by(F('min_discount_pct').desc(nulls_last=True))
    else:
        products = products.order_by(SORT_OPTIONS[sort])

    # Sidebar dropdowns — small tables, fetched once.
    # When a category is active, show only its factions (hierarchical filter).
    categories = list(Category.objects.all())
    if category_slug:
        factions = list(
            Faction.objects
            .filter(category__slug=category_slug)
            .select_related('category')
        )
    else:
        factions = []  # Only show factions once a category is chosen

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
            ('discount',   'Best Discount'),
            ('price_asc',  'Price: Low to High'),
            ('price_desc', 'Price: High to Low'),
            ('name',       'Name: A to Z'),
            ('name_desc',  'Name: Z to A'),
            ('newest',     'Newest Arrivals'),
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
            # not_available entries (price=NULL) always sink to the bottom
            .order_by('not_available', 'price')
        )
        # Related products: prefer same faction+category, then same faction,
        # then same category — avoids the alphabetical Adepta Sororitas problem.
        exclude_pk = product.pk
        related_products = list(
            Product.objects
            .filter(faction=product.faction, category=product.category, is_active=True)
            .exclude(pk=exclude_pk)
            .select_related('category', 'faction')
            .order_by('name')[:4]
        )
        if len(related_products) < 4 and product.faction_id:
            existing_pks = {p.pk for p in related_products} | {exclude_pk}
            more = list(
                Product.objects
                .filter(faction=product.faction, is_active=True)
                .exclude(pk__in=existing_pks)
                .select_related('category', 'faction')
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
                .order_by('name')[:4 - len(related_products)]
            )
            related_products.extend(more)

        savings = product.get_savings_vs_retail()

        # Use GW's own CurrentPrice as the MSRP reference when available —
        # GW's live price is the most accurate benchmark.  Fall back to the
        # stored msrp field if GW has no tracked price for this product.
        gw_cp = next(
            (
                cp for cp in current_prices
                if cp.retailer.slug == 'games-workshop'
                and not cp.not_available
                and cp.price
            ),
            None,
        )
        gw_ref_price = gw_cp.price if gw_cp else product.msrp

        cached_ctx = {
            'product':          product,
            'current_prices':   current_prices,
            'related_products': related_products,
            'savings':          savings,
            'gw_ref_price':     gw_ref_price,
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

    The price shown in the dropdown is the lowest live CurrentPrice
    (same source as the browse page card) so the two always agree.

    Security: query is stripped and capped at 100 characters; only
    name, slug, and min_price are returned — no sensitive fields.
    """
    query = request.GET.get('q', '').strip()[:100]

    if len(query) < 2:
        return JsonResponse({'results': []})

    # v2 — bumped to bust old cached entries that stored msrp instead of min_price
    cache_key = f'autocomplete_v2|{query.lower()}'
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
                filter=Q(current_prices__not_available=False),
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

    cache.set(cache_key, results, timeout=300)  # 5 minutes
    return JsonResponse({'results': results})


@login_required
@require_http_methods(['POST'])
def toggle_watchlist(request, slug):
    """
    Toggle a product on/off the authenticated user's watchlist.

    POST only.  Supports both standard form POST (redirects back to the
    product page) and AJAX (returns JSON so the page can update in-place
    without creating a duplicate browser-history entry, which caused the
    'Back button needs two clicks' bug).

    AJAX callers must set the ``X-Requested-With: XMLHttpRequest`` header.
    Response: ``{"on_watchlist": true|false}``
    """
    product = get_object_or_404(Product.objects.filter(is_active=True), slug=slug)
    item, created = WatchlistItem.objects.get_or_create(
        user=request.user, product=product,
    )
    if not created:
        item.delete()
        on_watchlist = False
    else:
        on_watchlist = True

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'on_watchlist': on_watchlist})

    return redirect('products:detail', slug=slug)


@require_http_methods(['GET', 'POST'])
def report_issue(request, slug):
    """
    Let any visitor report a data problem on a product page.

    GET  — renders the report form inside a modal (or as a standalone page
           if JS is disabled / the user navigates directly to the URL).
    POST — validates the form, sends an email to ISSUE_REPORT_EMAIL, then
           redirects back to the product page with a flash message.

    No login required — anonymous reports are accepted so that casual
    visitors can flag stale prices without creating an account.
    """
    product = get_object_or_404(
        Product.objects.filter(is_active=True),
        slug=slug,
    )

    if request.method == 'POST':
        form = IssueReportForm(request.POST)
        if form.is_valid():
            issue_label = dict(IssueReportForm.ISSUE_TYPE_CHOICES).get(
                form.cleaned_data['issue_type'],
                form.cleaned_data['issue_type'],
            )
            description   = form.cleaned_data['description']
            contact_email = form.cleaned_data.get('contact_email') or 'Anonymous'

            body = (
                f"Product : {product.name} (SKU: {product.gw_sku})\n"
                f"Page    : https://www.thrifthammer.com/products/{product.slug}/\n\n"
                f"Issue   : {issue_label}\n\n"
                f"Details :\n{description}\n\n"
                f"Reporter: {contact_email}"
            )

            send_mail(
                subject=f'[ThriftHammer] Issue Report — {product.name}',
                message=body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[settings.ISSUE_REPORT_EMAIL],
                fail_silently=True,  # never crash the user's page on email failure
            )

            messages.success(
                request,
                'Thanks for the report! We review every submission and will '
                'update the data as quickly as possible.',
            )
            return redirect('products:detail', slug=slug)
        # form invalid — fall through to re-render with errors
    else:
        form = IssueReportForm()

    return render(request, 'products/report_issue.html', {
        'product': product,
        'form':    form,
    })


@require_POST
def newsletter_signup(request):
    """
    Save an email address for the weekly deal alerts opt-in.

    POST only. Redirects back to the home page with a flash message.
    Gracefully handles duplicate signups and invalid addresses.
    """
    email = request.POST.get('email', '').strip().lower()
    if not email:
        messages.error(request, 'Please enter a valid email address.')
        return redirect('home')

    try:
        validate_email(email)
    except ValidationError:
        messages.error(request, 'Please enter a valid email address.')
        return redirect('home')

    _, created = NewsletterSignup.objects.get_or_create(email=email)
    if created:
        messages.success(
            request,
            "You're on the list! We'll send you the best weekly deals.",
        )
    else:
        messages.info(request, "You're already signed up for deal alerts.")
    return redirect('home')


def newsletter_unsubscribe(request, token):
    """
    One-click unsubscribe page.

    GET  → show a confirmation page with the subscriber's email.
    POST → delete the NewsletterSignup record and show a farewell message.
    If the token is unknown we still show a neutral success page (prevents
    probing for valid tokens).
    """
    signup = NewsletterSignup.objects.filter(token=token).first()

    if request.method == 'POST':
        if signup:
            signup.delete()
        return render(request, 'products/newsletter_unsubscribed.html')

    return render(request, 'products/newsletter_unsubscribe_confirm.html', {
        'email': signup.email if signup else None,
        'token': token,
    })
