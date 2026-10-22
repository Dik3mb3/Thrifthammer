"""
Find and optionally apply eBay prices for Gundam products that have none stored.

eBay has no usable GTIN/barcode data for this catalog (verified directly
against both the Browse API's `gtin` search parameter and ebay.com's own
search -- both return zero results for every barcode tried), so the
barcode-anchored approach used for Amazon (find_gundam_amazon_asins.py)
doesn't work here. Instead this uses a stricter version of keyword search:

  1. Extract each product's Gunpla kit number (e.g. "MSZ-006", "BB198") and
     search eBay by that number alone -- far more specific than a full name
     search, and returns every grade/variant of that kit as candidates.
  2. Group our own catalog by kit number and diff each product's name
     against its siblings' names to find the words that are genuinely
     distinguishing (e.g. "Revive", "Ver.Ka", "HD Color") vs. shared base
     words ("Zeta", "Gundam") -- data-driven from our own product names,
     not a hand-typed keyword list.
  3. A candidate listing must contain ALL of a product's own distinguishing
     words (+ the kit number, + its grade) and NONE of any sibling's
     distinguishing words. Take the first Best Match candidate that passes.

This directly targets the failure mode discovered during the Amazon keyword
search: same kit number, same grade even, but the wrong specific
variant/color release matching because eBay/Amazon's own relevance ranking
doesn't understand Gunpla variant naming.

Products with no extractable kit number (a handful of one-off items with no
siblings to disambiguate against, e.g. "Metal Build Zeta Gundam") fall back
to a plain cleaned-name search with no exclusion set.

A product may set Product.ebay_search_name, a plainer phrase sellers actually use.
It becomes the eBay search query, and its words (not the product name's) are what a
listing title must contain. Excluded words (siblings' words and negative keywords) still apply.

Per-product exceptions (a wrong match whose bad word doesn't fall out of the
auto sibling-diff) are NOT handled with hardcoded overrides in this file --
same rule as the rest of the site's eBay matching: only Product.ebay_negative_keywords
(a real, reviewed, user-directed data field) may refine a match, never a
code-level shortcut.

Selection (Gundam only, mirrors the Warhammer matcher): Best Match #1 decides which
kit it is, and the cheapest valid listing replaces it when it is at least 10% cheaper
delivered, from the first 10 results, with every word of the kit's name or phrase, no
spare-part or accessory word, and at least 50% of the Gundam Planet price.

Worldwide listings (Gundam only): the search above uses the shared client, which only
looks at New fixed-price listings located in the US. A second search accepts New
fixed-price listings from sellers anywhere that ship to the US (see _search_outside_us).
The best US listing wins unless the best worldwide one is at least 25% cheaper delivered
(see _pooled_winner); with no valid US listing the worldwide one is used. Duties and taxes
are NOT in any price (eBay gives no figure). The chart tags worldwide picks "[ABROAD JP]"
and the stored price includes the real shipping to the US. The shared client and Warhammer
matching are unchanged.

Workflow:
  1. Run without --apply to see matches (nothing written).
  2. Review the chart. For any wrong result, add the distinguishing word to
     that product's ebay_negative_keywords field (same process as the
     Warhammer side) and re-run.
  3. Re-run with --apply to write to the database.

Usage:
    python manage.py find_gundam_ebay_prices                     # dry run, all products
    python manage.py find_gundam_ebay_prices --apply              # write to DB
    python manage.py find_gundam_ebay_prices --batch-tag zeta-gundam
    python manage.py find_gundam_ebay_prices --batch-tag 08th-ms-team --rematch 242

--rematch re-runs the matcher for a kit that already has a link (after its phrase or
negative keywords were corrected). It never empties anything: a new match replaces the
link, no match leaves the old link untouched.

A "#NNN" catalog number ("HGUC #79" vs "HGUC #210", two releases of one suit) works in a
phrase (it must appear in the title) and as a negative keyword "#210" (a title that writes
it is rejected); plain digits in a negative keyword stay blocked item ids.
"""

import re
import shlex
import time
from collections import defaultdict
from decimal import Decimal

from django.conf import settings
from django.core.management.base import BaseCommand

