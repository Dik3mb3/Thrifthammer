"""
Management command: seed_mm_asoiaf_brotherhood_prices

Seeds Miniature Market URLs for A Song of Ice and Fire: Brotherhood Without
Banners products. The master "ASOIAF Miniature Market.xlsx" sheet (Title,
Title_URL, Price; 40 rows spanning every house) had 1 kit that matches one of the
3 SKUs: "Brotherhood without Banners - Heroes #1 (Multilingual)" (cmnsif015 =
SIF015 Heroes 1, $35.99). The match is confirmed by the manufacturer part number
in the Miniature Market URL, which is CMON's own SKU. The row was also read live
on miniaturemarket.com on 2026-11-11 with the Miniature Market scraper's own page
reader: price and stock state match the sheet (in stock).

The other 2 SKUs (Starter Set, Sworn Knights) are not in the sheet. They were
searched for: the Sworn Knights pages a web search returned (both URL forms) and
the alternate Heroes URL all answer 404 on miniaturemarket.com today (stale
search-engine copies), and no Starter Set page exists: no rows are created.

create_defaults pattern: price, in_stock, last_seen are set only on creation so
scraper-set prices survive later runs. url, listing_title, not_available are in
defaults (always updated) and are also repeated in create_defaults, because
Django 5 uses create_defaults INSTEAD of defaults when the row does not exist
yet, as is the case for these new SKUs. Run ONCE by hand; it is not in the
Procfile.

Usage:
    python manage.py seed_mm_asoiaf_brotherhood_prices
"""

from django.core.management.base import BaseCommand

MM_PRICES = [
    # (gw_sku, listing_title, price, url, in_stock, not_available)
    ('BROTHERHOOD-003', 'A Song of Ice & Fire: Brotherhood without Banners - Heroes #1 (Multilingual)', 35.99, 'https://www.miniaturemarket.com/song-ice-fire-brotherhood-without-banners-heroes-1-multilingual-cmnsif015.html', True, False),  # CMNSIF015
]


class Command(BaseCommand):
    """Seed Miniature Market URLs for A Song of Ice and Fire: Brotherhood Without Banners products."""

    help = 'seed_mm_asoiaf_brotherhood_prices: MM URLs for Brotherhood Without Banners (1 of 3 SKUs confirmed)'

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
                # yet (Django 5), and this faction has no Miniature Market rows
                # to update, so the link fields must be repeated here.
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
            f'seed_mm_asoiaf_brotherhood_prices complete. {seeded} record(s) seeded.'
        ))
