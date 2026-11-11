"""
Management command: seed_nk_asoiaf_free_folk_prices

Seeds Noble Knight URLs for A Song of Ice and Fire: Free Folk products.
The user-supplied "Noble Knight - AOSIAF.xlsx" sheet (122 rows spanning every
house; columns Title, Title_URL, stock number, year, category, condition,
price, add-to-cart) had 13 Free Folk kits. All 13 match an existing catalog SKU;
each match is confirmed by the stock number on the Noble Knight page, which is
CMON's own SKU (CMNSIF401 = SIF401 Free Folk Raiders, CMNSIF405 = SIF405
Spearwives, and so on, shown in the trailing comment on every row). Every row
was also read live on nobleknight.com on 2026-11-10 with the Noble Knight
scraper's own session: stock number, price and in-stock state all match the
sheet (13 of 13; several pages say "New & Used Copy" in the title and the first
price equals the sheet's New price). The lower of the two price cells is the
price (the other is the MSRP). War Mammoths shows the stock number "CMNSIF1412",
Noble Knight's own stray-"1" typo for CMNSIF412; the match rests on the unique
title and that typo pattern.

The sheet was used first. The 6 catalog SKUs missing from it were then searched
for on Noble Knight (web search, then each page read live with the scraper's own
session on 2026-11-10):
  * Free Folk Starter Set (CMNSIF003) has a Noble Knight page, but it is out of
    print with no price and no add-to-cart button, so the row keeps the link
    with price None and in_stock False (same as Stark's Tully Cavaliers).
  * Frozen Shore Bear Riders (CMNSIF414), Free Folk Heroes #3 (CMNSIF415),
    Varamyr Sixskins (CMNSIF417) and Giant Spear Throwers (CMNSIF418) have a
    page with ONLY a used copy for sale ("Used Copy" alone in the page title).
    This site tracks New prices only and the Noble Knight scraper cannot tell
    used from new, so no row is created for these four.
  * Followers of Bone (CMNSIF407) appears only on Noble Knight's European store:
    no US page, no row.

Every URL carries the Noble Knight affiliate tag ?awid=1576.

create_defaults pattern: price, in_stock, last_seen are set only on creation so
scraper-set prices survive later runs. url, listing_title, not_available are in
defaults (always updated) and are also repeated in create_defaults, because
Django 5 uses create_defaults INSTEAD of defaults when the row does not exist
yet, as is the case for these new SKUs. Run ONCE by hand; it is not in the
Procfile.

Usage:
    python manage.py seed_nk_asoiaf_free_folk_prices
"""

from django.core.management.base import BaseCommand

NK_PRICES = [
    # (gw_sku, listing_title, price, url, in_stock, not_available)
    ('FREEFOLK-002', 'Free Folk Raiders', 24.95, 'https://www.nobleknight.com/P/2147746334/Free-Folk-Raiser?awid=1576', True, False),  # CMNSIF401
    ('FREEFOLK-003', 'Free Folk Trappers', 24.95, 'https://www.nobleknight.com/P/2147752832/Free-Folk-Trappers?awid=1576', True, False),  # CMNSIF403 (Sale Price)
    ('FREEFOLK-004', 'Thenn Warriors', 29.95, 'https://www.nobleknight.com/P/2147771344/Thenn-Warriros?awid=1576', True, False),  # CMNSIF404
    ('FREEFOLK-005', 'Free Folk Spearwives', 32.95, 'https://www.nobleknight.com/P/2147744011/Spearwives?awid=1576', True, False),  # CMNSIF405
    ('FREEFOLK-006', 'Savage Giants', 39.95, 'https://www.nobleknight.com/P/2147746335/Free-Folk-Savage-Giants?awid=1576', True, False),  # CMNSIF406
    ('FREEFOLK-008', 'Cave Dweller Savages', 27.95, 'https://www.nobleknight.com/P/2147752850/Free-Folk-Cave-Dweller-Savages?awid=1576', True, False),  # CMNSIF408
    ('FREEFOLK-009', 'Free Folk Heroes #1', 27.95, 'https://www.nobleknight.com/P/2147761319/Free-Folk-Heroes-1?awid=1576', True, False),  # CMNSIF409
    ('FREEFOLK-010', 'Free Folk Heroes #2', 59.95, 'https://www.nobleknight.com/P/2147942066/Free-Folk-Heroes-2?awid=1576', True, False),  # CMNSIF410
    ('FREEFOLK-011', 'Frozen Shore Chariots', 39.95, 'https://www.nobleknight.com/P/2147942057/Frozen-Shore-Chariots?awid=1576', True, False),  # CMNSIF411
    ('FREEFOLK-012', 'War Mammoths', 39.95, 'https://www.nobleknight.com/P/2147841564/War-Mammoths?awid=1576', True, False),  # CMNSIF1412 (typo for SIF412)
    ('FREEFOLK-013', 'Frozen Shore Hunters', 24.95, 'https://www.nobleknight.com/P/2148033505/Frozen-Shore-Hunters?awid=1576', True, False),  # CMNSIF413
    ('FREEFOLK-016', 'Free Folk Attachments #1', 24.95, 'https://www.nobleknight.com/P/2147841565/Free-Folk-Attachments-1?awid=1576', True, False),  # CMNSIF416
    ('FREEFOLK-019', "Harma's Vanguard", 24.95, 'https://www.nobleknight.com/P/2148125976/Harmas-Vanguard?awid=1576', True, False),  # CMNSIF419
    # Found by search after the sheet was used (not in the sheet), page read live;
    # out of print, no price on the page, so the link is kept with price None:
    ('FREEFOLK-001', 'Free Folk Starter Set', None, 'https://www.nobleknight.com/P/2147744012/Free-Folk-Starter-Set?awid=1576', False, False),  # CMNSIF003
]


class Command(BaseCommand):
    """Seed Noble Knight URLs for A Song of Ice and Fire: Free Folk products."""

    help = 'seed_nk_asoiaf_free_folk_prices: NK URLs for Free Folk (14 of 19 SKUs confirmed)'

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
                # yet (Django 5), and Free Folk has no Noble Knight rows to
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
            f'seed_nk_asoiaf_free_folk_prices complete. {seeded} record(s) seeded.'
        ))
