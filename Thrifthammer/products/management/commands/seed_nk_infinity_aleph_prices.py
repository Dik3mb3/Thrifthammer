"""
Seed Noble Knight Games US prices for Infinity: ALEPH.

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
link where one exists, and the picks and the missing list were confirmed with
the user (2026-10-03). All 20 listings were in stock on 2026-10-03, none on
sale; price is create-only so the NK scraper's later refreshes survive
redeploys.

20 of 22 ALEPH SKUs written here. Not in the sheet (confirmed by searching
it) and not supplied: ALE-020 Andromeda, ALE-022 Penthesilea Amazon Biker
Special Edition.

Notes (all confirmed with the user):
- ALE-002 ALEPH Support Pack is NK's "ALEPH Support Pack (2026 Edition)"
  ($39.95, CVB280891-1209, the code on our Miniature Market link), not the
  older plain "Aleph Support Pack" (2022, CVB280870-0963).
- ALE-015 Dactyls is NK's plain "Aleph Support Pack" ($51.95, 2022, one Dactyl
  Engineer, one Dactyl Doctor and two Yudbots). Its code CVB280870-0963 is the
  REF Corvus Belli's store shows for Dactyls (280870-0963), although NK's title
  does not say Dactyls. NK's out-of-print "Dactyls - Engineer" (CVB280843) and
  "Acmon, Sergeant of Dactyls" (CVB280846) are different, older products.
- ALE-007 Atalanta is "Atalanta, Agema's NCO & Spotbot" ($34.95, CVB280883-1074,
  matching Miniature Market), not the 2013 out-of-print "Atalanta - Agema's NCO
  & Spotbot" ($39.95).
- ALE-012 Expansion Pack Beta is NK's "Aleph Booster Pack Beta" ($62.95,
  CVB280874, matching our Corvus Belli URL and Miniature Market listing).
- ALE-016 Marut is "Marut - Pose B" ($51.95, CVB280869-0946, Corvus Belli's
  store REF 280869-0946).
- ALE-021 Hector's code (CVB280848-0571) matches Miniature Market, but NK's
  price ($50.95, listed as "2 figures") is well above our $24.99 MSRP; stored
  as NK shows it.

Run once on Railway startup via Procfile. Safe to re-run -- idempotent.
"""
from decimal import Decimal

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Product, Retailer

_NK_SLUG = 'noble-knight-games'

# (gw_sku, usd_price, url, in_stock)
_PRICES = [
    ('ALE-001', Decimal('82.95'), 'https://www.nobleknight.com/P/2148527048/Tarkshyas-Interception-Wing?awid=1576', True),
    ('ALE-002', Decimal('39.95'), 'https://www.nobleknight.com/P/2148527003/ALEPH-Support-Pack-2026-Edition?awid=1576', True),
    ('ALE-003', Decimal('85.95'), 'https://www.nobleknight.com/P/2148526954/ALEPH-Army-Pack?awid=1576', True),
    ('ALE-004', Decimal('46.95'), 'https://www.nobleknight.com/P/2148400357/K2-Auxiliars?awid=1576', True),
    ('ALE-005', Decimal('78.95'), 'https://www.nobleknight.com/P/2148246292/Posthumans?awid=1576', True),
    ('ALE-006', Decimal('42.95'), 'https://www.nobleknight.com/P/2148278473/Ajax-the-Great?awid=1576', True),
    ('ALE-007', Decimal('34.95'), 'https://www.nobleknight.com/P/2148145379/Atalanta-Agemas-NCO-and-Spotbot?awid=1576', True),
    ('ALE-008', Decimal('84.95'), 'https://www.nobleknight.com/P/2148117864/Reinforcements---ALEPH-Pack-Alpha?awid=1576', True),
    ('ALE-009', Decimal('66.95'), 'https://www.nobleknight.com/P/2148112958/Myrmidons?awid=1576', True),
    ('ALE-010', Decimal('49.95'), 'https://www.nobleknight.com/P/2148097516/Steel-Phalanx-Expansion-Pack-Alpha?awid=1576', True),
    ('ALE-011', Decimal('16.49'), 'https://www.nobleknight.com/P/2148071631/Phoenix-Heavy-Rocket-Launcher?awid=1576', True),
    ('ALE-012', Decimal('62.95'), 'https://www.nobleknight.com/P/2148055331/Aleph-Booster-Pack-Beta?awid=1576', True),
    ('ALE-013', Decimal('36.95'), 'https://www.nobleknight.com/P/2148037803/Agamemnon-the-Atreides?awid=1576', True),
    ('ALE-014', Decimal('66.95'), 'https://www.nobleknight.com/P/2148036097/Rebot-Remotes-Pack?awid=1576', True),
    ('ALE-015', Decimal('51.95'), 'https://www.nobleknight.com/P/2148013965/Aleph-Support-Pack?awid=1576', True),
    ('ALE-016', Decimal('51.95'), 'https://www.nobleknight.com/P/2148036098/Marut---Pose-B?awid=1576', True),
    ('ALE-017', Decimal('42.95'), 'https://www.nobleknight.com/P/2148278506/Probots?awid=1576', True),
    ('ALE-018', Decimal('47.95'), 'https://www.nobleknight.com/P/2147746272/Yadu-Troops?awid=1576', True),
    ('ALE-019', Decimal('16.49'), 'https://www.nobleknight.com/P/2147743986/Dart---Optimate-Huntress?awid=1576', True),
    ('ALE-021', Decimal('50.95'), 'https://www.nobleknight.com/P/2147620072/Hector---Homerid-Champion-w-Heavy-Pistol?awid=1576', True),
]


class Command(BaseCommand):
    help = 'Seed Noble Knight Games US prices and URLs for Infinity: ALEPH. Idempotent.'

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
                f'Seeded {seeded} Infinity ALEPH Noble Knight prices. Skipped: {skipped}.'
            )
        )
