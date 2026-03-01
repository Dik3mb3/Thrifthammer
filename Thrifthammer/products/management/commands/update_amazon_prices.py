"""
Management command: update_amazon_prices

Fetches live Amazon prices using the Product Advertising API (PA-API) 5.0
for all active products that have an Amazon URL stored in CurrentPrice.

Extracts ASINs from stored Amazon URLs, batches them into PA-API GetItems
calls (up to 10 ASINs per call), and updates CurrentPrice records.

Prerequisites:
  1. You must have an active Amazon Associates account
  2. Your account must have made qualifying sales recently (PA-API requirement)
  3. Set environment variables:
       AMAZON_ACCESS_KEY   — from Associates/PA-API portal
       AMAZON_SECRET_KEY   — from Associates/PA-API portal
       AMAZON_PARTNER_TAG  — your Associates tag (e.g. thrifthammer-21)
       AMAZON_REGION       — us-east-1 (default, for Amazon.com)

Getting PA-API credentials:
  1. Go to https://affiliate-program.amazon.com/
  2. Sign in to your Associates account
  3. Go to Tools → Product Advertising API
  4. Request access / view your credentials

Usage:
    # Dry run — see what would be updated without saving:
    python manage.py update_amazon_prices --dry-run

    # Full run:
    python manage.py update_amazon_prices

    # Test with a subset of products:
    python manage.py update_amazon_prices --limit 20

    # Update a single product by DB ID:
    python manage.py update_amazon_prices --product 42

Notes:
    - Only products with an Amazon URL already stored in CurrentPrice will
      be processed. Run import_prices first to load Amazon URLs from CSV.
    - Rate limit: ~1 call/second (10 ASINs/call = ~10 products/second)
    - ASINs that return no data are marked not_available=True
    - Daily call limits scale with your Associates activity
"""

import time

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Product, Retailer
from products.amazon_api_client import AmazonPAAPI, AmazonAPIError


