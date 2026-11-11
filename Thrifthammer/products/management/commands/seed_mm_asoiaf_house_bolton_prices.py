"""
Management command: seed_mm_asoiaf_house_bolton_prices

Seeds Miniature Market URLs for A Song of Ice and Fire: House Bolton products.
The master "ASOIAF Miniature Market.xlsx" sheet (Title, Title_URL, Price; 40
rows spanning every house) had 1 kit that matches a new House Bolton SKU:
"House Bolton - Heroes 1" (cmnsif506 = SIF506 Bolton Heroes, $31.99). The match
is confirmed by the manufacturer part number in the Miniature Market URL, which
is CMON's own SKU. The row was also read live on miniaturemarket.com on
2026-11-11 with the Miniature Market scraper's own page reader: price and part
number match the sheet. The sheet's stock column was blank (in stock) but the
live page is OUT of stock, so the row is seeded as out of stock (the live page
is the truth); it self-heals when the scheduled Miniature Market refresh sees it
restocked.

Dreadfort Spearmen (CMNSIF522) and Dreadfort Archers (CMNSIF523) are not in the
sheet and no Miniature Market page could be found for them (web search only
returned other houses and the Bolton Starter Set): no rows are created.

The six House Bolton products that already exist under the Neutrals faction
(NEUTRALS-001..006) already have their Miniature Market rows from
seed_mm_asoiaf_neutrals_prices; they are dual-tagged to House Bolton and need no
new rows.

create_defaults pattern: price, in_stock, last_seen are set only on creation so
scraper-set prices survive later runs. url, listing_title, not_available are in
defaults (always updated) and are also repeated in create_defaults, because
Django 5 uses create_defaults INSTEAD of defaults when the row does not exist
yet, as is the case for these new SKUs. Run ONCE by hand; it is not in the
Procfile.

Usage:
    python manage.py seed_mm_asoiaf_house_bolton_prices
"""

from django.core.management.base import BaseCommand

MM_PRICES = [
    # (gw_sku, listing_title, price, url, in_stock, not_available)
    ('BOLTON-001', 'A Song of Ice & Fire: House Bolton - Heroes 1', 31.99, 'https://www.miniaturemarket.com/song-ice-fire-house-bolton-heroes-1-cmnsif506.html', False, False),  # CMNSIF506
]


class Command(BaseCommand):
    """Seed Miniature Market URLs for A Song of Ice and Fire: House Bolton products."""

    help = 'seed_mm_asoiaf_house_bolton_prices: MM URLs for House Bolton (1 of 3 SKUs confirmed)'

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
                # yet (Django 5), and House Bolton has no Miniature Market rows
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
            f'seed_mm_asoiaf_house_bolton_prices complete. {seeded} record(s) seeded.'
        ))
