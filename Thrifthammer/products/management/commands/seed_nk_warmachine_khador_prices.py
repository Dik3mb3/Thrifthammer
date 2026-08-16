"""
Management command: seed_nk_warmachine_khador_prices

Seeds Noble Knight URLs for Warmachine: Khador products from the master
"Warmachine - Noble Knight.xlsx" sheet plus 3 additional confirmed URLs
the user found directly 2026-08-15.

11 of the 52 Khador products have a confirmed NK listing:
- 8 from the master sheet fuzzy-match, in stock with a price at scrape time.
- WMH-058 (AC-2 Bison) and WMH-180 (Shock Trooper Gunners): confirmed real,
  current Mk IV Khador listings, verified via browser 2026-08-15 -- both
  currently out of stock ("Notify Me"), seeded with price=None,
  in_stock=False, not_available=False. A real listing exists; the
  scheduled NK scraper will flip in_stock and populate price automatically
  once these come back in stock.
- WMH-261 (Two Player Starter Set): confirmed real (Steamforged part#
  SFIK-CKSS154 matches the MM listing for the same box exactly), also
  currently out of stock, same treatment as above.

WMH-057 (Battle Mechanik) was checked and rejected: the only NK listing
found is "Warmachine Mk II - Khador (28mm)" (2011, Metal) -- a discontinued
old-edition product, not the current Mk IV kit in our catalog. Left
unmatched per user instruction 2026-08-15 rather than guessed.

create_defaults pattern: price, in_stock, last_seen are set only on
creation so scraper-set prices survive Railway redeploys.
url, listing_title, not_available are in defaults and always updated.

Usage:
    python manage.py seed_nk_warmachine_khador_prices
"""

from django.core.management.base import BaseCommand

NK_PRICES = [
    # (gw_sku, listing_title, price, url, in_stock, not_available)
    ('WMH-072', 'Khador SKS-6 Command Cadre', 63.95, 'https://www.nobleknight.com/P/2148315712/Khador-SKS-6-Command-Cadre?awid=1576', True, False),
    ('WMH-174', 'Winter Korps Core Expansion Set', 144.95, 'https://www.nobleknight.com/P/2148221301/Winter-Korps-Core-Expansion-Set?awid=1576', True, False),
    ('WMH-175', 'Winter Korps Auxiliary Expansion Set', 135.95, 'https://www.nobleknight.com/P/2148221302/Winter-Korps-Auxiliary-Expansion-Set?awid=1576', True, False),
    ('WMH-176', 'Winter Korps Battlegroup Box', 67.95, 'https://www.nobleknight.com/P/2148207540/Winter-Korps-Battlegroup-Box?awid=1576', True, False),
    ('WMH-237', 'Old Umbrey Battlegroup Box', 67.95, 'https://www.nobleknight.com/P/2148483662/Old-Umbrey-Battlegroup-Box?awid=1576', True, False),
    ('WMH-253', 'Old Umbrey Command Starter Set', 72.95, 'https://www.nobleknight.com/P/2148472898/Old-Umbrey-Command-Starter-Set?awid=1576', True, False),
    ('WMH-325', 'Old Umbrey Core Expansion', 144.95, 'https://www.nobleknight.com/P/2148472838/Old-Umbrey-Core-Expansion?awid=1576', True, False),
    ('WMH-328', 'Old Umbrey Auxiliary Expansion', 144.95, 'https://www.nobleknight.com/P/2148472840/Old-Umbrey-Auxiliary-Expansion?awid=1576', True, False),
    # -- User-confirmed by direct URL 2026-08-15, all currently out of stock --
    ('WMH-058', 'AC-2 Bison', None, 'https://www.nobleknight.com/P/2148064289/AC-2-Bison?awid=1576', False, False),
    ('WMH-180', 'Shock Trooper Gunners', None, 'https://www.nobleknight.com/P/2148250638/Shock-Trooper-Gunners?awid=1576', False, False),
    ('WMH-261', 'Two Player Starter Set', None, 'https://www.nobleknight.com/P/2148299077/Two-Player-Starter-Set?awid=1576', False, False),
]


class Command(BaseCommand):
    """Seed Noble Knight URLs for Warmachine: Khador products."""

    help = 'seed_nk_warmachine_khador_prices — NK URLs for Khador (11 of 52 SKUs confirmed)'

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
            f'seed_nk_warmachine_khador_prices complete. {seeded} record(s) seeded.'
        ))
