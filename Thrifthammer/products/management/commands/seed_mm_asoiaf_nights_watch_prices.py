"""
Management command: seed_mm_asoiaf_nights_watch_prices

Seeds Miniature Market URLs for A Song of Ice and Fire: Night's Watch products.
The master "ASOIAF Miniature Market.xlsx" sheet (Title, Title_URL, Price; 40
rows spanning every house) had 4 Night's Watch rows. 3 are kits that match an
existing catalog SKU; each match is confirmed by the manufacturer part number in
the Miniature Market URL, which is CMON's own SKU (CMNSIF310-ML = SIF310
Night's Watch Heroes 2, CMNSIF305-ML Ranger Hunters, CMNSIF313 Shadow Tower
Spearmen). Every row was also read live on miniaturemarket.com on 2026-11-09 with
the Miniature Market scraper's own page reader: price, stock state and part
number all match the sheet (3 of 3).

The 4th row, "Night's Watch - Card Update Pack (2021)" (CMNSIFFP03, $15.99), is
a card pack, not a kit, and has no product in the catalog: not seeded.

"(Multilingual)" in a title and the "-ML" part-number suffix mark Miniature
Market's multilingual printing of the same CMON box.

The other 12 catalog SKUs are not in the sheet. They were searched for: the
product pages a web search returned (Ranger Trackers, Ranger Vanguard,
Attachments #1, Heroes #1, Heroes #3) all answer 404 on miniaturemarket.com
today (stale search-engine copies), so no row is created for them.

Stock on 2026-11-09: only Heroes 2 was in stock; the other two keep their real
price with in_stock=False and self-heal when the scheduled Miniature Market
refresh sees them restocked.

create_defaults pattern: price, in_stock, last_seen are set only on creation so
scraper-set prices survive later runs. url, listing_title, not_available are in
defaults (always updated) and are also repeated in create_defaults, because
Django 5 uses create_defaults INSTEAD of defaults when the row does not exist
yet, as is the case for these new SKUs. Run ONCE by hand; it is not in the
Procfile.

Usage:
    python manage.py seed_mm_asoiaf_nights_watch_prices
"""

from django.core.management.base import BaseCommand

MM_PRICES = [
    # (gw_sku, listing_title, price, url, in_stock, not_available)
    ('NIGHTSWATCH-006', "A Song of Ice & Fire: Night's Watch - Ranger Hunters (Multilingual)", 30.99, 'https://www.miniaturemarket.com/song-ice-fire-nights-watch-ranger-hunters-multilingual-cmnsif305-ml.html', False, False),  # CMNSIF305-ML
    ('NIGHTSWATCH-011', "A Song of Ice & Fire: Night's Watch - Heroes #2 (Multilingual)", 31.99, 'https://www.miniaturemarket.com/song-ice-fire-nights-watch-heroes-2-multilingual-cmnsif310-ml.html', True, False),  # CMNSIF310-ML
    ('NIGHTSWATCH-013', "A Song of Ice & Fire: Night's Watch - Shadow Tower Spearmen", 30.99, 'https://www.miniaturemarket.com/song-ice-fire-nights-watch-shadow-tower-spearmen-cmnsif313.html', False, False),  # CMNSIF313
]


class Command(BaseCommand):
    """Seed Miniature Market URLs for A Song of Ice and Fire: Night's Watch products."""

    help = "seed_mm_asoiaf_nights_watch_prices: MM URLs for Night's Watch (3 of 15 SKUs confirmed)"

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
                # yet (Django 5), and Night's Watch has no Miniature Market rows
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
            f'seed_mm_asoiaf_nights_watch_prices complete. {seeded} record(s) seeded.'
        ))
