"""
Seed Noble Knight Games US prices for Infinity: Ariadna.

Uses the existing `noble-knight-games` Retailer (US, is_uk=False) -- does
not create it, matching the pattern for every other category's NK seed
command.

Source: user-supplied "Noble Knight U.S Infinity.xlsx" (Title/Title_URL/
Price columns), plus 2 user-supplied URLs for products not in the sheet
(ARI-011 Patchers, ARI-014 Chernobog). Noble Knight's price is a retailer
price, not an MSRP, so Product.msrp is deliberately not touched here.

Every URL below carries Noble Knight's `?awid=1576` affiliate parameter
(see add_nk_affiliate_tags.py) -- added directly here since that cleanup
command is not in the Procfile and would not fix this command's own output
on the next redeploy otherwise. The NK scraper strips the tag when fetching.

Every match was made by reading, not by script, every URL was fetched live
and its page title and current price confirmed (against the sheet for the 29
sheet rows), and the picks and the missing list were confirmed with the user
(2026-10-03). Price is create-only so the NK scraper's later refreshes
survive redeploys.

31 of 33 Ariadna SKUs written here. Not written:
- Not in the sheet and not supplied: ARI-027 Line Kazaks.
- Deliberately unmatched (confirmed with the user): ARI-028 Kazak Spetsnazs.
  NK's only candidate is the older single-model "Spetsnaz w/Sniper Rifle"
  ($20.95), while our SKU is the box (UK MSRP 31.70).

ARI-011 Patchers and ARI-014 Chernobog are real NK listings that are OUT OF
STOCK right now (pages read "Last Stocked on 9/24/2026" and "9/18/2026" with
"Notify Me When Back In-Stock" and no price shown; their Corvus Belli codes,
CVB281130-1006 and CVB281124-0961, match the Miniature Market listings for the
same products). Recorded with price=None, in_stock=False, not_available=False
(real listing, no current price to capture), the same convention as SC-001 and
SC-009 in seed_nk_starcraft_prices.

ARI-024 Pavel McMannus and ARI-026 Frontoviks are ON SALE ("Was old price
$19.49 New Price $18.95" and "$40.95 / $36.95"): the current price is stored.

Notes on individual picks (confirmed with the user):
- ARI-018 Irmandinhos is NK's "Irmandihnos" ($27.95, NK's own spelling), not
  the older "Irmandinhos w/Boarding Shotgun" ($13.95).
- ARI-019 TankHunters is "Tankhunters w/Autocannon" ($24.95), not the older
  single "Tank Hunter w/Autocannon" ($29.95).
- ARI-023 Intel Spec-Ops is the plain listing ($27.95), not the "Promo
  Resculpt" ($99.95).
- ARI-016 Ariadna Expansion Pack Alpha is NK's exact "Ariadna Expansion Pack
  Alpha"; ARI-030 is the "Van Zant w/Heavy Pistol & AP CC Weapon" listing.

Run once on Railway startup via Procfile. Safe to re-run -- idempotent.
"""
from decimal import Decimal

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Product, Retailer

_NK_SLUG = 'noble-knight-games'

