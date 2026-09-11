"""
Find and optionally apply Amazon prices for book BookFormatPrice rows that
have no Amazon price yet.

Same workflow as find_amazon_asins.py, adapted for books:
  1. Run without --apply to see what the API would find (nothing written).
  2. Review the output chart. Add overrides to ASIN_OVERRIDES for any wrong
     results, or SKIP_FORMATS for ones with no correct Amazon listing.
  3. Re-run with --apply to write the prices to the database.

Two different search strategies, depending on format:

  Paperback / Hardback -- searched by ISBN (the GW-sourced BookFormatPrice
  row for each format already carries the verified ISBN -- see
  populate_horus_heresy_books.py). ISBN search is precise enough that no
  brand filter is needed (unlike find_amazon_asins.py, which defaults to
  brand="Games Workshop" to disambiguate title search). GW remains the
  MSRP reference for these formats -- the Amazon row written here never
  sets is_msrp_source.

  E-Book / Audio Book -- neither has a print ISBN, so there is nothing to
  search by. Instead this searches by title + author + a format-specific
  suffix ("kindle edition" / "audiobook") and filters the results for a
  matching itemInfo.classifications.binding.displayValue ("Kindle Edition" /
  "Audible Audiobook") -- a plain title search otherwise mostly returns
  unrelated Games Workshop miniature kits, since GW's Amazon storefront
  covers both. GW does not sell e-books or audiobooks at all, so the Amazon
  row created here IS the MSRP reference for these two formats
  (is_msrp_source=True), unlike Paperback/Hardback.

  Audio Book pricing has an extra wrinkle: Audible listings commonly show
  TWO "New" offers -- a $0.00 "free with trial" promotional price (usually
  the buy-box winner) and the real cash "Buy Now" price. Only the latter is
  written; _best_audiobook_price() explicitly skips near-zero prices rather
  than taking the first "New" listing the way E-Book/Paperback/Hardback do.

Unlike find_amazon_asins.py (one CurrentPrice row per product), books need
one BookFormatPrice row per (product, format) -- different formats can have
different editions, ISBNs, and Amazon listings/prices entirely.

Format rows that already have an Amazon price are always skipped -- existing
data is never overwritten.

Not added to the Procfile -- run manually, on demand, same as
find_amazon_asins.py.

Usage:
    python manage.py find_amazon_book_asins --faction horus-heresy-series                    # dry run, all formats
    python manage.py find_amazon_book_asins --faction horus-heresy-series --apply             # write to DB
    python manage.py find_amazon_book_asins --faction horus-heresy-series --formats audiobook # Audible only
    python manage.py find_amazon_book_asins --category warhammer --brand "Black Library"
"""

import time

from django.conf import settings
from django.core.management.base import BaseCommand

from prices.models import BookFormatPrice
from products.models import Category, Faction, Product, Retailer
from scrapers.retailers.amazon_creators import AmazonCreatorsClient

SOFTBACK = BookFormatPrice.FORMAT_SOFTBACK
HARDBACK = BookFormatPrice.FORMAT_HARDBACK
EBOOK = BookFormatPrice.FORMAT_EBOOK
AUDIOBOOK = BookFormatPrice.FORMAT_AUDIOBOOK

_FORMAT_ALIASES = {'paperback': SOFTBACK, 'hardback': HARDBACK, 'ebook': EBOOK, 'audiobook': AUDIOBOOK}
_FORMAT_LABELS = dict(BookFormatPrice.FORMAT_CHOICES)
# Formats with no print ISBN -- searched by title instead, and are the MSRP
# source themselves since GW sells neither directly.
_TITLE_SEARCH_FORMATS = (EBOOK, AUDIOBOOK)

