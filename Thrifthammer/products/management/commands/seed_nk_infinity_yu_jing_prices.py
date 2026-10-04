"""
Seed Noble Knight Games US prices for Infinity: Yu Jing.

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
and its page title and price confirmed against the sheet, and the picks and
the missing list were confirmed with the user (2026-10-02). All 33 listings
were in stock on 2026-10-02; price is create-only so the NK scraper's later
refreshes survive redeploys.

33 of 37 Yu Jing SKUs written here. Not in the sheet (confirmed by searching
it): YUJ-001 Gui Feng Spec-Ops Bundle, YUJ-002 Gui Feng Spec-Ops, YUJ-025
White Banner Action Pack, YUJ-037 Yaopu Pangguling.

Notes on individual picks (confirmed with the user):
- YUJ-007 is NK's "Yu Jing Hero, Lei Gong, Invincibles Lord of Thunder"
  ($33.95), not the plain "Lei Gong" listing ($27.95).
- YUJ-012 Yu Jing Support Pack is the "(2025 Edition)" ($35.95), not the older
  plain listing ($28.95).
- YUJ-014 Yu Jing Action Pack is "Essentials - Yu Jing Action Pack" ($104.95),
  not the plain "Yu Jing Action Pack" ($121.95).
- YUJ-003 Ninjas is the "(MULTI Sniper/Hacker)" listing, not the older "Ninjas
  w/Multi Hacker"; YUJ-004 is the exact "Sun Tze (Thunderbolt, Light Shotgun)".
- YUJ-032 Tiger Soldiers is ON SALE: its page reads "Was old price: $25.95
  New Price $23.95", so the current price $23.95 is stored. NOTE: the NK
  scraper's _extract_price takes the FIRST dollar amount in that element and
  would read the old $25.95 on its next run.

Run once on Railway startup via Procfile. Safe to re-run -- idempotent.
"""
from decimal import Decimal

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Product, Retailer

_NK_SLUG = 'noble-knight-games'

