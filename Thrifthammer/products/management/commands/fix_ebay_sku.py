"""
Management command: fix_ebay_sku

Adds negative keywords to a SKU AND immediately re-scrapes eBay for that SKU
in one atomic step — preventing the most common mistake of updating keywords
but forgetting to run the live eBay update, leaving stale URLs in the DB.

Usage:
    # Add keyword and re-scrape immediately (dry run first to verify)
    python manage.py fix_ebay_sku --sku 01-07 --add-keywords "vertus praetor"

    # Skip the dry-run preview and go straight to live update
    python manage.py fix_ebay_sku --sku 01-07 --add-keywords "vertus" --no-preview

    # Just re-scrape without changing keywords (useful to force-refresh a SKU)
    python manage.py fix_ebay_sku --sku 48-23 --rescrape-only

    # View current keywords for a SKU without changing anything
    python manage.py fix_ebay_sku --sku 56-14 --show
"""

from django.core.management.base import BaseCommand, CommandError

from products.models import Product


class Command(BaseCommand):
    """Add eBay negative keywords to a SKU and immediately re-scrape."""

    help = (
        'Add eBay negative keywords to a SKU and immediately re-scrape eBay '
        'to replace any stale URL/price in the DB.'
    )

    def add_arguments(self, parser):
        """Define CLI arguments."""
        parser.add_argument(
            '--sku',
            required=True,
            help='GW SKU to update (e.g. 01-07)',
        )
        parser.add_argument(
            '--add-keywords',
            default='',
            help='Space-separated keywords to append to ebay_negative_keywords',
        )
        parser.add_argument(
            '--no-preview',
            action='store_true',
            default=False,
            help='Skip dry-run preview and go straight to live update',
        )
        parser.add_argument(
            '--rescrape-only',
            action='store_true',
            default=False,
            help='Re-scrape eBay without changing any keywords',
        )
        parser.add_argument(
            '--show',
            action='store_true',
            default=False,
            help='Print current keyword settings and exit',
        )

    def handle(self, *args, **options):
        """Execute the command."""
        sku = options['sku'].strip()
        new_keywords = options['add_keywords'].strip().lower().split()

        try:
            product = Product.objects.get(gw_sku=sku)
        except Product.DoesNotExist:
            raise CommandError(f'No product found with gw_sku="{sku}"')

        # --show mode: just print current state
        if options['show']:
            self.stdout.write(f'Product : {product.name}')
            self.stdout.write(f'SKU     : {product.gw_sku}')
            self.stdout.write(f'Search  : "{product.ebay_search_name or "(auto)"}"')
            self.stdout.write(f'Neg KWs : "{product.ebay_negative_keywords or "(none)"}"')
            return

        # Step 1 — Add new keywords (deduplicated)
        if new_keywords and not options['rescrape_only']:
            existing = (product.ebay_negative_keywords or '').lower().split()
            to_add = [kw for kw in new_keywords if kw not in existing]
            if to_add:
                current = (product.ebay_negative_keywords or '').strip()
                product.ebay_negative_keywords = (current + ' ' + ' '.join(to_add)).strip()
                product.save(update_fields=['ebay_negative_keywords'])
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Added keywords: {to_add}\n'
                        f'  Now: "{product.ebay_negative_keywords}"'
                    )
                )
            else:
                self.stdout.write(f'All keywords already present: {new_keywords}')
        elif options['rescrape_only']:
            self.stdout.write(f'Rescraping {product.name} without keyword changes.')

        # Step 2 — Dry-run preview (unless --no-preview)
        if not options['no_preview']:
            self.stdout.write('\n--- DRY RUN PREVIEW ---')
            from django.core.management import call_command
            call_command('update_ebay_prices', sku=sku, dry_run=True)
            self.stdout.write('\nLooks good? Running live update now...\n')

        # Step 3 — Live eBay update for this SKU
        from django.core.management import call_command
        call_command('update_ebay_prices', sku=sku)

        self.stdout.write(
            self.style.SUCCESS(
                f'\nDone -- {product.name} eBay price updated live. '
                f'Cache busted. Website will reflect the new listing immediately.'
            )
        )