from gundam.models import CurrentPrice, Product
from products.ebay_api_client import (
    DAILY_CALL_SAFETY_LIMIT, MARKETPLACE_ID, EbayAPIError, EbayBrowseAPI,
)
from products.models import Retailer

_CALL_DELAY = 0.3  # eBay's daily limit is generous (100k/day); light pacing only
_MAX_CANDIDATES = 50

# Gundam only: when no US-located listing passes the checks, fall back to New
# fixed-price listings from sellers anywhere that ship to the US. Many Gunpla
# kits (out of print, exclusives) are only sold from Japan. The shared client
# (and so every Warhammer search) still searches US-located listings only.
_ABROAD_FILTER = 'buyingOptions:{FIXED_PRICE},conditions:{NEW},deliveryCountry:US'

# Title words that mark an accessory sheet, never the kit (approved 2026-10-17
# after decal and etched-metal sheets matched kits). Applied to every Gundam kit
# unless a kit's own required words include the word.
_GUNDAM_BASELINE_EXCLUDED = frozenset({'decal', 'decals', 'waterslide', 'sticker', 'stickers', 'etched'})

_KIT_RE = re.compile(r'\b([A-Z]{1,4}-\d{2,5}[A-Z]?(?:/[A-Z0-9-]+)?|BB\d{2,4})\b')
# "senshi" excluded: real listings for the BB-series (SD chibi kits) often
# drop it entirely (e.g. "Bandai Hobby Legend BB No. 198 BB198 ... Zeta
# Gundam"), so requiring it produces false negatives for real listings.
_STOPWORDS = {'zeta', 'gundam', 'mobile', 'suit', 'the', 'and', 'of', 'a', 'z', 'senshi'}
# Word-form equivalences -- eBay sellers spell some words differently than
# our own product names do. Applied to BOTH required and excluded checks
# (via _expand), so e.g. requiring/excluding "ver" also matches "version".
_TERM_ALT = {
    'hguc': {'hguc', 'hg'},
    'ver':  {'ver', 'version'},
    'mg':   {'mg', 'master'},
}


def _expand(term):
    return _TERM_ALT.get(term, {term})

# EPN affiliate tracking parameters (US marketplace) -- same as
# products/management/commands/update_ebay_prices.py's _add_epn_params.
_EPN_PARAMS = 'mkcid=1&mkrid=711-53200-19255-0&toolid=10001&mkevt=1'


def _add_epn_params(url, campaign_id):
    """Append eBay Partner Network tracking parameters to an eBay item URL."""
    if not campaign_id:
        return url
    for marker in ('mkcid=1', '&mkcid=1'):
        idx = url.find(marker)
        if idx != -1:
            url = url[:idx].rstrip('?&')
            break
    separator = '&' if '?' in url else '?'
    return f'{url}{separator}{_EPN_PARAMS}&campid={campaign_id}'


def _safe(text):
    """Strip characters the Windows console (cp1252) can't print."""
    return str(text).encode('cp1252', errors='replace').decode('cp1252')


def _kit_number(name):
    m = _KIT_RE.search(name)
    return m.group(1) if m else None


# Collapses dotted-acronym runs ("A.E.U.G.", "A.N.I.M.E.") into one word
# ("AEUG", "ANIME") before tokenizing. Our own product names spell these
# without dots; real eBay listing titles usually use the dotted form. Without
# this, both sides tokenize the same acronym differently and never match.
# Deliberately narrow (2+ single letters each followed by a dot) so it does
# NOT touch "Ver.Ka" (a 2-letter, non-single-letter-run token) or "Ver. Rare"
# (space breaks the run).
_DOTTED_ACRONYM_RE = re.compile(r'\b(?:[A-Za-z]\.){2,}')


def _collapse_dotted_acronyms(text):
    return _DOTTED_ACRONYM_RE.sub(lambda m: m.group(0).replace('.', ''), text)


def _strip_seps(text):
    """Strip hyphens and slashes so e.g. 'FXA-05D/RX-178' -> 'fxa05drx178' as
    one token on both the required-term side and the title-tokenizing side --
    without this, a compound kit number keeps its slash on one side but the
    title tokenizer (which treats '/' as a separator) never produces a
    matching token on the other, so the required check can never pass."""
    return text.replace('-', '').replace('/', '')


