"""
Management command: seed_mm_warmachine_khymaera_prices

Seeds Miniature Market URLs for Warmachine: Khymaera products. The master
"Warmachine - Miniature Market.xlsx" sheet (Title + Price only, no URL
column, spans the whole Warmachine line) had 3 Khymaera rows, all matching
existing catalog SKUs by exact title. Each was confirmed live on
miniaturemarket.com (search, verify title + price match the sheet, grab
the real product URL and MFG part #) before being written here.

MFG parts confirm these are 3 genuinely distinct products (KMR144 Core,
KMR145 Auxiliary, KMR152 Battlegroup Box) -- useful cross-check, since
Amazon's search had incorrectly matched the Battlegroup Box to the same
ASIN as the Auxiliary Expansion (see find_amazon_asins.py SKIP_SKUS).

create_defaults pattern: price, in_stock, last_seen are set only on
creation so scraper-set prices survive Railway redeploys.
url, listing_title, not_available are in defaults and always updated.

Usage:
    python manage.py seed_mm_warmachine_khymaera_prices
"""

from django.core.management.base import BaseCommand

MM_PRICES = [
    # (gw_sku, listing_title, price, url, in_stock, not_available)
    ('WMH-226', 'Warmachine: Khymaera Shadowflame Shard Core Expansion', 135.99, 'https://www.miniaturemarket.com/warmachine-khymaera-shadowflame-shard-core-expansion-sfik-kmr144.html', True, False),
    ('WMH-227', 'Warmachine: Khymaera Shadowflame Shard Auxiliary Expansion', 127.99, 'https://www.miniaturemarket.com/warmachine-khymaera-shadowflame-shard-auxiliary-expansion-sfik-kmr145.html', True, False),
    ('WMH-228', 'Warmachine: Khymaera Shadowflame Shard Battlegroup Box', 63.99, 'https://www.miniaturemarket.com/warmachine-khymaera-shadowflame-shard-battlegroup-box-sfik-kmr152.html', True, False),
]


class Command(BaseCommand):
    """Seed Miniature Market URLs for Warmachine: Khymaera products."""

    help = 'seed_mm_warmachine_khymaera_prices — MM URLs for Khymaera (3 of 26 SKUs confirmed)'

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
            f'seed_mm_warmachine_khymaera_prices complete. {seeded} record(s) seeded.'
        ))
