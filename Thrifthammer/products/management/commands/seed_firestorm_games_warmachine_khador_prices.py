"""
Seed Firestorm Games UK prices for Warmachine: Khador.

Idempotent -- CurrentPrice rows are written via update_or_create keyed on
(product, retailer), price is create-only (see create_defaults below) so a
redeploy never resets a price a manual correction or future live updater
has since changed. NEVER writes msrp_gbp -- Firestorm is a discount
competitor here, not the MSRP source; steamforged-games-uk holds that role
for Warmachine (see seed_steamforged_uk_warmachine_crucible_guard_prices.py).

Price parsing rule: Firestorm shows two numbers per listing (struck-through
RRP, then sale price). ALWAYS use the lower (sale) price, never the RRP.

Source: https://www.firestormgames.co.uk/wargames-miniatures/warmachine-4th-edition
(KHADOR sub-category, confirmed exactly 9 genuine Warmachine listings there
2026-09-26) plus a full-site search for "Khador" and each of the 42 other
individual DB product names in this faction (Lord of The Hunt, Gorger,
Kontroller, Old Umbrey Lupine variants, Behemoth, Great Bear variants,
Winter Korps Snipers/Officer/Standard Bearer, Battle Mechanik, AC-2 Bison,
Kapitan Yana Kovoskiy, Old Umbrey Liegemen units, Animist, Old Umbrey
Defenses, Dire Wolf, Shock Trooper Gunners/Pikemen, Arkanists, Mortar Team,
Man-O-War Suppressors/Wrecking Crew, Mastodon, Winter Korp Infantry A/B,
Avalanche, Winter Korps Infantry Support Weapon Troopers, Old Umbrey
Primeval/Feral Warbeast, Old Umbrey Shearlings, Old Umbrey Ursine variants,
Kapitan Kazimir Morozov) -- none returned a genuine match, confirmed
2026-09-26.

9 of 51 catalog SKUs matched, each opened and verified individually.
WMH-328's Old Umbrey Auxiliary Expansion is priced at a different tier
(RRP £139.99) than the usual £134.99 Auxiliary Expansion seen in other
factions -- confirmed genuine via its contents (1 Warlock, 5 Solos, 8 Unit
models -- a larger box), not a data error.

Run once on Railway startup via Procfile. Safe to re-run -- idempotent.
"""
from decimal import Decimal

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Product, Retailer

_FIRESTORM_SLUG = 'firestorm-games'

# (gw_sku, gbp_price, url, in_stock)
_PRICES = [
    ('WMH-328', Decimal('125.99'), 'https://www.firestormgames.co.uk/warmachine:-khador-old-umbrey-auxiliary-expansion?aff=6a4ab07d1c6f9', True),
    ('WMH-325', Decimal('130.49'), 'https://www.firestormgames.co.uk/warmachine:-khador-old-umbrey-core-expansion?aff=6a4ab07d1c6f9', True),
    ('WMH-237', Decimal('62.99'), 'https://www.firestormgames.co.uk/warmachine:-khador-old-umbrey-battlegroup-box?aff=6a4ab07d1c6f9', True),
    ('WMH-253', Decimal('67.49'), 'https://www.firestormgames.co.uk/warmachine:-khador-old-umbrey-command-starter?aff=6a4ab07d1c6f9', True),
    ('WMH-072', Decimal('58.49'), 'https://www.firestormgames.co.uk/warmachine:-khador-sks-6-command-cadre-hips?aff=6a4ab07d1c6f9', True),
    ('WMH-289', Decimal('85.49'), 'https://www.firestormgames.co.uk/warmachine:-command-starter-for-the-khador-winter-korps-army?aff=6a4ab07d1c6f9', True),
    ('WMH-176', Decimal('62.99'), 'https://www.firestormgames.co.uk/warmachine:-khador-winter-korps-battlegroup-box?aff=6a4ab07d1c6f9', False),
    ('WMH-175', Decimal('121.49'), 'https://www.firestormgames.co.uk/warmachine:-khador-winter-korps-auxiliary-expansion?aff=6a4ab07d1c6f9', True),
    ('WMH-174', Decimal('130.49'), 'https://www.firestormgames.co.uk/warmachine:-khador-winter-korps-core-expansion?aff=6a4ab07d1c6f9', True),
]


class Command(BaseCommand):
    help = 'Seed Firestorm Games UK prices and URLs for Warmachine: Khador. Idempotent.'

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
                f'Seeded {seeded} Warmachine: Khador Firestorm Games prices. Skipped: {skipped}.'
            )
        )
