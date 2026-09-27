"""
Seed Firestorm Games UK prices for Warmachine: Khymaera.

Idempotent -- CurrentPrice rows are written via update_or_create keyed on
(product, retailer), price is create-only (see create_defaults below) so a
redeploy never resets a price a manual correction or future live updater
has since changed. NEVER writes msrp_gbp -- Firestorm is a discount
competitor here, not the MSRP source; steamforged-games-uk holds that role
for Warmachine (see seed_steamforged_uk_warmachine_crucible_guard_prices.py).

Price parsing rule: Firestorm shows two numbers per listing (struck-through
RRP, then sale price). ALWAYS use the lower (sale) price, never the RRP.

Source: https://www.firestormgames.co.uk/wargames-miniatures/warmachine-4th-edition
(KHYMAERA sub-category, exactly 5 listings there -- confirmed by the user
2026-09-26) plus a full-site search for "Khymaera" and each of the 22 other
individual DB product names in this faction (Trikhymaerax, Shadow Seraph,
Hydrix + Variant, Vypex, Quick Fang Master/Stalkers/Wind Strikers,
Shadowmancer Scion, Wraithwing Paragon, Spinner, Talon Death Dealers/
Lashers, Wyrmspine Shadowmancers/Cinderbacks, Incarnate Conjuror + Variant,
Incarnate Knights, Drakyon, Lylyth the Raven Vengeance) -- none returned a
genuine match, confirmed 2026-09-26.

Only 4 of the 5 KHYMAERA-page listings map to catalog SKUs. The 5th,
"Warmachine: Khymaera Shard Nocturnes Command Starter" (£67.49), was
opened and verified to be a DIFFERENT, genuinely separate Command Starter
box (contents: Vallyx warlock, Aklyss, Pythia, Regulus, Shades) than our
WMH-323 "Khymaera Shadowflame Shard Command Starter (HIPS)" -- none of its
component models match any SKU in our catalog. WMH-323 itself has zero
listings on Firestorm under any name (confirmed via a dedicated search for
"Shadowflame Shard Command Starter"). Not force-matched; flagged here as a
genuine catalog gap (a real, current, separate retail SKU we don't carry),
not created per the no-new-products-in-seed-commands rule.

4 of 26 catalog SKUs matched, each opened and verified individually.

Run once on Railway startup via Procfile. Safe to re-run -- idempotent.
"""
from decimal import Decimal

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Product, Retailer

_FIRESTORM_SLUG = 'firestorm-games'

# (gw_sku, gbp_price, url, in_stock)
_PRICES = [
    ('WMH-229', Decimal('85.49'), 'https://www.firestormgames.co.uk/warmachine:-khymaera-shard-incarnates-cadre?aff=6a4ab07d1c6f9', True),
    ('WMH-228', Decimal('62.99'), 'https://www.firestormgames.co.uk/warmachine:-khymaera-shadowflame-shard-battlegroup-box?aff=6a4ab07d1c6f9', True),
    ('WMH-227', Decimal('121.49'), 'https://www.firestormgames.co.uk/warmachine:-khymaera-shadowflame-shard-auxiliary-expansion?aff=6a4ab07d1c6f9', True),
    ('WMH-226', Decimal('130.49'), 'https://www.firestormgames.co.uk/warmachine:-khymaera-shadowflame-shard-core-expansion?aff=6a4ab07d1c6f9', True),
]


class Command(BaseCommand):
    help = 'Seed Firestorm Games UK prices and URLs for Warmachine: Khymaera. Idempotent.'

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
                f'Seeded {seeded} Warmachine: Khymaera Firestorm Games prices. Skipped: {skipped}.'
            )
        )
