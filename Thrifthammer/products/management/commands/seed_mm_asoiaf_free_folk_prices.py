"""
Management command: seed_mm_asoiaf_free_folk_prices

Seeds Miniature Market URLs for A Song of Ice and Fire: Free Folk products.
The master "ASOIAF Miniature Market.xlsx" sheet (Title, Title_URL, Price; 40
rows spanning every house) had 3 Free Folk rows. 2 are kits that match an
existing catalog SKU; each match is confirmed by the manufacturer part number in
the Miniature Market URL, which is CMON's own SKU (CMNSIF409 = SIF409 Free Folk
Heroes 1, CMNSIF407 = SIF407 Followers of Bone). Every row was also read live on
miniaturemarket.com on 2026-11-10 with the Miniature Market scraper's own page
reader: price, stock state and part number all match the sheet (2 of 2).

The 3rd row, "Free Folk - Card Update Pack (2021)" (CMNSIFFP04, $11.99), is a
card pack, not a kit, and has no product in the catalog: not seeded.

The other 17 catalog SKUs are not in the sheet. They were searched for: the
product pages a web search returned (Frozen Shore Hunters, Attachments 1, Frozen
Shore Bear Riders, Savage Giants, Heroes 3, Cave Dweller Savages, Giant Spear
Throwers, Thenn Warriors, and the bare /cmnsif409.html form) all answer 404 on
miniaturemarket.com today (stale search-engine copies), so no row is created
for them.

Stock on 2026-11-10: both were out of stock; they keep their real price with
in_stock=False and self-heal when the scheduled Miniature Market refresh sees
them restocked.

create_defaults pattern: price, in_stock, last_seen are set only on creation so
scraper-set prices survive later runs. url, listing_title, not_available are in
defaults (always updated) and are also repeated in create_defaults, because
Django 5 uses create_defaults INSTEAD of defaults when the row does not exist
yet, as is the case for these new SKUs. Run ONCE by hand; it is not in the
Procfile.

Usage:
    python manage.py seed_mm_asoiaf_free_folk_prices
"""

from django.core.management.base import BaseCommand

MM_PRICES = [
    # (gw_sku, listing_title, price, url, in_stock, not_available)
    ('FREEFOLK-007', 'A Song of Ice & Fire: Free Folk - Followers of Bone Unit Box', 33.99, 'https://www.miniaturemarket.com/song-ice-fire-free-folk-followers-of-bone-unit-box-cmnsif407.html', False, False),  # CMNSIF407
    ('FREEFOLK-009', 'A Song of Ice & Fire: Free Folk - Heroes #1', 31.99, 'https://www.miniaturemarket.com/song-ice-fire-free-folk-heroes-1-cmnsif409.html', False, False),  # CMNSIF409
]


class Command(BaseCommand):
    """Seed Miniature Market URLs for A Song of Ice and Fire: Free Folk products."""

    help = 'seed_mm_asoiaf_free_folk_prices: MM URLs for Free Folk (2 of 19 SKUs confirmed)'

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
                # yet (Django 5), and Free Folk has no Miniature Market rows to
                # update, so the link fields must be repeated here.
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
            f'seed_mm_asoiaf_free_folk_prices complete. {seeded} record(s) seeded.'
        ))
