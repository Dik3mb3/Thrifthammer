"""
Management command: seed_nk_warcry_prices

Seeds Noble Knight URLs for Warcry products.

All 6 new Warcry products (WC-001 through WC-006) have a confirmed NK
listing. WC-006's listing ("Chaos Legionnaires", no "Warcry:" prefix in
the title) was initially left out as ambiguous with the existing Slaves
to Darkness product of the same name -- user confirmed 2026-08-09 it's
the correct listing for this SKU.

The 18 existing Warcry-tagged products (Chaotic Beasts, Fomoroid
Crusher, Vulkyn Flameseekers, Wildercorps Hunters, Centaurion Marshal,
Monsta Killaz, etc.) also appear in the source spreadsheet, but their NK
pricing is owned by their original faction's own seed command -- not
duplicated here.

create_defaults pattern: price, in_stock, last_seen are set only on
creation so scraper-set prices survive Railway redeploys.
url, listing_title, not_available are in defaults and always updated.

Usage:
    python manage.py seed_nk_warcry_prices
"""

from django.core.management.base import BaseCommand

NK_PRICES = [
    # (slug, listing_title, price, url, in_stock, not_available)
    ('ydrilan-riverblades', 'Ydrilan Riverblades', None, 'https://www.nobleknight.com/P/2148179072/Ydrilan-Riverblades?awid=1576', False, False),
    ('jade-obelisk', 'Jade Obelisk, The', None, 'https://www.nobleknight.com/P/2148036066/Jade-Obelisk-The?awid=1576', False, False),
    ('questor-soulsworn', 'Questor Soulsworn', None, 'https://www.nobleknight.com/P/2148070749/Questor-Soulsworn?awid=1576', False, False),
    ('pyregheists', 'Pyregheists', None, 'https://www.nobleknight.com/P/2148179077/Pyregheists?awid=1576', False, False),
    ('hunters-of-huanchi', 'Hunters of Huanchi', None, 'https://www.nobleknight.com/P/2148036065/Hunters-of-Huanchi?awid=1576', False, False),
    ('warcry-chaos-legionnaires', 'Chaos Legionnaires', None, 'https://www.nobleknight.com/P/2147996722/Chaos-Legionnaires?awid=1576', False, False),
]


class Command(BaseCommand):
    """Seed Noble Knight URLs for Warcry products."""

    help = 'seed_nk_warcry_prices — NK URLs for Warcry (6 of 6 SKUs confirmed)'

    def handle(self, *args, **options):
        """Run the command."""
        from django.utils import timezone

        from prices.models import CurrentPrice
        from products.models import Product, Retailer

        nk_retailer = Retailer.objects.get(slug='noble-knight-games')
        seeded = 0

        for (slug, listing_title, price, url, in_stock, not_available) in NK_PRICES:
            product = Product.objects.get(slug=slug)
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
            self.stdout.write(f'  seeded NK: {slug}')
            seeded += 1

        self.stdout.write(self.style.SUCCESS(
            f'seed_nk_warcry_prices complete. {seeded} record(s) seeded.'
        ))