# A "#NNN" catalog number ("HGUC #79", "HGUC #210") is what tells two releases of
# the same suit apart when their names and kit numbers are identical. Bare short
# digits are normally dropped as noise, so a hash number is kept as one token
# ("hash79") on every side: phrases, titles and negative keywords. Only the
# explicit "#" form counts, so "1/144" and "RX-79" never produce one.
_HASH_NUMBER_RE = re.compile(r'#\s*(\d{2,3})\b')


def _hash_tokens(text):
    """Return the "hash###" tokens for every "#NNN" catalog number written in text."""
    return {'hash' + digits for digits in _HASH_NUMBER_RE.findall(text)}


def _clean_words(name, kit_num=None):
    """
    Tokenize a product name into meaningful words for comparison.

    Strips hyphens before tokenizing (so "MSZ-006" -> "msz006" as one token,
    matching how a hyphen-stripped eBay title tokenizes), collapses dotted
    acronyms ("A.E.U.G." -> "AEUG"), drops the kit number itself, common
    stopwords, bare short numeric tokens (scale fractions like "1/144" are
    noisy split into "1"/"144" and rarely distinguish one variant from
    another), and single-character tokens. A "#NNN" catalog number is kept as
    one "hash###" token (see _HASH_NUMBER_RE).
    """
    text = _strip_seps(_collapse_dotted_acronyms(name))
    words = re.findall(r'[a-z0-9]+', text.lower())
    kn_clean = _strip_seps(kit_num).lower() if kit_num else None
    kept = {
        w for w in words
        if w not in _STOPWORDS
        and w != kn_clean
        and len(w) > 1
        and not (w.isdigit() and len(w) <= 3)
    }
    return kept | _hash_tokens(name)


# BB Senshi kits are identified by their number, and eBay sellers write it many
# ways: "BB390", "BB-390", "BB 390", "BB #390", "BB# 390", "BB No. 391",
# "BB Senshi 392", "BB Senshi No.392". The product name side always yields the
# single token "bb390", so the title side must produce the same token.
# Requires the letters "bb" as a whole word directly before the number, so
# "BB392EVO" (a bike part) and "No. 391" with no "BB" in front never qualify.
_BB_NUMBER_RE = re.compile(r'\bbb\s*(?:senshi\s*)?(?:no\.?\s*|number\s*)?#?\s*(\d{2,4})\b')
_BB_KIT_TOKEN_RE = re.compile(r'bb\d{2,4}')
_BB_LISTING_TOKEN_RE = re.compile(r'bb\d{3}')


def _title_words(title):
    """
    Tokenize an eBay listing title into a set of lowercase words.

    Besides plain words, a BB Senshi number written in any common style is
    added as one "bb###" token (plus "bb" itself when only the glued form was
    present), so it compares equal to the token built from our product name.
    A "#NNN" catalog number is added as one "hash###" token.
    """
    text = _strip_seps(_collapse_dotted_acronyms(title)).lower()
    words = set(re.findall(r'[a-z0-9]+', text)) | _hash_tokens(title)
    for match in _BB_NUMBER_RE.finditer(text):
        words.add('bb' + match.group(1))
    if any(_BB_KIT_TOKEN_RE.fullmatch(word) for word in words):
        words.add('bb')
    return words


def _parse_negative_keywords(raw):
    """
    Split Product.ebay_negative_keywords into (excluded_words, blocked_item_ids).

    Same convention as products/ebay_api_client.py: a pure-digit token is a
    blocked eBay item ID (checked against the candidate's own item ID), not
    a title word. A "#NNN" token ("#210") is the catalog-number word instead:
    it excludes titles that write that number.
    """
    words, item_ids = set(), set()
    for token in shlex.split(raw or ''):
        token = token.strip()
        if not token:
            continue
        if _HASH_NUMBER_RE.fullmatch(token):
            words |= _hash_tokens(token)
        elif token.isdigit():
            item_ids.add(token)
        else:
            # Same normalization as title tokenizing (_strip_seps +
            # _collapse_dotted_acronyms) so e.g. "P-Bandai" matches a title's
            # hyphen-stripped "pbandai" token instead of silently never firing.
            words.add(_strip_seps(_collapse_dotted_acronyms(token)).lower())
    return words, item_ids


