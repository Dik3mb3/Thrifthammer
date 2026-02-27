"""
eBay scraper using the official eBay Browse API.

Uses OAuth 2.0 Client Credentials flow to authenticate, then calls the
Browse API item_summary/search endpoint to find the lowest-priced NEW
listing for each product.

Environment variables required:
    EBAY_APP_ID     — eBay App ID (Client ID) from developer.ebay.com
    EBAY_CERT_ID    — eBay Cert ID (Client Secret) from developer.ebay.com

Usage:
    python manage.py run_scrapers ebay

Notes:
- Only searches for NEW condition items to ensure quality listings.
- Picks the lowest-priced active listing for each product.
- Always writes a row — either with price or not_available=True.
- OAuth token is cached for the duration of the run (expires after 2 hours).
- Respects SCRAPER_REQUEST_DELAY between API calls.
"""

import logging
import os
import re
import time
from decimal import Decimal, InvalidOperation

import requests
from django.conf import settings
from django.utils import timezone

from prices.models import CurrentPrice
from products.models import Product, Retailer
from scrapers.models import ScrapeJob

logger = logging.getLogger(__name__)

# eBay API endpoints (Production)
OAUTH_URL = 'https://api.ebay.com/identity/v1/oauth2/token'
BROWSE_URL = 'https://api.ebay.com/buy/browse/v1/item_summary/search'

# Only show NEW condition listings
CONDITION_NEW = 'NEW'

# eBay marketplace ID for US
MARKETPLACE_ID = 'EBAY_US'


class EbayScraper:
    """
    eBay price fetcher using the official Browse API.

    For each active product, searches eBay for the lowest-priced NEW
    listing matching the product name. Saves price, stock status, and
    a direct search URL to the DB.
    """

    retailer_slug = 'ebay'

    def __init__(self):
        """Initialise session and load credentials from environment."""
        self.session = requests.Session()
        self.app_id = os.environ.get('EBAY_APP_ID', '')
        self.cert_id = os.environ.get('EBAY_CERT_ID', '')
        self.delay = getattr(settings, 'SCRAPER_REQUEST_DELAY', 2)
        self._token = None

        if not self.app_id or not self.cert_id:
            raise RuntimeError(
                'EBAY_APP_ID and EBAY_CERT_ID environment variables are required. '
                'Add them to Railway Variables.'
            )

    # -------------------------------------------------------------------------
    # Public entry point
    # -------------------------------------------------------------------------

    def run(self):
        """Execute a full price fetch job and return the ScrapeJob record."""
        try:
            retailer = Retailer.objects.get(slug=self.retailer_slug)
        except Retailer.DoesNotExist:
            logger.error('Retailer "%s" not found in DB.', self.retailer_slug)
            raise

        # Get OAuth token once for the whole run
        self._token = self._get_oauth_token()

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
                result = self._find_cheapest_listing(product.name)

                if result is None:
                    self._save_not_available(product, retailer)
                    logger.info('[n/a]      %s — no listings found on eBay', product.name)
                else:
                    price, url = result
                    CurrentPrice.objects.update_or_create(
                        product=product,
                        retailer=retailer,
                        defaults={
                            'price': price,
                            'url': url,
                            'in_stock': True,  # Active eBay listings are always available
                            'not_available': False,
                        },
                    )
                    logger.info('[updated]  %s — $%.2f', product.name, price)

                job.prices_updated += 1

            except Exception as exc:
                msg = f'{product.name}: {exc}'
                errors.append(msg)
                logger.exception('Error fetching eBay price for %s', product.name)

            time.sleep(self.delay)

        job.status = 'success'
        job.errors = '\n'.join(errors)
        job.finished_at = timezone.now()
        job.save()
        return job

    # -------------------------------------------------------------------------
    # eBay API calls
    # -------------------------------------------------------------------------

    def _get_oauth_token(self):
        """
        Fetch an OAuth 2.0 Client Credentials token from eBay.

        Returns the access token string. Raises RuntimeError on failure.
        """
        import base64
        credentials = base64.b64encode(
            f'{self.app_id}:{self.cert_id}'.encode()
        ).decode()

        response = requests.post(
            OAUTH_URL,
            headers={
                'Authorization': f'Basic {credentials}',
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            data={
                'grant_type': 'client_credentials',
                'scope': 'https://api.ebay.com/oauth/api_scope',
            },
            timeout=15,
        )

        if response.status_code != 200:
            raise RuntimeError(
                f'eBay OAuth failed: {response.status_code} — {response.text}'
            )

        token = response.json().get('access_token')
        if not token:
            raise RuntimeError('eBay OAuth returned no access_token')

        logger.info('eBay OAuth token obtained successfully.')
        return token

    def _find_cheapest_listing(self, product_name):
        """
        Search eBay for the cheapest NEW listing matching the product name.

        Returns (Decimal price, str url) or None if no listings found.
        """
        # Build clean search query
        search_query = self._build_search_query(product_name)

        params = {
            'q': search_query,
            'filter': f'conditions:{{{CONDITION_NEW}}},buyingOptions:{{FIXED_PRICE}}',
            'sort': 'price',           # cheapest first
            'limit': '5',              # only need top 5
            'fieldgroups': 'MATCHING_ITEMS',
        }

        headers = {
            'Authorization': f'Bearer {self._token}',
            'X-EBAY-C-MARKETPLACE-ID': MARKETPLACE_ID,
            'Content-Type': 'application/json',
        }

        try:
            response = self.session.get(
                BROWSE_URL,
                headers=headers,
                params=params,
                timeout=15,
            )
        except Exception as exc:
            raise RuntimeError(f'eBay API request failed: {exc}') from exc

        if response.status_code == 401:
            raise RuntimeError('eBay token expired or invalid — re-run to refresh')
        if response.status_code != 200:
            raise RuntimeError(
                f'eBay API error {response.status_code}: {response.text[:200]}'
            )

        data = response.json()
        items = data.get('itemSummaries', [])

        if not items:
            return None

        # Pick the cheapest listing — items are sorted by price ascending
        for item in items:
            try:
                price_data = item.get('price', {})
                price = Decimal(str(price_data.get('value', 0)))
                url = item.get('itemWebUrl', '')

                # Sanity check — GW products range from ~$5 to ~$1500
                if price < 5 or price > 1500:
                    continue
                if not url:
                    continue

                return price, url

            except (InvalidOperation, KeyError, TypeError):
                continue

        return None

    # -------------------------------------------------------------------------
    # Helpers
    # -------------------------------------------------------------------------

    @staticmethod
    def _save_not_available(product, retailer):
        """Upsert a not_available=True CurrentPrice row."""
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

    @staticmethod
    def _build_search_query(name):
        """
        Build a clean eBay search query from a product name.

        Adds 'Warhammer' if not already present to narrow results.
        Strips faction prefixes that eBay sellers don't use.

        E.g. 'Space Marine Intercessors' → 'Warhammer Space Marine Intercessors'
             'Citadel Contrast Paint'    → 'Citadel Contrast Paint'
        """
        # These products are well known by brand name — don't add Warhammer
        citadel_keywords = ['citadel', 'citadel paint', 'brush', 'spray', 'contrast']
        name_lower = name.lower()

        if any(kw in name_lower for kw in citadel_keywords):
            return name

        # Add Warhammer prefix for miniature products
        if 'warhammer' not in name_lower:
            return f'Warhammer {name}'

        return name
