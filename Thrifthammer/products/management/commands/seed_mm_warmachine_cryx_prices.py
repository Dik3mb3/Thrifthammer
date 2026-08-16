"""
Management command: seed_mm_warmachine_cryx_prices

Seeds Miniature Market URLs for Warmachine: Cryx products from confirmed
URLs in the user-supplied "Warmachine - Miniature Market.xlsx".

Only 4 of the 23 Cryx products have a confirmed MM listing (all 4
Necrofactorium items).

create_defaults pattern: price, in_stock, last_seen are set only on
creation so scraper-set prices survive Railway redeploys.
url, listing_title, not_available are in defaults and always updated.

Usage:
    python manage.py seed_mm_warmachine_cryx_prices
"""

from django.core.management.base import BaseCommand

MM_PRICES = [
    # (gw_sku, listing_title, price, url, in_stock, not_available)
    ('WMH-004', 'Warmachine: Cryx Necrofactorium Command Starter', 67.99, 'https://www.miniaturemarket.com/warmachine-cryx-necrofactorium-command-starter-sfik-crx055.html', True, False),
    ('WMH-235', 'Warmachine: Cryx Necrofactorium Battlegroup Box', 63.99, 'https://www.miniaturemarket.com/warmachine-cryx-necrofactorium-battlegroup-box-sfik-crx062.html', True, False),
    ('WMH-254', 'Warmachine: Cryx Necrofactorium Core Expansion', 135.99, 'https://www.miniaturemarket.com/warmachine-cryx-necrofactorium-core-expansion-sfik-crx056.html', True, False),
    ('WMH-233', 'Warmachine: Cryx Necrofactorium Auxilliary Expansion', 127.99, 'https://www.miniaturemarket.com/warmachine-cryx-necrofactorium-auxilliary-expansion-sfik-crx057.html', True, False),
]


class Command(BaseCommand):
    """Seed Miniature Market URLs for Warmachine: Cryx products."""

    help = 'seed_mm_warmachine_cryx_prices — MM URLs for Cryx (4 of 23 SKUs confirmed)'

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
            f'seed_mm_warmachine_cryx_prices complete. {seeded} record(s) seeded.'
        ))
