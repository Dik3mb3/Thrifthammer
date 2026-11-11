"""
Management command: seed_nk_asoiaf_house_stark_prices

Seeds Noble Knight URLs for A Song of Ice and Fire: House Stark products.
The user-supplied "Noble Knight - AOSIAF.xlsx" sheet (122 rows spanning every
house; columns Title, Title_URL, stock number, year, category, condition,
price, add-to-cart) had 17 rows in the Stark category plus no other row
carrying a House Stark stock code. 15 are kits that match an existing catalog
SKU; each match is confirmed by the stock number on the Noble Knight page,
which is CMON's own SKU (CMNSIF102 = SIF102 Stark Outriders, CMNSIF01A =
SIF001A Stark Starter Set, and so on, shown in the trailing comment on every
row). Every row was also read live on nobleknight.com on 2026-11-08 with the
Noble Knight scraper's own session: page title, stock number, price and
in-stock state all match the sheet (15 of 15).

The 2 other Stark rows, "House Stark Dice" and "Stark Deluxe Activation
Banner", are accessories with no product in the catalog: not seeded.

The sheet was used first. The 5 catalog SKUs missing from it were then searched
for on Noble Knight (web search, then each page read live with the scraper's own
session on 2026-11-08). 3 have a page: Tully Cavaliers Unit Box (CMNSIF108, out
of print: the page has no price, so the row keeps the link with price None and
in_stock False) is seeded below, marked "found by search". Stark Heroes #2
(CMNSIF110, $85.00) and Stark Attachments #1 (CMNSIF116, $25.00) are NOT seeded:
their pages only sell a USED copy ("Used Copy" in the page title), and this
site tracks New prices only. The Noble Knight scraper refreshes every row that
has a stored URL and cannot tell used from new, so those two rows have no link
(they were cleared in prod on 2026-11-08 at the owner's decision). No US Noble
Knight page exists for CMON SIF101 Stark Sworn Swords (only loose figures) or
SIF119 Winterfell Guards (a European-store page only), so no row is created for
those two.

Every URL carries the Noble Knight affiliate tag ?awid=1576.

create_defaults pattern: price, in_stock, last_seen are set only on creation so
scraper-set prices survive later runs. url, listing_title, not_available are in
defaults (always updated) and are also repeated in create_defaults, because
Django 5 uses create_defaults INSTEAD of defaults when the row does not exist
yet, as is the case for these new SKUs. Run ONCE by hand; it is not in the
Procfile.

Usage:
    python manage.py seed_nk_asoiaf_house_stark_prices
"""

from django.core.management.base import BaseCommand

NK_PRICES = [
    # (gw_sku, listing_title, price, url, in_stock, not_available)
    ('STARK-001', 'Stark Starter Set', 125.00, 'https://www.nobleknight.com/P/2147959895/Stark-Starter-Set?awid=1576', True, False),  # CMNSIF01A
    ('STARK-003', 'Stark Outriders', 39.95, 'https://www.nobleknight.com/P/2147745404/Stark-Outriders?awid=1576', True, False),  # CMNSIF102
    ('STARK-004', 'Umber Berserkers', 29.95, 'https://www.nobleknight.com/P/2147736773/Umber-Berserkers?awid=1576', True, False),  # CMNSIF103
    ('STARK-005', 'Umber Greataxes', 69.95, 'https://www.nobleknight.com/P/2147736518/Umber-Greataxes?awid=1576', True, False),  # CMNSIF104
    ('STARK-006', 'Tully Sworn Shields', 24.95, 'https://www.nobleknight.com/P/2147735701/Tully-Sworn-Shields?awid=1576', True, False),  # CMNSIF105
    ('STARK-007', 'Stark Bowmen Unit Box', 19.95, 'https://www.nobleknight.com/P/2147728858/Stark-Bowmen-Unit-Box?awid=1576', True, False),  # CMNSIF106
    ('STARK-008', 'Crannogman Trackers', 32.95, 'https://www.nobleknight.com/P/2147746332/Stark-Crannogman-Trackers?awid=1576', True, False),  # CMNSIF107
    ('STARK-010', 'Stark Heroes #1', 49.95, 'https://www.nobleknight.com/P/2147728874/Stark-Heroes-1?awid=1576', True, False),  # CMNSIF109
    ('STARK-012', 'Mormont She-Bears', 39.95, 'https://www.nobleknight.com/P/2147876774/Mormont-She-Bears?awid=1576', True, False),  # CMNSIF111
    ('STARK-013', 'Mormont Bruisers', 29.95, 'https://www.nobleknight.com/P/2147954228/Mormont-Bruisers?awid=1576', True, False),  # CMNSIF112
    ('STARK-014', 'Karstark Loyalists', 49.95, 'https://www.nobleknight.com/P/2147976063/Karstark-Loyalists?awid=1576', True, False),  # CMNSIF113
    ('STARK-015', 'House Karstark Spearmen', 29.95, 'https://www.nobleknight.com/P/2147953186/House-Karstark-Spearmen?awid=1576', True, False),  # CMNSIF114
    ('STARK-016', 'Stark Heroes #3', 129.95, 'https://www.nobleknight.com/P/2147976062/Stark-Heroes-3?awid=1576', True, False),  # CMNSIF115
    ('STARK-018', 'Crannogman Bog Devils', 29.95, 'https://www.nobleknight.com/P/2148033504/Crannogman-Bog-Devils?awid=1576', True, False),  # CMNSIF117
    ('STARK-019', 'House Umber Ravagers', 44.95, 'https://www.nobleknight.com/P/2148097152/House-Umber-Ravagers?awid=1576', True, False),  # CMNSIF118
    # Found by search after the sheet was used (not in the sheet), each page read live:
    ('STARK-009', 'Tully Cavaliers Unit Box', None, 'https://www.nobleknight.com/P/2147766446/Stark-Tully-Cavaliers-Unit-Box?awid=1576', False, False),  # CMNSIF108, out of print, no price on the page
]


class Command(BaseCommand):
    """Seed Noble Knight URLs for A Song of Ice and Fire: House Stark products."""

    help = 'seed_nk_asoiaf_house_stark_prices: NK URLs for House Stark (16 of 20 SKUs confirmed)'

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
                # yet (Django 5), and House Stark has no Noble Knight rows to
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
            f'seed_nk_asoiaf_house_stark_prices complete. {seeded} record(s) seeded.'
        ))