class Command(BaseCommand):
    """
    Fetch live Amazon prices using PA-API 5.0.

    Updates CurrentPrice records for the Amazon retailer. Requires Amazon
    URLs to already be stored — run import_prices first to load them.
    """

    help = 'Update product prices from Amazon using PA-API 5.0.'

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
            '--region',
            type=str,
            default=None,
            metavar='REGION',
            help='AWS region override (e.g. us-east-1, eu-west-1). Defaults to AMAZON_REGION setting.',
        )

    def handle(self, *args, **options):
        """Entry point — run the Amazon price update."""
        limit      = options['limit']
        product_id = options['product']
        dry_run    = options['dry_run']
        region     = options['region']

        # ── Configuration summary ────────────────────────────────────────────
        self.stdout.write('\nAmazon PA-API 5.0 — Price Update')
        self.stdout.write('=' * 55)
        self.stdout.write(f'  Dry run    : {dry_run}')
        if limit:
            self.stdout.write(f'  Limit      : {limit} products')
        if product_id:
            self.stdout.write(f'  Product ID : {product_id}')
        if region:
            self.stdout.write(f'  Region     : {region}')
        self.stdout.write('=' * 55 + '\n')

        # ── Initialise API client ────────────────────────────────────────────
        try:
            kwargs = {}
            if region:
                kwargs['region'] = region
            amazon_api = AmazonPAAPI(**kwargs)
        except ValueError as exc:
            self.stderr.write(self.style.ERROR(f'Configuration error: {exc}'))
            self.stderr.write(
                'Follow the setup steps in the command docstring to get '
                'Amazon PA-API credentials.'
            )
            return

        # ── Get Amazon retailer ──────────────────────────────────────────────
        try:
            amazon_retailer = Retailer.objects.get(slug='amazon')
        except Retailer.DoesNotExist:
            self.stderr.write(
                self.style.ERROR(
                    'Amazon retailer not found in DB. '
                    'Run import_prices with Amazon rows first.'
                )
            )
            return

        # ── Get CurrentPrice records with Amazon URLs ────────────────────────
        qs = CurrentPrice.objects.filter(
            retailer=amazon_retailer,
        ).exclude(
            url='',
        ).select_related('product')

        if product_id:
            qs = qs.filter(product__id=product_id)

        if limit:
            qs = qs[:limit]

        price_records = list(qs)
        total = len(price_records)

        if total == 0:
            self.stdout.write(
                self.style.WARNING(
                    'No Amazon price records with URLs found. '
                    'Run import_prices --retailer Amazon first to load Amazon URLs.'
                )
            )
            return

        self.stdout.write(f'Found {total} Amazon price records with URLs.\n')

        # ── Build ASIN → CurrentPrice mapping ────────────────────────────────
        asin_to_record = {}
        skipped_no_asin = 0

        for record in price_records:
            asin = amazon_api.extract_asin_from_url(record.url)
            if asin:
                asin_to_record[asin] = record
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f'  [no asin] {record.product.name} — could not extract '
                        f'ASIN from: {record.url[:70]}'
                    )
                )
                skipped_no_asin += 1

        asins = list(asin_to_record.keys())
        self.stdout.write(
            f'Extracted {len(asins)} valid ASINs '
            f'({skipped_no_asin} skipped — no ASIN in URL).\n'
        )

        # ── Fetch prices from PA-API ─────────────────────────────────────────
        self.stdout.write('Fetching prices from Amazon PA-API...\n')

        results = amazon_api.get_prices_for_asins(asins)

        # ── Process results ──────────────────────────────────────────────────
        updated    = 0
        not_found  = 0
        errors     = 0

        for asin, record in asin_to_record.items():
            product = record.product
            result = results.get(asin)

            if result:
                price    = result['price']
                in_stock = result['in_stock']
                title    = result.get('title', '')[:60]
                url      = result.get('url', record.url)  # Use affiliate URL from API

                price_display = f'£{price:.2f}' if price else '(no price)'
                stock_display = 'in stock' if in_stock else 'out of stock'
                self.stdout.write(
                    self.style.SUCCESS(
                        f'  {product.gw_sku:8s}  {price_display:10s}  '
                        f'{stock_display:12s}  {title}'
                    )
                )

                if not dry_run:
                    defaults = {
                        'in_stock':      in_stock,
                        'not_available': False,
                        'url':           url,
                    }
                    if price is not None:
                        defaults['price'] = price

                    try:
                        CurrentPrice.objects.update_or_create(
                            product=product,
                            retailer=amazon_retailer,
                            defaults=defaults,
                        )
                    except Exception as exc:  # noqa: BLE001
                        self.stdout.write(
                            self.style.ERROR(
                                f'  DB error for {product.gw_sku}: {exc}'
                            )
                        )
                        errors += 1
                        continue

                updated += 1

            else:
                self.stdout.write(
                    self.style.WARNING(
                        f'  {product.gw_sku:8s}  Not found on Amazon (ASIN: {asin})'
                    )
                )
                if not dry_run:
                    CurrentPrice.objects.filter(
                        product=product,
                        retailer=amazon_retailer,
                    ).update(
                        in_stock=False,
                        not_available=True,
                    )
                not_found += 1

        # ── Summary ──────────────────────────────────────────────────────────
        self.stdout.write('\n' + '=' * 55)
        self.stdout.write(self.style.SUCCESS('Summary'))
        self.stdout.write('=' * 55)
        self.stdout.write(f'  Products processed : {len(asins)}')
        self.stdout.write(
            self.style.SUCCESS(f'  Prices updated     : {updated}')
        )
        if not_found:
            self.stdout.write(
                self.style.WARNING(f'  Not found on Amazon: {not_found}')
            )
        if skipped_no_asin:
            self.stdout.write(
                self.style.WARNING(f'  No ASIN in URL     : {skipped_no_asin}')
            )
        if errors:
            self.stdout.write(
                self.style.ERROR(f'  Errors             : {errors}')
            )
        self.stdout.write(
            f'  PA-API calls made  : {amazon_api.api_calls_made}'
        )
        if dry_run:
            self.stdout.write(
                self.style.WARNING('\n  DRY RUN — no changes saved to database.')
            )
        self.stdout.write('=' * 55 + '\n')
