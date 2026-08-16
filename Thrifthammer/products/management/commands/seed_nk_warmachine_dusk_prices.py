"""
Management command: seed_nk_warmachine_dusk_prices

Seeds Noble Knight URLs for Warmachine: Dusk products from confirmed URLs
in the user-supplied "Warmachine - Noble Knight.xlsx".

23 of the 46 Dusk products have a confirmed NK listing: 16 in-stock with
a price from the original sheet, plus 7 more the user found and confirmed
directly by URL 2026-08-13. Those 7 are currently out of stock at NK with
no price shown on the page -- seeded with in_stock=False, price=None (a
real listing exists, it's just not currently priced/stocked). The
scheduled NK scraper will flip in_stock and populate price automatically
once these come back in stock, same as any other product.

3 further candidate rows ("Fane of Nyrro - Strygon Heavy Warbeast
Options", a bare generic "Battlegroup" listing, "Mage Hunter Assassin
Variant") were reviewed and confirmed by the user 2026-08-13 as not
matching any of our 46 SKUs -- left unmatched rather than guessed. The
generic "Battlegroup" listing in particular is a genuinely different NK
product page from the specific "House Kallyss Battlegroup Box" listing
used for WMH-063 below (confirmed via distinct URLs).

create_defaults pattern: price, in_stock, last_seen are set only on
creation so scraper-set prices survive Railway redeploys.
url, listing_title, not_available are in defaults and always updated.

Usage:
    python manage.py seed_nk_warmachine_dusk_prices
"""

from django.core.management.base import BaseCommand

NK_PRICES = [
    # (gw_sku, listing_title, price, url, in_stock, not_available)
    ('WMH-096', 'Fane of Nyrro - Strygon Light Warbeast Options', 18.49, 'https://www.nobleknight.com/P/2148498633/Fane-of-Nyrro---Strygon-Light-Warbeast-Options?awid=1576', True, False),
    ('WMH-007', 'Fane of Nyrro - Blood Sirens', 22.95, 'https://www.nobleknight.com/P/2148498638/Fane-of-Nyrro---Blood-Sirens?awid=1576', True, False),
    ('WMH-022', "Fane of Nyrro Army Box - Death's Whisper", 153.95, 'https://www.nobleknight.com/P/2148498622/Fane-of-Nyrro-Army-Box---Deaths-Whisper?awid=1576', True, False),
    ('WMH-094', 'Fane of Nyrro - Strygon Rider', 32.95, 'https://www.nobleknight.com/P/2148488463/Fane-of-Nyrro---Strygon-Rider?awid=1576', True, False),
    ('WMH-024', 'Fane of Nyrro - Sythyss Prophet', 18.49, 'https://www.nobleknight.com/P/2148483698/Fane-of-Nyrro---Sythyss-Prophet?awid=1576', True, False),
    ('WMH-013', 'Fane of Nyrro - Sythyss Overseer', 18.49, 'https://www.nobleknight.com/P/2148498640/Fane-of-Nyrro---Sythyss-Overseer?awid=1576', True, False),
    ('WMH-093', 'Fane of Nyrro - Fane Knights', 32.95, 'https://www.nobleknight.com/P/2148488464/Fane-of-Nyrro---Fane-Knights?awid=1576', True, False),
    ('WMH-041', 'Fane of Nyrro - Strygon, Light Warbeast', 37.95, 'https://www.nobleknight.com/P/2148483690/Fane-of-Nyrro---Strygon-Light-Warbeast?awid=1576', True, False),
    ('WMH-040', 'Fane of Nyrro - Vordak, Heavy Warbeast', 40.95, 'https://www.nobleknight.com/P/2148483697/Fane-of-Nyrro---Vordak-Heavy-Warbeast?awid=1576', True, False),
    ('WMH-020', "Fane of Nyrro - Executioner's Toll", 72.95, 'https://www.nobleknight.com/P/2148483684/Fane-of-Nyrro---Executioners-Toll?awid=1576', True, False),
    ('WMH-009', 'Fane of Nyrro - Fane Stalkers', 29.95, 'https://www.nobleknight.com/P/2148498628/Fane-of-Nyrro---Fane-Stalkers?awid=1576', True, False),
    ('WMH-100', 'Final Hunt Command Cadre (HIPS)', 72.95, 'https://www.nobleknight.com/P/2148472868/Final-Hunt-Command-Cadre-HIPS?awid=1576', True, False),
    ('WMH-048', 'Imperatus, Ashen Phoenix', 79.95, 'https://www.nobleknight.com/P/2148461047/Imperatus-Ashen-Phoenix?awid=1576', True, False),
    ('WMH-063', 'House Kallyss Battlegroup Box', 67.95, 'https://www.nobleknight.com/P/2148207466/House-Kallyss-Battlegroup-Box?awid=1576', True, False),
    ('WMH-197', 'House Kallyss Core Expansion Set', 144.95, 'https://www.nobleknight.com/P/2148207442/House-Kallyss-Core-Expansion-Set?awid=1576', True, False),
    ('WMH-266', 'Mage Hunter Assassin', 14.95, 'https://www.nobleknight.com/P/2147417756/Mage-Hunter-Assassin?awid=1576', True, False),
    # -- User-confirmed by direct URL 2026-08-13, all currently out of stock --
    ('WMH-026', 'Scyrafael - Nis-Issyr of Desolation', None, 'https://www.nobleknight.com/P/2148169817/Scyrafael---Nis-Issyr-of-Desolation?awid=1576', False, False),
    ('WMH-198', 'House Kallyss Auxiliary Expansion Set', None, 'https://www.nobleknight.com/P/2148221299/House-Kallyss-Auxiliary-Expansion-Set?awid=1576', False, False),
    ('WMH-199', 'Heavy Warjack - Eidolon', None, 'https://www.nobleknight.com/P/2148082130/Heavy-Warjack---Eidolon?awid=1576', False, False),
    ('WMH-200', 'Light Warjack - Ghast', None, 'https://www.nobleknight.com/P/2148082131/Light-Warjack---Ghast?awid=1576', False, False),
    ('WMH-201', 'Eidolon Chassis Variant', None, 'https://www.nobleknight.com/P/2148169820/Eidolon-Chassis-Variant?awid=1576', False, False),
    ('WMH-206', 'Void Engine & Wights', None, 'https://www.nobleknight.com/P/2148082124/Void-Engine-and-Wights?awid=1576', False, False),
    ('WMH-211', 'Mage Hunter Commander Variant', None, 'https://www.nobleknight.com/P/2148141405/Mage-Hunter-Commander-Variant?awid=1576', False, False),
]


class Command(BaseCommand):
    """Seed Noble Knight URLs for Warmachine: Dusk products."""

    help = 'seed_nk_warmachine_dusk_prices — NK URLs for Dusk (23 of 46 SKUs confirmed)'

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
            f'seed_nk_warmachine_dusk_prices complete. {seeded} record(s) seeded.'
        ))
