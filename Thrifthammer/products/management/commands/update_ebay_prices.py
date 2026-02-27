"""
Management command: update_ebay_prices

Fetches live eBay prices for all active products using the official
eBay Finding API v1.0.0. Saves results to the CurrentPrice model.

Compliance:
  - Uses official eBay Finding API (not scraping)
  - Respects 5,000 calls/day limit
  - Links to viewItemURL provided by eBay API
  - Attributes eBay as price source

Usage:
    # Test with sandbox (fake data, confirms API works):
    python manage.py update_ebay_prices --sandbox --limit 5

    # Dry run with production (real data, no DB saves):
    python manage.py update_ebay_prices --limit 10 --dry-run

    # Full production run (all products):
    python manage.py update_ebay_prices

    # Single product by ID:
    python manage.py update_ebay_prices --product 42

    # Custom delay between calls:
    python manage.py update_ebay_prices --delay 1.0
"""

import time
from decimal import Decimal

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils.text import slugify

from prices.models import CurrentPrice
from products.models import Product, Retailer
from products.ebay_api_client import EbayFindingAPI, EbayAPIError


class Command(BaseCommand):
    """
    Fetch live eBay prices using the official Finding API.

    Updates CurrentPrice records for the eBay retailer. Products not
    found on eBay are marked not_available=True (never silently skipped).
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

    def handle(self, *args, **options):
        """Entry point — run the eBay price update."""
        use_sandbox = options['sandbox']
        limit = options['limit']
        delay = options['delay']
        product_id = options['product']
        dry_run = options['dry_run']

        # ── Configuration summary ────────────────────────────────────────────
        env_label = 'SANDBOX (fake data)' if use_sandbox else 'PRODUCTION'
        self.stdout.write('\neBay Finding API — Price Update')
        self.stdout.write('=' * 50)
        self.stdout.write(f'  Environment : {env_label}')
        self.stdout.write(f'  Delay       : {delay}s between calls')
        self.stdout.write(f'  Dry run     : {dry_run}')
        if limit:
            self.stdout.write(f'  Limit       : {limit} products')
        if product_id:
            self.stdout.write(f'  Product ID  : {product_id}')
        self.stdout.write('=' * 50 + '\n')

        # ── Initialise API client ────────────────────────────────────────────
        try:
            ebay_api = EbayFindingAPI(use_sandbox=use_sandbox)
        except ValueError as exc:
            self.stderr.write(self.style.ERROR(f'Configuration error: {exc}'))
            self.stderr.write(
                'Add EBAY_APP_ID_PRODUCTION to your Railway environment variables.'
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
        else:
            products = Product.objects.filter(is_active=True).order_by('gw_sku')

        if limit:
            products = products[:limit]

        total = products.count()
        self.stdout.write(f'Processing {total} products...\n')

        # ── Counters ─────────────────────────────────────────────────────────
        success = 0
        not_found = 0
        errors = 0
        api_calls_start = ebay_api.api_calls_made

        # ── Main loop ────────────────────────────────────────────────────────
        for index, product in enumerate(products, 1):
            self.stdout.write(f'[{index}/{total}] {product.name}')

            # Check daily call limit before each request
            if ebay_api.api_calls_made >= 4500:
                self.stdout.write(self.style.WARNING(
                    f'\nApproaching eBay daily limit '
                    f'({ebay_api.api_calls_made}/5000 calls). Stopping safely.'
                ))
                break

            # Retry logic — up to 3 attempts per product
            result = None
            last_error = None
            for attempt in range(1, 4):
                try:
                    result = ebay_api.find_best_match_for_product(product)
                    break
                except EbayAPIError as exc:
                    last_error = exc
                    self.stdout.write(
                        self.style.WARNING(
                            f'  Attempt {attempt}/3 failed: {exc}'
                        )
                    )
                    time.sleep(delay * 2)
                except RuntimeError as exc:
                    last_error = exc
                    self.stdout.write(
                        self.style.WARNING(
                            f'  Attempt {attempt}/3 error: {exc}'
                        )
                    )
                    time.sleep(delay * 2)

            if last_error and result is None:
                self.stdout.write(
                    self.style.ERROR(f'  Failed after 3 attempts: {last_error}')
                )
                errors += 1
                time.sleep(delay)
                continue

            # ── Save result ──────────────────────────────────────────────────
            if result:
                price = result['total_cost']
                url = result['url']
                title_preview = result['title'][:55]

                self.stdout.write(
                    self.style.SUCCESS(
                        f'  ${price:.2f} — {title_preview}...'
                    )
                )

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
