"""
Management command: seed_mm_warmachine_southern_kriels_prices

Seeds Miniature Market URLs for Warmachine: Southern Kriels products.
The user-supplied master "Warmachine - Miniature Market.xlsx" sheet (Title +
Price only, no URL column, spans the whole Warmachine line) had 9 Southern
Kriels rows. 8 matched an existing catalog SKU by exact/near-exact title;
each was confirmed live on miniaturemarket.com (search, verify title +
price match the sheet, grab the real product URL) before being written here.

9th row, "Warmachine: Southern Kriels Command Cadre Foulblood's Armada"
($67.99), does not match any of the 54 Southern Kriels SKUs in our catalog
-- not included, flagged to the user as a possible missing product rather
than guessed at.

create_defaults pattern: price, in_stock, last_seen are set only on
creation so scraper-set prices survive Railway redeploys.
url, listing_title, not_available are in defaults and always updated.

Usage:
    python manage.py seed_mm_warmachine_southern_kriels_prices
"""

from django.core.management.base import BaseCommand

MM_PRICES = [
    # (gw_sku, listing_title, price, url, in_stock, not_available)
    ('WMH-010', 'Warmachine: Southern Kriels Kithguard Command Starter', 67.99, 'https://www.miniaturemarket.com/Warmachine-Southern-Kriels-Kithguard-Command-Starter/SFIK-SKR387', True, False),
    ('WMH-042', 'Warmachine: Southern Kriels Kithguard Battlegroup Box', 63.99, 'https://www.miniaturemarket.com/Warmachine-Southern-Kriels-Kithguard-Battlegroup-Box/SFIK-SKR384', True, False),
    ('WMH-120', 'Warmachine: Southern Kriels Kithguard Core Expansion', 135.99, 'https://www.miniaturemarket.com/Warmachine-Southern-Kriels-Kithguard-Core-Expansion/SFIK-SKR400', True, False),
    ('WMH-138', 'Warmachine: Southern Kriels Kithguard Auxiliary Expansion', 127.99, 'https://www.miniaturemarket.com/Warmachine-Southern-Kriels-Kithguard-Auxiliary-Expansion/SFIK-SKR401', True, False),
    ('WMH-212', 'Warmachine: Southern Kriels Brineblood Marauders Core Expansion', 135.99, 'https://www.miniaturemarket.com/warmachine-southern-kriels-brineblood-marauders-core-expansion-sfik-skr121.html', True, False),
    ('WMH-213', 'Warmachine: Southern Kriels Brineblood Marauders Auxiliary Expansion', 127.99, 'https://www.miniaturemarket.com/warmachine-southern-kriels-brineblood-marauders-auxiliary-expansion-sfik-skr122.html', True, False),
    ('WMH-214', 'Warmachine: Southern Kriels Brineblood Marauders Battlegroup Box', 63.99, 'https://www.miniaturemarket.com/warmachine-southern-kriels-brineblood-marauders-battlegroup-box-sfik-skr126.html', True, False),
    ('WMH-287', 'Warmachine: Southern Kriels Command Cadre Fire Tongue Warriors', 84.99, 'https://www.miniaturemarket.com/warmachine-firetongue-cadre-sfik-skr289.html', True, False),
]


class Command(BaseCommand):
    """Seed Miniature Market URLs for Warmachine: Southern Kriels products."""

    help = 'seed_mm_warmachine_southern_kriels_prices — MM URLs for Southern Kriels (8 of 54 SKUs confirmed)'

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
            f'seed_mm_warmachine_southern_kriels_prices complete. {seeded} record(s) seeded.'
        ))