def _phrase_words(product):
    """
    Return the words an eBay title must contain when the product has a plainer
    ebay_search_name, or an empty set when it does not.

    Same convention as the Warhammer side: the phrase is what we expect sellers
    to call the kit, so a listing is checked against it, not against our own
    product name (which carries codes and punctuation sellers leave out).
    """
    if not product.ebay_search_name:
        return set()
    words = _clean_words(product.ebay_search_name)
    kit_num = _kit_number(product.name)
    if kit_num and kit_num.startswith('BB'):
        # The BB number is the kit's identity and short digits are dropped from
        # the phrase, so keep it as a required token or "BB 360" and "BB 390"
        # kits that share words (Unicorn Gundam) could match each other's listing.
        words.add(_strip_seps(kit_num).lower())
    return words


def _build_term_sets(products):
    """
    Group products by kit number and compute each product's required
    (its own distinguishing words + kit number) and excluded (its
    siblings' distinguishing words, plus its own ebay_negative_keywords)
    term sets.

    Products with no extractable kit number get required = their own
    cleaned name words, excluded = ebay_negative_keywords only (no sibling
    group to compare against), and search_query = their cleaned name.

    Returns:
        dict[product.pk] -> {'required': set, 'excluded': set,
                              'blocked_item_ids': set, 'query': str}
    """
    groups = defaultdict(list)
    standalone = []
    for p in products:
        kn = _kit_number(p.name)
        if kn:
            groups[kn].append(p)
        else:
            standalone.append(p)

    result = {}

    for kn, members in groups.items():
        word_sets = {p.pk: _clean_words(p.name, kn) for p in members}
        common = set.intersection(*word_sets.values()) if len(members) > 1 else set()
        # "BB###" kit numbers are short and generic enough to collide with
        # unrelated real-world part numbers across all of eBay (car parts,
        # toy SKUs, etc.) -- requiring "gundam" too kills that junk. Longer
        # hyphenated kit numbers (MSZ-006, RX-178, MSN-00100...) are already
        # specific enough on their own, and some genuine listings for them
        # don't say "Gundam" anywhere in the title, so forcing it there only
        # creates false negatives.
        base_required = {_strip_seps(kn).lower()}
        if kn.startswith('BB'):
            base_required.add('gundam')
        for p in members:
            extra = word_sets[p.pk] - common
            others_extra = set()
            for op in members:
                if op.pk != p.pk:
                    others_extra |= (word_sets[op.pk] - common)
            neg_words, neg_ids = _parse_negative_keywords(p.ebay_negative_keywords)
            result[p.pk] = {
                'required':         _phrase_words(p) or (extra | base_required),
                'excluded':         others_extra - extra | neg_words,
                'blocked_item_ids': neg_ids,
                'query':            p.ebay_search_name or kn,
            }

    for p in standalone:
        words = _clean_words(p.name)
        neg_words, neg_ids = _parse_negative_keywords(p.ebay_negative_keywords)
        result[p.pk] = {
            'required':         _phrase_words(p) or words,
            'excluded':         neg_words,
            'blocked_item_ids': neg_ids,
            'query':            p.ebay_search_name or p.name,
        }

    for terms in result.values():
        # Accessory sheets (decals, stickers, etched metal parts) carry the kit
        # name in their titles; never let them stand in for the kit itself.
        terms['excluded'] |= _GUNDAM_BASELINE_EXCLUDED - terms['required']

    return result


def _matches(title, required, excluded):
    """
    Return True when the title has every required word and no excluded word.

    A BB Senshi kit also rejects any title naming a different BB number, which
    keeps a two-kit lot ("BB 390 + BB 391") or a sibling's listing from matching.
    """
    tw = _title_words(title)
    own_bb = {term for term in required if _BB_KIT_TOKEN_RE.fullmatch(term)}
    if own_bb and {w for w in tw if _BB_LISTING_TOKEN_RE.fullmatch(w)} - own_bb:
        return False
    for term in required:
        if not (tw & _expand(term)):
            return False
    for term in excluded:
        if tw & _expand(term):
            return False
    return True