# (gw_sku, usd_price or None when the listing shows no price, url, in_stock)
_PRICES = [
    ('ARI-001', Decimal('56.95'), 'https://www.nobleknight.com/P/2148527036/Ioann-Bann-Varangian-Dog-Warrior?awid=1576', True),
    ('ARI-002', Decimal('21.95'), 'https://www.nobleknight.com/P/2148428292/1st-Highlander-SAS-Chain-Rifle?awid=1576', True),
    ('ARI-003', Decimal('57.95'), 'https://www.nobleknight.com/P/2148491614/Ariadna-Support-Pack-2026-Edition?awid=1576', True),
    ('ARI-004', Decimal('44.95'), 'https://www.nobleknight.com/P/2148491603/Vystrel-Mobile-Artillery-Regiment?awid=1576', True),
    ('ARI-005', Decimal('54.95'), 'https://www.nobleknight.com/P/2148322090/TAK-Expansion-Pack-Alpha?awid=1576', True),
    ('ARI-006', Decimal('51.95'), 'https://www.nobleknight.com/P/2148246304/Kibervolk-Patrol?awid=1576', True),
    ('ARI-007', Decimal('108.95'), 'https://www.nobleknight.com/P/2148491584/Ariadna-Action-Pack?awid=1576', True),
    ('ARI-008', Decimal('101.95'), 'https://www.nobleknight.com/P/2148145367/Reinforcements---Ariadna-Pack-Alpha?awid=1576', True),
    ('ARI-009', Decimal('29.95'), 'https://www.nobleknight.com/P/2148112951/Highlander-Cateran-T2-Sniper?awid=1576', True),
    ('ARI-010', Decimal('40.95'), 'https://www.nobleknight.com/P/2148088038/Kosmoflot-Support-Pack?awid=1576', True),
    ('ARI-011', None, 'https://www.nobleknight.com/P/2148064430/Patchers-Structural-Response-Team?awid=1576', False),
    ('ARI-012', Decimal('45.95'), 'https://www.nobleknight.com/P/2148037790/Kosmoflot-Expansion-Pack-Alpha?awid=1576', True),
    ('ARI-013', Decimal('47.95'), 'https://www.nobleknight.com/P/2148036096/Scots-Guard?awid=1576', True),
    ('ARI-014', None, 'https://www.nobleknight.com/P/2148014257/Chernobog-Armored-Detachment?awid=1576', False),
    ('ARI-015', Decimal('20.95'), 'https://www.nobleknight.com/P/2147994082/Uxia-McNeill-w-Boarding-Shotgun?awid=1576', True),
    ('ARI-016', Decimal('44.95'), 'https://www.nobleknight.com/P/2148491276/Ariadna-Expansion-Pack-Alpha?awid=1576', True),
    ('ARI-017', Decimal('45.95'), 'https://www.nobleknight.com/P/2148073886/Polaris-Team-Beast-Pack?awid=1576', True),
    ('ARI-018', Decimal('27.95'), 'https://www.nobleknight.com/P/2148491647/Irmandihnos?awid=1576', True),
    ('ARI-019', Decimal('24.95'), 'https://www.nobleknight.com/P/2147892583/Tankhunters-w-Autocannon?awid=1576', True),
    ('ARI-020', Decimal('20.95'), 'https://www.nobleknight.com/P/2147869489/Uxia-McNeill-Assault-Pistol?awid=1576', True),
    ('ARI-021', Decimal('70.95'), 'https://www.nobleknight.com/P/2147846060/Equipe-Mirage-5?awid=1576', True),
    ('ARI-022', Decimal('113.95'), 'https://www.nobleknight.com/P/2147837146/Tartary-Army-Corps-Action-Pack?awid=1576', True),
    ('ARI-023', Decimal('27.95'), 'https://www.nobleknight.com/P/2147796792/Intel-Spec-Ops?awid=1576', True),
    ('ARI-024', Decimal('18.95'), 'https://www.nobleknight.com/P/2147775256/Pavel-Aleksie-McMannus-Spetsgruppa-C-w-Ojotnik?awid=1576', True),
    ('ARI-025', Decimal('55.95'), 'https://www.nobleknight.com/P/2147757383/Dynamo-Reg-of-Kazak---Light-Cavalry?awid=1576', True),
    ('ARI-026', Decimal('36.95'), 'https://www.nobleknight.com/P/2147747357/Frontovkis---Assault-Separated-Bat?awid=1576', True),
    ('ARI-029', Decimal('27.95'), 'https://www.nobleknight.com/P/2147623470/Col-Yevgueni-Voronin---Cossack-Diplomatic-Corps?awid=1576', True),
    ('ARI-030', Decimal('19.49'), 'https://www.nobleknight.com/P/2147603973/Van-Zant-w-Heavy-Pistol-and-AP-CC-Weapon?awid=1576', True),
    ('ARI-031', Decimal('96.95'), 'https://www.nobleknight.com/P/2147654636/Dog-Warriors?awid=1576', True),
    ('ARI-032', Decimal('85.95'), 'https://www.nobleknight.com/P/2147556199/Antipode-Assault-Pack-2nd-Edition?awid=1576', True),
    ('ARI-033', Decimal('69.95'), 'https://www.nobleknight.com/P/2147463358/Traktor-Muls---Artillery-and-Support-Regiment?awid=1576', True),
]


class Command(BaseCommand):
    help = 'Seed Noble Knight Games US prices and URLs for Infinity: Ariadna. Idempotent.'

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
                f'Seeded {seeded} Infinity Ariadna Noble Knight prices. Skipped: {skipped}.'
            )
        )
