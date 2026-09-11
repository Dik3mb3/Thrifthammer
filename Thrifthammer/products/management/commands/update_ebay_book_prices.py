"""
Management command: update_ebay_book_prices

Fetches live eBay US prices for book BookFormatPrice rows (Paperback /
Hardback only -- eBay is a physical-goods marketplace, so E-Book and Audio
Book are out of scope) using the official eBay Browse API v1.

Sibling to update_ebay_prices.py rather than an extension of it: books need
a completely different matching strategy from miniatures. The miniature
validator (_is_valid_result in ebay_api_client.py) explicitly blocklists
'paperback', 'hardback', 'hardcover', 'novel', and 'library' as bits/parts
signals -- protections built to keep Black Library novels OUT of miniature
kit searches. Real eBay book listings almost always contain those exact
words, so reusing that validator for books would reject nearly everything.

Search strategy (extensively tested against real eBay data before writing
this command -- see session notes):
  - Default query: "{isbn} {book title} -bundle -lot"
    ISBN + title together are precise for most titles. "-bundle -lot"
    excludes the "Warhammer Black Library Book Lot -- Pick any or many and
    save!" listing that otherwise matches nearly every ISBN search.
    Confirmed eBay's `gtin` filter (searches its structured product catalog
    directly, bypassing keyword relevance) is NOT a viable alternative: it
    returned 0 results for a real, verified-listed edition (Horus Rising's
    2026 paperback isn't in eBay's GTIN catalog at all) and separately
    matched a paperback ISBN to hardcover-only listings for another title --
    both worse than plain keyword search.
  - Winner selection (changed 2026-09-06 to match the miniature matcher's
    find_best_match_for_product() in ebay_api_client.py -- see _pick_winner
    below): Best Match #1 is trusted for product identity, but a candidate
    from the same result set is used instead if it's genuinely (>=10%)
    cheaper once both candidates' real shipping cost is verified (search-
    result shipping is frequently $0 or wrong). Books have no equivalent of
    the miniature _is_valid_result validator (it blocklists "paperback"/
    "hardback"/"novel"/"library" as bits/parts signals -- incompatible with
    books), so this compares raw top-N results directly rather than
    validated ones; the ISBN+title query is precise enough in practice that
    every case found so far was a price-ranking issue, not a wrong-book
    match, once the query already includes both ISBN and title. Originally
    this command trusted Best Match #1 unconditionally with no cheaper-
    alternative comparison -- changed after two real cases were found where
    Best Match #1 was a genuine but needlessly expensive listing while a
    meaningfully cheaper genuine listing for the same book sat further down
    the same result set (Gotrek and Maleneth: The Omnibus, $74.95 Best
    Match #1 vs $20.98 four results down; Witch Hunters: The Omnibus, a
    user-found $21 flat-rate listing cheaper than the $35.60-delivered
    PRESALE listing Best Match had been picking).
  - QUERY_OVERRIDES: some titles could not be reliably matched by the
    default formula even after heavy testing (documented inline per entry).
    This overrides ONLY the search query, never a matched URL -- eBay URLs
    are exclusively written by this automated matcher, never by hand, even
    with a user-confirmed real listing (see CLAUDE.md-equivalent project
    memory: "eBay URLs -- never manual"). A QUERY_OVERRIDES entry must only
    ever be built from the book's own stable identifiers (ISBN, title,
    format word) -- never a specific listing's item ID or seller-specific
    wording, since that stops working the moment that exact listing sells.

No price ceiling is applied in this version -- deliberately deferred.

Safety rules (same as update_ebay_prices.py):
  - BookFormatPrice entries with manual_url_override=True are NEVER touched.
  - Not found is always recorded (not_available=True), never silently
    skipped, so a book's state on the site always reflects the last real
    check.
  - Uses .save()/update_or_create() (not QuerySet.update()) so any future
    cache-invalidation signals on BookFormatPrice would still fire.

Not added to the Procfile -- run manually, on demand, same as the other
find/update commands introduced for the Books feature.

Usage:
    python manage.py update_ebay_book_prices --dry-run                       # preview, no writes
    python manage.py update_ebay_book_prices                                 # live run, all books
    python manage.py update_ebay_book_prices --faction "Horus Heresy Series"
    python manage.py update_ebay_book_prices --skus BOOK-HH-004,BOOK-HH-018 --debug --dry-run
"""

import re
import shlex
import time
from decimal import Decimal

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import InterfaceError, OperationalError, connection

