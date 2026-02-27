"""
eBay Finding API v1.0.0 client for ThriftHammer.

Uses eBay's official Finding API to search for live product listings.
This is a price comparison use case, which is fully compliant with
eBay's developer program terms of service.

Compliance summary:
  - Uses official Finding API (NOT web scraping)
  - Respects 5,000 calls/day rate limit
  - Links back to eBay using viewItemURL from API response
  - Does not modify eBay pricing data
  - Does not claim affiliation with eBay
  - Properly attributes eBay as the price source

API Documentation:
  https://developer.ebay.com/DevZone/finding/Concepts/FindingAPIGuide.html

Authentication:
  Finding API uses App ID only — no OAuth required.
  Set EBAY_APP_ID_PRODUCTION in Railway environment variables.
"""

import logging
import re
from decimal import Decimal, InvalidOperation

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

# eBay Finding API endpoint
FINDING_API_ENDPOINT = (
    'https://svcs.ebay.com/services/search/FindingService/v1'
)
FINDING_API_SANDBOX_ENDPOINT = (
    'https://svcs.sandbox.ebay.com/services/search/FindingService/v1'
)

# Daily call limit per eBay developer program terms
DAILY_CALL_LIMIT = 5000

# Stop if we reach this threshold to leave buffer for other uses
DAILY_CALL_SAFETY_LIMIT = 4500


class EbayAPIError(Exception):
    """Raised when eBay API returns an error response."""
    pass