# (gw_sku, usd_price, url, in_stock)
_PRICES = [
    ('YUJ-003', Decimal('51.95'), 'https://www.nobleknight.com/P/2148527059/Ninjas-MULTI-Sniper-Hacker?awid=1576', True),
    ('YUJ-004', Decimal('34.95'), 'https://www.nobleknight.com/P/2148527063/Sun-Tze-Thunderbolt-Light-Shotgun?awid=1576', True),
    ('YUJ-005', Decimal('60.95'), 'https://www.nobleknight.com/P/2148491613/Kuang-Shi-2026-Edition?awid=1576', True),
    ('YUJ-006', Decimal('81.95'), 'https://www.nobleknight.com/P/2148368383/Feiquan-Imperial-Tactical-Wing?awid=1576', True),
    ('YUJ-007', Decimal('33.95'), 'https://www.nobleknight.com/P/2148368753/Yu-Jing-Hero-Lei-Gong-Invincibles-Lord-of-Thunder?awid=1576', True),
    ('YUJ-008', Decimal('25.95'), 'https://www.nobleknight.com/P/2148491653/Shinobu-Kitsune-Monofilament-CCW?awid=1576', True),
    ('YUJ-009', Decimal('34.95'), 'https://www.nobleknight.com/P/2148491610/Yu-Jing-Booster-Pack-Alpha-2025-Edition?awid=1576', True),
    ('YUJ-010', Decimal('51.95'), 'https://www.nobleknight.com/P/2148322094/Yu-Jing-Blue-Wolf-Mongol-Cavalry-TAG-Pack?awid=1576', True),
    ('YUJ-011', Decimal('64.95'), 'https://www.nobleknight.com/P/2148301992/Longwang-Imperial-TAG-Police?awid=1576', True),
    ('YUJ-012', Decimal('35.95'), 'https://www.nobleknight.com/P/2148301976/Yu-Jing-Support-Pack-2025-Edition?awid=1576', True),
    ('YUJ-013', Decimal('52.95'), 'https://www.nobleknight.com/P/2148281447/White-Banner-Expansion-Pack-Beta?awid=1576', True),
    ('YUJ-014', Decimal('104.95'), 'https://www.nobleknight.com/P/2148281461/Essentials---Yu-Jing-Action-Pack?awid=1576', True),
    ('YUJ-015', Decimal('42.95'), 'https://www.nobleknight.com/P/2148206359/White-Banner-Expansion-Pack-Alpha?awid=1576', True),
    ('YUJ-016', Decimal('48.95'), 'https://www.nobleknight.com/P/2148491590/Yaoxie-Remotes-Lu-Duan---Rui-Shi?awid=1576', True),
    ('YUJ-017', Decimal('44.95'), 'https://www.nobleknight.com/P/2148491587/Invincible-Army-Expansion-Pack?awid=1576', True),
    ('YUJ-018', Decimal('25.95'), 'https://www.nobleknight.com/P/2148117869/Guilang---Hacker?awid=1576', True),
    ('YUJ-019', Decimal('57.95'), 'https://www.nobleknight.com/P/2148491581/Zuyong-Invincibles?awid=1576', True),
    ('YUJ-020', Decimal('90.95'), 'https://www.nobleknight.com/P/2148088913/Reinforcements---Yu-Jing-Pack-Alpha?awid=1576', True),
    ('YUJ-021', Decimal('20.95'), 'https://www.nobleknight.com/P/2148088006/Bixie-the-Jade-Champion?awid=1576', True),
    ('YUJ-022', Decimal('56.95'), 'https://www.nobleknight.com/P/2148071627/Shaolin-Warrior-Monks?awid=1576', True),
    ('YUJ-023', Decimal('23.95'), 'https://www.nobleknight.com/P/2148055316/Hulang-Shocktroopers-Submachine-Gun?awid=1576', True),
    ('YUJ-024', Decimal('56.95'), 'https://www.nobleknight.com/P/2147994079/Tian-Gou-Orbital-Activity-Squad?awid=1576', True),
    ('YUJ-026', Decimal('56.95'), 'https://www.nobleknight.com/P/2148218257/Yaofang-Long-Ya?awid=1576', True),
    ('YUJ-027', Decimal('60.95'), 'https://www.nobleknight.com/P/2148218256/Jujak-Regiment-Korean-Shock-Infantry?awid=1576', True),
    ('YUJ-028', Decimal('61.95'), 'https://www.nobleknight.com/P/2147895065/Shang-Ji-Invincibles?awid=1576', True),
    ('YUJ-029', Decimal('72.95'), 'https://www.nobleknight.com/P/2147878445/Betrayal-Characters-Pack?awid=1576', True),
    ('YUJ-030', Decimal('24.95'), 'https://www.nobleknight.com/P/2147788229/Libertos-Freedom-Fighters-Light-Shotgun?awid=1576', True),
    ('YUJ-031', Decimal('37.95'), 'https://www.nobleknight.com/P/2147769074/Mowang-Troops?awid=1576', True),
    ('YUJ-032', Decimal('23.95'), 'https://www.nobleknight.com/P/2147680850/Tiger-Soldiers-w-Boarding-Shotgun-and-Spitfire?awid=1576', True),
    ('YUJ-033', Decimal('20.95'), 'https://www.nobleknight.com/P/2147623464/Dragon-Lady---Imperial-Service-Judge?awid=1576', True),
    ('YUJ-034', Decimal('55.95'), 'https://www.nobleknight.com/P/2147620066/Su-Juian---Immediate-Action-Unit?awid=1576', True),
    ('YUJ-035', Decimal('85.95'), 'https://www.nobleknight.com/P/2147603962/Guijia-Squadrons?awid=1576', True),
    ('YUJ-036', Decimal('28.95'), 'https://www.nobleknight.com/P/2147592386/Yan-Huo-Invincibles-w-HMC?awid=1576', True),
]


class Command(BaseCommand):
    help = 'Seed Noble Knight Games US prices and URLs for Infinity: Yu Jing. Idempotent.'

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
                f'Seeded {seeded} Infinity Yu Jing Noble Knight prices. Skipped: {skipped}.'
            )
        )
