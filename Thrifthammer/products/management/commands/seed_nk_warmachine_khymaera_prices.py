"""
Management command: seed_nk_warmachine_khymaera_prices

Seeds Noble Knight URLs for Warmachine: Khymaera products. Sourced directly
from a user-supplied, pre-filtered NK category URL (Khymaera product line,
New condition only) rather than a spreadsheet -- the live listing page
itself already carries title, price, MFG part #, and stock/condition for
each row, so no separate per-product verification pass was needed beyond
what's shown on that page.

FOUND 4 SEARCH RESULTS. All 4 MFG part numbers (KMR144/145/152/155/329)
match the KMR-prefix codes already confirmed against eBay/Miniature Market
listings for this faction -- no cross-check needed.

WMH-323 "Khymaera Shadowflame Shard Command Starter (HIPS)" was NOT part
of the original 26-item "Khymaera - Warmachine - Steamforge.xlsx" batch --
it already existed in the DB (from the original flat 348-product seed) but
had never been assigned to a faction. This NK listing confirmed it as a
real, current Khymaera product; user-confirmed 2026-09-09 to assign it to
the Khymaera faction (now the 27th product) before seeding its price here.

Only 4 of the (now) 27 Khymaera products have a confirmed NK listing --
Noble Knight does not currently carry the Auxiliary Expansion or any of
the individual character/unit SKUs new condition.

create_defaults pattern: price, in_stock, last_seen are set only on
creation so scraper-set prices survive Railway redeploys.
url, listing_title, not_available are in defaults and always updated.

Usage:
    python manage.py seed_nk_warmachine_khymaera_prices
"""

from django.core.management.base import BaseCommand

NK_PRICES = [
    # (gw_sku, listing_title, price, url, in_stock, not_available)
    ('WMH-323', 'Shadowflame Shard Command Starter (HIPS)', 72.95, 'https://www.nobleknight.com/P/2148472881/Shadowflame-Shard-Command-Starter-HIPS?awid=1576', True, False),
    ('WMH-228', 'Shadowflame Shard Battlegroup Box', 67.95, 'https://www.nobleknight.com/P/2148207536/Shadowflame-Shard-Battlegroup-Box?awid=1576', True, False),
    ('WMH-229', 'Shard Incarnates Command Cadre', 90.95, 'https://www.nobleknight.com/P/2148213931/Shard-Incarnates-Command-Cadre?awid=1576', True, False),
    ('WMH-226', 'Shadowflame Shard Core Expansion Set', 144.95, 'https://www.nobleknight.com/P/2148221303/Shadowflame-Shard-Core-Expansion-Set?awid=1576', True, False),
]


class Command(BaseCommand):
    """Seed Noble Knight URLs for Warmachine: Khymaera products."""

    help = 'seed_nk_warmachine_khymaera_prices — NK URLs for Khymaera (4 of 27 SKUs confirmed)'

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
            f'seed_nk_warmachine_khymaera_prices complete. {seeded} record(s) seeded.'
        ))
