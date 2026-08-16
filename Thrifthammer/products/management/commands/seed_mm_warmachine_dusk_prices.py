"""
Management command: seed_mm_warmachine_dusk_prices

Seeds Miniature Market URLs for Warmachine: Dusk products from confirmed
URLs in the user-supplied "Warmachine - Miniature Market.xlsx".

12 of the 46 Dusk products have a confirmed MM listing. 2 further rows
that fuzzy-matched to these SKUs ("Krueger, Wrath of Blighterghast" and
"The Graveborn Command Cadre") were reviewed and rejected by the user
2026-08-13 -- both are real Steamforged products, just for different SKUs
outside Dusk (Krueger is Mercenaries, WMH-062; Graveborn is Orgoth's own
Command Cadre release, WMH-101) -- their confirmed URLs were applied
directly to those SKUs instead, not here.

create_defaults pattern: price, in_stock, last_seen are set only on
creation so scraper-set prices survive Railway redeploys.
url, listing_title, not_available are in defaults and always updated.

Usage:
    python manage.py seed_mm_warmachine_dusk_prices
"""

from django.core.management.base import BaseCommand

MM_PRICES = [
    # (gw_sku, listing_title, price, url, in_stock, not_available)
    ('WMH-199', 'Warmachine MKIV: Dusk House Kallyss - Eidolon, Heavy Warjack', 38.99, 'https://www.miniaturemarket.com/warmachine-mkiv-dusk-house-kallyss-eidolon-heavy-warjack-pip27004.html', True, False),
    ('WMH-063', 'Warmachine: Dusk House Kallyss Battlegroup Box', 63.99, 'https://www.miniaturemarket.com/warmachine-dusk-house-kallyss-battlegroup-box-sfik-dsk111.html', True, False),
    ('WMH-198', 'Warmachine: Dusk House Kallyss Auxiliary Expansion', 127.99, 'https://www.miniaturemarket.com/warmachine-dusk-house-kallyss-auxiliary-expansion-sfik-dsk104.html', True, False),
    ('WMH-200', 'Warmachine MKIV: Dusk House Kallyss - Ghast, Light Warjack', 29.99, 'https://www.miniaturemarket.com/warmachine-mkiv-dusk-house-kallyss-ghast-light-warjack-pip27005.html', True, False),
    ('WMH-197', 'Warmachine: Dusk House Kallyss Core Expansion', 135.99, 'https://www.miniaturemarket.com/warmachine-dusk-house-kallyss-core-expansion-sfik-dsk103.html', True, False),
    ('WMH-334', 'Warmachine: Frozen & Forgotten', 101.99, 'https://www.miniaturemarket.com/Warmachine-Frozen-Forgotten/SFIK-DOSS326', True, False),
    ('WMH-100', 'Warmachine: The Final Hunt Command Cadre', 67.99, 'https://www.miniaturemarket.com/Warmachine-The-Final-Hunt-Command-Cadre/SFIK-DSK369', True, False),
    ('WMH-020', "Warmachine: Dusk Fane of Nyrro - Executioner's Toll (New Arrival)", 67.99, 'https://www.miniaturemarket.com/Warmachine-Dusk-Fane-of-Nyrro-Executioner-s-Toll-New-Arrival/SFIK-DSK442', True, False),
    ('WMH-040', 'Warmachine: Dusk Fane of Nyrro - Vordak Heavy Warbeast (New Arrival)', 38.99, 'https://www.miniaturemarket.com/Warmachine-Dusk-Fane-of-Nyrro-Vordak-Heavy-Warbeast-New-Arrival/SFIK-DSK487', True, False),
    ('WMH-041', 'Warmachine: Dusk Fane of Nyrro - Strygon Light Warbeast (New Arrival)', 32.99, 'https://www.miniaturemarket.com/Warmachine-Dusk-Fane-of-Nyrro-Strygon-Light-Warbeast-New-Arrival/SFIK-DSK488', True, False),
    ('WMH-022', "Warmachine: Dusk Fane of Nyrro - Death's Whisper (New Arrival)", 144.99, 'https://www.miniaturemarket.com/Warmachine-Dusk-Fane-of-Nyrro-Death-s-Whisper-New-Arrival/SFIK-DSK441', True, False),
    ('WMH-005', 'Warmachine: Dusk Fane of Nyrro - Court of Shadows Army Box (Preorder)', 135.99, 'https://www.miniaturemarket.com/Warmachine-Dusk-Fane-of-Nyrro-Court-of-Shadows-Army-Box-Preorder/SFIK-DSK443', True, False),
]


class Command(BaseCommand):
    """Seed Miniature Market URLs for Warmachine: Dusk products."""

    help = 'seed_mm_warmachine_dusk_prices — MM URLs for Dusk (12 of 46 SKUs confirmed)'

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
            f'seed_mm_warmachine_dusk_prices complete. {seeded} record(s) seeded.'
        ))
