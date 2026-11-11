"""
Management command: seed_mm_asoiaf_house_targaryen_prices

Seeds Miniature Market URLs for A Song of Ice and Fire: House Targaryen products.
The master "ASOIAF Miniature Market.xlsx" sheet (Title, Title_URL, Price; 40 rows
spanning every house) had 5 kits that match the 14 new House Targaryen SKUs; each
match is confirmed by the manufacturer part number in the Miniature Market URL,
which is CMON's own SKU (cmnsif615 = SIF615 Targaryen Heroes 3, cmnsif605 =
SIF605 Freedmen, cmnsif603 = SIF603 Dothraki Outriders, cmnsif602 = SIF602
Dothraki Veterans, cmnsif610 = SIF610 Targaryen Heroes 2). All 5 rows were also
read live on miniaturemarket.com on 2026-11-11 with the Miniature Market
scraper's own page reader: price and stock state match the sheet (5 of 5).

The other 9 SKUs are not in the sheet. They were searched for: the product pages a
web search returned (Starter Set, Brazen Beasts, Heroes 1, Dothraki Hrakkars,
Unsullied Swordmasters, Pit Fighters, and the bare cmnsif610/cmnsif615 forms) all
answer 404 on miniaturemarket.com today (stale search-engine copies), so no row
is created for them.

The three Stormcrow products that are also on the House Targaryen page already
exist under the Neutrals faction (NEUTRALS-011..013), already have their Miniature
Market rows from seed_mm_asoiaf_neutrals_prices, and are dual-tagged to House
Targaryen: no new rows.

Stock on 2026-11-11: only Dothraki Outriders was in stock; the other four keep
their real price with in_stock=False and self-heal when the scheduled Miniature
Market refresh sees them restocked.

create_defaults pattern: price, in_stock, last_seen are set only on creation so
scraper-set prices survive later runs. url, listing_title, not_available are in
defaults (always updated) and are also repeated in create_defaults, because
Django 5 uses create_defaults INSTEAD of defaults when the row does not exist
yet, as is the case for these new SKUs. Run ONCE by hand; it is not in the
Procfile.

Usage:
    python manage.py seed_mm_asoiaf_house_targaryen_prices
"""

from django.core.management.base import BaseCommand

MM_PRICES = [
    # (gw_sku, listing_title, price, url, in_stock, not_available)
    ('TARGARYEN-003', 'A Song of Ice & Fire: House Targaryen - Dothraki Veterans', 31.99, 'https://www.miniaturemarket.com/song-ice-fire-house-targaryen-dothraki-veterans-cmnsif602.html', False, False),  # CMNSIF602
    ('TARGARYEN-004', 'A Song of Ice & Fire: House Targaryen - Dothraki Outriders', 31.99, 'https://www.miniaturemarket.com/song-ice-fire-house-targaryen-dothraki-outriders-cmnsif603.html', True, False),  # CMNSIF603
    ('TARGARYEN-006', 'A Song of Ice & Fire: House Targaryen - Freedmen', 24.99, 'https://www.miniaturemarket.com/song-ice-fire-house-targaryen-freedmen-cmnsif605.html', False, False),  # CMNSIF605
    ('TARGARYEN-011', 'A Song of Ice & Fire: House Targaryen - Heroes #2', 31.99, 'https://www.miniaturemarket.com/song-ice-fire-house-targaryen-heroes-2-cmnsif610.html', False, False),  # CMNSIF610
    ('TARGARYEN-014', 'A Song of Ice & Fire: House Targaryen - Heroes #3', 31.99, 'https://www.miniaturemarket.com/song-ice-fire-house-targaryen-heroes-3-cmnsif615.html', False, False),  # CMNSIF615
]


class Command(BaseCommand):
    """Seed Miniature Market URLs for A Song of Ice and Fire: House Targaryen products."""

    help = 'seed_mm_asoiaf_house_targaryen_prices: MM URLs for House Targaryen (5 of 14 SKUs confirmed)'

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
                # yet (Django 5), and House Targaryen has no Miniature Market
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
            f'seed_mm_asoiaf_house_targaryen_prices complete. {seeded} record(s) seeded.'
        ))
