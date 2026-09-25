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

import json
import logging

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.postgres.search import TrigramWordSimilarity
from django.core.cache import cache
from django.core.mail import EmailMultiAlternatives, send_mail
from django.template.loader import render_to_string

logger = logging.getLogger(__name__)
from django.core.paginator import InvalidPage, Paginator
from django.db.models import Case, Count, DecimalField, ExpressionWrapper, F, FloatField, Min, OuterRef, Q, Subquery, Value, When
from django.db.models.functions import Coalesce
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from accounts.models import WatchlistItem
from calculators.models import UnitType
from prices.models import BookFormatPrice, CurrentPrice

from .forms import IssueReportForm
from .models import Category, Faction, IssueReport, NewsletterSignup, Product


# ---------------------------------------------------------------------------
# Hot Deals selection strategy
# ---------------------------------------------------------------------------
# Isolated function — change SPOTLIGHT_COUNT or the scoring formula here to
# adjust which deals appear on the home page without touching the view.

SPOTLIGHT_COUNT = 10  # Number of deals to show in the Top 10 Best Deals section


def _get_spotlight_deals(count=SPOTLIGHT_COUNT, category_name=None, exclude_category=None):
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

    Args:
        count: Maximum number of deals to return.
        category_name: If set, only include products in this category.
        exclude_category: If set, exclude products in this category.

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

    # Fetch all active, priced, in-stock entries from non-GW US retailers.
    # Exclude UK retailers (country='UK') so that GBP prices stored for the
    # UK version never appear as artificially cheap USD deals on the home page.
    qs = (
        CurrentPrice.objects
        .select_related('product', 'retailer', 'product__category')
        .filter(
            product__is_active=True,
            product__msrp__isnull=False,
            product__msrp__gt=0,
            price__isnull=False,
            in_stock=True,
            not_available=False,
        )
        .exclude(retailer__slug='games-workshop')
        .exclude(retailer__is_uk=True)
    )

    if category_name:
        qs = qs.filter(product__category__name=category_name)
    if exclude_category:
        qs = qs.exclude(product__category__name=exclude_category)

    candidates = list(qs.order_by('product_id', 'price'))  # cheapest first per product

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
                cp.discount_pct_vs_ref = int(round(pct))
                discounted.append(cp)

    # Sort by discount percentage — highest % off first
    discounted.sort(key=lambda cp: cp.discount_pct_vs_ref, reverse=True)
    return discounted[:count]


# Products shown per page on the list view
PRODUCTS_PER_PAGE = 30

# Allowed sort keys → ORM order_by expressions.
# All values are validated against this whitelist before use to prevent
# any possibility of ORM injection via the sort= query parameter.
# 'relevance' has no direct field mapping (it orders by the annotated
# name_similarity score instead) — it's listed here only so it passes the
# whitelist check; the actual ordering happens in its own branch below.
SORT_OPTIONS = {
    'name':       'name',
    'name_desc':  '-name',
    'price_asc':  'min_price',          # requires Min annotation (added below)
    'price_desc': '-min_price',         # requires Min annotation (added below)
    'newest':     '-created_at',
    'discount':   '-min_discount_pct',  # requires min_discount_pct annotation; NULLs sort last
    'relevance':  '-name_similarity',   # requires query; requires name_similarity annotation
}

# Trigram word-similarity cutoff for fuzzy/typo-tolerant search matches.
# Tuned empirically against the live catalog: 0.3 (Postgres's own pg_trgm
# default) let unrelated products leak in on multi-word queries — e.g.
# "leman russ" matched random BattleTech products at ~0.36 similarity.
# 0.4 cleanly separates real typo/partial matches (>=0.58 in testing) from
# that noise while still catching one or two letter typos on a real word.
SEARCH_SIMILARITY_THRESHOLD = 0.4


def _search_filter(query, *, include_description=True):
    """
    Build a loose, typo-tolerant product search filter.

    Splits the query into words and requires every word to appear
    (substring match) somewhere across name/SKU/faction/category — this
    alone drops the old "must match one literal contiguous phrase" behavior,
    so word order and which field a term lives in no longer matter.

    Combined (OR) with a Postgres trigram word-similarity match against the
    product name, so a misspelled model name ("intercesor") still finds the
    real product ("Intercessor Squad") instead of returning nothing.

    Callers must annotate the queryset with name_similarity via
    TrigramWordSimilarity(query, 'name') before applying this filter.
    """
    words = query.split()
    word_match_q = Q()
    for word in words:
        field_q = Q(name__icontains=word) | Q(gw_sku__icontains=word) \
            | Q(faction__name__icontains=word) | Q(category__name__icontains=word)
        if include_description:
            field_q |= Q(description__icontains=word)
        word_match_q &= field_q
    return word_match_q | Q(name_similarity__gt=SEARCH_SIMILARITY_THRESHOLD)