# ─── Manual ASIN overrides ────────────────────────────────────────────────────
# Add entries here when SearchItems returns the wrong listing for a
# (SKU, format) pair. Key format: 'gw_sku:format' -> ASIN.
# The override ASIN is used directly -- the API search is skipped entirely.
# These are permanent: leave them here so future runs always use the right ASIN.
#
# NOTE for override prices: an override skips the search, so its price still
# needs fetching separately (this command doesn't call GetItems for overrides).
# For an 'audiobook' override, do NOT use AmazonCreatorsClient.get_items() to
# fetch that price -- its shared _extract_price() takes the first "New"
# listing same as this file's _best_new_price(), which is the $0.00 trial
# offer for Audible titles. Fetch raw and apply _best_audiobook_price()-style
# logic (skip listings under _TRIAL_PRICE_THRESHOLD) instead.
#
# Example:
#   'BOOK-HH-006:softback': 'B0XXXXXXX',   # Horus Rising PB -- search returned wrong edition
ASIN_OVERRIDES = {
    'BOOK-HH-003:ebook': 'B0H5R5QD9C',  # Flames of Betrayal -- title search matched an
                                        # unrelated book; user-confirmed via direct Amazon link.
    'BOOK-HH-012:ebook': 'B0F94H9W6Z',  # Era of Ruin -- user-confirmed via direct Amazon link.
                                        # Same ASIN the ISBN search surfaced for the hardback
                                        # candidate at $13.99 (see SKIP_FORMATS below) -- that
                                        # was never a mismatched hardback, it's this Kindle
                                        # edition being surfaced by the hardback's ISBN search.
    'BOOK-HH-016:ebook': 'B0BVBSCR2G',  # The End and the Death Volume 1 -- title search matched
                                        # an unrelated book; user-confirmed via direct Amazon link.
    'BOOK-HH-012:audiobook': 'B0F9KZRT4Z',      # Era of Ruin -- title search found nothing
                                                 # ("Various Authors"); user-confirmed via direct link.
    'BOOK-HH-021:audiobook': 'B076DMFTXZ',      # The Flight of the Eisenstein -- title search found
                                                 # nothing; user-confirmed via direct link.
    'BOOK-HH-004:softback': '1844164764',       # Fulgrim -- no ISBN search match found; user-confirmed
                                                 # via direct link (this is Graham McNeill's classic HH
                                                 # novel, not the unrelated 40K "Fulgrim - The Perfect
                                                 # Son" -- verified before writing).
    'BOOK-40K-008:softback': '1789990580',      # Belisarius Cawl: The Great Work -- ISBN search found
                                                 # nothing; user-confirmed via direct link.
    'BOOK-40K-030:softback': '1804070785',      # Gaunt's Ghosts: The Victory (Part Two) -- ISBN search
                                                 # surfaced the Kindle edition instead (see SKIP_FORMATS
                                                 # below); user-confirmed the real paperback via direct link.
    'BOOK-40K-057:softback': '1836091648',      # The High Kâhl's Oath -- ISBN search found nothing;
                                                 # user-confirmed via direct link.
    'BOOK-40K-072:softback': '1836093608',      # Yarrick: The Omnibus -- ISBN search found nothing;
                                                 # user-confirmed via direct link.
    'BOOK-AOS-010:ebook': 'B0GNZRDM2W',          # Grombrindal: The Legend of the White Dwarf -- title
                                                  # search found nothing; user-confirmed via direct link.
    'BOOK-AOS-019:ebook': 'B0D14VLB37',          # War for the Mortal Realms -- title search found
                                                  # nothing; user-confirmed via direct link.
}

