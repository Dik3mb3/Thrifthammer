"""
Seed Noble Knight Games US prices for Infinity: Combined Army.

Uses the existing `noble-knight-games` Retailer (US, is_uk=False) -- does
not create it, matching the pattern for every other category's NK seed
command.

Source: user-supplied "Noble Knight U.S Infinity.xlsx" (Title/Title_URL/
Price columns), plus one user-supplied URL for a product not in the sheet
(CA-009 Combined Army Paint Set). Noble Knight's price is a retailer price,
not an MSRP, so Product.msrp is deliberately not touched here.

Every URL below carries Noble Knight's `?awid=1576` affiliate parameter
(see add_nk_affiliate_tags.py) -- added directly here since that cleanup
command is not in the Procfile and would not fix this command's own output
on the next redeploy otherwise. The NK scraper strips the tag when fetching.

Every match was made by reading, not by script, every URL was fetched live
and its page title and current price confirmed (against the sheet for the 29
sheet rows), each NK "MFG. Part #" was compared with the Corvus Belli code in
our Miniature Market link (or Corvus Belli's own store REF where we have no
Miniature Market link), and the picks and the missing list were confirmed with
the user (2026-10-03). All 31 listings were in stock on 2026-10-03; price is
create-only so the NK scraper's later refreshes survive redeploys.

31 of 37 Combined Army SKUs written here. Not written:
- Not in the sheet (confirmed by searching it) and not supplied: CA-001
  Nexus-7 Spec-Ops Bundle, CA-002 Nexus-7 Spec-Ops, CA-024 Bultrak Mobile
  Armored Regiment, CA-027 Taigha Creatures, CA-037 Xeodron Batroids.
- Deliberately unmatched (confirmed with the user): CA-004 Booster Pack Alpha.
  Corvus Belli's current pack is REF 281652-1234 and has no NK listing.
- CA-028 Shasvastii Expansion Pack Gamma is NK's "Combined Army Booster Pack
  Alpha" ($45.95, 2020): its code CVB281607-0852 is the REF Corvus Belli's
  store shows for the Gamma pack (281607-0852) and its box is Tensho, Jayth
  Cutthroats and a Noctifer (Shasvastii contents), although NK's title is the
  old name. The "Shasvastii Expansion Pack Beta" page (CVB281635-1107) is
  CA-013's and was not reused (confirmed with the user).

Sale items (the current price is stored): CA-015 Caskuda ("Was old price
$42.95 New Price $38.95"), CA-020 Shasvastii Expansion Pack Alpha ($49.99 ->
$44.95) and CA-035 Avatar ($69.95 -> $62.95).

Notes on individual picks (confirmed with the user):
- CA-003 is the 2026 "Combined Army Hero, The Charontids (Plasma Rifle)", not
  the 2017 "Charontids w/Plasma Rifle". CA-006 is the plain Drone Remotes Pack,
  not the out-of-print "(CodeOne)". CA-007 is the "(2026 Edition)" Support
  Pack, not the out-of-print plain one. CA-008 is the plain "Achilles", not
  the out-of-print "Achilles V2".
- CA-011 is "Action Pack - Next Wave Combined Army" (CVB281636-1187), not NK's
  separate 2026 "Combined Army Action Pack". CA-017 is "Combined Army Expansion
  Pack Alpha" (CVB281629-1019), not "Next Wave Expansion Pack Alpha".
- CA-020 is "Shasvastii - Expansion Pack Alpha" (CVB281624-0984), not "Expansion
  Pack Delta". CA-022 is "Kornak Gazarot w/Breaker Combi Rifle"
  (CVB281622-0962), not the 2014 out-of-print plain "Kornak Gazarot".
- CA-015 is NK's "Caskuda WCD Armored Jump Operator" (CVB281632-1062), CA-029
  is NK's "Shasvatii Special Armored Core Sphinx" (NK's own spelling) and
  CA-035 is "Avatar & Staldron".

Run once on Railway startup via Procfile. Safe to re-run -- idempotent.
"""
from decimal import Decimal

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Product, Retailer

_NK_SLUG = 'noble-knight-games'