# Display order for book format tabs on the product detail page. Formats
# with no BookFormatPrice rows for a given book are simply omitted rather
# than shown empty -- E-Book/Audio Book will start appearing automatically
# once that sourcing work begins, with no template changes needed.
# Labels are pulled from BookFormatPrice.FORMAT_CHOICES (single source of
# truth) rather than duplicated here.
BOOK_FORMAT_VALUE_ORDER = [
    BookFormatPrice.FORMAT_EBOOK,
    BookFormatPrice.FORMAT_AUDIOBOOK,
    BookFormatPrice.FORMAT_SOFTBACK,
    BookFormatPrice.FORMAT_HARDBACK,
]
BOOK_FORMAT_LABELS = dict(BookFormatPrice.FORMAT_CHOICES)


def _category_descendant_ids(categories, root_slug):
    """
    Resolve a category slug to its own pk plus every subcategory pk,
    recursively (e.g. "books-and-novels" -> {books-and-novels, warhammer}).

    Products are tagged to their most specific category (e.g. Horus Heresy
    books are tagged "Warhammer", not "Books and Novels"), so browsing a
    parent category needs this closure or it returns zero results.

    Takes the already-fetched `categories` list rather than querying, since
    callers already load the full table for the sidebar.
    """
    children_of = {}
    for c in categories:
        if c.parent_category_id:
            children_of.setdefault(c.parent_category_id, []).append(c.pk)

    root = next((c for c in categories if c.slug == root_slug), None)
    if root is None:
        return set()

    ids = {root.pk}
    stack = [root.pk]
    while stack:
        pk = stack.pop()
        for child_pk in children_of.get(pk, []):
            if child_pk not in ids:
                ids.add(child_pk)
                stack.append(child_pk)
    return ids


def privacy_policy(request):
    """Static privacy policy page — required for affiliate program applications."""
    return render(request, 'privacy_policy.html')


