"""
Management command: seed_nk_asoiaf_house_bolton_prices

Seeds Noble Knight URLs for A Song of Ice and Fire: House Bolton products.
The user-supplied "Noble Knight - AOSIAF.xlsx" sheet had 2 kits that match the 3
new House Bolton SKUs; each match is confirmed by the stock number on the Noble
Knight page, which is CMON's own SKU (CMNSIF506 = SIF506 Bolton Heroes,
CMNSIF523 = SIF523 Dreadfort Archers, shown in the trailing comment on every
row). Both rows were also read live on nobleknight.com on 2026-11-11 with the
Noble Knight scraper's own session: stock number, price and in-stock state match
the sheet (2 of 2, both with a New copy).

The third new SKU, Dreadfort Spearmen (CMNSIF522), is not in the sheet. It was
searched for on Noble Knight (web search, then the neighbouring product ids of
the other new Bolton pages): no page could be found, so no row is created.

The six House Bolton products that already exist under the Neutrals faction
(NEUTRALS-001..006) already have their Noble Knight rows from
seed_nk_asoiaf_neutrals_prices; they are dual-tagged to House Bolton and need no
new rows. Sheet rows for Bolton accessories (Deluxe Activation Banners) and the
Roose Bolton game night kit are not products: not seeded.

Every URL carries the Noble Knight affiliate tag ?awid=1576.

create_defaults pattern: price, in_stock, last_seen are set only on creation so
scraper-set prices survive later runs. url, listing_title, not_available are in
defaults (always updated) and are also repeated in create_defaults, because
Django 5 uses create_defaults INSTEAD of defaults when the row does not exist
yet, as is the case for these new SKUs. Run ONCE by hand; it is not in the
Procfile.

Usage:
    python manage.py seed_nk_asoiaf_house_bolton_prices
"""

from django.core.management.base import BaseCommand

NK_PRICES = [
    # (gw_sku, listing_title, price, url, in_stock, not_available)
    ('BOLTON-001', 'Bolton Heroes #1', 79.95, 'https://www.nobleknight.com/P/2148077588/Bolton-Heroes-1?awid=1576', True, False),  # CMNSIF506
    ('BOLTON-003', 'Dreadfort Archers', 21.95, 'https://www.nobleknight.com/P/2148077590/Dreadfort-Archers?awid=1576', True, False),  # CMNSIF523
]


class Command(BaseCommand):
    """Seed Noble Knight URLs for A Song of Ice and Fire: House Bolton products."""

    help = 'seed_nk_asoiaf_house_bolton_prices: NK URLs for House Bolton (2 of 3 SKUs confirmed)'

    def handle(self, *args, **options):
        """Create or update the Noble Knight price row for each confirmed SKU."""
        from django.utils import timezone

        from prices.models import CurrentPrice
        from products.models import Product, Retailer

        nk_retailer = Retailer.objects.get(slug='noble-knight-games')
        seeded = 0

        for (gw_sku, listing_title, price, url, in_stock, not_available) in NK_PRICES:
            product = Product.objects.get(gw_sku=gw_sku, category__slug='asoiaf')
            CurrentPrice.objects.update_or_create(
                product=product,
                retailer=nk_retailer,
                defaults={
                    'listing_title': listing_title,
                    'url': url,
                    'not_available': not_available,
                },
                # create_defaults REPLACES defaults when the row does not exist
                # yet (Django 5), and House Bolton has no Noble Knight rows to
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
            self.stdout.write(f'  seeded NK: {gw_sku}')
            seeded += 1

        self.stdout.write(self.style.SUCCESS(
            f'seed_nk_asoiaf_house_bolton_prices complete. {seeded} record(s) seeded.'
        ))
