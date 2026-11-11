"""
Management command: seed_nk_asoiaf_neutrals_prices

Seeds Noble Knight URLs for A Song of Ice and Fire: Neutrals products.
The user-supplied "Noble Knight - AOSIAF.xlsx" sheet (122 rows spanning every
house; columns Title, Title_URL, stock number, year, category, condition,
price, add-to-cart) had 10 kits that match an existing Neutrals SKU; each match
is confirmed by the stock number on the Noble Knight page, which is CMON's own
SKU (CMNSIF005 = SIF005 Bolton Starter Set, CMNSIF504 = SIF504 Bolton
Blackguards, and so on, shown in the trailing comment on every row). Every row
was also read live on nobleknight.com on 2026-11-11 with the Noble Knight
scraper's own session: stock number, price and in-stock state all match the
sheet (10 of 10; several pages say "New & Used Copy" in the title and the first
price equals the sheet's New price). The lower of the two price cells is the
price. Two stock numbers carry Noble Knight's own stray-"1" typo
(CMNSIF1501 = SIF501 Bolton Cutthroats, CMNSIF1505 = SIF505 Neutral Heroes #1,
which Noble Knight files as "Mercenary-Heroes-1"); those matches rest on the
unique title and the typo pattern.

Rows in the sheet that are NOT seeded: Bolton Deluxe Activation Banners and
Neutral Heroes Deluxe Activation Banners (accessories), Roose Bolton (game night
kit), and two Bolton house kits that are not part of the Neutrals collection and
have no product yet (Bolton Heroes #1 CMNSIF506, Dreadfort Archers CMNSIF523);
those belong to the future House Bolton build.

The sheet was used first. The 8 Neutrals SKUs missing from it were then searched
for on Noble Knight (web search, then each page read live with the scraper's own
session on 2026-11-11):
  * Bolton Flayed Men (CMNSIF503), Hedge Knights (CMNSIF507), Bloody Mummer
    Skirmishers (CMNSIF508), Stormcrow Mercenaries (CMNSIF511), Golden Company
    Swordsmen (CMNSIF516) and Golden Company Elephants (CMNSIF518) each have a
    Noble Knight page, but it is out of print with no price and no add-to-cart
    button, so each row keeps the link with price None and in_stock False (same
    as Stark's Tully Cavaliers). The Golden Company pages turned up on the
    European store; the same product ids resolve on the US store.
  * Golden Company Crossbowmen (CMNSIF517) and Neutral Heroes #3 (CMNSIF515)
    have no Noble Knight page that could be found (searches and neighbouring
    product ids): no row is created.

Every URL carries the Noble Knight affiliate tag ?awid=1576.

create_defaults pattern: price, in_stock, last_seen are set only on creation so
scraper-set prices survive later runs. url, listing_title, not_available are in
defaults (always updated) and are also repeated in create_defaults, because
Django 5 uses create_defaults INSTEAD of defaults when the row does not exist
yet, as is the case for these new SKUs. Run ONCE by hand; it is not in the
Procfile.

Usage:
    python manage.py seed_nk_asoiaf_neutrals_prices
"""

from django.core.management.base import BaseCommand

NK_PRICES = [
    # (gw_sku, listing_title, price, url, in_stock, not_available)
    ('NEUTRALS-001', 'Bolton Starter Set', 89.95, 'https://www.nobleknight.com/P/2148077582/Bolton-Starter-Set?awid=1576', True, False),  # CMNSIF005
    ('NEUTRALS-002', 'Bolton Cutthroats', 19.95, 'https://www.nobleknight.com/P/2147736521/Bolton-Cutthroats?awid=1576', True, False),  # CMNSIF1501 (typo for SIF501)
    ('NEUTRALS-003', "Bolton Bastard's Girls", 29.95, 'https://www.nobleknight.com/P/2147728867/Bolton-Bastards-Girls?awid=1576', True, False),  # CMNSIF502
    ('NEUTRALS-005', 'Bolton Blackguards', 24.95, 'https://www.nobleknight.com/P/2147771342/Bolton-Blackguards?awid=1576', True, False),  # CMNSIF504
    ('NEUTRALS-006', 'Neutral Heroes #1', 24.95, 'https://www.nobleknight.com/P/2147728873/Mercenary-Heroes-1?awid=1576', True, False),  # CMNSIF1505 (typo for SIF505)
    ('NEUTRALS-009', 'Bloody Mummer Zorse Riders Unit', 24.95, 'https://www.nobleknight.com/P/2147793962/Zorse-Riders-Unit?awid=1576', True, False),  # CMNSIF509
    ('NEUTRALS-010', 'Neutral Heroes #2', 99.95, 'https://www.nobleknight.com/P/2147773806/Neutral-Heroes-2?awid=1576', True, False),  # CMNSIF510
    ('NEUTRALS-012', 'Stormcrow Archers', 21.95, 'https://www.nobleknight.com/P/2147790273/Stormcrow-Archers?awid=1576', True, False),  # CMNSIF512
    ('NEUTRALS-013', 'Stormcrow Dervishes', 69.95, 'https://www.nobleknight.com/P/2147793963/Stormcrow-Dervishes?awid=1576', True, False),  # CMNSIF513
    ('NEUTRALS-018', 'Lysene Sellswords', 29.95, 'https://www.nobleknight.com/P/2148039904/Lysene-Sellswords?awid=1576', True, False),  # CMNSIF519
    # Found by search after the sheet was used (not in the sheet), each page read live;
    # out of print, no price on the page, so the link is kept with price None:
    ('NEUTRALS-004', 'Bolton Flayed Men', None, 'https://www.nobleknight.com/P/2147728872/Bolton-Flayed-Men?awid=1576', False, False),  # CMNSIF503
    ('NEUTRALS-007', 'Hedge Knights', None, 'https://www.nobleknight.com/P/2147876773/Hedge-Knights?awid=1576', False, False),  # CMNSIF507
    ('NEUTRALS-008', 'Bloody Mummer Skirmishers Unit', None, 'https://www.nobleknight.com/P/2147793961/Bloody-Mummer-Skirmishers-Unit?awid=1576', False, False),  # CMNSIF508
    ('NEUTRALS-011', 'Stormcrow Mercenaries', None, 'https://www.nobleknight.com/P/2147790328/Stormcrow-Mercenaries?awid=1576', False, False),  # CMNSIF511
    ('NEUTRALS-015', 'Golden Company Swordsmen', None, 'https://www.nobleknight.com/P/2148000397/Golden-Company-Swordsmen?awid=1576', False, False),  # CMNSIF516
    ('NEUTRALS-017', 'Golden Company Elephants', None, 'https://www.nobleknight.com/P/2148000400/Golden-Company-Elephants?awid=1576', False, False),  # CMNSIF518
]


class Command(BaseCommand):
    """Seed Noble Knight URLs for A Song of Ice and Fire: Neutrals products."""

    help = 'seed_nk_asoiaf_neutrals_prices: NK URLs for Neutrals (16 of 18 SKUs confirmed)'

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
                # yet (Django 5), and Neutrals has no Noble Knight rows to
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
            f'seed_nk_asoiaf_neutrals_prices complete. {seeded} record(s) seeded.'
        ))
