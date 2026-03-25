"""
Noble Knight Games scraper — Zoovu search API approach.

Noble Knight's search results page is JavaScript-rendered (SiteSearch360 /
Zoovu), so standard HTML scraping of the search page returns empty placeholders.
Instead, this scraper calls the Zoovu search API directly — the same API that
Noble Knight's own page uses to populate product listings.

API endpoint:
    https://api.search.zoovu.com/search?projectId=43167&query={query}&limit=50

Project ID 43167 is Noble Knight's Zoovu project ID (embedded in their
/bundles/js/bundle/51850.js bundle file).

Approach:
  For each active product:
    1. Search the NK Zoovu API using the product name.
    2. Filter candidates to boxed miniature sets (Miniatures Box Set / Pack),
       in-stock, and new/near-mint condition only.
    3. Score candidates against our product name using an F1-like word-overlap
       formula (same algorithm as MiniatureMarketScraper).
    4. Accept the cheapest candidate that meets the score threshold.
    5. Upsert CurrentPrice with the price and direct NK product URL.

Condition filtering:
    Noble Knight grades items and lists them at various conditions. We only want
    items that are new or essentially new:
      - SW (...)      — Shrink Wrapped: factory-sealed, equivalent to new
      - MINT/New      — Explicitly new
      - NM            — Near Mint: open box but pristine, essentially new

    We explicitly exclude: VG, VG+, EX, Fair, used conditions (even when
    combined with NM, e.g. "VG+/NM" means the box outer is VG+ grade).

Product type filtering:
    We only match:
      - Miniatures Box Set   — standard GW retail boxes
      - Miniatures Pack      — smaller blister/clampack formats
      - Miniature Sets       — alternate label for box sets

    We exclude:
      - Miniatures Loose     — individual loose minis (not box sets)
      - Action Figure        — Todd McFarlane-style figures
      - Magazine             — Imperium/Mortal Realms issues
      - Foam / Cases / Bags  — accessories

Usage:
    python manage.py run_scrapers noble-knight-games

Notes:
  - Products without a match are marked not_available=True so the site shows
    "Not Available at Noble Knight" instead of a stale price.
  - Noble Knight frequently stocks multiple editions (e.g. "Intercessors 2017
    Edition" and "Intercessors 2020 Edition"). The scraper picks the cheapest
    eligible match so users see the best available deal.
  - Existing CurrentPrice URLs (from manual XLSX imports) are NOT overwritten
    when manual_url_override=True on that row. Prices are still updated.
  - The Zoovu API is non-authenticated but requires Origin / Referer headers
    matching nobleknight.com to avoid 403 responses.
"""

import logging
import re
import time
import urllib.parse
from decimal import Decimal, InvalidOperation

import requests
from django.utils import timezone

from prices.models import CurrentPrice
from products.models import Product, Retailer
from scrapers.models import ScrapeJob

logger = logging.getLogger(__name__)

# ── Zoovu API constants ────────────────────────────────────────────────────────

ZOOVU_SEARCH_URL = (
    'https://api.search.zoovu.com/search'
    '?projectId=43167'
    '&query={query}'
    '&limit=50'
)

NK_BASE_URL = 'https://www.nobleknight.com'

# ── Match thresholds ───────────────────────────────────────────────────────────

# Minimum F1-like word-overlap score to accept a name match.
# 0.65 is slightly lower than the MM scraper (0.75) because NK product names
# often include edition years ("2020 Edition") that reduce overlap.
ACCEPT_THRESHOLD = 0.65

# ── Condition filtering ────────────────────────────────────────────────────────

# Conditions we treat as "new enough" for price comparison.
# NK condition codes:  SW = Shrink Wrapped, NM = Near Mint, MINT = Mint.
# Any condition string that starts with "SW" is factory-sealed (new).
_CONDITION_STARTS_NEW = ('sw',)
_CONDITION_EXACT_NEW  = ('nm', 'mint', 'new')

# ── Product type filtering ─────────────────────────────────────────────────────

# Product types we accept as comparable to GW retail boxes.
_ACCEPTED_TYPES = frozenset({
    'miniatures box set',
    'miniatures pack',
    'miniature sets',
    'miniatures set',
})

# ── Name normalisation ─────────────────────────────────────────────────────────

# Edition year patterns to strip from NK titles so they don't lower scores.
_EDITION_RE = re.compile(
    r'\s*\(?(?:19|20)\d{2}\s+[Ee]dition\)?\s*'
    r'|\s*\((?:19|20)\d{2}\)\s*',
    re.IGNORECASE,
)

