"""
Management command: update_ebay_uk_book_prices

Fetches live eBay UK prices for book BookFormatPrice rows (Paperback /
Hardback only -- eBay is a physical-goods marketplace, so E-Book and Audio
Book are out of scope) using the official eBay Browse API v1 on the EBAY_GB
marketplace. Saves results to the 'ebay-uk' retailer with currency='GBP',
with EPN UK affiliate tracking params appended to every saved URL.

Sibling to update_ebay_book_prices.py (US) and update_ebay_uk_prices.py
(UK miniatures) rather than an extension of either: it reuses the US book
command's matching strategy (ISBN+title query, Best-Match-vs-cheaper-
alternative winner selection, book-safe bits/apparel filtering -- see that
file's docstring for the full research behind those choices) but talks to
the UK marketplace client (EbayBrowseAPIUK) and UK EPN params, the same way
update_ebay_uk_prices.py mirrors update_ebay_prices.py for miniatures.

Source rows / ISBN resolution:
  Covers every Softback/Hardback BookFormatPrice row under the 'games-
  workshop-uk' retailer (all UK books-and-novels products, not just one
  batch). Games Workshop UK rows do not all carry their own ISBN yet (only
  newly-added UK-exclusive titles do -- older rows were bootstrapped from
  GW UK URLs without re-researching an ISBN that ThriftHammer already has
  on file). Since a Black Library paperback/hardback print run is the same
  physical edition worldwide, this command resolves each row's ISBN as:
    1. the GW-UK row's own isbn, if set;
    2. otherwise, any other retailer's row for the same product+format
       that already has a non-blank isbn (typically the US GW or Amazon
       row) -- reusing data already sourced, never re-fabricating it.
  Two products have no ISBN anywhere in the DB (BOOK-40K-018 "Da
  Freebooterz Code" hardback, BOOK-40K-049 "Paragon of Faith and Other
  Stories" paperback) -- these run as title-only queries until ISBN
  research is done for them, same as how the US command's Fulgrim override
  runs without an ISBN anchor.

QUERY_OVERRIDES_UK is intentionally empty at introduction. The US
command's QUERY_OVERRIDES entries were tuned against real eBay US search
results (specific item IDs, USD prices) and do not carry over to eBay UK's
own listings inventory -- overrides here must be discovered the same way
the US ones were: run with --debug --dry-run on a "not found" or
suspicious title and add an entry from what's actually returned.

Safety rules (same as update_ebay_book_prices.py / update_ebay_uk_prices.py):
  - BookFormatPrice entries with manual_url_override=True are NEVER touched.
  - Not found is always recorded (not_available=True), never silently
    skipped, so a book's state on the site always reflects the last real
    check.
  - Only writes to the 'ebay-uk' retailer -- never touches US 'ebay' rows.

Not added to the Procfile -- run manually, on demand, same as the other
find/update commands introduced for the Books feature.

Usage:
    python manage.py update_ebay_uk_book_prices --dry-run                        # preview, no writes
    python manage.py update_ebay_uk_book_prices                                  # live run, all UK books
    python manage.py update_ebay_uk_book_prices --faction "Horus Heresy Books"
    python manage.py update_ebay_uk_book_prices --skus BOOK-40K-073,BOOK-HH-027 --debug --dry-run
"""

import shlex
import time
from decimal import Decimal

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import InterfaceError, OperationalError, connection

from prices.models import BookFormatPrice
from products.ebay_api_client_uk import EbayAPIError, EbayBrowseAPIUK
from products.management.commands.update_ebay_book_prices import _pick_winner
from products.management.commands.update_ebay_uk_prices import _add_epn_params_uk
from products.models import Retailer

