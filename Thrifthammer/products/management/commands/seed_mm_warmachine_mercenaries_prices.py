"""
Management command: seed_mm_warmachine_mercenaries_prices

Seeds Miniature Market URLs for Warmachine: Mercenaries products. The
master "Warmachine - Miniature Market.xlsx" sheet (Title + Price only, no
URL column, spans the whole Warmachine line) had 13 Mercenaries rows, all
matching existing catalog SKUs by exact title. Each was confirmed live on
miniaturemarket.com (search, verify title + price match the sheet, grab
the real product URL and MFG part #) before being written here.

11 of the 13 are in stock. 2 are real listings but currently out of stock
(WMH-194 Greygore Boomhowler, WMH-016 Eilish Garrity) -- kept with their
real price and in_stock=False rather than dropped, so the URL still earns
affiliate credit and the scheduled scraper flips in_stock automatically
once restocked.

create_defaults pattern: price, in_stock, last_seen are set only on
creation so scraper-set prices survive Railway redeploys.
url, listing_title, not_available are in defaults and always updated.

Usage:
    python manage.py seed_mm_warmachine_mercenaries_prices
"""

from django.core.management.base import BaseCommand

MM_PRICES = [
    # (gw_sku, listing_title, price, url, in_stock, not_available)
    ('WMH-016', 'Warmachine: Eilish Garrity, the Dark Traitor', 13.99, 'https://www.miniaturemarket.com/warmachine-eilish-garrity-dark-traitor-sfik-mer089.html', False, False),
    ('WMH-017', 'Warmachine: Alexia, Queen of the Damned', 13.99, 'https://www.miniaturemarket.com/warmachine-alexia-queen-damned-sfik-mer092.html', True, False),
    ('WMH-059', 'Warmachine: Maulgreth, the Charnel Plague', 16.99, 'https://www.miniaturemarket.com/warmachine-maulgreth-charnel-plague-sfik-mer087.html', True, False),
    ('WMH-060', 'Warmachine: Magnus the Unstoppable and Invictus', 67.99, 'https://www.miniaturemarket.com/warmachine-magnus-unstoppable-and-invictus-sfik-mer093.html', True, False),
    ('WMH-061', 'Warmachine: Emperor Carver Ultimus Esquire III & War Boar MMD47', 67.99, 'https://www.miniaturemarket.com/warmachine-emperor-carver-ultimus-esquire-iii-war-boar-mmd47-sfik-mer101.html', True, False),
    ('WMH-062', 'Warmachine: Krueger, Wrath of Blighterghast', 29.99, 'https://www.miniaturemarket.com/warmachine-krueger-wrath-blighterghast-sfik-mer102.html', True, False),
    ('WMH-187', 'Warmachine: Prisoner 102822', 13.99, 'https://www.miniaturemarket.com/warmachine-prisoner-102822-sfik-mer088.html', True, False),
    ('WMH-188', 'Warmachine: Koldun Lord Damien Korovnik', 13.99, 'https://www.miniaturemarket.com/warmachine-koldun-lord-damien-korovnik-sfik-mer090.html', True, False),
    ('WMH-189', 'Warmachine: Eiryss, Shadow of Retribution', 13.99, 'https://www.miniaturemarket.com/warmachine-eiryss-shadow-retribution-sfik-mer091.html', True, False),
    ('WMH-190', 'Warmachine: Nissak, Totem Huntress Champion', 16.99, 'https://www.miniaturemarket.com/warmachine-nissak-totem-huntress-champion-sfik-mer094.html', True, False),
    ('WMH-192', 'Warmachine: Bellighul, Master of Pain', 16.99, 'https://www.miniaturemarket.com/warmachine-bellighul-master-pain-sfik-mer096.html', True, False),
    ('WMH-193', "Warmachine: Zacchaeus, Winter's Chill", 25.99, 'https://www.miniaturemarket.com/warmachine-zacchaeus-winters-chill-sfik-mer097.html', True, False),
    ('WMH-194', 'Warmachine: Greygore Boomhowler', 16.99, 'https://www.miniaturemarket.com/warmachine-greygore-boomhowler-sfik-mer098.html', False, False),
]


class Command(BaseCommand):
    """Seed Miniature Market URLs for Warmachine: Mercenaries products."""

    help = 'seed_mm_warmachine_mercenaries_prices — MM URLs for Mercenaries (13 of 22 SKUs confirmed)'

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
            f'seed_mm_warmachine_mercenaries_prices complete. {seeded} record(s) seeded.'
        ))
