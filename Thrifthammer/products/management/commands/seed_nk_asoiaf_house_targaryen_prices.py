"""
Management command: seed_nk_asoiaf_house_targaryen_prices

Seeds Noble Knight URLs for A Song of Ice and Fire: House Targaryen products.
The user-supplied "Noble Knight - AOSIAF.xlsx" sheet had 10 kits that match the 14
new House Targaryen SKUs; each match is confirmed by the stock number on the
Noble Knight page, which is CMON's own SKU (CMNSIF602 = SIF602 Dothraki Veterans,
CMNSIF615 = SIF615 Targaryen Heroes 3, and so on, shown in the trailing comment
on every row). All 10 rows were also read live on nobleknight.com on 2026-11-11
with the Noble Knight scraper's own session: stock number, price and in-stock
state match the sheet for 9 of 10 (all with a New copy). The 10th, Mother of
Dragons, is live at $54.95 against the sheet's $59.95, so the live price is used;
its stock number is Noble Knight's own stray-"1" typo (CMNSIF1608 = SIF608), and
the match rests on the unique title and that typo pattern. The lower of the two
price cells is the price.

The sheet was used first. The 4 SKUs missing from it were then searched for on
Noble Knight (web search, then each page read live with the scraper's own session
on 2026-11-11):
  * Targaryen Starter Set (CMNSIF006) and Unsullied Pikemen (CMNSIF606) each have
    a Noble Knight page, but it only sells a USED copy ("Used Copy" alone in the
    page title; $125.00 and $55.00). This site tracks New prices only and the
    Noble Knight scraper cannot tell used from new, so no row is created.
  * Unsullied Swordmasters (CMNSIF607) and Targaryen Heroes #1 (CMNSIF609) have
    no Noble Knight page that could be found (searches and neighbouring product
    ids): no row is created.

The three Stormcrow products that are also on the House Targaryen page already
exist under the Neutrals faction (NEUTRALS-011..013), already have their Noble
Knight rows from seed_nk_asoiaf_neutrals_prices, and are dual-tagged to House
Targaryen: no new rows.

Every URL carries the Noble Knight affiliate tag ?awid=1576.

create_defaults pattern: price, in_stock, last_seen are set only on creation so
scraper-set prices survive later runs. url, listing_title, not_available are in
defaults (always updated) and are also repeated in create_defaults, because
Django 5 uses create_defaults INSTEAD of defaults when the row does not exist
yet, as is the case for these new SKUs. Run ONCE by hand; it is not in the
Procfile.

Usage:
    python manage.py seed_nk_asoiaf_house_targaryen_prices
"""

from django.core.management.base import BaseCommand

NK_PRICES = [
    # (gw_sku, listing_title, price, url, in_stock, not_available)
    ('TARGARYEN-002', 'Dothraki Screamers Unit', 49.95, 'https://www.nobleknight.com/P/2147793964/Dothraki-Screamers-Unit?awid=1576', True, False),  # CMNSIF601
    ('TARGARYEN-003', 'Dothraki Veterans', 29.95, 'https://www.nobleknight.com/P/2147841566/Dothraki-Veterans?awid=1576', True, False),  # CMNSIF602
    ('TARGARYEN-004', 'Dothraki Outriders', 29.95, 'https://www.nobleknight.com/P/2147889376/Dothraki-Outriders?awid=1576', True, False),  # CMNSIF603
    ('TARGARYEN-005', 'Dothraki Hrakkars', 49.95, 'https://www.nobleknight.com/P/2147840774/Dothraki-Hrakkars?awid=1576', True, False),  # CMNSIF604
    ('TARGARYEN-006', 'Freedmen', 29.95, 'https://www.nobleknight.com/P/2147876776/Freedmen?awid=1576', True, False),  # CMNSIF605
    ('TARGARYEN-009', 'Mother of Dragons', 54.95, 'https://www.nobleknight.com/P/2147840771/Mother-of-Dragons?awid=1576', True, False),  # CMNSIF1608 (typo for SIF608), live price
    ('TARGARYEN-011', 'Targaryen Heroes 2', 79.95, 'https://www.nobleknight.com/P/2147953175/Targaryen-Heroes-2?awid=1576', True, False),  # CMNSIF610
    ('TARGARYEN-012', 'Brazen Beasts', 39.95, 'https://www.nobleknight.com/P/2148039902/Brazen-Beasts?awid=1576', True, False),  # CMNSIF611
    ('TARGARYEN-013', 'Pit Fighters', 44.95, 'https://www.nobleknight.com/P/2148077600/Pit-Fighters?awid=1576', True, False),  # CMNSIF612
    ('TARGARYEN-014', 'Targaryen Heroes 3', 79.95, 'https://www.nobleknight.com/P/2148006530/Targaryen-Heroes-3?awid=1576', True, False),  # CMNSIF615
]


class Command(BaseCommand):
    """Seed Noble Knight URLs for A Song of Ice and Fire: House Targaryen products."""

    help = 'seed_nk_asoiaf_house_targaryen_prices: NK URLs for House Targaryen (10 of 14 SKUs confirmed)'

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
                # yet (Django 5), and House Targaryen has no Noble Knight rows
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
            f'seed_nk_asoiaf_house_targaryen_prices complete. {seeded} record(s) seeded.'
        ))