def _first_match(items, terms):
    """Return the first listing that passes the word check and is not a blocked item id."""
    blocked_ids = terms.get('blocked_item_ids', set())
    for item in items:
        if not _matches(item['title'], terms['required'], terms['excluded']):
            continue
        legacy_id = item['item_id'].split('|')[1] if item['item_id'].count('|') == 2 else item['item_id']
        if legacy_id in blocked_ids:
            continue
        return item
    return None


# Same selection rule as the Warhammer matcher (EbayBrowseAPI.find_best_match_for_product):
# trust Best Match #1 for which kit it is, but take the cheapest valid listing when it is
# at least 10% cheaper delivered. Small gaps are not worth the identity risk.
_CHEAPER_THRESHOLD = Decimal('0.90')

# Spare parts and aftermarket items must never compete for "cheapest": they are the cheap
# listings. A title word here rejects the listing unless the kit's own required words contain
# it (so a kit literally named "... Parts Set" still matches). Unlike the Warhammer list this
# one leaves out "custom", "head", "metal", "exclusive": Gunpla kit names use them.
_SPARE_PART_WORDS = frozenset({
    'part', 'parts', 'replacement', 'conversion', 'resin', 'upgrade', 'upgrades', 'bits', 'bit',
    'sprue', 'sprues', 'runner', 'runners', 'garage', 'gk', 'accessory', 'accessories',
    'marking', 'markings', 'led', 'stand', 'assembled', 'built', 'painted', 'damaged',
    'broken', 'incomplete', 'missing', 'junk', 'option', 'options', 'expansion', 'launcher',
})

# An item priced under this share of the Gundam Planet price is a part or a sheet, not the kit
# (the same 50%-of-MSRP floor the Warhammer matcher uses).
_MIN_PRICE_FRACTION = Decimal('0.50')

# Like Warhammer (which only ever reads the first 10 Best Match results), a cheaper listing is
# only accepted from the first 10 results. Further down, Best Match has stopped meaning "same
# product" and the cheap ones are other kits, candy-toy figures, display cases and shims.
_CHEAPER_WINDOW = 10
_IDENTITY_STOPWORDS = frozenset({'the', 'and', 'of', 'a', 'mobile', 'suit'})


def _identity_words(product):
    """
    Return the alphabetic words of the kit's search phrase (or name), generic filler removed.

    The word check used for Best Match #1 drops words like "zeta" and "gundam" as noise, which
    is fine for picking the kit but lets "Metal Build Freedom Gundam" stand in for "Metal Build
    Zeta Gundam" on price. A listing that is only cheaper must carry every one of these words.
    Kit codes (RX-79G) are skipped because sellers write them many ways.
    """
    if product is None:
        return set()
    text = _strip_seps(_collapse_dotted_acronyms(product.ebay_search_name or product.name)).lower()
    return {word for word in re.findall(r'[a-z0-9]+', text) if word.isalpha()} - _IDENTITY_STOPWORDS


def _valid_listings(items, terms, product=None):
    """
    Return the listings, in Best Match order, that are the kit itself.

    A listing must pass the word check and the blocked-item-id check, must not carry a
    spare-part word, and must not be priced implausibly far below the kit's Gundam Planet
    price (the floor only applies when the kit has a price).
    """
    parts = _SPARE_PART_WORDS - terms['required']
    msrp = getattr(product, 'msrp', None)
    floor = Decimal(msrp) * _MIN_PRICE_FRACTION if msrp else Decimal('0')
    valid = []
    for rank, item in enumerate(items):
        if _first_match([item], terms) is None:
            continue
        if _title_words(item['title']) & parts or item['price'] < floor:
            continue
        item['rank'] = rank  # position in Best Match order, used by the cheaper-listing window
        valid.append(item)
    return valid


