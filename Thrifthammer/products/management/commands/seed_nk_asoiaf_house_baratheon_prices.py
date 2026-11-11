"""
Management command: seed_nk_asoiaf_house_baratheon_prices

Seeds Noble Knight URLs for A Song of Ice and Fire: House Baratheon products.
The user-supplied "Noble Knight - AOSIAF.xlsx" sheet had 10 kits that match the 20
new House Baratheon SKUs; each match is confirmed by the stock number on the
Noble Knight page, which is CMON's own SKU (CMNSIF802 = SIF802 Sentinels, CMNSIF008
= SIF008 Starter Set, and so on, shown in the trailing comment on every row). All
10 rows were also read live on nobleknight.com on 2026-11-11 with the Noble Knight
scraper's own session: stock number, price and in-stock state match the sheet for
10 of 10 (all with a New copy; the Starter Set page offers "New & Used Copy" and
the $239.95 is the New price). The lower of the two price cells is the price.

The sheet was used first. The 10 SKUs missing from it were then searched for on
Noble Knight (neighbouring product ids, a web search and NK's own Baratheon
product-line page, each page read live with the scraper's own session on
2026-11-11):
  * Champions of the Stag (CMNSIF804), King's Men (805), Queen's Men (806),
    R'hllor Lightbringers (807), R'hllor Faithful (808), Heroes #2 (810), Rose
    Knights (811), Thorn Watch (812) and Crownland Scouts (818) each have a Noble
    Knight page, but it is "Out of Print" with no copy for sale and no price. The
    link is kept with a blank price (in_stock False) so the scheduled Noble Knight
    scraper picks a price up by itself if a New copy is ever listed.
  * Halberdiers (CMNSIF817) has a Noble Knight page, but it only sells a USED copy
    ("Used Copy" alone in the page title; $45.00 EX/NM, some figures primed). This
    site tracks New prices only and the Noble Knight scraper cannot tell used from
    new, so no row is created.

Every URL carries the Noble Knight affiliate tag ?awid=1576.

create_defaults pattern: price, in_stock, last_seen are set only on creation so
scraper-set prices survive later runs. url, listing_title, not_available are in
defaults (always updated) and are also repeated in create_defaults, because
Django 5 uses create_defaults INSTEAD of defaults when the row does not exist
yet, as is the case for these new SKUs. Run ONCE by hand; it is not in the
Procfile.

Usage:
    python manage.py seed_nk_asoiaf_house_baratheon_prices
"""

from django.core.management.base import BaseCommand

NK_PRICES = [
    # (gw_sku, listing_title, price, url, in_stock, not_available)
    ('BARATHEON-001', 'Baratheon Starter Set', 239.95, 'https://www.nobleknight.com/P/2147775120/Baratheon-Starter-Set?awid=1576', True, False),  # CMNSIF008
    ('BARATHEON-002', 'Wardens Unit', 29.95, 'https://www.nobleknight.com/P/2147793966/Wardens-Unit?awid=1576', True, False),  # CMNSIF801
    ('BARATHEON-003', 'Baratheon Sentinels', 29.95, 'https://www.nobleknight.com/P/2147841567/Baratheon-Sentinels?awid=1576', True, False),  # CMNSIF802
    ('BARATHEON-004', 'Stag Knights', 29.95, 'https://www.nobleknight.com/P/2147793967/Stag-Knights?awid=1576', True, False),  # CMNSIF803
    ('BARATHEON-005', 'Champions of the Stag', None, 'https://www.nobleknight.com/P/2147793968/Champions-of-the-Stag?awid=1576', False, False),  # CMNSIF804, out of print, no price on the page
    ('BARATHEON-006', "Baratheon King's Men", None, 'https://www.nobleknight.com/P/2147876777/Baratheon-Kings-Men?awid=1576', False, False),  # CMNSIF805, out of print, no price on the page
    ('BARATHEON-007', "Baratheon Queen's Men", None, 'https://www.nobleknight.com/P/2147876778/Baratheon-Queens-Men?awid=1576', False, False),  # CMNSIF806, out of print, no price on the page
    ('BARATHEON-008', "R'hllor Lightbringers", None, 'https://www.nobleknight.com/P/2147876775/Rhllor-Lightbringers?awid=1576', False, False),  # CMNSIF807, out of print, no price on the page
    ('BARATHEON-009', "R'hllor Faithful", None, 'https://www.nobleknight.com/P/2147816523/Rhllor-Faithful?awid=1576', False, False),  # CMNSIF808, out of print, no price on the page
    ('BARATHEON-010', 'Baratheon Heroes #1', 59.95, 'https://www.nobleknight.com/P/2147793969/Baratheon-Heroes-1?awid=1576', True, False),  # CMNSIF809
    ('BARATHEON-011', 'Baratheon Heroes #2', None, 'https://www.nobleknight.com/P/2147793970/Baratheon-Heroes-2?awid=1576', False, False),  # CMNSIF810, out of print, no price on the page
    ('BARATHEON-012', 'Rose Knights', None, 'https://www.nobleknight.com/P/2147816524/Rose-Knights?awid=1576', False, False),  # CMNSIF811, out of print, no price on the page
    ('BARATHEON-013', 'Thorn Watch', None, 'https://www.nobleknight.com/P/2147953179/Thorn-Watch?awid=1576', False, False),  # CMNSIF812, out of print, no price on the page
    ('BARATHEON-014', 'Riders of Highgarden', 59.95, 'https://www.nobleknight.com/P/2147976066/Riders-of-Highgarden?awid=1576', True, False),  # CMNSIF813
    ('BARATHEON-015', 'Highgarden Pikemen', 59.95, 'https://www.nobleknight.com/P/2147980821/Highgarden-Pikemen?awid=1576', True, False),  # CMNSIF814
    ('BARATHEON-016', 'Baratheon Heroes #3', 59.95, 'https://www.nobleknight.com/P/2148025922/Baratheon-Heroes-3?awid=1576', True, False),  # CMNSIF815
    ('BARATHEON-017', 'Baratheon Attachments #1', 79.95, 'https://www.nobleknight.com/P/2147841569/Baratheon-Attachments-1?awid=1576', True, False),  # CMNSIF816
    ('BARATHEON-019', 'Crownland Scouts', None, 'https://www.nobleknight.com/P/2148175387/Crownland-Scouts?awid=1576', False, False),  # CMNSIF818, out of print, no price on the page
    ('BARATHEON-020', 'Baratheon Heroes #4', 59.95, 'https://www.nobleknight.com/P/2148025923/Baratheon-Heroes-4?awid=1576', True, False),  # CMNSIF820
]


class Command(BaseCommand):
    """Seed Noble Knight URLs for A Song of Ice and Fire: House Baratheon products."""

    help = 'seed_nk_asoiaf_house_baratheon_prices: NK URLs for House Baratheon (19 of 20 SKUs)'

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
                # yet (Django 5), and House Baratheon has no Noble Knight rows
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
            f'seed_nk_asoiaf_house_baratheon_prices complete. {seeded} record(s) seeded.'
        ))
