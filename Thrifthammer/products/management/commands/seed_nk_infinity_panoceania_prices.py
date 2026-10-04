"""
Seed Noble Knight Games US prices for Infinity: PanOceania.

Uses the existing `noble-knight-games` Retailer (US, is_uk=False) -- does
not create it, matching the pattern for every other category's NK seed
command.

Source: user-supplied "Noble Knight U.S Infinity.xlsx" (Title/Title_URL/
Price columns), plus 2 user-supplied URLs for products not in the sheet
(PAN-009 paint set, PAN-028 Karhu). Noble Knight's price is a retailer price,
not an MSRP, so Product.msrp is deliberately not touched here.

Every URL below carries Noble Knight's `?awid=1576` affiliate parameter
(see add_nk_affiliate_tags.py) -- added directly here since that cleanup
command is not in the Procfile and would not fix this command's own output
on the next redeploy otherwise. The NK scraper strips the tag when fetching.

Every match was made by reading, not by script, every URL was fetched live
and its page title and price confirmed (the sheet's price for the 43 sheet
rows, the live page price for the 2 user-supplied URLs), and the picks and the
missing list were confirmed with the user (2026-10-02). All 45 listings were
in stock on 2026-10-02; price is create-only so the NK scraper's later
refreshes survive redeploys.

45 of 48 PanOceania SKUs written here. Not in the sheet and not supplied:
PAN-001 Indigo Spec-Ops Bundle, PAN-032 Vargar Maximum Security Team, PAN-047
Seraphs.

Notes on individual picks (confirmed with the user):
- PAN-012 PanOceania Support Pack is NK's "Essentials - PanOceania Support
  Pack" ($29.95), not the plain "PanOceania Support Pack" ($34.95).
- PAN-008 is "PanOceania Cutters TAG Pack" ($59.95), not NK's older plain
  "Cutters" listing.
- PAN-023 Reinforcements: PanOceania Pack Alpha is NK's "Acontecimento Combat
  Force Repack Alpha" (URL supplied by the user; NK has no listing named
  "Reinforcements - PanOceania Pack Alpha"). Its page reads "Was old price:
  $138.95 New Price $117.95", so the current price $117.95 is stored. NOTE:
  the NK scraper's _extract_price takes the FIRST dollar amount in that
  element and would read the old $138.95 on its next run.
- PAN-009 PanOceania Paint Set is NK's "Panoceania Paint Set w/Exclusive
  Fusilier Paramedic" (user-supplied URL, $65.95).
- PAN-028 Karhu Special Team is user-supplied ($50.00).

Run once on Railway startup via Procfile. Safe to re-run -- idempotent.
"""
from decimal import Decimal

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Product, Retailer

_NK_SLUG = 'noble-knight-games'

