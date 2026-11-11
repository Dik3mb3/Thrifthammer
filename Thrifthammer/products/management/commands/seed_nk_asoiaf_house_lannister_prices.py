"""
Management command: seed_nk_asoiaf_house_lannister_prices

Seeds Noble Knight URLs for A Song of Ice and Fire: House Lannister products.
The user-supplied "Noble Knight - AOSIAF.xlsx" sheet (122 rows spanning every
house; columns Title, Title_URL, stock number, year, category, condition,
price, add-to-cart) had 16 rows in the Lannister category. 14 are kits that
match an existing catalog SKU; each match is confirmed by the stock number on
the Noble Knight page, which is CMON's own SKU (CMNSIF201 = SIF201 Lannister
Guardsmen, CMNSIF214 = SIF214 Clegane Brigands, and so on, shown in the trailing
comment on every row). Every row was also read live on nobleknight.com on
2026-11-08 with the Noble Knight scraper's own session: stock number, price and
in-stock state all match the sheet (14 of 14). The lower of the two price cells
is the price (the other is the MSRP).

The 2 other Lannister rows, "House Lannister Dice" and "House Lannister Dice
Bag (Kickstarter Exclusive)", are accessories with no product in the catalog:
not seeded. The sheet's "Starter Set - Stark vs Lannister" (CMNSIF001) is the
old two-player box, a different product from the Lannister-only Starter Set
(SIF001B): not seeded.

The sheet was used first. The 5 catalog SKUs missing from it were then searched
for on Noble Knight (web search, then each page read live with the scraper's own
session on 2026-11-08):
  * Lannister Heroes #2 (CMNSIF210), Casterly Rock Honor Guard (CMNSIF213) and
    Stone Crows (CMNSIF521) all have a Noble Knight page, but it is out of print
    with no price and no add-to-cart button, so each row keeps the link with
    price None and in_stock False (same as Stark's Tully Cavaliers).
  * Lannister Starter Set (CMNSIF01B) and Lannister Red Cloaks (CMNSIF211) have a
    page with ONLY a used copy for sale ("Used Copy" in the page title, VG+/NM,
    $195.00 and $22.00). A used price is not a New price, so no row is created
    for these two until the owner decides.

Every URL carries the Noble Knight affiliate tag ?awid=1576.

create_defaults pattern: price, in_stock, last_seen are set only on creation so
scraper-set prices survive later runs. url, listing_title, not_available are in
defaults (always updated) and are also repeated in create_defaults, because
Django 5 uses create_defaults INSTEAD of defaults when the row does not exist
yet, as is the case for these new SKUs. Run ONCE by hand; it is not in the
Procfile.

Usage:
    python manage.py seed_nk_asoiaf_house_lannister_prices
"""

from django.core.management.base import BaseCommand

NK_PRICES = [
    # (gw_sku, listing_title, price, url, in_stock, not_available)
    ('LANNISTER-002', 'Lannister Guardsmen', 19.95, 'https://www.nobleknight.com/P/2147735712/Lannister-Guardsmen?awid=1576', True, False),  # CMNSIF201
    ('LANNISTER-003', 'Lannister Halberdiers', 19.95, 'https://www.nobleknight.com/P/2147753464/Lannister-Halberdiers?awid=1576', True, False),  # CMNSIF202
    ('LANNISTER-004', "Mountain's Men, The", 19.95, 'https://www.nobleknight.com/P/2147736775/The-Mountains-Men?awid=1576', True, False),  # CMNSIF203
    ('LANNISTER-005', 'Lannister Pyromancers', 29.95, 'https://www.nobleknight.com/P/2147736517/Pyromancers?awid=1576', True, False),  # CMNSIF204
    ('LANNISTER-006', 'Knights of Casterly Rock (2018 Edition)', 69.95, 'https://www.nobleknight.com/P/2147728869/Knights-of-Casterly-Rock-2018-Edition?awid=1576', True, False),  # CMNSIF205
    ('LANNISTER-007', 'Lannister Crossbowmen', 39.95, 'https://www.nobleknight.com/P/2147735558/Lannister-Crossbowmen-Unit-Box?awid=1576', True, False),  # CMNSIF206
    ('LANNISTER-008', "Warrior's Sons, The", 49.95, 'https://www.nobleknight.com/P/2147752838/Warriors-Sons-The?awid=1576', True, False),  # CMNSIF207
    ('LANNISTER-009', 'Poor Fellows Unit Box', 24.95, 'https://www.nobleknight.com/P/2147766448/Lannister-Poor-Fellows-Unit-Box?awid=1576', True, False),  # CMNSIF208
    ('LANNISTER-010', 'Lannister Heroes #1', 29.95, 'https://www.nobleknight.com/P/2147728863/Lannister-Heroes-1?awid=1576', True, False),  # CMNSIF209
    ('LANNISTER-013', 'Lannisport City Watch', 39.95, 'https://www.nobleknight.com/P/2147959882/Lannisport-City-Watch?awid=1576', True, False),  # CMNSIF212
    ('LANNISTER-015', 'House Clegane Brigands', 39.95, 'https://www.nobleknight.com/P/2147953182/House-Clegane-Brigands?awid=1576', True, False),  # CMNSIF214
    ('LANNISTER-016', 'Lannister Heroes #3', 89.95, 'https://www.nobleknight.com/P/2147976064/Lannister-Heores-3?awid=1576', True, False),  # CMNSIF215
    ('LANNISTER-017', 'Lannister Attachments #1', 29.95, 'https://www.nobleknight.com/P/2147841562/Lannister-Attachments-1?awid=1576', True, False),  # CMNSIF216
    ('LANNISTER-018', 'Gold Cloaks', 24.95, 'https://www.nobleknight.com/P/2148077602/Gold-Cloaks?awid=1576', True, False),  # CMNSIF217
    # Found by search after the sheet was used (not in the sheet), each page read live;
    # out of print, no price on the page, so the link is kept with price None:
    ('LANNISTER-011', 'Lannister Heroes #2', None, 'https://www.nobleknight.com/P/2147752839/?awid=1576', False, False),  # CMNSIF210
    ('LANNISTER-014', 'Casterly Rock Honor Guard', None, 'https://www.nobleknight.com/P/2148000383/Casterly-Rock-Honor-Guard?awid=1576', False, False),  # CMNSIF213
    ('LANNISTER-019', 'Stone Crows', None, 'https://www.nobleknight.com/P/2148132267/Stone-Crows?awid=1576', False, False),  # CMNSIF521
]


class Command(BaseCommand):
    """Seed Noble Knight URLs for A Song of Ice and Fire: House Lannister products."""

    help = 'seed_nk_asoiaf_house_lannister_prices: NK URLs for House Lannister (17 of 19 SKUs confirmed)'

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
                # yet (Django 5), and House Lannister has no Noble Knight rows
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
            f'seed_nk_asoiaf_house_lannister_prices complete. {seeded} record(s) seeded.'
        ))
