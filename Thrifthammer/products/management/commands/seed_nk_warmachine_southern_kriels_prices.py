"""
Management command: seed_nk_warmachine_southern_kriels_prices

Seeds Noble Knight URLs for Warmachine: Southern Kriels products from the
user-supplied "Southern Kriels - NK.xlsx" sheet (18 rows, Title/URL/Price).
Every row was fetched and verified live before inclusion -- title, format,
stock, and (where present) manufacturer part # cross-checked against the
Miniature Market listings sourced the same day.

12 of the 54 Southern Kriels products have a confirmed real NK listing:
- 9 in stock with a current price at verification time.
- WMH-215 (Deepborn Dire Troll), WMH-216 (Reef Troll), WMH-068 (Pyg Battle
  Brig): real listings, but tagged "Out of Print" (old Privateer Press
  Mk III-era PIP-numbered printing of the same sculpt, not a current
  Steamforged Mk IV restock) -- seeded with price=None, in_stock=False,
  not_available=False so the URL still earns affiliate credit and self-
  heals if NK ever relists a current printing.

WMH-042 (Kithguard Battlegroup Box): the sheet's $55.00 price is NK's
"Fair/NM" (used) condition tier -- rejected as not a fair new-price
comparison, per site convention. Used the same listing's "MINT/New" tier
($67.95) instead.

WMH-120 (Kithguard Core Expansion): the sheet had TWO NK listings for this
exact same physical product (same title/description/content, same $144.95
price) -- NKG #2148459583 ("Southern Kriels Kithguard Core Expansion") and
NKG #2148472861 ("Kithguard Core Expansion"). The first's own MFG Part #
field (SFIK-SKR121) is wrong -- that's actually the Brineblood Core
Expansion's part number, an NK data-entry error (title/description are
unambiguously Kithguard). Used the second listing instead, whose MFG Part #
(SFIK-SKR400) is internally consistent and matches the MM-verified code.

Not included -- checked live, none map to an existing catalog SKU or are
otherwise excluded:
  - Major Abraham Stormcraw (2026 Convention Exclusive): explicitly a
    convention-exclusive special release, also Out of Print -- excluded
    per the site's standing special/limited-edition convention.
  - Foulblood's Armada Command Cadre ($72.95 MSRP $79.99, MFG Part
    SFIK-SKR328, in stock): a genuine, current Steamforged Southern Kriels
    product -- confirmed real via both this NK listing and an independent
    Miniature Market listing the same day -- but does not match any of the
    54 SKUs in our catalog. Very likely a real product missing from the
    original "Southern Kriels - Warmachine - Steamforged.xlsx" batch that
    built this faction. Flagged to the user 2026-09-09, not added without
    explicit instruction.
  - Great Old One Character Warbeast Pack, Brineblood Marauders Army
    Expansion: old Privateer Press Mk III-era listings ("Fantasy Minis
    28mm", Out of Print), no matching catalog SKU either way.
  - Admiral Boomhowler: old Privateer Press Mk III-era listing, Out of
    Print. Possibly the old-edition name for "Greygore Boomhowler"
    (WMH-194), which exists in the DB but is NOT currently part of the
    Southern Kriels faction (still faction=None) -- flagged, not acted on.

create_defaults pattern: price, in_stock, last_seen are set only on
creation so scraper-set prices survive Railway redeploys.
url, listing_title, not_available are in defaults and always updated.

Usage:
    python manage.py seed_nk_warmachine_southern_kriels_prices
"""

from django.core.management.base import BaseCommand

NK_PRICES = [
    # (gw_sku, listing_title, price, url, in_stock, not_available)
    ('WMH-010', 'Kithguard Command Starter', 72.95, 'https://www.nobleknight.com/P/2148415372/Kithguard-Command-Starter?awid=1576', True, False),
    ('WMH-042', 'Kithguard Battlegroup Box', 67.95, 'https://www.nobleknight.com/P/2148425697/Kithguard-Battlegroup-Box?awid=1576', True, False),
    ('WMH-120', 'Kithguard Core Expansion', 144.95, 'https://www.nobleknight.com/P/2148472861/Kithguard-Core-Expansion?awid=1576', True, False),
    ('WMH-138', 'Southern Kriels Kithguard Auxiliary Expansion', 135.95, 'https://www.nobleknight.com/P/2148461014/Southern-Kriels-Kithguard-Auxiliary-Expansion?awid=1576', True, False),
    ('WMH-002', 'Fortress King', 199.95, 'https://www.nobleknight.com/P/2148515138/Fortress-King?awid=1576', True, False),
    ('WMH-212', 'Brineblood Marauders Core Expansion', 144.95, 'https://www.nobleknight.com/P/2148213917/Brineblood-Marauders-Core-Expansion?awid=1576', True, False),
    ('WMH-213', 'Brineblood Marauders Auxiliary Expansion', 135.95, 'https://www.nobleknight.com/P/2148213918/Brineblood-Marauders-Auxiliary-Expansion?awid=1576', True, False),
    ('WMH-214', 'Brineblood Marauders Battlegroup box', 67.95, 'https://www.nobleknight.com/P/2148213923/Brineblood-Marauders-Battlegroup-box?awid=1576', True, False),
    ('WMH-287', 'Fire Tongue Warriors Command Cadre', 90.95, 'https://www.nobleknight.com/P/2148207545/Fire-Tongue-Warriors-Command-Cadre?awid=1576', True, False),
    # -- Real listings, currently Out of Print (old PIP-numbered printing) --
    ('WMH-215', 'Deepborn Dire Troll', None, 'https://www.nobleknight.com/P/2148089024/Deepborn-Dire-Troll?awid=1576', False, False),
    ('WMH-216', 'Reef Troll', None, 'https://www.nobleknight.com/P/2148089028/Reef-Troll?awid=1576', False, False),
    ('WMH-068', 'Pyg Battle Brig', None, 'https://www.nobleknight.com/P/2148113601/Pyg-Battle-Brig?awid=1576', False, False),
]


class Command(BaseCommand):
    """Seed Noble Knight URLs for Warmachine: Southern Kriels products."""

    help = 'seed_nk_warmachine_southern_kriels_prices — NK URLs for Southern Kriels (12 of 54 SKUs confirmed)'

    def handle(self, *args, **options):
        """Run the command."""
        from django.utils import timezone

        from prices.models import CurrentPrice
        from products.models import Product, Retailer

        nk_retailer = Retailer.objects.get(slug='noble-knight-games')
        seeded = 0

        for (gw_sku, listing_title, price, url, in_stock, not_available) in NK_PRICES:
            product = Product.objects.get(gw_sku=gw_sku)
            CurrentPrice.objects.update_or_create(
                product=product,
                retailer=nk_retailer,
                defaults={
                    'listing_title': listing_title,
                    'url': url,
                    'not_available': not_available,
                },
                create_defaults={
                    'price': price,
                    'in_stock': in_stock,
                    'last_seen': timezone.now(),
                },
            )
            self.stdout.write(f'  seeded NK: {gw_sku}')
            seeded += 1

        self.stdout.write(self.style.SUCCESS(
            f'seed_nk_warmachine_southern_kriels_prices complete. {seeded} record(s) seeded.'
        ))
