"""
Seed Noble Knight Games US prices for Infinity: Nomads.

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
picks and the missing list were confirmed with the user (2026-10-03). All 30
listings were in stock on 2026-10-03; price is create-only so the NK
scraper's later refreshes survive redeploys.

30 of 36 Nomads SKUs written here. Not in the sheet (confirmed by searching
it) and not supplied: NOM-010 Nomads Support Pack, NOM-023 Corregidor Fireteam
Pack Alpha, NOM-025 Cassandra Kusanagi, NOM-029 Corregidor Bandits, NOM-030
The Hollow Men, NOM-032 Zoe and Pi-Well.

Notes:
- NOM-031 Hecklers is ON SALE ("Was old price $19.95 New Price $17.95"): the
  current price $17.95 is stored.
- NOM-011 Moran is NK's "Moran - Massai Hunters (2024 Edition)" ($36.95), not
  the "2023 Edition" ($26.95, on sale from $32.95) (confirmed with the user).
- NOM-033 Mobile Brigada is the four-model "Mobile Brigadas w/Missile Launcher,
  Boarding Shotgun, HMG, & Hacker" box ($69.95), not the single "Mobile Brigada
  w/HMG" ($19.95) (confirmed with the user).
- NOM-012 Zeros is the plain "Zeros" ($62.95), not the older single "Zeros
  w/Combi Rifle & Hacker". NOM-013 is NK's "Lizard Squadron", NOM-014 is NK's
  "Nomads Pack Alpha", NOM-005 is NK's exact "Nomads Hero, Wolfgang Amadeus
  Wolff".

Run once on Railway startup via Procfile. Safe to re-run -- idempotent.
"""
from decimal import Decimal

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Product, Retailer

_NK_SLUG = 'noble-knight-games'

# (gw_sku, usd_price, url, in_stock)
_PRICES = [
    ('NOM-001', Decimal('61.95'), 'https://www.nobleknight.com/P/2148527043/Gecko-Squadron-2026-Edition?awid=1576', True),
    ('NOM-002', Decimal('85.95'), 'https://www.nobleknight.com/P/2148526974/Nomads-Army-Pack?awid=1576', True),
    ('NOM-003', Decimal('46.95'), 'https://www.nobleknight.com/P/2148368756/Tunguska-Triggermen?awid=1576', True),
    ('NOM-004', Decimal('62.95'), 'https://www.nobleknight.com/P/2148368472/Switchers-Gruppa?awid=1576', True),
    ('NOM-005', Decimal('33.95'), 'https://www.nobleknight.com/P/2148368514/Nomads-Hero-Wolfgang-Amadeus-Wolff?awid=1576', True),
    ('NOM-006', Decimal('34.95'), 'https://www.nobleknight.com/P/2148491611/Nomads-Booster-Pack-Alpha?awid=1576', True),
    ('NOM-007', Decimal('65.95'), 'https://www.nobleknight.com/P/2148491606/Go-Pods?awid=1576', True),
    ('NOM-008', Decimal('69.95'), 'https://www.nobleknight.com/P/2148322096/Nomads-Szalamandra-Squadron-TAG-Pack?awid=1576', True),
    ('NOM-009', Decimal('38.95'), 'https://www.nobleknight.com/P/2148322065/Nomads-Zonds-Remotes-Pack?awid=1576', True),
    ('NOM-011', Decimal('36.95'), 'https://www.nobleknight.com/P/2148491594/Moran---Massai-Hunters-2024-Edition?awid=1576', True),
    ('NOM-012', Decimal('62.95'), 'https://www.nobleknight.com/P/2148137111/Zeros?awid=1576', True),
    ('NOM-013', Decimal('51.95'), 'https://www.nobleknight.com/P/2148112952/Lizard-Squadron?awid=1576', True),
    ('NOM-014', Decimal('91.95'), 'https://www.nobleknight.com/P/2148278480/Nomads-Pack-Alpha?awid=1576', True),
    ('NOM-015', Decimal('46.95'), 'https://www.nobleknight.com/P/2148097509/Bakunin-Expansion-Pack-Beta?awid=1576', True),
    ('NOM-016', Decimal('52.95'), 'https://www.nobleknight.com/P/2148088034/Bakunin-Uberfallkommando?awid=1576', True),
    ('NOM-017', Decimal('48.95'), 'https://www.nobleknight.com/P/2148071609/Bakunin-Expansion-Pack-Alpha?awid=1576', True),
    ('NOM-018', Decimal('65.95'), 'https://www.nobleknight.com/P/2148064387/Sputniks?awid=1576', True),
    ('NOM-019', Decimal('49.95'), 'https://www.nobleknight.com/P/2148064425/Stigmata?awid=1576', True),
    ('NOM-020', Decimal('34.95'), 'https://www.nobleknight.com/P/2148055311/Meteor-Zond-Boarding-Shotgun?awid=1576', True),
    ('NOM-021', Decimal('51.95'), 'https://www.nobleknight.com/P/2148047604/Corregidor-Fireteam-Pack-Beta?awid=1576', True),
    ('NOM-022', Decimal('55.95'), 'https://www.nobleknight.com/P/2148037784/Tomcats?awid=1576', True),
    ('NOM-024', Decimal('51.95'), 'https://www.nobleknight.com/P/2148014254/Gator-Squadron?awid=1576', True),
    ('NOM-026', Decimal('71.95'), 'https://www.nobleknight.com/P/2147854998/Tunguska-Cheerkillers?awid=1576', True),
    ('NOM-027', Decimal('55.95'), 'https://www.nobleknight.com/P/2147769067/Puppetactica-Company?awid=1576', True),
    ('NOM-028', Decimal('94.95'), 'https://www.nobleknight.com/P/2147760436/Fast-Offensive-Unit-Zondnautica?awid=1576', True),
    ('NOM-031', Decimal('17.95'), 'https://www.nobleknight.com/P/2147728050/Hecklers-Combi-Rifle?awid=1576', True),
    ('NOM-033', Decimal('69.95'), 'https://www.nobleknight.com/P/2147599719/Mobile-Brigadas-w-Missile-Launcher-Boarding-Shotgun-HMG-and-Hacker?awid=1576', True),
    ('NOM-034', Decimal('47.95'), 'https://www.nobleknight.com/P/2147586447/Corregidor-Jaguars?awid=1576', True),
    ('NOM-035', Decimal('44.95'), 'https://www.nobleknight.com/P/2147554962/Tunguska-Interventors?awid=1576', True),
    ('NOM-036', Decimal('47.95'), 'https://www.nobleknight.com/P/2147428399/Salyut-Zonds-w-Evo-Repeater-and-Combi-Rifle?awid=1576', True),
]


class Command(BaseCommand):
    help = 'Seed Noble Knight Games US prices and URLs for Infinity: Nomads. Idempotent.'

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
                f'Seeded {seeded} Infinity Nomads Noble Knight prices. Skipped: {skipped}.'
            )
        )