def _ranked_listings(client, valid, product=None):
    """
    Return the valid listings to try, best first (Warhammer rule: cheapest unless within 10%).

    Best Match #1 (the first valid listing) decides which kit it is. A cheaper listing can only
    replace it when it sits in the first 10 results and carries every word of the kit's own
    name or phrase. Real shipping is fetched for both candidates first, because search results
    often show $0 shipping that is not real; the cheaper one wins only when it is at least 10%
    cheaper delivered. Best Match #1 stays as the fallback if the winner cannot be priced.
    """
    first_valid = valid[0]
    own = _identity_words(product)
    pool = [item for item in valid
            if item.get('rank', 0) < _CHEAPER_WINDOW
            and all(_title_words(item['title']) & _expand(word) for word in own)] or [first_valid]
    cheapest = min(pool, key=lambda item: item['total_cost'])
    if cheapest is first_valid:
        return [first_valid]
    for candidate in (first_valid, cheapest):
        real = client._fetch_item_shipping(candidate['item_id'])
        if real is not None:
            candidate['shipping'] = real
            candidate['total_cost'] = candidate['price'] + real
            candidate['shipping_verified'] = True
    if cheapest['total_cost'] <= first_valid['total_cost'] * _CHEAPER_THRESHOLD:
        cheapest['best_match_total'] = first_valid['total_cost']
        return [cheapest, first_valid]
    return [first_valid]


def _priced_winner(client, ranked):
    """Return the first ranked listing whose real shipping resolves (total cost set), or None."""
    for candidate in ranked:
        if candidate.get('shipping_verified'):
            real = candidate['shipping']
        else:
            real = client._fetch_item_shipping(candidate['item_id'])
        if real is None:
            continue  # LOCAL_PICKUP or fetch failure: no real total cost
        candidate['shipping'] = real
        candidate['total_cost'] = candidate['price'] + real
        return candidate
    return None


# A worldwide listing replaces the best US listing only when it is at least 25% cheaper
# delivered. eBay gives no duty or tax figure, abroad sellers differ on whether duties are
# included, and economy shipping from Japan can take weeks, so a small saving is not worth it.
_WORLDWIDE_MARGIN = Decimal('0.75')

# Listings from sellers in these countries are never linked, even when they are the cheapest
# (the user's call, 2026-10-21). Codes are the ones eBay returns in itemLocation.country.
_AVOIDED_SELLER_COUNTRIES = frozenset({'LK', 'CN'})


def _best_in_pool(client, items, terms, product):
    """Return the priced winner of one search pool (Best Match #1 or a cheaper valid listing), or None."""
    valid = _valid_listings(items, terms, product)
    return _priced_winner(client, _ranked_listings(client, valid, product)) if valid else None


def _pooled_winner(client, product, terms, us_items, worldwide_items):
    """
    Pick the listing to link from the US results and the worldwide results.

    The best US listing wins unless the best worldwide listing is at least 25% cheaper
    delivered. With no valid US listing the worldwide one is used. The worldwide search also
    returns US-located listings the US search did not; those only need the usual 10% gap.
    Worldwide listings from an avoided seller country are dropped before anything is compared.
    The returned listing carries 'pool' ('us' or 'worldwide') and, when a worldwide listing
    won over a US one, 'us_best_total'.
    """
    worldwide_items = [item for item in worldwide_items
                       if item.get('ships_from') not in _AVOIDED_SELLER_COUNTRIES]
    us_win = _best_in_pool(client, us_items, terms, product)
    world_win = _best_in_pool(client, worldwide_items, terms, product)
    if world_win is None:
        if us_win is not None:
            us_win['pool'] = 'us'
        return us_win
    world_win['pool'] = 'worldwide'
    if us_win is None:
        return world_win
    margin = _CHEAPER_THRESHOLD if world_win.get('ships_from') == 'US' else _WORLDWIDE_MARGIN
    if world_win['total_cost'] <= us_win['total_cost'] * margin:
        world_win['us_best_total'] = us_win['total_cost']
        return world_win
    us_win['pool'] = 'us'
    return us_win


