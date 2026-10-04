"""
Seed Noble Knight Games US prices for Infinity: NA2.

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
and its page title and current price confirmed against the sheet, each NK
"MFG. Part #" was compared with the Corvus Belli code in our Miniature Market
link (or Corvus Belli's own store REF for NA2-015), and the picks and the
missing list were confirmed with the user (2026-10-03). All 22 listings were
in stock on 2026-10-03; price is create-only so the NK scraper's later
refreshes survive redeploys.

22 of 26 NA2 SKUs written here. Not written:
- Not in the sheet (confirmed by searching it) and not supplied: NA2-001
  Rumbler Spec-Ops Preorder Exclusive Miniature, NA2-011 Mechazoid
  Sokorentai, NA2-026 Yojimbo, Mercenary Sword.
- NA2-014 JSA Expansion Pack Alpha (Corvus Belli code 280771-1039): no NK row
  in the sheet carries that code. The URL the user supplied is the same page
  as NA2-003's "JSA Oban Expansion Pack Alpha" (CVB281715-1214), so it was not
  reused for a second SKU.

Sale item (the current price is stored): NA2-020 Brawlers ("Was old price
$35.95 New Price $34.95").

Notes on individual picks (confirmed with the user):
- NA2-002 Taowu is "Taowu, Mastermind and Schemer (Viral Pistol)"
  (CVB281364-1248), not the older "Taowu Mastermind" (CVB281344-1096).
- NA2-006 is "Essentials - JSA Booster Pack Alpha" (CVB281712-1161) and
  NA2-009 is "Essentials - JSA Support Pack" (CVB281708-1138), not the 2016
  out-of-print plain "JSA Support Pack".
- NA2-010 is "Reinforcements - Domaru Takeshi Neko Oyama" (CVB281703-1109),
  not the 2013 out-of-print plain listing.
- NA2-019 Saito Togan is the "Mercenary Ninja w/Combi Rifle" listing
  (CVB280738-0778), not the Limited Edition. NA2-020 is "NA2 Brawlers -
  Mercenary Enforcers" (CVB280736-0766), not the Daedalus' Fall Limited Edition.
- NA2-013 Father Lucien Sforza is the user-chosen "Father Lucien Sforza w/Viral
  Rifle & ADHL" listing: a 2011 out-of-print page with manufacturer code
  CVB280708, whereas Corvus Belli's current product is 280769-1016 (the only
  Father Lucien row in the sheet).
- NA2-005 is NK's "Iguana Squadron", NA2-021 is "Mercenaries Aragoto
  Senkenbutai", NA2-022 is "Corporate Security Unit w/Boarding Shotgun" and
  NA2-023 is "Tanko Zensenbutai" (NK's titles).
- NA2-017 Karakuri, NA2-019 Saito Togan and NA2-024 Mushashi are flagged out of
  print on NK but in stock.

Run once on Railway startup via Procfile. Safe to re-run -- idempotent.
"""
from decimal import Decimal

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Product, Retailer

_NK_SLUG = 'noble-knight-games'

# (gw_sku, usd_price, url, in_stock)
_PRICES = [
    ('NA2-002', Decimal('26.95'), 'https://www.nobleknight.com/P/2148527068/Taowu-Mastermind-and-Schemer-Viral-Pistol?awid=1576', True),
    ('NA2-003', Decimal('62.95'), 'https://www.nobleknight.com/P/2148384966/JSA-Oban-Expansion-Pack-Alpha?awid=1576', True),
    ('NA2-004', Decimal('98.95'), 'https://www.nobleknight.com/P/2148384968/Anaconda-Mercenary-TAG-Squadron?awid=1576', True),
    ('NA2-005', Decimal('96.95'), 'https://www.nobleknight.com/P/2148343227/Iguana-Squadron?awid=1576', True),
    ('NA2-006', Decimal('34.95'), 'https://www.nobleknight.com/P/2148322135/Essentials---JSA-Booster-Pack-Alpha?awid=1576', True),
    ('NA2-007', Decimal('61.95'), 'https://www.nobleknight.com/P/2148322087/Imperial-Service-Expansion-Pack-Alpha?awid=1576', True),
    ('NA2-008', Decimal('51.95'), 'https://www.nobleknight.com/P/2148322072/JSA-O-Yoroi-Kidobutai-TAG-Pack?awid=1576', True),
    ('NA2-009', Decimal('34.95'), 'https://www.nobleknight.com/P/2148281444/Essentials---JSA-Support-Pack?awid=1576', True),
    ('NA2-010', Decimal('28.95'), 'https://www.nobleknight.com/P/2148206400/Reinforcements---Domaru-Takeshi-Neko-Oyama?awid=1576', True),
    ('NA2-012', Decimal('61.95'), 'https://www.nobleknight.com/P/2148112962/Druze-Shock-Teams?awid=1576', True),
    ('NA2-013', Decimal('29.95'), 'https://www.nobleknight.com/P/2147461981/Father-Lucien-Sforza-w-Viral-Rifle-and-ADHL?awid=1576', True),
    ('NA2-015', Decimal('39.95'), 'https://www.nobleknight.com/P/2148036106/McMurrough---Mercenary-Dog-Warrior?awid=1576', True),
    ('NA2-016', Decimal('19.95'), 'https://www.nobleknight.com/P/2148038731/Valerya-Gromoz-w-Hacker?awid=1576', True),
    ('NA2-017', Decimal('40.95'), 'https://www.nobleknight.com/P/2147909633/Karakuri-Special-Project?awid=1576', True),
    ('NA2-018', Decimal('57.95'), 'https://www.nobleknight.com/P/2147771746/Soldiers-of-Fortune?awid=1576', True),
    ('NA2-019', Decimal('16.49'), 'https://www.nobleknight.com/P/2147757390/Saito-Togan----Mercenary-Ninja-w-Combi-Rifle?awid=1576', True),
    ('NA2-020', Decimal('34.95'), 'https://www.nobleknight.com/P/2147747355/Brawlers---Mercenary-Enforcers?awid=1576', True),
    ('NA2-021', Decimal('49.95'), 'https://www.nobleknight.com/P/2147736525/Mercenaries-Aragoto-Senkenbutai?awid=1576', True),
    ('NA2-022', Decimal('20.95'), 'https://www.nobleknight.com/P/2147728051/Corporate-Security-Unit-w-Boarding-Shotgun?awid=1576', True),
    ('NA2-023', Decimal('58.95'), 'https://www.nobleknight.com/P/2147705244/Tanko-Zensenbutai?awid=1576', True),
    ('NA2-024', Decimal('29.95'), 'https://www.nobleknight.com/P/2147647999/Miyamoto-Mushashi-Aristeia-Outfit?awid=1576', True),
    ('NA2-025', Decimal('19.95'), 'https://www.nobleknight.com/P/2147608743/Avicenna---Mercenary-Doctor?awid=1576', True),
]


class Command(BaseCommand):
    help = 'Seed Noble Knight Games US prices and URLs for Infinity: NA2. Idempotent.'

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
                f'Seeded {seeded} Infinity NA2 Noble Knight prices. Skipped: {skipped}.'
            )
        )