from prices.models import BookFormatPrice
from products.ebay_api_client import EbayAPIError, EbayBrowseAPI
from products.management.commands.update_ebay_prices import _add_epn_params
from products.models import Retailer

# ─── Per-(SKU, format) search query overrides ─────────────────────────────────
# The default "{isbn} {title} -bundle -lot" query fails for these specific
# titles (tested extensively -- see module docstring). Format: 'gw_sku:format'
# -> full replacement query string. This only changes what gets searched for;
# the winning listing is still validated and matched the same way as any
# other result.
QUERY_OVERRIDES = {
    # Fulgrim -- including the ISBN in the query drops the correct listing
    # entirely (confirmed: title-only query finds it at Best Match #1,
    # $36.20; ISBN+title query returns different, unrelated results).
    # NOTE: this product's Product.ebay_negative_keywords is separately set
    # to "Reid" (excludes a wrong-book collision -- see docstring above and
    # _build_query below) -- that exclusion is NOT baked into this override
    # string, it's appended automatically from the DB field, mirroring how
    # the miniature matcher layers ebay_negative_keywords on top of
    # ebay_search_name.
    'BOOK-HH-004:softback': 'Fulgrim -bundle -lot',
    # The End and the Death: Volume III -- ISBN+title AND "-bundle -lot"
    # combined with this specific title's wording reproducibly returns 0
    # results (confirmed not a fluke: retried, reordered exclusions, tried
    # "-bundles" -- all 0). Dropping both the ISBN and the exclusion
    # keywords, and using "Vol III" + "paperback" instead of the stored
    # title's "Volume III" wording, finds the correct listing at Best
    # Match #1 ($28.05).
    'BOOK-HH-018:softback': 'End and the Death Vol III paperback',
    # Dominion Genesis -- our SKU is Paperback-only, but the default query's
    # Best Match #1 was a $60 Hardcover listing (a real, different, more
    # expensive edition ranked above 4 genuine ~$18-20 paperback listings
    # for the same title). Excluding hardcover/hardback surfaces the correct
    # format at Best Match #1 instead.
    'BOOK-40K-025:softback': '9781836091493 Dominion Genesis -bundle -lot -hardcover -hardback',
    # These 5 came back "not found" under the default ISBN+title formula
    # (0 results each -- confirmed, not a fluke). User supplied direct eBay
    # links for all 5; each was fetched by legacy item ID via the Browse API
    # and confirmed as a real, New-condition, correctly-titled listing before
    # writing anything. Per project convention, eBay URLs are never written
    # by hand -- these overrides only change the search QUERY, so the
    # automated matcher still finds and writes the URL itself; each query
    # below was verified to put the user's exact confirmed item at Best
    # Match #1 (matched by legacy item ID during testing).
    'BOOK-40K-022:hardback': 'Death Rider -bundle -lot',                        # item 298032533788, $29.95
    'BOOK-40K-033:hardback': 'Ghost Legion hardback',                          # item 277809035832, $26.64
    'BOOK-40K-058:hardback': 'The Infinite and the Divine hardback',           # item 318778172680, $35.00
    'BOOK-40K-060:softback': 'Macharian Crusade Angel of Fire -bundle -lot',   # item 267512975608, $29.99
    'BOOK-40K-072:softback': 'Yarrick: The Omnibus -bundle -lot',              # item 318460007437, $20.09
    # Gotrek and Maleneth: The Omnibus -- the default ISBN+full-title query's
    # exact "and"-spelled phrase only matched one real but expensive ($74.95)
    # listing, missing 3 cheaper genuine listings (as low as $20.98) whose
    # own titles use "&" instead of "and". Dropping "and"/"The" to just the
    # distinctive keywords surfaces the cheapest genuine listing at Best
    # Match #1 instead.
    'BOOK-AOS-008:softback': '9781804079669 Gotrek Maleneth Omnibus -bundle -lot',
}
# ─────────────────────────────────────────────────────────────────────────────

_MAX_SEARCH_RESULTS = 10

# A candidate must be at least this much cheaper than Best Match #1 to win
# instead of it -- matches the miniature matcher's find_best_match_for_product()
# threshold in ebay_api_client.py exactly, so the two commands behave the same way.
_CHEAPER_THRESHOLD = Decimal('0.90')  # must be >=10% cheaper to beat Best Match #1


