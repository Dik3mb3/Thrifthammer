"""
Amazon Product Advertising API (PA-API) 5.0 client for ThriftHammer.

Uses Amazon's official PA-API 5.0 to fetch live prices for products
already stored in the database with Amazon URLs/ASINs.

Compliance summary:
  - Uses official PA-API 5.0 (NOT web scraping)
  - Requires active Amazon Associates account with qualifying sales
  - Fetches only price and availability data (no bulk exports)
  - Links back to Amazon using the affiliate tag
  - Does not cache data beyond 24 hours (PA-API terms)

API Documentation:
  https://webservices.amazon.com/paapi5/documentation/

Authentication:
  PA-API 5.0 requires:
    - AMAZON_ACCESS_KEY   — Access key from Associates / PA-API portal
    - AMAZON_SECRET_KEY   — Secret key from Associates / PA-API portal
    - AMAZON_PARTNER_TAG  — Your Associates tracking ID (e.g. thrifthammer-21)
    - AMAZON_REGION       — Defaults to 'us-east-1' for Amazon.com

  Set these in Railway environment variables (or local .env for development).

Rate limits (Amazon.com):
  - 1 request per second
  - GetItems: up to 10 ASINs per call
  - Daily limit scales with Associates activity

ASIN extraction:
  Amazon product URLs contain the ASIN in the path:
    https://www.amazon.com/dp/B08XYZ123/
    https://www.amazon.com/product-name/dp/B08XYZ123/ref=...
  This client extracts the ASIN automatically from stored URLs.
"""

import hashlib
import hmac
import json
import logging
import re
import time
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

# PA-API endpoints by region
PAAPI_ENDPOINTS = {
    'us-east-1': 'webservices.amazon.com',
    'eu-west-1': 'webservices.amazon.co.uk',
    'us-west-2': 'webservices.amazon.ca',
    'ap-northeast-1': 'webservices.amazon.co.jp',
    'ap-southeast-1': 'webservices.amazon.com.au',
}

PAAPI_OPERATION = 'GetItems'
PAAPI_PATH = '/paapi5/getitems'
PAAPI_SERVICE = 'ProductAdvertisingAPI'
PAAPI_TARGET = 'com.amazon.paapi5.v1.ProductAdvertisingAPIv1.GetItems'

# Regex to extract ASIN from Amazon URLs
# Matches /dp/ASIN or /gp/product/ASIN
_ASIN_RE = re.compile(r'(?:/dp/|/gp/product/)([A-Z0-9]{10})', re.IGNORECASE)

# Resources to request from PA-API
_REQUESTED_RESOURCES = [
    'Offers.Listings.Price',
    'Offers.Listings.Availability.Message',
    'Offers.Listings.Availability.Type',
    'Offers.Listings.DeliveryInfo.IsFreeShippingEligible',
    'ItemInfo.Title',
]

# Batching — PA-API allows up to 10 ASINs per GetItems call
BATCH_SIZE = 10

# Minimum delay between requests (1 req/sec limit)
REQUEST_DELAY = 1.1


class AmazonAPIError(Exception):
    """Raised when PA-API returns an error response."""
    pass