def _search_outside_us(client, keywords, max_results=_MAX_CANDIDATES):
    """
    Search eBay for New fixed-price listings that ship to the US from sellers
    located anywhere (Gundam only, used as a fallback after the US search).

    Reuses the shared client's session, token and result parser, but sends its
    own filter, so the client itself is unchanged. Each returned listing carries
    'ships_from', the seller's country code.
    """
    if client.api_calls_made >= DAILY_CALL_SAFETY_LIMIT:
        raise RuntimeError('Approaching eBay daily call limit. Stopping.')
    try:
        response = client.session.get(
            client.browse_endpoint,
            params={'q': keywords, 'filter': _ABROAD_FILTER, 'limit': str(min(max_results, 200)), 'fieldgroups': 'EXTENDED'},
            headers={
                'Authorization': f'Bearer {client._get_access_token()}',
                'X-EBAY-C-MARKETPLACE-ID': MARKETPLACE_ID,
                'Content-Type': 'application/json',
            },
            timeout=10,
        )
    except Exception as exc:
        raise RuntimeError(f'eBay API network error: {exc}') from exc
    finally:
        client.api_calls_made += 1
    data = response.json()
    if not response.ok:
        raise EbayAPIError(f'eBay API error for "{keywords}": {client._extract_browse_error(data)} (HTTP {response.status_code})')
    listings = []
    for raw in data.get('itemSummaries', []):
        parsed = client._parse_item(raw)
        if parsed is not None:
            parsed['ships_from'] = raw.get('itemLocation', {}).get('country', '')
            listings.append(parsed)
    return listings