class EbayFindingAPI:
    """
    Client for eBay Finding API v1.0.0.

    Searches eBay for 'Buy It Now' listings in 'New' condition,
    sorted by lowest total price (price + shipping). Returns the
    cheapest validated listing for each product.

    Compliant with eBay developer program requirements:
      - Uses official API endpoint
      - Respects rate limits
      - Links to viewItemURL provided by API
      - Attributes eBay as price source

    Usage:
        api = EbayFindingAPI(use_sandbox=False)
        result = api.find_best_match_for_product(product)
        if result:
            print(result['price'], result['url'])
    """

    def __init__(self, app_id=None, use_sandbox=False):
        """
        Initialise the eBay Finding API client.

        Args:
            app_id: eBay App ID. Defaults to settings.EBAY_APP_ID_PRODUCTION
                    or settings.EBAY_APP_ID_SANDBOX depending on use_sandbox.
            use_sandbox: If True, use sandbox endpoint with sandbox App ID.
        """
        self.use_sandbox = use_sandbox
        self.session = requests.Session()
        self.api_calls_made = 0

        if app_id:
            self.app_id = app_id
        elif use_sandbox:
            self.app_id = getattr(settings, 'EBAY_APP_ID_SANDBOX', '')
        else:
            self.app_id = getattr(settings, 'EBAY_APP_ID_PRODUCTION', '')

        if not self.app_id:
            raise ValueError(
                'No eBay App ID configured. Set EBAY_APP_ID_PRODUCTION '
                'in Railway environment variables.'
            )

        self.endpoint = (
            FINDING_API_SANDBOX_ENDPOINT if use_sandbox
            else FINDING_API_ENDPOINT
        )

        env_label = 'SANDBOX' if use_sandbox else 'PRODUCTION'
        logger.info('eBay Finding API client initialised (%s)', env_label)

    # -------------------------------------------------------------------------
    # Public methods
    # -------------------------------------------------------------------------

    def find_best_match_for_product(self, product):
        """
        Find the cheapest valid eBay listing for a given product.

        Search strategy:
          1. Build optimised search query from product name
          2. Call findItemsAdvanced with Buy It Now + New filters
          3. Sort by PricePlusShippingLowest (cheapest total cost first)
          4. Validate each result against the product
          5. Return first valid match

        Args:
            product: Product model instance with .name and .gw_sku fields.

        Returns:
            dict with keys:
                price       (Decimal) — item price
                shipping    (Decimal) — shipping cost (0 if free)
                total_cost  (Decimal) — price + shipping
                title       (str)     — eBay listing title
                url         (str)     — viewItemURL from eBay API
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
                    '[ebay] Match: "%s" — $%.2f + $%.2f shipping',
                    item['title'][:60], item['price'], item['shipping'],
                )
                return item

        logger.debug('[ebay] No valid match for "%s"', product.name)
        return None

    def search_items(self, keywords, max_results=10):
        """
        Search eBay for items matching keywords using findItemsAdvanced.

        Filters applied:
          - ListingType: FixedPrice (Buy It Now only, no auctions)
          - Condition: New
          - HideDuplicateItems: true

        Sort order: PricePlusShippingLowest (cheapest total first)

        Args:
            keywords: Search query string.
            max_results: Number of results to request (max 100).

        Returns:
            List of dicts with parsed item data, or empty list.

        Raises:
            EbayAPIError: If eBay returns an API-level error.
            RuntimeError: If daily call limit is approaching.
        """
        if self.api_calls_made >= DAILY_CALL_SAFETY_LIMIT:
            raise RuntimeError(
                f'Approaching eBay daily call limit '
                f'({self.api_calls_made}/{DAILY_CALL_LIMIT}). Stopping.'
            )

        params = {
            # Required Finding API parameters
            'OPERATION-NAME': 'findItemsAdvanced',
            'SERVICE-VERSION': '1.0.0',
            'SECURITY-APPNAME': self.app_id,
            'RESPONSE-DATA-FORMAT': 'JSON',
            'REST-PAYLOAD': '',

            # Search query
            'keywords': keywords,

            # Pagination
            'paginationInput.entriesPerPage': str(min(max_results, 100)),
            'paginationInput.pageNumber': '1',

            # Item filters
            'itemFilter(0).name': 'ListingType',
            'itemFilter(0).value(0)': 'FixedPrice',
            'itemFilter(1).name': 'Condition',
            'itemFilter(1).value(0)': 'New',
            'itemFilter(2).name': 'HideDuplicateItems',
            'itemFilter(2).value(0)': 'true',

            # Sort by cheapest total (price + shipping)
            'sortOrder': 'PricePlusShippingLowest',
        }

        try:
            response = self.session.get(
                self.endpoint,
                params=params,
                timeout=10,
            )
            response.raise_for_status()
        except requests.Timeout:
            raise RuntimeError(f'eBay API timeout for query: "{keywords}"')
        except requests.RequestException as exc:
            raise RuntimeError(f'eBay API network error: {exc}') from exc
        finally:
            self.api_calls_made += 1

        try:
            data = response.json()
        except ValueError as exc:
            raise RuntimeError(
                f'eBay API returned invalid JSON: {exc}'
            ) from exc

        # Check API-level success
        try:
            response_root = data['findItemsAdvancedResponse'][0]
            ack = response_root.get('ack', [''])[0]
        except (KeyError, IndexError) as exc:
            raise RuntimeError(
                f'Unexpected eBay API response structure: {exc}'
            ) from exc

        if ack not in ('Success', 'Warning'):
            error_msg = self._extract_error_message(response_root)
            raise EbayAPIError(
                f'eBay API error for "{keywords}": {error_msg}'
            )

        # Extract items from response
        try:
            items_raw = (
                response_root
                .get('searchResult', [{}])[0]
                .get('item', [])
            )
        except (KeyError, IndexError):
            return []

        return [self._parse_item(item) for item in items_raw
                if self._parse_item(item) is not None]

    # -------------------------------------------------------------------------
    # Private methods
    # -------------------------------------------------------------------------

    @staticmethod
    def _build_search_query(product_name):
        """
        Build an optimised eBay search query from a product name.

        Rules:
          - Remove special characters that confuse eBay search
          - Add 'Warhammer' if not present (narrows to hobby products)
          - Citadel/hobby supply products keep their own brand name
          - Limit to 50 characters for best eBay results

        Args:
            product_name: Raw product name from DB.

        Returns:
            Clean search query string.
        """
        # Remove special characters except spaces and alphanumerics
        query = re.sub(r"[^\w\s']", ' ', product_name)
        query = re.sub(r'\s+', ' ', query).strip()

        # Citadel hobby products are well known by brand — don't add Warhammer
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

        # eBay works best with concise queries — truncate to 50 chars
        if len(query) > 50:
            query = query[:50].rsplit(' ', 1)[0]

        return query.strip()

    @staticmethod
    def _parse_item(item):
        """
        Parse a raw eBay API item dict into a clean result dict.

        Extracts price, shipping, total cost, title, and URL.
        Uses viewItemURL as required by eBay API terms.

        Args:
            item: Raw item dict from eBay API response.

        Returns:
            Parsed dict or None if essential fields are missing.
        """
        try:
            title = item.get('title', [''])[0]

            # Item URL — must use viewItemURL per eBay API terms
            url = item.get('viewItemURL', [''])[0]
            if not url:
                return None

            # Item ID
            item_id = item.get('itemId', [''])[0]

            # Price
            selling_status = item.get('sellingStatus', [{}])[0]
            current_price = selling_status.get('currentPrice', [{}])[0]
            price_value = current_price.get('__value__', '0')
            price = Decimal(str(price_value))

            # Shipping cost (0 if free shipping)
            shipping_info = item.get('shippingInfo', [{}])[0]
            shipping_cost_data = shipping_info.get('shippingServiceCost', [{}])
            if shipping_cost_data:
                shipping_value = shipping_cost_data[0].get('__value__', '0')
                shipping = Decimal(str(shipping_value))
            else:
                shipping = Decimal('0')

            total_cost = price + shipping

            return {
                'title': title,
                'url': url,
                'item_id': item_id,
                'price': price,
                'shipping': shipping,
                'total_cost': total_cost,
            }

        except (KeyError, IndexError, InvalidOperation, TypeError):
            return None

    @staticmethod
    def _is_valid_result(result, product):
        """
        Validate that an eBay listing is a genuine match for our product.

        Validation checks:
          1. Title contains at least 2 keywords from our product name
             (words longer than 3 chars to skip noise words)
          2. Total cost is in a reasonable range ($1 — $1,000)
          3. Shipping cost is not suspiciously high (max $100)
          4. URL is present and links to eBay

        Args:
            result: Parsed item dict from _parse_item.
            product: Product model instance.

        Returns:
            True if listing is a valid match, False otherwise.
        """
        if not result or not result.get('url'):
            return False

        title_lower = result['title'].lower()
        product_name_lower = product.name.lower()

        # Extract meaningful keywords (skip short words like 'of', 'the')
        keywords = [
            word for word in product_name_lower.split()
            if len(word) > 3
        ]

        # Require at least 2 keyword matches in the listing title
        matches = sum(1 for kw in keywords if kw in title_lower)
        if matches < 2:
            logger.debug(
                '[ebay] Rejected (keyword mismatch): "%s" vs "%s" (%d matches)',
                result['title'][:60], product.name, matches,
            )
            return False

        # Total cost sanity check
        total_cost = result.get('total_cost', Decimal('0'))
        if total_cost < Decimal('1.00') or total_cost > Decimal('1000.00'):
            logger.debug(
                '[ebay] Rejected (price out of range): $%.2f for "%s"',
                total_cost, product.name,
            )
            return False

        # Shipping sanity check
        shipping = result.get('shipping', Decimal('0'))
        if shipping > Decimal('100.00'):
            logger.debug(
                '[ebay] Rejected (shipping too high): $%.2f for "%s"',
                shipping, product.name,
            )
            return False

        # URL must link to eBay
        if 'ebay.com' not in result['url']:
            return False

        return True

    @staticmethod
    def _extract_error_message(response_root):
        """Extract a human-readable error message from an eBay API error response."""
        try:
            error_data = response_root.get('errorMessage', [{}])[0]
            error = error_data.get('error', [{}])[0]
            message = error.get('message', ['Unknown eBay API error'])[0]
            return message
        except (KeyError, IndexError):
            return 'Unknown eBay API error'
