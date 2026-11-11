"""
Management command: seed_nk_asoiaf_house_greyjoy_prices

Seeds Noble Knight URLs for A Song of Ice and Fire: House Greyjoy products.
The user-supplied "Noble Knight - AOSIAF.xlsx" sheet had 11 kits that match the 13
new House Greyjoy SKUs; each match is confirmed by the stock number on the Noble
Knight page, which is CMON's own SKU (CMNSIF901 = SIF901 Ironborn Reavers,
CMNSIF009 = SIF009 Greyjoy Starter Set, and so on, shown in the trailing comment
on every row). All 11 rows were also read live on nobleknight.com on 2026-11-11
with the Noble Knight scraper's own session: stock number, price and in-stock
state match the sheet for 10 of 11 (all with a New copy; most pages offer "New &
Used Copy" and the price is the New price). The 11th, the Starter Set, is live at
$99.95 against the sheet's $129.95, so the live price is used (Noble Knight's own
Greyjoy product-line page shows the New "SW (MINT/New)" copy at $99.95). The
lower of the two price cells is the price.

The sheet was used first. The 2 SKUs missing from it were then searched for on
Noble Knight (NK's own Greyjoy product-line page, each page read live with the
scraper's own session on 2026-11-11):
  * Blacktyde Chosen (CMNSIF906) and Greyjoy Heroes #1 (CMNSIF909) each have a
    Noble Knight page, but it only sells a USED copy ("Used Copy" alone in the
    page title; $45.00 EX/NM and $35.00 EX/NM). This site tracks New prices only
    and the Noble Knight scraper cannot tell used from new, so no row is created.

Every URL carries the Noble Knight affiliate tag ?awid=1576.

create_defaults pattern: price, in_stock, last_seen are set only on creation so
scraper-set prices survive later runs. url, listing_title, not_available are in
defaults (always updated) and are also repeated in create_defaults, because
Django 5 uses create_defaults INSTEAD of defaults when the row does not exist
yet, as is the case for these new SKUs. Run ONCE by hand; it is not in the
Procfile.

Usage:
    python manage.py seed_nk_asoiaf_house_greyjoy_prices
"""

from django.core.management.base import BaseCommand

NK_PRICES = [
    # (gw_sku, listing_title, price, url, in_stock, not_available)
    ('GREYJOY-001', 'Greyjoy Starter Set', 99.95, 'https://www.nobleknight.com/P/2147870750/Greyjoy-Starter-Set?awid=1576', True, False),  # CMNSIF009, live price (sheet had $129.95)
    ('GREYJOY-002', 'Ironborn Reavers', 19.95, 'https://www.nobleknight.com/P/2147944580/Ironborn-Reavers?awid=1576', True, False),  # CMNSIF901
    ('GREYJOY-003', 'Ironborn Bowmen', 29.95, 'https://www.nobleknight.com/P/2147944546/Ironborn-Bowman?awid=1576', True, False),  # CMNSIF902
    ('GREYJOY-004', 'Ironmakers', 89.95, 'https://www.nobleknight.com/P/2147875266/Ironmakers?awid=1576', True, False),  # CMNSIF903
    ('GREYJOY-005', 'Ironborn Trappers', 29.95, 'https://www.nobleknight.com/P/2147875267/Ironborn-Trappers?awid=1576', True, False),  # CMNSIF904
    ('GREYJOY-006', 'House Harlaw Reapers', 29.95, 'https://www.nobleknight.com/P/2147953174/House-Harlaw-Reapers?awid=1576', True, False),  # CMNSIF905
    ('GREYJOY-008', 'Drowned Men', 39.95, 'https://www.nobleknight.com/P/2147976068/Drowned-Men?awid=1576', True, False),  # CMNSIF907
    ('GREYJOY-009', 'Silenced Men', 79.95, 'https://www.nobleknight.com/P/2147942069/Silenced-Men?awid=1576', True, False),  # CMNSIF908
    ('GREYJOY-011', 'Greyjoy Heroes #2', 39.95, 'https://www.nobleknight.com/P/2147954218/Greyjoy-Heroes-2?awid=1576', True, False),  # CMNSIF910
    ('GREYJOY-012', 'Stony Shore Pillagers', 39.95, 'https://www.nobleknight.com/P/2148097145/Stony-Shore-Pillagers?awid=1576', True, False),  # CMNSIF911
    ('GREYJOY-013', 'Iron Victory Crew', 49.95, 'https://www.nobleknight.com/P/2148179439/Iron-Victory-Crew?awid=1576', True, False),  # CMNSIF912
]


class Command(BaseCommand):
    """Seed Noble Knight URLs for A Song of Ice and Fire: House Greyjoy products."""

    help = 'seed_nk_asoiaf_house_greyjoy_prices: NK URLs for House Greyjoy (11 of 13 SKUs)'

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
                # yet (Django 5), and House Greyjoy has no Noble Knight rows
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
            self.stdout.write(f'  seeded NK: {gw_sku}')
            seeded += 1

        self.stdout.write(self.style.SUCCESS(
            f'seed_nk_asoiaf_house_greyjoy_prices complete. {seeded} record(s) seeded.'
        ))