class Command(BaseCommand):
    """Find eBay prices for Gundam products via kit-number + variant-term matching."""

    help = (
        'Search eBay for Gundam products with no price, using kit-number-anchored '
        'search with strict variant-term matching (no GTIN data exists on eBay for '
        'this catalog). Shows a chart of findings. Use --apply to write to DB.'
    )

    def add_arguments(self, parser):
        parser.add_argument('--batch-tag', help='Only search products with this batch_tag')
        parser.add_argument('--apply', action='store_true', help='Write results to the database')
        parser.add_argument(
            '--rematch', nargs='+', type=int, metavar='PRODUCT_ID', default=[],
            help='Also search these products even though they already have an eBay link. '
                 'A new match replaces the link; when nothing matches the existing link is '
                 'left exactly as it is (a row is never emptied).',
        )

    def handle(self, *args, **options):
        applying = options['apply']

        try:
            ebay_retailer = Retailer.objects.get(slug='ebay')
        except Retailer.DoesNotExist:
            self.stderr.write(self.style.ERROR('eBay retailer not found in DB.'))
            return

        all_products = Product.objects.filter(is_active=True)
        if options['batch_tag']:
            all_products = all_products.filter(batch_tag=options['batch_tag'])
        all_products = list(all_products.order_by('name'))

        has_url = set(
            CurrentPrice.objects
            .filter(retailer=ebay_retailer, product__in=all_products)
            .exclude(url='').exclude(url__isnull=True)
            .values_list('product_id', flat=True)
        ) - set(options['rematch'])
        candidates = [p for p in all_products if p.id not in has_url]
        skipped_count = len(all_products) - len(candidates)

        self.stdout.write(
            f'\nScope    : {"batch_tag=" + options["batch_tag"] if options["batch_tag"] else "all active Gundam products"}'
            f'\nMode     : {"APPLY - writing to DB" if applying else "DRY RUN - nothing will be written"}'
            f'\nMatching : kit-number search + required/excluded distinguishing-term filter'
            f'\nHave URL : {skipped_count} (skipped)'
            f'\nNo URL   : {len(candidates)} (will search)'
        )

        if not candidates:
            self.stdout.write(self.style.SUCCESS('\nAll products already have eBay prices. Nothing to do.\n'))
            return

        term_sets = _build_term_sets(candidates)

        try:
            client = EbayBrowseAPI()
        except ValueError as exc:
            self.stderr.write(self.style.ERROR(str(exc)))
            return

        found = []      # (product, item, total_cost, source)
        not_found = []  # (product, reason)

        for idx, product in enumerate(candidates):
            if idx > 0:
                time.sleep(_CALL_DELAY)

            terms = term_sets.get(product.pk)
            if not terms:
                not_found.append((product, 'no search terms'))
                continue

            try:
                items = client.search_items(terms['query'], max_results=_MAX_CANDIDATES)
            except EbayAPIError as exc:
                self.stderr.write(self.style.ERROR(f'  eBay error for "{_safe(product.name)}": {exc}'))
                not_found.append((product, 'API error'))
                continue
            except RuntimeError as exc:
                self.stderr.write(self.style.ERROR(f'  eBay error for "{_safe(product.name)}": {exc}'))
                not_found.append((product, 'API error'))
                continue

            # Sellers abroad that ship to the US are searched for every kit too: a worldwide
            # listing can win, but only by a clear margin (see _pooled_winner).
            time.sleep(_CALL_DELAY)
            try:
                abroad = _search_outside_us(client, terms['query'])
            except (EbayAPIError, RuntimeError) as exc:
                self.stderr.write(self.style.ERROR(f'  eBay error (abroad) for "{_safe(product.name)}": {exc}'))
                abroad = []

            # Best Match decides which kit it is; the cheapest valid listing wins when it is
            # at least 10% cheaper delivered (same rule as the Warhammer matcher).
            winner = _pooled_winner(client, product, terms, items, abroad)
            if winner is None:
                reason = 'winner had no resolvable shipping' if (
                    _valid_listings(items, terms, product) or _valid_listings(abroad, terms, product)
                ) else f'no match in {len(items)} candidates'
                not_found.append((product, reason))
                continue
            abroad_win = winner.get('pool') == 'worldwide' and winner.get('ships_from') != 'US'
            source = f'ABROAD {winner.get("ships_from") or "?"}' if abroad_win else 'MATCH'

            found.append((product, winner, winner['total_cost'], source))

        self.stdout.write('')

        if found:
            self.stdout.write(f'{"#":<4} {"Product Name":<45} {"Total":>8}  eBay Title')
            self.stdout.write('-' * 145)
            for i, (product, item, total_cost, source) in enumerate(found, 1):
                name_safe = _safe(product.name)[:44]
                title_safe = _safe(item['title'])[:80]
                tag = '' if source == 'MATCH' else f'[{source}] '
                beat = item.get('best_match_total')
                note = f'   <- cheaper than Best Match #1 (${beat:.2f})' if beat is not None else ''
                if item.get('us_best_total') is not None:
                    note += f'   <- 25%+ cheaper than the best US listing (${item["us_best_total"]:.2f})'
                self.stdout.write(self.style.SUCCESS(
                    f'{i:<4} {name_safe:<45} ${total_cost:>7.2f}  {tag}{title_safe}{note}'
                ))

        if applying and found:
            self.stdout.write('')
            written = 0
            campaign_id = getattr(settings, 'EBAY_AFFILIATE_CAMPAIGN_ID', '')
            for product, item, total_cost, source in found:
                url = _add_epn_params(item['url'], campaign_id)
                cp, created = CurrentPrice.objects.update_or_create(
                    retailer=ebay_retailer,
                    product=product,
                    defaults={
                        'url':           url,
                        'price':         total_cost,
                        'in_stock':      True,
                        'not_available': False,
                    },
                )
                written += 1
                self.stdout.write(f'  {"Created" if created else "Updated"}: {_safe(product.name)} -> {url}')
            self.stdout.write(self.style.SUCCESS(f'\n{written} price(s) written to database.'))

        self.stdout.write('\n' + '-' * 50)
        self.stdout.write(self.style.SUCCESS(f'  Matched      : {len(found)}'))
        self.stdout.write(self.style.WARNING(f'  Still no URL : {len(not_found)}'))
        if not_found:
            for p, reason in not_found:
                kept = ' -- existing link kept' if p.id in options['rematch'] else ''
                self.stdout.write(f'    - {_safe(p.name)}  ({reason}){kept}')

        if not applying:
            self.stdout.write(self.style.WARNING(
                '\nDry run complete. Review the chart above, add overrides if needed, '
                'then re-run with --apply.\n'
            ))
        else:
            self.stdout.write('')
