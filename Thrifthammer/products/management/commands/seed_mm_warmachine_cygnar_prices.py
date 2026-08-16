"""
Management command: seed_mm_warmachine_cygnar_prices

Seeds Miniature Market URLs for Warmachine: Cygnar products from confirmed
URLs in the user-supplied "Warmachine - Miniature Market.xlsx".

10 of the 49 Cygnar products have a confirmed MM listing. 6 other MM rows
that fuzzy-matched to these SKUs (Khador Annihilators Command Cadre, Cryx
Necrofactorium Command Starter/Battlegroup Box/Core Expansion, Cygnar
Storm Forge Command Cadre, The Graveborn Command Cadre) were reviewed and
rejected by the user 2026-08-13 -- all are real Steamforged products, just
not these Cygnar SKUs (wrong faction or a genuinely different Command
Cadre release).

create_defaults pattern: price, in_stock, last_seen are set only on
creation so scraper-set prices survive Railway redeploys.
url, listing_title, not_available are in defaults and always updated.

Usage:
    python manage.py seed_mm_warmachine_cygnar_prices
"""

from django.core.management.base import BaseCommand

MM_PRICES = [
    # (gw_sku, listing_title, price, url, in_stock, not_available)
    ('WMH-030', 'Warmachine: Cygnar Gravediggers Bandit (Preorder)', 67.99, 'https://www.miniaturemarket.com/Warmachine-Cygnar-Gravediggers-Bandit-Preorder/SFIK-CGN530', True, False),
    ('WMH-034', 'Warmachine: Cygnar Storm Legion Core Expanion', 135.99, 'https://www.miniaturemarket.com/warmachine-cygnar-storm-legion-core-expanion-sfik-cgn001.html', True, False),
    ('WMH-071', 'Warmachine: Cygnar Hellslingers Command Cadre', 59.99, 'https://www.miniaturemarket.com/warmachine-cygnar-hellslingers-command-cadre-sfik-cgn220.html', True, False),
    ('WMH-074', 'Warmachine: Cygnar Gravediggers Command Starter', 67.99, 'https://www.miniaturemarket.com/warmachine-cygnar-gravediggers-command-starter-sfik-cgn222.html', True, False),
    ('WMH-142', 'Warmachine: Cygnar Storm Legion Auxiliary Expansion', 127.99, 'https://www.miniaturemarket.com/warmachine-cygnar-storm-legion-auxiliary-expansion-sfik-cgn002.html', True, False),
    ('WMH-143', 'Warmachine: Cygnar Storm Legion Battlegroup Box', 63.99, 'https://www.miniaturemarket.com/warmachine-cygnar-storm-legion-battlegroup-box-sfik-cgn008.html', True, False),
    ('WMH-234', 'Warmachine: Cygnar Gravediggers Auxiliary Expansion', 127.99, 'https://www.miniaturemarket.com/warmachine-cygnar-gravediggers-auxiliary-expansion-sfik-cgn207.html', True, False),
    ('WMH-236', 'Warmachine: Cygnar Gravediggers Battlegroup Box', 63.99, 'https://www.miniaturemarket.com/warmachine-cygnar-gravediggers-battlegroup-box-sfik-cgn209.html', True, False),
    ('WMH-255', 'Warmachine: Cygnar Gravediggers Core Expansion', 135.99, 'https://www.miniaturemarket.com/warmachine-cygnar-gravediggers-core-expansion-sfik-cgn212.html', True, False),
    ('WMH-261', 'Warmachine: Two-Player Starter Set - Khador vs Cygnar', 84.99, 'https://www.miniaturemarket.com/warmachine-two-player-starter-set-khador-vs-cygnar-sfik-ckss154.html', True, False),
]


class Command(BaseCommand):
    """Seed Miniature Market URLs for Warmachine: Cygnar products."""

    help = 'seed_mm_warmachine_cygnar_prices — MM URLs for Cygnar (10 of 49 SKUs confirmed)'

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
            f'seed_mm_warmachine_cygnar_prices complete. {seeded} record(s) seeded.'
        ))
