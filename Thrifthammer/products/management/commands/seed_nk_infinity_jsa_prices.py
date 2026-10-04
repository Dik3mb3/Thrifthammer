"""
Seed Noble Knight Games US prices for Infinity: JSA.

Uses the existing `noble-knight-games` Retailer (US, is_uk=False) -- does
not create it, matching the pattern for every other category's NK seed
command.

Source: user-supplied "Noble Knight U.S Infinity.xlsx" (Title/Title_URL/
Price columns), plus one user-supplied URL for a product not in the sheet
(JSA-001 JSA Paint Set). Noble Knight's price is a retailer price, not an
MSRP, so Product.msrp is deliberately not touched here.

Every URL below carries Noble Knight's `?awid=1576` affiliate parameter
(see add_nk_affiliate_tags.py) -- added directly here since that cleanup
command is not in the Procfile and would not fix this command's own output
on the next redeploy otherwise. The NK scraper strips the tag when fetching.

Every match was made by reading, not by script, every URL was fetched live
and its page title and current price confirmed (against the sheet for the 3
sheet rows), each NK "MFG. Part #" was compared with the Corvus Belli code in
our Miniature Market link, and the list and the missing SKUs were confirmed
with the user (2026-10-03). All 4 listings were in stock on 2026-10-03, none on
sale; price is create-only so the NK scraper's later refreshes survive
redeploys.

4 of 5 JSA SKUs written here. Not in the sheet (confirmed by searching it) and
not supplied: JSA-004 Shindenbutai Expansion Pack Alpha (NK only lists the
Beta and Delta packs, which are different products).

Run once on Railway startup via Procfile. Safe to re-run -- idempotent.
"""
from decimal import Decimal

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Product, Retailer

_NK_SLUG = 'noble-knight-games'

# (gw_sku, usd_price, url, in_stock)
_PRICES = [
    ('JSA-001', Decimal('59.95'), 'https://www.nobleknight.com/P/2148301961/JSA-Paint-Set-w-Exclusive-Keisotsu-Paramedic?awid=1576', True),
    ('JSA-002', Decimal('38.95'), 'https://www.nobleknight.com/P/2148301991/JSA-Aibot-Remotes-Pack?awid=1576', True),
    ('JSA-003', Decimal('94.95'), 'https://www.nobleknight.com/P/2148348923/JSA-Army-Pack?awid=1576', True),
    ('JSA-005', Decimal('98.95'), 'https://www.nobleknight.com/P/2148200483/Reinforcements---JSA-Pack-Alpha?awid=1576', True),
]


class Command(BaseCommand):
    help = 'Seed Noble Knight Games US prices and URLs for Infinity: JSA. Idempotent.'

    def handle(self, *args, **options):
        retailer = Retailer.objects.get(slug=_NK_SLUG)

        seeded = 0
        skipped = 0
        for gw_sku, usd_price, url, in_stock in _PRICES:
            try:
                product = Product.objects.get(gw_sku=gw_sku)
            except Product.DoesNotExist:
                self.stderr.write(f'SKIP — SKU {gw_sku} not in DB')
                skipped += 1
                continue

            cp_defaults = {'url': url, 'in_stock': in_stock, 'not_available': False, 'currency': 'USD'}
            CurrentPrice.objects.update_or_create(
                product=product,
                retailer=retailer,
                defaults=cp_defaults,
                create_defaults={**cp_defaults, 'price': usd_price},
            )
            seeded += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Seeded {seeded} Infinity JSA Noble Knight prices. Skipped: {skipped}.'
            )
        )
