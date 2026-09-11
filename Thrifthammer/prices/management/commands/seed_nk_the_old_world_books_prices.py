"""
Management command: seed_nk_the_old_world_books_prices

Seeds Noble Knight Games BookFormatPrice rows for the The Old World Books
batch (2 titles). No spreadsheet was used -- both titles were searched
directly on Noble Knight's site (nobleknight.com/Search?text=...), since a
2-title batch doesn't warrant the spreadsheet-cross-reference workflow used
for larger batches.

  - Grudge Bearer: confirmed live match -- MFG Part # GAWBL3283 (matches the
    "GWBL3283" item number seen on other retailers for this exact 2026
    printing), Author Gav Thorpe, Publish Year 2026, Type Novel - Softcover,
    MINT/New, in stock.
  - The Rise of Nagash: NOT included. Searched by title, by "Mike Lee
    Nagash", by its own ISBN (9781836092001), and by GW's MPN
    (60102781005) -- every query resolves to the same single Noble Knight
    catalog entry, which is a broken/unpublished stub (product link
    "/P/0/", no title, author, image, or type populated, permanently
    listed Out of Stock). Treated as genuinely not carried rather than
    seeded against unusable data, per the project's no-fabrication rule.

Not added to the Procfile -- run manually, on demand, same as the other
one-time seed commands introduced for the Books feature.

Usage:
    python manage.py seed_nk_the_old_world_books_prices
"""

from django.core.management.base import BaseCommand, CommandError

from prices.models import BookFormatPrice
from products.models import Product, Retailer

NK_AWID = '1576'

# (gw_sku, format, listing_title, price_or_None, url, in_stock)
NK_PRICES = [
    ('BOOK-TOW-001', 'softback', 'Grudge Bearer', 16.49, 'https://www.nobleknight.com/P/2148426683/Grudge-Bearer', True),
]


class Command(BaseCommand):
    """Seed Noble Knight BookFormatPrice rows for the The Old World Books batch."""

    help = 'Seeds verified Noble Knight Games prices for The Old World Books. Idempotent.'

    def handle(self, *args, **options):
        """Run the command."""
        nk_retailer = Retailer.objects.filter(slug='noble-knight-games').first()
        if not nk_retailer:
            raise CommandError('Noble Knight Games retailer not found.')

        created = updated = 0

        for gw_sku, fmt, listing_title, price, url, in_stock in NK_PRICES:
            try:
                product = Product.objects.get(gw_sku=gw_sku)
            except Product.DoesNotExist:
                self.stderr.write(self.style.ERROR(f'Product not found: {gw_sku}'))
                continue

            affiliate_url = f'{url}?awid={NK_AWID}'

            bfp, was_created = BookFormatPrice.objects.update_or_create(
                product=product,
                retailer=nk_retailer,
                format=fmt,
                defaults={
                    'price': price,
                    'currency': 'USD',
                    'url': affiliate_url,
                    'listing_title': listing_title,
                    'in_stock': in_stock,
                    'not_available': False,
                },
            )
            if was_created:
                created += 1
            else:
                updated += 1

            status = f'${price:.2f}' if price is not None else ('out of stock' if not in_stock else 'in stock, no price')
            self.stdout.write(
                f"  {'Created' if was_created else 'Updated'}: {product.name} ({bfp.get_format_display()}) - {status}"
            )

        self.stdout.write(self.style.SUCCESS(
            f'\nDone. {created} created, {updated} updated.'
        ))
