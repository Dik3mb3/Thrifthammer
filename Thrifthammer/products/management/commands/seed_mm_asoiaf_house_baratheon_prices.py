"""
Management command: seed_mm_asoiaf_house_baratheon_prices

Seeds Miniature Market URLs for A Song of Ice and Fire: House Baratheon products.
The master "ASOIAF Miniature Market.xlsx" sheet (Title, Title_URL, Price; 40 rows
spanning every house) had 1 kit that matches one of the 20 new House Baratheon
SKUs: "A Song of Ice & Fire: House Baratheon - Stag Knights Unit Box" (cmnsif803 =
SIF803 Stag Knights, $30.99). The match is confirmed by the manufacturer part
number in the Miniature Market URL, which is CMON's own SKU. The row was also read
live on miniaturemarket.com on 2026-11-11 with the Miniature Market scraper's own
page reader: price and stock state match the sheet (in stock).

The other 19 SKUs are not in the sheet. They were searched for: Miniature
Market's own suggest endpoint (the one the scraper uses) returns only the Stag
Knights page for every Baratheon unit name, and the product pages a web search
returned (Heroes #1, Crownland Scouts, King's Men, Highgarden Pikemen, R'hllor
Lightbringers, R'hllor Faithful, Champions of the Stag, Queen's Men) plus 18
guessed URLs in the same pattern all answer 404 on miniaturemarket.com today
(stale search-engine copies), so no row is created for them.

create_defaults pattern: price, in_stock, last_seen are set only on creation so
scraper-set prices survive later runs. url, listing_title, not_available are in
defaults (always updated) and are also repeated in create_defaults, because
Django 5 uses create_defaults INSTEAD of defaults when the row does not exist
yet, as is the case for this new SKU. Run ONCE by hand; it is not in the
Procfile.

Usage:
    python manage.py seed_mm_asoiaf_house_baratheon_prices
"""

from django.core.management.base import BaseCommand

MM_PRICES = [
    # (gw_sku, listing_title, price, url, in_stock, not_available)
    ('BARATHEON-004', 'A Song of Ice & Fire: House Baratheon - Stag Knights Unit Box', 30.99, 'https://www.miniaturemarket.com/song-ice-fire-house-baratheon-stag-knights-unit-box-cmnsif803.html', True, False),  # CMNSIF803
]


class Command(BaseCommand):
    """Seed Miniature Market URLs for A Song of Ice and Fire: House Baratheon products."""

    help = 'seed_mm_asoiaf_house_baratheon_prices: MM URLs for House Baratheon (1 of 20 SKUs confirmed)'

    def handle(self, *args, **options):
        """Create or update the Miniature Market price row for each confirmed SKU."""
        from django.utils import timezone

        from prices.models import CurrentPrice
        from products.models import Product, Retailer

        mm_retailer = Retailer.objects.get(slug='miniature-market')
        seeded = 0

        for (gw_sku, listing_title, price, url, in_stock, not_available) in MM_PRICES:
            product = Product.objects.get(gw_sku=gw_sku, category__slug='asoiaf')
            CurrentPrice.objects.update_or_create(
                product=product,
                retailer=mm_retailer,
                defaults={
                    'listing_title': listing_title,
                    'url': url,
                    'not_available': not_available,
                },
                # create_defaults REPLACES defaults when the row does not exist
                # yet (Django 5), and House Baratheon has no Miniature Market
                # rows to update, so the link fields must be repeated here.
                create_defaults={
                    'listing_title': listing_title,
                    'url': url,
                    'not_available': not_available,
                    'price': price,
                    'in_stock': in_stock,
                    'last_seen': timezone.now(),
                },
            )
            self.stdout.write(f'  seeded MM: {gw_sku}')
            seeded += 1

        self.stdout.write(self.style.SUCCESS(
            f'seed_mm_asoiaf_house_baratheon_prices complete. {seeded} record(s) seeded.'
        ))
