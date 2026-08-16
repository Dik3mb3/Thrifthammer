"""
Management command: seed_mm_warmachine_crucible_guard_prices

Seeds Miniature Market URLs for Warmachine: Crucible Guard products from
confirmed URLs in the user-supplied "Warmachine - Miniature Market.xlsx".

Only 1 of the 22 Crucible Guard products has a confirmed MM listing.

create_defaults pattern: price, in_stock, last_seen are set only on
creation so scraper-set prices survive Railway redeploys.
url, listing_title, not_available are in defaults and always updated.

Usage:
    python manage.py seed_mm_warmachine_crucible_guard_prices
"""

from django.core.management.base import BaseCommand

MM_PRICES = [
    # (gw_sku, listing_title, price, url, in_stock, not_available)
    ('WMH-109', 'Warmachine: Crucible Guard - Vulcan (Preorder)', 127.99, 'https://www.miniaturemarket.com/Warmachine-Crucible-Guard-Vulcan-Preorder/SFIK-CGU448', True, False),
]


class Command(BaseCommand):
    """Seed Miniature Market URLs for Warmachine: Crucible Guard products."""

    help = 'seed_mm_warmachine_crucible_guard_prices — MM URLs for Crucible Guard (1 of 22 SKUs confirmed)'

    def handle(self, *args, **options):
        """Run the command."""
        from django.utils import timezone

        from prices.models import CurrentPrice
        from products.models import Product, Retailer

        mm_retailer = Retailer.objects.get(slug='miniature-market')
        seeded = 0

        for (gw_sku, listing_title, price, url, in_stock, not_available) in MM_PRICES:
            product = Product.objects.get(gw_sku=gw_sku)
            CurrentPrice.objects.update_or_create(
                product=product,
                retailer=mm_retailer,
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
            self.stdout.write(f'  seeded MM: {gw_sku}')
            seeded += 1

        self.stdout.write(self.style.SUCCESS(
            f'seed_mm_warmachine_crucible_guard_prices complete. {seeded} record(s) seeded.'
        ))
