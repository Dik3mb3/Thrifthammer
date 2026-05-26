"""
Management command: update_ebay_uk_prices

Fetches live eBay UK prices for all active products using the official
eBay Browse API v1 on the EBAY_GB marketplace. Saves results to the
CurrentPrice model linked to the 'ebay-uk' retailer, with currency='GBP'.

This command is part of the UK version feature (Phase 5).
It uses the same eBay API credentials as the US scraper — only the
marketplace ID changes (EBAY_GB vs EBAY_US).

Compliance:
  - Uses official eBay Browse API (not scraping)
  - Respects 5,000 calls/day limit (shared with US scraper)
  - Links to viewItemURL provided by eBay API
  - Attributes eBay as price source

Rules:
  - CurrentPrice entries with manual_url_override=True are NEVER touched.
  - Only saves to 'ebay-uk' retailer — never touches US 'ebay' records.

Usage:
    # Dry run (no DB writes):
    python manage.py update_ebay_uk_prices --dry-run --limit 5

    # Full run (all products):
    python manage.py update_ebay_uk_prices

    # Single product by GW SKU:
    python manage.py update_ebay_uk_prices --sku 01-07

    # Diagnose a "Not found" product:
    python manage.py update_ebay_uk_prices --sku 01-07 --debug --dry-run

    # Filter by faction or category:
    python manage.py update_ebay_uk_prices --faction "Necrons"
    python manage.py update_ebay_uk_prices --category "Warhammer 40,000"
"""

import shlex
import time
from decimal import Decimal

from django.conf import settings
from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Product, Retailer
from products.ebay_api_client_uk import EbayBrowseAPIUK, EbayAPIError

# EPN affiliate tracking parameters for eBay UK marketplace.
# mkrid=710-53481-19255-0 is the UK-specific routing key.
# Set EBAY_UK_AFFILIATE_CAMPAIGN_ID in environment to enable affiliate tracking.
_EPN_PARAMS_UK = 'mkcid=1&mkrid=710-53481-19255-0&toolid=10001&mkevt=1'


def _add_epn_params_uk(url, campaign_id):
    """
    Append eBay UK Partner Network tracking parameters to an eBay item URL.

    Safe to call on URLs that already contain these params — strips any
    existing EPN params first so we never double-append on re-runs.

    Args:
        url:         Raw eBay item URL from the Browse API.
        campaign_id: EPN campaign ID from settings.EBAY_UK_AFFILIATE_CAMPAIGN_ID.

    Returns:
        URL with EPN tracking params appended, or original URL if no
        campaign_id is configured.
    """
    if not campaign_id:
        return url

    # Strip any previously appended EPN params to avoid duplication on re-runs
    for marker in ('mkcid=1', '&mkcid=1'):
        idx = url.find(marker)
        if idx != -1:
            url = url[:idx].rstrip('?&')
            break

    separator = '&' if '?' in url else '?'
    return f'{url}{separator}{_EPN_PARAMS_UK}&campid={campaign_id}'


def _debug_search(ebay_api, product, stdout, style):
    """
    Print every eBay UK candidate for a product with pass/fail reason per filter.

    Used when --debug is active and a product returns "Not found".
    """
    search_name = product.ebay_search_name or product.name
    raw_negatives = getattr(product, 'ebay_negative_keywords', '') or ''
    extra_negatives = shlex.split(raw_negatives) if raw_negatives else None
    query = EbayBrowseAPIUK._build_search_query(search_name, extra_negatives)
    stdout.write(f'    DEBUG query: "{query}"')

    try:
        items = ebay_api.search_items(query, max_results=10)
    except Exception as exc:
        stdout.write(style.ERROR(f'    DEBUG search error: {exc}'))
        return

    if not items:
        stdout.write(style.WARNING('    DEBUG: eBay UK returned 0 results'))
        return

    stdout.write(f'    DEBUG: {len(items)} results from eBay UK —')
    for i, item in enumerate(items, 1):
        title      = item.get('title', '')[:70]
        price      = item.get('total_cost', Decimal('0'))
        reasons    = EbayBrowseAPIUK._get_rejection_reasons(item, product)
        short_desc = item.get('short_description', '')[:100]
        if reasons:
            stdout.write(style.WARNING(f'      [{i}] FAIL  £{price:.2f}  "{title}"'))
            for r in reasons:
                stdout.write(f'           -> {r}')
        else:
            stdout.write(style.SUCCESS(f'      [{i}] PASS  £{price:.2f}  "{title}"'))
        if short_desc:
            stdout.write(f'           Desc: {short_desc}')


