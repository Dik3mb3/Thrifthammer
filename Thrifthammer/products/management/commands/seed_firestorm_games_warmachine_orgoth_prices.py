"""
Seed Firestorm Games UK prices for Warmachine: Orgoth (Sea Raiders).

Idempotent -- CurrentPrice rows are written via update_or_create keyed on
(product, retailer), price is create-only (see create_defaults below) so a
redeploy never resets a price a manual correction or future live updater
has since changed. NEVER writes msrp_gbp -- Firestorm is a discount
competitor here, not the MSRP source; steamforged-games-uk holds that role
for Warmachine (see seed_steamforged_uk_warmachine_crucible_guard_prices.py).

Price parsing rule: Firestorm shows two numbers per listing (struck-through
RRP, then sale price). ALWAYS use the lower (sale) price, never the RRP.

Source: https://www.firestormgames.co.uk/wargames-miniatures/warmachine-4th-edition
(ORGOTH sub-category, exactly 6 listings there -- confirmed by the user
2026-09-26) plus a full-site search for "Orgoth" and each of the 24 other
individual DB product names in this faction (Orsus the Betrayed, Tyrant
Chassis Variant, Vulcar Forge Master, Tyrant/Jackal Warjacks, Assault/
Strike Reavers, Ulkor Barragers/Axers, Warwitch Coven, Reaver Skirmishers,
Rhok Harriers, Siege Tarask, Reaver Commander/Standard Variant, Horruskh,
Gharlghast, Orgoth Standard Bearer, Orgoth Reaver Commander, Ravener,
Grhotten Champion/Keeper, Gnashers, Orgoth Sea Raiders Command Starter) --
none returned a genuine match, confirmed 2026-09-26.

Only 4 of the 6 ORGOTH-page listings map to catalog SKUs. The other 2:
- "Warmachine: Frozen & Forgotten" (£94.49) is the SAME product already
  recorded under WMH-334 in seed_firestorm_games_warmachine_dusk_prices.py
  (Dusk-scoped row; no Orgoth-scoped sibling row exists in our catalog for
  it) -- not duplicated here.
- "Warmachine: Cursebound Command Cadre" (£85.49) was opened and verified
  to be a bundle box (Oriax the Soul Slaver + Halexus the Warlord +
  Gnashers + Grhotten Champion/Keeper + Raveners) with no single matching
  Product row -- its component units DO exist individually in our catalog
  (WMH-273/274/275/276), but the bundle itself as a retail SKU does not.
  Not force-matched; flagged as a genuine catalog gap.

4 of 28 catalog SKUs matched, each opened and verified individually.
"Warmachine: Orgoth Graveborn" on Firestorm maps to our WMH-101 "The
Graveborn Command Cadre (HIPS)" -- confirmed via contents (Anathia the
Imperishable Desolation, Revenant Champion, Barrow Ghoul, Charnel Hound,
The Execrators).

Run once on Railway startup via Procfile. Safe to re-run -- idempotent.
"""
from decimal import Decimal

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Product, Retailer

_FIRESTORM_SLUG = 'firestorm-games'

# (gw_sku, gbp_price, url, in_stock)
_PRICES = [
    ('WMH-101', Decimal('67.49'), 'https://www.firestormgames.co.uk/warmachine:-orgoth-graveborn?aff=6a4ab07d1c6f9', True),
    ('WMH-159', Decimal('62.99'), 'https://www.firestormgames.co.uk/warmachine:-orgoth-sea-raiders-battlegroup-box?aff=6a4ab07d1c6f9', True),
    ('WMH-158', Decimal('121.49'), 'https://www.firestormgames.co.uk/warmachine:-orgoth-sea-raiders-auxiliary-expansion?aff=6a4ab07d1c6f9', True),
    ('WMH-157', Decimal('130.49'), 'https://www.firestormgames.co.uk/warmachine:-orgoth-sea-raiders-core-expansion?aff=6a4ab07d1c6f9', True),
]


class Command(BaseCommand):
    help = 'Seed Firestorm Games UK prices and URLs for Warmachine: Orgoth. Idempotent.'

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
                f'Seeded {seeded} Warmachine: Orgoth Firestorm Games prices. Skipped: {skipped}.'
            )
        )
