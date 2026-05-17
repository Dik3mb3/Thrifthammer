"""
Amazon Creators API client — OAuth2 (LWA) authentication.

This is a clean replacement for the HTML-scraping approach in amazon.py.
PA-API v5 was retired on May 15 2026; the Creators API is the official
successor for Amazon Associates price lookups.

Authentication:
  Uses Login with Amazon (LWA) OAuth2 client credentials flow.
  Token endpoint: https://api.amazon.com/auth/o2/token
  Scope: creatorsapi::default
  The access token is valid for ~3600 seconds and is cached in memory.

Rate limits (revenue-linked, not hard-coded):
  Default (new/low-revenue accounts): 1 TPS, 8,640 calls/day.
  Each GetItems call handles up to 10 ASINs, so at 1 TPS that is
  86,400 ASIN lookups/day — far more than our entire catalog.

DO NOT modify scrapers/retailers/amazon.py — it remains intact as backup.
The HTML scraper continues to work and can be run manually if needed.

Usage (via management command):
  python manage.py update_amazon_creators_prices --test-auth
  python manage.py update_amazon_creators_prices --dry-run
  python manage.py update_amazon_creators_prices --sku AS-001
  python manage.py update_amazon_creators_prices --batch-tag skaven
  python manage.py update_amazon_creators_prices
"""

import logging
import re
import time
from decimal import Decimal, InvalidOperation

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# API endpoint constants — update here if Amazon changes paths
# ---------------------------------------------------------------------------

# LWA token endpoint (Login with Amazon OAuth2)
_TOKEN_URL = 'https://api.amazon.com/auth/o2/token'

# Creators API base and items path
_API_BASE   = 'https://creatorsapi.amazon'
_ITEMS_PATH = '/catalog/v1/getItems'

# Resources to request.
# 'offersV2.listings.condition' lets us filter out Used/Collectible/Refurbished
# listings so we only surface new-condition prices to users.
# Note: availability.type is NOT a valid resource — do not add it.
_RESOURCES = [
    'offersV2.listings.price',
    'offersV2.listings.condition',
]

# Amazon limits GetItems to 10 ASINs per call
_BATCH_SIZE = 10

# Delay between API calls in seconds — keeps us safely under 1 TPS
_CALL_DELAY = 1.1

# Regex to extract bare ASIN from any Amazon URL (same pattern as amazon.py)
_ASIN_RE = re.compile(r'/dp/([A-Z0-9]{10})')


def extract_asin(url):
    """
    Extract the 10-character ASIN from any Amazon product URL.

    Args:
        url: Any Amazon URL (with or without tracking params).

    Returns:
        ASIN string, or None if no ASIN found.
    """
    match = _ASIN_RE.search(url or '')
    return match.group(1) if match else None