# (gw_sku, format) pairs to explicitly exclude from Amazon price discovery.
# Add a pair here if the API returns the wrong listing and there's no correct
# ASIN to substitute -- the format row will simply have no Amazon price.
# Format: 'gw_sku:format'
SKIP_FORMATS = {
    'BOOK-HH-012:hardback',  # Era of Ruin -- ISBN search's only "New" match was actually
                             # the Kindle edition (ASIN B0F94H9W6Z, see ASIN_OVERRIDES above),
                             # not a real hardback listing. No correct hardback ASIN
                             # confirmed yet -- revisit manually.

    # Warhammer 40,000 Books batch (2026-09-06 dry run) -- same "Era of Ruin" pitfall:
    # the physical-format ISBN search's only "New" match shares the exact same ASIN
    # and price as that title's independently-confirmed Kindle edition (title search +
    # binding filter), meaning the ISBN search surfaced the ebook, not a real print
    # listing. All are brand-new 2025/2026 releases without a distinct Amazon print
    # listing yet. No correct physical-format ASIN confirmed -- revisit manually.
    'BOOK-40K-006:hardback',   # Armageddon: Season of Fire -- shared ASIN B0H1GTDW1G, $13.99
    'BOOK-40K-010:hardback',   # Blackheart: Claws of the Maelstrom -- shared ASIN B0HGG4G4CT, $13.99
    'BOOK-40K-013:hardback',   # Chem Dog -- shared ASIN B0GNZW796L, $13.99
    'BOOK-40K-030:softback',   # Gaunt's Ghosts: The Victory (Part Two) -- shared ASIN B0BJLVLG8P, $21.99
    'BOOK-40K-058:hardback',   # The Infinite and the Divine -- shared ASIN B08J7DJCSJ, $9.99
    'BOOK-40K-064:hardback',   # The Wicked and the Warped -- shared ASIN B0H8S5VQ5J, $13.99
    'BOOK-40K-069:hardback',   # Voice of Command -- shared ASIN B0HDSLP983, $13.99

    # Same batch -- title search matched a completely unrelated book (wrong genre/author
    # entirely, not just a wrong edition). Confirmed by near-zero price plus zero shared
    # keywords between our title and the Amazon listing title.
    'BOOK-40K-012:ebook',      # Carnage Unending -- matched "Bewitching the Werewolf" ($0.00)
    'BOOK-40K-041:ebook',      # Legends of the Waaagh! -- matched a romance novel ($0.00)
    'BOOK-40K-048:ebook',      # Once a Killer -- matched "A Mersey Killing" true-crime book ($0.00)
    'BOOK-40K-048:audiobook',  # Once a Killer -- matched an unrelated Bruno Chief of Police audiobook
    'BOOK-40K-049:ebook',      # Paragon of Faith and Other Stories -- matched a Bible-study ebook ($0.99)
    'BOOK-40K-056:ebook',      # The Green Tide -- matched "Ask The River" ($0.00)
    'BOOK-40K-056:audiobook',  # The Green Tide -- matched an unrelated "Tides of Fortune" audiobook

    # Age of Sigmar Books batch (2026-09-06 dry run) -- same "Era of Ruin" pitfall:
    # the paperback ISBN search's only "New" match shares the exact same ASIN and
    # price as that title's independently-confirmed Kindle edition. No correct
    # paperback ASIN confirmed yet -- revisit manually.
    'BOOK-AOS-014:softback',   # Soulblight Gravelords: Masters of Death -- shared ASIN B0DZXW4FP2, $21.99
    'BOOK-AOS-020:softback',   # Witch Hunters: The Omnibus -- shared ASIN B0GX2PDX7Z, $21.99
}
# ─────────────────────────────────────────────────────────────────────────────

_CALL_DELAY = 1.1  # seconds between API calls — keeps us under 1 TPS
_TITLE_SEARCH_COUNT = 10  # title search returns lots of unrelated kits; need enough results to find the right binding among them
_TRIAL_PRICE_THRESHOLD = 1.00  # Audible "free with trial" offers price at $0.00 -- anything under this is that, not a real Buy Now price


def _build_url(asin):
    """Build a clean affiliate URL from an ASIN."""
    tag = settings.AMAZON_ASSOCIATE_TAG
    return f'https://www.amazon.com/dp/{asin}?tag={tag}'


def _best_new_price(item):
    """Extract the first new-condition listing price from a SearchItems result."""
    listings = item.get('offersV2', {}).get('listings', [])
    for listing in listings:
        if listing.get('condition', {}).get('value', 'New') != 'New':
            continue
        amount = listing.get('price', {}).get('money', {}).get('amount')
        if amount is not None:
            return float(amount)
    return None


def _binding(item):
    """The classifications.binding.displayValue of a SearchItems result item, if any."""
    return item.get('itemInfo', {}).get('classifications', {}).get('binding', {}).get('displayValue')


def _best_audiobook_price(item):
    """
    Extract the real "Buy Now" price from an Audible SearchItems result,
    skipping the $0.00 "free with your trial" promotional offer.

    Audible listings commonly carry two "New" offers with the same
    savingBasis (list price): a $0.00 trial offer (usually isBuyBoxWinner)
    and the actual cash price. Taking the first listing (as _best_new_price
    does for other formats) would silently write $0.00 as the price.
    """
    listings = item.get('offersV2', {}).get('listings', [])
    for listing in listings:
        if listing.get('condition', {}).get('value', 'New') != 'New':
            continue
        amount = listing.get('price', {}).get('money', {}).get('amount')
        if amount is not None and amount >= _TRIAL_PRICE_THRESHOLD:
            return float(amount)
    return None