class AmazonPAAPI:
    """
    Client for Amazon Product Advertising API 5.0.

    Fetches live prices and availability for products using their ASINs.
    ASINs are extracted automatically from stored Amazon product URLs.

    Authentication uses AWS Signature Version 4 (SigV4) as required
    by PA-API 5.0.

    Usage:
        api = AmazonPAAPI()
        results = api.get_prices_for_asins(['B08XYZ123', 'B09ABC456'])
        for asin, data in results.items():
            print(asin, data['price'], data['in_stock'])
    """

    def __init__(self, access_key=None, secret_key=None, partner_tag=None, region=None):
        """
        Initialise the Amazon PA-API client.

        Args:
            access_key:  PA-API access key. Defaults to settings.AMAZON_ACCESS_KEY.
            secret_key:  PA-API secret key. Defaults to settings.AMAZON_SECRET_KEY.
            partner_tag: Associates tag. Defaults to settings.AMAZON_PARTNER_TAG.
            region:      AWS region. Defaults to settings.AMAZON_REGION or 'us-east-1'.
        """
        self.access_key  = access_key  or getattr(settings, 'AMAZON_ACCESS_KEY', '')
        self.secret_key  = secret_key  or getattr(settings, 'AMAZON_SECRET_KEY', '')
        self.partner_tag = partner_tag or getattr(settings, 'AMAZON_PARTNER_TAG', '')
        self.region      = region      or getattr(settings, 'AMAZON_REGION', 'us-east-1')

        missing = []
        if not self.access_key:
            missing.append('AMAZON_ACCESS_KEY')
        if not self.secret_key:
            missing.append('AMAZON_SECRET_KEY')
        if not self.partner_tag:
            missing.append('AMAZON_PARTNER_TAG')

        if missing:
            raise ValueError(
                f'Amazon PA-API not configured. Missing: {", ".join(missing)}. '
                'Set these in Railway environment variables.'
            )

        self.host = PAAPI_ENDPOINTS.get(self.region, 'webservices.amazon.com')
        self.session = requests.Session()
        self.api_calls_made = 0

        logger.info(
            'Amazon PA-API client initialised (region=%s, tag=%s)',
            self.region, self.partner_tag,
        )

    # -------------------------------------------------------------------------
    # Public methods
    # -------------------------------------------------------------------------

    @staticmethod
    def extract_asin_from_url(url):
        """
        Extract the ASIN from an Amazon product URL.

        Supports URL formats:
          - https://www.amazon.com/dp/B08XYZ123/
          - https://www.amazon.com/Product-Name/dp/B08XYZ123/ref=...
          - https://www.amazon.co.uk/gp/product/B08XYZ123

        Args:
            url: Amazon product URL string.

        Returns:
            ASIN string (10 alphanumeric chars) or None if not found.
        """
        if not url:
            return None
        match = _ASIN_RE.search(url)
        return match.group(1).upper() if match else None

    def get_prices_for_asins(self, asins):
        """
        Fetch live prices and availability for a list of ASINs.

        Makes batched GetItems requests (up to 10 ASINs per call).
        Respects the 1 request/second rate limit with automatic throttling.

        Args:
            asins: List of ASIN strings (e.g. ['B08XYZ123', 'B09ABC456']).

        Returns:
            Dict mapping ASIN → result dict:
                price     (Decimal or None) — item price (None if unavailable)
                in_stock  (bool)            — True if available to buy
                title     (str)             — product title from Amazon
                url       (str)             — product URL with affiliate tag
            ASINs that returned errors are omitted from the result dict.
        """
        if not asins:
            return {}

        results = {}
        # Process in batches of BATCH_SIZE
        for batch_start in range(0, len(asins), BATCH_SIZE):
            batch = asins[batch_start:batch_start + BATCH_SIZE]
            logger.debug('[amazon] Fetching batch of %d ASINs: %s', len(batch), batch)

            try:
                batch_results = self._get_items(batch)
                results.update(batch_results)
            except AmazonAPIError as exc:
                logger.error('[amazon] Batch error: %s', exc)
            except RuntimeError as exc:
                logger.error('[amazon] Request error: %s', exc)

            # Throttle between batches
            if batch_start + BATCH_SIZE < len(asins):
                time.sleep(REQUEST_DELAY)

        return results

    def get_price_for_url(self, url):
        """
        Fetch the current price for a single Amazon product URL.

        Convenience wrapper around get_prices_for_asins.

        Args:
            url: Amazon product URL with a valid ASIN.

        Returns:
            Result dict (price, in_stock, title, url) or None if not found.
        """
        asin = self.extract_asin_from_url(url)
        if not asin:
            logger.warning('[amazon] Could not extract ASIN from URL: %s', url)
            return None

        results = self.get_prices_for_asins([asin])
        return results.get(asin)

    # -------------------------------------------------------------------------
    # Private methods
    # -------------------------------------------------------------------------

    def _get_items(self, asins):
        """
        Make a single GetItems PA-API request for up to 10 ASINs.

        Args:
            asins: List of up to 10 ASIN strings.

        Returns:
            Dict mapping ASIN → result dict.

        Raises:
            AmazonAPIError: If PA-API returns an error.
            RuntimeError: On network or parsing errors.
        """
        payload = {
            'ItemIds': asins,
            'Resources': _REQUESTED_RESOURCES,
            'PartnerTag': self.partner_tag,
            'PartnerType': 'Associates',
            'Marketplace': self._get_marketplace(),
        }
        payload_json = json.dumps(payload, separators=(',', ':'))

        # Build SigV4 signed headers
        headers = self._build_signed_headers(payload_json)

        try:
            response = self.session.post(
                f'https://{self.host}{PAAPI_PATH}',
                data=payload_json,
                headers=headers,
                timeout=15,
            )
            response.raise_for_status()
        except requests.Timeout:
            raise RuntimeError('Amazon PA-API timeout')
        except requests.HTTPError as exc:
            # Parse error body if available
            try:
                err_body = exc.response.json()
                err_msg = err_body.get('Errors', [{}])[0].get('Message', str(exc))
            except Exception:  # noqa: BLE001
                err_msg = str(exc)
            raise AmazonAPIError(f'Amazon PA-API HTTP error: {err_msg}') from exc
        except requests.RequestException as exc:
            raise RuntimeError(f'Amazon PA-API network error: {exc}') from exc
        finally:
            self.api_calls_made += 1

        try:
            data = response.json()
        except ValueError as exc:
            raise RuntimeError(f'Amazon PA-API returned invalid JSON: {exc}') from exc

        # Check for top-level errors
        if 'Errors' in data:
            error_msgs = [e.get('Message', 'Unknown') for e in data['Errors']]
            raise AmazonAPIError(f'Amazon PA-API errors: {"; ".join(error_msgs)}')

        return self._parse_items_response(data)

    def _parse_items_response(self, data):
        """
        Parse a GetItems response into a clean result dict.

        Args:
            data: Parsed JSON response from PA-API.

        Returns:
            Dict mapping ASIN → result dict.
        """
        results = {}

        items_result = data.get('ItemsResult', {})
        items = items_result.get('Items', [])

        for item in items:
            asin = item.get('ASIN')
            if not asin:
                continue

            try:
                result = self._parse_single_item(item)
                if result:
                    results[asin] = result
            except Exception as exc:  # noqa: BLE001
                logger.warning('[amazon] Failed to parse item %s: %s', asin, exc)

        return results

    def _parse_single_item(self, item):
        """
        Parse a single item from the PA-API response.

        Args:
            item: Single item dict from the Items array.

        Returns:
            Result dict or None if essential data is missing.
        """
        asin = item.get('ASIN', '')

        # Title
        title = ''
        item_info = item.get('ItemInfo', {})
        if item_info:
            title_data = item_info.get('Title', {})
            title = title_data.get('DisplayValue', '')

        # Build affiliate URL
        url = f'https://www.amazon.com/dp/{asin}?tag={self.partner_tag}'
        if self.region == 'eu-west-1':
            url = f'https://www.amazon.co.uk/dp/{asin}?tag={self.partner_tag}'

        # Price and availability
        price = None
        in_stock = False

        offers = item.get('Offers', {})
        listings = offers.get('Listings', [])

        if listings:
            # Take the first (usually lowest/Featured) listing
            listing = listings[0]

            # Price
            price_data = listing.get('Price', {})
            if price_data:
                price_amount = price_data.get('Amount')
                if price_amount is not None:
                    try:
                        price = Decimal(str(price_amount))
                    except InvalidOperation:
                        price = None

            # Availability
            availability = listing.get('Availability', {})
            avail_type = availability.get('Type', '')
            # PA-API availability types: Now, 1-2 days, Usually ships in X days, etc.
            in_stock = avail_type in ('Now', 'Available')

        if price is None and not in_stock:
            return None

        return {
            'asin':     asin,
            'price':    price,
            'in_stock': in_stock,
            'title':    title,
            'url':      url,
        }

    def _get_marketplace(self):
        """Return the Amazon marketplace string for the configured region."""
        marketplaces = {
            'us-east-1':     'www.amazon.com',
            'eu-west-1':     'www.amazon.co.uk',
            'us-west-2':     'www.amazon.ca',
            'ap-northeast-1': 'www.amazon.co.jp',
            'ap-southeast-1': 'www.amazon.com.au',
        }
        return marketplaces.get(self.region, 'www.amazon.com')

    def _build_signed_headers(self, payload_json):
        """
        Build AWS Signature Version 4 (SigV4) signed headers for a PA-API request.

        PA-API 5.0 requires SigV4 authentication on every request.

        Args:
            payload_json: JSON string of the request payload.

        Returns:
            Dict of HTTP headers including Authorization, X-Amz-Date, etc.
        """
        now = datetime.now(timezone.utc)
        amzdate = now.strftime('%Y%m%dT%H%M%SZ')
        datestamp = now.strftime('%Y%m%d')

        # Canonical headers (must be lowercase, sorted)
        canonical_headers = (
            f'content-encoding:amz-1.0\n'
            f'content-type:application/json; charset=utf-8\n'
            f'host:{self.host}\n'
            f'x-amz-date:{amzdate}\n'
            f'x-amz-target:{PAAPI_TARGET}\n'
        )
        signed_headers = 'content-encoding;content-type;host;x-amz-date;x-amz-target'

        # Payload hash
        payload_hash = hashlib.sha256(payload_json.encode('utf-8')).hexdigest()

        # Canonical request
        canonical_request = '\n'.join([
            'POST',
            PAAPI_PATH,
            '',  # No query string
            canonical_headers,
            signed_headers,
            payload_hash,
        ])

        # String to sign
        credential_scope = f'{datestamp}/{self.region}/{PAAPI_SERVICE}/aws4_request'
        string_to_sign = '\n'.join([
            'AWS4-HMAC-SHA256',
            amzdate,
            credential_scope,
            hashlib.sha256(canonical_request.encode('utf-8')).hexdigest(),
        ])

        # Signing key
        signing_key = self._get_signing_key(datestamp)

        # Signature
        signature = hmac.new(
            signing_key,
            string_to_sign.encode('utf-8'),
            hashlib.sha256,
        ).hexdigest()  # type: ignore[attr-defined]

        # Authorization header
        authorization = (
            f'AWS4-HMAC-SHA256 '
            f'Credential={self.access_key}/{credential_scope}, '
            f'SignedHeaders={signed_headers}, '
            f'Signature={signature}'
        )

        return {
            'Content-Encoding': 'amz-1.0',
            'Content-Type': 'application/json; charset=utf-8',
            'Host': self.host,
            'X-Amz-Date': amzdate,
            'X-Amz-Target': PAAPI_TARGET,
            'Authorization': authorization,
        }

    def _get_signing_key(self, datestamp):
        """
        Derive the SigV4 signing key.

        Args:
            datestamp: Date string in YYYYMMDD format.

        Returns:
            HMAC signing key as bytes.
        """
        def _sign(key, msg):
            return hmac.new(key, msg.encode('utf-8'), hashlib.sha256).digest()

        k_date    = _sign(('AWS4' + self.secret_key).encode('utf-8'), datestamp)
        k_region  = _sign(k_date, self.region)
        k_service = _sign(k_region, PAAPI_SERVICE)
        k_signing = _sign(k_service, 'aws4_request')
        return k_signing
