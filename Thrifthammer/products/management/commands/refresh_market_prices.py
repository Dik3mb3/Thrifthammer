"""
Management command: refresh_market_prices

Recalculates the Average Market Price (Product.market_price) of every product
ticked uses_market_price: out-of-print products that have no MSRP.

Only US retailers count (UK retailers are skipped, so every price is USD).

How the number is worked out:
  * First calculation (market_price still empty): the median of the prices US
    retailers show today, meaning CurrentPrice rows that have a price, are in
    stock and are available.
  * Every later calculation: the median over the last --window-days days
    (default 90) of PriceHistory. Each retailer counts once for every day it
    had an in-stock price, using the last price it recorded on or before that
    day. History is only written when a price changes, so a price that stood
    for 40 days counts 40 times.
  * Each way falls back to the other when it finds nothing. If both find
    nothing the stored value is left as it is and the product is reported.

Only Product.market_price is ever written. The page cache is not cleared here;
product pages pick up a new value when their cache entry expires.

Usage:
    python manage.py refresh_market_prices
    python manage.py refresh_market_prices --dry-run
    python manage.py refresh_market_prices --skus WBG-001,WBG-002
    python manage.py refresh_market_prices --window-days 60
"""

import datetime
import statistics
from decimal import ROUND_HALF_UP, Decimal

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from prices.models import CurrentPrice, PriceHistory
from products.models import Product

DEFAULT_WINDOW_DAYS = 90
CENT = Decimal('0.01')


def current_prices(product):
    """Return the prices US retailers show today: priced, in stock and available."""
    return list(
        CurrentPrice.objects
        .filter(product=product, price__gt=0, in_stock=True, not_available=False)
        .exclude(retailer__is_uk=True)
        .values_list('price', flat=True)
    )


def history_by_retailer(product):
    """Return {retailer_id: [(day, price, in_stock), ...]}, oldest first, US retailers only."""
    rows = (
        PriceHistory.objects
        .filter(product=product)
        .exclude(retailer__is_uk=True)
        .order_by('retailer_id', 'recorded_at')
        .values_list('retailer_id', 'recorded_at', 'price', 'in_stock')
    )
    grouped = {}
    for retailer_id, recorded_at, price, in_stock in rows:
        day = timezone.localtime(recorded_at).date()
        grouped.setdefault(retailer_id, []).append((day, price, in_stock))
    return grouped


def retailer_days(records, first_day, last_day):
    """
    Walk one retailer's price changes day by day from first_day to last_day and
    return the price of every day on which it had an in-stock price. The price
    of a day is the last one recorded on or before that day, so a change made
    before first_day still counts for the days after it.
    """
    prices = []
    latest = -1  # index of the newest record on or before the day being walked
    day = first_day
    while day <= last_day:
        while latest + 1 < len(records) and records[latest + 1][0] <= day:
            latest += 1
        if latest >= 0:
            _, price, in_stock = records[latest]
            if in_stock and price > 0:
                prices.append(price)
        day += datetime.timedelta(days=1)
    return prices


def window_prices(product, window_days, today):
    """Return every retailer-day price over the last window_days days, ending today."""
    first_day = today - datetime.timedelta(days=window_days - 1)
    samples = []
    for records in history_by_retailer(product).values():
        samples.extend(retailer_days(records, first_day, today))
    return samples


def median_price(values):
    """Return the median of the prices rounded to whole cents, or None when there are none."""
    if not values:
        return None
    return Decimal(statistics.median(values)).quantize(CENT, rounding=ROUND_HALF_UP)


def compute_market_price(product, window_days, today):
    """
    Return (price, source, count) for a product: source is 'today' or 'history'
    and count is how many prices the median was taken over. Returns
    (None, None, 0) when neither way finds a US retailer price.
    """
    ways = [
        ('today', lambda: current_prices(product)),
        ('history', lambda: window_prices(product, window_days, today)),
    ]
    if product.market_price is not None:
        ways.reverse()  # already calculated once: the history window comes first
    for source, find in ways:
        values = find()
        price = median_price(values)
        if price is not None:
            return price, source, len(values)
    return None, None, 0


class Command(BaseCommand):
    """Refresh Product.market_price for every product ticked uses_market_price."""

    help = 'Recalculate the Average Market Price of out-of-print products (uses_market_price).'

    def add_arguments(self, parser):
        """Add the command line options."""
        parser.add_argument(
            '--dry-run', action='store_true', default=False,
            help='Show the new prices without saving them.',
        )
        parser.add_argument(
            '--skus', type=str, default='',
            help='Comma-separated gw_sku values to refresh (default: every ticked product).',
        )
        parser.add_argument(
            '--window-days', type=int, default=DEFAULT_WINDOW_DAYS,
            help=f'Days of price history the median covers (default {DEFAULT_WINDOW_DAYS}).',
        )

    def handle(self, *args, **options):
        """Recalculate each ticked product and save the ones whose price changed."""
        window_days = options['window_days']
        if window_days < 1:
            raise CommandError('--window-days must be at least 1.')
        dry_run = options['dry_run']
        products = self._products(options['skus'])
        today = timezone.localdate()

        changed = unchanged = no_data = 0
        for product in products:
            price, source, count = compute_market_price(product, window_days, today)
            if price is None:
                no_data += 1
                self.stdout.write(self.style.WARNING(
                    f'{product.gw_sku:<12} no US retailer price found, left at {product.market_price}'
                ))
            elif price == product.market_price:
                unchanged += 1
            else:
                changed += 1
                self.stdout.write(
                    f'{product.gw_sku:<12} {product.market_price} -> {price} '
                    f'({source}, {count} prices) {product.name[:50]}'
                )
                if not dry_run:
                    product.market_price = price
                    product.save(update_fields=['market_price'])

        verb = 'would change' if dry_run else 'changed'
        self.stdout.write(
            f'Done: {len(products)} product(s) | {verb}: {changed} | '
            f'unchanged: {unchanged} | no data: {no_data}'
        )

    def _products(self, skus):
        """Return the ticked products, limited to --skus when given (warning about unticked ones)."""
        products = Product.objects.filter(uses_market_price=True).order_by('gw_sku')
        if not skus:
            return list(products)
        wanted = [s.strip() for s in skus.split(',') if s.strip()]
        products = list(products.filter(gw_sku__in=wanted))
        for sku in sorted(set(wanted) - {p.gw_sku for p in products}):
            self.stdout.write(self.style.WARNING(
                f'{sku}: not found or not ticked uses_market_price, skipped'
            ))
        return products