def _build_query(product, isbn, override_key):
    """
    Return the search query for a (product, format).

    Mirrors the miniature matcher's two-layer query construction in
    ebay_api_client.py's _build_search_query(): a base query (here, either
    the default "{isbn} {title} -bundle -lot" formula or a QUERY_OVERRIDES
    entry for the handful of titles where that formula returns zero
    results), with Product.ebay_negative_keywords always layered on top to
    exclude wrong matches -- the same field, parsed the same way (shlex,
    quoted phrases -> -"phrase", single words -> -word), that miniatures
    use. QUERY_OVERRIDES changes the base text only when the default
    formula is unusable; ebay_negative_keywords is the one mechanism for
    excluding a specific wrong match from an otherwise-working query, kept
    deliberately mirrored with the miniature side rather than folded into
    a per-title override string.
    """
    if override_key in QUERY_OVERRIDES:
        query = QUERY_OVERRIDES[override_key]
    else:
        query = f'{isbn} {product.name} -bundle -lot'

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


# Book-safe wrong-category blocklist. Deliberately NOT a reuse of
# ebay_api_client.py's full _BITS_KEYWORDS -- that set's body-part words
# ('arm', 'leg', 'head', ...) and broad condition/category words ('single',
# 'proxy', 'metal', ...) are tuned for miniature kits and far too broad for
# book titles. Also deliberately excludes 'novel'/'paperback'/'hardback'/
# 'hardcover', which the miniature validator blocklists but which are
# exactly what a real book listing's title should contain.
#
# Grown from two real misses found re-checking "Death Rider" (a query
# override with no ISBN anchor, so unusually collision-prone): the word
# "bits" caught two miniature spare-parts listings ("...Power Sabres(x9)
# Bits...", "...Death Rider Bits (b30)"), but a third result --
# "EMPEROR Death Rider Unisex Black T Shirt" -- shared no keyword with
# either set and still won on price alone, since it's simply a different
# product category (apparel) that happens to share the title's two words.
# Extending the blocklist (not adding a position/rank cutoff) was the fix
# chosen deliberately: a rank cutoff would have discarded a *genuine*
# cheaper Saturnine listing found at position 7 of 9 results during the
# same re-check.
_BOOK_BITS_KEYWORDS = {
    'bit', 'bits', 'bitz', 'sprue', 'sprues', 'nos', 'blister',
    'shirt', 'shirts', 'tee', 'tees', 'tshirt', 'hoodie', 'apparel',
}


def _title_words(title):
    """Lowercase word-tokenise a listing title for keyword-set matching (strips punctuation)."""
    return set(re.findall(r"[a-z']+", title.lower()))


def _pick_winner(items, ebay_api, stdout=None, trust_best_match=False):
    """
    Pick the winning listing from a book search's results.

    Mirrors ebay_api_client.py's find_best_match_for_product(): Best Match
    #1 is trusted for product identity, but a candidate elsewhere in the
    same result set wins instead if it's genuinely (>=10%) cheaper once
    both candidates' real shipping cost is verified (search-result shipping
    is frequently $0 or wrong -- see the module docstring for two real
    cases this caught).

    If trust_best_match is True (Product.ebay_trust_best_match), the
    cheaper-alternative comparison is skipped entirely and Best Match #1 is
    always used -- the original, pre-2026-09-06 behavior for this one
    product. For "Fulgrim" (a bare one-word query with no ISBN anchor,
    since the default ISBN+title formula returns nothing for it), the
    cheapest raw result was a different unrelated item on every re-test
    (miniature spare-parts bits, a t-shirt, a Citadel paint pot) no matter
    what negative keywords were added, while Best Match #1 was reliably
    the correct book every time -- confirming the query itself is too weak
    to safely rank by price at all, not fixable by excluding one more
    keyword at a time.

    Unlike the miniature version, this does NOT reuse ebay_api_client.py's
    full _is_valid_result validator -- it blocklists "paperback"/"hardback"/
    "novel"/"library" as bits/parts signals, which would reject nearly every
    genuine book listing. It DOES apply a small book-safe subset of that
    validator's bits/parts terms (_BOOK_BITS_KEYWORDS below) before picking
    a cheaper alternative -- added after a real miss: for "Death Rider"
    (an override query with no ISBN anchor), the cheapest raw result was
    "Death Korps of Krieg - Death Rider - Power Sabres(x9) Bits Warhammer"
    -- a miniature spare-parts listing that happens to share the book's
    title, not the book itself. An ISBN-anchored default-formula query is
    unlikely to pick up an unrelated bits listing (confirmed: every other
    cheaper-alternative candidate found across a 98-book re-check was a
    genuine copy of the correct book), but an override query built from
    title words alone has no such anchor, so the filter applies to every
    query, not just overrides, as a low-cost safeguard.

    Args:
        items: search_items() results, already in eBay Best Match order.
        ebay_api: EbayBrowseAPI instance (for the shipping detail fetch).
        stdout: optional Command.stdout to log when a cheaper alternative wins.

    Returns:
        The winning item dict, with 'shipping'/'total_cost' corrected to
        real values, or None if it had to be discarded (LOCAL_PICKUP or a
        failed detail fetch).
    """
    candidates = [it for it in items if not (_BOOK_BITS_KEYWORDS & _title_words(it['title']))] or items

    first = candidates[0]
    cheapest = first if trust_best_match else min(candidates, key=lambda x: x['total_cost'])

    verified_ids = set()
    if cheapest is not first:
        for candidate in (first, cheapest):
            real_ship = ebay_api._fetch_item_shipping(candidate['item_id'])
            if real_ship is not None:
                candidate['shipping'] = real_ship
                candidate['total_cost'] = candidate['price'] + real_ship
                verified_ids.add(candidate['item_id'])

    if cheapest['total_cost'] <= first['total_cost'] * _CHEAPER_THRESHOLD:
        winner = cheapest
        if winner is not first and stdout is not None:
            stdout.write(
                f'  [cheaper alternative] ${cheapest["total_cost"]:.2f} beats '
                f'Best Match #1 (${first["total_cost"]:.2f})'
            )
    else:
        winner = first

    if winner['item_id'] in verified_ids:
        real_shipping = winner['shipping']
    else:
        real_shipping = ebay_api._fetch_item_shipping(winner['item_id'])
        if real_shipping is None:
            return None
        winner['shipping'] = real_shipping
        winner['total_cost'] = winner['price'] + real_shipping

    return winner


