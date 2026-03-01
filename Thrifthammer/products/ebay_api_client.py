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
  Configured for EBAY_GB (UK) to return GBP prices, matching the
  site's currency. Change MARKETPLACE_ID for other regions.
"""

import base64
import logging
import re
import time
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

# ── Browse API endpoints ──────────────────────────────────────────────────────
BROWSE_API_ENDPOINT   = 'https://api.ebay.com/buy/browse/v1/item_summary/search'
BROWSE_API_SANDBOX    = 'https://api.sandbox.ebay.com/buy/browse/v1/item_summary/search'

OAUTH_ENDPOINT        = 'https://api.ebay.com/identity/v1/oauth2/token'
OAUTH_ENDPOINT_SANDBOX = 'https://api.sandbox.ebay.com/identity/v1/oauth2/token'

# UK marketplace — GBP prices
MARKETPLACE_ID        = 'EBAY_GB'

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

    Searches eBay UK for fixed-price 'New' listings, sorted by lowest
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
        Find the cheapest valid eBay UK listing for a given product.

        Search strategy:
          1. Build optimised search query from product name
          2. Search Browse API with Fixed Price + New condition filters
          3. Sort by price ascending (cheapest first)
          4. Validate each result against the product name
          5. Return first valid match

        Args:
            product: Product model instance with .name and .gw_sku fields.

        Returns:
            dict with keys:
                price       (Decimal) — item price in GBP
                shipping    (Decimal) — shipping cost (0 if free)
                total_cost  (Decimal) — price + shipping
                title       (str)     — eBay listing title
                url         (str)     — direct link to eBay listing
                item_id     (str)     — eBay item ID
            or None if no valid listing found.
        """
        query = self._build_search_query(product.name)
        items = self.search_items(query, max_results=10)

        if not items:
            logger.debug('[ebay] No results for "%s"', query)
            return None

        for item in items:
            if self._is_valid_result(item, product):
                logger.debug(
                    '[ebay] Match: "%s" — £%.2f + £%.2f shipping',
                    item['title'][:60], item['price'], item['shipping'],
                )
                return item

        logger.debug('[ebay] No valid match for "%s"', product.name)
        return None

    def search_items(self, keywords, max_results=10):
        """
        Search eBay UK for items matching keywords using the Browse API.

        Filters applied:
          - buyingOptions: FIXED_PRICE (no auctions)
          - conditions: NEW
        Marketplace: EBAY_GB (UK, GBP prices)
        Sort: price ascending (cheapest first)

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
            'q':      keywords,
            'filter': 'buyingOptions:{FIXED_PRICE},conditions:{NEW}',
            'sort':   'price',
            'limit':  str(min(max_results, 200)),
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
    def _build_search_query(product_name):
        """
        Build an optimised eBay search query from a product name.

        Rules:
          - Remove special characters that confuse eBay search
          - Add 'Warhammer' if not already present (narrows to hobby)
          - Citadel/hobby supply products keep their own brand name
          - Truncate to 50 chars for best results

        Args:
            product_name: Raw product name from DB.

        Returns:
            Clean search query string.
        """
        query = re.sub(r"[^\w\s']", ' ', product_name)
        query = re.sub(r'\s+', ' ', query).strip()

        citadel_terms = [
            'citadel', 'contrast paint', 'base paint', 'layer paint',
            'shade', 'technical paint', 'dry paint', 'texture paint',
            'spray', 'brush', 'painting handle', 'plastic glue',
            'super glue', 'hobby knife', 'mouldline',
        ]
        query_lower = query.lower()
        is_citadel = any(term in query_lower for term in citadel_terms)

        if not is_citadel and 'warhammer' not in query_lower:
            query = f'{query} Warhammer'

        if len(query) > 50:
            query = query[:50].rsplit(' ', 1)[0]

        return query.strip()

    @staticmethod
    def _parse_item(item):
        """
        Parse a raw Browse API item dict into a clean result dict.

        Browse API price fields use {'value': '34.99', 'currency': 'GBP'}
        format, unlike the old Finding API's {'__value__': '34.99'} format.

        Args:
            item: Raw item dict from Browse API itemSummaries array.

        Returns:
            Parsed dict or None if essential fields are missing.
        """
        try:
            title   = item.get('title', '')
            url     = item.get('itemWebUrl', '')
            item_id = item.get('itemId', '')

            if not url:
                return None

            # Price
            price_data = item.get('price', {})
            price_value = price_data.get('value', '0')
            price = Decimal(str(price_value))

            # Shipping — use first shipping option if available
            shipping = Decimal('0')
            shipping_options = item.get('shippingOptions', [])
            if shipping_options:
                ship_cost = shipping_options[0].get('shippingCost', {})
                ship_value = ship_cost.get('value', '0')
                try:
                    shipping = Decimal(str(ship_value))
                except InvalidOperation:
                    shipping = Decimal('0')

            total_cost = price + shipping

            return {
                'title':      title,
                'url':        url,
                'item_id':    item_id,
                'price':      price,
                'shipping':   shipping,
                'total_cost': total_cost,
            }

        except (KeyError, InvalidOperation, TypeError):
            return None

    @staticmethod
    def _is_valid_result(result, product):
        """
        Validate that a Browse API listing is a genuine match for our product.

        Validation checks:
          1. Title contains at least 2 keywords from the product name
             (words longer than 3 chars to skip noise words)
          2. Total cost is in a sensible range (£1 — £1,000)
          3. Shipping is not suspiciously high (max £100)
          4. URL is present and links to eBay

        Args:
            result:  Parsed item dict from _parse_item.
            product: Product model instance.

        Returns:
            True if the listing is a valid match, False otherwise.
        """
        if not result or not result.get('url'):
            return False

        title_lower       = result['title'].lower()
        product_name_lower = product.name.lower()

        keywords = [w for w in product_name_lower.split() if len(w) > 3]
        matches  = sum(1 for kw in keywords if kw in title_lower)

        if matches < 2:
            logger.debug(
                '[ebay] Rejected (keyword mismatch): "%s" vs "%s" (%d matches)',
                result['title'][:60], product.name, matches,
            )
            return False

        total_cost = result.get('total_cost', Decimal('0'))
        if total_cost < Decimal('1.00') or total_cost > Decimal('1000.00'):
            logger.debug(
                '[ebay] Rejected (price out of range): £%.2f for "%s"',
                total_cost, product.name,
            )
            return False

        shipping = result.get('shipping', Decimal('0'))
        if shipping > Decimal('100.00'):
            logger.debug(
                '[ebay] Rejected (shipping too high): £%.2f for "%s"',
                shipping, product.name,
            )
            return False

        if 'ebay.' not in result['url']:
            return False

        return True

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
