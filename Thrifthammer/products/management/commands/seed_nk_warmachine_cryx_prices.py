"""
Management command: seed_nk_warmachine_cryx_prices

Seeds Noble Knight URLs for Warmachine: Cryx products from confirmed URLs
in the user-supplied "Warmachine - Noble Knight.xlsx".

Only 4 of the 23 Cryx products have a confirmed NK listing (all 4
Necrofactorium items). 3 further NK listings ("Machine Wraith", "Skarlock
Commander", "Skarlock Thrall", "Iron Lich Asphyxious") were considered as
possible matches for WMH-294, WMH-298, WMH-302 but explicitly rejected by
the user 2026-08-13 -- character names don't line up cleanly (missing
"Dominator"/"Lieutenant"/"Commander" qualifiers, and two different
Skarlock listings for one SKU), so left unmatched rather than guessed.

create_defaults pattern: price, in_stock, last_seen are set only on
creation so scraper-set prices survive Railway redeploys.
url, listing_title, not_available are in defaults and always updated.

Usage:
    python manage.py seed_nk_warmachine_cryx_prices
"""

from django.core.management.base import BaseCommand

NK_PRICES = [
    # (gw_sku, listing_title, price, url, in_stock, not_available)
    ('WMH-004', 'Cryx Necrofactorium Command Starter', 72.95, 'https://www.nobleknight.com/P/2148207475/Cryx-Necrofactorium-Command-Starter?awid=1576', True, False),
    ('WMH-235', 'Cryx Necrofactorium Battlegroup Box', 67.95, 'https://www.nobleknight.com/P/2148207532/Cryx-Necrofactorium-Battlegroup-Box?awid=1576', True, False),
    ('WMH-254', 'Necrofactorium Core Expansion Set', 144.95, 'https://www.nobleknight.com/P/2148207428/Necrofactorium-Core-Expansion-Set?awid=1576', True, False),
    ('WMH-233', 'Necrofactorium Auxiliary Expansion Set', 135.95, 'https://www.nobleknight.com/P/2148207431/Necrofactorium-Auxiliary-Expansion-Set?awid=1576', True, False),
]


class Command(BaseCommand):
    """Seed Noble Knight URLs for Warmachine: Cryx products."""

    help = 'seed_nk_warmachine_cryx_prices — NK URLs for Cryx (4 of 23 SKUs confirmed)'

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
            f'seed_nk_warmachine_cryx_prices complete. {seeded} record(s) seeded.'
        ))