# Per-format config for the two title-searched formats: the keyword suffix
# that reliably biases Amazon's search ranking toward the right binding (see
# module docstring), the classification binding string to filter for, and
# the price-extraction function to use.
_TITLE_SEARCH_CONFIG = {
    EBOOK: {
        'suffix': 'kindle edition',
        'target_binding': 'Kindle Edition',
        'price_fn': _best_new_price,
    },
    AUDIOBOOK: {
        'suffix': 'audiobook',
        'target_binding': 'Audible Audiobook',
        'price_fn': _best_audiobook_price,
    },
}


class Command(BaseCommand):
    """Find Amazon prices for book format rows. Dry-run by default."""

    help = (
        'Search Amazon for book format prices -- Paperback/Hardback by ISBN, '
        'E-Book (Kindle) by title. Shows a chart of findings. Use --apply to write to DB.'
    )

    def add_arguments(self, parser):
        group = parser.add_mutually_exclusive_group(required=True)
        group.add_argument(
            '--faction',
            help='Faction slug (e.g. horus-heresy-series)',
        )
        group.add_argument(
            '--category',
            help='Category slug (e.g. warhammer, under Books and Novels)',
        )
        parser.add_argument(
            '--apply',
            action='store_true',
            help='Write found prices to the database (default: dry run only)',
        )
        parser.add_argument(
            '--brand',
            default=None,
            help=(
                'Optional brand filter to pass to SearchItems. Default: none -- '
                'ISBN search is precise enough on its own, and books may be '
                'catalogued under "Black Library" rather than "Games Workshop".'
            ),
        )
        parser.add_argument(
            '--formats',
            default='paperback,hardback,ebook,audiobook',
            help='Comma-separated formats to search: paperback, hardback, ebook, audiobook (default: all four)',
        )

    def handle(self, *args, **options):
        applying = options['apply']
        brand = options['brand']

        requested = {f.strip().lower() for f in options['formats'].split(',') if f.strip()}
        unknown = requested - set(_FORMAT_ALIASES)
        if unknown:
            self.stderr.write(self.style.ERROR(
                f'Unknown format(s): {", ".join(sorted(unknown))}. Valid: paperback, hardback, ebook, audiobook.'
            ))
            return
        requested_values = {_FORMAT_ALIASES[f] for f in requested}

        try:
            amazon_retailer = Retailer.objects.get(slug='amazon')
        except Retailer.DoesNotExist:
            self.stderr.write(self.style.ERROR('Amazon retailer not found in DB.'))
            return

        gw_retailer = Retailer.objects.filter(name='Games Workshop', is_uk=False).first()
        if not gw_retailer:
            self.stderr.write(self.style.ERROR('Games Workshop (US) retailer not found in DB.'))
            return

        # ── Resolve faction or category ─────────────────────────────────────────
        if options['faction']:
            faction_slug = options['faction'].strip()
            try:
                faction = Faction.objects.get(slug=faction_slug)
            except Faction.DoesNotExist:
                self.stderr.write(self.style.ERROR(f'Faction "{faction_slug}" not found.'))
                return
            scope_label = f'Faction: {faction.name}'
            product_qs_kwargs = {'faction': faction}
        else:
            category_slug = options['category'].strip()
            try:
                category = Category.objects.get(slug=category_slug)
            except Category.DoesNotExist:
                slugs = list(Category.objects.order_by('name').values_list('slug', 'name'))
                self.stderr.write(self.style.ERROR(f'Category "{category_slug}" not found.'))
                self.stderr.write('Available categories:')
                for slug, name in slugs:
                    self.stderr.write(f'  {slug:<35} ({name})')
                return
            scope_label = f'Category: {category.name}'
            product_qs_kwargs = {'category': category}

        products = list(
            Product.objects.filter(is_active=True, **product_qs_kwargs).order_by('name')
        )
        has_amazon = set(
            BookFormatPrice.objects
            .filter(retailer=amazon_retailer, product__in=products)
            .exclude(url='').exclude(url__isnull=True)
            .values_list('product_id', 'format')
        )
        gw_isbns = {
            (row.product_id, row.format): row.isbn
            for row in BookFormatPrice.objects
                .filter(product__in=products, retailer=gw_retailer)
                .exclude(isbn='')
        }

        # ── Build candidates ─────────────────────────────────────────────────────
        # Each candidate: {product, format, mode ('isbn'|'title'), search_key, isbn}
        candidates = []
        total_possible = 0
        for product in products:
            for fmt_value in (SOFTBACK, HARDBACK):
                if fmt_value not in requested_values:
                    continue
                isbn = gw_isbns.get((product.id, fmt_value))
                if not isbn:
                    continue  # no verified ISBN for this (product, format) -- nothing to search with
                total_possible += 1
                if (product.id, fmt_value) in has_amazon:
                    continue
                candidates.append({
                    'product': product, 'format': fmt_value, 'mode': 'isbn',
                    'search_key': isbn, 'isbn': isbn,
                })
            for fmt_value in _TITLE_SEARCH_FORMATS:
                if fmt_value not in requested_values:
                    continue
                total_possible += 1
                if (product.id, fmt_value) in has_amazon:
                    continue
                # Appending the format's own suffix ("kindle edition" /
                # "audiobook") to the query itself -- not just filtering
                # results after the fact -- reliably biases Amazon's search
                # ranking toward the right binding as the top hit. Tested
                # against titles that previously mismatched badly under a
                # plain title+genre search with post-hoc binding filtering
                # (e.g. "Raldoron: Revenant" matching an unrelated novel).
                suffix = _TITLE_SEARCH_CONFIG[fmt_value]['suffix']
                title_search = f'{product.name} {product.author} {suffix}'.strip()
                candidates.append({
                    'product': product, 'format': fmt_value, 'mode': 'title',
                    'search_key': title_search, 'isbn': '',
                })

        skipped_count = total_possible - len(candidates)

        self.stdout.write(
            f'\n{scope_label}'
            f'\nMode         : {"APPLY — writing to DB" if applying else "DRY RUN — nothing will be written"}'
            f'\nBrand filter : {brand or "none"}'
            f'\nFormats      : {", ".join(sorted(requested))}'
            f'\nHave price   : {skipped_count} (skipped)'
            f'\nNo price     : {len(candidates)} (will search)'
        )

        if not candidates:
            self.stdout.write(self.style.SUCCESS(
                f'\nAll {total_possible} format row(s) already have Amazon prices. Nothing to do.\n'
            ))
            return

        client = AmazonCreatorsClient()

        # ── Search phase ──────────────────────────────────────────────────────
        found = []      # (cand, asin, amazon_title, api_price, source)
        not_found = []  # candidates where search returned nothing

        for idx, cand in enumerate(candidates):
            if idx > 0:
                time.sleep(_CALL_DELAY)

            override_key = f'{cand["product"].gw_sku}:{cand["format"]}'

            # Explicitly skipped — no Amazon price wanted for this format
            if override_key in SKIP_FORMATS:
                not_found.append(cand)
                continue

            # Check for manual override first
            if override_key in ASIN_OVERRIDES:
                asin = ASIN_OVERRIDES[override_key]
                found.append((cand, asin, '(override — not searched)', None, 'OVERRIDE'))
                continue

            try:
                if cand['mode'] == 'isbn':
                    items = client.search_items(
                        keywords=cand['search_key'],
                        marketplace='www.amazon.com',
                        brand=brand,
                        item_count=1,
                    )
                    top = items[0] if items else None
                else:  # title mode — filtered to the format's specific binding from a noisier result set
                    target_binding = _TITLE_SEARCH_CONFIG[cand['format']]['target_binding']
                    items = client.search_items(
                        keywords=cand['search_key'],
                        marketplace='www.amazon.com',
                        brand=brand,
                        item_count=_TITLE_SEARCH_COUNT,
                        resources=[
                            'itemInfo.title',
                            'itemInfo.classifications',
                            'offersV2.listings.price',
                            'offersV2.listings.condition',
                        ],
                    )
                    top = next(
                        (it for it in items if _binding(it) == target_binding),
                        None,
                    )
            except Exception as exc:
                detail = ''
                if hasattr(exc, 'response') and exc.response is not None:
                    try:
                        detail = str(exc.response.json())
                    except Exception:
                        detail = exc.response.text[:120]
                self.stderr.write(self.style.ERROR(
                    f'  API error for "{cand["product"].name}" '
                    f'({_FORMAT_LABELS[cand["format"]]}): {exc}'
                    + (f'\n  Detail: {detail}' if detail else '')
                ))
                not_found.append(cand)
                continue

            if not top:
                not_found.append(cand)
                continue

            asin = top.get('asin', '')
            amazon_title = top.get('itemInfo', {}).get('title', {}).get('displayValue', '—')
            price_fn = _TITLE_SEARCH_CONFIG[cand['format']]['price_fn'] if cand['mode'] == 'title' else _best_new_price
            api_price = price_fn(top)

            if not asin:
                not_found.append(cand)
                continue

            found.append((cand, asin, amazon_title, api_price, 'API'))

        # ── Report ────────────────────────────────────────────────────────────
        self.stdout.write('')

        if found:
            self.stdout.write(
                f'{"#":<4} {"Product Name":<38} {"Format":<10} {"Key":<15} {"ASIN":<12} {"Price":>8}  {"Src":<8}  Amazon Title'
            )
            self.stdout.write('─' * 165)

            for i, (cand, asin, amazon_title, api_price, source) in enumerate(found, 1):
                price_str = f'${api_price:.2f}' if api_price is not None else '—'
                key_display = cand['isbn'] or '(title search)'
                fmt_display = _FORMAT_LABELS[cand['format']]
                src_style = self.style.WARNING if source == 'OVERRIDE' else self.style.SUCCESS
                self.stdout.write(src_style(
                    f'{i:<4} {cand["product"].name[:37]:<38} {fmt_display:<10} {key_display:<15} {asin:<12} {price_str:>8}  {source:<8}  {amazon_title}'
                ))

        # ── Apply ─────────────────────────────────────────────────────────────
        if applying and found:
            self.stdout.write('')
            written = 0
            for cand, asin, amazon_title, api_price, source in found:
                url = _build_url(asin)
                # Amazon is the MSRP source for E-Book/Audio Book (GW sells
                # neither directly), but never for Paperback/Hardback where
                # GW already holds that role.
                is_msrp = cand['format'] in _TITLE_SEARCH_FORMATS
                bfp, created = BookFormatPrice.objects.get_or_create(
                    retailer=amazon_retailer,
                    product=cand['product'],
                    format=cand['format'],
                    defaults={
                        'url':           url,
                        'price':         api_price,
                        'currency':      'USD',
                        'in_stock':      api_price is not None,
                        'not_available': api_price is None,
                        'isbn':          cand['isbn'],
                        'listing_title': amazon_title if amazon_title != '—' else '',
                        'is_msrp_source': is_msrp,
                    },
                )
                if not created:
                    # Record exists but had no URL — update URL only
                    bfp.url = url
                    bfp.save(update_fields=['url'])
                written += 1
                fmt_display = _FORMAT_LABELS[cand['format']]
                self.stdout.write(
                    f'  {"Created" if created else "Updated"}: '
                    f'{cand["product"].name} ({fmt_display}) → {url}'
                )
            self.stdout.write(self.style.SUCCESS(f'\n{written} price row(s) written to database.'))

        # ── Summary ───────────────────────────────────────────────────────────
        self.stdout.write('\n' + '─' * 50)
        self.stdout.write(self.style.SUCCESS(f'  Found via API    : {sum(1 for *_, s in found if s == "API")}'))
        self.stdout.write(self.style.WARNING(f'  From overrides   : {sum(1 for *_, s in found if s == "OVERRIDE")}'))
        self.stdout.write(self.style.WARNING(f'  Still no price   : {len(not_found)}'))
        if not_found:
            for cand in not_found:
                fmt_display = _FORMAT_LABELS[cand['format']]
                key_display = cand['isbn'] or '(title search)'
                self.stdout.write(f'    - {cand["product"].name} ({fmt_display}, {key_display})')

        if not applying:
            self.stdout.write(self.style.WARNING(
                '\nDry run complete. Review the chart above, add any overrides to '
                'ASIN_OVERRIDES in this file,\nthen re-run with --apply to write to the database.\n'
            ))
        else:
            self.stdout.write('')
