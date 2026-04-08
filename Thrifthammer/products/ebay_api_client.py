"""
eBay Browse API client for ThriftHammer.

Replaces the decommissioned Finding API (shut down 2024) with eBay's
current Browse API v1. Uses OAuth 2.0 Client Credentials flow.

API Documentation:
  https://developer.ebay.com/api-docs/buy/browse/static/overview.html

Authentication:
  Browse API requires OAuth 2.0 (Client Credentials grant).
  Set these in Railway environment variables (or local .env):
    EBAY_APP_ID_PRODUCTION   — Client ID from developer.ebay.com/my/keys
    EBAY_CERT_ID_PRODUCTION  — Client Secret (Cert ID) from developer.ebay.com/my/keys
    EBAY_APP_ID_SANDBOX      — Sandbox Client ID (for testing)
    EBAY_CERT_ID_SANDBOX     — Sandbox Client Secret

Token caching:
  OAuth tokens are valid for 2 hours. This client caches the token
  in memory and auto-refreshes it before it expires.

Rate limits (Browse API):
  5,000 calls/day for standard developer accounts.
  Resets at midnight Pacific Time.

Marketplace:
  Configured for EBAY_US to return USD prices.
  Change MARKETPLACE_ID for other regions (e.g. EBAY_GB for GBP).
"""

import base64
import logging
import math
import re
import time
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from urllib.parse import unquote_plus

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

# ── Browse API endpoints ──────────────────────────────────────────────────────
BROWSE_API_ENDPOINT   = 'https://api.ebay.com/buy/browse/v1/item_summary/search'
BROWSE_API_SANDBOX    = 'https://api.sandbox.ebay.com/buy/browse/v1/item_summary/search'

OAUTH_ENDPOINT        = 'https://api.ebay.com/identity/v1/oauth2/token'
OAUTH_ENDPOINT_SANDBOX = 'https://api.sandbox.ebay.com/identity/v1/oauth2/token'

# US marketplace — USD prices
MARKETPLACE_ID        = 'EBAY_US'

# OAuth scope for public Browse API access (no user login required)
OAUTH_SCOPE           = 'https://api.ebay.com/oauth/api_scope'

# Refresh token 5 minutes before it expires
TOKEN_REFRESH_BUFFER  = 300

# Daily call safety limit
DAILY_CALL_SAFETY_LIMIT = 4500
DAILY_CALL_LIMIT        = 5000


class EbayAPIError(Exception):
    """Raised when eBay API returns an error response."""
    pass


