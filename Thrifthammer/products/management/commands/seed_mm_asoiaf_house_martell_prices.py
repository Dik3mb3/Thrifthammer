"""
Management command: seed_mm_asoiaf_house_martell_prices

Seeds Miniature Market URLs for A Song of Ice and Fire: House Martell products.
The master "ASOIAF Miniature Market.xlsx" sheet (Title, Title_URL, Price; 40 rows
spanning every house) had 5 kits that match the 12 new House Martell SKUs; each
match is confirmed by the manufacturer part number in the Miniature Market URL,
which is CMON's own SKU (cmnsif701 = SIF701 Martell Spearmen, cmnsif702 = SIF702
Sand Skirmishers, cmnsif703 = SIF703 Sunspear Dervishes, cmnsif707 = SIF707
Starfall Knights, cmnsif1709 = SIF709 Martell Heroes #1 Multilingual; Miniature
Market's own URL carries the stray "1" in "1709"). All 5 rows were also read live
on miniaturemarket.com on 2026-11-11 with the Miniature Market scraper's own page
reader: price matches the sheet for 5 of 5, stock differs by product (Spearmen and
Sunspear Dervishes in stock; Sand Skirmishers, Starfall Knights and Heroes #1 not).

The other 7 SKUs are not in the sheet. They were searched for: Miniature
Market's own suggest endpoint (the one the scraper uses) returns only these 5
pages for every Martell unit name, and 10 guessed URLs in the same pattern
(Starter Set, Sunspear Royal Guard, Dune Vipers, Starfall Outriders, Darkstar
Retinue, Heroes #2 and Skyreach Bowmen) all answer 404 on miniaturemarket.com
today, so no row is created for them.

Out-of-stock rows keep their real price with in_stock=False and self-heal when
the scheduled Miniature Market refresh sees them restocked.

create_defaults pattern: price, in_stock, last_seen are set only on creation so
scraper-set prices survive later runs. url, listing_title, not_available are in
defaults (always updated) and are also repeated in create_defaults, because
Django 5 uses create_defaults INSTEAD of defaults when the row does not exist
yet, as is the case for these new SKUs. Run ONCE by hand; it is not in the
Procfile.

Usage:
    python manage.py seed_mm_asoiaf_house_martell_prices
"""

from django.core.management.base import BaseCommand

MM_PRICES = [
    # (gw_sku, listing_title, price, url, in_stock, not_available)
    ('MARTELL-002', 'A Song of Ice & Fire: House Martell - Spearmen', 30.99, 'https://www.miniaturemarket.com/song-ice-fire-house-martell-spearmen-cmnsif701.html', True, False),  # CMNSIF701
    ('MARTELL-003', 'A Song of Ice & Fire: House Martell - Sand Skirmishers', 30.99, 'https://www.miniaturemarket.com/song-ice-fire-house-martell-sand-skirmishers-cmnsif702.html', False, False),  # CMNSIF702
    ('MARTELL-004', 'A Song of Ice & Fire: House Martell - Sunspear Dervishes', 30.99, 'https://www.miniaturemarket.com/song-ice-fire-house-martell-sunspear-dervishes-cmnsif703.html', True, False),  # CMNSIF703
    ('MARTELL-008', 'A Song of Ice & Fire: House Martell - Starfall Knights', 31.99, 'https://www.miniaturemarket.com/song-ice-fire-house-martell-starfall-knights-cmnsif707.html', False, False),  # CMNSIF707
    ('MARTELL-010', 'A Song of Ice & Fire: House Martell - Heroes #1 (Multilingual)', 31.99, 'https://www.miniaturemarket.com/song-ice-fire-house-martell-heroes-1-multilingual-cmnsif1709.html', False, False),  # CMNSIF1709 (typo for SIF709), Multilingual
]


class Command(BaseCommand):
    """Seed Miniature Market URLs for A Song of Ice and Fire: House Martell products."""

    help = 'seed_mm_asoiaf_house_martell_prices: MM URLs for House Martell (5 of 12 SKUs confirmed)'

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
                # yet (Django 5), and House Martell has no Miniature Market
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
            f'seed_mm_asoiaf_house_martell_prices complete. {seeded} record(s) seeded.'
        ))
