"""
Management command: seed_mm_asoiaf_house_greyjoy_prices

Seeds Miniature Market URLs for A Song of Ice and Fire: House Greyjoy products.
The master "ASOIAF Miniature Market.xlsx" sheet (Title, Title_URL, Price; 40 rows
spanning every house) had 4 kits that match the 13 new House Greyjoy SKUs; each
match is confirmed by the manufacturer part number in the Miniature Market URL,
which is CMON's own SKU (cmnsif901 = SIF901 Ironborn Reavers, cmnsif902 = SIF902
Ironborn Bowmen, cmnsif905 = SIF905 House Harlaw Reapers, cmnsif1909 = SIF909
Greyjoy Heroes #1 Multilingual; Miniature Market's own URL carries the stray "1"
in "1909"). All 4 rows were also read live on miniaturemarket.com on 2026-11-11
with the Miniature Market scraper's own page reader: price matches the sheet for 4
of 4, stock differs by product (only Ironborn Reavers in stock).

The other 9 SKUs are not in the sheet. They were searched for: Miniature
Market's own suggest endpoint (the one the scraper uses) returns only these 4
pages for every Greyjoy unit name, and 11 guessed URLs in the same pattern
(Starter Set, Ironmakers, Ironborn Trappers, Blacktyde Chosen, Drowned Men,
Silenced Men, Heroes #2, Stony Shore Pillagers and Iron Victory Crew) all answer
404 on miniaturemarket.com today, so no row is created for them.

Out-of-stock rows keep their real price with in_stock=False and self-heal when
the scheduled Miniature Market refresh sees them restocked.

create_defaults pattern: price, in_stock, last_seen are set only on creation so
scraper-set prices survive later runs. url, listing_title, not_available are in
defaults (always updated) and are also repeated in create_defaults, because
Django 5 uses create_defaults INSTEAD of defaults when the row does not exist
yet, as is the case for these new SKUs. Run ONCE by hand; it is not in the
Procfile.

Usage:
    python manage.py seed_mm_asoiaf_house_greyjoy_prices
"""

from django.core.management.base import BaseCommand

MM_PRICES = [
    # (gw_sku, listing_title, price, url, in_stock, not_available)
    ('GREYJOY-002', 'A Song of Ice & Fire: House Greyjoy - Ironborn Reavers', 30.99, 'https://www.miniaturemarket.com/song-ice-fire-house-greyjoy-ironborn-reavers-cmnsif901.html', True, False),  # CMNSIF901
    ('GREYJOY-003', 'A Song of Ice & Fire: House Greyjoy - Ironborn Bowmen', 30.99, 'https://www.miniaturemarket.com/song-ice-fire-house-greyjoy-ironborn-bowmen-cmnsif902.html', False, False),  # CMNSIF902
    ('GREYJOY-006', 'A Song of Ice & Fire: House Greyjoy - House Harlaw Reapers', 30.99, 'https://www.miniaturemarket.com/song-ice-fire-house-greyjoy-house-harlaw-reapers-cmnsif905.html', False, False),  # CMNSIF905
    ('GREYJOY-010', 'A Song of Ice & Fire: House Greyjoy - Heroes #1 (Multilingual)', 31.99, 'https://www.miniaturemarket.com/song-ice-fire-house-greyjoy-heroes-1-multilingual-cmnsif1909.html', False, False),  # CMNSIF1909 (typo for SIF909), Multilingual
]


class Command(BaseCommand):
    """Seed Miniature Market URLs for A Song of Ice and Fire: House Greyjoy products."""

    help = 'seed_mm_asoiaf_house_greyjoy_prices: MM URLs for House Greyjoy (4 of 13 SKUs confirmed)'

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
                # yet (Django 5), and House Greyjoy has no Miniature Market
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
            f'seed_mm_asoiaf_house_greyjoy_prices complete. {seeded} record(s) seeded.'
        ))