class Command(BaseCommand):
    """
    Fetch live eBay UK prices using the Browse API v1 (EBAY_GB marketplace).

    Updates CurrentPrice records for the 'ebay-uk' retailer with currency='GBP'.
    Never touches US eBay ('ebay' retailer) records.

    Uses the same eBay API credentials as update_ebay_prices — only the
    marketplace ID is different (EBAY_GB instead of EBAY_US).
    """

    help = 'Update product prices from eBay UK using the official Browse API (EBAY_GB marketplace).'

    def add_arguments(self, parser):
        """Register command-line arguments."""
        parser.add_argument(
            '--limit',
            type=int,
            default=None,
            metavar='N',
            help='Process only the first N products (for testing).',
        )
        parser.add_argument(
            '--delay',
            type=float,
            default=0.5,
            metavar='SECONDS',
            help='Delay between API calls in seconds (default: 0.5).',
        )
        parser.add_argument(
            '--product',
            type=int,
            default=None,
            metavar='ID',
            help='Update a single product by its database ID.',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            default=False,
            help='Show results without saving to the database.',
        )
        parser.add_argument(
            '--faction',
            type=str,
            default=None,
            metavar='NAME',
            help='Filter to products of a specific faction (case-insensitive, '
                 'e.g. "Orks", "Space Marines", "Adeptus Custodes").',
        )
        parser.add_argument(
            '--debug',
            action='store_true',
            default=False,
            help='For "Not found" products, print every eBay candidate with the '
                 'filter that rejected it. Use with --dry-run for safe diagnosis.',
        )
        parser.add_argument(
            '--category',
            type=str,
            default=None,
            metavar='NAME',
            help='Filter to products in a specific category (case-insensitive, '
                 'e.g. "Paint & Supplies", "Warhammer 40,000", "Age of Sigmar").',
        )
        parser.add_argument(
            '--sku',
            type=str,
            default=None,
            metavar='SKU',
            help='Update a single product by its GW SKU (e.g. 01-07). '
                 'Useful for diagnosing a specific listing with --debug --dry-run.',
        )
        parser.add_argument(
            '--batch-tag',
            type=str,
            default=None,
            metavar='TAG',
            help='Filter to products with a specific batch_tag (e.g. "phase-2", "phase-3").',
        )

    def handle(self, *args, **options):
        """Entry point — run the eBay UK price update."""
        limit      = options['limit']
        delay      = options['delay']
        product_id = options['product']
        dry_run    = options['dry_run']
        faction    = options['faction']
        category   = options['category']
        debug      = options['debug']
        sku_filter = (options['sku'] or '').strip()
        batch_tag  = (options.get('batch_tag') or '').strip()

        # ── Configuration summary ────────────────────────────────────────────
        self.stdout.write('\neBay UK Browse API — Price Update (EBAY_GB / GBP)')
        self.stdout.write('=' * 55)
        self.stdout.write(f'  Marketplace  : EBAY_GB (eBay UK)')
        self.stdout.write(f'  Currency     : GBP (£)')
        self.stdout.write(f'  Retailer     : ebay-uk')
        self.stdout.write(f'  Delay        : {delay}s between calls')
        self.stdout.write(f'  Dry run      : {dry_run}')
        if debug:
            self.stdout.write(self.style.WARNING(
                '  Debug        : ON (prints all eBay UK candidates for "Not found" products)'
            ))
        if faction:
            self.stdout.write(f'  Faction      : {faction}')
        if category:
            self.stdout.write(f'  Category     : {category}')
        if batch_tag:
            self.stdout.write(f'  Batch tag    : {batch_tag}')
        if limit:
            self.stdout.write(f'  Limit        : {limit} products')
        if product_id:
            self.stdout.write(f'  Product ID   : {product_id}')
        if sku_filter:
            self.stdout.write(f'  SKU filter   : {sku_filter}')
        self.stdout.write('=' * 55 + '\n')

        # ── Initialise API client (EBAY_GB marketplace) ──────────────────────
        try:
            ebay_api = EbayBrowseAPIUK()
        except ValueError as exc:
            self.stderr.write(self.style.ERROR(f'Configuration error: {exc}'))
            self.stderr.write(
                'Add EBAY_APP_ID_PRODUCTION and EBAY_CERT_ID_PRODUCTION '
                'to your Railway environment variables.'
            )
            return

        # ── EPN affiliate campaign ID (UK) ───────────────────────────────────
        campaign_id = getattr(settings, 'EBAY_UK_AFFILIATE_CAMPAIGN_ID', '')
        if campaign_id:
            self.stdout.write(f'  EPN affiliate (UK) : campid={campaign_id}')
        else:
            self.stdout.write(
                self.style.WARNING(
                    '  EPN affiliate (UK) : NOT configured '
                    '(set EBAY_UK_AFFILIATE_CAMPAIGN_ID to enable UK affiliate tracking)'
                )
            )

        # ── Get or create eBay UK retailer ───────────────────────────────────
        ebay_uk_retailer, created = Retailer.objects.get_or_create(
            slug='ebay-uk',
            defaults={
                'name':      'eBay UK',
                'website':   'https://www.ebay.co.uk',
                'country':   'UK',
                'is_active': True,
            },
        )
        if created:
            self.stdout.write(self.style.SUCCESS('Created eBay UK retailer in DB.'))

        # ── Get products to process ──────────────────────────────────────────
        if product_id:
            products = Product.objects.filter(id=product_id, is_active=True)
            if not products.exists():
                self.stderr.write(
                    self.style.ERROR(f'No active product found with ID {product_id}.')
                )
                return
        elif sku_filter:
            products = Product.objects.filter(gw_sku=sku_filter, is_active=True)
            if not products.exists():
                self.stderr.write(
                    self.style.ERROR(f'No active product found with SKU "{sku_filter}".')
                )
                return
        else:
            products = Product.objects.filter(is_active=True).order_by('gw_sku')

        if faction:
            products = products.filter(faction__name__iexact=faction)
            if not products.exists():
                self.stderr.write(
                    self.style.ERROR(
                        f'No active products found for faction "{faction}". '
                        'Check the faction name (e.g. "Orks", "Space Marines").'
                    )
                )
                return

        if category:
            products = products.filter(category__name__icontains=category)
            if not products.exists():
                self.stderr.write(
                    self.style.ERROR(
                        f'No active products found for category "{category}". '
                        'Use the full or partial name '
                        '(e.g. "paint", "40,000", "Age of Sigmar").'
                    )
                )
                return

        if batch_tag:
            products = products.filter(batch_tag=batch_tag)
            if not products.exists():
                self.stderr.write(
                    self.style.ERROR(
                        f'No active products found with batch_tag="{batch_tag}". '
                        'Check the tag value (e.g. "phase-2", "phase-3").'
                    )
                )
                return

        if limit:
            products = products[:limit]

        total = products.count()
        self.stdout.write(f'Processing {total} products...\n')

        # ── Counters ─────────────────────────────────────────────────────────
        success          = 0
        not_found        = 0
        errors           = 0
        skipped_override = 0
        api_calls_start  = ebay_api.api_calls_made
        index            = 0

        # ── Main loop ────────────────────────────────────────────────────────
        for index, product in enumerate(products, 1):
            override_label = (
                f'  (eBay search: "{product.ebay_search_name}")'
                if product.ebay_search_name else ''
            )
            self.stdout.write(f'[{index}/{total}] {product.name}{override_label}')

            # ── manual_url_override guard ─────────────────────────────────────
            try:
                existing_cp = CurrentPrice.objects.get(
                    product=product,
                    retailer=ebay_uk_retailer,
                )
                if existing_cp.manual_url_override:
                    self.stdout.write(
                        self.style.WARNING('  [manual override] URL is manually set — skipping.')
                    )
                    skipped_override += 1
                    continue
            except CurrentPrice.DoesNotExist:
                pass  # No existing entry — proceed to create one

            # Check daily call limit before each request
            if ebay_api.api_calls_made >= 4500:
                self.stdout.write(self.style.WARNING(
                    f'\nApproaching eBay daily limit '
                    f'({ebay_api.api_calls_made}/5000 calls). Stopping safely.'
                ))
                break

            # Retry logic — up to 3 attempts per product
            result     = None
            last_error = None
            for attempt in range(1, 4):
                try:
                    result = ebay_api.find_best_match_for_product(product)
                    break
                except EbayAPIError as exc:
                    last_error = exc
                    error_str  = str(exc).lower()
                    is_rate_limit = 'exceeded' in error_str or '10001' in error_str
                    is_auth_error = 'invalid application' in error_str or '11002' in error_str

                    if is_rate_limit:
                        self.stdout.write(self.style.ERROR(
                            '\n  eBay daily rate limit reached — stopping run.\n'
                            '  The limit resets at midnight Pacific Time.\n'
                            '  Run again tomorrow or after the reset.'
                        ))
                    elif is_auth_error:
                        self.stdout.write(self.style.ERROR(
                            '\n  eBay authentication failed — check your App ID.\n'
                            '  Set EBAY_APP_ID_PRODUCTION in your environment.'
                        ))
                    else:
                        self.stdout.write(
                            self.style.ERROR(f'  eBay API error (aborting product): {exc}')
                        )
                    break
                except RuntimeError as exc:
                    last_error = exc
                    self.stdout.write(
                        self.style.WARNING(f'  Attempt {attempt}/3 error: {exc}')
                    )
                    time.sleep(delay * 2)

            if last_error and result is None:
                error_str = str(last_error).lower()
                if 'exceeded' in error_str or '10001' in error_str:
                    break
                if 'invalid application' in error_str or '11002' in error_str:
                    break
                self.stdout.write(
                    self.style.ERROR(f'  Failed after 3 attempts: {last_error}')
                )
                errors += 1
                time.sleep(delay)
                continue

            # ── Save result ──────────────────────────────────────────────────
            if result:
                price         = result['total_cost']
                url           = _add_epn_params_uk(result['url'], campaign_id)
                shipping      = result['shipping']
                title_preview = (
                    result['title'][:70]
                    .encode('ascii', 'replace')
                    .decode('ascii')
                )
                desc_preview = (
                    result.get('short_description', '')[:120]
                    .encode('ascii', 'replace')
                    .decode('ascii')
                )

                self.stdout.write(
                    self.style.SUCCESS(
                        f'  £{price:.2f} (+ £{shipping:.2f} ship) — {title_preview}'
                    )
                )
                self.stdout.write(f'  URL: {url}')
                if desc_preview:
                    self.stdout.write(f'  Desc: {desc_preview}')

                if not dry_run:
                    CurrentPrice.objects.update_or_create(
                        product=product,
                        retailer=ebay_uk_retailer,
                        defaults={
                            'price':         price,
                            'url':           url,
                            'currency':      'GBP',
                            'in_stock':      True,
                            'not_available': False,
                            'shipping_cost': shipping,
                        },
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING('  [DRY RUN] Not saved to DB.')
                    )
                success += 1

            else:
                self.stdout.write(self.style.WARNING('  Not found on eBay UK.'))
                if debug:
                    _debug_search(ebay_api, product, self.stdout, self.style)
                if not dry_run:
                    CurrentPrice.objects.update_or_create(
                        product=product,
                        retailer=ebay_uk_retailer,
                        defaults={
                            'price':         None,
                            'url':           '',
                            'currency':      'GBP',
                            'in_stock':      False,
                            'not_available': True,
                        },
                    )
                not_found += 1

            time.sleep(delay)

        # ── Summary ──────────────────────────────────────────────────────────
        api_calls_used  = ebay_api.api_calls_made - api_calls_start
        calls_remaining = 5000 - ebay_api.api_calls_made

        self.stdout.write('\n' + '=' * 55)
        self.stdout.write(self.style.SUCCESS('Summary (eBay UK)'))
        self.stdout.write('=' * 55)
        self.stdout.write(f'  Products processed : {index}')
        self.stdout.write(
            self.style.SUCCESS(f'  Prices updated     : {success}')
        )
        self.stdout.write(
            self.style.WARNING(f'  Not found on eBay UK : {not_found}')
        )
        if skipped_override:
            self.stdout.write(
                self.style.WARNING(f'  Manual override    : {skipped_override} (skipped)')
            )
        if errors:
            self.stdout.write(
                self.style.ERROR(f'  Errors             : {errors}')
            )
        self.stdout.write(f'  API calls used     : {api_calls_used}')
        self.stdout.write(f'  Calls remaining    : ~{calls_remaining}/day')
        if dry_run:
            self.stdout.write(
                self.style.WARNING('\n  DRY RUN — no changes saved to database.')
            )
        self.stdout.write('=' * 55 + '\n')
