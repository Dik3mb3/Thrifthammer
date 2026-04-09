"""
Management command: fetch_corsair_prices

Fetches live prices for the 6 new 2026 Aeldari Corsair products from
Amazon, Noble Knight Games, and Miniature Market.

Bypasses the usual full-scraper run (which processes hundreds of products
at 2s+ per request) and targets only these 6 products directly.

Also works around the MM scraper's non-numeric GW SKU skip — these products
have P-240xxx SKUs which the normal MM scraper would skip automatically.

Usage:
    python manage.py fetch_corsair_prices
    python manage.py fetch_corsair_prices --dry-run
"""

import logging
import time

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Product, Retailer

logger = logging.getLogger(__name__)

SLUGS = [
    'aeldari-corsair-skyreavers',
    'aeldari-corsair-voidreavers',
    'aeldari-prince-yriel',
    'aeldari-kharseth',
    'aeldari-vyper',
    'combat-patrol-aeldari-corsairs',
]


def _fetch_amazon(entries, dry_run, stdout):
    """Fetch Amazon prices using the existing AmazonScraper internals."""
    from scrapers.retailers.amazon import AmazonScraper
    scraper = AmazonScraper()
    scraper._make_fresh_session()

    updated = 0
    for entry in entries:
        url = entry.url
        if not url or 'amazon' not in url:
            stdout.write(f'  [amazon] SKIP {entry.product.name} — no URL')
            continue

        stdout.write(f'  [amazon] Fetching {entry.product.name}...')
        result = scraper._fetch_price(url)

        if result is None:
            # one retry
            time.sleep(4)
            result = scraper._fetch_price(url)

        if result is None:
            stdout.write(f'    -> no price extracted (blocked or not listed yet)')
        else:
            price, in_stock = result
            stock = 'in stock' if in_stock else 'OOS'
            stdout.write(f'    -> ${price}  {stock}')
            if not dry_run:
                entry.price = price
                entry.in_stock = in_stock
                entry.not_available = False
                entry.save(update_fields=['price', 'in_stock', 'not_available'])
                updated += 1

        time.sleep(2)

    return updated


def _fetch_nk(entries, dry_run, stdout):
    """Fetch Noble Knight prices using the existing NKScraper internals."""
    from scrapers.retailers.noble_knight import NoblekKnightScraper, _FETCH_ERROR
    scraper = NoblekKnightScraper()

    updated = 0
    for entry in entries:
        url = entry.url
        if not url or 'nobleknight' not in url:
            stdout.write(f'  [nk] SKIP {entry.product.name} — no URL')
            continue

        # Strip affiliate param before fetching
        fetch_url = url.split('?awid=')[0].split('&awid=')[0]

        stdout.write(f'  [nk] Fetching {entry.product.name}...')
        result = scraper._fetch_price(fetch_url)

        if result is _FETCH_ERROR:
            time.sleep(3)
            result = scraper._fetch_price(fetch_url)

        if result is _FETCH_ERROR or result is None:
            stdout.write(f'    -> no price extracted')
        else:
            price, in_stock = result
            stock = 'in stock' if in_stock else 'OOS'
            stdout.write(f'    -> ${price}  {stock}')
            if not dry_run:
                entry.price = price
                entry.in_stock = in_stock
                entry.not_available = False
                entry.save(update_fields=['price', 'in_stock', 'not_available'])
                updated += 1

        time.sleep(1.5)

    return updated


def _fetch_mm(products_and_entries, dry_run, stdout):
    """
    Fetch Miniature Market prices via their suggest search endpoint.

    The standard MM scraper skips non-numeric GW SKUs (P-240xxx).
    This function calls _find_product() directly, bypassing that SKU check.
    """
    from scrapers.retailers.miniature_market import MiniatureMarketScraper
    scraper = MiniatureMarketScraper()

    updated = 0
    for product, entry in products_and_entries:
        stdout.write(f'  [mm] Searching for {product.name}...')
        result = scraper._find_product(product.name)

        if result is None:
            stdout.write(f'    -> not found on MM (pre-order or not listed yet)')
        else:
            price, in_stock, mm_url = result
            stock = 'in stock' if in_stock else 'OOS'
            full_url = (
                mm_url if mm_url.startswith('http')
                else f'https://www.miniaturemarket.com{mm_url}'
            )
            stdout.write(f'    -> ${price}  {stock}  {full_url}')
            if not dry_run:
                entry.price = price
                entry.in_stock = in_stock
                entry.not_available = False
                entry.url = full_url
                entry.save(update_fields=['price', 'in_stock', 'not_available', 'url'])
                updated += 1

        time.sleep(1)

    return updated


class Command(BaseCommand):
    """Fetch live prices for 2026 Aeldari Corsair products from 3 retailers."""

    help = (
        'Fetches live prices for Corsair Skyreavers, Voidreavers, Prince Yriel, '
        'Kharseth, Vyper, and Combat Patrol: Aeldari Corsairs from Amazon, '
        'Noble Knight Games, and Miniature Market.'
    )

    def add_arguments(self, parser):
        """Add --dry-run flag."""
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Print fetched prices without saving to DB.',
        )

    def handle(self, *args, **options):
        """Execute targeted price fetch for the 6 Corsair products."""
        dry_run = options['dry_run']
        if dry_run:
            self.stdout.write('=== DRY RUN — no DB writes ===\n')

        # Load products and their CurrentPrice entries for each retailer
        products = {
            p.slug: p
            for p in Product.objects.filter(slug__in=SLUGS, is_active=True)
        }
        if not products:
            self.stderr.write('No matching products found. Run populate_aeldari_phase3_products first.')
            return

        missing = [s for s in SLUGS if s not in products]
        if missing:
            self.stderr.write(f'Products not found: {", ".join(missing)}')

        amazon_r   = Retailer.objects.filter(name='Amazon').first()
        nk_r       = Retailer.objects.filter(name='Noble Knight Games').first()
        mm_r       = Retailer.objects.filter(name='Miniature Market').first()

        def get_entries(retailer):
            if not retailer:
                return []
            return list(
                CurrentPrice.objects
                .filter(product__slug__in=SLUGS, retailer=retailer)
                .select_related('product')
                .order_by('product__name')
            )

        amazon_entries = get_entries(amazon_r)
        nk_entries     = get_entries(nk_r)
        mm_entries     = get_entries(mm_r)
        mm_pairs       = [(e.product, e) for e in mm_entries]

        total = 0

        # ── Amazon ──────────────────────────────────────────────────────────────
        self.stdout.write('\nAmazon:')
        total += _fetch_amazon(amazon_entries, dry_run, self.stdout)

        # ── Noble Knight ────────────────────────────────────────────────────────
        self.stdout.write('\nNoble Knight Games:')
        total += _fetch_nk(nk_entries, dry_run, self.stdout)

        # ── Miniature Market ────────────────────────────────────────────────────
        self.stdout.write('\nMiniature Market:')
        total += _fetch_mm(mm_pairs, dry_run, self.stdout)

        if not dry_run:
            # Bust the cache for these product pages so changes show immediately.
            from django.core.cache import cache
            cache.clear()
            self.stdout.write('\nCache cleared.')
            self.stdout.write(
                self.style.SUCCESS(f'\nDone. {total} CurrentPrice records updated.')
            )
        else:
            self.stdout.write('\n(dry run — nothing saved)')
