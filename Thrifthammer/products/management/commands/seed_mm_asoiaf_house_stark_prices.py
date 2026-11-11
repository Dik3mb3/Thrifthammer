"""
Management command: seed_mm_asoiaf_house_stark_prices

Seeds Miniature Market URLs for A Song of Ice and Fire: House Stark products.
The master "ASOIAF Miniature Market.xlsx" sheet (Title, Title_URL, Price; 40
rows spanning every house) had 8 House Stark rows. 7 are kits that match an
existing catalog SKU; each match is confirmed by the manufacturer part number
in the Miniature Market URL, which is CMON's own SKU (CMNSIF104 = SIF104 Umber
Greataxes, CMNSIF105 Tully Sworn Shields, CMNSIF106 Stark Bowmen, CMNSIF107
Crannogman Trackers, CMNSIF111 Mormont She-Bears, CMNSIF114 Karstark Spearmen,
CMNSIF118 House Umber Ravagers). Every row was also confirmed live on
miniaturemarket.com on 2026-11-08 (page title, part number and price match the
sheet).

The 8th row, "House Stark Card Update Pack (2021)" (CMNSIFFP01, $15.99), is a
card pack, not a kit, and has no product in the catalog: not seeded.

"(Multilingual)" in a title and the "-ML" part-number suffix mark Miniature
Market's multilingual printing of the same CMON box.

Stock on 2026-11-08: only Tully Sworn Shields was in stock; the other six keep
their real price with in_stock=False and self-heal when the scheduled
Miniature Market refresh sees them restocked.

create_defaults pattern: price, in_stock, last_seen are set only on creation so
scraper-set prices survive later runs. url, listing_title, not_available are in
defaults (always updated) and are also repeated in create_defaults, because
Django 5 uses create_defaults INSTEAD of defaults when the row does not exist
yet, as is the case for these new SKUs. Run ONCE by hand; it is not in the
Procfile.

Usage:
    python manage.py seed_mm_asoiaf_house_stark_prices
"""

from django.core.management.base import BaseCommand

MM_PRICES = [
    # (gw_sku, listing_title, price, url, in_stock, not_available)
    ('STARK-005', 'A Song of Ice & Fire: House Stark - Umber Greataxes (Multilingual)', 30.99, 'https://www.miniaturemarket.com/song-ice-fire-house-stark-umber-greataxes-multilingual-cmnsif104-ml.html', False, False),  # CMNSIF104-ML
    ('STARK-006', 'A Song of Ice & Fire: House Stark - Tully Sworn Shields (Multilingual)', 30.99, 'https://www.miniaturemarket.com/song-ice-fire-house-stark-tully-sworn-shields-multilingual-cmnsif105-ml.html', True, False),  # CMNSIF105-ML
    ('STARK-007', 'A Song of Ice & Fire: House Stark - Bowmen (Multilingual)', 22.99, 'https://www.miniaturemarket.com/song-ice-fire-house-stark-bowmen-multilingual-cmnsif106-ml.html', False, False),  # CMNSIF106-ML
    ('STARK-008', 'A Song of Ice & Fire: House Stark - Crannogman Trackers', 30.99, 'https://www.miniaturemarket.com/song-ice-fire-house-stark-crannogman-trackers-cmnsif107.html', False, False),  # CMNSIF107
    ('STARK-012', 'A Song of Ice & Fire: House Stark - Mormont She-Bears (Multilingual)', 30.99, 'https://www.miniaturemarket.com/song-ice-fire-house-stark-mormont-she-bears-multilingual-cmnsif111-ml.html', False, False),  # CMNSIF111-ML
    ('STARK-015', 'A Song of Ice & Fire: House Stark - House Karstark Spearmen', 30.99, 'https://www.miniaturemarket.com/song-ice-fire-house-stark-house-karstark-spearmen-cmnsif114.html', False, False),  # CMNSIF114
    ('STARK-019', 'A Song of Ice & Fire: House Stark - House Umber Ravagers', 35.99, 'https://www.miniaturemarket.com/song-ice-fire-house-stark-house-umber-ravagers-cmnsif118.html', False, False),  # CMNSIF118
]


class Command(BaseCommand):
    """Seed Miniature Market URLs for A Song of Ice and Fire: House Stark products."""

    help = 'seed_mm_asoiaf_house_stark_prices: MM URLs for House Stark (7 of 20 SKUs confirmed)'

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
                # yet (Django 5), and House Stark has no Miniature Market rows
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
            f'seed_mm_asoiaf_house_stark_prices complete. {seeded} record(s) seeded.'
        ))
