"""
Management command: check_amazon_stock
=======================================
Updates the in_stock flag for every Amazon CurrentPrice entry based on URL
presence AND a valid price — no scraping, no page fetching.

Rules:
  - Entries with manual_url_override=True are NEVER touched.
  - Entries with a valid Amazon URL AND price > 0  -> in_stock=True, not_available=False
  - Entries with a valid Amazon URL but price None/0 -> in_stock stays False, [no price] warning
    (URL was set manually but price hasn't been populated yet; showing $0 to
     users would be misleading — wait until a real price is known.)
  - Entries with an empty URL -> no change (no listing found yet)

This replaces the previous page-scraping approach, which was unreliable due
to Amazon bot-detection returning inconsistent results.

Usage:
    python manage.py check_amazon_stock
    python manage.py check_amazon_stock --dry-run   # print results, no DB writes
    python manage.py check_amazon_stock --sku 48-75 # single product by GW SKU
"""

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Retailer


class Command(BaseCommand):
    """Mark Amazon listings as in_stock=True when a URL is present."""

    help = (
        'Updates Amazon in_stock flags based on URL presence. '
        'Entries with manual_url_override=True are never modified.'
    )

    def add_arguments(self, parser):
        """Add optional --dry-run and --sku flags."""
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Print results without writing to the database.',
        )
        parser.add_argument(
            '--sku',
            type=str,
            default='',
            help='Only check the product with this GW SKU (e.g. 48-75).',
        )

    def handle(self, *args, **options):
        """Apply URL-presence stock logic to all eligible Amazon entries."""
        dry_run = options['dry_run']
        sku_filter = options['sku'].strip()

        try:
            amazon = Retailer.objects.get(slug='amazon')
        except Retailer.DoesNotExist:
            self.stderr.write(self.style.ERROR("Retailer 'amazon' not found in DB."))
            return

        qs = CurrentPrice.objects.filter(
            retailer=amazon,
            manual_url_override=False,   # never touch manually-set entries
        ).select_related('product')

        if sku_filter:
            qs = qs.filter(product__gw_sku=sku_filter)

        entries = list(qs)
        total = len(entries)

        if total == 0:
            self.stdout.write('No Amazon CurrentPrice entries to check.')
            return

        mode = 'DRY-RUN ' if dry_run else ''
        self.stdout.write(f'{mode}Checking {total} Amazon listing(s)...\n')

        marked_in_stock = 0
        already_correct = 0
        no_url_count = 0
        no_price_count = 0

        for cp in entries:
            name = cp.product.name
            sku = cp.product.gw_sku or '-'
            has_url = bool(cp.url and 'amazon.com' in cp.url)
            has_price = cp.price is not None and cp.price > 0

            if not has_url:
                self.stdout.write(
                    self.style.WARNING(f'  [no url]   {name} ({sku}) -- no Amazon URL')
                )
                no_url_count += 1

            elif not has_price:
                # URL present but price is missing or zero — a manually-set URL
                # hasn't had its price populated yet.  Do NOT mark in_stock=True:
                # showing $0.00 "in stock" on the site is worse than showing
                # nothing.  Leave in_stock=False until a real price is known.
                self.stdout.write(
                    self.style.WARNING(
                        f'  [no price] {name} ({sku}) -- URL set but price missing '
                        f'(price={cp.price}); skipping in_stock update'
                    )
                )
                no_price_count += 1

            else:
                if cp.in_stock and not cp.not_available:
                    self.stdout.write(f'  [ok]       {name} ({sku})')
                    already_correct += 1
                else:
                    self.stdout.write(
                        self.style.SUCCESS(f'  [in_stock] {name} ({sku})')
                    )
                    marked_in_stock += 1
                    if not dry_run:
                        CurrentPrice.objects.filter(pk=cp.pk).update(
                            in_stock=True,
                            not_available=False,
                        )

        self.stdout.write(self.style.SUCCESS(
            f'\n{"[DRY-RUN] " if dry_run else ""}'
            f'Done -- '
            f'Marked in stock: {marked_in_stock}  |  '
            f'Already correct: {already_correct}  |  '
            f'No URL: {no_url_count}  |  '
            f'No price (skipped): {no_price_count}'
        ))