# (gw_sku, usd_price, url, in_stock)
_PRICES = [
    ('CA-003', Decimal('32.95'), 'https://www.nobleknight.com/P/2148527010/Combined-Army-Hero-The-Charontids-Plasma-Rifle?awid=1576', True),
    ('CA-005', Decimal('55.95'), 'https://www.nobleknight.com/P/2148491627/Combined-Army-Overdron-Batroids-TAG-Pack?awid=1576', True),
    ('CA-006', Decimal('38.95'), 'https://www.nobleknight.com/P/2148428252/Combined-Army-Drone-Remotes-Pack?awid=1576', True),
    ('CA-007', Decimal('34.95'), 'https://www.nobleknight.com/P/2148491622/Combined-Army-Support-Pack-2026-Edition?awid=1576', True),
    ('CA-008', Decimal('46.95'), 'https://www.nobleknight.com/P/2148385191/Achilles?awid=1576', True),
    ('CA-009', Decimal('69.95'), 'https://www.nobleknight.com/P/2148379212/Paint-Set---Combined-Army-w-Harbinger-Paramedic?awid=1576', True),
    ('CA-010', Decimal('84.95'), 'https://www.nobleknight.com/P/2148379202/Juggernauts-Armored-Assault-Brigade-Multi-HMG?awid=1576', True),
    ('CA-011', Decimal('153.95'), 'https://www.nobleknight.com/P/2148379217/Action-Pack---Next-Wave-Combined-Army?awid=1576', True),
    ('CA-012', Decimal('34.95'), 'https://www.nobleknight.com/P/2148322238/Krakot-Renegades-2-SMG-Chest-Mine?awid=1576', True),
    ('CA-013', Decimal('42.95'), 'https://www.nobleknight.com/P/2148206380/Shasvastii-Expansion-Pack-Beta?awid=1576', True),
    ('CA-014', Decimal('42.95'), 'https://www.nobleknight.com/P/2148137116/Anathematics-The-Hacker?awid=1576', True),
    ('CA-015', Decimal('38.95'), 'https://www.nobleknight.com/P/2148112959/Caskuda-WCD-Armored-Jump-Operator?awid=1576', True),
    ('CA-016', Decimal('113.95'), 'https://www.nobleknight.com/P/2148181901/Reinforcements---Combined-Army-Pack-Alpha?awid=1576', True),
    ('CA-017', Decimal('76.95'), 'https://www.nobleknight.com/P/2148088040/Combined-Army-Expansion-Pack-Alpha?awid=1576', True),
    ('CA-018', Decimal('70.95'), 'https://www.nobleknight.com/P/2148071619/Morat-Expansion-Pack-Beta?awid=1576', True),
    ('CA-019', Decimal('66.95'), 'https://www.nobleknight.com/P/2148037797/Hungries-The---Gakis-and-Pretas?awid=1576', True),
    ('CA-020', Decimal('44.95'), 'https://www.nobleknight.com/P/2148036094/Shasvastii---Expansion-Pack-Alpha?awid=1576', True),
    ('CA-021', Decimal('61.95'), 'https://www.nobleknight.com/P/2148036095/Morat---Expansion-Pack-Alpha?awid=1576', True),
    ('CA-022', Decimal('31.95'), 'https://www.nobleknight.com/P/2148013950/Kornak-Gazarot-w-Breaker-Combi-Rifle?awid=1576', True),
    ('CA-023', Decimal('70.95'), 'https://www.nobleknight.com/P/2148278525/Morat-Fireteam-Pack?awid=1576', True),
    ('CA-025', Decimal('46.95'), 'https://www.nobleknight.com/P/2147980054/Morat-Tarlok-Pack?awid=1576', True),
    ('CA-026', Decimal('135.95'), 'https://www.nobleknight.com/P/2148002507/Morat-Aggression-Forces-Action-Pack?awid=1576', True),
    ('CA-028', Decimal('45.95'), 'https://www.nobleknight.com/P/2147846058/Combined-Army-Booster-Pack-Alpha?awid=1576', True),
    ('CA-029', Decimal('51.95'), 'https://www.nobleknight.com/P/2147854606/Shasvatii-Special-Armored-Core-Sphinx?awid=1576', True),
    ('CA-030', Decimal('141.95'), 'https://www.nobleknight.com/P/2147810601/Shasvastii-Action-Pack?awid=1576', True),
    ('CA-031', Decimal('19.95'), 'https://www.nobleknight.com/P/2147810597/Greif-Operators-2-Breaker-Pistols?awid=1576', True),
    ('CA-032', Decimal('58.95'), 'https://www.nobleknight.com/P/2147806124/Shasvastii-Nox-Troops?awid=1576', True),
    ('CA-033', Decimal('79.95'), 'https://www.nobleknight.com/P/2147728047/Raicho---Armored-Brigade?awid=1576', True),
    ('CA-034', Decimal('37.95'), 'https://www.nobleknight.com/P/2147692227/Bit-and-Kiss?awid=1576', True),
    ('CA-035', Decimal('62.95'), 'https://www.nobleknight.com/P/2147684184/Avatar-and-Staldron?awid=1576', True),
    ('CA-036', Decimal('14.95'), 'https://www.nobleknight.com/P/2147680851/Pneumarch-of-the-Ur-Hegemony?awid=1576', True),
]


class Command(BaseCommand):
    help = 'Seed Noble Knight Games US prices and URLs for Infinity: Combined Army. Idempotent.'

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
                f'Seeded {seeded} Infinity Combined Army Noble Knight prices. Skipped: {skipped}.'
            )
        )
