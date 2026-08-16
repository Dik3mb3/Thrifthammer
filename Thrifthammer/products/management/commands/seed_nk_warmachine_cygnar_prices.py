"""
Management command: seed_nk_warmachine_cygnar_prices

Seeds Noble Knight URLs for Warmachine: Cygnar products from confirmed
URLs in the user-supplied "Warmachine - Noble Knight.xlsx" (8 matches from
the sheet itself) plus 10 more the user found and confirmed directly by
URL 2026-08-13.

6 of the user-confirmed 10 are currently out of stock at NK with no price
displayed on the page -- those are seeded with in_stock=False, price=None
(a real listing exists, it's just not currently priced/stocked), not as
not_available (which is reserved for "no listing exists at all").

"Stormguard" and "Storm Lance" (bare, no "Legionnaires" qualifier) and a
generic "Battlegroup" listing were all explicitly rejected by the user as
too ambiguous to confirm -- left unmatched.

create_defaults pattern: price, in_stock, last_seen are set only on
creation so scraper-set prices survive Railway redeploys.
url, listing_title, not_available are in defaults and always updated.

Usage:
    python manage.py seed_nk_warmachine_cygnar_prices
"""

from django.core.management.base import BaseCommand

NK_PRICES = [
    # (gw_sku, listing_title, price, url, in_stock, not_available)
    # -- From the original NK sheet --
    ('WMH-034', 'Storm Legion Core Expansion Set', 144.95, 'https://www.nobleknight.com/P/2148207454/Storm-Legion-Core-Expansion-Set?awid=1576', True, False),
    ('WMH-071', 'Cygnar Hellslingers Command Cadre', 63.95, 'https://www.nobleknight.com/P/2148378997/Cygnar-Hellslingers-Command-Cadre?awid=1576', True, False),
    ('WMH-074', 'Cygnar Gravediggers Command Starter Set', 72.95, 'https://www.nobleknight.com/P/2148429624/Cygnar-Gravediggers-Command-Starter-Set?awid=1576', True, False),
    ('WMH-142', 'Storm Legion Auxiliary Expansion Set', 135.95, 'https://www.nobleknight.com/P/2148207457/Storm-Legion-Auxiliary-Expansion-Set?awid=1576', True, False),
    ('WMH-143', 'Storm Legion Battlegroup Box Set', 67.95, 'https://www.nobleknight.com/P/2148207472/Storm-Legion-Battlegroup-Box-Set?awid=1576', True, False),
    ('WMH-234', 'Cygnar Gravediggers Auxiliary Expansion', 135.95, 'https://www.nobleknight.com/P/2148429621/Cygnar-Gravediggers-Auxiliary-Expansion?awid=1576', True, False),
    ('WMH-236', 'Cygnar Gravediggers Battlegroup Box Set', 67.95, 'https://www.nobleknight.com/P/2148338598/Cygnar-Gravediggers-Battlegroup-Box-Set?awid=1576', True, False),
    ('WMH-255', 'Cygnar Gravediggers Core Expansion', 144.95, 'https://www.nobleknight.com/P/2148429618/Cygnar-Gravediggers-Core-Expansion?awid=1576', True, False),
    # -- User-confirmed by direct URL 2026-08-13 --
    ('WMH-030', 'Gravediggers - Bandit', None, 'https://www.nobleknight.com/P/2148494224/Gravediggers---Bandit?awid=1576', False, False),
    ('WMH-035', 'Sharpshooter', 12.00, 'https://www.nobleknight.com/P/2148126924/Sharpshooter?awid=1576', True, False),
    ('WMH-036', 'Captain Raef Huxley', None, 'https://www.nobleknight.com/P/2148169782/Captain-Raef-Huxley?awid=1576', False, False),
    ('WMH-049', 'Courser Light Warjack', None, 'https://www.nobleknight.com/P/2148047742/Courser-Light-Warjack?awid=1576', False, False),
    ('WMH-051', 'Sharpshooter Variant', 30.00, 'https://www.nobleknight.com/P/2148125898/Sharpshooter-Variant?awid=1576', True, False),
    ('WMH-102', 'Thunderhead - Heavy Warjack', 59.95, 'https://www.nobleknight.com/P/2147624079/Thunderhead---Heavy-Warjack?awid=1576', True, False),
    ('WMH-144', 'Stryker Heavy Warjack', 55.00, 'https://www.nobleknight.com/P/2148047750/Stryker-Heavy-Warjack?awid=1576', True, False),
    ('WMH-152', 'Cygnar Zephyr', None, 'https://www.nobleknight.com/P/2148064290/Cygnar-Zephyr?awid=1576', False, False),
    ('WMH-261', 'Two Player Starter Set', None, 'https://www.nobleknight.com/P/2148299077/Two-Player-Starter-Set?awid=1576', False, False),
    ('WMH-312', 'Trencher Commando Officer', None, 'https://www.nobleknight.com/P/2147682158/Trencher-Commando-Officer?awid=1576', False, False),
]


class Command(BaseCommand):
    """Seed Noble Knight URLs for Warmachine: Cygnar products."""

    help = 'seed_nk_warmachine_cygnar_prices — NK URLs for Cygnar (18 of 49 SKUs confirmed)'

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
            f'seed_nk_warmachine_cygnar_prices complete. {seeded} record(s) seeded.'
        ))