# ─── Per-(SKU, format) search query overrides (eBay UK) ───────────────────────
# Empty at introduction -- see module docstring. Format: 'gw_sku:format' ->
# full replacement query string, discovered the same way as the US overrides
# (run --debug --dry-run, inspect real results, only ever built from the
# book's own stable identifiers -- never a specific listing's item ID).
# Any entry here must be shown to and approved by the user before it is
# written, every time -- see feedback_ebay_matching_needs_permission memory.
QUERY_OVERRIDES_UK = {}
# ─────────────────────────────────────────────────────────────────────────────

_MAX_SEARCH_RESULTS = 10


def _resolve_isbn(row):
    """
    Return the ISBN to search with for this GW-UK BookFormatPrice row.

    Uses the row's own isbn if set; otherwise falls back to any other
    retailer's row for the same product+format that already has one (see
    module docstring -- the physical edition is not region-specific, so
    reusing an already-sourced ISBN is correct, not a fabrication).
    """
    if row.isbn:
        return row.isbn
    other = (
        BookFormatPrice.objects
        .filter(product=row.product, format=row.format)
        .exclude(isbn='')
        .exclude(retailer=row.retailer)
        .first()
    )
    return other.isbn if other else ''


def _build_query_uk(product, isbn, override_key, drop_isbn=False):
    """
    Return the eBay UK search query for a (product, format).

    Mirrors update_ebay_book_prices.py's _build_query(): a base query
    (default "{isbn} {name} -bundle -lot" formula, or a QUERY_OVERRIDES_UK
    entry), with Product.ebay_negative_keywords always layered on top --
    the same shared field the US book command and both miniature commands
    (US/UK) use, parsed the same way (shlex, quoted phrases -> -"phrase").

    The {name} portion uses ebay_search_name_uk / ebay_search_name as an
    override on product.name, mirroring the exact fallback chain the
    miniature matcher already uses (ebay_api_client_uk.py) -- this lets a
    title's search phrase be loosened (e.g. dropping a subtitle, changing
    word order) without touching the product's real display name. A book
    with no override set behaves identically to before (falls through to
    product.name), so this only changes behavior for a title an override
    is explicitly set on.

    drop_isbn=True omits the ISBN from the default formula -- used by the
    caller as a second-attempt retry when the ISBN+name search finds
    nothing (confirmed necessary: several titles' correct listings don't
    mention the ISBN at all, so including it returns zero results even
    with a well-tuned search name). ISBN is always tried first; this is
    only the fallback, never the first attempt.
    """
    effective_name = (
        getattr(product, 'ebay_search_name_uk', '') or
        getattr(product, 'ebay_search_name', '') or
        product.name
    )
    if override_key in QUERY_OVERRIDES_UK:
        query = QUERY_OVERRIDES_UK[override_key]
    elif isbn and not drop_isbn:
        query = f'{isbn} {effective_name} -bundle -lot'.strip()
    else:
        query = f'{effective_name} -bundle -lot'.strip()

    raw_negatives = getattr(product, 'ebay_negative_keywords', '') or ''
    if raw_negatives:
        for phrase in shlex.split(raw_negatives):
            phrase = phrase.strip()
            if not phrase:
                continue
            if ' ' in phrase:
                query += f' -"{phrase}"'
            else:
                query += f' -{phrase}'

    return query


def _local_negative_filter(items, product):
    """
    Drop any result whose title contains a Product.ebay_negative_keywords
    phrase, re-checked locally in Python.

    This is a reliability backstop on top of the "-keyword" terms already
    sent to eBay in the query string (see _build_query_uk): eBay's own
    negative-term matching was confirmed unreliable during testing -- a
    "-Taschenbuch" query term still returned a listing whose title contained
    "Taschenbuch" (German import edition of Fulgrim). Checking locally
    against the actual returned titles catches whatever eBay's own filtering
    missed, without depending on it working correctly.
    """
    raw_negatives = getattr(product, 'ebay_negative_keywords', '') or ''
    if not raw_negatives:
        return items
    phrases = [p.strip().lower() for p in shlex.split(raw_negatives) if p.strip()]
    if not phrases:
        return items
    return [it for it in items if not any(p in it['title'].lower() for p in phrases)]