def _with_db_retry(operation, stderr, style):
    """Execute a single DB operation, recovering from a dropped connection (same as update_ebay_prices.py)."""
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
    """Fetch live eBay US prices for book Paperback/Hardback format rows via the Browse API."""

    help = (
        'Update Paperback/Hardback BookFormatPrice rows from eBay (E-Book/Audio '
        'Book are out of scope -- eBay is a physical-goods marketplace).'
    )

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', default=False, help='Show results without saving to the database.')
        parser.add_argument('--delay', type=float, default=1.2, metavar='SECONDS', help='Delay between API calls in seconds (default: 1.2).')
        parser.add_argument('--faction', type=str, default=None, metavar='NAME', help='Filter to a faction (e.g. "Horus Heresy Series").')
        parser.add_argument('--category', type=str, default=None, metavar='NAME', help='Filter to a category (e.g. "Warhammer").')
        parser.add_argument('--skus', type=str, default=None, metavar='SKUS', help='Comma-separated GW SKUs (e.g. "BOOK-HH-004,BOOK-HH-018").')
        parser.add_argument('--limit', type=int, default=None, metavar='N', help='Process only the first N format rows.')
        parser.add_argument('--debug', action='store_true', default=False, help='Print every eBay candidate returned for each query, not just the winner.')

    def handle(self, *args, **options):
        dry_run  = options['dry_run']
        delay    = options['delay']
        faction  = options['faction']
        category = options['category']
        skus     = [s.strip() for s in (options['skus'] or '').split(',') if s.strip()]
        limit    = options['limit']
        debug    = options['debug']

        try:
            ebay_api = EbayBrowseAPI(use_sandbox=False)
        except ValueError as exc:
            self.stderr.write(self.style.ERROR(f'Configuration error: {exc}'))
            return

        campaign_id = getattr(settings, 'EBAY_AFFILIATE_CAMPAIGN_ID', '')

        ebay_retailer, created = Retailer.objects.get_or_create(
            slug='ebay',
            defaults={'name': 'eBay', 'website': 'https://www.ebay.com', 'country': 'US', 'is_active': True},
        )
        if created:
            self.stdout.write(self.style.SUCCESS('Created eBay retailer in DB.'))

        gw_retailer = Retailer.objects.filter(name='Games Workshop', is_uk=False).first()
        if not gw_retailer:
            self.stderr.write(self.style.ERROR('Games Workshop (US) retailer not found in DB.'))
            return

        # ── Resolve GW-sourced Paperback/Hardback rows (with a verified ISBN) ───
        gw_qs = (
            BookFormatPrice.objects
            .filter(
                retailer=gw_retailer,
                format__in=[BookFormatPrice.FORMAT_SOFTBACK, BookFormatPrice.FORMAT_HARDBACK],
            )
            .exclude(isbn='')
            .select_related('product', 'product__faction', 'product__category')
        )

        if skus:
            gw_qs = gw_qs.filter(product__gw_sku__in=skus)
        if faction:
            gw_qs = gw_qs.filter(product__faction__name__iexact=faction)
        if category:
            gw_qs = gw_qs.filter(product__category__name__icontains=category)

        rows = list(gw_qs.order_by('product__name', 'format'))
        if limit:
            rows = rows[:limit]

        if not rows:
            self.stdout.write(self.style.WARNING('No matching book format rows found for the given filters.'))
            return

        env_label = 'DRY RUN — nothing will be written' if dry_run else 'LIVE — writing to DB'
        self.stdout.write(f'\neBay Book Price Update\n{"=" * 50}')
        self.stdout.write(f'  Mode        : {env_label}')
        self.stdout.write(f'  Rows        : {len(rows)}')
        self.stdout.write(f'  EPN campaign: {campaign_id or "NOT configured"}')
        self.stdout.write('=' * 50 + '\n')

        found = not_found = skipped_override = errors = 0

        for idx, row in enumerate(rows, 1):
            product = row.product
            fmt_display = row.get_format_display()
            override_key = f'{product.gw_sku}:{row.format}'
            self.stdout.write(f'[{idx}/{len(rows)}] {product.name} ({fmt_display})')

            # ── manual_url_override guard ───────────────────────────────────────
            existing, db_ok = _with_db_retry(
                lambda: BookFormatPrice.objects.filter(
                    product=product, retailer=ebay_retailer, format=row.format
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

            query = _build_query(product, row.isbn, override_key)
            try:
                items = ebay_api.search_items(query, max_results=_MAX_SEARCH_RESULTS)
            except EbayAPIError as exc:
                self.stdout.write(self.style.ERROR(f'  eBay API error: {exc}'))
                errors += 1
                time.sleep(delay)
                continue
            except RuntimeError as exc:
                self.stdout.write(self.style.WARNING(f'  Error: {exc}'))
                errors += 1
                time.sleep(delay)
                continue

            if debug:
                self.stdout.write(f'  query: "{query}" -> {len(items)} result(s)')
                for it in items:
                    self.stdout.write(f'    ${it["total_cost"]:>7} | {it["title"][:75]}')

            if not items:
                self.stdout.write(self.style.WARNING('  Not found on eBay.'))
                if not dry_run:
                    _, db_ok = _with_db_retry(
                        lambda: BookFormatPrice.objects.update_or_create(
                            product=product, retailer=ebay_retailer, format=row.format,
                            defaults={'price': None, 'url': '', 'in_stock': False, 'not_available': True, 'isbn': row.isbn},
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
                            product=product, retailer=ebay_retailer, format=row.format,
                            defaults={'price': None, 'url': '', 'in_stock': False, 'not_available': True, 'isbn': row.isbn},
                        ),
                        self.stderr, self.style,
                    )
                    if not db_ok:
                        errors += 1
                not_found += 1
                time.sleep(delay)
                continue

            total_cost = winner['total_cost']
            url = _add_epn_params(winner['url'], campaign_id)
            title_preview = winner['title'][:70].encode('ascii', 'replace').decode('ascii')

            self.stdout.write(self.style.SUCCESS(
                f'  ${total_cost:.2f} (${winner["price"]:.2f} + ${winner["shipping"]:.2f} ship) — {title_preview}'
            ))
            self.stdout.write(f'  URL: {url}')

            if not dry_run:
                _, db_ok = _with_db_retry(
                    lambda: BookFormatPrice.objects.update_or_create(
                        product=product, retailer=ebay_retailer, format=row.format,
                        defaults={
                            'price': total_cost, 'currency': 'USD', 'url': url,
                            'listing_title': winner['title'][:300],
                            'in_stock': True, 'not_available': False, 'isbn': row.isbn,
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
        self.stdout.write(self.style.SUCCESS('Summary'))
        self.stdout.write('=' * 50)
        self.stdout.write(f'  Found            : {found}')
        self.stdout.write(f'  Not found        : {not_found}')
        self.stdout.write(f'  Manual override  : {skipped_override} (skipped)')
        self.stdout.write(f'  Errors           : {errors}')
