"""
Management command: seed_mm_warmachine_khador_prices

Seeds Miniature Market URLs for Warmachine: Khador products from confirmed
URLs in the master "Warmachine - Miniature Market.xlsx" sheet.

9 of the 52 Khador products have a confirmed MM listing. WMH-289 (Khador
Winter Korps Command Starter) fuzzy-matched to the same listing already
claimed by WMH-176 (Winter Korps Battlegroup Box) -- user-confirmed
2026-08-15 that match is wrong (Command Starter != Battlegroup Box) --
left unmatched (not_available) rather than written incorrectly.

WMH-261 (Two Player Starter Set) matches "Two-Player Starter Set - Khador
vs Cygnar" -- part# SFIK-CKSS154 confirmed against the NK listing for the
same box, description literally covers both factions. Consistent with the
dual-tag (Cygnar primary / Khador secondary) applied in
assign_warmachine_khador.py.

create_defaults pattern: price, in_stock, last_seen are set only on
creation so scraper-set prices survive Railway redeploys.
url, listing_title, not_available are in defaults and always updated.

Usage:
    python manage.py seed_mm_warmachine_khador_prices
"""

from django.core.management.base import BaseCommand

MM_PRICES = [
    # (gw_sku, listing_title, price, url, in_stock, not_available)
    ('WMH-072', 'Warmachine: Khador SKS-6 Command Cadre', 59.99, 'https://www.miniaturemarket.com/warmachine-khador-sks-6-command-cadre-sfik-kdr221.html', True, False),
    ('WMH-174', 'Warmachine: Khador Winter Korps Core Expansion', 135.99, 'https://www.miniaturemarket.com/warmachine-khador-winter-korps-core-expansion-sfik-kdr067.html', True, False),
    ('WMH-175', 'Warmachine: Khador Winter Korps Auxiliary Expansion', 127.99, 'https://www.miniaturemarket.com/warmachine-khador-winter-korps-auxiliary-expansion-sfik-kdr068.html', True, False),
    ('WMH-176', 'Warmachine: Khador Winter Korps Battlegroup Box', 63.99, 'https://www.miniaturemarket.com/warmachine-khador-winter-korps-battlegroup-box-sfik-kdr073.html', True, False),
    ('WMH-237', 'Warmachine: Khador Old Umbrey Battlegroup Box', 63.99, 'https://www.miniaturemarket.com/warmachine-khador-old-umbrey-battlegroup-box-sfik-kdr210.html', True, False),
    ('WMH-253', 'Warmachine: Khador Old Umbrey Command Starter', 67.99, 'https://www.miniaturemarket.com/warmachine-khador-old-umbrey-command-starter-sfik-kdr223.html', True, False),
    ('WMH-325', 'Warmachine: Khador Old Umbrey Core Expansion', 135.99, 'https://www.miniaturemarket.com/warmachine-khador-old-umbrey-core-expansion-sfik-kdr348.html', True, False),
    ('WMH-328', 'Warmachine: Khador Old Umbrey Auxiliary Expansion', 135.99, 'https://www.miniaturemarket.com/warmachine-khador-old-umbrey-auxiliary-expansion-sfik-kdr349.html', True, False),
    ('WMH-261', 'Warmachine: Two-Player Starter Set - Khador vs Cygnar', 84.99, 'https://www.miniaturemarket.com/warmachine-two-player-starter-set-khador-vs-cygnar-sfik-ckss154.html', True, False),
]


class Command(BaseCommand):
    """Seed Miniature Market URLs for Warmachine: Khador products."""

    help = 'seed_mm_warmachine_khador_prices — MM URLs for Khador (9 of 52 SKUs confirmed)'

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
            f'seed_mm_warmachine_khador_prices complete. {seeded} record(s) seeded.'
        ))