class AmazonCreatorsClient:
    """
    OAuth2 client for the Amazon Creators API.

    Handles token acquisition with automatic caching, and batched
    GetItems requests for price and availability data by ASIN.

    Thread safety: not guaranteed. Intended for single-threaded use
    inside management commands.
    """

    def __init__(self):
        """Initialise the client with an empty token cache."""
        self._access_token = None
        self._token_expires_at = 0.0
        self._session = requests.Session()
        self._session.headers.update({'Accept': 'application/json'})

    # -------------------------------------------------------------------------
    # Authentication
    # -------------------------------------------------------------------------

    def get_token(self):
        """
        Return a valid OAuth2 access token, refreshing if within 60s of expiry.

        Raises:
            requests.HTTPError: if token request fails.
            RuntimeError: if credentials are not configured.
        """
        if not settings.AMAZON_CREATORS_CLIENT_ID:
            raise RuntimeError(
                'AMAZON_CREATORS_CLIENT_ID is not set. '
                'Add it to your .env file or Railway environment variables.'
            )
        if not settings.AMAZON_CREATORS_CLIENT_SECRET:
            raise RuntimeError(
                'AMAZON_CREATORS_CLIENT_SECRET is not set. '
                'Add it to your .env file or Railway environment variables.'
            )

        if self._access_token and time.time() < self._token_expires_at - 60:
            return self._access_token

        logger.debug('[creators-api] Fetching new OAuth2 token')

        resp = self._session.post(
            _TOKEN_URL,
            data={
                'grant_type':    'client_credentials',
                'client_id':     settings.AMAZON_CREATORS_CLIENT_ID,
                'client_secret': settings.AMAZON_CREATORS_CLIENT_SECRET,
                'scope':         'creatorsapi::default',
            },
            headers={'Content-Type': 'application/x-www-form-urlencoded'},
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()

        self._access_token = data['access_token']
        expires_in = data.get('expires_in', 3600)
        self._token_expires_at = time.time() + expires_in

        logger.debug('[creators-api] Token acquired, valid for %ds', expires_in)
        return self._access_token

    # -------------------------------------------------------------------------
    # Data retrieval
    # -------------------------------------------------------------------------

    def get_items(self, asins):
        """
        Call GetItems for up to 10 ASINs in a single API request.

        Args:
            asins: list of ASIN strings (max _BATCH_SIZE).

        Returns:
            dict mapping ASIN -> {'price': Decimal or None, 'in_stock': bool}.

        Raises:
            requests.HTTPError: on non-2xx responses (after one retry on 429).
        """
        if not asins:
            return {}

        token = self.get_token()
        payload = {
            'itemIds':     asins,
            'partnerTag':  settings.AMAZON_ASSOCIATE_TAG,
            'partnerType': 'Associates',
            'resources':   _RESOURCES,
        }
        headers = {
            'Authorization': f'Bearer {token}',
            'x-marketplace': 'www.amazon.com',
            'Content-Type':  'application/json; charset=utf-8',
        }

        resp = self._session.post(
            f'{_API_BASE}{_ITEMS_PATH}',
            json=payload,
            headers=headers,
            timeout=20,
        )

        if resp.status_code == 429:
            logger.warning('[creators-api] Rate limited (429) — sleeping 5s then retrying')
            time.sleep(5)
            resp = self._session.post(
                f'{_API_BASE}{_ITEMS_PATH}',
                json=payload,
                headers=headers,
                timeout=20,
            )

        resp.raise_for_status()
        data = resp.json()

        results = {}
        items = data.get('itemsResult', {}).get('items', [])
        for item in items:
            asin = item.get('asin')
            if not asin:
                continue
            results[asin] = {
                'price':    self._extract_price(item),
                'in_stock': self._extract_in_stock(item),
            }

        logger.debug(
            '[creators-api] GetItems: requested %d, received %d',
            len(asins), len(results),
        )
        return results

    def get_items_batched(self, asins, delay=_CALL_DELAY):
        """
        Call GetItems for any number of ASINs, batching into groups of 10.

        Args:
            asins:  list of ASIN strings (any length).
            delay:  seconds to sleep between batch calls.

        Returns:
            Merged dict mapping ASIN -> {'price': Decimal or None, 'in_stock': bool}.
        """
        all_results = {}
        batches = [asins[i:i + _BATCH_SIZE] for i in range(0, len(asins), _BATCH_SIZE)]

        for idx, batch in enumerate(batches):
            if idx > 0:
                time.sleep(delay)
            logger.debug(
                '[creators-api] Batch %d/%d: %s',
                idx + 1, len(batches), ', '.join(batch),
            )
            batch_result = self.get_items(batch)
            all_results.update(batch_result)

        return all_results

    # -------------------------------------------------------------------------
    # Response parsing
    # -------------------------------------------------------------------------

    @staticmethod
    def _is_new_condition(listing):
        """
        Return True if a listing is new condition (not used/collectible/refurbished).

        Amazon condition values: 'New', 'Used', 'UsedLikeNew', 'UsedVeryGood',
        'UsedGood', 'UsedAcceptable', 'Collectible', 'Refurbished', etc.

        If the condition field is absent from the response (e.g. the resource was
        not returned), we default to True so we do not accidentally hide prices.
        """
        condition = listing.get('condition', {})
        if not condition:
            return True
        return condition.get('value', 'New') == 'New'

    @staticmethod
    def _extract_price(item):
        """
        Extract the lowest NEW-condition listing price from a GetItems response item.

        Filters to new-condition listings only to avoid surfacing used/collectible
        prices (e.g. a $7 used book undercutting the $60 new price).

        The API returns price under listing.price.money.amount (not listing.price.amount).

        Returns:
            Decimal price, or None if no new-condition price is available.
        """
        try:
            listings = item.get('offersV2', {}).get('listings', [])
            if not listings:
                return None

            prices = []
            for listing in listings:
                if not AmazonCreatorsClient._is_new_condition(listing):
                    continue
                amount = listing.get('price', {}).get('money', {}).get('amount')
                if amount is not None:
                    prices.append(Decimal(str(amount)))

            # Return the first new-condition listing price (Buy Box / featured
            # offer) rather than the cheapest across all new sellers.  The API
            # returns listings in Buy Box priority order, so index 0 is what
            # most users see when they click through to Amazon.
            return prices[0] if prices else None

        except (InvalidOperation, ValueError, TypeError):
            return None

    @staticmethod
    def _extract_in_stock(item):
        """
        Determine availability from a GetItems response item.

        The API does not expose a dedicated availability resource, so we
        infer stock status from whether any new-condition listing has a buyable
        price. Used/collectible listings do not count as in-stock.

        Returns:
            True if at least one new-condition listing has a purchasable price.
        """
        try:
            listings = item.get('offersV2', {}).get('listings', [])
            for listing in listings:
                if not AmazonCreatorsClient._is_new_condition(listing):
                    continue
                amount = listing.get('price', {}).get('money', {}).get('amount')
                if amount is not None:
                    return True
            return False
        except (TypeError, AttributeError):
            return False
