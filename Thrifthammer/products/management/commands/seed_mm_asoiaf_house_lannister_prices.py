"""
Management command: seed_mm_asoiaf_house_lannister_prices

Seeds Miniature Market URLs for A Song of Ice and Fire: House Lannister
products. The master "ASOIAF Miniature Market.xlsx" sheet (Title, Title_URL,
Price; 40 rows spanning every house) had 5 House Lannister rows, all kits that
match an existing catalog SKU. Each match is confirmed by the manufacturer part
number in the Miniature Market URL, which is CMON's own SKU (CMNSIF201 = SIF201
Lannister Guardsmen, CMNSIF202 Halberdiers, CMNSIF207 Warrior's Sons, CMNSIF208
Poor Fellows, CMNSIF214 Clegane Brigands). Every row was also read live on
miniaturemarket.com on 2026-11-08 with the Miniature Market scraper's own page
reader: price, stock state and part number all match the sheet (5 of 5).

The other 14 catalog SKUs are not in the sheet. They were searched for: the
product pages a web search returned for six of them (Starter Set, Red Cloaks,
Crossbowmen, Attachments #1, Heroes #3, The Mountain's Men) and the same URL
pattern for the other eight all answer 404 on miniaturemarket.com today (stale
search-engine copies), so no row is created for them.

Stock on 2026-11-08: only Lannister Guardsmen was in stock; the other four keep
their real price with in_stock=False and self-heal when the scheduled
Miniature Market refresh sees them restocked.

create_defaults pattern: price, in_stock, last_seen are set only on creation so
scraper-set prices survive later runs. url, listing_title, not_available are in
defaults (always updated) and are also repeated in create_defaults, because
Django 5 uses create_defaults INSTEAD of defaults when the row does not exist
yet, as is the case for these new SKUs. Run ONCE by hand; it is not in the
Procfile.

Usage:
    python manage.py seed_mm_asoiaf_house_lannister_prices
"""

from django.core.management.base import BaseCommand

MM_PRICES = [
    # (gw_sku, listing_title, price, url, in_stock, not_available)
    ('LANNISTER-002', 'A Song of Ice & Fire: House Lannister - Guardsmen', 33.99, 'https://www.miniaturemarket.com/song-ice-fire-house-lannister-guardsmen-cmnsif201.html', True, False),  # CMNSIF201
    ('LANNISTER-003', 'A Song of Ice & Fire: House Lannister - Halberdiers', 33.99, 'https://www.miniaturemarket.com/song-ice-fire-house-lannister-halberdiers-cmnsif202.html', False, False),  # CMNSIF202
    ('LANNISTER-008', "A Song of Ice & Fire: House Lannister - Warrior's Sons Unit Box", 30.99, 'https://www.miniaturemarket.com/song-ice-fire-house-lannister-warriors-sons-unit-box-cmnsif207.html', False, False),  # CMNSIF207
    ('LANNISTER-009', 'A Song of Ice & Fire: House Lannister - Poor Fellows', 30.99, 'https://www.miniaturemarket.com/song-ice-fire-house-lannister-poor-fellows-cmnsif208.html', False, False),  # CMNSIF208
    ('LANNISTER-015', 'A Song of Ice & Fire: House Lannister - Clegane Brigands', 31.99, 'https://www.miniaturemarket.com/song-ice-fire-house-lannister-clegane-brigands-cmnsif214.html', False, False),  # CMNSIF214
]


class Command(BaseCommand):
    """Seed Miniature Market URLs for A Song of Ice and Fire: House Lannister products."""

    help = 'seed_mm_asoiaf_house_lannister_prices: MM URLs for House Lannister (5 of 19 SKUs confirmed)'

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
                # yet (Django 5), and House Lannister has no Miniature Market
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
            f'seed_mm_asoiaf_house_lannister_prices complete. {seeded} record(s) seeded.'
        ))
