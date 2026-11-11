"""
Management command: seed_nk_asoiaf_house_martell_prices

Seeds Noble Knight URLs for A Song of Ice and Fire: House Martell products.
The user-supplied "Noble Knight - AOSIAF.xlsx" sheet had 8 kits that match the 12
new House Martell SKUs; each match is confirmed by the stock number on the Noble
Knight page, which is CMON's own SKU (CMNSIF701 = SIF701 Martell Spearmen,
CMNSIF710 = SIF710 Martell Heroes 2, and so on, shown in the trailing comment on
every row). All 8 rows were also read live on nobleknight.com on 2026-11-11 with
the Noble Knight scraper's own session: stock number, price and in-stock state
match the sheet for 8 of 8 (all with a New copy; Sunspear Dervishes and Martell
Heroes #1 pages offer "New & Used Copy" and the price is the New price). The
lower of the two price cells is the price.

The sheet was used first. The 4 SKUs missing from it were then searched for on
Noble Knight (web search, neighbouring product ids and NK's own Martell
product-line page, each page read live with the scraper's own session on
2026-11-11):
  * Starfall Outriders (CMNSIF706), Starfall Knights (707) and Darkstar Retinue
    (708) each have a Noble Knight page, but it is "Out of Print" with no copy for
    sale and no price. The link is kept with a blank price (in_stock False) so the
    scheduled Noble Knight scraper picks a price up by itself if a New copy is ever
    listed.
  * Martell Starter Set (CMNSIF007) has a Noble Knight page, but it only sells a
    USED copy ("Used Copy" alone in the page title; one NM unpunched box at
    $90.00). This site tracks New prices only and the Noble Knight scraper cannot
    tell used from new, so no row is created.

Every URL carries the Noble Knight affiliate tag ?awid=1576.

create_defaults pattern: price, in_stock, last_seen are set only on creation so
scraper-set prices survive later runs. url, listing_title, not_available are in
defaults (always updated) and are also repeated in create_defaults, because
Django 5 uses create_defaults INSTEAD of defaults when the row does not exist
yet, as is the case for these new SKUs. Run ONCE by hand; it is not in the
Procfile.

Usage:
    python manage.py seed_nk_asoiaf_house_martell_prices
"""

from django.core.management.base import BaseCommand

NK_PRICES = [
    # (gw_sku, listing_title, price, url, in_stock, not_available)
    ('MARTELL-002', 'Martell Spearmen', 21.95, 'https://www.nobleknight.com/P/2148062580/Martell-Spearmen?awid=1576', True, False),  # CMNSIF701
    ('MARTELL-003', 'Sand Skirmishers', 29.95, 'https://www.nobleknight.com/P/2148006525/Sand-Skirmishers?awid=1576', True, False),  # CMNSIF702
    ('MARTELL-004', 'Sunspear Dervishes', 29.95, 'https://www.nobleknight.com/P/2148006526/Sunspear-Dervishes?awid=1576', True, False),  # CMNSIF703
    ('MARTELL-005', 'Sunspear Royal Guard', 39.95, 'https://www.nobleknight.com/P/2148006527/Sunspear-Royal-Guard?awid=1576', True, False),  # CMNSIF704
    ('MARTELL-006', 'Dune Vipers', 59.95, 'https://www.nobleknight.com/P/2148021491/Dune-Vipers?awid=1576', True, False),  # CMNSIF705
    ('MARTELL-007', 'Starfall Outriders', None, 'https://www.nobleknight.com/P/2148021498/Starfall-Outriders?awid=1576', False, False),  # CMNSIF706, out of print, no price on the page
    ('MARTELL-008', 'Starfall Knights', None, 'https://www.nobleknight.com/P/2148021494/Starfall-Knights?awid=1576', False, False),  # CMNSIF707, out of print, no price on the page
    ('MARTELL-009', 'Darkstar Retinue', None, 'https://www.nobleknight.com/P/2148097028/Darkstar-Retinue?awid=1576', False, False),  # CMNSIF708, out of print, no price on the page
    ('MARTELL-010', 'Martell Heroes #1', 39.95, 'https://www.nobleknight.com/P/2148006528/Martell-Heroes-1?awid=1576', True, False),  # CMNSIF709
    ('MARTELL-011', 'Martell Heroes #2', 29.95, 'https://www.nobleknight.com/P/2148062578/Martell-Heroes-2?awid=1576', True, False),  # CMNSIF710
    ('MARTELL-012', 'Skyreach Bowmen', 29.95, 'https://www.nobleknight.com/P/2148243627/Skyreach-Bowmen?awid=1576', True, False),  # CMNSIF711
]


class Command(BaseCommand):
    """Seed Noble Knight URLs for A Song of Ice and Fire: House Martell products."""

    help = 'seed_nk_asoiaf_house_martell_prices: NK URLs for House Martell (11 of 12 SKUs)'

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
                # yet (Django 5), and House Martell has no Noble Knight rows
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
            f'seed_nk_asoiaf_house_martell_prices complete. {seeded} record(s) seeded.'
        ))
