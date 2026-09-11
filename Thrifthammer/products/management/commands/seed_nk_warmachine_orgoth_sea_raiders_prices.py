"""
Management command: seed_nk_warmachine_orgoth_sea_raiders_prices

Seeds Noble Knight URLs for Warmachine: Orgoth Sea Raiders products.
Sourced directly from a user-supplied, pre-filtered NK category URL (Orgoth
product line, New condition only), same approach as Khymaera -- the live
listing page itself already carries title, price, MFG part #, and
stock/condition for each row.

FOUND 5 SEARCH RESULTS, all 5 matching existing catalog SKUs by name (no
missing/unassigned products this time, unlike Khymaera's WMH-323 case).
"Cursebound Command Cadre" (SFIK-ORG292, MSRP $99.99) matches WMH-290
"Orgoth Sea Raiders Command Starter" -- Steamforged's own product page URL
slug for this SKU is "warmachine-orgoth-cursebound-command-cadre" and the
MSRP matches exactly, confirming it's the same product under its full
in-universe name.

Only 5 of the 28 Orgoth Sea Raiders products have a confirmed NK listing.

create_defaults pattern: price, in_stock, last_seen are set only on
creation so scraper-set prices survive Railway redeploys.
url, listing_title, not_available are in defaults and always updated.

Usage:
    python manage.py seed_nk_warmachine_orgoth_sea_raiders_prices
"""

from django.core.management.base import BaseCommand

NK_PRICES = [
    # (gw_sku, listing_title, price, url, in_stock, not_available)
    ('WMH-101', 'Graveborn Command Cadre (HIPS)', 72.95, 'https://www.nobleknight.com/P/2148472887/Graveborn-Command-Cadre-HIPS?awid=1576', True, False),
    ('WMH-159', 'Orgoth Sea Raiders Battlegroup Box', 67.95, 'https://www.nobleknight.com/P/2148207549/Orgoth-Sea-Raiders-Battlegroup-Box?awid=1576', True, False),
    ('WMH-158', 'Orgoth Sea Raiders Auxiliary Expansion', 135.95, 'https://www.nobleknight.com/P/2148237338/Orgoth-Sea-Raiders-Auxiliary-Expansion?awid=1576', True, False),
    ('WMH-157', 'Orgoth Sea Raiders Core Expansion', 144.95, 'https://www.nobleknight.com/P/2148207450/Orgoth-Sea-Raiders-Core-Expansion?awid=1576', True, False),
    ('WMH-290', 'Cursebound Command Cadre', 90.95, 'https://www.nobleknight.com/P/2148213926/Cursebound-Command-Cadre?awid=1576', True, False),
]


class Command(BaseCommand):
    """Seed Noble Knight URLs for Warmachine: Orgoth Sea Raiders products."""

    help = 'seed_nk_warmachine_orgoth_sea_raiders_prices — NK URLs for Orgoth Sea Raiders (5 of 28 SKUs confirmed)'

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
            f'seed_nk_warmachine_orgoth_sea_raiders_prices complete. {seeded} record(s) seeded.'
        ))