# (gw_sku, usd_price, url, in_stock)
_PRICES = [
    ('PAN-002', Decimal('29.95'), 'https://www.nobleknight.com/P/2147479915/Indigo-Spec-Ops?awid=1576', True),
    ('PAN-003', Decimal('39.95'), 'https://www.nobleknight.com/P/2148527061/Optimate-Agent-Maximus?awid=1576', True),
    ('PAN-004', Decimal('52.95'), 'https://www.nobleknight.com/P/2148454549/Kestrel-Expansion-Pack-Delta?awid=1576', True),
    ('PAN-005', Decimal('25.95'), 'https://www.nobleknight.com/P/2148491651/Jeanne-dArc-20-Mobility-Armor?awid=1576', True),
    ('PAN-006', Decimal('39.95'), 'https://www.nobleknight.com/P/2148322116/Essentials---PanOceania-Booster-Pack-Alpha?awid=1576', True),
    ('PAN-007', Decimal('51.95'), 'https://www.nobleknight.com/P/2148322081/Drummers-Mobile-Support-Section?awid=1576', True),
    ('PAN-008', Decimal('59.95'), 'https://www.nobleknight.com/P/2148322067/PanOceania-Cutters-TAG-Pack?awid=1576', True),
    ('PAN-009', Decimal('65.95'), 'https://www.nobleknight.com/P/2148301959/Panoceania-Paint-Set-w-Exclusive-Fusilier-Paramedic?awid=1576', True),
    ('PAN-010', Decimal('54.95'), 'https://www.nobleknight.com/P/2148301989/Kestrel-Expansion-Pack-Gamma?awid=1576', True),
    ('PAN-011', Decimal('39.95'), 'https://www.nobleknight.com/P/2148301981/Dronbot-Remotes-Pack?awid=1576', True),
    ('PAN-012', Decimal('29.95'), 'https://www.nobleknight.com/P/2148281441/Essentials---PanOceania-Support-Pack?awid=1576', True),
    ('PAN-013', Decimal('52.95'), 'https://www.nobleknight.com/P/2148281437/Kestrel-Expansion-Pack-Beta?awid=1576', True),
    ('PAN-014', Decimal('27.95'), 'https://www.nobleknight.com/P/2148348948/Dr-Priya-Harper---Archeo-Raider-Plasma-Carbine?awid=1576', True),
    ('PAN-015', Decimal('82.95'), 'https://www.nobleknight.com/P/2148348921/PanOceania-Army-Pack?awid=1576', True),
    ('PAN-016', Decimal('26.95'), 'https://www.nobleknight.com/P/2148246258/Beasthunters-Free-Guild-Tactical-Bow?awid=1576', True),
    ('PAN-017', Decimal('70.95'), 'https://www.nobleknight.com/P/2148206374/Triphammers---Repurposed-Industrial-TAGs?awid=1576', True),
    ('PAN-018', Decimal('20.95'), 'https://www.nobleknight.com/P/2148200477/Freelance-Operator-Samsa-Plasma-Rifle?awid=1576', True),
    ('PAN-019', Decimal('49.95'), 'https://www.nobleknight.com/P/2148186786/Tikbalangs---Armored-Chasseurs-Regiment?awid=1576', True),
    ('PAN-020', Decimal('24.95'), 'https://www.nobleknight.com/P/2148145386/Warcors---War-Correspondents?awid=1576', True),
    ('PAN-021', Decimal('47.95'), 'https://www.nobleknight.com/P/2148278509/Maximus-Optimate-and-HexaDome-Legend?awid=1576', True),
    ('PAN-022', Decimal('34.95'), 'https://www.nobleknight.com/P/2148112955/Diggers-Armed-Prospectors-Chain-Rifle?awid=1576', True),
    ('PAN-023', Decimal('117.95'), 'https://www.nobleknight.com/P/2148424924/Acontecimento-Combat-Force-Repack-Alpha?awid=1576', True),
    ('PAN-024', Decimal('57.95'), 'https://www.nobleknight.com/P/2148071626/Military-Orders-Expansion-Pack-Alpha?awid=1576', True),
    ('PAN-025', Decimal('55.95'), 'https://www.nobleknight.com/P/2148071623/Armbots?awid=1576', True),
    ('PAN-026', Decimal('66.95'), 'https://www.nobleknight.com/P/2148048605/Dire-Foes-Mission-Pack-12---Troubled-Theft?awid=1576', True),
    ('PAN-027', Decimal('122.95'), 'https://www.nobleknight.com/P/2148036108/Military-Order-Hospitaller-Action-Pack?awid=1576', True),
    ('PAN-028', Decimal('50.00'), 'https://www.nobleknight.com/P/2148408163/Karhu-Special-Team?awid=1576', True),
    ('PAN-029', Decimal('46.95'), 'https://www.nobleknight.com/P/2147994075/PanOceania-Headquarters-Pack?awid=1576', True),
    ('PAN-030', Decimal('20.95'), 'https://www.nobleknight.com/P/2148408062/Nokken-Special-Intervention-and-Recon-Team?awid=1576', True),
    ('PAN-031', Decimal('121.95'), 'https://www.nobleknight.com/P/2148482355/Panoceania-WinterFor-Action-Pack?awid=1576', True),
    ('PAN-033', Decimal('24.95'), 'https://www.nobleknight.com/P/2148278471/Knight-of-Santiago-Spitfire?awid=1576', True),
    ('PAN-034', Decimal('66.95'), 'https://www.nobleknight.com/P/2148036099/Knight-of-Montesa-Red-Fury?awid=1576', True),
    ('PAN-035', Decimal('30.95'), 'https://www.nobleknight.com/P/2148299294/Motorized-Bounty-Hunters-Boarding-Shotgun?awid=1576', True),
    ('PAN-036', Decimal('18.95'), 'https://www.nobleknight.com/P/2148491646/Oktavia-Grimsdottir-Icebreaker-Harpooner-2025-Edition?awid=1576', True),
    ('PAN-037', Decimal('58.95'), 'https://www.nobleknight.com/P/2147895060/Trinitarian-Tertiaries?awid=1576', True),
    ('PAN-038', Decimal('72.95'), 'https://www.nobleknight.com/P/2147909629/Teutonic-Knights?awid=1576', True),
    ('PAN-039', Decimal('126.95'), 'https://www.nobleknight.com/P/2147869314/Military-Orders-Action-Pack?awid=1576', True),
    ('PAN-040', Decimal('23.95'), 'https://www.nobleknight.com/P/2147875596/Monstruckers-Boarding-Shotgun?awid=1576', True),
    ('PAN-041', Decimal('21.95'), 'https://www.nobleknight.com/P/2147869497/Aida-Swanson---Submondo-Smuggler-Submachine-Gun?awid=1576', True),
    ('PAN-042', Decimal('36.95'), 'https://www.nobleknight.com/P/2147788236/Helot-Militia?awid=1576', True),
    ('PAN-043', Decimal('36.95'), 'https://www.nobleknight.com/P/2147757385/Orc-Troops?awid=1576', True),
    ('PAN-044', Decimal('17.95'), 'https://www.nobleknight.com/P/2147753242/Patsy-Garnett?awid=1576', True),
    ('PAN-045', Decimal('31.95'), 'https://www.nobleknight.com/P/2147656990/Tech-Bee-and-Crabbot-Ancillary-Remote-Unit?awid=1576', True),
    ('PAN-046', Decimal('19.95'), 'https://www.nobleknight.com/P/2147655149/Miranda-Ashcroft---Authorized-Bounty-Hunter-w-Combi-Rifle?awid=1576', True),
    ('PAN-048', Decimal('47.95'), 'https://www.nobleknight.com/P/2148013956/Mulebots?awid=1576', True),
]


class Command(BaseCommand):
    help = 'Seed Noble Knight Games US prices and URLs for Infinity: PanOceania. Idempotent.'

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
                f'Seeded {seeded} Infinity PanOceania Noble Knight prices. Skipped: {skipped}.'
            )
        )
