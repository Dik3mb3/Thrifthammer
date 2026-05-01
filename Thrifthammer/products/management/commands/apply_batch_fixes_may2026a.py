"""
Fallback Amazon prices for SKUs that the browser scraper cannot reliably
price-extract (no_price / unavailable status).

These are set ONLY when the existing CurrentPrice record is marked
not_available=True (meaning the last scrape failed).  If the batch
scraper successfully finds a live price in a future run, the importer's
update_or_create will take precedence and this command becomes a no-op
for that SKU — so automatic price updates continue to work normally.

SKUs handled here
-----------------
43-04  Angron            $144.50  — scraper returns no_price (selector miss)
97-08  Bloodletters       $45.95  — scraper returns no_price (selector miss)
56-06  Fire Warriors (T'au) $51.00 — old ASIN B07G8N6HJ8 is discontinued;
                                     updated to B09SBXJ53W in the scraper

Usage:
    python manage.py apply_batch_fixes_may2026a
    python manage.py apply_batch_fixes_may2026a --dry-run
"""

import decimal

from django.core.management.base import BaseCommand, CommandError

from prices.models import CurrentPrice
from products.models import Product, Retailer

# ---------------------------------------------------------------------------
# Fallback prices — only applied when the record is currently not_available.
# sku → (fallback_price, amazon_url)
# ---------------------------------------------------------------------------
FALLBACK_PRICES = {
    # Angron — page loads but price selector doesn't match layout
    '43-04': ('144.50', 'https://www.amazon.com/dp/B0BTDDDLD5'),
    # Bloodletters — same selector-miss issue
    '97-08': ('45.95',  'https://www.amazon.com/dp/B0DHXCGWN7'),
    # Fire Warriors — old ASIN (B07G8N6HJ8) discontinued; new ASIN B09SBXJ53W
    '56-06': ('51.00',  'https://www.amazon.com/dp/B09SBXJ53W'),
}


class Command(BaseCommand):
    """Set fallback Amazon prices for SKUs the scraper cannot currently price."""

    help = (
        'Apply fallback Amazon prices for SKUs where the scraper returns '
        'no_price or unavailable.  Only updates records that are currently '
        'marked not_available=True, so successful automatic scrapes always win.'
    )

    def add_arguments(self, parser):
        """Register --dry-run flag."""
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Preview changes without writing to the database.',
        )

    def handle(self, *args, **options):
        """Execute fallback price updates."""
        dry_run = options['dry_run']

        try:
            amazon = Retailer.objects.get(name='Amazon')
        except Retailer.DoesNotExist:
            raise CommandError("Retailer 'Amazon' not found in the database.")

        applied = 0
        skipped = 0

        for sku, (price_str, url) in FALLBACK_PRICES.items():
            product = Product.objects.filter(gw_sku=sku, is_active=True).first()
            if not product:
                self.stdout.write(self.style.WARNING(
                    f'  [skip] {sku} — not in active products'
                ))
                skipped += 1
                continue

            existing = CurrentPrice.objects.filter(
                product=product, retailer=amazon,
            ).first()

            if existing is not None and not existing.not_available:
                # A live (not_available=False) price already exists — the batch
                # scraper has successfully updated this SKU; leave it alone.
                self.stdout.write(
                    f'  [ok]   {sku} {product.name} — already available '
                    f'(${existing.price}), skipping fallback'
                )
                skipped += 1
                continue

            price = decimal.Decimal(price_str)
            action = 'create' if existing is None else 'restore'
            self.stdout.write(
                f'  [{"dry " if dry_run else ""}{action}] '
                f'{sku} {product.name} → ${price}'
            )

            if not dry_run:
                CurrentPrice.objects.update_or_create(
                    product=product,
                    retailer=amazon,
                    defaults={
                        'price':         price,
                        'url':           url,
                        'in_stock':      True,
                        'not_available': False,
                    },
                )
            applied += 1

        label = '[DRY RUN] ' if dry_run else ''
        self.stdout.write(self.style.SUCCESS(
            f'\n{label}Done — {applied} fallback prices applied, '
            f'{skipped} skipped (live price exists or product not found).'
        ))
