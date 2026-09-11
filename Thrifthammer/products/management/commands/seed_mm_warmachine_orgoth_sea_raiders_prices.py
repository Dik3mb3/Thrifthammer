"""
Management command: seed_mm_warmachine_orgoth_sea_raiders_prices

Seeds Miniature Market URLs for Warmachine: Orgoth Sea Raiders products.
The master "Warmachine - Miniature Market.xlsx" sheet (Title + Price only,
no URL column, spans the whole Warmachine line) had 3 Orgoth Sea Raiders
rows, all matching existing catalog SKUs by exact title. Each was confirmed
live on miniaturemarket.com (search, verify title + price match the sheet,
grab the real product URL and MFG part #) before being written here.

MFG parts (ORG031 Core, ORG032 Auxiliary, ORG038 Battlegroup Box) confirm
these are 3 genuinely distinct products.

create_defaults pattern: price, in_stock, last_seen are set only on
creation so scraper-set prices survive Railway redeploys.
url, listing_title, not_available are in defaults and always updated.

Usage:
    python manage.py seed_mm_warmachine_orgoth_sea_raiders_prices
"""

from django.core.management.base import BaseCommand

MM_PRICES = [
    # (gw_sku, listing_title, price, url, in_stock, not_available)
    ('WMH-157', 'Warmachine: Orgoth Sea Raiders Core Expansion', 135.99, 'https://www.miniaturemarket.com/warmachine-orgoth-sea-raiders-core-expansion-sfik-org031.html', True, False),
    ('WMH-158', 'Warmachine: Orgoth Sea Raiders Auxiliary Expansion', 127.99, 'https://www.miniaturemarket.com/warmachine-orgoth-sea-raiders-auxiliary-expansion-sfik-org032.html', True, False),
    ('WMH-159', 'Warmachine: Orgoth Sea Raiders Battlegroup Box', 63.99, 'https://www.miniaturemarket.com/warmachine-orgoth-sea-raiders-battlegroup-box-sfik-org038.html', True, False),
]


class Command(BaseCommand):
    """Seed Miniature Market URLs for Warmachine: Orgoth Sea Raiders products."""

    help = 'seed_mm_warmachine_orgoth_sea_raiders_prices — MM URLs for Orgoth Sea Raiders (3 of 28 SKUs confirmed)'

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
            f'seed_mm_warmachine_orgoth_sea_raiders_prices complete. {seeded} record(s) seeded.'
        ))
