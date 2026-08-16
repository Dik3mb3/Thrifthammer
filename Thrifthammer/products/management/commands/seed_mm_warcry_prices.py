"""
Management command: seed_mm_warcry_prices

Seeds Miniature Market URLs for Warcry products.

Only 1 of the 6 new Warcry products (WC-001 through WC-006) has a
confirmed MM listing. The other 5 either aren't in MM's catalog under
this name, or only appear as a companion Dice Pack / different bundle
(e.g. "Warcry: The Jade Obelisk Dice (18)" is not the same product as
Jade Obelisk itself) -- left out rather than guessed.

The 18 existing Warcry-tagged products (Twistweald, Rotmire Creed, etc.)
also appear in the source spreadsheet, but their MM pricing is owned by
their original faction's own seed command -- not duplicated here.

create_defaults pattern: price, in_stock, last_seen are set only on
creation so scraper-set prices survive Railway redeploys.
url, listing_title, not_available are in defaults and always updated.

Usage:
    python manage.py seed_mm_warcry_prices
"""

from django.core.management.base import BaseCommand

MM_PRICES = [
    # (slug, listing_title, price, url, in_stock, not_available)
    ('ydrilan-riverblades', 'Warcry: Ydrilan Riverblades', None, 'https://www.miniaturemarket.com/warcry-ydrilan-riverblades-gw-112-13.html', False, False),
]


class Command(BaseCommand):
    """Seed Miniature Market URLs for Warcry products."""

    help = 'seed_mm_warcry_prices — MM URLs for Warcry (0 of 6 SKUs confirmed)'

    def handle(self, *args, **options):
        """Run the command."""
        from django.utils import timezone

        from prices.models import CurrentPrice
        from products.models import Product, Retailer

        mm_retailer = Retailer.objects.get(slug='miniature-market')
        seeded = 0

        for (slug, listing_title, price, url, in_stock, not_available) in MM_PRICES:
            product = Product.objects.get(slug=slug)
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
            self.stdout.write(f'  seeded MM: {slug}')
            seeded += 1

        self.stdout.write(self.style.SUCCESS(
            f'seed_mm_warcry_prices complete. {seeded} record(s) seeded.'
        ))
