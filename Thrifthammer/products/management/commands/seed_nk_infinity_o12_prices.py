"""
Seed Noble Knight Games US prices for Infinity: O-12.

Uses the existing `noble-knight-games` Retailer (US, is_uk=False) -- does
not create it, matching the pattern for every other category's NK seed
command.

Source: user-supplied "Noble Knight U.S Infinity.xlsx" (Title/Title_URL/
Price columns), plus one user-supplied URL for a product not in the sheet
(O12-001 O-12 Paint Set). Noble Knight's price is a retailer price, not an
MSRP, so Product.msrp is deliberately not touched here.

Every URL below carries Noble Knight's `?awid=1576` affiliate parameter
(see add_nk_affiliate_tags.py) -- added directly here since that cleanup
command is not in the Procfile and would not fix this command's own output
on the next redeploy otherwise. The NK scraper strips the tag when fetching.

Every match was made by reading, not by script, every URL was fetched live
and its page title and current price confirmed (against the sheet for the 21
sheet rows), each NK "MFG. Part #" was compared with the Corvus Belli code in
our Miniature Market link (or Corvus Belli's own store REF for O12-011), and
the picks and the missing list were confirmed with the user (2026-10-03). All
22 listings were in stock on 2026-10-03; price is create-only so the NK
scraper's later refreshes survive redeploys.

22 of 23 O-12 SKUs written here. Not written:
- Deliberately unmatched (confirmed with the user): O12-005 Raveneye Officer.
  NK's only Raveneye row is "Raveneye (Exclusive Edition Miniature)" ($69.95,
  2022, out of print, no manufacturer code), a different product from
  Corvus Belli's Raveneye Officer REF 282031-1108.

Sale items (the current price is stored): O12-017 Zeta Unit ("Was old price
$53.95 New Price $48.95") and O12-021 O-12 Action Pack ($95.95 -> $86.95).

Notes on individual picks (confirmed with the user):
- O12-015 "O-12 Expansion Pack Beta" is NK's "O-12 Booster Pack Beta"
  (CVB282010-0863) and O12-016 "O-12 Expansion Pack Alpha" is NK's "O-12 Booster
  Pack Alpha" (CVB282009-0854). O12-020 is "O-12 Support Pack - Specialized
  Support Unit Lambda" (CVB282006-0832).
- O12-004 is "Torchlight Brigade Expansion Pack Beta" (CVB282032-1113), not the
  "Torchlight Brigade Expansion Pack Alpha", which has no O-12 SKU here.
- O12-003 is "Jamie Arantes - Netdroid Rover", O12-012 is "Cyberghost (Hacker,
  Pitcher)" and O12-018 is NK's "O-12 Starmada Action Pack" (NK's own URL slug
  spells it "Q-12"). O12-009's NK part number reads CVB28204-1008 (a typo on
  NK's side; the -1008 suffix matches Miniature Market).

Run once on Railway startup via Procfile. Safe to re-run -- idempotent.
"""
from decimal import Decimal

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Product, Retailer

_NK_SLUG = 'noble-knight-games'

# (gw_sku, usd_price, url, in_stock)
_PRICES = [
    ('O12-001', Decimal('69.95'), 'https://www.nobleknight.com/P/2148368375/O-12-Paint-Set-w-Exclusive-Kappa-Missile-Launcher?awid=1576', True),
    ('O12-002', Decimal('34.95'), 'https://www.nobleknight.com/P/2148302109/Tinker-and-Zetbot-Remote?awid=1576', True),
    ('O12-003', Decimal('30.95'), 'https://www.nobleknight.com/P/2148348944/Jamie-Arantes---Netdroid-Rover?awid=1576', True),
    ('O12-004', Decimal('70.95'), 'https://www.nobleknight.com/P/2148246275/Torchlight-Brigade-Expansion-Pack-Beta?awid=1576', True),
    ('O12-006', Decimal('49.95'), 'https://www.nobleknight.com/P/2148213395/Wreckers-Fire-Recon-Armored-Squad?awid=1576', True),
    ('O12-007', Decimal('174.95'), 'https://www.nobleknight.com/P/2148137135/O-12-Torchlight-Brigade-Action-Pack?awid=1576', True),
    ('O12-008', Decimal('75.95'), 'https://www.nobleknight.com/P/2148137132/Reinforcements---O-12-Pack-Alpha?awid=1576', True),
    ('O12-009', Decimal('51.95'), 'https://www.nobleknight.com/P/2148064382/Starmada-Expansion-Pack-Alpha?awid=1576', True),
    ('O12-010', Decimal('69.95'), 'https://www.nobleknight.com/P/2148047600/RoadBots-Highway-Patrol?awid=1576', True),
    ('O12-011', Decimal('45.95'), 'https://www.nobleknight.com/P/2148278492/Fuzzbots?awid=1576', True),
    ('O12-012', Decimal('19.49'), 'https://www.nobleknight.com/P/2147922252/Cyberghost-Hacker-Pitcher?awid=1576', True),
    ('O12-013', Decimal('55.95'), 'https://www.nobleknight.com/P/2147878491/Raptor-Boarding-Squad?awid=1576', True),
    ('O12-014', Decimal('55.95'), 'https://www.nobleknight.com/P/2147867779/Nyoka-Assault-Troops?awid=1576', True),
    ('O12-015', Decimal('62.95'), 'https://www.nobleknight.com/P/2147869466/O-12-Booster-Pack-Beta?awid=1576', True),
    ('O12-016', Decimal('39.95'), 'https://www.nobleknight.com/P/2147846057/O-12-Booster-Pack-Alpha?awid=1576', True),
    ('O12-017', Decimal('48.95'), 'https://www.nobleknight.com/P/2147854603/Zeta-Unit?awid=1576', True),
    ('O12-018', Decimal('81.95'), 'https://www.nobleknight.com/P/2147839654/Q-12-Starmada-Action-Pack?awid=1576', True),
    ('O12-019', Decimal('51.95'), 'https://www.nobleknight.com/P/2147832368/Copperbot-Remotes-Pack?awid=1576', True),
    ('O12-020', Decimal('55.95'), 'https://www.nobleknight.com/P/2147816445/O-12-Support-Pack---Specialized-Support-Unit-Lambda?awid=1576', True),
    ('O12-021', Decimal('86.95'), 'https://www.nobleknight.com/P/2147809144/O-12-Action-Pack?awid=1576', True),
    ('O12-022', Decimal('28.95'), 'https://www.nobleknight.com/P/2147792248/Alpha-Unit?awid=1576', True),
    ('O12-023', Decimal('31.95'), 'https://www.nobleknight.com/P/2147788238/Team-Sirius?awid=1576', True),
]


class Command(BaseCommand):
    help = 'Seed Noble Knight Games US prices and URLs for Infinity: O-12. Idempotent.'

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
                f'Seeded {seeded} Infinity O-12 Noble Knight prices. Skipped: {skipped}.'
            )
        )
