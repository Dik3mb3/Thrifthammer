"""
Management command: update_ebay_prices

Fetches live eBay prices for all active products using the official
eBay Browse API v1. Saves results to the CurrentPrice model.

Compliance:
  - Uses official eBay Browse API (not scraping)
  - Respects 5,000 calls/day limit
  - Links to viewItemURL provided by eBay API
  - Attributes eBay as price source

Rules:
  - CurrentPrice entries with manual_url_override=True are NEVER touched.
    (These are manually-curated URLs that must not be overwritten by the cron.)

Usage:
    # Test with sandbox (fake data, confirms API works):
    python manage.py update_ebay_prices --sandbox --limit 5

    # Dry run with production (real data, no DB saves):
    python manage.py update_ebay_prices --limit 10 --dry-run

    # Full production run (all products):
    python manage.py update_ebay_prices

    # Single product by DB ID:
    python manage.py update_ebay_prices --product 42

    # Single product by GW SKU:
    python manage.py update_ebay_prices --sku 01-07

    # Diagnose a "Not found" product (shows all eBay candidates + rejection reasons):
    python manage.py update_ebay_prices --sku 01-07 --debug --dry-run

    # Custom delay between calls:
    python manage.py update_ebay_prices --delay 1.0
"""

import shlex
import time
from decimal import Decimal

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils.text import slugify

from prices.models import CurrentPrice
from products.models import Product, Retailer
from products.ebay_api_client import EbayBrowseAPI, EbayAPIError


def _debug_search(ebay_api, product, stdout, style):
    """
    Print every eBay candidate for a product with pass/fail reason per filter.

    Used when --debug is active and a product returns "Not found" — shows
    exactly which filter rejected each listing so you can pinpoint false
    positives without adding logger.debug noise to normal runs.
    """
    from products.ebay_api_client import EbayBrowseAPI
    search_name = product.ebay_search_name or product.name
    raw_negatives = getattr(product, 'ebay_negative_keywords', '') or ''
    extra_negatives = shlex.split(raw_negatives) if raw_negatives else None
    query = EbayBrowseAPI._build_search_query(search_name, extra_negatives)
    stdout.write(f'    DEBUG query: "{query}"')

    try:
        items = ebay_api.search_items(query, max_results=10)
    except Exception as exc:
        stdout.write(style.ERROR(f'    DEBUG search error: {exc}'))
        return

    if not items:
        stdout.write(style.WARNING('    DEBUG: eBay returned 0 results'))
        return

    stdout.write(f'    DEBUG: {len(items)} results from eBay —')
    for i, item in enumerate(items, 1):
        title      = item.get('title', '')[:70]
        price      = item.get('total_cost', Decimal('0'))
        reasons    = EbayBrowseAPI._get_rejection_reasons(item, product)
        short_desc = item.get('short_description', '')[:100]
        if reasons:
            stdout.write(style.WARNING(f'      [{i}] FAIL  ${price:.2f}  "{title}"'))
            for r in reasons:
                stdout.write(f'           -> {r}')
        else:
            stdout.write(style.SUCCESS(f'      [{i}] PASS  ${price:.2f}  "{title}"'))
        if short_desc:
            stdout.write(f'           Desc: {short_desc}')