def faq(request):
    """FAQ page — answers common questions about ThriftHammer and Warhammer pricing."""
    return render(request, 'faq.html')


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
    cache_key = 'home_page_data_v8'
    ctx = cache.get(cache_key)
    if ctx is None:
        categories = list(Category.objects.all())
        deals_40k = _get_spotlight_deals(category_name='Warhammer 40,000')
        deals_other = _get_spotlight_deals(exclude_category='Warhammer 40,000')
        ctx = {'categories': categories, 'deals_40k': deals_40k, 'deals_other': deals_other}
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
    # A text search defaults to relevance ordering rather than discount —
    # "Best Discount" first is a strange default when the user just typed
    # a specific model name. Explicitly choosing a different sort still wins.
    default_sort  = 'relevance' if query else 'discount'
    sort          = request.GET.get('sort', default_sort).strip()
    page_number   = request.GET.get('page', '1').strip()

    # Whitelist sort to prevent ORM injection. 'relevance' only makes sense
    # alongside a query (it orders by similarity to it), so fall back
    # otherwise rather than hitting the missing-annotation error path.
    if sort not in SORT_OPTIONS or (sort == 'relevance' and not query):
        sort = default_sort

    # Fetched once, up front -- needed both for the category-descendant
    # closure below (parent categories like "Books and Novels" have no
    # products of their own; their products live on subcategories like
    # "Warhammer") and to resolve is_books_category before the queryset is
    # built, since it decides which price/sort annotations get used.
    categories = list(Category.objects.all())
    selected_category_obj = next((c for c in categories if c.slug == category_slug), None)

    # True when browsing "Books and Novels" or any of its subcategories —
    # drives the sidebar's Format filter, the "Book Series"/"All Series"
    # label swap, and which price/sort annotation (book_min_price vs
    # min_price) is used below. Covers future subcategories automatically
    # (e.g. a Battletech books subcategory) since it's not slug-hardcoded.
    books_category_ids = _category_descendant_ids(categories, 'books-and-novels')
    is_books_category = bool(selected_category_obj and selected_category_obj.pk in books_category_ids)

    # Which format's price ranks/displays books by (Books and Novels category
    # only -- harmless no-op elsewhere). Defaults to E-Book to match the
    # product detail page's default. Whitelisted against BOOK_FORMAT_LABELS'
    # keys (the same internal BookFormatPrice.FORMAT_* values used there).
    book_format = request.GET.get('book_format', '').strip()
    if book_format not in BOOK_FORMAT_LABELS:
        book_format = BookFormatPrice.FORMAT_EBOOK

    # Resolved here (before the book-format fallback below, which needs to
    # know which currency to check for) -- moved up from its original spot
    # further down in this function.
    #
    # /uk/products/ (see products/urls_uk.py) routes here too, with region
    # forced to 'uk' regardless of session state -- same rationale as
    # product_detail() above.
    if request.path.startswith('/uk/'):
        region = 'uk'
    else:
        region_param = request.GET.get('region', '').strip()
        if region_param in ('us', 'uk'):
            request.session['region'] = region_param
        region = request.session.get('region', 'us')

    # A book batch often launches physical-only (GW added first; Amazon
    # E-Book/Audio Book sourcing comes later, same rollout order used for
    # Horus Heresy Series and Warhammer 40,000 Books) -- if the current
    # format has zero price data anywhere in the selected category/faction
    # scope, every card would show "No price yet" until the user manually
    # switches the Format dropdown. Fall back to the first format in display
    # order that actually has data for this scope instead. Scoped by
    # currency (USD/GBP) so a UK visitor never falls back to a format that
    # only has US data, and vice versa.
    if is_books_category:
        _book_currency = 'GBP' if region == 'uk' else 'USD'
        _scope_q = Q(product__category_id__in=books_category_ids, currency=_book_currency)
        if faction_slug:
            _scope_q &= Q(product__faction__slug=faction_slug)
        if not BookFormatPrice.objects.filter(_scope_q, format=book_format, price__isnull=False).exists():
            for fmt in BOOK_FORMAT_VALUE_ORDER:
                if BookFormatPrice.objects.filter(_scope_q, format=fmt, price__isnull=False).exists():
                    book_format = fmt
                    break

    # Stable cache key covers every filter dimension including region.
    # Bump the version suffix (v2, v3…) whenever sort_options or the card
    # template change significantly — forces a cache miss on all existing entries.
    # product_list_generation is incremented by the bust_price_caches signal on
    # every CurrentPrice save, invalidating all list page variants at once.
    list_gen = cache.get('product_list_generation', 0)
    cache_key = (
        f'product_list_v5|gen={list_gen}|region={region}|q={query}|cat={category_slug}'
        f'|fac={faction_slug}|sort={sort}|page={page_number}|bfmt={book_format}'
    )
    cached = cache.get(cache_key)
    if cached:
        return render(request, 'products/product_list.html', cached)

    # --- Build queryset ---
    # select_related covers category/faction (avoids N+1 for badges in template).
    #
    # min_price: cheapest IN-STOCK price only (not_available=False AND in_stock=True).
    # We intentionally exclude OOS listings so the browse card never shows a price
    # the user can't actually buy at — showing an OOS price as "Best Price" erodes
    # trust.  If a product has no in-stock price, min_price will be NULL and the
    # template will fall through to "No price yet".
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

    # book_min_price: cheapest in-stock price for the selected book_format
    # (E-Book/Audio Book/Paperback/Hardback -- picked via the Format sidebar
    # filter, Books and Novels category only) for book products, sourced
    # from BookFormatPrice instead of CurrentPrice. A Subquery (not a joined
    # Min()) so it can't fan-out against the current_prices join used by
    # min_price above — same reason gw_ref_price_sq above is a Subquery
    # rather than a second annotated Min(). Region-scoped by currency (USD
    # for US, GBP for UK) so a GBP price can never surface as a USD "deal"
    # or vice versa.
    #
    # book_msrp_price: that same format's MSRP-source row -- is_msrp_source
    # for US (GW for Paperback/Hardback, Amazon for E-Book/Audio Book),
    # is_msrp_source_uk for UK (a separate flag with its own database
    # constraint, so the two regions never contend over which row is "the"
    # MSRP reference for a given product+format). Used as the discount
    # reference so "Best Discount" sort/display for books means the same
    # thing it does for miniatures (ref_price vs min_price).
    if region == 'uk':
        book_min_price_sq = Subquery(
            BookFormatPrice.objects
            .filter(
                product=OuterRef('pk'),
                format=book_format,
                not_available=False,
                in_stock=True,
                price__isnull=False,
                currency='GBP',
            )
            .order_by('price')
            .values('price')[:1]
        )
        book_msrp_sq = Subquery(
            BookFormatPrice.objects
            .filter(
                product=OuterRef('pk'),
                format=book_format,
                is_msrp_source_uk=True,
                price__isnull=False,
                currency='GBP',
            )
            .values('price')[:1]
        )
    else:
        book_min_price_sq = Subquery(
            BookFormatPrice.objects
            .filter(
                product=OuterRef('pk'),
                format=book_format,
                not_available=False,
                in_stock=True,
                price__isnull=False,
                currency='USD',
            )
            .order_by('price')
            .values('price')[:1]
        )
        book_msrp_sq = Subquery(
            BookFormatPrice.objects
            .filter(
                product=OuterRef('pk'),
                format=book_format,
                is_msrp_source=True,
                price__isnull=False,
                currency='USD',
            )
            .values('price')[:1]
        )

    # min_price annotation: for UK show only UK retailer prices (GBP),
    # for US exclude UK retailers so GBP prices don't appear as cheap USD deals.
    if region == 'uk':
        _min_price_filter = Q(
            current_prices__not_available=False,
            current_prices__in_stock=True,
            current_prices__retailer__is_uk=True,
        )
    else:
        _min_price_filter = Q(
            current_prices__not_available=False,
            current_prices__in_stock=True,
        ) & ~Q(current_prices__retailer__is_uk=True)

    products = (
        Product.objects
        .filter(is_active=True)
        .select_related('category', 'faction')
        .annotate(
            min_price=Min(
                'current_prices__price',
                filter=_min_price_filter,
            )
        )
        .annotate(gw_ref_price=gw_ref_price_sq)
        .annotate(book_min_price=book_min_price_sq)
        .annotate(book_msrp_price=book_msrp_sq)
        .annotate(
            book_min_discount_pct=Case(
                When(
                    book_msrp_price__gt=0,
                    book_min_price__isnull=False,
                    then=ExpressionWrapper(
                        (F('book_msrp_price') - F('book_min_price')) / F('book_msrp_price') * Value(100),
                        output_field=FloatField(),
                    ),
                ),
                default=None,
                output_field=FloatField(),
            )
        )
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
        products = (
            products
            .annotate(name_similarity=TrigramWordSimilarity(query, 'name'))
            .filter(_search_filter(query))
        )

    if category_slug:
        category_ids = _category_descendant_ids(categories, category_slug)
        if category_slug == 'warcry':
            # Warcry is its own top-level category, but most Warcry warbands
            # are the same physical kit as an existing Age of Sigmar faction
            # product (dual-tagged via secondary_factions rather than given
            # their own category) -- include those here too, same OR-pattern
            # as the secondary_factions faction-level inclusion below.
            warcry_secondary_pks = Product.objects.filter(
                secondary_factions__slug='warcry'
            ).values('pk')
            products = products.filter(
                Q(category_id__in=category_ids) | Q(pk__in=warcry_secondary_pks)
            )
        else:
            products = products.filter(category_id__in=category_ids)
    if faction_slug:
        # Include products whose secondary_factions include this faction too
        # (cross-faction units like Chaos Daemons dual-tagged onto a mono-god
        # faction page). Resolved via a separate pk__in subquery rather than
        # a direct Q(secondary_factions__slug=...) OR-filter, because joining
        # the M2M directly into this queryset would duplicate rows against
        # the current_prices join already used by the min_price annotation
        # above and corrupt Min() -- same pattern already used for this
        # exact reason in factions/views.py's Top Deals query.
        secondary_pks = Product.objects.filter(secondary_factions__slug=faction_slug).values('pk')
        products = products.filter(Q(faction__slug=faction_slug) | Q(pk__in=secondary_pks))

    # Discount sort: NULLs (no live price) must go last, not first.
    # F().desc(nulls_last=True) produces "ORDER BY col DESC NULLS LAST" in PostgreSQL.
    # Books rank by the selected format's price/discount (book_min_price /
    # book_min_discount_pct) instead of the CurrentPrice-based min_price /
    # min_discount_pct used everywhere else -- name/newest sorts are
    # unaffected since they don't reference either. Coalesce falls back to
    # the regular CurrentPrice-based field for Books-and-Novels products
    # that aren't multi-format novels (Codexes, Battletomes, Arcane
    # Journals) -- they only ever populate min_price/min_discount_pct, never
    # book_min_price, so without the fallback they'd always sort dead last
    # regardless of their real discount.
    if is_books_category and sort == 'discount':
        products = products.order_by(
            Coalesce(F('book_min_discount_pct'), F('min_discount_pct')).desc(nulls_last=True)
        )
    elif is_books_category and sort == 'price_asc':
        products = products.order_by(
            Coalesce(F('book_min_price'), F('min_price')).asc(nulls_last=True)
        )
    elif is_books_category and sort == 'price_desc':
        products = products.order_by(
            Coalesce(F('book_min_price'), F('min_price')).desc(nulls_last=True)
        )
    elif sort == 'discount':
        products = products.order_by(F('min_discount_pct').desc(nulls_last=True))
    elif sort == 'relevance':
        products = products.order_by(F('name_similarity').desc(nulls_last=True))
    else:
        products = products.order_by(SORT_OPTIONS[sort])

    # Faction sidebar dropdown — only shown once a category is chosen.
    # Uses the same category-descendant closure as the product filter above,
    # so choosing "Books and Novels" surfaces factions like "Horus Heresy
    # Series" that actually live on its "Warhammer" subcategory.
    if category_slug:
        factions = list(
            Faction.objects
            .filter(category_id__in=_category_descendant_ids(categories, category_slug))
            .select_related('category')
            .order_by('name')
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

    # Resolve selected faction to an object for template title/description use.
    # selected_category_obj / is_books_category were already resolved above,
    # before the queryset was built.
    selected_faction_obj = next((f for f in factions if f.slug == faction_slug), None)

    ctx = {
        'page_obj':               page_obj,
        'products':               product_list_evaluated,
        'paginator':              paginator,
        'categories':             categories,
        'factions':               factions,
        'query':                  query,
        'selected_category':      category_slug,
        'selected_faction':       faction_slug,
        'is_books_category':      is_books_category,
        'selected_category_obj':  selected_category_obj,
        'selected_faction_obj':   selected_faction_obj,
        'selected_book_format':   book_format,
        'selected_book_format_label': BOOK_FORMAT_LABELS[book_format],
        'book_format_options':    [(v, BOOK_FORMAT_LABELS[v]) for v in BOOK_FORMAT_VALUE_ORDER],
        'sort':              sort,
        'sort_options': (
            [('relevance', 'Best Match')] if query else []
        ) + [
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

    The bulk of the context is cached for 30 minutes per region (US/UK).
    Watchlist status is per-user and always fetched fresh outside the cache.

    /uk/products/<slug>/ (see products/urls_uk.py) routes here too, with
    region forced to 'uk' regardless of session state -- a URL under the
    dedicated UK path must always show UK content. ?region=uk on a plain
    /products/<slug>/ URL still works as before via the session.
    """
    if request.path.startswith('/uk/'):
        region = 'uk'
    else:
        region_param = request.GET.get('region', '').strip()
        if region_param in ('us', 'uk'):
            request.session['region'] = region_param
        region = request.session.get('region', 'us')
    cache_key  = f'product_detail|{slug}|{region}'
    cached_ctx = cache.get(cache_key)

    if cached_ctx is None:
        product = get_object_or_404(
            Product.objects
            .select_related('category', 'faction')
            .filter(is_active=True),
            slug=slug,
        )

        # Filter prices to the active region's retailers.
        # UK: only show ebay-uk / amazon-uk (country='UK').
        # US: exclude UK retailers so GBP prices never appear in the USD table.
        if region == 'uk':
            current_prices = list(
                CurrentPrice.objects
                .filter(product=product, retailer__is_uk=True)
                .select_related('retailer')
                .order_by('not_available', '-in_stock', 'price')
            )
        else:
            current_prices = list(
                CurrentPrice.objects
                .filter(product=product)
                .exclude(retailer__is_uk=True)
                .select_related('retailer')
                # Sort: available first, then in-stock before out-of-stock,
                # then cheapest first.
                .order_by('not_available', '-in_stock', 'price')
            )

        # Books: price varies by format (E-Book/Audio Book/Paperback/Hardback)
        # rather than one price per retailer, so they're grouped separately
        # from current_prices. Region-scoped by currency (USD rows for US,
        # GBP rows for UK) via the explicit currency= filter below -- without
        # it, once both regions have data, a GBP row would leak into a US
        # visitor's price table (and vice versa) since BookFormatPrice has no
        # other region marker on its own.
        # All 4 tabs always render (E-Book/Audio Book included even with no
        # BookFormatPrice rows yet) so the tab bar's shape doesn't change once
        # that sourcing work begins -- their panel just shows "not tracked
        # yet" until then. default_book_format (the first format that HAS
        # data, not necessarily the first in display order) is what's
        # initially active and seeds the "Best Price Available" card; JS
        # keeps that card in sync with whichever tab is actually clicked.
        book_formats = []
        default_book_format = None
        all_book_prices = []
        if product.author:
            _book_currency = 'GBP' if region == 'uk' else 'USD'
            _is_msrp_field = 'is_msrp_source_uk' if region == 'uk' else 'is_msrp_source'
            all_book_prices = list(
                BookFormatPrice.objects
                .filter(product=product, currency=_book_currency)
                .select_related('retailer')
                .order_by('not_available', '-in_stock', 'price')
            )
            for fmt_value in BOOK_FORMAT_VALUE_ORDER:
                fmt_prices = [bfp for bfp in all_book_prices if bfp.format == fmt_value]
                # MSRP reference for this format's Discount column -- the
                # is_msrp_source (US) / is_msrp_source_uk (UK) row's price,
                # found explicitly rather than assumed to be prices[0] since
                # a cheaper non-MSRP retailer (e.g. Amazon) can sort first.
                fmt_msrp = next(
                    (bfp.price for bfp in fmt_prices if getattr(bfp, _is_msrp_field) and bfp.price),
                    None,
                )
                book_formats.append({
                    'value': fmt_value,
                    'label': BOOK_FORMAT_LABELS[fmt_value],
                    'prices': fmt_prices,
                    'msrp': fmt_msrp,
                })
            default_book_format = next((f for f in book_formats if f['prices']), book_formats[0])

            # UK-only, link-no-price Amazon row (see AMAZON_ONELINK_SCRIPT):
            # reuses the existing US-currency Amazon URL per format rather
            # than a separate UK price/retailer row, since we have no way to
            # source a real GBP price for Amazon yet. Deliberately kept out
            # of the strict currency-filtered `prices` list above (which
            # exists specifically to stop a USD row leaking into a UK
            # visitor's price table) -- this is a separate, clearly-labelled
            # template element instead. To revert: delete this block and the
            # matching template block in product_detail.html.
            if region == 'uk':
                amazon_us_links = {
                    bfp.format: bfp.url
                    for bfp in BookFormatPrice.objects.filter(
                        product=product, retailer__slug='amazon', currency='USD',
                    ).exclude(url='')
                }
                for fmt in book_formats:
                    fmt['amazon_link'] = amazon_us_links.get(fmt['value'])

        # Related products: prefer same faction+category, then same faction,
        # then same category — avoids the alphabetical Adepta Sororitas problem.
        # Region-aware exclusion matches product_list's _min_price_filter —
        # without it, a UK-only price (e.g. eBay UK) can leak into a US-region
        # visitor's "Best Price" card on a related-product tile.
        if region == 'uk':
            _rp_price_filter = Q(
                current_prices__not_available=False,
                current_prices__in_stock=True,
                current_prices__retailer__is_uk=True,
            )
        else:
            _rp_price_filter = Q(
                current_prices__not_available=False,
                current_prices__in_stock=True,
            ) & ~Q(current_prices__retailer__is_uk=True)
        # Related-products MSRP must never trust the static product.msrp /
        # msrp_gbp snapshot on its own -- those fields only update when
        # someone manually re-syncs, so they drift stale after every GW
        # price change. Annotate the same live-GW Subquery pattern
        # product_list already uses (gw_ref_price_sq) for both regions, so
        # this widget always shows today's real GW price, falling back to
        # the stored msrp/msrp_gbp only when no live GW CurrentPrice is
        # tracked at all. Both are annotated unconditionally (cheap extra
        # joins) so the same query works for either region's template branch.
        related_gw_ref_price_sq = Subquery(
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
        related_gw_ref_price_gbp_sq = Subquery(
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
        exclude_pk = product.pk
        related_products = list(
            Product.objects
            .filter(faction=product.faction, category=product.category, is_active=True)
            .exclude(pk=exclude_pk)
            .select_related('category', 'faction')
            .annotate(min_price=Min('current_prices__price', filter=_rp_price_filter))
            .annotate(gw_ref_price=related_gw_ref_price_sq)
            .annotate(gw_ref_price_gbp=related_gw_ref_price_gbp_sq)
            .order_by('name')[:4]
        )
        if len(related_products) < 4 and product.faction_id:
            existing_pks = {p.pk for p in related_products} | {exclude_pk}
            more = list(
                Product.objects
                .filter(faction=product.faction, is_active=True)
                .exclude(pk__in=existing_pks)
                .select_related('category', 'faction')
                .annotate(min_price=Min('current_prices__price', filter=_rp_price_filter))
                .annotate(gw_ref_price=related_gw_ref_price_sq)
                .annotate(gw_ref_price_gbp=related_gw_ref_price_gbp_sq)
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
                .annotate(min_price=Min('current_prices__price', filter=_rp_price_filter))
                .annotate(gw_ref_price=related_gw_ref_price_sq)
                .annotate(gw_ref_price_gbp=related_gw_ref_price_gbp_sq)
                .order_by('name')[:4 - len(related_products)]
            )
            related_products.extend(more)

        # Discount reference price and savings — region-specific.
        # UK: use games-workshop-uk's live GBP CurrentPrice if tracked, else
        #     stored msrp_gbp -- same live-first pattern as US below.
        #     savings is skipped because get_savings_vs_retail() is USD-only.
        # US: use GW's live USD CurrentPrice if tracked, else stored msrp.
        if region == 'uk':
            gw_cp_uk = next(
                (
                    cp for cp in current_prices
                    if cp.retailer.slug == 'games-workshop-uk'
                    and not cp.not_available
                    and cp.price
                ),
                None,
            )
            gw_ref_price = gw_cp_uk.price if gw_cp_uk else product.msrp_gbp
            savings = None
        else:
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
            savings = product.get_savings_vs_retail()

        # Pre-filter for JSON-LD schema — only offers with a real price and
        # not marked unavailable.  Using a separate list means forloop.last
        # in the template is always accurate (no skipped-entry comma bugs).
        # Books draw from BookFormatPrice instead of CurrentPrice.
        schema_prices = [
            cp for cp in current_prices
            if cp.price and not cp.not_available
        ] + [
            bfp for bfp in all_book_prices
            if bfp.price and not bfp.not_available
        ]

        # Build JSON-LD using json.dumps() so the output is always valid JSON.
        # The template's |escapejs filter converts ' → \' which is valid in JS
        # string literals but is an invalid escape sequence in JSON — causing
        # "Unparsable structured data" errors in Google Search Console for any
        # product whose name, description, or retailer URL contains an apostrophe.
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
        price_currency = 'GBP' if region == 'uk' else 'USD'
        if schema_prices:
            schema_dict['offers'] = [
                {
                    '@type': 'Offer',
                    'seller': {'@type': 'Organization', 'name': cp.retailer.name},
                    'price': float(cp.price),
                    'priceCurrency': price_currency,
                    'availability': (
                        'https://schema.org/InStock' if cp.in_stock
                        else 'https://schema.org/OutOfStock'
                    ),
                    'url': cp.url or '',
                }
                for cp in schema_prices
            ]
        json_ld = json.dumps(schema_dict, ensure_ascii=False)

        # ── SEO title enrichment ──────────────────────────────────────────────
        # Google treats titles under 30 chars as too short and may rewrite them.
        # For short product names ("Rhino", "Kahl", "Wulfen") we append the
        # faction or a Warhammer qualifier to hit ≥30 chars while staying ≤60.
        # Faction first (most specific long-tail signal), then generic fallback.
        # For names already over 60 chars we trim at a word boundary so Google's
        # snippet cut falls cleanly ("…" added) rather than mid-word.
        _SUFFIX = ' | ThriftHammer'        # 16 chars
        _MAX    = 60
        _MIN    = 30
        _name   = product.name

        # Trim overlong product names to fit cleanly within the 60-char budget.
        _max_name_len = _MAX - len(_SUFFIX)          # = 44
        if len(_name) > _max_name_len:
            # Cut at last space within the budget, then append ellipsis.
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

        # Linked unit datasheets — used for the collapsible stats block.
        # Require both movement and toughness to be seeded (filters out
        # partially-seeded records like Black Templars cross-faction stubs).
        # Deduplicate by stat fingerprint: shared-kit units (e.g. Intercessors
        # across 7 SM sub-factions) have identical stats — show only one block.
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

        # Points per dollar — 40K products only, faction-matched unit.
        # Single lightweight query; result is cached with the rest of the context.
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
        pts_per_dollar = None
        if _unit_points and current_prices and current_prices[0].price:
            pts_per_dollar = round(float(_unit_points) / float(current_prices[0].price), 1)

        cached_ctx = {
            'product':          product,
            'current_prices':   current_prices,
            'book_formats':         book_formats,
            'default_book_format':  default_book_format,
            'schema_prices':    schema_prices,
            'related_products': related_products,
            'savings':          savings,
            'gw_ref_price':     gw_ref_price,
            'json_ld':          json_ld,
            'page_title':       page_title,
            'unit_types':       unit_types,
            'pts_per_dollar':   pts_per_dollar,
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
    /uk/products/search/autocomplete/ (see products/urls_uk.py) routes here
    too -- region is resolved from the path the same way as product_detail()
    / product_list(), and the price annotation's is_uk filter direction
    flips accordingly so UK callers get GBP UK-retailer prices, not USD.

    Security: query is stripped and capped at 100 characters; only
    name, slug, and min_price are returned — no sensitive fields.
    """
    query  = request.GET.get('q', '').strip()[:100]
    region = 'uk' if request.path.startswith('/uk/') else 'us'

    if len(query) < 2:
        return JsonResponse({'results': []})

    # v3 — bumped for the switch to loose/typo-tolerant matching (word-based
    # + trigram similarity) instead of a single literal substring match.
    cache_key = f'autocomplete_v3|{region}|{query.lower()}'
    cached    = cache.get(cache_key)
    if cached is not None:
        return JsonResponse({'results': cached})

    _is_uk_price = Q(current_prices__retailer__is_uk=True) if region == 'uk' else ~Q(current_prices__retailer__is_uk=True)
    matches = (
        Product.objects
        .filter(is_active=True)
        .annotate(name_similarity=TrigramWordSimilarity(query, 'name'))
        .filter(_search_filter(query, include_description=False))
        .annotate(
            min_price=Min(
                'current_prices__price',
                filter=Q(
                    current_prices__not_available=False,
                    current_prices__in_stock=True,
                ) & _is_uk_price,
            )
        )
        .order_by(F('name_similarity').desc(nulls_last=True), 'name')
        .values('name', 'slug', 'min_price')[:10]
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
        # Rate limit: 5 reports per IP per hour to block bot floods
        ip = request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR', ''))
        ip = ip.split(',')[0].strip()
        rate_key = f'report_issue_rate_{ip}'
        rate_count = cache.get(rate_key, 0)
        if rate_count >= 5:
            messages.error(
                request,
                'Too many reports submitted. Please wait an hour before trying again.',
            )
            return redirect('products:detail', slug=slug)
        cache.set(rate_key, rate_count + 1, 3600)

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

            IssueReport.objects.create(
                product=product,
                issue_type=form.cleaned_data['issue_type'],
                description=description,
                contact_email=contact_email if contact_email != 'Anonymous' else '',
            )
            logger.info('Issue report saved for product %s', product.gw_sku)

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

    # Region comes from a hidden field the form pre-fills with the visitor's
    # current browsing-region session value. Validated against the model's
    # own choices rather than trusted as-is -- a POST body is client input.
    region = request.POST.get('region', '').strip().lower()
    if region not in dict(NewsletterSignup.REGION_CHOICES):
        region = NewsletterSignup.REGION_US

    signup, created = NewsletterSignup.objects.get_or_create(
        email=email,
        defaults={'is_confirmed': False, 'region': region},
    )
    if created:
        # Send confirmation email — new subscribers must click to confirm.
        _send_newsletter_confirmation(signup)
        messages.success(
            request,
            "Almost there! Check your inbox and click the confirmation link to activate your deal alerts.",
        )
    elif not signup.is_confirmed:
        # Resend confirmation if they try again before confirming.
        _send_newsletter_confirmation(signup)
        messages.info(
            request,
            "We sent you another confirmation email. Check your inbox to activate your deal alerts.",
        )
    else:
        messages.info(request, "You're already signed up for deal alerts.")
    return redirect('home')


def _send_newsletter_confirmation(signup):
    """Send the double opt-in confirmation email to a new subscriber."""
    confirmation_url = signup.get_confirmation_url()
    context = {
        'confirmation_url': confirmation_url,
        'site_url': 'https://thrifthammer.com',
    }
    html_body = render_to_string('emails/newsletter_confirmation.html', context)
    text_body = (
        'THANK YOU FOR SUBSCRIBING TO THRIFTHAMMER!\n\n'
        'One quick click to activate your account and start receiving weekly deals.\n\n'
        f'{confirmation_url}\n\n'
        "WHAT YOU'LL RECEIVE (by default):\n"
        '- Wednesday: Warhammer 40K deals\n'
        '- Friday: Warhammer Universe deals (Age of Sigmar, The Old World, Horus Heresy,\n'
        '  Kill Team, Necromunda, Warcry & Blood Bowl)\n\n'
        'PERSONALIZE YOUR NEWSLETTERS:\n'
        'Create a free account with this same email address for more control. It links to\n'
        'this subscription automatically. Then visit Account Settings to choose exactly\n'
        'which newsletters you receive:\n'
        '- A Sunday digest for your specific faction(s)\n'
        '- A Monday digest customized to other miniature gaming systems you are interested in\n'
        'https://thrifthammer.com/accounts/register/\n\n'
        'STAY CONNECTED:\n'
        'Join r/DealHammer on Reddit for another way to catch the best deals as they drop.\n'
        'https://reddit.com/r/DealHammer\n\n'
        'Run into an issue or have feedback? Reply to this email or write to '
        'Thrifthammer.com@gmail.com.\n\n'
        'If you did not sign up for ThriftHammer deal alerts, you can ignore this email.\n'
        '-- ThriftHammer\n'
        'https://thrifthammer.com'
    )
    msg = EmailMultiAlternatives(
        subject='Thank You for Subscribing to ThriftHammer!',
        body=text_body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[signup.email],
    )
    msg.attach_alternative(html_body, 'text/html')
    try:
        msg.send(fail_silently=True)
    except Exception:
        pass  # Never let email failure block the user flow


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


def newsletter_confirm(request, token):
    """
    One-click confirmation for new homepage newsletter signups.

    GET → set is_confirmed=True and show success page.
    Unknown tokens show a neutral success page to prevent probing.
    """
    signup = NewsletterSignup.objects.filter(token=token).first()
    if signup and not signup.is_confirmed:
        signup.is_confirmed = True
        signup.save(update_fields=['is_confirmed'])

    return render(request, 'products/newsletter_confirmed.html', {
        'email': signup.email if signup else None,
    })
