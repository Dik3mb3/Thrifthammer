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

Per-product exceptions (a wrong match whose bad word doesn't fall out of the
auto sibling-diff) are NOT handled with hardcoded overrides in this file --
same rule as the rest of the site's eBay matching: only Product.ebay_negative_keywords
(a real, reviewed, user-directed data field) may refine a match, never a
code-level shortcut.

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
"""

import re
import shlex
import time
from collections import defaultdict
from decimal import Decimal

from django.conf import settings
from django.core.management.base import BaseCommand

from gundam.models import CurrentPrice, Product
from products.ebay_api_client import EbayAPIError, EbayBrowseAPI
from products.models import Retailer

_CALL_DELAY = 0.3  # eBay's daily limit is generous (100k/day); light pacing only
_MAX_CANDIDATES = 50

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


def _clean_words(name, kit_num=None):
    """
    Tokenize a product name into meaningful words for comparison.

    Strips hyphens before tokenizing (so "MSZ-006" -> "msz006" as one token,
    matching how a hyphen-stripped eBay title tokenizes), collapses dotted
    acronyms ("A.E.U.G." -> "AEUG"), drops the kit number itself, common
    stopwords, bare short numeric tokens (scale fractions like "1/144" are
    noisy split into "1"/"144" and rarely distinguish one variant from
    another), and single-character tokens.
    """
    text = _strip_seps(_collapse_dotted_acronyms(name))
    words = re.findall(r'[a-z0-9]+', text.lower())
    kn_clean = _strip_seps(kit_num).lower() if kit_num else None
    return {
        w for w in words
        if w not in _STOPWORDS
        and w != kn_clean
        and len(w) > 1
        and not (w.isdigit() and len(w) <= 3)
    }


def _title_words(title):
    text = _strip_seps(_collapse_dotted_acronyms(title))
    return set(re.findall(r'[a-z0-9]+', text.lower()))


def _parse_negative_keywords(raw):
    """
    Split Product.ebay_negative_keywords into (excluded_words, blocked_item_ids).

    Same convention as products/ebay_api_client.py: a pure-digit token is a
    blocked eBay item ID (checked against the candidate's own item ID), not
    a title word.
    """
    words, item_ids = set(), set()
    for token in shlex.split(raw or ''):
        token = token.strip()
        if not token:
            continue
        if token.isdigit():
            item_ids.add(token)
        else:
            # Same normalization as title tokenizing (_strip_seps +
            # _collapse_dotted_acronyms) so e.g. "P-Bandai" matches a title's
            # hyphen-stripped "pbandai" token instead of silently never firing.
            words.add(_strip_seps(_collapse_dotted_acronyms(token)).lower())
    return words, item_ids


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
                'required':         extra | base_required,
                'excluded':         others_extra - extra | neg_words,
                'blocked_item_ids': neg_ids,
                'query':            kn,
            }

    for p in standalone:
        words = _clean_words(p.name)
        neg_words, neg_ids = _parse_negative_keywords(p.ebay_negative_keywords)
        result[p.pk] = {
            'required':         words,
            'excluded':         neg_words,
            'blocked_item_ids': neg_ids,
            'query':            p.name,
        }

    return result


def _matches(title, required, excluded):
    tw = _title_words(title)
    for term in required:
        if not (tw & _expand(term)):
            return False
    for term in excluded:
        if tw & _expand(term):
            return False
    return True


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
        )
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

            blocked_ids = terms.get('blocked_item_ids', set())
            winner = None
            for item in items:
                if not _matches(item['title'], terms['required'], terms['excluded']):
                    continue
                legacy_id = item['item_id'].split('|')[1] if item['item_id'].count('|') == 2 else item['item_id']
                if legacy_id in blocked_ids:
                    continue
                winner = item
                break

            if winner is None:
                not_found.append((product, f'no match in {len(items)} candidates'))
                continue

            real_shipping = client._fetch_item_shipping(winner['item_id'])
            if real_shipping is None:
                # LOCAL_PICKUP or fetch failure -- can't resolve a real total cost
                not_found.append((product, 'winner had no resolvable shipping'))
                continue
            winner['shipping'] = real_shipping
            winner['total_cost'] = winner['price'] + real_shipping

            found.append((product, winner, winner['total_cost'], 'MATCH'))

        self.stdout.write('')

        if found:
            self.stdout.write(f'{"#":<4} {"Product Name":<45} {"Total":>8}  eBay Title')
            self.stdout.write('-' * 145)
            for i, (product, item, total_cost, source) in enumerate(found, 1):
                name_safe = _safe(product.name)[:44]
                title_safe = _safe(item['title'])[:80]
                self.stdout.write(self.style.SUCCESS(
                    f'{i:<4} {name_safe:<45} ${total_cost:>7.2f}  {title_safe}'
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
                self.stdout.write(f'    - {_safe(p.name)}  ({reason})')

        if not applying:
            self.stdout.write(self.style.WARNING(
                '\nDry run complete. Review the chart above, add overrides if needed, '
                'then re-run with --apply.\n'
            ))
        else:
            self.stdout.write('')