class Command(BaseCommand):
    """
    Fetch live eBay UK prices using the Browse API v1.

    Updates CurrentPrice records for the eBay retailer. Products not
    found on eBay are marked not_available=True (never silently skipped).

    The legacy Finding API was decommissioned in 2024. This command now
    uses the Browse API with OAuth 2.0 Client Credentials authentication.
    """

    help = 'Update product prices from eBay using the official Finding API.'

    def add_arguments(self, parser):
        """Register command-line arguments."""
        parser.add_argument(
            '--sandbox',
            action='store_true',
            default=False,
            help='Use eBay sandbox environment (test keys, fake data).',
        )
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
            '--list-overrides',
            action='store_true',
            default=False,
            help='Print all products that have an ebay_search_name override set, '
                 'then exit.  No API calls are made.',
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
            help='Filter to products with a specific batch_tag (e.g. "phase-2", "phase-3"). '
                 'Can be combined with --faction to target e.g. all phase-2 Ork products.',
        )

    def handle(self, *args, **options):
        """Entry point — run the eBay price update."""
        use_sandbox = options['sandbox']
        limit      = options['limit']
        delay      = options['delay']
        product_id = options['product']
        dry_run    = options['dry_run']
        faction    = options['faction']
        category   = options['category']
        debug      = options['debug']
        list_overrides = options['list_overrides']
        sku_filter = (options['sku'] or '').strip()
        batch_tag  = (options.get('batch_tag') or '').strip()

        # ── --list-overrides: print audit table and exit (no API calls) ──────
        if list_overrides:
            overrides = (
                Product.objects
                .filter(is_active=True)
                .exclude(ebay_search_name='')
                .order_by('faction__name', 'name')
                .values_list('gw_sku', 'name', 'ebay_search_name', 'faction__name')
            )
            if not overrides:
                self.stdout.write(self.style.WARNING('No eBay search name overrides are set.'))
                return
            self.stdout.write(f'\nProducts with eBay search name overrides ({len(overrides)}):')
            self.stdout.write(f'  {"SKU":<12}{"Display Name":<45}{"eBay Search Name":<35}Faction')
            self.stdout.write('  ' + '-' * 105)
            for sku, name, search_name, faction_name in overrides:
                faction_label = faction_name or '—'
                self.stdout.write(
                    f'  {sku:<12}{name:<45}{search_name:<35}{faction_label}'
                )
            self.stdout.write('')
            return

        # ── Configuration summary ────────────────────────────────────────────
        env_label = 'SANDBOX (fake data)' if use_sandbox else 'PRODUCTION'
        self.stdout.write('\neBay Browse API — Price Update')
        self.stdout.write('=' * 50)
        self.stdout.write(f'  Environment : {env_label}')
        self.stdout.write(f'  Delay       : {delay}s between calls')
        self.stdout.write(f'  Dry run     : {dry_run}')
        if debug:
            self.stdout.write(self.style.WARNING('  Debug       : ON (prints all eBay candidates for "Not found" products)'))
        if faction:
            self.stdout.write(f'  Faction     : {faction}')
        if category:
            self.stdout.write(f'  Category    : {category}')
        if batch_tag:
            self.stdout.write(f'  Batch tag   : {batch_tag}')
        if limit:
            self.stdout.write(f'  Limit       : {limit} products')
        if product_id:
            self.stdout.write(f'  Product ID  : {product_id}')
        if sku_filter:
            self.stdout.write(f'  SKU filter  : {sku_filter}')
        self.stdout.write('=' * 50 + '\n')

        # ── Initialise API client ────────────────────────────────────────────
        try:
            ebay_api = EbayBrowseAPI(use_sandbox=use_sandbox)
        except ValueError as exc:
            self.stderr.write(self.style.ERROR(f'Configuration error: {exc}'))
            self.stderr.write(
                'Add EBAY_APP_ID_PRODUCTION and EBAY_CERT_ID_PRODUCTION '
                'to your Railway environment variables.'
            )
            return

        # ── Get or create eBay retailer ──────────────────────────────────────
        ebay_retailer, created = Retailer.objects.get_or_create(
            slug='ebay',
            defaults={
                'name': 'eBay',
                'website': 'https://www.ebay.com',
                'country': 'US',
                'is_active': True,
            },
        )
        if created:
            self.stdout.write(self.style.SUCCESS('Created eBay retailer in DB.'))

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
            # Use iexact (case-insensitive exact match) rather than icontains
            # so that "--faction Space Marines" only returns the Space Marines
            # faction and does NOT accidentally match "Chaos Space Marines"
            # (which also contains the substring "Space Marines").
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
            # icontains so "--category paint" matches "Paint & Supplies" and
            # "--category 40" matches "Warhammer 40,000".
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
        success = 0
        not_found = 0
        errors = 0
        skipped_override = 0
        api_calls_start = ebay_api.api_calls_made

        # ── Main loop ────────────────────────────────────────────────────────
        for index, product in enumerate(products, 1):
            override_label = (
                f'  (eBay search: "{product.ebay_search_name}")'
                if product.ebay_search_name else ''
            )
            self.stdout.write(f'[{index}/{total}] {product.name}{override_label}')

            # ── manual_url_override guard ─────────────────────────────────────
            # If the existing eBay CurrentPrice entry was manually curated, skip it.
            # This protects URLs set via the admin or shell from being overwritten
            # by the daily automated cron (e.g. hard-to-find products, Celestian
            # Sacresants Amazon URL, etc.).
            try:
                existing_cp = CurrentPrice.objects.get(
                    product=product,
                    retailer=ebay_retailer,
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
            # EbayAPIError (rate limit, auth) aborts immediately — retrying
            # won't help and wastes limited daily API calls.
            result = None
            last_error = None
            for attempt in range(1, 4):
                try:
                    result = ebay_api.find_best_match_for_product(product)
                    break
                except EbayAPIError as exc:
                    last_error = exc
                    error_str = str(exc).lower()
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
                        self.style.WARNING(
                            f'  Attempt {attempt}/3 error: {exc}'
                        )
                    )
                    time.sleep(delay * 2)

            if last_error and result is None:
                error_str = str(last_error).lower()
                # Stop the entire run on rate limit or auth errors
                if 'exceeded' in error_str or '10001' in error_str:
                    break  # Already printed the message above
                if 'invalid application' in error_str or '11002' in error_str:
                    break  # Already printed the message above
                self.stdout.write(
                    self.style.ERROR(f'  Failed after 3 attempts: {last_error}')
                )
                errors += 1
                time.sleep(delay)
                continue

            # ── Save result ──────────────────────────────────────────────────
            if result:
                price         = result['total_cost']
                url           = result['url']
                shipping      = result['shipping']
                # Sanitise display strings to ASCII so Windows cp1252 terminals
                # don't crash on special chars (™, é, etc.) in eBay titles.
                # The raw values stored in the DB are never touched.
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
                    self.style.SUCCESS(f'  ${price:.2f} (+ ${shipping:.2f} ship) — {title_preview}')
                )
                # Always show the URL so you can verify the listing in dry-run mode
                self.stdout.write(f'  URL: {url}')
                # Show description excerpt if available (helps verify description matching)
                if desc_preview:
                    self.stdout.write(f'  Desc: {desc_preview}')

                if not dry_run:
                    CurrentPrice.objects.update_or_create(
                        product=product,
                        retailer=ebay_retailer,
                        defaults={
                            'price': price,
                            'url': url,
                            'in_stock': True,
                            'not_available': False,
                        },
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING('  [DRY RUN] Not saved to DB.')
                    )
                success += 1

            else:
                self.stdout.write(
                    self.style.WARNING('  Not found on eBay.')
                )
                if debug:
                    _debug_search(ebay_api, product, self.stdout, self.style)
                if not dry_run:
                    CurrentPrice.objects.update_or_create(
                        product=product,
                        retailer=ebay_retailer,
                        defaults={
                            'price': None,
                            'url': '',
                            'in_stock': False,
                            'not_available': True,
                        },
                    )
                not_found += 1

            time.sleep(delay)

        # ── Summary ──────────────────────────────────────────────────────────
        api_calls_used = ebay_api.api_calls_made - api_calls_start
        calls_remaining = 5000 - ebay_api.api_calls_made

        self.stdout.write('\n' + '=' * 50)
        self.stdout.write(self.style.SUCCESS('Summary'))
        self.stdout.write('=' * 50)
        self.stdout.write(f'  Products processed : {index}')
        self.stdout.write(
            self.style.SUCCESS(f'  Prices updated     : {success}')
        )
        self.stdout.write(
            self.style.WARNING(f'  Not found on eBay  : {not_found}')
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
        self.stdout.write('=' * 50 + '\n')