# Words to ignore when scoring name similarity.
_SKIP_WORDS = frozenset({
    'warhammer', '40000', '40k', 'the', 'and', 'of', 'at', 'in', 'a',
    'edition', 'new', 'box', 'set', 'miniatures', 'miniature', 'games',
    'workshop', 'gw', 'citadel',
    # Generic unit words that appear across many kits and would inflate scores
    'squad', 'team', 'warriors', 'warrior', 'guard',
})

# Faction/system prefixes stripped from both sides before scoring.
_FACTION_PREFIXES = [
    'warhammer 40,000', 'warhammer 40k', 'warhammer age of sigmar',
    'age of sigmar', 'horus heresy', 'kill team', 'warcry', 'necromunda',
    'space marines', 'space marine', 'chaos space marines', 'dark angels',
    'blood angels', 'space wolves', 'grey knights', 'deathwatch',
    'adepta sororitas', 'adeptus custodes', 'adeptus mechanicus',
    'astra militarum', 'imperial guard', 'imperial knights',
    'chaos knights', 'death guard', 'thousand sons', 'world eaters',
    "t'au empire", 'tau empire', "t'au", 'tau',
    'tyranids', 'tyranid', 'genestealer cults', 'necrons', 'necron',
    'orks', 'ork', 'drukhari', 'aeldari', 'craftworlds',
    'ossiarch bonereapers', 'nighthaunt', 'stormcast eternals',
    'leagues of votann', 'leagues',
]


