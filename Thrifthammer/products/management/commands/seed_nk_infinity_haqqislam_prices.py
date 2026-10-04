"""
Seed Noble Knight Games US prices for Infinity: Haqqislam.

Uses the existing `noble-knight-games` Retailer (US, is_uk=False) -- does
not create it, matching the pattern for every other category's NK seed
command.

Source: user-supplied "Noble Knight U.S Infinity.xlsx" (Title/Title_URL/
Price columns). Noble Knight's price is a retailer price, not an MSRP, so
Product.msrp is deliberately not touched here.

Every URL below carries Noble Knight's `?awid=1576` affiliate parameter
(see add_nk_affiliate_tags.py) -- added directly here since that cleanup
command is not in the Procfile and would not fix this command's own output
on the next redeploy otherwise. The NK scraper strips the tag when fetching.

Every match was made by reading, not by script, every URL was fetched live
and its page title and current price confirmed against the sheet, and the
list and the missing SKUs were confirmed with the user (2026-10-03). All 24
listings were in stock on 2026-10-03; price is create-only so the NK
scraper's later refreshes survive redeploys.

24 of 28 Haqqislam SKUs written here. Not in the sheet (confirmed by
searching it) and not supplied: HQQ-022 Hakims, HQQ-023 Maghariba Guard,
HQQ-024 Naffatun, HQQ-028 Odalisques.

Notes:
- HQQ-011 Hassassin Fireteam Pack Alpha is ON SALE ("Was old price $41.95 New
  Price $37.95"): the current price $37.95 is stored.
- HQQ-003 Yuan Yuan is NK's plain "Yuan Yuan" ($34.95), not the "w/Chain Rifle"
  blister ($25.95) or the "Mercenaries" listing ($129.95).
- HQQ-027 is NK's plural "Kameel Remotes", HQQ-025 is "Kum Enforcers - Nazarova
  Twins" and HQQ-026 is "Ghazi Muttawi'ah" (NK's own titles); HQQ-019 is the
  "Namurr Active Response Unit w/Heavy Pistol" listing.

Run once on Railway startup via Procfile. Safe to re-run -- idempotent.
"""
from decimal import Decimal

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Product, Retailer

_NK_SLUG = 'noble-knight-games'

# (gw_sku, usd_price, url, in_stock)
_PRICES = [
    ('HQQ-001', Decimal('42.95'), 'https://www.nobleknight.com/P/2148491625/Hassassin-Expansion-Pack-Gamma?awid=1576', True),
    ('HQQ-002', Decimal('62.95'), 'https://www.nobleknight.com/P/2148454551/Haytham-Aero-unit?awid=1576', True),
    ('HQQ-003', Decimal('34.95'), 'https://www.nobleknight.com/P/2148428302/Yuan-Yuan?awid=1576', True),
    ('HQQ-004', Decimal('43.95'), 'https://www.nobleknight.com/P/2148400359/Mukthar-Active-Response-Unit?awid=1576', True),
    ('HQQ-005', Decimal('96.95'), 'https://www.nobleknight.com/P/2148384977/Zeybek-Aero-Unit?awid=1576', True),
    ('HQQ-006', Decimal('62.95'), 'https://www.nobleknight.com/P/2148368452/Ramah-Taskforce-Expansion-Pack-Alpha?awid=1576', True),
    ('HQQ-007', Decimal('70.95'), 'https://www.nobleknight.com/P/2148491609/Scarface-and-Cordelia---Mercenary-Armored-Team-2025-Edition?awid=1576', True),
    ('HQQ-008', Decimal('66.95'), 'https://www.nobleknight.com/P/2148278501/Hassassin-Expansion-Pack-Alpha?awid=1576', True),
    ('HQQ-009', Decimal('105.95'), 'https://www.nobleknight.com/P/2148117858/Reinforcements---Haqqislam-Pack-Alpha?awid=1576', True),
    ('HQQ-010', Decimal('29.95'), 'https://www.nobleknight.com/P/2148275358/Fiddler---Aristeias-Ex-Toymaker?awid=1576', True),
    ('HQQ-011', Decimal('37.95'), 'https://www.nobleknight.com/P/2148088917/Hassassin-Fireteam-Pack-Alpha?awid=1576', True),
    ('HQQ-012', Decimal('19.95'), 'https://www.nobleknight.com/P/2148071630/Yara-Haddad-AP-Marksman-Rifle?awid=1576', True),
    ('HQQ-013', Decimal('49.95'), 'https://www.nobleknight.com/P/2148037806/Shakush-Light-Armored-Unit?awid=1576', True),
    ('HQQ-014', Decimal('62.95'), 'https://www.nobleknight.com/P/2148036100/Haqqislam-Remotes-Pack?awid=1576', True),
    ('HQQ-015', Decimal('38.95'), 'https://www.nobleknight.com/P/2148013973/Haqqislam-Support-Pack?awid=1576', True),
    ('HQQ-016', Decimal('22.95'), 'https://www.nobleknight.com/P/2148322108/Saladin---O-12-Liaison-Officer?awid=1576', True),
    ('HQQ-017', Decimal('23.95'), 'https://www.nobleknight.com/P/2147892582/Bashi-Bazouks-w-Submachine-Gun-and-Boarding-Shotgun?awid=1576', True),
    ('HQQ-018', Decimal('89.95'), 'https://www.nobleknight.com/P/2147846059/Haqqislam-Action-Pack?awid=1576', True),
    ('HQQ-019', Decimal('19.49'), 'https://www.nobleknight.com/P/2147757403/Namurr-Active-Response-Unit-w-Heavy-Pistol?awid=1576', True),
    ('HQQ-020', Decimal('41.95'), 'https://www.nobleknight.com/P/2147753177/Zhayedan-Intervention-Troops?awid=1576', True),
    ('HQQ-021', Decimal('55.95'), 'https://www.nobleknight.com/P/2147746277/Khawarijs?awid=1576', True),
    ('HQQ-025', Decimal('57.95'), 'https://www.nobleknight.com/P/2147585420/Kum-Enforcers---Nazarova-Twins?awid=1576', True),
    ('HQQ-026', Decimal('54.95'), 'https://www.nobleknight.com/P/2147555759/Ghazi-Muttawiah?awid=1576', True),
    ('HQQ-027', Decimal('48.95'), 'https://www.nobleknight.com/P/2147458357/Kameel-Remotes?awid=1576', True),
]


class Command(BaseCommand):
    help = 'Seed Noble Knight Games US prices and URLs for Infinity: Haqqislam. Idempotent.'

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
                f'Seeded {seeded} Infinity Haqqislam Noble Knight prices. Skipped: {skipped}.'
            )
        )
