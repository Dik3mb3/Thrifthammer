"""
Management command: seed_nk_asoiaf_nights_watch_prices

Seeds Noble Knight URLs for A Song of Ice and Fire: Night's Watch products.
The user-supplied "Noble Knight - AOSIAF.xlsx" sheet (122 rows spanning every
house; columns Title, Title_URL, stock number, year, category, condition,
price, add-to-cart) had 14 Night's Watch kits. All 14 match an existing catalog
SKU; each match is confirmed by the stock number on the Noble Knight page, which
is CMON's own SKU (CMNSIF002 = SIF002 Night's Watch Starter Set, CMNSIF301 =
SIF301 Sworn Brothers, and so on, shown in the trailing comment on every row).
Every row was also read live on nobleknight.com on 2026-11-09 with the Noble
Knight scraper's own session: stock number, price and in-stock state all match
the sheet (14 of 14; Sworn Brothers, Heroes #1 and Heroes #2 say "New & Used
Copy" in the page title and the first price equals the sheet's New price). The
lower of the two price cells is the price (the other is the MSRP).

The sheet was used first. The 1 catalog SKU missing from it, Veterans of the
Watch (CMNSIF303), was then searched for on Noble Knight (web search, then the
page read live with the scraper's own session on 2026-11-09): the page exists
but is out of print with no price and no add-to-cart button, so the row keeps
the link with price None and in_stock False (same as Stark's Tully Cavaliers).

Every URL carries the Noble Knight affiliate tag ?awid=1576.

create_defaults pattern: price, in_stock, last_seen are set only on creation so
scraper-set prices survive later runs. url, listing_title, not_available are in
defaults (always updated) and are also repeated in create_defaults, because
Django 5 uses create_defaults INSTEAD of defaults when the row does not exist
yet, as is the case for these new SKUs. Run ONCE by hand; it is not in the
Procfile.

Usage:
    python manage.py seed_nk_asoiaf_nights_watch_prices
"""

from django.core.management.base import BaseCommand

NK_PRICES = [
    # (gw_sku, listing_title, price, url, in_stock, not_available)
    ('NIGHTSWATCH-001', "Night's Watch Starter Set, The", 79.95, 'https://www.nobleknight.com/P/2147738628/Nights-Watch-Starter-Set-The?awid=1576', True, False),  # CMNSIF002
    ('NIGHTSWATCH-002', 'Sworn Brothers', 24.95, 'https://www.nobleknight.com/P/2147738626/Sworn-Brothers?awid=1576', True, False),  # CMNSIF301
    ('NIGHTSWATCH-003', 'Ranger Trackers', 31.95, 'https://www.nobleknight.com/P/2147758614/Ranger-Trackers?awid=1576', True, False),  # CMNSIF302 (Sale Price)
    ('NIGHTSWATCH-005', 'Builder Crossbowmen Unit Box', 29.95, 'https://www.nobleknight.com/P/2147766451/Nights-Watch-Builder-Crossbowmen-Unit-Box?awid=1576', True, False),  # CMNSIF304
    ('NIGHTSWATCH-006', 'Ranger Hunters', 49.95, 'https://www.nobleknight.com/P/2147738625/Ranger-Hunters?awid=1576', True, False),  # CMNSIF305
    ('NIGHTSWATCH-007', 'Builder Scorpion Crew', 39.95, 'https://www.nobleknight.com/P/2147746333/Night-Watch-Builder-Scorpion-Crew?awid=1576', True, False),  # CMNSIF306
    ('NIGHTSWATCH-008', 'Builder Stone Thrower', 39.95, 'https://www.nobleknight.com/P/2147771477/Builder-Stone-Thrower?awid=1576', True, False),  # CMNSIF307
    ('NIGHTSWATCH-009', "Night's Watch Conscripts", 59.95, 'https://www.nobleknight.com/P/2147752846/Night-Watchs-Conscripts?awid=1576', True, False),  # CMNSIF308
    ('NIGHTSWATCH-010', "Night's Watch Heroes #1", 34.95, 'https://www.nobleknight.com/P/2147761318/Nights-Watch-Heroes-1?awid=1576', True, False),  # CMNSIF309
    ('NIGHTSWATCH-011', "Night's Watch Heroes #2", 69.95, 'https://www.nobleknight.com/P/2147793959/Nights-Watch-Heroes-2?awid=1576', True, False),  # CMNSIF310
    ('NIGHTSWATCH-012', 'Ranger Vanguards', 34.95, 'https://www.nobleknight.com/P/2147953188/Ranger-Vanguards?awid=1576', True, False),  # CMNSIF312
    ('NIGHTSWATCH-013', 'Shadow Tower Spearmen', 39.95, 'https://www.nobleknight.com/P/2147954226/Shadow-Tower-Spearmen?awid=1576', True, False),  # CMNSIF313
    ('NIGHTSWATCH-014', "Night's Watch Heroes #3", 39.95, 'https://www.nobleknight.com/P/2147976065/Nights-Watch-Heroes-3?awid=1576', True, False),  # CMNSIF315
    ('NIGHTSWATCH-015', "Night's Watch Attachments #1", 39.95, 'https://www.nobleknight.com/P/2147841563/Nights-Watch-Attachments-1?awid=1576', True, False),  # CMNSIF316
    # Found by search after the sheet was used (not in the sheet), page read live;
    # out of print, no price on the page, so the link is kept with price None:
    ('NIGHTSWATCH-004', 'Veterans of the Watch Unit Box', None, 'https://www.nobleknight.com/P/2147766450/Nights-Watch-Veterans-of-the-Watch?awid=1576', False, False),  # CMNSIF303
]


class Command(BaseCommand):
    """Seed Noble Knight URLs for A Song of Ice and Fire: Night's Watch products."""

    help = "seed_nk_asoiaf_nights_watch_prices: NK URLs for Night's Watch (15 of 15 SKUs confirmed)"

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
                # yet (Django 5), and Night's Watch has no Noble Knight rows to
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
            f'seed_nk_asoiaf_nights_watch_prices complete. {seeded} record(s) seeded.'
        ))