class NoblekKnightScraper:
    """
    Scraper for Noble Knight Games (nobleknight.com).

    Uses the Noble Knight Zoovu search API to find matching in-stock new-
    condition products for each tracked GW miniature box set.
    """

    retailer_slug = 'noble-knight-games'

    def __init__(self):
        """Initialise requests session with browser-like headers."""
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': (
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                'AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/124.0.0.0 Safari/537.36'
            ),
            'Accept': 'application/json, text/html, */*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            # Required by the Zoovu API to avoid 403 responses
            'Origin': 'https://www.nobleknight.com',
            'Referer': 'https://www.nobleknight.com/',
        })
        # 1.5-second delay between requests — NK is a small retailer
        self.delay = 1.5

    # -------------------------------------------------------------------------
    # Public entry point
    # -------------------------------------------------------------------------

    def run(self):
        """Execute a full scrape job and return the ScrapeJob record."""
        try:
            retailer = Retailer.objects.get(slug=self.retailer_slug)
        except Retailer.DoesNotExist:
            logger.error('Retailer "%s" not found in DB.', self.retailer_slug)
            raise

        job = ScrapeJob.objects.create(
            retailer=retailer,
            status='running',
            started_at=timezone.now(),
        )
        errors = []
        products = Product.objects.filter(is_active=True).exclude(gw_sku='')

        for product in products:
            job.products_found += 1
            try:
                result = self._find_product(product.name)

                if result is None:
                    self._save_not_available(product, retailer)
                    logger.info('[nk] [n/a]     %s — no matching in-stock new item', product.name)
                else:
                    price, url = result
                    cp, created = CurrentPrice.objects.get_or_create(
                        product=product,
                        retailer=retailer,
                        defaults={
                            'price': price,
                            'url': url,
                            'in_stock': True,
                            'not_available': False,
                        },
                    )
                    if not created:
                        if cp.manual_url_override:
                            # URL is manually curated — only update the price
                            cp.price = price
                            cp.in_stock = True
                            cp.not_available = False
                            cp.save(update_fields=['price', 'in_stock', 'not_available'])
                        else:
                            cp.price = price
                            cp.url = url
                            cp.in_stock = True
                            cp.not_available = False
                            cp.save(update_fields=['price', 'url', 'in_stock', 'not_available'])

                    logger.info('[nk] [updated] %s — $%.2f', product.name, price)

                job.prices_updated += 1

            except Exception as exc:
                msg = f'{product.name}: {exc}'
                errors.append(msg)
                logger.exception('[nk] Error scraping %s', product.name)

            time.sleep(self.delay)

        job.status = 'success'
        job.errors = '\n'.join(errors)
        job.finished_at = timezone.now()
        job.save()
        return job

    # -------------------------------------------------------------------------
    # Product finder
    # -------------------------------------------------------------------------

    def _find_product(self, name):
        """
        Search the NK Zoovu API and return the cheapest new-condition match.

        Args:
            name: Our product name (e.g. "Space Marine Intercessors").

        Returns:
            (Decimal price, str url) or None if no acceptable match found.
        """
        candidates = self._search(name)
        if not candidates:
            return None

        best_score = 0.0
        best_price = None
        best_url = None

        for c in candidates:
            score = self._score_name(name, c['name'])
            logger.debug(
                '[nk] Candidate "%s" | score=%.2f | $%s',
                c['name'][:60], score, c['price'],
            )
            if score < ACCEPT_THRESHOLD:
                continue

            # Among equally-scored candidates, prefer the cheapest price.
            # If this candidate scores strictly higher than our best, reset.
            if score > best_score + 0.01:
                best_score = score
                best_price = c['price']
                best_url = c['url']
            elif score >= best_score - 0.01 and best_price is not None:
                if c['price'] < best_price:
                    best_price = c['price']
                    best_url = c['url']
                    best_score = score
            elif best_price is None:
                best_score = score
                best_price = c['price']
                best_url = c['url']

        if best_price is None:
            logger.debug('[nk] No match for "%s" (best=%.2f < %.2f)', name, best_score, ACCEPT_THRESHOLD)
            return None

        logger.debug('[nk] MATCH "%s" score=%.2f | $%.2f | %s', name, best_score, best_price, best_url)
        return best_price, best_url

    # -------------------------------------------------------------------------
    # Zoovu API
    # -------------------------------------------------------------------------

    def _search(self, name):
        """
        Call the Zoovu search API and return filtered, normalised candidates.

        Returns a list of dicts: {'name': str, 'price': Decimal, 'url': str}.
        Only includes in-stock, new/near-mint, box-set type results.
        """
        query = urllib.parse.quote(self._clean_name(name))
        url = ZOOVU_SEARCH_URL.format(query=query)
        try:
            response = self.session.get(url, timeout=15)
        except Exception as exc:
            logger.warning('[nk] Search request failed for "%s": %s', name, exc)
            return []

        if response.status_code != 200:
            logger.debug('[nk] Zoovu API returned HTTP %d for "%s"', response.status_code, name)
            return []

        try:
            data = response.json()
        except ValueError:
            logger.warning('[nk] Non-JSON response for "%s"', name)
            return []

        products_group = next(
            (g for g in data.get('searchResults', []) if g.get('type') == 'products'),
            None,
        )
        if not products_group:
            return []

        results = []
        for result_group in products_group.get('results', []):
            for item in result_group:
                candidate = self._parse_item(item)
                if candidate is not None:
                    results.append(candidate)

        return results

    def _parse_item(self, item):
        """
        Parse a single Zoovu result item into a candidate dict.

        Returns dict or None if the item fails condition/type/availability filters.
        """
        dps = {dp['conceptIdName']: dp['value'] for dp in item.get('dataPoints', [])}

        # Availability filter
        if dps.get('AVAILABLE', '').lower() != 'in stock':
            return None

        # Product type filter
        ptype = dps.get('PRODUCT TYPE', '').lower()
        if ptype not in _ACCEPTED_TYPES:
            return None

        # Condition filter
        condition = dps.get('CONDITION', '')
        if not self._is_new_condition(condition):
            return None

        # Price filter
        price_str = dps.get('SELLING PRICE')
        if not price_str:
            return None
        try:
            price = Decimal(str(price_str).strip())
            if not (1 <= price <= 2000):
                return None
        except InvalidOperation:
            return None

        # Publisher filter — only GW products
        publisher = dps.get('PUBLISHER', '')
        if publisher and 'games workshop' not in publisher.lower():
            return None

        link = item.get('link', '')
        if not link or '/P/' not in link:
            return None

        full_url = NK_BASE_URL + link

        return {
            'name': item.get('name', ''),
            'price': price,
            'url': full_url,
            'condition': condition,
        }

    # -------------------------------------------------------------------------
    # Condition check
    # -------------------------------------------------------------------------

    @staticmethod
    def _is_new_condition(condition):
        """
        Return True if the NK condition string represents a new/near-mint item.

        Accepted:
          SW (...)    — any Shrink Wrapped condition (factory sealed)
          MINT/New    — explicitly new
          NM          — Near Mint (open box but essentially new)

        Rejected:
          VG, VG+, EX, Fair, Used (including dual-code like "VG+/NM")
        """
        c = condition.lower().strip()
        if not c:
            return False
        # Shrink Wrapped always = new, regardless of inner condition code
        if c.startswith('sw'):
            return True
        # Exact single-condition codes
        if c in _CONDITION_EXACT_NEW:
            return True
        # "mint/new" compound
        if 'mint' in c and 'new' in c:
            return True
        return False

    # -------------------------------------------------------------------------
    # Name scoring
    # -------------------------------------------------------------------------

    @classmethod
    def _score_name(cls, our_name, candidate_title):
        """
        Score name similarity using an F1-like bidirectional word overlap.

        F1 = 2 * |matched| / (|our_words| + |their_words|)

        Edition years and faction prefixes are stripped from both sides
        before scoring so "Devastator Squad (2020 Edition)" correctly matches
        "Space Marine Devastators".

        A faction-conflict penalty (-0.6) is applied when our product belongs
        to faction A but the NK candidate explicitly names a different faction B.
        This prevents "Blood Angels Death Company" matching "Dark Angels Death
        Company" — the penalty drops the score below ACCEPT_THRESHOLD.

        Returns float in [0.0, 1.0] (may go negative with penalty, clamped to 0).
        """
        # Faction-conflict check before stripping
        our_faction   = cls._detect_faction(our_name)
        their_faction = cls._detect_faction(candidate_title)
        faction_penalty = 0.0
        if (
            our_faction is not None
            and their_faction is not None
            and our_faction != their_faction
        ):
            faction_penalty = 0.6

        our   = cls._normalise(our_name)
        their = cls._normalise(candidate_title)

        if not our or not their:
            return 0.0

        # Exact containment (short names)
        if their in our or our in their:
            return max(0.0, 1.0 - faction_penalty)

        our_words   = cls._words(our)
        their_words = cls._words(their)

        if not our_words:
            return 0.0

        matched = sum(
            1 for w in our_words
            if w in their_words or w + 's' in their_words or (w.endswith('s') and w[:-1] in their_words)
        )

        score = 2 * matched / (len(our_words) + len(their_words))
        return max(0.0, score - faction_penalty)

    @staticmethod
    def _detect_faction(name):
        """
        Return the first faction prefix found in name (lowercase), or None.

        Checked longest-first so 'chaos space marines' is returned before
        'space marines' for a name that contains 'chaos space marines'.
        """
        lower = name.lower()
        for prefix in sorted(_FACTION_PREFIXES, key=len, reverse=True):
            if prefix in lower:
                return prefix
        return None

    @staticmethod
    def _normalise(name):
        """
        Strip edition years, faction prefixes and punctuation from a name.

        Returns a lowercased clean string.
        """
        text = name.lower().strip()
        # Strip edition year patterns: "(2020 Edition)", "2020 Edition", etc.
        text = _EDITION_RE.sub(' ', text)
        # Strip faction/game prefixes (longest first)
        for prefix in sorted(_FACTION_PREFIXES, key=len, reverse=True):
            text = text.replace(prefix, ' ')
        # Normalise punctuation
        text = re.sub(r'[^\w\s]', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    @staticmethod
    def _words(text):
        """Return a set of meaningful words (length > 2, not in skip list)."""
        return {
            w for w in text.split()
            if len(w) > 2 and w not in _SKIP_WORDS
        }

    @staticmethod
    def _clean_name(name):
        """
        Produce a clean search query from a product name.

        Intentionally keeps faction words in the query so the NK API can rank
        faction-correct results higher (e.g. searching "Blood Angels Death
        Company" ranks Blood Angels results above Dark Angels ones).
        Only removes parenthetical qualifiers and normalises punctuation.
        """
        text = name.strip()
        # Remove parenthetical qualifiers like "(Combat Patrol)"
        text = re.sub(r'\s*\([^)]+\)', '', text)
        # Remove punctuation, normalise whitespace
        text = re.sub(r'[^\w\s]', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    # -------------------------------------------------------------------------
    # Helpers
    # -------------------------------------------------------------------------

    @staticmethod
    def _save_not_available(product, retailer):
        """Upsert a not_available=True CurrentPrice row for this product."""
        cp = CurrentPrice.objects.filter(product=product, retailer=retailer).first()
        if cp and cp.manual_url_override:
            # Respect manually-set URL; only update availability flags
            cp.in_stock = False
            cp.not_available = True
            cp.save(update_fields=['in_stock', 'not_available'])
        else:
            CurrentPrice.objects.update_or_create(
                product=product,
                retailer=retailer,
                defaults={
                    'price': None,
                    'url': '',
                    'in_stock': False,
                    'not_available': True,
                },
            )
