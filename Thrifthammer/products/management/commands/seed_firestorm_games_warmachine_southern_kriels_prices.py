"""
Seed Firestorm Games UK prices for Warmachine: Southern Kriels.

Idempotent -- CurrentPrice rows are written via update_or_create keyed on
(product, retailer), price is create-only (see create_defaults below) so a
redeploy never resets a price a manual correction or future live updater
has since changed. NEVER writes msrp_gbp -- Firestorm is a discount
competitor here, not the MSRP source; steamforged-games-uk holds that role
for Warmachine (see seed_steamforged_uk_warmachine_crucible_guard_prices.py).

Price parsing rule: Firestorm shows two numbers per listing (struck-through
RRP, then sale price). ALWAYS use the lower (sale) price, never the RRP.

Source: https://www.firestormgames.co.uk/wargames-miniatures/warmachine-4th-edition
(SOUTHERN KRIELS sub-category, exactly 9 listings there -- confirmed by
the user 2026-09-26) plus a full-site search for "Southern Kriels" and
each of the 45 other individual DB product names in this faction (Fortress
King, Kithguard Journeyman & Ramhead, Ol' Scuttlebutt, Kithguard Infantry/
Sergeant/Steelbacks/Sidewinder, Quartermaster, Bosun, Tapper, Pyg Boarding
Party/Battle Brig/Shockers/Dirge/Galley Crew/Cannon Crew, Braghen
Ragemonger, Marauder Crew A/B, Vorogger + Variant, Shadows & Scum, General
Gunnbjorn, Kithguard Defenses/Mortar Team/Medics/Tunnel Rats/Throat
Cutters/Hailer/Guard Post, Deepborn Dire Troll + Variant, Reef Troll, Booty
Boss, Coxswain, Surgeon, Abyssal King, Fire Guardians + Variant, Fugue
Walker, Fire Spitters, Spirit Shamans, Brinebloods Command Starter,
Mistborn Dire Troll, Jungle Troll) -- none returned a genuine match,
confirmed 2026-09-26.

Only 8 of the 9 SOUTHERN KRIELS-page listings map to catalog SKUs. The
9th, "Warmachine: Foulblood's Armada Command Starter" (£67.49, 1 in
stock), is the SAME missing SKU already flagged to the user in an earlier
session (see project_warmachine_faction_rollout memory, Southern Kriels
section) -- confirmed independently on Miniature Market and Noble Knight
as a genuine, current, in-stock Steamforged product (MFG Part SFIK-SKR328)
with no matching Product row in our catalog. Firestorm is now a third
independent retailer confirming it exists. Not added here -- still
requires explicit user instruction to create the Product row, per the
no-new-products-in-seed-commands rule.

8 of 54 catalog SKUs matched, each opened and verified individually.
"Southern Kriels Fire Tongue Warriors Command Cadre" (WMH-287) is
0-in-stock/UNAVAILABLE at Firestorm -- seeded with the real price and
in_stock=False, per the sold-out-listing rule.

Run once on Railway startup via Procfile. Safe to re-run -- idempotent.
"""
from decimal import Decimal

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Product, Retailer

_FIRESTORM_SLUG = 'firestorm-games'

# (gw_sku, gbp_price, url, in_stock)
_PRICES = [
    ('WMH-138', Decimal('121.49'), 'https://www.firestormgames.co.uk/warmachine:-southern-kriels-kithguard-auxiliary-expansion?aff=6a4ab07d1c6f9', True),
    ('WMH-120', Decimal('130.49'), 'https://www.firestormgames.co.uk/warmachine:-southern-kriels-kithguard-core-expansion?aff=6a4ab07d1c6f9', False),
    ('WMH-042', Decimal('62.99'), 'https://www.firestormgames.co.uk/warmachine---southern-kriels-kithguard-battlegroup-box?aff=6a4ab07d1c6f9', True),
    ('WMH-010', Decimal('67.49'), 'https://www.firestormgames.co.uk/warmachine---southern-kriels-kithguard-command-starter?aff=6a4ab07d1c6f9', True),
    ('WMH-287', Decimal('85.49'), 'https://www.firestormgames.co.uk/warmachine:-southern-kriels-fire-tongue-warriors-command-cadre-?aff=6a4ab07d1c6f9', False),
    ('WMH-214', Decimal('62.99'), 'https://www.firestormgames.co.uk/warmachine:-southern-kriels-brineblood-marauders-battlegroup-box?aff=6a4ab07d1c6f9', True),
    ('WMH-213', Decimal('121.49'), 'https://www.firestormgames.co.uk/warmachine:-southern-kriels-brineblood-marauders-auxiliary-expansion?aff=6a4ab07d1c6f9', True),
    ('WMH-212', Decimal('130.49'), 'https://www.firestormgames.co.uk/warmachine:-southern-kriels-brineblood-marauders-core-expansion?aff=6a4ab07d1c6f9', True),
]


class Command(BaseCommand):
    help = 'Seed Firestorm Games UK prices and URLs for Warmachine: Southern Kriels. Idempotent.'

    def handle(self, *args, **options):
        retailer, created = Retailer.objects.get_or_create(
            slug=_FIRESTORM_SLUG,
            defaults={
                'name': 'Firestorm Games',
                'website': 'https://www.firestormgames.co.uk/?aff=6a4ab07d1c6f9',
                'country': 'UK',
                'is_active': True,
                'is_uk': True,
            },
        )
        if created:
            self.stdout.write(f'Created retailer: {retailer.name}')

        seeded = 0
        skipped = 0
        for gw_sku, gbp_price, url, in_stock in _PRICES:
            try:
                product = Product.objects.get(gw_sku=gw_sku)
            except Product.DoesNotExist:
                self.stderr.write(f'SKIP — SKU {gw_sku} not in DB')
                skipped += 1
                continue

            cp_defaults = {'url': url, 'in_stock': in_stock, 'not_available': False, 'currency': 'GBP'}
            CurrentPrice.objects.update_or_create(
                product=product,
                retailer=retailer,
                defaults=cp_defaults,
                create_defaults={**cp_defaults, 'price': gbp_price},
            )
            seeded += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Seeded {seeded} Warmachine: Southern Kriels Firestorm Games prices. Skipped: {skipped}.'
            )
        )