def _with_db_retry(operation, stderr, style):
    """Execute a single DB operation, recovering from a dropped connection (same as the sibling commands)."""
    try:
        return operation(), True
    except (OperationalError, InterfaceError) as exc:
        stderr.write(style.WARNING(f'  [db-retry] connection error, retrying: {exc}'))
        connection.close()
        time.sleep(2)
        try:
            return operation(), True
        except (OperationalError, InterfaceError) as exc2:
            stderr.write(style.ERROR(f'  [db-error] failed after retry, skipping: {exc2}'))
            return None, False


class Command(BaseCommand):
    """Fetch live eBay UK prices for book Paperback/Hardback format rows via the Browse API (EBAY_GB)."""

    help = (
        'Update Paperback/Hardback BookFormatPrice rows from eBay UK (E-Book/Audio '
        'Book are out of scope -- eBay is a physical-goods marketplace). Writes to '
        'the ebay-uk retailer with EPN UK affiliate tracking.'
    )

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', default=False, help='Show results without saving to the database.')
        parser.add_argument('--delay', type=float, default=1.2, metavar='SECONDS', help='Delay between API calls in seconds (default: 1.2).')
        parser.add_argument('--faction', type=str, default=None, metavar='NAME', help='Filter to a faction (e.g. "Horus Heresy Books").')
        parser.add_argument('--category', type=str, default=None, metavar='NAME', help='Filter to a category (e.g. "Warhammer").')
        parser.add_argument('--skus', type=str, default=None, metavar='SKUS', help='Comma-separated GW SKUs (e.g. "BOOK-40K-073,BOOK-HH-027").')
        parser.add_argument('--limit', type=int, default=None, metavar='N', help='Process only the first N format rows.')
        parser.add_argument('--debug', action='store_true', default=False, help='Print every eBay UK candidate returned for each query, not just the winner.')

    def handle(self, *args, **options):
        dry_run  = options['dry_run']
        delay    = options['delay']
        faction  = options['faction']
        category = options['category']
        skus     = [s.strip() for s in (options['skus'] or '').split(',') if s.strip()]
        limit    = options['limit']
        debug    = options['debug']

        try:
            ebay_api = EbayBrowseAPIUK(use_sandbox=False)
        except ValueError as exc:
            self.stderr.write(self.style.ERROR(f'Configuration error: {exc}'))
            return

        campaign_id = getattr(settings, 'EBAY_UK_AFFILIATE_CAMPAIGN_ID', '')

        ebay_uk_retailer, created = Retailer.objects.get_or_create(
            slug='ebay-uk',
            defaults={'name': 'eBay UK', 'website': 'https://www.ebay.co.uk', 'country': 'UK', 'is_active': True},
        )
        if created:
            self.stdout.write(self.style.SUCCESS('Created eBay UK retailer in DB.'))

        gw_uk_retailer = Retailer.objects.filter(slug='games-workshop-uk').first()
        if not gw_uk_retailer:
            self.stderr.write(self.style.ERROR('Games Workshop UK retailer not found in DB.'))
            return

        # ── Resolve GW-UK Paperback/Hardback rows (all of them -- ISBN is
        # resolved per-row below, with a fallback for rows missing one) ──────
        gw_uk_qs = (
            BookFormatPrice.objects
            .filter(
                retailer=gw_uk_retailer,
                format__in=[BookFormatPrice.FORMAT_SOFTBACK, BookFormatPrice.FORMAT_HARDBACK],
            )
            .select_related('product', 'product__faction', 'product__category')
        )

        if skus:
            gw_uk_qs = gw_uk_qs.filter(product__gw_sku__in=skus)
        if faction:
            gw_uk_qs = gw_uk_qs.filter(product__faction__name__iexact=faction)
        if category:
            gw_uk_qs = gw_uk_qs.filter(product__category__name__icontains=category)

        rows = list(gw_uk_qs.order_by('product__name', 'format'))
        if limit:
            rows = rows[:limit]

        if not rows:
            self.stdout.write(self.style.WARNING('No matching UK book format rows found for the given filters.'))
            return

        env_label = 'DRY RUN — nothing will be written' if dry_run else 'LIVE — writing to DB'
        self.stdout.write(f'\neBay UK Book Price Update (EBAY_GB / GBP)\n{"=" * 50}')
        self.stdout.write(f'  Mode        : {env_label}')
        self.stdout.write(f'  Rows        : {len(rows)}')
        self.stdout.write(f'  Retailer    : ebay-uk')
        if campaign_id:
            self.stdout.write(f'  EPN affiliate (UK) : campid={campaign_id}')
        else:
            self.stdout.write(self.style.WARNING(
                '  EPN affiliate (UK) : NOT configured '
                '(set EBAY_UK_AFFILIATE_CAMPAIGN_ID to enable UK affiliate tracking)'
            ))
        self.stdout.write('=' * 50 + '\n')

        found = not_found = skipped_override = errors = 0

        for idx, row in enumerate(rows, 1):
            product = row.product
            fmt_display = row.get_format_display()
            isbn = _resolve_isbn(row)
            override_key = f'{product.gw_sku}:{row.format}'
            self.stdout.write(f'[{idx}/{len(rows)}] {product.name} ({fmt_display})')
            if not isbn:
                self.stdout.write(self.style.WARNING('  [no ISBN anywhere] title-only query.'))

            # ── manual_url_override guard ───────────────────────────────────────
            existing, db_ok = _with_db_retry(
                lambda: BookFormatPrice.objects.filter(
                    product=product, retailer=ebay_uk_retailer, format=row.format
                ).first(),
                self.stderr, self.style,
            )
            if not db_ok:
                errors += 1
                time.sleep(delay)
                continue
            if existing and existing.manual_url_override:
                self.stdout.write(self.style.WARNING('  [manual override] skipping.'))
                skipped_override += 1
                continue

            # ── Stage 1: ISBN + name, negative keywords applied both at the
            # query level (sent to eBay) and re-checked locally (see
            # _local_negative_filter) ────────────────────────────────────────
            query = _build_query_uk(product, isbn, override_key)
            try:
                items = ebay_api.search_items(query, max_results=_MAX_SEARCH_RESULTS)
            except EbayAPIError as exc:
                self.stdout.write(self.style.ERROR(f'  eBay UK API error: {exc}'))
                errors += 1
                time.sleep(delay)
                continue
            except RuntimeError as exc:
                self.stdout.write(self.style.WARNING(f'  Error: {exc}'))
                errors += 1
                time.sleep(delay)
                continue

            raw_count = len(items)
            items = _local_negative_filter(items, product)
            if debug:
                dropped = raw_count - len(items)
                dropped_note = f' ({dropped} dropped by negative-keyword re-check)' if dropped else ''
                self.stdout.write(f'  query: "{query}" -> {raw_count} result(s){dropped_note}')
                for it in items:
                    it_title = it['title'][:75].encode('ascii', 'replace').decode('ascii')
                    self.stdout.write(f'    £{it["total_cost"]:>7} | {it_title}')

            # ── Stage 2: name-only fallback, same negative-keyword filtering.
            # Triggers whenever stage 1 has nothing left -- either eBay found
            # zero results, or everything it found got dropped by the
            # negative-keyword re-check above. Several titles' correct
            # listings don't mention the ISBN at all, so this only ever adds
            # a second chance -- it never changes a result stage 1 kept. ────
            if not items and isbn and override_key not in QUERY_OVERRIDES_UK:
                fallback_query = _build_query_uk(product, isbn, override_key, drop_isbn=True)
                try:
                    fb_items = ebay_api.search_items(fallback_query, max_results=_MAX_SEARCH_RESULTS)
                except (EbayAPIError, RuntimeError) as exc:
                    self.stdout.write(self.style.WARNING(f'  Fallback search error: {exc}'))
                    fb_items = []
                fb_raw_count = len(fb_items)
                items = _local_negative_filter(fb_items, product)
                query = fallback_query
                if debug:
                    dropped = fb_raw_count - len(items)
                    dropped_note = f' ({dropped} dropped by negative-keyword re-check)' if dropped else ''
                    self.stdout.write(f'  [stage 2: search name only] query: "{query}" -> {fb_raw_count} result(s){dropped_note}')
                    for it in items:
                        it_title = it['title'][:75].encode('ascii', 'replace').decode('ascii')
                        self.stdout.write(f'    £{it["total_cost"]:>7} | {it_title}')

            if not items:
                self.stdout.write(self.style.WARNING('  Not found on eBay UK.'))
                if not dry_run:
                    _, db_ok = _with_db_retry(
                        lambda: BookFormatPrice.objects.update_or_create(
                            product=product, retailer=ebay_uk_retailer, format=row.format,
                            defaults={'price': None, 'url': '', 'currency': 'GBP', 'in_stock': False, 'not_available': True, 'isbn': isbn},
                        ),
                        self.stderr, self.style,
                    )
                    if not db_ok:
                        errors += 1
                not_found += 1
                time.sleep(delay)
                continue

            winner = _pick_winner(
                items, ebay_api, stdout=self.stdout,
                trust_best_match=getattr(product, 'ebay_trust_best_match', False),
            )
            if winner is None:
                # LOCAL_PICKUP or a failed detail fetch -- no resolvable delivered cost
                self.stdout.write(self.style.WARNING('  Winner discarded (LOCAL_PICKUP or shipping fetch failed).'))
                if not dry_run:
                    _, db_ok = _with_db_retry(
                        lambda: BookFormatPrice.objects.update_or_create(
                            product=product, retailer=ebay_uk_retailer, format=row.format,
                            defaults={'price': None, 'url': '', 'currency': 'GBP', 'in_stock': False, 'not_available': True, 'isbn': isbn},
                        ),
                        self.stderr, self.style,
                    )
                    if not db_ok:
                        errors += 1
                not_found += 1
                time.sleep(delay)
                continue

            total_cost = winner['total_cost']
            url = _add_epn_params_uk(winner['url'], campaign_id)
            title_preview = winner['title'][:70].encode('ascii', 'replace').decode('ascii')

            self.stdout.write(self.style.SUCCESS(
                f'  £{total_cost:.2f} (£{winner["price"]:.2f} + £{winner["shipping"]:.2f} ship) — {title_preview}'
            ))
            self.stdout.write(f'  URL: {url}')

            if not dry_run:
                _, db_ok = _with_db_retry(
                    lambda: BookFormatPrice.objects.update_or_create(
                        product=product, retailer=ebay_uk_retailer, format=row.format,
                        defaults={
                            'price': total_cost, 'currency': 'GBP', 'url': url,
                            'listing_title': winner['title'][:300],
                            'in_stock': True, 'not_available': False, 'isbn': isbn,
                        },
                    ),
                    self.stderr, self.style,
                )
                if not db_ok:
                    errors += 1
                    time.sleep(delay)
                    continue
            else:
                self.stdout.write(self.style.WARNING('  [DRY RUN] Not saved to DB.'))
            found += 1
            time.sleep(delay)

        self.stdout.write('\n' + '=' * 50)
        self.stdout.write(self.style.SUCCESS('Summary (eBay UK Books)'))
        self.stdout.write('=' * 50)
        self.stdout.write(f'  Found            : {found}')
        self.stdout.write(f'  Not found        : {not_found}')
        self.stdout.write(f'  Manual override  : {skipped_override} (skipped)')
        self.stdout.write(f'  Errors           : {errors}')