class EbayBrowseAPI:
    """
    Client for eBay Browse API v1.

    Searches eBay US for fixed-price 'New' listings, sorted by lowest
    price, and returns the cheapest validated listing for each product.

    Replaces the legacy Finding API which was decommissioned in 2024.

    Authentication:
      Uses OAuth 2.0 Client Credentials grant. Tokens are cached and
      auto-refreshed so you don't need to manage them manually.

    Usage:
        api = EbayBrowseAPI(use_sandbox=False)
        result = api.find_best_match_for_product(product)
        if result:
            print(result['price'], result['url'])
    """

    def __init__(self, app_id=None, cert_id=None, use_sandbox=False):
        """
        Initialise the eBay Browse API client.

        Args:
            app_id:      Client ID. Defaults to settings.EBAY_APP_ID_PRODUCTION
                         or settings.EBAY_APP_ID_SANDBOX.
            cert_id:     Client Secret. Defaults to settings.EBAY_CERT_ID_PRODUCTION
                         or settings.EBAY_CERT_ID_SANDBOX.
            use_sandbox: If True, use eBay sandbox environment for testing.
        """
        self.use_sandbox = use_sandbox
        self.session = requests.Session()
        self.api_calls_made = 0

        # ── Resolve credentials ───────────────────────────────────────────────
        if use_sandbox:
            self.app_id  = app_id  or getattr(settings, 'EBAY_APP_ID_SANDBOX', '')
            self.cert_id = cert_id or getattr(settings, 'EBAY_CERT_ID_SANDBOX', '')
        else:
            self.app_id  = app_id  or getattr(settings, 'EBAY_APP_ID_PRODUCTION', '')
            self.cert_id = cert_id or getattr(settings, 'EBAY_CERT_ID_PRODUCTION', '')

        missing = []
        if not self.app_id:
            key = 'EBAY_APP_ID_SANDBOX' if use_sandbox else 'EBAY_APP_ID_PRODUCTION'
            missing.append(key)
        if not self.cert_id:
            key = 'EBAY_CERT_ID_SANDBOX' if use_sandbox else 'EBAY_CERT_ID_PRODUCTION'
            missing.append(key)

        if missing:
            raise ValueError(
                f'eBay Browse API not configured. Missing: {", ".join(missing)}. '
                'Set these in Railway environment variables.'
            )

        self.browse_endpoint = BROWSE_API_SANDBOX if use_sandbox else BROWSE_API_ENDPOINT
        self.oauth_endpoint  = OAUTH_ENDPOINT_SANDBOX if use_sandbox else OAUTH_ENDPOINT

        # Token cache
        self._access_token = None
        self._token_expires_at = 0  # Unix timestamp

        env_label = 'SANDBOX' if use_sandbox else 'PRODUCTION'
        logger.info('eBay Browse API client initialised (%s)', env_label)

    # -------------------------------------------------------------------------
    # Public methods
    # -------------------------------------------------------------------------

    def find_best_match_for_product(self, product):
        """
        Find the cheapest valid eBay US listing for a given product.

        Search strategy:
          1. Build optimised search query from product name
          2. Search Browse API with Fixed Price + New condition filters,
             requesting EXTENDED fieldgroup to include shortDescription
          3. Sort by price ascending (cheapest first)
          4. Validate each result against the product name (title keywords,
             bits blocklist, price floor, shipping cap)
          5. Cross-check shortDescription for bits keywords and product
             keyword presence as a secondary accuracy filter
          6. Return first valid match

        Args:
            product: Product model instance with .name and .gw_sku fields.

        Returns:
            dict with keys:
                price       (Decimal) — item price in USD
                shipping    (Decimal) — shipping cost (0 if free)
                total_cost  (Decimal) — price + shipping
                title       (str)     — eBay listing title
                url         (str)     — direct link to eBay listing
                item_id     (str)     — eBay item ID
            or None if no valid listing found.
        """
        # Use ebay_search_name override if set, otherwise fall back to product name.
        # This lets Deathwatch / faction-aliased products search eBay using the
        # name their listings actually appear under (e.g. Space Marine kit names)
        # while keeping their display name unchanged on the site.
        search_name = getattr(product, 'ebay_search_name', '') or product.name

        # Product-specific negative keywords prevent similarly-named products from
        # appearing in eBay results (e.g. "-plastic" stops Plastic Glue listings
        # from showing up when searching for Super Glue).
        raw_negatives = getattr(product, 'ebay_negative_keywords', '') or ''
        extra_negatives = raw_negatives.split() if raw_negatives else None

        query = self._build_search_query(search_name, extra_negatives)
        items = self.search_items(query, max_results=10)

        if not items:
            logger.debug('[ebay] No results for "%s"', query)
            return None

        valid_items = [item for item in items if self._is_valid_result(item, product)]

        if not valid_items:
            logger.debug('[ebay] No valid match for "%s"', product.name)
            return None

        # Validate all results, then pick the best one.
        # Strategy: trust Best Match's #1 result for product identity, but
        # switch to a cheaper listing if one is meaningfully cheaper (>10%).
        #
        # Why not always return cheapest?
        #   Products with short names (e.g. "Ork Warboss") share keywords with
        #   related variants ("Ork Warboss in Mega Armour").  Both pass keyword
        #   validation, so "return cheapest" can pick the wrong variant if it
        #   happens to be listed a few dollars cheaper.  Best Match is a better
        #   signal for product identity when prices are close.
        #
        # Why not always return Best Match #1?
        #   Best Match doesn't guarantee lowest price — a correct listing at
        #   position 3 may be 20–30% cheaper than the position-1 listing.
        #
        # Threshold: if cheapest valid is >10% below Best Match winner, take it.
        # Small differences (< 10%) aren't worth the product-identity risk.

        first_valid = valid_items[0]
        cheapest    = min(valid_items, key=lambda x: x['total_cost'])

        cheaper_threshold = Decimal('0.90')  # must be ≥10% cheaper to beat Best Match
        if cheapest['total_cost'] <= first_valid['total_cost'] * cheaper_threshold:
            best = cheapest
            logger.debug(
                '[ebay] Cheaper alternative chosen over Best Match: '
                '"%.60s" $%.2f vs "%.60s" $%.2f',
                cheapest['title'], cheapest['total_cost'],
                first_valid['title'], first_valid['total_cost'],
            )
        else:
            best = first_valid

        logger.debug(
            '[ebay] Match: "%s" — $%.2f + $%.2f shipping '
            '(%d valid from top-%d Best Match results)',
            best['title'][:60], best['price'], best['shipping'],
            len(valid_items), len(items),
        )
        return best

    def search_items(self, keywords, max_results=10):
        """
        Search eBay US for items matching keywords using the Browse API.

        Filters applied:
          - buyingOptions: FIXED_PRICE (no auctions)
          - conditions: NEW
          - itemLocationCountry: US
        Marketplace: EBAY_US (USD prices)
        Sort: Best Match (eBay default relevance — full sealed kits from
              reputable sellers rank above cheap bits/spare parts)

        Args:
            keywords:    Search query string.
            max_results: Number of results to request (max 200).

        Returns:
            List of parsed item dicts, or empty list on no results.

        Raises:
            EbayAPIError: If eBay returns an API-level error.
            RuntimeError: On network errors or daily limit approaching.
        """
        if self.api_calls_made >= DAILY_CALL_SAFETY_LIMIT:
            raise RuntimeError(
                f'Approaching eBay daily call limit '
                f'({self.api_calls_made}/{DAILY_CALL_LIMIT}). Stopping.'
            )

        token = self._get_access_token()

        params = {
            'q':           keywords,
            'filter':      (
                'buyingOptions:{FIXED_PRICE},'
                'conditions:{NEW},'
                'itemLocationCountry:US'
            ),
            # No 'sort' parameter → eBay "Best Match" (default relevance ranking).
            # Best Match surfaces well-matched listings from reputable sellers first,
            # which are almost always full sealed retail kits.  Sorting by price
            # ascending put cheap bits/spare parts at the top of every search,
            # burying genuine full-kit listings beyond our scan window.
            'limit':       str(min(max_results, 200)),
            # EXTENDED fieldgroup adds shortDescription to each result (no extra API call).
            # We use it to catch bits/parts listings whose titles look legitimate but
            # whose descriptions reveal they are individual components.
            'fieldgroups': 'EXTENDED',
        }

        headers = {
            'Authorization':            f'Bearer {token}',
            'X-EBAY-C-MARKETPLACE-ID':  MARKETPLACE_ID,
            'Content-Type':             'application/json',
        }

        try:
            response = self.session.get(
                self.browse_endpoint,
                params=params,
                headers=headers,
                timeout=10,
            )
        except requests.Timeout:
            raise RuntimeError(f'eBay API timeout for query: "{keywords}"')
        except requests.RequestException as exc:
            raise RuntimeError(f'eBay API network error: {exc}') from exc
        finally:
            self.api_calls_made += 1

        # Parse JSON regardless of HTTP status — eBay puts error details in body
        try:
            data = response.json()
        except ValueError as exc:
            raise RuntimeError(
                f'eBay API HTTP {response.status_code} — invalid JSON body'
            ) from exc

        # Handle errors (Browse API returns them as HTTP 4xx/5xx with JSON body)
        if not response.ok:
            error_msg = self._extract_browse_error(data)
            raise EbayAPIError(
                f'eBay API error for "{keywords}": {error_msg} '
                f'(HTTP {response.status_code})'
            )

        items_raw = data.get('itemSummaries', [])
        return [
            parsed for parsed in (self._parse_item(item) for item in items_raw)
            if parsed is not None
        ]

    # -------------------------------------------------------------------------
    # Token management
    # -------------------------------------------------------------------------

    def _get_access_token(self):
        """
        Return a valid OAuth 2.0 access token, fetching a new one if needed.

        Tokens are cached in memory and refreshed 5 minutes before expiry.

        Returns:
            Access token string.

        Raises:
            EbayAPIError: If token fetch fails.
        """
        now = time.time()
        if self._access_token and now < self._token_expires_at - TOKEN_REFRESH_BUFFER:
            return self._access_token

        logger.debug('[ebay] Fetching new OAuth access token')

        # Basic auth: base64(client_id:client_secret)
        credentials = base64.b64encode(
            f'{self.app_id}:{self.cert_id}'.encode('utf-8')
        ).decode('utf-8')

        try:
            response = self.session.post(
                self.oauth_endpoint,
                headers={
                    'Content-Type':  'application/x-www-form-urlencoded',
                    'Authorization': f'Basic {credentials}',
                },
                data={
                    'grant_type': 'client_credentials',
                    'scope':      OAUTH_SCOPE,
                },
                timeout=10,
            )
        except requests.RequestException as exc:
            raise EbayAPIError(f'eBay OAuth token request failed: {exc}') from exc

        try:
            token_data = response.json()
        except ValueError as exc:
            raise EbayAPIError(
                f'eBay OAuth returned invalid JSON (HTTP {response.status_code})'
            ) from exc

        if not response.ok:
            error = token_data.get('error_description', token_data.get('error', 'Unknown'))
            raise EbayAPIError(f'eBay OAuth error: {error} (HTTP {response.status_code})')

        self._access_token = token_data.get('access_token', '')
        expires_in = token_data.get('expires_in', 7200)
        self._token_expires_at = time.time() + expires_in

        logger.info('[ebay] OAuth token obtained, expires in %ds', expires_in)
        return self._access_token

    # -------------------------------------------------------------------------
    # Private methods
    # -------------------------------------------------------------------------

    @staticmethod
    def _build_search_query(product_name, extra_negatives=None):
        """
        Build an optimised eBay search query from a product name.

        Rules:
          - Remove special characters that confuse eBay search
          - Add 'Warhammer' if not already present (narrows to hobby)
          - Citadel/hobby supply products keep their own brand name
          - Truncate the positive portion to 50 chars for best results
          - Append eBay negative keywords (-bits -bitz -sprue) so eBay's
            own engine filters out individual component listings before
            they reach our validator. This is critical: Warhammer searches
            are dominated by cheap bits/spare parts that would otherwise
            fill the entire result window, pushing genuine full kit listings
            beyond our scan limit.
          - Append product-specific negative keywords (extra_negatives) to
            exclude similar-but-wrong products at the eBay search level.
            e.g. "-plastic" for Super Glue prevents Plastic Glue listings.

        Args:
            product_name:    Raw product name from DB or ebay_search_name override.
            extra_negatives: Optional list of words to exclude via eBay -word syntax.
                             These are appended after the standard -bits -bitz -sprue
                             exclusions. Sourced from Product.ebay_negative_keywords.

        Returns:
            Clean search query string with negative keyword suffixes.
        """
        query = re.sub(r"[^\w\s']", ' ', product_name)
        query = re.sub(r'\s+', ' ', query).strip()

        citadel_terms = [
            'citadel', 'contrast paint', 'base paint', 'layer paint',
            'shade', 'technical paint', 'dry paint', 'texture paint',
            'spray', 'brush', 'painting handle', 'plastic glue',
            'super glue', 'hobby knife', 'mouldline', 'water pot',
        ]
        query_lower = query.lower()
        is_citadel = any(term in query_lower for term in citadel_terms)

        # NOTE: "Warhammer" is intentionally NOT appended to the query.
        #
        # eBay's Browse API matches query words against listing titles.
        # Many legitimate sellers title their listings with just the product
        # name — e.g. "Space Marine Whirlwind" — without including "Warhammer".
        # Adding "Warhammer" to the query turns it into a required title keyword,
        # causing eBay to silently exclude any listing whose title doesn't contain
        # that word, even if it is a genuine, new, fixed-price, US-based copy of
        # exactly the product we want.
        #
        # Product-identity accuracy is handled entirely by _is_valid_result:
        #   - 65% keyword match ensures the product name is in the title
        #   - bits/parts blocklist filters non-kit listings
        #   - price floor filters implausibly cheap single-model listings
        # These checks are sufficient without requiring "Warhammer" in the query.

        # Truncate the positive terms only — negative keywords are appended after
        # so they are never cut off by the length limit.
        if len(query) > 50:
            query = query[:50].rsplit(' ', 1)[0]

        # Negative keyword exclusions (eBay -word syntax).
        # These words overwhelmingly indicate individual component listings
        # ("bits", "bitz", "sprue") rather than full sealed retail kits.
        # Excluding them at the eBay query level stops bits listings from
        # filling the result window before the genuine full-kit listings appear.
        # Citadel hobby supplies don't suffer from this problem, so skip for them.
        # "-decor" is included globally because "decor" / "wall decor" / "room decor"
        # listings appear across all faction searches (GW-branded art prints, display
        # pieces, room accessories) and are never sealed miniature kit retail products.
        # "-cards -datacards" are included globally because GW publishes small cardboard
        # reference card sets (e.g. "Space Marine Datacards") that share exact product
        # names with miniature kits and are priced much cheaper — excluding them at the
        # eBay query level prevents card sets from winning the best-price match over
        # the actual miniature box.
        if not is_citadel:
            query = f'{query.strip()} -bits -bitz -sprue -decor -cards -datacards'

        # Product-specific negative keywords: exclude similarly-named products
        # that our keyword validator cannot distinguish (e.g. Plastic Glue vs
        # Super Glue both contain "citadel" + "glue" and pass the 65% threshold).
        # Sourced from Product.ebay_negative_keywords — space-separated words.
        if extra_negatives:
            for word in extra_negatives:
                word = word.strip()
                if word:
                    query = f'{query} -{word}'

        return query.strip()

    @staticmethod
    def _parse_item(item):
        """
        Parse a raw Browse API item dict into a clean result dict.

        Browse API price fields use {'value': '34.99', 'currency': 'USD'}
        format, unlike the old Finding API's {'__value__': '34.99'} format.

        Only USD listings are returned. Non-USD items (GBP, EUR, etc.) are
        skipped because:
          - Their numeric prices appear artificially low when treated as USD
            (e.g., £30 looks like $30, but is actually ~$38).
          - Their shipping costs are often missing or also in local currency,
            making total_cost unreliable for price comparison.

        Args:
            item: Raw item dict from Browse API itemSummaries array.

        Returns:
            Parsed dict or None if essential fields are missing or non-USD.
        """
        try:
            # Some eBay sellers submit their listing title in URL-encoded form
            # (e.g. "Land+Raider+Crusader+%2F+Redeemer").  Decode it so the
            # title is a clean string before any validation checks run.
            # unquote_plus handles both %XX percent-encoding and + → space.
            title   = unquote_plus(item.get('title', ''))
            url     = item.get('itemWebUrl', '')
            item_id = item.get('itemId', '')

            if not url:
                return None

            # Price — only process USD listings
            price_data     = item.get('price', {})
            price_currency = price_data.get('currency', 'USD')
            if price_currency != 'USD':
                logger.debug(
                    '[ebay] Skipping non-USD listing (%s): "%s"',
                    price_currency, title[:60],
                )
                return None
            price_value = price_data.get('value', '0')
            price = Decimal(str(price_value))

            # Shipping — use first shipping option if available
            shipping = Decimal('0')
            shipping_options = item.get('shippingOptions', [])
            if shipping_options:
                ship_cost     = shipping_options[0].get('shippingCost', {})
                ship_currency = ship_cost.get('currency', 'USD')
                ship_value    = ship_cost.get('value', '0')
                # Only use shipping cost if it is also in USD
                if ship_currency == 'USD':
                    try:
                        shipping = Decimal(str(ship_value))
                    except InvalidOperation:
                        shipping = Decimal('0')

            total_cost = price + shipping

            # shortDescription is populated when fieldgroups=EXTENDED is set.
            # It is a plain-text excerpt from the seller's full description.
            short_description = item.get('shortDescription', '')

            return {
                'title':             title,
                'url':               url,
                'item_id':           item_id,
                'price':             price,
                'shipping':          shipping,
                'total_cost':        total_cost,
                'short_description': short_description,
            }

        except (KeyError, InvalidOperation, TypeError):
            return None

    # Keywords that indicate a listing is a spare part/bit, not a full kit.
    # eBay is flooded with individual components — we must exclude them.
    #
    # NOTE: This set is used for TITLE checks only.  Titles are short and
    # structured so anatomical words ('arm', 'body', 'back') almost always
    # signal individual component listings.  See _DESC_BITS_KEYWORDS below
    # for the more conservative set used on shortDescription text, where
    # those same words appear innocently in vehicle kit descriptions
    # ("sponson arms", "vehicle body", "missiles on the back").
    _BITS_KEYWORDS = {
        # Seller classification terms
        'bit', 'bits', 'bitz', 'sprue', 'sprues', 'upgrade',
        # Body parts — in a listing *title*, these signal components, not full kits
        'head', 'heads', 'arm', 'arms', 'torso', 'leg', 'legs',
        'body', 'bodies', 'hand', 'hands', 'chest', 'back',
        # Individual equipment pieces — singular and plural forms
        # ("Helmets Choppas Sluggas" in a title = weapon-option bits listing)
        'bolter', 'pistol', 'backpack', 'pauldron', 'shoulder',
        'misericordia', 'helmet', 'helmets', 'helm', 'banner', 'tabard', 'cloak',
        # Mount/transport components sold individually — e.g. "Disc of Tzeentch"
        # (the flying disc model that Sorcerers ride, extracted from the Exalted
        # Sorcerers kit and sold as a single component).  No GW sealed retail
        # box is named simply "disc" — it is always a component-level term here.
        # Note: word-tokenised match only — "Disciples" does NOT match 'disc'.
        'disc', 'discs',
        # Conversion/non-genuine terms
        'conversion', 'kitbash', 'kitbashed', 'custom', 'resin',
        'alternative', 'proxy', 'sculpt', 'sculpted',
        # Condition flags that indicate not a complete new retail kit
        'damaged', 'broken', 'incomplete', 'partial', 'loose', 'oob',
        # Single model from a multi-model box
        'single', 'singles', 'individual',
        # "Only" — signals a partial kit in eBay titles
        # e.g. "Land Raider Hull ONLY, NO Sponsons or Accessories"
        # Full sealed retail kit listings never use "only" to describe their contents.
        'only',
        # "New on Sprue" — pulled from a box, not a sealed retail kit
        'nos',
        # Blister pack — old GW single-model/small-group packaging (cardboard +
        # plastic bubble). Never used for full multi-model retail box kits.
        # e.g. "Plague Marine Champion Death Guard NIB Blister" — one model, not
        # the full 7-model Death Guard Plague Marines boxed kit.
        'blister',
        # Old/discontinued GW product indicators — never appear in current
        # plastic boxed kit titles:
        #   'metal'    — old GW metal models (pre-plastic era, ~pre-2010)
        #   'oop'      — "Out of Print/Production"; current in-production kits
        #                are never OOP. Prevents ancient discontinued sculpts
        #                from matching current product searches.
        #   'finecast' — GW's discontinued resin casting material (~2011–2022)
        #   'epic'     — Epic 40K / Epic Armageddon: a different GW game system
        #                using 6mm scale models (~1/4 the size of regular 40K).
        #                e.g. "Epic 40K Space Marine Whirlwind NIB Metal OOP"
        'metal', 'oop', 'finecast', 'epic',
        # "Squat" — the old (pre-10th edition) fan/community term for Leagues of
        # Votann.  eBay sellers use it alongside the new name to boost search
        # visibility, which is a strong signal of a non-retail-kit listing (bits,
        # old sculpts, individual extracted models).  No current GW sealed retail
        # box for Leagues of Votann uses "Squat" in its official product title.
        'squat', 'squats',
        # "Commemorative" — GW event-exclusive and limited-release special models
        # (e.g. "Kahl Yoht Grendok Commemorative").  These are NOT standard retail
        # kits — they are special event/store purchases, often multi-part resin
        # sets priced far above the standard retail equivalent.
        'commemorative',
        # "Exclusive" — GW wargame-exclusive, store-exclusive, or event-exclusive
        # limited-release items (e.g. "Ork Elektro Rokker Wargame Exclusive").
        # These are NOT standard retail kits available at multiple retailers.
        # Standard sealed retail box titles never use "exclusive" to describe
        # the product itself.
        'exclusive',
        # Apparel / merchandise — T-shirts, graphic tees, and vintage clothing
        # share faction/unit names with miniature kits (e.g. "Space Marines Tee",
        # "Warhammer Vintage Graphic Shirt", "Kayvaan Shrike T-Shirt").
        # 'shirt' catches T-shirt/shirt listings where the hyphen-split prevents
        # 'tee' from matching (eBay titles sometimes use "T-Shirt" or just "Shirt").
        'graphic', 'tee', 'vintage', 'shirt', 'shirts',
        # "Service" — catches "Paint Service", "Painting Service", "Commission
        # Service" listings where a seller is offering a painting service rather
        # than selling a sealed retail kit.  Pairs with 'commission'/'painted'.
        'service',
        # Costume / cosplay items — faction-themed Halloween costumes, cosplay
        # armour, etc. appear in searches but are not miniature kits.
        # 'roma' — Roma Costume brand produces Warhammer-themed dress-up items.
        'costume', 'roma',
        # Terrain / scenery — landscape and wargaming terrain pieces that share
        # kit names (e.g. "Ork Trukk Shed Terrain").  These are not sealed retail
        # miniature kits and appear especially in Ork searches.
        'shed', 'kamp',
        # Popular culture / media crossover terms — appear in faction searches
        # because sellers tag unrelated products with Warhammer keywords:
        #   'halo'     — Halo video game franchise merchandise / action figures
        #   'joker'    — DC Comics character; appears in Ork / Chaos searches
        #   'hardcore'  — music genre merch that appears in Ork searches
        #   '1997'     — year tag on old metal OOP models / vintage merchandise
        'halo', 'joker', 'hardcore', '1997',
        # McFarlane Toys — GW-licensed maker of large pre-painted articulated
        # action figures (e.g. McFarlane Space Marine, McFarlane Ork).  Same
        # unit names as miniature kits but a completely different product category.
        # 'mcfarlane' is the unambiguous brand marker.
        'mcfarlane',
        # Third-party / non-GW manufacturer terms — not genuine GW kits.
        # These companies produce Warhammer-compatible alternative models that
        # appear in faction searches but are not GW products.
        #   'kromlech'  — Polish third-party resin/plastic bits & alternative minis
        #   'artel'     — Artel W Miniatures; produces alternative sculpts for
        #                 named characters (e.g. alternative Howling Banshees exarch)
        #   'alternative', 'proxy', 'sculpt', 'sculpted', 'conversion', 'custom',
        #   'resin', 'kitbash', 'kitbashed' — already covered above
        'kromlech', 'artel',
        # Non-GW toy/collectible terms — not genuine Warhammer miniature kits
        'minifigure', 'minifigures', 'minifigs', 'minifig', 'figurine', 'figurines',
        # JOYTOY: GW-licensed third-party maker of pre-painted, pre-assembled
        # articulated action figures. Same faction/unit names as GW kits but
        # a completely different product category — not plastic model kits.
        'joytoy',
        # Collectible pins, badges, enamel pins, display dioramas —
        # GW-branded merchandise that appears in miniature kit searches but
        # is a completely different product category.
        # e.g. "Necron Diorama Pin-Metal-OOP-Lychguard-Badge-Lord-Koyo"
        'pin', 'pins', 'badge', 'badges', 'enamel', 'diorama', 'dioramas',
        # Vehicle component terms — in a listing *title*, these signal that only
        # part of a kit is being sold, not the complete retail box.
        #   'turret'  — e.g. "Space Marine Predator Tank TURRET Twin Lascannon"
        #               GW sells complete tank kits; individual turrets are swaps.
        #   'sponson' — side-mounted weapon pod; sold separately as upgrades.
        #   'hull'    — e.g. "Land Raider Hull, Chasis, Treads" (no sponsons/turret).
        'turret', 'sponson', 'sponsons', 'hull',
        # Books / novels — Games Workshop publishes Black Library fiction under
        # the same brand name (e.g. "Ork Warboss" novel).  "library" is the
        # reliable signal: it appears in "Black Library" book titles but never
        # in genuine miniature kit titles.  "Librarian" (SM psyker unit) is a
        # different word and is not affected.
        'novel', 'paperback', 'hardback', 'hardcover', 'library',
        # Painted/assembled miniatures — not sealed retail kits.
        #   'painted'     — "Pro Painted", "hand painted", "painted army builder";
        #                   sealed kit listings never describe their contents as painted.
        #   'assembled'   — likewise; a kit that ships assembled was not bought sealed.
        #   'commission'  — commission painting service listings ("Ravager - Commission");
        #                   a seller offering to paint to order, not selling a sealed kit.
        'painted', 'assembled', 'commission',
        # Adeptus Titanicus — GW's 8mm-scale Titan/Knight game. Same unit names
        # (e.g. "Cerastus Knight Lancer") but ~1/6th the size and price of
        # the standard 40K/30K kits. "titanicus" is the unambiguous marker.
        'titanicus',
        # Forge World — GW's premium resin subsidiary. Produces alternative
        # sculpts for many standard units (e.g. Carnifex, Dreadnought) that
        # are out of scope for ThriftHammer price comparisons (different product,
        # usually more expensive, not available in standard retail).
        # "forgeworld" catches the common one-word seller spelling; the two-word
        # official form "Forge World" is caught by the _MISSING_PHRASES phrase
        # check below (tokenising would split it into 'forge'/'world' — neither
        # blockable alone without excessive false positives).
        'forgeworld',
        # Decor / decorative merchandise — GW-branded art prints, wall decor,
        # display pieces, room accessories, and similar non-miniature products.
        # These appear across all faction searches but are never sealed retail kits.
        # Globally blocked (also excluded at eBay query level via -decor above).
        'decor', 'decors',
        # Reference card sets — GW publishes small cardboard datacards/command card
        # sets (e.g. "Space Marine Datacards", "Chaos Space Marines Cards") that
        # share exact faction/unit names with miniature kits but cost only ~$15–25.
        # Without this exclusion, card sets win the best-price match over the actual
        # miniature box because they are cheaper and pass all keyword checks.
        # Globally blocked (also excluded at eBay query level via -cards -datacards).
        'card', 'cards', 'datacard', 'datacards',
    }

    # Conservative bits keyword set used for shortDescription checks only.
    #
    # shortDescription is a plain-text excerpt from the seller's full listing
    # description. Unlike titles, descriptions are verbose prose — words like
    # 'arm', 'back', 'body', 'head' appear constantly in legitimate vehicle kit
    # listings ("sponson arms", "back of the hull", "main vehicle body").
    # Using the full _BITS_KEYWORDS set here produces false positives that
    # incorrectly reject genuine sealed kits (Whirlwind, Predator Destructor,
    # Land Raider Crusader have all been observed as victims of this).
    #
    # This set contains only terms that are unambiguously bad in any context:
    # - 'bits'/'bitz'/'sprue' — seller classification terms never used in prose
    #   descriptions of full kits
    # - 'nos' / 'blister' — product packaging terms; always means not a full kit
    # - 'joytoy' / product-category terms (book, pin, diorama) — wrong category
    # - 'incomplete' / 'damaged' / 'broken' — condition terms clearly bad in any
    #   context
    _DESC_BITS_KEYWORDS = {
        # Unambiguous bits/sprue seller terminology
        'bit', 'bits', 'bitz',
        'sprue', 'sprues',
        'nos',      # "new on sprue" — extracted sprue, not a sealed retail kit
        'blister',  # blister pack single
        # Non-GW manufacturer
        'joytoy',
        # Conversion/proxy — not a genuine GW kit
        'kitbash', 'kitbashed',
        'proxy',
        # Non-miniature product types
        'minifigure', 'minifigures', 'minifigs', 'minifig', 'figurine', 'figurines',
        'finecast',
        'novel', 'paperback', 'hardback', 'hardcover',
        'diorama', 'dioramas',
        'pin', 'pins', 'badge', 'badges', 'enamel',
        # Clearly incomplete or damaged
        'damaged', 'broken', 'incomplete', 'partial', 'oob',
        # Adeptus Titanicus — different GW game (8mm scale Knights/Titans).
        # Same unit names as 40K but a completely different product.
        # Caught in descriptions when sellers list contents: "1x Adeptus
        # Titanicus Cerastus Knight Transfer Sheet" or "AT Castellan / Lancer".
        'titanicus',
        # Painted miniatures — not sealed kits.
        # Note: 'assembled' is intentionally excluded here (unlike the title
        # filter) because kit descriptions often say "assembles to...", "when
        # assembled", etc. in legitimate sealed-kit listings. Titles are short
        # and structured; "assembled" in a title unambiguously means built.
        'painted',
    }

    @staticmethod
    def _is_valid_result(result, product):
        """
        Validate that a Browse API listing is a genuine complete kit match.

        Validation checks:
          1. Title keyword match: ≥ 65% of meaningful product name keywords
             must appear in the listing title (min 2). Falls back to a
             unit-suffix check (last 2 keywords both present) to handle
             sellers who omit the faction name, e.g., "Custodian Wardens"
             instead of "Adeptus Custodes Custodian Wardens".
          2. Title bits filter: title words must not overlap the bits/parts
             blocklist — filters individual components sold separately.
          3. Loose-minis count filter: rejects titles matching "NUMBER +
             miniatures/minis/figures" (e.g., "10 Miniatures") — sealed GW
             retail boxes never use this phrasing; only loose/NOS sprue
             sellers describe contents this way.
          4. Dual-kit slash filter: rejects titles containing " / " between
             unit names (e.g., "Vertus Praetor / Shield Captain") — this is
             the standard eBay format for individual dual-build sprues; full
             retail boxes never use this format.
          5. Price range: total cost $8–$1,000 ($8 min, or 50% of MSRP).
             50% of GBP MSRP ≈ 40% of USD street price, reliably catching
             single-model sprues extracted from multi-model boxes.
          6. Shipping cap: max $30.
          7. Description bits filter: shortDescription (from EXTENDED
             fieldgroup) must not contain bits/parts keywords — catches
             cases where the title looks fine but the description reveals
             individual components.
          8. URL must link to eBay.

        Args:
            result:  Parsed item dict from _parse_item.
            product: Product model instance with .name and .msrp fields.

        Returns:
            True if the listing is a valid complete-kit match, False otherwise.
        """
        if not result or not result.get('url'):
            return False

        title_lower = result['title'].lower()

        # When ebay_search_name is set, validate against that name — it is what
        # was actually sent to eBay, so it is what should appear in the title.
        # Falls back to product.name for products without an override.
        effective_name     = getattr(product, 'ebay_search_name', '') or product.name
        product_name_lower = effective_name.lower()

        # ── Keyword match ─────────────────────────────────────────────────────
        # Require 65% of meaningful keywords to match (min 2, or however many
        # keywords exist if fewer than 2).
        #
        # Threshold is len >= 3 (include 3-char words like "Ork", "Tau").
        # Previously len > 3 excluded these, leaving Ork products with only
        # 1 keyword ("nobz") and min_matches=1 — too loose, causing the
        # wrong product to match (e.g. "Beast Boss" matching "Ork Warboss"
        # because "warboss" alone was the only required keyword).
        # With len >= 3, "Ork Warboss" → ["ork", "warboss"] → needs both.
        # Only 1-2 char words (articles, prepositions) are now excluded.
        #
        # Examples:
        #   "Ork Nobz"                          → 2 keywords → need 2
        #   "Ork Boyz"                          → 2 keywords → need 2
        #   "Ork Warboss"                       → 2 keywords → need 2
        #   "Trajann Valoris"                   → 2 keywords → need 2
        #   "Custodian Guard"                   → 2 keywords → need 2
        #   "Adeptus Custodes Shield-Captain"   → 4 keywords → need 3
        #   "Adeptus Custodes Custodian Wardens"→ 4 keywords → need 3
        keywords    = [w for w in product_name_lower.split() if len(w) >= 3]
        n_keywords  = len(keywords)
        min_matches = max(min(2, n_keywords), math.ceil(n_keywords * 0.65))
        matches     = sum(1 for kw in keywords if kw in title_lower)

        # Unit-suffix fallback: many eBay sellers omit the faction name
        # ("Adeptus Custodes", "Space Marines") from their listing title and
        # only name the unit — e.g., "Custodian Wardens" instead of
        # "Adeptus Custodes Custodian Wardens".  In that case the full 65%
        # threshold would reject a genuinely correct listing.
        # Fix: if the last 2 unit-specific keywords both appear in the title,
        # accept the listing even if the faction prefix is absent.
        unit_keywords   = keywords[-2:] if len(keywords) >= 2 else keywords
        unit_suffix_hit = len(unit_keywords) >= 2 and all(
            kw in title_lower for kw in unit_keywords
        )

        if matches < min_matches and not unit_suffix_hit:
            logger.debug(
                '[ebay] Rejected (keyword mismatch): "%s" vs "%s" '
                '(%d/%d matches, unit suffix match: %s)',
                result['title'][:60], product.name, matches, min_matches, unit_suffix_hit,
            )
            return False

        # ── Product-specific negative keywords — title check ─────────────────
        # eBay's -keyword search operator does not always filter hyphenated
        # compounds: "-shirt" fails to block "T-shirts" because eBay treats the
        # hyphenated token as a different word.  We apply the per-product negative
        # keywords locally against the title using word-boundary matching so that
        # e.g. blocking "special" does not accidentally reject listings whose
        # titles contain "specialists" or "especially".
        _raw_neg = getattr(product, 'ebay_negative_keywords', '') or ''
        if _raw_neg:
            _result_item_id = result.get('item_id', '')
            for _neg_kw in _raw_neg.lower().split():
                # Pure-digit tokens are treated as blocked eBay item IDs rather
                # than title keywords (item IDs never appear in listing titles).
                if _neg_kw.isdigit():
                    if _result_item_id and _neg_kw == _result_item_id:
                        logger.debug(
                            '[ebay] Rejected (blocked item ID %s): "%s"',
                            _result_item_id, result['title'][:60],
                        )
                        return False
                elif re.search(r'\b' + re.escape(_neg_kw) + r'\b', title_lower):
                    logger.debug(
                        '[ebay] Rejected (negative keyword "%s" in title): "%s"',
                        _neg_kw, result['title'][:60],
                    )
                    return False

        # ── Bits/parts filter ─────────────────────────────────────────────────
        # Split title into words and check against the bits keyword set.
        title_words = set(re.sub(r"[^\w\s]", ' ', title_lower).split())
        bits_matches = title_words & EbayBrowseAPI._BITS_KEYWORDS
        if bits_matches:
            logger.debug(
                '[ebay] Rejected (bits/parts): "%s" matched keywords: %s',
                result['title'][:60], bits_matches,
            )
            return False

        # ── Standalone count / partial-set detection ──────────────────────────
        # Sealed GW retail boxes use the official product name in their title
        # and never include a model count.  Count digits appear in two kinds
        # of wrong listings:
        #
        # (a) Partial-set listings — sellers splitting a multi-model box:
        #     "Crusader Squad 5 Primaris Space Marines"  (5 of 10 models)
        #     "5 Ork Boyz Warhammer 40K"
        #     Fix: reject any title containing a standalone digit 1–9.
        #     Safe exclusions:
        #       • "40K" / "40,000" — "40" is ≥ 2 digits, not caught.
        #       • Product codes "XV8", "XV25" — digit is inside a word token
        #         (no word boundary on both sides), not caught.
        #       • "10th Edition" — "10th" is one word token, not caught.
        #
        # (b) NOS (New-on-Sprue) listings with a generic descriptor:
        #     "T'au Fire Warriors - 10 Miniatures"
        #     "15 Figures New"
        #     Fix: reject NUMBER + miniatures/minis/figures (covers 10+).
        if re.search(r'\b[1-9]\b', title_lower):
            logger.debug(
                '[ebay] Rejected (standalone count digit): "%s"',
                result['title'][:60],
            )
            return False

        if re.search(r'\b\d+\s+(?:miniatures?|minis?|figures?)\b', title_lower):
            logger.debug(
                '[ebay] Rejected (count + generic descriptor): "%s"',
                result['title'][:60],
            )
            return False

        # ── Dual-kit single-model detection ───────────────────────────────────
        # Games Workshop produces many character models as dual-build sprues —
        # one sprue that assembles as either Unit A or Unit B.  eBay sellers of
        # individual sprues consistently title these listings as:
        #   "Vertus Praetor / Shield Captain"  ($10–20)
        #   "Captain / Lieutenant"             ($10–20)
        #
        # However, GW also sells some full multi-part vehicle boxes as dual-build
        # kits with " / " in the official product name, e.g.:
        #   "Land Raider Crusader / Redeemer"  ($95–120)
        #
        # Distinguishing factor: price.  Single dual-build sprues are priced
        # at $8–20; full dual-build boxes are priced at $50–120+.
        # Threshold: 75% of MSRP (stored in GBP, used directly as a floor).
        # Any " / " listing below this floor is a cheap sprue, not a full box.
        if ' / ' in result['title']:
            slash_floor = Decimal('30.00')  # fallback if MSRP is missing
            if hasattr(product, 'msrp') and product.msrp and product.msrp > 0:
                slash_floor = product.msrp * Decimal('0.75')
            slash_cost = result.get('total_cost', Decimal('0'))
            if slash_cost < slash_floor:
                logger.debug(
                    '[ebay] Rejected (dual-kit single sprue, "/" + price $%.2f < floor $%.2f): "%s"',
                    slash_cost, slash_floor, result['title'][:60],
                )
                return False

        # ── Bundle detection ──────────────────────────────────────────────────
        # " & " between product names indicates a bundle of two separate
        # products (e.g. "Predator Annihilator/Destructor & Razorback").
        # GW sealed retail kits are single products — their official names
        # never include " & ".  No products in the ThriftHammer DB use "&".
        if ' & ' in result['title']:
            logger.debug(
                '[ebay] Rejected (bundle listing, "&" in title): "%s"',
                result['title'][:60],
            )
            return False

        # ── Individual model variant detection (#A / #B / #C pattern) ─────────
        # eBay sellers who extract individual models from a multi-model kit
        # commonly suffix the listing title with a hash + single letter/digit
        # to denote which specific model variant they are selling:
        #   "Inner Circle Companions #C Dark Angels Veterans"
        #   "Custodian Guard #A"
        # No GW sealed retail kit title ever contains "#" — official product
        # names use letter suffixes only in product codes (e.g. "XV8"), and
        # those appear inside a word token without a preceding space.
        # A space-hash-word pattern is therefore an unambiguous extraction signal.
        if re.search(r'\s#\w', result['title']):
            logger.debug(
                '[ebay] Rejected (individual model variant, "#X" in title): "%s"',
                result['title'][:60],
            )
            return False

        # ── Blocked title phrases ─────────────────────────────────────────────
        # Multi-word phrases that cannot be caught by the single-word _BITS_KEYWORDS
        # word-set intersection.  Covers two categories:
        #
        # Incomplete kit markers — seller explicitly states what is missing:
        # "no box"       — product removed from retail packaging
        # "no weapons"   — weapons/arms stripped out (common on Knights, Titans)
        #                  e.g. "Cerastus Lancer Knight Titan NO WEAPONS or SHEET"
        # "no elbows"    — sub-assembly missing ("Knight Questoris NO WEAPONS OR ELBOWS")
        # "no arms"      — arm weapons removed from the frame
        # "no transfers" — transfer sheet missing from box
        # "no sword"     — specific weapon stripped, e.g. "Eldrad Ulthran NO Sword or Staff"
        # "no staff"     — ditto
        #
        # Wrong product category:
        # "forge world"  — Forge World (GW resin subsidiary) official two-word form.
        #                  Resin FW sculpts share unit names with standard plastic kits
        #                  but are a different product not tracked by ThriftHammer.
        #                  The one-word variant "forgeworld" is caught by _BITS_KEYWORDS.
        _MISSING_PHRASES = (
            'no box', 'no weapons', 'no weapon',
            'no elbows', 'no elbow', 'no arms',
            'no transfers', 'no transfer sheet',
            'no sword', 'no staff',
            'forge world',
            # Bundle/starter sets — "paints included" indicates a GW starter
            # bundle (kit + Contrast paints) which is a different, usually more
            # expensive product from the standalone plastic kit.  We track the
            # standalone kit MSRP, so paint bundles are always the wrong product.
            'paints included',
            # Action figures — McFarlane Toys and similar brands produce large
            # pre-painted articulated action figures under the GW licence.
            # "action figure" unambiguously identifies these (the single word
            # 'mcfarlane' is also in _BITS_KEYWORDS for title-level blocking).
            'action figure',
        )
        allow_no_box = getattr(product, 'ebay_allow_no_box', False)
        for phrase in _MISSING_PHRASES:
            # Per-product override: skip the "no box" check for products that
            # are commonly sold as loose sprues without retail packaging.
            if phrase == 'no box' and allow_no_box:
                continue
            if phrase in title_lower:
                logger.debug(
                    '[ebay] Rejected (blocked phrase "%s" in title): "%s"',
                    phrase, result['title'][:60],
                )
                return False

        # ── Price range ───────────────────────────────────────────────────────
        total_cost = result.get('total_cost', Decimal('0'))
        # Absolute minimum $8 — even the cheapest genuine kit (small paint pot,
        # glue) starts around that price.
        # MSRP floor: 50% of MSRP (stored in GBP) gives a useful USD lower bound
        # because GBP MSRP × 0.50 ≈ 40% of the actual USD street price, which
        # reliably filters out single-model sprues pulled from multi-model boxes
        # (e.g., a £50 MSRP squadron kit → floor £25; a single sprue at $24.95
        # fails, the full box at $55 passes).
        min_price = Decimal('8.00')
        if hasattr(product, 'msrp') and product.msrp and product.msrp > 0:
            msrp_floor = product.msrp * Decimal('0.50')
            min_price = max(min_price, msrp_floor)

        if total_cost < min_price or total_cost > Decimal('1000.00'):
            logger.debug(
                '[ebay] Rejected (price out of range): $%.2f for "%s" (min $%.2f)',
                total_cost, product.name, min_price,
            )
            return False

        # ── Shipping ──────────────────────────────────────────────────────────
        shipping = result.get('shipping', Decimal('0'))
        if shipping > Decimal('30.00'):
            logger.debug(
                '[ebay] Rejected (shipping too high): $%.2f for "%s"',
                shipping, product.name,
            )
            return False

        # ── Description bits check (uses shortDescription from EXTENDED fieldgroup) ─
        # shortDescription is a plain-text excerpt from the seller's full description.
        # We check it for bits/parts keywords to catch listings whose titles look
        # legitimate but whose descriptions reveal individual components — e.g.,
        # "selling spare torsos from this kit" or "5 heads from the box".
        #
        # NOTE: We intentionally do NOT require product keywords to appear in the
        # description. Legitimate sellers commonly write generic descriptions such as
        # "Brand new sealed. Ships fast from USA." that contain no unit-specific words.
        # The title keyword check is the right place to verify product identity.
        short_desc = result.get('short_description', '').lower()
        if short_desc:
            desc_words     = set(re.sub(r'[^\w\s]', ' ', short_desc).split())
            desc_bits_hits = desc_words & EbayBrowseAPI._DESC_BITS_KEYWORDS
            if desc_bits_hits:
                logger.debug(
                    '[ebay] Rejected (bits keyword in description): "%s" — %s',
                    result['title'][:60], desc_bits_hits,
                )
                return False

            # Detect individual models extracted from multi-model kits or sets.
            # Sellers who pull one model from a box often write descriptions like:
            #   "1 Shield Captain from the Custodes Wardens model kit."
            #   "Canoness and base from Adepta Sororitas Army Box Set / Combat Patrol."
            #   "Spare bits from the Blood Angels Assault Squad model kit."
            # Any "from X [model kit / box set / army box / army set /
            # starter set / combat patrol]" phrase is an unambiguous extraction
            # signal — GW sealed retail listings never describe their product this
            # way.  We do NOT require "the/a/an" after "from" because sellers
            # also write e.g. "from Black Templar Primaris Grimaldus & Retinue
            # model kit."  False positives are prevented by requiring the specific
            # terminal phrase (model kit / box set / etc.) rather than the article.
            _EXTRACTION_RE = re.compile(
                r'\bfrom\b.{0,80}'
                r'\b(?:model kit|box set|army box|army set|starter set|combat patrol)\b',
                re.IGNORECASE,
            )
            if _EXTRACTION_RE.search(short_desc):
                logger.debug(
                    '[ebay] Rejected (single model extracted from set, '
                    '"from X [set/kit]" in description): "%s"',
                    result['title'][:60],
                )
                return False

            # ── 3D print / aftermarket resin detection ────────────────────────
            # Aftermarket 3D-printed miniatures and non-GW resin casts share
            # exact unit names with official GW kits but are not the sealed
            # retail plastic boxes we track.  Sellers of these items consistently
            # use phrases like "resin miniature", "3d printed", "resin print",
            # "fdm printed", "fan sculpt", or "proxy" in their descriptions.
            # Note: "resin" alone is NOT blocked at the title level to avoid
            # rejecting Forge World (official GW resin subsidiary) listings when
            # they appear in eBay search results.  The description phrases below
            # are specific enough to identify aftermarket prints without false
            # positives from genuine Forge World items.
            _PRINT_PHRASES = (
                'resin miniature',
                'resin mini',
                'resin print',
                '3d printed',
                '3d print',
                'fdm printed',
                'fan sculpt',
                'fan-sculpt',
                'proxy miniature',
                'proxy mini',
                'not gw',
                'not official',
            )
            for _phrase in _PRINT_PHRASES:
                if _phrase in short_desc:
                    logger.debug(
                        '[ebay] Rejected (3D print/aftermarket resin, '
                        '"%s" in description): "%s"',
                        _phrase, result['title'][:60],
                    )
                    return False

            # Reject reseller/content-creator storefronts that sell non-standard
            # listings (pre-assembled, display, or hobby-service models).
            # Frontline Gaming (frontlinegaming.org) uses a boilerplate description
            # containing "tabletop gaming blog" — their listings carry internal
            # codes (HAA-xx, GZZ-xx, HAF-xx) and are not sealed retail boxes.
            if re.search(r'\btabletop gaming blog\b', short_desc, re.IGNORECASE):
                logger.debug(
                    '[ebay] Rejected (reseller storefront, '
                    '"tabletop gaming blog" in description): "%s"',
                    result['title'][:60],
                )
                return False

            # Apply product-specific negative keywords to the description.
            # eBay's -keyword search operator filters listing TITLES only —
            # descriptions are not filtered server-side.  A listing whose title
            # passes all checks can still reveal the wrong product via its
            # description (e.g. the Grimaldus Retinue set: title has no
            # "cenobyte" but the description says "assemble one Chaplain
            # Grimaldus and his three Cenobyte Servitors").
            raw_negatives = getattr(product, 'ebay_negative_keywords', '') or ''
            if raw_negatives:
                for neg_kw in raw_negatives.lower().split():
                    if re.search(r'\b' + re.escape(neg_kw) + r'\b', short_desc):
                        logger.debug(
                            '[ebay] Rejected (negative keyword "%s" in description): "%s"',
                            neg_kw, result['title'][:60],
                        )
                        return False

            # ── Description-mirrors-title bot detection ────────────────────
            # Bot/spam storefronts generate listings whose descriptions simply
            # repeat the listing title followed by generic shipping boilerplate,
            # e.g.:
            #   title:       "Astra Militarum Cadian Shock Troops Warhammer 40k"
            #   description: "warhammer 40k astra militarum Cadian Shock Troops .
            #                 Condition is New. Shipped with USPS Ground Advantage."
            #
            # Legitimate sellers write genuine descriptions about condition,
            # contents, or provenance — they don't just echo the title.
            #
            # Detection: if ≥ 70% of meaningful title words (len ≥ 3) appear
            # in the first 150 characters of the description, the description
            # is mirroring the title — a reliable bot signal.  The 150-char
            # window is large enough to catch all title words even when the
            # description leads with them, and short enough to avoid false
            # positives from genuine sellers who happen to mention the product
            # name once near the start of a longer description.
            title_kws = [
                w for w in re.sub(r'[^\w\s]', ' ', title_lower).split()
                if len(w) >= 3
            ]
            if len(title_kws) >= 3:
                desc_prefix = short_desc[:150]
                mirror_matches = sum(1 for w in title_kws if w in desc_prefix)
                mirror_ratio = mirror_matches / len(title_kws)
                if mirror_ratio >= 0.70:
                    logger.debug(
                        '[ebay] Rejected (description mirrors title, %.0f%% word overlap): "%s"',
                        mirror_ratio * 100, result['title'][:60],
                    )
                    return False

        # ── URL must link to eBay ─────────────────────────────────────────────
        if 'ebay.' not in result['url']:
            return False

        return True

    @staticmethod
    def _get_rejection_reasons(result, product):
        """
        Run each validation check individually and return a list of failure reasons.

        Used by the --debug flag in update_ebay_prices to show exactly why each
        eBay candidate was rejected without hiding the detail behind a single bool.

        Args:
            result:  Parsed item dict from _parse_item.
            product: Product model instance with .name and .msrp fields.

        Returns:
            List of human-readable rejection reason strings.
            Empty list means the item would pass validation (is valid).
        """
        reasons = []

        if not result or not result.get('url'):
            reasons.append('missing url')
            return reasons

        title_lower    = result['title'].lower()
        effective_name = getattr(product, 'ebay_search_name', '') or product.name
        product_name_lower = effective_name.lower()

        # Keyword match
        keywords    = [w for w in product_name_lower.split() if len(w) >= 3]
        n_keywords  = len(keywords)
        min_matches = max(min(2, n_keywords), math.ceil(n_keywords * 0.65))
        matches     = sum(1 for kw in keywords if kw in title_lower)
        unit_keywords   = keywords[-2:] if len(keywords) >= 2 else keywords
        unit_suffix_hit = len(unit_keywords) >= 2 and all(
            kw in title_lower for kw in unit_keywords
        )
        if matches < min_matches and not unit_suffix_hit:
            reasons.append(
                f'keyword mismatch ({matches}/{min_matches} needed, '
                f'unit suffix: {unit_suffix_hit}) — keywords: {keywords}'
            )

        # Product-specific negative keywords — title check (word-boundary match)
        # Pure-digit tokens are treated as blocked eBay item IDs, not title words.
        _raw_neg = getattr(product, 'ebay_negative_keywords', '') or ''
        if _raw_neg:
            _result_item_id = result.get('item_id', '')
            for _neg_kw in _raw_neg.lower().split():
                if _neg_kw.isdigit():
                    if _result_item_id and _neg_kw == _result_item_id:
                        reasons.append(f'blocked item ID {_result_item_id}')
                        break
                elif re.search(r'\b' + re.escape(_neg_kw) + r'\b', title_lower):
                    reasons.append(f'negative keyword "{_neg_kw}" in title')
                    break

        # Title bits filter
        title_words  = set(re.sub(r"[^\w\s]", ' ', title_lower).split())
        bits_matches = title_words & EbayBrowseAPI._BITS_KEYWORDS
        if bits_matches:
            reasons.append(f'title bits keywords: {bits_matches}')

        # Standalone count digit
        if re.search(r'\b[1-9]\b', title_lower):
            reasons.append('standalone count digit in title')

        # Count + generic descriptor
        if re.search(r'\b\d+\s+(?:miniatures?|minis?|figures?)\b', title_lower):
            reasons.append('count+descriptor in title')

        # Slash — price-aware: only reject if cost is below 75% of MSRP
        if ' / ' in result['title']:
            slash_floor = Decimal('30.00')
            if hasattr(product, 'msrp') and product.msrp and product.msrp > 0:
                slash_floor = product.msrp * Decimal('0.75')
            slash_cost = result.get('total_cost', Decimal('0'))
            if slash_cost < slash_floor:
                reasons.append(
                    f'" / " dual-kit sprue in title, price ${slash_cost:.2f} '
                    f'< floor ${slash_floor:.2f}'
                )

        # Bundle
        if ' & ' in result['title']:
            reasons.append('" & " (bundle) in title')

        # Individual model variant (#A / #B / #C pattern)
        if re.search(r'\s#\w', result['title']):
            reasons.append('individual model variant ("#X" suffix in title)')

        # Blocked title phrases (incomplete kit markers + wrong product category)
        _MISSING_PHRASES = (
            'no box', 'no weapons', 'no weapon',
            'no elbows', 'no elbow', 'no arms',
            'no transfers', 'no transfer sheet',
            'no sword', 'no staff',
            'forge world',
            'paints included',
        )
        allow_no_box = getattr(product, 'ebay_allow_no_box', False)
        for phrase in _MISSING_PHRASES:
            if phrase == 'no box' and allow_no_box:
                continue
            if phrase in title_lower:
                reasons.append(f'blocked phrase ("{phrase}" in title)')
                break

        # Price
        total_cost = result.get('total_cost', Decimal('0'))
        min_price  = Decimal('8.00')
        if hasattr(product, 'msrp') and product.msrp and product.msrp > 0:
            msrp_floor = product.msrp * Decimal('0.50')
            min_price  = max(min_price, msrp_floor)
        if total_cost < min_price or total_cost > Decimal('1000.00'):
            reasons.append(
                f'price out of range: ${total_cost:.2f} '
                f'(min ${min_price:.2f}, max $1000.00)'
            )

        # Shipping
        shipping = result.get('shipping', Decimal('0'))
        if shipping > Decimal('30.00'):
            reasons.append(f'shipping too high: ${shipping:.2f}')

        # Description bits
        short_desc = result.get('short_description', '').lower()
        if short_desc:
            desc_words     = set(re.sub(r'[^\w\s]', ' ', short_desc).split())
            desc_bits_hits = desc_words & EbayBrowseAPI._DESC_BITS_KEYWORDS
            if desc_bits_hits:
                reasons.append(f'description bits keywords: {desc_bits_hits}')

            # Single model/component extracted from a multi-model kit or set
            _EXTRACTION_RE = re.compile(
                r'\bfrom\b.{0,80}'
                r'\b(?:model kit|box set|army box|army set|starter set|combat patrol)\b',
                re.IGNORECASE,
            )
            if _EXTRACTION_RE.search(short_desc):
                reasons.append(
                    'single model extracted from set '
                    '("from X [set/kit]" in description)'
                )

            if re.search(r'\btabletop gaming blog\b', short_desc, re.IGNORECASE):
                reasons.append('reseller storefront ("tabletop gaming blog" in description)')

            # Product-specific negative keywords applied to description (word-boundary)
            raw_negatives = getattr(product, 'ebay_negative_keywords', '') or ''
            if raw_negatives:
                for neg_kw in raw_negatives.lower().split():
                    if re.search(r'\b' + re.escape(neg_kw) + r'\b', short_desc):
                        reasons.append(
                            f'negative keyword "{neg_kw}" in description'
                        )
                        break

            # Description-mirrors-title bot detection
            title_kws = [
                w for w in re.sub(r'[^\w\s]', ' ', title_lower).split()
                if len(w) >= 3
            ]
            if len(title_kws) >= 3:
                desc_prefix = short_desc[:150]
                mirror_matches = sum(1 for w in title_kws if w in desc_prefix)
                mirror_ratio = mirror_matches / len(title_kws)
                if mirror_ratio >= 0.70:
                    reasons.append(
                        f'description mirrors title ({mirror_ratio:.0%} word overlap)'
                    )

        # URL
        if 'ebay.' not in result.get('url', ''):
            reasons.append('url not on ebay')

        return reasons

    @staticmethod
    def _extract_browse_error(data):
        """
        Extract a human-readable error message from a Browse API error response.

        Browse API error format:
          {"errors": [{"message": "...", "errorId": 123, ...}]}

        Args:
            data: Parsed JSON response body.

        Returns:
            Error message string.
        """
        try:
            errors = data.get('errors', [])
            if errors:
                return errors[0].get('message', 'Unknown eBay error')
            return data.get('message', 'Unknown eBay error')
        except (KeyError, IndexError, TypeError):
            return 'Unknown eBay error'
