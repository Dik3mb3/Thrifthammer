"""
Management command: seed_nk_warmachine_dark_operations_prices

Seeds Noble Knight URLs for Warmachine: Dark Operations products from
confirmed URLs in the user-supplied "Warmachine - Noble Knight.xlsx".

Only 2 of the 19 Dark Operations products have a confirmed NK listing.

create_defaults pattern: price, in_stock, last_seen are set only on
creation so scraper-set prices survive Railway redeploys.
url, listing_title, not_available are in defaults and always updated.

Usage:
    python manage.py seed_nk_warmachine_dark_operations_prices
"""

from django.core.management.base import BaseCommand

NK_PRICES = [
    # (gw_sku, listing_title, price, url, in_stock, not_available)
    ('WMH-118', 'Cognifex Cyphon', 29.95, 'https://www.nobleknight.com/P/2147598032/Cognifex-Cyphon?awid=1576', True, False),
    ('WMH-342', 'Exulon Thexus', 24.95, 'https://www.nobleknight.com/P/2147555933/Exulon-Thexus?awid=1576', True, False),
]


class Command(BaseCommand):
    """Seed Noble Knight URLs for Warmachine: Dark Operations products."""

    help = 'seed_nk_warmachine_dark_operations_prices — NK URLs for Dark Operations (2 of 19 SKUs confirmed)'

    def handle(self, *args, **options):
        """Run the command."""
        from django.utils import timezone

        from prices.models import CurrentPrice
        from products.models import Product, Retailer

        nk_retailer = Retailer.objects.get(slug='noble-knight-games')
        seeded = 0

        for (gw_sku, listing_title, price, url, in_stock, not_available) in NK_PRICES:
            product = Product.objects.get(gw_sku=gw_sku)
            CurrentPrice.objects.update_or_create(
                product=product,
                retailer=nk_retailer,
                defaults={
                    'listing_title': listing_title,
                    'url': url,
                    'not_available': not_available,
                },
                create_defaults={
                    'price': price,
                    'in_stock': in_stock,
                    'last_seen': timezone.now(),
                },
            )
            self.stdout.write(f'  seeded NK: {gw_sku}')
            seeded += 1

        self.stdout.write(self.style.SUCCESS(
            f'seed_nk_warmachine_dark_operations_prices complete. {seeded} record(s) seeded.'
        ))
