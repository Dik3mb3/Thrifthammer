"""
Management command: seed_nk_asoiaf_brotherhood_prices

Seeds Noble Knight URLs for A Song of Ice and Fire: Brotherhood Without Banners
products. The user-supplied "Noble Knight - AOSIAF.xlsx" sheet had 2 kits that
match the 3 SKUs; each match is confirmed by the stock number on the Noble Knight
page, which is CMON's own SKU (CMNSIF015 = SIF015 Heroes 1, CMNSIF014 = SIF014
Sworn Knights, shown in the trailing comment on every row). Both rows were also
read live on nobleknight.com on 2026-11-11 with the Noble Knight scraper's own
session: stock number, price and in-stock state match the sheet (2 of 2, both
with a New copy).

The sheet was used first. The 1 SKU missing from it, the Starter Set (CMNSIF010),
was then searched for on Noble Knight (web search, then the page read live with
the scraper's own session on 2026-11-11): the page exists but is out of print
with no price and no add-to-cart button, so the row keeps the link with price
None and in_stock False (same as Stark's Tully Cavaliers).

Every URL carries the Noble Knight affiliate tag ?awid=1576.

create_defaults pattern: price, in_stock, last_seen are set only on creation so
scraper-set prices survive later runs. url, listing_title, not_available are in
defaults (always updated) and are also repeated in create_defaults, because
Django 5 uses create_defaults INSTEAD of defaults when the row does not exist
yet, as is the case for these new SKUs. Run ONCE by hand; it is not in the
Procfile.

Usage:
    python manage.py seed_nk_asoiaf_brotherhood_prices
"""

from django.core.management.base import BaseCommand

NK_PRICES = [
    # (gw_sku, listing_title, price, url, in_stock, not_available)
    ('BROTHERHOOD-002', 'Brotherhood Sworn Knights', 39.95, 'https://www.nobleknight.com/P/2148242043/Brotherhood-Sworn-Knights?awid=1576', True, False),  # CMNSIF014
    ('BROTHERHOOD-003', 'Brotherhood Without Banners Heroes #1', 29.95, 'https://www.nobleknight.com/P/2148242042/Brotherhood-Without-Banners-Heroes-1?awid=1576', True, False),  # CMNSIF015
    # Found by search after the sheet was used (not in the sheet), page read live;
    # out of print, no price on the page, so the link is kept with price None:
    ('BROTHERHOOD-001', 'Brotherhood Without Banners Starter Set', None, 'https://www.nobleknight.com/P/2148242036/Brotherhood-Without-Banners-Starter-Set?awid=1576', False, False),  # CMNSIF010
]


class Command(BaseCommand):
    """Seed Noble Knight URLs for A Song of Ice and Fire: Brotherhood Without Banners products."""

    help = 'seed_nk_asoiaf_brotherhood_prices: NK URLs for Brotherhood Without Banners (3 of 3 SKUs confirmed)'

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
                # yet (Django 5), and this faction has no Noble Knight rows to
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
            f'seed_nk_asoiaf_brotherhood_prices complete. {seeded} record(s) seeded.'
        ))
